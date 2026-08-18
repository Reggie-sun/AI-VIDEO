"""Reusable provider-neutral media and flexible video-output constraints."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.models import StrictModel


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"


class _VideoContractModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class VideoProviderTaskBinding(_VideoContractModel):
    """Opaque exact provider request/response identity sealed before submit."""

    request_target_id: str = Field(pattern=_SAFE_ID)
    response_model_id: str = Field(pattern=_SAFE_ID)


class VideoMediaReferenceBinding(_VideoContractModel):
    kind: Literal["video", "audio"]
    role: Literal["reference_video", "reference_audio"]
    asset_id: str = Field(pattern=_SAFE_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    duration_millis: int = Field(strict=True, gt=0)
    size_bytes: int = Field(strict=True, gt=0)
    width: int | None = Field(default=None, strict=True, gt=0)
    height: int | None = Field(default=None, strict=True, gt=0)
    fps: int | None = Field(default=None, strict=True, gt=0, le=240)

    @model_validator(mode="after")
    def _validate_kind(self) -> "VideoMediaReferenceBinding":
        expected_role = f"reference_{self.kind}"
        if self.role != expected_role:
            raise ValueError("video media role must match its media kind")
        measured_video = self.width is not None and self.height is not None and self.fps is not None
        if self.kind == "video" and not measured_video:
            raise ValueError("video references require measured width, height, and FPS")
        if self.kind == "audio" and any(
            value is not None for value in (self.width, self.height, self.fps)
        ):
            raise ValueError("audio references cannot contain video measurements")
        return self


class VideoFlexibleOutputRequirement(_VideoContractModel):
    timing_mode: Literal["exact_seconds", "provider_selected", "frame_count"]
    duration_seconds: int | None = Field(default=None, strict=True, gt=0, le=600)
    frame_count: int | None = Field(default=None, strict=True, gt=0, le=144_000)
    dimension_mode: Literal["exact", "adaptive"]
    width: int | None = Field(default=None, strict=True, gt=0, le=16384)
    height: int | None = Field(default=None, strict=True, gt=0, le=16384)
    resolution_label: str = Field(pattern=_SAFE_ID)
    ratio: Literal["21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "adaptive"]
    fps: int = Field(strict=True, gt=0, le=240)
    container: Literal["mp4", "mov"]
    mime_type: Literal["video/mp4", "video/quicktime"]
    native_audio: bool

    @model_validator(mode="after")
    def _validate_output(self) -> "VideoFlexibleOutputRequirement":
        if self.timing_mode == "exact_seconds":
            timing_valid = self.duration_seconds is not None and self.frame_count is None
        elif self.timing_mode == "frame_count":
            timing_valid = self.duration_seconds is None and self.frame_count is not None
        else:
            timing_valid = self.duration_seconds is None and self.frame_count is None
        if not timing_valid:
            raise ValueError("flexible video timing fields do not match timing mode")

        if self.dimension_mode == "exact":
            dimensions_valid = self.width is not None and self.height is not None
        else:
            dimensions_valid = (
                self.width is None
                and self.height is None
                and self.ratio == "adaptive"
            )
        if not dimensions_valid:
            raise ValueError("flexible video dimensions do not match dimension mode")

        expected_mime = {
            "mp4": "video/mp4",
            "mov": "video/quicktime",
        }[self.container]
        if self.mime_type != expected_mime:
            raise ValueError("video container and MIME type must match")
        return self


class VideoOutputCapability(_VideoContractModel):
    min_duration_seconds: int = Field(strict=True, gt=0, le=600)
    max_duration_seconds: int = Field(strict=True, gt=0, le=600)
    provider_selected_duration: bool
    timing_modes: tuple[
        Literal["exact_seconds", "provider_selected", "frame_count"], ...
    ] | None = None
    frame_count_min: int | None = Field(default=None, strict=True, gt=0)
    frame_count_max: int | None = Field(default=None, strict=True, gt=0)
    frame_count_step: int | None = Field(default=None, strict=True, gt=0)
    frame_count_remainder: int | None = Field(default=None, strict=True, ge=0)
    dimension_modes: tuple[Literal["exact", "adaptive"], ...] = Field(min_length=1)
    resolution_labels: tuple[str, ...] = Field(min_length=1)
    ratios: tuple[
        Literal["21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "adaptive"], ...
    ] = Field(min_length=1)
    fps_values: tuple[int, ...] = Field(min_length=1)
    containers: tuple[Literal["mp4", "mov"], ...] = Field(min_length=1)
    native_audio_options: tuple[bool, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_capability(self) -> "VideoOutputCapability":
        if self.min_duration_seconds > self.max_duration_seconds:
            raise ValueError("video output duration range is invalid")
        frame_values = (
            self.frame_count_min,
            self.frame_count_max,
            self.frame_count_step,
            self.frame_count_remainder,
        )
        if any(value is not None for value in frame_values) and any(
            value is None for value in frame_values
        ):
            raise ValueError("video frame-count capability must be fully specified")
        if (
            self.frame_count_min is not None
            and self.frame_count_max is not None
            and self.frame_count_min > self.frame_count_max
        ):
            raise ValueError("video frame-count range is invalid")
        if self.timing_modes is not None:
            if not self.timing_modes or len(set(self.timing_modes)) != len(
                self.timing_modes
            ):
                raise ValueError("video output timing modes must be non-empty and unique")
            if (
                "provider_selected" in self.timing_modes
                and not self.provider_selected_duration
            ) or (
                "frame_count" in self.timing_modes
                and self.frame_count_min is None
            ):
                raise ValueError("video output timing modes exceed declared timing support")
        for values, label in (
            (self.dimension_modes, "dimension modes"),
            (self.resolution_labels, "resolution labels"),
            (self.ratios, "ratios"),
            (self.fps_values, "FPS values"),
            (self.containers, "containers"),
            (self.native_audio_options, "native audio options"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"video output capability {label} must be unique")
        return self

    def supports(self, output: VideoFlexibleOutputRequirement) -> bool:
        timing_modes = self.timing_modes or (
            "exact_seconds",
            *(("provider_selected",) if self.provider_selected_duration else ()),
            *(("frame_count",) if self.frame_count_min is not None else ()),
        )
        if output.timing_mode not in timing_modes:
            return False
        if output.timing_mode == "exact_seconds":
            timing_supported = (
                output.duration_seconds is not None
                and self.min_duration_seconds
                <= output.duration_seconds
                <= self.max_duration_seconds
            )
        elif output.timing_mode == "provider_selected":
            timing_supported = self.provider_selected_duration
        else:
            timing_supported = (
                output.frame_count is not None
                and self.frame_count_min is not None
                and self.frame_count_max is not None
                and self.frame_count_step is not None
                and self.frame_count_remainder is not None
                and self.frame_count_min <= output.frame_count <= self.frame_count_max
                and output.frame_count % self.frame_count_step == self.frame_count_remainder
            )
        return bool(
            timing_supported
            and output.dimension_mode in self.dimension_modes
            and output.resolution_label in self.resolution_labels
            and output.ratio in self.ratios
            and output.fps in self.fps_values
            and output.container in self.containers
            and output.native_audio in self.native_audio_options
        )


class VideoMediaCapability(_VideoContractModel):
    kind: Literal["video", "audio"]
    roles: tuple[Literal["reference_video", "reference_audio"], ...] = Field(min_length=1)
    min_count: int = Field(strict=True, ge=0, le=32)
    max_count: int = Field(strict=True, ge=0, le=32)
    allowed_mime_types: tuple[str, ...] = Field(min_length=1)
    max_size_bytes: int = Field(strict=True, gt=0)
    min_duration_millis: int = Field(strict=True, gt=0)
    max_duration_millis: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def _validate_capability(self) -> "VideoMediaCapability":
        if self.min_count > self.max_count:
            raise ValueError("video media count range is invalid")
        if self.min_duration_millis > self.max_duration_millis:
            raise ValueError("video media duration range is invalid")
        if any(role != f"reference_{self.kind}" for role in self.roles):
            raise ValueError("video media capability roles must match media kind")
        if len(set(self.roles)) != len(self.roles) or len(set(self.allowed_mime_types)) != len(
            self.allowed_mime_types
        ):
            raise ValueError("video media capability values must be unique")
        return self

    def supports(self, bindings: tuple[VideoMediaReferenceBinding, ...]) -> bool:
        selected = tuple(binding for binding in bindings if binding.kind == self.kind)
        return bool(
            self.min_count <= len(selected) <= self.max_count
            and all(
                binding.role in self.roles
                and binding.mime_type in self.allowed_mime_types
                and binding.size_bytes <= self.max_size_bytes
                and self.min_duration_millis
                <= binding.duration_millis
                <= self.max_duration_millis
                for binding in selected
            )
        )


def media_bindings_satisfy_capabilities(
    bindings: tuple[VideoMediaReferenceBinding, ...],
    capabilities: tuple[VideoMediaCapability, ...],
) -> bool:
    if len({capability.kind for capability in capabilities}) != len(capabilities):
        return False
    if any(
        binding.kind not in {capability.kind for capability in capabilities}
        for binding in bindings
    ):
        return False
    return all(capability.supports(bindings) for capability in capabilities)


__all__ = [
    "VideoFlexibleOutputRequirement",
    "VideoMediaCapability",
    "VideoMediaReferenceBinding",
    "VideoOutputCapability",
    "VideoProviderTaskBinding",
    "media_bindings_satisfy_capabilities",
]
