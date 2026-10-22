"""Composition-time checks for an explicit visual source-audio choice."""

from __future__ import annotations

from fractions import Fraction

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition_contracts import (
    AudioKind,
    CompositionLayerSpec,
    CompositionSpec,
    ResolvedAudioSpan,
    ResolvedTimeline,
    ResolvedVisualSpan,
)
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    VideoAssetMetadata,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_video_probe_receipt_path,
)
from ai_video.production.video_artifact import VideoProbeReceipt


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.AUDIO_TIMELINE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _probe_stream_count(
    project: LoadedProductionProject, asset: AssetRecord
) -> int | None:
    """Return stream count only when the source probe is exact and reopened."""
    metadata = asset.video_metadata
    if metadata is None:
        return None

    from ai_video.production.repair_input_admission import (
        is_repair_input_record,
        verify_repair_input,
    )

    if is_repair_input_record(asset, project.root):
        try:
            admission = verify_repair_input(asset, project.root)
        except (OSError, ValueError, ValidationError) as exc:
            raise _invalid(
                f"Development video {asset.asset_id} source-audio evidence is invalid.",
                str(exc),
            ) from exc
        if admission.contract_version in {"development-repair-input/4", "development-repair-input/5"}:
            # These owners verify the local derivative's bytes and metadata.
            # preview_probe intentionally describes the original Provider file.
            measured = (admission.cleanup.output if admission.contract_version.endswith("/4")
                        else admission.viewing.output)
            return measured.audio_stream_count
        probe = getattr(admission, "preview_probe", None)
        if probe is None:
            return None
    elif asset.source_kind is AssetSourceKind.IMPORTED:
        # Ordinary imports have measured visual metadata, not a VideoProbeReceipt.
        return None
    else:
        try:
            receipt_path = canonical_video_probe_receipt_path(
                metadata.probe_receipt_id
            )
        except ValueError:
            return None
        path = project.root / receipt_path
        try:
            raw = _read_regular_file_nofollow(
                path,
                contained_by=project.root / "state",
            )
        except FileNotFoundError:
            # Old registry snapshots may predate retained probe receipts.
            return None
        except (OSError, ValueError) as exc:
            raise _invalid(
                f"Video {asset.asset_id} source-audio probe could not be reopened safely.",
                str(exc),
            ) from exc
        try:
            probe = VideoProbeReceipt.model_validate_json(raw.data)
        except (ValidationError, ValueError) as exc:
            raise _invalid(
                f"Video {asset.asset_id} source-audio probe is invalid.", str(exc)
            ) from exc

    if not _probe_matches_asset(probe, asset, metadata):
        raise _invalid(
            f"Video {asset.asset_id} source-audio probe does not match its exact bytes and metadata."
        )
    return probe.measured.audio_stream_count


def _probe_matches_asset(
    probe: VideoProbeReceipt, asset: AssetRecord, metadata: VideoAssetMetadata
) -> bool:
    measured = probe.measured
    return (
        probe.content_hash == metadata.probe_receipt_id
        and probe.request_receipt_fingerprint == metadata.request_receipt_fingerprint
        and probe.resolved_generation_hash == metadata.resolved_generation_hash
        and measured.artifact_sha256 == asset.sha256
        and measured.size_bytes == asset.size_bytes
        and measured.container_name == metadata.container_name
        and measured.codec_name == metadata.codec_name
        and measured.width == metadata.width
        and measured.height == metadata.height
        and measured.fps_numerator == metadata.fps_numerator
        and measured.fps_denominator == metadata.fps_denominator
        and measured.duration_milliseconds == metadata.duration_milliseconds
        and measured.frame_count == metadata.frame_count
    )


def _grouped_visual_spans(
    timeline: ResolvedTimeline, layer_id: str
) -> tuple[ResolvedVisualSpan, ...]:
    prefix = layer_id + "--retime-"
    return tuple(
        span
        for span in timeline.visual_spans
        if span.layer_id == layer_id
        or (
            span.layer_id.startswith(prefix)
            and span.layer_id[len(prefix) :].isdigit()
        )
    )


def _visual_window(
    layer: CompositionLayerSpec,
    asset: AssetRecord,
    spans: tuple[ResolvedVisualSpan, ...],
) -> tuple[int, int]:
    if not spans or any(
        span.shot_id != layer.shot_id
        or span.asset_id != asset.asset_id
        or span.asset_sha256 != asset.sha256
        for span in spans
    ):
        raise _invalid(
            f"Video layer {layer.layer_id} has no exact grouped visual spans."
        )
    ordered = sorted(spans, key=lambda span: span.start_sample)
    start = ordered[0].start_sample
    end = ordered[0].start_sample + ordered[0].duration_samples
    for span in ordered[1:]:
        if span.start_sample != end:
            raise _invalid(
                f"Video layer {layer.layer_id} visual spans are not continuous."
            )
        end += span.duration_samples
    if end <= start:
        raise _invalid(f"Video layer {layer.layer_id} has an empty visual interval.")
    return start, end


def _audio_asset_by_id(
    project: LoadedProductionProject, span: ResolvedAudioSpan
) -> AssetRecord | None:
    asset = next(
        (item for item in project.registry.assets if item.asset_id == span.asset_id),
        None,
    )
    if (
        asset is None
        or asset.sha256 != span.asset_sha256
        or asset.audio_metadata is None
        or asset.asset_type not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}
    ):
        return None
    return asset


def _source_audio_asset_matches(
    audio: AssetRecord,
    video: AssetRecord,
    *,
    usage_scope: str,
) -> bool:
    metadata = audio.audio_metadata
    if metadata is None:
        return False
    source = metadata.source
    if usage_scope == "development_audio_preview":
        return (
            audio.source_kind is AssetSourceKind.DERIVED
            and source.kind is AssetSourceKind.DERIVED
            and audio.input_artifact_ids == (video.asset_id,)
            and source.input_artifact_ids == (video.asset_id,)
            and audio.input_fingerprint == video.sha256
            and source.input_fingerprint == video.sha256
        )
    return (
        usage_scope == "production"
        and audio.source_kind is AssetSourceKind.GENERATED
        and audio.creation_receipt_id.startswith("generated-video-audio-")
        and source.kind is AssetSourceKind.GENERATED
        and audio.input_artifact_ids == ()
        and source.input_artifact_ids == ()
        and audio.input_fingerprint == video.sha256
        and source.input_fingerprint == video.sha256
    )


def _native_span_matches(
    span: ResolvedAudioSpan,
    layer: CompositionLayerSpec,
    asset: AssetRecord,
    visual_start: int,
    visual_end: int,
) -> bool:
    mapping = span.native_audio_retime
    return (
        span.audio_kind is AudioKind.NATIVE_VIDEO
        and mapping is not None
        and mapping.visual_layer_id == layer.layer_id
        and span.asset_id == asset.asset_id
        and span.asset_sha256 == asset.sha256
        and span.gain_millidb == 0
        and span.start_sample <= visual_start
        and span.start_sample + span.duration_samples >= visual_end
        and sum(segment.output_duration_samples for segment in mapping.segments)
        == span.duration_samples
    )


def _normal_speed(layer: CompositionLayerSpec) -> bool:
    mapping = layer.source_time_map
    if mapping is None:
        return True
    return all(
        right.source_frame - left.source_frame
        == right.output_frame - left.output_frame
        for left, right in zip(mapping.points, mapping.points[1:])
    )


def _expected_source_trim(
    layer: CompositionLayerSpec,
    video: AssetRecord,
    timeline: ResolvedTimeline,
    sample_rate: int,
    visual_spans: tuple[ResolvedVisualSpan, ...],
) -> tuple[int, int] | None:
    metadata = video.video_metadata
    if metadata is None or not _normal_speed(layer):
        return None
    if layer.source_time_map is not None:
        source_frames = layer.source_time_map.source_duration_frames
    elif layer.trim_duration_frames is not None:
        source_frames = layer.trim_duration_frames
    else:
        source_frames = sum(span.duration_frames for span in visual_spans)

    if timeline.usage_scope == "development_audio_preview":
        fps = Fraction(timeline.delivery_profile.fps, 1)
    else:
        fps = Fraction(metadata.fps_numerator, metadata.fps_denominator)

    start_frame = layer.trim_start_frame
    start = start_frame * sample_rate * fps.denominator // fps.numerator
    end_frame = start_frame + source_frames
    end = end_frame * sample_rate * fps.denominator // fps.numerator
    return start, end - start


def _kept_p4_span_matches(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    timeline: ResolvedTimeline,
    layer: CompositionLayerSpec,
    video: AssetRecord,
    visual_spans: tuple[ResolvedVisualSpan, ...],
    visual_start: int,
    visual_end: int,
) -> bool:
    expected_trim = _expected_source_trim(
        layer, video, timeline, spec.sample_rate, visual_spans
    )
    if expected_trim is None:
        return False
    tracks_by_id = {track.track_id: track for track in spec.audio_tracks}
    for span in timeline.audio_spans:
        if span.audio_kind is AudioKind.NATIVE_VIDEO:
            continue
        track = tracks_by_id.get(span.track_id)
        audio = _audio_asset_by_id(project, span)
        if (
            track is None
            or audio is None
            or (track.shot_id is not None and track.shot_id != layer.shot_id)
            or not _source_audio_asset_matches(
                audio, video, usage_scope=timeline.usage_scope
            )
            or span.gain_millidb <= -96_000
            or span.start_sample > visual_start
            or span.start_sample + span.duration_samples < visual_end
            or span.source_start_sample + (visual_start - span.start_sample)
            != expected_trim[0]
            or span.source_start_sample + span.source_duration_samples
            < expected_trim[0] + expected_trim[1]
        ):
            continue
        return True
    return False


def _replacement_span_covers(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    timeline: ResolvedTimeline,
    layer: CompositionLayerSpec,
    visual_start: int,
    visual_end: int,
) -> bool:
    tracks_by_id = {track.track_id: track for track in spec.audio_tracks}
    for span in timeline.audio_spans:
        if span.audio_kind is AudioKind.NATIVE_VIDEO:
            continue
        track = tracks_by_id.get(span.track_id)
        audio = _audio_asset_by_id(project, span)
        if (
            track is None
            or audio is None
            or (track.shot_id is not None and track.shot_id != layer.shot_id)
            or span.gain_millidb <= -96_000
            or span.start_sample > visual_start
            or span.start_sample + span.duration_samples < visual_end
        ):
            continue
        if span.fade_in_samples + span.fade_out_samples >= span.duration_samples:
            continue
        return True
    return False


def require_source_audio(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    timeline: ResolvedTimeline,
) -> None:
    """Require each known kept source track to reach the single resolved timeline."""
    assets = {item.asset_id: item for item in project.registry.assets}
    for layer in spec.layers:
        video = assets.get(layer.asset_id)
        if video is None or video.asset_type is not AssetType.VIDEO:
            continue

        policy = layer.source_audio_policy
        if policy in {"MUTE", "REPLACE"} and (
            layer.source_time_map is not None
            and layer.source_time_map.audio_policy == "retime_preserve_pitch"
        ):
            raise _invalid(
                f"Video layer {layer.layer_id} source-audio policy conflicts with its native retime."
            )

        if policy == "MUTE":
            continue

        visual_spans = _grouped_visual_spans(timeline, layer.layer_id)
        visual_start, visual_end = _visual_window(layer, video, visual_spans)

        if policy == "REPLACE":
            if not _replacement_span_covers(
                project, spec, timeline, layer, visual_start, visual_end
            ):
                raise _invalid(
                    f"Video layer {layer.layer_id} requires a P4 replacement audio span covering its full visual interval."
                )
            continue

        stream_count = _probe_stream_count(project, video)
        if policy is None:
            # Old imports without a sealed source-audio choice remain readable;
            # exact source evidence below opts newer compositions into the guard.
            if stream_count is None or stream_count == 0:
                continue
            policy = "KEEP"
        if policy != "KEEP":
            continue
        if stream_count is not None and stream_count > 1:
            raise _invalid(
                f"Video layer {layer.layer_id} has multiple native audio streams and cannot default to KEEP."
            )
        native_match = any(
            _native_span_matches(
                span, layer, video, visual_start, visual_end
            )
            for span in timeline.audio_spans
        )
        p4_match = _kept_p4_span_matches(
            project,
            spec,
            timeline,
            layer,
            video,
            visual_spans,
            visual_start,
            visual_end,
        )
        if native_match or p4_match:
            continue
        if stream_count == 0:
            continue
        if stream_count is None:
            raise _invalid(
                f"Video layer {layer.layer_id} explicitly keeps source audio but has no exact source-audio evidence or linked audio span."
            )
        raise _invalid(
            f"Video layer {layer.layer_id} source contains audio but no exact native or same-source P4 span covers it."
        )
