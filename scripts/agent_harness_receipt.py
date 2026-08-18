"""Receipt and artifact persistence for the development Harness."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    from scripts.agent_harness_runtime import seal_receipt, sha256
except ModuleNotFoundError:  # Direct import from ``scripts/``.
    from agent_harness_runtime import seal_receipt, sha256


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    seal_receipt(receipt)
    atomic_write_json(path, receipt)


def record_workspace_cleanup(
    path: Path, *, status: str, error: str | None = None
) -> None:
    if status not in {"passed", "failed"}:
        raise ValueError(f"invalid workspace cleanup status: {status!r}")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["workspace_cleanup_status"] = status
    if status == "failed":
        receipt["status"] = "failed"
        receipt["failure_reason"] = error or "isolated workspace cleanup failed"
    write_receipt(path, receipt)


def write_artifact(run_dir: Path, path: Path, content: str | bytes) -> dict[str, Any]:
    data = content.encode("utf-8") if isinstance(content, str) else content
    path.write_bytes(data)
    return {
        "path": path.relative_to(run_dir).as_posix(),
        "sha256": sha256(data),
        "bytes": len(data),
    }


def _artifact_matches(run_dir: Path, descriptor: object) -> bool:
    if not isinstance(descriptor, dict):
        return False
    relative = descriptor.get("path")
    if not isinstance(relative, str):
        return False
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return False
    artifact_path = run_dir / relative_path
    try:
        resolved = artifact_path.resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    if artifact_path.is_symlink() or not resolved.is_relative_to(run_dir.resolve()):
        return False
    try:
        data = resolved.read_bytes()
    except OSError:
        return False
    return descriptor.get("bytes") == len(data) and descriptor.get("sha256") == sha256(data)


def verify_receipt_artifacts(receipt: Mapping[str, Any], run_dir: Path) -> bool:
    checks = receipt.get("checks")
    if checks is None:
        return True
    if not isinstance(checks, list):
        return False
    for check in checks:
        if not isinstance(check, dict):
            return False
        if check.get("status") == "skipped":
            continue
        if not _artifact_matches(run_dir, check.get("stdout")):
            return False
        if not _artifact_matches(run_dir, check.get("stderr")):
            return False
        if "junit" in check and not _artifact_matches(run_dir, check["junit"]):
            return False
    return True
