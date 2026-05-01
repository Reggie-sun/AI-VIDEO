from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from ai_video.config import sha256_file
from ai_video.errors import AiVideoError, ErrorCode


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AttemptRecord(BaseModel):
    attempt: int
    status: str = "pending"
    comfy_prompt_id: str | None = None
    error: dict | None = None


class ShotRecord(BaseModel):
    shot_id: str
    status: str = "pending"
    attempts: list[AttemptRecord] = Field(default_factory=list)
    active_attempt: int = 0
    seed: int | None = None
    rendered_workflow_path: str | None = None
    rendered_workflow_hash: str | None = None
    comfy_prompt_id: str | None = None
    clip_path: str | None = None
    clip_hash: str | None = None
    normalized_clip_path: str | None = None
    normalized_clip_hash: str | None = None
    last_frame_path: str | None = None
    last_frame_hash: str | None = None
    chain_input_hash: str | None = None
    character_ref_hashes: dict[str, str] = Field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    error: dict | None = None

    @classmethod
    def succeeded(
        cls,
        *,
        shot_id: str,
        seed: int,
        clip_path: Path,
        last_frame_path: Path,
        chain_input_hash: str | None,
        character_ref_hashes: dict[str, str],
    ) -> "ShotRecord":
        return cls(
            shot_id=shot_id,
            status="succeeded",
            seed=seed,
            clip_path=str(clip_path),
            clip_hash=sha256_file(clip_path),
            last_frame_path=str(last_frame_path),
            last_frame_hash=sha256_file(last_frame_path),
            chain_input_hash=chain_input_hash,
            character_ref_hashes=character_ref_hashes,
            completed_at=_now(),
        )


class RunManifest(BaseModel):
    run_id: str
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)
    project_config_path: str | None = None
    shot_list_path: str | None = None
    project_config_hash: str | None = None
    workflow_template_hash: str | None = None
    workflow_binding_hash: str | None = None
    status: str = "pending"
    shots: list[ShotRecord] = Field(default_factory=list)
    final_output: str | None = None


def atomic_write_manifest(path: str | Path, manifest: RunManifest) -> None:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.updated_at = _now()
    temp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temp_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    temp_path.replace(manifest_path)


def load_manifest(path: str | Path) -> RunManifest:
    manifest_path = Path(path)
    try:
        return RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AiVideoError(
            code=ErrorCode.MANIFEST_INVALID,
            user_message=f"Could not load manifest: {manifest_path}",
            technical_detail=str(exc),
            retryable=False,
        ) from exc


def _path_hash_matches(path_text: str | None, expected_hash: str | None) -> bool:
    if not path_text or not expected_hash:
        return False
    path = Path(path_text)
    if not path.exists():
        return False
    return sha256_file(path) == expected_hash


def successful_shot_is_valid(record: ShotRecord) -> bool:
    if record.status != "succeeded":
        return False
    return _path_hash_matches(record.clip_path, record.clip_hash) and _path_hash_matches(
        record.last_frame_path, record.last_frame_hash
    )


def mark_downstream_stale(manifest: RunManifest, starting_after_shot_id: str) -> RunManifest:
    found = False
    updated = []
    for shot in manifest.shots:
        if found and shot.status == "succeeded":
            shot = shot.model_copy(update={"status": "stale"})
        if shot.shot_id == starting_after_shot_id:
            found = True
        updated.append(shot)
    return manifest.model_copy(update={"shots": updated, "updated_at": _now()})
