"""Exercise no-regression at the public Router and execution binding seams."""

import pytest

from ai_video.production.final_output_contracts import KnownRequirementViolation
from ai_video.production.generation_diagnosis import diagnose_attempt, intervention_prediction_outcome
from test_production_generation_decision import (
    setup_decision, recipe_with_rules, decide, evidence, intervention, compile_decision,
)


def setup_full_requirements():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    timing = candidate.recipe.expressions[0]
    natural = timing.model_copy(update={"requirement_id": "natural", "proof": "human",
        "observable": "Natural performance throughout the whole shot"})
    recipe = recipe_with_rules(candidate.recipe, (timing, natural))
    candidate = candidate.model_copy(update={"recipe": recipe})
    setup["inputs"] = setup["inputs"].model_copy(update={
        "candidates": (candidate,), "rubric_hash": recipe.rubric_hash})
    baseline = compile_decision(decide(setup), setup).request
    latest = evidence(setup, verdict="FAIL", task_id="task", request_hash=baseline.request_input_hash)
    latest = latest.model_copy(update={"findings": (latest.findings[0],
        latest.findings[0].model_copy(update={"requirement_id": "natural", "proof": "human", "verdict": "PASS"}))})
    return setup, baseline, latest


def test_router_refuses_omitted_protection_and_known_global_regression():
    setup, baseline, latest = setup_full_requirements()
    proposed = intervention(latest, protected_requirements=("natural",))
    for candidate in (proposed.model_copy(update={"protected_requirements": ()}),
                      proposed.model_copy(update={"known_requirement_violations": (
                          KnownRequirementViolation(requirement_id="natural", evidence_sha256="c" * 64,
                              reason="Known global regression despite timing improvement"),)})):
        result = decide(setup, evidence=(latest,), latest_attempt_hash=latest.evidence_hash,
            interventions=(candidate,), baseline_request=baseline)
        assert result.disposition == "REASSESS_FEASIBILITY"
        assert result.routing is None


@pytest.mark.parametrize("natural,timing,expected", [
    ("FAIL", "PASS", "refuted"), ("NOT_EVALUATED", "PASS", "undetermined"),
    (None, "PASS", "undetermined"), ("PASS", "FAIL", "refuted"), ("PASS", "PASS", "supported"),
])
def test_prediction_needs_entire_requirement_set(natural, timing, expected):
    setup, _, latest = setup_full_requirements()
    proposed = intervention(latest)  # Caller omission cannot conceal a failure.
    findings = (latest.findings[0].model_copy(update={"verdict": timing}),)
    if natural is not None:
        findings += (latest.findings[1].model_copy(update={"verdict": natural}),)
    result = latest.model_copy(update={"artifact_sha256": "e" * 64, "findings": findings})
    diagnosis = diagnose_attempt(result, setup["inputs"].candidates[0].recipe)
    assert intervention_prediction_outcome(proposed, diagnosis) == expected


def test_router_cannot_drop_requirement_by_replacing_baseline_rubric():
    setup, baseline, latest = setup_full_requirements()
    prior = setup["inputs"].candidates[0]
    truncated = recipe_with_rules(prior.recipe, prior.recipe.expressions[:1])
    setup["inputs"] = setup["inputs"].model_copy(update={
        "candidates": (prior.model_copy(update={"recipe": truncated}),),
        "rubric_hash": truncated.rubric_hash, "historical_recipes": (prior,)})
    result = decide(setup, evidence=(latest,), latest_attempt_hash=latest.evidence_hash,
        interventions=(intervention(latest),), baseline_request=baseline)
    assert result.disposition == "RUBRIC_OR_STAGE_ERROR"
    assert result.diagnosis.failed_requirements == ("duration",)


def test_old_decision_policy_remains_readable_but_cannot_execute(tmp_path):
    from ai_video.production.generation_decision import DecisionPolicy
    from test_generation_execution import _runtime

    _, _, _, binding, committer = _runtime(tmp_path)
    # An old sealed policy is readable. Current-effect validation does not let
    # a caller choose that policy to bypass the new execution constraint.
    old = DecisionPolicy(version="2")
    assert DecisionPolicy.model_validate_json(old.model_dump_json()) == old
    changed = binding.model_copy(update={"inputs": binding.inputs.model_copy(update={"policy": old})})
    with pytest.raises(ValueError, match="no-regression decision policy/3"):
        changed.validate_current_project(committer._load_production_project(tmp_path / "project.yaml"))


def test_real_begin_rejects_stale_goal_and_for_project_binds_current_qa(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.video_generation import VideoGenerationService
    from test_generation_execution import _runtime
    from test_production_final_output import viewing_policy

    _, provider, request, binding, committer = _runtime(tmp_path)
    loaded = committer._load_production_project(tmp_path / "project.yaml")
    goal = viewing_policy().final_output
    qa = seal_artifact(loaded.qa_policy.model_copy(update={"final_output": goal}))
    committer.activate_qa_policy(qa, expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="select-final-output-goal")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(AiVideoError, match="lineage") as failure:
        VideoGenerationService(committer=committer, provider=provider).start(
            attempt_id="wrong-goal", request=request, execution_binding=binding)
    assert "final-output goal" in str(failure.value.__cause__)
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    candidate = binding.inputs.candidates[0]
    caller = GenerationFeedbackOrchestrator.for_project(committer=committer,
        targets=(RegisteredGenerationTarget(provider, candidate.provider_profile,
            candidate.compiler_contract, candidate.output_requirement),),
        context_loader=lambda loaded: {
            "projection": binding.projection, "context": binding.context,
            "policy": binding.policy, "lifecycle": binding.lifecycle,
            "acceptance": candidate.recipe.acceptance_policy,
            "final_output_goal": None,  # A caller cannot replace canonical QA.
        }, policy=binding.inputs.policy)
    prepared = caller.start(committer=committer, attempt_id="current-goal", limits=binding.inputs.limits)
    assert prepared.execution_binding is not None
    assert all(c.final_output_goal == goal for c in prepared.inputs.candidates)
    assert committer._read_manifest().attempts[-1].video_generation_state.execution_binding is not None
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 0


def test_real_begin_reports_missing_qa_as_typed_failure(tmp_path, monkeypatch):
    from ai_video.errors import AiVideoError
    from ai_video.production.video_generation import VideoGenerationService
    from test_generation_execution import _runtime

    _, provider, request, binding, committer = _runtime(tmp_path)
    loaded = committer._load_production_project(tmp_path / "project.yaml")
    missing = loaded.model_copy(update={"qa_policy": None})
    monkeypatch.setattr(committer, "_load_production_project", lambda path: missing)
    revision = committer._read_manifest().manifest_revision
    with pytest.raises(AiVideoError, match="lineage") as failure:
        VideoGenerationService(committer=committer, provider=provider).start(
            attempt_id="missing-qa", request=request, execution_binding=binding)
    assert "current QA policy" in str(failure.value.__cause__)
    assert committer._read_manifest().manifest_revision == revision
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 0


@pytest.mark.parametrize("new_goal", [False, True])
def test_explicit_generation_goal_revision_preserves_failed_history_and_can_progress(new_goal):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    setup, baseline, latest = setup_full_requirements()
    prior = setup["inputs"].candidates[0]
    from test_production_final_output import viewing_policy
    goal = viewing_policy().final_output
    prior = prior.model_copy(update={"final_output_goal": goal})
    latest = latest.model_copy(update={"recipe_scope_hash": prior.scope_hash})
    payload = dict(prior.recipe.acceptance_policy.profile_payload)
    payload.pop("content_hash")
    payload["profile_version"] = "2"
    new_hash = canonical_sha256(payload)
    acceptance = DomainAcceptancePolicy.model_validate({
        **prior.recipe.acceptance_policy.model_dump(mode="python"),
        "profile_version": "2", "profile_content_hash": new_hash,
        "profile_payload": {**payload, "content_hash": new_hash}})
    candidate = prior.model_copy(update={"recipe": prior.recipe.model_copy(update={
        "rubric_hash": new_hash, "acceptance_policy": acceptance}),
        "final_output_goal": goal.model_copy(update={"goal_version": "2"}) if new_goal else goal})
    setup["inputs"] = setup["inputs"].model_copy(update={"candidates": (candidate,),
        "rubric_hash": new_hash, "historical_recipes": (prior,)})
    result = decide(setup, evidence=(latest,), latest_attempt_hash=latest.evidence_hash,
        baseline_request=baseline)
    if not new_goal:
        assert result.disposition == "RUBRIC_OR_STAGE_ERROR"
        return
    assert result.disposition == "GENERATE_ONCE"
    assert result.intervention is None  # A new goal is not success of the old repair.
    assert result.diagnosis.failed_requirements == ("duration",)
    assert compile_decision(result, setup).request is not None
    assert result.routing.provider_bound_request.generation_recipe.rubric_hash == new_hash
