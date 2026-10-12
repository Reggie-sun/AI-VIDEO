"""Documented Grok media models and profile-bound video controls."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.grok_video_controls import (
    GrokTimedKeyframe,
    validate_grok_video_controls,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.video_contracts import (
    VideoBindingCardinalityConstraint,
    VideoMediaCapability,
    canonicalize_cardinality_constraints,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoOutputCapability,
    VideoOutputRecoveryStrategy,
    VideoProviderCapabilities,
)


GROK_PROFILE_VERSION = "grok-subscription-media-2026-10-12"
GROK_VIDEO_MODEL_CLASSIC = "grok-imagine-video"
GROK_VIDEO_MODEL_FULL = "grok-imagine-video-1.5"
GROK_VIDEO_MODEL_LITE = "grok-imagine-video-1.5-lite"
GROK_VIDEO_MODELS = (
    GROK_VIDEO_MODEL_CLASSIC,
    GROK_VIDEO_MODEL_FULL,
    GROK_VIDEO_MODEL_LITE,
)
# Preserve the pre-inventory public constant and every existing full 1.5 ID.
GROK_VIDEO_MODEL = GROK_VIDEO_MODEL_FULL
GROK_IMAGE_MODEL = "grok-imagine-image-2.0"

_SHA256 = r"^[0-9a-f]{64}$"
_API_ORIGIN: Literal["https://cli-chat-proxy.grok.com"] = "https://cli-chat-proxy.grok.com"
_VIDEO_IMAGE_MIMES = ("image/png", "image/jpeg", "image/webp")
VideoRatio = Literal[
    "21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "3:2", "2:3", "5:2", "adaptive",
]
_ALL_RATIOS: tuple[VideoRatio, ...] = (
    "21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "3:2", "2:3", "5:2", "adaptive",
)
_ADAPTIVE_RATIOS: tuple[VideoRatio, ...] = ("adaptive",)
_STANDARD_RESOLUTIONS = ("480p", "720p", "1080p")
_REFERENCE_RESOLUTIONS = ("480p", "720p")
_ALL_IMAGE_ROLES = ("first_frame", "last_frame", "reference")
_ALL_BINDING_ROLES = (
    "first_frame", "last_frame", "reference", "reference_video", "reference_audio",
)


class GrokProviderProfile(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    origin: Literal["https://cli-chat-proxy.grok.com"] = _API_ORIGIN
    account_fingerprint: str = Field(pattern=_SHA256)
    max_download_bytes: int = Field(default=512 * 1024 * 1024, strict=True, gt=0)
    image_resolution: Literal["1k", "2k"] = "1k"
    keyframes: tuple[GrokTimedKeyframe, ...] = Field(default=(), max_length=4)
    reference_voices: tuple[str, ...] = Field(default=(), max_length=3)

    @model_validator(mode="after")
    def _validate_controls(self) -> "GrokProviderProfile":
        validate_grok_video_controls(self.keyframes, self.reference_voices)
        return self

    @model_serializer(mode="wrap")
    def _preserve_legacy_control_defaults(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if not self.keyframes:
            data.pop("keyframes", None)
        if not self.reference_voices:
            data.pop("reference_voices", None)
        return data

    def pointer(self) -> ProviderProfilePointer:
        digest = canonical_sha256(self.model_dump(mode="json"))
        return ProviderProfilePointer(profile_id="grok-subscription-media",
            profile_version=GROK_PROFILE_VERSION,
            profile_path=Path(f"provider-profiles/{digest}.json"), profile_sha256=digest)


def _output(
    *,
    minimum: int,
    maximum: int,
    resolutions: tuple[str, ...],
    audio: tuple[bool, ...] = (False, True),
    ratios: tuple[VideoRatio, ...] = _ALL_RATIOS,
    timing_modes: tuple[Literal["exact_seconds", "nominal_seconds", "provider_selected"], ...]
    = ("nominal_seconds",),
) -> VideoOutputCapability:
    provider_selected = "provider_selected" in timing_modes
    return VideoOutputCapability(
        min_duration_seconds=minimum,
        max_duration_seconds=maximum,
        provider_selected_duration=provider_selected,
        timing_modes=timing_modes,
        dimension_modes=("adaptive",),
        resolution_labels=resolutions,
        ratios=ratios,
        fps_values=(None,),
        containers=("mp4",),
        native_audio_options=audio,
    )


def _constraint(
    roles: tuple[str, ...], minimum: int, maximum: int
) -> VideoBindingCardinalityConstraint:
    return VideoBindingCardinalityConstraint(
        roles=roles, min_count=minimum, max_count=maximum
    )


def _constraints(
    values: tuple[tuple[tuple[str, ...], int, int], ...]
) -> tuple[VideoBindingCardinalityConstraint, ...]:
    return canonicalize_cardinality_constraints(
        tuple(_constraint(roles, minimum, maximum)
              for roles, minimum, maximum in values)
    )


def _c4_static_constraints() -> tuple[VideoBindingCardinalityConstraint, ...]:
    return _constraints((
        (("first_frame",), 1, 1),
        (("last_frame",), 1, 1),
        (("reference",), 1, 1),
        (("reference_video",), 0, 0),
        (("reference_audio",), 0, 0),
        (_ALL_BINDING_ROLES, 3, 3),
    ))


def _variant(
    *,
    capability_id: str,
    model_id: str,
    mode: VideoGenerationMode,
    minimum: int,
    maximum: int,
    resolutions: tuple[str, ...],
    image_roles: tuple[Literal["first_frame", "last_frame", "reference"], ...] = (),
    required_first_frame: bool = False,
    max_references: int = 0,
    constraints: tuple[VideoBindingCardinalityConstraint, ...] = (),
    media: tuple[VideoMediaCapability, ...] = (),
    audio: tuple[bool, ...] = (False, True),
    ratios: tuple[VideoRatio, ...] = _ALL_RATIOS,
    timing_modes: tuple[Literal["exact_seconds", "nominal_seconds", "provider_selected"], ...]
    = ("nominal_seconds",),
) -> VideoCapabilityVariant:
    return VideoCapabilityVariant(
        capability_id=capability_id,
        provider_kind="grok",
        model_id=model_id,
        profile_version=GROK_PROFILE_VERSION,
        execution_kind=VideoExecutionKind.REMOTE,
        billing_kind=BillingKind.METERED,
        mode=mode,
        output_capability=_output(
            minimum=minimum,
            maximum=maximum,
            resolutions=resolutions,
            audio=audio,
            ratios=ratios,
            timing_modes=timing_modes,
        ),
        allowed_image_roles=image_roles,
        required_first_frame=required_first_frame,
        max_reference_count=max_references,
        allowed_image_mime_types=_VIDEO_IMAGE_MIMES if image_roles else (),
        max_image_bytes=20 * 1024 * 1024,
        min_image_width=1,
        min_image_height=1,
        media_capabilities=media,
        negative_prompt_supported=False,
        seed_supported=False,
        fps_supported=False,
        idempotent_submit=False,
        lookup_supported=True,
        output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
        binding_cardinality_constraints=constraints,
    )


def _grok_video_source(
    *, min_duration_millis: int = 1, max_duration_millis: int
) -> VideoMediaCapability:
    return VideoMediaCapability(
        kind="video",
        roles=("reference_video",),
        min_count=1,
        max_count=1,
        allowed_mime_types=("video/mp4",),
        max_size_bytes=128 * 1024 * 1024,
        min_duration_millis=min_duration_millis,
        max_duration_millis=max_duration_millis,
    )


def _generation_variants(
    *,
    model_id: str,
    prefix: str,
    resolutions: tuple[str, ...],
    duration: int,
    include_reference: bool,
    include_last_frame: bool,
    include_c4: bool,
    keyframe_count: int,
    voice_enabled: bool,
    preserve_legacy_ids: bool = False,
) -> list[VideoCapabilityVariant]:
    audio = (True,) if voice_enabled else (False, True)
    suffix = "-voices" if voice_enabled else ""
    variants: list[VideoCapabilityVariant] = []
    if not keyframe_count:
        variants.append(_variant(
            capability_id=(
                f"grok-imagine-video-1.5-t2v-v1"
                if preserve_legacy_ids and not suffix
                else f"{prefix}-t2v{suffix}-v1"
            ),
            model_id=model_id,
            mode=VideoGenerationMode.TEXT_TO_VIDEO,
            minimum=1,
            maximum=duration,
            resolutions=resolutions,
            audio=audio,
        ))
    if keyframe_count:
        keyframe_minimum = keyframe_count
        keyframe_maximum = 14 + keyframe_count
        image_roles: tuple[Literal["first_frame", "last_frame", "reference"], ...] = (
            "first_frame", "last_frame", "reference",
        )
        first_only_constraints = _constraints((
            (("first_frame",), 1, 1),
            (("last_frame",), 0, 0),
            (("reference",), keyframe_minimum, keyframe_maximum),
        ))
        first_last_constraints = _constraints((
            (("first_frame",), 1, 1),
            (("last_frame",), 1, 1),
            (("reference",), keyframe_minimum, keyframe_maximum),
        ))
        variants.extend((
            _variant(
                capability_id=f"{prefix}-i2v-keyframes{suffix}-v1",
                model_id=model_id,
                mode=VideoGenerationMode.IMAGE_TO_VIDEO,
                minimum=1,
                maximum=duration,
                resolutions=resolutions,
                image_roles=image_roles,
                required_first_frame=True,
                max_references=keyframe_maximum,
                constraints=first_only_constraints,
                audio=audio,
                ratios=_ADAPTIVE_RATIOS,
            ),
            _variant(
                capability_id=f"{prefix}-i2v-keyframes-last-frame{suffix}-v1",
                model_id=model_id,
                mode=VideoGenerationMode.IMAGE_TO_VIDEO,
                minimum=1,
                maximum=duration,
                resolutions=resolutions,
                image_roles=image_roles,
                required_first_frame=True,
                max_references=keyframe_maximum,
                constraints=first_last_constraints,
                audio=audio,
                ratios=_ADAPTIVE_RATIOS,
            ),
            _variant(
                capability_id=f"{prefix}-r2v-keyframes{suffix}-v1",
                model_id=model_id,
                mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                minimum=1,
                maximum=duration,
                resolutions=resolutions,
                image_roles=_ALL_IMAGE_ROLES,
                max_references=keyframe_maximum,
                constraints=_r2v_constraints(
                    minimum_references=keyframe_minimum,
                    maximum_references=keyframe_maximum,
                    minimum_total_images=keyframe_minimum,
                ),
                audio=audio,
            ),
        ))
        return variants

    variants.append(_variant(
        capability_id=(
            "grok-imagine-video-1.5-i2v-v1"
            if preserve_legacy_ids and not suffix
            else f"{prefix}-i2v{suffix}-v1"
        ),
        model_id=model_id,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        minimum=1,
        maximum=duration,
        resolutions=resolutions,
        image_roles=("first_frame",),
        required_first_frame=True,
        audio=audio,
        ratios=_ADAPTIVE_RATIOS,
    ))
    if include_last_frame:
        variants.append(_variant(
            capability_id=f"{prefix}-i2v-last-frame{suffix}-v1",
            model_id=model_id,
            mode=VideoGenerationMode.IMAGE_TO_VIDEO,
            minimum=1,
            maximum=duration,
            resolutions=resolutions,
            image_roles=("first_frame", "last_frame"),
            required_first_frame=True,
            constraints=_constraints((
                (("first_frame",), 1, 1),
                (("last_frame",), 1, 1),
                (("reference",), 0, 0),
            )),
            audio=audio,
            ratios=_ADAPTIVE_RATIOS,
        ))
    if include_c4:
        variants.append(_variant(
            capability_id=f"{prefix}-i2v-c4-static{suffix}-v1",
            model_id=model_id,
            mode=VideoGenerationMode.IMAGE_TO_VIDEO,
            minimum=1,
            maximum=duration,
            resolutions=_REFERENCE_RESOLUTIONS,
            image_roles=_ALL_IMAGE_ROLES,
            required_first_frame=True,
            max_references=1,
            constraints=_c4_static_constraints(),
            audio=audio,
            timing_modes=("exact_seconds",),
            ratios=_ADAPTIVE_RATIOS,
        ))
    if include_reference:
        variants.append(_variant(
            capability_id=f"{prefix}-r2v{suffix}-v1",
            model_id=model_id,
            mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
            minimum=1,
            maximum=min(duration, 10) if model_id == GROK_VIDEO_MODEL_CLASSIC else duration,
            resolutions=_REFERENCE_RESOLUTIONS,
            image_roles=("reference",) if model_id == GROK_VIDEO_MODEL_CLASSIC
            else _ALL_IMAGE_ROLES,
            max_references=7 if model_id == GROK_VIDEO_MODEL_CLASSIC else 14,
            constraints=(
                _constraints((
                    (("reference",), 1, 7),
                ))
                if model_id == GROK_VIDEO_MODEL_CLASSIC
                else _r2v_constraints(
                    minimum_references=0,
                    maximum_references=14,
                    minimum_total_images=0 if voice_enabled else 1,
                )
            ),
            audio=audio,
            ratios=_ALL_RATIOS,
        ))
    return variants


def _r2v_constraints(
    *, minimum_references: int, maximum_references: int, minimum_total_images: int
) -> tuple[VideoBindingCardinalityConstraint, ...]:
    maximum_total_images = maximum_references + 2
    return _constraints((
        (("first_frame",), 0, 1),
        (("last_frame",), 0, 1),
        (("reference",), minimum_references, maximum_references),
        (("last_frame", "reference"), 1 if minimum_total_images else 0, maximum_references + 1),
        (("reference_video",), 0, 0),
        (("reference_audio",), 0, 0),
        (_ALL_BINDING_ROLES, minimum_total_images, maximum_total_images),
    ))


def grok_capabilities(
    profile: GrokProviderProfile | None = None,
) -> VideoProviderCapabilities:
    """Return only model/mode variants that honor every sealed profile control."""

    keyframe_count = len({frame.asset_id for frame in profile.keyframes}) if profile is not None else 0
    voice_enabled = bool(profile and profile.reference_voices)
    has_controls = keyframe_count > 0 or voice_enabled
    variants: list[VideoCapabilityVariant] = []

    # Keep the original full 1.5 text/image capability IDs and add only
    # documented model and input-shape variants around them.
    variants.extend(_generation_variants(
        model_id=GROK_VIDEO_MODEL_FULL,
        prefix="grok-imagine-video-1.5",
        resolutions=_REFERENCE_RESOLUTIONS if has_controls else _STANDARD_RESOLUTIONS,
        duration=15,
        include_reference=not keyframe_count,
        include_last_frame=not keyframe_count,
        include_c4=not keyframe_count,
        keyframe_count=keyframe_count,
        voice_enabled=voice_enabled,
        preserve_legacy_ids=True,
    ))

    if not has_controls:
        variants.extend(_generation_variants(
            model_id=GROK_VIDEO_MODEL_CLASSIC,
            prefix="grok-imagine-video-classic",
            resolutions=_REFERENCE_RESOLUTIONS,
            duration=15,
            include_reference=True,
            include_last_frame=False,
            include_c4=False,
            keyframe_count=0,
            voice_enabled=False,
        ))
        variants.extend(_generation_variants(
            model_id=GROK_VIDEO_MODEL_LITE,
            prefix="grok-imagine-video-1.5-lite",
            resolutions=_STANDARD_RESOLUTIONS,
            duration=15,
            include_reference=False,
            include_last_frame=False,
            include_c4=False,
            keyframe_count=0,
            voice_enabled=False,
        ))
        # Classic operations inherit the exact Registry-bound source video's
        # geometry and audio. The adapter sends no output controls to xAI.
        variants.extend((
            _variant(
                capability_id="grok-imagine-video-classic-edit-v1",
                model_id=GROK_VIDEO_MODEL_CLASSIC,
                mode=VideoGenerationMode.VIDEO_EDIT,
                minimum=1,
                maximum=9,
                resolutions=("source", *_REFERENCE_RESOLUTIONS),
                media=(_grok_video_source(max_duration_millis=8_700),),
                audio=(True,),
                ratios=_ADAPTIVE_RATIOS,
                timing_modes=("nominal_seconds", "provider_selected"),
            ),
            _variant(
                capability_id="grok-imagine-video-classic-extend-v1",
                model_id=GROK_VIDEO_MODEL_CLASSIC,
                mode=VideoGenerationMode.VIDEO_EXTEND,
                minimum=4,
                maximum=25,
                resolutions=("source", *_REFERENCE_RESOLUTIONS),
                media=(_grok_video_source(
                    min_duration_millis=2_000, max_duration_millis=15_000,
                ),),
                audio=(True,),
                ratios=_ADAPTIVE_RATIOS,
            ),
        ))

    return VideoProviderCapabilities.create(provider_name="grok", variants=tuple(variants))


__all__ = [
    "GROK_IMAGE_MODEL",
    "GROK_PROFILE_VERSION",
    "GROK_VIDEO_MODEL",
    "GROK_VIDEO_MODEL_CLASSIC",
    "GROK_VIDEO_MODEL_FULL",
    "GROK_VIDEO_MODEL_LITE",
    "GROK_VIDEO_MODELS",
    "GrokProviderProfile",
    "grok_capabilities",
]
