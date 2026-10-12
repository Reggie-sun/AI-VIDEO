"""Documented Grok media controls; account admission remains a separate gate."""

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.video import (
    BillingKind, ProviderProfilePointer, VideoCapabilityVariant, VideoExecutionKind,
    VideoGenerationMode, VideoOutputCapability, VideoOutputRecoveryStrategy,
    VideoProviderCapabilities,
)

GROK_PROFILE_VERSION = "grok-subscription-media-2026-10-12"
GROK_VIDEO_MODEL = "grok-imagine-video-1.5"
GROK_IMAGE_MODEL = "grok-imagine-image-2.0"


class GrokProviderProfile(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    origin: Literal["https://cli-chat-proxy.grok.com"] = "https://cli-chat-proxy.grok.com"
    account_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    max_download_bytes: int = Field(default=512 * 1024 * 1024, strict=True, gt=0)
    image_resolution: Literal["1k", "2k"] = "1k"

    def pointer(self) -> ProviderProfilePointer:
        digest = canonical_sha256(self.model_dump(mode="json"))
        return ProviderProfilePointer(profile_id="grok-subscription-media",
            profile_version=GROK_PROFILE_VERSION,
            profile_path=Path(f"provider-profiles/{digest}.json"), profile_sha256=digest)


def grok_capabilities() -> VideoProviderCapabilities:
    variants = []
    for mode in (VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO):
        images = mode is VideoGenerationMode.IMAGE_TO_VIDEO
        variants.append(VideoCapabilityVariant(
            capability_id=f"grok-imagine-video-1.5-{'i2v' if images else 't2v'}-v1",
            provider_kind="grok", model_id=GROK_VIDEO_MODEL, profile_version=GROK_PROFILE_VERSION,
            execution_kind=VideoExecutionKind.REMOTE, billing_kind=BillingKind.METERED, mode=mode,
            output_capability=VideoOutputCapability(min_duration_seconds=1, max_duration_seconds=15,
                provider_selected_duration=False, timing_modes=("nominal_seconds",),
                dimension_modes=("adaptive",), resolution_labels=("480p", "720p", "1080p"),
                ratios=("adaptive",), fps_values=(None,), containers=("mp4",),
                native_audio_options=(False, True)),
            allowed_image_roles=("first_frame",) if images else (), required_first_frame=images,
            max_reference_count=0, allowed_image_mime_types=("image/png", "image/jpeg", "image/webp") if images else (),
            max_image_bytes=20 * 1024 * 1024, min_image_width=1, min_image_height=1,
            negative_prompt_supported=False, seed_supported=False, fps_supported=False,
            idempotent_submit=False, lookup_supported=True,
            output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID))
    return VideoProviderCapabilities.create(provider_name="grok", variants=tuple(variants))
