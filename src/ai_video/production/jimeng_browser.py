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
from ai_video.production.jimeng_contracts import (
    JimengMaterial, JimengProfile, JimengSubmitNotDispatched,
)


_WORKER = Path(__file__).with_name("jimeng_browser.cjs")
_DEFAULT_PLAYWRIGHT = "playwright"


def _failure(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


def _reap_worker(child) -> None:
    """Also run on cancellation; never leave an approved child detached."""

    if child is None:
        return
    if child.poll() is None:
        child.kill()
    child.wait()
    for stream in (child.stdin, child.stdout, child.stderr):
        if stream is not None:
            try:
                stream.close()
            except OSError:
                pass


class JimengBrowserTransport:
    """One operation per child. Browser credentials remain inside page context."""

    def __init__(self, *, profile_dir: Path,
                 playwright_module: Path | str = _DEFAULT_PLAYWRIGHT,
                 node_binary: str = "node", timeout_seconds: int = 300):
        self._profile_dir = Path(profile_dir)
        self._playwright_module = str(playwright_module)
        self._node_binary = node_binary
        self._timeout_seconds = timeout_seconds

    def _process(self):
        return subprocess.Popen(
            [self._node_binary, str(_WORKER)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            bufsize=1, close_fds=True,
        )

    def _base(self, profile: JimengProfile) -> dict[str, object]:
        return {"profile": {**profile.model_dump(mode="json"), "model_id": profile.model_id},
                "profile_dir": str(self._profile_dir),
                "playwright_module": str(self._playwright_module)}

    def _single(self, operation: str, profile: JimengProfile, extra: dict) -> dict:
        child = None
        try:
            child = self._process()
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
            raise _failure(ErrorCode.VIDEO_PROVIDER_FAILED,
                           "Jimeng browser operation failed; account state was not exported.") from None
        finally:
            _reap_worker(child)

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
        try:
            child = self._process()
        except OSError:
            raise JimengSubmitNotDispatched() from None
        selector = selectors.DefaultSelector()
        admitted = False
        try:
            assert child.stdin is not None and child.stdout is not None
            selector.register(child.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + self._timeout_seconds
            command = {"operation": "submit", **self._base(profile),
                "video_params": video_params,
                "materials": [x.model_dump(mode="json") for x in materials]}
            child.stdin.write(json.dumps(command, ensure_ascii=False) + "\n")
            child.stdin.flush()
            buffered = b""
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Jimeng browser submit timed out")
                if b"\n" not in buffered:
                    if not selector.select(remaining):
                        raise TimeoutError("Jimeng browser submit timed out")
                    chunk = os.read(child.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError("browser worker ended without result")
                    buffered += chunk
                    if len(buffered) > 65536:
                        raise ValueError("browser submit protocol frame is too large")
                    continue
                line, buffered = buffered.split(b"\n", 1)
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("browser protocol frame is invalid")
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
                    # The worker's readline interface stays alive until EOF.
                    child.stdin.close()
                    child.stdin = None
                    tail, _ = child.communicate(timeout=max(0, deadline - time.monotonic()))
                    if child.returncode != 0 or buffered.strip() or tail.strip():
                        raise ValueError("browser worker did not exit cleanly")
                    return message
                if message.get("ok") is False and message.get("no_effect") is True and not admitted:
                    child.stdin.close()
                    child.stdin = None
                    tail, _ = child.communicate(timeout=max(0, deadline - time.monotonic()))
                    if child.returncode == 1 and not buffered.strip() and not tail.strip():
                        raise JimengSubmitNotDispatched()
                raise ValueError("browser worker returned no accepted dispatch")
        except JimengSubmitNotDispatched:
            raise
        except Exception:
            raise _failure(ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                           "Jimeng native submit outcome is unknown; do not submit again.") from None
        finally:
            selector.close()
            _reap_worker(child)

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
