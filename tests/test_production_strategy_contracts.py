import pytest

from ai_video.production.production_strategy_contracts import (
    ProductionCoverage, ProductionIntent, ProductionOperation, ProductionUnit,
    ProductionSourceOption,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.seedance_source_expression import (
    PreservedSourceExpression, SourceReferenceMaterial, SourceReferencePart,
    SourceTextPart, source_parts_sha256,
)
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint


def unit(**changes):
    values = dict(component_id="action", shot_id="shot-action",
        intent="The hand rises beside the glass.", duration_frames=48,
        requirement_ids=("hand",), motion_required=True)
    values.update(changes)
    return ProductionUnit(**values)


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


def test_retimed_source_window_is_distinct_from_output_duration_and_legacy_dump_omits_none():
    time_map = VideoTimeMap(points=(
        VideoTimePoint(source_frame=0, output_frame=0),
        VideoTimePoint(source_frame=48, output_frame=24),
    ), audio_policy="mute")
    source = ProductionSourceOption(
        asset_id="clip", asset_sha256="a" * 64, role="primary_visual",
        timebase="frames", duration=48, source_time_map=time_map,
    )
    retimed = unit(duration_frames=24, source_options=(source,))
    legacy_source = ProductionSourceOption(
        asset_id="legacy", asset_sha256="b" * 64, role="primary_visual",
        timebase="frames", duration=48,
    )

    assert retimed.duration_frames == time_map.output_duration_frames
    assert source.duration == time_map.source_duration_frames
    assert "source_time_map" in source.model_dump(mode="json")
    assert "source_time_map" not in legacy_source.model_dump(mode="json")


@pytest.mark.parametrize(("source_frames", "output_frames"), [(47, 24), (48, 23), (48, 25)])
def test_retimed_source_map_must_end_at_exact_source_and_output_frames(source_frames, output_frames):
    time_map = VideoTimeMap(points=(
        VideoTimePoint(source_frame=0, output_frame=0),
        VideoTimePoint(source_frame=source_frames, output_frame=output_frames),
    ), audio_policy="mute")
    with pytest.raises(ValueError, match="time map|source duration"):
        source = ProductionSourceOption(
            asset_id="clip", asset_sha256="a" * 64, role="primary_visual",
            timebase="frames", duration=48, source_time_map=time_map,
        )
        unit(duration_frames=24, source_options=(source,))


@pytest.mark.parametrize(
    "source_text",
    (
        "At a glass partition, a courier pauses and lowers one hand.",
        "A rover crosses a workshop, stops, and turns toward a doorway.",
    ),
)
def test_production_unit_preserves_exact_source_expression_and_reference_order(source_text):
    materials = (
        SourceReferenceMaterial(asset_id="identity-a", asset_sha256="a" * 64, role="identity"),
        SourceReferenceMaterial(asset_id="scene-b", asset_sha256="b" * 64, role="scene"),
    )
    parts = (
        SourceTextPart(text=source_text),
        SourceReferencePart(slot_id="ordered-reference", materials=materials),
        SourceTextPart(text="保持原文的结尾与限制。"),
    )
    expression = PreservedSourceExpression(
        source_sha256=source_parts_sha256(parts), parts=parts,
    )

    authored = unit(preserved_source_expression=expression)
    reopened = ProductionUnit.model_validate_json(authored.model_dump_json())

    assert authored.preserved_source_expression == expression
    assert authored.preserved_source_expression.parts == parts
    assert authored.preserved_source_expression.parts[1].materials == materials
    assert reopened.preserved_source_expression == expression


def test_legacy_production_unit_omits_absent_source_expression_without_changing_hash():
    authored = unit()

    assert "preserved_source_expression" not in authored.model_dump(mode="json")
    assert canonical_sha256(authored.model_dump(mode="json")) == (
        "6a432817533fa54564fc3db23d07dc22bee199c1e9582afbdd762f72e77806b1"
    )
