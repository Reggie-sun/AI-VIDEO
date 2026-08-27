"""Current M0-only terminal motion-tail contract."""

from __future__ import annotations

from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import AssetRecord, LoadedProductionProject
from ai_video.production.shot_continuity_m0_qualification import (
    M0_REFERENCE_VIDEO_MAX_DURATION_MILLISECONDS,
    M0_REFERENCE_VIDEO_MIN_DURATION_MILLISECONDS,
)
from ai_video.production.shot_continuity_terminal_motion_tail import (
    TerminalMotionTailReceipt,
    validate_terminal_motion_tail,
)


def validate_m0_motion_tail(
    project_root: str | Path,
    project: LoadedProductionProject,
    receipt_or_asset: str | AssetRecord,
) -> TerminalMotionTailReceipt:
    """Require the shortest exact terminal window for the sealed M0 workflow."""

    try:
        receipt = validate_terminal_motion_tail(project_root, project, receipt_or_asset)
    except AiVideoError as exc:
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message=(
                "M0 requires the exact 48-frame, 2000 ms terminal motion tail."
            ),
            technical_detail=str(exc),
            retryable=False,
        ) from exc
    if (
        receipt.selection_rule_version != "terminal-window-frame-exact-v1"
        or receipt.provider_min_duration_milliseconds
        != M0_REFERENCE_VIDEO_MIN_DURATION_MILLISECONDS
        or receipt.provider_max_duration_milliseconds
        != M0_REFERENCE_VIDEO_MAX_DURATION_MILLISECONDS
        or receipt.source_fps_numerator != 24
        or receipt.source_fps_denominator != 1
        or receipt.extracted_fps_numerator != 24
        or receipt.extracted_fps_denominator != 1
        or receipt.extracted_frame_count != 48
        or receipt.extracted_duration_milliseconds != 2_000
        or receipt.end_frame_index - receipt.start_frame_index + 1 != 48
    ):
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message=(
                "M0 requires the exact 48-frame, 2000 ms terminal motion tail."
            ),
            retryable=False,
        )
    return receipt


__all__ = ["validate_m0_motion_tail"]
