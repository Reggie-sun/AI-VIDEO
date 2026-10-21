from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

from ai_video.download import stream_public_video
from ai_video.errors import AiVideoError, ErrorCode, retryable_error


_ARTIFACT_HTTP_EXCHANGE: ContextVar[bool] = ContextVar("comfy_artifact_http_exchange", default=False)


class _ArtifactHttpLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # HTTPcore DEBUG includes response headers, including signed Location and
        # Set-Cookie. Suppress only this request context, without changing logger
        # levels, handlers, or diagnostics emitted by concurrent requests.
        return not _ARTIFACT_HTTP_EXCHANGE.get()


_artifact_http_log_filter = _ArtifactHttpLogFilter()
for _logger_name in (
    "httpx", "httpcore.connection", "httpcore.http11", "httpcore.http2",
    "httpcore.proxy", "httpcore.socks",
):
    logging.getLogger(_logger_name).addFilter(_artifact_http_log_filter)


@contextmanager
def _artifact_http_logging_scope():
    token = _ARTIFACT_HTTP_EXCHANGE.set(True)
    try:
        yield
    finally:
        _ARTIFACT_HTTP_EXCHANGE.reset(token)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MISSING = "missing"
    TIMEOUT = "timeout"


@dataclass
class JobResult:
    status: JobStatus
    prompt_id: str
    history: dict[str, Any] | None = None
    error: AiVideoError | None = None


class ComfyClient:
    def __init__(self, base_url: str, http_client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client or httpx.Client(timeout=30)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def check_available(self) -> None:
        try:
            response = self.http.get(self._url("/system_stats"))
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise retryable_error(
                ErrorCode.COMFY_UNAVAILABLE,
                "ComfyUI is unavailable.",
                str(exc),
                exc,
            ) from exc

    def get_object_info(self) -> dict[str, Any]:
        """Return the server's registered node inventory without mutating state."""

        try:
            response = self.http.get(self._url("/object_info"))
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise retryable_error(
                ErrorCode.COMFY_UNAVAILABLE,
                "Could not read the ComfyUI node inventory.",
                str(exc),
                exc,
            ) from exc
        if not isinstance(payload, dict):
            raise AiVideoError(
                ErrorCode.COMFY_UNAVAILABLE,
                "ComfyUI returned an invalid node inventory.",
                retryable=False,
            )
        return payload

    def upload_input(self, path: str | Path) -> str:
        input_path = Path(path)
        try:
            with input_path.open("rb") as handle:
                return self._upload_input_payload(input_path.name, handle)
        except OSError as exc:
            raise retryable_error(
                ErrorCode.COMFY_SUBMISSION_FAILED,
                f"Could not upload ComfyUI input: {input_path}",
                str(exc),
                exc,
            ) from exc

    def upload_input_bytes(self, filename: str, payload: bytes) -> str:
        """Upload an immutable in-memory input through the canonical route."""

        return self._upload_input_payload(filename, bytes(payload))

    def _upload_input_payload(self, filename: str, payload: Any) -> str:
        try:
            response = self.http.post(
                self._url("/upload/image"),
                files={"image": (filename, payload)},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise retryable_error(
                ErrorCode.COMFY_SUBMISSION_FAILED,
                f"Could not upload ComfyUI input: {filename}",
                str(exc),
                exc,
            ) from exc
        data = response.json()
        return data.get("name") or data.get("filename") or filename

    def upload_image(self, path: str | Path) -> str:
        return self.upload_input(path)

    def prepare_image(self, path: str | Path) -> str:
        return self.upload_image(path)

    def submit_prompt(self, workflow: dict[str, Any]) -> str:
        try:
            response = self.http.post(self._url("/prompt"), json={"prompt": workflow})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise retryable_error(
                ErrorCode.COMFY_SUBMISSION_FAILED,
                "Could not submit workflow to ComfyUI.",
                str(exc),
                exc,
            ) from exc
        data = response.json()
        if data.get("error") or data.get("node_errors"):
            raise AiVideoError(
                code=ErrorCode.COMFY_SUBMISSION_FAILED,
                user_message="ComfyUI rejected the workflow.",
                technical_detail=str(data),
                retryable=False,
            )
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise AiVideoError(
                code=ErrorCode.COMFY_SUBMISSION_FAILED,
                user_message="ComfyUI response did not include prompt_id.",
                technical_detail=str(data),
                retryable=False,
            )
        return str(prompt_id)

    def poll_job(
        self,
        prompt_id: str,
        *,
        poll_interval_seconds: float,
        timeout_seconds: float,
    ) -> JobResult:
        deadline = time.monotonic() + timeout_seconds
        last_error: AiVideoError | None = None
        while time.monotonic() <= deadline:
            history = self._get_history(prompt_id)
            if history is not None:
                status = history.get("status")
                if isinstance(status, dict) and status.get("status_str") == "error":
                    error = AiVideoError(
                        code=ErrorCode.COMFY_JOB_FAILED,
                        user_message="ComfyUI generation failed.",
                        technical_detail=str(history),
                        retryable=True,
                    )
                    return JobResult(JobStatus.FAILED, prompt_id, history=history, error=error)
                if history.get("outputs"):
                    return JobResult(JobStatus.COMPLETED, prompt_id, history=history)

            queued = self._is_in_queue(prompt_id)
            if queued:
                time.sleep(poll_interval_seconds)
                continue
            last_error = AiVideoError(
                code=ErrorCode.COMFY_OUTPUT_MISSING,
                user_message=f"ComfyUI history is missing for prompt {prompt_id}.",
                retryable=True,
            )
            if poll_interval_seconds:
                time.sleep(poll_interval_seconds)
            else:
                break

        return JobResult(JobStatus.TIMEOUT, prompt_id, error=last_error)

    def _get_history(self, prompt_id: str) -> dict[str, Any] | None:
        try:
            response = self.http.get(self._url(f"/history/{prompt_id}"))
            if response.status_code == 404:
                return None
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        data = response.json()
        if prompt_id in data:
            return data[prompt_id]
        if "outputs" in data:
            return data
        return None

    def _is_in_queue(self, prompt_id: str) -> bool:
        try:
            response = self.http.get(self._url("/queue"))
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        data = response.json()
        for key in ("queue_running", "queue_pending"):
            for item in data.get(key, []):
                if isinstance(item, (list, tuple)) and prompt_id in item:
                    return True
                if isinstance(item, dict) and item.get("prompt_id") == prompt_id:
                    return True
        return False

    def _get_artifact(self, *, filename: str, subfolder: str, type_: str) -> bytes:
        # Only the selected ComfyUI endpoint receives API authentication. Artifact
        # redirects use the shared non-logging downloader without ambient secrets.
        with _artifact_http_logging_scope(), self.http.stream(
            "GET", self._url("/view"),
            params={"filename": filename, "subfolder": subfolder, "type": type_},
            follow_redirects=False,
        ) as response:
            if not response.has_redirect_location:
                response.raise_for_status()
                return response.read()
            target = response.request.url.join(response.headers["location"])
            target = target.copy_with(username="", password="")
        with stream_public_video(str(target), timeout_seconds=30) as downloaded:
            if not 200 <= downloaded.status_code < 300:
                raise AiVideoError(
                    ErrorCode.COMFY_OUTPUT_MISSING,
                    "ComfyUI artifact download failed.",
                )
            return b"".join(downloaded.iter_bytes())

    def download_artifact(
        self,
        *,
        filename: str,
        subfolder: str,
        type_: str,
        target: str | Path,
    ) -> None:
        target_path = Path(target)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            content = self._get_artifact(filename=filename, subfolder=subfolder, type_=type_)
        except (httpx.HTTPError, AiVideoError) as exc:
            raise retryable_error(
                ErrorCode.COMFY_OUTPUT_MISSING,
                f"Could not download ComfyUI artifact: {filename}",
                type(exc).__name__,
                exc,
            ) from exc
        target_path.write_bytes(content)

    def fetch_artifact_bytes(
        self,
        *,
        filename: str,
        subfolder: str,
        type_: str,
    ) -> bytes:
        """Byte-returning variant of :meth:`download_artifact` for adapters that
        must not write to a project path (e.g. P7.1 local image provider).

        Preserves the original ``download_artifact`` semantics; the new method
        does not mutate the filesystem.
        """
        try:
            content = self._get_artifact(filename=filename, subfolder=subfolder, type_=type_)
        except (httpx.HTTPError, AiVideoError) as exc:
            raise retryable_error(
                ErrorCode.COMFY_OUTPUT_MISSING,
                f"Could not fetch ComfyUI artifact bytes: {filename}",
                type(exc).__name__,
                exc,
            ) from exc
        return content

    def free_memory(self) -> None:
        try:
            self.http.post(self._url("/free"), json={"unload_models": True, "free_memory": True})
        except httpx.HTTPError:
            return

    def submit_and_collect_clip(self, workflow: dict[str, Any], output_path: Path) -> str:
        prompt_id = self.submit_prompt(workflow)
        result = self.poll_job(prompt_id, poll_interval_seconds=2, timeout_seconds=1800)
        if result.status is not JobStatus.COMPLETED:
            raise result.error or AiVideoError(
                code=ErrorCode.COMFY_JOB_TIMEOUT,
                user_message=f"ComfyUI job did not complete: {prompt_id}",
                retryable=True,
            )
        return prompt_id
