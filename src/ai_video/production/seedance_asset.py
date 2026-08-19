"""Sealed imports for Ark materialized assets consumed by Seedance."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, StrictModel
from ai_video.production.video import (
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.VIDEO_REQUEST_INVALID, message, retryable=False)


class SeedanceAssetMaterializationReceipt(StrictModel):
    """Human-observed binding from one exact local asset to an active Ark asset."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"] = "1"
    provider_name: Literal["seedance"] = "seedance"
    provider_kind: Literal["volcengine_ark_seedance"] = "volcengine_ark_seedance"
    source_surface: Literal["ark_console"] = "ark_console"
    source_asset_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    source_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_mime_type: str = Field(pattern=r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$")
    source_size_bytes: int = Field(strict=True, gt=0)
    provider_asset_id: str = Field(pattern=r"^asset-[A-Za-z0-9._:-]{1,250}$")
    provider_asset_group_id: str = Field(pattern=r"^group-[A-Za-z0-9._:-]{1,250}$")
    materialization_scope: Literal["aigc", "trusted_real_person"]
    observed_status: Literal["Active"]
    observed_at: datetime
    observed_by: ActorIdentity
    provider_confirmation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rights_source_note: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_truthful_observation(self) -> "SeedanceAssetMaterializationReceipt":
        if self.observed_at.tzinfo is None:
            raise ValueError("Ark asset observation requires a timezone-aware timestamp")
        if self.observed_by.actor_kind != "human":
            raise ValueError("Ark console asset observation requires a human actor")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("Ark asset materialization receipt seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "SeedanceAssetMaterializationReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.setdefault("provider_name", "seedance")
        data.setdefault("provider_kind", "volcengine_ark_seedance")
        data.setdefault("source_surface", "ark_console")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(
                mode="json", exclude={"content_hash"}, warnings=False
            )
        )
        return cls.model_validate(data)


class SeedanceAssetReferenceResolver:
    """Resolve only exact local bindings backed by sealed active Ark receipts."""

    def __init__(
        self,
        receipts: tuple[SeedanceAssetMaterializationReceipt, ...],
        *,
        provider_confirmation_evidence: Mapping[str, bytes],
    ) -> None:
        by_source: dict[str, SeedanceAssetMaterializationReceipt] = {}
        provider_ids: set[str] = set()
        for receipt in receipts:
            if (
                receipt.source_asset_id in by_source
                or receipt.provider_asset_id in provider_ids
            ):
                raise _invalid("Seedance Ark asset materialization identities are ambiguous.")
            confirmation = provider_confirmation_evidence.get(receipt.provider_asset_id)
            if (
                not isinstance(confirmation, bytes)
                or hashlib.sha256(confirmation).hexdigest()
                != receipt.provider_confirmation_sha256
            ):
                raise _invalid("Seedance Ark asset confirmation evidence is not exact.")
            by_source[receipt.source_asset_id] = receipt
            provider_ids.add(receipt.provider_asset_id)
        self._by_source = by_source

    def __call__(
        self, binding: VideoImageReferenceBinding | VideoMediaReferenceBinding
    ) -> str:
        receipt = self._by_source.get(binding.asset_id)
        if receipt is None:
            raise _invalid("Seedance input has no active Ark asset materialization receipt.")
        if (
            receipt.source_asset_sha256 != binding.asset_sha256
            or receipt.source_mime_type != binding.mime_type
            or receipt.source_size_bytes != binding.size_bytes
        ):
            raise _invalid("Seedance Ark asset receipt does not match the exact local input.")
        return f"asset://{receipt.provider_asset_id}"
