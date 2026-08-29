"""Read-only recovery of exact video evidence from an invalid Runs workspace."""

from __future__ import annotations

from pathlib import Path

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
from ai_video.provider_console_manifest import (
    read_production_manifest_nofollow as _read_manifest_for_evidence,
)

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
