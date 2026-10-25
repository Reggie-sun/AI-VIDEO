"""Reusable watermark authoring inputs for the existing composition owner."""
from __future__ import annotations

import base64
import hashlib
import io
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_video.production.commercial_graphics import GraphicAnimation, GraphicRole, GraphicTreatment
from ai_video.production.composition_contracts import CompositionSpec, TransitionKind
from ai_video.production.text_design import MotionPose, TextDesign, TextRun, TextVisualNode
from ai_video.production.text_fonts import EmbeddedFont


class WatermarkWaypoint(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    time_milli: int = Field(ge=0, le=1000)
    center_x_milli: int = Field(ge=0, le=1000)
    center_y_milli: int = Field(ge=0, le=1000)


class WatermarkPreset(BaseModel):
    """Editable display name and copy; all positions are canvas-relative."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal["watermark-preset/1"] = "watermark-preset/1"
    name: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=4096)
    font_size_px: int = Field(default=32, ge=8, le=256)
    color: str = Field(default="#FFF7E8", pattern=r"^#[0-9A-Fa-f]{6}$")
    opacity_milli: int = Field(default=550, ge=1, le=1000)
    outline_color: str = Field(default="#172333", pattern=r"^#[0-9A-Fa-f]{6}$")
    outline_milli_px: int = Field(default=1000, ge=0, le=16000)
    waypoints: tuple[WatermarkWaypoint, ...] = (
        WatermarkWaypoint(time_milli=0, center_x_milli=120, center_y_milli=70),
        WatermarkWaypoint(time_milli=500, center_x_milli=500, center_y_milli=900),
        WatermarkWaypoint(time_milli=1000, center_x_milli=880, center_y_milli=70),
    )

    @model_validator(mode="after")
    def _usable_path(self):
        if not self.name.strip() or not self.text.strip() or any(c in self.text for c in "\r\n"):
            raise ValueError("Watermark name and single-line text must be nonblank")
        if (len(self.waypoints) < 2 or self.waypoints[0].time_milli != 0
                or self.waypoints[-1].time_milli != 1000
                or any(b.time_milli <= a.time_milli for a, b in zip(self.waypoints, self.waypoints[1:]))):
            raise ValueError("Watermark path must increase from time 0 to 1000")
        return self


def build_watermark_font(text: str) -> EmbeddedFont:
    """Capture the licensed installed font subset for the current editable text."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", fontNumber=2,
                  recalcTimestamp=False)
    subsetter = subset.Subsetter()
    subsetter.populate(text=text)
    subsetter.subset(font)
    stream = io.BytesIO()
    font.save(stream)
    payload = stream.getvalue()
    embedded = EmbeddedFont(family="Noto Sans CJK SC", sha256=hashlib.sha256(payload).hexdigest(),
                            data_base64=base64.b64encode(payload).decode("ascii"),
                            license="SIL Open Font License 1.1; Google Noto CJK")
    embedded.require_glyphs(text)
    return embedded


def build_watermark_layers(
    spec: CompositionSpec, *, duration_frames_by_shot: Mapping[str, int],
    preset: WatermarkPreset, font: EmbeddedFont | None = None,
) -> tuple[GraphicTreatment, ...]:
    """Build text layers; ResolvedTimeline alone owns their actual placement."""
    preset = WatermarkPreset.model_validate(preset.model_dump(mode="python"))
    shots = tuple(spec.shot_ids)
    if spec.schema_version not in {"2.2", "2.3", "2.4"}:
        raise ValueError("Watermarks require composition text-layer support")
    if not shots or set(duration_frames_by_shot) != set(shots) or any(
        type(duration_frames_by_shot[s]) is not int or duration_frames_by_shot[s] <= 0 for s in shots
    ):
        raise ValueError("Watermark duration map must cover every Shot with positive frames")
    if (tuple((t.from_shot_id, t.to_shot_id) for t in spec.transitions) != tuple(zip(shots, shots[1:]))
            or any(t.kind is not TransitionKind.CUT or t.duration_frames != 0 for t in spec.transitions)):
        raise ValueError("Watermark path requires ordered zero-duration cuts")
    total_frames = sum(duration_frames_by_shot.values())
    if total_frames < 3:
        raise ValueError("Watermark motion requires at least three output frames")
    font = font or build_watermark_font(preset.text)
    font.require_glyphs(preset.text)
    from fontTools.ttLib import TTFont
    with TTFont(io.BytesIO(font.font_bytes())) as parsed:
        cmap = parsed.getBestCmap()
        advance = sum(parsed["hmtx"].metrics[cmap[ord(c)]][0] for c in preset.text)
        width = math.ceil(advance * preset.font_size_px / parsed["head"].unitsPerEm) + 12
    height = math.ceil(preset.font_size_px * 1.5) + 8
    profile = spec.delivery_profile
    anchors = tuple((round(w.time_milli * (total_frames - 1) / 1000),
                     round(w.center_x_milli * profile.width / 1000 - width / 2),
                     round(w.center_y_milli * profile.height / 1000 - height / 2))
                    for w in preset.waypoints)
    if any(b[0] <= a[0] for a, b in zip(anchors, anchors[1:])):
        raise ValueError("Watermark waypoints collapse on this output frame grid")
    if any(x < 0 or y < 0 or x + width > profile.width or y + height > profile.height
           for _, x, y in anchors):
        raise ValueError("Watermark text leaves the canvas; reduce font size or move its path inward")

    def position(frame):
        for a, b in zip(anchors, anchors[1:]):
            if a[0] <= frame <= b[0]:
                ratio = (frame - a[0]) / (b[0] - a[0])
                return round(a[1] + ratio * (b[1] - a[1])), round(a[2] + ratio * (b[2] - a[2]))
        raise ValueError("Watermark sample lies outside its composition")

    existing = {g.graphic_id for g in (*spec.commercial_graphics, *spec.text_layers)}
    result, start = [], 0
    for shot in shots:
        count = duration_frames_by_shot[shot]
        frames = {start, start + count - 1}
        frames.update(f for f, _, _ in anchors if start <= f < start + count)
        poses = tuple(MotionPose(frame=f - start, translate_x_px=position(f)[0],
                                 translate_y_px=position(f)[1], opacity_milli=preset.opacity_milli,
                                 easing=(0, 0, 1000, 1000)) for f in sorted(frames))
        graphic_id = "watermark-" + hashlib.sha256(shot.encode()).hexdigest()[:12]
        if graphic_id in existing:
            raise ValueError("Watermark layer already exists on this Shot")
        design = TextDesign(intent=f"Merchant watermark preset: {preset.name}",
            hierarchy="Translucent merchant name moves along the authored path.",
            reference_width_px=profile.width, reference_height_px=profile.height, fonts=(font,),
            nodes=(TextVisualNode(node_id="merchant-watermark", purpose="Merchant attribution",
                x_px=0, y_px=0, width_px=width, height_px=height,
                runs=(TextRun(text=preset.text, font_family=font.family, font_size_px=preset.font_size_px,
                              color=preset.color, font_weight=400),),
                outline_color=preset.outline_color, outline_milli_px=preset.outline_milli_px,
                motion=poses),))
        result.append(GraphicTreatment(graphic_id=graphic_id, role=GraphicRole.HEADLINE,
            text=preset.text, shot_id=shot, start_frame_offset=0, duration_frames=count,
            x_milli=0, y_milli=0, width_milli=1000, font_size_px=preset.font_size_px,
            font_weight=400, text_color=preset.color, background_color=None,
            entrance=GraphicAnimation.NONE, exit=GraphicAnimation.NONE, z_index=500, text_design=design))
        start += count
    return tuple(result)
