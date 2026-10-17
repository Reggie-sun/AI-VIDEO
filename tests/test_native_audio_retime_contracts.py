from pydantic import ValidationError
import pytest

from ai_video.production.hashing import canonical_sha256
from ai_video.production.paths import canonical_video_probe_receipt_path
from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint


def _points():
    return (
        VideoTimePoint(source_frame=0, output_frame=0),
        VideoTimePoint(source_frame=24, output_frame=18),
        VideoTimePoint(source_frame=48, output_frame=40),
    )


def test_video_time_map_versions_separate_muted_and_native_audio_use():
    muted = VideoTimeMap(
        contract_version="video-time-map/1",
        points=_points(),
        audio_policy="mute",
    )
    preserved = VideoTimeMap(
        contract_version="video-time-map/2",
        points=_points(),
        audio_policy="retime_preserve_pitch",
    )

    assert muted.audio_policy == "mute"
    assert preserved.audio_policy == "retime_preserve_pitch"

    with pytest.raises(ValidationError):
        VideoTimeMap(
            contract_version="video-time-map/1",
            points=_points(),
            audio_policy="retime_preserve_pitch",
        )
    with pytest.raises(ValidationError):
        VideoTimeMap(
            contract_version="video-time-map/2",
            points=_points(),
            audio_policy="mute",
        )


def test_native_video_kind_cannot_be_authored_as_an_independent_audio_track():
    from ai_video.production.composition_contracts import AudioKind, AudioTrackSpec

    with pytest.raises(ValidationError, match="derived from a mapped visual layer"):
        AudioTrackSpec(track_id="native-injection", asset_id="video", shot_id="shot-1",
                       audio_kind=AudioKind.NATIVE_VIDEO)


def attach_exact_audio_probe(
    loaded,
    asset_id: str = "image-shot-2",
    *,
    source_fps_numerator: int | None = None,
    source_fps_denominator: int = 1,
    audio_stream_count: int = 1,
):
    """Add a canonical sealed probe fixture for the selected VIDEO bytes."""
    from ai_video.production.models import VideoAssetMetadata

    asset_index = next(
        index for index, item in enumerate(loaded.registry.assets)
        if item.asset_id == asset_id
    )
    asset = loaded.registry.assets[asset_index]
    metadata = asset.video_metadata
    assert metadata is not None
    fps_numerator = source_fps_numerator or metadata.fps_numerator
    duration_milliseconds = metadata.frame_count * 1000 * source_fps_denominator // fps_numerator
    measured = MeasuredVideoMetadata(
        container_name="mp4",
        codec_name=metadata.codec_name,
        width=metadata.width,
        height=metadata.height,
        fps_numerator=fps_numerator,
        fps_denominator=source_fps_denominator,
        duration_milliseconds=duration_milliseconds,
        frame_count=metadata.frame_count,
        audio_stream_count=audio_stream_count,
        size_bytes=asset.size_bytes,
        artifact_sha256=asset.sha256,
    )
    proof = {
        "request_receipt_fingerprint": metadata.request_receipt_fingerprint,
        "resolved_generation_hash": metadata.resolved_generation_hash,
        "fetch_fingerprint": "3" * 64,
        "measured": measured,
        "continuity_evidence": None,
        "commercial_evidence": None,
        "nominal_endpoint_recovery": None,
    }
    candidate = VideoProbeReceipt.model_construct(**proof, content_hash="0" * 64)
    receipt = VideoProbeReceipt.model_validate({
        **candidate.model_dump(mode="json"),
        "content_hash": canonical_sha256(
            candidate.model_dump(mode="json", exclude={"content_hash"})
        ),
    })
    probe_path = loaded.root / canonical_video_probe_receipt_path(receipt.content_hash)
    probe_path.parent.mkdir(parents=True, exist_ok=True)
    probe_path.write_text(receipt.model_dump_json(), encoding="utf-8")
    updated_metadata = VideoAssetMetadata(
        **{
            **metadata.model_dump(mode="python"),
            "fps_numerator": fps_numerator,
            "fps_denominator": source_fps_denominator,
            "duration_milliseconds": duration_milliseconds,
            "probe_receipt_id": receipt.content_hash,
        }
    )
    assets = list(loaded.registry.assets)
    assets[asset_index] = asset.model_copy(
        update={
            "video_metadata": updated_metadata,
            "duration_seconds": duration_milliseconds / 1000,
        }
    )
    registry = loaded.registry.model_copy(update={"assets": tuple(assets)})
    return loaded.model_copy(update={"registry": registry})


@pytest.mark.parametrize(
    ("fps", "first_output_frame", "expected_segments", "expected_source_window"),
    (
        (24, 18, ((24_000, 48_000, 0, 36_000), (72_000, 72_000, 36_000, 60_000)), (24_000, 120_000)),
        (30, 30, ((19_200, 38_400, 0, 48_000), (57_600, 57_600, 48_000, 48_000)), (19_200, 96_000)),
    ),
)
def test_native_audio_retime_uses_absolute_trimmed_source_samples_and_shot_offsets(
    tmp_path, fps, first_output_frame, expected_segments, expected_source_window
):
    from ai_video.production.composition import resolve_composition
    from ai_video.production.composition_contracts import AudioKind, AudioTrackSpec, ResolvedTimeline
    from ai_video.production.video_retime import VideoTimeMap
    from production_project_factory import make_composition_spec, write_and_load_two_shot_project
    from test_production_video_retime import _reseal, _with_map, _with_video_layer

    loaded = write_and_load_two_shot_project(tmp_path, fps=fps)
    spec = _reseal(
        make_composition_spec(),
        delivery_profile=loaded.project.delivery_profile,
    )
    loaded, spec = _with_video_layer(
        tmp_path,
        loaded,
        spec,
        shot_index=1,
        trim_start_frame=12,
        trim_duration_frames=60,
        frame_count=72,
    )
    loaded = attach_exact_audio_probe(loaded, source_fps_numerator=fps)
    time_map = VideoTimeMap(
        contract_version="video-time-map/2",
        points=(
            VideoTimePoint(source_frame=0, output_frame=0),
            VideoTimePoint(source_frame=24, output_frame=first_output_frame),
            VideoTimePoint(source_frame=60, output_frame=fps * 2),
        ),
        audio_policy="retime_preserve_pitch",
    )
    with pytest.raises(ValidationError, match="require CompositionSpec 2.4"):
        _with_map(spec, layer_index=1, time_map=time_map, schema="2.3")
    spec = _with_map(spec, layer_index=1, time_map=time_map, schema="2.4")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.schema_version == "2.4"
    native = next(span for span in timeline.audio_spans if span.audio_kind is AudioKind.NATIVE_VIDEO)
    assert native.track_id == "native-video-audio::layer-shot-2"
    assert native.asset_id == "image-shot-2"
    assert native.asset_sha256 == next(
        item.sha256 for item in loaded.registry.assets if item.asset_id == native.asset_id
    )
    assert (native.start_sample, native.duration_samples) == (96_000, 96_000)
    assert (native.source_start_sample, native.source_duration_samples) == expected_source_window
    assert native.native_audio_retime.visual_layer_id == "layer-shot-2"
    assert native.native_audio_retime.time_map_sha256 == canonical_sha256(
        time_map.model_dump(mode="json")
    )
    assert tuple(
        (
            segment.source_start_sample,
            segment.source_duration_samples,
            segment.output_offset_sample,
            segment.output_duration_samples,
        )
        for segment in native.native_audio_retime.segments
    ) == expected_segments

    altered = timeline.model_dump(mode="python")
    native_index = next(
        index for index, item in enumerate(altered["audio_spans"])
        if item["audio_kind"] is AudioKind.NATIVE_VIDEO
        or item["audio_kind"] == AudioKind.NATIVE_VIDEO.value
    )
    altered["audio_spans"][native_index]["asset_sha256"] = "f" * 64
    with pytest.raises(ValidationError, match="exact mapped VIDEO asset"):
        ResolvedTimeline.model_validate(altered)

    with pytest.raises(ValidationError, match="explicitly muted visual-only"):
        _reseal(
            spec,
            audio_tracks=(AudioTrackSpec(
                track_id="extra-same-shot",
                audio_kind=AudioKind.AMBIENCE,
                asset_id="unresolved-audio",
                shot_id="shot-2",
            ),),
        )


@pytest.mark.parametrize("shot_frames", [1, 3])
def test_native_audio_uses_global_sample_boundaries_after_fractional_frame(
    tmp_path, shot_frames,
):
    from ai_video.production.composition import resolve_composition
    from ai_video.production.composition_contracts import AudioKind
    from production_project_factory import make_composition_spec, write_and_load_two_shot_project
    from test_production_video_retime import _reseal, _with_map, _with_video_layer

    loaded = write_and_load_two_shot_project(
        tmp_path, seconds=(shot_frames / 24, shot_frames / 24), fps=24,
    )
    spec = _reseal(make_composition_spec(sample_rate=44_100),
                   delivery_profile=loaded.project.delivery_profile)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, shot_index=1, trim_start_frame=0,
        trim_duration_frames=shot_frames, frame_count=shot_frames,
    )
    loaded = attach_exact_audio_probe(loaded)
    anchors = ((0, 0), (1, 1), (3, 3)) if shot_frames == 3 else ((0, 0), (1, 1))
    mapping = VideoTimeMap(
        contract_version="video-time-map/2", audio_policy="retime_preserve_pitch",
        points=tuple(VideoTimePoint(source_frame=s, output_frame=o) for s, o in anchors),
    )
    spec = _with_map(spec, layer_index=1, time_map=mapping, schema="2.4")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    native, = (span for span in timeline.audio_spans if span.audio_kind is AudioKind.NATIVE_VIDEO)
    expected_start = shot_frames * 44_100 // 24
    expected_end = 2 * shot_frames * 44_100 // 24
    assert (native.start_sample, native.duration_samples) == (
        expected_start, expected_end - expected_start,
    )
    assert native.start_sample + native.duration_samples == timeline.total_samples == expected_end
    assert native.source_duration_samples == shot_frames * 44_100 // 24
    segments = native.native_audio_retime.segments
    assert segments[0].output_offset_sample == 0
    assert segments[0].output_duration_samples == 1_838
    assert sum(segment.output_duration_samples for segment in segments) == native.duration_samples


def test_native_audio_requires_one_exact_probe_stream_and_schema_24(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.composition import resolve_composition
    from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
    from production_project_factory import make_loaded_project_and_spec
    from test_production_video_retime import _with_map, _with_video_layer

    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, shot_index=1, trim_start_frame=12,
        trim_duration_frames=60, frame_count=72,
    )
    loaded = attach_exact_audio_probe(loaded, audio_stream_count=0)
    time_map = VideoTimeMap(
        contract_version="video-time-map/2",
        points=(
            VideoTimePoint(source_frame=0, output_frame=0),
            VideoTimePoint(source_frame=60, output_frame=48),
        ),
        audio_policy="retime_preserve_pitch",
    )
    spec = _with_map(spec, layer_index=1, time_map=time_map, schema="2.4")

    with pytest.raises(AiVideoError, match="one audio stream"):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


@pytest.mark.parametrize("extra_track", ("same_shot_audio", "global_audio", "caption", "voice"))
def test_v2_map_keeps_manual_p4_and_voice_exclusions(tmp_path, extra_track):
    from pathlib import Path

    from ai_video.production.composition_contracts import (
        AudioKind,
        AudioTrackSpec,
        CaptionStyleReference,
        CaptionTrackBinding,
        VoiceCompositionSource,
    )
    from ai_video.production.models import GenerationExecutionBindingPointer
    from ai_video.production.video_retime import VideoTimeMap
    from production_project_factory import make_loaded_project_and_spec
    from test_production_video_retime import _reseal, _with_map

    _loaded, spec = make_loaded_project_and_spec(tmp_path)
    time_map = VideoTimeMap(
        contract_version="video-time-map/2",
        points=(
            VideoTimePoint(source_frame=0, output_frame=0),
            VideoTimePoint(source_frame=48, output_frame=48),
        ),
        audio_policy="retime_preserve_pitch",
    )
    spec = _with_map(spec, layer_index=1, time_map=time_map, schema="2.4")
    if extra_track in {"same_shot_audio", "global_audio"}:
        track = AudioTrackSpec(
            track_id="manual-audio",
            audio_kind=AudioKind.AMBIENCE,
            asset_id="manual-audio-asset",
            shot_id="shot-2" if extra_track == "same_shot_audio" else None,
            start_sample=0 if extra_track == "global_audio" else None,
        )
        fields = {"audio_tracks": (track,)}
    elif extra_track == "caption":
        style_hash = "e" * 64
        fields = {
            "caption_tracks": (CaptionTrackBinding(
                binding_id="manual-caption",
                caption_asset_id="manual-caption-asset",
                source_audio_track_id="manual-audio",
                shot_id="shot-2",
                style_reference=CaptionStyleReference(
                    artifact_id="style",
                    revision=1,
                    content_hash=style_hash,
                    path=Path(f"assets/styles/{style_hash}.json"),
                ),
            ),)
        }
    else:
        binding_hash = "b" * 64
        fields = {
            "voice_sources": (VoiceCompositionSource(
                shot_id="shot-2",
                source_project_file=Path("/tmp/source/project.yaml"),
                execution_binding=GenerationExecutionBindingPointer(
                    path=Path(f"state/video-generation/decision-bindings/{binding_hash}.json"),
                    binding_hash=binding_hash,
                    request_fingerprint="c" * 64,
                    file_sha256="d" * 64,
                ),
            ),)
        }

    with pytest.raises(ValidationError, match="explicitly muted visual-only"):
        _reseal(spec, **fields)
