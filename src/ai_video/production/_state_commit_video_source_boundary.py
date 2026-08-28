"""Durable source-boundary P6 checkpoint owned by ProductionStateCommitter."""

from __future__ import annotations

import hashlib

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports
from ai_video.production.models import (
    QaVerdict,
    SourceBoundaryEvaluationPhase,
    SourceBoundaryEvaluationState,
    SourceBoundaryReviewEvidencePointer,
    SourceBoundaryReviewIntentPointer,
    SourceBoundaryReviewReceiptPointer,
    StateCommitStatus,
    ToolIdentity,
    VideoAttemptPhase,
    VideoProbeReceiptPointer,
    VideoProvenanceReceiptPointer,
)
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    canonical_source_boundary_review_evidence_path,
    canonical_source_boundary_review_intent_path,
    canonical_source_boundary_review_receipt_path,
    canonical_video_probe_receipt_path,
    canonical_video_provenance_receipt_path,
)
from ai_video.production.shot_continuity_source_review import (
    SourceBoundaryReviewEvidence,
    SourceBoundaryReviewIntent,
    adjudicate_source_boundary_review,
    is_source_boundary_qualification_request,
    source_boundary_supported_rubric_payload,
    validate_source_boundary_review_closure,
    validate_source_boundary_review_intent,
)
from ai_video.production.video_artifact import (
    VideoProbeReceipt,
    VideoProvenanceReceipt,
    probe_generated_video_candidate,
)

from ._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact


def _prepared_artifact(path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def _validate_supported_rubric(inputs, p0_receipt) -> None:
    rubric = next((item for item in inputs if item.input_kind == "rubric"), None)
    if (
        rubric is None
        or rubric.content_hash != p0_receipt.rubric_hash
        or rubric.payload != source_boundary_supported_rubric_payload()
    ):
        raise _state_invalid(
            "Source boundary measurement contract does not match the active P0 rubric."
        )


def _validate_intent(
    intent: SourceBoundaryReviewIntent,
    *,
    request,
    measured=None,
    fetch_receipt,
    reviewer,
    p0_receipt,
) -> None:
    scope = request.activation_scope
    if scope is None:
        raise _state_invalid("Source boundary request has no authoring scope.")
    contract = reviewer.measurement_contract
    human = reviewer.human_decision
    try:
        validate_source_boundary_review_intent(
            request=request,
            fetch_receipt=fetch_receipt,
            intent=intent,
        )
    except ValueError as exc:
        raise _state_invalid(
            "Source boundary review intent does not bind exact request/fetch inputs.",
            str(exc),
        ) from exc
    if (
        not is_source_boundary_qualification_request(request)
        or reviewer.source_execution_stack_hash != request.execution_stack_hash
        or contract.p0_qualification_receipt_hash != p0_receipt.content_hash
        or contract.p0_rubric_hash != p0_receipt.rubric_hash
        or intent.artifact_sha256 != fetch_receipt.artifact_sha256
        or intent.artifact_size_bytes != fetch_receipt.size_bytes
        or intent.source_profile_content_hash != reviewer.source_profile_content_hash
        or intent.source_execution_stack_hash != reviewer.source_execution_stack_hash
        or intent.measurement_contract_hash != contract.content_hash
        or intent.human_decision_hash != human.content_hash
        or intent.evaluator != reviewer.evaluator
        or reviewer.evaluator
        != ToolIdentity(name="ai-video-source-boundary-review", version="1")
        or human.resolved_generation_hash != request.resolved_generation_hash
        or human.artifact_sha256 != fetch_receipt.artifact_sha256
        or contract.first_frame_asset_id != request.image_bindings[0].asset_id
        or contract.first_frame_sha256 != request.image_bindings[0].asset_sha256
        or contract.last_frame_asset_id != request.image_bindings[1].asset_id
        or contract.last_frame_sha256 != request.image_bindings[1].asset_sha256
        or measured is not None
        and (
            contract.sample_width != measured.width
            or contract.sample_height != measured.height
        )
    ):
        raise _state_invalid(
            "Source boundary review intent does not bind exact qualification inputs."
        )


def validate_current_source_boundary_video_state(
    committer,
    *,
    manifest,
    state,
    request,
    require_pass: bool = True,
):
    """Strictly reopen one source-boundary PASS before activation or replay."""

    evaluation = state.source_boundary_evaluation
    required = is_source_boundary_qualification_request(request)
    if not required and evaluation is None:
        return None
    if (
        not required
        or not manifest_supports(manifest.schema_version, ManifestCapability.SOURCE_BOUNDARY)
        or evaluation is None
        or evaluation.phase is not SourceBoundaryEvaluationPhase.EVIDENCED
        or evaluation.evidence is None
        or evaluation.receipt is None
        or evaluation.probe is None
        or evaluation.provenance is None
    ):
        raise _state_invalid("Source boundary checkpoint is incomplete.")
    try:
        intent = committer._reopen_source_boundary_review_intent(evaluation.intent)
        evidence = committer._reopen_source_boundary_review_evidence(
            evaluation.evidence
        )
        receipt = committer._reopen_source_boundary_review_receipt(evaluation.receipt)
        probe = committer._reopen_video_probe_receipt(evaluation.probe)
        provenance = committer._reopen_video_provenance_receipt(evaluation.provenance)
        fetch_receipt = (
            committer._reopen_local_video_fetch(state.local_fetch_receipt)
            if state.local_fetch_receipt is not None
            else committer._reopen_video_fetch(state.fetch_receipt)
            if state.fetch_receipt is not None
            else None
        )
        if fetch_receipt is None:
            raise ValueError("source boundary fetch evidence is missing")
        p0_receipt, _, _, _, inputs, source_stacks = (
            committer.reopen_p0_qualification_history(
                evidence.measurement_contract.p0_qualification_receipt_hash
            )
        )
        _validate_supported_rubric(inputs, p0_receipt)
        rubric = next(item for item in inputs if item.input_kind == "rubric")
        validate_source_boundary_review_closure(
            request=request,
            fetch_receipt=fetch_receipt,
            intent=intent,
            evidence=evidence,
            receipt=receipt,
            probe=probe,
            provenance=provenance,
            p0_receipt=p0_receipt,
            p0_rubric=rubric,
            source_execution_stack_hashes=tuple(
                item.execution_stack_hash for item in source_stacks
            ),
            require_pass=require_pass,
        )
    except (AiVideoError, OSError, ValueError) as exc:
        raise _state_invalid(
            "Source boundary checkpoint is not current exact PASS.", str(exc)
        ) from exc
    return evidence


def checkpoint_source_boundary_review_intent(
    committer,
    *,
    attempt_id,
    manifest,
    attempt,
    state,
    request,
    measured,
    fetch_receipt,
    reviewer,
):
    """Persist the exact source intent before any decoded measurement effect."""

    if not manifest_supports(manifest.schema_version, ManifestCapability.SOURCE_BOUNDARY):
        raise _state_invalid("Source boundary intent requires Manifest 2.14.")
    evaluation = state.source_boundary_evaluation
    if evaluation is not None:
        intent = committer._reopen_source_boundary_review_intent(evaluation.intent)
        if evaluation.phase is SourceBoundaryEvaluationPhase.INTENT:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                user_message=(
                    "Source boundary measurement outcome is unknown; explicit recovery is required."
                ),
                retryable=False,
            )
        return manifest, attempt, state, False
    if reviewer is None:
        raise _state_invalid(
            "Source boundary intent requires an explicit reviewer contract."
        )
    p0_receipt, _, _, _, inputs = committer.reopen_p0_qualification_prepared()
    _validate_supported_rubric(inputs, p0_receipt)
    source_stacks = committer.reopen_p0_qualification_source_stacks()
    if reviewer.source_execution_stack_hash not in tuple(
        item.execution_stack_hash for item in source_stacks
    ):
        raise _state_invalid("Source boundary reviewer stack is not active P0 truth.")
    intent = reviewer.create_intent(request, measured, fetch_receipt, p0_receipt)
    if not isinstance(intent, SourceBoundaryReviewIntent):
        raise _state_invalid("Source boundary reviewer returned an invalid intent.")
    _validate_intent(
        intent,
        request=request,
        measured=measured,
        fetch_receipt=fetch_receipt,
        reviewer=reviewer,
        p0_receipt=p0_receipt,
    )
    artifact = _prepared_artifact(
        canonical_source_boundary_review_intent_path(intent.content_hash),
        _canonical_json_bytes(intent),
    )
    committer._write_immutable_artifact(artifact, attempt_id=attempt_id)
    committer._reopen_exact_video_artifact(artifact)
    pointer = SourceBoundaryReviewIntentPointer(
        path=artifact.relative_path,
        content_hash=intent.content_hash,
        evaluation_fingerprint=intent.evaluation_fingerprint,
        resolved_generation_hash=intent.resolved_generation_hash,
        artifact_sha256=intent.artifact_sha256,
        file_sha256=artifact.file_sha256,
    )
    checkpoint_state = state.model_copy(
        update={
            "source_boundary_evaluation": SourceBoundaryEvaluationState(
                phase=SourceBoundaryEvaluationPhase.INTENT,
                intent=pointer,
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
    reopened = committer._read_manifest()
    reopened_attempt = committer._video_attempt(reopened, attempt_id)
    reopened_state = reopened_attempt.video_generation_state
    if (
        reopened_state is None
        or reopened_state.source_boundary_evaluation is None
        or reopened_state.source_boundary_evaluation.intent != pointer
    ):
        raise _state_invalid("Source boundary intent checkpoint was lost.")
    return reopened, reopened_attempt, reopened_state, True


def checkpoint_source_boundary_review(
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
    observation,
    local_lane,
    reviewer,
):
    """Persist intent then evidence; replay never invokes the reviewer again."""

    if not manifest_supports(manifest.schema_version, ManifestCapability.SOURCE_BOUNDARY):
        raise _state_invalid("Source boundary validation requires Manifest 2.14.")
    evaluation = state.source_boundary_evaluation
    if reviewer is None:
        if (
            evaluation is None
            or evaluation.phase is not SourceBoundaryEvaluationPhase.EVIDENCED
            or evaluation.probe is None
            or evaluation.provenance is None
        ):
            raise _state_invalid(
                "Source boundary validation requires an explicit reviewer."
            )
        validate_current_source_boundary_video_state(
            committer,
            manifest=manifest,
            state=state,
            request=request,
        )
        return (
            manifest,
            attempt,
            state,
            committer._reopen_video_probe_receipt(evaluation.probe),
            committer._reopen_video_provenance_receipt(evaluation.provenance),
        )
    manifest, attempt, state, intent_created = checkpoint_source_boundary_review_intent(
        committer,
        attempt_id=attempt_id,
        manifest=manifest,
        attempt=attempt,
        state=state,
        request=request,
        measured=measured,
        fetch_receipt=fetch_receipt,
        reviewer=reviewer,
    )
    evaluation = state.source_boundary_evaluation
    p0_receipt, _, _, _, inputs = committer.reopen_p0_qualification_prepared()
    _validate_supported_rubric(inputs, p0_receipt)
    source_stacks = committer.reopen_p0_qualification_source_stacks()
    if reviewer.source_execution_stack_hash not in tuple(
        item.execution_stack_hash for item in source_stacks
    ):
        raise _state_invalid("Source boundary reviewer stack is not active P0 truth.")

    if evaluation is None:
        raise _state_invalid("Source boundary intent checkpoint is missing.")
    intent = committer._reopen_source_boundary_review_intent(evaluation.intent)
    _validate_intent(
        intent,
        request=request,
        measured=measured,
        fetch_receipt=fetch_receipt,
        reviewer=reviewer,
        p0_receipt=p0_receipt,
    )

    if evaluation.phase is SourceBoundaryEvaluationPhase.INTENT:
        if not intent_created:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                user_message=(
                    "Source boundary evaluator outcome is unknown; explicit recovery is required."
                ),
                retryable=False,
            )
        evidence = reviewer(held_fd, request, measured, intent)
        if not isinstance(evidence, SourceBoundaryReviewEvidence):
            raise _state_invalid("Source boundary reviewer returned invalid evidence.")
        receipt = adjudicate_source_boundary_review(evidence)
        if (
            evidence.intent != intent
            or evidence.measurement_contract != reviewer.measurement_contract
            or evidence.human_decision != reviewer.human_decision
            or evidence.measured_metadata_hash != canonical_sha256(measured)
            or evidence.first_frame.frame_index != 0
            or evidence.last_frame.frame_index != measured.frame_count - 1
        ):
            raise _state_invalid("Source boundary evidence is not exact.")
        probe = VideoProbeReceipt.create(
            request=request,
            fetch_receipt=fetch_receipt,
            measured=measured,
        )
        provenance = (
            VideoProvenanceReceipt.create_local(
                request=request,
                observation=observation,
                fetch_receipt=fetch_receipt,
                probe_receipt=probe,
            )
            if local_lane
            else VideoProvenanceReceipt.create(
                request=request,
                observation=observation,
                fetch_receipt=fetch_receipt,
                probe_receipt=probe,
            )
        )
        evidence_artifact = _prepared_artifact(
            canonical_source_boundary_review_evidence_path(evidence.content_hash),
            _canonical_json_bytes(evidence),
        )
        receipt_artifact = _prepared_artifact(
            canonical_source_boundary_review_receipt_path(receipt.content_hash),
            _canonical_json_bytes(receipt),
        )
        probe_artifact = _prepared_artifact(
            canonical_video_probe_receipt_path(probe.content_hash),
            _canonical_json_bytes(probe),
        )
        provenance_artifact = _prepared_artifact(
            canonical_video_provenance_receipt_path(provenance.content_hash),
            _canonical_json_bytes(provenance),
        )
        for artifact in (
            evidence_artifact,
            receipt_artifact,
            probe_artifact,
            provenance_artifact,
        ):
            committer._write_immutable_artifact(artifact, attempt_id=attempt_id)
            committer._reopen_exact_video_artifact(artifact)
        evidenced_state = state.model_copy(
            update={
                "source_boundary_evaluation": SourceBoundaryEvaluationState(
                    phase=SourceBoundaryEvaluationPhase.EVIDENCED,
                    intent=evaluation.intent,
                    evidence=SourceBoundaryReviewEvidencePointer(
                        path=evidence_artifact.relative_path,
                        content_hash=evidence.content_hash,
                        intent_content_hash=intent.content_hash,
                        evaluation_fingerprint=intent.evaluation_fingerprint,
                        artifact_sha256=intent.artifact_sha256,
                        file_sha256=evidence_artifact.file_sha256,
                    ),
                    receipt=SourceBoundaryReviewReceiptPointer(
                        path=receipt_artifact.relative_path,
                        content_hash=receipt.content_hash,
                        intent_content_hash=receipt.intent_content_hash,
                        evidence_content_hash=receipt.evidence_content_hash,
                        resolved_generation_hash=receipt.resolved_generation_hash,
                        artifact_sha256=receipt.artifact_sha256,
                        verdict=receipt.verdict.value,
                        file_sha256=receipt_artifact.file_sha256,
                    ),
                    probe=VideoProbeReceiptPointer(
                        path=probe_artifact.relative_path,
                        content_hash=probe.content_hash,
                        request_receipt_fingerprint=probe.request_receipt_fingerprint,
                        resolved_generation_hash=probe.resolved_generation_hash,
                        fetch_fingerprint=probe.fetch_fingerprint,
                        artifact_sha256=probe.measured.artifact_sha256,
                        file_sha256=probe_artifact.file_sha256,
                    ),
                    provenance=VideoProvenanceReceiptPointer(
                        path=provenance_artifact.relative_path,
                        content_hash=provenance.content_hash,
                        request_receipt_fingerprint=provenance.request_receipt_fingerprint,
                        resolved_generation_hash=provenance.resolved_generation_hash,
                        fetch_fingerprint=provenance.fetch_fingerprint,
                        artifact_sha256=provenance.artifact_sha256,
                        probe_receipt_id=provenance.probe_receipt_id,
                        file_sha256=provenance_artifact.file_sha256,
                    ),
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
        if state is None or state.source_boundary_evaluation is None:
            raise _state_invalid("Source boundary evidence checkpoint was lost.")
        evaluation = state.source_boundary_evaluation
    else:
        if evaluation.evidence is None or evaluation.receipt is None:
            raise _state_invalid("Source boundary checkpoint is incomplete.")
        evidence = committer._reopen_source_boundary_review_evidence(
            evaluation.evidence
        )
        receipt = committer._reopen_source_boundary_review_receipt(evaluation.receipt)
        if evaluation.probe is None or evaluation.provenance is None:
            raise _state_invalid("Source boundary capture checkpoint is incomplete.")
        probe = committer._reopen_video_probe_receipt(evaluation.probe)
        provenance = committer._reopen_video_provenance_receipt(evaluation.provenance)

    expected_receipt = adjudicate_source_boundary_review(evidence)
    if (
        receipt != expected_receipt
        or probe.fetch_fingerprint != fetch_receipt.fetch_fingerprint
        or probe.measured != measured
        or provenance.probe_receipt_id != probe.content_hash
        or provenance.artifact_sha256 != measured.artifact_sha256
    ):
        raise _state_invalid("Source boundary capture checkpoint is not exact.")
    if receipt.verdict is not QaVerdict.PASS:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message="Source boundary P6 review did not pass.",
            technical_detail=f"verdict={receipt.verdict.value}",
            retryable=False,
        )
    return manifest, attempt, state, probe, provenance


def recover_source_boundary_review(
    committer,
    *,
    attempt_id: str,
    recovered_evidence: SourceBoundaryReviewEvidence,
    probe=None,
):
    """Explicitly seal a recovered evaluator outcome without rerunning it."""

    if not isinstance(recovered_evidence, SourceBoundaryReviewEvidence):
        raise _state_invalid("Recovered source boundary evidence is invalid.")
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (
            not manifest_supports(manifest.schema_version, ManifestCapability.SOURCE_BOUNDARY)
            or attempt.status
            not in {StateCommitStatus.RUNNING, StateCommitStatus.INTERRUPTED}
            or state is None
            or state.phase is not VideoAttemptPhase.VALIDATE
            or state.source_boundary_evaluation is None
            or state.source_boundary_evaluation.phase
            is not SourceBoundaryEvaluationPhase.INTENT
            or state.source_boundary_evaluation.evidence is not None
            or state.local_fetch_receipt is None
            or state.local_latest_observation is None
        ):
            raise _state_invalid(
                "Source boundary recovery requires one exact local intent-only checkpoint."
            )
        evaluation = state.source_boundary_evaluation
        request = committer._reopen_video_request(state.request)
        if not is_source_boundary_qualification_request(request):
            raise _state_invalid("Source boundary recovery request is not exact.")
        intent = committer._reopen_source_boundary_review_intent(evaluation.intent)
        fetch_receipt = committer._reopen_local_video_fetch(state.local_fetch_receipt)
        observation = committer._reopen_local_video_status(
            state.local_latest_observation
        )
        with _open_regular_file_nofollow(
            committer._project_root / state.local_fetch_receipt.artifact_path,
            contained_by=(
                committer._project_root / "state" / "video-generation" / "fetch"
            ),
        ) as (held_fd, _):
            _, measured, probe_receipt = probe_generated_video_candidate(
                held_fd,
                request,
                fetch_receipt,
                probe=probe,
            )
        evidence = SourceBoundaryReviewEvidence.model_validate(
            recovered_evidence.model_dump(mode="python")
        )
        receipt = adjudicate_source_boundary_review(evidence)
        provenance = VideoProvenanceReceipt.create_local(
            request=request,
            observation=observation,
            fetch_receipt=fetch_receipt,
            probe_receipt=probe_receipt,
        )
        p0_receipt, _, _, _, inputs, source_stacks = (
            committer.reopen_p0_qualification_history(
                evidence.measurement_contract.p0_qualification_receipt_hash
            )
        )
        _validate_supported_rubric(inputs, p0_receipt)
        rubric = next(item for item in inputs if item.input_kind == "rubric")
        try:
            validate_source_boundary_review_closure(
                request=request,
                fetch_receipt=fetch_receipt,
                intent=intent,
                evidence=evidence,
                receipt=receipt,
                probe=probe_receipt,
                provenance=provenance,
                p0_receipt=p0_receipt,
                p0_rubric=rubric,
                source_execution_stack_hashes=tuple(
                    item.execution_stack_hash for item in source_stacks
                ),
                require_pass=False,
            )
        except ValueError as exc:
            raise _state_invalid(
                "Recovered source boundary evidence is not exact PASS.",
                str(exc),
            ) from exc

        evidence_artifact = _prepared_artifact(
            canonical_source_boundary_review_evidence_path(evidence.content_hash),
            _canonical_json_bytes(evidence),
        )
        receipt_artifact = _prepared_artifact(
            canonical_source_boundary_review_receipt_path(receipt.content_hash),
            _canonical_json_bytes(receipt),
        )
        probe_artifact = _prepared_artifact(
            canonical_video_probe_receipt_path(probe_receipt.content_hash),
            _canonical_json_bytes(probe_receipt),
        )
        provenance_artifact = _prepared_artifact(
            canonical_video_provenance_receipt_path(provenance.content_hash),
            _canonical_json_bytes(provenance),
        )
        for artifact in (
            evidence_artifact,
            receipt_artifact,
            probe_artifact,
            provenance_artifact,
        ):
            committer._write_immutable_artifact(artifact, attempt_id=attempt_id)
            committer._reopen_exact_video_artifact(artifact)
        recovered_state = state.model_copy(
            update={
                "source_boundary_evaluation": SourceBoundaryEvaluationState(
                    phase=SourceBoundaryEvaluationPhase.EVIDENCED,
                    intent=evaluation.intent,
                    evidence=SourceBoundaryReviewEvidencePointer(
                        path=evidence_artifact.relative_path,
                        content_hash=evidence.content_hash,
                        intent_content_hash=intent.content_hash,
                        evaluation_fingerprint=intent.evaluation_fingerprint,
                        artifact_sha256=intent.artifact_sha256,
                        file_sha256=evidence_artifact.file_sha256,
                    ),
                    receipt=SourceBoundaryReviewReceiptPointer(
                        path=receipt_artifact.relative_path,
                        content_hash=receipt.content_hash,
                        intent_content_hash=receipt.intent_content_hash,
                        evidence_content_hash=receipt.evidence_content_hash,
                        resolved_generation_hash=receipt.resolved_generation_hash,
                        artifact_sha256=receipt.artifact_sha256,
                        verdict=receipt.verdict.value,
                        file_sha256=receipt_artifact.file_sha256,
                    ),
                    probe=VideoProbeReceiptPointer(
                        path=probe_artifact.relative_path,
                        content_hash=probe_receipt.content_hash,
                        request_receipt_fingerprint=(
                            probe_receipt.request_receipt_fingerprint
                        ),
                        resolved_generation_hash=(
                            probe_receipt.resolved_generation_hash
                        ),
                        fetch_fingerprint=probe_receipt.fetch_fingerprint,
                        artifact_sha256=probe_receipt.measured.artifact_sha256,
                        file_sha256=probe_artifact.file_sha256,
                    ),
                    provenance=VideoProvenanceReceiptPointer(
                        path=provenance_artifact.relative_path,
                        content_hash=provenance.content_hash,
                        request_receipt_fingerprint=(
                            provenance.request_receipt_fingerprint
                        ),
                        resolved_generation_hash=(provenance.resolved_generation_hash),
                        fetch_fingerprint=provenance.fetch_fingerprint,
                        artifact_sha256=provenance.artifact_sha256,
                        probe_receipt_id=provenance.probe_receipt_id,
                        file_sha256=provenance_artifact.file_sha256,
                    ),
                )
            }
        )
        recovered_attempt = _validated_transition(
            attempt,
            {
                "status": StateCommitStatus.RUNNING,
                "video_generation_state": recovered_state,
                "error_code": None,
                "error_message": None,
                "finished_at": None,
            },
        )
        recovered_manifest = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": tuple(
                    recovered_attempt if item.attempt_id == attempt_id else item
                    for item in manifest.attempts
                ),
            },
        )
        committer._write_manifest_atomic(recovered_manifest)
        reopened = committer._read_manifest()
        if reopened != recovered_manifest:
            raise _state_invalid(
                "Recovered source boundary Manifest did not reopen exactly."
            )
        validate_current_source_boundary_video_state(
            committer,
            manifest=reopened,
            state=recovered_state,
            request=request,
            require_pass=False,
        )
        return reopened


__all__ = [
    "checkpoint_source_boundary_review_intent",
    "checkpoint_source_boundary_review",
    "recover_source_boundary_review",
    "validate_current_source_boundary_video_state",
]
