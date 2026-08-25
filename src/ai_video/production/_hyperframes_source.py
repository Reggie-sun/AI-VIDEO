from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_EVEN
from html import escape

from ai_video.production.models import RendererAudioBinding, ResolvedTimeline
from ai_video.production.commercial_graphics import (
    GraphicAnimation,
    ResolvedCommercialGraphic,
)
from ai_video.production.visual_media import render_visual_element, visual_media_css


class HyperFramesSourceError(ValueError):
    pass


def seconds(frame_count: int, fps: int) -> str:
    value = Decimal(frame_count) / Decimal(fps)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _clip_start_seconds(frame: int, fps: int) -> str:
    value = Decimal(frame) / Decimal(fps)
    rendered = format(
        value.quantize(Decimal("0.000000001"), rounding=ROUND_FLOOR), "f"
    )
    return rendered.rstrip("0").rstrip(".") or "0"


def capture_safe_boundary_percent(
    frame: int,
    *,
    total_frames: int,
    fps: int,
    serialized_duration: str,
) -> str:
    if frame == 0:
        return "0%"
    if frame == total_frames:
        return "100%"
    if not 0 < frame < total_frames:
        raise HyperFramesSourceError(
            "CSS boundary frame is outside the timeline."
        )
    duration_decimal = Decimal(serialized_duration)
    if not duration_decimal.is_finite() or duration_decimal <= 0:
        raise HyperFramesSourceError(
            "Serialized CSS duration is not finite and positive."
        )
    previous_time = Decimal(frame - 1) / Decimal(fps)
    current_time = Decimal(frame) / Decimal(fps)
    target_time = (Decimal(frame) - Decimal("0.5")) / Decimal(fps)
    value = (target_time * Decimal(100) / duration_decimal).quantize(
        Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
    )
    rendered = format(value, "f").rstrip("0").rstrip(".")
    mapped_decimal = Decimal(rendered) * duration_decimal / Decimal(100)
    duration_f = float(serialized_duration)
    duration_ms_f = duration_f * 1000.0
    offset_progress_f = float(rendered) / 100.0
    previous_raw_seconds_f = (frame - 1) / fps
    current_raw_seconds_f = frame / fps
    previous_frame_position_f = previous_raw_seconds_f * fps + 1e-9
    current_frame_position_f = current_raw_seconds_f * fps + 1e-9
    values = (
        duration_f,
        duration_ms_f,
        offset_progress_f,
        previous_raw_seconds_f,
        current_raw_seconds_f,
        previous_frame_position_f,
        current_frame_position_f,
    )
    if duration_ms_f <= 0.0 or not all(math.isfinite(item) for item in values):
        raise HyperFramesSourceError(
            "Serialized CSS millisecond seek values are invalid."
        )
    previous_quantized_seconds_f = math.floor(previous_frame_position_f) / fps
    current_quantized_seconds_f = math.floor(current_frame_position_f) / fps
    previous_ms_f = previous_quantized_seconds_f * 1000.0
    current_ms_f = current_quantized_seconds_f * 1000.0
    previous_progress_f = previous_ms_f / duration_ms_f
    current_progress_f = current_ms_f / duration_ms_f
    quantized_values = (
        previous_quantized_seconds_f,
        current_quantized_seconds_f,
        previous_ms_f,
        current_ms_f,
        previous_progress_f,
        current_progress_f,
    )
    if not (
        previous_time < mapped_decimal < current_time
        and all(math.isfinite(item) for item in quantized_values)
        and previous_progress_f < current_progress_f
        and previous_progress_f < offset_progress_f < current_progress_f
    ):
        raise HyperFramesSourceError(
            "Serialized CSS boundary is not capture-frame safe."
        )
    return f"{rendered}%"


def _css_animation_name(layer_id: str) -> str:
    return f"p3-layer-{hashlib.sha256(layer_id.encode('utf-8')).hexdigest()}"


def _graphic_animation_name(graphic_id: str) -> str:
    return f"p22-graphic-{hashlib.sha256(graphic_id.encode('utf-8')).hexdigest()}"


def _graphic_layer_animation_name(layer_id: str) -> str:
    return f"p22-layer-{hashlib.sha256(layer_id.encode('utf-8')).hexdigest()}"


def css_visibility_keyframes(
    name: str,
    *,
    start_frame: int,
    end_frame: int,
    total_frames: int,
    fps: int,
    serialized_duration: str,
    target_opacity: str,
) -> str:
    start = capture_safe_boundary_percent(
        start_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    end = capture_safe_boundary_percent(
        end_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    if start_frame == 0 and end_frame == total_frames:
        body = f"0%,100%{{opacity:{target_opacity}}}"
    elif start_frame == 0:
        body = f"0%,{end}{{opacity:{target_opacity}}}{end},100%{{opacity:0}}"
    elif end_frame == total_frames:
        body = f"0%,{start}{{opacity:0}}{start},100%{{opacity:{target_opacity}}}"
    else:
        body = (
            f"0%,{start}{{opacity:0}}"
            f"{start},{end}{{opacity:{target_opacity}}}"
            f"{end},100%{{opacity:0}}"
        )
    return f"@keyframes {name}{{{body}}}"


def _graphic_keyframes(
    graphic: ResolvedCommercialGraphic,
    *,
    total_frames: int,
    fps: int,
    serialized_duration: str,
) -> str:
    name = _graphic_animation_name(graphic.graphic_id)
    start = capture_safe_boundary_percent(
        graphic.start_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    end = capture_safe_boundary_percent(
        graphic.end_frame_exclusive,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    duration_frames = graphic.end_frame_exclusive - graphic.start_frame
    motion_frames = min(6, max(1, duration_frames // 3))
    entry_frame = min(
        graphic.end_frame_exclusive,
        graphic.start_frame + motion_frames,
    )
    exit_frame = max(graphic.start_frame, graphic.end_frame_exclusive - motion_frames)
    entry = capture_safe_boundary_percent(
        entry_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    exit_start = capture_safe_boundary_percent(
        exit_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    entrance_transform = {
        GraphicAnimation.NONE: "none",
        GraphicAnimation.FADE: "none",
        GraphicAnimation.SLIDE_UP: "translateY(24px)",
        GraphicAnimation.SCALE_IN: "scale(.92)",
    }[graphic.entrance]
    exit_transform = {
        GraphicAnimation.NONE: "none",
        GraphicAnimation.FADE: "none",
        GraphicAnimation.SLIDE_UP: "translateY(-24px)",
        GraphicAnimation.SCALE_IN: "scale(.92)",
    }[graphic.exit]
    before = "" if graphic.start_frame == 0 else f"0%,{start}{{opacity:0;transform:{entrance_transform}}}"
    after = (
        ""
        if graphic.end_frame_exclusive == total_frames
        else f"{end},100%{{opacity:0;transform:{exit_transform}}}"
    )
    body = (
        f"{before}{start}{{opacity:{0 if graphic.entrance is not GraphicAnimation.NONE else 1};"
        f"transform:{entrance_transform}}}"
        f"{entry},{exit_start}{{opacity:1;transform:none}}"
        f"{end}{{opacity:{0 if graphic.exit is not GraphicAnimation.NONE else 1};"
        f"transform:{exit_transform}}}{after}"
    )
    return f"@keyframes {name}{{{body}}}"


def _graphic_layer_keyframes(
    *,
    name: str,
    start_frame: int,
    end_frame: int,
    entrance: GraphicAnimation,
    exit: GraphicAnimation,
    target_opacity: str,
    total_frames: int,
    fps: int,
    serialized_duration: str,
) -> str:
    start = capture_safe_boundary_percent(
        start_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    end = capture_safe_boundary_percent(
        end_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    duration_frames = end_frame - start_frame
    motion_frames = min(6, max(1, duration_frames // 3))
    entry = capture_safe_boundary_percent(
        min(end_frame, start_frame + motion_frames),
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    exit_start = capture_safe_boundary_percent(
        max(start_frame, end_frame - motion_frames),
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    entrance_transform = {
        GraphicAnimation.NONE: "none",
        GraphicAnimation.FADE: "none",
        GraphicAnimation.SLIDE_UP: "translateY(24px)",
        GraphicAnimation.SCALE_IN: "scale(.92)",
    }[entrance]
    exit_transform = {
        GraphicAnimation.NONE: "none",
        GraphicAnimation.FADE: "none",
        GraphicAnimation.SLIDE_UP: "translateY(-24px)",
        GraphicAnimation.SCALE_IN: "scale(.92)",
    }[exit]
    before = "" if start_frame == 0 else f"0%,{start}{{opacity:0;transform:{entrance_transform}}}"
    after = (
        ""
        if end_frame == total_frames
        else f"{end},100%{{opacity:0;transform:{exit_transform}}}"
    )
    body = (
        f"{before}{start}{{opacity:{0 if entrance is not GraphicAnimation.NONE else target_opacity};"
        f"transform:{entrance_transform}}}"
        f"{entry},{exit_start}{{opacity:{target_opacity};transform:none}}"
        f"{end}{{opacity:{0 if exit is not GraphicAnimation.NONE else target_opacity};"
        f"transform:{exit_transform}}}{after}"
    )
    return f"@keyframes {name}{{{body}}}"


def _commercial_graphic_css(graphic: ResolvedCommercialGraphic, duration: str) -> str:
    name = _graphic_animation_name(graphic.graphic_id)
    background = graphic.background_color or "transparent"
    return (
        f".{name}{{left:{_decimal_milli(graphic.x_milli * 100)}%;"
        f"top:{_decimal_milli(graphic.y_milli * 100)}%;"
        f"width:{_decimal_milli(graphic.width_milli * 100)}%;"
        f"font-size:{graphic.font_size_px}px;color:{graphic.text_color};"
        f"background:{background};z-index:{graphic.z_index};"
        f"animation-name:{name};animation-duration:{duration}s;"
        "animation-fill-mode:both;animation-play-state:paused;"
        "animation-timing-function:linear;transform-origin:50% 50%}"
    )


def _commercial_graphic_text(graphic: ResolvedCommercialGraphic) -> str:
    if not graphic.keyword_emphasis:
        return escape(graphic.text)
    emphasis = {item.text: item.brand_token_id for item in graphic.keyword_emphasis}
    pattern = re.compile("(" + "|".join(re.escape(item) for item in emphasis) + ")")
    return "".join(
        (
            f'<span class="commercial-keyword-emphasis" data-brand-token-id="{escape(emphasis[part])}">{escape(part)}</span>'
            if part in emphasis
            else escape(part)
        )
        for part in pattern.split(graphic.text)
    )


def _decimal_milli(value: int) -> str:
    rendered = format(Decimal(value) / Decimal(1000), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _sample_seconds(samples: int, sample_rate: int) -> str:
    value = Decimal(samples) / Decimal(sample_rate)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _stable_dom_id(prefix: str, identity: str) -> str:
    return f"{prefix}-{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"


def _caption_style_css(style_hash: str, style: Mapping[str, object]) -> str:
    if style.get("schema_version") != "1":
        raise HyperFramesSourceError(
            "Caption style schema version is unsupported."
        )

    def integer(name: str, default: int, minimum: int, maximum: int) -> int:
        value = style.get(name, default)
        if isinstance(value, bool) or not isinstance(value, int):
            raise HyperFramesSourceError(
                f"Caption style {name} must be an integer."
            )
        if not minimum <= value <= maximum:
            raise HyperFramesSourceError(
                f"Caption style {name} is out of range."
            )
        return value

    def color(name: str, default: str) -> str:
        value = style.get(name, default)
        if (
            not isinstance(value, str)
            or re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is None
        ):
            raise HyperFramesSourceError(
                f"Caption style {name} must be a six-digit hex color."
            )
        return value.upper()

    font_family = style.get("font_family", "sans-serif")
    if (
        not isinstance(font_family, str)
        or not 1 <= len(font_family) <= 100
        or any(ord(character) < 32 for character in font_family)
    ):
        raise HyperFramesSourceError("Caption style font_family is invalid.")
    font_size = integer("font_size_px", 24, 8, 200)
    bottom = integer("bottom_margin_px", 52, 0, 500)
    max_width = integer("max_width_milli", 900, 100, 1000)
    outline_width = integer("outline_width_px", 2, 0, 20)
    text_color = color("text_color", "#FFFFFF")
    outline_color = color("outline_color", "#101820")
    width_percent = format(
        (Decimal(max_width) / Decimal(10)).normalize(), "f"
    )
    quoted_family = json.dumps(font_family, ensure_ascii=True)
    shadow = "none"
    if outline_width:
        shadow = ",".join(
            (
                f"-{outline_width}px 0 {outline_color}",
                f"{outline_width}px 0 {outline_color}",
                f"0 -{outline_width}px {outline_color}",
                f"0 {outline_width}px {outline_color}",
            )
        )
    return (
        f"    .caption-style-{style_hash}{{left:50%;right:auto;"
        f"bottom:{bottom}px;width:{width_percent}%;transform:translateX(-50%);"
        f"padding:0;background:transparent;color:{text_color};text-align:center;"
        f"font-family:{quoted_family};font-size:{font_size}px;font-weight:700;"
        f"line-height:1.25;white-space:pre-wrap;text-shadow:{shadow}}}"
    )


def render_source(
    timeline: ResolvedTimeline,
    mixed_audio: RendererAudioBinding | None = None,
    caption_styles: Mapping[str, Mapping[str, object]] | None = None,
    *,
    legacy_caption_style: bool = False,
    caption_top_auto: bool = True,
) -> str:
    caption_styles = caption_styles or {}
    expected_style_hashes = {
        cue.style_content_hash
        for cue in timeline.caption_cues
        if cue.style_content_hash
    }
    if not legacy_caption_style and set(caption_styles) != expected_style_hashes:
        raise HyperFramesSourceError(
            "Caption style values do not match the resolved timeline."
        )
    if legacy_caption_style and caption_styles:
        raise HyperFramesSourceError(
            "Legacy caption source cannot consume style values."
        )
    fps = timeline.delivery_profile.fps
    duration = seconds(timeline.total_frames, fps)
    clips: list[str] = []
    audio_elements: list[str] = []
    caption_elements: list[str] = []
    graphic_elements: list[str] = []
    animations: list[str] = []
    keyframes: list[str] = []
    for track_index, span in enumerate(timeline.visual_spans):
        if span.graphic_animation is None:
            name = _css_animation_name(span.layer_id)
        else:
            name = _graphic_layer_animation_name(span.layer_id)
        animations.append(
            f".{name}{{animation-name:{name};animation-duration:{duration}s;"
            "animation-fill-mode:both;animation-play-state:paused;"
            "animation-timing-function:step-end}"
        )
        if span.graphic_animation is None:
            keyframes.append(
                css_visibility_keyframes(
                    name,
                    start_frame=span.start_frame,
                    end_frame=span.start_frame + span.duration_frames,
                    total_frames=timeline.total_frames,
                    fps=fps,
                    serialized_duration=duration,
                    target_opacity=_decimal_milli(span.opacity_milli),
                )
            )
        else:
            keyframes.append(
                _graphic_layer_keyframes(
                    name=name,
                    start_frame=span.start_frame,
                    end_frame=span.start_frame + span.duration_frames,
                    entrance=span.graphic_animation.entrance,
                    exit=span.graphic_animation.exit,
                    target_opacity=_decimal_milli(span.opacity_milli),
                    total_frames=timeline.total_frames,
                    fps=fps,
                    serialized_duration=duration,
                )
            )
        media = render_visual_element(
            span,
            video_id=_stable_dom_id("p3-video", span.layer_id),
            start_seconds=_clip_start_seconds(span.start_frame, fps),
            duration_seconds=seconds(span.duration_frames, fps),
            media_start_seconds=_clip_start_seconds(span.trim_start_frame, fps),
            track_index=track_index,
        )
        motion_attributes = (
            f' data-layer-entrance="{span.graphic_animation.entrance.value}"'
            f' data-layer-exit="{span.graphic_animation.exit.value}"'
            if span.graphic_animation is not None
            else ""
        )
        clips.append(
            "\n".join(
                [
                    (
                        f'<div class="clip {name}" data-layer-id="{escape(span.layer_id)}"'
                        f' data-animation-name="{name}" data-shot-id="{escape(span.shot_id)}"'
                        f' data-asset-id="{escape(span.asset_id)}"'
                        f' data-asset-role="{escape(span.asset_role)}"'
                        f' data-asset-sha256="{span.asset_sha256}"'
                        f' data-start-frame="{span.start_frame}"'
                        f' data-duration-frames="{span.duration_frames}"'
                        f' data-start-sample="{span.start_sample}"'
                        f' data-duration-samples="{span.duration_samples}"'
                        ' data-transition-kind="cut" data-transition-frames="0"'
                        f'{motion_attributes}'
                        f' style="z-index:{span.z_index}">'
                    ),
                    media,
                    "</div>",
                ]
            )
        )
    if mixed_audio is not None:
        audio_elements.append(
            (
                f'<audio id="{_stable_dom_id("p4-audio-mix", timeline.composition_fingerprint)}"'
                f' class="clip" src="{mixed_audio.materialized_path.as_posix()}"'
                f' data-mix-asset-id="{escape(mixed_audio.asset_id)}"'
                f' data-mix-sha256="{mixed_audio.asset_sha256}"'
                f' data-resolved-track-ids="{escape(",".join(mixed_audio.resolved_track_ids))}"'
                ' data-start="0"'
                f' data-duration="{_sample_seconds(timeline.total_samples, timeline.sample_rate)}"'
                ' data-media-start="0" data-track-index="10000" data-volume="1"></audio>'
            )
        )
    for track_index, cue in enumerate(timeline.caption_cues, start=20_000):
        if cue.style_content_hash is None:
            raise HyperFramesSourceError(
                "Resolved caption cue is missing its style identity."
            )
        caption_class = "clip caption"
        if not legacy_caption_style:
            caption_class += f" caption-style-{cue.style_content_hash}"
        caption_elements.append(
            (
                f'<div id="{_stable_dom_id("p4-caption", cue.caption_track_id + ":" + cue.segment_id)}" class="{caption_class}" data-layout-allow-caption-zone'
                f' data-caption-track-id="{escape(cue.caption_track_id)}"'
                f' data-caption-asset-id="{escape(cue.caption_asset_id)}"'
                f' data-caption-asset-sha256="{cue.caption_asset_sha256}"'
                f' data-caption-timing-fingerprint="{cue.caption_timing_fingerprint}"'
                f' data-segment-id="{escape(cue.segment_id)}"'
                f' data-style-reference-id="{escape(cue.style_reference_id or "")}"'
                f' data-style-content-hash="{cue.style_content_hash or ""}"'
                f' data-start-sample="{cue.start_sample}" data-end-sample="{cue.end_sample}"'
                f' data-start-frame="{cue.start_frame}" data-end-frame-exclusive="{cue.end_frame_exclusive}"'
                f' data-start="{_clip_start_seconds(cue.start_frame, fps)}"'
                f' data-duration="{seconds(cue.end_frame_exclusive - cue.start_frame, fps)}"'
                f' data-track-index="{track_index}">{escape(cue.text)}</div>'
            )
        )
    for graphic in timeline.commercial_graphics:
        name = _graphic_animation_name(graphic.graphic_id)
        animations.append(_commercial_graphic_css(graphic, duration))
        keyframes.append(
            _graphic_keyframes(
                graphic,
                total_frames=timeline.total_frames,
                fps=fps,
                serialized_duration=duration,
            )
        )
        graphic_elements.append(
            (
                f'<div id="{_stable_dom_id("p22-commercial-graphic", graphic.graphic_id)}"'
                f' class="clip commercial-graphic {name}"'
                f' data-commercial-graphic-id="{escape(graphic.graphic_id)}"'
                f' data-commercial-graphic-role="{graphic.role.value}"'
                f' data-shot-id="{escape(graphic.shot_id)}"'
                f' data-start-frame="{graphic.start_frame}"'
                f' data-end-frame-exclusive="{graphic.end_frame_exclusive}"'
                f' data-start-sample="{graphic.start_sample}"'
                f' data-end-sample="{graphic.end_sample}"'
                f' data-claim-reference-ids="{escape(",".join(graphic.claim_reference_ids))}"'
                f' data-avoidance-target-ids="{escape(",".join(graphic.avoidance_target_ids))}"'
                f' data-brand-token-ids="{escape(",".join(graphic.brand_token_ids))}"'
                f' data-synchronized-event-id="{escape(graphic.synchronized_event_id or "")}"'
                f' data-sound-cue-ids="{escape(",".join(graphic.sound_cue_ids))}"'
                f' data-safe-area="{graphic.safe_area.top_milli},{graphic.safe_area.right_milli},{graphic.safe_area.bottom_milli},{graphic.safe_area.left_milli}"'
                f' data-entrance="{graphic.entrance.value}"'
                f' data-exit="{graphic.exit.value}">{_commercial_graphic_text(graphic)}</div>'
            )
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            "  <style>",
            "    html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000}",
            "    #stage{position:relative;overflow:hidden}",
            "    .clip{position:absolute;inset:0}",
            *(
                (
                    "    .commercial-graphic{inset:auto;box-sizing:border-box;padding:.2em .3em;font-family:sans-serif;font-weight:700;line-height:1.15;white-space:pre-wrap;overflow:hidden}",
                    "    .commercial-keyword-emphasis{font-weight:900;text-decoration:underline;text-decoration-thickness:.08em}",
                )
                if timeline.commercial_graphics
                else ()
            ),
            visual_media_css(timeline.visual_spans),
            *(
                (
                    (
                        "    .caption{position:absolute;left:5%;right:5%;bottom:8%;padding:10px;background:#00ffff;color:#000;text-align:center;font:700 24px/1.25 sans-serif}"
                        if legacy_caption_style
                        else (
                            "    .caption{position:absolute;top:auto}"
                            if caption_top_auto
                            else "    .caption{position:absolute}"
                        )
                    ),
                )
                if timeline.caption_cues
                else ()
            ),
            *(
                _caption_style_css(style_hash, caption_styles[style_hash])
                for style_hash in sorted(caption_styles)
            ),
            *(f"    {rule}" for rule in animations),
            *(f"    {rule}" for rule in keyframes),
            "  </style>",
            "</head>",
            "<body>",
            (
                f'<div id="stage" data-no-timeline data-composition-id="{escape(timeline.timeline_id)}"'
                f' data-timeline-fingerprint="{timeline.composition_fingerprint}"'
                f' data-renderer-version="{escape(timeline.renderer.version)}"'
                f' data-start="0" data-duration="{duration}"'
                f' data-width="{timeline.delivery_profile.width}"'
                f' data-height="{timeline.delivery_profile.height}" data-fps="{fps}">'
            ),
            *clips,
            *graphic_elements,
            *caption_elements,
            *audio_elements,
            "</div>",
            "</body>",
            "</html>",
            "",
        ]
    )
