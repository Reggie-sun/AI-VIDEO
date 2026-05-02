from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class McpErrorCode(str, Enum):
    FILE_NOT_FOUND = "file_not_found"
    FILE_TOO_LARGE = "file_too_large"
    VIDEO_TOO_LONG = "video_too_long"
    NO_VIDEO_STREAM = "no_video_stream"
    NO_AUDIO_STREAM = "no_audio_stream"
    FFMPEG_FAILED = "ffmpeg_failed"
    WHISPER_FAILED = "whisper_failed"
    INVALID_PARAMETER = "invalid_parameter"
    INTERNAL_ERROR = "internal_error"


@dataclass
class McpError(Exception):
    code: McpErrorCode
    message: str
    detail: str | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict:
        return {"error": self.code.value, "message": self.message, "detail": self.detail}
