"""Durable commercial Shot evaluator checkpoint owned by the Production committer."""

from __future__ import annotations

import hashlib

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    CommercialShotEvaluationIntentPointer,
    CommercialShotEvaluationPhase,
    CommercialShotEvaluationState,
    GeneratedCommercialShotEvidencePointer,
    QaVerdict,
)
from ai_video.production.paths import (
    canonical_commercial_shot_evaluation_intent_path,
    canonical_generated_commercial_shot_evidence_path,
)
from ai_video.production.ecommerce_media_acceptance import (
    adjudicate_generated_commercial_shot_evidence,
)
from ai_video.production.video_artifact import (
    invoke_generated_commercial_shot_reviewer,
    validate_generated_commercial_shot_evidence,
    validate_generated_commercial_shot_intent,
)

from ._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact


def _prepared_artifact(relative_path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(
        relative_path,
        payload,
        hashlib.sha256(payload).hexdigest(),
    )


def checkpoint_generated_commercial_shot(
    committer,
    *,
    attempt_id,
    manifest,
    attempt,
    state,
    held_fd,
    request,
    measured,
    commercial_reviewer,
    commercial_policy_content_hash,
    commercial_authorities,
):
    """Persist one intent/evidence pair and return exact reopened PASS evidence."""

    evaluation_state = state.commercial_evaluation
    created_intent = False
    if evaluation_state is None:
        create_intent = getattr(commercial_reviewer, "create_intent", None)
        if (
            manifest.schema_version != "2.13"
            or request.commercial_binding is None
            or commercial_reviewer is None
            or create_intent is None
            or commercial_policy_content_hash is None
            or not commercial_authorities
        ):
            raise _state_invalid(
                "Commercial-bound video validation requires Manifest 2.13 and a durable evaluator intent."
            )
        intent = create_intent(
            request,
            measured,
            commercial_policy_content_hash,
        )
        try:
            validate_generated_commercial_shot_intent(
                intent,
                request=request,
                measured=measured,
                policy_content_hash=commercial_policy_content_hash,
                authorities=commercial_authorities,
            )
        except AiVideoError as exc:
            raise _state_invalid(
                "Commercial Shot evaluation intent does not bind exact validation inputs.",
                exc.technical_detail or str(exc),
            ) from exc
        intent_artifact = _prepared_artifact(
            canonical_commercial_shot_evaluation_intent_path(intent.content_hash),
            _canonical_json_bytes(intent),
        )
        committer._write_immutable_artifact(intent_artifact, attempt_id=attempt_id)
        committer._reopen_exact_video_artifact(intent_artifact)
        intent_pointer = CommercialShotEvaluationIntentPointer(
            path=intent_artifact.relative_path,
            content_hash=intent.content_hash,
            evaluation_fingerprint=intent.evaluation_fingerprint,
            binding_content_hash=intent.binding_content_hash,
            artifact_sha256=intent.artifact_sha256,
            evaluator_profile_content_hash=intent.evaluator_profile_content_hash,
            file_sha256=intent_artifact.file_sha256,
        )
        checkpoint_state = state.model_copy(
            update={
                "commercial_evaluation": CommercialShotEvaluationState(
                    phase=CommercialShotEvaluationPhase.INTENT,
                    intent=intent_pointer,
                )
            }
        )
        checkpoint_attempt = _validated_transition(
            attempt,
            {"video_generation_state": checkpoint_state},
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
        if state is None or state.commercial_evaluation is None:
            raise _state_invalid("Commercial Shot evaluation intent checkpoint was lost.")
        evaluation_state = state.commercial_evaluation
        created_intent = True
    intent = committer._reopen_commercial_shot_evaluation_intent(
        evaluation_state.intent
    )
    try:
        validate_generated_commercial_shot_intent(
            intent,
            request=request,
            measured=measured,
            policy_content_hash=commercial_policy_content_hash,
            authorities=commercial_authorities,
        )
    except AiVideoError as exc:
        raise _state_invalid(
            "Commercial Shot evaluation intent checkpoint is not exact.",
            exc.technical_detail or str(exc),
        ) from exc

    if evaluation_state.phase is CommercialShotEvaluationPhase.INTENT:
        if not created_intent:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                user_message=(
                    "Commercial Shot evaluator outcome is unknown; explicit recovery is required."
                ),
                retryable=False,
            )
        evidence = invoke_generated_commercial_shot_reviewer(
            held_fd,
            request,
            measured,
            intent,
            commercial_reviewer,
            commercial_policy_content_hash,
            commercial_authorities,
        )
        evidence_artifact = _prepared_artifact(
            canonical_generated_commercial_shot_evidence_path(
                evidence.content_hash
            ),
            _canonical_json_bytes(evidence),
        )
        committer._write_immutable_artifact(
            evidence_artifact,
            attempt_id=attempt_id,
        )
        committer._reopen_exact_video_artifact(evidence_artifact)
        evidence_pointer = GeneratedCommercialShotEvidencePointer(
            path=evidence_artifact.relative_path,
            content_hash=evidence.content_hash,
            intent_content_hash=evidence.intent_content_hash,
            evaluation_fingerprint=evidence.evaluation_fingerprint,
            binding_content_hash=evidence.binding_content_hash,
            artifact_sha256=evidence.artifact_sha256,
            file_sha256=evidence_artifact.file_sha256,
        )
        evidenced_state = state.model_copy(
            update={
                "commercial_evaluation": CommercialShotEvaluationState(
                    phase=CommercialShotEvaluationPhase.EVIDENCED,
                    intent=evaluation_state.intent,
                    evidence=evidence_pointer,
                )
            }
        )
        evidenced_attempt = _validated_transition(
            attempt,
            {"video_generation_state": evidenced_state},
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
        if state is None or state.commercial_evaluation is None:
            raise _state_invalid("Commercial Shot evidence checkpoint was lost.")
    else:
        if evaluation_state.evidence is None:
            raise _state_invalid("Commercial Shot evidence checkpoint is incomplete.")
        evidence = committer._reopen_generated_commercial_shot_evidence(
            evaluation_state.evidence
        )

    validate_generated_commercial_shot_evidence(
        evidence,
        request=request,
        measured=measured,
        policy_content_hash=commercial_policy_content_hash,
        authorities=commercial_authorities,
        require_pass=False,
        intent=intent,
    )
    verdict = adjudicate_generated_commercial_shot_evidence(
        evidence,
        binding=request.commercial_binding,
    )
    if verdict is not QaVerdict.PASS:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message=(
                "Commercial Shot review did not produce a complete passing verdict."
            ),
            technical_detail=f"verdict={verdict.value}",
            retryable=False,
        )
    return manifest, attempt, state, evidence
