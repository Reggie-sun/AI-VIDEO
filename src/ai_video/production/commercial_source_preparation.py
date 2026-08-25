from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.commercial_visual_review import CommercialSourceReviewReceipt
from ai_video.production.commercial_reference import ProductReferenceSet
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image_import import CommercialImageImportReceipt
from ai_video.production.models import QaVerdict, StrictModel


class CommercialCreativeReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(strict=True, ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class CommercialSourceAcquisitionKind(str, Enum):
    REGISTERED_IMPORT = "registered_import"
    P7_GENERATION = "p7_generation"


class CommercialSourcePreparationRequest(StrictModel):
    schema_version: Literal["commercial-source-preparation-request/1"] = "commercial-source-preparation-request/1"
    request_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    acquisition_kind: CommercialSourceAcquisitionKind
    expected_output_role: Literal["commercial_interaction_keyframe"] = "commercial_interaction_keyframe"
    ad_creative_plan_id: str = Field(min_length=1)
    ad_creative_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_projection_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_project_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_registry_revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_registry_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_dependency_graph_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set_id: str = Field(min_length=1)
    product_reference_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set: ProductReferenceSet
    product_reference_asset_ids: tuple[str, ...] = Field(min_length=1)
    product_reference_asset_hashes: tuple[str, ...] = Field(min_length=1)
    character_references: tuple[CommercialCreativeReference, ...] = Field(min_length=1)
    scene_references: tuple[CommercialCreativeReference, ...] = Field(min_length=1)
    character_reference_ids: tuple[str, ...] = Field(min_length=1)
    scene_reference_ids: tuple[str, ...] = Field(min_length=1)
    wardrobe_requirement_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    accessory_requirement_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("product_reference_asset_hashes")
    @classmethod
    def _canonical_product_asset_hashes(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        if any(
            len(item) != 64
            or any(character not in "0123456789abcdef" for character in item)
            for item in value
        ):
            raise ValueError("Product reference asset hashes must be lowercase SHA-256")
        if len(value) != len(set(value)):
            raise ValueError("Product reference asset hashes must be unique")
        return tuple(sorted(value))

    @model_validator(mode="after")
    def _validate_fingerprint(self) -> "CommercialSourcePreparationRequest":
        if len(self.product_reference_asset_ids) != len(
            set(self.product_reference_asset_ids)
        ):
            raise ValueError("Product reference asset IDs must be unique")
        if len({item.artifact_id for item in self.character_references}) != len(
            self.character_references
        ) or len({item.artifact_id for item in self.scene_references}) != len(
            self.scene_references
        ):
            raise ValueError("Commercial creative references must be unique")
        if self.product_reference_asset_ids != tuple(
            sorted(self.product_reference_asset_ids)
        ):
            raise ValueError("Product reference asset IDs must be canonically ordered")
        if (
            self.product_reference_set_id != self.product_reference_set.artifact_id
            or self.product_reference_set_hash != self.product_reference_set.content_hash
            or self.product_reference_asset_ids
            != tuple(sorted(item.asset_id for item in self.product_reference_set.assets))
            or self.product_reference_asset_hashes
            != tuple(
                sorted(item.asset_sha256 for item in self.product_reference_set.assets)
            )
            or self.character_reference_ids
            != tuple(item.artifact_id for item in self.character_references)
            or self.scene_reference_ids
            != tuple(item.artifact_id for item in self.scene_references)
        ):
            raise ValueError(
                "Commercial source request ProductReferenceSet binding is not exact"
            )
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"request_fingerprint"})
        )
        if self.request_fingerprint != expected:
            raise ValueError("Commercial source request fingerprint does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "CommercialSourcePreparationRequest":
        data = dict(values)
        data.setdefault("schema_version", "commercial-source-preparation-request/1")
        data.setdefault("expected_output_role", "commercial_interaction_keyframe")
        reference_set = data.get("product_reference_set")
        if isinstance(reference_set, dict):
            reference_set = ProductReferenceSet.model_validate(reference_set)
            data["product_reference_set"] = reference_set
        if isinstance(reference_set, ProductReferenceSet):
            data.setdefault("product_reference_set_id", reference_set.artifact_id)
            data.setdefault("product_reference_set_hash", reference_set.content_hash)
            data.setdefault(
                "product_reference_asset_ids",
                tuple(item.asset_id for item in reference_set.assets),
            )
            data.setdefault(
                "product_reference_asset_hashes",
                tuple(item.asset_sha256 for item in reference_set.assets),
            )
        for field in ("character_references", "scene_references"):
            if field in data:
                references = tuple(
                    item
                    if isinstance(item, CommercialCreativeReference)
                    else CommercialCreativeReference.model_validate(item)
                    for item in data[field]  # type: ignore[union-attr]
                )
                data[field] = tuple(
                    sorted(references, key=lambda item: item.artifact_id)
                )
        if "character_references" in data:
            data.setdefault(
                "character_reference_ids",
                tuple(item.artifact_id for item in data["character_references"]),  # type: ignore[union-attr]
            )
        if "scene_references" in data:
            data.setdefault(
                "scene_reference_ids",
                tuple(item.artifact_id for item in data["scene_references"]),  # type: ignore[union-attr]
            )
        if "product_reference_asset_ids" in data:
            data["product_reference_asset_ids"] = tuple(
                sorted(data["product_reference_asset_ids"])  # type: ignore[arg-type]
            )
        if "product_reference_asset_hashes" in data:
            data["product_reference_asset_hashes"] = tuple(
                sorted(data["product_reference_asset_hashes"])  # type: ignore[arg-type]
            )
        data.pop("request_fingerprint", None)
        provisional = cls.model_construct(**data, request_fingerprint="0" * 64)
        data["request_fingerprint"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"request_fingerprint"})
        )
        return cls.model_validate(data)


class CommercialSourceCandidate(StrictModel):
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    import_receipt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    import_receipt: CommercialImageImportReceipt

    @model_validator(mode="after")
    def _validate_import_receipt(self) -> "CommercialSourceCandidate":
        receipt = self.import_receipt
        if (
            receipt.target_kind != "commercial_interaction_keyframe"
            or self.import_receipt_hash != receipt.content_hash
            or self.asset_id != receipt.output_asset_id
            or self.asset_sha256 != receipt.output_sha256
            or self.target_shot_id != receipt.target_shot_id
            or self.target_shot_content_hash != receipt.target_shot_content_hash
        ):
            raise ValueError(
                "Commercial source candidate import receipt is not exact"
            )
        return self


class ApprovedCommercialSourceBinding(StrictModel):
    schema_version: Literal["approved-commercial-source-binding/1"] = "approved-commercial-source-binding/1"
    approval_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    ad_creative_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_projection_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    keyframe_asset_id: str = Field(min_length=1)
    keyframe_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set_id: str = Field(min_length=1)
    product_reference_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set: ProductReferenceSet
    product_source_asset_hashes: tuple[str, ...] = Field(min_length=1)
    character_references: tuple[CommercialCreativeReference, ...] = Field(min_length=1)
    scene_references: tuple[CommercialCreativeReference, ...] = Field(min_length=1)
    character_reference_ids: tuple[str, ...] = Field(min_length=1)
    scene_reference_ids: tuple[str, ...] = Field(min_length=1)
    wardrobe_requirement_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    accessory_requirement_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_receipt_id: str = Field(min_length=1)
    review_receipt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("product_source_asset_hashes")
    @classmethod
    def _canonical_product_source_hashes(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        if any(
            len(item) != 64
            or any(character not in "0123456789abcdef" for character in item)
            for item in value
        ):
            raise ValueError("Product source asset hashes must be lowercase SHA-256")
        if len(value) != len(set(value)):
            raise ValueError("Product source asset hashes must be unique")
        return tuple(sorted(value))

    @model_validator(mode="after")
    def _validate_seal(self) -> "ApprovedCommercialSourceBinding":
        if (
            self.product_reference_set_id != self.product_reference_set.artifact_id
            or self.product_reference_set_hash != self.product_reference_set.content_hash
            or self.product_source_asset_hashes
            != tuple(
                sorted(item.asset_sha256 for item in self.product_reference_set.assets)
            )
            or self.character_reference_ids
            != tuple(item.artifact_id for item in self.character_references)
            or self.scene_reference_ids
            != tuple(item.artifact_id for item in self.scene_references)
        ):
            raise ValueError("Approved commercial source references are not exact")
        expected = canonical_sha256(self.model_dump(mode="json", exclude={"content_hash"}))
        if self.content_hash != expected:
            raise ValueError("Approved commercial source content_hash does not match")
        return self

    @classmethod
    def create(
        cls,
        *,
        candidate: CommercialSourceCandidate,
        review_receipt: CommercialSourceReviewReceipt,
        **values: object,
    ) -> "ApprovedCommercialSourceBinding":
        if review_receipt.verdict is not QaVerdict.PASS:
            raise ValueError("Approved commercial source requires exact semantic PASS")
        if (
            review_receipt.source_request_hash != candidate.request_hash
            or review_receipt.target_shot_id != candidate.target_shot_id
            or review_receipt.target_shot_content_hash != candidate.target_shot_content_hash
            or review_receipt.candidate_asset_id != candidate.asset_id
            or review_receipt.candidate_sha256 != candidate.asset_sha256
        ):
            raise ValueError("Commercial source review receipt does not bind exact candidate")
        data = dict(values)
        reference_set = data.get("product_reference_set")
        if isinstance(reference_set, dict):
            reference_set = ProductReferenceSet.model_validate(reference_set)
            data["product_reference_set"] = reference_set
        if isinstance(reference_set, ProductReferenceSet):
            data.setdefault("product_reference_set_id", reference_set.artifact_id)
            data.setdefault("product_reference_set_hash", reference_set.content_hash)
            data.setdefault(
                "product_source_asset_hashes",
                tuple(item.asset_sha256 for item in reference_set.assets),
            )
        for field in ("character_references", "scene_references"):
            if field in data:
                references = tuple(
                    item
                    if isinstance(item, CommercialCreativeReference)
                    else CommercialCreativeReference.model_validate(item)
                    for item in data[field]  # type: ignore[union-attr]
                )
                data[field] = tuple(
                    sorted(references, key=lambda item: item.artifact_id)
                )
        if "character_references" in data:
            data.setdefault(
                "character_reference_ids",
                tuple(item.artifact_id for item in data["character_references"]),  # type: ignore[union-attr]
            )
        if "scene_references" in data:
            data.setdefault(
                "scene_reference_ids",
                tuple(item.artifact_id for item in data["scene_references"]),  # type: ignore[union-attr]
            )
        if "product_source_asset_hashes" in data:
            data["product_source_asset_hashes"] = tuple(
                sorted(set(data["product_source_asset_hashes"]))  # type: ignore[arg-type]
            )
        data.update(
            {
                "schema_version": "approved-commercial-source-binding/1",
                "source_request_hash": candidate.request_hash,
                "target_shot_id": candidate.target_shot_id,
                "target_shot_content_hash": candidate.target_shot_content_hash,
                "keyframe_asset_id": candidate.asset_id,
                "keyframe_sha256": candidate.asset_sha256,
                "review_receipt_id": review_receipt.receipt_id,
                "review_receipt_hash": review_receipt.content_hash,
            }
        )
        if data.get("product_reference_set_hash") != review_receipt.product_reference_set_hash:
            raise ValueError("Commercial source approval ProductReferenceSet is inconsistent")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)


class CommercialSourcePreparationCoordinator:
    def prepare(self, request: CommercialSourcePreparationRequest) -> object | None:
        checked = CommercialSourcePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        if checked.acquisition_kind is CommercialSourceAcquisitionKind.P7_GENERATION:
            raise AiVideoError(
                ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
                "Commercial source P7 generation is not implemented; only exact registered import is supported.",
                retryable=False,
            )
        return None
