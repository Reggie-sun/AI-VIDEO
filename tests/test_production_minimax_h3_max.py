"""Official MiniMax H3 Max adapter contracts; all transport is in-memory."""

import base64
import hashlib
import json
from io import BytesIO

import pytest
from PIL import Image

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.minimax_h3 import MiniMaxH3TransportResponse
from ai_video.production.minimax_h3_max import (
    MINIMAX_H3_MAX_MODEL_ID,
    MINIMAX_H3_MAX_ORIGIN,
    MiniMaxH3MaxProfile,
    MiniMaxH3MaxVideoProvider,
)
from ai_video.production.paid_provider import PaidProviderCallPreview, SecretReference
from ai_video.production.video import (
    VideoGenerationMode,
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
    VideoSubmission,
    build_video_paid_permit_binding,
)
from test_production_minimax_h3 import (
    _FakeTransport,
    _fixed_now,
    _paid_authorization,
    _paid_submit_receipt,
    _real_permit,
    _request,
    _download_response,
    _submit_response,
)


def _setup(*, currency="CNY", resolution="768P", aspect_ratio="16:9",
           duration=5, transport=None, api_region=None):
    raw = {"s01-whitebox": b"exact verified reference image bytes"}
    image = VideoImageReferenceBinding(
        role="reference",
        asset_id="s01-whitebox",
        asset_sha256=hashlib.sha256(raw["s01-whitebox"]).hexdigest(),
        mime_type="image/png",
        width=512,
        height=288,
        size_bytes=len(raw["s01-whitebox"]),
    )
    profile = MiniMaxH3MaxProfile(
        duration=duration,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        currency=currency,
        cost_upper_bound_microunits=2_000_000,
        **({"api_region": api_region} if api_region is not None else {}),
    )
    transport = transport or _FakeTransport(submit_response=_submit_response())
    provider = MiniMaxH3MaxVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "FAKE-MINIMAX-TEST-ONLY",
        reference_resolver=lambda binding: raw[binding.asset_id],
        now=_fixed_now,
    )
    request = _request(
        provider_name="minimax_h3_max",
        provider_kind="minimax_h3_max",
        model_id=MINIMAX_H3_MAX_MODEL_ID,
        provider_profile=profile.pointer(),
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        prompt_text="Lin Yan raises her left hand toward the train window.",
        image_bindings=(image,),
        output_requirement=profile.output(),
    )
    resolved = provider.resolve(request)
    return provider, resolved, profile, transport, raw


def _paid(provider, resolved):
    video_preview = provider.preview(resolved)
    paid_preview = PaidProviderCallPreview.create(
        attempt_id="attempt-h3-max-1",
        operation="video_generation",
        provider_kind=resolved.provider_kind,
        model_id=resolved.model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered",
        currency=video_preview.currency,
        estimated_cost_upper_bound_microunits=video_preview.estimated_cost_upper_bound_microunits,
        destination=video_preview.destination,
        method="POST",
        egress_items=provider.egress_items(resolved),
        retention_mode="provider_standard",
        provider_policy_snapshot_id="minimax-h3-max-test",
        secret_reference=SecretReference(kind="secret_store", reference_id=provider.secret_reference_id),
    )
    authorization = _paid_authorization(paid_preview)
    permit = _real_permit(build_video_paid_permit_binding(
        resolved, video_preview, paid_preview, authorization))
    return video_preview, paid_preview, authorization, permit


def test_official_h3_max_exact_reference_payload_and_paid_submit():
    provider, resolved, profile, transport, raw = _setup()
    video_preview, paid_preview, authorization, permit = _paid(provider, resolved)

    assert video_preview.destination == MINIMAX_H3_MAX_ORIGIN
    assert video_preview.currency == "CNY"
    assert profile.pointer().profile_sha256 == resolved.provider_profile.profile_sha256
    payload = json.loads(provider.native_payload(resolved))
    assert {key: value for key, value in payload.items() if key != "content"} == {
        "model": "MiniMax-H3-Max",
        "duration": 5,
        "resolution": "768P",
        "ratio": "16:9",
        "extra": {"prompt_expansion_mode": "balanced"},
    }
    assert payload["content"][0] == {
        "type": "text", "text": resolved.prompt_text,
    }
    assert payload["content"][1]["type"] == "image_url"
    assert payload["content"][1]["role"] == "reference_image"
    data_uri = payload["content"][1]["image_url"]["url"]
    assert base64.b64decode(data_uri.split(",", 1)[1]) == raw["s01-whitebox"]

    result = provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert result.external_effect_id == "task-h3-1"
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call.url == "https://api.minimax.io/v2/video_generation"
    assert call.headers["authorization"] == "Bearer FAKE-MINIMAX-TEST-ONLY"
    assert json.loads(call.body) == payload
    assert "FAKE-MINIMAX" not in repr(call) + repr(result) + call.body.decode()
    with pytest.raises(AiVideoError):
        provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert len(transport.calls) == 1


def test_cn_region_is_explicit_sealed_and_uses_its_own_credential_reference():
    global_provider, global_request, global_profile, _, _ = _setup()
    provider, request, profile, transport, _ = _setup(api_region="cn")
    legacy = global_profile.model_dump(mode="json")
    assert "api_region" not in legacy
    from ai_video.production.hashing import canonical_sha256
    assert global_profile.pointer().profile_sha256 == canonical_sha256(legacy)
    published = MiniMaxH3MaxProfile(duration=5, resolution="768P", aspect_ratio="9:16",
        currency="CNY", cost_upper_bound_microunits=50_000_000)
    assert published.pointer().profile_sha256 == "f2975240788894b02b1e58bba222d09a95e57f91806b15378b82a1dde79443a8"
    assert profile.pointer().profile_sha256 != global_profile.pointer().profile_sha256
    assert profile.model_dump(mode="json")["api_region"] == "cn"
    assert provider.native_payload(request) == global_provider.native_payload(global_request)
    assert global_provider.origin == "https://api.minimax.io"
    assert provider.origin == provider.base_url == "https://api.minimax.cn"
    assert provider.secret_reference_id == "MINIMAX_H3_CN_API_KEY"
    preview, paid, authorization, permit = _paid(provider, request)
    wrong = paid.model_dump(mode="python", exclude={"preview_fingerprint"})
    wrong["secret_reference"] = SecretReference(kind="secret_store", reference_id="MINIMAX_H3_API_KEY")
    wrong = PaidProviderCallPreview.create(**wrong)
    wrong_authorization = _paid_authorization(wrong)
    wrong_permit = _real_permit(build_video_paid_permit_binding(
        request, preview, wrong, wrong_authorization))
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, wrong, wrong_authorization, wrong_permit)
    assert len(transport.calls) == 0
    provider.submit(request, preview, paid, authorization, permit)
    assert transport.calls[0].url == "https://api.minimax.cn/v2/video_generation"
    assert len(transport.calls) == 1
    with pytest.raises(ValueError):
        MiniMaxH3MaxProfile.model_validate({**legacy, "api_region": "https://untrusted.invalid"})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"duration": 4},
        {"duration": 16},
        {"resolution": "2K"},
    ],
)
def test_profile_rejects_unsupported_h3_max_ranges(kwargs):
    values = {
        "duration": 5,
        "resolution": "768P",
        "aspect_ratio": "16:9",
        "currency": "CNY",
        "cost_upper_bound_microunits": 1,
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        MiniMaxH3MaxProfile(**values)


def test_provider_constructor_revalidates_profile_and_rejects_metaso_profile():
    from ai_video.production.metaso_h3 import MetasoH3Profile

    metaso = MetasoH3Profile(
        duration=5,
        resolution="768P",
        aspect_ratio="16:9",
        context_ir=True,
        cost_upper_bound_microunits=1,
    )
    with pytest.raises(TypeError):
        MiniMaxH3MaxVideoProvider(
            profile=metaso,
            transport=object(),
            credential=lambda: "unused",
            reference_resolver=lambda _: b"unused",
        )

    forged = MiniMaxH3MaxProfile.model_construct(
        duration=4,
        resolution="2K",
        aspect_ratio="16:9",
        prompt_expansion_mode="balanced",
        currency="CNY",
        cost_upper_bound_microunits=1,
    )
    with pytest.raises(ValueError):
        MiniMaxH3MaxVideoProvider(
            profile=forged,
            transport=object(),
            credential=lambda: "unused",
            reference_resolver=lambda _: b"unused",
        )


def test_profile_currency_and_credential_supplier_are_explicit():
    provider, resolved, usd_profile, _, _ = _setup(currency="USD")
    assert provider.preview(resolved).currency == "USD"
    _, _, cny_profile, _, _ = _setup(currency="CNY")
    assert usd_profile.pointer().profile_sha256 != cny_profile.pointer().profile_sha256

    with pytest.raises(TypeError):
        MiniMaxH3MaxVideoProvider(
            profile=usd_profile,
            transport=object(),
            reference_resolver=lambda _: b"unused",
        )
    with pytest.raises(TypeError):
        MiniMaxH3MaxVideoProvider(
            profile=usd_profile,
            transport=object(),
            credential="raw-key-is-not-a-supplier",
            reference_resolver=lambda _: b"unused",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("destination", "https://metaso.cn"),
        ("currency", "USD"),
        ("model_id", "MiniMax-H3"),
        ("provider_kind", "metaso_h3"),
    ],
)
def test_paid_preview_identity_mismatch_is_zero_effect(field, value):
    provider, resolved, _, transport, _ = _setup()
    video_preview, paid_preview, _, _ = _paid(provider, resolved)
    changes = {field: value}
    mismatched = PaidProviderCallPreview.create(**{
        **paid_preview.model_dump(mode="python", exclude={"preview_fingerprint"}),
        **changes,
    })
    authorization = _paid_authorization(mismatched)

    with pytest.raises(AiVideoError):
        provider.submit(resolved, video_preview, mismatched, authorization, object())
    assert transport.calls == []


def test_reference_bytes_are_rehashed_before_paid_submit():
    provider, resolved, _, transport, raw = _setup()
    video_preview, paid_preview, authorization, permit = _paid(provider, resolved)
    raw["s01-whitebox"] = b"different bytes"

    with pytest.raises(AiVideoError) as exc:
        provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert exc.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.calls == []


def test_reference_mode_rejects_first_frame_role_and_total_media_over_15s():
    provider, resolved, profile, _, _ = _setup()
    request = resolved.activation_scope.request
    first_frame = request.image_bindings[0].model_copy(update={"role": "first_frame"})
    with pytest.raises(AiVideoError):
        provider.resolve(request.model_copy(update={"image_bindings": (first_frame,)}))

    videos = tuple(VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id=f"motion-{index}",
        asset_sha256=hashlib.sha256(f"video-{index}".encode()).hexdigest(),
        mime_type="video/mp4",
        size_bytes=7,
        duration_millis=6000,
        width=1280,
        height=720,
        fps=24,
    ) for index in range(3))
    too_long = _request(
        provider_name="minimax_h3_max",
        provider_kind="minimax_h3_max",
        model_id=MINIMAX_H3_MAX_MODEL_ID,
        provider_profile=profile.pointer(),
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        prompt_text="Reference mode.",
        image_bindings=request.image_bindings,
        media_bindings=videos,
        output_requirement=profile.output(),
    )
    with pytest.raises(AiVideoError):
        provider.resolve(too_long)


def test_reference_video_and_audio_are_bound_as_exact_official_content_items():
    provider, resolved, _, _, raw = _setup()
    raw["motion-reference"] = b"exact motion video bytes"
    raw["dialogue-reference"] = b"exact dialogue audio bytes"
    video = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="motion-reference",
        asset_sha256=hashlib.sha256(raw["motion-reference"]).hexdigest(),
        mime_type="video/mp4",
        size_bytes=len(raw["motion-reference"]),
        duration_millis=4000,
        width=1280,
        height=720,
        fps=24,
    )
    audio = VideoMediaReferenceBinding(
        kind="audio",
        role="reference_audio",
        asset_id="dialogue-reference",
        asset_sha256=hashlib.sha256(raw["dialogue-reference"]).hexdigest(),
        mime_type="audio/wav",
        size_bytes=len(raw["dialogue-reference"]),
        duration_millis=3000,
    )
    source_request = resolved.activation_scope.request
    request = _request(**{
        **source_request.model_dump(mode="python", exclude={"request_input_hash"}),
        "media_bindings": (video, audio),
    })
    resolved = provider.resolve(request)

    items = json.loads(provider.native_payload(resolved))["content"]

    assert [item["type"] for item in items] == [
        "text", "image_url", "video_url", "audio_url",
    ]
    assert [item["role"] for item in items[1:]] == [
        "reference_image", "reference_video", "reference_audio",
    ]
    for item, binding in zip(items[1:], (request.image_bindings[0], video, audio), strict=True):
        kind = item["type"][:-4]
        uri = item[f"{kind}_url"]["url"]
        assert base64.b64decode(uri.split(",", 1)[1]) == raw[binding.asset_id]


@pytest.mark.parametrize("api_region", ["international", "cn"])
def test_status_checks_optional_h3_max_model_and_output_echoes(api_region):
    transport = _FakeTransport(
        submit_response=_submit_response(),
        query_response=MiniMaxH3TransportResponse(
            200, {}, json.dumps({"task": {
                "id": "task-h3-1", "model": "MiniMax-H3", "status": "running",
            }}).encode(),
        ),
    )
    provider, resolved, _, _, _ = _setup(transport=transport, api_region=api_region)
    video_preview, paid_preview, authorization, permit = _paid(provider, resolved)
    provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=receipt)

    with pytest.raises(AiVideoError):
        provider.get_status(submission, receipt)
    assert transport.calls[-1].url == (
        provider.origin + "/v2/query/video_generation/task-h3-1"
    )
    transport.query_response = MiniMaxH3TransportResponse(
        200, {}, json.dumps({"task": {
            "id": "task-h3-1", "status": "running",
        }}).encode(),
    )
    observation = provider.get_status(submission, receipt)
    assert observation.state.value == "running"

    transport.query_response = MiniMaxH3TransportResponse(
        200, {}, json.dumps({"task": {
            "id": "task-h3-1", "model": "MiniMax-H3-Max", "status": "running",
            "duration": 4,
        }}).encode(),
    )
    with pytest.raises(AiVideoError):
        provider.get_status(submission, receipt)

    transport.query_response = MiniMaxH3TransportResponse(
        200, {}, json.dumps({"task": {
            "id": "task-h3-1", "model": "MiniMax-H3-Max", "status": "running",
            "duration": 5, "resolution": "768P", "ratio": "16:9",
        }}).encode(),
    )
    assert provider.get_status(submission, receipt).state.value == "running"


@pytest.mark.parametrize("api_region", ["international", "cn"])
def test_fetch_requeries_h3_max_identity_and_never_sends_bearer_to_result_host(api_region):
    from io import BytesIO

    signed_url = "https://cdn.example.org/out.mp4?token=short-lived"
    query = MiniMaxH3TransportResponse(
        200, {}, json.dumps({"task": {
            "id": "task-h3-1", "model": "MiniMax-H3-Max", "status": "succeeded",
            "content": {"url": signed_url},
        }}).encode(),
    )
    transport = _FakeTransport(
        submit_response=_submit_response(),
        query_response=query,
        download_response=_download_response(body=b"\x00\x00\x00\x18ftypisom" + b"\x00" * 32),
    )
    provider, resolved, _, _, _ = _setup(transport=transport, api_region=api_region)
    video_preview, paid_preview, authorization, permit = _paid(provider, resolved)
    provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=receipt)
    observation = provider.get_status(submission, receipt)
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)

    assert len(transport.calls) == 3
    assert all(call.url.startswith(provider.origin) for call in transport.calls)
    assert transport.stream_calls[0].url == signed_url
    assert dict(transport.stream_calls[0].headers) == {"accept": "video/mp4"}
    assert signed_url not in repr(fetched) + repr(transport.stream_calls[0])
    assert fetched.artifact_sha256 == hashlib.sha256(sink.getvalue()).hexdigest()


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, ErrorCode.VIDEO_PROVIDER_FAILED),
        (429, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN),
        (503, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN),
    ],
)
def test_submit_failure_boundary_known_client_error_vs_unknown(status, expected):
    transport = _FakeTransport(submit_response=_submit_response(
        status=status, body={"error": "safe fixture"}))
    provider, resolved, _, _, _ = _setup(transport=transport)
    video_preview, paid_preview, authorization, permit = _paid(provider, resolved)

    with pytest.raises(AiVideoError) as exc:
        provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert exc.value.code is expected
    with pytest.raises(AiVideoError):
        provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert len(transport.calls) == 1


def test_first_last_frame_mode_serializes_frame_roles_and_omits_ratio():
    raw = {}
    images = []
    for role, color in (("first_frame", "navy"), ("last_frame", "white")):
        sink = BytesIO()
        Image.new("RGB", (512, 288), color).save(sink, format="PNG")
        raw[role] = sink.getvalue()
        images.append(VideoImageReferenceBinding(
            role=role,
            asset_id=role,
            asset_sha256=hashlib.sha256(raw[role]).hexdigest(),
            mime_type="image/png",
            width=512,
            height=288,
            size_bytes=len(raw[role]),
        ))
    profile = MiniMaxH3MaxProfile(
        duration=5, resolution="768P", aspect_ratio="adaptive", currency="CNY",
        cost_upper_bound_microunits=1,
    )
    provider = MiniMaxH3MaxVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: pytest.fail("frame preflight must not read credentials"),
        reference_resolver=lambda binding: raw[binding.asset_id],
    )
    request = _request(
        provider_name="minimax_h3_max",
        provider_kind="minimax_h3_max",
        model_id=MINIMAX_H3_MAX_MODEL_ID,
        provider_profile=profile.pointer(),
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=tuple(images),
        output_requirement=profile.output(),
    )
    resolved = provider.resolve(request)
    payload = json.loads(provider.native_payload(resolved))
    assert "ratio" not in payload
    assert [item["role"] for item in payload["content"][1:]] == ["first_frame", "last_frame"]
    assert payload["extra"] == {"prompt_expansion_mode": "balanced"}


@pytest.mark.parametrize("api_region,origin", [
    ("international", "https://api.minimax.io"),
    ("cn", "https://api.minimax.cn"),
])
def test_canonical_video_generation_service_uses_paid_committer_path(tmp_path, monkeypatch, api_region, origin):
    from production_remote_generation_factory import prepare_remote_generation
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    import production_remote_generation_factory as factory

    output_need = factory.OutputNeed
    monkeypatch.setattr(factory, "OutputNeed", lambda **kwargs: output_need(
        **{**kwargs, "timing_mode": "content_driven"}))
    provider, resolved, _, transport, raw = _setup(api_region=api_region)
    source_request = resolved.activation_scope.request
    prepared = prepare_remote_generation(
        root=tmp_path,
        provider=provider,
        request=source_request,
        compiler_id="minimax-h3-max-video-compiler",
        compiler_version="1",
        input_bytes=raw,
    )
    resolved = prepared.resolved_request
    video_preview, paid_preview, authorization, _ = _paid(provider, resolved)
    assert video_preview.destination == origin
    committer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda _: authorization,
        paid_provider_clock=_fixed_now,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=paid_preview.attempt_id,
        request=resolved,
        execution_binding=prepared.execution_binding,
    )
    submission = service.submit_once(
        attempt_id=paid_preview.attempt_id,
        paid_preview=paid_preview,
        reservation_id="h3-max-reservation-1",
    )

    assert submission.resolved_generation_hash == resolved.resolved_generation_hash
    assert len(transport.calls) == 1
    assert transport.calls[0].url == origin + "/v2/video_generation"
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest.attempts[-1].video_generation_state is not None


def test_official_h3_max_compiles_preserved_source_with_its_registered_identity():
    from ai_video.production._shot_router_contracts import (
        AdapterCompilerContract,
        ProviderBoundVideoRequest,
    )
    from ai_video.production._video_capability_fingerprint import capability_variant_fingerprint
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from test_production_metaso_h3 import _metaso_preserved_source_case

    _, source_bound, requirement, source = _metaso_preserved_source_case()
    profile = MiniMaxH3MaxProfile(
        duration=source_bound.output_requirement.duration_seconds,
        resolution="768P",
        aspect_ratio="adaptive",
        currency="CNY",
        cost_upper_bound_microunits=1,
    )
    provider = MiniMaxH3MaxVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: pytest.fail("source compilation must not read credentials"),
        reference_resolver=lambda _: pytest.fail("source compilation must not read assets"),
    )
    capability = next(
        item for item in provider.capabilities().variants
        if item.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="minimax-h3-max-video-compiler",
        compiler_version="1",
    )
    values = {
        name: getattr(source_bound, name)
        for name in ProviderBoundVideoRequest.model_fields
        if name != "provider_bound_request_hash"
    }
    recipe = source_bound.generation_recipe.model_copy(update={
        "profile_sha256": profile.pointer().profile_sha256,
        "compiler_hash": compiler.compiler_hash,
    })
    values.update(
        provider_name="minimax_h3_max",
        provider_kind="minimax_h3_max",
        model_id=MINIMAX_H3_MAX_MODEL_ID,
        provider_profile=profile.pointer(),
        capability_id=capability.capability_id,
        capability_fingerprint=capability_variant_fingerprint(capability),
        execution_kind=capability.execution_kind,
        billing_kind=capability.billing_kind,
        output_requirement=profile.output(),
        compiler_contract=compiler,
        generation_recipe=recipe,
    )
    bound = ProviderBoundVideoRequest.create(**values)

    result = provider.compile_request(bound, requirement)

    assert isinstance(result, CompiledProviderVideoRequest)
    assert result.adapter_compiler_id == "minimax-h3-max-video-compiler"
    assert result.adapter_compiler_version == "1"
    assert result.provider_native_prompt == source
    assert result.request.prompt_text == source
    assert result.request.image_bindings[0].role == "first_frame"
