"""Typed, side-effect-free shadow strategy proposals and comparisons."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _PROJECT_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from ai_video.planning._planner_models import (
    ContinuityMode,
    GenerationMode,
    VideoGenerationPlan,
)
from ai_video.production.hashing import canonical_sha256
from scripts.composition_playbooks import (
    PLAYBOOK_ID_PATTERN,
    EvidenceRequirement,
    ExpectedFailureMode,
)


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_SEMVER = r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$"
_PROPOSAL_VERSION = "composition-strategy-proposal/1"

NonEmptyNote = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]


class _StrictShadowModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class ProposalRationaleCode(str, Enum):
    PLAYBOOK_APPLICABLE = "playbook_applicable"
    IDENTITY_REFERENCE_PREFERRED = "identity_reference_preferred"
    EXACT_TERMINAL_PREFERRED = "exact_terminal_preferred"
    GENERATED_MOTION_REQUIRED = "generated_motion_required"
    STATIC_VISUAL_SUFFICIENT = "static_visual_sufficient"
    IMAGE_MOTION_SUFFICIENT = "image_motion_sufficient"
    COST_EFFICIENCY = "cost_efficiency"
    CONTINUITY_RISK = "continuity_risk"
    ANGLE_CHANGE_REQUIRES_REFERENCE = "angle_change_requires_reference"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


class ProposalUncertainty(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StrategyProposalComparisonResult(str, Enum):
    MATCH = "match"
    DIFFERENT = "different"
    NOT_COMPARABLE = "not_comparable"


class ComparisonReasonCode(str, Enum):
    STRATEGY_MODE_MATCHES = "strategy_mode_matches"
    STRATEGY_MODE_DIFFERS = "strategy_mode_differs"
    CONTINUITY_MODE_DIFFERS = "continuity_mode_differs"
    AGENT_PREFERS_IDENTITY_REFERENCE = "agent_prefers_identity_reference"
    TARGET_SHOT_IDENTITY_DIFFERS = "target_shot_identity_differs"


class _ProposalSemantic(_StrictShadowModel):
    proposal_version: Literal["composition-strategy-proposal/1"] = _PROPOSAL_VERSION
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    playbook_id: str = Field(pattern=PLAYBOOK_ID_PATTERN)
    playbook_version: str = Field(pattern=_SEMVER)
    proposed_strategy: GenerationMode
    continuity_preference: ContinuityMode
    rationale_codes: tuple[ProposalRationaleCode, ...] = Field(min_length=1)
    rejected_strategies: tuple[GenerationMode, ...] = ()
    uncertainty: ProposalUncertainty
    required_evidence: tuple[EvidenceRequirement, ...] = Field(min_length=1)
    expected_failure_modes: tuple[ExpectedFailureMode, ...] = ()

    @model_validator(mode="after")
    def _validate_semantics(self) -> "_ProposalSemantic":
        for field_name in (
            "rationale_codes",
            "rejected_strategies",
            "required_evidence",
            "expected_failure_modes",
        ):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        if self.proposed_strategy in self.rejected_strategies:
            raise ValueError("rejected_strategies cannot include proposed_strategy")
        return self


class CompositionStrategyProposal(_ProposalSemantic):
    """Advisory evidence excluded from every Production canonical hash."""

    proposal_id: str = Field(pattern=_SAFE_ID)
    notes: NonEmptyNote | None = None
    proposal_hash: str = Field(pattern=_SHA256)

    def _semantic_payload(self) -> dict[str, object]:
        return {
            field_name: getattr(self, field_name)
            for field_name in _ProposalSemantic.model_fields
        }

    @model_validator(mode="after")
    def _validate_seal(self) -> "CompositionStrategyProposal":
        semantic = _ProposalSemantic.model_validate(self._semantic_payload())
        expected_hash = canonical_sha256(semantic.model_dump(mode="json"))
        if self.proposal_hash != expected_hash:
            raise ValueError("proposal_hash does not match semantic proposal fields")
        expected_id = f"composition-proposal-{expected_hash[:24]}"
        if self.proposal_id != expected_id:
            raise ValueError("proposal_id does not match proposal_hash")
        return self

    @classmethod
    def create(cls, **values: object) -> "CompositionStrategyProposal":
        payload = dict(values)
        payload.setdefault("proposal_version", _PROPOSAL_VERSION)
        notes = payload.pop("notes", None)
        semantic = _ProposalSemantic.model_validate(payload)
        proposal_hash = canonical_sha256(semantic.model_dump(mode="json"))
        return cls.model_validate(
            {
                **semantic.model_dump(mode="python"),
                "proposal_id": f"composition-proposal-{proposal_hash[:24]}",
                "notes": notes,
                "proposal_hash": proposal_hash,
            }
        )


class StrategyProposalComparison(_StrictShadowModel):
    comparison_version: Literal["composition-strategy-comparison/1"] = (
        "composition-strategy-comparison/1"
    )
    proposal_hash: str = Field(pattern=_SHA256)
    plan_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    result: StrategyProposalComparisonResult
    agent_strategy: GenerationMode
    planner_strategy: GenerationMode
    agent_continuity: ContinuityMode
    planner_continuity: ContinuityMode
    reason_codes: tuple[ComparisonReasonCode, ...] = Field(min_length=1)
    production_effect: Literal["none"] = "none"

    @model_validator(mode="after")
    def _validate_reason_codes(self) -> "StrategyProposalComparison":
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("comparison reason_codes must be unique")
        return self


def compare_strategy_proposal(
    proposal: CompositionStrategyProposal,
    current_plan: VideoGenerationPlan,
) -> StrategyProposalComparison:
    """Compare advisory evidence without mutating or executing Production state."""

    planner_strategy = current_plan.generation_mode
    planner_continuity = current_plan.continuity_mode
    common = {
        "proposal_hash": proposal.proposal_hash,
        "plan_hash": current_plan.plan_hash,
        "target_shot_id": proposal.target_shot_id,
        "agent_strategy": proposal.proposed_strategy,
        "planner_strategy": planner_strategy,
        "agent_continuity": proposal.continuity_preference,
        "planner_continuity": planner_continuity,
    }
    if (
        proposal.target_shot_id != current_plan.target_shot_id
        or proposal.target_shot_revision != current_plan.target_shot_revision
        or proposal.target_shot_content_hash != current_plan.target_shot_content_hash
    ):
        return StrategyProposalComparison(
            **common,
            result=StrategyProposalComparisonResult.NOT_COMPARABLE,
            reason_codes=(ComparisonReasonCode.TARGET_SHOT_IDENTITY_DIFFERS,),
        )
    differences: list[ComparisonReasonCode] = []
    if proposal.proposed_strategy is not planner_strategy:
        differences.append(ComparisonReasonCode.STRATEGY_MODE_DIFFERS)
        if (
            proposal.proposed_strategy is GenerationMode.REFERENCE_TO_VIDEO
            and (
                ProposalRationaleCode.IDENTITY_REFERENCE_PREFERRED
                in proposal.rationale_codes
            )
        ):
            differences.append(
                ComparisonReasonCode.AGENT_PREFERS_IDENTITY_REFERENCE
            )
    if proposal.continuity_preference is not planner_continuity:
        differences.append(ComparisonReasonCode.CONTINUITY_MODE_DIFFERS)
    if differences:
        return StrategyProposalComparison(
            **common,
            result=StrategyProposalComparisonResult.DIFFERENT,
            reason_codes=tuple(differences),
        )
    return StrategyProposalComparison(
        **common,
        result=StrategyProposalComparisonResult.MATCH,
        reason_codes=(ComparisonReasonCode.STRATEGY_MODE_MATCHES,),
    )
