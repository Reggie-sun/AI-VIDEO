import pytest

from ai_video.production.production_strategy_contracts import (
    ProductionCoverage, ProductionIntent, ProductionOperation, ProductionUnit,
    ProductionSourceOption,
)


def unit(**changes):
    return ProductionUnit(**dict(component_id="action", shot_id="shot-action",
        intent="The hand rises beside the glass.", duration_frames=48,
        requirement_ids=("hand",), motion_required=True, **changes))


def test_single_take_intent_rejects_visible_split_without_losing_requirements():
    coverage = ProductionCoverage(coverage_id="split", allocation_id="split",
        units=(unit(), ProductionUnit(component_id="reaction", shot_id="reaction",
            intent="Reaction", duration_frames=24, requirement_ids=("reaction",))))
    with pytest.raises(ValueError, match="single.take"):
        ProductionIntent(task_id="task", allowed_operations=(ProductionOperation.SPLIT_SHOT,),
            protected_requirement_ids=("hand", "reaction"), single_take=True,
            coverage_options=(coverage,))


def test_coverage_rejects_duplicate_component_and_shot_identity():
    with pytest.raises(ValueError, match="unique"):
        ProductionCoverage(coverage_id="split", allocation_id="split", units=(unit(), unit()))


def test_source_window_cannot_be_negative_or_zero():
    for updates in ({"start": -1}, {"duration": 0}):
        values = dict(asset_id="clip", asset_sha256="a" * 64, role="primary_visual",
            timebase="frames", start=0, duration=48, evidence_ids=("review",))
        with pytest.raises(ValueError):
            ProductionSourceOption(**{**values, **updates})


def test_generation_is_an_explicit_allowed_operation_not_an_implicit_fallback():
    intent = ProductionIntent(task_id="task",
        allowed_operations=(ProductionOperation.TRIM_EXISTING,),
        protected_requirement_ids=("hand",), coverage_options=(
            ProductionCoverage(coverage_id="master", allocation_id="master", units=(unit(),)),))
    assert ProductionOperation.GENERATE_FULL_SHOT not in intent.allowed_operations
    assert ProductionIntent.model_validate_json(intent.model_dump_json()) == intent
