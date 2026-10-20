"""Compile typed text drawing primitives into the existing HyperFrames source.

Browser shaping/SVG/CSS execute the design. This module never invents a design,
loads media, moves canonical time, runs JS, or changes production state.
"""
from __future__ import annotations

import hashlib
import json
import re
from html import escape

from ai_video.production.text_design import MotionPose, TextDesign


def embedded_render_url(value: str) -> bool:
    return re.fullmatch(r"data:(image/png|font/otf|font/ttf);base64,[A-Za-z0-9+/]+=*", value) is not None


def _number(value: int) -> str:
    return f"{value / 1000:.3f}".rstrip("0").rstrip(".")


def _pose(pose: MotionPose) -> str:
    return (
        f"opacity:{_number(pose.opacity_milli)};"
        f"transform:translate({pose.translate_x_px}px,{pose.translate_y_px}px) "
        f"rotate({_number(pose.rotation_millidegrees)}deg) scale({_number(pose.scale_milli)});"
        f"filter:blur({_number(pose.blur_milli_px)}px);"
        f"clip-path:inset({_number(pose.reveal_top_milli * 100)}% "
        f"{_number(pose.reveal_right_milli * 100)}% "
        f"{_number(pose.reveal_bottom_milli * 100)}% "
        f"{_number(pose.reveal_left_milli * 100)}%);"
        f"animation-timing-function:cubic-bezier({','.join(_number(v) for v in pose.easing)})"
    )


def render_text_design(graphic, *, timeline, duration: str, boundary) -> tuple[str, tuple[str, ...]]:
    design = graphic.text_design
    assert design is not None
    design = TextDesign.model_validate(design)
    design.validate_window(graphic.end_frame_exclusive - graphic.start_frame)
    css = []
    for font in design.fonts:
        css.append(
            f"@font-face{{font-family:{json.dumps(font.family)};"
            f"src:url(data:{font.mime};base64,{font.data_base64});font-display:block}}"
        )
    elements = []
    for node in design.nodes:
        identity = hashlib.sha256(f"{graphic.graphic_id}:{node.node_id}".encode()).hexdigest()
        name = "text-node-" + identity
        poses = node.motion or (MotionPose(frame=0),)
        steps = [f"0%{{{_pose(poses[0])}}}"]
        for pose in poses:
            frame = graphic.start_frame + pose.frame
            position = boundary(frame, total_frames=timeline.total_frames,
                                fps=timeline.delivery_profile.fps, serialized_duration=duration)
            steps.append(f"{position}{{{_pose(pose)}}}")
        steps.append(f"100%{{{_pose(poses[-1])}}}")
        css.append(f"@keyframes {name}{{{''.join(steps)}}}")
        css.append(
            f".{name}{{animation:{name} {duration}s linear both paused;"
            "transform-box:fill-box;transform-origin:center;overflow:visible}"
        )
        if node.path is not None:
            inner = (
                f'<svg x="{node.x_px}" y="{node.y_px}" width="{node.width_px}" height="{node.height_px}" '
                f'viewBox="0 0 {node.width_px} {node.height_px}" overflow="visible">'
                f'<path d="{escape(node.path)}" fill="{node.fill}" stroke="{node.stroke}" '
                f'stroke-width="{node.stroke_width_px}"/></svg>'
            )
        else:
            runs = []
            for run in node.runs:
                runs.append(
                    f'<span style="font-family:{escape(json.dumps(run.font_family), quote=True)};'
                    f'font-size:{run.font_size_px}px;font-weight:{run.font_weight};'
                    f'font-style:{"italic" if run.italic else "normal"};color:{run.color};'
                    f'letter-spacing:{run.tracking_px}px;position:relative;top:{-run.baseline_shift_px}px">'
                    f'{escape(run.text)}</span>'
                )
            inner = (
                f'<foreignObject x="{node.x_px}" y="{node.y_px}" width="{node.width_px}" height="{node.height_px}">'
                '<div xmlns="http://www.w3.org/1999/xhtml" '
                f'data-text-node-id="{escape(node.node_id)}" style="white-space:pre-wrap;'
                f'font-size:{max(run.font_size_px for run in node.runs)}px;'
                f'word-break:normal;overflow-wrap:normal;line-break:strict;text-align:{node.align};'
                f'writing-mode:{node.writing_mode};line-height:{_number(node.line_height_milli)};'
                f'-webkit-text-stroke:{_number(node.outline_milli_px)}px {node.outline_color};'
                f'paint-order:stroke fill">{"".join(runs)}</div></foreignObject>'
            )
        elements.append(f'<g class="{name}" data-design-purpose="{escape(node.purpose)}">{inner}</g>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {design.reference_width_px} {design.reference_height_px}" '
        'style="display:block;width:100%;height:auto;overflow:visible" '
        f'data-text-design="{design.schema_version}" data-text-design-intent="{escape(design.intent)}">'
        f'{"".join(elements)}</svg>'
    )
    return svg, tuple(css)


def render_ass_caption(cue, style, *, timeline, duration, boundary, visibility) -> tuple[str, tuple[str, ...]]:
    # Optional backend is loaded only for explicitly selected version-2 styles.
    from ai_video.production.subtitle_ass import render_subtitle_states

    highlight = style.get("word_highlight", False)
    words = cue.words or ()
    if highlight and not words:
        raise ValueError("Word highlighting requires resolved source word timing")
    states = render_subtitle_states(
        cue.text, style, width=timeline.delivery_profile.width,
        height=timeline.delivery_profile.height,
        word_texts=tuple(word.text for word in words) if highlight else (),
    )
    intervals = []
    cursor = cue.start_frame
    if highlight:
        for index, word in enumerate(words, 1):
            if word.start_frame > cursor:
                intervals.append((cursor, word.start_frame, 0))
            if word.end_frame_exclusive > word.start_frame:
                intervals.append((word.start_frame, word.end_frame_exclusive, index))
            cursor = word.end_frame_exclusive
    if cursor < cue.end_frame_exclusive:
        intervals.append((cursor, cue.end_frame_exclusive, 0))
    images, css = [], []
    for start, end, index in intervals:
        name = "ass-state-" + hashlib.sha256(f"{cue.caption_track_id}:{cue.segment_id}:{start}:{index}".encode()).hexdigest()
        images.append(f'<img class="{name}" src="{states[index]}" alt="{escape(cue.text)}" '
                      'style="position:absolute;inset:0;width:100%;height:100%"/>')
        css.append(f".{name}{{animation:{name} {duration}s step-end both paused}}")
        css.append(visibility(name, start_frame=start, end_frame=end,
                              total_frames=timeline.total_frames, fps=timeline.delivery_profile.fps,
                              serialized_duration=duration, target_opacity="1"))
    return "".join(images), tuple(css)
