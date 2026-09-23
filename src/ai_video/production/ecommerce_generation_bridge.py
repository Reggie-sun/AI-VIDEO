"""Project one exact commercial Shot failure into the selected generation QA."""

from __future__ import annotations

from pathlib import Path

from ai_video.production.artifact_contracts import QaPolicyPointer
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
    QaPolicy,
    StateCommitStatus,
    VideoAttemptPhase,
)


def _commercial_failure_source(*, root, state, request, qa_policy, qa_policy_pointer, acceptance):
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
        or qa_policy_pointer is None
        or qa_policy_pointer.content_hash != qa_policy.content_hash
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
        commercial_qa_policy=qa_policy_pointer,
    )


def validate_commercial_failure_evaluation_source(
    *, root, state, request, qa_policy, qa_policy_pointer, acceptance, source
) -> None:
    """Reopen the original Gate evidence; a caller cannot append its hash by hand."""

    if source.commercial_evidence_content_hash is None:
        raise ValueError("generation source has no commercial evidence identity")
    if source.commercial_qa_policy != qa_policy_pointer:
        raise ValueError("generation source has no exact evaluation-time QA pointer")
    expected = _commercial_failure_source(
        root=root,
        state=state,
        request=request,
        qa_policy=qa_policy,
        qa_policy_pointer=qa_policy_pointer,
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
        qa_policy_pointer=loaded.manifest.active_qa_policy,
        acceptance=selected_shot_generation_acceptance(
            loaded, binding.target_shot_id
        ),
    )


def commercial_failure_repair_readiness(*, root: Path, loaded, attempt) -> str:
    """Project current QA readiness without changing the failed attempt."""

    from ai_video.production._video_project_reader import (
        load_commercial_shot_evaluation_intent,
        load_generation_experience,
        load_video_request_receipt,
    )
    from ai_video.production.production_strategy_reader import (
        selected_shot_generation_acceptance,
    )

    state = attempt.video_generation_state
    if state is None:
        return "UNMAPPED"
    request = load_video_request_receipt(root, state.request)
    binding = request.commercial_binding
    if binding is None:
        return "UNMAPPED"
    if state.generation_experiences:
        experience = load_generation_experience(
            root, state.generation_experiences[-1]
        )
        tagged = tuple(
            source for source in experience.evaluation_sources
            if source.commercial_evidence_content_hash is not None
        )
        if tagged:
            if len(tagged) != 1:
                return "UNMAPPED"
            acceptance = selected_shot_generation_acceptance(
                loaded, binding.target_shot_id
            )
            if (
                tagged[0].commercial_qa_policy != loaded.manifest.active_qa_policy
                or acceptance is None
                or tagged[0].rubric_hash != acceptance.profile_content_hash
            ):
                return "QA_CHANGED"
            return "READY"  # Strict project reopen checked the frozen source.
    evaluation = state.commercial_evaluation
    if evaluation is not None:
        intent = load_commercial_shot_evaluation_intent(root, evaluation.intent)
        if (
            loaded.qa_policy is None
            or intent.qa_policy_content_hash != loaded.qa_policy.content_hash
        ):
            return "QA_CHANGED"
    try:
        _commercial_failure_source(
            root=root,
            state=state,
            request=request,
            qa_policy=loaded.qa_policy,
            qa_policy_pointer=loaded.manifest.active_qa_policy,
            acceptance=selected_shot_generation_acceptance(
                loaded, binding.target_shot_id
            ),
        )
    except ValueError:
        return "UNMAPPED"
    return "READY"


def load_frozen_commercial_qa_policy(root: Path, content_hash: str) -> QaPolicy:
    """Reopen the canonical policy named by a historical commercial intent."""

    from ai_video.production.paths import (
        _read_regular_file_nofollow,
        canonical_qa_policy_path,
    )
    from ai_video.production.project import load_qa_policy

    root = Path(root).resolve(strict=True)
    relative = canonical_qa_policy_path(content_hash)
    snapshot = _read_regular_file_nofollow(
        root / relative, contained_by=root / "state"
    )
    candidate = QaPolicy.model_validate_json(snapshot.data)
    pointer = QaPolicyPointer(
        path=relative,
        policy_id=candidate.policy_id,
        policy_version=candidate.policy_version,
        content_hash=content_hash,
        file_sha256=snapshot.file_sha256,
    )
    return load_qa_policy(root, pointer)


def load_commercial_checkpoint_qa_policy(root, evaluation, intent) -> QaPolicy:
    """Verify the original policy pointer when the checkpoint records its bytes."""

    if evaluation.qa_policy is None:
        policy = load_frozen_commercial_qa_policy(
            root, intent.qa_policy_content_hash
        )
    else:
        from ai_video.production.project import load_qa_policy

        policy = load_qa_policy(root, evaluation.qa_policy)
    if policy.content_hash != intent.qa_policy_content_hash:
        raise ValueError("Commercial evaluation QA policy identity changed")
    return policy
