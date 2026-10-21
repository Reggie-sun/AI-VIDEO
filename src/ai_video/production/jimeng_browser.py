"""Browser-owned Jimeng I/O without exporting the logged-in account session."""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import tempfile
import time
from pathlib import Path
from typing import BinaryIO

import httpx

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.jimeng_contracts import JimengMaterial, JimengProfile


_WORKER = Path(__file__).with_name("jimeng_browser.cjs")
_DEFAULT_PLAYWRIGHT = Path(
    "/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright"
)


def _failure(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


class JimengBrowserTransport:
    """One operation per child. Browser credentials remain inside page context."""

    def __init__(self, *, profile_dir: Path,
                 playwright_module: Path = _DEFAULT_PLAYWRIGHT,
                 node_binary: str = "node", timeout_seconds: int = 300):
        self._profile_dir = Path(profile_dir)
        self._playwright_module = Path(playwright_module)
        self._node_binary = node_binary
        self._timeout_seconds = timeout_seconds

    def _process(self):
        return subprocess.Popen(
            [self._node_binary, str(_WORKER)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            bufsize=1, close_fds=True,
        )

    def _base(self, profile: JimengProfile) -> dict[str, object]:
        return {"profile": profile.model_dump(mode="json"),
                "profile_dir": str(self._profile_dir),
                "playwright_module": str(self._playwright_module)}

    def _single(self, operation: str, profile: JimengProfile, extra: dict) -> dict:
        child = self._process()
        try:
            payload = {"operation": operation, **self._base(profile), **extra}
            output, _ = child.communicate(json.dumps(payload, ensure_ascii=False) + "\n",
                                          timeout=self._timeout_seconds)
            lines = output.strip().splitlines()
            if child.returncode != 0 or len(lines) != 1:
                raise ValueError("browser worker did not return one result")
            result = json.loads(lines[0])
            if not isinstance(result, dict) or result.get("ok") is not True:
                raise ValueError("browser operation failed")
            return result
        except (OSError, ValueError, subprocess.TimeoutExpired):
            child.kill()
            child.communicate()
            raise _failure(ErrorCode.VIDEO_PROVIDER_FAILED,
                           "Jimeng browser operation failed; account state was not exported.") from None

    def upload(self, *, profile: JimengProfile, kind: str, payload: bytes,
               mime_type: str) -> str:
        if kind not in {"image", "audio", "video"}:
            raise _failure(ErrorCode.VIDEO_REQUEST_INVALID, "Jimeng upload kind is invalid.")
        descriptor, name = tempfile.mkstemp(prefix="ai-video-jimeng-ref-", suffix=".bin")
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            result = self._single("upload", profile, {"kind": kind,
                "file": name, "mime_type": mime_type,
                "sha256": hashlib.sha256(payload).hexdigest()})
            identity = result.get("storage_id")
            if not isinstance(identity, str) or not identity:
                raise _failure(ErrorCode.VIDEO_PROVIDER_FAILED,
                               "Jimeng upload has no committed storage identity.")
            return identity
        finally:
            Path(name).unlink(missing_ok=True)

    def submit_native(self, *, profile: JimengProfile, video_params: dict,
                      materials: tuple[JimengMaterial, ...], admit):
        child = self._process()
        selector = selectors.DefaultSelector()
        try:
            assert child.stdin is not None and child.stdout is not None
            selector.register(child.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + self._timeout_seconds
            command = {"operation": "submit", **self._base(profile),
                "video_params": video_params,
                "materials": [x.model_dump(mode="json") for x in materials]}
            child.stdin.write(json.dumps(command, ensure_ascii=False) + "\n")
            child.stdin.flush()
            admitted = False
            while True:
                if not selector.select(max(0, deadline - time.monotonic())):
                    raise TimeoutError("Jimeng browser submit timed out")
                line = child.stdout.readline()
                if not line:
                    raise ValueError("browser worker ended without result")
                message = json.loads(line)
                if message.get("event") == "dispatch":
                    if admitted:
                        raise ValueError("second dispatch")
                    admitted = True
                    try:
                        admit(message["submit_id"], message["resource_id"])
                    except Exception:
                        child.stdin.write('{"approved":false}\n')
                        child.stdin.flush()
                        raise
                    child.stdin.write('{"approved":true}\n')
                    child.stdin.flush()
                    continue
                if message.get("ok") is True and admitted:
                    child.wait(timeout=max(0, deadline - time.monotonic()))
                    if child.returncode != 0:
                        raise ValueError("browser worker did not exit cleanly")
                    return message
                raise ValueError("browser worker returned no accepted dispatch")
        except Exception:
            child.kill()
            child.communicate()
            raise _failure(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                           "Jimeng native submit outcome is unknown; do not submit again.") from None
        finally:
            selector.close()

    def read_resource(self, *, profile: JimengProfile, resource_id: str):
        result = self._single("read", profile, {"resource_id": resource_id})
        resource = result.get("resource")
        if not isinstance(resource, dict):
            raise _failure(ErrorCode.VIDEO_PROVIDER_FAILED,
                           "Jimeng resource read returned no resource.")
        return resource

    def read_saved_canvas(self, *, profile: JimengProfile, resource_id: str) -> dict:
        result = self._single("canvas", profile, {"resource_id": resource_id})
        canvas = result.get("canvas")
        if not isinstance(canvas, dict):
            raise _failure(ErrorCode.VIDEO_PROVIDER_FAILED,
                           "Jimeng server-saved canvas draft is unavailable.")
        return canvas

    def download(self, *, url: str, sink: BinaryIO) -> tuple[int, str]:
        """Use the fresh resource URL; follow ordinary redirects, verify bytes."""

        digest = hashlib.sha256()
        size = 0
        with httpx.Client(follow_redirects=True, timeout=120) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    sink.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        return size, digest.hexdigest()


__all__ = ["JimengBrowserTransport"]
