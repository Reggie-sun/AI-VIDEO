"""Director-authored drawing primitives, independent of the rendering engine.

No genre templates, inferred copy, alignment or acceptance. Timing here is local
to an existing graphic window; only the composition resolver places that window.
"""
from __future__ import annotations

import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from ai_video.production.text_fonts import EmbeddedFont


class DesignModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, revalidate_instances="always")

    @field_validator("fonts", "nodes", "avoidance_regions", "runs", "motion", "easing", mode="before", check_fields=False)
    @classmethod
    def _json_arrays(cls, value: object, info: ValidationInfo) -> object:
        # Ancestor before-validators materialize JSON containers. Retain strict
        # Python-mode tuples while allowing the canonical JSON round trip.
        return tuple(value) if info.mode == "json" and isinstance(value, list) else value


Color = str


class TextRun(DesignModel):
    text: str = Field(min_length=1, max_length=4096)
    color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
    font_family: str = Field(min_length=1, max_length=100)
    font_size_px: int = Field(ge=1, le=1024)
    font_weight: int = Field(default=400, ge=100, le=900, multiple_of=100)
    italic: bool = False
    tracking_px: int = Field(default=0, ge=-16, le=128)
    baseline_shift_px: int = Field(default=0, ge=-512, le=512)


class MotionPose(DesignModel):
    frame: int = Field(ge=0)
    opacity_milli: int = Field(default=1000, ge=0, le=1000)
    translate_x_px: int = Field(default=0, ge=-16384, le=16384)
    translate_y_px: int = Field(default=0, ge=-16384, le=16384)
    scale_milli: int = Field(default=1000, ge=1, le=8000)
    rotation_millidegrees: int = Field(default=0, ge=-360000, le=360000)
    blur_milli_px: int = Field(default=0, ge=0, le=64000)
    # Insets form a reveal mask, independent of movement or font size.
    reveal_top_milli: int = Field(default=0, ge=0, le=1000)
    reveal_right_milli: int = Field(default=0, ge=0, le=1000)
    reveal_bottom_milli: int = Field(default=0, ge=0, le=1000)
    reveal_left_milli: int = Field(default=0, ge=0, le=1000)
    easing: tuple[int, int, int, int] = (250, 100, 250, 1000)

    @model_validator(mode="after")
    def _bounded_easing(self) -> "MotionPose":
        if any(not 0 <= v <= 1000 for v in self.easing):
            raise ValueError("Bezier easing must remain within its endpoints")
        return self


class TextVisualNode(DesignModel):
    node_id: str = Field(min_length=1, max_length=100)
    purpose: str = Field(min_length=1, max_length=2000)
    x_px: int = Field(ge=0, le=16384)
    y_px: int = Field(ge=0, le=16384)
    width_px: int = Field(gt=0, le=16384)
    height_px: int = Field(gt=0, le=16384)
    runs: tuple[TextRun, ...] = ()
    # SVG path grammar only. No URLs, markup, script, filters or CSS injection.
    path: str | None = Field(default=None, max_length=65536)
    fill: str = Field(default="#FFFFFF", pattern=r"^(none|#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?)$")
    stroke: str = Field(default="none", pattern=r"^(none|#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?)$")
    stroke_width_px: int = Field(default=0, ge=0, le=100)
    align: Literal["left", "center", "right"] = "left"
    line_height_milli: int = Field(default=1200, ge=600, le=3000)
    writing_mode: Literal["horizontal-tb", "vertical-rl", "vertical-lr"] = "horizontal-tb"
    outline_color: str = Field(default="#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    outline_milli_px: int = Field(default=0, ge=0, le=16000)
    motion: tuple[MotionPose, ...] = ()

    @model_validator(mode="after")
    def _valid_primitive(self) -> "TextVisualNode":
        if bool(self.runs) == (self.path is not None):
            raise ValueError("A node must contain text runs or one vector path")
        if self.path is not None and (
            not self.path.strip() or re.fullmatch(r"[MmZzLlHhVvCcSsQqTtAaEe0-9+.,\s-]+", self.path) is None
        ):
            raise ValueError("Vector path contains unsupported syntax")
        if any(b.frame <= a.frame for a, b in zip(self.motion, self.motion[1:])):
            raise ValueError("Motion frames must be strictly increasing")
        if self.motion and self.motion[0].frame != 0:
            raise ValueError("Motion requires an explicit opening pose at frame zero")
        return self


class TextAvoidanceRegion(DesignModel):
    target_id: str = Field(min_length=1)
    x_px: int = Field(ge=0)
    y_px: int = Field(ge=0)
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)
    start_frame_offset: int = Field(default=0, ge=0)
    end_frame_offset: int = Field(gt=0)


class TextDesign(DesignModel):
    schema_version: Literal["text-design/1"] = "text-design/1"
    intent: str = Field(min_length=1, max_length=8000)
    hierarchy: str = Field(min_length=1, max_length=4000)
    reference_width_px: int = Field(gt=0, le=16384)
    reference_height_px: int = Field(gt=0, le=16384)
    fonts: tuple[EmbeddedFont, ...] = Field(min_length=1, max_length=8)
    nodes: tuple[TextVisualNode, ...] = Field(min_length=1, max_length=128)
    avoidance_regions: tuple[TextAvoidanceRegion, ...] = ()

    @property
    def text(self) -> str:
        return "\n".join("".join(run.text for run in node.runs) for node in self.nodes if node.runs)

    @model_validator(mode="after")
    def _references_and_glyphs(self) -> "TextDesign":
        ids = [node.node_id for node in self.nodes]
        families = [font.family for font in self.fonts]
        if len(set(ids)) != len(ids) or len(set(families)) != len(families):
            raise ValueError("Text node IDs and embedded font families must be unique")
        fonts = {font.family: font for font in self.fonts}
        for node in self.nodes:
            if node.x_px + node.width_px > self.reference_width_px or node.y_px + node.height_px > self.reference_height_px:
                raise ValueError("Text design node exceeds its reference canvas")
            for run in node.runs:
                if run.font_family not in fonts:
                    raise ValueError("Text run requires an embedded exact font")
                fonts[run.font_family].require_glyphs(run.text)
        return self

    def validate_window(self, duration_frames: int) -> None:
        for region in self.avoidance_regions:
            if not region.start_frame_offset < region.end_frame_offset <= duration_frames:
                raise ValueError("Avoidance region exceeds graphic window")
        for node in self.nodes:
            if node.motion and node.motion[-1].frame >= duration_frames:
                raise ValueError("Text motion frame exceeds graphic window")
            poses = node.motion or (MotionPose(frame=0),)
            # Conservative swept bounds. Bounded Bezier control points prevent
            # overshoot between poses; rotation uses a circumscribed radius.
            boxes = []
            for pose in poses:
                scale = pose.scale_milli / 1000
                w, h = node.width_px * scale, node.height_px * scale
                if pose.rotation_millidegrees:
                    w = h = math.hypot(w, h)
                cx = node.x_px + node.width_px / 2 + pose.translate_x_px
                cy = node.y_px + node.height_px / 2 + pose.translate_y_px
                boxes.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
            left, top = min(b[0] for b in boxes), min(b[1] for b in boxes)
            right, bottom = max(b[2] for b in boxes), max(b[3] for b in boxes)
            if left < 0 or top < 0 or right > self.reference_width_px or bottom > self.reference_height_px:
                raise ValueError("Text motion leaves the declared canvas")
            for region in self.avoidance_regions:
                if left < region.x_px + region.width_px and right > region.x_px and top < region.y_px + region.height_px and bottom > region.y_px:
                    raise ValueError(f"Text swept bounds collide with avoidance target {region.target_id}")
