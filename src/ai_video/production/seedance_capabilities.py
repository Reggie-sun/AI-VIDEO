"""Dated declarative Seedance model and capability matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.models import StrictModel
from ai_video.production.video import (
    BillingKind,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoMediaCapability,
    VideoOutputCapability,
)


SEEDANCE_MODEL_IDS = (
    "doubao-seedance-2-5-260628",
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-2-0-mini-260615",
    "doubao-seedance-1-5-pro-251215",
    "doubao-seedance-1-0-pro-250528",
    "doubao-seedance-1-0-pro-fast-251015",
)

_PROVIDER_KIND = "volcengine_ark_seedance"
_PROFILE_VERSION = "seedance-2026-08-19"
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_NAMED_RATIOS = ("21:9", "16:9", "4:3", "1:1", "3:4", "9:16")
_COMMON_720 = (
    (1470, 630),
    (1280, 720),
    (1112, 834),
    (960, 960),
    (834, 1112),
    (720, 1280),
)
_COMMON_1080 = (
    (2206, 946),
    (1920, 1080),
    (1664, 1248),
    (1440, 1440),
    (1248, 1664),
    (1080, 1920),
)
_RASTERS_BY_FAMILY: dict[str, dict[str, tuple[tuple[int, int], ...]]] = {
    "2.5": {
        "480p": ((992, 432), (854, 480), (752, 560), (640, 640), (560, 752), (480, 854)),
        "720p": _COMMON_720,
        "1080p": _COMMON_1080,
    },
    "2.0": {
        "480p": ((992, 432), (864, 496), (752, 560), (640, 640), (560, 752), (496, 864)),
        "720p": _COMMON_720,
        "1080p": _COMMON_1080,
        "4k": ((4398, 1886), (3840, 2160), (3326, 2494), (2880, 2880), (2494, 3326), (2160, 3840)),
    },
    "1.5": {
        "480p": ((992, 432), (864, 496), (752, 560), (640, 640), (560, 752), (496, 864)),
        "720p": _COMMON_720,
        "1080p": _COMMON_1080,
    },
    "1.0": {
        "480p": ((960, 416), (864, 480), (736, 544), (640, 640), (544, 736), (480, 864)),
        "720p": ((1504, 640), (1248, 704), (1120, 832), (960, 960), (832, 1120), (704, 1248)),
        "1080p": (
            (2176, 928),
            (1920, 1088),
            (1664, 1248),
            (1440, 1440),
            (1248, 1664),
            (1088, 1920),
        ),
    },
}


class _CapabilityModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SeedanceOutputRaster(_CapabilityModel):
    resolution_label: str = Field(pattern=_SAFE_ID)
    ratio: Literal["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)


class SeedanceCapabilityProfile(_CapabilityModel):
    variant: VideoCapabilityVariant
    api_model_id: str = Field(pattern=_SAFE_ID)
    output_rasters: tuple[SeedanceOutputRaster, ...]
    service_tier: Literal["default", "flex"] = "default"
    watermark: bool = False
    return_last_frame: bool = False
    draft: bool = False
    camera_fixed: bool = False
    priority: int | None = Field(default=None, strict=True, ge=0, le=9)
    omni_reference_task_type: Literal["reference", "edit", "extend"] | None = None

    @model_validator(mode="after")
    def _validate_binding(self) -> "SeedanceCapabilityProfile":
        model_id = self.variant.model_id
        if model_id not in SEEDANCE_MODEL_IDS:
            raise ValueError("Seedance capability must bind an included Model ID")
        if self.api_model_id != model_id and not self.api_model_id.startswith("ep-"):
            raise ValueError("Seedance API model must be the exact Model ID or Endpoint ID")
        if self.service_tier == "flex" and model_id.startswith(
            ("doubao-seedance-2-5", "doubao-seedance-2-0")
        ):
            raise ValueError("Seedance 2.x does not support flex service tier")
        output = self.variant.output_capability
        if self.draft and (
            model_id != "doubao-seedance-1-5-pro-251215"
            or output is None
            or output.resolution_labels != ("480p",)
            or "last_frame" in self.variant.allowed_image_roles
            or self.service_tier != "default"
            or self.return_last_frame
        ):
            raise ValueError(
                "Seedance draft requires a 1.5 pro 480p profile without last-frame or flex"
            )
        if self.camera_fixed and (
            model_id
            not in {
                "doubao-seedance-1-5-pro-251215",
                "doubao-seedance-1-0-pro-250528",
                "doubao-seedance-1-0-pro-fast-251015",
            }
            or self.variant.mode is not VideoGenerationMode.TEXT_TO_VIDEO
        ):
            raise ValueError(
                "Seedance camera_fixed is limited to legacy text-to-video profiles"
            )
        expected_task_type = (
            {
                VideoGenerationMode.REFERENCE_TO_VIDEO: "reference",
                VideoGenerationMode.VIDEO_EDIT: "edit",
                VideoGenerationMode.VIDEO_EXTEND: "extend",
            }.get(self.variant.mode)
            if model_id == "doubao-seedance-2-5-260628"
            else None
        )
        if self.omni_reference_task_type != expected_task_type:
            raise ValueError(
                "Seedance omni_reference_task_type must exactly match the 2.5 mode"
            )
        if self.priority is not None and not model_id.startswith(
            ("doubao-seedance-2-5", "doubao-seedance-2-0")
        ):
            raise ValueError("Seedance priority is limited to 2.x")
        output = self.variant.output_capability
        if output is None:
            raise ValueError("Seedance capability requires a flexible output contract")
        expected_rasters = {
            (resolution, ratio)
            for resolution in output.resolution_labels
            for ratio in output.ratios
            if ratio != "adaptive"
        }
        actual_rasters = {
            (raster.resolution_label, raster.ratio) for raster in self.output_rasters
        }
        if actual_rasters != expected_rasters or len(actual_rasters) != len(
            self.output_rasters
        ):
            raise ValueError(
                "Seedance output rasters must cover each supported named output exactly once"
            )
        return self


@dataclass(frozen=True)
class _ModelSpec:
    resolutions: tuple[str, ...]
    min_duration: int
    max_duration: int
    provider_selected_duration: bool
    modes: tuple[VideoGenerationMode, ...]
    containers: tuple[Literal["mp4", "mov"], ...]
    native_audio_options: tuple[bool, ...]
    seed_supported: bool
    last_frame_supported: bool
    max_reference_images: int
    max_reference_videos: int
    max_reference_audio: int
    max_reference_duration_millis: int
    frame_contract: tuple[int, int, int, int] | None = None


_MODEL_SPECS: dict[str, _ModelSpec] = {
    "doubao-seedance-2-5-260628": _ModelSpec(
        resolutions=("480p", "720p", "1080p"),
        min_duration=4,
        max_duration=30,
        provider_selected_duration=True,
        modes=(
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            VideoGenerationMode.VIDEO_EDIT,
            VideoGenerationMode.VIDEO_EXTEND,
        ),
        containers=("mp4", "mov"),
        native_audio_options=(False, True),
        seed_supported=False,
        last_frame_supported=True,
        max_reference_images=30,
        max_reference_videos=10,
        max_reference_audio=10,
        max_reference_duration_millis=30_000,
    ),
    "doubao-seedance-2-0-260128": _ModelSpec(
        resolutions=("480p", "720p", "1080p", "4k"),
        min_duration=4,
        max_duration=15,
        provider_selected_duration=True,
        modes=(
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            VideoGenerationMode.VIDEO_EDIT,
            VideoGenerationMode.VIDEO_EXTEND,
        ),
        containers=("mp4",),
        native_audio_options=(False, True),
        seed_supported=False,
        last_frame_supported=True,
        max_reference_images=9,
        max_reference_videos=3,
        max_reference_audio=3,
        max_reference_duration_millis=15_000,
    ),
    "doubao-seedance-2-0-fast-260128": _ModelSpec(
        resolutions=("480p", "720p"),
        min_duration=4,
        max_duration=15,
        provider_selected_duration=True,
        modes=(
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            VideoGenerationMode.VIDEO_EDIT,
            VideoGenerationMode.VIDEO_EXTEND,
        ),
        containers=("mp4",),
        native_audio_options=(False, True),
        seed_supported=False,
        last_frame_supported=True,
        max_reference_images=9,
        max_reference_videos=3,
        max_reference_audio=3,
        max_reference_duration_millis=15_000,
    ),
    "doubao-seedance-2-0-mini-260615": _ModelSpec(
        resolutions=("480p", "720p"),
        min_duration=4,
        max_duration=15,
        provider_selected_duration=True,
        modes=(
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            VideoGenerationMode.VIDEO_EDIT,
            VideoGenerationMode.VIDEO_EXTEND,
        ),
        containers=("mp4",),
        native_audio_options=(False, True),
        seed_supported=False,
        last_frame_supported=True,
        max_reference_images=9,
        max_reference_videos=3,
        max_reference_audio=3,
        max_reference_duration_millis=15_000,
    ),
    "doubao-seedance-1-5-pro-251215": _ModelSpec(
        resolutions=("480p", "720p", "1080p"),
        min_duration=4,
        max_duration=12,
        provider_selected_duration=True,
        modes=(VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO),
        containers=("mp4",),
        native_audio_options=(False, True),
        seed_supported=True,
        last_frame_supported=True,
        max_reference_images=0,
        max_reference_videos=0,
        max_reference_audio=0,
        max_reference_duration_millis=1,
    ),
    "doubao-seedance-1-0-pro-250528": _ModelSpec(
        resolutions=("480p", "720p", "1080p"),
        min_duration=2,
        max_duration=12,
        provider_selected_duration=False,
        modes=(VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO),
        containers=("mp4",),
        native_audio_options=(False,),
        seed_supported=True,
        last_frame_supported=True,
        max_reference_images=0,
        max_reference_videos=0,
        max_reference_audio=0,
        max_reference_duration_millis=1,
        frame_contract=(29, 289, 4, 1),
    ),
    "doubao-seedance-1-0-pro-fast-251015": _ModelSpec(
        resolutions=("480p", "720p", "1080p"),
        min_duration=2,
        max_duration=12,
        provider_selected_duration=False,
        modes=(VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.IMAGE_TO_VIDEO),
        containers=("mp4",),
        native_audio_options=(False,),
        seed_supported=True,
        last_frame_supported=False,
        max_reference_images=0,
        max_reference_videos=0,
        max_reference_audio=0,
        max_reference_duration_millis=1,
        frame_contract=(29, 289, 4, 1),
    ),
}


def _output_capability(model_id: str, mode: VideoGenerationMode) -> VideoOutputCapability:
    spec = _MODEL_SPECS[model_id]
    adaptive_only = model_id == "doubao-seedance-2-5-260628" and mode in {
        VideoGenerationMode.IMAGE_TO_VIDEO,
        VideoGenerationMode.VIDEO_EDIT,
        VideoGenerationMode.VIDEO_EXTEND,
    }
    adaptive_supported = not model_id.startswith("doubao-seedance-1-0") or (
        mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )
    ratios = (
        ("adaptive",)
        if adaptive_only
        else (*_NAMED_RATIOS, "adaptive")
        if adaptive_supported
        else _NAMED_RATIOS
    )
    frame = spec.frame_contract or (None, None, None, None)
    timing_modes: list[
        Literal["exact_seconds", "provider_selected", "frame_count"]
    ] = []
    if not (
        model_id == "doubao-seedance-2-5-260628"
        and mode is VideoGenerationMode.VIDEO_EDIT
    ):
        timing_modes.append("exact_seconds")
    if spec.provider_selected_duration:
        timing_modes.append("provider_selected")
    if spec.frame_contract is not None:
        timing_modes.append("frame_count")
    return VideoOutputCapability(
        min_duration_seconds=spec.min_duration,
        max_duration_seconds=spec.max_duration,
        provider_selected_duration=spec.provider_selected_duration,
        timing_modes=tuple(timing_modes),
        frame_count_min=frame[0],
        frame_count_max=frame[1],
        frame_count_step=frame[2],
        frame_count_remainder=frame[3],
        dimension_modes=(
            ("adaptive",)
            if adaptive_only
            else ("exact", "adaptive")
            if adaptive_supported
            else ("exact",)
        ),
        resolution_labels=spec.resolutions,
        ratios=ratios,
        fps_values=(24,),
        containers=spec.containers,
        native_audio_options=spec.native_audio_options,
    )


def _media_capabilities(
    model_id: str, mode: VideoGenerationMode
) -> tuple[VideoMediaCapability, ...]:
    spec = _MODEL_SPECS[model_id]
    if mode not in {
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        VideoGenerationMode.VIDEO_EDIT,
        VideoGenerationMode.VIDEO_EXTEND,
    }:
        return ()
    return (
        VideoMediaCapability(
            kind="video",
            roles=("reference_video",),
            min_count=(
                1
                if mode in {VideoGenerationMode.VIDEO_EDIT, VideoGenerationMode.VIDEO_EXTEND}
                else 0
            ),
            max_count=spec.max_reference_videos,
            allowed_mime_types=("video/mp4", "video/quicktime"),
            max_size_bytes=200_000_000,
            min_duration_millis=(
                4_000
                if model_id == "doubao-seedance-2-5-260628"
                and mode is VideoGenerationMode.VIDEO_EDIT
                else 2_000
            ),
            max_duration_millis=spec.max_reference_duration_millis,
        ),
        VideoMediaCapability(
            kind="audio",
            roles=("reference_audio",),
            min_count=0,
            max_count=spec.max_reference_audio,
            allowed_mime_types=("audio/wav", "audio/mpeg"),
            max_size_bytes=15_000_000,
            min_duration_millis=2_000,
            max_duration_millis=spec.max_reference_duration_millis,
        ),
    )


def _raster_family(model_id: str) -> str:
    if "-2-5-" in model_id:
        return "2.5"
    if "-2-0-" in model_id:
        return "2.0"
    if "-1-5-" in model_id:
        return "1.5"
    return "1.0"


def _output_rasters(
    model_id: str, output: VideoOutputCapability
) -> tuple[SeedanceOutputRaster, ...]:
    table = _RASTERS_BY_FAMILY[_raster_family(model_id)]
    return tuple(
        SeedanceOutputRaster(
            resolution_label=resolution,
            ratio=ratio,
            width=table[resolution][index][0],
            height=table[resolution][index][1],
        )
        for resolution in output.resolution_labels
        for index, ratio in enumerate(_NAMED_RATIOS)
        if ratio in output.ratios
    )


def default_seedance_capabilities() -> tuple[SeedanceCapabilityProfile, ...]:
    entries: list[SeedanceCapabilityProfile] = []
    for model_id in SEEDANCE_MODEL_IDS:
        spec = _MODEL_SPECS[model_id]
        for mode in spec.modes:
            if mode is VideoGenerationMode.TEXT_TO_VIDEO:
                image_roles: tuple[
                    Literal["first_frame", "last_frame", "reference"], ...
                ] = ()
                required_first = False
                max_images = 0
            elif mode is VideoGenerationMode.IMAGE_TO_VIDEO:
                image_roles = (
                    ("first_frame", "last_frame")
                    if spec.last_frame_supported
                    else ("first_frame",)
                )
                required_first = True
                max_images = 0
            else:
                image_roles = ("reference",)
                required_first = False
                max_images = spec.max_reference_images
            capability_id = (
                f"seedance-{model_id.removeprefix('doubao-seedance-')}-{mode.value}"
            )
            variant = VideoCapabilityVariant(
                capability_id=capability_id,
                provider_kind=_PROVIDER_KIND,
                model_id=model_id,
                profile_version=_PROFILE_VERSION,
                execution_kind=VideoExecutionKind.REMOTE,
                billing_kind=BillingKind.METERED,
                mode=mode,
                output=None,
                output_capability=_output_capability(model_id, mode),
                allowed_image_roles=image_roles,
                required_first_frame=required_first,
                max_reference_count=max_images,
                allowed_image_mime_types=(
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "image/bmp",
                    "image/tiff",
                    "image/gif",
                    *(
                        ("image/heic", "image/heif")
                        if not model_id.startswith("doubao-seedance-1-0")
                        else ()
                    ),
                ),
                max_image_bytes=30_000_000,
                min_image_width=300,
                min_image_height=300,
                media_capabilities=_media_capabilities(model_id, mode),
                negative_prompt_supported=False,
                seed_supported=spec.seed_supported,
                fps_supported=True,
                idempotent_submit=False,
                lookup_supported=True,
            )
            task_type = (
                {
                    VideoGenerationMode.REFERENCE_TO_VIDEO: "reference",
                    VideoGenerationMode.VIDEO_EDIT: "edit",
                    VideoGenerationMode.VIDEO_EXTEND: "extend",
                }.get(mode)
                if model_id == "doubao-seedance-2-5-260628"
                else None
            )
            entries.append(
                SeedanceCapabilityProfile(
                    variant=variant,
                    api_model_id=model_id,
                    output_rasters=_output_rasters(
                        model_id,
                        variant.output_capability,
                    ),
                    priority=(
                        0
                        if model_id.startswith(
                            ("doubao-seedance-2-5", "doubao-seedance-2-0")
                        )
                        else None
                    ),
                    omni_reference_task_type=task_type,
                )
            )
    return tuple(entries)


def validate_seedance_capability_matrix(
    entries: tuple[SeedanceCapabilityProfile, ...],
) -> None:
    """Reject profile mutations that omit or expand the frozen official matrix."""

    official_entries = default_seedance_capabilities()
    official_by_key = {
        (entry.variant.model_id, entry.variant.mode): entry
        for entry in official_entries
    }
    custom_by_key = {
        (entry.variant.model_id, entry.variant.mode): entry for entry in entries
    }
    if len(custom_by_key) != len(entries) or set(custom_by_key) != set(official_by_key):
        raise ValueError("Seedance capabilities must cover each official model mode exactly once")

    for key, custom in custom_by_key.items():
        official = official_by_key[key]
        variant = custom.variant
        official_variant = official.variant
        output = variant.output_capability
        official_output = official_variant.output_capability
        if output is None or official_output is None:
            raise ValueError("Seedance capability requires an official flexible output contract")
        if (
            variant.capability_id != official_variant.capability_id
            or variant.provider_kind != official_variant.provider_kind
            or variant.profile_version != official_variant.profile_version
            or variant.execution_kind is not official_variant.execution_kind
            or variant.billing_kind is not official_variant.billing_kind
            or variant.output is not None
            or variant.idempotent_submit != official_variant.idempotent_submit
            or variant.lookup_supported != official_variant.lookup_supported
            or variant.required_first_frame != official_variant.required_first_frame
            or variant.max_reference_count > official_variant.max_reference_count
            or not set(variant.allowed_image_roles).issubset(
                official_variant.allowed_image_roles
            )
            or not set(variant.allowed_image_mime_types).issubset(
                official_variant.allowed_image_mime_types
            )
            or variant.max_image_bytes > official_variant.max_image_bytes
            or variant.min_image_width < official_variant.min_image_width
            or variant.min_image_height < official_variant.min_image_height
            or variant.negative_prompt_supported
            and not official_variant.negative_prompt_supported
            or variant.seed_supported and not official_variant.seed_supported
            or variant.fps_supported and not official_variant.fps_supported
        ):
            raise ValueError("Seedance capability expands the frozen official variant")

        if output.timing_modes is None or official_output.timing_modes is None:
            raise ValueError("Seedance output requires explicit official timing modes")
        timing_modes = output.timing_modes
        official_timing_modes = official_output.timing_modes
        if (
            output.min_duration_seconds < official_output.min_duration_seconds
            or output.max_duration_seconds > official_output.max_duration_seconds
            or output.provider_selected_duration
            and not official_output.provider_selected_duration
            or not set(timing_modes).issubset(official_timing_modes)
            or not set(output.dimension_modes).issubset(official_output.dimension_modes)
            or not set(output.resolution_labels).issubset(
                official_output.resolution_labels
            )
            or not set(output.ratios).issubset(official_output.ratios)
            or not set(output.fps_values).issubset(official_output.fps_values)
            or not set(output.containers).issubset(official_output.containers)
            or not set(output.native_audio_options).issubset(
                official_output.native_audio_options
            )
            or (
                output.frame_count_min,
                output.frame_count_max,
                output.frame_count_step,
                output.frame_count_remainder,
            )
            != (
                official_output.frame_count_min,
                official_output.frame_count_max,
                official_output.frame_count_step,
                official_output.frame_count_remainder,
            )
        ):
            raise ValueError("Seedance output expands the frozen official capability")

        official_media = {
            capability.kind: capability
            for capability in official_variant.media_capabilities
        }
        custom_media = {
            capability.kind: capability for capability in variant.media_capabilities
        }
        if len(custom_media) != len(variant.media_capabilities) or set(custom_media) != set(
            official_media
        ):
            raise ValueError("Seedance media capabilities must preserve official media kinds")
        for kind, media in custom_media.items():
            official_media_capability = official_media[kind]
            if (
                not set(media.roles).issubset(official_media_capability.roles)
                or media.min_count < official_media_capability.min_count
                or media.max_count > official_media_capability.max_count
                or not set(media.allowed_mime_types).issubset(
                    official_media_capability.allowed_mime_types
                )
                or media.max_size_bytes > official_media_capability.max_size_bytes
                or media.min_duration_millis
                < official_media_capability.min_duration_millis
                or media.max_duration_millis
                > official_media_capability.max_duration_millis
            ):
                raise ValueError("Seedance media capability expands the official limits")

        official_rasters = {
            (raster.resolution_label, raster.ratio): raster
            for raster in official.output_rasters
        }
        if any(
            official_rasters.get((raster.resolution_label, raster.ratio)) != raster
            for raster in custom.output_rasters
        ):
            raise ValueError("Seedance output raster differs from the official pixel matrix")


__all__ = [
    "SEEDANCE_MODEL_IDS",
    "SeedanceCapabilityProfile",
    "SeedanceOutputRaster",
    "default_seedance_capabilities",
    "validate_seedance_capability_matrix",
]
