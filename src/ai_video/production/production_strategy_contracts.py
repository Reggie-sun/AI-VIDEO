"""Immutable authoring and handoff data; selection belongs to Planning."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import ArtifactReference, QaPolicyPointer, StrictModel
from ai_video.production.composition_contracts import (
    AudioTrackSpec, CaptionTrackBinding, FixedTransform,
)
from ai_video.production.hashing import canonical_sha256

SHA256 = r"^[0-9a-f]{64}$"


class ProductionOperation(str, Enum):
    GENERATE_FULL_SHOT = "GENERATE_FULL_SHOT"
    EXISTING_ASSET_REUSE = "EXISTING_ASSET_REUSE"
    SPLIT_SHOT = "SPLIT_SHOT"
    CUTAWAY = "CUTAWAY"
    REACTION_SHOT = "REACTION_SHOT"
    INSERT_SHOT = "INSERT_SHOT"
    REFRAME = "REFRAME"
    TRIM_EXISTING = "TRIM_EXISTING"
    EDIT_EXISTING_VIDEO = "EDIT_EXISTING_VIDEO"
    STILL_IMAGE_WITH_MOTION = "STILL_IMAGE_WITH_MOTION"
    REPLACE_AUDIO = "REPLACE_AUDIO"
    DUB_DIALOGUE = "DUB_DIALOGUE"
    EXTEND_VIDEO = "EXTEND_VIDEO"
    CHANGE_REFERENCE_STRATEGY = "CHANGE_REFERENCE_STRATEGY"
    CHANGE_PROVIDER = "CHANGE_PROVIDER"
    SIMPLIFY_ACTION = "SIMPLIFY_ACTION"
    COMPOSITE_MULTIPLE_ASSETS = "COMPOSITE_MULTIPLE_ASSETS"
    MASK_COMPOSITE = "MASK_COMPOSITE"
    TRACKING = "TRACKING"
    LIP_SYNC = "LIP_SYNC"


class ProductionSourceOption(StrictModel):
    """An authored possible use, not a claim that its content is qualified."""

    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=SHA256)
    role: str = Field(min_length=1)
    timebase: Literal["frames", "samples", "still"]
    start: int = Field(default=0, strict=True, ge=0)
    duration: int = Field(strict=True, gt=0)
    evidence_ids: tuple[str, ...] = ()
    requirement_ids: tuple[str, ...] = ()
    transform: FixedTransform = Field(default_factory=FixedTransform)
    z_index: int = 0
    opacity_milli: int = Field(default=1000, ge=0, le=1000)


class ProductionUnit(StrictModel):
    component_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    duration_frames: int = Field(strict=True, gt=0)
    requirement_ids: tuple[str, ...] = Field(min_length=1)
    motion_required: bool = False
    dialogue: str = ""
    narration: str = ""
    source_options: tuple[ProductionSourceOption, ...] = ()
    additional_sources: tuple[ProductionSourceOption, ...] = ()
    required_operations: tuple[ProductionOperation, ...] = ()
    first_frame_asset_id: str | None = None

    @model_validator(mode="after")
    def _unique_requirements(self):
        if len(set(self.requirement_ids)) != len(self.requirement_ids):
            raise ValueError("component requirements must be unique")
        for source in (*self.source_options, *self.additional_sources):
            if source.timebase == "samples":
                raise ValueError("visual component cannot use a sample window")
            if source.duration != self.duration_frames:
                raise ValueError("visual source duration must match the presentation unit")
            if not set(source.requirement_ids) <= set(self.requirement_ids):
                raise ValueError("source requirements must belong to the component")
        return self


class ProductionAudioUse(StrictModel):
    component_id: str = Field(min_length=1)
    requirement_ids: tuple[str, ...] = Field(min_length=1)
    source: ProductionSourceOption
    track: AudioTrackSpec

    @model_validator(mode="after")
    def _exact_audio_use(self):
        if (self.source.timebase != "samples"
                or self.track.asset_id != self.source.asset_id
                or self.track.trim_start_sample != self.source.start
                or self.track.trim_duration_samples != self.source.duration):
            raise ValueError("audio use must bind the exact track sample window")
        return self


class ProductionCoverage(StrictModel):
    coverage_id: str = Field(min_length=1)
    allocation_id: str = Field(min_length=1)
    units: tuple[ProductionUnit, ...] = Field(min_length=1, max_length=32)
    audio: tuple[ProductionAudioUse, ...] = ()
    captions: tuple[CaptionTrackBinding, ...] = ()

    @model_validator(mode="after")
    def _unique_units(self):
        ids = tuple(u.component_id for u in self.units) + tuple(a.component_id for a in self.audio)
        shot_ids = tuple(u.shot_id for u in self.units)
        if len(set(ids)) != len(ids) or len(set(shot_ids)) != len(shot_ids):
            raise ValueError("component and presentation Shot identities must be unique")
        if any(a.track.shot_id is not None and a.track.shot_id not in shot_ids for a in self.audio):
            raise ValueError("audio track must refer to a coverage Shot")
        if any(c.shot_id is not None and c.shot_id not in shot_ids for c in self.captions):
            raise ValueError("caption must refer to a coverage Shot")
        return self


class ProductionIntent(StrictModel):
    contract_version: Literal["production-intent/1"] = "production-intent/1"
    task_id: str = Field(min_length=1)
    allowed_operations: tuple[ProductionOperation, ...] = Field(min_length=1)
    protected_requirement_ids: tuple[str, ...] = Field(min_length=1)
    assembly_requirement_ids: tuple[str, ...] = ()
    single_take: bool = False
    co_visible_required: bool = False
    coverage_options: tuple[ProductionCoverage, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def _coverage_constraints(self):
        ids = tuple(c.coverage_id for c in self.coverage_options)
        if len(set(ids)) != len(ids):
            raise ValueError("coverage identities must be unique")
        for coverage in self.coverage_options:
            if len(coverage.units) > 1 and (self.single_take or self.co_visible_required):
                raise ValueError("single-take or co-visible intent cannot split visible Shots")
        if not set(self.assembly_requirement_ids) <= set(self.protected_requirement_ids):
            raise ValueError("assembly obligations must be protected requirements")
        return self


class ProductionComponentLineage(StrictModel):
    """Reopenable creative parent, not a mutable strategy lifecycle."""

    contract_version: Literal["production-component/1"] = "production-component/1"
    parent: ArtifactReference
    origin_project_hash: str = Field(pattern=SHA256)
    parent_shot_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    coverage_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    allocation_hash: str = Field(pattern=SHA256)
    allocation_policy: QaPolicyPointer | None = None
    decision_hash: str = Field(pattern=SHA256)
    operation: ProductionOperation
    source: ProductionSourceOption | None = None

    @model_validator(mode="after")
    def _parent_path(self):
        path = self.parent.path
        if path.is_absolute() or ".." in path.parts or not path.name:
            raise ValueError("production parent path must be a contained artifact")
        return self


class ProductionSelectedUnit(StrictModel):
    component: ProductionUnit
    operation: ProductionOperation
    source: ProductionSourceOption | None = None


class ProductionShotMixin(StrictModel):
    production_intent: ProductionIntent | None = None
    production_lineage: ProductionComponentLineage | None = None

    @model_serializer(mode="wrap")
    def _serialize_production_contract(self, handler):
        data = handler(self)
        for field in ("production_intent", "production_lineage"):
            if getattr(self, field) is None:
                data.pop(field, None)
        return data


class ProductionCandidate(StrictModel):
    coverage: ProductionCoverage
    allocation_hash: str = Field(pattern=SHA256)
    units: tuple[ProductionSelectedUnit, ...]
    operations: tuple[ProductionOperation, ...]
    blockers: tuple[str, ...] = ()
    new_generation_count: int = Field(ge=0)

    @property
    def candidate_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class ProductionStrategyDecision(StrictModel):
    input_hash: str = Field(pattern=SHA256)
    parent_shot_id: str
    parent_shot_content_hash: str = Field(pattern=SHA256)
    task_id: str
    candidates: tuple[ProductionCandidate, ...]
    selected: ProductionCandidate | None = None
    disposition: Literal["selected", "needs_authoring_revision", "evidence_required",
        "capability_gap", "unresolved_choice", "blocked_scope", "recovery_required"]
    reasons: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _selection(self):
        if (self.disposition == "selected") != (self.selected is not None):
            raise ValueError("selected disposition and candidate must agree")
        if self.selected is not None and (self.selected not in self.candidates or self.selected.blockers):
            raise ValueError("selected candidate must be a feasible evaluated candidate")
        return self

    @property
    def decision_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))
