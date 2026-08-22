from __future__ import annotations

from pathlib import Path
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
    VideoProviderRegistry,
)
from ai_video.production.video_contracts import VideoOutputCapability
from ai_video.production.hashing import canonical_sha256
from ai_video.production._video_capability_fingerprint import (
    project_capability_variant,
)
from ai_video.production.comfy_t8_video import (
    ComfyUIT8VideoProvider,
    load_t8_video_execution_profile,
)
from ai_video.production.comfy_t8_turbo_video import (
    load_t8_turbo_video_execution_profile,
    t8_turbo_capabilities,
)
from ai_video.production.comfy_t8_native_turbo_profile import (
    load_t8_native_turbo_execution_profile,
)
from ai_video.production.comfy_t8_native_turbo_video import (
    t8_native_turbo_capabilities,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


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
        self.previewed: list[object] = []
        self.preflighted: list[object] = []
        self.submitted: list[tuple[object, object, object, object]] = []
        self.statused: list[tuple[object, object]] = []
        self.fetched: list[tuple[object, object, object, object]] = []

    def capabilities(self) -> VideoProviderCapabilities:
        return self._capabilities

    def compile_request(self, provider_bound: object, requirement: object) -> object:
        self.compiled.append(provider_bound)
        return requirement

    def resolve(self, request: object) -> object:
        self.resolved.append(request)
        return request

    def preview(self, request: object) -> object:
        self.previewed.append(request)
        return SimpleNamespace(preview_fingerprint=f"preview-{id(request)}")

    def preflight(self, request: object) -> None:
        self.preflighted.append(request)

    def submit_local(
        self,
        request: object,
        preview: object,
        intent: object,
        permit: object,
    ) -> object:
        self.submitted.append((request, preview, intent, permit))
        return SimpleNamespace(submitted=True)

    def get_local_status(
        self, request: object, submission: object
    ) -> object:
        self.statused.append((request, submission))
        return SimpleNamespace(state="running")

    def fetch_local(
        self,
        request: object,
        submission: object,
        observation: object,
        sink: object,
    ) -> object:
        self.fetched.append((request, submission, observation, sink))
        return SimpleNamespace(complete=True)


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


def test_real_v1_capability_and_two_child_family_fingerprints_are_frozen() -> None:
    quality_profile = load_t8_video_execution_profile(
        REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_quality.json",
        artifact_root=REPO_ROOT,
    )
    quality_provider = object.__new__(ComfyUIT8VideoProvider)
    quality_provider.profile = quality_profile
    quality = quality_provider.capabilities()
    turbo_profile = load_t8_turbo_video_execution_profile(
        REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_turbo.json",
        artifact_root=REPO_ROOT,
    )
    turbo = t8_turbo_capabilities(turbo_profile)

    assert canonical_sha256(project_capability_variant(quality.variants[0])) == (
        "6ed812530fb4cff8fc3b3667396b1a50c3829ce5b109efa048ad649c8555aa31"
    )
    assert quality.capabilities_fingerprint == (
        "3b9e58ee57b38c51506573e9cb59127f75dd5b4ee4fe65c9efb97aed06e01761"
    )
    assert canonical_sha256(project_capability_variant(turbo.variants[0])) == (
        "1db0db35311e01b3a5a49af0caf63b9fd0163e99743bcbccf511aa10db037ffb"
    )
    assert turbo.capabilities_fingerprint == (
        "dc10a59156e1ab820f86f2fae0d8107ee7c3a55ead417a084eafeae579683799"
    )
    family = LocalH3VideoProviderFamily((_Child(quality.variants[0]), _Child(turbo.variants[0])))
    assert family.capabilities().capabilities_fingerprint == (
        "fe029252f59553434aeb23cfc0576ef5d6d476f27fb0bce57ed17ca0d7d68210"
    )


def test_live_v2_profiles_form_one_deterministic_six_child_snapshot() -> None:
    quality_profile = load_t8_video_execution_profile(
        REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_quality.json",
        artifact_root=REPO_ROOT,
    )
    quality_provider = object.__new__(ComfyUIT8VideoProvider)
    quality_provider.profile = quality_profile
    turbo_profile = load_t8_turbo_video_execution_profile(
        REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_turbo.json",
        artifact_root=REPO_ROOT,
    )
    native_profiles = tuple(
        load_t8_native_turbo_execution_profile(
            REPO_ROOT
            / f"workflows/profiles/minimax_h3_t8_{task}_turbo_native_v2.json",
            artifact_root=REPO_ROOT,
        )
        for task in ("t2va", "i2va", "fl2va", "ref2va")
    )

    assert all(profile.availability == "live-ready" for profile in native_profiles)
    variants = (
        quality_provider.capabilities().variants[0],
        t8_turbo_capabilities(turbo_profile).variants[0],
        *(
            t8_native_turbo_capabilities(profile).variants[0]
            for profile in native_profiles
        ),
    )
    family = LocalH3VideoProviderFamily(tuple(_Child(variant) for variant in variants))

    assert tuple(
        variant.capability_id for variant in family.capabilities().variants
    ) == (
        "minimax-h3-t8-fl2va-turbo-native-v2",
        "minimax-h3-t8-i2va-turbo-native-v2",
        "minimax-h3-t8-ref2va-turbo-native-v2",
        "minimax-h3-t8-t2va-quality-v1",
        "minimax-h3-t8-t2va-turbo-native-v2",
        "minimax-h3-t8-t2va-turbo-v1",
    )
    assert family.capabilities().capabilities_fingerprint == (
        "d3b8e5cc31570763aae6f7454ca794737634c345ec3ea6bbbcaadc36196381dd"
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


def _resolved_request(provider_kind: str, model_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        provider_name="comfy-local-h3-t8",
        provider_kind=provider_kind,
        model_id=model_id,
        provider_profile=SimpleNamespace(profile_version="v1"),
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        capability_id="placeholder",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        resolved_generation_hash="a" * 64,
    )


def test_family_dispatches_preview_by_exact_request_identity() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    request = _resolved_request(
        "minimax_h3_t8_t2va_turbo", "minimax-h3-t8-t2va-turbo"
    )

    preview = family.preview(request)

    assert quality.previewed == []
    assert turbo.previewed == [request]
    assert preview.preview_fingerprint == f"preview-{id(request)}"


def test_family_dispatches_preflight_by_exact_request_identity() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    request = _resolved_request(
        "minimax_h3_t8_t2va", "minimax-h3-t8-t2va-quality"
    )

    family.preflight(request)

    assert quality.preflighted == [request]
    assert turbo.preflighted == []


def test_family_dispatches_submit_local_by_exact_request_identity() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    request = _resolved_request(
        "minimax_h3_t8_t2va_turbo", "minimax-h3-t8-t2va-turbo"
    )
    preview = SimpleNamespace(preview_fingerprint="preview-token")
    intent = SimpleNamespace(intent_fingerprint="intent-token")
    permit = SimpleNamespace()

    result = family.submit_local(request, preview, intent, permit)

    assert quality.submitted == []
    assert turbo.submitted == [(request, preview, intent, permit)]
    assert result.submitted is True


def test_family_dispatches_get_local_status_by_exact_request_identity() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    request = _resolved_request(
        "minimax_h3_t8_t2va", "minimax-h3-t8-t2va-quality"
    )
    submission = SimpleNamespace(
        resolved_generation_hash=request.resolved_generation_hash,
        provider_request_id="prompt-id",
    )

    observation = family.get_local_status(request, submission)

    assert quality.statused == [(request, submission)]
    assert turbo.statused == []
    assert observation.state == "running"


def test_family_dispatches_fetch_local_by_exact_request_identity() -> None:
    quality = _quality()
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((quality, turbo))
    request = _resolved_request(
        "minimax_h3_t8_t2va_turbo", "minimax-h3-t8-t2va-turbo"
    )
    submission = SimpleNamespace(
        resolved_generation_hash=request.resolved_generation_hash,
        submission_fingerprint="c" * 64,
        submit_result_fingerprint="d" * 64,
        provider_request_id="prompt-id",
    )
    observation = SimpleNamespace(
        submission_fingerprint=submission.submission_fingerprint,
        submit_result_fingerprint=submission.submit_result_fingerprint,
        state="succeeded",
    )
    sink = SimpleNamespace()

    receipt = family.fetch_local(request, submission, observation, sink)

    assert quality.fetched == []
    assert turbo.fetched == [(request, submission, observation, sink)]
    assert receipt.complete is True


def test_family_rejects_foreign_provider_for_preview_seam() -> None:
    family = LocalH3VideoProviderFamily((_quality(), _turbo()))
    request = SimpleNamespace(
        provider_name="another-provider",
        provider_kind="minimax_h3_t8_t2va",
        model_id="minimax-h3-t8-t2va-quality",
        provider_profile=SimpleNamespace(profile_version="v1"),
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
    )

    with pytest.raises(AiVideoError) as exc_info:
        family.preview(request)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_family_rejects_unknown_identity_for_local_seam() -> None:
    family = LocalH3VideoProviderFamily((_quality(), _turbo()))
    request = SimpleNamespace(
        provider_name="comfy-local-h3-t8",
        provider_kind="unknown_kind",
        model_id="unknown",
        provider_profile=SimpleNamespace(profile_version="v1"),
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
    )

    with pytest.raises(AiVideoError) as exc_info:
        family.get_local_status(request, object())

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_family_rejects_status_for_submission_from_another_request() -> None:
    quality = _quality()
    family = LocalH3VideoProviderFamily((quality, _turbo()))
    request = _resolved_request(
        "minimax_h3_t8_t2va", "minimax-h3-t8-t2va-quality"
    )
    submission = SimpleNamespace(
        resolved_generation_hash="b" * 64,
        provider_request_id="prompt-id",
    )

    with pytest.raises(AiVideoError) as exc_info:
        family.get_local_status(request, submission)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert quality.statused == []


def test_family_rejects_fetch_for_observation_from_another_submission() -> None:
    turbo = _turbo()
    family = LocalH3VideoProviderFamily((_quality(), turbo))
    request = _resolved_request(
        "minimax_h3_t8_t2va_turbo", "minimax-h3-t8-t2va-turbo"
    )
    submission = SimpleNamespace(
        resolved_generation_hash=request.resolved_generation_hash,
        submission_fingerprint="c" * 64,
        submit_result_fingerprint="d" * 64,
        provider_request_id="prompt-id",
    )
    observation = SimpleNamespace(
        submission_fingerprint="e" * 64,
        submit_result_fingerprint=submission.submit_result_fingerprint,
        state="succeeded",
    )

    with pytest.raises(AiVideoError) as exc_info:
        family.fetch_local(request, submission, observation, SimpleNamespace())

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert turbo.fetched == []


class _FakeRemoteProvider:
    """Duck-typed remote Provider that records every call for zero-call assertions."""

    def __init__(self, name: str) -> None:
        self._name = name
        self.calls: list[str] = []

    def capabilities(self):
        self.calls.append("capabilities")
        return SimpleNamespace(provider_name=self._name, variants=())

    def resolve(self, request):
        self.calls.append("resolve")
        return request

    def preview(self, request):
        self.calls.append("preview")
        return request

    def submit(self, request, video_preview, paid_preview, authorization, permit):
        self.calls.append("submit")
        return SimpleNamespace()

    def get_status(self, submission, submit_receipt):
        self.calls.append("get_status")
        return SimpleNamespace()

    def fetch(self, submission, submit_receipt, observation, sink):
        self.calls.append("fetch")
        return SimpleNamespace()


def test_family_coexists_with_distinct_name_remote_providers_in_registry() -> None:
    family = LocalH3VideoProviderFamily((_quality(), _turbo()))
    seedance = _FakeRemoteProvider("seedance")
    hailuo = _FakeRemoteProvider("minimax_hailuo")
    cloud_h3 = _FakeRemoteProvider("minimax_h3")

    registry = VideoProviderRegistry(
        [
            ("comfy-local-h3-t8", family),
            ("seedance", seedance),
            ("minimax_hailuo", hailuo),
            ("minimax_h3", cloud_h3),
        ]
    )

    assert registry.resolve("comfy-local-h3-t8") is family
    assert registry.resolve("seedance") is seedance
    assert registry.resolve("minimax_hailuo") is hailuo
    assert registry.resolve("minimax_h3") is cloud_h3

    assert seedance.calls == []
    assert hailuo.calls == []
    assert cloud_h3.calls == []


def test_registry_rejects_duplicate_provider_name_across_family_and_fakes() -> None:
    first = LocalH3VideoProviderFamily((_quality(),))
    second = LocalH3VideoProviderFamily((_turbo(),))

    with pytest.raises(ValueError):
        VideoProviderRegistry(
            [
                ("comfy-local-h3-t8", first),
                ("comfy-local-h3-t8", second),
            ]
        )
