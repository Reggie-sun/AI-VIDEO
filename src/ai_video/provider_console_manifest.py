"""Bounded, read-only Production Manifest hints for Provider Console catalogs."""

from __future__ import annotations

import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from ai_video.production.models import ProductionManifest


_MAX_MANIFEST_BYTES = 16 * 1024 * 1024


def read_production_manifest_nofollow(root: Path) -> ProductionManifest:
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


def latest_video_attempt_at(manifest: ProductionManifest) -> str | None:
    latest: tuple[datetime, str] | None = None
    for attempt in manifest.attempts:
        if attempt.operation != "video_generation" or attempt.video_generation_state is None:
            continue
        value = attempt.started_at
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if parsed.tzinfo is None:
            continue
        normalized = parsed.astimezone(timezone.utc)
        if latest is None or normalized > latest[0]:
            latest = (normalized, value)
    return latest[1] if latest is not None else None
