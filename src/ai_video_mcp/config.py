from __future__ import annotations

from pydantic_settings import BaseSettings


class ServerConfig(BaseSettings):
    # Frame extraction
    frame_interval: float = 5.0
    max_frames: int = 20
    frame_width: int = 640
    frame_quality: int = 75
    frame_format: str = "jpeg"

    # Whisper
    whisper_model: str = "base"
    whisper_language: str | None = None

    # Scene detection
    scene_threshold: float = 0.4
    min_scene_length_seconds: float = 1.0

    # Caching
    cache_max_size: int = 32
    cache_ttl_seconds: int = 3600

    # Limits
    max_video_duration_seconds: int = 7200
    max_video_file_size_mb: int = 4096

    # Remote audio analysis is opt-in; these are non-secret operator bindings.
    audio_media_root: str | None = None
    audio_model_id: str = "gemini-3.8-flash"
    audio_runtime_factory: str | None = None

    model_config = {"env_prefix": "VIDEO_MCP_"}


def get_config() -> ServerConfig:
    return ServerConfig()
