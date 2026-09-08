"""Explicit close of a known fetched media QUALITY_FAILURE."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import replace

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource,
    GenerationObservation,
)
from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.generation_feedback import record_attempt_evaluation
from ai_video.production.generation_rejection import GenerationQualityRejectionReceipt
from ai_video.production._lifecycle_schema import (
    GenerationExperienceReceiptPointer, GenerationQualityRejectionReceiptPointer,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.hashing import seal_artifact
from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
from ai_video.production.models import (
    ActorIdentity, PaidProviderAttemptPhase, StateCommitStatus, ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_common import _canonical_json_bytes
from ai_video.production.video_pre_generation import (
    VideoPreGenerationDependencyInputs,
    build_video_pre_generation_applied_evidence,
    build_video_pre_generation_dependency_graph,
)
from ai_video_mcp.generation_feedback import review_generation_attempt

from test_generation_history_import_receipt import _legacy_source
from test_production_generated_video_e2e import ATTEMPT_ID


ACTOR = ActorIdentity(actor_id="codex-quality-close", actor_kind="codex")


def _fetched_experience(tmp_path, *, verdict="FAIL"):
    """Use the standard remote/metered fixture through fetched VALIDATE."""
    _, original, _, source = _legacy_source(tmp_path, strip_binding=False)
    candidate = original.candidate
    source = GenerationEvaluationSource(
        request_hash=source.request_hash,
        artifact_sha256=source.artifact_sha256,
        rubric_hash=source.rubric_hash,
        qa_policy_content_hash=source.qa_policy_content_hash,
        evaluator=source.evaluator,
        proof=source.proof,
        observations=(GenerationObservation(
            requirement_id=candidate.recipe.expressions[0].requirement_id,
            verdict=verdict,
            observation="Exact retained evaluator records the visibly malformed hand.",
        ),),
    )
    evidence = original.evidence[0].model_copy(
        update={"findings": source.project_findings()}
    )
    experience = GenerationExperience(
        projection=original.projection,
        candidate=candidate,
        evidence=(evidence,),
        evaluation_sources=(source,),
    )
    committer = ProductionStateCommitter(tmp_path)
    committer.record_generation_experience(
        attempt_id=ATTEMPT_ID, experience=experience
    )
    manifest = committer._read_manifest()
    attempt = next(item for item in manifest.attempts if item.attempt_id == ATTEMPT_ID)
    assert attempt.status is StateCommitStatus.RUNNING
    assert attempt.video_generation_state.phase is VideoAttemptPhase.VALIDATE
    return committer, experience, manifest, attempt


def _fetched_mixed_failure(tmp_path):
    committer, original, _, _ = _fetched_experience(tmp_path, verdict="NOT_EVALUATED")
    loaded = load_production_project(tmp_path / "project.yaml")
    from ai_video.production.models import GenerationEvaluationAuthority

    policy = loaded.qa_policy
    authority = GenerationEvaluationAuthority(
        proof="human", evaluator=policy.semantic_authorities[0],
    )
    policy = seal_artifact(policy.model_copy(update={
        "revision": policy.revision + 1,
        "generation_evaluation_authorities": (*policy.generation_evaluation_authorities, authority),
        "content_hash": "0" * 64,
    }))
    committer.activate_qa_policy(policy, expected_manifest_revision=loaded.manifest.manifest_revision,
                                 attempt_id="mixed-failure-authority")
    technical = original.evaluation_sources[0].model_copy(update={"qa_policy_content_hash": policy.content_hash})
    human = technical.model_copy(update={
        "proof": "human",
        "observations": (GenerationObservation(requirement_id="duration", verdict="FAIL",
            observation="Viewer rejects the usable duration; technical measurement is irrecoverable."),),
    })
    experience = original.model_copy(update={
        "evaluation_sources": (technical, human),
        "evidence": (original.evidence[0].model_copy(update={
            "findings": (*technical.project_findings(), *human.project_findings()),
        }),),
    })
    committer.record_generation_experience(attempt_id=ATTEMPT_ID, experience=experience)
    manifest = committer._read_manifest()
    attempt = next(a for a in manifest.attempts if a.attempt_id == ATTEMPT_ID)
    return committer, experience, manifest, attempt


def test_abandon_preserves_mixed_diagnosis_paid_state_and_exact_replay(tmp_path):
    committer, experience, manifest, before = _fetched_mixed_failure(tmp_path)
    state = before.video_generation_state
    arguments = dict(attempt_id=ATTEMPT_ID, expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash, actor=ACTOR,
        reason="Explicitly discard the failed output after evidence repair was exhausted.")
    with pytest.raises(AiVideoError, match="complete known quality failure"):
        committer.reject_video_generation(**{k: v for k, v in arguments.items() if k != "reason"})
    closed = committer.abandon_video_generation(**arguments)
    after = next(a for a in closed.attempts if a.attempt_id == ATTEMPT_ID)
    receipt = committer._reopen_generation_quality_rejection(after.video_generation_state.quality_rejection)
    assert after.status is StateCommitStatus.FAILED
    assert after.paid_provider_state == before.paid_provider_state
    assert closed.active_paid_provider_budget == manifest.active_paid_provider_budget
    assert after.video_generation_state.generation_experiences == state.generation_experiences
    assert after.video_generation_state.fetch_receipt == state.fetch_receipt
    assert receipt.diagnosis.failure_classes == ("EVIDENCE_GAP", "QUALITY_FAILURE")
    assert receipt.unresolved_requirements == ("duration",)
    assert not receipt.diagnosis.all_required_observed_pass
    assert receipt.schema_version == "generation-quality-rejection/2"
    assert load_production_project(tmp_path / "project.yaml").manifest == closed
    assert committer.abandon_video_generation(**arguments) == closed
    assert record_attempt_evaluation(committer=committer, attempt_id=ATTEMPT_ID) == experience
    with pytest.raises(AiVideoError, match="replay"):
        committer.abandon_video_generation(**{**arguments, "reason": "different reason"})
    with pytest.raises(AiVideoError, match="replay"):
        committer.reject_video_generation(**{k: v for k, v in arguments.items() if k != "reason"})


@pytest.mark.parametrize("verdict", ["PASS", "FAIL", "NOT_EVALUATED"])
def test_abandon_requires_both_known_failure_and_unresolved_evidence(tmp_path, verdict):
    committer, _, manifest, attempt = _fetched_experience(tmp_path, verdict=verdict)
    with pytest.raises(AiVideoError, match="quality failure with unresolved evidence"):
        committer.abandon_video_generation(attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
            actor=ACTOR, reason="Explicit abandonment")
    assert committer._read_manifest() == manifest


def test_abandoned_result_reaches_router_without_erasing_gap_or_authorizing_submit(tmp_path):
    from ai_video.production.generation_decision import DecisionInputs, DecisionPolicy
    from ai_video.production.generation_diagnosis import Intervention
    from ai_video.production.shot_router import VideoGenerationResolver

    committer, experience, manifest, attempt = _fetched_mixed_failure(tmp_path)
    state = attempt.video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    history = committer.read_generation_experiences()
    evidence = experience.evidence[-1]
    inputs = DecisionInputs.model_validate({**binding.inputs.model_dump(mode="python"),
        "policy": DecisionPolicy(), "evidence": tuple(e for x in history for e in x.evidence),
        "experiences": history, "latest_attempt_hash": evidence.evidence_hash,
        "historical_recipes": (experience.candidate,),
        "baseline_request": binding.compiled_request.activation_scope.request,
    })
    args = dict(projection=binding.projection, context=binding.context,
                policy=binding.policy, lifecycle=binding.lifecycle)
    router = VideoGenerationResolver()
    assert router.resolve_requirement(**args, inputs=inputs).disposition == "EVIDENCE_GAP"
    closed = committer.abandon_video_generation(attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR, reason="Same-bytes evidence repair exhausted; preserve failure and unknown proof.")
    after = next(a for a in closed.attempts if a.attempt_id == ATTEMPT_ID)
    receipt = committer._reopen_generation_quality_rejection(after.video_generation_state.quality_rejection)
    inputs = inputs.model_copy(update={"abandoned_result": receipt})
    result = router.resolve_requirement(**args, inputs=inputs)
    assert result.disposition == "REASSESS_FEASIBILITY"
    assert result.diagnosis.failure_classes == ("EVIDENCE_GAP", "QUALITY_FAILURE")
    proposal = Intervention(intervention_id="repair-after-abandonment", candidate_id="selected",
        purpose="resample", disposition="GENERATE_ONCE", closes=("duration",),
        support=(evidence.evidence_hash,), changed_variables=("seed",), held_constants=(),
        uncontrolled_variables=(), regression_risks=("all source requirements need new proof",),
        hypothesis="One bounded new sample may repair the rejected duration.", confidence_basis="observed failure",
        improvement_prediction="duration meets requirement", falsification_prediction="duration still fails",
        insufficient_evidence_condition="new exact result remains unobservable", resample_limit=1)
    inputs = inputs.model_copy(update={"interventions": (proposal,)})
    result = router.resolve_requirement(**args, inputs=inputs)
    assert result.disposition == "GENERATE_ONCE"
    assert not result.diagnosis.all_required_observed_pass
    assert "duration" in result.revalidate_requirements
    loaded = load_production_project(tmp_path / "project.yaml")
    # A pure decision is not terminal authority: execution requires the real pointer.
    guarded = binding.model_copy(update={"inputs": inputs})
    guarded.validate_current_project(loaded)
    unclosed = loaded.model_copy(update={"manifest": manifest})
    with pytest.raises(ValueError, match="canonical terminal authority"):
        guarded.validate_current_project(unclosed)
    for field in ("artifact_sha256", "request_fingerprint", "evidence_hash", "experience_content_hash"):
        values = {name: getattr(receipt, name) for name in type(receipt).model_fields
                  if name != "content_hash"}
        values[field] = "a" * 64
        if field == "evidence_hash":
            values["diagnosis"] = receipt.diagnosis.model_copy(update={"evidence_hashes": ("a" * 64,)})
        forged = GenerationQualityRejectionReceipt.create(**values)
        with pytest.raises(ValueError, match="exact latest evidence"):
            router.resolve_requirement(**args, inputs=inputs.model_copy(update={"abandoned_result": forged}))
    assert committer._read_manifest() == closed


def test_abandoned_result_real_feedback_binding_start_roundtrip(tmp_path):
    from ai_video.production.generation_decision import DecisionPolicy
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
    from ai_video.production._video_project_reader import load_generation_execution_binding
    from production_generation_execution_factory import NativeFixtureVideoProvider

    committer, experience, manifest, attempt = _fetched_mixed_failure(tmp_path)
    state = attempt.video_generation_state
    template = committer._reopen_generation_execution_binding(state.execution_binding)
    committer.abandon_video_generation(attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR, reason="Explicit proof remains unobservable after same-bytes review.")
    candidate = experience.candidate
    provider = NativeFixtureVideoProvider(capabilities=candidate.capabilities, artifact_bytes=b"unused",
        compiler_id=candidate.compiler_contract.compiler_id,
        compiler_version=candidate.compiler_contract.compiler_version,
        native_prompt_text=template.compiled_request.activation_scope.request.prompt_text)

    def context(loaded):
        return dict(projection=template.projection, context=template.context, policy=template.policy,
            lifecycle=template.lifecycle.model_copy(update={
                "generation_id": "after-abandonment", "output_asset_id": "after-abandonment-video",
                "base_project": loaded.manifest.active_project,
                "base_registry": loaded.manifest.active_registry,
                "base_dependency_graph": loaded.manifest.active_dependency_graph,
            }))

    caller = GenerationFeedbackOrchestrator.for_project(committer=committer,
        targets=(RegisteredGenerationTarget(provider, candidate.provider_profile,
            candidate.compiler_contract, candidate.output_requirement),),
        context_loader=context, policy=DecisionPolicy())
    limits = template.inputs.limits.model_copy(update={"allowed_remote_candidates": tuple(
            f"{candidate.capabilities.provider_name}/{variant.capability_id}"
            for variant in candidate.capabilities.variants)})
    assert caller.prepare(limits=limits).decision.disposition == "BLOCKED_EXECUTION"
    prepared = caller.start(committer=committer, attempt_id="after-abandonment",
                            limits=limits.model_copy(update={"paid_submit_ceiling": 2}))
    assert prepared.decision.disposition == "GENERATE_ONCE", prepared.decision
    assert prepared.execution_binding is not None, prepared.compilation
    assert prepared.inputs.abandoned_result.attempt_id == ATTEMPT_ID
    assert prepared.inputs.limits.paid_submits_used == 1
    assert prepared.inputs.experiences == committer.read_generation_experiences()
    loaded = load_production_project(tmp_path / "project.yaml")
    new_attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == "after-abandonment")
    reopened = load_generation_execution_binding(tmp_path, new_attempt.video_generation_state.execution_binding)
    assert reopened == prepared.execution_binding
    reopened.validate_current_project(loaded)
    assert new_attempt.paid_provider_state is None
    assert provider.call_counts.submit == provider.call_counts.status == provider.call_counts.fetch == 0


def test_closes_remote_fetched_quality_failure_without_paid_mutation_and_replays(tmp_path):
    committer, experience, manifest, before = _fetched_experience(tmp_path)
    state = before.video_generation_state
    assert state is not None
    paid_before = before.paid_provider_state.model_dump(mode="json")
    fetch_before = state.fetch_receipt
    revision = manifest.manifest_revision
    assert before.paid_provider_state.phase is PaidProviderAttemptPhase.ACCEPTED
    assert before.paid_provider_state.reservation_id == "p8-video-reservation-1"

    closed = committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    attempt = next(item for item in closed.attempts if item.attempt_id == ATTEMPT_ID)
    state = attempt.video_generation_state
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.error_code == ErrorCode.VIDEO_QUALITY_REJECTED.value
    assert state.phase is VideoAttemptPhase.VALIDATE
    assert state.quality_rejection is not None
    assert attempt.paid_provider_state.model_dump(mode="json") == paid_before
    assert state.fetch_receipt == fetch_before
    assert state.quality_rejection.experience_content_hash == state.generation_experiences[-1].content_hash

    # Standard loading still remeasures the retained remote artifact.
    load_production_project(tmp_path / "project.yaml")
    replay = ProductionStateCommitter(tmp_path).reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    assert replay.manifest_revision == closed.manifest_revision
    assert record_attempt_evaluation(
        committer=ProductionStateCommitter(tmp_path), attempt_id=ATTEMPT_ID
    ) == experience
    diagnosis = asyncio.run(review_generation_attempt(
        committer=ProductionStateCommitter(tmp_path), attempt_id=ATTEMPT_ID,
        session=None, adjudicate=None,
    ))
    assert diagnosis.failure_classes == ("QUALITY_FAILURE",)


@pytest.mark.parametrize("verdict", ["PASS", "NOT_EVALUATED"])
def test_refuses_non_quality_or_incomplete_evaluation(tmp_path, verdict):
    committer, _, manifest, attempt = _fetched_experience(tmp_path, verdict=verdict)
    state = attempt.video_generation_state
    with pytest.raises(AiVideoError, match="complete known quality failure"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )
    assert committer._read_manifest().manifest_revision == manifest.manifest_revision


def test_closed_rejection_rejects_stale_or_different_replay_and_tampered_media(tmp_path):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    closed = committer._read_manifest()
    closed_state = next(a for a in closed.attempts if a.attempt_id == ATTEMPT_ID).video_generation_state
    with pytest.raises(AiVideoError, match="replay differs"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=closed.manifest_revision,
            experience_content_hash=closed_state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )
    with pytest.raises(AiVideoError, match="replay differs"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=closed_state.generation_experiences[-1].content_hash,
            actor=ActorIdentity(actor_id="different", actor_kind="codex"),
        )
    (tmp_path / closed_state.fetch_receipt.artifact_path).write_bytes(b"tampered")
    with pytest.raises(AiVideoError):
        ProductionStateCommitter(tmp_path).reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=closed_state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )


def test_standard_loader_rejects_quality_error_without_immutable_receipt(tmp_path):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    invalid_attempt = attempt.model_copy(update={
        "status": StateCommitStatus.FAILED,
        "error_code": ErrorCode.VIDEO_QUALITY_REJECTED.value,
        "video_generation_state": state.model_copy(update={"quality_rejection": None}),
    })
    invalid_manifest = manifest.model_copy(update={
        "attempts": tuple(
            invalid_attempt if item.attempt_id == ATTEMPT_ID else item
            for item in manifest.attempts
        ),
    })
    (tmp_path / "state/manifest.json").write_bytes(_canonical_json_bytes(invalid_manifest))
    with pytest.raises(AiVideoError, match="Could not load production state"):
        load_production_project(tmp_path / "project.yaml")


def test_closed_quality_attempt_refuses_direct_new_feedback_without_writes(tmp_path):
    committer, experience, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    source = experience.evaluation_sources[0].model_copy(update={
        "observations": (GenerationObservation(
            requirement_id=experience.candidate.recipe.expressions[0].requirement_id,
            verdict="FAIL",
            observation="A later evaluator cannot alter a closed quality decision.",
        ),),
    })
    changed = experience.model_copy(update={
        "evidence": (experience.evidence[0].model_copy(
            update={"findings": source.project_findings()}
        ),),
        "evaluation_sources": (source,),
    })
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "state").rglob("*") if path.is_file()
    }
    with pytest.raises(AiVideoError, match="Closed quality rejection"):
        committer.record_generation_experience(
            attempt_id=ATTEMPT_ID, experience=changed
        )
    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "state").rglob("*") if path.is_file()
    }
    assert after == before


def test_refuses_component_qa_authority_before_rejection_write(tmp_path, monkeypatch):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    import ai_video.production.production_strategy_reader as strategy_reader

    monkeypatch.setattr(
        strategy_reader,
        "selected_shot_generation_acceptance",
        lambda *_: object(),
    )
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "state").rglob("*") if path.is_file()
    }
    with pytest.raises(AiVideoError, match="component QA authority"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )
    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "state").rglob("*") if path.is_file()
    }
    assert after == before


@pytest.mark.parametrize("field", [
    "qa_policy",
    "attempt_id",
])
def test_replay_refuses_semantically_forged_quality_receipt(field, tmp_path):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    closed = committer._read_manifest()
    closed_attempt = next(item for item in closed.attempts if item.attempt_id == ATTEMPT_ID)
    closed_state = closed_attempt.video_generation_state
    receipt = committer._reopen_generation_quality_rejection(closed_state.quality_rejection)
    values = receipt.model_dump(mode="python")
    values.pop("content_hash")
    values.update(actor=receipt.actor, diagnosis=receipt.diagnosis, qa_policy=receipt.qa_policy)
    if field == "qa_policy":
        values[field] = receipt.qa_policy.model_copy(update={
            "content_hash": "f" * 64,
            "path": receipt.qa_policy.path.with_name(f"policy.{'f' * 64}.json"),
            "file_sha256": "f" * 64,
        })
    else:
        values[field] = "forged-other-attempt"
    forged = GenerationQualityRejectionReceipt.create(**values)
    payload = _canonical_json_bytes(forged)
    path = tmp_path / "state/video-generation/rejections" / f"{forged.content_hash}.json"
    path.write_bytes(payload)
    pointer = GenerationQualityRejectionReceiptPointer(
        path=path.relative_to(tmp_path),
        content_hash=forged.content_hash,
        attempt_id=(
            forged.attempt_id if field == "attempt_id"
            else closed_state.quality_rejection.attempt_id
        ),
        request_fingerprint=closed_state.request.request_input_hash,
        artifact_sha256=closed_state.fetch_receipt.artifact_sha256,
        experience_content_hash=closed_state.generation_experiences[-1].content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    forged_state = closed_state.model_copy(update={"quality_rejection": pointer})
    forged_attempt = closed_attempt.model_copy(
        update={"video_generation_state": forged_state}
    )
    forged_manifest = closed.model_copy(update={
        "attempts": tuple(
            forged_attempt if item.attempt_id == ATTEMPT_ID else item
            for item in closed.attempts
        ),
    })
    (tmp_path / "state/manifest.json").write_bytes(_canonical_json_bytes(forged_manifest))
    with pytest.raises(AiVideoError):
        ProductionStateCommitter(tmp_path).reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )


def test_standard_reader_rejects_resealed_unauthorized_evaluator(tmp_path):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    closed = committer._read_manifest()
    closed_attempt = next(item for item in closed.attempts if item.attempt_id == ATTEMPT_ID)
    closed_state = closed_attempt.video_generation_state
    experience = committer._reopen_generation_experience(
        closed_state.generation_experiences[-1]
    )
    source = experience.evaluation_sources[0].model_copy(update={
        "evaluator": ToolIdentity(name="not-selected-by-qa", version="1"),
    })
    forged_experience = experience.model_copy(update={
        "evidence": (experience.evidence[0].model_copy(
            update={"findings": source.project_findings()}
        ),),
        "evaluation_sources": (source,),
    })
    experience_hash = canonical_sha256(forged_experience.model_dump(mode="json"))
    experience_payload = _canonical_json_bytes(forged_experience)
    experience_path = tmp_path / "state/video-generation/experience" / f"{experience_hash}.json"
    experience_path.write_bytes(experience_payload)
    experience_pointer = GenerationExperienceReceiptPointer(
        path=experience_path.relative_to(tmp_path),
        content_hash=experience_hash,
        request_fingerprint=closed_state.request.request_input_hash,
        file_sha256=hashlib.sha256(experience_payload).hexdigest(),
    )
    old_receipt = committer._reopen_generation_quality_rejection(
        closed_state.quality_rejection
    )
    values = old_receipt.model_dump(mode="python")
    values.pop("content_hash")
    values.update(
        actor=old_receipt.actor,
        qa_policy=old_receipt.qa_policy,
        diagnosis=diagnose_exact_result(
            forged_experience.evidence[0], forged_experience.evidence,
            forged_experience.candidate.recipe,
        ),
        experience_content_hash=experience_hash,
        evidence_hash=forged_experience.evidence[0].evidence_hash,
    )
    forged_receipt = GenerationQualityRejectionReceipt.create(**values)
    receipt_payload = _canonical_json_bytes(forged_receipt)
    receipt_path = tmp_path / "state/video-generation/rejections" / f"{forged_receipt.content_hash}.json"
    receipt_path.write_bytes(receipt_payload)
    receipt_pointer = GenerationQualityRejectionReceiptPointer(
        path=receipt_path.relative_to(tmp_path),
        content_hash=forged_receipt.content_hash,
        attempt_id=closed_state.quality_rejection.attempt_id,
        request_fingerprint=closed_state.request.request_input_hash,
        artifact_sha256=closed_state.fetch_receipt.artifact_sha256,
        experience_content_hash=experience_hash,
        file_sha256=hashlib.sha256(receipt_payload).hexdigest(),
    )
    forged_attempt = closed_attempt.model_copy(update={
        "video_generation_state": closed_state.model_copy(update={
            "generation_experiences": (experience_pointer,),
            "quality_rejection": receipt_pointer,
        }),
    })
    forged_manifest = closed.model_copy(update={
        "attempts": tuple(
            forged_attempt if item.attempt_id == ATTEMPT_ID else item
            for item in closed.attempts
        ),
    })
    (tmp_path / "state/manifest.json").write_bytes(_canonical_json_bytes(forged_manifest))
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_later_qa_selection_does_not_invalidate_closed_rejection_replay(tmp_path):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    loaded = load_production_project(tmp_path / "project.yaml")
    old_policy = loaded.qa_policy
    changed_policy = seal_artifact(old_policy.model_copy(update={
        "revision": old_policy.revision + 1,
        "policy_version": old_policy.policy_version + "-later",
        "creation_receipt_id": old_policy.creation_receipt_id + "-later",
        "content_hash": "0" * 64,
    }))
    committer.activate_qa_policy(
        changed_policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="later-qa-policy",
    )
    replay = ProductionStateCommitter(tmp_path).reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    assert replay.active_qa_policy.content_hash == changed_policy.content_hash


@pytest.mark.parametrize(
    "error_code",
    [ErrorCode.VIDEO_PROVIDER_FAILED, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN],
)
def test_refuses_provider_failure_and_unknown_outcomes(error_code, tmp_path):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.record_video_provider_failure(
        attempt_id=ATTEMPT_ID,
        error_code=error_code,
        message="Fixture Provider terminal outcome.",
    )
    with pytest.raises(AiVideoError, match="requires a running fetched validate attempt"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision + 1,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )


def test_closed_quality_attempt_allows_real_changed_graph_transaction(tmp_path):
    committer, experience, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    loaded = load_production_project(tmp_path / "project.yaml")
    request = committer._reopen_video_request(state.request)
    inputs = VideoPreGenerationDependencyInputs(
        project=loaded,
        target_shot_id=request.activation_scope.request.target_shot_id,
        target_asset_role=request.activation_scope.request.target_asset_role,
        requirement_hash="1" * 64,
        planning_request_hash="2" * 64,
        verified_projection_hash="3" * 64,
    )
    graph = build_video_pre_generation_dependency_graph(inputs)
    states = resolve_dependency_state(
        graph, build_video_pre_generation_applied_evidence(inputs)
    ).states
    assert graph.content_hash != loaded.manifest.active_dependency_graph.content_hash
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    base = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=loaded.project,
        registry=loaded.registry,
        attempt_id="quality-rejection-graph-transition",
    )
    graph_payload = _canonical_json_bytes(graph)
    request_commit = replace(
        base,
        dependency_graph_transition=transition,
        artifacts=tuple(sorted(
            (*base.artifacts, PreparedArtifact(
                transition.candidate_dependency_graph.path,
                graph_payload,
                hashlib.sha256(graph_payload).hexdigest(),
            )),
            key=lambda artifact: artifact.relative_path.as_posix(),
        )),
    )
    committed = committer.commit(request_commit)
    assert committed.active_dependency_graph == transition.candidate_dependency_graph
    replay = ProductionStateCommitter(tmp_path).reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    assert replay.active_dependency_graph == transition.candidate_dependency_graph
    assert record_attempt_evaluation(
        committer=ProductionStateCommitter(tmp_path), attempt_id=ATTEMPT_ID
    ) == experience


def test_manifest_publication_failure_keeps_rejection_orphan_for_exact_retry(tmp_path, monkeypatch):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    original = committer._write_manifest_atomic

    def fail_manifest(*args, **kwargs):
        raise OSError("injected rejection publication failure")

    monkeypatch.setattr(committer, "_write_manifest_atomic", fail_manifest)
    with pytest.raises(OSError, match="publication failure"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )
    assert committer._read_manifest() == manifest
    assert list((tmp_path / "state/video-generation/rejections").glob("*.json"))
    monkeypatch.setattr(committer, "_write_manifest_atomic", original)
    closed = committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    assert next(item for item in closed.attempts if item.attempt_id == ATTEMPT_ID).video_generation_state.quality_rejection


def test_post_publication_failure_replays_exact_rejection_without_duplicate_write(tmp_path, monkeypatch):
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    original = committer._write_manifest_atomic

    def publish_then_fail(next_manifest):
        original(next_manifest)
        raise OSError("injected post-publication failure")

    monkeypatch.setattr(committer, "_write_manifest_atomic", publish_then_fail)
    with pytest.raises(OSError, match="post-publication failure"):
        committer.reject_video_generation(
            attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
        )
    closed = committer._read_manifest()
    monkeypatch.setattr(committer, "_write_manifest_atomic", original)
    assert committer.reject_video_generation(
        attempt_id=ATTEMPT_ID,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    ) == closed
