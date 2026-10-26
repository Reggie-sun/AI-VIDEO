"""Same-rubric authored changes retain evidence and remain bounded at the Router."""
import pytest

from ai_video.planning.video_planner import VideoPlanner
from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement, VerifiedGenerationRequirementProjection
from test_production_generation_decision import setup_decision, decide, evidence, compile_decision
from test_production_paid_submit_quota import _goal


def case(*, verdict="NOT_EVALUATED", outcome="media"):
    s = setup_decision(remote=True, reference_hash="a" * 64, seed_supported=False)
    candidate = s["inputs"].candidates[0]
    from test_production_shot_router import _capabilities
    caps = _capabilities(candidate.capabilities.variants[0].model_copy(
        update={"production_qualification": "UNQUALIFIED"}))
    s["policy"] = s["policy"].model_copy(update={"execution_purpose": "qualification"})
    old = candidate.model_copy(update={"final_output_goal": _goal("1"), "capabilities": caps})
    limits = s["inputs"].limits.model_copy(update={"allowed_remote_candidates": (old.candidate_id,)})
    s["inputs"] = s["inputs"].model_copy(update={"candidates": (old,), "limits": limits})
    baseline = compile_decision(decide(s), s).request
    e = evidence(s, candidate=old, verdict=verdict, outcome=outcome, task_id="task",
                 request_hash=baseline.request_input_hash)
    experience = GenerationExperience(projection=s["projection"], candidate=old, evidence=(e,))
    r = s["projection"].requirement
    intent = r.generation_intent.model_copy(update={"subject_action":
        r.generation_intent.subject_action.model_copy(update={"progression": "Set down, release, withdraw."})})
    requirement = ProviderNeutralVideoRequirement.create(**{
        **r.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "generation_intent": intent})
    projection = VerifiedGenerationRequirementProjection.create(**{
        **s["projection"].model_dump(mode="python", exclude={"projection_hash", "requirement"}),
        "requirement": requirement})
    target = old.model_copy(update={"final_output_goal": _goal("2"), "recipe":
        old.recipe.model_copy(update={"requirement_hash": requirement.requirement_hash})})
    s["projection"] = projection
    s["policy"] = s["policy"].model_copy(update={"execution_purpose": "qualification"})
    s["inputs"] = s["inputs"].model_copy(update={
        "projection_hash": projection.projection_hash,
        "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"],
        "policy": DecisionPolicy(max_resamples=0, allow_bounded_exploration=True),
        "limits": limits.model_copy(update={"paid_submits_used": 1}),
        "candidates": (target,), "historical_recipes": (old,), "evidence": (e,),
        "experiences": (experience,), "latest_attempt_hash": e.evidence_hash,
        "baseline_request": baseline})
    return s


@pytest.mark.parametrize("verdict", ["NOT_EVALUATED", "FAIL"])
def test_same_rubric_new_intent_is_considered_without_claiming_old_media_passed(verdict):
    result = decide(case(verdict=verdict))
    assert result.disposition == "GENERATE_ONCE"
    assert not result.diagnosis.all_required_observed_pass
    assert ("EVIDENCE_GAP" if verdict == "NOT_EVALUATED" else "QUALITY_FAILURE") in result.diagnosis.failure_classes


@pytest.mark.parametrize("mutation", ["goal", "intent", "budget", "resample", "baseline", "production"])
def test_prospective_route_does_not_admit_unchanged_or_unbounded_work(mutation):
    s = case()
    i = s["inputs"]
    if mutation == "goal":
        s["inputs"] = i.model_copy(update={"candidates": (i.candidates[0].model_copy(update={"final_output_goal": _goal("1")}),)})
    elif mutation == "intent":
        old = i.experiences[0]
        s["inputs"] = i.model_copy(update={"experiences": (old.model_copy(update={"projection": s["projection"]}),)})
    elif mutation == "budget":
        s["inputs"] = i.model_copy(update={"limits": i.limits.model_copy(update={"paid_submit_ceiling": 1})})
    elif mutation == "resample":
        s["inputs"] = i.model_copy(update={"policy": DecisionPolicy(max_resamples=1, allow_bounded_exploration=True)})
    elif mutation == "baseline":
        s["inputs"] = i.model_copy(update={"baseline_request": None})
    else:
        s["policy"] = s["policy"].model_copy(update={"execution_purpose": "production"})
    if mutation == "intent":
        with pytest.raises(ValueError, match="historical requirement"):
            decide(s)
    else:
        assert decide(s).disposition != "GENERATE_ONCE"


@pytest.mark.parametrize("outcome,expected", [("unknown_outcome", "UNKNOWN_OUTCOME"), ("runtime_failure", "RUNTIME_FAILURE")])
def test_authored_goal_never_overrides_unknown_or_runtime_failure(outcome, expected):
    assert decide(case(outcome=outcome)).disposition == expected
