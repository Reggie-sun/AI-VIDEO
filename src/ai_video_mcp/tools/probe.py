from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.errors import McpError, McpErrorCode


def _validate_video(path: str, config: ServerConfig) -> Path:
    p = Path(path).resolve()
    if not p.exists():
        raise McpError(McpErrorCode.FILE_NOT_FOUND, f"File not found: {path}")
    if not p.is_file():
        raise McpError(McpErrorCode.FILE_NOT_FOUND, f"Not a file: {path}")
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > config.max_video_file_size_mb:
        raise McpError(
            McpErrorCode.FILE_TOO_LARGE,
            f"File too large: {size_mb:.1f}MB exceeds {config.max_video_file_size_mb}MB limit",
        )
    return p


def _run_ffprobe(path: Path) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as exc:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            "ffprobe command failed",
            detail=(exc.stderr or exc.stdout or str(exc)).strip(),
        ) from exc
    except json.JSONDecodeError as exc:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            "ffprobe returned invalid JSON",
            detail=str(exc),
        ) from exc


def _format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def video_probe(video_path: str, config: ServerConfig, cache: AnalysisCache) -> dict:
    p = _validate_video(video_path, config)

    cached = cache.get(p, "probe")
    if cached is not None:
        return cached

    raw = _run_ffprobe(p)

    fmt = raw.get("format", {})
    streams = raw.get("streams", [])

    video_stream = None
    audio_stream = None
    for s in streams:
        if s.get("codec_type") == "video" and video_stream is None:
            duration_s = float(fmt.get("duration", 0))
            if duration_s > config.max_video_duration_seconds:
                raise McpError(
                    McpErrorCode.VIDEO_TOO_LONG,
                    f"Video too long: {_format_duration(duration_s)} exceeds {_format_duration(config.max_video_duration_seconds)} limit",
                )
            fps = 0.0
            r_frame_rate = s.get("r_frame_rate", "0/0")
            try:
                num, den = r_frame_rate.split("/")
                fps = float(num) / float(den) if float(den) != 0 else 0.0
            except (ValueError, ZeroDivisionError):
                pass

            video_stream = {
                "codec": s.get("codec_name", "unknown"),
                "profile": s.get("profile"),
                "width": int(s.get("width", 0)),
                "height": int(s.get("height", 0)),
                "aspect_ratio": s.get("display_aspect_ratio", "N/A"),
                "fps": round(fps, 2),
                "pixel_format": s.get("pix_fmt"),
                "bit_rate_kbps": round(int(s.get("bit_rate", 0)) / 1000) if s.get("bit_rate") else None,
                "frame_count": int(s.get("nb_frames", 0)) if s.get("nb_frames") else None,
            }
        elif s.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = {
                "codec": s.get("codec_name", "unknown"),
                "sample_rate": int(s.get("sample_rate", 0)),
                "channels": int(s.get("channels", 0)),
                "channel_layout": s.get("channel_layout"),
                "bit_rate_kbps": round(int(s.get("bit_rate", 0)) / 1000) if s.get("bit_rate") else None,
                "language": s.get("tags", {}).get("language"),
            }

    if video_stream is None:
        raise McpError(McpErrorCode.NO_VIDEO_STREAM, "No video stream found in file")

    duration_s = float(fmt.get("duration", 0))
    result = {
        "file": {
            "path": str(p),
            "size_bytes": int(fmt.get("size", 0)),
            "size_mb": round(int(fmt.get("size", 0)) / (1024 * 1024), 2),
            "format_name": fmt.get("format_name", ""),
            "format_long_name": fmt.get("format_long_name", ""),
            "duration_seconds": round(duration_s, 3),
            "duration_hms": _format_duration(duration_s),
            "bit_rate_kbps": round(int(fmt.get("bit_rate", 0)) / 1000),
        },
        "video_stream": video_stream,
        "audio_stream": audio_stream,
        "metadata": fmt.get("tags", {}),
    }

    cache.set(p, "probe", result)
    return result
