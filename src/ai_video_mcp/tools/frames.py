from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path

from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.errors import McpError, McpErrorCode
from ai_video_mcp.tools.probe import _validate_video, _format_duration, video_probe


def _compute_timestamps(duration: float, interval: float, max_frames: int, *, fps: float) -> list[float]:
    if duration <= 0:
        return [0.0]
    frame_margin = 1.0 / fps if fps > 0 else 0.1
    cutoff = max(0.0, duration - frame_margin)
    count = int(duration / interval) + 1
    if count <= max_frames:
        timestamps = [round(i * interval, 3) for i in range(count) if i * interval < cutoff]
        return timestamps or [0.0]
    step = duration / max_frames
    timestamps = [round(i * step, 3) for i in range(max_frames) if i * step < cutoff]
    return timestamps or [0.0]


def _extract_single_frame(
    video_path: Path,
    timestamp: float,
    output_path: Path,
    width: int,
    quality: int,
    fmt: str,
) -> dict:
    ext = "jpg" if fmt == "jpeg" else "png"
    out_file = output_path / f"frame_{timestamp:.3f}.{ext}"

    scale_filter = f"scale={width}:-1" if width > 0 else ""
    vf_parts = []
    if scale_filter:
        vf_parts.append(scale_filter)
    vf = ",".join(vf_parts) if vf_parts else None

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-frames:v", "1",
    ]
    if vf:
        cmd += ["-vf", vf]
    if fmt == "jpeg":
        cmd += ["-q:v", str(max(1, min(31, 31 - quality * 31 // 100)))]
    cmd.append(str(out_file))

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            f"Frame extraction failed at {timestamp}s",
            detail=(exc.stderr or str(exc)).strip(),
        ) from exc

    if not out_file.exists() or out_file.stat().st_size == 0:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            f"Extracted frame is empty at {timestamp}s",
        )

    img_data = out_file.read_bytes()
    b64 = base64.b64encode(img_data).decode("ascii")

    return {
        "timestamp_seconds": timestamp,
        "timestamp_hms": _format_duration(timestamp),
        "format": fmt,
        "width": width if width > 0 else 0,
        "size_bytes": len(img_data),
        "base64": b64,
    }


def video_extract_frames(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    interval_seconds: float | None = None,
    max_frames: int | None = None,
    width: int | None = None,
    quality: int | None = None,
    fmt: str | None = None,
) -> dict:
    p = _validate_video(video_path, config)

    interval = interval_seconds if interval_seconds is not None else config.frame_interval
    max_f = max_frames if max_frames is not None else config.max_frames
    w = width if width is not None else config.frame_width
    q = quality if quality is not None else config.frame_quality
    f = fmt if fmt is not None else config.frame_format

    if interval <= 0:
        raise McpError(McpErrorCode.INVALID_PARAMETER, "interval_seconds must be > 0")
    if max_f <= 0:
        raise McpError(McpErrorCode.INVALID_PARAMETER, "max_frames must be > 0")

    probe_result = video_probe(video_path, config, cache)
    duration = probe_result["file"]["duration_seconds"]
    fps = float(probe_result.get("video_stream", {}).get("fps") or 0.0)

    timestamps = _compute_timestamps(duration, interval, max_f, fps=fps)

    frames = []
    with tempfile.TemporaryDirectory(prefix="video_mcp_frames_") as tmpdir:
        tmp = Path(tmpdir)
        for ts in timestamps:
            frame = _extract_single_frame(p, ts, tmp, w, q, f)
            frames.append(frame)

    return {
        "video_path": str(p),
        "total_frames_extracted": len(frames),
        "interval_used": interval if len(frames) <= max_f else round(duration / max_f, 3),
        "frames": frames,
    }
