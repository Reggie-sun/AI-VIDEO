"""Fresh-generation acting obligations and read-only projections of their inputs.

Intent, selected QA and the request retain their existing owners. These checks
neither invent acting nor certify model quality, and never run on history reads.
"""
from collections.abc import Mapping

from ai_video.errors import AiVideoError, ErrorCode

_ROOT = "generation_intent.performance_intent"
_DIRECTIONS = f"{_ROOT}.character_directions"
_BEAT_FIELDS = ("trigger", "emotion", "intensity", "facial_expression", "gaze_target",
                "breathing", "body_behavior")


def _value(rule, name, default=None):
    return rule.get(name, default) if isinstance(rule, Mapping) else getattr(rule, name, default)


def _actor_paths(actor, index):
    base = f"{_DIRECTIONS}.{index}"
    if actor.visibility == "offscreen":
        return (f"{base}.visibility", f"{base}.offscreen_reason")
    return tuple(f"{base}.beats.{number}.{field}"
        for number, _ in enumerate(actor.beats) for field in _BEAT_FIELDS)


def _matching_rules(paths, rules, required_ids):
    admitted = [rule for rule in rules if _value(rule, "level") == "acceptance"
        and _value(rule, "stage") == "raw_generation" and _value(rule, "proof") in {"analyzer", "human"}
        and _value(rule, "requirement_id") in required_ids]
    coverage = {path: tuple(_value(rule, "requirement_id") for rule in admitted if any(
        target.startswith(_ROOT) and (path == target or path.startswith(target + "."))
        for target in _value(rule, "intent_paths", ()))) for path in paths}
    return coverage


def performance_acceptance_issues(intent, rules, required_ids):
    performance = intent.performance_intent
    actors = () if performance is None else performance.character_directions
    missing = []
    for index, actor in enumerate(actors):
        coverage = _matching_rules(_actor_paths(actor, index), rules, required_ids)
        if any(not ids for ids in coverage.values()):
            missing.append(f"{_DIRECTIONS}.{actor.character_id}.acceptance")
    return tuple(missing)


def require_performance_authoring(requirement, acceptance):
    """Require explicit acting before creating a new generation, never on reopen."""
    from ai_video.production.performance_direction import performance_direction_issues

    issues = list(performance_direction_issues(requirement.generation_intent, requirement.characters))
    payload = getattr(acceptance, "profile_payload", {})
    issues.extend(performance_acceptance_issues(requirement.generation_intent,
        payload.get("generation_requirements", ()), getattr(acceptance, "required_requirement_ids", ())))
    if issues:
        raise AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Author character performance and its raw analyzer/human acceptance before new generation: "
                + ", ".join(issues))


def performance_authoring_report(*, intent, characters, rules=None, required_ids=(), prompt_text=None):
    """Project mandatory authoring, lexical expression and QA separately."""
    from pydantic import ValidationError
    from ai_video.production.video_requirement import GenerationIntent
    from ai_video.production.performance_direction import (
        performance_direction_issues, render_performance_direction,
    )

    if not isinstance(intent, GenerationIntent):
        try:
            intent = GenerationIntent.model_validate(intent or {})
        except ValidationError as error:
            return {"mandatory_for_new_generation": bool(characters), "authoring_status": "INVALID",
                "issues": ["generation_intent." + ".".join(map(str, item["loc"])) for item in error.errors()],
                "actual_quality": "NOT_EVALUATED"}
    issues = list(performance_direction_issues(intent, characters))
    if rules is not None:
        issues.extend(performance_acceptance_issues(intent, rules, required_ids))
    performance = intent.performance_intent
    actors = () if performance is None else performance.character_directions
    block = "" if performance is None else render_performance_direction(performance)
    expression = ("NOT_EVALUATED" if prompt_text is None or not block else
                  "LEXICALLY_EXPRESSED" if block in prompt_text else "UNEXPRESSED")
    entries = []
    for index, actor in enumerate(actors):
        coverage = {} if rules is None else _matching_rules(_actor_paths(actor, index), rules, required_ids)
        entries.append({"intent_path": f"{_DIRECTIONS}.{index}",
            "direction": actor.model_dump(mode="json"),
            "acceptance_requirement_ids": sorted({identifier for ids in coverage.values() for identifier in ids})})
    return {"mandatory_for_new_generation": bool(characters),
        "authoring_status": "INCOMPLETE" if issues else "AUTHORED" if characters else "NO_CAST",
        "issues": issues, "characters": entries, "native_text_required": block,
        "input_expression": expression, "mechanism": "MODEL_PROMPT_GUIDANCE",
        "acceptance_mapping": "NOT_EVALUATED" if rules is None else "MISSING" if any(
            issue.endswith(".acceptance") for issue in issues) else "DECLARED",
        "actual_quality": "NOT_EVALUATED"}
