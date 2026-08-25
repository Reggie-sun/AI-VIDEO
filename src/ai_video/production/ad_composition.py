from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.commercial_graphics import ResolvedCommercialGraphic
from ai_video.production.models import AssetType, CompositionSpec, VisualStrategy


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.COMPOSITION_INVALID,
        user_message=message,
        retryable=False,
    )


def classify_composition_layer(
    *,
    visual_strategy: VisualStrategy,
    layer_id: str,
    graphic_layer_ids: set[str],
) -> tuple[bool, bool, AssetType]:
    is_video = visual_strategy in {
        VisualStrategy.GENERATED_VIDEO,
        VisualStrategy.EXISTING_VIDEO,
    }
    is_graphic_layer = layer_id in graphic_layer_ids
    expected_type = (
        AssetType.IMAGE
        if is_graphic_layer
        else AssetType.VIDEO if is_video else AssetType.IMAGE
    )
    return is_video, is_graphic_layer, expected_type


def resolve_commercial_graphics(
    spec: CompositionSpec,
    *,
    shot_start_frames: dict[str, int],
    duration_frames_by_shot: dict[str, int],
) -> tuple[ResolvedCommercialGraphic, ...]:
    resolved: list[ResolvedCommercialGraphic] = []
    for graphic in spec.commercial_graphics:
        shot_start = shot_start_frames.get(graphic.shot_id)
        shot_duration = duration_frames_by_shot.get(graphic.shot_id)
        if shot_start is None or shot_duration is None:
            raise _invalid("Commercial graphic references an unordered Shot.")
        end_offset = graphic.start_frame_offset + graphic.duration_frames
        if end_offset > shot_duration:
            raise _invalid("Commercial graphic exceeds its resolved Shot interval.")
        start_frame = shot_start + graphic.start_frame_offset
        end_frame = shot_start + end_offset
        resolved.append(
            ResolvedCommercialGraphic(
                graphic_id=graphic.graphic_id,
                role=graphic.role,
                text=graphic.text,
                shot_id=graphic.shot_id,
                start_frame=start_frame,
                end_frame_exclusive=end_frame,
                start_sample=start_frame * spec.sample_rate // spec.delivery_profile.fps,
                end_sample=end_frame * spec.sample_rate // spec.delivery_profile.fps,
                x_milli=graphic.x_milli,
                y_milli=graphic.y_milli,
                width_milli=graphic.width_milli,
                font_size_px=graphic.font_size_px,
                text_color=graphic.text_color,
                background_color=graphic.background_color,
                claim_reference_ids=graphic.claim_reference_ids,
                safe_area=graphic.safe_area,
                avoidance_target_ids=graphic.avoidance_target_ids,
                keyword_emphasis=graphic.keyword_emphasis,
                brand_token_ids=graphic.brand_token_ids,
                synchronized_event_id=graphic.synchronized_event_id,
                sound_cue_ids=graphic.sound_cue_ids,
                entrance=graphic.entrance,
                exit=graphic.exit,
                z_index=graphic.z_index,
            )
        )
    return tuple(
        sorted(resolved, key=lambda item: (item.start_frame, item.z_index, item.graphic_id))
    )
