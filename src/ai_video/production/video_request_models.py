"""Small immutable identities shared by generated-video requests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"


class VideoOutputRequirement(StrictModel):
    duration_seconds: int = Field(strict=True, gt=0, le=600)
    width: int = Field(strict=True, gt=0, le=16384)
    height: int = Field(strict=True, gt=0, le=16384)
    fps: int | None = Field(default=None, strict=True, gt=0, le=240)
    container: Literal["mp4"]
    mime_type: Literal["video/mp4"]
    native_audio: bool


class VideoImageReferenceBinding(StrictModel):
    role: Literal["first_frame", "last_frame", "reference"]
    asset_id: str = Field(pattern=_SAFE_ID.pattern)
    asset_sha256: str = Field(pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    size_bytes: int | None = Field(default=None, strict=True, ge=0)


class ProviderProfilePointer(StrictModel):
    profile_id: str = Field(pattern=_SAFE_ID.pattern)
    profile_version: str = Field(pattern=_SAFE_ID.pattern)
    profile_path: Path
    profile_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _canonical_path(self) -> "ProviderProfilePointer":
        if (
            self.profile_path.is_absolute()
            or ".." in self.profile_path.parts
            or self.profile_path
            != Path(f"provider-profiles/{self.profile_sha256}.json")
        ):
            raise ValueError("provider profile path must be canonical and content-addressed")
        return self
