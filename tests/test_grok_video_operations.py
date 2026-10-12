"""Offline operation-shape tests for Grok's documented video endpoints."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.grok import (
    GrokVideoProvider,
    GrokTransportRequest,
    HttpxGrokTransport,
)
from ai_video.production.grok_profile import (
    GROK_VIDEO_MODEL_CLASSIC,
    GROK_VIDEO_MODEL_FULL,
    GROK_VIDEO_MODEL_LITE,
    GrokTimedKeyframe,
    grok_capabilities,
)
from ai_video.production.video import (
    VideoFlexibleOutputRequirement,
    VideoGenerationMode,
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
)
from ai_video.production.grok_video_request import grok_endpoint_for_mode
from test_production_grok import (
    FakeTransport,
    MP4,
    _profile,
    _binding,
    _request,
    _setup,
)


def _image(asset_id: str, role: str = "reference") -> tuple[VideoImageReferenceBinding, bytes]:
    raw = f"grok-image:{asset_id}".encode("ascii")
    return (
        VideoImageReferenceBinding(
            role=role,
            asset_id=asset_id,
            asset_sha256=hashlib.sha256(raw).hexdigest(),
            mime_type="image/png",
            size_bytes=len(raw),
            width=1280,
            height=720,
        ),
        raw,
    )


def _output(
    *,
    duration: int = 5,
    resolution: str = "720p",
    native_audio: bool = False,
    timing: str = "nominal_seconds",
    ratio: str = "adaptive",
) -> VideoFlexibleOutputRequirement:
    return VideoFlexibleOutputRequirement(
        timing_mode=timing,
        duration_seconds=duration if timing != "provider_selected" else None,
        dimension_mode="adaptive",
        width=None,
        height=None,
        resolution_label=resolution,
        ratio=ratio,
        fps=None,
        container="mp4",
        mime_type="video/mp4",
        native_audio=native_audio,
    )


def _media(*, duration_millis: int = 5_000, width: int = 1280, height: int = 720):
    return VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="source-video",
        asset_sha256=hashlib.sha256(MP4).hexdigest(),
        mime_type="video/mp4",
        duration_millis=duration_millis,
        size_bytes=len(MP4),
        width=width,
        height=height,
        fps=30,
    )


def _payload(transport) -> dict[str, object]:
    assert len(transport.calls) == 1
    return json.loads(transport.calls[0].body)


def _assert_resolve_rejected_before_egress(request, profile) -> None:
    transport = FakeTransport()
    credential_reads: list[bool] = []
    provider = GrokVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: credential_reads.append(True) or "token",
        image_resolver=lambda _binding: b"image",
        media_resolver=lambda _binding: MP4,
        subscription_guard=lambda _binding: None,
    )
    with pytest.raises(AiVideoError):
        provider.resolve(request)
    assert not credential_reads
    assert not transport.calls


def test_full_r2v_first_frame_alone_is_not_reference_conditioning():
    first, _ = _image("first", "first_frame")
    _assert_resolve_rejected_before_egress(_request(mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=(first,), input_artifact_ids=("shot", "first")), _profile())


@pytest.mark.parametrize("timed", [False, True])
def test_exact_image_can_occupy_multiple_native_frame_positions(timed):
    first, raw = _image("repeated", "reference" if timed else "first_frame")
    profile = _profile(keyframes=(GrokTimedKeyframe(asset_id=first.asset_id,
        asset_sha256=first.asset_sha256, timestamp_ticks=3), GrokTimedKeyframe(asset_id=first.asset_id,
        asset_sha256=first.asset_sha256, timestamp_ticks=6))) if timed else _profile()
    bindings = (first,) if timed else (first, first.model_copy(update={"role": "last_frame"}))
    request = _request(profile, mode=VideoGenerationMode.REFERENCE_TO_VIDEO if timed else VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=bindings, input_artifact_ids=("shot", first.asset_id))
    provider, transport, args, *_ = _setup(request=request, profile=profile, image_resolver=lambda _: raw)
    provider.submit(*args)
    payload = _payload(transport)
    if timed:
        assert len(payload["keyframes"]) == 2
        assert payload["keyframes"][0]["image"] == payload["keyframes"][1]["image"]
        assert "reference_images" not in payload
    else:
        assert payload["image"] == payload["last_frame"]


def test_repeated_frame_asset_with_conflicting_bytes_is_rejected():
    from ai_video.production.grok_video_request import grok_egress_inputs

    first, _ = _image("repeated", "first_frame")
    last = first.model_copy(update={"role": "last_frame", "asset_sha256": "0" * 64})
    request = _request(mode=VideoGenerationMode.IMAGE_TO_VIDEO, image_bindings=(first, last),
        input_artifact_ids=("shot", first.asset_id))
    provider = GrokVideoProvider(profile=_profile(), transport=lambda _: pytest.fail("no POST"),
        credential=lambda: pytest.fail("no credential lookup"))
    with pytest.raises(AiVideoError):
        grok_egress_inputs(provider.resolve(request))


def test_capability_inventory_covers_all_models_and_five_operation_modes():
    variants = grok_capabilities().variants
    assert {variant.model_id for variant in variants} == {
        GROK_VIDEO_MODEL_FULL,
        GROK_VIDEO_MODEL_CLASSIC,
        GROK_VIDEO_MODEL_LITE,
    }
    assert {variant.mode for variant in variants} == set(VideoGenerationMode)
    assert {
        mode: grok_endpoint_for_mode(mode)
        for mode in VideoGenerationMode
    } == {
        VideoGenerationMode.TEXT_TO_VIDEO: "generations",
        VideoGenerationMode.IMAGE_TO_VIDEO: "generations",
        VideoGenerationMode.REFERENCE_TO_VIDEO: "generations",
        VideoGenerationMode.VIDEO_EDIT: "edits",
        VideoGenerationMode.VIDEO_EXTEND: "extensions",
    }
    lite_modes = {item.mode for item in variants if item.model_id == GROK_VIDEO_MODEL_LITE}
    assert lite_modes == {
        VideoGenerationMode.TEXT_TO_VIDEO,
        VideoGenerationMode.IMAGE_TO_VIDEO,
    }


@pytest.mark.parametrize(
    ("model_id", "mode", "resolution"),
    [
        (GROK_VIDEO_MODEL_CLASSIC, VideoGenerationMode.TEXT_TO_VIDEO, "720p"),
        (GROK_VIDEO_MODEL_CLASSIC, VideoGenerationMode.IMAGE_TO_VIDEO, "720p"),
        (GROK_VIDEO_MODEL_LITE, VideoGenerationMode.TEXT_TO_VIDEO, "1080p"),
        (GROK_VIDEO_MODEL_LITE, VideoGenerationMode.IMAGE_TO_VIDEO, "1080p"),
    ],
)
def test_classic_and_lite_generate_documented_text_and_first_frame_payloads(
    model_id, mode, resolution
):
    pairs = [_image("first-frame", "first_frame")] if mode is VideoGenerationMode.IMAGE_TO_VIDEO else []
    request = _request(
        model_id=model_id,
        mode=mode,
        image_bindings=tuple(item[0] for item in pairs),
        input_artifact_ids=("shot", *(item[0].asset_id for item in pairs)),
        output_requirement=_output(resolution=resolution, ratio="adaptive"),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        image_resolver=lambda _binding: pairs[0][1],
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["model"] == model_id
    assert payload["prompt"] == request.prompt_text
    assert payload["resolution"] == resolution
    assert ("image" in payload) is (mode is VideoGenerationMode.IMAGE_TO_VIDEO)


def test_classic_reference_video_emits_seven_bound_reference_images():
    pairs = [_image(f"classic-reference-{index}") for index in range(7)]
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=tuple(item[0] for item in pairs),
        input_artifact_ids=("shot", *(item[0].asset_id for item in pairs)),
        output_requirement=_output(duration=10, resolution="720p", ratio="5:2"),
    )
    data = {binding.asset_id: raw for binding, raw in pairs}
    provider, transport, args, *_ = _setup(
        request=request,
        image_resolver=lambda binding: data[binding.asset_id],
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["model"] == GROK_VIDEO_MODEL_CLASSIC
    assert payload["duration"] == 10
    assert payload["aspect_ratio"] == "5:2"
    assert len(payload["reference_images"]) == 7


def test_full_first_and_last_frame_image_to_video_uses_both_exact_images():
    pairs = [
        _image("first-frame", "first_frame"),
        _image("last-frame", "last_frame"),
    ]
    data = {binding.asset_id: raw for binding, raw in pairs}
    request = _request(
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=tuple(item[0] for item in pairs),
        input_artifact_ids=("shot", *(item[0].asset_id for item in pairs)),
        output_requirement=_output(ratio="adaptive"),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        image_resolver=lambda binding: data[binding.asset_id],
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["image"]["url"].endswith(base64.b64encode(data["first-frame"]).decode("ascii"))
    assert payload["last_frame"]["url"].endswith(base64.b64encode(data["last-frame"]).decode("ascii"))


def test_full_keyframed_image_to_video_uses_first_frame_and_timed_reference_pins():
    first, first_bytes = _image("first-frame", "first_frame")
    pin, pin_bytes = _image("pin")
    profile = _profile(keyframes=(GrokTimedKeyframe(
        asset_id=pin.asset_id,
        asset_sha256=pin.asset_sha256,
        timestamp_ticks=3,
    ),))
    request = _request(
        profile,
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=(first, pin),
        input_artifact_ids=("shot", first.asset_id, pin.asset_id),
        output_requirement=_output(resolution="720p"),
    )
    data = {first.asset_id: first_bytes, pin.asset_id: pin_bytes}
    provider, transport, args, *_ = _setup(
        request=request,
        profile=profile,
        image_resolver=lambda binding: data[binding.asset_id],
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["image"]["url"].endswith(base64.b64encode(first_bytes).decode("ascii"))
    assert payload["keyframes"] == [{
        "image": {"url": "data:image/png;base64," + base64.b64encode(pin_bytes).decode("ascii")},
        "timestamp_s": 1.0,
    }]
    assert "reference_images" not in payload


@pytest.mark.parametrize(
    "shape",
    [
        "last_only",
        "first_and_reference",
        "first_and_last",
        "first_last_and_fourteen_references",
        "fourteen_references",
    ],
)
def test_full_15_reference_video_emits_only_the_bound_image_roles_in_order(shape):
    profile = _profile()
    pairs: list[tuple[VideoImageReferenceBinding, bytes]]
    if shape == "last_only":
        pairs = [_image("last-frame", "last_frame")]
    elif shape == "first_and_reference":
        pairs = [_image("first-frame", "first_frame"), _image("reference-a")]
    elif shape == "first_and_last":
        pairs = [_image("first-frame", "first_frame"), _image("last-frame", "last_frame")]
    elif shape == "first_last_and_fourteen_references":
        pairs = [
            _image("first-frame", "first_frame"),
            _image("last-frame", "last_frame"),
            *(_image(f"reference-{index:02d}") for index in range(14)),
        ]
    else:
        pairs = [_image(f"reference-{index:02d}") for index in range(14)]
    bindings = tuple(item[0] for item in pairs)
    data = {binding.asset_id: raw for binding, raw in pairs}
    request = _request(
        profile,
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=bindings,
        input_artifact_ids=("shot", *(binding.asset_id for binding in bindings)),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        profile=profile,
        image_resolver=lambda binding: data[binding.asset_id],
    )
    provider.submit(*args)
    payload = _payload(transport)
    expected_refs = [
        {"url": "data:image/png;base64," + base64.b64encode(data[item.asset_id]).decode("ascii")}
        for item in bindings
        if item.role == "reference"
    ]
    assert transport.calls[0].url.endswith("/v1/videos/generations")
    assert payload.get("reference_images", []) == expected_refs
    assert ("image" in payload) is (shape in {
        "first_and_reference", "first_and_last", "first_last_and_fourteen_references",
    })
    assert ("last_frame" in payload) is (shape in {
        "last_only", "first_and_last", "first_last_and_fourteen_references",
    })


def test_profile_keyframes_and_voices_are_exactly_bound_and_not_double_sent():
    pinned = [_image(f"pin-{index}") for index in range(1, 5)]
    ordinary = [_image(f"reference-{index:02d}") for index in range(14)]
    profile = _profile(
        keyframes=tuple(
            GrokTimedKeyframe(
                asset_id=binding.asset_id,
                asset_sha256=binding.asset_sha256,
                timestamp_ticks=index * 3,
            )
            for index, (binding, _raw) in enumerate(pinned, start=1)
        ),
        reference_voices=("eve", "leo"),
    )
    pairs = pinned + ordinary
    bindings = tuple(item[0] for item in pairs)
    data = {binding.asset_id: raw for binding, raw in pairs}
    request = _request(
        profile,
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=bindings,
        input_artifact_ids=("shot", *(binding.asset_id for binding in bindings)),
        output_requirement=_output(native_audio=True),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        profile=profile,
        image_resolver=lambda binding: data[binding.asset_id],
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert len(payload["reference_images"]) == 14
    assert len(payload["keyframes"]) == 4
    assert [item["timestamp_s"] for item in payload["keyframes"]] == [1.0, 2.0, 3.0, 4.0]
    assert [item["voice_id"] for item in payload["reference_audios"]] == ["eve", "leo"]
    assert payload["generate_audio"] is True
    assert all(
        pin["image"]["url"] not in {item["url"] for item in payload["reference_images"]}
        for pin in payload["keyframes"]
    )


@pytest.mark.parametrize("optional_frame", ["none", "first", "last", "both"])
def test_keyframed_reference_mode_allows_documented_optional_boundary_frames(optional_frame):
    pins = [_image("pin-a"), _image("pin-b")]
    boundaries = []
    if optional_frame in {"first", "both"}:
        boundaries.append(_image("first-frame", "first_frame"))
    if optional_frame in {"last", "both"}:
        boundaries.append(_image("last-frame", "last_frame"))
    profile = _profile(
        keyframes=(
            GrokTimedKeyframe(
                asset_id="pin-a",
                asset_sha256=pins[0][0].asset_sha256,
                timestamp_ticks=3,
            ),
            GrokTimedKeyframe(
                asset_id="pin-b",
                asset_sha256=pins[1][0].asset_sha256,
                timestamp_ticks=6,
            ),
        ),
    )
    pairs = [*boundaries, *pins]
    request = _request(
        profile,
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=tuple(item[0] for item in pairs),
        input_artifact_ids=("shot", *(binding.asset_id for binding, _raw in pairs)),
    )
    data = {binding.asset_id: raw for binding, raw in pairs}
    provider, transport, args, *_ = _setup(
        request=request,
        profile=profile,
        image_resolver=lambda binding: data[binding.asset_id],
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert len(payload["keyframes"]) == 2
    assert payload.get("reference_images", []) == []
    assert ("image" in payload) is (optional_frame in {"first", "both"})
    assert ("last_frame" in payload) is (optional_frame in {"last", "both"})


def test_voice_only_text_request_uses_reference_audio_controls():
    profile = _profile(reference_voices=("eve",))
    request = _request(
        profile,
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        output_requirement=_output(native_audio=True),
    )
    provider, transport, args, *_ = _setup(request=request, profile=profile)
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["reference_audios"] == [{"voice_id": "eve"}]
    assert payload["generate_audio"] is True
    assert "image" not in payload
    assert "reference_images" not in payload


def test_voice_conditioned_reference_mode_emits_bound_images_and_voice_presets():
    profile = _profile(reference_voices=("eve",))
    reference, raw = _image("reference")
    request = _request(
        profile,
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=(reference,),
        input_artifact_ids=("shot", reference.asset_id),
        output_requirement=_output(native_audio=True),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        profile=profile,
        image_resolver=lambda _binding: raw,
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["reference_audios"] == [{"voice_id": "eve"}]
    assert payload["generate_audio"] is True
    assert payload["reference_images"] == [{
        "url": "data:image/png;base64," + base64.b64encode(raw).decode("ascii"),
    }]


def test_generation_payload_preserves_authored_image_and_audio_tags_verbatim():
    profile = _profile(reference_voices=("eve",))
    request = _request(
        profile,
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        prompt_text="Keep <IMAGE_0> visible and use <AUDIO_0> as the voice reference.",
        output_requirement=_output(native_audio=True),
    )
    provider, transport, args, *_ = _setup(request=request, profile=profile)
    provider.submit(*args)
    payload = _payload(transport)
    assert payload["prompt"] == request.prompt_text


@pytest.mark.parametrize(
    ("mode", "duration_millis", "total_seconds", "endpoint", "wire_duration"),
    [
        (VideoGenerationMode.VIDEO_EDIT, 5_000, 5, "edits", None),
        (VideoGenerationMode.VIDEO_EXTEND, 5_000, 9, "extensions", 4),
    ],
)
def test_classic_edit_and_extension_use_exact_video_bytes_and_inherited_output(
    mode, duration_millis, total_seconds, endpoint, wire_duration
):
    source = _media(duration_millis=duration_millis)
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=mode,
        media_bindings=(source,),
        input_artifact_ids=("shot", source.asset_id),
        output_requirement=_output(
            duration=total_seconds,
            resolution="source",
            native_audio=True,
        ),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        media_resolver=lambda binding: MP4,
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert transport.calls[0].url.endswith(f"/v1/videos/{endpoint}")
    assert payload == {
        "model": GROK_VIDEO_MODEL_CLASSIC,
        "prompt": request.prompt_text,
        "video": {"url": "data:video/mp4;base64," + base64.b64encode(MP4).decode("ascii")},
        **({"duration": wire_duration} if wire_duration is not None else {}),
    }
    assert "resolution" not in payload
    assert "aspect_ratio" not in payload


def test_unbound_or_invalid_source_video_fails_before_credential_and_post():
    source = _media()
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=VideoGenerationMode.VIDEO_EDIT,
        media_bindings=(source,),
        input_artifact_ids=("shot", source.asset_id),
        output_requirement=_output(resolution="source", native_audio=True),
    )
    credential_reads: list[bool] = []
    provider, transport, args, *_ = _setup(
        request=request,
        media_resolver=lambda _binding: b"not an MP4 source",
        credential=lambda: credential_reads.append(True) or "token",
    )
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert not credential_reads
    assert not transport.calls


@pytest.mark.parametrize(
    ("source_kwargs", "resolution"),
    [
        ({"width": 1920, "height": 1080}, "source"),
        ({"width": 1280, "height": 720}, "480p"),
    ],
)
def test_edit_rejects_source_resolution_outside_inherited_output_before_post(source_kwargs, resolution):
    source = _media(**source_kwargs)
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=VideoGenerationMode.VIDEO_EDIT,
        media_bindings=(source,),
        input_artifact_ids=("shot", source.asset_id),
        output_requirement=_output(resolution=resolution, native_audio=True),
    )
    _assert_resolve_rejected_before_egress(request, _profile())


@pytest.mark.parametrize(
    "case",
    [
        "classic_last_only_r2v",
        "lite_r2v",
        "lite_with_reference_image",
        "full_i2v_with_reference_image",
        "i2v_with_named_ratio",
        "full_r2v_with_video_media",
        "edit_with_image_media_mix",
        "edit_without_inherited_audio",
        "extension_with_image_media_mix",
        "voice_profile_without_native_audio",
    ],
)
def test_unsupported_model_role_and_operation_shapes_fail_before_egress(case):
    profile = _profile()
    pairs = []
    media_bindings = ()
    model = GROK_VIDEO_MODEL_FULL
    mode = VideoGenerationMode.REFERENCE_TO_VIDEO
    output = _output()
    if case == "classic_last_only_r2v":
        model = GROK_VIDEO_MODEL_CLASSIC
        pairs = [_image("last", "last_frame")]
    elif case == "lite_r2v":
        model = GROK_VIDEO_MODEL_LITE
        pairs = [_image("reference")]
    elif case == "lite_with_reference_image":
        model = GROK_VIDEO_MODEL_LITE
        mode = VideoGenerationMode.IMAGE_TO_VIDEO
        pairs = [_image("first", "first_frame"), _image("reference")]
    elif case == "full_i2v_with_reference_image":
        mode = VideoGenerationMode.IMAGE_TO_VIDEO
        pairs = [_image("first", "first_frame"), _image("reference")]
    elif case == "i2v_with_named_ratio":
        mode = VideoGenerationMode.IMAGE_TO_VIDEO
        pairs = [_image("first", "first_frame")]
        output = _output(ratio="16:9")
    elif case == "full_r2v_with_video_media":
        source = _media()
        media_bindings = (source,)
    elif case == "edit_with_image_media_mix":
        model = GROK_VIDEO_MODEL_CLASSIC
        mode = VideoGenerationMode.VIDEO_EDIT
        source = _media()
        media_bindings = (source,)
        pairs = [_image("reference")]
        output = _output(resolution="source", native_audio=True)
    elif case == "edit_without_inherited_audio":
        model = GROK_VIDEO_MODEL_CLASSIC
        mode = VideoGenerationMode.VIDEO_EDIT
        source = _media()
        media_bindings = (source,)
        output = _output(resolution="source", native_audio=False)
    elif case == "extension_with_image_media_mix":
        model = GROK_VIDEO_MODEL_CLASSIC
        mode = VideoGenerationMode.VIDEO_EXTEND
        source = _media()
        media_bindings = (source,)
        pairs = [_image("reference")]
        output = _output(duration=9, resolution="source", native_audio=True)
    else:
        profile = _profile(reference_voices=("eve",))
        mode = VideoGenerationMode.TEXT_TO_VIDEO
        output = _output(native_audio=False)

    request = _request(
        profile,
        model_id=model,
        mode=mode,
        image_bindings=tuple(item[0] for item in pairs),
        media_bindings=media_bindings,
        input_artifact_ids=(
            "shot",
            *(binding.asset_id for binding, _raw in pairs),
            *(binding.asset_id for binding in media_bindings),
        ),
        output_requirement=output,
    )
    _assert_resolve_rejected_before_egress(request, profile)


def test_keyframe_profile_must_match_exact_bound_reference_hash_before_egress():
    image, _raw = _image("pin")
    profile = _profile(
        keyframes=(GrokTimedKeyframe(
            asset_id="pin",
            asset_sha256="f" * 64,
            timestamp_ticks=3,
        ),),
    )
    request = _request(
        profile,
        model_id=GROK_VIDEO_MODEL_FULL,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        image_bindings=(image,),
        input_artifact_ids=("shot", image.asset_id),
    )
    _assert_resolve_rejected_before_egress(request, profile)


def test_edit_preserves_fractional_source_timing_with_provider_selected_output():
    source = _media(duration_millis=5_500)
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=VideoGenerationMode.VIDEO_EDIT,
        media_bindings=(source,),
        input_artifact_ids=("shot", source.asset_id),
        output_requirement=_output(
            resolution="source",
            native_audio=True,
            timing="provider_selected",
        ),
    )
    provider, transport, args, *_ = _setup(
        request=request,
        media_resolver=lambda _binding: MP4,
    )
    provider.submit(*args)
    payload = _payload(transport)
    assert set(payload) == {"model", "prompt", "video"}


def test_extension_rejects_unrepresentable_added_duration_before_post():
    source = _media(duration_millis=5_500)
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=VideoGenerationMode.VIDEO_EXTEND,
        media_bindings=(source,),
        input_artifact_ids=("shot", source.asset_id),
        output_requirement=_output(
            duration=9,
            resolution="source",
            native_audio=True,
        ),
    )
    credential_reads: list[bool] = []
    with pytest.raises(AiVideoError):
        _setup(
            request=request,
            media_resolver=lambda _binding: MP4,
            credential=lambda: credential_reads.append(True) or "token",
        )
    assert not credential_reads


def test_wrong_operation_subscription_binding_fails_before_credential_or_post():
    source = _media()
    request = _request(
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        mode=VideoGenerationMode.VIDEO_EDIT,
        media_bindings=(source,),
        input_artifact_ids=("shot", source.asset_id),
        output_requirement=_output(resolution="source", native_audio=True),
    )
    wrong = _binding(
        _profile(),
        model_id=GROK_VIDEO_MODEL_CLASSIC,
        operation_path="/v1/videos/extensions",
    )
    credential_reads: list[bool] = []
    provider, transport, args, *_ = _setup(
        request=request,
        binding=wrong,
        media_resolver=lambda _binding: MP4,
        credential=lambda: credential_reads.append(True) or "token",
    )
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert not credential_reads
    assert not transport.calls


def test_edit_and_extension_transport_allow_only_the_three_fixed_post_paths():
    headers = {
        "authorization": "Bearer fake",
        "content-type": "application/json",
        "accept": "application/json",
    }
    for path in ("generations", "edits", "extensions"):
        HttpxGrokTransport._validate_api_request(
            GrokTransportRequest(
                "POST",
                f"https://cli-chat-proxy.grok.com/v1/videos/{path}",
                headers,
                b"{}",
            )
        )
    with pytest.raises(AiVideoError):
        HttpxGrokTransport._validate_api_request(
            GrokTransportRequest(
                "POST",
                "https://cli-chat-proxy.grok.com/v1/videos/arbitrary",
                headers,
                b"{}",
            )
        )
