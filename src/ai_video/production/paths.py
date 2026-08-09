from __future__ import annotations

from pathlib import Path


def resolve_contained_path(
    project_root: Path,
    stored: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    if stored.is_absolute() or ".." in stored.parts:
        raise ValueError(f"Path must be clean and project-relative: {stored}")
    try:
        root = project_root.resolve()
        boundary = (allowed_root or root).resolve()
        resolved = (root / stored).resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Path could not be resolved safely: {stored}") from exc
    try:
        boundary.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Allowed root escapes project root: {boundary}") from exc
    try:
        resolved.relative_to(boundary)
    except ValueError as exc:
        raise ValueError(f"Path escapes allowed root: {stored}") from exc
    return resolved
