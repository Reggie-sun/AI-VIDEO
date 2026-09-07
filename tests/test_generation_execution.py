"""Decision-bound generation persistence without Provider effects."""

from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError
from ai_video.production._video_project_reader import (
    load_generation_execution_binding,
)
from ai_video.production.generation_diagnosis import AttemptEvidence
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator,
    RegisteredGenerationTarget,
)
from ai_video.production.project import load_production_project
from ai_video.production.video_generation import VideoGenerationService
from test_production_local_video_state import _runtime


def test_record_attempt_after_restart_uses_durable_binding_without_provider(tmp_path):
    from ai_video.production.generation_feedback import record_attempt_evaluation

    _, provider, request, binding, committer = _runtime(tmp_path)
    VideoGenerationService(committer=committer, provider=provider).start(
        attempt_id="restart-feedback", request=request, execution_binding=binding)
    from ai_video.production.state_commit import ProductionStateCommitter

    restarted = ProductionStateCommitter(tmp_path)
    record_attempt_evaluation(committer=restarted, attempt_id="restart-feedback")
    experience = restarted.read_generation_experiences()[0]
    assert experience.evidence[0].outcome == "not_submitted"
    assert experience.evidence[0].request_hash == request.request_input_hash
    revision = restarted._read_manifest().manifest_revision
    record_attempt_evaluation(committer=restarted, attempt_id="restart-feedback")
    assert restarted._read_manifest().manifest_revision == revision
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 0


def test_real_feedback_roundtrip_generates_one_controlled_repair_then_stops(tmp_path):
    """A real committer and scripted local transport, with injected Gate FAILs."""
    import hashlib
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
    from test_production_generated_video_e2e import FIXTURE

    _, provider, _, template, committer = _runtime(tmp_path)
    candidate = template.inputs.candidates[0]
    sequence = [0]

    def context(loaded):
        return {
            "projection": template.projection, "context": template.context,
            "policy": template.policy, "acceptance": candidate.recipe.acceptance_policy,
            "lifecycle": template.lifecycle.model_copy(update={
                "generation_id": f"feedback-roundtrip-{sequence[0]}",
                "output_asset_id": f"feedback-roundtrip-video-{sequence[0]}",
                "base_project": loaded.manifest.active_project,
                "base_registry": loaded.manifest.active_registry,
                "base_dependency_graph": loaded.manifest.active_dependency_graph,
            }),
        }

    limits = template.inputs.limits.model_copy(update={"local_batch_limit": 3})
    caller = GenerationFeedbackOrchestrator.for_project(
        committer=committer, targets=(RegisteredGenerationTarget(provider,
            candidate.provider_profile, candidate.compiler_contract, candidate.output_requirement),),
        context_loader=context, policy=template.inputs.policy)
    previous_seed = None
    for number in range(2):
        sequence[0] = number
        attempt_id = f"feedback-attempt-{number}"
        prepared = caller.start(committer=committer, attempt_id=attempt_id, limits=limits)
        assert prepared.execution_binding is not None, prepared
        if number:
            # Abandon one prepared request. It must neither consume a sample
            # nor turn the previous FAIL into a fresh first-attempt decision.
            caller.record_evaluation(committer=committer, prepared=prepared,
                attempt_id=attempt_id, outcome="not_submitted")
            sequence[0] = 10 + number
            attempt_id += "-executed"
            prepared = caller.start(committer=committer, attempt_id=attempt_id, limits=limits)
            assert prepared.execution_binding is not None, prepared
            assert prepared.decision.intervention.purpose == "resample"
            assert prepared.decision.intervention.changed_variables == ("seed",)
            assert prepared.resolved_request.effective_seed == previous_seed + 1
        service = VideoGenerationService(committer=committer, provider=provider)
        service.submit_local_once(attempt_id=attempt_id)
        service.refresh_local_once(attempt_id=attempt_id)
        service.fetch_local_once(attempt_id=attempt_id)
        qa_policy = load_production_project(tmp_path / "project.yaml").qa_policy
        artifact_sha256 = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        source = GenerationEvaluationSource(
            request_hash=prepared.resolved_request.request_input_hash,
            artifact_sha256=artifact_sha256, rubric_hash=prepared.inputs.rubric_hash,
            qa_policy_content_hash=qa_policy.content_hash,
            evaluator=qa_policy.semantic_authorities[0], proof="technical",
            observations=(GenerationObservation(requirement_id="duration", verdict="FAIL",
                observation="Injected evaluator failure for offline orchestration regression"),))
        if number == 0:
            with pytest.raises(AiVideoError, match="evaluation source"):
                caller.record_evaluation(committer=committer, prepared=prepared, attempt_id=attempt_id,
                    outcome="media", artifact_sha256=artifact_sha256,
                    evaluation_sources=(source.model_copy(update={"artifact_sha256": "f" * 64}),))
            assert committer.read_generation_experiences() == ()
        caller.record_evaluation(committer=committer, prepared=prepared, attempt_id=attempt_id,
            outcome="media", artifact_sha256=artifact_sha256, evaluation_sources=(source,))
        previous_seed = prepared.resolved_request.effective_seed
    sequence[0] = 2
    next_decision = caller.prepare(limits=limits)
    assert next_decision.decision.disposition == "REASSESS_FEASIBILITY"
    assert next_decision.execution_binding is None
    assert next_decision.inputs.limits.local_total_used == 2
    assert len(committer.read_generation_experiences()) == 3
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 2


def test_real_project_persists_and_reopens_decision_bound_feedback(
    tmp_path,
) -> None:
    _, provider, request, binding, committer = _runtime(tmp_path)
    service = VideoGenerationService(committer=committer, provider=provider)

    service.start(
        attempt_id="decision-bound-attempt",
        request=request,
        execution_binding=binding,
    )
    state = committer._read_manifest().attempts[-1].video_generation_state
    assert state is not None and state.execution_binding is not None
    assert (
        load_generation_execution_binding(tmp_path, state.execution_binding)
        == binding
    )

    candidate = binding.inputs.candidates[0]
    evidence = AttemptEvidence(
        task_id=binding.inputs.limits.task_id,
        shot_id=binding.context.target_shot_id,
        attempt_id="decision-bound-attempt",
        recipe_scope_hash=candidate.scope_hash,
        facts_hash=binding.inputs.facts_hash,
        rubric_hash=candidate.recipe.rubric_hash,
        request_hash=request.request_input_hash,
        outcome="not_submitted",
    )
    committer.record_generation_experience(
        attempt_id="decision-bound-attempt",
        experience=GenerationExperience(
            projection=binding.projection,
            candidate=candidate,
            evidence=(evidence,),
        ),
    )

    reopened = load_production_project(tmp_path / "project.yaml")
    assert len(reopened.manifest.attempts[-1].video_generation_state.generation_experiences) == 1
    assert committer.read_generation_experiences()[0].evidence == (evidence,)
    next_generation = GenerationFeedbackOrchestrator.for_project(
        committer=committer,
        targets=(
            RegisteredGenerationTarget(
                provider=provider,
                profile=candidate.provider_profile,
                compiler_contract=candidate.compiler_contract,
                output_requirement=candidate.output_requirement,
            ),
        ),
        context_loader=lambda _project: {
            "projection": binding.projection,
            "context": binding.context,
            "policy": binding.policy,
            "lifecycle": binding.lifecycle.model_copy(
                update={"generation_id": "decision-bound-next"}
            ),
            "acceptance": candidate.recipe.acceptance_policy,
        },
        policy=binding.inputs.policy,
    ).prepare(limits=binding.inputs.limits)
    assert next_generation.inputs.latest_attempt_hash == evidence.evidence_hash
    assert next_generation.inputs.baseline_request == request.activation_scope.request
    assert next_generation.inputs.limits.local_total_used == 0
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 0


def test_decision_binding_rejects_stale_current_shot_before_request_write(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, provider, request, binding, committer = _runtime(tmp_path)
    stale_shot = inputs.project.shots[0].model_copy(update={"revision": 999})
    stale_project = inputs.project.model_copy(update={"shots": (stale_shot,)})
    monkeypatch.setattr(
        committer,
        "_load_production_project",
        lambda _path: stale_project,
    )

    with pytest.raises(AiVideoError, match="lineage"):
        VideoGenerationService(committer=committer, provider=provider).start(
            attempt_id="stale-decision-bound-attempt",
            request=request,
            execution_binding=binding,
        )

    assert all(
        attempt.operation != "video_generation"
        for attempt in committer._read_manifest().attempts
    )
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 0
