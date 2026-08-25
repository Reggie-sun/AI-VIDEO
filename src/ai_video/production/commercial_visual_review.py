from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    QaPolicy,
    QaVerdict,
    StrictModel,
    ToolIdentity,
)
from ai_video.production.review import adjudicate_layer


class CommercialVisualDimension(str, Enum):
    CHARACTER_IDENTITY = "character_identity"
    HAIRSTYLE = "hairstyle"
    WARDROBE = "wardrobe"
    ACCESSORY = "accessory"
    PRODUCT_PRESENCE = "product_presence"
    PACKAGING_IDENTITY = "packaging_identity"
    BOTTLE_SILHOUETTE = "bottle_silhouette"
    DOMINANT_COLOR = "dominant_color"
    CAP_COLOR = "cap_color"
    LOGO_LABEL_IDENTITY = "logo_label_identity"
    LABEL_TEXT_ZONE_INTEGRITY = "label_text_zone_integrity"
    PRODUCT_SCALE = "product_scale"
    PERSPECTIVE_MATCH = "perspective_match"
    LIGHTING_MATCH = "lighting_match"
    HAND_OBJECT_CONTACT = "hand_object_contact"
    OCCLUSION_PLAUSIBILITY = "occlusion_plausibility"
    INTERACTION_PLAUSIBILITY = "interaction_plausibility"
    FLAT_OVERLAY_ABSENT = "flat_overlay_absent"


class CommercialMatchStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_EVALUATED = "not_evaluated"


class CommercialFailureType(str, Enum):
    INVALID_PRODUCT_REFERENCE = "invalid_product_reference"
    PRODUCT_FIDELITY_MISMATCH = "product_fidelity_mismatch"
    CHARACTER_IDENTITY_MISMATCH = "character_identity_mismatch"
    WARDROBE_ACCESSORY_MISMATCH = "wardrobe_accessory_mismatch"
    PHYSICAL_INTERACTION_MISMATCH = "physical_interaction_mismatch"
    POST_GENERATION_ACTION_MISMATCH = "post_generation_action_mismatch"
    COMMERCIAL_TYPOGRAPHY = "commercial_typography"
    AUDIO = "audio"
    PACING = "pacing"


class CommercialVisualMeasurement(StrictModel):
    dimension: CommercialVisualDimension
    status: CommercialMatchStatus
    expected: str = Field(min_length=1)
    observed: str = Field(min_length=1)
    confidence_milli: int = Field(strict=True, ge=0, le=1000)
    rationale: str = Field(min_length=1)


class CommercialVisualEvidence(StrictModel):
    schema_version: Literal["commercial-visual-evidence/1"] = "commercial-visual-evidence/1"
    evidence_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_asset_id: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority_kind: Literal["human", "calibrated_automatic", "automatic"]
    tool_identity: ToolIdentity
    measurements: tuple[CommercialVisualMeasurement, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_complete_dimensions_and_seal(self) -> "CommercialVisualEvidence":
        dimensions = tuple(item.dimension for item in self.measurements)
        if dimensions != tuple(CommercialVisualDimension):
            raise ValueError("Commercial visual evidence must evaluate every dimension in canonical order")
        expected = canonical_sha256(self.model_dump(mode="json", exclude={"content_hash"}))
        if self.content_hash != expected:
            raise ValueError("Commercial visual evidence content_hash does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "CommercialVisualEvidence":
        data = dict(values)
        data.setdefault("schema_version", "commercial-visual-evidence/1")
        measurements = tuple(data.get("measurements", ()))
        data["measurements"] = tuple(
            sorted(measurements, key=lambda item: tuple(CommercialVisualDimension).index(item.dimension))
        )
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)


class CommercialFailureClassification(StrictModel):
    schema_version: Literal["commercial-failure-classification/1"] = "commercial-failure-classification/1"
    failure_type: CommercialFailureType
    root_owner: str = Field(min_length=1)
    root_node_ids: tuple[str, ...] = Field(min_length=1)
    proposed_boundary_node_ids: tuple[str, ...] = Field(min_length=1)


class CommercialSourceReviewReceipt(StrictModel):
    receipt_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_asset_id: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_id: str = Field(min_length=1)
    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority: ToolIdentity
    verdict: QaVerdict
    target_kind: Literal["source_image"] = "source_image"
    failure_classification: CommercialFailureClassification | None = None

    @model_validator(mode="after")
    def _validate_receipt_seal(self) -> "CommercialSourceReviewReceipt":
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"receipt_id", "content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("Commercial source review receipt content_hash does not match")
        if self.receipt_id != f"commercial-source-review-{expected}":
            raise ValueError("Commercial source review receipt ID does not match content")
        if (
            self.verdict is QaVerdict.FAIL
        ) != (self.failure_classification is not None):
            raise ValueError("Commercial source FAIL must carry one failure classification")
        return self

    @classmethod
    def create(cls, **values: object) -> "CommercialSourceReviewReceipt":
        data = dict(values)
        data.setdefault("target_kind", "source_image")
        data["verdict"] = QaVerdict(data["verdict"])
        if isinstance(data.get("failure_classification"), dict):
            data["failure_classification"] = CommercialFailureClassification.model_validate(
                data["failure_classification"]
            )
        data.pop("receipt_id", None)
        data.pop("content_hash", None)
        provisional = cls.model_construct(
            **data,
            receipt_id="commercial-source-review-unsealed",
            content_hash="0" * 64,
        )
        digest = canonical_sha256(
            provisional.model_dump(
                mode="json", exclude={"receipt_id", "content_hash"}
            )
        )
        data["receipt_id"] = f"commercial-source-review-{digest}"
        data["content_hash"] = digest
        return cls.model_validate(data)


_PRODUCT_DIMENSIONS = {
    CommercialVisualDimension.PRODUCT_PRESENCE,
    CommercialVisualDimension.PACKAGING_IDENTITY,
    CommercialVisualDimension.BOTTLE_SILHOUETTE,
    CommercialVisualDimension.DOMINANT_COLOR,
    CommercialVisualDimension.CAP_COLOR,
    CommercialVisualDimension.LOGO_LABEL_IDENTITY,
    CommercialVisualDimension.LABEL_TEXT_ZONE_INTEGRITY,
    CommercialVisualDimension.PRODUCT_SCALE,
}
_CHARACTER_DIMENSIONS = {
    CommercialVisualDimension.CHARACTER_IDENTITY,
    CommercialVisualDimension.HAIRSTYLE,
}
_WARDROBE_DIMENSIONS = {
    CommercialVisualDimension.WARDROBE,
    CommercialVisualDimension.ACCESSORY,
}


def _failure_for_dimension(dimension: CommercialVisualDimension) -> CommercialFailureType:
    if dimension in _PRODUCT_DIMENSIONS:
        return CommercialFailureType.PRODUCT_FIDELITY_MISMATCH
    if dimension in _CHARACTER_DIMENSIONS:
        return CommercialFailureType.CHARACTER_IDENTITY_MISMATCH
    if dimension in _WARDROBE_DIMENSIONS:
        return CommercialFailureType.WARDROBE_ACCESSORY_MISMATCH
    return CommercialFailureType.PHYSICAL_INTERACTION_MISMATCH


def adjudicate_commercial_visual_evidence(
    evidence: CommercialVisualEvidence,
    *,
    policy: QaPolicy,
) -> CommercialSourceReviewReceipt:
    checked = CommercialVisualEvidence.model_validate(evidence.model_dump(mode="python"))
    selected_policy = QaPolicy.model_validate(policy.model_dump(mode="python"))
    if not verify_artifact_hash(selected_policy):
        raise ValueError("Commercial source review requires a sealed QA policy")
    verdict = QaVerdict.NOT_EVALUATED
    failure: CommercialFailureClassification | None = None
    if (
        checked.policy_hash != selected_policy.content_hash
        or checked.tool_identity not in selected_policy.semantic_authorities
    ):
        verdict = QaVerdict.NOT_EVALUATED
    else:
        mismatch = next(
            (item for item in checked.measurements if item.status is CommercialMatchStatus.MISMATCH),
            None,
        )
        if mismatch is not None:
            failure_type = _failure_for_dimension(mismatch.dimension)
            failure = CommercialFailureClassification(
                failure_type=failure_type,
                root_owner="commercial_source_materialization",
                root_node_ids=(checked.candidate_asset_id,),
                proposed_boundary_node_ids=(checked.candidate_asset_id, checked.target_shot_id),
            )
        incomplete = any(
            item.status is CommercialMatchStatus.NOT_EVALUATED
            for item in checked.measurements
        )
        strength = {
            "human": EvidenceStrength.HUMAN,
            "calibrated_automatic": EvidenceStrength.EXPLICIT_EVALUATOR,
            "automatic": EvidenceStrength.MEASURED,
        }[checked.authority_kind]
        result = (
            "fail"
            if mismatch is not None
            else "unknown"
            if incomplete or checked.authority_kind == "automatic"
            else "pass"
        )
        verdict = adjudicate_layer(
            QaLayer.SEMANTIC,
            ({"strength": strength.value, "result": result},),
        )
        if verdict is not QaVerdict.FAIL:
            failure = None
    receipt_payload = {
        "source_request_hash": checked.source_request_hash,
        "target_shot_id": checked.target_shot_id,
        "target_shot_content_hash": checked.target_shot_content_hash,
        "candidate_asset_id": checked.candidate_asset_id,
        "candidate_sha256": checked.candidate_sha256,
        "product_reference_set_hash": checked.product_reference_set_hash,
        "policy_hash": selected_policy.content_hash,
        "evidence_id": checked.evidence_id,
        "evidence_hash": checked.content_hash,
        "authority": checked.tool_identity,
        "verdict": verdict,
        "target_kind": "source_image",
        "failure_classification": failure,
    }
    return CommercialSourceReviewReceipt.create(**receipt_payload)


def classify_commercial_failure(
    *,
    failure_type: CommercialFailureType,
    product_reference_node_id: str,
    source_node_id: str,
    shot_node_id: str,
    composition_node_id: str | None = None,
    audio_node_id: str | None = None,
    timeline_node_id: str | None = None,
) -> CommercialFailureClassification:
    if failure_type is CommercialFailureType.INVALID_PRODUCT_REFERENCE:
        owner = "product_reference_set"
        roots = (product_reference_node_id,)
        boundary = (product_reference_node_id, source_node_id, shot_node_id)
    elif failure_type in {
        CommercialFailureType.PRODUCT_FIDELITY_MISMATCH,
        CommercialFailureType.CHARACTER_IDENTITY_MISMATCH,
        CommercialFailureType.WARDROBE_ACCESSORY_MISMATCH,
        CommercialFailureType.PHYSICAL_INTERACTION_MISMATCH,
    }:
        owner = "commercial_source_materialization"
        roots = (source_node_id,)
        boundary = (source_node_id, shot_node_id)
    elif failure_type is CommercialFailureType.POST_GENERATION_ACTION_MISMATCH:
        owner = "generated_shot"
        roots = boundary = (shot_node_id,)
    elif failure_type is CommercialFailureType.COMMERCIAL_TYPOGRAPHY:
        if composition_node_id is None:
            raise ValueError("Commercial typography classification requires composition node")
        owner = "composition"
        roots = boundary = (composition_node_id,)
    elif failure_type is CommercialFailureType.AUDIO:
        if audio_node_id is None:
            raise ValueError("Audio classification requires audio node")
        owner = "p4_audio"
        roots = boundary = (audio_node_id,)
    else:
        if timeline_node_id is None or composition_node_id is None:
            raise ValueError("Pacing classification requires timeline and composition nodes")
        owner = "resolved_timeline"
        roots = (timeline_node_id,)
        boundary = (timeline_node_id, composition_node_id)
    return CommercialFailureClassification(
        failure_type=failure_type,
        root_owner=owner,
        root_node_ids=roots,
        proposed_boundary_node_ids=boundary,
    )
