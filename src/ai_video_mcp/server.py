from __future__ import annotations

import asyncio
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import get_config, ServerConfig
from ai_video_mcp.errors import McpError
from ai_video_mcp.tools.analyze import video_analyze as _video_analyze
from ai_video_mcp.tools.apply_optimization import apply_video_optimization as _apply_video_optimization
from ai_video_mcp.tools.frames import video_extract_frames as _video_extract_frames
from ai_video_mcp.tools.optimize_plan import video_optimize_plan as _video_optimize_plan
from ai_video_mcp.tools.probe import video_probe as _video_probe
from ai_video_mcp.tools.review import video_review as _video_review
from ai_video_mcp.tools.scene_detect import video_scene_detect as _video_scene_detect
from ai_video_mcp.tools.transcribe import video_transcribe as _video_transcribe

config = get_config()
cache = AnalysisCache(max_size=config.cache_max_size, ttl_seconds=config.cache_ttl_seconds)

mcp = FastMCP(
    name="video-analysis",
    instructions=(
        "Video analysis tools: probe metadata, extract keyframes as base64 images, "
        "transcribe audio via Whisper, detect scene changes, and review videos for optimization guidance. "
        "Use video_analyze for comprehensive analysis, video_review for actionable optimization hints, "
        "video_optimize_plan for repo-file optimization targets, video_apply_optimization for safe auto-edits, "
        "or individual tools for targeted queries."
    ),
)


def _handle_error(e: Exception) -> dict:
    if isinstance(e, McpError):
        return e.to_dict()
    return {"error": "internal", "message": str(e)}


@mcp.tool()
async def video_probe(video_path: str, ctx: Context) -> dict:
    """Extract video metadata: duration, resolution, fps, codec, bitrate, audio info.

    Args:
        video_path: Absolute path to the video file
    """
    try:
        return await asyncio.to_thread(_video_probe, video_path, config, cache)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def video_extract_frames(
    video_path: str,
    interval_seconds: Optional[float] = None,
    max_frames: Optional[int] = None,
    width: Optional[int] = None,
    quality: Optional[int] = None,
    format: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """Extract keyframes from a video as base64-encoded images for visual analysis.

    Args:
        video_path: Absolute path to the video file
        interval_seconds: Seconds between frames (default: 5.0)
        max_frames: Maximum frames to return (default: 20)
        width: Resize width in pixels, 0 for original (default: 640)
        quality: JPEG quality 1-100 (default: 75)
        format: Image format "jpeg" or "png" (default: "jpeg")
    """
    try:
        return await asyncio.to_thread(
            _video_extract_frames,
            video_path, config, cache,
            interval_seconds=interval_seconds,
            max_frames=max_frames,
            width=width,
            quality=quality,
            fmt=format,
        )
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def video_transcribe(
    video_path: str,
    model: Optional[str] = None,
    language: Optional[str] = None,
    word_timestamps: bool = False,
    ctx: Context = None,
) -> dict:
    """Transcribe video audio using Whisper with timestamps.

    Args:
        video_path: Absolute path to the video file
        model: Whisper model name (tiny/base/small/medium/large, default: base)
        language: Language code e.g. "en", "zh" (default: auto-detect)
        word_timestamps: Include word-level timestamps (default: false)
    """
    try:
        return await asyncio.to_thread(
            _video_transcribe,
            video_path, config, cache,
            model=model,
            language=language,
            word_timestamps=word_timestamps,
        )
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def video_scene_detect(
    video_path: str,
    threshold: Optional[float] = None,
    min_scene_length_seconds: Optional[float] = None,
    ctx: Context = None,
) -> dict:
    """Detect scene changes (hard cuts) in a video.

    Args:
        video_path: Absolute path to the video file
        threshold: Scene change score 0-1, lower=more sensitive (default: 0.4)
        min_scene_length_seconds: Minimum seconds between scenes (default: 1.0)
    """
    try:
        return await asyncio.to_thread(
            _video_scene_detect,
            video_path, config, cache,
            threshold=threshold,
            min_scene_length_seconds=min_scene_length_seconds,
        )
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def video_analyze(
    video_path: str,
    extract_frames: bool = True,
    frame_interval: Optional[float] = None,
    max_frames: Optional[int] = None,
    transcribe_audio: bool = True,
    whisper_model: Optional[str] = None,
    detect_scenes: bool = True,
    scene_threshold: Optional[float] = None,
    ctx: Context = None,
) -> dict:
    """Comprehensive video analysis: metadata + keyframes + transcription + scene detection.

    Args:
        video_path: Absolute path to the video file
        extract_frames: Whether to extract keyframes (default: true)
        frame_interval: Seconds between frames (default: 5.0)
        max_frames: Maximum frames (default: 20)
        transcribe_audio: Whether to transcribe audio (default: true)
        whisper_model: Whisper model name (default: base)
        detect_scenes: Whether to detect scene changes (default: true)
        scene_threshold: Scene change threshold (default: 0.4)
    """
    try:
        return await asyncio.to_thread(
            _video_analyze,
            video_path, config, cache,
            extract_frames=extract_frames,
            frame_interval=frame_interval,
            max_frames=max_frames,
            transcribe_audio=transcribe_audio,
            whisper_model=whisper_model,
            detect_scenes=detect_scenes,
            scene_threshold=scene_threshold,
        )
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def video_review(
    video_path: str,
    frame_interval: Optional[float] = None,
    max_frames: Optional[int] = None,
    scene_threshold: Optional[float] = None,
    transcribe_audio: bool = False,
    ctx: Context = None,
) -> dict:
    """Review a rendered video and return actionable optimization hints for workflow/config/code iteration.

    Args:
        video_path: Absolute path to the video file
        frame_interval: Seconds between extracted frames (default: config default)
        max_frames: Maximum extracted frames (default: config default)
        scene_threshold: Scene change threshold (default: 0.4)
        transcribe_audio: Whether to include Whisper speaking-duration evidence (default: false)
    """
    try:
        return await asyncio.to_thread(
            _video_review,
            video_path,
            config,
            cache,
            frame_interval=frame_interval,
            max_frames=max_frames,
            scene_threshold=scene_threshold,
            transcribe_audio=transcribe_audio,
        )
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def video_optimize_plan(
    video_path: str,
    project_path: Optional[str] = None,
    shots_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """Map video review issues to concrete repo files and suggested edits.

    Args:
        video_path: Absolute path to the rendered video file
        project_path: Optional absolute path to a project config file
        shots_path: Optional absolute path to a shot list file
        manifest_path: Optional absolute path to a run manifest that can provide project and shot paths
    """
    try:
        return await asyncio.to_thread(
            _video_optimize_plan,
            video_path,
            config,
            cache,
            project_path=project_path,
            shots_path=shots_path,
            manifest_path=manifest_path,
        )
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="video_apply_optimization")
async def video_apply_optimization(
    video_path: str,
    project_path: Optional[str] = None,
    shots_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """Apply safe optimization edits to project and shot files based on detected video issues.

    Args:
        video_path: Absolute path to the rendered video file
        project_path: Optional absolute path to a project config file
        shots_path: Optional absolute path to a shot list file
        manifest_path: Optional absolute path to a run manifest that can provide project and shot paths
    """
    try:
        return await asyncio.to_thread(
            _apply_video_optimization,
            video_path,
            config,
            cache,
            project_path=project_path,
            shots_path=shots_path,
            manifest_path=manifest_path,
        )
    except Exception as e:
        return _handle_error(e)
