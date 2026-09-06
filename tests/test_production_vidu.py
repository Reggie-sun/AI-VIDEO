"""Offline Vidu adapter contract and transport boundary tests."""

from datetime import UTC, datetime, timedelta
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import hashlib
import json

import httpx
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.vidu import ViduVideoProvider, ViduTransportResponse, ViduTransportRequest, HttpxViduTransport
from ai_video.production.vidu_profile import ViduProviderProfile
from ai_video.production.video import (
    VideoGenerationMode, VideoProviderRegistry, VideoGenerationRequest,
    VideoFlexibleOutputRequirement, VideoImageReferenceBinding, VideoSubmission,
    VideoTaskState, VideoMediaReferenceBinding, build_video_paid_permit_binding,
)
from ai_video.production.video_requirement import (
    ActionEndpoint, CameraEndpoint, CameraIntent, ContinuityStateKind,
    GenerationIntent, SceneContinuity, SubjectAction, TypedStateReference,
)
from ai_video.production.models import (
    ProjectSnapshotPointer, RegistrySnapshotPointer, DependencyGraphSnapshotPointer,
    ActorIdentity,
)
from ai_video.production.paid_provider import (
    PaidProviderCallPreview, PaidProviderEgressItem, SecretReference,
    PaidProviderAuthorizationDecision, PaidProviderSubmitReceipt, PaidProviderSubmitOutcome,
)
from ai_video.production._state_commit_contracts import _DurablePaidProviderSubmitPermit, _PAID_PROVIDER_PERMIT_TOKEN


NOW = datetime(2026, 9, 5, tzinfo=UTC)
HASH = "a" * 64
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isomiso2"
URL = "https://media.vidu.example/output.mp4?private=token"


def _profile(**changes):
    values = dict(
        origin="https://api.vidu.cn",
        result_origins=("https://media.vidu.example",),
        cost_upper_bound_microunits=10_000_000,
        pricing_observed_at=NOW,
        pricing_expires_at=NOW + timedelta(days=1),
    )
    values.update(changes)
    return ViduProviderProfile(**values)


def test_registry_accepts_explicit_vidu_provider():
    provider = ViduVideoProvider(profile=_profile(), transport=None, credential=lambda: "test", now=lambda: NOW)
    registry = VideoProviderRegistry((("vidu", provider),))
    assert registry.resolve("vidu") is provider
    variants = provider.capabilities().variants
    assert {v.model_id for v in variants} == {"viduq3-pro", "viduq3-turbo", "viduq3", "viduq2-pro", "viduq2-turbo"}
    assert {v.mode for v in variants} == {VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO,
                                        VideoGenerationMode.REFERENCE_TO_VIDEO, VideoGenerationMode.VIDEO_EXTEND}


@pytest.mark.parametrize("origin", ["http://api.vidu.cn", "https://evil.example", "https://api.vidu.cn/"])
def test_profile_rejects_unsealed_api_origin(origin):
    with pytest.raises(ValueError):
        _profile(origin=origin)


def _request(profile=None, images=(), **changes):
    profile = profile or _profile()
    values = dict(
        generation_id="vidu-generation", provider_name="vidu", provider_kind="vidu",
        model_id="viduq3-pro", provider_profile=profile.pointer(),
        target_shot_id="shot", target_shot_revision=1, target_shot_content_hash=HASH,
        target_asset_role="primary_visual", target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO if images else VideoGenerationMode.TEXT_TO_VIDEO,
        prompt_text="A bird takes flight.", negative_prompt_text="", image_bindings=images,
        output_requirement=VideoFlexibleOutputRequirement(
            timing_mode="exact_seconds", duration_seconds=5,
            dimension_mode="adaptive" if images else "exact",
            width=None if images else 1280, height=None if images else 720,
            resolution_label="720p", ratio="adaptive" if images else "16:9",
            fps=24, container="mp4", mime_type="video/mp4", native_audio=True,
        ), seed=None,
        base_project=ProjectSnapshotPointer(path=Path("project.yaml"), revision=1, content_hash=HASH, file_sha256=HASH),
        base_registry=RegistrySnapshotPointer(path=Path(f"assets/registry.{HASH}.json"), revision_id=HASH, content_hash=HASH, file_sha256=HASH),
        base_dependency_graph=DependencyGraphSnapshotPointer(path=Path(f"state/dependency_graph.{HASH}.json"), revision_id=HASH, content_hash=HASH, file_sha256=HASH),
        input_artifact_ids=("shot",), output_asset_id="vidu-output",
    )
    values.update(changes)
    return VideoGenerationRequest.create(**values)


class Transport:
    def __init__(self):
        self.calls = []
        self.downloads = []
        self.submit_status = 200
        self.submit = {"task_id": "task-1", "model": "viduq3-pro", "state": "created"}
        self.query = {"state": "success", "creations": [{"id": "creation-1", "url": URL}]}
        self.body = MP4
        self.download_status = 200
        self.headers = {"content-type": "video/mp4"}
        self.error = None

    def request(self, request):
        self.calls.append(request)
        if self.error:
            raise self.error
        return ViduTransportResponse(self.submit_status if request.method == "POST" else 200, {},
                                     json.dumps(self.submit if request.method == "POST" else self.query).encode())

    @contextmanager
    def stream(self, request):
        self.downloads.append(request)
        yield self

    @property
    def status_code(self):
        return self.download_status

    def iter_bytes(self):
        for index in range(0, len(self.body), 3):
            yield self.body[index:index + 3]


def _setup(request=None, profile=None, **provider_args):
    profile = profile or _profile()
    transport = Transport()
    provider = ViduVideoProvider(profile=profile, transport=transport, credential=lambda: "PRIVATE-KEY", now=lambda: NOW, **provider_args)
    resolved = provider.resolve(request or _request(profile))
    preview = provider.preview(resolved)
    prompt = resolved.prompt_text.encode()
    items = [PaidProviderEgressItem(item_id="prompt", sha256=hashlib.sha256(prompt).hexdigest(), size_bytes=len(prompt), mime_type="text/plain", purpose="prompt")]
    items.extend(PaidProviderEgressItem(item_id=b.asset_id, sha256=b.asset_sha256, size_bytes=b.size_bytes, mime_type=b.mime_type, purpose="reference") for b in resolved.image_bindings)
    items.extend(PaidProviderEgressItem(item_id=b.asset_id, sha256=b.asset_sha256, size_bytes=b.size_bytes, mime_type=b.mime_type, purpose="reference") for b in resolved.media_bindings)
    paid = PaidProviderCallPreview.create(
        attempt_id="attempt-1", operation="video_generation", provider_kind="vidu", model_id=resolved.model_id,
        request_fingerprint=resolved.resolved_generation_hash, billing_mode="remote_metered",
        currency=preview.currency, estimated_cost_upper_bound_microunits=preview.estimated_cost_upper_bound_microunits,
        destination=preview.destination, method="POST", egress_items=tuple(items), retention_mode="provider_standard",
        provider_policy_snapshot_id="vidu-policy", secret_reference=SecretReference(kind="secret_store", reference_id="VIDU_API_KEY"),
    )
    auth = PaidProviderAuthorizationDecision.create(
        attempt_id=paid.attempt_id, preview_fingerprint=paid.preview_fingerprint, explicit_opt_in=True,
        actor=ActorIdentity(actor_id="tester", actor_kind="human"), opt_in_policy_receipt_id="opt-in",
        budget_policy_id="budget", budget_currency=paid.currency, project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=paid.estimated_cost_upper_bound_microunits, egress_authorized=True,
        egress_policy_receipt_id="egress", live_test_authorized=True, live_authorization_receipt_id="live",
        issued_at=NOW, expires_at=NOW + timedelta(minutes=5), max_submit_count=1,
    )
    permit = _DurablePaidProviderSubmitPermit(_PAID_PROVIDER_PERMIT_TOKEN,
        binding=build_video_paid_permit_binding(resolved, preview, paid, auth), durability_validator=lambda: True)
    return provider, transport, (resolved, preview, paid, auth, permit)


def _native_prompt_intent(scene_id="scene-room"):
    return GenerationIntent(
        open_state=TypedStateReference(kind=ContinuityStateKind.TYPED_TEXT, state_text="The shot begins from the supplied image."),
        close_state=TypedStateReference(kind=ContinuityStateKind.TYPED_TEXT, state_text="The action settles without changing the composition."),
        scene_continuity=SceneContinuity(scene_id=scene_id, state_constraints=("Keep the authored visible scene constraints.",)),
        subject_action=SubjectAction(start_state="The subject waits.", progression="The subject performs the authored action.",
            endpoint=ActionEndpoint(state_text="The subject reaches the authored endpoint.", required_change=True)),
        camera_intent=CameraIntent(movement="locked", stability="locked-off", framing_intent="preserve the original framing"),
        camera_endpoint=CameraEndpoint(start_framing="original composition", end_framing="same composition", position_lock=True, orientation_lock=True),
    )


def _submitted(provider, args):
    result = provider.submit(*args)
    resolved, _, paid, _, _ = args
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id=paid.attempt_id, request_fingerprint=resolved.resolved_generation_hash,
        preview_fingerprint=paid.preview_fingerprint, gate_receipt_fingerprint=HASH, reservation_id="reservation",
        outcome=PaidProviderSubmitOutcome.ACCEPTED, external_effect_id=result.external_effect_id, recorded_at=NOW,
    )
    return VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=receipt), receipt


def test_submit_poll_fetch_and_rotating_url_keep_exact_creation():
    provider, transport, args = _setup()
    submission, receipt = _submitted(provider, args)
    post = transport.calls[0]
    assert post.url == "https://api.vidu.cn/ent/v2/text2video"
    assert json.loads(post.body) == dict(model="viduq3-pro", prompt="A bird takes flight.", duration=5,
                                        resolution="720p", audio=True, off_peak=False, aspect_ratio="16:9")
    assert post.headers["authorization"] == "Token PRIVATE-KEY"
    observation = provider.get_status(submission, receipt)
    transport.query["creations"][0]["url"] = URL + "-refreshed"
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == MP4
    assert fetched.artifact_sha256 == hashlib.sha256(MP4).hexdigest()
    assert transport.downloads[0].headers == {"accept": "video/mp4"}
    assert "PRIVATE-KEY" not in repr(post)
    assert URL not in repr(transport.downloads[0]) + fetched.model_dump_json() + observation.model_dump_json()
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert sum(c.method == "POST" for c in transport.calls) == 1


@pytest.mark.parametrize("status,code", [(401, ErrorCode.VIDEO_PROVIDER_FAILED), (429, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN), (500, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN), (302, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN)])
def test_post_failure_never_retries(status, code):
    provider, transport, args = _setup()
    transport.submit_status = status
    with pytest.raises(AiVideoError) as exc:
        provider.submit(*args)
    assert exc.value.code == code
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("payload", [{}, {"task_id": "x", "model": "wrong", "state": "created"}, {"task_id": "x", "model": "viduq3-pro", "state": []}])
def test_bad_submit_response_is_unknown(payload):
    provider, transport, args = _setup()
    transport.submit = payload
    with pytest.raises(AiVideoError) as exc:
        provider.submit(*args)
    assert exc.value.code == ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN


@pytest.mark.parametrize("state,expected", [("created", VideoTaskState.QUEUED), ("queueing", VideoTaskState.QUEUED), ("processing", VideoTaskState.RUNNING), ("failed", VideoTaskState.FAILED)])
def test_task_states(state, expected):
    provider, transport, args = _setup()
    submission, receipt = _submitted(provider, args)
    transport.query = {"state": state}
    assert provider.get_status(submission, receipt).state is expected


@pytest.mark.parametrize("mutation", ["creation", "origin", "mime", "redirect", "length", "bytes"])
def test_fetch_rejects_changed_or_invalid_result(mutation):
    provider, transport, args = _setup()
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    if mutation == "creation": transport.query["creations"][0]["id"] = "other"
    if mutation == "origin": transport.query["creations"][0]["url"] = "https://evil.example/a.mp4"
    if mutation == "mime": transport.headers["content-type"] = "text/html"
    if mutation == "redirect": transport.download_status = 302
    if mutation == "length": transport.headers["content-length"] = "9999"
    if mutation == "bytes": transport.body = b"not a video at all"
    with pytest.raises(AiVideoError):
        provider.fetch(submission, receipt, observation, BytesIO())


@pytest.mark.parametrize("last", [False, True])
def test_image_and_start_end_payload(last):
    raw = b"image-test-bytes"
    images = tuple(VideoImageReferenceBinding(role=role, asset_id=role, asset_sha256=hashlib.sha256(raw).hexdigest(),
                    mime_type="image/png", size_bytes=len(raw), width=1280, height=720)
                   for role in (("first_frame", "last_frame") if last else ("first_frame",)))
    provider, transport, args = _setup(_request(images=images), image_resolver=lambda _: raw)
    provider.submit(*args)
    assert transport.calls[0].url.endswith("start-end2video" if last else "img2video")
    payload = json.loads(transport.calls[0].body)
    assert len(payload["images"]) == len(images)
    assert "is_rec" not in payload
    assert "aspect_ratio" not in payload


def test_expired_profile_blocks_preview_without_network():
    profile = _profile(pricing_expires_at=NOW + timedelta(seconds=1))
    provider = ViduVideoProvider(profile=profile, transport=None, credential=lambda: "key", now=lambda: NOW + timedelta(seconds=2))
    with pytest.raises(AiVideoError) as exc:
        provider.preview(provider.resolve(_request(profile)))
    assert exc.value.code == ErrorCode.PAID_PROVIDER_BUDGET_REJECTED


@pytest.mark.parametrize("version,expects_is_rec", [("1", False), ("2", True)])
def test_versioned_i2v_payload_only_adds_is_rec_for_new_v2(version, expects_is_rec):
    raw = b"image-test-bytes"
    image = VideoImageReferenceBinding(role="first_frame", asset_id="first-frame",
        asset_sha256=hashlib.sha256(raw).hexdigest(), mime_type="image/png",
        size_bytes=len(raw), width=1280, height=720)
    request = _request(images=(image,))
    values = request.model_dump(mode="python", exclude={"request_input_hash"})
    values.update(requirement_hash=HASH, provider_bound_request_hash=HASH,
        adapter_compiler_id="vidu-video-compiler", adapter_compiler_version=version,
        adapter_compiler_hash=HASH)
    versioned = VideoGenerationRequest.create(**values)
    provider = ViduVideoProvider(profile=_profile(), transport=None, credential=lambda: "key",
        image_resolver=lambda _: raw, now=lambda: NOW)
    _, body = provider._payload(provider.resolve(versioned))

    if not expects_is_rec:
        _, historic_body = provider._payload(provider.resolve(request))
        assert body == historic_body
        assert "is_rec" not in json.loads(body)
        return
    submitted_provider, transport, args = _setup(versioned, image_resolver=lambda _: raw)
    submitted_provider.submit(*args)
    assert json.loads(transport.calls[0].body)["is_rec"] is False


def test_transport_does_not_follow_redirects():
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": "https://evil.example"})
    client = httpx.Client(transport=httpx.MockTransport(respond), follow_redirects=True)
    transport = HttpxViduTransport(client=client)
    assert transport.request(ViduTransportRequest("GET", "https://api.vidu.cn/ent/v2/tasks/t/creations", {})).status_code == 302
    assert len(calls) == 1
    client.close()


def test_fetch_rejects_replacement_profile_before_query():
    provider, transport, args = _setup()
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    replacement = ViduVideoProvider(profile=_profile(result_origins=("https://other.example",)),
                                    transport=transport, credential=lambda: "key", now=lambda: NOW)
    count = len(transport.calls)
    with pytest.raises(AiVideoError):
        replacement.fetch(submission, receipt, observation, BytesIO())
    assert len(transport.calls) == count
    assert transport.downloads == []


def test_preview_rejects_same_capability_id_with_changed_model():
    from ai_video.production.video import ResolvedVideoGenerationRequest
    provider, transport, _ = _setup()
    request = _request(model_id="unapproved-model")
    variant = provider.capabilities().variants[0].model_copy(update={"model_id": "unapproved-model"})
    forged = ResolvedVideoGenerationRequest.create(request=request, capability=variant,
        effective_output=request.output_requirement, effective_seed=None, effective_negative_prompt_text="")
    with pytest.raises(AiVideoError):
        provider.preview(forged)
    assert transport.calls == []


def test_real_service_durable_permit_and_restart_replay(tmp_path):
    from production_project_factory import write_production_project, make_manifest_23_project
    from ai_video.production.models import ProductionManifest
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    write_production_project(tmp_path)
    make_manifest_23_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
    manifest_path.write_text(manifest.model_copy(update={"schema_version": "2.7"}).model_dump_json())
    provider, transport, (resolved, _, paid, auth, _) = _setup()
    committer = ProductionStateCommitter(tmp_path,
        paid_provider_authorizer=lambda exact: auth if exact == paid else None, paid_provider_clock=lambda: NOW)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=paid.attempt_id, request=resolved)
    submission = service.submit_once(attempt_id=paid.attempt_id, paid_preview=paid, reservation_id="reservation")
    assert submission.resolved_generation_hash == resolved.resolved_generation_hash
    restarted = VideoGenerationService(committer=ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: NOW), provider=provider)
    with pytest.raises(AiVideoError):
        restarted.submit_once(attempt_id=paid.attempt_id, paid_preview=paid, reservation_id="reservation")
    assert len(transport.calls) == 1


@pytest.mark.parametrize("change", [{"seed": 0}, {"seed": 2**32}, {"negative_prompt_text": "bad"}, {"model_id": "viduq2"}, {"prompt_text": "a" * 5001}])
def test_invalid_request_rejected_before_transport(change):
    provider, transport, _ = _setup()
    with pytest.raises(AiVideoError):
        provider.resolve(_request(**change))
    assert transport.calls == []


def test_api_transport_excludes_injected_client_auth_and_cookies():
    seen = []
    def respond(request):
        seen.append(request)
        return httpx.Response(200, content=b"{}")
    with httpx.Client(transport=httpx.MockTransport(respond), auth=("user", "password"),
                      headers={"Authorization": "CLIENT-SECRET"}, cookies={"private": "cookie"}) as client:
        transport = HttpxViduTransport(client=client)
        transport.request(ViduTransportRequest("POST", "https://api.vidu.cn/ent/v2/text2video", {"authorization": "Token SUPPLIER"}))
    assert seen[0].headers["authorization"] == "Token SUPPLIER"
    assert "cookie" not in seen[0].headers
    assert len(seen) == 1


def test_router_compiler_resolver_uses_vidu_capability_without_network():
    from test_production_provider_neutral_adapters import _replace_requirement
    from test_production_shot_router import _context, _verified_requirement, _policy, _lifecycle
    from ai_video.production.shot_router import AdapterCompilerContract, VideoGenerationResolver, MotionRequirement
    from ai_video.production.video_requirement import OutputNeed, AudioNeed
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    provider, transport, args = _setup()
    output = args[0].effective_output
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    projection = _replace_requirement(_verified_requirement(context),
        generation_intent=_native_prompt_intent(context.activated_shot.scene_id),
        output_need=OutputNeed(duration_seconds=5,
            width=1280, height=720, aspect_ratio="16:9", fps=24, container_mime="video/mp4"),
        audio_need=AudioNeed.REQUIRED)
    routing = VideoGenerationResolver()._bind_requirement(
        projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_profile().pointer(), capabilities=provider.capabilities(),
        selected_capability_id=args[0].capability_id, output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="2"),
    )
    assert routing.provider_bound_request is not None, routing.decision.model_dump_json()
    compiled = provider.compile_request(routing.provider_bound_request, projection.requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert provider.resolve(compiled.request).capability_id == args[0].capability_id
    assert transport.calls == []
    legacy_routing = VideoGenerationResolver()._bind_requirement(
        projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_profile().pointer(), capabilities=provider.capabilities(),
        selected_capability_id=args[0].capability_id, output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="1"),
    )
    assert legacy_routing.provider_bound_request is not None
    legacy = provider.compile_request(legacy_routing.provider_bound_request, projection.requirement)
    from ai_video.production.video_compiler import ProviderRequirementUnsupported, ProviderRequirementUnsupportedReason
    assert isinstance(legacy, ProviderRequirementUnsupported)
    assert legacy.reason is ProviderRequirementUnsupportedReason.COMPILER_VERSION_UNSUPPORTED
    with pytest.warns(UserWarning):
        malformed = provider.compile_request(
            routing.provider_bound_request,
            projection.requirement.model_copy(update={"generation_intent": "malformed"}),
        )
    assert isinstance(malformed, ProviderRequirementUnsupported)
    assert malformed.reason is ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH


@pytest.mark.parametrize("last", [False, True])
def test_router_compiled_v2_i2v_posts_is_rec_and_ordered_exact_frames(last):
    import base64
    from test_production_provider_neutral_adapters import _replace_requirement
    from test_production_shot_router import _asset, _context, _lifecycle, _policy, _verified_requirement
    from ai_video.production.shot_router import AdapterCompilerContract, MotionRequirement, VideoGenerationResolver
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from ai_video.production.video_requirement import (
        AssetEvidence, AudioNeed, GenerationMode as RequirementGenerationMode,
        OutputGeometryPolicy, OutputNeed, SemanticReferenceRole,
    )

    raw_by_role = {"first_frame": b"canonical-first", "last_frame": b"canonical-last"}
    first = _asset("first_frame", "router-first", hashlib.sha256(raw_by_role["first_frame"]).hexdigest(),
        size_bytes=len(raw_by_role["first_frame"]), width=1280, height=720)
    endpoint = _asset("last_frame", "router-last", hashlib.sha256(raw_by_role["last_frame"]).hexdigest(),
        size_bytes=len(raw_by_role["last_frame"]), width=1280, height=720)
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False,
        keyframe=first, last_frame=endpoint if last else None)
    roles = (SemanticReferenceRole.FIRST_FRAME,)
    assets = (first,)
    if last:
        roles += (SemanticReferenceRole.LAST_FRAME,)
        assets += (endpoint,)
    evidence = tuple(AssetEvidence(role=role, asset_id=asset.asset_id,
        asset_sha256=asset.asset_sha256, mime_type=asset.mime_type, width=asset.width,
        height=asset.height, size_bytes=asset.size_bytes,
        canonical_owner_id=asset.canonical_owner_id,
        canonical_owner_content_hash=asset.canonical_owner_content_hash)
        for role, asset in zip(roles, assets, strict=True))
    output = _request(images=(VideoImageReferenceBinding(role="first_frame", asset_id="unused",
        asset_sha256=hashlib.sha256(b"unused").hexdigest(), mime_type="image/png",
        size_bytes=len(b"unused"), width=1280, height=720),)).output_requirement
    projection = _replace_requirement(_verified_requirement(context),
        generation_mode=(RequirementGenerationMode.FIRST_LAST_FRAME_VIDEO if last else RequirementGenerationMode.IMAGE_TO_VIDEO),
        generation_intent=_native_prompt_intent(context.activated_shot.scene_id),
        semantic_reference_roles=roles, asset_evidence=evidence,
        output_need=OutputNeed(duration_seconds=output.duration_seconds,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE, aspect_ratio="adaptive",
            fps=output.fps, container_mime=output.mime_type), audio_need=AudioNeed.REQUIRED)
    provider, _, _ = _setup()
    routing = VideoGenerationResolver()._bind_requirement(projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True), provider_profile=_profile().pointer(),
        capabilities=provider.capabilities(), selected_capability_id="viduq3-pro-i2v-v1",
        output_requirement=output, lifecycle=_lifecycle(context).model_copy(update={
            "input_artifact_ids": (context.target_shot_id, *(asset.asset_id for asset in assets)),
        }), compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="2"))
    assert routing.provider_bound_request is not None, routing.decision.model_dump_json()
    compiled = provider.compile_request(routing.provider_bound_request, projection.requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    raw_by_asset = {asset.asset_id: raw_by_role[role] for role, asset in zip(("first_frame", "last_frame"), (first, endpoint), strict=True)}
    provider, transport, args = _setup(compiled.request, image_resolver=lambda binding: raw_by_asset[binding.asset_id])
    provider.submit(*args)
    payload = json.loads(transport.calls[0].body)
    assert payload["is_rec"] is False
    assert payload["audio"] is True
    assert "The subject performs the authored action." in payload["prompt"]
    assert "收束状态" in payload["prompt"]
    assert "generation_mode=" not in payload["prompt"]
    assert transport.calls[0].url.endswith("start-end2video" if last else "img2video")
    expected_images = [raw_by_role["first_frame"]]
    if last:
        expected_images.append(raw_by_role["last_frame"])
    assert [base64.b64decode(value.split(",", 1)[1]) for value in payload["images"]] == expected_images


def test_missing_authorization_and_credential_failure_do_not_consume_permit():
    provider, transport, args = _setup()
    resolved, preview, paid, auth, permit = args
    with pytest.raises(AiVideoError):
        provider.submit(resolved, preview, paid, auth, None)
    provider._credential = lambda: "bad\nkey"
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert permit._validate_paid_provider_operation_permit(**build_video_paid_permit_binding(resolved, preview, paid, auth))
    assert transport.calls == []


def _references(count):
    return tuple(VideoImageReferenceBinding(role="reference", asset_id=f"subject-{i:02}",
        asset_sha256=hashlib.sha256(f"image-{i}".encode()).hexdigest(),
        mime_type="image/png", size_bytes=len(f"image-{i}"), width=1280, height=720)
        for i in range(count))


@pytest.mark.parametrize("model", ["viduq3", "viduq3-turbo"])
@pytest.mark.parametrize("count", [1, 2, 7])
def test_reference_to_video_posts_ordered_subject_images(model, count):
    import base64
    images = _references(count)
    request = _request(images=images, mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        model_id=model, output_requirement=_request().output_requirement)
    provider, transport, args = _setup(request,
        image_resolver=lambda b: f"image-{int(b.asset_id[-2:])}".encode())
    transport.submit["model"] = model
    provider.submit(*args)
    payload = json.loads(transport.calls[0].body)
    assert transport.calls[0].url.endswith("/reference2video")
    assert payload["aspect_ratio"] == "16:9"
    assert payload["model"] == model
    assert [base64.b64decode(s.split(",")[1]) for s in payload["images"]] == [f"image-{i}".encode() for i in range(count)]


def test_extension_capabilities_are_q2_only_with_exact_source_count():
    provider, _, _ = _setup()
    variants = [v for v in provider.capabilities().variants if v.mode is VideoGenerationMode.VIDEO_EXTEND]
    assert {v.model_id for v in variants} == {"viduq2-pro", "viduq2-turbo"}
    assert all(v.media_capabilities[0].min_count == v.media_capabilities[0].max_count == 1 for v in variants)
    assert all(not v.seed_supported for v in variants)


def _extension_input(profile=None):
    from ai_video.production.vidu_source import ViduExtensionSource
    from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt
    provider, _, args = _setup(_request(profile, output_requirement=_request().output_requirement.model_copy(update={"native_audio": False})), profile=profile)
    submission, paid = _submitted(provider, args)
    observation = provider.get_status(submission, paid)
    fetched = provider.fetch(submission, paid, observation, BytesIO())
    measured = MeasuredVideoMetadata(container_name="mp4", codec_name="h264", width=1280, height=720,
        fps_numerator=24, fps_denominator=1, duration_milliseconds=5000, frame_count=120,
        audio_stream_count=0, size_bytes=len(MP4), artifact_sha256=hashlib.sha256(MP4).hexdigest())
    source = ViduExtensionSource(submission=submission, submit_receipt=paid, fetch_receipt=fetched,
        probe_receipt=VideoProbeReceipt.create(request=args[0], fetch_receipt=fetched, measured=measured))
    binding = VideoMediaReferenceBinding(kind="video", role="reference_video", asset_id="source-video",
        asset_sha256=measured.artifact_sha256, mime_type="video/mp4", duration_millis=5000,
        size_bytes=len(MP4), width=1280, height=720, fps=24)
    return binding, source


def _extension_request(binding, model="viduq2-turbo", added=4, images=()):
    output = _request().output_requirement.model_copy(update=dict(
        duration_seconds=binding.duration_millis // 1000 + added, native_audio=False,
        dimension_mode="adaptive", width=None, height=None, ratio="adaptive"))
    return _request(model_id=model, mode=VideoGenerationMode.VIDEO_EXTEND,
        media_bindings=(binding,), output_requirement=output, images=images)


@pytest.mark.parametrize("model", ["viduq2-pro", "viduq2-turbo"])
@pytest.mark.parametrize("added,last", [(1, False), (7, True)])
def test_extension_requeries_exact_source_and_posts_added_duration(model, added, last):
    binding, source = _extension_input()
    images = (_references(1)[0].model_copy(update={"role": "last_frame"}),) if last else ()
    provider, transport, args = _setup(_extension_request(binding, model, added, images),
        extension_source=lambda _: source, image_resolver=lambda _: b"image-0")
    transport.submit["model"] = model
    submission, receipt = _submitted(provider, args)
    assert [c.method for c in transport.calls] == ["GET", "GET", "POST"]
    assert transport.downloads[0].headers == {"accept": "video/mp4"}
    payload = json.loads(transport.calls[-1].body)
    assert transport.calls[-1].url.endswith("/extend")
    assert payload["video_creation_id"] == "creation-1"
    assert payload["duration"] == added
    assert args[0].effective_output.duration_seconds == 5 + added
    assert bool(payload.get("images")) == last
    assert not {"video_url", "aspect_ratio", "audio", "off_peak", "seed"} & payload.keys()
    assert "source-video" in args[1].egress_item_ids
    assert next(i for i in args[2].egress_items if i.item_id == "source-video").sha256 == binding.asset_sha256
    observation = provider.get_status(submission, receipt)
    assert provider.fetch(submission, receipt, observation, BytesIO()).artifact_sha256 == hashlib.sha256(MP4).hexdigest()
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert sum(c.method == "POST" for c in transport.calls) == 1


@pytest.mark.parametrize("change", ["missing", "hash", "probe", "creation", "running", "origin", "remote_bytes"])
def test_extension_bad_source_blocks_post_without_consuming_permit(change):
    binding, source = _extension_input()
    if change == "hash": binding = binding.model_copy(update={"asset_sha256": HASH})
    if change == "probe": source = source.model_copy(update={"probe_receipt": source.probe_receipt.model_copy(update={"fetch_fingerprint": HASH})})
    if change == "origin":
        from ai_video.production.vidu_source import ViduExtensionSource
        from ai_video.production.video_artifact import VideoProbeReceipt
        profile = _profile(origin="https://api.vidu.com")
        p, _, a = _setup(profile=profile)
        s, r = _submitted(p, a)
        f = p.fetch(s, r, p.get_status(s, r), BytesIO())
        source = ViduExtensionSource(submission=s, submit_receipt=r, fetch_receipt=f,
            probe_receipt=VideoProbeReceipt.create(request=a[0], fetch_receipt=f, measured=source.probe_receipt.measured))
    provider, transport, args = _setup(_extension_request(binding),
        extension_source=None if change == "missing" else lambda _: source)
    if change == "creation": transport.query["creations"][0]["id"] = "other"
    if change == "running": transport.query["state"] = "processing"
    if change == "remote_bytes": transport.body = MP4 + b"changed"
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert all(c.method == "GET" for c in transport.calls)
    r, p, paid, auth, permit = args
    assert permit._validate_paid_provider_operation_permit(**build_video_paid_permit_binding(r, p, paid, auth))


@pytest.mark.parametrize("added", [0, 8])
def test_extension_added_duration_bounds(added):
    binding, _ = _extension_input()
    provider, _, _ = _setup()
    with pytest.raises(AiVideoError):
        provider.resolve(_extension_request(binding, added=added))


@pytest.mark.parametrize("change", ["short", "long", "fractional", "fps", "seed", "q3", "audio", "extra_video", "first_frame"])
def test_extension_rejects_unsupported_source_or_output(change):
    binding, _ = _extension_input()
    changes = {"short": {"duration_millis": 3000}, "long": {"duration_millis": 61000},
               "fractional": {"duration_millis": 5500}, "fps": {"fps": 30}}
    binding = binding.model_copy(update=changes.get(change, {}))
    request = _extension_request(binding)
    values = request.model_dump(mode="python", exclude={"request_input_hash"})
    if change == "seed": values["seed"] = 1
    if change == "q3": values["model_id"] = "viduq3-turbo"
    if change == "audio": values["output_requirement"]["native_audio"] = True
    if change == "extra_video": values["media_bindings"] = (binding, binding.model_copy(update={"asset_id": "source-video-2"}))
    if change == "first_frame": values["image_bindings"] = (_references(1)[0].model_copy(update={"role": "first_frame"}),)
    provider, transport, _ = _setup()
    with pytest.raises(AiVideoError):
        provider.resolve(VideoGenerationRequest.create(**values))
    assert transport.calls == []


def test_extension_source_egress_must_bind_exact_bytes_even_with_matching_permit():
    binding, source = _extension_input()
    provider, transport, (resolved, preview, paid, auth, _) = _setup(_extension_request(binding), extension_source=lambda _: source)
    values = paid.model_dump(mode="python", exclude={"preview_fingerprint"})
    values["egress_items"] = tuple(i.model_copy(update={"sha256": HASH}) if i.item_id == binding.asset_id else i
                                   for i in paid.egress_items)
    paid = PaidProviderCallPreview.create(**values)
    values = auth.model_dump(mode="python", exclude={"authorization_fingerprint"})
    values["preview_fingerprint"] = paid.preview_fingerprint
    auth = PaidProviderAuthorizationDecision.create(**values)
    permit_binding = build_video_paid_permit_binding(resolved, preview, paid, auth)
    permit = _DurablePaidProviderSubmitPermit(_PAID_PROVIDER_PERMIT_TOKEN,
        binding=permit_binding, durability_validator=lambda: True)
    with pytest.raises(AiVideoError):
        provider.submit(resolved, preview, paid, auth, permit)
    assert permit._validate_paid_provider_operation_permit(**permit_binding)
    assert transport.calls == []


@pytest.mark.parametrize("expiry", ["authorization", "pricing"])
def test_extension_rechecks_expiry_after_source_query_before_consuming_permit(expiry):
    profile = _profile(pricing_expires_at=NOW + timedelta(minutes=1 if expiry == "pricing" else 60))
    binding, source = _extension_input(profile)
    values = _extension_request(binding).model_dump(mode="python", exclude={"request_input_hash"})
    values["provider_profile"] = profile.pointer()
    provider, transport, args = _setup(VideoGenerationRequest.create(**values), profile=profile, extension_source=lambda _: source)
    clock = [NOW]
    provider._now = lambda: clock[0]
    original = transport.request
    def slow_query(request):
        response = original(request)
        if request.method == "GET": clock[0] = NOW + timedelta(minutes=2 if expiry == "pricing" else 6)
        return response
    transport.request = slow_query
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert transport.calls and all(c.method == "GET" for c in transport.calls)
    resolved, preview, paid, auth, permit = args
    assert permit._validate_paid_provider_operation_permit(**build_video_paid_permit_binding(resolved, preview, paid, auth))


def test_extension_prompt_limit_is_2000():
    binding, _ = _extension_input()
    values = _extension_request(binding).model_dump(mode="python", exclude={"request_input_hash"})
    values["prompt_text"] = "x" * 2001
    provider, transport, _ = _setup()
    with pytest.raises(AiVideoError):
        provider.resolve(VideoGenerationRequest.create(**values))
    assert transport.calls == []


@pytest.mark.parametrize("change", ["count", "size", "role", "duration", "prompt", "model", "audio_reference"])
def test_r2v_rejects_unsupported_inputs_before_network(change):
    images = _references(8 if change == "count" else 1)
    if change == "size": images = (images[0].model_copy(update={"width": 127}),)
    if change == "role": images = (images[0].model_copy(update={"role": "first_frame"}),)
    values = dict(model_id="viduq3", mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        output_requirement=_request().output_requirement)
    if change == "duration": values["output_requirement"] = values["output_requirement"].model_copy(update={"duration_seconds": 2})
    if change == "prompt": values["prompt_text"] = "x" * 2001
    if change == "model": values["model_id"] = "viduq3-pro"
    if change == "audio_reference": values["media_bindings"] = (VideoMediaReferenceBinding(kind="audio", role="reference_audio",
        asset_id="audio", asset_sha256=HASH, mime_type="audio/mpeg", duration_millis=1000, size_bytes=100),)
    provider, transport, _ = _setup()
    with pytest.raises(AiVideoError):
        provider.resolve(_request(images=images, **values))
    assert transport.calls == []


def test_extension_and_r2v_use_real_service_durable_permit(tmp_path):
    from production_project_factory import write_production_project, make_manifest_23_project
    from ai_video.production.models import ProductionManifest
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    binding, source = _extension_input()
    requests = (_extension_request(binding), _request(images=_references(2), model_id="viduq3",
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO, output_requirement=_request().output_requirement))
    for index, request in enumerate(requests):
        root = tmp_path / str(index)
        root.mkdir()
        write_production_project(root)
        make_manifest_23_project(root)
        manifest_path = root / "state/manifest.json"
        manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
        manifest_path.write_text(manifest.model_copy(update={"schema_version": "2.7"}).model_dump_json())
        provider, transport, (resolved, _, paid, auth, _) = _setup(request, extension_source=lambda _: source,
            image_resolver=lambda b: f"image-{int(b.asset_id[-2:])}".encode())
        transport.submit["model"] = request.model_id
        committer = ProductionStateCommitter(root, paid_provider_authorizer=lambda exact: auth if exact == paid else None,
            paid_provider_clock=lambda: NOW)
        service = VideoGenerationService(committer=committer, provider=provider)
        service.start(attempt_id=paid.attempt_id, request=resolved)
        service.submit_once(attempt_id=paid.attempt_id, paid_preview=paid, reservation_id="reservation")
        restarted = VideoGenerationService(committer=ProductionStateCommitter(root, paid_provider_clock=lambda: NOW), provider=provider)
        with pytest.raises(AiVideoError):
            restarted.submit_once(attempt_id=paid.attempt_id, paid_preview=paid, reservation_id="reservation")
        assert sum(c.method == "POST" for c in transport.calls) == 1


@pytest.mark.parametrize("extend", [False, True])
def test_r2v_and_extension_router_compiler_reach_adapter(extend):
    from test_production_provider_neutral_adapters import _replace_requirement
    from test_production_shot_router import _context, _verified_requirement, _policy, _lifecycle, _asset
    from ai_video.production.shot_router import AdapterCompilerContract, VideoGenerationResolver, MotionRequirement
    from ai_video.production.video_requirement import (
        AssetEvidence, AudioNeed, OutputNeed, OutputGeometryPolicy, GenerationMode as RequirementGenerationMode, SemanticReferenceRole,
    )
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    provider, transport, _ = _setup()
    if extend:
        binding, _ = _extension_input()
        output = _extension_request(binding).output_requirement
        asset = _asset("reference_video", "source-video", binding.asset_sha256, mime_type="video/mp4",
            width=1280, height=720, duration_millis=5000, fps=24)
        context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False, reference_videos=(asset,))
        mode, semantic = RequirementGenerationMode.VIDEO_EXTEND, SemanticReferenceRole.VIDEO_REFERENCE
        capability_id = "viduq2-turbo-extend-v1"
    else:
        from tests.fixtures.planning_factory import make_scene
        scene = make_scene(scene_id="scene-room")
        output = _request().output_requirement
        asset = _asset("scene_reference", "scene", HASH, mime_type="image/png", width=1280, height=720,
            canonical_owner_content_hash=scene.content_hash)
        context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False, scene_reference=asset,
            scene_content_hash=scene.content_hash)
        mode, semantic = RequirementGenerationMode.REFERENCE_TO_VIDEO, SemanticReferenceRole.SCENE
        capability_id = "viduq3-r2v-v1"
    base = _verified_requirement(context)
    evidence = (AssetEvidence(role=semantic,
            asset_id=asset.asset_id, asset_sha256=asset.asset_sha256, mime_type=asset.mime_type,
            width=asset.width, height=asset.height, size_bytes=asset.size_bytes,
            duration_millis=asset.duration_millis, fps=asset.fps,
            canonical_owner_id=asset.canonical_owner_id, canonical_owner_content_hash=asset.canonical_owner_content_hash),)
    projection = _replace_requirement(base, generation_mode=mode,
        generation_intent=_native_prompt_intent(context.activated_shot.scene_id),
        semantic_reference_roles=(semantic,), asset_evidence=evidence,
        output_need=OutputNeed(duration_seconds=output.duration_seconds, width=output.width, height=output.height,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE if extend else OutputGeometryPolicy.EXACT,
            aspect_ratio=output.ratio, fps=24, container_mime="video/mp4"),
        audio_need=AudioNeed.FORBIDDEN if extend else AudioNeed.REQUIRED)
    routing = VideoGenerationResolver()._bind_requirement(projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True), provider_profile=_profile().pointer(),
        capabilities=provider.capabilities(), selected_capability_id=capability_id, output_requirement=output,
        lifecycle=_lifecycle(context).model_copy(update={"input_artifact_ids": (context.target_shot_id, asset.asset_id)}),
        compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="2"))
    assert routing.provider_bound_request is not None, routing.decision.model_dump_json()
    compiled = provider.compile_request(routing.provider_bound_request, projection.requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert provider.resolve(compiled.request).capability_id == capability_id
    assert transport.calls == []
