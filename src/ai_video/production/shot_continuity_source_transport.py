"""Concrete loopback transport for Shot Continuity source qualification."""

from __future__ import annotations

import hashlib
from typing import Any

import httpx

from ai_video.comfy_client import ComfyClient, JobResult
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import validate_loopback_endpoint
from ai_video.production.shot_continuity_source_contracts import (
    SourceQualificationInput,
)


SOURCE_COMFY_BASE_URL = "http://127.0.0.1:8188"
SOURCE_COMFY_DEPLOYMENT_IDENTITY = "loopback-127.0.0.1-8188"


class ComfySourceQualificationTransport:
    """Bind every ComfyUI operation to one exact validated loopback origin."""

    deployment_identity = SOURCE_COMFY_DEPLOYMENT_IDENTITY

    def __init__(
        self,
        *,
        base_url: str = SOURCE_COMFY_BASE_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        canonical = validate_loopback_endpoint(base_url)
        if canonical != SOURCE_COMFY_BASE_URL:
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="Source qualification requires the sealed ComfyUI loopback endpoint.",
                retryable=False,
            )
        if http_client is None:
            http_client = httpx.Client(
                timeout=30,
                trust_env=False,
                follow_redirects=False,
            )
        self.base_url = canonical
        self._client = ComfyClient(canonical, http_client=http_client)

    def get_object_info(self) -> dict[str, Any]:
        return self._client.get_object_info()

    def upload_input(self, item: SourceQualificationInput) -> str:
        if (
            len(item.data) != item.size_bytes
            or hashlib.sha256(item.data).hexdigest() != item.file_sha256
        ):
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="Source qualification input bytes do not match their seal.",
                retryable=False,
            )
        return self._client.upload_input_bytes(item.file_name, item.data)

    def submit_prompt(self, workflow: dict[str, Any]) -> str:
        return self._client.submit_prompt(workflow)

    def poll_job(
        self,
        prompt_id: str,
        *,
        poll_interval_seconds: float,
        timeout_seconds: float,
    ) -> JobResult:
        return self._client.poll_job(
            prompt_id,
            poll_interval_seconds=poll_interval_seconds,
            timeout_seconds=timeout_seconds,
        )

    def fetch_artifact_bytes(
        self,
        *,
        filename: str,
        subfolder: str,
        type_: str,
    ) -> bytes:
        return self._client.fetch_artifact_bytes(
            filename=filename,
            subfolder=subfolder,
            type_=type_,
        )


__all__ = [
    "ComfySourceQualificationTransport",
    "SOURCE_COMFY_BASE_URL",
    "SOURCE_COMFY_DEPLOYMENT_IDENTITY",
]
