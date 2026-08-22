from __future__ import annotations

import copy
import os
import socket
import subprocess

import pytest
from pydantic import ValidationError

from ai_video.planning import ContinuityMode, GenerationMode
from scripts.composition_playbooks import EvidenceRequirement
from scripts.composition_shadow import (
    ComparisonReasonCode,
    CompositionStrategyProposal,
    ProposalRationaleCode,
    ProposalUncertainty,
    StrategyProposalComparisonResult,
    compare_strategy_proposal,
)
from tests.fixtures.planning_factory import ONE_HASH, make_plan


def _proposal(**overrides: object) -> CompositionStrategyProposal:
    values: dict[str, object] = {
        "target_shot_id": "shot-1",
        "target_shot_revision": 1,
        "target_shot_content_hash": ONE_HASH,
        "playbook_id": "character_consistent_dialogue_scene",
        "playbook_version": "1.0.0",
        "proposed_strategy": GenerationMode.REFERENCE_TO_VIDEO,
        "continuity_preference": ContinuityMode.REFERENCE,
        "rationale_codes": (
            ProposalRationaleCode.PLAYBOOK_APPLICABLE,
            ProposalRationaleCode.IDENTITY_REFERENCE_PREFERRED,
        ),
        "rejected_strategies": (GenerationMode.IMAGE_TO_VIDEO,),
        "uncertainty": ProposalUncertainty.LOW,
        "required_evidence": (
            EvidenceRequirement.TARGET_SHOT_IDENTITY,
            EvidenceRequirement.CHARACTER_IDENTITY_REFERENCES,
        ),
        "expected_failure_modes": ("identity_drift",),
        "notes": "Diagnostic observation only.",
    }
    values.update(overrides)
    return CompositionStrategyProposal.create(**values)


def test_valid_proposal_is_strict_typed_and_sealed() -> None:
    proposal = _proposal()

    assert proposal.proposal_version == "composition-strategy-proposal/1"
    assert proposal.proposal_id == f"composition-proposal-{proposal.proposal_hash[:24]}"
    assert proposal.proposed_strategy is GenerationMode.REFERENCE_TO_VIDEO


@pytest.mark.parametrize(
    "missing_field",
    ["target_shot_id", "target_shot_revision", "target_shot_content_hash"],
)
def test_target_shot_identity_must_be_complete(missing_field: str) -> None:
    values = _proposal().model_dump(mode="python")
    values.pop(missing_field)
    values.pop("proposal_id")
    values.pop("proposal_hash")
    values.pop("proposal_version")

    with pytest.raises(ValidationError, match=missing_field):
        CompositionStrategyProposal.create(**values)


def test_invalid_strategy_fails() -> None:
    with pytest.raises(ValidationError, match="proposed_strategy"):
        _proposal(proposed_strategy="magic_video")


def test_proposal_playbook_id_uses_canonical_playbook_format() -> None:
    with pytest.raises(ValidationError, match="playbook_id"):
        _proposal(playbook_id="../non-canonical")


def test_duplicate_rationale_code_fails() -> None:
    with pytest.raises(ValidationError, match="rationale_codes must be unique"):
        _proposal(
            rationale_codes=(
                ProposalRationaleCode.PLAYBOOK_APPLICABLE,
                ProposalRationaleCode.PLAYBOOK_APPLICABLE,
            )
        )


def test_rejected_strategy_cannot_equal_proposed_strategy() -> None:
    with pytest.raises(ValidationError, match="cannot include proposed_strategy"):
        _proposal(rejected_strategies=(GenerationMode.REFERENCE_TO_VIDEO,))


def test_invalid_uncertainty_fails() -> None:
    with pytest.raises(ValidationError, match="uncertainty"):
        _proposal(uncertainty="almost-certain")


def test_proposal_hash_is_deterministic_and_notes_are_non_semantic() -> None:
    first = _proposal(notes="First diagnostic note")
    second = _proposal(notes="Different diagnostic note")
    changed = _proposal(uncertainty=ProposalUncertainty.HIGH)

    assert first.proposal_hash == second.proposal_hash
    assert first.proposal_id == second.proposal_id
    assert changed.proposal_hash != first.proposal_hash


def test_match_compares_same_strategy_and_continuity() -> None:
    plan = make_plan(
        target_shot_content_hash=ONE_HASH,
        generation_mode=GenerationMode.REFERENCE_TO_VIDEO,
        continuity_mode=ContinuityMode.REFERENCE,
    )

    comparison = compare_strategy_proposal(_proposal(), plan)

    assert comparison.result is StrategyProposalComparisonResult.MATCH
    assert comparison.reason_codes == (ComparisonReasonCode.STRATEGY_MODE_MATCHES,)
    assert comparison.production_effect == "none"


def test_difference_reports_strategy_and_advisory_identity_preference() -> None:
    plan = make_plan(
        target_shot_content_hash=ONE_HASH,
        generation_mode=GenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=ContinuityMode.REFERENCE,
    )

    comparison = compare_strategy_proposal(_proposal(), plan)

    assert comparison.result is StrategyProposalComparisonResult.DIFFERENT
    assert comparison.reason_codes == (
        ComparisonReasonCode.STRATEGY_MODE_DIFFERS,
        ComparisonReasonCode.AGENT_PREFERS_IDENTITY_REFERENCE,
    )
    assert comparison.agent_strategy is GenerationMode.REFERENCE_TO_VIDEO
    assert comparison.planner_strategy is GenerationMode.IMAGE_TO_VIDEO


def test_identity_difference_code_requires_reference_to_video_proposal() -> None:
    proposal = _proposal(
        proposed_strategy=GenerationMode.STATIC_IMAGE,
        rejected_strategies=(GenerationMode.IMAGE_TO_VIDEO,),
    )
    plan = make_plan(
        target_shot_content_hash=ONE_HASH,
        generation_mode=GenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=ContinuityMode.REFERENCE,
    )

    comparison = compare_strategy_proposal(proposal, plan)

    assert comparison.result is StrategyProposalComparisonResult.DIFFERENT
    assert comparison.reason_codes == (ComparisonReasonCode.STRATEGY_MODE_DIFFERS,)


@pytest.mark.parametrize(
    "operation",
    [GenerationMode.VIDEO_EDIT, GenerationMode.VIDEO_EXTEND],
)
def test_planner_reachable_video_operations_are_comparable(
    operation: GenerationMode,
) -> None:
    proposal = _proposal(
        proposed_strategy=operation,
        rejected_strategies=(GenerationMode.REFERENCE_TO_VIDEO,),
    )
    plan = make_plan(
        target_shot_content_hash=ONE_HASH,
        generation_mode=operation,
        continuity_mode=ContinuityMode.REFERENCE,
    )

    comparison = compare_strategy_proposal(proposal, plan)

    assert comparison.result is StrategyProposalComparisonResult.MATCH
    assert comparison.reason_codes == (ComparisonReasonCode.STRATEGY_MODE_MATCHES,)


def test_different_target_shot_identity_is_not_comparable() -> None:
    plan = make_plan(
        target_shot_id="different-shot",
        target_shot_content_hash=ONE_HASH,
        generation_mode=GenerationMode.REFERENCE_TO_VIDEO,
        continuity_mode=ContinuityMode.REFERENCE,
    )

    comparison = compare_strategy_proposal(_proposal(), plan)

    assert comparison.result is StrategyProposalComparisonResult.NOT_COMPARABLE
    assert comparison.reason_codes == (
        ComparisonReasonCode.TARGET_SHOT_IDENTITY_DIFFERS,
    )


def test_comparison_is_pure_and_leaves_plan_and_environment_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = make_plan(
        target_shot_content_hash=ONE_HASH,
        generation_mode=GenerationMode.REFERENCE_TO_VIDEO,
        continuity_mode=ContinuityMode.REFERENCE,
    )
    before = copy.deepcopy(plan.model_dump(mode="json"))

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("comparison attempted an external side effect")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(os, "getenv", forbidden)

    comparison = compare_strategy_proposal(_proposal(), plan)

    assert comparison.result is StrategyProposalComparisonResult.MATCH
    assert plan.model_dump(mode="json") == before
    assert plan.plan_hash == make_plan(
        target_shot_content_hash=ONE_HASH,
        generation_mode=GenerationMode.REFERENCE_TO_VIDEO,
        continuity_mode=ContinuityMode.REFERENCE,
    ).plan_hash
