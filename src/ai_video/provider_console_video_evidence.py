"""Read-only recovery of exact video evidence from an invalid Runs workspace."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from ai_video.production.models import ProductionManifest
from ai_video.production.project import (
    load_production_project,
    load_production_project_candidate,
)
from ai_video.provider_console import (
    _invalid_production_detail,
    _legacy_detail,
    _production_detail,
    _runs_root,
    _selected_workspace,
)


_MAX_MANIFEST_BYTES = 16 * 1024 * 1024


def _read_manifest_for_evidence(root: Path) -> ProductionManifest:
    path = root / "state" / "manifest.json"
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("production manifest is unavailable") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or resolved != path
        or root not in resolved.parents
        or metadata.st_size > _MAX_MANIFEST_BYTES
    ):
        raise ValueError("production manifest is not one contained regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ValueError("production manifest is unavailable") from exc
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_size != metadata.st_size
        ):
            raise ValueError("production manifest changed before reading")
        chunks: list[bytes] = []
        size = 0
        while chunk := os.read(fd, min(1024 * 1024, _MAX_MANIFEST_BYTES + 1 - size)):
            chunks.append(chunk)
            size += len(chunk)
            if size > _MAX_MANIFEST_BYTES:
                raise ValueError("production manifest exceeds read limit")
        after = os.fstat(fd)
        if size != opened.st_size or (after.st_size, after.st_mtime_ns) != (
            opened.st_size,
            opened.st_mtime_ns,
        ):
            raise ValueError("production manifest changed while reading")
        return ProductionManifest.model_validate_json(b"".join(chunks))
    finally:
        os.close(fd)


def project_workspace_video_evidence(
    runs_root: str | Path, workspace: str
) -> dict[str, object]:
    """Recover request/output evidence without validating render activation.

    The normal detail reader remains fail-closed. This narrower reader may reopen
    the Manifest-selected project and Registry candidate after a full workspace
    audit fails, but it never calls the committer, mutates state, or calls a
    Provider.
    """

    root = _runs_root(runs_root)
    entry, kind = _selected_workspace(root, workspace)
    if kind != "production":
        return _legacy_detail(entry, workspace)
    try:
        loaded = load_production_project(entry)
        return _production_detail(root, entry, workspace, loaded=loaded)
    except Exception:
        pass
    try:
        manifest = _read_manifest_for_evidence(entry.parent)
        active_project = manifest.active_project
        active_registry = manifest.active_registry
        if active_project is None or active_registry is None:
            raise ValueError("active project evidence is unavailable")
        loaded = load_production_project_candidate(
            entry.parent,
            manifest,
            active_project.path,
            active_registry.path,
        )
        if Path(loaded.root) != entry.parent:
            raise ValueError("recovered project root does not match workspace")
    except Exception:
        return _invalid_production_detail(workspace)
    result = _production_detail(
        root,
        entry,
        workspace,
        loaded=loaded,
        status="recovered_video_evidence",
    )
    if result.get("status") != "invalid":
        result["workspace_strict_status"] = "invalid"
    return result
