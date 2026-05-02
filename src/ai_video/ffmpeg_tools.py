from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Sequence

from ai_video.errors import AiVideoError, ErrorCode


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise AiVideoError(
            code=ErrorCode.FFMPEG_FAILED,
            user_message=f"ffmpeg command failed: {args[0]}",
            technical_detail=detail,
            retryable=True,
            cause=exc,
        ) from exc


def probe_clip(path: str | Path) -> dict:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(result.stdout)


def validate_clip(path: str | Path) -> None:
    clip_path = Path(path)
    if not clip_path.exists() or clip_path.stat().st_size == 0:
        raise AiVideoError(
            code=ErrorCode.OUTPUT_INVALID,
            user_message=f"Generated clip is missing or empty: {clip_path}",
            retryable=True,
        )
    probe_clip(clip_path)


def extract_last_frame(source: str | Path, target: str | Path) -> None:
    source_path = Path(source)
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    def _fallback_first_frame() -> None:
        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source_path),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(target_path),
            ]
        )

    try:
        run_command(
            [
                "ffmpeg",
                "-y",
                "-sseof",
                "-0.1",
                "-i",
                str(source_path),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(target_path),
            ]
        )
    except AiVideoError:
        _fallback_first_frame()
    if not target_path.exists() or target_path.stat().st_size == 0:
        _fallback_first_frame()
    if not target_path.exists() or target_path.stat().st_size == 0:
        raise AiVideoError(
            code=ErrorCode.FFMPEG_FAILED,
            user_message=f"Could not extract last frame from {source_path}",
            retryable=True,
        )


def normalize_clip(
    source: str | Path,
    target: str | Path,
    *,
    width: int,
    height: int,
    fps: int,
    encoder: str,
) -> None:
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vf",
            f"scale={width}:{height},fps={fps}",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-c:v",
            encoder,
            str(target_path),
        ]
    )


def _escape_concat_path(path: str) -> str:
    return path.replace("'", "'\\''")


def concat_list_text(paths: Sequence[str | Path]) -> str:
    return "".join(f"file '{_escape_concat_path(str(Path(path).resolve()))}'\n" for path in paths)


def stitch_clips(normalized_clips: Sequence[str | Path], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        handle.write(concat_list_text(normalized_clips))
        list_path = Path(handle.name)
    try:
        try:
            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_path),
                    "-c",
                    "copy",
                    str(output),
                ]
            )
        except AiVideoError:
            if output.exists():
                output.unlink()
            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_path),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-an",
                    str(output),
                ]
            )
    finally:
        list_path.unlink(missing_ok=True)
