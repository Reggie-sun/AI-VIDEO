"""Read-only Provider Console projection for exact continuity review."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Callable

from ai_video.production._video_project_reader import (
    load_local_video_fetch_receipt,
    load_video_fetch_receipt,
    load_video_request_receipt,
)
from ai_video.production.continuity_review_coordinator import HumanReviewRequestV1
from ai_video.production.models import StateCommitStatus, ToolIdentity, VideoAttemptPhase
from ai_video.production.project import load_production_project, load_qa_policy


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _shot_projection(shot: object) -> dict[str, object]:
    duration = getattr(shot, "duration_policy", None)
    duration_data = duration.model_dump(mode="json", exclude_none=True) if duration else None
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


def _continuity_media_token(workspace: str, attempt_id: str, sha256: str) -> str:
    identity = f"continuity-review\0{workspace}\0{attempt_id}\0{sha256}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:40]


def measure_contained_file(path: Path, *, root: Path) -> tuple[str, int]:
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("continuity review media is unavailable") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or resolved != path
        or root not in resolved.parents
    ):
        raise ValueError("continuity review media is not contained")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ValueError("continuity review media is unavailable") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError("continuity review media is not one regular file")
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(fd, 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        if size != opened.st_size:
            raise ValueError("continuity review media changed while reading")
        return digest.hexdigest(), size
    finally:
        os.close(fd)


def project_continuity_review(
    *,
    root: Path,
    entry: Path,
    workspace: str,
    attempt_id: str,
    automatic_evaluator: ToolIdentity,
    required_reviewer: ToolIdentity,
    project_loader: Callable[[Path], object] = load_production_project,
) -> dict[str, object]:
    """Project one exact VALIDATE attempt without creating Production state."""

    loaded = project_loader(entry)
    if root not in loaded.root.parents:
        raise ValueError("continuity review workspace escapes runs root")
    attempt = next(
        (
            item
            for item in loaded.manifest.attempts
            if item.attempt_id == attempt_id and item.operation == "video_generation"
        ),
        None,
    )
    state = getattr(attempt, "video_generation_state", None)
    if (
        attempt is None
        or attempt.status is not StateCommitStatus.RUNNING
        or state is None
        or state.phase is not VideoAttemptPhase.VALIDATE
        or state.continuity_evaluation is not None
    ):
        raise ValueError("continuity review requires an unevaluated VALIDATE attempt")
    request = load_video_request_receipt(loaded.root, state.request)
    binding = request.continuity_binding
    original = request.activation_scope.request if request.activation_scope else None
    if (
        binding is None
        or original is None
        or binding.target_shot_id != original.target_shot_id
        or binding.target_shot_content_hash != original.target_shot_content_hash
    ):
        raise ValueError("continuity review binding is unavailable")
    fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
    if fetch_pointer is None or (
        state.local_fetch_receipt is not None and state.fetch_receipt is not None
    ):
        raise ValueError("continuity review requires one fetched artifact")
    fetch_receipt = (
        load_local_video_fetch_receipt(loaded.root, fetch_pointer)
        if state.local_fetch_receipt is not None
        else load_video_fetch_receipt(loaded.root, fetch_pointer)
    )
    if (
        fetch_receipt.artifact_sha256 != fetch_pointer.artifact_sha256
        or fetch_receipt.size_bytes != fetch_pointer.artifact_size_bytes
    ):
        raise ValueError("continuity review fetch evidence is stale")
    expected_artifact_path = Path(
        "state/video-generation/fetch/files/"
        f"{fetch_pointer.artifact_sha256}.mp4"
    )
    if fetch_pointer.artifact_path != expected_artifact_path:
        raise ValueError("continuity review media path is not canonical")
    artifact_path = loaded.root / fetch_pointer.artifact_path
    artifact_sha256, artifact_size = measure_contained_file(
        artifact_path, root=loaded.root
    )
    if (
        artifact_sha256 != fetch_pointer.artifact_sha256
        or artifact_size != fetch_pointer.artifact_size_bytes
    ):
        raise ValueError("continuity review media bytes are stale")
    policy_pointer = loaded.manifest.active_qa_policy
    if policy_pointer is None:
        raise ValueError("continuity review requires an active QA policy")
    policy = load_qa_policy(loaded.root, policy_pointer)
    if (
        policy.policy_id != policy_pointer.policy_id
        or policy.policy_version != policy_pointer.policy_version
        or policy.content_hash != policy_pointer.content_hash
        or automatic_evaluator not in policy.semantic_authorities
        or required_reviewer not in policy.semantic_authorities
    ):
        raise ValueError("continuity review identities are not selected by policy")
    review_request = HumanReviewRequestV1.create(
        attempt_id=attempt_id,
        source_shot_id=binding.terminal_frame.source_shot_id,
        target_shot_id=original.target_shot_id,
        target_shot_content_hash=original.target_shot_content_hash,
        resolved_generation_hash=request.resolved_generation_hash,
        artifact_sha256=fetch_pointer.artifact_sha256,
        continuity_constraints_hash=binding.constraints.content_hash,
        qa_policy_content_hash=policy.content_hash,
        automatic_evaluator=automatic_evaluator,
        required_reviewer=required_reviewer,
        media_identity=f"sha256:{fetch_pointer.artifact_sha256}",
    )
    shots = {shot.shot_id: _shot_projection(shot) for shot in loaded.shots}
    media_token = _continuity_media_token(
        workspace, attempt_id, fetch_pointer.artifact_sha256
    )
    media = {
        "token": media_token,
        "mime_type": "video/mp4",
        "bytes": artifact_size,
        "sha256": artifact_sha256,
    }
    return {
        "boundary": {"read_only": True, "local_only": True, "network": False},
        "workspace": workspace,
        "attempt_id": attempt_id,
        "review_request": review_request.model_dump(mode="json"),
        "source_shot": shots.get(review_request.source_shot_id),
        "target_shot": shots.get(review_request.target_shot_id),
        "constraints": binding.constraints.model_dump(mode="json"),
        "media": media,
        "_media": {
            media_token: {
                "source_path": str(artifact_path),
                "mime_type": "video/mp4",
                "bytes": artifact_size,
                "sha256": artifact_sha256,
            }
        },
    }
