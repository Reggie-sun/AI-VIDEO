"""Append-only revocation of an unused runtime authorization, owned by committer."""
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, StateCommitStatus, StrictModel


class RuntimeRepairRevocation(StrictModel):
    schema_version: Literal["runtime-repair-revocation/1"] = "runtime-repair-revocation/1"
    project_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    authorization_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    actor: ActorIdentity
    reason: str = Field(min_length=1)
    expected_manifest_revision: int = Field(strict=True, ge=0)
    recorded_at: datetime
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _sealed(self):
        if not self.reason.strip() or self.recorded_at.tzinfo is None:
            raise ValueError("Runtime repair revocation needs a reason and aware time")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("Runtime repair revocation content hash is invalid")
        return self

    @classmethod
    def create(cls, **values):
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls(**values, content_hash=canonical_sha256(provisional.model_dump(mode="json")))


def load_revocation(root, grant_pointer, *, project_id=None):
    """Read exact contained receipt bytes; no mutable state lives in the receipt."""
    from ai_video.production._generation_feedback_reader import _invalid, _root_and_path
    from ai_video.production.paths import _read_regular_file_nofollow

    pointer = grant_pointer.revocation
    if pointer is None:
        return None
    try:
        resolved_root, resolved = _root_and_path(root, pointer.path)
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        receipt = RuntimeRepairRevocation.model_validate_json(raw.data)
        if (raw.file_sha256 != pointer.file_sha256
                or receipt.content_hash != pointer.content_hash
                or receipt.authorization_hash != grant_pointer.content_hash
                or receipt.attempt_id != grant_pointer.attempt_id
                or receipt.evidence_hash != grant_pointer.evidence_hash
                or grant_pointer.consumed
                or project_id is not None and receipt.project_id != project_id):
            raise ValueError("revocation identity mismatch")
        return receipt
    except (OSError, ValueError) as exc:
        raise _invalid("Could not reopen runtime repair revocation.", str(exc)) from exc


def revoke_runtime_repair_authorization(committer, *, attempt_id, authorization_hash,
                                        expected_manifest_revision, actor, reason):
    """Revoke only an unused, unreserved grant; retain its receipt and all counts."""
    from ai_video.production._lifecycle_schema import RuntimeRepairRevocationPointer
    from ai_video.production._state_commit_common import (
        _canonical_json_bytes, _state_invalid, _validated_transition,
    )
    from ai_video.production._state_commit_contracts import PreparedArtifact
    import hashlib

    try:
        actor = ActorIdentity.model_validate(actor.model_dump(mode="python"))
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("missing reason")
    except (AttributeError, ValueError) as exc:
        raise _state_invalid("Runtime repair revocation input is invalid.") from exc
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        pointer = next((p for p in state.runtime_repairs
                        if p.content_hash == authorization_hash), None) if state else None
        if pointer is None:
            raise _state_invalid("Runtime repair revocation authorization is missing.")
        authorization = committer._reopen_runtime_repair_authorization(pointer)
        if authorization.actor != actor:
            raise _state_invalid("Runtime repair revocation requires the original authorization actor.")
        if pointer.revocation is not None:
            existing = load_revocation(committer.project_root, pointer, project_id=manifest.project_id)
            if (existing.actor != actor or existing.reason != reason
                    or existing.expected_manifest_revision != expected_manifest_revision):
                raise _state_invalid("Runtime repair revocation replay identity differs.")
            return pointer.revocation
        if (manifest.manifest_revision != expected_manifest_revision
                or attempt.status is not StateCommitStatus.FAILED or pointer.consumed):
            raise _state_invalid("Runtime repair revocation requires a current unused failed-attempt grant.")
        for item in manifest.attempts:
            other = item.video_generation_state
            if (item.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN,
                                StateCommitStatus.INTERRUPTED}
                    and other is not None and other.execution_binding is not None):
                binding = committer._reopen_generation_execution_binding(other.execution_binding)
                repair = binding.decision.runtime_repair
                if repair is not None and repair.content_hash == authorization_hash:
                    raise _state_invalid("Runtime repair revocation cannot cancel a pending successor.")
        receipt = RuntimeRepairRevocation.create(project_id=manifest.project_id,
            attempt_id=attempt_id, authorization_hash=authorization_hash,
            evidence_hash=pointer.evidence_hash, actor=actor, reason=reason,
            expected_manifest_revision=expected_manifest_revision,
            recorded_at=committer._paid_provider_clock())
        raw = _canonical_json_bytes(receipt)
        path = Path(f"state/video-generation/runtime-repair/revocations/{receipt.content_hash}.json")
        artifact = PreparedArtifact(path, raw, hashlib.sha256(raw).hexdigest())
        ref = RuntimeRepairRevocationPointer(path=path, content_hash=receipt.content_hash,
                                            file_sha256=artifact.file_sha256)
        replacement = pointer.model_copy(update={"revocation": ref})
        next_state = state.model_copy(update={"runtime_repairs": tuple(
            replacement if p.content_hash == authorization_hash else p for p in state.runtime_repairs)})
        next_attempt = _validated_transition(attempt, {"video_generation_state": next_state})
        next_manifest = _validated_transition(manifest, {
            "manifest_revision": manifest.manifest_revision + 1,
            "attempts": tuple(next_attempt if a.attempt_id == attempt_id else a for a in manifest.attempts)})
        committer._write_immutable_artifact(artifact, attempt_id=attempt_id)
        committer._write_manifest_atomic(next_manifest)
        load_revocation(committer.project_root, replacement, project_id=manifest.project_id)
        return ref
