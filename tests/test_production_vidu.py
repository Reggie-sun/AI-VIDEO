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
    VideoTaskState, build_video_paid_permit_binding,
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
    assert {v.model_id for v in variants} == {"viduq3-pro", "viduq3-turbo"}
    assert {v.mode for v in variants} == {VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO}


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
    assert "aspect_ratio" not in payload


def test_expired_profile_blocks_preview_without_network():
    profile = _profile(pricing_expires_at=NOW + timedelta(seconds=1))
    provider = ViduVideoProvider(profile=profile, transport=None, credential=lambda: "key", now=lambda: NOW + timedelta(seconds=2))
    with pytest.raises(AiVideoError) as exc:
        provider.preview(provider.resolve(_request(profile)))
    assert exc.value.code == ErrorCode.PAID_PROVIDER_BUDGET_REJECTED


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


def test_transport_excludes_injected_client_auth_and_cookies():
    seen = []
    def respond(request):
        seen.append(request)
        return httpx.Response(200, content=b"{}")
    with httpx.Client(transport=httpx.MockTransport(respond), auth=("user", "password"),
                      headers={"Authorization": "CLIENT-SECRET"}, cookies={"private": "cookie"}) as client:
        transport = HttpxViduTransport(client=client)
        transport.request(ViduTransportRequest("POST", "https://api.vidu.cn/ent/v2/text2video", {"authorization": "Token SUPPLIER"}))
        with transport.stream(ViduTransportRequest("GET", URL, {"accept": "video/mp4"})) as response:
            list(response.iter_bytes())
    assert seen[0].headers["authorization"] == "Token SUPPLIER"
    assert "cookie" not in seen[0].headers
    assert "authorization" not in seen[1].headers
    assert "cookie" not in seen[1].headers


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
        output_need=OutputNeed(duration_seconds=5,
            width=1280, height=720, aspect_ratio="16:9", fps=24, container_mime="video/mp4"),
        audio_need=AudioNeed.REQUIRED)
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_profile().pointer(), capabilities=provider.capabilities(),
        selected_capability_id=args[0].capability_id, output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="1"),
    )
    assert routing.provider_bound_request is not None, routing.decision.model_dump_json()
    compiled = provider.compile_request(routing.provider_bound_request, projection.requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert provider.resolve(compiled.request).capability_id == args[0].capability_id
    assert transport.calls == []


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
