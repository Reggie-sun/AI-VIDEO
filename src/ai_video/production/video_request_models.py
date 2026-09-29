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


def generation_request_fingerprint_payload(data: dict[str, object]) -> dict[str, object]:
    media_bindings = data.get("media_bindings")
    mode = data.get("mode")
    output = data.get("output_requirement")
    image_bindings = data.get("image_bindings")
    continuity = data.get("continuity_binding")
    hard_cut = data.get("hard_cut_keyframe_binding")
    c4_binding = data.get("c4_multi_anchor_binding")
    execution_stack_hash = data.get("execution_stack_hash")
    commercial_binding = data.get("commercial_binding")
    seal_terminal_frame = data.get("seal_terminal_frame", False)
    lineage_fields = (
        "requirement_hash",
        "provider_bound_request_hash",
        "adapter_compiler_id",
        "adapter_compiler_version",
        "adapter_compiler_hash",
    )
    uses_provider_neutral_lineage = all(
        data.get(field) is not None for field in lineage_fields
    )
    advanced = bool(
        media_bindings
        or mode
        in {
            "reference_to_video",
            "video_edit",
            "video_extend",
        }
        or isinstance(output, dict)
        and "timing_mode" in output
        or isinstance(image_bindings, list)
        and any(binding.get("role") == "last_frame" for binding in image_bindings)
    )
    selected = {
        key: value
        for key, value in data.items()
        if key not in {"generation_id", "request_input_hash"}
    }
    if not advanced:
        selected.pop("media_bindings", None)
    if continuity is None:
        selected.pop("continuity_binding", None)
    if c4_binding is None:
        selected.pop("c4_multi_anchor_binding", None)
    if hard_cut is None:
        selected.pop("hard_cut_keyframe_binding", None)
    if execution_stack_hash is None:
        selected.pop("execution_stack_hash", None)
    if commercial_binding is None:
        selected.pop("commercial_binding", None)
    if not seal_terminal_frame:
        selected.pop("seal_terminal_frame", None)
    if not uses_provider_neutral_lineage:
        for field in lineage_fields:
            selected.pop(field, None)
    return {
        "schema": (
            "ai-video-generation-request/9"
            if data.get("subject_bindings")
            else "ai-video-generation-request/8"
            if commercial_binding is not None
            else "ai-video-generation-request/7"
            if execution_stack_hash is not None
            else "ai-video-generation-request/6"
            if c4_binding is not None
            else "ai-video-generation-request/5"
            if uses_provider_neutral_lineage
            else "ai-video-generation-request/4"
            if hard_cut is not None
            else "ai-video-generation-request/3"
            if continuity is not None or seal_terminal_frame
            else "ai-video-generation-request/2"
            if advanced
            else "ai-video-generation-request/1"
        ),
        **selected,
    }

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
