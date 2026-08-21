"""Durable continuity-evaluator checkpoint owned by the Production committer."""

from __future__ import annotations

import hashlib

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    ContinuityEvaluationIntentPointer,
    ContinuityEvaluationPhase,
    ContinuityEvaluationState,
    GeneratedShotContinuityEvidencePointer,
    QaVerdict,
)
from ai_video.production.paths import (
    canonical_continuity_evaluation_intent_path,
    canonical_generated_shot_continuity_evidence_path,
)
from ai_video.production.review import adjudicate_generated_shot_continuity
from ai_video.production.video_artifact import (
    VideoProbeReceipt,
    invoke_generated_shot_continuity_reviewer,
    validate_generated_shot_continuity_evidence,
)

from ._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact


def _prepared_artifact(relative_path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(
        relative_path, payload, hashlib.sha256(payload).hexdigest()
    )


def checkpoint_generated_shot_continuity(
    committer,
    *,
    attempt_id,
    manifest,
    attempt,
    state,
    held_fd,
    request,
    measured,
    fetch_receipt,
    continuity_reviewer,
    continuity_policy_content_hash,
    continuity_authorities,
):
    """Checkpoint intent/evidence once, then return exact reopened state and receipt."""

    evaluation_state = state.continuity_evaluation
    created_evaluation_intent = False
    intent = None
    if evaluation_state is None:
        create_intent = getattr(continuity_reviewer, "create_intent", None)
        if (
            manifest.schema_version != "2.9"
            or continuity_reviewer is None
            or create_intent is None
            or continuity_policy_content_hash is None
            or not continuity_authorities
        ):
            raise _state_invalid(
                "Continuity evaluation requires Manifest 2.9 and a durable evaluator intent."
            )
        intent = create_intent(request, measured, continuity_policy_content_hash)
        binding = request.continuity_binding
        original = request.activation_scope.request
        if (
            intent.source_shot_id != binding.terminal_frame.source_shot_id
            or intent.target_shot_id != original.target_shot_id
            or intent.target_shot_content_hash != original.target_shot_content_hash
            or intent.resolved_generation_hash != request.resolved_generation_hash
            or intent.artifact_sha256 != measured.artifact_sha256
            or intent.continuity_constraints_hash != binding.constraints.content_hash
            or intent.qa_policy_content_hash != continuity_policy_content_hash
            or intent.evaluator not in continuity_authorities
        ):
            raise _state_invalid(
                "Continuity evaluation intent does not bind exact validation inputs."
            )
        intent_artifact = _prepared_artifact(
            canonical_continuity_evaluation_intent_path(intent.content_hash),
            _canonical_json_bytes(intent),
        )
        committer._write_immutable_artifact(intent_artifact, attempt_id=attempt_id)
        committer._reopen_exact_video_artifact(intent_artifact)
        intent_pointer = ContinuityEvaluationIntentPointer(
            path=intent_artifact.relative_path,
            content_hash=intent.content_hash,
            evaluation_fingerprint=intent.evaluation_fingerprint,
            artifact_sha256=intent.artifact_sha256,
            evaluator_profile_content_hash=intent.evaluator_profile_content_hash,
            file_sha256=intent_artifact.file_sha256,
        )
        checkpoint_state = state.model_copy(
            update={
                "continuity_evaluation": ContinuityEvaluationState(
                    phase=ContinuityEvaluationPhase.INTENT,
                    intent=intent_pointer,
                )
            }
        )
        checkpoint_attempt = _validated_transition(
            attempt, {"video_generation_state": checkpoint_state}
        )
        checkpoint_manifest = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": tuple(
                    checkpoint_attempt if item.attempt_id == attempt_id else item
                    for item in manifest.attempts
                ),
            },
        )
        committer._write_manifest_atomic(checkpoint_manifest)
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None or state.continuity_evaluation is None:
            raise _state_invalid("Continuity evaluation intent checkpoint was lost.")
        evaluation_state = state.continuity_evaluation
        created_evaluation_intent = True
    else:
        intent = committer._reopen_continuity_evaluation_intent(
            evaluation_state.intent
        )

    if evaluation_state.phase is ContinuityEvaluationPhase.INTENT:
        if not created_evaluation_intent:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                user_message=(
                    "Continuity evaluator outcome is unknown; explicit recovery is required."
                ),
                retryable=False,
            )
        evidence = invoke_generated_shot_continuity_reviewer(
            held_fd,
            request,
            measured,
            continuity_reviewer,
            continuity_policy_content_hash,
            continuity_authorities,
        )
        if evidence.evaluation_fingerprint != intent.evaluation_fingerprint:
            raise _state_invalid(
                "Continuity evidence does not match its durable intent."
            )
        evidence_artifact = _prepared_artifact(
            canonical_generated_shot_continuity_evidence_path(
                evidence.content_hash
            ),
            _canonical_json_bytes(evidence),
        )
        committer._write_immutable_artifact(
            evidence_artifact, attempt_id=attempt_id
        )
        committer._reopen_exact_video_artifact(evidence_artifact)
        evidence_pointer = GeneratedShotContinuityEvidencePointer(
            path=evidence_artifact.relative_path,
            content_hash=evidence.content_hash,
            evaluation_fingerprint=evidence.evaluation_fingerprint,
            artifact_sha256=evidence.artifact_sha256,
            file_sha256=evidence_artifact.file_sha256,
        )
        evidenced_state = state.model_copy(
            update={
                "continuity_evaluation": ContinuityEvaluationState(
                    phase=ContinuityEvaluationPhase.EVIDENCED,
                    intent=evaluation_state.intent,
                    evidence=evidence_pointer,
                )
            }
        )
        evidenced_attempt = _validated_transition(
            attempt, {"video_generation_state": evidenced_state}
        )
        evidenced_manifest = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": tuple(
                    evidenced_attempt if item.attempt_id == attempt_id else item
                    for item in manifest.attempts
                ),
            },
        )
        committer._write_manifest_atomic(evidenced_manifest)
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None or state.continuity_evaluation is None:
            raise _state_invalid("Continuity evidence checkpoint was lost.")
    else:
        if evaluation_state.evidence is None:
            raise _state_invalid("Continuity evidence checkpoint is incomplete.")
        evidence = committer._reopen_generated_shot_continuity_evidence(
            evaluation_state.evidence
        )

    validate_generated_shot_continuity_evidence(
        evidence,
        request=request,
        measured=measured,
        policy_content_hash=continuity_policy_content_hash,
        authorities=continuity_authorities,
        require_pass=False,
    )
    probe_receipt = VideoProbeReceipt.create(
        request=request,
        fetch_receipt=fetch_receipt,
        measured=measured,
        continuity_evidence=evidence,
    )
    verdict = adjudicate_generated_shot_continuity(evidence)
    if verdict is not QaVerdict.PASS:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message=(
                "Generated Shot continuity review did not produce a complete passing verdict."
            ),
            technical_detail=f"verdict={verdict.value}",
            retryable=False,
        )
    return manifest, attempt, state, probe_receipt
