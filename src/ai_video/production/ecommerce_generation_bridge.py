"""Project one exact commercial Shot failure into the selected generation QA."""

from __future__ import annotations

from pathlib import Path

from ai_video.production.ecommerce_media_acceptance import (
    adjudicate_generated_commercial_shot_evidence,
)
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource,
    GenerationObservation,
)
from ai_video.production.models import (
    CommercialShotEvaluationPhase,
    EvidenceStrength,
    QaVerdict,
    StateCommitStatus,
    VideoAttemptPhase,
)


def _commercial_failure_source(*, root, state, request, qa_policy, acceptance):
    from ai_video.production._video_project_reader import (
        load_commercial_shot_evaluation_intent,
        load_generated_commercial_shot_evidence,
        load_local_video_fetch_receipt,
        load_video_fetch_receipt,
    )

    evaluation = state.commercial_evaluation
    binding = request.commercial_binding
    fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
    if (
        state.phase is not VideoAttemptPhase.VALIDATE
        or evaluation is None
        or evaluation.phase is not CommercialShotEvaluationPhase.EVIDENCED
        or evaluation.evidence is None
        or binding is None
        or fetch_pointer is None
        or qa_policy is None
        or acceptance is None
        or acceptance.profile_payload.get("requirement_semantics_version")
        or qa_policy.domain_acceptance is None
        or qa_policy.domain_acceptance.profile_content_hash != binding.profile_content_hash
    ):
        raise ValueError("commercial generation projection needs a complete unmarked QA checkpoint")
    intent = load_commercial_shot_evaluation_intent(root, evaluation.intent)
    evidence = load_generated_commercial_shot_evidence(root, evaluation.evidence)
    fetch = (
        load_local_video_fetch_receipt(root, fetch_pointer)
        if state.local_fetch_receipt is not None
        else load_video_fetch_receipt(root, fetch_pointer)
    )
    if (
        evidence.intent_content_hash != intent.content_hash
        or evidence.content_hash != evaluation.evidence.content_hash
        or evidence.evaluation_fingerprint != intent.evaluation_fingerprint
        or evidence.binding_content_hash != binding.content_hash
        or evidence.resolved_generation_hash != request.resolved_generation_hash
        or evidence.artifact_sha256 != fetch.artifact_sha256
        or evidence.artifact_sha256 != intent.artifact_sha256
        or evidence.measured_metadata_hash != intent.measured_metadata_hash
        or evidence.qa_policy_content_hash != qa_policy.content_hash
        or intent.qa_policy_content_hash != qa_policy.content_hash
        or intent.binding_content_hash != binding.content_hash
        or intent.evaluator != evidence.evaluator
        or evidence.evaluator not in qa_policy.semantic_authorities
        or adjudicate_generated_commercial_shot_evidence(evidence, binding=binding)
        is not QaVerdict.FAIL
    ):
        raise ValueError("commercial generation projection is not the exact failed fetched Shot")
    proof = "human" if evidence.strength is EvidenceStrength.HUMAN else "analyzer"
    authorities = qa_policy.generation_evaluation_authorities
    if not any(item.evaluator == evidence.evaluator and item.proof == proof for item in authorities):
        raise ValueError("commercial evaluator is not a selected generation QA authority")
    rules = {
        item["requirement_id"]: item
        for item in acceptance.profile_payload.get("generation_requirements", ())
    }
    if any(
        requirement_id not in rules
        or rules[requirement_id]["level"] != "acceptance"
        or rules[requirement_id]["stage"] != "raw_generation"
        or rules[requirement_id]["proof"] != proof
        for requirement_id in binding.applicable_requirement_ids
    ):
        raise ValueError("commercial findings have no selected raw-generation QA mapping")
    return GenerationEvaluationSource(
        request_hash=request.request_input_hash,
        artifact_sha256=fetch.artifact_sha256,
        rubric_hash=acceptance.profile_content_hash,
        qa_policy_content_hash=qa_policy.content_hash,
        evaluator=evidence.evaluator,
        proof=proof,
        observations=tuple(
            GenerationObservation(
                requirement_id=item.requirement_id,
                verdict=item.verdict.name,
                observation=item.rationale,
            )
            for item in evidence.findings
        ),
        commercial_evidence_content_hash=evidence.content_hash,
    )


def validate_commercial_failure_evaluation_source(
    *, root, state, request, qa_policy, acceptance, source
) -> None:
    """Reopen the original Gate evidence; a caller cannot append its hash by hand."""

    if source.commercial_evidence_content_hash is None:
        raise ValueError("generation source has no commercial evidence identity")
    expected = _commercial_failure_source(
        root=root,
        state=state,
        request=request,
        qa_policy=qa_policy,
        acceptance=acceptance,
    )
    if source != expected:
        raise ValueError("generation source differs from exact commercial findings")


def commercial_failure_evaluation_source(
    *, root: Path, attempt_id: str
) -> GenerationEvaluationSource:
    """Return the original commercial FAIL as a source, with no media effects."""

    from ai_video.production._video_project_reader import load_video_request_receipt
    from ai_video.production.production_strategy_reader import (
        selected_shot_generation_acceptance,
    )
    from ai_video.production.project import load_production_project

    loaded = load_production_project(root / "project.yaml")
    attempt = next(
        (item for item in loaded.manifest.attempts if item.attempt_id == attempt_id),
        None,
    )
    if attempt is None or attempt.status is not StateCommitStatus.RUNNING:
        raise ValueError("commercial source requires the current running Shot attempt")
    state = attempt.video_generation_state
    if state is None:
        raise ValueError("commercial source requires video generation state")
    request = load_video_request_receipt(root, state.request)
    binding = request.commercial_binding
    if binding is None:
        raise ValueError("commercial source requires a bound Shot request")
    return _commercial_failure_source(
        root=root,
        state=state,
        request=request,
        qa_policy=loaded.qa_policy,
        acceptance=selected_shot_generation_acceptance(
            loaded, binding.target_shot_id
        ),
    )
