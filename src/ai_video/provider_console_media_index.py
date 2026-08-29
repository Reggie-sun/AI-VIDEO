"""Read-only exact media associations from canonical Provider Console Runs."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ai_video.provider_console import catalog_runs, project_workspace_detail


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _binding_for_output(
    *,
    workspace: str,
    attempt: Mapping[str, Any],
    sha256: str,
    size: int,
    media_roles: list[str],
) -> dict[str, object]:
    snapshot_status = attempt.get("shot_snapshot_status")
    snapshot = attempt.get("shot_snapshot")
    if snapshot_status != "verified" or not isinstance(snapshot, dict):
        snapshot = None
    return {
        "sha256": sha256,
        "bytes": size,
        "workspace": workspace,
        "attempt_id": attempt.get("attempt_id"),
        "target_shot_id": attempt.get("target_shot_id"),
        "target_shot_revision": attempt.get("target_shot_revision"),
        "target_shot_content_hash": attempt.get("target_shot_content_hash"),
        "generation_type": attempt.get("generation_type"),
        "prompt_text": attempt.get("prompt_text"),
        "shot_snapshot_status": snapshot_status or "unavailable",
        "shot_snapshot": snapshot,
        "media_roles": media_roles,
    }


def project_runs_media_index(
    runs_root: str | Path,
    *,
    catalog_loader: Callable[[str | Path], Mapping[str, Any]] = catalog_runs,
    detail_loader: Callable[[str | Path, str], Mapping[str, Any]] = project_workspace_detail,
) -> dict[str, object]:
    """Project exact output SHA/size to sanitized Runs request and Shot evidence."""

    catalog = catalog_loader(runs_root)
    workspaces = catalog.get("workspaces")
    workspace_items = workspaces if isinstance(workspaces, list) else []
    bindings: list[dict[str, object]] = []
    projected_workspaces = 0
    failed_workspaces = 0

    for item in workspace_items:
        workspace = item.get("workspace") if isinstance(item, dict) else None
        if not isinstance(workspace, str) or not workspace:
            continue
        try:
            detail = detail_loader(runs_root, workspace)
        except Exception:
            failed_workspaces += 1
            continue
        if detail.get("kind") == "production" and detail.get("status") == "invalid":
            failed_workspaces += 1
            continue
        projected_workspaces += 1
        attempts = detail.get("attempts")
        if not isinstance(attempts, list):
            continue
        for attempt in attempts:
            if not isinstance(attempt, dict):
                continue
            outputs: dict[tuple[str, int], list[str]] = {}
            for role in ("candidate_media", "fetched_media"):
                media = attempt.get(role)
                if not isinstance(media, dict):
                    continue
                sha256 = media.get("sha256")
                size = media.get("bytes")
                if not isinstance(sha256, str) or not _SHA256.fullmatch(sha256):
                    continue
                if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                    continue
                outputs.setdefault((sha256, size), []).append(role)
            for (sha256, size), media_roles in outputs.items():
                bindings.append(_binding_for_output(
                    workspace=workspace,
                    attempt=attempt,
                    sha256=sha256,
                    size=size,
                    media_roles=media_roles,
                ))

    bindings.sort(key=lambda item: (
        str(item["sha256"]),
        str(item["workspace"]),
        str(item.get("attempt_id") or ""),
    ))
    return {
        "boundary": {
            "read_only": True,
            "association": "exact_sha256_and_bytes",
            "lifecycle_projection": False,
            "complete": catalog.get("truncated") is not True and failed_workspaces == 0,
        },
        "bindings": bindings,
        "summary": {
            "workspace_count": len(workspace_items),
            "projected_workspace_count": projected_workspaces,
            "failed_workspace_count": failed_workspaces,
            "catalog_truncated": catalog.get("truncated") is True,
            "binding_count": len(bindings),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai_video.provider_console_media_index")
    parser.add_argument("--runs-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = project_runs_media_index(args.runs_root)
    except Exception:
        result = {"error": {"code": "RUNS_MEDIA_INDEX_UNAVAILABLE", "message": "Runs media evidence 当前不可用。"}}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 5
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
