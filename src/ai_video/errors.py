from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    CONFIG_INVALID = "config_invalid"
    WORKFLOW_INVALID = "workflow_invalid"
    BINDING_INVALID = "binding_invalid"
    COMFY_UNAVAILABLE = "comfy_unavailable"
    COMFY_SUBMISSION_FAILED = "comfy_submission_failed"
    COMFY_QUEUE_TIMEOUT = "comfy_queue_timeout"
    COMFY_JOB_TIMEOUT = "comfy_job_timeout"
    COMFY_JOB_FAILED = "comfy_job_failed"
    COMFY_OUTPUT_MISSING = "comfy_output_missing"
    OUTPUT_INVALID = "output_invalid"
    FFMPEG_FAILED = "ffmpeg_failed"
    MANIFEST_INVALID = "manifest_invalid"
    DISK_SPACE_LOW = "disk_space_low"


@dataclass
class AiVideoError(Exception):
    code: ErrorCode
    user_message: str
    technical_detail: Optional[str] = None
    retryable: bool = False
    cause: Optional[BaseException] = None

    def __str__(self) -> str:
        return self.user_message


def config_error(code: ErrorCode, message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, technical_detail=detail, retryable=False)


def retryable_error(
    code: ErrorCode,
    message: str,
    detail: str | None = None,
    cause: BaseException | None = None,
) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=detail,
        retryable=True,
        cause=cause,
    )
