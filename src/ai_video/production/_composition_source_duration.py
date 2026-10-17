from __future__ import annotations

from decimal import Decimal

from ai_video.production.models import (
    AssetType, CompositionSpec, LoadedProductionProject, Shot, VisualStrategy,
)
from ai_video.production.visual_media import (
    VisualMediaValidationError, resolved_video_trim_duration,
)


def content_driven_video_frames(
    project: LoadedProductionProject, spec: CompositionSpec, shot: Shot,
) -> int:
    """Resolve a selected primary video's real interval within the composition owner."""
    layers = [layer for layer in spec.layers if layer.shot_id == shot.shot_id
              and layer.layer_id not in spec.graphic_layer_ids]
    if shot.visual_strategy not in {
        VisualStrategy.GENERATED_VIDEO, VisualStrategy.EXISTING_VIDEO,
    } or len(layers) != 1:
        raise VisualMediaValidationError(
            f"Content-driven Shot {shot.shot_id} requires one primary video layer."
        )
    layer = layers[0]
    asset = next((item for item in project.registry.assets
                  if item.asset_id == layer.asset_id), None)
    role = next((item for item in shot.required_asset_roles
                 if item.role == layer.asset_role), None)
    if (asset is None or asset.asset_type is not AssetType.VIDEO
            or asset.video_metadata is None or role is None
            or asset.asset_id not in role.asset_ids
            or AssetType.VIDEO not in role.allowed_asset_types):
        raise VisualMediaValidationError(
            f"Content-driven Shot {shot.shot_id} has no bound video metadata."
        )
    if layer.source_time_map is not None:
        frames = layer.source_time_map.output_duration_frames
    else:
        frames = layer.trim_duration_frames
        if frames is None:
            frames = asset.video_metadata.frame_count - layer.trim_start_frame
    if frames <= 0:
        raise VisualMediaValidationError("Content-driven video interval is empty.")
    resolved_video_trim_duration(
        asset, layer, duration_frames=frames, delivery_profile=spec.delivery_profile,
    )
    seconds = Decimal(frames) / Decimal(spec.delivery_profile.fps)
    policy = shot.duration_policy
    if ((policy.minimum_seconds is not None
         and seconds < Decimal(str(policy.minimum_seconds)))
            or (policy.maximum_seconds is not None
                and seconds > Decimal(str(policy.maximum_seconds)))):
        raise VisualMediaValidationError(
            f"Content-driven Shot {shot.shot_id} violates its duration bounds."
        )
    return frames
