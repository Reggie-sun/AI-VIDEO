"""Exact multimodal METASO requests and failure boundaries, without network."""

import hashlib
import json

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.metaso_h3 import (
    METASO_BASE_URL, MetasoH3Profile, MetasoH3VideoProvider,
    metaso_environment_credential,
)
from ai_video.production.minimax_h3 import MiniMaxH3TransportResponse
from ai_video.production.paid_provider import PaidProviderCallPreview, SecretReference
from ai_video.production.video import (
    VideoGenerationMode, VideoImageReferenceBinding, VideoMediaReferenceBinding,
    VideoSubmission, build_video_paid_permit_binding,
)
from test_production_minimax_h3 import (
    _FakeTransport, _fixed_now, _paid_authorization, _paid_submit_receipt,
    _real_permit, _request, _submit_response,
)


def setup(*, audio=True, context_ir=True, transport=None):
    raw = {"a-scene": b"original scene", "b-COCO": b"original COCO", "c-Nosha": b"original Nosha"}
    images = tuple(VideoImageReferenceBinding(role="reference", asset_id=k,
        asset_sha256=hashlib.sha256(v).hexdigest(), mime_type="image/png",
        width=1672, height=941, size_bytes=len(v)) for k, v in raw.items())
    media = ()
    if audio:
        raw["coco-canvas-dialogue"] = b"original confirmed WAV"
        media = (VideoMediaReferenceBinding(kind="audio", role="reference_audio",
            asset_id="coco-canvas-dialogue", asset_sha256=hashlib.sha256(raw["coco-canvas-dialogue"]).hexdigest(),
            mime_type="audio/wav", duration_millis=5000, size_bytes=len(raw["coco-canvas-dialogue"])),)
    profile = MetasoH3Profile(duration=15, resolution="768P", aspect_ratio="16:9",
                             context_ir=context_ir, cost_upper_bound_microunits=2_000_000)
    transport = transport or _FakeTransport(submit_response=_submit_response())
    provider = MetasoH3VideoProvider(profile=profile, transport=transport,
        credential=lambda: "FAKE-METASO-TEST-ONLY", now=_fixed_now,
        reference_resolver=lambda b: raw[b.asset_id])
    request = _request(provider_name="metaso_h3", provider_kind="metaso_h3",
        provider_profile=profile.pointer(), mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=images, media_bindings=media, output_requirement=profile.output(),
        prompt_text="Image 1 scene; Image 2 COCO; Image 3 Nosha; Audio 1 voice. One causal take.")
    resolved = provider.resolve(request)
    preview = provider.preview(resolved)
    paid = PaidProviderCallPreview.create(attempt_id="attempt-metaso-1", operation="video_generation",
        provider_kind="metaso_h3", model_id="MiniMax-H3", request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered", currency="CNY", estimated_cost_upper_bound_microunits=2_000_000,
        destination="https://metaso.cn", method="POST", egress_items=provider.egress_items(resolved),
        retention_mode="provider_standard", provider_policy_snapshot_id="metaso-h3-test",
        secret_reference=SecretReference(kind="secret_store", reference_id="METASO_API_KEY"))
    auth = _paid_authorization(paid)
    permit = _real_permit(build_video_paid_permit_binding(resolved, preview, paid, auth))
    return provider, resolved, preview, paid, auth, permit, transport, raw


def test_exact_canvas_multimodal_body_and_one_use_permit():
    provider, request, preview, paid, auth, permit, transport, raw = setup()
    result = provider.submit(request, preview, paid, auth, permit)
    assert result.external_effect_id == "task-h3-1"
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call.url == METASO_BASE_URL + "/v2/video_generation"
    body = json.loads(call.body)
    assert {k: v for k, v in body.items() if k != "content"} == {
        "model": "MiniMax-H3", "duration": 15, "resolution": "768P", "ratio": "16:9",
        "context_ir_enabled": True}
    assert [i["type"] for i in body["content"]] == ["text", "image_url", "image_url", "image_url", "audio_url"]
    assert [i["role"] for i in body["content"][1:]] == ["reference_image"] * 3 + ["reference_audio"]
    import base64
    for item, binding in zip(body["content"][1:], (*request.image_bindings, *request.media_bindings), strict=True):
        uri = item[item["type"]]["url"]
        assert base64.b64decode(uri.split(",", 1)[1]) == raw[binding.asset_id]
    assert "FAKE-METASO" not in repr(call) + repr(result) + call.body.decode()
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, paid, auth, permit)
    assert len(transport.calls) == 1


def test_context_ir_false_is_explicit_and_profile_bound():
    provider, request, *_ = setup(context_ir=False)
    assert json.loads(provider.native_payload(request))["context_ir_enabled"] is False
    other, *_ = setup(context_ir=True)
    with pytest.raises(AiVideoError):
        other.preview(request)


@pytest.mark.parametrize("mutation", ["bytes", "size", "prompt", "credential", "no_permit"])
def test_invalid_inputs_are_zero_effect(mutation):
    provider, request, preview, paid, auth, permit, transport, raw = setup()
    if mutation == "bytes":
        raw["b-COCO"] = b"wrong bytes"
    elif mutation == "size":
        raw["b-COCO"] += b"extra"
    elif mutation == "prompt":
        request = request.model_copy(update={"prompt_text": "changed"})
    elif mutation == "credential":
        provider._credential = lambda: ""
    else:
        permit = object()
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, paid, auth, permit)
    assert not transport.calls


@pytest.mark.parametrize("response", [MiniMaxH3TransportResponse(200, {}, b"{}"),
    MiniMaxH3TransportResponse(503, {}, b"secret response"),
    MiniMaxH3TransportResponse(200, {}, b'{"task_id":"x","base_resp":{"status_code":1}}')])
def test_uncertain_acknowledgement_fences_permit(response):
    transport = _FakeTransport(submit_response=response)
    provider, request, preview, paid, auth, permit, *_ = setup(transport=transport)
    with pytest.raises(AiVideoError) as exc:
        provider.submit(request, preview, paid, auth, permit)
    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, paid, auth, permit)
    assert len(transport.calls) == 1


def test_audio_total_duration_and_audio_only_are_rejected():
    provider, request, *_ = setup()
    original = request.activation_scope.request
    bindings = tuple(original.media_bindings[0].model_copy(update={
        "asset_id": f"voice-{i}", "duration_millis": 6000}) for i in range(3))
    with pytest.raises(AiVideoError):
        provider.resolve(original.model_copy(update={"media_bindings": bindings}))
    with pytest.raises(AiVideoError):
        provider.resolve(original.model_copy(update={"image_bindings": ()}))


@pytest.mark.parametrize("duration", [3, 17])
def test_duration_limits(duration):
    with pytest.raises(ValueError):
        MetasoH3Profile(duration=duration, resolution="768P", aspect_ratio="16:9",
                       context_ir=True, cost_upper_bound_microunits=2_000_000)


def test_environment_lookup_does_not_fallback(monkeypatch):
    monkeypatch.delenv("METASO_API_KEY", raising=False)
    monkeypatch.setenv("MINIMAX_H3_API_KEY", "unrelated")
    assert metaso_environment_credential() == ""


def test_query_identity_and_failed_status_take_precedence_over_url():
    transport = _FakeTransport(submit_response=_submit_response(), query_response=
        MiniMaxH3TransportResponse(200, {}, json.dumps({"task": {"id": "task-h3-1",
            "status": "failed", "content": {"url": "https://cdn.example.org/v.mp4"}}}).encode()))
    provider, request, preview, paid, auth, permit, *_ = setup(transport=transport)
    provider.submit(request, preview, paid, auth, permit)
    receipt = _paid_submit_receipt(request, paid)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=receipt)
    assert provider.get_status(submission, receipt).state.value == "failed"


def test_real_committer_and_standard_loading(tmp_path, monkeypatch):
    from production_remote_generation_factory import prepare_remote_generation
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.project import load_production_project
    # The shared fixture defaults to frame-exact timing. H3 is a nominal
    # duration Provider, so author this test's neutral requirement accordingly.
    import production_remote_generation_factory as factory
    output_need = factory.OutputNeed
    monkeypatch.setattr(factory, "OutputNeed", lambda **kwargs: output_need(
        **{**kwargs, "timing_mode": "content_driven"}))
    provider, request, *_ = setup(audio=False)
    # Exercise the real production execution binding and durable paid owner.
    raw = {"a-scene": b"original scene"}
    provider._reference_resolver = lambda b: raw[b.asset_id]
    original = request.activation_scope.request
    original = _request(**{**original.model_dump(exclude={"request_input_hash"}),
                          "image_bindings": original.image_bindings[:1]})
    prepared = prepare_remote_generation(root=tmp_path, provider=provider, request=original,
        compiler_id="metaso-h3-video-compiler", compiler_version="1", input_bytes=raw)
    resolved = prepared.resolved_request
    preview = provider.preview(resolved)
    paid = PaidProviderCallPreview.create(attempt_id="attempt-metaso-1", operation="video_generation",
        provider_kind="metaso_h3", model_id="MiniMax-H3", request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered", currency="CNY", estimated_cost_upper_bound_microunits=2_000_000,
        destination=preview.destination, method="POST", egress_items=provider.egress_items(resolved),
        retention_mode="provider_standard", provider_policy_snapshot_id="metaso-h3-test",
        secret_reference=SecretReference(kind="secret_store", reference_id="METASO_API_KEY"))
    auth = _paid_authorization(paid)
    committer = ProductionStateCommitter(tmp_path, paid_provider_authorizer=lambda _: auth,
                                        paid_provider_clock=_fixed_now)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=paid.attempt_id, request=resolved, execution_binding=prepared.execution_binding)
    submission = service.submit_once(attempt_id=paid.attempt_id, paid_preview=paid,
                                    reservation_id="metaso-reservation-1")
    assert submission.resolved_generation_hash == resolved.resolved_generation_hash
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest.attempts[-1].video_generation_state is not None


def test_authorization_expiring_during_permit_consume_is_zero_post():
    provider, request, preview, paid, auth, permit, transport, _ = setup()
    times = iter((_fixed_now(), _fixed_now(), auth.expires_at))
    provider._now = lambda: next(times)
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, paid, auth, permit)
    assert not transport.calls


def test_reference_video_uses_official_content_role_and_rejects_geometry():
    provider, request, _, _, _, _, _, raw = setup(audio=False)
    raw['motion-video'] = b'exact motion reference'
    video = VideoMediaReferenceBinding(kind='video', role='reference_video',
        asset_id='motion-video', asset_sha256=hashlib.sha256(raw['motion-video']).hexdigest(),
        mime_type='video/mp4', size_bytes=len(raw['motion-video']), duration_millis=4000,
        width=1280, height=720, fps=24)
    original = request.activation_scope.request
    resolved = provider.resolve(_request(**{**original.model_dump(exclude={'request_input_hash'}),
                                            'media_bindings': (video,)}))
    content = json.loads(provider.native_payload(resolved))['content']
    assert content[-1]['type'] == 'video_url'
    assert content[-1]['role'] == 'reference_video'
    with pytest.raises(AiVideoError):
        provider.resolve(original.model_copy(update={'media_bindings': (
            video.model_copy(update={'width': 12800}),)}))


def test_metaso_status_and_fetch_bind_task_and_never_forward_bearer():
    from io import BytesIO
    from test_production_minimax_h3 import _download_response
    body = b'\x00\x00\x00\x18ftypisom' + b'\x00' * 32
    transport = _FakeTransport(query_response=MiniMaxH3TransportResponse(200, {},
        json.dumps({'task': {'id': 'task-h3-1', 'model': 'MiniMax-H3',
            'status': 'succeeded', 'content': {'url': 'https://cdn.example.org/out.mp4?token=short'}}}).encode()),
        download_response=_download_response(body=body))
    provider, request, _, paid, *_ = setup(transport=transport)
    receipt = _paid_submit_receipt(request, paid)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=receipt)
    observation = provider.get_status(submission, receipt)
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == body
    assert fetched.artifact_sha256 == hashlib.sha256(body).hexdigest()
    assert transport.calls[0].url == METASO_BASE_URL + '/v2/query/video_generation/task-h3-1'
    assert dict(transport.stream_calls[0].headers) == {'accept':'video/mp4'}
    assert 'short' not in repr(fetched) + repr(transport.stream_calls[0])
    transport.query_response = MiniMaxH3TransportResponse(200, {},
        b'{"task":{"id":"wrong-task","status":"succeeded"}}')
    with pytest.raises(AiVideoError): provider.get_status(submission, receipt)


def test_real_transport_handles_case_insensitive_http_download_headers(monkeypatch):
    from contextlib import contextmanager
    from io import BytesIO
    from types import SimpleNamespace
    import httpx
    import ai_video.production.metaso_h3 as module
    body = b'\x00\x00\x00\x18ftypisom' + b'\x00' * 32
    @contextmanager
    def public_stream(url, *, timeout_seconds):
        assert url == 'https://cdn.example.org/out.mp4'
        yield SimpleNamespace(status_code=200,
            headers={'Content-Type':'video/mp4;charset=UTF-8','Content-Length':str(len(body))},
            iter_bytes=lambda:iter((body,)))
    monkeypatch.setattr(module,'stream_public_video',public_stream)
    with httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
        'task':{'id':'task-h3-1','status':'succeeded','content':{'url':'https://cdn.example.org/out.mp4'}}}))) as client:
        transport = module.HttpxMetasoH3Transport(client=client)
        provider, request, _, paid, *_ = setup(transport=transport)
        receipt = _paid_submit_receipt(request,paid)
        submission = VideoSubmission.from_paid_submit_receipt(resolved=request,receipt=receipt)
        observed = provider.get_status(submission,receipt)
        sink = BytesIO()
        result = provider.fetch(submission,receipt,observed,sink)
    assert sink.getvalue()==body
    assert result.size_bytes==len(body)


def _frame_setup(*, last=False, aspect_ratio="adaptive"):
    from io import BytesIO
    from PIL import Image

    raw, images = {}, []
    for role in ("first_frame", "last_frame") if last else ("first_frame",):
        sink = BytesIO()
        Image.new("RGB", (512, 288), "navy" if role == "first_frame" else "green").save(sink, format="PNG")
        raw[role] = sink.getvalue()
        images.append(VideoImageReferenceBinding(role=role, asset_id=role,
            asset_sha256=hashlib.sha256(raw[role]).hexdigest(), mime_type="image/png",
            width=512, height=288, size_bytes=len(raw[role])))

    def forbidden(*args, **kwargs):
        pytest.fail("offline frame preparation must not read credentials or contact a Provider")

    from types import SimpleNamespace
    profile = MetasoH3Profile(duration=4, resolution="768P", aspect_ratio=aspect_ratio,
        context_ir=True, cost_upper_bound_microunits=1)
    provider = MetasoH3VideoProvider(profile=profile,
        transport=SimpleNamespace(request=forbidden, stream=forbidden), credential=forbidden,
        reference_resolver=lambda binding: raw[binding.asset_id])
    request = _request(provider_name="metaso_h3", provider_kind="metaso_h3",
        provider_profile=profile.pointer(), mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=tuple(images), output_requirement=profile.output())
    return provider, request, raw


def test_frame_capability_and_ref2va_serialization_are_deterministic():
    from ai_video.production.video import VideoProviderCapabilities
    provider, _, _ = _frame_setup()
    capabilities = provider.capabilities()
    assert capabilities == provider.capabilities()
    assert VideoProviderCapabilities.model_validate_json(capabilities.model_dump_json()) == capabilities
    ref, frame = capabilities.variants
    from ai_video.production._video_capability_fingerprint import capability_variant_fingerprint
    assert capability_variant_fingerprint(ref) == "fcfca8c570a0244792f956f9cdfb25c370d81c5ea454a7f220962ca57d78c24f"
    assert ref.capability_id == "metaso-h3-ref2va-v1"
    assert frame.capability_id == "metaso-h3-fl2va-v1"
    assert frame.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert frame.allowed_image_roles == ("first_frame", "last_frame")
    assert frame.required_first_frame and frame.max_reference_count == 0
    assert not frame.media_capabilities and not frame.seed_supported
    fixed, _, _ = _frame_setup(aspect_ratio="16:9")
    assert fixed.capabilities().variants == (ref,)
    assert provider._profile.pointer().profile_version == ref.profile_version


@pytest.mark.parametrize("last", [False, True])
def test_frame_native_exact_bytes_roles_order_and_pre_submit(last):
    import base64
    provider, request, raw = _frame_setup(last=last)
    resolved = provider.resolve(request)
    assert resolved.capability_id == "metaso-h3-fl2va-v1"
    assert provider.preview(resolved).resolved_generation_hash == resolved.resolved_generation_hash
    body = json.loads(provider.native_payload(resolved))
    assert {k: v for k, v in body.items() if k != "content"} == {
        "model": "MiniMax-H3", "duration": 4, "resolution": "768P", "context_ir_enabled": True}
    assert body["content"][0] == {"type": "text", "text": request.prompt_text}
    expected = ["first_frame", "last_frame"] if last else ["first_frame"]
    assert [item["role"] for item in body["content"][1:]] == expected
    for item in body["content"][1:]:
        assert item["type"] == "image_url"
        assert base64.b64decode(item["image_url"]["url"].split(",", 1)[1]) == raw[item["role"]]


@pytest.mark.parametrize("roles", [(), ("last_frame",), ("reference",),
    ("first_frame", "reference"), ("first_frame", "first_frame"),
    ("first_frame", "last_frame", "last_frame")])
def test_frame_invalid_roles_block(roles):
    provider, request, _ = _frame_setup()
    image = request.image_bindings[0]
    bindings = tuple(image.model_copy(update={"role": role, "asset_id": f"frame-{i}"})
        for i, role in enumerate(roles))
    with pytest.raises((AiVideoError, ValueError)):
        provider.resolve(_request(**{**request.model_dump(exclude={"request_input_hash"}),
            "image_bindings": bindings}))


@pytest.mark.parametrize("updates", [
    {"width": 255}, {"height": 255}, {"width": 5761}, {"height": 5761},
    {"width": 1000, "height": 256}, {"width": 256, "height": 1000},
    {"mime_type": "image/gif"}, {"size_bytes": None}, {"size_bytes": 30 * 1024 * 1024 + 1},
])
def test_frame_invalid_metadata_blocks(updates):
    provider, request, _ = _frame_setup()
    with pytest.raises((AiVideoError, ValueError)):
        provider.resolve(_request(**{**request.model_dump(exclude={"request_input_hash"}),
            "image_bindings": (request.image_bindings[0].model_copy(update=updates),)}))


@pytest.mark.parametrize("role", ["first_frame", "last_frame"])
@pytest.mark.parametrize("defect", ["hash", "size", "encoded_geometry", "encoded_mime", "invalid_image"])
def test_frame_exact_bytes_and_encoded_metadata_block_before_effect(role, defect):
    provider, request, raw = _frame_setup(last=True)
    updates = {}
    if defect == "hash":
        original = raw[role]
        raw[role] = bytes([original[0] ^ 1]) + original[1:]
    elif defect == "size":
        raw[role] += b"extra"
    elif defect == "encoded_geometry":
        updates = {"width": 640}
    elif defect == "encoded_mime":
        updates = {"mime_type": "image/jpeg"}
    else:
        raw[role] = b"not an image"
        updates = {"size_bytes": len(raw[role]), "asset_sha256": hashlib.sha256(raw[role]).hexdigest()}
    request = _request(**{**request.model_dump(exclude={"request_input_hash"}),
        "image_bindings": tuple(b.model_copy(update=updates) if b.role == role else b
            for b in request.image_bindings)})
    with pytest.raises(AiVideoError):
        provider.native_payload(provider.resolve(request))


def test_frame_ratio_profile_and_media_cannot_be_silently_dropped():
    provider, request, _ = _frame_setup(aspect_ratio="16:9")
    with pytest.raises(AiVideoError):
        provider.resolve(request)
    provider, request, _ = _frame_setup()
    audio = VideoMediaReferenceBinding(kind="audio", role="reference_audio", asset_id="audio",
        asset_sha256="a" * 64, mime_type="audio/wav", size_bytes=4, duration_millis=4000)
    with pytest.raises((AiVideoError, ValueError)):
        provider.resolve(_request(**{**request.model_dump(exclude={"request_input_hash"}),
            "media_bindings": (audio,)}))


def test_optional_last_has_independently_legal_geometry():
    from io import BytesIO
    from PIL import Image
    provider, request, raw = _frame_setup(last=True)
    sink = BytesIO()
    Image.new("RGB", (640, 640)).save(sink, format="PNG")
    raw["last_frame"] = sink.getvalue()
    last = request.image_bindings[1].model_copy(update={"width": 640, "height": 640,
        "size_bytes": len(raw["last_frame"]), "asset_sha256": hashlib.sha256(raw["last_frame"]).hexdigest()})
    request = _request(**{**request.model_dump(exclude={"request_input_hash"}),
        "image_bindings": (request.image_bindings[0], last)})
    assert json.loads(provider.native_payload(provider.resolve(request)))["content"][-1]["role"] == "last_frame"


@pytest.mark.parametrize("image_format,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_frame_supported_encoded_image_formats(image_format, mime):
    from io import BytesIO
    from PIL import Image
    provider, request, raw = _frame_setup()
    sink = BytesIO()
    Image.new("RGB", (512, 288)).save(sink, format=image_format)
    raw["first_frame"] = sink.getvalue()
    binding = request.image_bindings[0].model_copy(update={"mime_type": mime,
        "asset_sha256": hashlib.sha256(raw["first_frame"]).hexdigest(), "size_bytes": len(raw["first_frame"])})
    request = _request(**{**request.model_dump(exclude={"request_input_hash"}), "image_bindings": (binding,)})
    uri = json.loads(provider.native_payload(provider.resolve(request)))["content"][1]["image_url"]["url"]
    assert uri.startswith(f"data:{mime};base64,")


def _metaso_frame_router_fixture(monkeypatch, *, hard_cut):
    import test_production_shot_router as r
    from ai_video.production.shot_router import AdapterCompilerContract
    from ai_video.production.video_requirement import OutputNeed, AudioNeed, OutputGeometryPolicy
    from tests.test_production_video_intent_validation import _complete_intent, _compatible_fl2va
    from ai_video.production.video_requirement import ConditioningLane
    provider, request, raw = _frame_setup(last=True)
    variant = next(v for v in provider.capabilities().variants if v.mode is VideoGenerationMode.IMAGE_TO_VIDEO)
    compiler = AdapterCompilerContract.create(compiler_id="metaso-h3-video-compiler", compiler_version="1")
    common = dict(policy=r._policy(remote_authorized=True, budget_authorized=True),
        provider_profile=provider._profile.pointer(), capabilities=provider.capabilities(),
        selected_capability_id=variant.capability_id, output_requirement=provider._profile.output(),
        compiler_contract=compiler)

    def nominal_projection(projection):
        intent = _complete_intent().model_copy(update={
            "pacing": r.GenerationIntent().pacing.model_copy(update={"shot_duration_seconds": 4}),
        })
        return r._reseal_projection(projection,
            contract_version="provider-neutral-video-requirement/4", generation_intent=intent,
            conditioning_compatibility=_compatible_fl2va().model_copy(update={
                "lane": ConditioningLane.I2VA, "first_anchor_id": projection.requirement.asset_evidence[0].asset_id,
                "last_anchor_id": None, "available_duration_seconds": 4,
            }),
            output_need=OutputNeed(timing_mode="content_driven", duration_seconds=4,
                geometry_policy=OutputGeometryPolicy.ADAPTIVE, aspect_ratio="adaptive",
                fps=24, container_mime="video/mp4"), audio_need=AudioNeed.REQUIRED)

    def metaso_source_route(context, **kwargs):
        result = r.VideoGenerationResolver()._bind_requirement(context=context,
            projection=nominal_projection(r._first_frame_projection(context)),
            lifecycle=kwargs["lifecycle"], **common)
        assert result.provider_bound_request is not None, result.decision
        return result.provider_bound_request

    # The existing terminal/C2 fixtures now derive their source from the same
    # real METASO capability through Router; no production source is fabricated.
    monkeypatch.setattr(r, "_route_first_frame", metaso_source_route)
    original_asset = r._asset

    def frame_asset(role, suffix, sha256, **kwargs):
        if role in {"first_frame", "continuity_terminal"}:
            image = request.image_bindings[1] if suffix == "derived-new-camera" else request.image_bindings[0]
            # Separate terminal and derived keyframe identities, with exact offline image bytes.
            kwargs.update(width=image.width, height=image.height, size_bytes=image.size_bytes)
            sha256 = image.asset_sha256
            asset = original_asset(role, suffix, sha256, **kwargs)
            raw[asset.asset_id] = raw[image.role]
            return asset
        return original_asset(role, suffix, sha256, **kwargs)

    monkeypatch.setattr(r, "_asset", frame_asset)
    if hard_cut:
        fixture = r._hard_cut_full_fixture()
    else:
        source, previous, context, lifecycle, _ = r._sequence_fixture()
        fixture = dict(context=context, lifecycle=lifecycle,
            projection=r._exact_terminal_projection(context))
    fixture["projection"] = nominal_projection(fixture["projection"])
    fixture.update(common)
    route = r._selected_route_identity(provider_name="metaso_h3", variant=variant,
        provider_profile=provider._profile.pointer(), compiler_contract=compiler)
    if hard_cut:
        sequence = fixture["continuity_routing"]
        transition = r._causal_policy(sequence.transition_policy, fixture["projection"],
            destination_execution_stack_hash=r._execution_stack_identity(route).execution_stack_hash)
        fixture["continuity_routing"] = r._continuity_routing(transition=transition,
            previous_bound=sequence.previous_provider_bound_request, previous_shot=sequence.previous_shot,
            destination_route=route)
    else:
        transition = r._causal_policy(r._transition_policy(source_context=source,
            target_context=context, lifecycle=lifecycle, boundary=r.BoundaryKind.WITHIN_CONTINUOUS_TAKE,
            obligation=r.ContinuityObligation.FULL_CONTINUITY,
            source_route=r._bound_route_identity(previous), destination_route=route), fixture["projection"])
        fixture["continuity_routing"] = r._continuity_routing(transition=transition,
            previous_bound=previous, previous_shot=source.activated_shot, destination_route=route)
    return provider, fixture


@pytest.mark.parametrize("hard_cut", [False, True])
def test_metaso_exact_terminal_and_hard_cut_c2_reach_native_pre_submit(monkeypatch, hard_cut):
    from ai_video.production.shot_router import VideoGenerationResolver, RoutingOutcome
    from ai_video.production.video_compiler import require_compiled_provider_request
    provider, fixture = _metaso_frame_router_fixture(monkeypatch, hard_cut=hard_cut)
    result = VideoGenerationResolver()._bind_requirement(**fixture)
    assert result.decision.outcome is RoutingOutcome.SELECTED, result.decision
    assert result.decision.required_binding_roles == ("first_frame",)
    bound = result.provider_bound_request
    expected = fixture["context"].shot_keyframe if hard_cut else fixture["context"].upstream_terminal
    assert bound.input_assets == (expected,)
    sequence = fixture["continuity_routing"]
    assert sequence.source_route == sequence.destination_route
    assert sequence.source_execution_stack == sequence.destination_execution_stack
    compiled = require_compiled_provider_request(provider.compile_request(bound, fixture["projection"].requirement))
    assert compiled.request.image_bindings[0].asset_id == expected.asset_id
    resolved = provider.resolve(compiled.request)
    assert resolved.capability_id == "metaso-h3-fl2va-v1"
    assert provider.preview(resolved).resolved_generation_hash == resolved.resolved_generation_hash
    assert json.loads(provider.native_payload(resolved))["content"][1]["role"] == "first_frame"
    if hard_cut:
        assert compiled.request.hard_cut_keyframe_binding == fixture["lifecycle"].hard_cut_keyframe_binding
        assert bound.input_assets[0] != fixture["context"].upstream_terminal
    else:
        assert compiled.request.continuity_binding == fixture["lifecycle"].continuity_binding


def test_added_frame_variant_does_not_change_explicit_soft_full_block():
    import test_production_shot_router as r
    from ai_video.production.shot_router import VideoGenerationResolver, RouterReasonCode
    provider, _, _ = _frame_setup()
    fixture = r._metaso_continuity_fixture()
    fixture["capabilities"] = provider.capabilities()
    result = VideoGenerationResolver()._bind_requirement(**fixture)
    assert RouterReasonCode.CONTINUITY_FRAME_CONDITIONING_REQUIRED in result.decision.reason_codes
    assert result.provider_bound_request is None


def test_metaso_first_last_requirement_compiles_through_router(monkeypatch):
    import test_production_shot_router as r
    from ai_video.production.video_requirement import (
        AssetEvidence, CapabilityNeed, ConditioningLane, GenerationMode, SemanticReferenceRole,
        ContinuityMode,
    )
    from ai_video.production.video_compiler import require_compiled_provider_request
    from tests.test_production_video_intent_validation import _compatible_fl2va
    provider, fixture = _metaso_frame_router_fixture(monkeypatch, hard_cut=True)
    _, request, _ = _frame_setup(last=True)
    last = request.image_bindings[1]
    endpoint = r._asset("last_frame", "endpoint", last.asset_sha256,
        size_bytes=last.size_bytes, width=last.width, height=last.height).model_copy(update={"asset_id": last.asset_id})
    context = fixture["context"].model_copy(update={"continuity_mode": r.ContinuityMode.NONE,
        "upstream_terminal": None, "last_frame": endpoint})
    first = context.shot_keyframe
    fixture["projection"] = r._reseal_projection(fixture["projection"],
        generation_mode=GenerationMode.FIRST_LAST_FRAME_VIDEO, continuity_mode=ContinuityMode.NONE,
        semantic_reference_roles=(SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.LAST_FRAME),
        asset_evidence=tuple(AssetEvidence(role=role, asset_id=a.asset_id, asset_sha256=a.asset_sha256,
            mime_type=a.mime_type, size_bytes=a.size_bytes, width=a.width, height=a.height)
            for role, a in ((SemanticReferenceRole.FIRST_FRAME, first), (SemanticReferenceRole.LAST_FRAME, endpoint))),
        capability_need=CapabilityNeed(needs_first_frame=True, needs_last_frame=True),
        conditioning_compatibility=_compatible_fl2va().model_copy(update={
            "lane": ConditioningLane.FL2VA, "first_anchor_id": first.asset_id,
            "last_anchor_id": endpoint.asset_id, "available_duration_seconds": 4}))
    fixture["context"] = context
    fixture["lifecycle"] = fixture["lifecycle"].model_copy(update={
        "hard_cut_keyframe_binding": None,
        "input_artifact_ids": (context.target_shot_id, first.asset_id, endpoint.asset_id)})
    del fixture["continuity_routing"]
    bound = r.VideoGenerationResolver()._bind_requirement(**fixture).provider_bound_request
    assert bound is not None
    compiled = require_compiled_provider_request(provider.compile_request(bound, fixture["projection"].requirement))
    assert tuple(b.role for b in compiled.request.image_bindings) == ("first_frame", "last_frame")
    body = json.loads(provider.native_payload(provider.resolve(compiled.request)))
    assert [item["role"] for item in body["content"][1:]] == ["first_frame", "last_frame"]


def test_typed_hash_sequence_prompt_remains_explicitly_unsupported(monkeypatch):
    import test_production_shot_router as r
    from ai_video.planning.sequence_continuity import causal_state_column_hash
    from ai_video.production.video_requirement import TypedStateReference
    from ai_video.production.video_compiler import ProviderRequirementUnsupported, ProviderRequirementUnsupportedReason
    provider, fixture = _metaso_frame_router_fixture(monkeypatch, hard_cut=True)
    sequence = fixture["continuity_routing"]
    state_hash = causal_state_column_hash(sequence.transition_policy.causal_state_changes, endpoint="target_open")
    intent = fixture["projection"].requirement.generation_intent.model_copy(update={
        "open_state": TypedStateReference(kind="typed_hash", state_hash=state_hash),
        "close_state": TypedStateReference(kind="typed_hash", state_hash=state_hash)})
    fixture["projection"] = r._reseal_projection(fixture["projection"], generation_intent=intent)
    fixture["continuity_routing"] = r._continuity_routing(
        transition=r._causal_policy(sequence.transition_policy, fixture["projection"]),
        previous_bound=sequence.previous_provider_bound_request, previous_shot=sequence.previous_shot,
        destination_route=sequence.destination_route)
    bound = r.VideoGenerationResolver()._bind_requirement(**fixture).provider_bound_request
    assert bound is not None
    result = provider.compile_request(bound, fixture["projection"].requirement)
    assert isinstance(result, ProviderRequirementUnsupported)
    assert result.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert set(result.unsupported_field_paths) == {"generation_intent.open_state", "generation_intent.close_state"}
