"""Read-only filesystem observations, never Production Shot or lifecycle truth."""

from __future__ import annotations

import hashlib
import json
import os
import re
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


def _reference_groups(root: Path) -> tuple[list[dict], bool]:
    """Only the dedicated browsing configuration can supply character labels."""
    path = root.parent / "provider-console/src/reference-library-groups.json"
    if not path.exists():
        return [], True
    try:
        if path.resolve(strict=True) != path:
            raise ValueError("linked configuration")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 65536:
                raise ValueError("unbounded configuration")
            value = json.loads(os.read(fd, 65537))
        finally:
            os.close(fd)
        if value.get("schema") != "reference-library-groups/1" or not isinstance(value.get("projects"), list):
            raise ValueError("invalid configuration")
        projects = value["projects"]
        if len(projects) > 64:
            raise ValueError("too many projects")
        seen = set()
        for project in projects:
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", project["id"]) or project["id"] in seen:
                raise ValueError("invalid project")
            seen.add(project["id"])
            if not isinstance(project["name"], str) or not 0 < len(project["name"]) <= 80:
                raise ValueError("invalid project label")
            prefixes = project["path_prefixes"]
            if not isinstance(prefixes, list) or not 0 < len(prefixes) <= 32 or any(not isinstance(p, str) or not p or len(p) > 256 or p.startswith("/") or ".." in p.split("/") for p in prefixes):
                raise ValueError("invalid prefixes")
            if not isinstance(project["characters"], list) or len(project["characters"]) > 128:
                raise ValueError("invalid characters")
            character_ids = set()
            for character in project["characters"]:
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", character["id"]) or character["id"] in character_ids:
                    raise ValueError("invalid character")
                character_ids.add(character["id"])
                if not isinstance(character["name"], str) or not 0 < len(character["name"]) <= 80:
                    raise ValueError("invalid character label")
                names = character["directory_names"]
                if not isinstance(names, list) or not 0 < len(names) <= 16 or any(not isinstance(n, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", n) for n in names):
                    raise ValueError("invalid character directories")
        return projects, False
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return [], True


def _reference_group(relative: str, projects: list[dict]) -> dict[str, str]:
    parts = Path(relative).parts
    matches = [p for p in projects if any(relative.startswith(prefix) for prefix in p["path_prefixes"])]
    project = matches[0] if len(matches) == 1 else None
    scope = project["id"] if project else "/".join(parts[:2] if parts[0] in {"runs", "outputs"} else parts[:1])
    project_name = project["name"] if project else scope
    characters = [c for c in (project["characters"] if project else []) if any(name in parts[:-1] for name in c["directory_names"])]
    if len(characters) == 1:
        character = characters[0]
        usage = "身份底图" if any(part == "identity" or part.startswith("identity-") for part in parts) else "身份合板" if "boards" in parts else "场次参考" if "scene" in parts else "来源画面" if "source-frames" in parts else "人物单图"
        return {"category": "character", "group_id": f"character:{scope}:{character['id']}", "group_label": character["name"], "project_label": project_name, "usage": usage}
    # The containing Shot directory takes precedence over a predecessor named in the filename.
    pattern = r"(?:^|[-_])(CO-[A-Z0-9]+|[A-Z]{1,3}\d{1,3})(?=$|[-_.])"
    shot = next((match.group(1) for part in reversed(parts[:-1]) if (match := re.search(pattern, part))), None)
    if not shot and not characters:
        match = re.match(r"^(CO-[A-Z0-9]+|[A-Z]{1,3}\d{1,3})(?=$|[-_.])", Path(relative).stem)
        shot = match.group(1) if match else None
    if shot and len(matches) <= 1 and len(characters) <= 1:
        return {"category": "shot", "group_id": f"shot:{scope}:{shot}", "group_label": shot, "project_label": project_name, "usage": "镜头参考"}
    return {"category": "other", "group_id": f"other:{scope}", "group_label": "其他素材", "project_label": project_name, "usage": "未明确归属"}


def catalog_reference_library(root: Path, *, query: str = "", offset: int = 0, category: str = "all", group: str = "") -> dict[str, object]:
    """Browse the configured local image archive, with bounded scans and page reads."""
    if len(query) > 256 or offset < 0 or offset > 100_000 or category not in {"all", "character", "shot", "other"} or len(group) > 256:
        raise ValueError("reference library query is invalid")
    result = {"source": "referces", "status": "available", "items": [], "total": 0,
              "offset": 0, "page_size": 12, "truncated": False, "_media": {},
              "groups": [], "category_counts": {"character": 0, "shot": 0, "other": 0}, "selected_group": group}
    try:
        if root.is_symlink() or not root.is_dir() or root.resolve(strict=True) != root:
            raise ValueError("reference root unavailable")
    except (OSError, ValueError, RuntimeError):
        return {**result, "status": "unavailable"}
    projects, result["classification_unavailable"] = _reference_groups(root)
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
                        classification = _reference_group(relative, projects)
                        if query.casefold() in f"{relative} {classification['group_label']} {classification['project_label']}".casefold():
                            files.append((entry.stat(follow_symlinks=False).st_mtime, relative, path, classification))
        except OSError:
            result["truncated"] = True
    result["truncated"] |= bool(pending)
    files.sort(key=lambda row: (-row[0], row[1]))
    groups = {}
    for _, _, _, classification in files:
        key = classification["group_id"]
        groups.setdefault(key, {k: v for k, v in classification.items() if k != "usage"} | {"count": 0})
        groups[key]["count"] += 1
        result["category_counts"][classification["category"]] += 1
    result["groups"] = sorted(groups.values(), key=lambda row: (row["project_label"], row["group_label"]))
    if category != "all":
        available_groups = [row for row in result["groups"] if row["category"] == category]
        group = group or (available_groups[0]["group_id"] if available_groups else "")
        files = [row for row in files if row[3]["category"] == category and row[3]["group_id"] == group]
    elif group:
        files = [row for row in files if row[3]["group_id"] == group]
    result["selected_group"] = group
    result["total"] = len(files)
    offset = min(offset, max(0, (len(files) - 1) // 12 * 12))
    result["offset"] = offset
    budget = [_MAX_TOTAL_BYTES]
    for _, relative, path, classification in files[offset:offset + 12]:
        item = {"file_name": path.name, "relative_path": relative, "media": None, **classification}
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
