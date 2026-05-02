from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

from ai_video.errors import AiVideoError, ErrorCode, retryable_error


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

    def upload_image(self, path: str | Path) -> str:
        image_path = Path(path)
        try:
            with image_path.open("rb") as handle:
                response = self.http.post(
                    self._url("/upload/image"),
                    files={"image": (image_path.name, handle)},
                )
            response.raise_for_status()
        except (OSError, httpx.HTTPError) as exc:
            raise retryable_error(
                ErrorCode.COMFY_SUBMISSION_FAILED,
                f"Could not upload image: {image_path}",
                str(exc),
                exc if isinstance(exc, BaseException) else None,
            ) from exc
        data = response.json()
        return data.get("name") or data.get("filename") or image_path.name

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
            response = self.http.get(
                self._url("/view"),
                params={"filename": filename, "subfolder": subfolder, "type": type_},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise retryable_error(
                ErrorCode.COMFY_OUTPUT_MISSING,
                f"Could not download ComfyUI artifact: {filename}",
                str(exc),
                exc,
            ) from exc
        target_path.write_bytes(response.content)

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
