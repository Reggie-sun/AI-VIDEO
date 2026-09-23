"""Durable commercial Shot evaluator checkpoint owned by the Production committer."""

from __future__ import annotations

import hashlib

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.commercial_video_validation import (
    bound_commercial_source_approval,
    current_commercial_source_approval,
    validate_commercial_source_binding,
    validate_current_commercial_checkpoint,
)
from ai_video.production.ecommerce_media_acceptance import (
    adjudicate_generated_commercial_shot_evidence,
)
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports
from ai_video.production.models import (
    CommercialShotEvaluationIntentPointer,
    CommercialShotEvaluationPhase,
    CommercialShotEvaluationState,
    GeneratedCommercialShotEvidencePointer,
    QaVerdict,
    VideoAttemptPhase,
)
from ai_video.production.paths import (
    canonical_commercial_shot_evaluation_intent_path,
    canonical_generated_commercial_shot_evidence_path,
)
from ai_video.production.project import load_qa_policy
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


def commercial_evaluation_authority(committer, *, manifest, request):
    """Resolve the exact current policy and source approval before evaluation."""

    binding = request.commercial_binding
    if binding is None:
        return None, ()
    if (
        not manifest_supports(manifest.schema_version, ManifestCapability.COMMERCIAL_VIDEO)
        or manifest.active_qa_policy is None
    ):
        raise _state_invalid(
            "Commercial-bound video validation requires Manifest 2.13 and an active QA policy."
        )
    policy = load_qa_policy(committer._project_root, manifest.active_qa_policy)
    domain = policy.domain_acceptance
    requirement_ids = (
        tuple(domain.profile_payload.get("shot_requirement_ids", ()))
        if domain is not None
        else ()
    )
    if (
        domain is None
        or domain.domain_id != "ecommerce"
        or domain.profile_content_hash != binding.profile_content_hash
        or any(item not in requirement_ids for item in binding.applicable_requirement_ids)
        or not policy.semantic_authorities
    ):
        raise _state_invalid(
            "Commercial-bound video validation requires the exact active Ecommerce profile."
        )
    try:
        loaded = committer._load_production_project(
            committer._project_root / "project.yaml"
        )
        if loaded.manifest != manifest:
            raise ValueError("active commercial Manifest changed")
        approval = current_commercial_source_approval(loaded, binding)
        validate_commercial_source_binding(binding, approval)
    except (AiVideoError, OSError, ValueError) as exc:
        raise _state_invalid(
            "Commercial-bound video validation requires its exact current source approval.",
            str(exc),
        ) from exc
    return policy.content_hash, policy.semantic_authorities


def validate_current_commercial_video_state(
    committer,
    *,
    manifest,
    state,
    request,
):
    """Reopen one PASS checkpoint against its exact canonical owners."""

    evaluation = state.commercial_evaluation
    if request.commercial_binding is None and evaluation is None:
        return None
    if (
        request.commercial_binding is None
        or evaluation is None
        or evaluation.evidence is None
        or evaluation.probe is None
        or evaluation.provenance is None
        or manifest.active_qa_policy is None
    ):
        raise _state_invalid("Commercial Shot checkpoint is incomplete.")
    try:
        intent = committer._reopen_commercial_shot_evaluation_intent(
            evaluation.intent
        )
        evidence = committer._reopen_generated_commercial_shot_evidence(
            evaluation.evidence
        )
        probe = committer._reopen_video_probe_receipt(evaluation.probe)
        provenance = committer._reopen_video_provenance_receipt(
            evaluation.provenance
        )
        loaded = committer._load_production_project(
            committer._project_root / "project.yaml"
        )
        if loaded.manifest != manifest:
            raise ValueError("active commercial Manifest changed")
        if state.phase is VideoAttemptPhase.ACTIVATE:
            from ai_video.production.ecommerce_generation_bridge import (
                load_commercial_checkpoint_qa_policy,
            )

            policy = load_commercial_checkpoint_qa_policy(
                committer._project_root, evaluation, intent
            )
            loaded = loaded.model_copy(update={"qa_policy": policy})
        else:
            policy = load_qa_policy(
                committer._project_root, manifest.active_qa_policy
            )
        approval = bound_commercial_source_approval(
            loaded,
            request.commercial_binding,
            require_current=state.phase is not VideoAttemptPhase.ACTIVATE,
        )
        validate_current_commercial_checkpoint(
            request=request,
            intent=intent,
            evidence=evidence,
            probe=probe,
            policy=policy,
            approval=approval,
        )
        if (
            provenance.probe_receipt_id != probe.content_hash
            or provenance.artifact_sha256 != evidence.artifact_sha256
            or provenance.resolved_generation_hash
            != request.resolved_generation_hash
        ):
            raise ValueError("commercial provenance is not exact")
    except (AiVideoError, OSError, ValueError) as exc:
        raise _state_invalid(
            "Commercial Shot checkpoint is not current exact PASS.", str(exc)
        ) from exc
    return evidence


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
    repair_not_evaluated=False,
):
    """Persist one intent/evidence pair and return exact reopened PASS evidence."""

    evaluation_state = state.commercial_evaluation
    if repair_not_evaluated and (
        evaluation_state is None or evaluation_state.evidence is None
    ):
        raise _state_invalid(
            "Commercial evidence repair requires an exact existing evidence checkpoint."
        )
    created_intent = False
    if evaluation_state is None:
        create_intent = getattr(commercial_reviewer, "create_intent", None)
        if (
            not manifest_supports(manifest.schema_version, ManifestCapability.COMMERCIAL_VIDEO)
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
                    qa_policy=manifest.active_qa_policy,
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
                    qa_policy=evaluation_state.qa_policy,
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
        if repair_not_evaluated:
            previous_verdict = adjudicate_generated_commercial_shot_evidence(
                evidence,
                binding=request.commercial_binding,
            )
            if previous_verdict is not QaVerdict.NOT_EVALUATED:
                raise _state_invalid(
                    "Commercial evidence repair requires NOT_EVALUATED evidence."
                )
            previous_evaluation_state = evaluation_state
            repair_intent_state = state.model_copy(
                update={
                    "commercial_evaluation": CommercialShotEvaluationState(
                        phase=CommercialShotEvaluationPhase.INTENT,
                        intent=evaluation_state.intent,
                        qa_policy=evaluation_state.qa_policy,
                        evidence_history=(
                            *evaluation_state.evidence_history,
                            evaluation_state.evidence,
                        ),
                    )
                }
            )
            repair_intent_attempt = _validated_transition(
                attempt,
                {"video_generation_state": repair_intent_state},
            )
            repair_intent_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        repair_intent_attempt
                        if item.attempt_id == attempt_id
                        else item
                        for item in manifest.attempts
                    ),
                },
            )
            committer._write_manifest_atomic(repair_intent_manifest)
            manifest = committer._read_manifest()
            attempt = committer._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                state is None
                or state.commercial_evaluation is None
                or state.commercial_evaluation.phase
                is not CommercialShotEvaluationPhase.INTENT
            ):
                raise _state_invalid(
                    "Commercial evidence repair intent checkpoint was lost."
                )
            evaluation_state = state.commercial_evaluation
            replacement = invoke_generated_commercial_shot_reviewer(
                held_fd,
                request,
                measured,
                intent,
                commercial_reviewer,
                commercial_policy_content_hash,
                commercial_authorities,
            )
            known_failures = {
                item.requirement_id for item in evidence.findings
                if item.verdict is QaVerdict.FAIL
            }
            remaining_failures = {
                item.requirement_id for item in replacement.findings
                if item.verdict is QaVerdict.FAIL
            }
            duplicate_evidence = replacement.content_hash == evidence.content_hash
            if (
                duplicate_evidence
                or not known_failures <= remaining_failures
            ):
                restored_state = state.model_copy(
                    update={"commercial_evaluation": previous_evaluation_state}
                )
                restored_attempt = _validated_transition(
                    attempt,
                    {"video_generation_state": restored_state},
                )
                restored_manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "attempts": tuple(
                            restored_attempt if item.attempt_id == attempt_id else item
                            for item in manifest.attempts
                        ),
                    },
                )
                committer._write_manifest_atomic(restored_manifest)
                raise AiVideoError(
                    code=ErrorCode.REVIEW_EVIDENCE_INVALID,
                    user_message=(
                        "Commercial evidence repair did not produce new exact evidence."
                        if duplicate_evidence
                        else "Commercial evidence repair cannot clear known failures."
                    ),
                    retryable=False,
                )
            evidence_artifact = _prepared_artifact(
                canonical_generated_commercial_shot_evidence_path(
                    replacement.content_hash
                ),
                _canonical_json_bytes(replacement),
            )
            committer._write_immutable_artifact(
                evidence_artifact,
                attempt_id=attempt_id,
            )
            committer._reopen_exact_video_artifact(evidence_artifact)
            evidence_pointer = GeneratedCommercialShotEvidencePointer(
                path=evidence_artifact.relative_path,
                content_hash=replacement.content_hash,
                intent_content_hash=replacement.intent_content_hash,
                evaluation_fingerprint=replacement.evaluation_fingerprint,
                binding_content_hash=replacement.binding_content_hash,
                artifact_sha256=replacement.artifact_sha256,
                file_sha256=evidence_artifact.file_sha256,
            )
            evidenced_state = state.model_copy(
                update={
                    "commercial_evaluation": CommercialShotEvaluationState(
                        phase=CommercialShotEvaluationPhase.EVIDENCED,
                        intent=evaluation_state.intent,
                        qa_policy=evaluation_state.qa_policy,
                        evidence=evidence_pointer,
                        evidence_history=evaluation_state.evidence_history,
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
                        evidenced_attempt
                        if item.attempt_id == attempt_id
                        else item
                        for item in manifest.attempts
                    ),
                },
            )
            committer._write_manifest_atomic(evidenced_manifest)
            manifest = committer._read_manifest()
            attempt = committer._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if state is None or state.commercial_evaluation is None:
                raise _state_invalid(
                    "Repaired commercial Shot evidence checkpoint was lost."
                )
            evidence = replacement

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
