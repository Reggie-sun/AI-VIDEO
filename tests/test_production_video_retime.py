from __future__ import annotations

import hashlib
import struct
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.composition import resolve_composition
from ai_video.production.composition_contracts import (
    ResolvedTimeline,
    VoiceCompositionSource,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    AudioKind,
    AudioTrackSpec,
    CaptionStyleReference,
    CaptionTrackBinding,
    CompositionSpec,
    DurationPolicy,
    GenerationExecutionBindingPointer,
    ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
from ai_video.production.visual_media import (
    VisualMediaValidationError,
    render_visual_element,
)
from production_project_factory import (
    make_loaded_project_and_spec,
    make_p4_composition_fixture,
)


def _video_payload() -> bytes:
    return (
        struct.pack(">I4s4sI4s", 20, b"ftyp", b"isom", 0, b"isom")
        + struct.pack(">I4s", 8, b"moov")
    )


def _with_video_layer(
    root: Path,
    loaded,
    spec,
    *,
    shot_index: int = 0,
    trim_start_frame: int = 12,
    trim_duration_frames: int | None = 60,
    frame_count: int = 72,
):
    payload = _video_payload()
    shot_id = loaded.shots[shot_index].shot_id
    path = root / f"assets/files/{shot_id}.mp4"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    metadata = VideoAssetMetadata(
        container_name="mp4",
        codec_name="h264",
        width=1280,
        height=720,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=frame_count * 1000 // 24,
        frame_count=frame_count,
        probe_receipt_id=f"probe-{shot_id}",
        request_receipt_fingerprint="1" * 64,
        resolved_generation_hash="2" * 64,
        provenance_receipt_id=f"provenance-{shot_id}",
    )
    original = loaded.registry.assets[shot_index]
    video = original.model_copy(
        update={
            "asset_type": AssetType.VIDEO,
            "artifact_path": path.relative_to(root),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "mime_type": "video/mp4",
            "duration_seconds": frame_count / 24,
            "width": 1280,
            "height": 720,
            "source_kind": AssetSourceKind.GENERATED,
            "tool": ToolIdentity(name="fixture-video", version="1"),
            "video_metadata": metadata,
        }
    )
    role = AssetRoleRequirement(
        role="video",
        asset_ids=(video.asset_id,),
        allowed_asset_types=(AssetType.VIDEO,),
    )
    shots = list(loaded.shots)
    shots[shot_index] = shots[shot_index].model_copy(
        update={"visual_strategy": "generated_video", "required_asset_roles": (role,)}
    )
    assets = list(loaded.registry.assets)
    assets[shot_index] = video
    asset_paths = dict(loaded.asset_paths)
    asset_paths[video.asset_id] = path
    loaded = loaded.model_copy(
        update={
            "shots": tuple(shots),
            "registry": loaded.registry.model_copy(update={"assets": tuple(assets)}),
            "asset_paths": asset_paths,
        }
    )
    layers = list(spec.layers)
    layers[shot_index] = layers[shot_index].model_copy(
        update={
            "asset_role": "video",
            "trim_start_frame": trim_start_frame,
            "trim_duration_frames": trim_duration_frames,
        }
    )
    spec = _reseal(spec, layers=tuple(layers))
    return loaded, spec


def _reseal(spec, **changes):
    candidate = spec.model_copy(
        update={"content_hash": "0" * 64, **changes}
    )
    sealed = seal_artifact(candidate)
    return CompositionSpec.model_validate(sealed.model_dump(mode="python"))


def _time_map(*pairs: tuple[int, int]) -> VideoTimeMap:
    return VideoTimeMap(
        points=tuple(
            VideoTimePoint(source_frame=source, output_frame=output)
            for source, output in pairs
        ),
        audio_policy="mute",
    )


def _with_map(spec, *, layer_index: int, time_map: VideoTimeMap, schema: str = "2.3"):
    layers = list(spec.layers)
    layers[layer_index] = layers[layer_index].model_copy(
        update={"source_time_map": time_map}
    )
    return _reseal(spec, schema_version=schema, layers=tuple(layers))


def test_video_time_map_uses_strict_integer_anchors_and_inclusive_rate_bounds():
    assert _time_map((0, 0), (5, 1)).source_duration_frames == 5
    assert _time_map((0, 0), (1, 10)).output_duration_frames == 10
    with pytest.raises(ValidationError):
        _time_map((0, 0), (1, 11))
    with pytest.raises(ValidationError):
        _time_map((0, 0), (10, 1))
    with pytest.raises(ValidationError):
        VideoTimeMap(
            points=(
                VideoTimePoint(source_frame=0, output_frame=0),
                VideoTimePoint(source_frame=1.5, output_frame=1),
            ),
            audio_policy="mute",
        )


def test_legacy_composition_layer_bytes_omit_absent_time_map(tmp_path):
    _loaded, spec = make_loaded_project_and_spec(tmp_path)
    payload = spec.model_dump(mode="json")
    assert spec.schema_version == "2.0"
    assert all("source_time_map" not in layer for layer in payload["layers"])
    assert spec.content_hash == (
        "05cdde712778ca78f4574dfe3c560da748b041786bd91903031452083cc7acc4"
    )


def test_piecewise_time_map_resolves_exact_same_shot_visual_spans(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec, shot_index=1)
    spec = _with_map(
        spec,
        layer_index=1,
        time_map=_time_map((0, 0), (24, 12), (54, 36), (60, 48)),
    )

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.schema_version == "2.3"
    spans = tuple(item for item in timeline.visual_spans if item.shot_id == "shot-2")
    assert tuple(item.start_frame for item in spans) == tuple(range(48, 96))
    assert all(item.duration_frames == 1 for item in spans)
    assert tuple(item.trim_start_frame for item in spans) == (
        *range(12, 36, 2),
        36, 37, 38, 39, 41, 42, 43, 44, 46, 47, 48, 49,
        51, 52, 53, 54, 56, 57, 58, 59, 61, 62, 63, 64,
        66, 66, 67, 67, 68, 68, 69, 69, 70, 70, 71, 71,
    )
    assert all(item.trim_duration_frames == 1 for item in spans)
    assert tuple(item.layer_id for item in spans) == (
        "layer-shot-2",
        *(f"layer-shot-2--retime-{index}" for index in range(2, 49)),
    )
    assert tuple((item.start_sample, item.duration_samples) for item in spans) == tuple(
        (sample, 2_000) for sample in range(96_000, 192_000, 2_000)
    )
    assert len({item.layer_id for item in spans}) == len(spans)
    assert spans[0].incoming_transition is not None
    assert all(item.incoming_transition is None for item in spans[1:])
    assert timeline.total_frames == 96
    assert timeline.total_samples == 192_000


def test_unit_rate_time_map_resolves_as_one_continuous_span(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, shot_index=1, trim_start_frame=0,
        trim_duration_frames=48, frame_count=48,
    )
    spec = _with_map(
        spec, layer_index=1, time_map=_time_map((0, 0), (48, 48))
    )
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    span = next(item for item in timeline.visual_spans if item.shot_id == "shot-2")

    assert (
        span.layer_id,
        span.start_frame,
        span.duration_frames,
        span.trim_start_frame,
        span.trim_duration_frames,
    ) == ("layer-shot-2", 48, 48, 0, 48)


@pytest.mark.parametrize("trim_duration", [None, 48])
def test_legacy_unit_rate_video_span_renders_with_optional_trim_duration(
    tmp_path, trim_duration,
):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, shot_index=1, trim_start_frame=0,
        trim_duration_frames=48, frame_count=48,
    )
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    span = next(item for item in timeline.visual_spans if item.shot_id == "shot-2")
    span = span.model_copy(update={"trim_duration_frames": trim_duration})

    element = render_visual_element(
        span, video_id="legacy-video", start_seconds="2", duration_seconds="2",
        media_start_seconds="0", track_index=0,
    )

    assert '<video id="legacy-video"' in element
    assert 'data-duration="2"' in element
    assert "data-playback-rate" not in element


def test_renderer_rejects_nonunit_video_span_without_resolved_sampling(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, shot_index=1, trim_start_frame=0,
        trim_duration_frames=48, frame_count=48,
    )
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    span = next(item for item in timeline.visual_spans if item.shot_id == "shot-2")
    span = span.model_copy(update={"trim_duration_frames": 24})

    with pytest.raises(VisualMediaValidationError, match="source-frame sampling"):
        render_visual_element(
            span, video_id="unsampled-video", start_seconds="2", duration_seconds="2",
            media_start_seconds="0", track_index=0,
        )


def test_content_driven_duration_uses_time_map_output_endpoint(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec, shot_index=1)
    loaded_shot = loaded.shots[1].model_copy(
        update={
            "duration_policy": DurationPolicy(
                mode="content_driven", minimum_seconds=1.4, maximum_seconds=1.6
            )
        }
    )
    loaded = loaded.model_copy(update={"shots": (loaded.shots[0], loaded_shot)})
    spec = _with_map(
        spec,
        layer_index=1,
        time_map=_time_map((0, 0), (60, 36)),
    )

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.total_frames == 84
    assert timeline.visual_spans[0].duration_frames == 48
    mapped = tuple(item for item in timeline.visual_spans if item.shot_id == "shot-2")
    assert len(mapped) == 36
    assert tuple(item.start_frame for item in mapped) == tuple(range(48, 84))
    assert tuple(item.trim_start_frame for item in mapped) == tuple(
        12 + (index * 60) // 36 for index in range(36)
    )
    assert all(
        item.duration_frames == item.trim_duration_frames == 1 for item in mapped
    )


def test_timeline_usage_scope_is_versioned_and_preserved_in_23(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec, shot_index=1)
    spec = _with_map(
        spec,
        layer_index=1,
        time_map=_time_map((0, 0), (60, 48)),
    )
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    preview = seal_artifact(
        timeline.model_copy(
            update={"content_hash": "0" * 64, "usage_scope": "development_preview"}
        )
    )

    reopened = ResolvedTimeline.model_validate(preview.model_dump(mode="python"))

    assert reopened.usage_scope == "development_preview"
    legacy_payload = timeline.model_dump(mode="python")
    legacy_payload.update(schema_version="2.2", usage_scope="development_preview")
    with pytest.raises(ValidationError, match="requires ResolvedTimeline 2.3"):
        ResolvedTimeline.model_validate(legacy_payload)


def test_composition_23_retains_existing_p4_audio_and_caption_projection(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    spec = _reseal(spec, schema_version="2.3")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.schema_version == "2.3"
    assert len(timeline.audio_spans) == 5
    assert len(timeline.caption_cues) == 2


@pytest.mark.parametrize("schema", ["2.0", "2.1", "2.2"])
def test_legacy_composition_versions_reject_time_maps(tmp_path, schema):
    _loaded, spec = make_loaded_project_and_spec(tmp_path)
    layer = spec.layers[0].model_dump(mode="python")
    layer["source_time_map"] = _time_map((0, 0), (60, 48)).model_dump(mode="python")
    payload = spec.model_dump(mode="python")
    payload.update(schema_version=schema, layers=(layer, *payload["layers"][1:]))

    with pytest.raises(ValidationError):
        CompositionSpec.model_validate(payload)


@pytest.mark.parametrize(
    ("time_map", "trim_duration"),
    [
        (_time_map((0, 0), (60, 47)), 60),
        (_time_map((0, 0), (59, 48)), 60),
    ],
)
def test_map_endpoints_must_match_output_and_selected_source_trim(
    tmp_path, time_map, trim_duration
):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, trim_duration_frames=trim_duration
    )
    spec = _with_map(spec, layer_index=0, time_map=time_map)

    with pytest.raises(AiVideoError, match="time map|source trim"):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_time_map_rejects_raster_layers_and_source_overrun(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    mapped_raster = _with_map(
        spec, layer_index=0, time_map=_time_map((0, 0), (60, 48))
    )
    with pytest.raises(AiVideoError, match="video|raster"):
        resolve_composition(loaded, mapped_raster, renderer_version="0.7.103")

    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, trim_start_frame=12, trim_duration_frames=60
    )
    mapped_overrun = _with_map(
        spec, layer_index=0, time_map=_time_map((0, 0), (61, 48))
    )
    with pytest.raises(AiVideoError, match="time map|source trim|exceed"):
        resolve_composition(loaded, mapped_overrun, renderer_version="0.7.103")


@pytest.mark.parametrize("binding_kind", ["audio", "caption", "voice"])
def test_retimed_shot_rejects_same_shot_audio_coupling(tmp_path, binding_kind):
    _loaded, spec = make_loaded_project_and_spec(tmp_path)
    layer = spec.layers[1].model_copy(
        update={"source_time_map": _time_map((0, 0), (60, 48))}
    )
    changes = {
        "schema_version": "2.3",
        "layers": (spec.layers[0], layer),
    }
    if binding_kind == "audio":
        changes["audio_tracks"] = (
            AudioTrackSpec(
                track_id="shot-2-ambience",
                audio_kind=AudioKind.AMBIENCE,
                asset_id="missing-audio",
                shot_id="shot-2",
            ),
        )
    elif binding_kind == "caption":
        style_hash = "a" * 64
        changes["caption_tracks"] = (
            CaptionTrackBinding(
                binding_id="shot-2-captions",
                caption_asset_id="missing-captions",
                source_audio_track_id="missing-audio",
                shot_id="shot-2",
                style_reference=CaptionStyleReference(
                    artifact_id="caption-style",
                    revision=1,
                    content_hash=style_hash,
                    path=Path(f"assets/styles/{style_hash}.json"),
                ),
            ),
        )
    else:
        binding_hash = "b" * 64
        changes["voice_sources"] = (
            VoiceCompositionSource(
                shot_id="shot-2",
                source_project_file=Path("/tmp/source/project.yaml"),
                execution_binding=GenerationExecutionBindingPointer(
                    path=Path(
                        "state/video-generation/decision-bindings/"
                        f"{binding_hash}.json"
                    ),
                    binding_hash=binding_hash,
                    request_fingerprint="c" * 64,
                    file_sha256="d" * 64,
                ),
            ),
        )

    with pytest.raises(ValidationError, match="muted|audio|caption|voice"):
        CompositionSpec.model_validate(
            seal_artifact(spec.model_copy(update={"content_hash": "0" * 64, **changes}))
            .model_dump(mode="python")
        )
