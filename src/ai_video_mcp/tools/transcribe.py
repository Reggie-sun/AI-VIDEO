from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.errors import McpError, McpErrorCode
from ai_video_mcp.tools.probe import _validate_video, _format_duration, video_probe

_model_cache: dict[str, object] = {}


def _get_whisper_model(model_name: str):
    if model_name not in _model_cache:
        try:
            import whisper
            _model_cache[model_name] = whisper.load_model(model_name)
        except Exception as exc:
            raise McpError(
                McpErrorCode.WHISPER_FAILED,
                f"Failed to load Whisper model '{model_name}'",
                detail=str(exc),
            ) from exc
    return _model_cache[model_name]


def _extract_audio(video_path: Path, output_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            "Audio extraction failed",
            detail=(exc.stderr or str(exc)).strip(),
        ) from exc


def video_transcribe(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    model: str | None = None,
    language: str | None = None,
    word_timestamps: bool = False,
) -> dict:
    p = _validate_video(video_path, config)

    model_name = model if model is not None else config.whisper_model
    lang = language if language is not None else config.whisper_language

    import whisper as _w
    available = _w.available_models()
    if model_name not in available:
        raise McpError(
            McpErrorCode.INVALID_PARAMETER,
            f"Unknown Whisper model '{model_name}'. Available: {', '.join(available)}",
        )

    cached = cache.get(p, "transcribe", model=model_name, language=lang)
    if cached is not None:
        return cached

    probe_result = video_probe(video_path, config, cache)
    has_audio = probe_result.get("audio_stream") is not None
    if not has_audio:
        raise McpError(
            McpErrorCode.NO_AUDIO_STREAM,
            "No audio stream found in video file",
        )

    duration = probe_result["file"]["duration_seconds"]

    with tempfile.TemporaryDirectory(prefix="video_mcp_audio_") as tmpdir:
        audio_path = Path(tmpdir) / "audio.wav"
        _extract_audio(p, audio_path)

        whisper_model = _get_whisper_model(model_name)

        try:
            result = whisper_model.transcribe(
                str(audio_path),
                language=lang,
                word_timestamps=word_timestamps,
            )
        except Exception as exc:
            raise McpError(
                McpErrorCode.WHISPER_FAILED,
                "Whisper transcription failed",
                detail=str(exc),
            ) from exc

    detected_lang = result.get("language", lang or "unknown")

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "id": seg.get("id", 0),
            "start": round(seg.get("start", 0), 3),
            "end": round(seg.get("end", 0), 3),
            "start_hms": _format_duration(seg.get("start", 0)),
            "end_hms": _format_duration(seg.get("end", 0)),
            "text": seg.get("text", "").strip(),
        })

    full_text = "\n".join(s["text"] for s in segments if s["text"])

    result_data = {
        "video_path": str(p),
        "model": model_name,
        "language": detected_lang,
        "duration_seconds": round(duration, 3),
        "segments": segments,
        "full_text": full_text,
    }

    cache.set(p, "transcribe", result_data, model=model_name, language=lang)
    return result_data
