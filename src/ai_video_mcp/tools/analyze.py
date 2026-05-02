from __future__ import annotations

from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.tools.frames import video_extract_frames
from ai_video_mcp.tools.probe import _validate_video, video_probe
from ai_video_mcp.tools.scene_detect import video_scene_detect
from ai_video_mcp.tools.transcribe import video_transcribe


def video_analyze(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    extract_frames: bool = True,
    frame_interval: float | None = None,
    max_frames: int | None = None,
    transcribe_audio: bool = True,
    whisper_model: str | None = None,
    detect_scenes: bool = True,
    scene_threshold: float | None = None,
) -> dict:
    p = _validate_video(video_path, config)

    probe_result = video_probe(video_path, config, cache)

    frames_result = None
    transcription_result = None
    scenes_result = None

    if extract_frames:
        frames_result = video_extract_frames(
            video_path, config, cache,
            interval_seconds=frame_interval,
            max_frames=max_frames,
        )

    if detect_scenes:
        scenes_result = video_scene_detect(
            video_path, config, cache,
            threshold=scene_threshold,
        )

    if transcribe_audio and probe_result.get("audio_stream") is not None:
        transcription_result = video_transcribe(
            video_path, config, cache,
            model=whisper_model,
        )

    duration = probe_result["file"]["duration_seconds"]
    resolution = f"{probe_result['video_stream']['width']}x{probe_result['video_stream']['height']}"
    has_audio = probe_result.get("audio_stream") is not None

    speaking_duration = 0.0
    if transcription_result:
        for seg in transcription_result.get("segments", []):
            if seg.get("text", "").strip():
                speaking_duration += seg["end"] - seg["start"]

    summary = {
        "duration_hms": probe_result["file"]["duration_hms"],
        "resolution": resolution,
        "has_audio": has_audio,
        "estimated_speaking_duration_seconds": round(speaking_duration, 1),
        "scene_count": scenes_result["total_scenes"] if scenes_result else 0,
        "frames_extracted": frames_result["total_frames_extracted"] if frames_result else 0,
    }

    return {
        "video_path": str(p),
        "probe": probe_result,
        "frames": frames_result,
        "transcription": transcription_result,
        "scenes": scenes_result,
        "analysis_summary": summary,
    }
