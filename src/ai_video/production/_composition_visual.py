from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ai_video.errors import AiVideoError
from ai_video.production.ad_composition import classify_composition_layer
from ai_video.production.commercial_graphics import GraphicLayerAnimation
from ai_video.production.composition_contracts import (
    CompositionLayerSpec,
    CompositionSpec,
    ResolvedVisualSpan,
    TransitionSpec,
)
from ai_video.production.models import (
    LoadedProductionProject,
    Shot,
)
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.video_retime import (
    resolve_video_time_segments,
    resolve_video_time_source_frames,
)
from ai_video.production.visual_media import (
    VisualMediaValidationError,
    resolved_video_trim_duration,
    validated_visual_suffix,
)


@dataclass(frozen=True)
class _VisualSegment:
    layer_id: str
    start_frame: int
    duration_frames: int
    trim_start_frame: int
    trim_duration_frames: int | None
    incoming_transition: TransitionSpec | None


def resolve_preview_layer_ids(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    shots_by_id: Mapping[str, Shot],
    *,
    invalid: Callable[..., AiVideoError],
) -> set[str]:
    preview_layer_ids: set[str] = set()
    preview_scopes: set[str] = set()
    roles_by_shot = {
        shot_id: {role.role: role for role in shots_by_id[shot_id].required_asset_roles}
        for shot_id in spec.shot_ids
        if shot_id in shots_by_id
    }
    for layer in spec.layers:
        shot = shots_by_id.get(layer.shot_id)
        if shot is None:
            continue
        role = roles_by_shot.get(layer.shot_id, {}).get(layer.asset_role)
        if role is None or layer.asset_id in role.asset_ids:
            continue
        from ai_video.production.repair_input_admission import (
            allows_repair_preview_layer,
            verify_repair_input,
        )

        if allows_repair_preview_layer(project, layer, shot):
            preview_layer_ids.add(layer.layer_id)
            asset = next(a for a in project.registry.assets if a.asset_id == layer.asset_id)
            preview_scopes.add(verify_repair_input(asset, project.root).preview_use.scope)
    if preview_layer_ids:
        if spec.schema_version not in {"2.3", "2.4"}:
            raise invalid("Development repair previews require CompositionSpec 2.3 or 2.4.")
        if "replacement_audio_preview" in preview_scopes:
            if (spec.schema_version != "2.3" or preview_scopes != {"replacement_audio_preview"} or not spec.audio_tracks
                    or any(t.audio_kind.value not in {"bgm", "sfx", "ambience"} for t in spec.audio_tracks)
                    or spec.caption_tracks or spec.voice_sources):
                raise invalid("Replacement audio preview requires explicit P4 music/SFX/ambience only.")
        elif spec.audio_tracks or spec.caption_tracks or spec.voice_sources:
            raise invalid(
                "Development repair previews cannot contain audio, captions, or voice sources."
            )
    return preview_layer_ids


def _segments_for_layer(
    layer: CompositionLayerSpec,
    *,
    duration_frames: int,
    trim_duration_frames: int | None,
    start_frame: int,
    incoming_transition: TransitionSpec | None,
) -> tuple[_VisualSegment, ...]:
    if layer.source_time_map is None:
        return (
            _VisualSegment(
                layer_id=layer.layer_id,
                start_frame=start_frame,
                duration_frames=duration_frames,
                trim_start_frame=layer.trim_start_frame,
                trim_duration_frames=trim_duration_frames,
                incoming_transition=incoming_transition,
            ),
        )
    resolved: list[_VisualSegment] = []
    first = True
    for segment in resolve_video_time_segments(layer.source_time_map):
        if segment.source_duration_frames == segment.output_duration_frames:
            output_offset = segment.output_start_frame
            resolved.append(
                _VisualSegment(
                    layer_id=_retime_span_id(layer.layer_id, output_offset),
                    start_frame=start_frame + output_offset,
                    duration_frames=segment.output_duration_frames,
                    trim_start_frame=(
                        layer.trim_start_frame + segment.source_start_frame
                    ),
                    trim_duration_frames=segment.source_duration_frames,
                    incoming_transition=incoming_transition if first else None,
                )
            )
            first = False
            continue
        for sample_offset, source_frame in enumerate(
            resolve_video_time_source_frames(segment)
        ):
            output_offset = segment.output_start_frame + sample_offset
            resolved.append(
                _VisualSegment(
                    layer_id=_retime_span_id(layer.layer_id, output_offset),
                    start_frame=start_frame + output_offset,
                    duration_frames=1,
                    trim_start_frame=layer.trim_start_frame + source_frame,
                    trim_duration_frames=1,
                    incoming_transition=incoming_transition if first else None,
                )
            )
            first = False
    return tuple(resolved)


def _retime_span_id(layer_id: str, output_offset: int) -> str:
    if output_offset == 0:
        return layer_id
    return f"{layer_id}--retime-{output_offset + 1}"


def resolve_shot_visual_spans(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    shot: Shot,
    layers: Sequence[CompositionLayerSpec],
    *,
    duration_frames: int,
    start_frame: int,
    incoming_transition: TransitionSpec | None,
    preview_layer_ids: set[str],
    graphic_layer_ids: set[str],
    graphic_animation_by_layer: Mapping[str, GraphicLayerAnimation],
    sample_at_frame: Callable[[int], int],
    invalid: Callable[..., AiVideoError],
) -> tuple[ResolvedVisualSpan, ...]:
    if not layers:
        raise invalid(f"Shot {shot.shot_id} has no CompositionSpec layer.")
    z_values = [item.z_index for item in layers]
    if len(z_values) != len(set(z_values)):
        raise invalid(f"Shot {shot.shot_id} has duplicate z_index values.")
    if all(item.layer_id in graphic_layer_ids for item in layers):
        raise invalid(f"Shot {shot.shot_id} requires a primary visual layer.")

    assets_by_id = {item.asset_id: item for item in project.registry.assets}
    roles = {item.role: item for item in shot.required_asset_roles}
    spans: list[ResolvedVisualSpan] = []
    for layer in sorted(layers, key=lambda item: (item.z_index, item.layer_id)):
        asset = assets_by_id.get(layer.asset_id)
        source_path = project.asset_paths.get(layer.asset_id)
        if asset is None or source_path is None:
            raise invalid(f"Layer {layer.layer_id} references an unregistered asset.")
        role = roles.get(layer.asset_role)
        if role is None or (
            layer.asset_id not in role.asset_ids
            and layer.layer_id not in preview_layer_ids
        ):
            raise invalid(
                f"Layer {layer.layer_id} is not bound to its declared Shot asset role."
            )
        is_video, is_graphic_layer, expected_type = classify_composition_layer(
            visual_strategy=shot.visual_strategy,
            layer_id=layer.layer_id,
            graphic_layer_ids=graphic_layer_ids,
        )
        if expected_type not in role.allowed_asset_types or asset.asset_type is not expected_type:
            raise invalid(
                f"Layer {layer.layer_id} must bind a registry {expected_type.value} asset."
            )
        if layer.source_time_map is not None and (
            not is_video or is_graphic_layer or asset.mime_type != "video/mp4"
        ):
            raise invalid(
                f"Layer {layer.layer_id} time mapping requires a primary video asset."
            )
        if layer.source_time_map is not None:
            if spec.schema_version not in {"2.3", "2.4"}:
                raise invalid("Video time mapping requires CompositionSpec 2.3 or 2.4.")
            if layer.source_time_map.output_duration_frames != duration_frames:
                raise invalid(
                    f"Layer {layer.layer_id} time map output endpoint must equal its Shot duration."
                )
            if (
                layer.trim_duration_frames is not None
                and layer.trim_duration_frames
                != layer.source_time_map.source_duration_frames
            ):
                raise invalid(
                    f"Layer {layer.layer_id} time map source endpoint must equal its selected source trim."
                )
        if is_video and not is_graphic_layer:
            try:
                trim_duration_frames = resolved_video_trim_duration(
                    asset,
                    layer,
                    duration_frames=duration_frames,
                    delivery_profile=spec.delivery_profile,
                )
            except VisualMediaValidationError as exc:
                raise invalid(str(exc)) from exc
        else:
            if layer.trim_start_frame != 0 or layer.trim_duration_frames is not None:
                raise invalid("P3 static raster layers do not implement trim.")
            trim_duration_frames = None

        if asset.artifact_path.is_absolute() or ".." in asset.artifact_path.parts:
            raise invalid(f"Asset path is not clean: {asset.asset_id}.")
        registered_path = project.root / asset.artifact_path
        if Path(source_path) != registered_path:
            raise invalid(f"Loaded asset path does not match registry path: {asset.asset_id}.")
        source_snapshot = _read_regular_file_nofollow(
            registered_path,
            contained_by=project.root,
        )
        if (
            source_snapshot.file_sha256 != asset.sha256
            or source_snapshot.size_bytes != asset.size_bytes
        ):
            raise invalid(f"Asset bytes changed before timeline resolution: {asset.asset_id}.")
        try:
            suffix = validated_visual_suffix(
                source_snapshot.data,
                suffix=registered_path.suffix,
                mime_type=asset.mime_type,
            )
        except VisualMediaValidationError as exc:
            raise invalid(str(exc)) from exc
        logical_path = Path("assets") / f"{asset.sha256}{suffix}"
        segments = _segments_for_layer(
            layer,
            duration_frames=duration_frames,
            trim_duration_frames=trim_duration_frames,
            start_frame=start_frame,
            incoming_transition=incoming_transition,
        )
        for segment in segments:
            segment_end_frame = segment.start_frame + segment.duration_frames
            segment_start_sample = sample_at_frame(segment.start_frame)
            segment_end_sample = sample_at_frame(segment_end_frame)
            spans.append(
                ResolvedVisualSpan(
                    layer_id=segment.layer_id,
                    shot_id=shot.shot_id,
                    asset_role=layer.asset_role,
                    asset_id=asset.asset_id,
                    asset_sha256=asset.sha256,
                    asset_mime_type=asset.mime_type,
                    materialized_path=logical_path,
                    start_frame=segment.start_frame,
                    duration_frames=segment.duration_frames,
                    start_sample=segment_start_sample,
                    duration_samples=segment_end_sample - segment_start_sample,
                    trim_start_frame=segment.trim_start_frame,
                    trim_duration_frames=segment.trim_duration_frames,
                    transform=layer.transform,
                    opacity_milli=layer.opacity_milli,
                    z_index=layer.z_index,
                    incoming_transition=segment.incoming_transition,
                    graphic_animation=graphic_animation_by_layer.get(layer.layer_id),
                )
            )
    return tuple(spans)
