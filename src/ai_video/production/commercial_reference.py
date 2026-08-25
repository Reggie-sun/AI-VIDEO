from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetRegistrySnapshot, AssetType, StrictModel


ProductReferenceView = Literal["front", "label", "side", "back", "detail", "usage"]
ProductReferencePurpose = Literal["product_truth", "packaging", "label", "silhouette"]


class ProductReferenceAssetBinding(StrictModel):
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    view: ProductReferenceView
    purpose: ProductReferencePurpose


class ProductReferenceSet(StrictModel):
    schema_version: Literal["product-reference-set/1"] = "product-reference-set/1"
    artifact_id: str = Field(min_length=1)
    revision: int = Field(strict=True, ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_id: str = Field(min_length=1)
    sku_id: str = Field(min_length=1)
    formal_name: str = Field(min_length=1)
    truth_reference_ids: tuple[str, ...] = Field(min_length=1)
    registry_revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    registry_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    assets: tuple[ProductReferenceAssetBinding, ...] = Field(min_length=1)
    packaging_form: str = Field(min_length=1)
    bottle_silhouette: str = Field(min_length=1)
    dominant_color: str = Field(min_length=1)
    cap_color: str = Field(min_length=1)
    logo_label_identity: str = Field(min_length=1)
    protected_text_zones: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_identity_and_seal(self) -> "ProductReferenceSet":
        asset_ids = tuple(item.asset_id for item in self.assets)
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("Product reference set contains duplicate asset IDs")
        if len(self.truth_reference_ids) != len(set(self.truth_reference_ids)):
            raise ValueError("Product reference truth IDs must be unique")
        if len(self.protected_text_zones) != len(set(self.protected_text_zones)):
            raise ValueError("Product protected text zones must be unique")
        views = {item.view for item in self.assets}
        if not {"front", "label"}.issubset(views):
            raise ValueError("Product reference set requires front and label views")
        canonical = tuple(
            sorted(self.assets, key=lambda item: (item.purpose, item.view, item.asset_id))
        )
        if self.assets != canonical:
            raise ValueError("Product reference assets must be canonically ordered")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("Product reference set content_hash does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "ProductReferenceSet":
        data = dict(values)
        data.setdefault("schema_version", "product-reference-set/1")
        assets = tuple(
            item
            if isinstance(item, ProductReferenceAssetBinding)
            else ProductReferenceAssetBinding.model_validate(item)
            for item in data.get("assets", ())
        )
        data["assets"] = tuple(
            sorted(assets, key=lambda item: (item.purpose, item.view, item.asset_id))
        )
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)


def validate_product_reference_set_against_registry(
    reference_set: ProductReferenceSet,
    registry: AssetRegistrySnapshot,
    *,
    require_registry_identity: bool = True,
) -> None:
    checked = ProductReferenceSet.model_validate(reference_set.model_dump(mode="python"))
    if require_registry_identity and (
        checked.registry_revision_id != registry.revision_id
        or checked.registry_content_hash != registry.content_hash
    ):
        raise ValueError("Product reference set Registry identity is stale")
    records = {item.asset_id: item for item in registry.assets}
    for binding in checked.assets:
        record = records.get(binding.asset_id)
        if (
            record is None
            or record.asset_type is not AssetType.IMAGE
            or record.sha256 != binding.asset_sha256
            or record.mime_type != binding.mime_type
            or record.width != binding.width
            or record.height != binding.height
        ):
            raise ValueError("Product reference asset is missing, tampered, or unregistered")
