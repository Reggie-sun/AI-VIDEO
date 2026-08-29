"""Read-only exact media associations from canonical Provider Console Runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from ai_video.provider_console import (
    catalog_runs,
    project_workspace_detail,
)
from ai_video.provider_console_video_evidence import project_workspace_video_evidence


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VIDEO_SUFFIXES = frozenset({".m4v", ".mov", ".mp4", ".webm"})
_MAX_UNRESOLVED_ENTRIES = 16_384
_MAX_UNRESOLVED_MEDIA = 512
_MAX_UNRESOLVED_DEPTH = 12


def _workspace_root(runs_root: str | Path, workspace: str) -> Path:
    supplied_root = Path(runs_root)
    root = supplied_root.resolve(strict=True)
    relative = PurePosixPath(workspace)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError("workspace key is invalid")
    entry = root.joinpath(*relative.parts)
    metadata = entry.lstat()
    resolved = entry.resolve(strict=True)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or resolved != entry
        or root not in entry.parents
        or entry.name not in {"project.yaml", "manifest.json"}
    ):
        raise ValueError("workspace entry is invalid")
    return entry.parent


def _measure_regular_video(path: Path, *, root: Path) -> tuple[str, int]:
    metadata = path.lstat()
    resolved = path.resolve(strict=True)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or resolved != path
        or root not in resolved.parents
    ):
        raise ValueError("workspace video is not contained")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError("workspace video is not one regular file")
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(fd, 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(fd)
        if size != opened.st_size or (after.st_size, after.st_mtime_ns) != (
            opened.st_size,
            opened.st_mtime_ns,
        ):
            raise ValueError("workspace video changed while reading")
        return digest.hexdigest(), size
    finally:
        os.close(fd)


def project_unresolved_workspace_media(
    runs_root: str | Path, workspace: str
) -> dict[str, object]:
    """Over-approximate media identities in a workspace that cannot be reopened."""

    try:
        root = _workspace_root(runs_root, workspace)
    except (OSError, RuntimeError, ValueError):
        return {"complete": False, "identities": []}
    pending: list[tuple[Path, int]] = [(root, 0)]
    entries_seen = 0
    identities: set[tuple[str, int]] = set()
    complete = True
    while pending:
        directory, depth = pending.pop()
        remaining = _MAX_UNRESOLVED_ENTRIES - entries_seen
        if remaining <= 0:
            complete = False
            break
        try:
            entries = []
            overflow = False
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if len(entries) >= remaining:
                        overflow = True
                        break
                    entries.append(entry)
        except OSError:
            complete = False
            continue
        if overflow:
            complete = False
            break
        entries.sort(key=lambda item: item.name, reverse=True)
        for entry in entries:
            entries_seen += 1
            try:
                if entry.is_symlink():
                    continue
                path = Path(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    if depth < _MAX_UNRESOLVED_DEPTH:
                        pending.append((path, depth + 1))
                    else:
                        complete = False
                    continue
                if (
                    entry.is_file(follow_symlinks=False)
                    and path.suffix.lower() in _VIDEO_SUFFIXES
                ):
                    identity = _measure_regular_video(path, root=root)
                    if identity not in identities and len(identities) >= _MAX_UNRESOLVED_MEDIA:
                        complete = False
                        pending.clear()
                        break
                    identities.add(identity)
            except (OSError, RuntimeError, ValueError):
                complete = False
    return {
        "complete": complete,
        "identities": [
            {"sha256": sha256, "bytes": size}
            for sha256, size in sorted(identities)
        ],
    }


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
    video_evidence_loader: Callable[[str | Path, str], Mapping[str, Any]] = project_workspace_video_evidence,
    unresolved_media_loader: Callable[[str | Path, str], Mapping[str, Any]] = project_unresolved_workspace_media,
) -> dict[str, object]:
    """Project exact output SHA/size to sanitized Runs request and Shot evidence."""

    catalog = catalog_loader(runs_root)
    workspaces = catalog.get("workspaces")
    workspace_items = workspaces if isinstance(workspaces, list) else []
    bindings: list[dict[str, object]] = []
    projected_workspaces = 0
    failed_workspaces = 0
    recovered_workspaces = 0
    identity_coverage_complete = catalog.get("truncated") is not True
    unresolved_media: set[tuple[str, int]] = set()

    for item in workspace_items:
        workspace = item.get("workspace") if isinstance(item, dict) else None
        if not isinstance(workspace, str) or not workspace:
            continue
        try:
            detail = detail_loader(runs_root, workspace)
        except Exception:
            detail = {"kind": item.get("kind"), "status": "invalid"}
        if detail.get("status") == "invalid":
            recovered = detail
            if detail.get("kind") == "production" or item.get("kind") == "production":
                try:
                    recovered = video_evidence_loader(runs_root, workspace)
                except Exception:
                    recovered = detail
            if recovered.get("status") == "recovered_video_evidence":
                detail = recovered
                recovered_workspaces += 1
            else:
                failed_workspaces += 1
                try:
                    unresolved = unresolved_media_loader(runs_root, workspace)
                except Exception:
                    unresolved = {"complete": False, "identities": []}
                if unresolved.get("complete") is not True:
                    identity_coverage_complete = False
                identities = unresolved.get("identities")
                if isinstance(identities, list):
                    for identity in identities:
                        if not isinstance(identity, dict):
                            identity_coverage_complete = False
                            continue
                        sha256 = identity.get("sha256")
                        size = identity.get("bytes")
                        if (
                            isinstance(sha256, str)
                            and _SHA256.fullmatch(sha256)
                            and isinstance(size, int)
                            and not isinstance(size, bool)
                            and size >= 0
                        ):
                            unresolved_media.add((sha256, size))
                        else:
                            identity_coverage_complete = False
                else:
                    identity_coverage_complete = False
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
            "complete": (
                catalog.get("truncated") is not True
                and failed_workspaces == 0
                and recovered_workspaces == 0
            ),
            "identity_coverage_complete": identity_coverage_complete,
        },
        "bindings": bindings,
        "unresolved_media": [
            {"sha256": sha256, "bytes": size}
            for sha256, size in sorted(unresolved_media)
        ],
        "summary": {
            "workspace_count": len(workspace_items),
            "projected_workspace_count": projected_workspaces,
            "failed_workspace_count": failed_workspaces,
            "recovered_workspace_count": recovered_workspaces,
            "catalog_truncated": catalog.get("truncated") is True,
            "binding_count": len(bindings),
            "unresolved_media_count": len(unresolved_media),
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
