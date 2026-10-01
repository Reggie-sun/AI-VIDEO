"""Canonical closure of a production REQUEST with no external-effect intent."""

from __future__ import annotations

import json
from typing import Literal

from ai_video.errors import ErrorCode
from ai_video.production._state_commit_common import (
    _state_invalid, _timestamp, _validated_transition,
)
from ai_video.production.models import ActorIdentity, StateCommitStatus, VideoAttemptPhase


CloseReason = Literal["expired_execution_window", "superseded_before_submit"]
_REASONS = {"expired_execution_window", "superseded_before_submit"}


def _closure_metadata(actor, reason):
    if not isinstance(actor, ActorIdentity) or type(reason) is not str or reason not in _REASONS:
        raise _state_invalid("Unsubmitted closure requires a typed actor and reason.")
    try:
        actor = ActorIdentity.model_validate(actor.model_dump())
    except ValueError as exc:
        raise _state_invalid("Unsubmitted closure actor is invalid.") from exc
    return json.dumps({"actor": actor.model_dump(mode="json"), "reason": reason},
                      sort_keys=True, separators=(",", ":"))


def _require_unsubmitted(committer, manifest, attempt):
    state = attempt.video_generation_state
    if (attempt.operation != "video_generation" or state is None
            or state.phase is not VideoAttemptPhase.REQUEST
            or state.execution_binding is None
            or attempt.paid_provider_state is not None
            or attempt.provider_request_id is not None
            or any(getattr(state, name) is not None for name in (
                "paid_submit_receipt", "latest_observation", "fetch_receipt",
                "local_submit_intent", "local_submit_receipt", "local_latest_observation",
                "local_fetch_receipt", "provider_file_id", "quality_rejection",
                "terminal_frame_evidence", "terminal_frame_extraction",
                "continuity_evaluation", "commercial_evaluation", "source_boundary_evaluation"))
            or state.candidate_video_asset_ids or state.candidate_continuity_asset_ids
            or not state.generation_experiences):
        raise _state_invalid("Closure requires an evaluated request without submit evidence.")
    if manifest.active_paid_provider_budget is not None:
        budget = committer._reopen_paid_budget(manifest.active_paid_provider_budget)
        if any(item.attempt_id == attempt.attempt_id for item in budget.reservations):
            raise _state_invalid("Unsubmitted closure cannot release a paid reservation.")
    request = committer._reopen_video_request(state.request)
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    binding.validate_request(request)
    candidate = next(c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id)
    for pointer in state.generation_experiences:
        experience = committer._reopen_generation_experience(pointer)
        if (experience.projection != binding.projection or experience.candidate != candidate
                or experience.evaluation_sources or not experience.evidence):
            raise _state_invalid("Unsubmitted closure evidence differs from the exact decision.")
        for evidence in experience.evidence:
            if (evidence.outcome != "not_submitted" or evidence.artifact_sha256 is not None
                    or evidence.findings or evidence.unresolved_quality_refs):
                raise _state_invalid("Unsubmitted closure requires exact not-submitted evidence.")
            committer._validate_generation_evidence(
                attempt=attempt, state=state, request=request, binding=binding, evidence=evidence)


def is_verified_closed_unsubmitted_video_attempt(committer, *, manifest, attempt):
    """Verify terminal metadata AND immutable history before inheriting a task cap."""
    if (attempt.status is not StateCommitStatus.FAILED
            or attempt.error_code != ErrorCode.VIDEO_GENERATION_NOT_SUBMITTED.value
            or attempt.finished_at is None):
        return False
    try:
        metadata = json.loads(attempt.error_message)
        if set(metadata) != {"actor", "reason"}:
            return False
        actor = ActorIdentity.model_validate(metadata["actor"])
        if _closure_metadata(actor, metadata["reason"]) != attempt.error_message:
            return False
        _require_unsubmitted(committer, manifest, attempt)
    except (ValueError, TypeError, KeyError):
        return False
    return True


def close_unsubmitted_video_generation(committer, *, attempt_id: str,
                                      expected_manifest_revision: int,
                                      actor: ActorIdentity, reason: CloseReason):
    """Close zero-effect preparation; never cancel, refund, retry or activate."""
    from ai_video.production.project import load_production_project

    metadata = _closure_metadata(actor, reason)
    if type(expected_manifest_revision) is not int or expected_manifest_revision < 1:
        raise _state_invalid("Unsubmitted closure revision must be a positive integer.")
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        loaded = load_production_project(committer.project_root / "project.yaml")
        if loaded.manifest != manifest:
            raise _state_invalid("Manifest changed during unsubmitted closure.")
        attempt = committer._video_attempt(manifest, attempt_id)
        if is_verified_closed_unsubmitted_video_attempt(
                committer, manifest=manifest, attempt=attempt):
            if attempt.error_message != metadata:
                raise _state_invalid("Unsubmitted closure replay differs from its actor or reason.")
            return manifest
        if (attempt.status is not StateCommitStatus.RUNNING
                or type(expected_manifest_revision) is not int
                or expected_manifest_revision != manifest.manifest_revision):
            raise _state_invalid("Unsubmitted closure requires the current running request revision.")
        _require_unsubmitted(committer, manifest, attempt)
        closed = _validated_transition(attempt, {
            "status": StateCommitStatus.FAILED, "finished_at": _timestamp(),
            "error_code": ErrorCode.VIDEO_GENERATION_NOT_SUBMITTED.value,
            "error_message": metadata,
        })
        successor = _validated_transition(manifest, {
            "manifest_revision": manifest.manifest_revision + 1,
            "attempts": tuple(closed if a.attempt_id == attempt_id else a
                              for a in manifest.attempts),
        })
        committer._write_manifest_atomic(successor)
        return committer._read_manifest()


def failed_generation_history_outcome(committer, *, manifest, attempt):
    """Retain paid reconciliation and explicit zero-effect preparation separately."""
    from ai_video.production.paid_provider_no_effect_reconciliation import (
        is_verified_reconciled_no_effect_video_attempt,
    )

    closed = is_verified_closed_unsubmitted_video_attempt(
        committer, manifest=manifest, attempt=attempt,
    )
    reconciled = is_verified_reconciled_no_effect_video_attempt(
        committer, attempt_id=attempt.attempt_id,
    )
    return "not_submitted" if closed or reconciled else "runtime_failure"
