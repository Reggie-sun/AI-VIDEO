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
