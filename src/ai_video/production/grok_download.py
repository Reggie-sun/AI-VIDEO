"""Pinned, credential-free Grok video result downloads."""

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
        user_message="Grok video result must use the documented public HTTPS origin.",
    )


def parse_grok_result_url(url: str) -> ViduResultLocator:
    """Require the documented host before using the shared pinned-IP downloader."""

    try:
        locator = parse_result_url(url)
    except AiVideoError:
        raise _invalid_locator() from None
    if locator.origin != GROK_VIDEO_RESULT_ORIGIN:
        raise _invalid_locator()
    return locator


@contextmanager
def stream_public_grok_video(url: str, *, timeout_seconds: float) -> Iterator[object]:
    """Stream a Grok result without credentials, redirects, or unpinned DNS."""

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
