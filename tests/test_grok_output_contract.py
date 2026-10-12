import pytest

from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.grok_profile import grok_capabilities


def output(**changes):
    values = dict(timing_mode="nominal_seconds", duration_seconds=4,
        dimension_mode="adaptive", width=None, height=None, resolution_label="720p",
        ratio="adaptive", fps=None, container="mp4", mime_type="video/mp4",
        native_audio=False)
    values.update(changes)
    return VideoFlexibleOutputRequirement(**values)


def test_unknown_fps_is_explicit_and_does_not_claim_exact_frame_count():
    value = output()
    generation_variants = tuple(v for v in grok_capabilities().variants
        if v.mode.value not in {"video_edit", "video_extend"} and "c4-static" not in v.capability_id)
    assert generation_variants
    assert all(v.output_capability.supports(value) for v in generation_variants)
    assert value.matches_timing_measurement(duration_milliseconds=4000, frame_count=120)
    assert value.matches_timing_measurement(duration_milliseconds=4000, frame_count=96)
    assert not value.matches_timing_measurement(duration_milliseconds=5000, frame_count=120)


def test_frame_count_cannot_be_declared_without_fps():
    with pytest.raises(ValueError):
        VideoFlexibleOutputRequirement(timing_mode="frame_count", frame_count=120,
            dimension_mode="adaptive", width=None, height=None, fps=None, container="mp4",
            mime_type="video/mp4", native_audio=False)


@pytest.mark.parametrize("ratio,width,height", [
    ("16:9", 1280, 720), ("9:16", 720, 1280), ("1:1", 720, 720),
    ("3:2", 1080, 720), ("2:3", 720, 1080), ("5:2", 1800, 720),
])
def test_requested_ratio_is_measured_even_with_adaptive_raster(ratio, width, height):
    from ai_video.production.video_geometry import matches_video_geometry

    requirement = output(ratio=ratio)
    assert requirement.width is None and requirement.height is None
    assert matches_video_geometry(requirement, width=width, height=height)
    assert not matches_video_geometry(requirement, width=width + 10, height=height)


def test_existing_exact_provider_raster_is_not_reinterpreted_as_adaptive_ratio(tmp_path):
    from ai_video.production.seedance import SeedanceVideoProvider
    from ai_video.production.video_artifact import probe_generated_video_candidate
    from test_production_seedance import (
        FIXED_NOW, _FakeTransport, _active_profile, _provider_asset_reference, _request,
    )
    from test_production_video import _continuity_fetch_receipt, _continuity_probe

    model = "doubao-seedance-2-0-fast-260128"
    profile = _active_profile(model)
    provider = SeedanceVideoProvider(profile=profile, transport=_FakeTransport(),
        credential=lambda: pytest.fail("offline output verification must not read credentials"),
        input_reference=_provider_asset_reference, now=lambda: FIXED_NOW)
    requirement = output(timing_mode="exact_seconds", duration_seconds=15,
        dimension_mode="exact", width=864, height=496, resolution_label="480p",
        ratio="16:9", fps=24, native_audio=True)
    resolved = provider.resolve(_request(profile, model_id=model, output=requirement))
    data = b"sealed-candidate-video"
    path = tmp_path / "candidate.mp4"
    path.write_bytes(data)

    def probe(fd):
        value = _continuity_probe(fd)
        value["streams"][0].update(width=864, height=496, duration="15", nb_frames="360")
        value["streams"].append({"codec_type": "audio", "codec_name": "aac"})
        value["format"]["duration"] = "15"
        return value

    with path.open("rb") as held:
        _, measured, _ = probe_generated_video_candidate(held.fileno(), resolved,
            _continuity_fetch_receipt(resolved, data), probe=probe)
    assert (measured.width, measured.height) == (864, 496)


@pytest.mark.parametrize("ratio,accepted", [("16:9", True), ("4:3", False)])
def test_fetched_candidate_rejects_wrong_requested_aspect_ratio(tmp_path, ratio, accepted):
    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production.grok import GrokVideoProvider
    from ai_video.production.video_artifact import probe_generated_video_candidate
    from test_production_grok import _profile, _request
    from test_production_video import _continuity_fetch_receipt, _continuity_probe

    profile = _profile()
    provider = GrokVideoProvider(profile=profile,
        credential=lambda: pytest.fail("pure resolution must not load credentials"))
    resolved = provider.resolve(_request(profile,
        output_requirement=output(ratio=ratio, duration_seconds=6)))
    data = b"sealed-candidate-video"
    path = tmp_path / "candidate.mp4"
    path.write_bytes(data)
    receipt = _continuity_fetch_receipt(resolved, data)
    with path.open("rb") as held:
        if accepted:
            _, measured, _ = probe_generated_video_candidate(
                held.fileno(), resolved, receipt, probe=_continuity_probe)
            assert measured.width == 1280 and measured.height == 720
        else:
            with pytest.raises(AiVideoError) as failure:
                probe_generated_video_candidate(held.fileno(), resolved, receipt,
                    probe=_continuity_probe)
            assert failure.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID


@pytest.mark.parametrize("mode", ["video_edit", "video_extend", "image_to_video", "text_to_video"])
@pytest.mark.parametrize("defect", [None, "geometry", "duration", "resolution"])
def test_grok_output_is_reopened_against_inherited_inputs(tmp_path, mode, defect):
    from ai_video.errors import AiVideoError
    from ai_video.production.grok import GrokVideoProvider
    from ai_video.production.video import VideoGenerationMode
    from ai_video.production.video_artifact import probe_generated_video_candidate
    from test_grok_video_operations import _image, _media
    from test_production_grok import _profile, _request
    from test_production_video import _continuity_fetch_receipt, _continuity_probe

    profile = _profile()
    kwargs = {"mode": VideoGenerationMode(mode)}
    if mode in {"video_edit", "video_extend"}:
        kwargs.update(model_id="grok-imagine-video", media_bindings=(
            _media(duration_millis=6250 if mode == "video_edit" else 3000),),
            input_artifact_ids=("shot", "source-video"))
    elif mode == "image_to_video":
        binding, _ = _image("first", "first_frame")
        kwargs.update(image_bindings=(binding,), input_artifact_ids=("shot", "first"))
    provider = GrokVideoProvider(profile=profile,
        credential=lambda: pytest.fail("pure resolution must not load credentials"))
    resolved = provider.resolve(_request(profile, **kwargs, output_requirement=output(
        duration_seconds=None if mode == "video_edit" else 6,
        timing_mode="provider_selected" if mode == "video_edit" else "nominal_seconds",
        resolution_label="source" if mode in {"video_edit", "video_extend"} else "720p",
        native_audio=mode in {"video_edit", "video_extend"})))
    raw = b"sealed-candidate-video"
    path = tmp_path / "candidate.mp4"
    path.write_bytes(raw)
    receipt = _continuity_fetch_receipt(resolved, raw)

    def probe(fd):
        value = _continuity_probe(fd)
        video = value["streams"][0]
        duration = "6.25" if mode == "video_edit" else "6"
        if defect == "duration":
            duration = "7"
        if defect == "geometry":
            video["width"] = 720
        if defect == "resolution":
            video.update(width=640, height=360)
        video.update(duration=duration, nb_frames="150" if duration == "6.25" else "144")
        value["format"]["duration"] = duration
        if resolved.effective_output.native_audio:
            value["streams"].append({"codec_type": "audio", "codec_name": "aac"})
        return value

    # T2V adaptive geometry permits an unspecified aspect ratio; the declared
    # resolution, duration and every inherited source obligation still bind.
    accepted = defect is None or (mode == "text_to_video" and defect == "geometry")
    with path.open("rb") as held:
        if accepted:
            probe_generated_video_candidate(held.fileno(), resolved, receipt, probe=probe)
        else:
            with pytest.raises(AiVideoError):
                probe_generated_video_candidate(held.fileno(), resolved, receipt, probe=probe)
