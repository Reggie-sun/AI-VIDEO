"""P6 temporal eligibility; fixture attestations are not real film acceptance."""
import pytest

from ai_video.production.final_output_review import adjudicate_final_output_details
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import EvidenceStrength, QaLayer, QaVerdict
from ai_video.production.production_strategy_salvage import (
    candidate_plan_key, preferred_salvage_candidates,
)
from ai_video.production.review import adjudicate_review_evidence
from test_production_review import evidence
from test_production_strategy_salvage import make_persisted_salvage_fixture


@pytest.fixture
def salvage_fixture(tmp_path):
    return make_persisted_salvage_fixture(tmp_path)


def playback_evidence(loaded, **changes):
    policy = loaded.qa_policy
    tool = policy.semantic_authorities[0]
    raw = {"contract_hash": policy.final_output.contract_hash,
           "review_request_content_hash": "a" * 64,
           "viewing_mode": "full_playback", "viewing_speed_milli": 1000,
           "audio_reviewed": True,
           "findings": [{"requirement_id": r.requirement_id, "verdict": "pass",
                         "observation": "Injected whole-scene fixture observation"}
                        for r in policy.final_output.requirements], **changes}
    item = evidence(QaLayer.SEMANTIC, EvidenceStrength.EXPLICIT_EVALUATOR,
        evaluator_identity=f"{tool.name}@{tool.version}", final_output=raw)
    return seal_artifact(item.model_copy(update={"tool_identity": tool}))


@pytest.mark.parametrize("change", [
    {"viewing_mode": "sampled_frames"}, {"viewing_speed_milli": 2000},
    {"audio_reviewed": False}, {"audio_reviewed": None},
    {"review_request_content_hash": "b" * 64}, {"findings": []},
])
def test_scene_and_transition_cannot_pass_on_stills_or_incomplete_audio(salvage_fixture, change):
    _, _, loaded, _, _, _ = salvage_fixture
    assert adjudicate_review_evidence(loaded.qa_policy, QaLayer.SEMANTIC,
        (playback_evidence(loaded, **change),), review_request_content_hash="a" * 64) is QaVerdict.NOT_EVALUATED


def test_fresh_continuous_scene_evidence_passes_eligibility_without_accepting_film(salvage_fixture):
    _, _, loaded, _, _, _ = salvage_fixture
    # The fixture's domain is not a supported final domain evaluator, so test
    # the exact final-output eligibility owner, not an invented domain PASS.
    result = adjudicate_final_output_details(loaded.qa_policy.final_output,
        (playback_evidence(loaded),), review_request_content_hash="a" * 64,
        continuous_requirement_ids=("visual",))
    assert result.verdict is QaVerdict.PASS
    assert loaded.manifest.final_acceptance_state is None


def test_scene_failure_vetoes_individually_qualified_take(salvage_fixture):
    fixture, service, loaded, _, _, _ = salvage_fixture
    assert service.prepare(parent_shot_id=fixture.parent_shot_id).selected is not None
    item = playback_evidence(loaded, findings=[
        {"requirement_id": "visual", "verdict": "fail", "observation": "Reaction has no preceding cause"},
        {"requirement_id": "dialogue", "verdict": "pass", "observation": "Words remain intact"},
    ])
    assert adjudicate_review_evidence(loaded.qa_policy, QaLayer.SEMANTIC,
        (item,), review_request_content_hash="a" * 64) is QaVerdict.FAIL


def test_trim_plus_insert_keeps_valid_frames_and_generates_only_missing_unit(tmp_path):
    fixture, service, loaded, review, _, _ = make_persisted_salvage_fixture(tmp_path, insert_coverage=True)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is not None
    assert decision.selected.new_generation_count == 1
    assert decision.selected.units[0].source is not None
    assert decision.selected.units[1].source is None
    plan = next(p for p in review.candidate_plans if p.plan_key == candidate_plan_key(decision.selected))
    assert "GENERATE_INSERT" in plan.operations
    assert service.prepare(parent_shot_id=fixture.parent_shot_id,
        include_salvage_report=True)["salvage"]["verification"] == "NOT_EVALUATED"


def test_stale_review_cannot_compose_old_materialization(salvage_fixture):
    from ai_video.errors import AiVideoError
    fixture, service, _, _, _, _ = salvage_fixture
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="salvage-materialization")
    loaded = service._load()
    review = loaded.qa_policy.production_salvage_reviews[0]
    changed = review.model_copy(update={"scene_intent": review.scene_intent + " 修订后的情绪要求"})
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1, "production_salvage_reviews": (changed,)}))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="salvage-new-review")
    with pytest.raises(AiVideoError, match="salvage"):
        service.composition(decision=decision, renderer_version="test/1")


def test_uncertain_risks_are_not_replaced_by_precise_cost_scores(salvage_fixture):
    _, service, loaded, review, _, _ = salvage_fixture
    decision = service.prepare(parent_shot_id=review.parent_shot_id)
    source = decision.selected
    # Two distinct authored candidates, equal qualification, incomparable risk.
    other = source.model_copy(update={"coverage": source.coverage.model_copy(update={"coverage_id": "alternative"})})
    plan = next(p for p in review.candidate_plans if p.plan_key == candidate_plan_key(source))
    alternative = plan.model_copy(update={"plan_key": candidate_plan_key(other),
        "risks": plan.risks.model_copy(update={"identity": "unknown"})})
    review = review.model_copy(update={"candidate_plans": (plan, alternative)})
    assert preferred_salvage_candidates((source, other), review) == (source, other)


def test_repeat_failure_counts_requests_not_duplicate_reviews(salvage_fixture):
    import hashlib
    from ai_video.production.generation_experience import GenerationExperience
    from ai_video.production.production_strategy_salvage import repeated_failure_requirements
    from test_production_generation_decision import setup_decision, evidence as generation_evidence

    _, _, loaded, review, _, _ = salvage_fixture
    setup = setup_decision()
    parent = loaded.shots[0].model_copy(update={"shot_id": setup["context"].target_shot_id})
    review = review.model_copy(update={"task_id": "task", "parent_shot_id": parent.shot_id})
    candidate = setup["inputs"].candidates[0]
    entries = tuple(generation_evidence(setup, task_id="task", verdict="FAIL", attempt=str(n),
        request_hash=hashlib.sha256(f"request-{n}".encode()).hexdigest()) for n in range(3))
    history = tuple(GenerationExperience(projection=setup["projection"], candidate=candidate,
        evidence=(entry,)) for entry in entries)
    assert repeated_failure_requirements((history[0],) * 5, parent, review) == ()
    assert repeated_failure_requirements(history, parent, review) == ("duration",)
    passed = generation_evidence(setup, task_id="task", verdict="PASS", attempt="success",
        request_hash="f" * 64)
    recovered = GenerationExperience(projection=setup["projection"], candidate=candidate, evidence=(passed,))
    assert repeated_failure_requirements((*history, recovered), parent, review) == ()


@pytest.mark.parametrize("review_change", ("modified", "deleted"))
def test_canonical_generation_and_source_use_reject_stale_salvage_lineage_before_effects(
    tmp_path, review_change,
):
    import pytest
    from types import SimpleNamespace

    from ai_video.errors import AiVideoError
    from ai_video.production.production_strategy_reader import (
        require_production_source_eligibility,
        selected_shot_generation_acceptance,
    )
    from ai_video.production.project import load_production_project

    fixture, service, _, old_review, _, _ = make_persisted_salvage_fixture(
        tmp_path, insert_coverage=True,
    )
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is not None
    assert decision.selected.new_generation_count == 1
    generated_unit = next(unit.component for unit in decision.selected.units if unit.source is None)
    service.materialize(decision=decision, attempt_id="salvage-generation-lineage")

    loaded = load_production_project(tmp_path / "project.yaml")
    active_review = loaded.qa_policy.production_salvage_reviews[0]
    assert active_review.review_hash == old_review.review_hash
    if review_change == "modified":
        changed = active_review.model_copy(update={
            "scene_intent": active_review.scene_intent + "；新增动作结果要求",
        })
        reviews = (changed,)
    else:
        reviews = ()
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1,
        "production_salvage_reviews": reviews,
    }))
    fixture.committer.activate_qa_policy(
        policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id=f"salvage-review-{review_change}",
    )
    current = load_production_project(tmp_path / "project.yaml")
    acceptance = selected_shot_generation_acceptance(current, generated_unit.shot_id)
    assert acceptance is not None
    binding = SimpleNamespace(
        context=SimpleNamespace(target_shot_id=generated_unit.shot_id),
        inputs=SimpleNamespace(
            limits=SimpleNamespace(task_id=fixture.task_id),
            candidates=(SimpleNamespace(recipe=SimpleNamespace(acceptance_policy=acceptance)),),
        ),
    )
    manifest_before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError, match="salvage"):
        fixture.committer._require_current_generation_acceptance(current, binding)
    with pytest.raises(AiVideoError, match="salvage"):
        require_production_source_eligibility(current, family_shot_id=generated_unit.shot_id)
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before
