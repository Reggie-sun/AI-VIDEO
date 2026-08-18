"""Strict dated Seedance provider and pricing profile contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.seedance_capabilities import (
    SEEDANCE_MODEL_IDS,
    SeedanceCapabilityProfile,
    default_seedance_capabilities,
    validate_seedance_capability_matrix,
)
from ai_video.production.video import ProviderProfilePointer


SEEDANCE_ORIGIN = "https://ark.cn-beijing.volces.com"
_PROFILE_ID = "seedance-official-full-models"
_PROFILE_VERSION = "seedance-2026-08-19"
_MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"


def _canonical_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Seedance result origin must be canonical HTTPS") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Seedance result origin must be canonical HTTPS")
    host = parsed.hostname.lower()
    canonical = f"https://{host}"
    if port is not None and port != 443:
        canonical = f"{canonical}:{port}"
    if value != canonical:
        raise ValueError("Seedance result origin must be canonical HTTPS")
    return value


class _SeedanceProfileModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SeedanceModelCostUpperBound(_SeedanceProfileModel):
    model_id: str = Field(pattern=_SAFE_ID)
    max_cost_microunits: int = Field(strict=True, gt=0)


class SeedancePricingSnapshot(_SeedanceProfileModel):
    snapshot_id: str = Field(pattern=_SAFE_ID)
    observed_at: datetime
    expires_at: datetime
    model_upper_bounds: tuple[SeedanceModelCostUpperBound, ...]
    snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("observed_at", "expires_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Seedance pricing timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _validate_snapshot(self) -> "SeedancePricingSnapshot":
        if self.observed_at >= self.expires_at:
            raise ValueError("Seedance pricing validity window is invalid")
        if len({entry.model_id for entry in self.model_upper_bounds}) != len(
            self.model_upper_bounds
        ):
            raise ValueError("Seedance pricing model IDs must be unique")
        if self.snapshot_sha256 != canonical_sha256(
            self.model_dump(mode="json", exclude={"snapshot_sha256"})
        ):
            raise ValueError("Seedance pricing snapshot hash does not match")
        return self

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: str,
        observed_at: datetime,
        expires_at: datetime,
        model_upper_bounds_microunits: Mapping[str, int],
    ) -> "SeedancePricingSnapshot":
        entries = tuple(
            SeedanceModelCostUpperBound(
                model_id=model_id,
                max_cost_microunits=model_upper_bounds_microunits[model_id],
            )
            for model_id in sorted(model_upper_bounds_microunits)
        )
        data: dict[str, object] = {
            "snapshot_id": snapshot_id,
            "observed_at": observed_at,
            "expires_at": expires_at,
            "model_upper_bounds": entries,
        }
        candidate = cls.model_construct(**data, snapshot_sha256="0" * 64)
        data["snapshot_sha256"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"snapshot_sha256"}, warnings=False
            )
        )
        return cls.model_validate(data)

    def upper_bound_for(self, model_id: str) -> int | None:
        return next(
            (
                entry.max_cost_microunits
                for entry in self.model_upper_bounds
                if entry.model_id == model_id
            ),
            None,
        )


class SeedanceProviderProfile(_SeedanceProfileModel):
    profile_id: str = Field(pattern=_SAFE_ID)
    profile_version: str = Field(pattern=_SAFE_ID)
    origin: str
    pricing: SeedancePricingSnapshot
    result_origins: tuple[str, ...] = Field(min_length=1)
    capabilities: tuple[SeedanceCapabilityProfile, ...] = Field(min_length=1)
    max_download_bytes: int = Field(strict=True, gt=0)
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("origin")
    @classmethod
    def _origin(cls, value: str) -> str:
        return _canonical_origin(value)

    @field_validator("result_origins")
    @classmethod
    def _result_origins(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_canonical_origin(origin) for origin in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("Seedance result origins must be unique")
        return normalized

    @model_validator(mode="after")
    def _validate_profile(self) -> "SeedanceProviderProfile":
        variants = tuple(entry.variant for entry in self.capabilities)
        validate_seedance_capability_matrix(self.capabilities)
        if len({variant.capability_id for variant in variants}) != len(variants):
            raise ValueError("Seedance capability IDs must be unique")
        if {entry.model_id for entry in self.pricing.model_upper_bounds} != set(
            SEEDANCE_MODEL_IDS
        ):
            raise ValueError("Seedance pricing must cover the exact included Model IDs")
        if {variant.model_id for variant in variants} != set(SEEDANCE_MODEL_IDS):
            raise ValueError("Seedance capabilities must cover the exact included Model IDs")
        if self.profile_sha256 != canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_sha256"})
        ):
            raise ValueError("Seedance profile hash does not match")
        return self

    @classmethod
    def create(
        cls,
        *,
        pricing: SeedancePricingSnapshot,
        result_origins: tuple[str, ...],
        capabilities: tuple[SeedanceCapabilityProfile, ...],
        max_download_bytes: int = _MAX_DOWNLOAD_BYTES,
    ) -> "SeedanceProviderProfile":
        data: dict[str, object] = {
            "profile_id": _PROFILE_ID,
            "profile_version": _PROFILE_VERSION,
            "origin": SEEDANCE_ORIGIN,
            "pricing": pricing,
            "result_origins": result_origins,
            "capabilities": capabilities,
            "max_download_bytes": max_download_bytes,
        }
        candidate = cls.model_construct(**data, profile_sha256="0" * 64)
        data["profile_sha256"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"profile_sha256"}, warnings=False
            )
        )
        return cls.model_validate(data)

    @classmethod
    def create_default(
        cls,
        *,
        pricing: SeedancePricingSnapshot,
        result_origins: tuple[str, ...],
    ) -> "SeedanceProviderProfile":
        return cls.create(
            pricing=pricing,
            result_origins=result_origins,
            capabilities=default_seedance_capabilities(),
        )

    def pointer(self) -> ProviderProfilePointer:
        return ProviderProfilePointer(
            profile_id=self.profile_id,
            profile_version=self.profile_version,
            profile_path=Path(f"provider-profiles/{self.profile_sha256}.json"),
            profile_sha256=self.profile_sha256,
        )


__all__ = [
    "SEEDANCE_ORIGIN",
    "SeedancePricingSnapshot",
    "SeedanceProviderProfile",
]
