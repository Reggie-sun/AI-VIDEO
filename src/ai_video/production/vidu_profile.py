"""Sealed Vidu API configuration and dated operator cost ceiling."""

from __future__ import annotations

import ipaddress
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.video import (
    BillingKind, ProviderProfilePointer, VideoCapabilityVariant,
    VideoExecutionKind, VideoGenerationMode, VideoOutputCapability, VideoMediaCapability,
    VideoOutputRecoveryStrategy, VideoProviderCapabilities,
)


VIDU_PROFILE_VERSION = "vidu-q3-2026-09-05"
VIDU_MODEL_IDS = ("viduq3-pro", "viduq3-turbo")
VIDU_REFERENCE_MODEL_IDS = ("viduq3", "viduq3-turbo")
VIDU_EXTEND_MODEL_IDS = ("viduq2-pro", "viduq2-turbo")


def canonical_result_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https" or not parsed.hostname
        or parsed.username is not None or parsed.password is not None
        or parsed.port not in (None, 443) or parsed.path or parsed.query
        or parsed.fragment or value != f"https://{parsed.hostname}"
        or parsed.hostname in {"localhost", "localhost.localdomain"}
        or "." not in parsed.hostname
    ):
        raise ValueError("Vidu result origin must be a canonical public HTTPS origin")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return value
    if not address.is_global:
        raise ValueError("Vidu result origin must not be a private address")
    return value


class ViduProviderProfile(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    origin: str
    result_origins: tuple[str, ...] = Field(min_length=1)
    cost_upper_bound_microunits: int = Field(strict=True, gt=0)
    pricing_observed_at: datetime
    pricing_expires_at: datetime
    max_download_bytes: int = Field(default=512 * 1024 * 1024, strict=True, gt=0)

    @model_validator(mode="after")
    def _validate_profile(self) -> "ViduProviderProfile":
        if self.origin not in {"https://api.vidu.cn", "https://api.vidu.com"}:
            raise ValueError("Vidu API origin must be an official explicit endpoint")
        for origin in self.result_origins:
            canonical_result_origin(origin)
        if len(set(self.result_origins)) != len(self.result_origins):
            raise ValueError("Vidu result origins must be unique")
        if any(t.tzinfo is None or t.utcoffset() is None for t in (
            self.pricing_observed_at, self.pricing_expires_at,
        )) or self.pricing_observed_at >= self.pricing_expires_at:
            raise ValueError("Vidu pricing must have an aware finite validity window")
        return self

    @property
    def currency(self) -> str:
        return "CNY" if self.origin == "https://api.vidu.cn" else "USD"

    def pointer(self) -> ProviderProfilePointer:
        digest = canonical_sha256(self.model_dump(mode="json"))
        return ProviderProfilePointer(
            profile_id="vidu-official-q3", profile_version=VIDU_PROFILE_VERSION,
            profile_path=Path(f"provider-profiles/{digest}.json"), profile_sha256=digest,
        )


def vidu_capabilities() -> VideoProviderCapabilities:
    variants = []
    for model in VIDU_MODEL_IDS:
        for mode in (VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO):
            image_mode = mode is VideoGenerationMode.IMAGE_TO_VIDEO
            variants.append(VideoCapabilityVariant(
                capability_id=f"{model}-{'i2v' if image_mode else 't2v'}-v1",
                provider_kind="vidu", model_id=model, profile_version=VIDU_PROFILE_VERSION,
                execution_kind=VideoExecutionKind.REMOTE, billing_kind=BillingKind.METERED,
                mode=mode,
                output_capability=VideoOutputCapability(
                    min_duration_seconds=1, max_duration_seconds=16,
                    provider_selected_duration=False, timing_modes=("exact_seconds", "nominal_seconds"),
                    dimension_modes=(("adaptive",) if image_mode else ("exact",)),
                    resolution_labels=("540p", "720p", "1080p"),
                    ratios=(("adaptive",) if image_mode else ("16:9", "9:16", "1:1", "3:4", "4:3")),
                    fps_values=(24,), containers=("mp4",), native_audio_options=(False, True),
                ),
                allowed_image_roles=(("first_frame", "last_frame") if image_mode else ()),
                required_first_frame=image_mode, max_reference_count=0,
                allowed_image_mime_types=(("image/png", "image/jpeg", "image/webp") if image_mode else ()),
                max_image_bytes=14 * 1024 * 1024, min_image_width=1, min_image_height=1,
                negative_prompt_supported=False, seed_supported=True, fps_supported=True,
                idempotent_submit=False, lookup_supported=True,
                output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
            ))
    for model in (*VIDU_REFERENCE_MODEL_IDS, *VIDU_EXTEND_MODEL_IDS):
        extend = model in VIDU_EXTEND_MODEL_IDS
        variants.append(VideoCapabilityVariant(
            capability_id=f"{model}-{'extend' if extend else 'r2v'}-v1",
            provider_kind="vidu", model_id=model, profile_version=VIDU_PROFILE_VERSION,
            execution_kind=VideoExecutionKind.REMOTE, billing_kind=BillingKind.METERED,
            mode=VideoGenerationMode.VIDEO_EXTEND if extend else VideoGenerationMode.REFERENCE_TO_VIDEO,
            output_capability=VideoOutputCapability(
                min_duration_seconds=5 if extend else 3, max_duration_seconds=67 if extend else 16,
                provider_selected_duration=False, timing_modes=("exact_seconds", "nominal_seconds"),
                dimension_modes=("adaptive",) if extend else ("exact",),
                resolution_labels=("540p", "720p", "1080p"),
                ratios=("adaptive",) if extend else ("16:9", "9:16", "1:1"),
                fps_values=(24,), containers=("mp4",), native_audio_options=(False,) if extend else (False, True),
            ),
            allowed_image_roles=("last_frame",) if extend else ("reference",),
            required_first_frame=False, max_reference_count=0 if extend else 7,
            allowed_image_mime_types=("image/png", "image/jpeg", "image/webp"),
            max_image_bytes=14 * 1024 * 1024 if extend else 10_000_000, min_image_width=1 if extend else 128,
            min_image_height=1 if extend else 128,
            media_capabilities=(VideoMediaCapability(
                kind="video", roles=("reference_video",), min_count=1, max_count=1,
                allowed_mime_types=("video/mp4",), max_size_bytes=512 * 1024 * 1024,
                min_duration_millis=4000, max_duration_millis=60000,
            ),) if extend else (),
            negative_prompt_supported=False, seed_supported=not extend, fps_supported=True,
            idempotent_submit=False, lookup_supported=True,
            output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
        ))
    return VideoProviderCapabilities.create(provider_name="vidu", variants=tuple(variants))
