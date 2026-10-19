"""New generation requires authored acting; history remains independently readable."""
from copy import deepcopy

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.performance_authoring import (
    performance_acceptance_issues, require_performance_authoring,
)
from ai_video.production.video_requirement import GenerationIntent


def direction():
    return {"trigger": "an approaching guest", "visible_response": "a restrained greeting",
        "gaze_target": "the doorway", "body_behavior": "shoulders ease",
        "hand_behavior": "hands stay on the counter", "terminal_performance_state": "attentive",
        "character_directions": [{"character_id": "host", "screen_identity": "the host in a blue apron",
            "role": "principal", "visibility": "visible", "beats": [{"phase": "throughout",
                "trigger": "the guest approaches", "emotion": "quiet anticipation", "intensity": "subtle",
                "facial_expression": "eyes soften and mouth corners lift slightly",
                "gaze_target": "the arriving guest", "breathing": "relaxed unforced breathing",
                "body_behavior": "a small natural shift of weight"}]}]}


def rule(**updates):
    return {"requirement_id": "acting", "level": "acceptance", "stage": "raw_generation",
        "proof": "analyzer", "intent_paths": ["generation_intent.performance_intent.character_directions"],
        **updates}


def test_acting_requires_semantic_raw_acceptance_and_complete_field_coverage():
    intent = GenerationIntent(performance_intent=direction())
    assert performance_acceptance_issues(intent, [rule()], ("acting",)) == ()
    for changed in ({"proof": "technical"}, {"stage": "final_composition"},
                    {"level": "recipe_hint"}, {"requirement_id": "not-required"},
                    {"intent_paths": ["generation_intent.subject_action.progression"]}):
        assert performance_acceptance_issues(intent, [rule(**changed)], ("acting",))
    only_gaze = rule(intent_paths=[
        "generation_intent.performance_intent.character_directions.0.beats.0.gaze_target"])
    assert performance_acceptance_issues(intent, [only_gaze], ("acting",))


def test_new_generation_guard_reports_missing_actor_without_autofilling():
    from types import SimpleNamespace
    requirement = SimpleNamespace(generation_intent=GenerationIntent(),
        characters=(SimpleNamespace(character_id="host"),))
    before = requirement.generation_intent.model_dump(mode="json")
    with pytest.raises(AiVideoError, match="host"):
        require_performance_authoring(requirement, None)
    assert requirement.generation_intent.model_dump(mode="json") == before
    requirement.characters = ()
    require_performance_authoring(requirement, None)


def test_guard_requires_every_visible_actor_and_preserves_explicit_offscreen():
    from types import SimpleNamespace
    data = direction()
    data["character_directions"].append({"character_id": "caller", "screen_identity": "the caller outside",
        "role": "supporting", "visibility": "offscreen", "offscreen_reason": "speaks from outside the shop",
        "beats": []})
    requirement = SimpleNamespace(generation_intent=GenerationIntent(performance_intent=data),
        characters=tuple(SimpleNamespace(character_id=x) for x in ("host", "caller")))
    acceptance = SimpleNamespace(profile_payload={"generation_requirements": [rule()]},
        required_requirement_ids=("acting",))
    require_performance_authoring(requirement, acceptance)
    altered = deepcopy(data)
    altered["character_directions"].pop()
    requirement.generation_intent = GenerationIntent(performance_intent=altered)
    with pytest.raises(AiVideoError, match="caller"):
        require_performance_authoring(requirement, acceptance)
