"""Fail-closed local runtime closure for an M0 qualification submit."""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paths import _open_regular_file_nofollow


_COMPONENT_DIRS = {
    "stock-ref2va": Path("models/diffusion_models"),
    "qwen-clip": Path("models/text_encoders"),
    "video-vae": Path("models/vae"),
    "audio-vae": Path("models/vae"),
    "turbo-lora": Path("models/loras"),
}
_RUNTIME_DIRS = {
    "comfyui": Path("."),
    "minimax-h3-audio-t8": Path("custom_nodes/minimax-h3-audio-T8"),
    "videohelpersuite": Path("custom_nodes/ComfyUI-VideoHelperSuite"),
}


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class M0RuntimeClosureValidator:
    """Reopen exact local checkouts and model bytes immediately pre-effect."""

    def __init__(
        self,
        *,
        comfy_root: str | Path,
        runtime_revisions: tuple[tuple[str, str], ...],
    ) -> None:
        self._comfy_root = Path(comfy_root).resolve(strict=True)
        self._runtime_revisions = dict(runtime_revisions)
        if set(self._runtime_revisions) != set(_RUNTIME_DIRS):
            raise _invalid("M0 runtime revision inventory is incomplete.")

    @staticmethod
    def _git_head(path: Path) -> str:
        try:
            result = subprocess.run(
                ("git", "-C", str(path), "rev-parse", "HEAD"),
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            status = subprocess.run(
                (
                    "git",
                    "-C",
                    str(path),
                    "status",
                    "--porcelain=v1",
                    "--untracked-files=normal",
                ),
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise _invalid("M0 runtime checkout could not be reopened.", str(exc)) from exc
        if status.stdout:
            raise _invalid("M0 runtime checkout has dirty or untracked files.")
        return result.stdout.strip()

    @staticmethod
    def _component_identity(path: Path, root: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        try:
            with _open_regular_file_nofollow(path, contained_by=root) as (
                descriptor,
                opened,
            ):
                while chunk := os.read(descriptor, 8 * 1024 * 1024):
                    digest.update(chunk)
                final = os.fstat(descriptor)
        except (OSError, ValueError) as exc:
            raise _invalid("M0 runtime component could not be reopened.", str(exc)) from exc
        if final.st_size != opened.st_size:
            raise _invalid("M0 runtime component changed while it was hashed.")
        return digest.hexdigest(), final.st_size

    def __call__(self, sources: Any) -> None:
        seals = {item.name: item for item in sources.profile.runtime_seals}
        for name, relative in _RUNTIME_DIRS.items():
            seal = seals.get(name)
            suffix = "" if seal is None else seal.version.rsplit("+", 1)[-1]
            if not suffix or not self._runtime_revisions[name].startswith(suffix):
                raise _invalid(f"M0 runtime seal {name} is not inventory-bound.")
            if self._git_head(self._comfy_root / relative) != self._runtime_revisions[name]:
                raise _invalid(f"M0 runtime checkout {name} changed.")
        for component in sources.profile.components:
            directory = _COMPONENT_DIRS.get(component.component_id)
            if directory is None:
                raise _invalid("M0 runtime component mapping is unsupported.")
            digest, size = self._component_identity(
                self._comfy_root / directory / component.filename,
                self._comfy_root,
            )
            if digest != component.sha256 or size != component.size_bytes:
                raise _invalid(
                    f"M0 runtime component {component.component_id} bytes changed."
                )


__all__ = ["M0RuntimeClosureValidator"]
