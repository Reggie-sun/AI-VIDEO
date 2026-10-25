"""Bounded mode-4 mappings, verified against native read-only config on 2026-10-22.

These declarations grant no paid authority or production qualification. See
tests/fixtures/generated_video/jimeng-native-models-20261022.json for evidence.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

JimengModelId = Literal[
    "seedance_2.5", "seedance_2.0_mini", "seedance_2.0_vip", "seedance_2.0_fast_vip",
]
_MIB = 1024 * 1024


@dataclass(frozen=True)
class JimengModelSpec:
    model_id: JimengModelId
    max_seconds: int
    resolutions: tuple[str, ...]
    prompt_max_characters: int
    max_materials: int
    max_images: int
    max_audios: int
    max_videos: int
    image_bytes: int
    audio_bytes: int
    video_bytes: int
    min_image_dimension: int
    max_image_dimension: int
    image_aspect_bounds: tuple[float, float] | None
    min_video_dimension: int
    max_video_dimension: int
    min_media_millis: int
    max_audio_millis: int
    max_video_millis: int
    requires_visual: bool
    production_qualification: Literal["UNQUALIFIED"] = "UNQUALIFIED"
    ratios: tuple[str, ...] = ("16:9", "9:16", "1:1", "4:3", "3:4")


# Equal limits remain explicit per model. No catch-all or model-family fallback.
# 2.5 keeps the previously supported, narrower 40/100 MiB image/video bounds.
JIMENG_MODEL_SPECS = MappingProxyType({
    "seedance_2.5": JimengModelSpec(
        "seedance_2.5", 30, ("480p", "720p", "1080p"), 15000, 50, 30, 10, 10,
        40 * _MIB, 15 * _MIB, 100 * _MIB, 300, 8192, (0.4, 2.5),
        300, 6000, 1800, 30200, 30200, False),
    "seedance_2.0_mini": JimengModelSpec(
        "seedance_2.0_mini", 15, ("720p",), 4000, 12, 9, 3, 3,
        50 * _MIB, 15 * _MIB, 50 * _MIB, 1, 8192, None,
        200, 2160, 2000, 15000, 15400, True),
    "seedance_2.0_vip": JimengModelSpec(
        "seedance_2.0_vip", 15, ("720p", "1080p", "4k"), 4000, 12, 9, 3, 3,
        50 * _MIB, 15 * _MIB, 50 * _MIB, 1, 8192, None,
        200, 2160, 2000, 15000, 15400, True),
    "seedance_2.0_fast_vip": JimengModelSpec(
        "seedance_2.0_fast_vip", 15, ("720p",), 4000, 12, 9, 3, 3,
        50 * _MIB, 15 * _MIB, 50 * _MIB, 1, 8192, None,
        200, 2160, 2000, 15000, 15400, True),
})
JIMENG_MODELS = tuple(JIMENG_MODEL_SPECS)


@dataclass(frozen=True)
class JimengInputModeSpec:
    """One explicitly mapped native Seedance mode, not model qualification."""

    input_mode: Literal["text_to_video", "first_frame", "first_last_frame", "multimodal"]
    native_mode: int
    generation_mode: Literal["text_to_video", "image_to_video", "reference_to_video"]
    image_roles: tuple[Literal["first_frame", "last_frame", "reference"], ...]
    editor_mode: Literal["firstLastFrame", "multiModal"]


# Current native client configuration was read without mutations for all four
# exact model IDs. Keep one Python contract for the mode-to-role mapping.
JIMENG_INPUT_MODE_SPECS = MappingProxyType({
    "text_to_video": JimengInputModeSpec(
        "text_to_video", 1, "text_to_video", (), "firstLastFrame"),
    "first_frame": JimengInputModeSpec(
        "first_frame", 2, "image_to_video", ("first_frame",), "firstLastFrame"),
    "first_last_frame": JimengInputModeSpec(
        "first_last_frame", 3, "image_to_video", ("first_frame", "last_frame"), "firstLastFrame"),
    "multimodal": JimengInputModeSpec(
        "multimodal", 4, "reference_to_video", ("reference",), "multiModal"),
})


def jimeng_profile_compiler_id(model_id: str, input_mode: str) -> str:
    if model_id not in JIMENG_MODEL_SPECS or input_mode not in JIMENG_INPUT_MODE_SPECS:
        raise ValueError("unsupported Jimeng model or input mode")
    suffix = "" if input_mode == "multimodal" else f"-{input_mode.replace('_', '-')}"
    return f"jimeng-{model_id.replace('_', '-')}{suffix}-video-compiler"


def jimeng_profile_version(model_id: str, input_mode: str) -> str:
    if model_id not in JIMENG_MODEL_SPECS or input_mode not in JIMENG_INPUT_MODE_SPECS:
        raise ValueError("unsupported Jimeng model or input mode")
    suffix = "" if input_mode == "multimodal" else f"-{input_mode.replace('_', '-')}"
    return f"canvas-{model_id.replace('_', '-')}{suffix}-v1"


def jimeng_capability_id(model_id: str, input_mode: str) -> str:
    if model_id not in JIMENG_MODEL_SPECS or input_mode not in JIMENG_INPUT_MODE_SPECS:
        raise ValueError("unsupported Jimeng model or input mode")
    suffix = input_mode.replace("_", "-")
    return f"jimeng-{model_id.replace('_', '-')}-{suffix}-v1"
