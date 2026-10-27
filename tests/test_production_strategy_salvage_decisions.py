"""Quality-first risk comparison and design-scoped failure history."""
import hashlib

import pytest

from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.production_strategy_salvage import (
    candidate_plan_key, preferred_salvage_candidates, repeated_failure_requirements,
)
from test_production_generation_decision import setup_decision, evidence
from test_production_strategy_salvage import make_persisted_salvage_fixture


def test_removed_review_cannot_be_laundered_by_rematerialization(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.production_strategy_materialization import prepare_strategy_commit

    fixture, service, _, review, _, _ = make_persisted_salvage_fixture(tmp_path, insert_coverage=True)
    decision = service.prepare(parent_shot_id=review.parent_shot_id)
    service.materialize(decision=decision, attempt_id="first-salvage-plan")
    loaded = service._load()
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1, "production_salvage_reviews": (),
    }))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="remove-salvage-policy")
    current = service.prepare(parent_shot_id=review.parent_shot_id)
    assert current.selected is None and current.disposition == "evidence_required"
    with pytest.raises(AiVideoError, match="salvage"):
        prepare_strategy_commit(loaded=service._load(), decision=decision, attempt_id="launder-salvage")


@pytest.mark.parametrize("risk,expected", [("unknown", (0, 1)), ("high", (1,)), ("low", (0,))])
def test_edit_priority_never_precedes_quality_risk(tmp_path, risk, expected):
    _, service, _, review, _, _ = make_persisted_salvage_fixture(tmp_path)
    decision = service.prepare(parent_shot_id=review.parent_shot_id)
    edit = decision.selected
    generation = next(c for c in decision.candidates if c.new_generation_count == 1)
    plans = tuple(p.model_copy(update={"risks": p.risks.model_copy(update={
        "narrative": risk if p.plan_key == candidate_plan_key(edit) else "low",
        "identity": "low", "continuity": "low", "performance": "low", "approved_content": "low",
    })}) for p in review.candidate_plans)
    review = review.model_copy(update={"candidate_plans": plans})
    assert tuple(c.new_generation_count for c in preferred_salvage_candidates((edit, generation), review)) == expected


def test_new_recipe_success_does_not_inherit_old_recipe_permanent_veto(tmp_path):
    _, _, loaded, review, _, _ = make_persisted_salvage_fixture(tmp_path)
    setup = setup_decision()
    parent = loaded.shots[0].model_copy(update={"shot_id": setup["context"].target_shot_id})
    review = review.model_copy(update={"task_id": "task", "parent_shot_id": parent.shot_id})
    candidate = setup["inputs"].candidates[0]
    history = tuple(GenerationExperience(projection=setup["projection"], candidate=candidate,
        evidence=(evidence(setup, task_id="task", verdict="FAIL", attempt=str(n),
            request_hash=hashlib.sha256(f"request-{n}".encode()).hexdigest()),)) for n in range(3))
    assert repeated_failure_requirements(history, parent, review) == ("duration",)
    new = candidate.model_copy(update={"recipe": candidate.recipe.model_copy(update={
        "seed": candidate.recipe.seed.model_copy(update={"kind": "uncontrolled", "value": None})})})
    recovered = GenerationExperience(projection=setup["projection"], candidate=new,
        evidence=(evidence(setup, candidate=new, task_id="task", verdict="PASS", attempt="new-success",
            request_hash="f" * 64),))
    assert repeated_failure_requirements((*history, recovered), parent, review) == ()


@pytest.mark.parametrize(("frames", "rename"), [(12, False), (13, False), (61, False), (12, True), (13, True)])
def test_replan_changes_design_without_resetting_task_or_failure_history(tmp_path, frames, rename):
    _, service, loaded, review, _, _ = make_persisted_salvage_fixture(tmp_path, insert_coverage=True)
    decision = service.prepare(parent_shot_id=review.parent_shot_id)
    service.materialize(decision=decision, attempt_id="design-history")
    current = service._load()
    shot = next(s for s in current.shots if s.production_lineage.source is None)
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.production_strategy_materialization import _seconds_for_frames
    # Frame/design calculation cases start from a standard materialized Shot.
    # They do not claim that this synthetic history was an actual generation.
    shot = seal_artifact(shot.model_copy(update={"duration_policy": shot.duration_policy.model_copy(update={
        "seconds": _seconds_for_frames(frames, loaded.project.delivery_profile.fps)})}))
    visual = decision.selected.units[1]
    visual = visual.model_copy(update={"component": visual.component.model_copy(update={
        "duration_frames": frames, "shot_id": "renamed-component" if rename else shot.shot_id})})
    selected = decision.selected.model_copy(update={"units": (decision.selected.units[0], visual),
        "coverage": decision.selected.coverage.model_copy(update={
            "units": (decision.selected.units[0].component, visual.component)})})
    setup = setup_decision()
    from ai_video.planning.video_planner import VideoPlanner
    from ai_video.production.video_requirement import (
        ProviderNeutralVideoRequirement, VerifiedGenerationRequirementProjection,
    )
    requirement = ProviderNeutralVideoRequirement.create(**{
        **setup["projection"].requirement.model_dump(exclude={"requirement_hash"}),
        "target_shot": shot, "scene": next(s for s in current.scenes if s.scene_id == shot.scene_id),
        "characters": tuple(c for c in current.characters if c.character_id in shot.character_ids),
    })
    historical = VerifiedGenerationRequirementProjection.create(**{
        **setup["projection"].model_dump(exclude={"projection_hash"}),
        "requirement": requirement, "target_shot_id": shot.shot_id,
        "target_shot_revision": shot.revision, "target_shot_content_hash": shot.content_hash,
    })
    candidate = setup["inputs"].candidates[0]
    candidate = candidate.model_copy(update={"recipe": candidate.recipe.model_copy(update={
        "requirement_hash": requirement.requirement_hash})})
    setup["inputs"] = setup["inputs"].model_copy(update={
        "candidates": (candidate,), "facts_hash": VideoPlanner.generation_difficulty(historical)["facts_hash"]})
    history = tuple(GenerationExperience(projection=historical, candidate=candidate,
        evidence=(evidence(setup, task_id=review.task_id, shot_id=shot.shot_id,
            verdict="FAIL", attempt=str(n), request_hash=hashlib.sha256(f"design-{n}".encode()).hexdigest()),))
        for n in range(3))
    parent = loaded.shots[0]
    parent = parent.model_copy(update={"production_intent": parent.production_intent.model_copy(update={
        "coverage_options": (selected.coverage,)})})
    kwargs = dict(candidate=selected, fps=loaded.project.delivery_profile.fps)
    assert repeated_failure_requirements(history, parent, review, **kwargs) == ("duration",)
    unit = selected.units[1]
    revised = selected.model_copy(update={"units": (selected.units[0],
        unit.model_copy(update={"component": unit.component.model_copy(update={
            "intent": "以静止结果特写替代连续复杂动作"})}))})
    assert repeated_failure_requirements(history, parent, review, candidate=revised,
        fps=loaded.project.delivery_profile.fps) == ()
    assert len(history) == 3 and all(e.evidence[0].task_id == review.task_id for e in history)
