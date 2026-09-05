"""Project only the active render already verified by the strict Project reader."""

from __future__ import annotations

import hashlib

from ai_video.production.models import LoadedProductionProject
from ai_video.provider_console_continuity import measure_contained_file


def active_render_media(
    loaded: LoadedProductionProject,
    workspace: str,
    media_map: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    state = getattr(loaded, "render_state", None)
    if state is None:
        return None
    output = state.output
    identity = f"active-render\0{workspace}\0{state.content_hash}\0{output.file_sha256}"
    token = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:40]
    attempt = next((a for a in loaded.manifest.attempts if a.attempt_id == state.attempt_id), None)
    descriptor = {
        "sha256": output.file_sha256,
        "bytes": output.size_bytes,
        "mime_type": "video/mp4",
        "relative_path": output.path.as_posix(),
        "source_kind": "active_render",
        "started_at": attempt.started_at if attempt is not None else None,
    }
    source = loaded.root / output.path
    try:
        if measure_contained_file(source, root=loaded.root) != (output.file_sha256, output.size_bytes):
            raise ValueError("render output changed after strict reopen")
    except (OSError, ValueError):
        return {**descriptor, "available": False}
    media_map[token] = {**descriptor, "source_path": str(source)}
    return {**descriptor, "token": token}
