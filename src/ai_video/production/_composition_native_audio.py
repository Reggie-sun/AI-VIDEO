"""Derive native video-audio spans from the canonical visual time map."""
from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

from ai_video.errors import AiVideoError
from ai_video.production.audio_retime_contracts import AudioTimeSegment, NativeAudioRetime
from ai_video.production.composition_contracts import (
    AUDIO_KIND_PRIORITY,
    AudioKind,
    CompositionSpec,
    ResolvedAudioSpan,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetRecord, AssetSourceKind, LoadedProductionProject
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_video_probe_receipt_path,
)
from ai_video.production.video_artifact import VideoProbeReceipt


def _native_audio_probe(
    project: LoadedProductionProject,
    asset: AssetRecord,
    *,
    invalid: Callable[..., AiVideoError],
) -> VideoProbeReceipt | None:
    metadata = asset.video_metadata
    if metadata is None:
        raise invalid(f"Mapped video asset {asset.asset_id} has no exact probe identity.")

    from ai_video.production.repair_input_admission import (
        is_repair_input_record,
        verify_repair_input,
    )

    if is_repair_input_record(asset, project.root):
        try:
            admission = verify_repair_input(asset, project.root)
        except (OSError, ValueError) as exc:
            raise invalid("Mapped development video admission is invalid.", str(exc)) from exc
        if admission.contract_version != "development-repair-input/3":
            raise invalid("Native audio preview requires development-repair-input/3.")
        probe = admission.preview_probe
    elif asset.source_kind is AssetSourceKind.IMPORTED:
        # Ordinary imports carry Registry measurements, not generation receipts.
        # The materializer verifies the held MP4's unique audio stream before P4.
        # Repair provenance must take the strict branch above even when imported.
        return None
    else:
        path = project.root / canonical_video_probe_receipt_path(metadata.probe_receipt_id)
        try:
            raw = _read_regular_file_nofollow(path, contained_by=project.root / "state")
            probe = VideoProbeReceipt.model_validate_json(raw.data)
        except (OSError, ValueError) as exc:
            raise invalid("Mapped video probe could not be reopened safely.", str(exc)) from exc

    measured = probe.measured
    if (
        probe.content_hash != metadata.probe_receipt_id
        or probe.request_receipt_fingerprint != metadata.request_receipt_fingerprint
        or probe.resolved_generation_hash != metadata.resolved_generation_hash
        or measured.artifact_sha256 != asset.sha256
        or measured.size_bytes != asset.size_bytes
        or measured.container_name != "mp4"
        or measured.codec_name != metadata.codec_name
        or measured.width != metadata.width
        or measured.height != metadata.height
        or measured.fps_numerator != metadata.fps_numerator
        or measured.fps_denominator != metadata.fps_denominator
        or measured.duration_milliseconds != metadata.duration_milliseconds
        or measured.frame_count != metadata.frame_count
        or measured.audio_stream_count != 1
    ):
        raise invalid("Native audio requires the exact video probe with one audio stream.")
    return probe


def resolve_native_audio_spans(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    *,
    shot_start_samples: dict[str, int],
    sample_at_frame: Callable[..., int],
    invalid: Callable[..., AiVideoError],
) -> tuple[ResolvedAudioSpan, ...]:
    """Create one sample-mapped P4 source for each v2 visual layer."""
    layers = tuple(
        layer
        for layer in spec.layers
        if layer.source_time_map is not None
        and layer.source_time_map.contract_version == "video-time-map/2"
    )
    if not layers:
        return ()

    assets_by_id = {item.asset_id: item for item in project.registry.assets}
    track_ids = {track.track_id for track in spec.audio_tracks}
    spans: list[ResolvedAudioSpan] = []
    for layer in layers:
        mapping = layer.source_time_map
        assert mapping is not None
        track_id = f"native-video-audio::{layer.layer_id}"
        if track_id in track_ids:
            raise invalid(f"Native audio track ID collides with authored audio: {track_id}.")
        track_ids.add(track_id)
        asset = assets_by_id.get(layer.asset_id)
        if asset is None or asset.mime_type != "video/mp4" or asset.video_metadata is None:
            raise invalid(f"Mapped layer {layer.layer_id} requires an exact VIDEO asset.")
        _native_audio_probe(project, asset, invalid=invalid)

        source_fps = Fraction(
            asset.video_metadata.fps_numerator,
            asset.video_metadata.fps_denominator,
        )
        segments: list[AudioTimeSegment] = []
        for left, right in zip(mapping.points, mapping.points[1:]):
            source_start = sample_at_frame(
                layer.trim_start_frame + left.source_frame,
                fps=source_fps,
                sample_rate=spec.sample_rate,
            )
            source_end = sample_at_frame(
                layer.trim_start_frame + right.source_frame,
                fps=source_fps,
                sample_rate=spec.sample_rate,
            )
            output_start = sample_at_frame(
                left.output_frame,
                fps=spec.delivery_profile.fps,
                sample_rate=spec.sample_rate,
            )
            output_end = sample_at_frame(
                right.output_frame,
                fps=spec.delivery_profile.fps,
                sample_rate=spec.sample_rate,
            )
            if source_end <= source_start or output_end <= output_start:
                raise invalid(f"Mapped layer {layer.layer_id} resolves an empty audio segment.")
            segments.append(
                AudioTimeSegment(
                    source_start_sample=source_start,
                    source_duration_samples=source_end - source_start,
                    output_offset_sample=output_start,
                    output_duration_samples=output_end - output_start,
                )
            )

        native = NativeAudioRetime(
            visual_layer_id=layer.layer_id,
            stream_index=0,
            time_map_sha256=canonical_sha256(mapping.model_dump(mode="json")),
            segments=tuple(segments),
        )
        output_duration = sum(item.output_duration_samples for item in segments)
        source_start = segments[0].source_start_sample
        source_end = segments[-1].source_start_sample + segments[-1].source_duration_samples
        spans.append(
            ResolvedAudioSpan(
                track_id=track_id,
                audio_kind=AudioKind.NATIVE_VIDEO,
                asset_id=asset.asset_id,
                asset_sha256=asset.sha256,
                start_sample=shot_start_samples[layer.shot_id],
                duration_samples=output_duration,
                source_start_sample=source_start,
                source_duration_samples=source_end - source_start,
                gain_millidb=0,
                fade_in_samples=0,
                fade_out_samples=0,
                native_audio_retime=native,
            )
        )
    return tuple(
        sorted(
            spans,
            key=lambda item: (
                AUDIO_KIND_PRIORITY[item.audio_kind],
                item.track_id,
                item.start_sample,
                item.asset_id,
            ),
        )
    )
