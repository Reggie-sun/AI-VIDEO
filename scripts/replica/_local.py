"""Path resolution and local CLI I/O for the reference edit tools."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import NamedTemporaryFile

from ai_video.errors import AiVideoError, ErrorCode


def tool_path(name: str, explicit: str | Path | None = None) -> Path:
    found = shutil.which(name if explicit is None else os.fspath(explicit))
    if found is None:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, f"{name} executable is unavailable.")
    return Path(found).resolve(strict=True)


def _editor_directory(path: Path) -> Path:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_dir():
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "An existing Agentcut directory is required.")
    directory = candidate.resolve(strict=True)
    for ancestor in (directory, *directory.parents):
        if (ancestor / "project.yaml").exists() or (ancestor / "state/manifest.json").exists():
            raise AiVideoError(ErrorCode.CONFIG_INVALID, "Agentcut edits require a directory outside Production projects.")
    return directory


def project_root(explicit: str | Path | None = None) -> Path:
    if explicit is None:
        workspace = os.environ.get("AGENTCUT_WORKSPACE")
        if not workspace:
            raise AiVideoError(ErrorCode.CONFIG_INVALID, "Set --projects-root or AGENTCUT_WORKSPACE.")
        explicit = Path(workspace) / "projects"
    return _editor_directory(Path(explicit))


def agentcut_project(path: Path) -> Path:
    directory = _editor_directory(path)
    metadata = directory / "project.json"
    if metadata.is_symlink() or not metadata.is_file():
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Agentcut project.json is missing or is not a regular file.")
    return directory


def read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, f"Cannot read JSON from {Path(path).name}.") from exc


def write_bytes(path: Path, payload: bytes) -> None:
    path = Path(path)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Output must be a regular file.")
    temp_path = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as output:
            temp_path = Path(output.name)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def cli(main) -> None:
    try:
        result = main(sys.argv[1:])
    except AiVideoError as error:
        print(json.dumps({"code": error.code.value, "message": error.user_message,
                          "retryable": error.retryable}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from None
    except (KeyError, OSError, TypeError, ValueError, subprocess.SubprocessError):
        print(json.dumps({"code": ErrorCode.CONFIG_INVALID.value, "message": "Invalid input or local file operation.",
                          "retryable": False}), file=sys.stderr)
        raise SystemExit(1) from None
    if isinstance(result, int):
        raise SystemExit(result)
