from __future__ import annotations

import math
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StrictInt, field_validator, model_validator

from ai_video.production.artifact_contracts import StrictModel


Coordinate: TypeAlias = tuple[StrictInt, StrictInt]
CleanupPolygon: TypeAlias = Annotated[tuple[Coordinate, ...], Field(min_length=3)]
AffineCoefficients: TypeAlias = tuple[float, float, float, float, float, float]


class CleanPlatePatch(StrictModel):
    plate_frame: StrictInt = Field(ge=0)
    polygons: tuple[CleanupPolygon, ...] = Field(min_length=1)
    plate_to_output_affine: AffineCoefficients = (1, 0, 0, 0, 1, 0)
    feather_px: StrictInt = Field(default=0, ge=0, le=64)

    @field_validator("plate_to_output_affine", mode="before")
    @classmethod
    def _finite_affine(cls, value: object) -> tuple[float, ...]:
        if not isinstance(value, (tuple, list)) or len(value) != 6:
            raise ValueError("plate_to_output_affine must contain six finite numbers")
        normalized: list[float] = []
        for component in value:
            if isinstance(component, bool) or not isinstance(component, (int, float)):
                raise ValueError("plate_to_output_affine must contain six finite numbers")
            try:
                numeric = float(component)
            except (OverflowError, ValueError):
                raise ValueError("plate_to_output_affine must contain six finite numbers") from None
            if not math.isfinite(numeric):
                raise ValueError("plate_to_output_affine must contain six finite numbers")
            normalized.append(numeric)
        return tuple(normalized)

    @model_validator(mode="after")
    def _invertible_affine(self) -> CleanPlatePatch:
        a, b, _, d, e, _ = self.plate_to_output_affine
        determinant = a * e - b * d
        if not math.isfinite(determinant) or determinant == 0.0:
            raise ValueError("plate_to_output_affine must be invertible")
        return self


class CleanPlateFrame(StrictModel):
    frame_index: StrictInt = Field(ge=0)
    patches: tuple[CleanPlatePatch, ...] = Field(min_length=1)
    protected_polygons: tuple[CleanupPolygon, ...] = ()


class VideoCleanupPlan(StrictModel):
    contract_version: Literal["video-clean-plate/1"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frames: tuple[CleanPlateFrame, ...] = Field(min_length=1, max_length=600)

    @model_validator(mode="after")
    def _strictly_ordered_frames(self) -> VideoCleanupPlan:
        indices = tuple(frame.frame_index for frame in self.frames)
        if indices != tuple(sorted(set(indices))):
            raise ValueError("frames must be strictly sorted by unique frame_index")
        return self


def video_cleanup_capability_report() -> dict:
    """Static source-preparation capability, never readiness or qualification."""
    return {"method": "non_generative_clean_plate", "availability": "IMPLEMENTED_DEVELOPMENT_PREPARATION",
        "entrypoint": "bootstrap_video_cleanup", "plan_contract": "video-clean-plate/1",
        "requires": ["exact_closed_failed_source", "clean_plate_frame", "authored_masks",
            "explicit_per_frame_affine", "foreground_protection", "injected_local_tools"],
        "tracking": "EXPLICIT_AFFINE_DATA_ONLY", "automatic_tracking": False,
        "timing": "SOURCE_FRAMES_AND_TIMESTAMPS_PRESERVED",
        "audio": "ORIGINAL_PCM_AND_TIMING_PRESERVED", "generation_calls": 0,
        "production_selection": "REQUIRES_SEPARATE_SOURCE_QUALIFICATION",
        "quality": "NOT_EVALUATED"}
