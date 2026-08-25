"""Concrete loopback transport for Shot Continuity source qualification."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, BinaryIO, Callable

import httpx

from ai_video.comfy_client import ComfyClient, JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import validate_loopback_endpoint
from ai_video.production.comfy_video import _video_artifact
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoTaskObservation,
)
from ai_video.production.shot_continuity_source_contracts import (
    SourceQualificationInput,
    SourceQualificationTransport,
)
from ai_video.production.video import VideoTaskState


SOURCE_COMFY_BASE_URL = "http://127.0.0.1:8188"
SOURCE_COMFY_DEPLOYMENT_IDENTITY = "loopback-127.0.0.1-8188"
SOURCE_POLL_INTERVAL_SECONDS = 2.0
SOURCE_POLL_TIMEOUT_SECONDS = 1800.0


def poll_source_qualification_output(
    *,
    transport: SourceQualificationTransport,
    resolved_generation_hash: str,
    submission: LocalVideoSubmission,
    output_node_id: str,
    clock: Callable[[], datetime],
) -> LocalVideoTaskObservation:
    if submission.resolved_generation_hash != resolved_generation_hash:
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message=(
                "Source qualification submission does not match the reopened "
                "request."
            ),
            retryable=False,
        )
    job = transport.poll_job(
        submission.provider_request_id,
        poll_interval_seconds=SOURCE_POLL_INTERVAL_SECONDS,
        timeout_seconds=SOURCE_POLL_TIMEOUT_SECONDS,
    )
    if job.status is JobStatus.FAILED:
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=VideoTaskState.FAILED,
            observed_at=clock(),
        )
    if job.status is not JobStatus.COMPLETED or not isinstance(job.history, dict):
        source = job.error or AiVideoError(
            code=ErrorCode.COMFY_JOB_TIMEOUT,
            user_message=(
                "Source qualification did not return a terminal job result."
            ),
            retryable=False,
        )
        raise AiVideoError(
            code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            user_message=(
                "Source qualification outcome is unknown; explicit recovery "
                "is required."
            ),
            technical_detail=f"{source.code.value}: {source.user_message}",
            retryable=False,
            cause=source,
        ) from source
    try:
        filename, subfolder, type_ = _video_artifact(job.history, output_node_id)
    except AiVideoError as exc:
        raise AiVideoError(
            code=ErrorCode.VIDEO_PROVIDER_FAILED,
            user_message=(
                "Source qualification completed without one valid MP4 output."
            ),
            technical_detail=f"{exc.code.value}: {exc.user_message}",
            retryable=False,
            cause=exc,
        ) from exc
    return LocalVideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        progress_milli=1000,
        provider_file_id=f"{subfolder}:{filename}:{type_}",
        observed_at=clock(),
    )


def fetch_source_qualification_output(
    *,
    transport: SourceQualificationTransport,
    resolved_generation_hash: str,
    submission: LocalVideoSubmission,
    observation: LocalVideoTaskObservation,
    sink: BinaryIO,
    clock: Callable[[], datetime],
) -> LocalVideoFetchReceipt:
    if submission.resolved_generation_hash != resolved_generation_hash:
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message=(
                "Source qualification submission does not match the reopened "
                "request."
            ),
            retryable=False,
        )
    if (
        observation.submission_fingerprint != submission.submission_fingerprint
        or observation.submit_result_fingerprint
        != submission.submit_result_fingerprint
    ):
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message=(
                "Source qualification observation does not match the durable "
                "submission."
            ),
            retryable=False,
        )
    if (
        observation.state is not VideoTaskState.SUCCEEDED
        or observation.provider_file_id is None
    ):
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message=(
                "Source qualification fetch requires a succeeded observation."
            ),
            retryable=False,
        )
    try:
        subfolder, filename, type_ = observation.provider_file_id.split(":", 2)
    except ValueError as exc:
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Source qualification output locator is invalid.",
            technical_detail=str(exc),
            retryable=False,
            cause=exc,
        ) from exc
    payload = transport.fetch_artifact_bytes(
        filename=filename,
        subfolder=subfolder,
        type_=type_,
    )
    if not payload or b"ftyp" not in payload[:64]:
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Source qualification returned non-MP4 bytes.",
            retryable=False,
        )
    sink.write(payload)
    return LocalVideoFetchReceipt.create(
        submission=submission,
        observation=observation,
        content_type="video/mp4",
        size_bytes=len(payload),
        artifact_sha256=hashlib.sha256(payload).hexdigest(),
        fetched_at=clock(),
    )


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
    "fetch_source_qualification_output",
    "poll_source_qualification_output",
]
