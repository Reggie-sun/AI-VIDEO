"""Immutable Review / Repair contracts; no execution or lifecycle ownership."""

from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


class FinalOutputRequirement(StrictModel):
    requirement_id: str = Field(min_length=1)
    observable: str = Field(min_length=1)
    proof: Literal["human", "evaluator"]


class FinalOutputContract(StrictModel):
    """A versioned user goal and its complete applicable viewing requirements."""

    goal_id: str = Field(min_length=1)
    goal_version: str = Field(min_length=1)
    user_goal: str = Field(min_length=1)
    requirements: tuple[FinalOutputRequirement, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_requirements(self):
        ids = [item.requirement_id for item in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("final-output requirements must be unique")
        return self

    @property
    def contract_hash(self):
        return canonical_sha256(self.model_dump(mode="json"))


class KnownRequirementViolation(StrictModel):
    requirement_id: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(min_length=1)


class RepairPredictionMixin:
    """Recorded known violations are fatal, regardless of operation or purpose."""

    known_requirement_violations: tuple[KnownRequirementViolation, ...] = ()

    @model_serializer(mode="wrap")
    def _serialize_predictions(self, handler):
        result = handler(self)
        if not self.known_requirement_violations:
            result.pop("known_requirement_violations", None)
        return result


class RepairBaselineMixin:
    # Forward reference is resolved by the canonical models module. Empty only
    # preserves historical bytes; new approval/execution requires exact pointers.
    baseline_review_receipts: tuple["ReviewReceiptPointer", ...] = ()

    @model_serializer(mode="wrap")
    def _serialize_baseline_reviews(self, handler):
        result = handler(self)
        if not self.baseline_review_receipts:
            result.pop("baseline_review_receipts", None)
        return result


class RepairAction(RepairPredictionMixin, StrictModel):
    kind: str = Field(min_length=1)
    parameters_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class RepairOutcomeMixin:
    # Historical outcomes only claimed success. Failure is now explicit, so a
    # later repair cannot rewrite this attempt's failed final output as a PASS.
    verdict: Literal["pass", "fail"] = "pass"

    @model_serializer(mode="wrap")
    def _serialize_outcome_verdict(self, handler):
        result = handler(self)
        if self.verdict == "pass":
            result.pop("verdict", None)
        return result
