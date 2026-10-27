"""Read-only filesystem observations, never Production Shot or lifecycle truth."""

from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


_IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
_MAX_IMAGE_BYTES = 16 * 1024 * 1024
_MAX_TOTAL_BYTES = 64 * 1024 * 1024
_MAX_GROUPS = 6
_MAX_IMAGES = 16


def preparation_directory(path: Path, root: Path) -> Path | None:
    """Only observe explicit references directories; do not infer Shot bindings."""
    if path.suffix.lower() not in _IMAGE_TYPES or path.parent.name != "references":
        return None
    if len(path.relative_to(root).parts) < 4:
        return None
    return path.parent.parent


def _read_image(path: Path, root: Path, budget: list[int]) -> tuple[str, int, float]:
    if path.resolve(strict=True) != path or root not in path.parents:
        raise ValueError("reference is not contained")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        limit = min(budget[0], _MAX_IMAGE_BYTES)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= limit:
            raise ValueError("reference is not a bounded regular file")
        digest = hashlib.sha256()
        size = 0
        while size < before.st_size:
            chunk = os.read(fd, min(1024 * 1024, before.st_size - size))
            if not chunk:
                raise ValueError("reference changed")
            size += len(chunk)
            budget[0] -= len(chunk)
            digest.update(chunk)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("reference changed")
        return digest.hexdigest(), size, before.st_mtime
    finally:
        os.close(fd)


def project_preparations(paths: list[Path], root: Path) -> dict[str, object]:
    groups: dict[Path, list[tuple[float, Path]]] = {}
    for path in paths:
        directory = preparation_directory(path, root)
        if directory is None:
            continue
        try:
            metadata = path.lstat()
            if stat.S_ISREG(metadata.st_mode):
                groups.setdefault(directory, []).append((metadata.st_mtime, path))
        except OSError:
            continue
    ordered = sorted(groups.items(), key=lambda item: (-max(row[0] for row in item[1]), str(item[0])))
    preparations, media_map = [], {}
    budget = [_MAX_TOTAL_BYTES]
    truncated = len(ordered) > _MAX_GROUPS
    for directory, files in ordered[:_MAX_GROUPS]:
        relative = directory.relative_to(root).as_posix()
        references = []
        modified = []
        omitted = len(files) > _MAX_IMAGES
        for _, path in sorted(files, key=lambda item: (-item[0], str(item[1])))[:_MAX_IMAGES]:
            try:
                sha256, size, mtime = _read_image(path, root, budget)
            except (OSError, ValueError, RuntimeError):
                omitted = True
                continue
            file_relative = path.relative_to(root).as_posix()
            token = hashlib.sha256(f"preparation\0{file_relative}\0{sha256}".encode()).hexdigest()[:40]
            media = {"token": token, "mime_type": _IMAGE_TYPES[path.suffix.lower()], "bytes": size, "sha256": sha256}
            media_map[token] = {"source_path": str(path), **{key: value for key, value in media.items() if key != "token"}}
            references.append({"file_name": path.name, "relative_path": file_relative, "media": media})
            modified.append(mtime)
        truncated |= omitted
        if references:
            preparations.append({
                "id": relative, "kind": "local_preparation", "directory_name": directory.name,
                "source_directory": relative, "run_id": relative.split("/")[0],
                "updated_at": datetime.fromtimestamp(max(modified), timezone.utc).isoformat(),
                "references": references, "references_truncated": omitted,
                "binding_status": "unbound_local_files",
            })
    return {"preparations": preparations, "preparations_truncated": truncated, "_media": media_map}


def catalog_reference_library(root: Path, *, query: str = "", offset: int = 0) -> dict[str, object]:
    """Browse the configured local image archive, with bounded scans and page reads."""
    if len(query) > 256 or offset < 0 or offset > 100_000:
        raise ValueError("reference library query is invalid")
    result = {"source": "referces", "status": "available", "items": [], "total": 0,
              "offset": 0, "page_size": 12, "truncated": False, "_media": {}}
    try:
        if root.is_symlink() or not root.is_dir() or root.resolve(strict=True) != root:
            raise ValueError("reference root unavailable")
    except (OSError, ValueError, RuntimeError):
        return {**result, "status": "unavailable"}
    pending, files, scanned = [(root, 0)], [], 0
    while pending and scanned < 4096:
        directory, depth = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if scanned >= 4096:
                        result["truncated"] = True
                        break
                    scanned += 1
                    if entry.name.startswith(".") or entry.is_symlink():
                        continue
                    path = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        if depth < 12:
                            pending.append((path, depth + 1))
                        else:
                            result["truncated"] = True
                    elif entry.is_file(follow_symlinks=False) and path.suffix.lower() in _IMAGE_TYPES:
                        relative = path.relative_to(root).as_posix()
                        if query.casefold() in relative.casefold():
                            files.append((entry.stat(follow_symlinks=False).st_mtime, relative, path))
        except OSError:
            result["truncated"] = True
    result["truncated"] |= bool(pending)
    files.sort(key=lambda row: (-row[0], row[1]))
    result["total"] = len(files)
    offset = min(offset, max(0, (len(files) - 1) // 12 * 12))
    result["offset"] = offset
    budget = [_MAX_TOTAL_BYTES]
    for _, relative, path in files[offset:offset + 12]:
        item = {"file_name": path.name, "relative_path": relative, "media": None}
        try:
            sha256, size, mtime = _read_image(path, root, budget)
            token = hashlib.sha256(f"reference-library\0{relative}\0{sha256}".encode()).hexdigest()[:40]
            media = {"token": token, "mime_type": _IMAGE_TYPES[path.suffix.lower()], "bytes": size, "sha256": sha256}
            result["_media"][token] = {"source_path": str(path), **{key: value for key, value in media.items() if key != "token"}}
            item.update(media=media, updated_at=datetime.fromtimestamp(mtime, timezone.utc).isoformat())
        except (OSError, ValueError, RuntimeError):
            item["availability"] = "unavailable"
        result["items"].append(item)
    return result
