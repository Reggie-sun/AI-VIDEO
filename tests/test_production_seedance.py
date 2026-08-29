from __future__ import annotations

import base64
import hashlib
import importlib
import importlib.util
import json
import struct
import zlib
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    ActorIdentity,
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ToolIdentity,
)
from ai_video.production.registry import registry_semantic_sha256
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
from ai_video.production._video_continuity import C4MultiAnchorBinding
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


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def _rgba_png(width: int = 320, height: int = 320) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = b"\x00" + b"\x22\x44\x66\xff" * width
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(row * height))
        + _png_chunk(b"IEND", b"")
    )


def _provider_asset_reference(binding) -> str:
    return f"asset://asset-{binding.asset_sha256[:24]}"


def _sealed_asset_resolver(*bindings):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    receipts = []
    evidence = {}
    for index, binding in enumerate(bindings):
        confirmation = f"ark-console-confirmation-{index}".encode()
        provider_asset_id = f"asset-test-{index}-{binding.asset_sha256[:16]}"
        receipts.append(
            asset_module.SeedanceAssetMaterializationReceipt.create(
                source_asset_id=binding.asset_id,
                source_asset_sha256=binding.asset_sha256,
                source_mime_type=binding.mime_type,
                source_size_bytes=binding.size_bytes,
                provider_asset_id=provider_asset_id,
                provider_asset_group_id=f"group-test-{index}",
                materialization_scope="aigc",
                observed_status="Active",
                observed_at=FIXED_NOW,
                observed_by=ActorIdentity(actor_id="operator", actor_kind="human"),
                provider_confirmation_sha256=hashlib.sha256(confirmation).hexdigest(),
                rights_source_note="Synthetic test fixture.",
            )
        )
        evidence[provider_asset_id] = confirmation
    return asset_module.SeedanceAssetReferenceResolver(
        tuple(receipts), provider_confirmation_evidence=evidence
    )


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


def test_historical_profile_without_output_recovery_strategy_reopens_with_same_hash():
    current = _profile()
    payload = current.model_dump(mode="json")
    for capability in payload["capabilities"]:
        capability["variant"].pop("output_recovery_strategy")
    payload["profile_sha256"] = canonical_sha256(
        {key: value for key, value in payload.items() if key != "profile_sha256"}
    )

    reopened = SeedanceProviderProfile.model_validate(payload)

    assert reopened.profile_sha256 == payload["profile_sha256"]
    assert all(
        capability.variant.output_recovery_strategy is None
        for capability in reopened.capabilities
    )
    assert "output_recovery_strategy" not in reopened.model_dump_json()


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
    c4_multi_anchor_binding: C4MultiAnchorBinding | None = None,
    input_artifact_ids: tuple[str, ...] | None = None,
    base_registry: RegistrySnapshotPointer | None = None,
) -> VideoGenerationRequest:
    selected_output = output or VideoFlexibleOutputRequirement(
        timing_mode=(
            "nominal_seconds"
            if model_id == "doubao-seedance-2-0-mini-260615"
            else "exact_seconds"
        ),
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
        c4_multi_anchor_binding=c4_multi_anchor_binding,
        continuity_binding=continuity_binding,
        media_bindings=media_bindings,
        output_requirement=selected_output,
        seed=seed,
        base_project=_project_pointer(),
        base_registry=base_registry or _registry_pointer(),
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


def _authorization(
    preview: PaidProviderCallPreview,
    *,
    egress_policy_receipt_id: str = "egress-seedance",
) -> PaidProviderAuthorizationDecision:
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
        egress_policy_receipt_id=egress_policy_receipt_id,
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


def _remote_refresh_permit(submission, observation, fetch_receipt):
    video_module = importlib.import_module("ai_video.production.remote_media")
    materialization = fetch_receipt.remote_materialization
    assert materialization is not None
    return video_module._RemoteReferenceRefreshPermit(
        video_module._REMOTE_REFERENCE_REFRESH_PERMIT_TOKEN,
        submission_fingerprint=submission.submission_fingerprint,
        observation_fingerprint=observation.observation_fingerprint,
        fetch_fingerprint=fetch_receipt.fetch_fingerprint,
        materialization_receipt_id=materialization.content_hash,
        durability_validator=lambda: True,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    ).resolve(_request(expired))
    with pytest.raises(AiVideoError) as exc_info:
        SeedanceVideoProvider(
            profile=expired,
            transport=_FakeTransport(),
            credential=lambda: "rotated-test-secret",
            input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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


def test_submit_rejects_authorization_not_selected_by_durable_permit_before_network():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-must-not-submit"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(_request(profile))
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    durable_authorization = _authorization(
        paid_preview, egress_policy_receipt_id="egress-policy-r1"
    )
    submit_authorization = _authorization(
        paid_preview, egress_policy_receipt_id="egress-policy-r2"
    )
    permit = _permit(
        resolved,
        video_preview,
        paid_preview,
        durable_authorization,
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            submit_authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert transport.requests == []
    assert permit._validate_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            resolved,
            video_preview,
            paid_preview,
            durable_authorization,
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
        input_reference=_provider_asset_reference,
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


def test_local_registry_asset_id_cannot_masquerade_as_ark_asset_uri():
    profile = _profile()
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=lambda _binding: "asset://asset-local-registry-1",
        now=lambda: FIXED_NOW,
    )
    first_frame = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-local-keyframe-1",
        asset_sha256=HASH_B,
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=1_000_000,
    )
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=(first_frame,),
        output=VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds",
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

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            _permit(resolved, video_preview, paid_preview, authorization),
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.requests == []

    asset_module = importlib.import_module("ai_video.production.seedance_asset")

    class ForgedResolver(asset_module.SeedanceAssetReferenceResolver):
        def __init__(self):
            pass

        def __call__(self, _binding):
            return "asset://asset-local-registry-1"

    forged_transport = _FakeTransport()
    forged_transport.responses.append(_json_response({"id": "task-subclass-bypass"}))
    forged_provider = SeedanceVideoProvider(
        profile=profile,
        transport=forged_transport,
        credential=lambda: "rotated-test-secret",
        input_reference=ForgedResolver(),
        now=lambda: FIXED_NOW,
    )
    forged_permit = _permit(resolved, video_preview, paid_preview, authorization)

    with pytest.raises(AiVideoError) as subclass_exc:
        forged_provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            forged_permit,
        )

    permit_binding = build_video_paid_permit_binding(
        resolved, video_preview, paid_preview, authorization
    )
    assert subclass_exc.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert forged_transport.requests == []
    assert forged_permit._validate_paid_provider_operation_permit(**permit_binding)


def test_active_ark_asset_receipt_resolves_exact_local_first_frame_identity():
    assert importlib.util.find_spec("ai_video.production.seedance_asset") is not None
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    confirmation = b"ark-console-active-asset-confirmation"
    receipt = asset_module.SeedanceAssetMaterializationReceipt.create(
        source_asset_id="image-local-keyframe-1",
        source_asset_sha256=HASH_B,
        source_mime_type="image/png",
        source_size_bytes=1_000_000,
        provider_asset_id="asset-20260820153000-alice1",
        provider_asset_group_id="group-20260820150000-alice1",
        materialization_scope="aigc",
        observed_status="Active",
        observed_at=FIXED_NOW,
        observed_by=ActorIdentity(actor_id="operator", actor_kind="human"),
        provider_confirmation_sha256=hashlib.sha256(confirmation).hexdigest(),
        rights_source_note="Project-owned fictional character keyframe.",
    )
    resolver = asset_module.SeedanceAssetReferenceResolver(
        (receipt,),
        provider_confirmation_evidence={receipt.provider_asset_id: confirmation},
    )
    first_frame = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-local-keyframe-1",
        asset_sha256=HASH_B,
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=1_000_000,
    )

    assert resolver(first_frame) == "asset://asset-20260820153000-alice1"
    assert receipt.content_hash != HASH_A


def test_ark_asset_materialization_owner_is_public_production_api():
    production = importlib.import_module("ai_video.production")
    asset_module = importlib.import_module("ai_video.production.seedance_asset")

    assert (
        production.SeedanceAssetMaterializationReceipt
        is asset_module.SeedanceAssetMaterializationReceipt
    )
    assert (
        production.SeedanceAssetReferenceResolver
        is asset_module.SeedanceAssetReferenceResolver
    )
    assert (
        production.SeedanceSyntheticImageAuthorizer
        is asset_module.SeedanceSyntheticImageAuthorizer
    )
    assert (
        production.SeedanceSyntheticImageReferenceReceipt
        is asset_module.SeedanceSyntheticImageReferenceReceipt
    )
    assert (
        production.SeedanceSyntheticImageReceiptBinding
        is asset_module.SeedanceSyntheticImageReceiptBinding
    )
    assert (
        production.SeedanceSyntheticImageEgressPolicyReceipt
        is asset_module.SeedanceSyntheticImageEgressPolicyReceipt
    )
    assert (
        production.SeedanceSyntheticImageReferenceResolver
        is asset_module.SeedanceSyntheticImageReferenceResolver
    )


def test_ark_asset_resolver_rejects_tampered_confirmation_evidence():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    confirmation = b"ark-console-active-asset-confirmation"
    receipt = asset_module.SeedanceAssetMaterializationReceipt.create(
        source_asset_id="image-local-keyframe-1",
        source_asset_sha256=HASH_B,
        source_mime_type="image/png",
        source_size_bytes=1_000_000,
        provider_asset_id="asset-20260820153000-alice1",
        provider_asset_group_id="group-20260820150000-alice1",
        materialization_scope="aigc",
        observed_status="Active",
        observed_at=FIXED_NOW,
        observed_by=ActorIdentity(actor_id="operator", actor_kind="human"),
        provider_confirmation_sha256=hashlib.sha256(confirmation).hexdigest(),
        rights_source_note="Project-owned fictional character keyframe.",
    )

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceAssetReferenceResolver(
            (receipt,),
            provider_confirmation_evidence={
                receipt.provider_asset_id: b"tampered-confirmation"
            },
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_ark_asset_resolver_rejects_local_input_hash_mismatch():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    confirmation = b"ark-console-active-asset-confirmation"
    receipt = asset_module.SeedanceAssetMaterializationReceipt.create(
        source_asset_id="image-local-keyframe-1",
        source_asset_sha256=HASH_B,
        source_mime_type="image/png",
        source_size_bytes=1_000_000,
        provider_asset_id="asset-20260820153000-alice1",
        provider_asset_group_id="group-20260820150000-alice1",
        materialization_scope="aigc",
        observed_status="Active",
        observed_at=FIXED_NOW,
        observed_by=ActorIdentity(actor_id="operator", actor_kind="human"),
        provider_confirmation_sha256=hashlib.sha256(confirmation).hexdigest(),
        rights_source_note="Project-owned fictional character keyframe.",
    )
    resolver = asset_module.SeedanceAssetReferenceResolver(
        (receipt,),
        provider_confirmation_evidence={receipt.provider_asset_id: confirmation},
    )
    changed_first_frame = VideoImageReferenceBinding(
        role="first_frame",
        asset_id=receipt.source_asset_id,
        asset_sha256=HASH_D,
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=1_000_000,
    )

    with pytest.raises(AiVideoError) as exc_info:
        resolver(changed_first_frame)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observed_status", "Processing"),
        ("observed_by", ActorIdentity(actor_id="bot", actor_kind="automation")),
    ],
)
def test_ark_asset_receipt_requires_human_observed_active_state(field, value):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    confirmation = b"ark-console-active-asset-confirmation"
    values = {
        "source_asset_id": "image-local-keyframe-1",
        "source_asset_sha256": HASH_B,
        "source_mime_type": "image/png",
        "source_size_bytes": 1_000_000,
        "provider_asset_id": "asset-20260820153000-alice1",
        "provider_asset_group_id": "group-20260820150000-alice1",
        "materialization_scope": "aigc",
        "observed_status": "Active",
        "observed_at": FIXED_NOW,
        "observed_by": ActorIdentity(actor_id="operator", actor_kind="human"),
        "provider_confirmation_sha256": hashlib.sha256(confirmation).hexdigest(),
        "rights_source_note": "Project-owned fictional character keyframe.",
    }
    values[field] = value

    with pytest.raises(ValidationError):
        asset_module.SeedanceAssetMaterializationReceipt.create(**values)


def _synthetic_receipt(
    asset_module,
    binding: VideoImageReferenceBinding,
    *,
    mode: VideoGenerationMode = VideoGenerationMode.IMAGE_TO_VIDEO,
    classification: str = "clearly_illustrated_anime_non_real_character",
    attested_by: ActorIdentity | None = None,
    registry_revision_id: str = HASH_C,
    permitted_use: str = "Seedance I2V test fixture.",
    source_record_id: str = "source-generation-receipt-1",
    source_tool: ToolIdentity | None = None,
    source_evidence_sha256: str = HASH_D,
):
    return asset_module.SeedanceSyntheticImageReferenceReceipt.create(
        source_asset_id=binding.asset_id,
        source_registry_revision_id=registry_revision_id,
        source_asset_sha256=binding.asset_sha256,
        source_mime_type=binding.mime_type,
        source_size_bytes=binding.size_bytes,
        source_width=binding.width,
        source_height=binding.height,
        creator=ActorIdentity(actor_id="fictional-character-artist", actor_kind="human"),
        source_record_id=source_record_id,
        source_tool=source_tool
        or ToolIdentity(name="gpt-image-2", version="2026-08-20"),
        source_evidence_sha256=source_evidence_sha256,
        rights_source_note="Project-owned synthetic illustrated character.",
        classification=classification,
        attested_by=attested_by
        or ActorIdentity(actor_id="rights-reviewer", actor_kind="human"),
        task_scope_id="seedance-synthetic-test-1",
        attested_at=FIXED_NOW,
        transport="inline_base64",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-0-mini-260615",
        mode=mode.value,
        permitted_use=permitted_use,
    )


def _synthetic_policy_receipt(
    asset_module,
    *children,
    mode: VideoGenerationMode = VideoGenerationMode.IMAGE_TO_VIDEO,
    attempt_id: str = "seedance-attempt-1",
    request_fingerprint: str = HASH_A,
    preview_fingerprint: str = HASH_B,
    model_id: str = "doubao-seedance-2-0-mini-260615",
):
    return asset_module.SeedanceSyntheticImageEgressPolicyReceipt.create(
        task_scope_id="seedance-synthetic-test-1",
        attempt_id=attempt_id,
        request_fingerprint=request_fingerprint,
        preview_fingerprint=preview_fingerprint,
        prompt_sha256=hashlib.sha256(PROMPT.encode()).hexdigest(),
        prompt_size_bytes=len(PROMPT.encode()),
        provider_kind="volcengine_ark_seedance",
        model_id=model_id,
        mode=mode.value,
        transport="inline_base64",
        destination="https://ark.cn-beijing.volces.com",
        retention_mode="provider_standard",
        children=children,
    )


def _canonical_model_bytes(model) -> bytes:
    return json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _synthetic_evidence_source(
    asset_module,
    receipts,
    aggregate,
    *,
    source_records: dict[str, bytes] | None = None,
):
    evidence = {
        f"seedance-synthetic-egress:{aggregate.content_hash}": _canonical_model_bytes(
            aggregate
        )
    }
    evidence.update(
        {
            f"seedance-synthetic-image:{receipt.content_hash}": _canonical_model_bytes(
                receipt
            )
            for receipt in receipts
        }
    )
    evidence.update(source_records or {})
    return evidence.__getitem__


def _synthetic_registry(
    *bindings: VideoImageReferenceBinding,
    record_updates: dict[str, object] | None = None,
):
    records = tuple(
        AssetRecord(
            asset_id=binding.asset_id,
            asset_type=AssetType.IMAGE,
            artifact_path=Path(f"assets/imported/{binding.asset_sha256}.png"),
            sha256=binding.asset_sha256,
            size_bytes=binding.size_bytes,
            mime_type=binding.mime_type,
            width=binding.width,
            height=binding.height,
            source_kind=AssetSourceKind.GENERATED,
            tool=ToolIdentity(name="gpt-image-2", version="2026-08-20"),
            input_fingerprint=HASH_A,
            creation_receipt_id="source-generation-receipt-1",
            usage_license="project-owned-synthetic",
        ).model_copy(update=record_updates or {})
        for binding in bindings
    )
    provisional = AssetRegistrySnapshot(
        schema_version="2.0",
        revision_id=HASH_A,
        content_hash=HASH_A,
        assets=records,
    )
    revision_id = registry_semantic_sha256(provisional)
    registry = provisional.model_copy(
        update={"revision_id": revision_id, "content_hash": revision_id}
    )
    payload = _canonical_model_bytes(registry) + b"\n"
    pointer = RegistrySnapshotPointer(
        path=Path(f"assets/registry.{revision_id}.json"),
        revision_id=revision_id,
        content_hash=revision_id,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    return registry, payload, pointer


def test_synthetic_png_resolver_seals_exact_bytes_and_request_aggregate():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-anime-first-frame-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )
    registry, registry_bytes, _ = _synthetic_registry(binding)
    receipt = _synthetic_receipt(
        asset_module, binding, registry_revision_id=registry.revision_id
    )
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    aggregate = _synthetic_policy_receipt(asset_module, child)
    resolver = asset_module.SeedanceSyntheticImageReferenceResolver(
        (receipt,),
        policy_receipt=aggregate,
        image_bytes={binding.asset_id: png},
        evidence_source=_synthetic_evidence_source(
            asset_module, (receipt,), aggregate
        ),
        registry_snapshot_bytes=registry_bytes,
    )

    assert resolver(binding) == (
        "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    )
    assert resolver.egress_policy_receipt_id == (
        f"seedance-synthetic-egress:{aggregate.content_hash}"
    )
    assert base64.b64encode(png).decode("ascii") not in repr(resolver)


@pytest.mark.parametrize("terminator", [b"", b"\n\n"])
def test_synthetic_resolver_rejects_noncanonical_registry_terminator(terminator):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-anime-registry-terminator-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )
    registry, registry_bytes, _ = _synthetic_registry(binding)
    receipt = _synthetic_receipt(
        asset_module, binding, registry_revision_id=registry.revision_id
    )
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    aggregate = _synthetic_policy_receipt(asset_module, child)

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceSyntheticImageReferenceResolver(
            (receipt,),
            policy_receipt=aggregate,
            image_bytes={binding.asset_id: png},
            evidence_source=_synthetic_evidence_source(
                asset_module, (receipt,), aggregate
            ),
            registry_snapshot_bytes=registry_bytes.rstrip(b"\n") + terminator,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert "Registry evidence is not canonical" in str(exc_info.value)


def test_synthetic_resolver_rejects_unreopenable_canonical_evidence():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-anime-first-frame-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )
    receipt = _synthetic_receipt(asset_module, binding)
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    aggregate = _synthetic_policy_receipt(asset_module, child)

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceSyntheticImageReferenceResolver(
            (receipt,),
            policy_receipt=aggregate,
            image_bytes={binding.asset_id: png},
            evidence_source=lambda _evidence_id: b"{}",
            registry_snapshot_bytes=b"{}",
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_synthetic_resolver_rejects_registry_asset_record_mismatch():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-anime-first-frame-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )
    mismatched_registry_binding = binding.model_copy(update={"asset_sha256": HASH_D})
    registry, registry_bytes, _ = _synthetic_registry(mismatched_registry_binding)
    receipt = _synthetic_receipt(
        asset_module, binding, registry_revision_id=registry.revision_id
    )
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    aggregate = _synthetic_policy_receipt(asset_module, child)

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceSyntheticImageReferenceResolver(
            (receipt,),
            policy_receipt=aggregate,
            image_bytes={binding.asset_id: png},
            evidence_source=_synthetic_evidence_source(
                asset_module, (receipt,), aggregate
            ),
            registry_snapshot_bytes=registry_bytes,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_synthetic_receipt_rejects_real_or_protected_identity():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-ineligible-person-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )

    with pytest.raises(ValidationError):
        _synthetic_receipt(
            asset_module,
            binding,
            classification="real_person_or_protected_identity",
        )


def test_synthetic_receipt_rejects_unattested_photorealistic_fictional_identity():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-unattested-photorealistic-fictional-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )

    with pytest.raises(ValidationError):
        _synthetic_receipt(
            asset_module,
            binding,
            classification="synthetic_photorealistic_person",
        )


def test_synthetic_receipt_permits_attested_project_owned_photorealistic_fictional_identity():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-attested-photorealistic-fictional-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )

    receipt = _synthetic_receipt(
        asset_module,
        binding,
        classification="synthetic_photorealistic_person",
        permitted_use=(
            "project-owned-fictional-no-protected-identity:seedance-i2v"
        ),
    )

    assert receipt.classification == "synthetic_photorealistic_person"
    assert receipt.attested_by.actor_kind == "human"


def test_synthetic_photorealistic_reference_to_video_requires_mode_specific_claim():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png(width=864, height=496)
    binding = VideoImageReferenceBinding(
        role="reference",
        asset_id="image-fictional-r2v-reference-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=len(png),
    )

    with pytest.raises(ValidationError):
        _synthetic_receipt(
            asset_module,
            binding,
            mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
            classification="synthetic_photorealistic_person",
            permitted_use=(
                "project-owned-fictional-no-protected-identity:seedance-i2v"
            ),
        )

    receipt = _synthetic_receipt(
        asset_module,
        binding,
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        classification="synthetic_photorealistic_person",
        permitted_use="project-owned-fictional-no-protected-identity:seedance-r2v",
    )
    assert receipt.mode == "reference_to_video"
    assert receipt.permitted_use.endswith(":seedance-r2v")
    assert receipt.attested_by.actor_kind == "human"


def test_synthetic_receipt_requires_human_attestation():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-anime-first-frame-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )

    with pytest.raises(ValidationError):
        _synthetic_receipt(
            asset_module,
            binding,
            attested_by=ActorIdentity(actor_id="classifier", actor_kind="automation"),
        )


@pytest.mark.parametrize(
    "record_updates",
    [
        {"source_kind": AssetSourceKind.IMPORTED},
        {"tool": ToolIdentity(name="unknown-tool", version="1")},
        {"creation_receipt_id": "different-generation-receipt"},
        {"usage_license": "unknown"},
    ],
)
def test_photorealistic_fictional_resolver_rejects_unsealed_registry_provenance(
    record_updates,
):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    source_evidence = b"canonical-source-generation-receipt"
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-photorealistic-fictional-provenance-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )
    registry, registry_bytes, _ = _synthetic_registry(
        binding,
        record_updates=record_updates,
    )
    receipt = _synthetic_receipt(
        asset_module,
        binding,
        classification="synthetic_photorealistic_person",
        registry_revision_id=registry.revision_id,
        permitted_use=(
            "project-owned-fictional-no-protected-identity:seedance-i2v"
        ),
        source_evidence_sha256=hashlib.sha256(source_evidence).hexdigest(),
    )
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    aggregate = _synthetic_policy_receipt(asset_module, child)

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceSyntheticImageReferenceResolver(
            (receipt,),
            policy_receipt=aggregate,
            image_bytes={binding.asset_id: png},
            evidence_source=_synthetic_evidence_source(
                asset_module,
                (receipt,),
                aggregate,
                source_records={receipt.source_record_id: source_evidence},
            ),
            registry_snapshot_bytes=registry_bytes,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert "provenance is not sealed" in str(exc_info.value)


@pytest.mark.parametrize(
    "source_records",
    [
        {},
        {"terminal-frame-extraction-receipt-1": b"tampered-source-evidence"},
    ],
)
def test_photorealistic_fictional_resolver_reopens_exact_source_evidence(
    source_records,
):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    png = _rgba_png()
    source_record_id = "terminal-frame-extraction-receipt-1"
    source_evidence = b"canonical-terminal-frame-extraction-receipt"
    source_tool = ToolIdentity(name="ffmpeg", version="9c33b2f")
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-photorealistic-fictional-source-evidence-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(png),
    )
    registry, registry_bytes, _ = _synthetic_registry(
        binding,
        record_updates={
            "source_kind": AssetSourceKind.DERIVED,
            "tool": source_tool,
            "creation_receipt_id": source_record_id,
            "usage_license": "provider-output",
        },
    )
    receipt = _synthetic_receipt(
        asset_module,
        binding,
        classification="synthetic_photorealistic_person",
        registry_revision_id=registry.revision_id,
        permitted_use=(
            "project-owned-fictional-no-protected-identity:seedance-i2v"
        ),
        source_record_id=source_record_id,
        source_tool=source_tool,
        source_evidence_sha256=hashlib.sha256(source_evidence).hexdigest(),
    )
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    aggregate = _synthetic_policy_receipt(asset_module, child)

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceSyntheticImageReferenceResolver(
            (receipt,),
            policy_receipt=aggregate,
            image_bytes={binding.asset_id: png},
            evidence_source=_synthetic_evidence_source(
                asset_module,
                (receipt,),
                aggregate,
                source_records=source_records,
            ),
            registry_snapshot_bytes=registry_bytes,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_synthetic_resolver_rejects_tampered_bytes_and_noncanonical_children():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    first_png = _rgba_png()
    last_png = _rgba_png(width=321)
    first = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-anime-first-frame-1",
        asset_sha256=hashlib.sha256(first_png).hexdigest(),
        mime_type="image/png",
        width=320,
        height=320,
        size_bytes=len(first_png),
    )
    last = VideoImageReferenceBinding(
        role="last_frame",
        asset_id="image-anime-last-frame-1",
        asset_sha256=hashlib.sha256(last_png).hexdigest(),
        mime_type="image/png",
        width=321,
        height=320,
        size_bytes=len(last_png),
    )
    registry, registry_bytes, _ = _synthetic_registry(first, last)
    first_receipt = _synthetic_receipt(
        asset_module, first, registry_revision_id=registry.revision_id
    )
    last_receipt = _synthetic_receipt(
        asset_module, last, registry_revision_id=registry.revision_id
    )
    first_child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=first.role,
        asset_id=first.asset_id,
        receipt_content_hash=first_receipt.content_hash,
    )
    last_child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=last.role,
        asset_id=last.asset_id,
        receipt_content_hash=last_receipt.content_hash,
    )

    with pytest.raises(ValidationError):
        _synthetic_policy_receipt(asset_module, last_child, first_child)

    aggregate = _synthetic_policy_receipt(asset_module, first_child, last_child)
    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceSyntheticImageReferenceResolver(
            (first_receipt, last_receipt),
            policy_receipt=aggregate,
            image_bytes={
                first.asset_id: first_png + b"tampered",
                last.asset_id: last_png,
            },
            evidence_source=_synthetic_evidence_source(
                asset_module, (first_receipt, last_receipt), aggregate
            ),
            registry_snapshot_bytes=registry_bytes,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def _synthetic_submit_fixture(
    *,
    mode: VideoGenerationMode = VideoGenerationMode.IMAGE_TO_VIDEO,
    binding_role: str = "first_frame",
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = (),
    registry_file_sha256: str | None = None,
    classification: str = "clearly_illustrated_anime_non_real_character",
    permitted_use: str = "Seedance I2V test fixture.",
    registry_record_updates: dict[str, object] | None = None,
    source_record_id: str = "source-generation-receipt-1",
    source_tool: ToolIdentity | None = None,
    source_evidence_bytes: bytes | None = None,
):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    profile = _profile()
    png = _rgba_png(width=864, height=496)
    binding = VideoImageReferenceBinding(
        role=binding_role,
        asset_id="image-anime-first-frame-1",
        asset_sha256=hashlib.sha256(png).hexdigest(),
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=len(png),
    )
    registry, registry_bytes, registry_pointer = _synthetic_registry(
        binding,
        record_updates=registry_record_updates,
    )
    receipt = _synthetic_receipt(
        asset_module,
        binding,
        mode=mode,
        classification=classification,
        registry_revision_id=registry.revision_id,
        permitted_use=permitted_use,
        source_record_id=source_record_id,
        source_tool=source_tool,
        source_evidence_sha256=(
            HASH_D
            if source_evidence_bytes is None
            else hashlib.sha256(source_evidence_bytes).hexdigest()
        ),
    )
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=binding.role,
        asset_id=binding.asset_id,
        receipt_content_hash=receipt.content_hash,
    )
    placeholder = _synthetic_policy_receipt(asset_module, child, mode=mode)
    placeholder_resolver = asset_module.SeedanceSyntheticImageReferenceResolver(
        (receipt,),
        policy_receipt=placeholder,
        image_bytes={binding.asset_id: png},
        evidence_source=_synthetic_evidence_source(
            asset_module,
            (receipt,),
            placeholder,
            source_records=(
                None
                if source_evidence_bytes is None
                else {source_record_id: source_evidence_bytes}
            ),
        ),
        registry_snapshot_bytes=registry_bytes,
    )
    bootstrap = SeedanceVideoProvider(
        profile=profile,
        transport=_FakeTransport(),
        credential=lambda: "rotated-test-secret",
        input_reference=placeholder_resolver,
        now=lambda: FIXED_NOW,
    )
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        mode=mode,
        image_bindings=(binding,),
        media_bindings=media_bindings,
        base_registry=(
            registry_pointer
            if registry_file_sha256 is None
            else registry_pointer.model_copy(
                update={"file_sha256": registry_file_sha256}
            )
        ),
        output=VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds",
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
    resolved = bootstrap.resolve(request)
    video_preview = bootstrap.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    aggregate = _synthetic_policy_receipt(
        asset_module,
        child,
        mode=mode,
        attempt_id=paid_preview.attempt_id,
        request_fingerprint=resolved.resolved_generation_hash,
        preview_fingerprint=paid_preview.preview_fingerprint,
        model_id=resolved.model_id,
    )
    resolver = asset_module.SeedanceSyntheticImageReferenceResolver(
        (receipt,),
        policy_receipt=aggregate,
        image_bytes={binding.asset_id: png},
        evidence_source=_synthetic_evidence_source(
            asset_module,
            (receipt,),
            aggregate,
            source_records=(
                None
                if source_evidence_bytes is None
                else {source_record_id: source_evidence_bytes}
            ),
        ),
        registry_snapshot_bytes=registry_bytes,
    )
    return (
        profile,
        resolved,
        video_preview,
        paid_preview,
        resolver,
        png,
        receipt,
        aggregate,
    )


def test_synthetic_authorizer_rejects_unreopenable_policy_evidence():
    (
        _,
        _,
        _,
        paid_preview,
        resolver,
        _,
        _,
        _,
    ) = _synthetic_submit_fixture()
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    authorizer = importlib.import_module(
        "ai_video.production.seedance_asset"
    ).SeedanceSyntheticImageAuthorizer(
        delegate=lambda exact: authorization if exact == paid_preview else None,
        evidence_source=lambda _evidence_id: b"{}",
    )

    with pytest.raises(AiVideoError) as exc_info:
        authorizer(paid_preview)

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED


@pytest.mark.parametrize(
    "classification",
    [
        "clearly_illustrated_anime_non_real_character",
        "ordinary_non_character_image",
    ],
)
def test_synthetic_authorizer_independently_reopens_exact_preview_evidence(
    classification,
):
    (
        _,
        _,
        _,
        paid_preview,
        resolver,
        _,
        receipt,
        aggregate,
    ) = _synthetic_submit_fixture(classification=classification)
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    authorizer = asset_module.SeedanceSyntheticImageAuthorizer(
        delegate=lambda exact: authorization if exact == paid_preview else None,
        evidence_source=_synthetic_evidence_source(
            asset_module, (receipt,), aggregate
        ),
    )

    assert authorizer(paid_preview) == authorization


def test_synthetic_authorizer_rejects_preview_not_bound_by_policy_evidence():
    (
        _,
        _,
        _,
        paid_preview,
        resolver,
        _,
        receipt,
        aggregate,
    ) = _synthetic_submit_fixture()
    items = list(paid_preview.egress_items)
    items[0] = items[0].model_copy(update={"sha256": HASH_D})
    mismatched_preview = PaidProviderCallPreview.create(
        **{
            **paid_preview.model_dump(
                mode="python", exclude={"preview_fingerprint"}
            ),
            "egress_items": tuple(items),
        }
    )
    authorization = _authorization(
        mismatched_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    authorizer = asset_module.SeedanceSyntheticImageAuthorizer(
        delegate=lambda exact: authorization if exact == mismatched_preview else None,
        evidence_source=_synthetic_evidence_source(
            asset_module, (receipt,), aggregate
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        authorizer(mismatched_preview)

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED


@pytest.mark.parametrize(
    "source_records",
    [
        {},
        {"terminal-frame-extraction-receipt-1": b"tampered-source-evidence"},
    ],
)
def test_photorealistic_fictional_authorizer_reopens_source_evidence(
    source_records,
):
    source_record_id = "terminal-frame-extraction-receipt-1"
    source_evidence = b"canonical-terminal-frame-extraction-receipt"
    source_tool = ToolIdentity(name="ffmpeg", version="9c33b2f")
    (
        _,
        _,
        _,
        paid_preview,
        resolver,
        _,
        receipt,
        aggregate,
    ) = _synthetic_submit_fixture(
        classification="synthetic_photorealistic_person",
        permitted_use=(
            "project-owned-fictional-no-protected-identity:seedance-i2v"
        ),
        registry_record_updates={
            "source_kind": AssetSourceKind.DERIVED,
            "tool": source_tool,
            "creation_receipt_id": source_record_id,
            "usage_license": "provider-output",
        },
        source_record_id=source_record_id,
        source_tool=source_tool,
        source_evidence_bytes=source_evidence,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    authorizer = asset_module.SeedanceSyntheticImageAuthorizer(
        delegate=lambda exact: authorization if exact == paid_preview else None,
        evidence_source=_synthetic_evidence_source(
            asset_module,
            (receipt,),
            aggregate,
            source_records=source_records,
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        authorizer(paid_preview)

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED


@pytest.mark.parametrize(
    ("mode", "binding_role", "permitted_use"),
    [
        (
            VideoGenerationMode.IMAGE_TO_VIDEO,
            "first_frame",
            "project-owned-fictional-no-protected-identity:seedance-i2v",
        ),
        (
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            "reference",
            "project-owned-fictional-no-protected-identity:seedance-r2v",
        ),
    ],
)
def test_photorealistic_fictional_authorizer_denies_valid_ark_egress(
    mode,
    binding_role,
    permitted_use,
):
    source_record_id = "terminal-frame-extraction-receipt-1"
    source_evidence = b"canonical-terminal-frame-extraction-receipt"
    source_tool = ToolIdentity(name="ffmpeg", version="9c33b2f")
    (
        _,
        _,
        _,
        paid_preview,
        resolver,
        _,
        receipt,
        aggregate,
    ) = _synthetic_submit_fixture(
        mode=mode,
        binding_role=binding_role,
        classification="synthetic_photorealistic_person",
        permitted_use=permitted_use,
        registry_record_updates={
            "source_kind": AssetSourceKind.DERIVED,
            "tool": source_tool,
            "creation_receipt_id": source_record_id,
            "usage_license": "provider-output",
        },
        source_record_id=source_record_id,
        source_tool=source_tool,
        source_evidence_bytes=source_evidence,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    authorizer = asset_module.SeedanceSyntheticImageAuthorizer(
        delegate=lambda exact: authorization if exact == paid_preview else None,
        evidence_source=_synthetic_evidence_source(
            asset_module,
            (receipt,),
            aggregate,
            source_records={source_record_id: source_evidence},
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        authorizer(paid_preview)

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED
    assert "photorealistic person-like references are disabled" in str(exc_info.value)


def test_synthetic_submit_rejects_registry_snapshot_pointer_mismatch_before_network():
    (
        profile,
        resolved,
        video_preview,
        paid_preview,
        resolver,
        _,
        _,
        _,
    ) = _synthetic_submit_fixture(registry_file_sha256=HASH_D)
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-must-not-submit"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    permit = _permit(
        resolved, video_preview, paid_preview, authorization
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.requests == []
    assert permit._validate_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            resolved, video_preview, paid_preview, authorization
        )
    )


@pytest.mark.parametrize(
    "classification",
    [
        "clearly_illustrated_anime_non_real_character",
        "ordinary_non_character_image",
    ],
)
def test_synthetic_inline_submit_uses_exact_data_uri_and_audio_opt_out(
    classification,
):
    profile, resolved, video_preview, paid_preview, resolver, png, _, _ = (
        _synthetic_submit_fixture(classification=classification)
    )
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-synthetic-inline-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )

    result = provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    payload = json.loads(transport.requests[0].body)
    assert result.external_effect_id == "task-synthetic-inline-1"
    assert payload["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "data:image/png;base64,"
            + base64.b64encode(png).decode("ascii")
        },
        "role": "first_frame",
    }
    assert payload["generate_audio"] is False
    assert base64.b64encode(png).decode("ascii") not in repr(transport.requests[0])


@pytest.mark.parametrize(
    "classification",
    [
        "clearly_illustrated_anime_non_real_character",
        "ordinary_non_character_image",
    ],
)
def test_synthetic_reference_to_video_inline_submit_uses_reference_image_role(
    classification,
):
    profile, resolved, video_preview, paid_preview, resolver, png, _, _ = (
        _synthetic_submit_fixture(
            mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
            binding_role="reference",
            classification=classification,
        )
    )
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-synthetic-r2v-inline-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )

    result = provider.submit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
        _permit(resolved, video_preview, paid_preview, authorization),
    )

    payload = json.loads(transport.requests[0].body)
    assert result.external_effect_id == "task-synthetic-r2v-inline-1"
    assert resolved.mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    assert payload["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "data:image/png;base64,"
            + base64.b64encode(png).decode("ascii")
        },
        "role": "reference_image",
    }
    assert payload["generate_audio"] is False


@pytest.mark.parametrize(
    ("mode", "role"),
    [
        (VideoGenerationMode.IMAGE_TO_VIDEO, "reference"),
        (VideoGenerationMode.REFERENCE_TO_VIDEO, "first_frame"),
    ],
)
def test_synthetic_policy_rejects_roles_from_another_generation_mode(mode, role):
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    child = asset_module.SeedanceSyntheticImageReceiptBinding(
        role=role,
        asset_id="image-synthetic-mode-role-1",
        receipt_content_hash=HASH_A,
    )

    with pytest.raises(ValidationError):
        _synthetic_policy_receipt(asset_module, child, mode=mode)


@pytest.mark.parametrize(
    ("kind", "role", "mime_type"),
    [
        ("video", "reference_video", "video/mp4"),
        ("audio", "reference_audio", "audio/wav"),
    ],
)
def test_synthetic_reference_to_video_rejects_media_before_permit_consumption(
    kind,
    role,
    mime_type,
):
    media_kwargs = {
        "kind": kind,
        "role": role,
        "asset_id": f"{kind}-r2v-reference-1",
        "asset_sha256": HASH_B,
        "mime_type": mime_type,
        "duration_millis": 5_000,
        "size_bytes": 5_000_000,
    }
    if kind == "video":
        media_kwargs.update(width=1280, height=720, fps=24)
    media = VideoMediaReferenceBinding(**media_kwargs)
    profile, resolved, video_preview, paid_preview, resolver, _, _, _ = (
        _synthetic_submit_fixture(
            mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
            binding_role="reference",
            media_bindings=(media,),
        )
    )
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )
    permit = _permit(
        resolved,
        video_preview,
        paid_preview,
        authorization,
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.requests == []
    assert permit._validate_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            resolved,
            video_preview,
            paid_preview,
            authorization,
        )
    )


@pytest.mark.parametrize(
    ("mode", "binding_role", "permitted_use"),
    [
        (
            VideoGenerationMode.IMAGE_TO_VIDEO,
            "first_frame",
            "project-owned-fictional-no-protected-identity:seedance-i2v",
        ),
        (
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            "reference",
            "project-owned-fictional-no-protected-identity:seedance-r2v",
        ),
    ],
)
def test_photorealistic_fictional_inline_submit_is_denied_before_network(
    mode,
    binding_role,
    permitted_use,
):
    source_tool = ToolIdentity(name="ffmpeg", version="9c33b2f")
    source_record_id = "terminal-frame-extraction-receipt-1"
    source_evidence = b"canonical-terminal-frame-extraction-receipt"
    profile, resolved, video_preview, paid_preview, resolver, _, _, _ = (
        _synthetic_submit_fixture(
            mode=mode,
            binding_role=binding_role,
            classification="synthetic_photorealistic_person",
            permitted_use=permitted_use,
            registry_record_updates={
                "source_kind": AssetSourceKind.DERIVED,
                "tool": source_tool,
                "creation_receipt_id": source_record_id,
                "usage_license": "provider-output",
            },
            source_record_id=source_record_id,
            source_tool=source_tool,
            source_evidence_bytes=source_evidence,
        )
    )
    transport = _FakeTransport()
    transport.responses.append(
        _json_response({"id": "task-photorealistic-fictional-inline-1"})
    )
    credential_calls: list[None] = []

    def credential() -> str:
        credential_calls.append(None)
        return "rotated-test-secret"

    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=credential,
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id=resolver.egress_policy_receipt_id,
    )

    permit = _permit(resolved, video_preview, paid_preview, authorization)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED
    assert "photorealistic person-like references are disabled" in str(exc_info.value)
    assert transport.requests == []
    assert credential_calls == []
    assert permit._validate_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            resolved,
            video_preview,
            paid_preview,
            authorization,
        )
    )


def test_synthetic_submit_rejects_wrong_aggregate_authorization_before_network():
    profile, resolved, video_preview, paid_preview, resolver, _, _, _ = (
        _synthetic_submit_fixture()
    )
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    authorization = _authorization(
        paid_preview,
        egress_policy_receipt_id="seedance-synthetic-egress:" + HASH_D,
    )
    permit = _permit(resolved, video_preview, paid_preview, authorization)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED
    assert transport.requests == []
    assert permit._validate_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            resolved, video_preview, paid_preview, authorization
        )
    )


def _compact_multi_image_body(target_size: int) -> bytes:
    payload = {
        "model": "doubao-seedance-2-0-mini-260615",
        "content": [
            {"type": "text", "text": ""},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,"},
                "role": "first_frame",
            },
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,"},
                "role": "last_frame",
            },
        ],
        "generate_audio": False,
    }
    empty = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    filler_size = target_size - len(empty)
    base64_size = filler_size - (filler_size % 4)
    prompt_size = filler_size - base64_size
    first_size = (base64_size // 8) * 4
    second_size = base64_size - first_size
    payload["content"][0]["text"] = "x" * prompt_size
    payload["content"][1]["image_url"]["url"] += "A" * first_size
    payload["content"][2]["image_url"]["url"] += "A" * second_size
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    assert len(body) == target_size
    return body


@pytest.mark.parametrize(
    ("target_size", "accepted"),
    [(63_999_999, True), (64_000_000, True), (64_000_001, False)],
)
def test_seedance_final_compact_multi_image_body_enforces_decimal_limit(
    target_size,
    accepted,
):
    body = _compact_multi_image_body(target_size)

    if accepted:
        assert seedance_adapter._validate_submit_body_size(body) is body
        return
    with pytest.raises(AiVideoError) as exc_info:
        seedance_adapter._validate_submit_body_size(body)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_synthetic_receipt_enforces_strict_30_decimal_megabyte_boundary():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    below = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-below-limit-1",
        asset_sha256=HASH_A,
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=29_999_999,
    )
    exact = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-at-limit-1",
        asset_sha256=HASH_A,
        mime_type="image/png",
        width=864,
        height=496,
        size_bytes=30_000_000,
    )

    assert _synthetic_receipt(asset_module, below).source_size_bytes == 29_999_999
    with pytest.raises(ValidationError):
        _synthetic_receipt(asset_module, exact)


def test_mini_default_payload_omits_optional_defaults_but_preserves_audio_opt_out():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-seedance-mini-1"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        output=VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds",
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

    mini_profile = next(
        entry
        for entry in profile.capabilities
        if entry.variant.model_id == "doubao-seedance-2-0-mini-260615"
        and entry.variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    )
    assert mini_profile.variant.output_capability.timing_modes == (
        "nominal_seconds",
        "provider_selected",
    )


def test_seedance_2_0_mini_continuity_binds_exact_terminal_frame_payload():
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.append(_json_response({"id": "task-seedance-mini-continuity-1"}))
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
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=_sealed_asset_resolver(first_frame),
        now=lambda: FIXED_NOW,
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
            timing_mode="nominal_seconds",
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
        "image_url": {"url": "asset://asset-test-0-bbbbbbbbbbbbbbbb"},
        "role": "first_frame",
    }


def test_seedance_mini_c4_mixed_anchors_fail_closed_before_preview_or_submit():
    from ai_video.production._video_continuity import C4SemanticBoundaryState
    from test_production_video import _c4_binding

    profile = _profile()
    transport = _FakeTransport()
    binding = _c4_binding(
        endpoint_changes={
            "target_shot_id": "shot-1",
            "target_shot_revision": 1,
            "target_shot_content_hash": HASH_A,
            "duration_milliseconds": 5_000,
        },
        semantic_boundary=C4SemanticBoundaryState.create(
            target_shot_id="shot-1",
            target_shot_revision=1,
            target_shot_content_hash=HASH_A,
            open_state=("exact terminal",),
            must_hold=("canonical identity and axis",),
            changes_here=("decelerate into approved endpoint",),
            close_state=("approved endpoint",),
        ),
    )
    terminal = binding.terminal
    endpoint = binding.approved_endpoint
    identity = binding.identity_anchor
    image_bindings = (
        VideoImageReferenceBinding(
            role="first_frame",
            asset_id=terminal.extracted_asset_id,
            asset_sha256=terminal.extracted_sha256,
            mime_type=terminal.extracted_mime_type,
            width=terminal.extracted_width,
            height=terminal.extracted_height,
            size_bytes=terminal.extracted_size_bytes,
        ),
        VideoImageReferenceBinding(
            role="last_frame",
            asset_id=endpoint.asset_id,
            asset_sha256=endpoint.asset_sha256,
            mime_type=endpoint.asset_mime_type,
            width=endpoint.asset_width,
            height=endpoint.asset_height,
            size_bytes=endpoint.asset_size_bytes,
        ),
        VideoImageReferenceBinding(
            role="reference",
            asset_id=identity.asset_id,
            asset_sha256=identity.asset_sha256,
            mime_type=identity.asset_mime_type,
            width=identity.asset_width,
            height=identity.asset_height,
            size_bytes=identity.asset_size_bytes,
        ),
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "must-not-be-read",
        input_reference=_sealed_asset_resolver(*image_bindings),
        now=lambda: FIXED_NOW,
    )
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        image_bindings=image_bindings,
        c4_multi_anchor_binding=binding,
        input_artifact_ids=(
            "shot-1",
            terminal.source_shot_id,
            terminal.source_video_asset_id,
            terminal.extracted_asset_id,
            terminal.source_provenance_receipt_id,
            terminal.extraction_receipt_id,
            binding.terminal_materialization_receipt_id,
            identity.asset_id,
            identity.source_provenance_receipt_id,
            identity.materialization_receipt_id,
            endpoint.asset_id,
            endpoint.source_provenance_receipt_id,
            endpoint.materialization_receipt_id,
            endpoint.feasibility_receipt.receipt_id,
            endpoint.feasibility_receipt.human_approval_receipt_id,
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

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(request)

    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert transport.requests == []


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
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(
        _request(
            profile,
            model_id=model_id,
            output=VideoFlexibleOutputRequirement(
                timing_mode=(
                    "nominal_seconds"
                    if model_id == "doubao-seedance-2-0-mini-260615"
                    else "exact_seconds"
                ),
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
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=_sealed_asset_resolver(video_binding),
        now=lambda: FIXED_NOW,
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
        "video_url": {"url": "asset://asset-test-0-bbbbbbbbbbbbbbbb"},
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
        input_reference=_provider_asset_reference,
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
    assert receipt.remote_materialization is not None
    assert receipt.remote_materialization.transport_kind == "provider_output_https"
    assert receipt.remote_materialization.remote_origin == "https://media.example"
    assert receipt.remote_materialization.remote_locator_sha256 == hashlib.sha256(
        b"https://media.example/result.mp4"
    ).hexdigest()
    assert receipt.remote_materialization.artifact_sha256 == receipt.artifact_sha256
    assert receipt.remote_materialization.artifact_size_bytes == receipt.size_bytes
    assert "https://media.example/result.mp4" not in receipt.model_dump_json()
    assert all("https://media.example/result.mp4" not in repr(req) for req in transport.requests)


def test_seedance_provider_output_lease_drives_exact_video_extend_without_ark_asset():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    result_url = "https://media.example/result.mp4?token=short-lived"
    profile = _profile()
    transport = _FakeTransport()
    transport.responses.extend(
        (
            _json_response(
                {
                    "id": "task-seedance-source-1",
                    "model": "doubao-seedance-2-0-mini-260615",
                    "status": "succeeded",
                    "content": {"video_url": result_url},
                }
            ),
            _json_response(
                {
                    "id": "task-seedance-source-1",
                    "model": "doubao-seedance-2-0-mini-260615",
                    "status": "succeeded",
                    "content": {"video_url": result_url},
                }
            ),
            _json_response(
                {
                    "id": "task-seedance-source-1",
                    "model": "doubao-seedance-2-0-mini-260615",
                    "status": "succeeded",
                    "content": {"video_url": result_url},
                }
            ),
            _json_response(
                {
                    "id": "task-seedance-source-1",
                    "model": "doubao-seedance-2-0-mini-260615",
                    "status": "succeeded",
                    "content": {"video_url": result_url},
                }
            ),
            _json_response({"id": "task-seedance-target-1"}),
        )
    )
    source_provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    source_resolved = source_provider.resolve(
        _request(profile, model_id="doubao-seedance-2-0-mini-260615")
    )
    source_preview = source_provider.preview(source_resolved)
    source_paid = _paid_preview(source_resolved, source_preview)
    source_receipt = _accepted_receipt(
        source_resolved,
        source_paid,
        task_id="task-seedance-source-1",
    )
    source_submission = VideoSubmission.from_paid_submit_receipt(
        resolved=source_resolved,
        receipt=source_receipt,
    )
    source_observation = source_provider.get_status(source_submission, source_receipt)
    sink = bytearray()

    class _Sink:
        def write(self, data: bytes):
            sink.extend(data)
            return len(data)

    source_fetch = source_provider.fetch(
        source_submission,
        source_receipt,
        source_observation,
        _Sink(),
    )
    request_count = len(transport.requests)
    with pytest.raises(AiVideoError) as no_authority:
        source_provider.refresh_provider_output_reference_lease(
            source_submission,
            source_receipt,
            source_observation,
            source_fetch,
            None,
        )
    assert no_authority.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert len(transport.requests) == request_count
    lease = source_provider.refresh_provider_output_reference_lease(
        source_submission,
        source_receipt,
        source_observation,
        source_fetch,
        _remote_refresh_permit(
            source_submission,
            source_observation,
            source_fetch,
        ),
    )
    original_stream = transport.stream_response
    transport.stream_response = _StreamResponse(
        status=200,
        content_type="video/mp4",
        chunks=(b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00", b"changed-video-bytes"),
    )
    with pytest.raises(AiVideoError) as changed:
        source_provider.refresh_provider_output_reference_lease(
            source_submission,
            source_receipt,
            source_observation,
            source_fetch,
            _remote_refresh_permit(
                source_submission,
                source_observation,
                source_fetch,
            ),
        )
    assert changed.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID
    transport.stream_response = original_stream
    source_binding = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="video-output-1",
        asset_sha256=source_fetch.artifact_sha256,
        mime_type=source_fetch.content_type,
        duration_millis=15_000,
        size_bytes=source_fetch.size_bytes,
        width=1280,
        height=720,
        fps=24,
    )
    resolver = asset_module.SeedanceRemoteReferenceResolver(
        materializations=(source_fetch.remote_materialization,),
        leases=(lease,),
        now=lambda: FIXED_NOW,
    )
    target_provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    target_request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        mode=VideoGenerationMode.VIDEO_EXTEND,
        media_bindings=(source_binding,),
        output=VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds",
            duration_seconds=15,
            dimension_mode="adaptive",
            resolution_label="720p",
            ratio="adaptive",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=True,
        ),
    )
    target_resolved = target_provider.resolve(target_request)
    target_preview = target_provider.preview(target_resolved)
    target_paid = _paid_preview(target_resolved, target_preview)
    target_authorization = _authorization(target_paid)

    target_provider.submit(
        target_resolved,
        target_preview,
        target_paid,
        target_authorization,
        _permit(target_resolved, target_preview, target_paid, target_authorization),
    )

    payload = json.loads(transport.requests[-1].body)
    assert payload["content"][1] == {
        "type": "video_url",
        "video_url": {"url": result_url},
        "role": "reference_video",
    }
    assert target_resolved.mode is VideoGenerationMode.VIDEO_EXTEND
    assert result_url not in repr(lease)
    assert result_url not in repr(resolver)


def test_seedance_remote_reference_lease_expiry_stops_before_submit_effect():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    materialization = asset_module.RemoteMediaMaterializationReceipt.create(
        transport_kind="provider_output_https",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-0-mini-260615",
        submission_fingerprint=HASH_A,
        paid_submit_receipt_fingerprint=HASH_B,
        provider_file_id="seedance-content-source-1",
        remote_origin="https://media.example",
        remote_locator_sha256=hashlib.sha256(b"https://media.example/source.mp4").hexdigest(),
        artifact_sha256=HASH_C,
        artifact_size_bytes=20_000_000,
        artifact_mime_type="video/mp4",
        accessibility_verification="exact_get",
        verified_at=FIXED_NOW - timedelta(minutes=10),
    )
    lease = asset_module.SeedanceRemoteReferenceLease(
        asset_module._REMOTE_REFERENCE_LEASE_TOKEN,
        materialization=materialization,
        url="https://media.example/source.mp4",
        issued_at=FIXED_NOW - timedelta(minutes=10),
        not_after=FIXED_NOW - timedelta(minutes=5),
        durability_validator=lambda: True,
    )
    resolver = asset_module.SeedanceRemoteReferenceResolver(
        materializations=(materialization,),
        leases=(lease,),
        now=lambda: FIXED_NOW,
    )
    binding = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="video-source",
        asset_sha256=HASH_C,
        mime_type="video/mp4",
        duration_millis=15_000,
        size_bytes=20_000_000,
        width=1280,
        height=720,
        fps=24,
    )
    profile = _profile()
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "must-not-be-read",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(
        _request(
            profile,
            model_id="doubao-seedance-2-0-mini-260615",
            mode=VideoGenerationMode.VIDEO_EXTEND,
            media_bindings=(binding,),
            output=VideoFlexibleOutputRequirement(
                timing_mode="nominal_seconds",
                duration_seconds=15,
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
    assert transport.requests == []


def test_seedance_remote_reference_resolver_rejects_direct_constructor_url_forgery():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    verified_url = "https://media.example/verified.mp4"
    materialization = asset_module.RemoteMediaMaterializationReceipt.create(
        transport_kind="provider_output_https",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-0-mini-260615",
        submission_fingerprint=HASH_A,
        paid_submit_receipt_fingerprint=HASH_B,
        provider_file_id="seedance-content-source-1",
        remote_origin="https://media.example",
        remote_locator_sha256=hashlib.sha256(verified_url.encode()).hexdigest(),
        artifact_sha256=HASH_C,
        artifact_size_bytes=20_000_000,
        artifact_mime_type="video/mp4",
        accessibility_verification="exact_get",
        verified_at=FIXED_NOW,
    )
    assert not hasattr(asset_module.SeedanceRemoteReferenceLease, "create")
    with pytest.raises(TypeError):
        asset_module.SeedanceRemoteReferenceLease(
            object(),
            materialization=materialization,
            url="https://media.example/unverified.mp4",
            issued_at=FIXED_NOW,
            not_after=FIXED_NOW + timedelta(minutes=5),
            durability_validator=lambda: True,
        )


def test_seedance_remote_reference_resolver_rejects_direct_constructor_long_lease():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    verified_url = "https://media.example/verified.mp4"
    materialization = asset_module.RemoteMediaMaterializationReceipt.create(
        transport_kind="provider_output_https",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-0-mini-260615",
        submission_fingerprint=HASH_A,
        paid_submit_receipt_fingerprint=HASH_B,
        provider_file_id="seedance-content-source-1",
        remote_origin="https://media.example",
        remote_locator_sha256=hashlib.sha256(verified_url.encode()).hexdigest(),
        artifact_sha256=HASH_C,
        artifact_size_bytes=20_000_000,
        artifact_mime_type="video/mp4",
        accessibility_verification="exact_get",
        verified_at=FIXED_NOW,
    )

    with pytest.raises(AiVideoError) as exc_info:
        asset_module.SeedanceRemoteReferenceLease(
            asset_module._REMOTE_REFERENCE_LEASE_TOKEN,
            materialization=materialization,
            url=verified_url,
            issued_at=FIXED_NOW,
            not_after=FIXED_NOW + timedelta(days=365),
            durability_validator=lambda: True,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_seedance_remote_reference_lease_stops_after_source_is_superseded():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    source_url = "https://media.example/verified.mp4"
    materialization = asset_module.RemoteMediaMaterializationReceipt.create(
        transport_kind="provider_output_https",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-0-mini-260615",
        submission_fingerprint=HASH_A,
        paid_submit_receipt_fingerprint=HASH_B,
        provider_file_id="seedance-content-source-1",
        remote_origin="https://media.example",
        remote_locator_sha256=hashlib.sha256(source_url.encode()).hexdigest(),
        artifact_sha256=HASH_C,
        artifact_size_bytes=20_000_000,
        artifact_mime_type="video/mp4",
        accessibility_verification="exact_get",
        verified_at=FIXED_NOW,
    )
    active = [True]
    lease = asset_module.SeedanceRemoteReferenceLease(
        asset_module._REMOTE_REFERENCE_LEASE_TOKEN,
        materialization=materialization,
        url=source_url,
        issued_at=FIXED_NOW,
        not_after=FIXED_NOW + timedelta(minutes=5),
        durability_validator=lambda: active[0],
    )
    resolver = asset_module.SeedanceRemoteReferenceResolver(
        materializations=(materialization,),
        leases=(lease,),
        now=lambda: FIXED_NOW,
    )
    binding = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="video-source",
        asset_sha256=HASH_C,
        mime_type="video/mp4",
        duration_millis=15_000,
        size_bytes=20_000_000,
        width=1280,
        height=720,
        fps=24,
    )

    assert resolver(binding) == source_url
    active[0] = False
    with pytest.raises(AiVideoError) as exc_info:
        resolver(binding)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_seedance_remote_reference_lease_is_rechecked_immediately_before_permit():
    asset_module = importlib.import_module("ai_video.production.seedance_asset")
    source_url = "https://media.example/source.mp4"
    materialization = asset_module.RemoteMediaMaterializationReceipt.create(
        transport_kind="provider_output_https",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-0-mini-260615",
        submission_fingerprint=HASH_A,
        paid_submit_receipt_fingerprint=HASH_B,
        provider_file_id="seedance-content-source-1",
        remote_origin="https://media.example",
        remote_locator_sha256=hashlib.sha256(source_url.encode()).hexdigest(),
        artifact_sha256=HASH_C,
        artifact_size_bytes=20_000_000,
        artifact_mime_type="video/mp4",
        accessibility_verification="exact_get",
        verified_at=FIXED_NOW,
    )
    lease = asset_module.SeedanceRemoteReferenceLease(
        asset_module._REMOTE_REFERENCE_LEASE_TOKEN,
        materialization=materialization,
        url=source_url,
        issued_at=FIXED_NOW,
        not_after=FIXED_NOW + timedelta(minutes=5),
        durability_validator=lambda: True,
    )
    lease_times = iter((FIXED_NOW, FIXED_NOW + timedelta(minutes=5)))
    resolver = asset_module.SeedanceRemoteReferenceResolver(
        materializations=(materialization,),
        leases=(lease,),
        now=lambda: next(lease_times),
    )
    binding = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="video-source",
        asset_sha256=HASH_C,
        mime_type="video/mp4",
        duration_millis=15_000,
        size_bytes=20_000_000,
        width=1280,
        height=720,
        fps=24,
    )
    profile = _profile()
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW,
    )
    resolved = provider.resolve(
        _request(
            profile,
            model_id="doubao-seedance-2-0-mini-260615",
            mode=VideoGenerationMode.VIDEO_EXTEND,
            media_bindings=(binding,),
            output=VideoFlexibleOutputRequirement(
                timing_mode="nominal_seconds",
                duration_seconds=15,
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
    permit = _permit(resolved, video_preview, paid_preview, authorization)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.requests == []
    assert permit._consumed is False


def test_fetch_accepts_rotated_locator_but_later_lease_rotation_fails_closed():
    profile = _profile()
    first_url = "https://media.example/result.mp4?token=first"
    rotated_url = "https://media.example/result.mp4?token=rotated"
    rotated_again_url = "https://media.example/result.mp4?token=rotated-again"
    transport = _FakeTransport()
    transport.responses.extend(
        (
            _json_response(
                {
                    "id": "task-seedance-1",
                    "status": "succeeded",
                    "content": {"video_url": first_url},
                }
            ),
            _json_response(
                {
                    "id": "task-seedance-1",
                    "status": "succeeded",
                    "content": {"video_url": rotated_url},
                }
            ),
            _json_response(
                {
                    "id": "task-seedance-1",
                    "status": "succeeded",
                    "content": {"video_url": rotated_again_url},
                }
            ),
        )
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "rotated-test-secret",
        input_reference=_provider_asset_reference,
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
    receipt = provider.fetch(
        submission,
        paid_receipt,
        observation,
        _FakeWriteSink(),
    )

    assert observation.provider_file_id == receipt.provider_file_id
    assert transport.requests[-1].url == rotated_url
    for durable in (observation.model_dump_json(), receipt.model_dump_json()):
        assert first_url not in durable
        assert rotated_url not in durable
    with pytest.raises(AiVideoError) as exc_info:
        provider.refresh_provider_output_reference_lease(
            submission,
            paid_receipt,
            observation,
            receipt,
            _remote_refresh_permit(submission, observation, receipt),
        )
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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
        input_reference=_provider_asset_reference,
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


# ---------------------------------------------------------------------------
# Milestone 2: Seedance 2.0 active-inventory isolation
# ---------------------------------------------------------------------------


def _base_only_pricing() -> SeedancePricingSnapshot:
    return SeedancePricingSnapshot.create(
        snapshot_id="seedance-base-only-price",
        observed_at=FIXED_NOW - timedelta(hours=1),
        expires_at=FIXED_NOW + timedelta(days=1),
        model_upper_bounds_microunits={"doubao-seedance-2-0-260128": 8_000_000},
    )


def _active_profile(model_id: str) -> SeedanceProviderProfile:
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    return SeedanceProviderProfile.create(
        pricing=SeedancePricingSnapshot.create(
            snapshot_id=f"seedance-active-price-{model_id}",
            observed_at=FIXED_NOW - timedelta(hours=1),
            expires_at=FIXED_NOW + timedelta(days=1),
            model_upper_bounds_microunits={model_id: 8_000_000},
        ),
        result_origins=("https://media.example",),
        capabilities=select_seedance_capabilities(model_id),
    )


def test_select_seedance_capabilities_returns_official_base_subset_byte_exact():
    from ai_video.production.seedance_capabilities import (
        default_seedance_capabilities,
        select_seedance_capabilities,
    )

    base_subset = select_seedance_capabilities("doubao-seedance-2-0-260128")
    official_base = tuple(
        entry
        for entry in default_seedance_capabilities()
        if entry.variant.model_id == "doubao-seedance-2-0-260128"
    )

    assert base_subset == official_base
    assert {entry.variant.model_id for entry in base_subset} == {
        "doubao-seedance-2-0-260128"
    }


def test_select_seedance_capabilities_rejects_empty_alias_family_and_unknown():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    with pytest.raises(ValueError, match="non-empty"):
        select_seedance_capabilities()

    with pytest.raises(ValueError, match="unknown"):
        select_seedance_capabilities("seedance-2.5")

    with pytest.raises(ValueError, match="unknown"):
        select_seedance_capabilities("doubao-seedance-2-0")

    with pytest.raises(ValueError, match="unknown"):
        select_seedance_capabilities("doubao-seedance-2-0-fast")

    with pytest.raises(ValueError, match="unknown"):
        select_seedance_capabilities("not-a-real-model")


def test_select_seedance_capabilities_rejects_duplicate_model_ids():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    with pytest.raises(ValueError, match="duplicate"):
        select_seedance_capabilities(
            "doubao-seedance-2-0-260128",
            "doubao-seedance-2-0-260128",
        )


def test_active_profile_accepts_official_base_only_capability_subset():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    base_profile = SeedanceProviderProfile.create(
        pricing=_base_only_pricing(),
        result_origins=("https://media.example",),
        capabilities=select_seedance_capabilities("doubao-seedance-2-0-260128"),
    )

    selected_ids = {entry.variant.model_id for entry in base_profile.capabilities}
    assert selected_ids == {"doubao-seedance-2-0-260128"}
    assert {entry.model_id for entry in base_profile.pricing.model_upper_bounds} == {
        "doubao-seedance-2-0-260128"
    }


def test_production_active_assembly_is_base_only_and_uses_logical_model_id():
    profile = SeedanceProviderProfile.create_active_base(
        pricing=_base_only_pricing(),
        result_origins=("https://media.example",),
    )

    assert {entry.variant.model_id for entry in profile.capabilities} == {
        "doubao-seedance-2-0-260128"
    }
    assert {entry.api_model_id for entry in profile.capabilities} == {
        "doubao-seedance-2-0-260128"
    }


def test_active_subset_rejects_noncanonical_mode_order_and_mixed_deployment():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    base_capabilities = select_seedance_capabilities("doubao-seedance-2-0-260128")
    with pytest.raises(ValueError, match="official catalog order"):
        SeedanceProviderProfile.create(
            pricing=_base_only_pricing(),
            result_origins=("https://media.example",),
            capabilities=tuple(reversed(base_capabilities)),
        )

    mixed_deployment = tuple(
        SeedanceCapabilityProfile(
            **{
                **entry.model_dump(),
                "api_model_id": "ep-seedance-base"
                if index == 0
                else entry.api_model_id,
            }
        )
        for index, entry in enumerate(base_capabilities)
    )
    with pytest.raises(ValueError, match="one exact deployment"):
        SeedanceProviderProfile.create(
            pricing=_base_only_pricing(),
            result_origins=("https://media.example",),
            capabilities=mixed_deployment,
        )


def test_active_profile_rejects_missing_pricing_for_selected_capabilities():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    empty_pricing = SeedancePricingSnapshot.create(
        snapshot_id="empty-price",
        observed_at=FIXED_NOW - timedelta(hours=1),
        expires_at=FIXED_NOW + timedelta(days=1),
        model_upper_bounds_microunits={},
    )

    with pytest.raises(ValueError):
        SeedanceProviderProfile.create(
            pricing=empty_pricing,
            result_origins=("https://media.example",),
            capabilities=select_seedance_capabilities("doubao-seedance-2-0-260128"),
        )


def test_active_profile_rejects_extra_pricing_models_not_in_capability_subset():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    extra_pricing = SeedancePricingSnapshot.create(
        snapshot_id="extra-price",
        observed_at=FIXED_NOW - timedelta(hours=1),
        expires_at=FIXED_NOW + timedelta(days=1),
        model_upper_bounds_microunits={
            "doubao-seedance-2-0-260128": 8_000_000,
            "doubao-seedance-2-0-fast-260128": 6_000_000,
        },
    )

    with pytest.raises(ValueError):
        SeedanceProviderProfile.create(
            pricing=extra_pricing,
            result_origins=("https://media.example",),
            capabilities=select_seedance_capabilities("doubao-seedance-2-0-260128"),
        )


def test_fast_and_mini_catalog_entries_remain_but_do_not_enter_base_active_subset():
    from ai_video.production.seedance_capabilities import (
        SEEDANCE_MODEL_IDS as CAPABILITY_MODEL_IDS,
        default_seedance_capabilities,
        select_seedance_capabilities,
    )

    catalog_ids = {entry.variant.model_id for entry in default_seedance_capabilities()}
    assert "doubao-seedance-2-0-fast-260128" in CAPABILITY_MODEL_IDS
    assert "doubao-seedance-2-0-mini-260615" in CAPABILITY_MODEL_IDS
    assert "doubao-seedance-2-0-fast-260128" in catalog_ids
    assert "doubao-seedance-2-0-mini-260615" in catalog_ids

    base_profile = SeedanceProviderProfile.create(
        pricing=_base_only_pricing(),
        result_origins=("https://media.example",),
        capabilities=select_seedance_capabilities("doubao-seedance-2-0-260128"),
    )

    active_ids = {entry.variant.model_id for entry in base_profile.capabilities}
    assert "doubao-seedance-2-0-fast-260128" not in active_ids
    assert "doubao-seedance-2-0-mini-260615" not in active_ids
    assert base_profile.pricing.upper_bound_for("doubao-seedance-2-0-fast-260128") is None
    assert base_profile.pricing.upper_bound_for("doubao-seedance-2-0-mini-260615") is None


@pytest.mark.parametrize(
    "unentitled_model_id",
    (
        "doubao-seedance-2-0-fast-260128",
        "doubao-seedance-2-0-mini-260615",
    ),
)
def test_base_active_profile_rejects_cross_model_request_before_any_effect(
    unentitled_model_id: str,
):
    profile = _active_profile("doubao-seedance-2-0-260128")
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "must-not-be-read",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    request = _request(
        profile,
        model_id=unentitled_model_id,
        output=VideoFlexibleOutputRequirement(
            timing_mode=(
                "nominal_seconds"
                if unentitled_model_id == "doubao-seedance-2-0-mini-260615"
                else "exact_seconds"
            ),
            duration_seconds=5,
            dimension_mode="exact",
            width=3840,
            height=2160,
            resolution_label="4k",
            ratio="16:9",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=True,
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(request)

    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert transport.requests == []


@pytest.mark.parametrize(
    ("model_id", "resolution_label", "width", "height"),
    (
        ("doubao-seedance-2-0-fast-260128", "1080p", 1920, 1080),
        ("doubao-seedance-2-0-mini-260615", "4k", 3840, 2160),
    ),
)
def test_fast_and_mini_profiles_reject_base_only_output_bounds_before_effect(
    model_id: str,
    resolution_label: str,
    width: int,
    height: int,
):
    profile = _active_profile(model_id)
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "must-not-be-read",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id=model_id,
                output=VideoFlexibleOutputRequirement(
                    timing_mode=(
                        "nominal_seconds"
                        if model_id == "doubao-seedance-2-0-mini-260615"
                        else "exact_seconds"
                    ),
                    duration_seconds=5,
                    dimension_mode="exact",
                    width=width,
                    height=height,
                    resolution_label=resolution_label,
                    ratio="16:9",
                    fps=24,
                    container="mp4",
                    mime_type="video/mp4",
                    native_audio=True,
                ),
            )
        )

    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert transport.requests == []


def test_cross_model_active_profiles_have_distinct_sealed_request_identities():
    base_profile = _active_profile("doubao-seedance-2-0-260128")
    fast_profile = _active_profile("doubao-seedance-2-0-fast-260128")
    assert base_profile.profile_sha256 != fast_profile.profile_sha256

    base_provider = SeedanceVideoProvider(
        profile=base_profile,
        transport=_FakeTransport(),
        credential=lambda: "must-not-be-read",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    fast_provider = SeedanceVideoProvider(
        profile=fast_profile,
        transport=_FakeTransport(),
        credential=lambda: "must-not-be-read",
        input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW,
    )
    base_resolved = base_provider.resolve(
        _request(base_profile, model_id="doubao-seedance-2-0-260128")
    )
    fast_resolved = fast_provider.resolve(
        _request(fast_profile, model_id="doubao-seedance-2-0-fast-260128")
    )

    assert base_resolved.capability_id != fast_resolved.capability_id
    assert base_resolved.resolved_generation_hash != fast_resolved.resolved_generation_hash
    assert base_resolved.provider_task_binding != fast_resolved.provider_task_binding

    base_video_preview = base_provider.preview(base_resolved)
    fast_video_preview = fast_provider.preview(fast_resolved)
    base_paid_preview = _paid_preview(base_resolved, base_video_preview)
    fast_paid_preview = _paid_preview(fast_resolved, fast_video_preview)
    assert base_paid_preview.preview_fingerprint != fast_paid_preview.preview_fingerprint
    base_authorization = _authorization(base_paid_preview)
    base_permit = _permit(
        base_resolved,
        base_video_preview,
        base_paid_preview,
        base_authorization,
    )
    fast_authorization = _authorization(fast_paid_preview)
    assert not base_permit._validate_paid_provider_operation_permit(
        **build_video_paid_permit_binding(
            fast_resolved,
            fast_video_preview,
            fast_paid_preview,
            fast_authorization,
        )
    )

    with pytest.raises(AiVideoError) as exc_info:
        fast_provider.resolve(
            _request(base_profile, model_id="doubao-seedance-2-0-fast-260128")
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_base_active_subset_yields_distinct_profile_identity_from_full_default_profile():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    base_profile = SeedanceProviderProfile.create(
        pricing=_base_only_pricing(),
        result_origins=("https://media.example",),
        capabilities=select_seedance_capabilities("doubao-seedance-2-0-260128"),
    )
    full_profile = SeedanceProviderProfile.create_default(
        pricing=_pricing(),
        result_origins=("https://media.example",),
    )

    assert base_profile.profile_id == full_profile.profile_id
    assert base_profile.profile_version == full_profile.profile_version
    assert base_profile.profile_sha256 != full_profile.profile_sha256
    assert base_profile.capabilities != full_profile.capabilities
    assert base_profile.pricing != full_profile.pricing


def test_active_subset_rejects_mutation_of_an_official_capability_entry():
    from ai_video.production.seedance_capabilities import select_seedance_capabilities

    base_subset = select_seedance_capabilities("doubao-seedance-2-0-260128")
    original_output = base_subset[0].variant.output_capability
    assert original_output is not None
    mutated_output = type(original_output)(
        **{**original_output.model_dump(), "max_duration_seconds": 600}
    )
    mutated_variant = VideoCapabilityVariant(
        **{
            **base_subset[0].variant.model_dump(),
            "output_capability": mutated_output,
        }
    )
    mutated = SeedanceCapabilityProfile(
        **{**base_subset[0].model_dump(), "variant": mutated_variant}
    )

    with pytest.raises(ValueError):
        SeedanceProviderProfile.create(
            pricing=_base_only_pricing(),
            result_origins=("https://media.example",),
            capabilities=(mutated, *base_subset[1:]),
        )


class _FakeWriteSink:
    def write(self, data: bytes):
        return len(data)
