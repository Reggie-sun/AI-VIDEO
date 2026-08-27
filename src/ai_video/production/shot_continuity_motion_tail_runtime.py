"""Compatibility dispatcher for legacy and frame-exact M0 motion tails."""

from __future__ import annotations

from pathlib import Path

from ai_video.errors import AiVideoError
from ai_video.production.models import AssetRecord, LoadedProductionProject
from ai_video.production.shot_continuity_motion_tail import validate_full_source_motion_tail
from ai_video.production.shot_continuity_terminal_motion_tail import validate_terminal_motion_tail


def validate_motion_tail(
    project_root: str | Path,
    project: LoadedProductionProject,
    receipt_or_asset: str | AssetRecord,
):
    """Validate exactly one supported receipt variant without weakening either."""

    try:
        return validate_terminal_motion_tail(project_root, project, receipt_or_asset)
    except AiVideoError as terminal_error:
        try:
            return validate_full_source_motion_tail(project_root, project, receipt_or_asset)
        except AiVideoError:
            raise terminal_error


__all__ = ["validate_motion_tail"]
