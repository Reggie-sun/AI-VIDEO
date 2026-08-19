from __future__ import annotations

import hashlib
import importlib.util
import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    ActorIdentity,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    SecretReference,
)
from ai_video.production import seedance as seedance_adapter
from ai_video.production._state_commit_contracts import (
    _PAID_PROVIDER_PERMIT_TOKEN,
    _DurablePaidProviderSubmitPermit,
)
from ai_video.production.video import (
    ContinuityConstraintSet,
    ContinuityReferenceBinding,
    ProviderProfilePointer,
    TerminalFrameEvidence,
    VideoCapabilityVariant,
    VideoFlexibleOutputRequirement,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
    VideoSubmission,
    build_video_paid_permit_binding,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
FIXED_NOW = datetime(2026, 8, 19, 1, 0, tzinfo=UTC)
PROMPT = "A restrained cinematic orbit around the subject."

ARK_API_KEY_REFERENCE = getattr(seedance_adapter, "ARK_API_KEY_REFERENCE", None)
SEEDANCE_MODEL_IDS = getattr(seedance_adapter, "SEEDANCE_MODEL_IDS", ())
SeedancePricingSnapshot = getattr(seedance_adapter, "SeedancePricingSnapshot", None)
SeedanceCapabilityProfile = getattr(seedance_adapter, "SeedanceCapabilityProfile", None)
SeedanceProviderProfile = getattr(seedance_adapter, "SeedanceProviderProfile", None)
SeedanceTransportRequest = getattr(seedance_adapter, "SeedanceTransportRequest", object)
SeedanceTransportResponse = getattr(seedance_adapter, "SeedanceTransportResponse", None)
SeedanceVideoProvider = getattr(seedance_adapter, "SeedanceVideoProvider", None)


class _StreamResponse:
    def __init__(self, *, status: int, content_type: str, chunks: tuple[bytes, ...]):
        self.status_code = status
        self.headers = {"content-type": content_type}
        self._chunks = chunks

    def iter_bytes(self):
        yield from self._chunks


class _FakeTransport:
    def __init__(self):
        self.requests: list[SeedanceTransportRequest] = []
        self.responses: list[SeedanceTransportResponse | Exception] = []
        self.stream_response = _StreamResponse(
            status=200,
            content_type="video/mp4",
            chunks=(b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00", b"video-bytes"),
        )

    def request(self, request: SeedanceTransportRequest) -> SeedanceTransportResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    @contextmanager
    def stream(self, request: SeedanceTransportRequest):
        self.requests.append(request)
        yield self.stream_response


def _json_response(payload: dict[str, object], *, status: int = 200) -> SeedanceTransportResponse:
    return SeedanceTransportResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=json.dumps(payload, separators=(",", ":")).encode(),
    )


def _pricing() -> SeedancePricingSnapshot:
    return SeedancePricingSnapshot.create(
        snapshot_id="seedance-price-2026-08-19",
        observed_at=FIXED_NOW - timedelta(hours=1),
        expires_at=FIXED_NOW + timedelta(days=1),
        model_upper_bounds_microunits={model_id: 8_000_000 for model_id in SEEDANCE_MODEL_IDS},
    )


def _profile() -> SeedanceProviderProfile:
    return SeedanceProviderProfile.create_default(
        pricing=_pricing(),
        result_origins=("https://media.example",),
    )


def _profile_pointer(profile: SeedanceProviderProfile) -> ProviderProfilePointer:
    return ProviderProfilePointer(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_path=Path(f"provider-profiles/{profile.profile_sha256}.json"),
        profile_sha256=profile.profile_sha256,
    )


def _project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"), revision=1, content_hash=HASH_A, file_sha256=HASH_B
    )


def _registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{HASH_B}.json"),
        revision_id=HASH_B,
        content_hash=HASH_B,
        file_sha256=HASH_C,
    )


def _graph_pointer() -> DependencyGraphSnapshotPointer:
    return DependencyGraphSnapshotPointer(
        path=Path(f"state/dependency_graph.{HASH_C}.json"),
        revision_id=HASH_C,
        content_hash=HASH_C,
        file_sha256=HASH_D,
    )


def _request(
    profile: SeedanceProviderProfile,
    *,
    model_id: str = "doubao-seedance-2-5-260628",
    mode: VideoGenerationMode = VideoGenerationMode.TEXT_TO_VIDEO,
    image_bindings: tuple[VideoImageReferenceBinding, ...] = (),
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = (),
    output: VideoFlexibleOutputRequirement | None = None,
    seed: int | None = None,
    continuity_binding: ContinuityReferenceBinding | None = None,
    input_artifact_ids: tuple[str, ...] | None = None,
) -> VideoGenerationRequest:
    selected_output = output or VideoFlexibleOutputRequirement(
        timing_mode="exact_seconds",
        duration_seconds=5,
        dimension_mode="exact",
        width=1280,
        height=720,
        resolution_label="720p",
        ratio="16:9",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    return VideoGenerationRequest.create(
        generation_id="seedance-generation-1",
        provider_name="seedance",
        provider_kind="volcengine_ark_seedance",
        model_id=model_id,
        provider_profile=_profile_pointer(profile),
        target_shot_id="shot-1",
        target_shot_revision=1,
        target_shot_content_hash=HASH_A,
        target_asset_role="primary_visual",
        target_visual_strategy="generated_video",
        mode=mode,
        prompt_text=PROMPT,
        negative_prompt_text="",
        image_bindings=image_bindings,
        continuity_binding=continuity_binding,
        media_bindings=media_bindings,
        output_requirement=selected_output,
        seed=seed,
        base_project=_project_pointer(),
        base_registry=_registry_pointer(),
        base_dependency_graph=_graph_pointer(),
        input_artifact_ids=input_artifact_ids
        or (
            "shot-1",
            *(binding.asset_id for binding in image_bindings),
            *(binding.asset_id for binding in media_bindings),
        ),
        output_asset_id="video-output-1",
    )


def _paid_preview(resolved, video_preview) -> PaidProviderCallPreview:
    egress = [
        PaidProviderEgressItem(
            item_id="prompt",
            sha256=hashlib.sha256(PROMPT.encode()).hexdigest(),
            size_bytes=len(PROMPT.encode()),
            mime_type="text/plain",
            purpose="prompt",
        )
    ]
    egress.extend(
        PaidProviderEgressItem(
            item_id=binding.asset_id,
            sha256=binding.asset_sha256,
            size_bytes=binding.size_bytes,
            mime_type=binding.mime_type,
            purpose="reference",
        )
        for binding in (*resolved.image_bindings, *resolved.media_bindings)
    )
    return PaidProviderCallPreview.create(
        attempt_id="seedance-attempt-1",
        operation="video_generation",
        provider_kind=resolved.provider_kind,
        model_id=resolved.model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered",
        currency="CNY",
        estimated_cost_upper_bound_microunits=video_preview.estimated_cost_upper_bound_microunits,
        destination=video_preview.destination,
        method="POST",
        egress_items=tuple(egress),
        retention_mode="provider_standard",
        provider_policy_snapshot_id="seedance-policy-2026-08-19",
        secret_reference=SecretReference(kind="secret_store", reference_id=ARK_API_KEY_REFERENCE),
    )


def _authorization(preview: PaidProviderCallPreview) -> PaidProviderAuthorizationDecision:
    return PaidProviderAuthorizationDecision.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="operator", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in-seedance",
        budget_policy_id="budget-seedance",
        budget_currency="CNY",
        project_budget_ceiling_microunits=20_000_000,
        per_call_ceiling_microunits=10_000_000,
        egress_authorized=True,
        egress_policy_receipt_id="egress-seedance",
        live_test_authorized=True,
        live_authorization_receipt_id="live-seedance",
        issued_at=FIXED_NOW - timedelta(minutes=1),
        expires_at=FIXED_NOW + timedelta(minutes=5),
        max_submit_count=1,
    )


def _permit(resolved, video_preview, paid_preview, authorization):
    return _DurablePaidProviderSubmitPermit(
        _PAID_PROVIDER_PERMIT_TOKEN,
        binding=build_video_paid_permit_binding(
            resolved, video_preview, paid_preview, authorization
        ),
        durability_validator=lambda: True,
    )


def _accepted_receipt(resolved, paid_preview, *, task_id: str = "task-seedance-1"):
    return PaidProviderSubmitReceipt.create(
        attempt_id=paid_preview.attempt_id,
        request_fingerprint=resolved.resolved_generation_hash,
        preview_fingerprint=paid_preview.preview_fingerprint,
        gate_receipt_fingerprint=HASH_A,
        reservation_id="reservation-seedance",
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id=task_id,
        recorded_at=FIXED_NOW,
    )


def test_seedance_provider_module_exists_as_an_independent_adapter():
    assert importlib.util.find_spec("ai_video.production.seedance") is not None


def test_seedance_adapter_exposes_strict_profile_transport_and_provider_contracts():
    assert ARK_API_KEY_REFERENCE == "ARK_API_KEY"
    assert len(SEEDANCE_MODEL_IDS) == 7
    assert all(
        value is not None
        for value in (
            SeedancePricingSnapshot,
            SeedanceCapabilityProfile,
            SeedanceProviderProfile,
            SeedanceTransportResponse,
            SeedanceVideoProvider,
        )
    )


def test_transport_reprs_hide_authorization_urls_and_raw_provider_response():
    request = SeedanceTransportRequest(
        method="GET",
        url="https://media.example/signed?token=secret",
        headers={"authorization": "Bearer secret"},
    )
    response = SeedanceTransportResponse(
        status_code=200,
        headers={"x-provider-account": "private-account"},
        body=b'{"raw":"provider-response"}',
    )

    assert "secret" not in repr(request)
    assert "private-account" not in repr(response)
    assert "provider-response" not in repr(response)


def test_model_specific_frames_and_audio_only_constraints_fail_closed():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    frame_output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=57,
        dimension_mode="exact",
        width=1248,
        height=704,
        resolution_label="720p",
        ratio="16:9",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )
    assert provider.resolve(
        _request(
            profile,
            model_id="doubao-seedance-1-0-pro-250528",
            output=frame_output,
        )
    ).effective_output.frame_count == 57
    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(_request(profile, output=frame_output))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED

    audio = VideoMediaReferenceBinding(
        kind="audio",
        role="reference_audio",
        asset_id="audio-source",
        asset_sha256=HASH_B,
        mime_type="audio/wav",
        duration_millis=5_000,
        size_bytes=1_000_000,
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id="doubao-seedance-2-0-260128",
                mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                media_bindings=(audio,),
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_profile_pins_endpoint_to_known_model_and_submit_uses_exact_endpoint():
    base = _profile()
    create_profile = getattr(SeedanceProviderProfile, "create", None)
    assert create_profile is not None
    rebound = tuple(
        SeedanceCapabilityProfile(
            **{
                **entry.model_dump(),
                "api_model_id": (
                    "ep-seedance-25-prod"
                    if entry.variant.model_id == "doubao-seedance-2-5-260628"
                    else entry.api_model_id
                ),
            }
        )
        for entry in base.capabilities
    )
    profile = create_profile(
        pricing=base.pricing,
        result_origins=base.result_origins,
        capabilities=rebound,
        max_download_bytes=base.max_download_bytes,
    )
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-endpoint-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    assert resolved.provider_task_binding.request_target_id == "ep-seedance-25-prod"
    assert (
        resolved.provider_task_binding.response_model_id
        == "doubao-seedance-2-5-260628"
    )
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)
    provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    assert json.loads(transport.requests[0].body)["model"] == "ep-seedance-25-prod"

    paid_receipt = _accepted_receipt(
        resolved, paid_preview, task_id="task-endpoint-1"
    )
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )
    assert submission.provider_task_binding == resolved.provider_task_binding


def test_profile_rejects_capability_expansion_and_omitted_official_mode():
    base = _profile()
    original = next(
        entry
        for entry in base.capabilities
        if entry.variant.model_id == "doubao-seedance-2-5-260628"
        and entry.variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    )
    output_type = type(original.variant.output_capability)
    expanded_output = output_type(
        **{
            **original.variant.output_capability.model_dump(),
            "max_duration_seconds": 600,
        }
    )
    expanded_variant = VideoCapabilityVariant(
        **{
            **original.variant.model_dump(),
            "output_capability": expanded_output,
        }
    )
    expanded_entry = SeedanceCapabilityProfile(
        **{
            **original.model_dump(),
            "variant": expanded_variant,
        }
    )
    expanded = tuple(
        expanded_entry if entry.variant.capability_id == original.variant.capability_id else entry
        for entry in base.capabilities
    )

    with pytest.raises(ValueError):
        SeedanceProviderProfile.create(
            pricing=base.pricing,
            result_origins=base.result_origins,
            capabilities=expanded,
            max_download_bytes=base.max_download_bytes,
        )

    edit = next(
        entry
        for entry in base.capabilities
        if entry.variant.model_id == "doubao-seedance-2-5-260628"
        and entry.variant.mode is VideoGenerationMode.VIDEO_EDIT
    )
    widened_edit_output = type(edit.variant.output_capability)(
        **{
            **edit.variant.output_capability.model_dump(),
            "timing_modes": None,
        }
    )
    widened_edit_variant = VideoCapabilityVariant(
        **{
            **edit.variant.model_dump(),
            "output_capability": widened_edit_output,
        }
    )
    widened_edit_entry = SeedanceCapabilityProfile(
        **{**edit.model_dump(), "variant": widened_edit_variant}
    )
    widened_edit = tuple(
        widened_edit_entry
        if entry.variant.capability_id == edit.variant.capability_id
        else entry
        for entry in base.capabilities
    )
    with pytest.raises(ValueError):
        SeedanceProviderProfile.create(
            pricing=base.pricing,
            result_origins=base.result_origins,
            capabilities=widened_edit,
            max_download_bytes=base.max_download_bytes,
        )

    omitted = tuple(
        entry
        for entry in base.capabilities
        if entry.variant.capability_id != original.variant.capability_id
    )
    with pytest.raises(ValueError):
        SeedanceProviderProfile.create(
            pricing=base.pricing,
            result_origins=base.result_origins,
            capabilities=omitted,
            max_download_bytes=base.max_download_bytes,
        )


def test_poll_rejects_a_different_allowlisted_model_for_the_same_task():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(
        _json_response(
            {
                "id": "task-seedance-1",
                "model": "doubao-seedance-2-0-mini-260615",
                "status": "running",
            }
        )
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.get_status(submission, paid_receipt)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED


@pytest.mark.parametrize("provider_status", ["cancelled", "expired", "failed"])
def test_terminal_provider_statuses_normalize_to_failed(provider_status: str):
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(
        _json_response(
            {
                "id": "task-seedance-1",
                "model": "doubao-seedance-2-5-260628",
                "status": provider_status,
            }
        )
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    observation = provider.get_status(
        VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=paid_receipt),
        paid_receipt,
    )

    assert observation.state.value == "failed"
    assert observation.provider_file_id is None


def test_default_profile_covers_exact_current_model_ids_and_modes_without_aliases():
    provider = SeedanceVideoProvider(
        profile=_profile(),
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    variants = provider.capabilities().variants

    assert {variant.model_id for variant in variants} == set(SEEDANCE_MODEL_IDS)
    modes_by_model = {
        model_id: {variant.mode for variant in variants if variant.model_id == model_id}
        for model_id in SEEDANCE_MODEL_IDS
    }
    assert VideoGenerationMode.VIDEO_EDIT in modes_by_model["doubao-seedance-2-5-260628"]
    assert VideoGenerationMode.VIDEO_EXTEND in modes_by_model["doubao-seedance-2-0-260128"]
    assert modes_by_model["doubao-seedance-1-0-pro-fast-251015"] == {
        VideoGenerationMode.TEXT_TO_VIDEO,
        VideoGenerationMode.IMAGE_TO_VIDEO,
    }
    assert all("lite" not in model_id for model_id in modes_by_model)


def test_draft_profile_requires_1_5_480p_without_last_frame_or_flex():
    entry = next(
        entry
        for entry in _profile().capabilities
        if entry.variant.model_id == "doubao-seedance-1-5-pro-251215"
        and entry.variant.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )

    with pytest.raises(ValueError, match="draft"):
        SeedanceCapabilityProfile(**{**entry.model_dump(), "draft": True})

    output = entry.variant.output_capability
    assert output is not None
    narrowed_variant = VideoCapabilityVariant(
        **{
            **entry.variant.model_dump(),
            "output_capability": {
                **output.model_dump(),
                "resolution_labels": ("480p",),
            },
            "allowed_image_roles": ("first_frame",),
        }
    )
    valid = SeedanceCapabilityProfile(
        **{
            **entry.model_dump(),
            "variant": narrowed_variant,
            "output_rasters": tuple(
                raster
                for raster in entry.output_rasters
                if raster.resolution_label == "480p"
            ),
            "draft": True,
            "return_last_frame": False,
            "service_tier": "default",
        }
    )
    assert valid.draft is True


@pytest.mark.parametrize(
    ("model_id", "mode"),
    [
        ("doubao-seedance-2-5-260628", VideoGenerationMode.TEXT_TO_VIDEO),
        ("doubao-seedance-1-5-pro-251215", VideoGenerationMode.IMAGE_TO_VIDEO),
    ],
)
def test_camera_fixed_profile_rejects_unsupported_model_or_reference_image_mode(
    model_id: str, mode: VideoGenerationMode
):
    entry = next(
        entry
        for entry in _profile().capabilities
        if entry.variant.model_id == model_id and entry.variant.mode is mode
    )
    with pytest.raises(ValueError, match="camera_fixed"):
        SeedanceCapabilityProfile(**{**entry.model_dump(), "camera_fixed": True})


def test_omni_reference_task_type_is_2_5_only_and_matches_mode():
    profile = _profile()
    seedance_20 = next(
        entry
        for entry in profile.capabilities
        if entry.variant.model_id == "doubao-seedance-2-0-260128"
        and entry.variant.mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    )
    seedance_25_edit = next(
        entry
        for entry in profile.capabilities
        if entry.variant.model_id == "doubao-seedance-2-5-260628"
        and entry.variant.mode is VideoGenerationMode.VIDEO_EDIT
    )

    with pytest.raises(ValueError, match="omni_reference_task_type"):
        SeedanceCapabilityProfile(
            **{**seedance_20.model_dump(), "omni_reference_task_type": "reference"}
        )
    with pytest.raises(ValueError, match="omni_reference_task_type"):
        SeedanceCapabilityProfile(
            **{**seedance_25_edit.model_dump(), "omni_reference_task_type": "extend"}
        )


def test_image_formats_are_model_specific_and_legacy_1_0_excludes_heic():
    variants = _profile().capabilities
    seedance_10 = next(
        entry.variant
        for entry in variants
        if entry.variant.model_id == "doubao-seedance-1-0-pro-250528"
        and entry.variant.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )
    seedance_15 = next(
        entry.variant
        for entry in variants
        if entry.variant.model_id == "doubao-seedance-1-5-pro-251215"
        and entry.variant.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )

    assert "image/heic" not in seedance_10.allowed_image_mime_types
    assert "image/heif" not in seedance_10.allowed_image_mime_types
    assert "image/heic" in seedance_15.allowed_image_mime_types


def test_legacy_1_0_i2v_supports_adaptive_ratio_but_t2v_does_not():
    variants = _profile().capabilities
    i2v = next(
        entry.variant.output_capability
        for entry in variants
        if entry.variant.model_id == "doubao-seedance-1-0-pro-250528"
        and entry.variant.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )
    t2v = next(
        entry.variant.output_capability
        for entry in variants
        if entry.variant.model_id == "doubao-seedance-1-0-pro-250528"
        and entry.variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    )
    assert i2v is not None
    assert t2v is not None
    assert "adaptive" in i2v.ratios
    assert "adaptive" in i2v.dimension_modes
    assert "adaptive" not in t2v.ratios


def test_profile_declares_official_model_specific_output_pixel_mappings():
    variants = _profile().capabilities
    seedance_10 = next(
        entry
        for entry in variants
        if entry.variant.model_id == "doubao-seedance-1-0-pro-250528"
        and entry.variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    )
    seedance_20 = next(
        entry
        for entry in variants
        if entry.variant.model_id == "doubao-seedance-2-0-260128"
        and entry.variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    )

    assert any(
        raster.resolution_label == "720p"
        and raster.ratio == "16:9"
        and (raster.width, raster.height) == (1248, 704)
        for raster in seedance_10.output_rasters
    )
    assert any(
        raster.resolution_label == "4k"
        and raster.ratio == "21:9"
        and (raster.width, raster.height) == (4398, 1886)
        for raster in seedance_20.output_rasters
    )


def test_exact_output_requires_official_model_specific_pixel_mapping():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )

    def output(width: int, height: int) -> VideoFlexibleOutputRequirement:
        return VideoFlexibleOutputRequirement(
            timing_mode="exact_seconds",
            duration_seconds=5,
            dimension_mode="exact",
            width=width,
            height=height,
            resolution_label="720p",
            ratio="16:9",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=False,
        )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id="doubao-seedance-1-0-pro-250528",
                output=output(1280, 720),
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert provider.resolve(
        _request(
            profile,
            model_id="doubao-seedance-1-0-pro-250528",
            output=output(1248, 704),
        )
    ).effective_output.width == 1248


def test_seedance_legacy_seed_range_accepts_random_sentinel_and_rejects_overflow():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    legacy_output = VideoFlexibleOutputRequirement(
        timing_mode="exact_seconds",
        duration_seconds=5,
        dimension_mode="exact",
        width=1248,
        height=704,
        resolution_label="720p",
        ratio="16:9",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )

    accepted = provider.resolve(
        _request(
            profile,
            model_id="doubao-seedance-1-0-pro-250528",
            output=legacy_output,
            seed=-1,
        )
    )
    assert accepted.effective_seed == -1
    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id="doubao-seedance-1-0-pro-250528",
                output=legacy_output,
                seed=2_147_483_648,
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_seedance_2_5_edit_requires_at_least_four_second_video_input():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    short_video = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="short-video",
        asset_sha256=HASH_B,
        mime_type="video/mp4",
        duration_millis=3_000,
        size_bytes=20_000_000,
        width=1280,
        height=720,
        fps=24,
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                mode=VideoGenerationMode.VIDEO_EDIT,
                media_bindings=(short_video,),
                output=VideoFlexibleOutputRequirement(
                    timing_mode="provider_selected",
                    dimension_mode="adaptive",
                    resolution_label="720p",
                    ratio="adaptive",
                    fps=24,
                    container="mp4",
                    mime_type="video/mp4",
                    native_audio=True,
                ),
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_seedance_2_5_edit_requires_provider_selected_duration():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    video = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="edit-source",
        asset_sha256=HASH_B,
        mime_type="video/mp4",
        duration_millis=12_000,
        size_bytes=20_000_000,
        width=1920,
        height=1080,
        fps=24,
    )
    edit_profile = next(
        entry
        for entry in profile.capabilities
        if entry.variant.model_id == "doubao-seedance-2-5-260628"
        and entry.variant.mode is VideoGenerationMode.VIDEO_EDIT
    )
    assert edit_profile.variant.output_capability.timing_modes == (
        "provider_selected",
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                mode=VideoGenerationMode.VIDEO_EDIT,
                media_bindings=(video,),
                output=VideoFlexibleOutputRequirement(
                    timing_mode="exact_seconds",
                    duration_seconds=5,
                    dimension_mode="adaptive",
                    resolution_label="720p",
                    ratio="adaptive",
                    fps=24,
                    container="mp4",
                    mime_type="video/mp4",
                    native_audio=True,
                ),
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_reference_media_total_duration_fails_closed():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )

    def video(asset_id: str):
        return VideoMediaReferenceBinding(
            kind="video",
            role="reference_video",
            asset_id=asset_id,
            asset_sha256=HASH_B,
            mime_type="video/mp4",
            duration_millis=8_000,
            size_bytes=20_000_000,
            width=1280,
            height=720,
            fps=24,
        )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id="doubao-seedance-2-0-260128",
                mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                media_bindings=(video("video-a"), video("video-b")),
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_reference_video_geometry_fails_closed():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    video = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="video-too-wide",
        asset_sha256=HASH_B,
        mime_type="video/mp4",
        duration_millis=8_000,
        size_bytes=20_000_000,
        width=7000,
        height=720,
        fps=24,
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id="doubao-seedance-2-0-260128",
                mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                media_bindings=(video,),
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_seedance_image_geometry_rejects_oversized_or_out_of_ratio_inputs():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    for width, height in ((6001, 1000), (300, 1000)):
        image = VideoImageReferenceBinding(
            role="first_frame",
            asset_id=f"image-{width}-{height}",
            asset_sha256=HASH_B,
            mime_type="image/png",
            width=width,
            height=height,
            size_bytes=1_000_000,
        )
        with pytest.raises(AiVideoError) as exc_info:
            provider.resolve(
                _request(
                    profile,
                    model_id="doubao-seedance-1-5-pro-251215",
                    mode=VideoGenerationMode.IMAGE_TO_VIDEO,
                    image_bindings=(image,),
                    output=VideoFlexibleOutputRequirement(
                        timing_mode="exact_seconds",
                        duration_seconds=5,
                        dimension_mode="exact",
                        width=1280,
                        height=720,
                        resolution_label="720p",
                        ratio="16:9",
                        fps=24,
                        container="mp4",
                        mime_type="video/mp4",
                        native_audio=True,
                    ),
                )
            )
        assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_resolve_fails_closed_for_marketing_alias_and_expired_pricing():
    profile = _profile()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(_request(profile, model_id="seedance-2.5"))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED

    expired = SeedanceProviderProfile.create_default(
        pricing=SeedancePricingSnapshot.create(
            snapshot_id="expired",
            observed_at=FIXED_NOW - timedelta(days=2),
            expires_at=FIXED_NOW - timedelta(days=1),
            model_upper_bounds_microunits={
                model_id: 8_000_000 for model_id in SEEDANCE_MODEL_IDS
            },
        ),
        result_origins=("https://media.example",),
    )
    resolved = SeedanceVideoProvider(
        profile=expired,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    ).resolve(_request(expired))
    with pytest.raises(AiVideoError) as exc_info:
        SeedanceVideoProvider(
            profile=expired,
            transport=_FakeTransport(),
            credential=lambda: "rotated-test-secret",
            input_reference=lambda binding: f"asset://{binding.asset_id}",
            now=lambda: FIXED_NOW,
        ).preview(resolved)
    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED


def test_submit_consumes_one_permit_and_never_retries_unknown_post():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(RuntimeError("connection lost"))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)
    permit = _permit(resolved, video_preview, paid_preview, authorization)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.requests) == 1
    assert transport.requests[0].method == "POST"
    assert "rotated-test-secret" not in repr(transport.requests[0])
    assert "rotated-test-secret" not in str(exc_info.value)


def test_missing_injected_ark_credential_fails_before_permit_consumption_or_network():
    profile = _profile()
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)
    permit = _permit(resolved, video_preview, paid_preview, authorization)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(resolved, video_preview, paid_preview, authorization, permit)
    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED
    assert transport.requests == []
    assert permit._consume_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            resolved, video_preview, paid_preview, authorization
        )
    )


def test_credential_supplier_failure_is_sanitized_before_network():
    profile = _profile()
    transport = _FakeTransport()

    def failing_credential() -> str:
        raise RuntimeError("supplier leaked-secret detail")

    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=failing_credential,
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            _permit(resolved, video_preview, paid_preview, authorization),
        )
    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED
    assert "leaked-secret" not in str(exc_info.value)
    assert transport.requests == []


def test_input_reference_supplier_failure_is_sanitized_before_network():
    profile = _profile()
    transport = _FakeTransport()
    image = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-source",
        asset_sha256=HASH_B,
        mime_type="image/png",
        width=1280,
        height=720,
        size_bytes=1_000_000,
    )

    def failing_reference(_binding) -> str:
        raise RuntimeError("signed-url leaked-secret detail")

    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=failing_reference,
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(
        _request(
            profile,
            mode=VideoGenerationMode.IMAGE_TO_VIDEO,
            image_bindings=(image,),
            output=VideoFlexibleOutputRequirement(
                timing_mode="exact_seconds",
                duration_seconds=5,
                dimension_mode="adaptive",
                resolution_label="720p",
                ratio="adaptive",
                fps=24,
                container="mp4",
                mime_type="video/mp4",
                native_audio=True,
            ),
        )
    )
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            _permit(resolved, video_preview, paid_preview, authorization),
        )
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert "leaked-secret" not in str(exc_info.value)
    assert transport.requests == []


def test_mini_default_payload_omits_optional_defaults_but_preserves_audio_opt_out():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-seedance-mini-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        output=VideoFlexibleOutputRequirement(
            timing_mode="exact_seconds",
            duration_seconds=5,
            dimension_mode="exact",
            width=864,
            height=496,
            resolution_label="480p",
            ratio="16:9",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=False,
        ),
    )
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)

    provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    assert json.loads(transport.requests[0].body) == {
        "model": "doubao-seedance-2-0-mini-260615",
        "content": [{"type": "text", "text": PROMPT}],
        "resolution": "480p",
        "ratio": "16:9",
        "generate_audio": False,
        "duration": 5,
    }


def test_seedance_2_0_mini_continuity_binds_exact_terminal_frame_payload():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-seedance-mini-continuity-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    terminal = TerminalFrameEvidence.create(
        source_shot_id="shot-0",
        source_shot_revision=1,
        source_shot_content_hash=HASH_A,
        source_video_asset_id="video-source-0",
        source_video_sha256=HASH_B,
        source_generation_id="seedance-generation-0",
        source_request_input_hash=HASH_C,
        source_resolved_generation_hash=HASH_D,
        source_provenance_receipt_id="seedance-provenance-0",
        extraction_receipt_id=HASH_D,
        source_registry=_registry_pointer(),
        source_container_name="mp4",
        source_codec_name="h264",
        source_width=864,
        source_height=496,
        source_fps_numerator=24,
        source_fps_denominator=1,
        source_duration_milliseconds=5000,
        source_frame_count=120,
        frame_index=119,
        timestamp_numerator=119,
        timestamp_denominator=24,
        selection_rule="generated_candidate_terminal",
        extraction_contract_version="terminal-frame-v1",
        extractor_name="ffmpeg",
        extractor_version="7.1",
        extracted_asset_id="terminal-frame-shot-0",
        extracted_sha256=HASH_B,
        extracted_mime_type="image/png",
        extracted_size_bytes=1_000_000,
        extracted_width=864,
        extracted_height=496,
        extracted_color_space="srgb",
    )
    continuity = ContinuityReferenceBinding.create(
        role="first_frame",
        terminal_frame=terminal,
        target_shot_id="shot-1",
        target_shot_revision=1,
        target_shot_content_hash=HASH_A,
        constraints=ContinuityConstraintSet.create(
            scene_identity={
                "artifact_id": "scene-1",
                "revision": 1,
                "content_hash": HASH_A,
            },
            character_identities=(
                {
                    "artifact_id": "character-1",
                    "revision": 1,
                    "content_hash": HASH_B,
                },
            ),
            camera_axis="axis-east-facing-left",
            framing="medium-wide-subject-left-third",
            lighting="warm-window-key-camera-right",
            color="warm-amber-low-saturation",
            motion_direction="subject-exits-screen-right",
            exit_state="right-foot-forward-at-doorway",
            entrance_state="right-foot-forward-entering-hall",
        ),
    )
    first_frame = VideoImageReferenceBinding(
        role="first_frame",
        asset_id=terminal.extracted_asset_id,
        asset_sha256=terminal.extracted_sha256,
        mime_type=terminal.extracted_mime_type,
        width=terminal.extracted_width,
        height=terminal.extracted_height,
        size_bytes=terminal.extracted_size_bytes,
    )
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=(first_frame,),
        continuity_binding=continuity,
        input_artifact_ids=(
            "shot-1",
            terminal.source_shot_id,
            terminal.source_video_asset_id,
            terminal.extracted_asset_id,
        ),
        output=VideoFlexibleOutputRequirement(
            timing_mode="exact_seconds",
            duration_seconds=5,
            dimension_mode="exact",
            width=864,
            height=496,
            resolution_label="480p",
            ratio="16:9",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=False,
        ),
    )
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)

    provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    assert resolved.continuity_binding == continuity
    assert paid_preview.egress_items[1].sha256 == terminal.extracted_sha256
    payload = json.loads(transport.requests[0].body)
    assert payload["model"] == "doubao-seedance-2-0-mini-260615"
    assert payload["generate_audio"] is False
    assert payload["content"][1] == {
        "type": "image_url",
        "image_url": {"url": "asset://terminal-frame-shot-0"},
        "role": "first_frame",
    }


@pytest.mark.parametrize(
    ("model_id", "profile_field", "profile_value"),
    [
        ("doubao-seedance-2-0-mini-260615", "watermark", True),
        ("doubao-seedance-2-0-mini-260615", "return_last_frame", True),
        ("doubao-seedance-2-0-mini-260615", "priority", 3),
        ("doubao-seedance-1-5-pro-251215", "service_tier", "flex"),
    ],
)
def test_non_default_provider_fields_remain_explicit(
    model_id: str, profile_field: str, profile_value: object
):
    base = _profile()
    original = next(
        entry
        for entry in base.capabilities
        if entry.variant.model_id == model_id
        and entry.variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    )
    customized = SeedanceCapabilityProfile(
        **{**original.model_dump(), profile_field: profile_value}
    )
    profile = SeedanceProviderProfile.create(
        pricing=base.pricing,
        result_origins=base.result_origins,
        capabilities=tuple(
            customized
            if entry.variant.capability_id == original.variant.capability_id
            else entry
            for entry in base.capabilities
        ),
        max_download_bytes=base.max_download_bytes,
    )
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-seedance-explicit-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(
        _request(
            profile,
            model_id=model_id,
            output=VideoFlexibleOutputRequirement(
                timing_mode="exact_seconds",
                duration_seconds=5,
                dimension_mode="exact",
                width=1280,
                height=720,
                resolution_label="720p",
                ratio="16:9",
                fps=24,
                container="mp4",
                mime_type="video/mp4",
                native_audio=False,
            ),
        )
    )
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)

    provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    assert json.loads(transport.requests[0].body)[profile_field] == profile_value


def test_seedance_2_5_edit_payload_maps_explicit_reference_and_provider_fields():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-seedance-edit-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    video_binding = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="video-source",
        asset_sha256=HASH_B,
        mime_type="video/mp4",
        duration_millis=12_000,
        size_bytes=20_000_000,
        width=1920,
        height=1080,
        fps=30,
    )
    request = _request(
        profile,
        mode=VideoGenerationMode.VIDEO_EDIT,
        media_bindings=(video_binding,),
        output=VideoFlexibleOutputRequirement(
            timing_mode="provider_selected",
            dimension_mode="adaptive",
            resolution_label="1080p",
            ratio="adaptive",
            fps=24,
            container="mov",
            mime_type="video/quicktime",
            native_audio=True,
        ),
    )
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    authorization = _authorization(paid_preview)
    result = provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    payload = json.loads(transport.requests[0].body)
    assert result.external_effect_id == "task-seedance-edit-1"
    assert payload["model"] == "doubao-seedance-2-5-260628"
    assert payload["omni_reference_task_type"] == "edit"
    assert payload["duration"] == -1
    assert payload["ratio"] == "adaptive"
    assert payload["output_format"] == "mov"
    assert payload["generate_audio"] is True
    assert payload["content"][1] == {
        "type": "video_url",
        "video_url": {"url": "asset://video-source"},
        "role": "reference_video",
    }


def test_poll_and_fetch_bind_same_task_and_accept_only_allowed_origin_mp4():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.extend(
        (
            _json_response(
                {
                    "id": "task-seedance-1",
                    "model": "doubao-seedance-2-5-260628",
                    "status": "succeeded",
                    "content": {"video_url": "https://media.example/result.mp4"},
                }
            ),
            _json_response(
                {
                    "id": "task-seedance-1",
                    "model": "doubao-seedance-2-5-260628",
                    "status": "succeeded",
                    "content": {"video_url": "https://media.example/result.mp4"},
                }
            ),
        )
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )
    observation = provider.get_status(submission, paid_receipt)
    sink = bytearray()

    class _Sink:
        def write(self, data: bytes):
            sink.extend(data)
            return len(data)

    receipt = provider.fetch(submission, paid_receipt, observation, _Sink())
    assert receipt.content_type == "video/mp4"
    assert receipt.size_bytes == len(sink)
    assert all("https://media.example/result.mp4" not in repr(req) for req in transport.requests)


def test_poll_rejects_provider_response_for_a_different_task_id():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(
        _json_response(
            {
                "id": "task-seedance-other",
                "model": "doubao-seedance-2-5-260628",
                "status": "running",
            }
        )
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.get_status(submission, paid_receipt)
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


@pytest.mark.parametrize(
    ("content_type", "suffix"),
    [("video/mp4", "mp4"), ("video/quicktime", "mov")],
)
def test_fetch_accepts_only_measured_supported_video_containers(
    content_type: str, suffix: str
):
    profile = _profile()
    transport = _FakeTransport()
    query = {
        "id": "task-seedance-1",
        "model": "doubao-seedance-2-5-260628",
        "status": "succeeded",
        "content": {"video_url": f"https://media.example/result.{suffix}"},
    }
    transport.responses.extend((_json_response(query), _json_response(query)))
    transport.stream_response = _StreamResponse(
        status=200,
        content_type=content_type,
        chunks=(
            b"\x00\x00\x00\x10ftyp"
            + (b"qt  " if suffix == "mov" else b"isom")
            + b"\x00\x00\x00\x00",
            b"video-bytes",
        ),
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="exact_seconds",
        duration_seconds=5,
        dimension_mode="exact",
        width=1280,
        height=720,
        resolution_label="720p",
        ratio="16:9",
        fps=24,
        container=suffix,
        mime_type=content_type,
        native_audio=True,
    )
    resolved = provider.resolve(_request(profile, output=output))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )
    observation = provider.get_status(submission, paid_receipt)

    receipt = provider.fetch(submission, paid_receipt, observation, _FakeWriteSink())
    assert receipt.content_type == content_type
    assert receipt.size_bytes == 27


@pytest.mark.parametrize(
    ("content_type", "prefix"),
    [
        ("video/mp4", b"ftypisom\x00\x00\x00\x00"),
        ("video/mp4", b"\x00\x00\x00\x10ftypqt  \x00\x00\x00\x00"),
        ("video/quicktime", b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00"),
    ],
)
def test_fetch_rejects_malformed_or_wrong_brand_container(
    content_type: str, prefix: bytes
):
    profile = _profile()
    transport = _FakeTransport()
    query = {
        "id": "task-seedance-1",
        "model": "doubao-seedance-2-5-260628",
        "status": "succeeded",
        "content": {"video_url": "https://media.example/result"},
    }
    transport.responses.extend((_json_response(query), _json_response(query)))
    transport.stream_response = _StreamResponse(
        status=200,
        content_type=content_type,
        chunks=(prefix, b"video-bytes"),
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="exact_seconds",
        duration_seconds=5,
        dimension_mode="exact",
        width=1280,
        height=720,
        resolution_label="720p",
        ratio="16:9",
        fps=24,
        container="mov" if content_type == "video/quicktime" else "mp4",
        mime_type=content_type,
        native_audio=True,
    )
    resolved = provider.resolve(_request(profile, output=output))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )
    observation = provider.get_status(submission, paid_receipt)

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, paid_receipt, observation, _FakeWriteSink())
    assert exc_info.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID


def test_fetch_rejects_container_that_differs_from_durable_submit_intent():
    profile = _profile()
    transport = _FakeTransport()
    query = {
        "id": "task-seedance-1",
        "model": "doubao-seedance-2-5-260628",
        "status": "succeeded",
        "content": {"video_url": "https://media.example/result"},
    }
    transport.responses.extend((_json_response(query), _json_response(query)))
    transport.stream_response = _StreamResponse(
        status=200,
        content_type="video/quicktime",
        chunks=(b"\x00\x00\x00\x10ftypqt  \x00\x00\x00\x00", b"video-bytes"),
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )
    observation = provider.get_status(submission, paid_receipt)

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, paid_receipt, observation, _FakeWriteSink())
    assert exc_info.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID


def test_fetch_rejects_download_over_profile_byte_ceiling():
    base = _profile()
    profile = SeedanceProviderProfile.create(
        pricing=base.pricing,
        result_origins=base.result_origins,
        capabilities=base.capabilities,
        max_download_bytes=12,
    )
    transport = _FakeTransport()
    query = {
        "id": "task-seedance-1",
        "model": "doubao-seedance-2-5-260628",
        "status": "succeeded",
        "content": {"video_url": "https://media.example/result.mp4"},
    }
    transport.responses.extend((_json_response(query), _json_response(query)))
    transport.stream_response = _StreamResponse(
        status=200,
        content_type="video/mp4",
        chunks=(b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00", b"too-large"),
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=paid_receipt
    )
    observation = provider.get_status(submission, paid_receipt)

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, paid_receipt, observation, _FakeWriteSink())
    assert exc_info.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID


@pytest.mark.parametrize(
    ("result_url", "status", "content_type", "expected_code"),
    [
        ("https://other.example/result.mp4", 200, "video/mp4", ErrorCode.VIDEO_PROVIDER_FAILED),
        ("https://media.example/result.mp4", 302, "video/mp4", ErrorCode.VIDEO_PROVIDER_FAILED),
        ("https://media.example/result.mp4", 200, "text/html", ErrorCode.VIDEO_ARTIFACT_INVALID),
    ],
)
def test_fetch_fails_closed_for_origin_redirect_and_non_video(
    result_url: str,
    status: int,
    content_type: str,
    expected_code: ErrorCode,
):
    profile = _profile()
    transport = _FakeTransport()
    query = {
        "id": "task-seedance-1",
        "model": "doubao-seedance-2-5-260628",
        "status": "succeeded",
        "content": {"video_url": result_url},
    }
    transport.responses.extend((_json_response(query), _json_response(query)))
    transport.stream_response = _StreamResponse(
        status=status,
        content_type=content_type,
        chunks=(b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00",),
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda binding: f"asset://{binding.asset_id}",
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_receipt = _accepted_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=paid_receipt)
    observation = provider.get_status(submission, paid_receipt)

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, paid_receipt, observation, _FakeWriteSink())
    assert exc_info.value.code is expected_code


class _FakeWriteSink:
    def write(self, data: bytes):
        return len(data)
