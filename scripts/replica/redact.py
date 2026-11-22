"""Bake privacy masks into local screen recordings with source-pixel rectangles."""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.ffmpeg_tools import run_command

from ._local import cli, read_json, tool_path
from .gridshot import video_input_options

FRAME = 1 / 30


def _even_span(a: int, b: int) -> tuple[int, int]:
    """Grow an odd span by one pixel, towards zero where possible."""
    if (b - a) % 2:
        return (a - 1, b) if a > 0 else (a, b + 1)
    return a, b


def _rectangle(rect):
    if not isinstance(rect, list) or len(rect) not in (6, 7):
        raise ValueError("Each mask requires four pixel coordinates and two timestamps.")
    x0, y0, x1, y1, t0, t1 = rect[:6]
    if (
        not all(type(value) is int for value in (x0, y0, x1, y1))
        or not (0 <= x0 < x1 and 0 <= y0 < y1)
        or not all(type(value) in (int, float) and isfinite(value) for value in (t0, t1))
        or not (0 <= t0 < t1)
    ):
        raise ValueError("Mask bounds and timestamps must define a nonempty region.")
    x0, x1 = _even_span(x0, x1)
    y0, y1 = _even_span(y0, y1)
    return x0, y0, x1, y1, t0, t1


def filter_graph(rects) -> tuple[str, str]:
    parts = ["[0:v]fps=30[v0]"]
    cur = "v0"
    for index, rect in enumerate(rects):
        x0, y0, x1, y1, t0, t1 = _rectangle(rect)
        width, height = x1 - x0, y1 - y0
        small_width, small_height = max(2, width // 14), max(2, height // 14)
        start = round(max(0.0, t0 - FRAME), 3)
        end = round(t1 + FRAME, 3)
        parts.append(f"[{cur}]format=yuv444p,split[a{index}][b{index}]")
        parts.append(
            f"[b{index}]crop={width}:{height}:{x0}:{y0}:exact=1,"
            f"scale={small_width}:{small_height}:flags=area,"
            f"scale={width}:{height}:flags=neighbor,gblur=sigma=6[c{index}]"
        )
        parts.append(
            f"[a{index}][c{index}]overlay={x0}:{y0}:format=yuv444:"
            f"enable='between(t,{start},{end})'[v{index + 1}]"
        )
        cur = f"v{index + 1}"
    return ";".join(parts), cur


def _relative_clip(root: Path, name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix.lower() not in {".mp4", ".mov"}:
        raise ValueError("The mask recipe requires relative MP4 or MOV paths.")
    clip = root / relative
    if clip.is_symlink() or not clip.resolve().is_relative_to(root):
        raise ValueError("A mask recipe clip must stay within its supplied root.")
    return clip


def _source_bounds(source: Path, ffprobe: Path) -> tuple[int, int, float]:
    result = run_command([str(ffprobe), "-v", "error", *video_input_options(source),
                          "-select_streams", "v:0", "-show_streams", "-of", "json", str(source)])
    streams = json.loads(result.stdout)["streams"]
    if not streams:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "A screen recording needs a video stream.")
    stream = streams[0]
    width, height = stream["width"], stream["height"]
    rotation = next((item["rotation"] for item in stream.get("side_data_list", []) if "rotation" in item),
                    stream.get("tags", {}).get("rotate", 0))
    rotation = float(rotation)
    if rotation % 90:
        raise ValueError("Mask calculation requires a right-angle source orientation.")
    if rotation % 180:
        width, height = height, width
    duration = float(stream["duration"])
    if not isfinite(duration) or duration <= 0:
        raise ValueError("Mask calculation requires a finite video duration.")
    return width, height, duration


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--ffprobe", type=Path)
    args = parser.parse_args(argv)
    ffmpeg = tool_path("ffmpeg", args.ffmpeg)
    ffprobe = tool_path("ffprobe", args.ffprobe)
    source_root = args.source_root.resolve(strict=True)
    output_root = args.output_root.resolve()
    jobs = read_json(args.recipe)["jobs"]
    if not jobs:
        raise ValueError("The mask recipe requires at least one clip.")
    prepared = {}
    for job in jobs:
        source = _relative_clip(source_root, job["input"])
        target = _relative_clip(output_root, job["output"])
        if not source.is_file() or target.exists() or target.resolve() in prepared or not job["rects"]:
            raise AiVideoError(ErrorCode.CONFIG_INVALID, "Masking requires a source, masks, and a new output path.")
        width, height, duration = _source_bounds(source, ffprobe)
        for rect in job["rects"]:
            _, _, x1, y1, start, end = _rectangle(rect)
            if x1 > width or y1 > height or start >= duration or end > duration + FRAME:
                raise AiVideoError(ErrorCode.CONFIG_INVALID, "Mask extends past the recording bounds.")
        graph, last = filter_graph(job["rects"])
        prepared[target.resolve()] = source, graph, last
    for target, (source, graph, last) in prepared.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".replica-redact-", dir=target.parent) as tmp:
            candidate = Path(tmp) / target.name
            run_command([str(ffmpeg), "-nostdin", "-v", "error", *video_input_options(source),
                         "-i", str(source), "-filter_complex", graph, "-map", f"[{last}]", "-an",
                         "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
                         "-r", "30", str(candidate)])
            if not candidate.is_file() or not candidate.stat().st_size:
                raise AiVideoError(ErrorCode.OUTPUT_INVALID, "FFmpeg did not produce a redacted clip.")
            target.hardlink_to(candidate)
        print("ok", target)


if __name__ == "__main__":
    cli(main)
