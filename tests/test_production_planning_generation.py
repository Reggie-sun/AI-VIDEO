"""Offline generation handoff boundaries for materialized production components."""

from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production_planning import ProductionPlanningService
from ai_video.planning.production_strategy import ProductionStrategyPolicy
from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator,
    RegisteredGenerationTarget,
)
from ai_video.production.production_strategy_reader import (
    selected_shot_generation_acceptance,
)
from ai_video.production.project import load_production_project
from production_strategy_factory import make_persisted_strategy_fixture
from test_generation_feedback import NativeFixtureProvider
from test_production_generation_decision import setup_decision


def _generation_target() -> RegisteredGenerationTarget:
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    provider = NativeFixtureProvider(
        capabilities=candidate.capabilities,
        artifact_bytes=b"offline-generation-handoff",
    )
    return RegisteredGenerationTarget(
        provider,
        candidate.provider_profile,
        candidate.compiler_contract,
        candidate.output_requirement,
    )


def _limits(task_id: str) -> ExecutionLimits:
    return ExecutionLimits(
        task_id=task_id,
        generation_forbidden=False,
        paid_submit_ceiling=0,
        paid_submits_used=0,
        local_batch_limit=1,
        local_batch_used=0,
        local_total_used=0,
        local_resource_available=True,
    )


def _generation_service(fixture):
    target = _generation_target()
    return (
        ProductionPlanningService(
            committer=fixture.committer,
            targets=(target,),
            policy=ProductionStrategyPolicy(
                preference="generation", allow_generation_exploration=True,
            ),
        ),
        target,
    )


def test_only_materialized_missing_component_reaches_generation_handoff(tmp_path, monkeypatch):
    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True)
    service, target = _generation_service(fixture)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.disposition == "selected"
    assert decision.selected is not None
    assert decision.selected.new_generation_count == 1
    service.materialize(decision=decision, attempt_id="strategy-generation-materialize")

    loaded = load_production_project(tmp_path / "project.yaml")
    child = next(shot for shot in loaded.shots if shot.shot_id == fixture.child_shot_id)
    assert child.production_lineage is not None
    assert child.production_lineage.source is None
    assert not next(role for role in child.required_asset_roles if role.role == "primary_visual").asset_ids
    assert selected_shot_generation_acceptance(
        loaded, fixture.child_shot_id,
    ) == fixture.component_generation_acceptance

    observed = {}
    sentinel = object()

    class _Orchestrator:
        def prepare(self, *, limits):
            observed["limits"] = limits
            return sentinel

    def _for_project(*, committer, targets, context_loader, policy):
        observed.update(
            committer=committer,
            targets=targets,
            context_loader=context_loader,
            policy=policy,
        )
        return _Orchestrator()

    monkeypatch.setattr(
        GenerationFeedbackOrchestrator, "for_project", staticmethod(_for_project),
    )
    generation_policy = DecisionPolicy(allow_bounded_exploration=True)
    result = service.prepare_generation(
        component_shot_id=fixture.child_shot_id,
        context_loader=lambda *_: pytest.fail("handoff spy must not invoke context"),
        limits=_limits(fixture.task_id),
        generation_policy=generation_policy,
    )

    assert result is sentinel
    assert observed["committer"] is fixture.committer
    assert observed["targets"] == (target,)
    assert observed["limits"].task_id == fixture.task_id
    assert observed["policy"] == generation_policy


def test_pending_component_rejects_a_generation_task_identity_change(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True)
    service, _ = _generation_service(fixture)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="strategy-generation-materialize")

    with pytest.raises(AiVideoError) as error:
        service.prepare_generation(
            component_shot_id=fixture.child_shot_id,
            context_loader=lambda *_: pytest.fail("wrong task must stop before context"),
            limits=_limits("another-task"),
            generation_policy=DecisionPolicy(allow_bounded_exploration=True),
        )
    assert error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_filled_reuse_component_cannot_reach_generation_handoff(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="strategy-reuse-materialize")

    with pytest.raises(AiVideoError) as error:
        service.prepare_generation(
            component_shot_id=fixture.child_shot_id,
            context_loader=lambda *_: pytest.fail("filled component must not load context"),
            limits=_limits(fixture.task_id),
            generation_policy=DecisionPolicy(allow_bounded_exploration=True),
        )
    assert error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_current_generation_guard_rejects_later_audio_failure_before_any_effect(tmp_path):
    import json
    from types import SimpleNamespace
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.source_use_evidence import SourceUseEvidence

    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True, generation_audio=True)
    service, _ = _generation_service(fixture)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="generated-visual-qualified-audio")
    loaded = load_production_project(tmp_path / "project.yaml")
    binding = SimpleNamespace(context=SimpleNamespace(target_shot_id=fixture.child_shot_id),
        inputs=SimpleNamespace(limits=_limits(fixture.task_id), candidates=(SimpleNamespace(
            recipe=SimpleNamespace(acceptance_policy=fixture.component_generation_acceptance)),)))
    fixture.committer._require_current_generation_acceptance(loaded, binding)
    evidence = loaded.qa_policy.production_source_evidence[0]
    raw = json.loads(evidence.response_json)
    raw["observations"][0]["verdict"] = "FAIL"
    failed = SourceUseEvidence.model_validate({**evidence.model_dump(), "evidence_id": "later-audio-fail",
                                              "response_json": json.dumps(raw)})
    qa = seal_artifact(loaded.qa_policy.model_copy(update={"revision": loaded.qa_policy.revision + 1,
        "production_source_evidence": (*loaded.qa_policy.production_source_evidence, failed)}))
    fixture.committer.activate_qa_policy(qa,
        expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="audio-review")
    current = load_production_project(tmp_path / "project.yaml")
    before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError, match="not currently qualified"):
        fixture.committer._require_current_generation_acceptance(current, binding)
    assert (tmp_path / "state/manifest.json").read_bytes() == before
