"""Pure typed Ecommerce post-media acceptance contracts and adjudication."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationError, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import QaVerdict


MEASUREMENT_CONTRACT_VERSION = "ecommerce-media-acceptance/1"

QINGYAN_SHOT_REQUIREMENT_IDS = (
    "shot.identity.main_character",
    "shot.identity.elder",
    "shot.cast.allowed_count",
    "shot.product.presence_window",
    "shot.product.packaging_identity",
    "shot.product.label_fidelity",
    "shot.product.interaction",
    "shot.dialogue.verbatim",
    "shot.dialogue.speaker_binding",
    "shot.motion.required",
    "shot.camera.intent",
    "shot.continuity.in_out",
)

QINGYAN_WHOLE_AD_REQUIREMENT_IDS = (
    "ad.hook.first_second",
    "ad.arc.problem_recommendation_use_payoff",
    "ad.cast.elder_interaction",
    "ad.product.first_appearance",
    "ad.product.exposure_balance",
    "ad.product.packaging_consistency",
    "ad.audio.coverage",
    "ad.audio.product_recommendation",
    "ad.audio.voice_continuity",
    "ad.cta.brand_closure",
    "ad.continuity.character",
    "ad.motion.required_windows",
    "ad.edit.pacing",
    "ad.copy.claim_compliance",
    "ad.delivery.duration_aspect",
)


class EcommerceAcceptanceProfile(StrictModel):
    schema_version: Literal["ecommerce-acceptance-profile/1"] = (
        "ecommerce-acceptance-profile/1"
    )
    domain_id: Literal["ecommerce"] = "ecommerce"
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    measurement_contract_version: Literal[
        "ecommerce-media-acceptance/1"
    ] = MEASUREMENT_CONTRACT_VERSION
    shot_requirement_ids: tuple[str, ...] = Field(min_length=1)
    required_requirement_ids: tuple[str, ...] = Field(min_length=1)
    product_first_appearance_start_milliseconds: int = Field(strict=True, ge=0)
    product_first_appearance_end_milliseconds: int = Field(strict=True, gt=0)
    end_card_max_duration_milliseconds: int = Field(strict=True, gt=0)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_profile(self) -> "EcommerceAcceptanceProfile":
        if (
            self.product_first_appearance_end_milliseconds
            <= self.product_first_appearance_start_milliseconds
        ):
            raise ValueError("Ecommerce product appearance window must be non-empty")
        for label, requirement_ids, prefix in (
            ("Shot", self.shot_requirement_ids, "shot."),
            ("whole-ad", self.required_requirement_ids, "ad."),
        ):
            if any(not item.startswith(prefix) for item in requirement_ids):
                raise ValueError(f"Ecommerce {label} requirement IDs have wrong scope")
            if len(set(requirement_ids)) != len(requirement_ids):
                raise ValueError(f"Ecommerce {label} requirement IDs must be unique")
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Ecommerce acceptance profile content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceAcceptanceProfile":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


class EcommerceRequirementFinding(StrictModel):
    requirement_id: str = Field(min_length=1)
    verdict: QaVerdict
    rationale: str = Field(min_length=1)


class EcommerceAcceptanceEvidencePayload(StrictModel):
    schema_version: Literal["ecommerce-acceptance-evidence/1"] = (
        "ecommerce-acceptance-evidence/1"
    )
    domain_id: Literal["ecommerce"] = "ecommerce"
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    measurement_contract_version: Literal[
        "ecommerce-media-acceptance/1"
    ] = MEASUREMENT_CONTRACT_VERSION
    findings: tuple[EcommerceRequirementFinding, ...] = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_evidence_seal(self) -> "EcommerceAcceptanceEvidencePayload":
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Ecommerce acceptance evidence content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceAcceptanceEvidencePayload":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


def create_qingyan_ecommerce_acceptance_profile() -> EcommerceAcceptanceProfile:
    return EcommerceAcceptanceProfile.create(
        profile_id="qingyan-ecommerce",
        profile_version="1",
        shot_requirement_ids=QINGYAN_SHOT_REQUIREMENT_IDS,
        required_requirement_ids=QINGYAN_WHOLE_AD_REQUIREMENT_IDS,
        product_first_appearance_start_milliseconds=3_000,
        product_first_appearance_end_milliseconds=6_000,
        end_card_max_duration_milliseconds=2_000,
    )


def adjudicate_ecommerce_acceptance(
    policy: DomainAcceptancePolicy,
    evidence: EcommerceAcceptanceEvidencePayload,
) -> QaVerdict:
    """Fail closed unless exact sealed profile and required findings agree."""
    try:
        selected_policy = DomainAcceptancePolicy.model_validate(
            policy.model_dump(mode="json")
        )
        selected_profile = EcommerceAcceptanceProfile.model_validate(
            selected_policy.profile_payload
        )
        measured = EcommerceAcceptanceEvidencePayload.model_validate(
            evidence.model_dump(mode="json")
        )
    except ValidationError:
        return QaVerdict.NOT_EVALUATED

    if selected_policy.domain_id != "ecommerce":
        return QaVerdict.NOT_EVALUATED
    if (
        selected_policy.profile_id,
        selected_policy.profile_version,
        selected_policy.profile_content_hash,
        selected_policy.measurement_contract_version,
    ) != (
        selected_profile.profile_id,
        selected_profile.profile_version,
        selected_profile.content_hash,
        selected_profile.measurement_contract_version,
    ):
        return QaVerdict.NOT_EVALUATED
    if (
        measured.domain_id,
        measured.profile_id,
        measured.profile_version,
        measured.profile_content_hash,
        measured.measurement_contract_version,
    ) != (
        selected_policy.domain_id,
        selected_policy.profile_id,
        selected_policy.profile_version,
        selected_policy.profile_content_hash,
        selected_policy.measurement_contract_version,
    ):
        return QaVerdict.NOT_EVALUATED

    finding_ids = tuple(item.requirement_id for item in measured.findings)
    if finding_ids != selected_policy.required_requirement_ids:
        return QaVerdict.NOT_EVALUATED
    if any(item.verdict is QaVerdict.FAIL for item in measured.findings):
        return QaVerdict.FAIL
    if any(item.verdict is not QaVerdict.PASS for item in measured.findings):
        return QaVerdict.NOT_EVALUATED
    return QaVerdict.PASS
