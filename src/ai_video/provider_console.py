"""Sanitized, read-only projections of local ``runs/`` workspaces.

This module deliberately depends only on canonical readers.  It never imports a
state committer or Provider adapter and never writes to a workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from ai_video.manifest import load_manifest
from ai_video.production._video_project_reader import load_video_request_receipt
from ai_video.production.project import load_production_project


_BOUNDARY = {"read_only": True, "local_only": True, "network": False}
_MEDIA_MIME_PREFIXES = ("image/", "video/")


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat(follow_symlinks=False).st_mtime, timezone.utc).isoformat()


def _runs_root(path: str | Path) -> Path:
    supplied = Path(path)
    try:
        metadata = supplied.lstat()
        resolved = supplied.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("runs root is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("runs root must be a real directory")
    return resolved


def _is_regular_nofollow(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.stat(follow_symlinks=False).st_mode) and not path.is_symlink()
    except OSError:
        return False


def _walk_files(
    root: Path,
    *,
    max_depth: int,
    max_entries: int,
    scan: dict[str, int | bool],
):
    """Yield regular files without following symlinks, in deterministic order."""

    pending: list[tuple[Path, int]] = [(root, 0)]
    while pending:
        directory, depth = pending.pop()
        remaining = max_entries - int(scan["entries"])
        if remaining <= 0:
            scan["truncated"] = True
            return
        try:
            entries = []
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if len(entries) >= remaining:
                        scan["entries"] = int(scan["entries"]) + len(entries)
                        scan["truncated"] = True
                        return
                    entries.append(entry)
        except OSError:
            continue
        scan["entries"] = int(scan["entries"]) + len(entries)
        entries.sort(key=lambda item: item.name, reverse=True)
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                path = Path(entry.path)
                relative_depth = len(path.relative_to(root).parts)
                if entry.is_file(follow_symlinks=False):
                    if relative_depth <= max_depth:
                        yield path
                elif entry.is_dir(follow_symlinks=False) and depth + 1 < max_depth:
                    pending.append((path, depth + 1))
            except OSError:
                continue


def catalog_runs(
    runs_root: str | Path,
    *,
    max_workspaces: int = 256,
    max_depth: int = 6,
    max_scanned_workspaces: int = 256,
    max_entries: int = 16_384,
) -> dict[str, object]:
    """Return a bounded catalog without claiming strict workspace validity."""

    root = _runs_root(runs_root)
    if min(max_workspaces, max_scanned_workspaces, max_entries) < 1 or max_depth < 2:
        raise ValueError("catalog bounds must be positive")
    candidates: dict[str, dict[str, object]] = {}
    scan: dict[str, int | bool] = {"entries": 0, "workspaces": 0, "truncated": False}
    workspace_truncated = False
    for path in _walk_files(root, max_depth=max_depth, max_entries=max_entries, scan=scan):
        relative = path.relative_to(root)
        workspace = relative.as_posix()
        kind: str | None = None
        marker = path
        if path.name == "project.yaml" and _is_regular_nofollow(path.parent / "state" / "manifest.json"):
            kind = "production"
            manifest = path.parent / "state" / "manifest.json"
            marker = max((path, manifest), key=lambda item: item.stat(follow_symlinks=False).st_mtime_ns)
        elif path.name == "manifest.json" and len(relative.parts) == 2:
            kind = "legacy"
        if kind is None:
            continue
        if workspace not in candidates and len(candidates) >= max_scanned_workspaces:
            workspace_truncated = True
            break
        candidates[workspace] = {
            "workspace": workspace,
            "run_id": relative.parts[0],
            "kind": kind,
            "status": "catalogued",
            "updated_at": _iso_mtime(marker),
            "_mtime_ns": marker.stat(follow_symlinks=False).st_mtime_ns,
        }
        scan["workspaces"] = len(candidates)
    ordered = sorted(candidates.values(), key=lambda item: (-int(item["_mtime_ns"]), str(item["workspace"])))
    public = [{key: value for key, value in item.items() if key != "_mtime_ns"} for item in ordered[:max_workspaces]]
    return {
        "boundary": dict(_BOUNDARY),
        "workspaces": public,
        "truncated": bool(scan["truncated"]) or workspace_truncated or len(ordered) > max_workspaces,
        "scan": {
            "entries": int(scan["entries"]),
            "workspaces": int(scan["workspaces"]),
        },
    }


def _selected_workspace(root: Path, workspace: str) -> tuple[Path, str]:
    if not isinstance(workspace, str) or not workspace or "\\" in workspace or "\0" in workspace:
        raise ValueError("workspace key is invalid")
    relative = PurePosixPath(workspace)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("workspace key is invalid")
    if relative.name == "project.yaml":
        kind = "production"
    elif relative.name == "manifest.json" and len(relative.parts) == 2:
        kind = "legacy"
    else:
        raise ValueError("workspace key is not a supported workspace")
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise FileNotFoundError("workspace was not found") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("workspace symlinks are not allowed")
    if not stat.S_ISREG(current.lstat().st_mode):
        raise ValueError("workspace entry point must be a regular file")
    resolved = current.resolve(strict=True)
    if resolved != current or root not in resolved.parents:
        raise ValueError("workspace escapes runs root")
    if kind == "production" and not _is_regular_nofollow(current.parent / "state" / "manifest.json"):
        raise FileNotFoundError("Production workspace manifest was not found")
    return current, kind


def _pointer(pointer: object | None) -> dict[str, object] | None:
    if pointer is None:
        return None
    result: dict[str, object] = {}
    for key in (
        "path",
        "file_sha256",
        "content_hash",
        "request_receipt_fingerprint",
        "request_input_hash",
        "resolved_generation_hash",
        "output_asset_id",
    ):
        value = getattr(pointer, key, None)
        if value is not None:
            result[key] = value.as_posix() if isinstance(value, Path) else _enum_value(value)
    return result


def _media_token(workspace: str, asset: object) -> str:
    identity = f"{workspace}\0{getattr(asset, 'asset_id')}\0{getattr(asset, 'sha256')}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:40]


def _media_projection(
    *,
    workspace: str,
    asset: object | None,
    asset_paths: dict[str, Path],
    root: Path,
    media_map: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    if asset is None:
        return None
    mime_type = getattr(asset, "mime_type", "")
    asset_id = getattr(asset, "asset_id", "")
    if not isinstance(mime_type, str) or not mime_type.startswith(_MEDIA_MIME_PREFIXES):
        return None
    source = asset_paths.get(asset_id)
    if source is None:
        return None
    try:
        source = Path(source)
        metadata = source.lstat()
        resolved = source.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return None
    if resolved != source or root not in resolved.parents:
        return None
    size = int(getattr(asset, "size_bytes"))
    if metadata.st_size != size:
        return None
    token = _media_token(workspace, asset)
    video = getattr(asset, "video_metadata", None)
    fps = None
    if video is not None:
        numerator = getattr(video, "fps_numerator", None)
        denominator = getattr(video, "fps_denominator", None)
        if numerator and denominator:
            fps = numerator / denominator
    public = {
        "token": token,
        "asset_id": asset_id,
        "asset_type": _enum_value(getattr(asset, "asset_type", None)),
        "mime_type": mime_type,
        "bytes": size,
        "sha256": getattr(asset, "sha256", None),
        "width": getattr(asset, "width", None),
        "height": getattr(asset, "height", None),
        "duration_seconds": getattr(asset, "duration_seconds", None),
        "fps": fps,
        "frame_count": getattr(video, "frame_count", None),
        "remote_egress": bool(getattr(getattr(asset, "egress", None), "remote", False)),
    }
    media_map[token] = {"source_path": str(source), "mime_type": mime_type, "bytes": size}
    return {key: value for key, value in public.items() if value is not None}


def _shot_projection(shot: object) -> dict[str, object]:
    duration = getattr(shot, "duration_policy", None)
    duration_data = duration.model_dump(mode="json", exclude_none=True) if duration is not None else None
    return {
        key: value
        for key, value in {
            "shot_id": getattr(shot, "shot_id", None),
            "scene_id": getattr(shot, "scene_id", None),
            "intent": getattr(shot, "intent", None),
            "visual_strategy": _enum_value(getattr(shot, "visual_strategy", None)),
            "duration_policy": duration_data,
            "revision": getattr(shot, "revision", None),
            "content_hash": getattr(shot, "content_hash", None),
        }.items()
        if value is not None
    }


def _asset_by_id(assets: dict[str, object], asset_id: str | None) -> object | None:
    return assets.get(asset_id) if asset_id else None


def _production_detail(root: Path, entry: Path, workspace: str) -> dict[str, object]:
    try:
        loaded = load_production_project(entry)
    except Exception:
        return {
            "boundary": dict(_BOUNDARY),
            "workspace": workspace,
            "run_id": PurePosixPath(workspace).parts[0],
            "kind": "production",
            "status": "invalid",
            "error": {
                "code": "PRODUCTION_PROJECT_INVALID",
                "message": "该 Production workspace 无法通过严格校验。",
            },
            "attempts": [],
            "_media": {},
        }
    assets = {asset.asset_id: asset for asset in loaded.registry.assets}
    media_map: dict[str, dict[str, object]] = {}
    attempts: list[dict[str, object]] = []
    for attempt in loaded.manifest.attempts:
        if getattr(attempt, "operation", None) != "video_generation":
            continue
        state = getattr(attempt, "video_generation_state", None)
        if state is None:
            continue
        try:
            request = load_video_request_receipt(loaded.root, state.request)
        except Exception:
            return {
                "boundary": dict(_BOUNDARY),
                "workspace": workspace,
                "run_id": PurePosixPath(workspace).parts[0],
                "kind": "production",
                "status": "invalid",
                "error": {
                    "code": "VIDEO_REQUEST_INVALID",
                    "message": "该 workspace 的 video request evidence 无法通过严格校验。",
                },
                "attempts": [],
                "_media": {},
            }
        scope = getattr(request, "activation_scope", None)
        original = getattr(scope, "request", None)
        target_shot_id = getattr(original, "target_shot_id", None)
        target_asset_role = getattr(original, "target_asset_role", None)
        bindings = tuple(getattr(request, "image_bindings", ()))
        first_binding = next((item for item in bindings if _enum_value(getattr(item, "role", None)) == "first_frame"), None)
        first_asset = _asset_by_id(assets, getattr(first_binding, "asset_id", None))
        candidate_ids = tuple(getattr(state, "candidate_video_asset_ids", ()))
        candidate_asset = _asset_by_id(assets, candidate_ids[-1] if candidate_ids else getattr(request, "output_asset_id", None))
        output = request.effective_output.model_dump(mode="json", exclude_none=True)
        video_metadata = getattr(candidate_asset, "video_metadata", None)
        if video_metadata is not None:
            output = {
                **output,
                "frame_count": video_metadata.frame_count,
                "fps": video_metadata.fps_numerator / video_metadata.fps_denominator,
            }
        profile = request.provider_profile
        attempts.append(
            {
                "attempt_id": attempt.attempt_id,
                "status": _enum_value(attempt.status),
                "phase": _enum_value(state.phase),
                "started_at": attempt.started_at,
                "finished_at": attempt.finished_at,
                "target_shot_id": target_shot_id,
                "target_asset_role": target_asset_role,
                "generation_id": state.generation_id,
                "provider": {
                    "name": request.provider_name,
                    "kind": request.provider_kind,
                    "model": request.model_id,
                    "profile": profile.profile_id,
                    "profile_version": profile.profile_version,
                    "profile_sha256": profile.profile_sha256,
                    "capability": request.capability_id,
                    "execution_kind": _enum_value(request.execution_kind),
                    "billing_kind": _enum_value(request.billing_kind),
                    "mode": _enum_value(request.mode),
                },
                "effective_output": output,
                "request_evidence": _pointer(state.request),
                "first_frame_media": _media_projection(
                    workspace=workspace, asset=first_asset, asset_paths=loaded.asset_paths,
                    root=loaded.root, media_map=media_map,
                ),
                "candidate_media": _media_projection(
                    workspace=workspace, asset=candidate_asset, asset_paths=loaded.asset_paths,
                    root=loaded.root, media_map=media_map,
                ),
                "continuity_role": (
                    type(request.continuity_binding).__name__
                    if getattr(request, "continuity_binding", None) is not None
                    else None
                ),
            }
        )
    project = loaded.project
    return {
        "boundary": dict(_BOUNDARY),
        "workspace": workspace,
        "run_id": PurePosixPath(workspace).parts[0],
        "kind": "production",
        "status": "valid",
        "updated_at": _iso_mtime(entry.parent / "state" / "manifest.json"),
        "project": {
            "project_id": project.project_id,
            "title": project.title,
            "revision": project.revision,
            "content_hash": project.content_hash,
        },
        "manifest": {
            "schema_version": loaded.manifest.schema_version,
            "revision": loaded.manifest.manifest_revision,
        },
        "shots": [_shot_projection(shot) for shot in loaded.shots],
        "attempts": attempts,
        "_media": media_map,
    }


def _legacy_detail(entry: Path, workspace: str) -> dict[str, object]:
    manifest = load_manifest(entry)
    return {
        "boundary": dict(_BOUNDARY),
        "workspace": workspace,
        "run_id": manifest.run_id,
        "kind": "legacy",
        "status": manifest.status,
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
        "shots": [
            {"shot_id": shot.shot_id, "status": shot.status, "active_attempt": shot.active_attempt}
            for shot in manifest.shots
        ],
        "attempts": [],
        "_media": {},
    }


def project_workspace_detail(runs_root: str | Path, workspace: str) -> dict[str, object]:
    """Strictly reopen one selected workspace and return its safe projection."""

    root = _runs_root(runs_root)
    entry, kind = _selected_workspace(root, workspace)
    if kind == "production":
        return _production_detail(root, entry, workspace)
    return _legacy_detail(entry, workspace)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ai_video.provider_console")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("catalog", "detail"):
        child = subparsers.add_parser(command)
        child.add_argument("--runs-root", required=True, type=Path)
        if command == "detail":
            child.add_argument("--workspace", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "catalog":
            result = catalog_runs(args.runs_root)
        else:
            result = project_workspace_detail(args.runs_root, args.workspace)
    except FileNotFoundError:
        result = {"error": {"code": "WORKSPACE_NOT_FOUND", "message": "workspace 不存在。"}}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 4
    except ValueError:
        if args.command == "detail":
            result = {"error": {"code": "INVALID_WORKSPACE", "message": "workspace 参数无效。"}}
            status = 3
        else:
            result = {"error": {"code": "RUNS_SOURCE_UNAVAILABLE", "message": "本地 runs 数据源不可用。"}}
            status = 5
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return status
    except Exception:
        result = {"error": {"code": "RUNS_SOURCE_UNAVAILABLE", "message": "本地 runs 数据源不可用。"}}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 5
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
