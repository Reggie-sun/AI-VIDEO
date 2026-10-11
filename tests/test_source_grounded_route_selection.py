"""Source-grounded selection remains distinct from legacy accepted sequence proof."""

from dataclasses import replace

import pytest


@pytest.fixture(scope="session")
def activated_legacy_sequence(tmp_path_factory):
    """Reuse one persisted accepted-media activation and its real sequence issuer."""
    import test_planning_sequence_continuity as sequence
    from test_typed_causal_native_expression import (
        canonical_expression_fixture,
        expression_context,
    )

    root = tmp_path_factory.mktemp("legacy-sequence-selection")
    accepted = sequence._activated_source(root)
    fixture = canonical_expression_fixture(root, source=accepted)
    opening = expression_context(fixture)
    assert opening.state_contract == "complete-causal/2"
    return {**fixture, "accepted_source": accepted, "legacy_opening": opening}


def test_legacy_accepted_source_does_not_issue_partial_selection(activated_legacy_sequence):
    from ai_video.production._sequence_source import (
        build_verified_source_selection_expression,
    )

    fixture = activated_legacy_sequence
    target = fixture["requirement"].target_shot
    assert fixture["loaded"].manifest.active_registry is not None
    assert target.preserved_source_expression is None

    with pytest.raises(ValueError, match="source selection target/snapshot is stale"):
        build_verified_source_selection_expression(
            loaded=fixture["loaded"],
            requirement=fixture["requirement"],
            provider_bound=fixture["provider_bound"],
        )


def test_wrong_canonical_target_cannot_issue_partial_selection(activated_legacy_sequence):
    from ai_video.production._sequence_source import (
        build_verified_source_selection_expression,
    )

    fixture = activated_legacy_sequence
    wrong_target = fixture["loaded"].shots[0]
    wrong_requirement = fixture["requirement"].model_copy(
        update={"target_shot": wrong_target}
    )
    with pytest.raises(ValueError):
        build_verified_source_selection_expression(
            loaded=fixture["loaded"],
            requirement=wrong_requirement,
            provider_bound=fixture["provider_bound"],
        )


def test_copied_legacy_opening_is_rejected_by_partial_source_compiler(
    activated_legacy_sequence,
):
    from ai_video.production.seedance_source_expression import (
        PreservedSourceExpression,
        SourceStateGrounding,
        SourceTextPart,
        compile_preserved_seedance_source,
        source_parts_sha256,
    )
    from ai_video.production.video_requirement import (
        ProviderNeutralVideoRequirement,
        TypedStateReference,
    )
    from ai_video.production.hashing import canonical_sha256
    from test_seedance_source_expression import _rebind_source_expression
    from test_seedance_source_prompt import _case

    _, bound, requirement, source_text = _case()
    fact = source_text[:8]
    parts = (SourceTextPart(text=source_text),)
    expression = PreservedSourceExpression(
        source_sha256=source_parts_sha256(parts),
        parts=parts,
        opening=(
            SourceStateGrounding(
                dimension="prop_identity", kind="quote", fact=fact
            ),
        ),
    )
    intent = requirement.generation_intent.model_copy(
        update={
            "open_state": TypedStateReference(
                kind="typed_hash",
                state_hash=canonical_sha256({"prop_identity": fact}),
            )
        }
    )
    grounded_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python", exclude={"requirement_id", "requirement_hash"}
            ),
            "generation_intent": intent,
        }
    )
    bound, grounded_requirement = _rebind_source_expression(
        bound, grounded_requirement, expression, source_text
    )

    copied_opening = replace(activated_legacy_sequence["legacy_opening"])
    with pytest.raises(ValueError, match="exact owner-issued lineage"):
        compile_preserved_seedance_source(
            bound, grounded_requirement, continuity_expression=copied_opening
        )
