from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_EVEN
from html import escape

from ai_video.production.models import RendererAudioBinding, ResolvedTimeline
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
    animations: list[str] = []
    keyframes: list[str] = []
    for track_index, span in enumerate(timeline.visual_spans):
        name = _css_animation_name(span.layer_id)
        animations.append(
            f".{name}{{animation-name:{name};animation-duration:{duration}s;"
            "animation-fill-mode:both;animation-play-state:paused;"
            "animation-timing-function:step-end}"
        )
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
        media = render_visual_element(
            span,
            video_id=_stable_dom_id("p3-video", span.layer_id),
            start_seconds=_clip_start_seconds(span.start_frame, fps),
            duration_seconds=seconds(span.duration_frames, fps),
            media_start_seconds=_clip_start_seconds(span.trim_start_frame, fps),
            track_index=track_index,
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
            *caption_elements,
            *audio_elements,
            "</div>",
            "</body>",
            "</html>",
            "",
        ]
    )
