from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.errors import McpError, McpErrorCode
from ai_video_mcp.tools.probe import _validate_video, _format_duration, video_probe


def _parse_scene_changes(stderr_text: str, threshold: float) -> list[dict]:
    timestamps = []
    for line in stderr_text.splitlines():
        t_match = re.search(r"t:([0-9.]+)", line)
        if t_match:
            t = float(t_match.group(1))
            score_match = re.search(r"scene:([0-9.]+)", line)
            score = float(score_match.group(1)) if score_match else threshold
            timestamps.append({"time": t, "score": score})
    timestamps.sort(key=lambda x: x["time"])
    return timestamps


def video_scene_detect(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    threshold: float | None = None,
    min_scene_length_seconds: float | None = None,
) -> dict:
    p = _validate_video(video_path, config)

    thresh = threshold if threshold is not None else config.scene_threshold
    min_len = min_scene_length_seconds if min_scene_length_seconds is not None else config.min_scene_length_seconds

    if not (0 < thresh < 1):
        raise McpError(McpErrorCode.INVALID_PARAMETER, "threshold must be between 0 and 1 (exclusive)")
    if min_len < 0:
        raise McpError(McpErrorCode.INVALID_PARAMETER, "min_scene_length_seconds must be >= 0")

    cache_key_suffix = f"{thresh}_{min_len}"
    cached = cache.get(p, "scene_detect", threshold=thresh, min_len=min_len)
    if cached is not None:
        return cached

    probe_result = video_probe(video_path, config, cache)
    duration = probe_result["file"]["duration_seconds"]

    cmd = [
        "ffmpeg",
        "-i", str(p),
        "-vf", f"select='gt(scene,{thresh})',showinfo",
        "-f", "null", "-",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        raise McpError(McpErrorCode.FFMPEG_FAILED, "Scene detection timed out")
    except subprocess.CalledProcessError as exc:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            "Scene detection failed",
            detail=(exc.stderr or str(exc)).strip(),
        ) from exc

    cuts = _parse_scene_changes(result.stderr, thresh)

    filtered = [cuts[0]] if cuts else []
    for c in cuts[1:]:
        if c["time"] - filtered[-1]["time"] >= min_len:
            filtered.append(c)
    cuts = filtered

    scenes = []
    for i, cut in enumerate(cuts):
        start = 0.0 if i == 0 else cuts[i - 1]["time"]
        end = cut["time"]
        scenes.append({
            "scene_number": i + 1,
            "start_time": round(start, 3),
            "start_hms": _format_duration(start),
            "end_time": round(end, 3),
            "end_hms": _format_duration(end),
            "duration_seconds": round(end - start, 3),
            "confidence": round(cut["score"], 4),
        })

    last_end = cuts[-1]["time"] if cuts else 0.0
    if last_end < duration:
        scenes.append({
            "scene_number": len(scenes) + 1,
            "start_time": round(last_end, 3),
            "start_hms": _format_duration(last_end),
            "end_time": round(duration, 3),
            "end_hms": _format_duration(duration),
            "duration_seconds": round(duration - last_end, 3),
            "confidence": None,
        })

    if not scenes:
        scenes.append({
            "scene_number": 1,
            "start_time": 0.0,
            "start_hms": _format_duration(0.0),
            "end_time": round(duration, 3),
            "end_hms": _format_duration(duration),
            "duration_seconds": round(duration, 3),
            "confidence": None,
        })

    result_data = {
        "video_path": str(p),
        "threshold": thresh,
        "total_scenes": len(scenes),
        "scenes": scenes,
    }

    cache.set(p, "scene_detect", result_data, threshold=thresh, min_len=min_len)
    return result_data
