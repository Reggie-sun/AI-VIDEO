"""Credential-free Grok video result downloads."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.vidu_download import (
    ViduResultLocator,
    parse_result_url,
    stream_public_video,
)


GROK_VIDEO_RESULT_ORIGIN = "https://vidgen.x.ai"


def _invalid_locator() -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_ARTIFACT_INVALID,
        user_message="Grok video result requires a valid credential-free HTTP(S) locator.",
    )


def parse_grok_result_url(url: str) -> ViduResultLocator:
    """Validate a result locator without constraining its origin."""

    try:
        return parse_result_url(url)
    except AiVideoError:
        raise _invalid_locator() from None


@contextmanager
def stream_public_grok_video(url: str, *, timeout_seconds: float) -> Iterator[object]:
    """Stream a Grok result without credentials or cookies on any redirect hop."""

    parse_grok_result_url(url)
    try:
        with stream_public_video(url, timeout_seconds=timeout_seconds) as response:
            yield response
    except AiVideoError:
        raise _invalid_locator() from None


__all__ = [
    "GROK_VIDEO_RESULT_ORIGIN",
    "parse_grok_result_url",
    "stream_public_grok_video",
]
