from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily
from ai_video.production.video import (
    BillingKind,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import VideoOutputCapability


def _output() -> VideoOutputCapability:
    return VideoOutputCapability(
        min_duration_seconds=5,
        max_duration_seconds=5,
        provider_selected_duration=False,
        timing_modes=("frame_count",),
        frame_count_min=124,
        frame_count_max=124,
        frame_count_step=17,
        frame_count_remainder=5,
        dimension_modes=("exact",),
        min_width=1344,
        max_width=1344,
        min_height=768,
        max_height=768,
        dimension_multiple=32,
        resolution_labels=("h3_t8_native",),
        ratios=("16:9",),
        fps_values=(24,),
        containers=("mp4",),
        native_audio_options=(True,),
    )


def _variant(
    capability_id: str,
    *,
    provider_kind: str,
    model_id: str,
) -> VideoCapabilityVariant:
    return VideoCapabilityVariant(
        capability_id=capability_id,
        provider_kind=provider_kind,
        model_id=model_id,
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        output_capability=_output(),
        allowed_image_roles=(),
        required_first_frame=False,
        max_reference_count=0,
        allowed_image_mime_types=(),
        max_image_bytes=1,
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )


class _Child:
    def __init__(
        self,
        variant: VideoCapabilityVariant,
        *,
        provider_name: str = "comfy-local-h3-t8",
    ) -> None:
        self._capabilities = VideoProviderCapabilities.create(
            provider_name=provider_name,
            variants=(variant,),
        )
        self.compiled: list[object] = []
        self.resolved: list[object] = []

    def capabilities(self) -> VideoProviderCapabilities:
        return self._capabilities

    def compile_request(self, provider_bound: object, requirement: object) -> object:
        self.compiled.append(provider_bound)
        return requirement

    def resolve(self, request: object) -> object:
        self.resolved.append(request)
        return request


def _quality() -> _Child:
    return _Child(
        _variant(
            "minimax-h3-t8-t2va-quality-v1",
            provider_kind="minimax_h3_t8_t2va",
            model_id="minimax-h3-t8-t2va-quality",
        )
    )


def _turbo() -> _Child:
    return _Child(
        _variant(
            "minimax-h3-t8-t2va-turbo-v1",
            provider_kind="minimax_h3_t8_t2va_turbo",
            model_id="minimax-h3-t8-t2va-turbo",
        )
    )


def test_family_exposes_both_capabilities_in_deterministic_order() -> None:
    family = LocalH3VideoProviderFamily((_turbo(), _quality()))

    assert family.capabilities().provider_name == "comfy-local-h3-t8"
    assert tuple(
        variant.capability_id for variant in family.capabilities().variants
    ) == (
        "minimax-h3-t8-t2va-quality-v1",
        "minimax-h3-t8-t2va-turbo-v1",
    )


def test_family_rejects_child_from_another_provider() -> None:
    child = _Child(
        _variant("turbo-v1", provider_kind="turbo", model_id="turbo"),
        provider_name="another-provider",
    )

    with pytest.raises(AiVideoError) as exc_info:
        LocalH3VideoProviderFamily((child,))

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_family_rejects_duplicate_capability_id() -> None:
    with pytest.raises(AiVideoError) as exc_info:
        LocalH3VideoProviderFamily((_quality(), _quality()))

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_family_rejects_ambiguous_variant_identity() -> None:
    first = _quality()
    second = _Child(
        _variant(
            "another-quality-id",
            provider_kind="minimax_h3_t8_t2va",
            model_id="minimax-h3-t8-t2va-quality",
        )
    )

    with pytest.raises(AiVideoError) as exc_info:
        LocalH3VideoProviderFamily((first, second))

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_compile_dispatches_only_to_selected_capability_owner() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    provider_bound = SimpleNamespace(
        provider_name="comfy-local-h3-t8",
        capability_id="minimax-h3-t8-t2va-turbo-v1",
    )
    requirement = object()

    assert family.compile_request(provider_bound, requirement) is requirement
    assert turbo.compiled == [provider_bound]
    assert quality.compiled == []


def test_compile_fails_closed_for_unknown_capability() -> None:
    family = LocalH3VideoProviderFamily((_quality(), _turbo()))
    provider_bound = SimpleNamespace(
        provider_name="comfy-local-h3-t8",
        capability_id="unknown-v1",
    )

    with pytest.raises(AiVideoError) as exc_info:
        family.compile_request(provider_bound, object())

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_resolve_dispatches_by_exact_variant_identity() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    request = SimpleNamespace(
        provider_name="comfy-local-h3-t8",
        provider_kind="minimax_h3_t8_t2va_turbo",
        model_id="minimax-h3-t8-t2va-turbo",
        provider_profile=SimpleNamespace(profile_version="v1"),
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
    )

    assert family.resolve(request) is request
    assert turbo.resolved == [request]
    assert quality.resolved == []


def test_resolve_fails_closed_without_exact_variant_identity() -> None:
    family = LocalH3VideoProviderFamily((_quality(), _turbo()))
    request = SimpleNamespace(
        provider_name="comfy-local-h3-t8",
        provider_kind="minimax_h3_t8_t2va_turbo",
        model_id="wrong-model",
        provider_profile=SimpleNamespace(profile_version="v1"),
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
    )

    with pytest.raises(AiVideoError) as exc_info:
        family.resolve(request)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
