"""Visual authoring and evidence leaves for the existing final-output owner.

No aesthetic classifier, media execution, aggregate score, or lifecycle state.
"""

from typing import Literal

from pydantic import Field, field_validator, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel

VisualDimension = Literal["typography", "palette", "layout", "style", "holistic"]
VisualContentKind = Literal["drama", "advertising"]
VISUAL_DIMENSIONS = ("typography", "palette", "layout", "style", "holistic")


class VisualDirection(StrictModel):
    """Concrete authored expectations; the resulting QA requirements own them."""

    content_kind: VisualContentKind | None = None
    typography: str = Field(min_length=1)
    palette: str = Field(min_length=1)
    layout: str = Field(min_length=1)
    style: str = Field(min_length=1)
    holistic: str = Field(min_length=1)

    @field_validator("typography", "palette", "layout", "style", "holistic")
    @classmethod
    def _nonblank(cls, value):
        if not value.strip():
            raise ValueError("Visual direction must describe an observable expectation")
        return value

    @model_serializer(mode="wrap")
    def _legacy_direction_bytes(self, handler):
        data = handler(self)
        if self.content_kind is None:
            data.pop("content_kind", None)
        return data


class VisualFrameReference(StrictModel):
    timestamp_ms: int = Field(strict=True, ge=0)
    frame_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    render_output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class VisualFrameInventory(StrictModel):
    """Selected evaluator's sealed extraction declaration, not a capture host."""

    duration_ms: int = Field(strict=True, gt=0)
    frames: tuple[VisualFrameReference, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _valid_windows(self):
        stamps = [f.timestamp_ms for f in self.frames]
        if len(stamps) != len(set(stamps)) or any(t >= self.duration_ms for t in stamps):
            raise ValueError("Visual frame inventory has duplicate or out-of-range timestamps")
        if len({f.render_output_sha256 for f in self.frames}) != 1:
            raise ValueError("Visual frame inventory must describe one exact render")
        return self


def visual_requirements(direction: VisualDirection):
    """Author five ordinary final-output requirements without selecting QA."""
    from ai_video.production.final_output_contracts import FinalOutputRequirement

    prefix = "visual" if direction.content_kind is None else f"visual.{direction.content_kind}"
    return tuple(FinalOutputRequirement(
        requirement_id=f"{prefix}.{dimension}",
        observable=getattr(direction, dimension),
        proof="human" if dimension == "holistic" else "evaluator",
        visual_dimension=dimension,
    ) for dimension in VISUAL_DIMENSIONS)


def valid_visual_finding(requirement, finding, source, evidence):
    """Validate provenance/coverage declarations, never invent a visual verdict."""
    if not finding.observation.strip() or not finding.visual_frames:
        return False
    inventory = source.visual_frame_inventory
    if inventory is None or not set(finding.visual_frames) <= set(inventory.frames):
        return False
    if any(frame.render_output_sha256 != evidence.render_output_sha256
           for frame in finding.visual_frames):
        return False
    # A sampled defect can reject a film, but sampled PASS cannot prove the
    # normal-speed, whole-film viewing required by the holistic criterion.
    if requirement.visual_dimension == "holistic" and finding.verdict == "pass":
        return source.viewing_mode == "full_playback" and source.viewing_speed_milli == 1000
    return True
