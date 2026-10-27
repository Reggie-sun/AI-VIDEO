"""Immutable footage salvage observations and repair-candidate records.

These contracts retain review evidence and competing plans. They do not run
media tools, select a timeline, authorize generation, or accept a finished edit.
"""

from __future__ import annotations

import re
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel, ToolIdentity
from ai_video.production.hashing import canonical_sha256

SHA256 = r"^[0-9a-f]{64}$"


class FrameWindow(StrictModel):
    """Half-open source-frame range ``[start, end)``."""

    start: int = Field(strict=True, ge=0)
    end: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def _nonempty(self) -> "FrameWindow":
        if self.end <= self.start:
            raise ValueError("frame window must be nonempty")
        return self

    def contains(self, other: "FrameWindow") -> bool:
        return self.start <= other.start and other.end <= self.end

    def contains_frame(self, frame: int) -> bool:
        return self.start <= frame < self.end

    def overlaps(self, other: "FrameWindow") -> bool:
        return self.start < other.end and other.start < self.end


class SalvageOperation(str, Enum):
    KEEP = "KEEP"
    TRIM = "TRIM"
    REASSEMBLE = "REASSEMBLE"
    REUSE = "REUSE"
    LOCAL_REPAIR = "LOCAL_REPAIR"
    GENERATIVE_REPAIR = "GENERATIVE_REPAIR"
    GENERATE_INSERT = "GENERATE_INSERT"
    REGENERATE = "REGENERATE"
    REPLAN = "REPLAN"
    OMIT = "OMIT"


class QualityDimension(str, Enum):
    VISUAL_QUALITY = "visual_quality"
    ACTION_FIDELITY = "action_fidelity"
    NARRATIVE_COMPLETENESS = "narrative_completeness"
    TEMPORAL_CONTINUITY = "temporal_continuity"
    CROSS_SHOT_CONTINUITY = "cross_shot_continuity"
    PERFORMANCE_QUALITY = "performance_quality"
    EDITABILITY = "editability"


def _ordered_disjoint(windows: tuple[FrameWindow, ...], label: str) -> None:
    previous_end = -1
    for item in windows:
        if item.start < previous_end:
            raise ValueError(f"{label} windows must be ordered and disjoint")
        previous_end = item.end


def _unique(values: tuple[str, ...], label: str, *, nonempty: bool = False) -> None:
    if nonempty and not values:
        raise ValueError(f"{label} must not be empty")
    if any(not value.strip() for value in values):
        raise ValueError(f"{label} must contain nonblank IDs")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class PlaybackEvidence(StrictModel):
    """What was inspected, how, and against which exact source bytes."""

    source_sha256: str = Field(pattern=SHA256)
    size_bytes: int = Field(strict=True, gt=0)
    evaluator: ToolIdentity
    proof: Literal["analyzer", "human"]
    mode: Literal["sampled_frames", "continuous_playback"]
    reviewed_windows: tuple[FrameWindow, ...] = Field(min_length=1)
    viewing_speed_milli: int = Field(strict=True, gt=0)
    audio_reviewed: bool
    evidence_sha256: str = Field(pattern=SHA256)

    @model_validator(mode="after")
    def _ordered_windows(self) -> "PlaybackEvidence":
        _ordered_disjoint(self.reviewed_windows, "reviewed")
        return self


class TakeObservation(StrictModel):
    """One requirement observation; an omitted or uncertain claim stays explicit."""

    requirement_id: str = Field(min_length=1)
    dimension: QualityDimension
    verdict: Literal["PASS", "FAIL", "UNREVIEWED"]
    observation: str = Field(min_length=1)
    window: FrameWindow | None = None

    @model_validator(mode="after")
    def _nonblank(self) -> "TakeObservation":
        if not self.observation.strip() or not self.requirement_id.strip():
            raise ValueError("take observation identity and evidence must be nonblank")
        return self


class TakeDefect(StrictModel):
    defect_id: str = Field(min_length=1)
    kind: Literal[
        "surface", "motion", "action_completion", "causality", "identity",
        "space", "performance", "narrative", "audio",
    ]
    severity: Literal["minor", "major", "blocker"]
    extent: Literal["local", "persistent", "structural"]
    window: FrameWindow
    requirement_ids: tuple[str, ...] = Field(min_length=1)
    observation: str = Field(min_length=1)

    @model_validator(mode="after")
    def _nonblank(self) -> "TakeDefect":
        _unique(self.requirement_ids, "defect requirement IDs", nonempty=True)
        if not self.defect_id.strip() or not self.observation.strip():
            raise ValueError("take defect identity and observation must be nonblank")
        return self


class TakeAssessment(StrictModel):
    """Full-take observations, source windows, states, and repair boundaries."""

    scene_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    take_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=SHA256)
    size_bytes: int = Field(strict=True, gt=0)
    source_revision: str = Field(min_length=1)
    total_frames: int = Field(strict=True, gt=0)
    duration_seconds: Decimal = Field(gt=0)
    playback: PlaybackEvidence
    usable_windows: tuple[FrameWindow, ...] = ()
    protected_windows: tuple[FrameWindow, ...] = ()
    removable_windows: tuple[FrameWindow, ...] = ()
    observations: tuple[TakeObservation, ...] = Field(min_length=1)
    defects: tuple[TakeDefect, ...] = ()
    first_state: str = Field(min_length=1)
    last_state: str = Field(min_length=1)
    alternative_asset_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _consistent_source_review(self) -> "TakeAssessment":
        if (self.playback.source_sha256 != self.asset_sha256
                or self.playback.size_bytes != self.size_bytes):
            raise ValueError("playback identity must match the exact take asset bytes")
        if not self.source_revision.strip() or not self.scene_id.strip() or not self.shot_id.strip():
            raise ValueError("take and source identities must be nonblank")
        for name, windows in (
            ("usable", self.usable_windows),
            ("protected", self.protected_windows),
            ("removable", self.removable_windows),
        ):
            _ordered_disjoint(windows, name)
            if any(item.end > self.total_frames for item in windows):
                raise ValueError(f"{name} window must be within the source frame range")
        if any(a.overlaps(b) for a in self.protected_windows for b in self.removable_windows):
            raise ValueError("protected and removable windows cannot overlap")
        if any(item.end > self.total_frames for item in self.playback.reviewed_windows):
            raise ValueError("reviewed window must be within the source frame range")
        observed_keys = [
            (item.requirement_id, item.dimension, item.window.start if item.window else None,
             item.window.end if item.window else None)
            for item in self.observations
        ]
        if len(observed_keys) != len(set(observed_keys)):
            raise ValueError("take observations must be unique by requirement, dimension and window")
        if any(item.window is not None and item.window.end > self.total_frames for item in self.observations):
            raise ValueError("observation window must be within the source frame range")
        if len({item.defect_id for item in self.defects}) != len(self.defects):
            raise ValueError("take defect IDs must be unique")
        observation_requirements = {item.requirement_id for item in self.observations}
        if any(not set(item.requirement_ids) <= observation_requirements for item in self.defects):
            raise ValueError("defects must reference observed requirements")
        if any(item.window.end > self.total_frames for item in self.defects):
            raise ValueError("defect window must be within the source frame range")
        _unique(self.alternative_asset_ids, "alternative asset IDs")
        if not self.first_state.strip() or not self.last_state.strip():
            raise ValueError("first and last states must be explicit")
        if not self.duration_seconds.is_finite():
            raise ValueError("take duration must be finite")
        return self


class CostEstimate(StrictModel):
    """A bounded estimate in a declared unit, or an explicit unknown value."""

    lower: Decimal | None
    upper: Decimal | None
    basis: str = Field(min_length=1)
    unit: str = Field(min_length=1)

    @model_validator(mode="after")
    def _bounded_and_finite(self) -> "CostEstimate":
        if (self.lower is None) != (self.upper is None):
            raise ValueError("cost estimate must provide both bounds or both bounds must be unknown")
        if not self.basis.strip() or not self.unit.strip():
            raise ValueError("cost estimate basis and unit must be nonblank")
        if self.lower is not None and self.upper is not None:
            if not self.lower.is_finite() or not self.upper.is_finite():
                raise ValueError("cost estimate bounds must be finite")
            if self.lower < 0 or self.upper < 0:
                raise ValueError("cost estimate bounds cannot be negative")
            if self.lower > self.upper:
                raise ValueError("cost estimate lower cost cannot exceed upper cost")
        return self


class CandidateRisk(StrictModel):
    """Separate uncertainty dimensions; values must not be collapsed into a score."""

    narrative: Literal["low", "medium", "high", "unknown"]
    identity: Literal["low", "medium", "high", "unknown"]
    continuity: Literal["low", "medium", "high", "unknown"]
    performance: Literal["low", "medium", "high", "unknown"]
    approved_content: Literal["low", "medium", "high", "unknown"]
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def _basis(self) -> "CandidateRisk":
        if not self.basis.strip():
            raise ValueError("risk assessment needs its evidence basis")
        return self


class CandidateRepairPlan(StrictModel):
    """Proposed operations and tradeoffs; feasibility is not media acceptance."""

    plan_key: str = Field(pattern=SHA256)
    operations: tuple[SalvageOperation, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    defect_ids: tuple[str, ...] = ()
    viability: Literal["feasible", "infeasible", "unreviewed"]
    rejection_reasons: tuple[str, ...] = ()
    evidence_sha256s: tuple[str, ...] = ()
    provider_cost: CostEstimate
    local_render_cost: CostEstimate
    elapsed_time: CostEstimate
    risks: CandidateRisk
    affected_shot_ids: tuple[str, ...] = Field(min_length=1)
    adjacent_shot_ids: tuple[str, ...] = ()
    protected_requirement_ids: tuple[str, ...] = Field(min_length=1)
    alternative_expression: str | None = None

    @model_validator(mode="after")
    def _candidate_evidence(self) -> "CandidateRepairPlan":
        _unique(tuple(item.value for item in self.operations), "candidate operations", nonempty=True)
        _unique(self.defect_ids, "candidate defect IDs")
        _unique(self.rejection_reasons, "candidate rejection reasons")
        _unique(self.evidence_sha256s, "candidate evidence hashes")
        if any(re.fullmatch(SHA256, item) is None for item in self.evidence_sha256s):
            raise ValueError("candidate evidence hashes must be SHA-256 values")
        _unique(self.affected_shot_ids, "affected shot IDs", nonempty=True)
        _unique(self.adjacent_shot_ids, "adjacent shot IDs")
        _unique(self.protected_requirement_ids, "protected requirement IDs", nonempty=True)
        if not self.rationale.strip():
            raise ValueError("candidate rationale must be nonblank")
        if set(self.affected_shot_ids) & set(self.adjacent_shot_ids):
            raise ValueError("affected and adjacent Shot IDs must be distinct")
        if self.viability == "feasible" and not self.evidence_sha256s:
            raise ValueError("feasible candidate requires evidence references")
        if self.viability == "infeasible" and not self.rejection_reasons:
            raise ValueError("infeasible candidate requires a rejection reason")
        if any(not reason.strip() for reason in self.rejection_reasons):
            raise ValueError("candidate rejection reasons must be nonblank")
        if any(not value.strip() for value in (*self.affected_shot_ids,
                                               *self.adjacent_shot_ids,
                                               *self.protected_requirement_ids)):
            raise ValueError("candidate IDs must be nonblank")
        if self.alternative_expression is not None and not self.alternative_expression.strip():
            raise ValueError("alternative expression must be nonblank when present")
        return self

    @property
    def uses_provider_generation(self) -> bool:
        return bool({SalvageOperation.GENERATIVE_REPAIR, SalvageOperation.GENERATE_INSERT,
                     SalvageOperation.REGENERATE} & set(self.operations))


class SalvageReview(StrictModel):
    """Immutable review of take evidence and viable repair alternatives."""

    contract_version: Literal["footage-salvage/1"] = "footage-salvage/1"
    task_id: str = Field(min_length=1)
    parent_shot_id: str = Field(min_length=1)
    parent_shot_content_hash: str = Field(pattern=SHA256)
    acceptance_profile_hash: str = Field(pattern=SHA256)
    genre: str = Field(min_length=1)
    scene_intent: str = Field(min_length=1)
    required_events: tuple[str, ...] = Field(min_length=1)
    transition_requirement_ids: tuple[str, ...] = Field(min_length=1)
    scene_requirement_ids: tuple[str, ...] = Field(min_length=1)
    takes: tuple[TakeAssessment, ...] = Field(min_length=1)
    candidate_plans: tuple[CandidateRepairPlan, ...] = ()
    repeated_failure_limit: int = Field(default=3, strict=True, ge=2)

    @model_validator(mode="after")
    def _review_references(self) -> "SalvageReview":
        for name, values in (
            ("required event IDs", self.required_events),
            ("transition requirement IDs", self.transition_requirement_ids),
            ("scene requirement IDs", self.scene_requirement_ids),
        ):
            _unique(values, name, nonempty=True)
        if any(not value.strip() for value in (self.task_id, self.parent_shot_id,
                                               self.genre, self.scene_intent)):
            raise ValueError("salvage review context must be nonblank")
        if len({item.take_id for item in self.takes}) != len(self.takes):
            raise ValueError("take IDs must be unique")
        if len({item.asset_id for item in self.takes}) != len(self.takes):
            raise ValueError("take assets must be unique")
        parent_takes = tuple(item for item in self.takes if item.shot_id == self.parent_shot_id)
        if not parent_takes:
            raise ValueError("salvage review must contain a take for its parent Shot")
        if any(not set(self.required_events) <= {row.requirement_id for row in item.observations}
               for item in parent_takes):
            raise ValueError("every required event must have an observation for each parent take")
        if len({item.plan_key for item in self.candidate_plans}) != len(self.candidate_plans):
            raise ValueError("plan keys must be unique")
        defects = {item.defect_id for take in self.takes for item in take.defects}
        if sum(len(item.defects) for item in self.takes) != len(defects):
            raise ValueError("defect IDs must be unique across the review")
        if any(not set(plan.defect_ids) <= defects for plan in self.candidate_plans):
            raise ValueError("candidate references an unknown defect")
        if any(self.parent_shot_id not in plan.affected_shot_ids for plan in self.candidate_plans):
            raise ValueError("candidate affected shots must include the parent Shot")
        return self

    @property
    def review_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))
