"""Synthetic, explicitly authored performance for scripted generation fixtures."""

from __future__ import annotations

from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.hashing import canonical_sha256
from ai_video.production.performance_direction import (
    CharacterPerformanceDirection,
    PerformanceBeat,
)
from ai_video.production.video_requirement import PerformanceIntent


def fixture_performance_intent(
    characters,
    *,
    trigger: str,
    emotion: str,
    facial_expression: str,
    gaze_target: str,
    breathing: str,
    body_behavior: str,
) -> PerformanceIntent:
    """Author one simple visible direction for every character in a test Shot."""

    characters = tuple(characters)
    if not characters:
        raise ValueError("fixture performance requires the Shot's actual cast")
    principal_id = next(
        (character.character_id for character in characters if character.character_id == "hero"),
        characters[0].character_id,
    )
    directions = tuple(
        CharacterPerformanceDirection(
            character_id=character.character_id,
            screen_identity=character.name,
            role="principal" if character.character_id == principal_id else "supporting",
            visibility="visible",
            beats=(
                PerformanceBeat(
                    phase="throughout",
                    trigger=trigger,
                    emotion=emotion,
                    intensity="subtle",
                    facial_expression=facial_expression,
                    gaze_target=gaze_target,
                    breathing=breathing,
                    body_behavior=body_behavior,
                ),
            ),
        )
        for character in characters
    )
    return PerformanceIntent(
        trigger=trigger,
        visible_response=facial_expression,
        gaze_target=gaze_target,
        body_behavior=body_behavior,
        hand_behavior="continues only the authored Shot action",
        terminal_performance_state="settled in the authored Shot action",
        character_directions=directions,
    )


def fixture_performance_expression(*, requirement_id="performance", semantics=False) -> RequirementExpression:
    """Raw analyzer obligation for the selected synthetic fixture rubric."""

    values = dict(
        requirement_id=requirement_id,
        level="acceptance",
        stage="raw_generation",
        dimension="character_performance",
        observable="The visible cast follows the authored per-character performance direction.",
        tolerance="match the authored direction",
        measurement="scripted analyzer observation on fixture media",
        proof="analyzer",
        intent_paths=("generation_intent.performance_intent",),
        native_text=(),
        production_owner="test_fixture",
    )
    if semantics:
        from ai_video.production.requirement_semantics import (
            HardBasis,
            IntentSourceReference,
            RequirementSemantics,
            SEMANTICS_VERSION,
        )

        source_hash = canonical_sha256({"fixture": "authored-character-performance"})
        locator = "tests/performance_fixture.py:fixture_performance_expression"
        source = IntentSourceReference(
            source_hash=source_hash,
            locator=locator,
            intent_item_id=requirement_id,
            quote="the authored fixture direction is a test input contract",
            origin="director_choice",
        )
        values["semantics"] = RequirementSemantics(
            version=SEMANTICS_VERSION,
            category="quality_critical",
            intent_role="preferred_performance",
            source_refs=(source,),
            hard_basis=HardBasis(
                source_hash=source_hash,
                locator=locator,
                kind="production_contract",
                necessity="The synthetic test exercises mandatory acting authoring and QA mapping.",
            ),
        )
    return RequirementExpression(**values)


def acceptance_with_fixture_performance(acceptance):
    """Extend the exact fixture QA profile while preserving its existing rules."""

    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.generation_recipe import RequirementExpression

    payload = dict(acceptance.profile_payload)
    raw_rules = tuple(payload.get("generation_requirements", ()))
    rules = tuple(RequirementExpression.model_validate(item) for item in raw_rules)
    if any(
        rule.requirement_id in acceptance.required_requirement_ids
        and rule.level == "acceptance"
        and rule.stage == "raw_generation"
        and rule.proof in {"analyzer", "human"}
        and any(path in {"generation_intent.performance_intent",
                         "generation_intent.performance_intent.character_directions"}
                for path in rule.intent_paths)
        for rule in rules
    ):
        return acceptance
    requirement_id = "performance" if all(rule.requirement_id != "performance" for rule in rules) else (
        "character-performance-fixture"
    )
    performance = fixture_performance_expression(
        requirement_id=requirement_id,
        semantics=bool(payload.get("requirement_semantics_version")),
    )
    required_ids = tuple(sorted({*acceptance.required_requirement_ids, performance.requirement_id}))
    raw_by_id = {item["requirement_id"]: item for item in raw_rules}
    raw_by_id[performance.requirement_id] = performance.model_dump(mode="json", exclude={"native_text"})
    payload.update(
        required_requirement_ids=required_ids,
        generation_requirements=tuple(raw_by_id[key] for key in sorted(raw_by_id)),
    )
    payload.pop("content_hash", None)
    digest = canonical_sha256(payload)
    payload["content_hash"] = digest
    return DomainAcceptancePolicy(
        domain_id=acceptance.domain_id,
        profile_id=acceptance.profile_id,
        profile_version=acceptance.profile_version,
        profile_content_hash=digest,
        measurement_contract_version=acceptance.measurement_contract_version,
        required_requirement_ids=required_ids,
        profile_payload=payload,
    )


__all__ = [
    "acceptance_with_fixture_performance",
    "fixture_performance_expression",
    "fixture_performance_intent",
]
