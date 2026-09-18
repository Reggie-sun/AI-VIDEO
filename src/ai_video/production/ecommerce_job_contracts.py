"""Immutable contracts for the Ecommerce Production Job application layer."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_video.errors import ErrorCode
from ai_video.production.ad_creative_types import (
    AdBeatRole,
    AdCreativePlanProposal,
    ProductPresentation,
)
from ai_video.production.commercial_graphics import (
    GraphicRole,
    GraphicSafeAreaInsets,
    GraphicTreatment,
)
from ai_video.production.models import (
    Character,
    CompositionDirective,
    ProductionBrief,
    Scene,
    Shot,
    Story,
    Storyboard,
    VisualStrategy,
)


_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_ZERO_HASH = "0" * 64


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def _canonical_identity(model: BaseModel, *, identity_field: str) -> str:
    payload = model.model_dump(mode="json", exclude={identity_field})
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class EcommerceDeliveryProfile(_StrictModel):
    schema_version: Literal["ecommerce-delivery-profile/1"] = (
        "ecommerce-delivery-profile/1"
    )
    profile_id: str = Field(pattern=_SHA256_PATTERN)
    aspect_ratio: Literal["9:16"]
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    fps: int = Field(strict=True, gt=0)
    codec_profile: str = Field(min_length=1)
    audio_sample_rate_hz: int = Field(strict=True, gt=0)
    platform: str = Field(min_length=1)
    placement: str = Field(min_length=1)
    constraints: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_profile(self) -> "EcommerceDeliveryProfile":
        if self.width * 16 != self.height * 9:
            raise ValueError("delivery geometry must exactly match 9:16")
        if self.profile_id != _canonical_identity(self, identity_field="profile_id"):
            raise ValueError("delivery profile identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceDeliveryProfile":
        provisional = cls.model_construct(**values, profile_id=_ZERO_HASH)
        return cls.model_validate(
            {
                **values,
                "profile_id": _canonical_identity(
                    provisional, identity_field="profile_id"
                ),
            }
        )


class EcommerceTypographyToken(_StrictModel):
    token_id: str = Field(min_length=1)
    font_family: Literal["sans-serif"]
    font_size_px: int = Field(strict=True, gt=0, le=512)
    font_weight: int = Field(strict=True, ge=100, le=900, multiple_of=100)
    letter_spacing_px: int = Field(strict=True, ge=0, le=16)
    text_color: str = Field(pattern=r"^#[0-9A-Fa-f]{8}$|^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{8}$|^#[0-9A-Fa-f]{6}$",
    )


class EcommerceGraphicRoleBinding(_StrictModel):
    role: GraphicRole
    typography_token_id: str = Field(min_length=1)


class EcommerceVisualSystemProfile(_StrictModel):
    schema_version: Literal["ecommerce-visual-system-profile/1"] = (
        "ecommerce-visual-system-profile/1"
    )
    profile_id: str = Field(pattern=_SHA256_PATTERN)
    brand_token_ids: tuple[str, ...] = Field(min_length=1)
    safe_area: GraphicSafeAreaInsets
    typography_tokens: tuple[EcommerceTypographyToken, ...]
    role_bindings: tuple[EcommerceGraphicRoleBinding, ...]

    @model_validator(mode="after")
    def _validate_profile(self) -> "EcommerceVisualSystemProfile":
        brand_ids = tuple(self.brand_token_ids)
        token_ids = tuple(item.token_id for item in self.typography_tokens)
        roles = tuple(item.role for item in self.role_bindings)
        if len(brand_ids) != len(set(brand_ids)):
            raise ValueError("brand token IDs must be unique")
        if len(token_ids) != len(set(token_ids)):
            raise ValueError("typography token IDs must be unique")
        if len(roles) != len(set(roles)):
            raise ValueError("graphic role bindings must be unique")
        if any(
            item.typography_token_id not in set(token_ids)
            for item in self.role_bindings
        ):
            raise ValueError("graphic role references an unknown typography token")
        if self.profile_id != _canonical_identity(self, identity_field="profile_id"):
            raise ValueError("visual system profile identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceVisualSystemProfile":
        provisional = cls.model_construct(**values, profile_id=_ZERO_HASH)
        return cls.model_validate(
            {
                **values,
                "profile_id": _canonical_identity(
                    provisional, identity_field="profile_id"
                ),
            }
        )


class EcommerceLayoutScene(_StrictModel):
    scene_id: str = Field(min_length=1)
    source_set_id: str | None = Field(default=None, min_length=1)
    location: str = Field(min_length=1)
    time: str = Field(min_length=1)
    mood: str = Field(min_length=1)
    participant_ids: tuple[str, ...]
    continuity_constraints: tuple[str, ...]


class EcommerceLayoutShot(_StrictModel):
    shot_id: str = Field(min_length=1)
    scene_id: str = Field(min_length=1)
    character_ids: tuple[str, ...]
    visual_strategy: VisualStrategy
    continuity_constraints: tuple[str, ...]
    composition_directives: tuple[CompositionDirective, ...] = ()


class EcommerceBeatRoleBinding(_StrictModel):
    beat_id: str = Field(min_length=1)
    role: AdBeatRole


class EcommerceLayoutPlan(_StrictModel):
    schema_version: Literal["ecommerce-layout-plan/1"] = "ecommerce-layout-plan/1"
    layout_plan_id: str = Field(pattern=_SHA256_PATTERN)
    source_package_id: str = Field(pattern=_SHA256_PATTERN)
    delivery_profile_id: str = Field(pattern=_SHA256_PATTERN)
    visual_system_profile_id: str = Field(pattern=_SHA256_PATTERN)
    scenes: tuple[EcommerceLayoutScene, ...] = Field(min_length=1)
    shots: tuple[EcommerceLayoutShot, ...] = Field(min_length=1)
    beat_roles: tuple[EcommerceBeatRoleBinding, ...]
    graphic_treatments: tuple[GraphicTreatment, ...]
    product_presentations: tuple[ProductPresentation, ...]
    protagonist_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_plan(self) -> "EcommerceLayoutPlan":
        scene_ids = tuple(item.scene_id for item in self.scenes)
        shot_ids = tuple(item.shot_id for item in self.shots)
        beat_ids = tuple(item.beat_id for item in self.beat_roles)
        graphic_ids = tuple(item.graphic_id for item in self.graphic_treatments)
        presentation_ids = tuple(
            item.presentation_id for item in self.product_presentations
        )
        for label, values in (
            ("scene", scene_ids),
            ("Shot", shot_ids),
            ("beat", beat_ids),
            ("graphic", graphic_ids),
            ("product presentation", presentation_ids),
            ("protagonist", self.protagonist_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        scene_set = set(scene_ids)
        if any(item.scene_id not in scene_set for item in self.shots):
            raise ValueError("layout Shot references an unknown scene")
        if self.layout_plan_id != _canonical_identity(
            self, identity_field="layout_plan_id"
        ):
            raise ValueError("layout plan identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceLayoutPlan":
        provisional = cls.model_construct(**values, layout_plan_id=_ZERO_HASH)
        return cls.model_validate(
            {
                **values,
                "layout_plan_id": _canonical_identity(
                    provisional, identity_field="layout_plan_id"
                ),
            }
        )


class EcommerceProductionCompileProfile(_StrictModel):
    schema_version: Literal["ecommerce-production-compile-profile/1"] = (
        "ecommerce-production-compile-profile/1"
    )
    profile_id: str = Field(pattern=_SHA256_PATTERN)
    delivery_profile_id: str = Field(pattern=_SHA256_PATTERN)
    visual_system_profile_id: str = Field(pattern=_SHA256_PATTERN)
    layout_plan_id: str = Field(pattern=_SHA256_PATTERN)
    requirement_resolutions: tuple["EcommerceRequirementResolution", ...] = ()

    @model_validator(mode="after")
    def _validate_profile(self) -> "EcommerceProductionCompileProfile":
        requirement_ids = tuple(
            item.requirement_id for item in self.requirement_resolutions
        )
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("compile requirement resolution IDs must be unique")
        if self.profile_id != _canonical_identity(self, identity_field="profile_id"):
            raise ValueError("compile profile identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceProductionCompileProfile":
        provisional = cls.model_construct(**values, profile_id=_ZERO_HASH)
        return cls.model_validate(
            {
                **values,
                "profile_id": _canonical_identity(
                    provisional, identity_field="profile_id"
                ),
            }
        )


class EcommerceRequirementResolution(_StrictModel):
    requirement_id: str = Field(min_length=1)
    capability: Literal["advertising_copy_graphics"]
    resolution_kind: Literal["EXACT_GRAPHIC_LAYOUT"]
    evidence_ids: tuple[str, ...] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def _validate_evidence(self) -> "EcommerceRequirementResolution":
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("requirement resolution evidence IDs must be unique")
        return self


class EcommerceArtifactProposals(_StrictModel):
    brief: ProductionBrief
    story: Story
    characters: tuple[Character, ...]
    scenes: tuple[Scene, ...] = Field(min_length=1)
    storyboard: Storyboard
    shots: tuple[Shot, ...] = Field(min_length=1)


class EcommerceAssetRequirement(_StrictModel):
    asset_id: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    rights_status: Literal["CONFIRMED", "RESTRICTED", "UNKNOWN"]
    expected_sha256: str | None = Field(default=None, pattern=_SHA256_PATTERN)
    expected_size_bytes: int | None = Field(default=None, strict=True, ge=0)

    @model_validator(mode="after")
    def _validate_exact_identity(self) -> "EcommerceAssetRequirement":
        if (self.expected_sha256 is None) != (self.expected_size_bytes is None):
            raise ValueError("asset expected hash and size must be all-or-none")
        return self


class EcommerceTruthSource(_StrictModel):
    source_id: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    rights_status: Literal["CONFIRMED", "RESTRICTED", "UNKNOWN"]


class EcommerceProductFact(_StrictModel):
    fact_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    source_ids: tuple[str, ...] = Field(min_length=1)


class EcommerceAllowedClaim(_StrictModel):
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    fact_ids: tuple[str, ...] = Field(min_length=1)
    source_ids: tuple[str, ...] = Field(min_length=1)


class EcommerceProhibitedClaim(_StrictModel):
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class EcommerceProductTruth(_StrictModel):
    product_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    sources: tuple[EcommerceTruthSource, ...] = Field(min_length=1)
    facts: tuple[EcommerceProductFact, ...] = Field(min_length=1)
    allowed_claims: tuple[EcommerceAllowedClaim, ...] = Field(min_length=1)
    prohibited_claims: tuple[EcommerceProhibitedClaim, ...]
    required_disclaimers: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_truth_graph(self) -> "EcommerceProductTruth":
        source_ids = tuple(item.source_id for item in self.sources)
        fact_ids = tuple(item.fact_id for item in self.facts)
        allowed_ids = tuple(item.claim_id for item in self.allowed_claims)
        prohibited_ids = tuple(item.claim_id for item in self.prohibited_claims)
        for label, values in (
            ("truth source", source_ids),
            ("product fact", fact_ids),
            ("allowed claim", allowed_ids),
            ("prohibited claim", prohibited_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        if set(allowed_ids).intersection(prohibited_ids):
            raise ValueError("claim cannot be both allowed and prohibited")
        if any(not set(item.source_ids).issubset(source_ids) for item in self.facts):
            raise ValueError("product fact references an unknown truth source")
        if any(
            not set(item.fact_ids).issubset(fact_ids)
            or not set(item.source_ids).issubset(source_ids)
            for item in self.allowed_claims
        ):
            raise ValueError("allowed claim references unknown truth evidence")
        return self


class EcommerceRuntimeRequirement(_StrictModel):
    requirement_id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    classification: Literal[
        "SUPPORTED_CURRENTLY",
        "REQUIRES_SOURCE_GENERATION_STRATEGY",
        "REQUIRES_RUNTIME_CAPABILITY",
        "REQUIRES_HUMAN_DECISION",
        "BLOCKED_BY_TRUTH_OR_RIGHTS",
    ]
    rationale: str = Field(min_length=1)


class EcommerceAcceptanceRequirement(_StrictModel):
    requirement_id: str = Field(min_length=1)
    scope: Literal["SHOT", "FINAL_OUTPUT"]
    subject_id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class EcommerceUnsupportedGap(_StrictModel):
    gap_id: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    requirement_ids: tuple[str, ...] = Field(min_length=1)
    blocker_code: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class EcommerceProductionHandoff(_StrictModel):
    schema_version: Literal["ecommerce-production-handoff/1"] = (
        "ecommerce-production-handoff/1"
    )
    handoff_id: str = Field(pattern=_SHA256_PATTERN)
    source_package_id: str = Field(pattern=_SHA256_PATTERN)
    source_input_hash: str = Field(pattern=_SHA256_PATTERN)
    delivery_profile: EcommerceDeliveryProfile
    visual_system_profile: EcommerceVisualSystemProfile
    layout_plan: EcommerceLayoutPlan
    compile_profile: EcommerceProductionCompileProfile
    product_truth: EcommerceProductTruth
    artifact_proposals: EcommerceArtifactProposals
    ad_creative_plan_proposal: AdCreativePlanProposal
    asset_requirements: tuple[EcommerceAssetRequirement, ...]
    runtime_requirements: tuple[EcommerceRuntimeRequirement, ...]
    acceptance_requirements: tuple[EcommerceAcceptanceRequirement, ...] = Field(
        min_length=1
    )
    unsupported_gaps: tuple[EcommerceUnsupportedGap, ...]

    @model_validator(mode="after")
    def _validate_handoff(self) -> "EcommerceProductionHandoff":
        if self.layout_plan.source_package_id != self.source_package_id:
            raise ValueError("layout plan does not bind the source package")
        if self.layout_plan.delivery_profile_id != self.delivery_profile.profile_id:
            raise ValueError("layout plan does not bind the delivery profile")
        if (
            self.layout_plan.visual_system_profile_id
            != self.visual_system_profile.profile_id
        ):
            raise ValueError("layout plan does not bind the visual system profile")
        if (
            self.compile_profile.delivery_profile_id
            != self.delivery_profile.profile_id
            or self.compile_profile.visual_system_profile_id
            != self.visual_system_profile.profile_id
            or self.compile_profile.layout_plan_id != self.layout_plan.layout_plan_id
        ):
            raise ValueError("compile profile does not bind the exact visual contracts")
        runtime_requirement_ids = tuple(
            item.requirement_id for item in self.runtime_requirements
        )
        if len(runtime_requirement_ids) != len(set(runtime_requirement_ids)):
            raise ValueError("runtime requirement IDs must be unique")
        asset_ids = tuple(item.asset_id for item in self.asset_requirements)
        acceptance_ids = tuple(
            item.requirement_id for item in self.acceptance_requirements
        )
        gap_ids = tuple(item.gap_id for item in self.unsupported_gaps)
        for label, values in (
            ("asset requirement", asset_ids),
            ("acceptance requirement", acceptance_ids),
            ("unsupported gap", gap_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        resolved_ids = {
            item.requirement_id for item in self.compile_profile.requirement_resolutions
        }
        if not resolved_ids.issubset(set(runtime_requirement_ids)):
            raise ValueError("compile profile resolves an unknown runtime requirement")
        unresolved_ids = {
            requirement_id
            for item in self.unsupported_gaps
            for requirement_id in item.requirement_ids
        }
        if not unresolved_ids.issubset(set(runtime_requirement_ids)):
            raise ValueError("unsupported gap references an unknown runtime requirement")
        if resolved_ids.intersection(unresolved_ids):
            raise ValueError("resolved requirement cannot remain an unsupported gap")
        if self.handoff_id != _canonical_identity(self, identity_field="handoff_id"):
            raise ValueError("ecommerce production handoff identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceProductionHandoff":
        provisional = cls.model_construct(**values, handoff_id=_ZERO_HASH)
        return cls.model_validate(
            {
                **values,
                "handoff_id": _canonical_identity(
                    provisional, identity_field="handoff_id"
                ),
            }
        )


class EcommerceJobNextAction(str, Enum):
    BOOTSTRAP_PROJECT = "BOOTSTRAP_PROJECT"
    RECONCILE_PROJECT = "RECONCILE_PROJECT"
    PREPARE_REFERENCES = "PREPARE_REFERENCES"
    GENERATE_SHOT = "GENERATE_SHOT"
    REPAIR_SHOT_EVIDENCE = "REPAIR_SHOT_EVIDENCE"
    REPAIR_SHOT_MEDIA = "REPAIR_SHOT_MEDIA"
    RECOVER_UNKNOWN_OUTCOME = "RECOVER_UNKNOWN_OUTCOME"
    PREPARE_COMPOSITION = "PREPARE_COMPOSITION"
    RENDER_FINAL = "RENDER_FINAL"
    REVIEW_FINAL = "REVIEW_FINAL"
    PACKAGE_DELIVERY = "PACKAGE_DELIVERY"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"


class EcommerceJobBlocker(_StrictModel):
    blocker_code: str = Field(min_length=1)
    error_code: ErrorCode | None = None
    stage: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    failure_classification: str = Field(min_length=1)
    diagnosis_id: str | None = Field(default=None, min_length=1)
    evidence_pointers: tuple[str, ...]
    retryable: bool
    required_owner: str = Field(min_length=1)
    required_action: str = Field(min_length=1)
    outcome_known: bool


class EcommerceProductionJobRequest(_StrictModel):
    schema_version: Literal["ecommerce-production-job-request/1"]
    job_id: str = Field(min_length=1)
    project_root: Path
    handoff_id: str = Field(pattern=_SHA256_PATTERN)
    expected_project_id: str = Field(min_length=1)
    execution_policy_id: str = Field(pattern=_SHA256_PATTERN)
    delivery_profile_id: str = Field(pattern=_SHA256_PATTERN)
    max_new_generation_attempts: int = Field(strict=True, ge=0)
    max_repairs_per_shot: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def _validate_root(self) -> "EcommerceProductionJobRequest":
        if not self.project_root.is_absolute():
            raise ValueError("project_root must be absolute")
        return self


class EcommerceProductionJobProjection(_StrictModel):
    schema_version: Literal["ecommerce-production-job-projection/1"]
    job_id: str = Field(min_length=1)
    handoff_id: str = Field(pattern=_SHA256_PATTERN)
    expected_project_id: str = Field(min_length=1)
    next_action: EcommerceJobNextAction
    manifest_revision: int | None = Field(default=None, ge=1)
    next_shot_id: str | None = Field(default=None, min_length=1)
    blocker: EcommerceJobBlocker | None = None

    @model_validator(mode="after")
    def _validate_blocker(self) -> "EcommerceProductionJobProjection":
        if (self.next_action is EcommerceJobNextAction.BLOCKED) != (
            self.blocker is not None
        ):
            raise ValueError("BLOCKED projection and blocker must be paired")
        return self


__all__ = [
    "EcommerceAcceptanceRequirement",
    "EcommerceAllowedClaim",
    "EcommerceArtifactProposals",
    "EcommerceAssetRequirement",
    "EcommerceBeatRoleBinding",
    "EcommerceDeliveryProfile",
    "EcommerceGraphicRoleBinding",
    "EcommerceJobBlocker",
    "EcommerceJobNextAction",
    "EcommerceLayoutPlan",
    "EcommerceLayoutScene",
    "EcommerceLayoutShot",
    "EcommerceProductionCompileProfile",
    "EcommerceProductionHandoff",
    "EcommerceProductionJobProjection",
    "EcommerceProductionJobRequest",
    "EcommerceProductFact",
    "EcommerceProductTruth",
    "EcommerceProhibitedClaim",
    "EcommerceRequirementResolution",
    "EcommerceRuntimeRequirement",
    "EcommerceTypographyToken",
    "EcommerceTruthSource",
    "EcommerceUnsupportedGap",
    "EcommerceVisualSystemProfile",
]
