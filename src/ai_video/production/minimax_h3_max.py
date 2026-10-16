"""Official MiniMax H3 Max reference-to-video adapter."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_serializer

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.metaso_h3 import (
    HttpxMetasoH3Transport,
    MetasoH3VideoProvider,
)
from ai_video.production.models import StrictModel
from ai_video.production.video import ProviderProfilePointer, VideoFlexibleOutputRequirement

MINIMAX_H3_MAX_ORIGIN = "https://api.minimax.io"
MINIMAX_H3_MAX_CN_ORIGIN = "https://api.minimax.cn"
MINIMAX_H3_MAX_MODEL_ID = "MiniMax-H3-Max"
MINIMAX_H3_MAX_PROVIDER_NAME = "minimax_h3_max"
_PROFILE_VERSION = "h3-max-reference-v1"
_FRAME_CAPABILITY_ID = "minimax-h3-max-fl2va-v1"
_COMPILER_ID = "minimax-h3-max-video-compiler"
_SECRET_REFERENCE_ID = "MINIMAX_H3_API_KEY"
_MAX_BODY_BYTES = 64 * 1024 * 1024


class MiniMaxH3MaxProfile(StrictModel):
    """One sealed official API input profile; cost is an operator upper bound."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    duration: int = Field(strict=True, ge=5, le=15)
    resolution: Literal["480P", "768P"]
    aspect_ratio: Literal["adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
    prompt_expansion_mode: Literal["balanced"] = "balanced"
    currency: Literal["CNY", "USD"]
    cost_upper_bound_microunits: int = Field(strict=True, gt=0)
    api_region: Literal["international", "cn"] = "international"

    @model_serializer(mode="wrap")
    def _legacy_international_profile(self, handler):
        data = handler(self)
        if self.api_region == "international":
            data.pop("api_region", None)
        return data

    def pointer(self) -> ProviderProfilePointer:
        digest = canonical_sha256(self.model_dump(mode="json"))
        return ProviderProfilePointer(
            profile_id=MINIMAX_H3_MAX_PROVIDER_NAME,
            profile_version=_PROFILE_VERSION,
            profile_path=Path(f"provider-profiles/{digest}.json"),
            profile_sha256=digest,
        )

    def output(self) -> VideoFlexibleOutputRequirement:
        return VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds",
            duration_seconds=self.duration,
            dimension_mode="adaptive",
            resolution_label=self.resolution,
            ratio="adaptive",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=True,
        )


class HttpxMiniMaxH3MaxTransport(HttpxMetasoH3Transport):
    """HTTP transport with the shared credential-free public result fetch."""

    error_label = "MiniMax H3 Max"


class MiniMaxH3MaxVideoProvider(MetasoH3VideoProvider):
    provider_name = MINIMAX_H3_MAX_PROVIDER_NAME
    provider_kind = MINIMAX_H3_MAX_PROVIDER_NAME
    model_id = MINIMAX_H3_MAX_MODEL_ID
    origin = MINIMAX_H3_MAX_ORIGIN
    base_url = MINIMAX_H3_MAX_ORIGIN
    profile_version = _PROFILE_VERSION
    frame_capability_id = _FRAME_CAPABILITY_ID
    compiler_id = _COMPILER_ID
    compiler_version = "1"
    secret_reference_id = _SECRET_REFERENCE_ID
    min_reference_video_fps = 23.976
    error_label = "MiniMax H3 Max"

    def __init__(self, *, profile: MiniMaxH3MaxProfile, transport,
                 reference_resolver: Callable, credential: Callable[[], str],
                 now: Callable[[], datetime] | None = None):
        if type(profile) is not MiniMaxH3MaxProfile:
            raise TypeError("MiniMax H3 Max requires its exact sealed profile type.")
        # Revalidate from plain data because model_copy/model_construct can
        # produce instances that bypass normal Pydantic input validation.
        validated_profile = MiniMaxH3MaxProfile.model_validate(
            profile.model_dump(mode="python"))
        if not callable(credential):
            raise TypeError("MiniMax H3 Max requires an injected credential supplier.")
        if not callable(reference_resolver):
            raise TypeError("MiniMax H3 Max requires a verified reference resolver.")
        self.origin, self.secret_reference_id = {
            "international": (MINIMAX_H3_MAX_ORIGIN, _SECRET_REFERENCE_ID),
            "cn": (MINIMAX_H3_MAX_CN_ORIGIN, "MINIMAX_H3_CN_API_KEY"),
        }[validated_profile.api_region]
        self.base_url = self.origin
        super().__init__(profile=validated_profile, transport=transport,
                         reference_resolver=reference_resolver, credential=credential, now=now)

    def _native_profile_options(self, *, frame_mode: bool) -> dict[str, object]:
        return {"extra": {"prompt_expansion_mode": self._profile.prompt_expansion_mode}}

    def _validate_query_output_echoes(self, task: dict[str, object]) -> None:
        expected = {
            "duration": self._profile.duration,
            "resolution": self._profile.resolution,
        }
        if self._profile.aspect_ratio != "adaptive":
            expected["ratio"] = self._profile.aspect_ratio
        if any(key in task and task[key] != value for key, value in expected.items()):
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_FAILED,
                user_message="minimax_h3_max query output identity mismatch.",
            )


__all__ = [
    "HttpxMiniMaxH3MaxTransport",
    "MINIMAX_H3_MAX_MODEL_ID",
    "MINIMAX_H3_MAX_ORIGIN",
    "MINIMAX_H3_MAX_CN_ORIGIN",
    "MINIMAX_H3_MAX_PROVIDER_NAME",
    "MiniMaxH3MaxProfile",
    "MiniMaxH3MaxVideoProvider",
]
