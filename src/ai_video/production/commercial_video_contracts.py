"""Commercial identities embedded in provider-neutral video requests."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SHA256 = r"^[0-9a-f]{64}$"


class GeneratedCommercialShotBinding(StrictModel):
    """Pre-resolve commercial identities sealed into one generated Shot request."""

    schema_version: Literal["generated-commercial-shot-binding/1"] = (
        "generated-commercial-shot-binding/1"
    )
    ad_creative_plan_id: str = Field(pattern=_SAFE_ID.pattern)
    ad_creative_plan_hash: str = Field(pattern=_SHA256)
    commercial_execution_projection_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID.pattern)
    profile_content_hash: str = Field(pattern=_SHA256)
    applicable_requirement_ids: tuple[str, ...] = Field(min_length=1)
    product_truth_hashes: tuple[str, ...] = ()
    product_reference_hashes: tuple[str, ...] = ()
    source_approval_hashes: tuple[str, ...] = ()
    expected_actor_ids: tuple[str, ...] = Field(min_length=1)
    output_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    content_hash: str = Field(pattern=_SHA256)

    @field_validator(
        "product_truth_hashes",
        "product_reference_hashes",
        "source_approval_hashes",
    )
    @classmethod
    def _canonical_hashes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(re.fullmatch(_SHA256, item) is None for item in value):
            raise ValueError("Commercial binding hashes must be lowercase SHA-256")
        if value != tuple(sorted(set(value))):
            raise ValueError("Commercial binding hashes must be unique and ordered")
        return value

    @model_validator(mode="after")
    def _validate_binding(self) -> "GeneratedCommercialShotBinding":
        if (
            len(set(self.applicable_requirement_ids))
            != len(self.applicable_requirement_ids)
            or any(not item.startswith("shot.") for item in self.applicable_requirement_ids)
        ):
            raise ValueError("Commercial binding requirement IDs must be unique Shot IDs")
        if len(set(self.expected_actor_ids)) != len(self.expected_actor_ids):
            raise ValueError("Commercial binding actor IDs must be unique")
        has_product_requirement = any(
            item.startswith("shot.product.")
            for item in self.applicable_requirement_ids
        )
        if has_product_requirement and not (
            self.product_truth_hashes and self.product_reference_hashes
        ):
            raise ValueError("Commercial product binding requires exact product truth")
        if (
            "shot.product.interaction" in self.applicable_requirement_ids
            and not self.source_approval_hashes
        ):
            raise ValueError("Commercial product interaction requires source approval")
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Commercial binding content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "GeneratedCommercialShotBinding":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


class CommercialVideoBindingMixin:
    """Attach one optional commercial binding without changing legacy JSON."""

    commercial_binding: GeneratedCommercialShotBinding | None = None

    @model_validator(mode="after")
    def _validate_commercial_video_target(self):
        binding = self.commercial_binding
        if binding is not None and (
            binding.target_shot_id
            != getattr(self, "target_shot_id", binding.target_shot_id)
            or binding.output_asset_id != self.output_asset_id
        ):
            raise ValueError("commercial binding does not match request target")
        return self

    @model_serializer(mode="wrap")
    def _serialize_optional_commercial_binding(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.commercial_binding is None:
            data.pop("commercial_binding", None)
        return data
