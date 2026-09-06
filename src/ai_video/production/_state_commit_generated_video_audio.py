from __future__ import annotations

import hashlib
import subprocess
from contextlib import contextmanager
from typing import Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - platform-specific committer boundary
    fcntl = None  # type: ignore[assignment]

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import AudioProbeToolchain
from ai_video.production.generated_video_audio import (
    GeneratedVideoAudioRequest,
    register_generated_video_audio,
)

class _StateCommitGeneratedVideoAudioMixin:
    @contextmanager
    def _generated_video_audio_effect_lock(
        self, request: GeneratedVideoAudioRequest
    ) -> Iterator[None]:
        if fcntl is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_UNSUPPORTED,
                user_message="Generated video audio requires POSIX effect locking.",
                retryable=False,
            )
        key = hashlib.sha256(request.attempt_id.encode("utf-8")).hexdigest()
        lock_path = (
            self._state_directory()
            / "generated-video-audio"
            / "locks"
            / f"{key}.lock"
        )
        self._ensure_directory_chain(lock_path.parent)
        self._reject_symlink(lock_path)
        try:
            handle = lock_path.open("a+b")
        except OSError as exc:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_COMMIT_FAILED,
                user_message="Could not open generated video audio effect lock.",
                technical_detail=str(exc),
                retryable=False,
            ) from exc
        try:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except OSError as exc:
                raise AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_BUSY,
                    user_message="Generated video audio effect lock could not be acquired.",
                    technical_detail=str(exc),
                    retryable=False,
                ) from exc
            yield
        finally:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    def register_generated_video_audio(
        self,
        request: GeneratedVideoAudioRequest,
        *,
        toolchain: AudioProbeToolchain,
        runner=subprocess.run,
    ):
        with self._generated_video_audio_effect_lock(request):
            return register_generated_video_audio(
                self,
                request,
                toolchain=toolchain,
                runner=runner,
            )
