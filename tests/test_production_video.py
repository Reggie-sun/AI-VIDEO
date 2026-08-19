from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import get_type_hints
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    ActorIdentity,
    DependencyGraphSnapshotPointer,
    FinalAcceptanceReceiptPointer,
    FinalAcceptanceState,
    ProductionManifest,
    ProjectSnapshotPointer,
    QaLayer,
    QaPolicyPointer,
    RegistrySnapshotPointer,
    ReviewLayerState,
    ReviewLifecycle,
    ReviewReceiptPointer,
)
from ai_video.production._state_commit_common import _validated_transition
from ai_video.production import video as video_contracts
from ai_video.production.paid_provider import (
    DurablePaidProviderSubmitPermit,
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    SecretReference,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoFetchReceipt,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoProviderFailure,
    VideoProviderRegistry,
    VideoSubmission,
    VideoSubmitResult,
    VideoTaskObservation,
    VideoTaskState,
)
from ai_video.production.video_artifact import (
    MeasuredVideoMetadata,
    TerminalFrameExtractionResult,
    extract_terminal_frame_candidate,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash=HASH_A,
        file_sha256=HASH_B,
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


def _profile(*, version: str = "hailuo-v1") -> ProviderProfilePointer:
    return ProviderProfilePointer(
        profile_id="hailuo-default",
        profile_version=version,
        profile_path=Path(f"provider-profiles/{HASH_D}.json"),
        profile_sha256=HASH_D,
    )


def test_manifest_27_identity_transition_stales_existing_p6_acceptance() -> None:
    review = ReviewReceiptPointer(
        path=Path(f"state/reviews/review.{HASH_A}.json"),
        review_id="review-before-video",
        layer=QaLayer.TECHNICAL,
        content_hash=HASH_A,
        file_sha256=HASH_B,
    )
    final_receipt = FinalAcceptanceReceiptPointer(
        path=Path(f"state/acceptance/final.{HASH_B}.json"),
        acceptance_id="acceptance-before-video",
        content_hash=HASH_B,
        file_sha256=HASH_C,
    )
    manifest = ProductionManifest(
        schema_version="2.7",
        project_id="p8-p6-staleness",
        manifest_revision=1,
        active_project=_project_pointer(),
        active_registry=_registry_pointer(),
        active_dependency_graph=_graph_pointer(),
        active_qa_policy=QaPolicyPointer(
            path=Path(f"state/reviews/policy.{HASH_C}.json"),
            policy_id="qa-before-video",
            policy_version="1",
            content_hash=HASH_C,
            file_sha256=HASH_D,
        ),
        active_review_receipts=(review,),
        review_states=(
            ReviewLayerState(
                layer=QaLayer.TECHNICAL,
                desired_fingerprint=HASH_A,
                applied_fingerprint=HASH_A,
                lifecycle=ReviewLifecycle.FRESH,
                active_receipt=review,
            ),
        ),
        final_acceptance_state=FinalAcceptanceState(
            desired_fingerprint=HASH_B,
            applied_fingerprint=HASH_B,
            lifecycle=ReviewLifecycle.FRESH,
            active_receipt=final_receipt,
        ),
    )
    next_project = ProjectSnapshotPointer(
        path=Path(f"state/projects/project.2.{HASH_D}.yaml"),
        revision=2,
        content_hash=HASH_D,
        file_sha256=HASH_A,
    )

    transitioned = _validated_transition(
        manifest,
        {"active_project": next_project},
    )

    assert transitioned.active_project == next_project
    assert transitioned.active_qa_policy == manifest.active_qa_policy
    assert transitioned.active_review_receipts == ()
    assert transitioned.review_states[0].lifecycle is ReviewLifecycle.STALE
    assert transitioned.review_states[0].active_receipt is None
    assert transitioned.final_acceptance_state is None


def _first_frame() -> VideoImageReferenceBinding:
    return VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-source",
        asset_sha256=HASH_A,
        mime_type="image/png",
        width=1280,
        height=720,
    )


def _continuity_constraints(**changes: object):
    values: dict[str, object] = {
        "scene_identity": {
            "artifact_id": "scene-001",
            "revision": 2,
            "content_hash": HASH_B,
        },
        "character_identities": (
            {
                "artifact_id": "character-001",
                "revision": 3,
                "content_hash": HASH_C,
            },
        ),
        "camera_axis": "axis-east-facing-left",
        "framing": "medium-wide-subject-left-third",
        "lighting": "warm-window-key-camera-right",
        "color": "warm-amber-low-saturation",
        "motion_direction": "subject-exits-screen-right",
        "exit_state": "right-foot-forward-at-doorway",
        "entrance_state": "right-foot-forward-entering-hall",
    }
    values.update(changes)
    return video_contracts.ContinuityConstraintSet.create(**values)


def _terminal_frame(**changes: object):
    values: dict[str, object] = {
        "source_shot_id": "shot-000",
        "source_shot_revision": 4,
        "source_shot_content_hash": HASH_A,
        "source_video_asset_id": "video-source-000",
        "source_video_sha256": HASH_B,
        "source_generation_id": "generation-source-000",
        "source_request_input_hash": HASH_C,
        "source_resolved_generation_hash": HASH_D,
        "source_provenance_receipt_id": "video-provenance-source-000",
        "extraction_receipt_id": HASH_D,
        "source_registry": _registry_pointer(),
        "source_container_name": "mp4",
        "source_codec_name": "h264",
        "source_width": 1280,
        "source_height": 720,
        "source_fps_numerator": 24,
        "source_fps_denominator": 1,
        "source_duration_milliseconds": 6000,
        "source_frame_count": 144,
        "frame_index": 143,
        "timestamp_numerator": 143,
        "timestamp_denominator": 24,
        "selection_rule": "generated_candidate_terminal",
        "extraction_contract_version": "terminal-frame-v1",
        "extractor_name": "ffmpeg",
        "extractor_version": "7.1",
        "extracted_asset_id": "terminal-frame-shot-000",
        "extracted_sha256": HASH_A,
        "extracted_mime_type": "image/png",
        "extracted_size_bytes": 4096,
        "extracted_width": 1280,
        "extracted_height": 720,
        "extracted_color_space": "bt709",
    }
    values.update(changes)
    return video_contracts.TerminalFrameEvidence.create(**values)


def _continuity_binding(**changes: object):
    values: dict[str, object] = {
        "role": "first_frame",
        "terminal_frame": _terminal_frame(),
        "target_shot_id": "shot-001",
        "target_shot_revision": 3,
        "target_shot_content_hash": HASH_A,
        "constraints": _continuity_constraints(),
    }
    values.update(changes)
    return video_contracts.ContinuityReferenceBinding.create(**values)


def _output(*, duration_seconds: int = 6, fps: int | None = 24) -> VideoOutputRequirement:
    return VideoOutputRequirement(
        duration_seconds=duration_seconds,
        width=1280,
        height=720,
        fps=fps,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )


def _request_values() -> dict[str, object]:
    return {
        "generation_id": "generation-001",
        "provider_name": "hailuo",
        "provider_kind": "minimax_hailuo",
        "model_id": "video-01",
        "provider_profile": _profile(),
        "target_shot_id": "shot-001",
        "target_shot_revision": 3,
        "target_shot_content_hash": HASH_A,
        "target_asset_role": "primary_visual",
        "target_visual_strategy": "generated_video",
        "mode": VideoGenerationMode.IMAGE_TO_VIDEO,
        "prompt_text": "A slow cinematic push toward the city.",
        "negative_prompt_text": "flicker",
        "image_bindings": (_first_frame(),),
        "output_requirement": _output(),
        "seed": 17,
        "base_project": _project_pointer(),
        "base_registry": _registry_pointer(),
        "base_dependency_graph": _graph_pointer(),
        "input_artifact_ids": ("shot-001", "image-source"),
        "output_asset_id": "video-output-001",
    }


def _request(**changes: object) -> VideoGenerationRequest:
    values = _request_values()
    values.update(changes)
    return VideoGenerationRequest.create(**values)


def _variant(**changes: object) -> VideoCapabilityVariant:
    values: dict[str, object] = {
        "capability_id": "hailuo-i2v-6s-720p",
        "provider_kind": "minimax_hailuo",
        "model_id": "video-01",
        "profile_version": "hailuo-v1",
        "execution_kind": VideoExecutionKind.REMOTE,
        "billing_kind": BillingKind.METERED,
        "mode": VideoGenerationMode.IMAGE_TO_VIDEO,
        "output": _output(),
        "allowed_image_roles": ("first_frame", "reference"),
        "required_first_frame": True,
        "max_reference_count": 2,
        "allowed_image_mime_types": ("image/jpeg", "image/png"),
        "max_image_bytes": 10_000_000,
        "min_image_width": 512,
        "min_image_height": 512,
        "negative_prompt_supported": True,
        "seed_supported": True,
        "fps_supported": True,
        "idempotent_submit": False,
        "lookup_supported": False,
    }
    values.update(changes)
    return VideoCapabilityVariant(**values)


def _resolved(
    request: VideoGenerationRequest | None = None,
    *,
    variant: VideoCapabilityVariant | None = None,
    effective_seed: int | None = 17,
) -> ResolvedVideoGenerationRequest:
    return ResolvedVideoGenerationRequest.create(
        request=request or _request(),
        capability=variant or _variant(),
        effective_output=(variant.output if variant is not None else _output()),
        effective_seed=effective_seed,
        effective_negative_prompt_text="flicker",
    )


def _paid_preview(
    resolved: ResolvedVideoGenerationRequest,
    *,
    attempt_id: str = "attempt-1",
    video_preview: VideoGenerationPreview | None = None,
    destination: str | None = None,
    estimated_cost_upper_bound_microunits: int | None = None,
    egress_item_ids: tuple[str, ...] | None = None,
) -> PaidProviderCallPreview:
    selected_preview = video_preview or VideoGenerationPreview.create(
        resolved=resolved,
        estimated_cost_upper_bound_microunits=1_000_000,
        currency="USD",
        destination="https://api.minimax.io",
        egress_item_ids=("prompt",),
    )
    selected_destination = (
        destination if destination is not None else selected_preview.destination
    )
    selected_cost = (
        estimated_cost_upper_bound_microunits
        if estimated_cost_upper_bound_microunits is not None
        else selected_preview.estimated_cost_upper_bound_microunits
    )
    selected_item_ids = (
        egress_item_ids
        if egress_item_ids is not None
        else selected_preview.egress_item_ids
    )
    assert selected_destination is not None
    assert selected_cost is not None
    assert selected_preview.currency is not None
    return PaidProviderCallPreview.create(
        attempt_id=attempt_id,
        operation="video_generation",
        provider_kind=resolved.provider_kind,
        model_id=resolved.model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered",
        currency=selected_preview.currency,
        estimated_cost_upper_bound_microunits=selected_cost,
        destination=selected_destination,
        method="POST",
        egress_items=tuple(
            PaidProviderEgressItem(
                item_id=item_id,
                sha256=HASH_A,
                size_bytes=42,
                mime_type="text/plain",
                purpose=item_id,
            )
            for item_id in selected_item_ids
        ),
        retention_mode="provider_standard",
        provider_policy_snapshot_id="minimax-policy-1",
        secret_reference=SecretReference(
            kind="environment",
            reference_id="MINIMAX_API_KEY",
        ),
    )


def _paid_authorization(
    preview: PaidProviderCallPreview,
    *,
    budget_policy_id: str = "budget-policy-1",
    egress_policy_receipt_id: str = "egress-policy-1",
) -> PaidProviderAuthorizationDecision:
    issued_at = datetime(2026, 8, 18, tzinfo=UTC)
    return PaidProviderAuthorizationDecision.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="operator-1", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in-1",
        budget_policy_id=budget_policy_id,
        budget_currency="USD",
        project_budget_ceiling_microunits=10_000_000,
        per_call_ceiling_microunits=1_000_000,
        egress_authorized=True,
        egress_policy_receipt_id=egress_policy_receipt_id,
        live_test_authorized=True,
        live_authorization_receipt_id="live-auth-1",
        issued_at=issued_at,
        expires_at=issued_at + timedelta(minutes=5),
        max_submit_count=1,
    )


def _paid_submit_receipt(
    resolved: ResolvedVideoGenerationRequest,
    preview: PaidProviderCallPreview,
    *,
    external_effect_id: str = "task-1",
) -> PaidProviderSubmitReceipt:
    return PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=resolved.resolved_generation_hash,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=HASH_A,
        reservation_id="reservation-1",
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id=external_effect_id,
        recorded_at=datetime(2026, 8, 18, tzinfo=UTC),
    )


def test_request_input_hash_seals_caller_intent_but_excludes_generation_id():
    baseline = _request()
    assert _request(generation_id="generation-002").request_input_hash == baseline.request_input_hash

    changes = (
        {"prompt_text": "A different shot."},
        {"image_bindings": (VideoImageReferenceBinding(**{**_first_frame().model_dump(), "asset_sha256": HASH_B}),)},
        {"provider_kind": "another_provider"},
        {"provider_profile": _profile(version="hailuo-v2")},
        {"output_requirement": _output(duration_seconds=10)},
    )
    for change in changes:
        assert _request(**change).request_input_hash != baseline.request_input_hash


def test_continuity_request_binds_exact_terminal_evidence_and_constraints():
    binding = _continuity_binding()
    terminal = binding.terminal_frame
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
        image_bindings=(first_frame,),
        continuity_binding=binding,
        input_artifact_ids=(
            "shot-001",
            terminal.source_shot_id,
            terminal.source_video_asset_id,
            terminal.extracted_asset_id,
        ),
    )

    assert request.continuity_binding == binding
    assert _request(
        generation_id="generation-002",
        image_bindings=(first_frame,),
        continuity_binding=binding,
        input_artifact_ids=request.input_artifact_ids,
    ).request_input_hash == request.request_input_hash
    assert _request(
        image_bindings=(
            first_frame.model_copy(update={"asset_sha256": HASH_D}),
        ),
        continuity_binding=_continuity_binding(
            terminal_frame=_terminal_frame(extracted_sha256=HASH_D)
        ),
        input_artifact_ids=request.input_artifact_ids,
    ).request_input_hash != request.request_input_hash
    assert _request(
        image_bindings=(first_frame,),
        continuity_binding=_continuity_binding(
            constraints=_continuity_constraints(
                motion_direction="subject-exits-screen-left"
            )
        ),
        input_artifact_ids=request.input_artifact_ids,
    ).request_input_hash != request.request_input_hash

    resolved = _resolved(request)
    assert resolved.continuity_binding == binding
    assert resolved.activation_scope is not None
    assert resolved.activation_scope.request.continuity_binding == binding


def test_terminal_frame_sealing_changes_request_hash_without_changing_legacy_hash():
    baseline = _request()
    sealed = _request(seal_terminal_frame=True)

    assert baseline.model_dump(mode="json").get("seal_terminal_frame") is False
    assert sealed.request_input_hash != baseline.request_input_hash
    assert _request().request_input_hash == baseline.request_input_hash


def test_extract_terminal_frame_candidate_seals_exact_source_and_measured_png(tmp_path: Path):
    source = b"exact-source-video-bytes"
    source_path = tmp_path / "source.mp4"
    source_path.write_bytes(source)
    png = (
        Path(__file__).parent
        / "fixtures/hyperframes/silent_image/source/assets/"
        "1ac67c3a1c909b3356cf6ff490c0f88b8a30ef4c28ca579657f6007146abe71c.png"
    ).read_bytes()
    measured = MeasuredVideoMetadata(
        container_name="mp4",
        codec_name="h264",
        width=320,
        height=180,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=1000,
        frame_count=24,
        audio_stream_count=0,
        size_bytes=len(source),
        artifact_sha256=__import__("hashlib").sha256(source).hexdigest(),
    )
    resolved = _resolved(_request(seal_terminal_frame=True))

    with source_path.open("rb") as held:
        extracted, measured_png, receipt = extract_terminal_frame_candidate(
            held.fileno(),
            request=resolved,
            measured_video=measured,
            source_provenance_receipt_id=HASH_A,
            extracted_asset_id="video-output-001:terminal-frame",
            extractor=lambda exact, frame_index: TerminalFrameExtractionResult(
                png_bytes=png,
                extractor_name="fixture-extractor",
                extractor_version="1.0",
            )
            if exact == source and frame_index == 23
            else (_ for _ in ()).throw(AssertionError("wrong extraction input")),
        )

    assert extracted == png
    assert measured_png.sha256 == receipt.extracted_sha256
    assert receipt.source_video_sha256 == measured.artifact_sha256
    assert receipt.frame_index == 23
    assert (receipt.timestamp_numerator, receipt.timestamp_denominator) == (23, 24)
    assert receipt.content_hash == video_contracts.canonical_sha256(
        {
            "schema": "ai-video-terminal-frame-extraction/1",
            **receipt.model_dump(mode="json", exclude={"content_hash"}),
        }
    )


def test_extract_terminal_frame_candidate_rejects_tampered_source_bytes(tmp_path: Path):
    source_path = tmp_path / "source.mp4"
    source_path.write_bytes(b"tampered")
    measured = MeasuredVideoMetadata(
        container_name="mp4",
        codec_name="h264",
        width=320,
        height=180,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=1000,
        frame_count=24,
        audio_stream_count=0,
        size_bytes=8,
        artifact_sha256=HASH_A,
    )

    with source_path.open("rb") as held, pytest.raises(
        AiVideoError, match="exact measured source"
    ):
        extract_terminal_frame_candidate(
            held.fileno(),
            request=_resolved(_request(seal_terminal_frame=True)),
            measured_video=measured,
            source_provenance_receipt_id=HASH_A,
            extracted_asset_id="video-output-001:terminal-frame",
            extractor=lambda *_: pytest.fail("extractor must not run"),
        )
@pytest.mark.parametrize(
    ("case", "match"),
    [
        ("t2v", "text-to-video"),
        ("wrong_target", "target Shot"),
        ("missing_input", "input artifact"),
        ("wrong_frame", "terminal frame"),
    ],
)
def test_continuity_request_rejects_unbound_or_mismatched_inputs(
    case: str, match: str
):
    values = {
        "continuity_binding": _continuity_binding(),
        "image_bindings": (
            VideoImageReferenceBinding(
                role="first_frame",
                asset_id="terminal-frame-shot-000",
                asset_sha256=HASH_A,
                mime_type="image/png",
                width=1280,
                height=720,
                size_bytes=4096,
            ),
        ),
        "input_artifact_ids": (
            "shot-001",
            "shot-000",
            "video-source-000",
            "terminal-frame-shot-000",
        ),
    }
    if case == "t2v":
        values["mode"] = VideoGenerationMode.TEXT_TO_VIDEO
    elif case == "wrong_target":
        values["continuity_binding"] = _continuity_binding(
            target_shot_id="shot-other"
        )
    elif case == "missing_input":
        values["input_artifact_ids"] = ("shot-001", "video-source-000")
    elif case == "wrong_frame":
        values["image_bindings"] = (_first_frame(),)
    with pytest.raises(ValidationError, match=match):
        _request(**values)


def test_historical_activation_scope_reopens_without_continuity_defaults():
    historical = _resolved().model_dump(mode="json")
    historical.pop("continuity_binding")
    historical.pop("seal_terminal_frame")
    scope = historical["activation_scope"]
    scope_request = scope["request"]
    scope_request.pop("continuity_binding")
    scope_request.pop("seal_terminal_frame")
    scope["scope_fingerprint"] = video_contracts.canonical_sha256(
        {
            "schema": "ai-video-activation-scope/1",
            "request": scope_request,
            "usage_license": scope["usage_license"],
        }
    )

    reopened = ResolvedVideoGenerationRequest.model_validate(historical)

    assert reopened.activation_scope is not None
    assert reopened.activation_scope.request.continuity_binding is None
    assert reopened.activation_scope.request.seal_terminal_frame is False
    assert reopened.resolved_generation_hash == _resolved().resolved_generation_hash


def test_extended_media_request_is_sealed_and_keeps_legacy_hashes_stable():
    assert _request().request_input_hash == (
        "a95362fdc0493bbc9ec08a7bc29e11960cb914ba981915a453e4230592132047"
    )
    assert _resolved().resolved_generation_hash == (
        "525d9e08851e766a14e000da2f37ce8dcf165db0c0283169074863021eacb8e7"
    )
    resolved = _resolved()
    assert resolved.activation_scope is not None
    assert resolved.activation_scope.request == _request()
    assert resolved.activation_scope.request.request_input_hash == resolved.request_input_hash

    dumped = resolved.model_dump(mode="json")
    scope = dumped["activation_scope"]
    scope["request"]["target_shot_id"] = "shot-tampered"
    with pytest.raises(ValidationError, match="request_input_hash|activation scope"):
        ResolvedVideoGenerationRequest.model_validate(dumped)

    binding_type = getattr(video_contracts, "VideoMediaReferenceBinding", None)
    output_type = getattr(video_contracts, "VideoFlexibleOutputRequirement", None)
    assert binding_type is not None
    assert output_type is not None
    video_binding = binding_type(
        kind="video",
        role="reference_video",
        asset_id="video-source",
        asset_sha256=HASH_B,
        mime_type="video/mp4",
        duration_millis=12_500,
        size_bytes=20_000_000,
        width=1920,
        height=1080,
        fps=30,
    )
    output = output_type(
        timing_mode="provider_selected",
        duration_seconds=None,
        frame_count=None,
        dimension_mode="adaptive",
        width=None,
        height=None,
        resolution_label="1080p",
        ratio="adaptive",
        fps=24,
        container="mov",
        mime_type="video/quicktime",
        native_audio=True,
    )
    request = _request(
        provider_name="seedance",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-5-260628",
        provider_profile=_profile(version="seedance-2026-08-19"),
        mode=VideoGenerationMode.VIDEO_EDIT,
        image_bindings=(),
        media_bindings=(video_binding,),
        output_requirement=output,
        negative_prompt_text="",
        seed=None,
        input_artifact_ids=("shot-001", "video-source"),
    )

    assert request.media_bindings == (video_binding,)
    assert request.request_input_hash != _request().request_input_hash
    assert VideoGenerationRequest.model_validate_json(request.model_dump_json()) == request


def test_extended_capability_validates_media_and_flexible_output_constraints():
    binding_type = getattr(video_contracts, "VideoMediaReferenceBinding", None)
    media_capability_type = getattr(video_contracts, "VideoMediaCapability", None)
    output_capability_type = getattr(video_contracts, "VideoOutputCapability", None)
    output_type = getattr(video_contracts, "VideoFlexibleOutputRequirement", None)
    assert None not in (
        binding_type,
        media_capability_type,
        output_capability_type,
        output_type,
    )
    video_binding = binding_type(
        kind="video",
        role="reference_video",
        asset_id="video-source",
        asset_sha256=HASH_B,
        mime_type="video/mp4",
        duration_millis=12_500,
        size_bytes=20_000_000,
        width=1920,
        height=1080,
        fps=30,
    )
    output = output_type(
        timing_mode="provider_selected",
        dimension_mode="adaptive",
        resolution_label="1080p",
        ratio="adaptive",
        fps=24,
        container="mov",
        mime_type="video/quicktime",
        native_audio=True,
    )
    request = _request(
        provider_name="seedance",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-5-260628",
        provider_profile=_profile(version="seedance-2026-08-19"),
        mode=VideoGenerationMode.VIDEO_EDIT,
        image_bindings=(),
        media_bindings=(video_binding,),
        output_requirement=output,
        negative_prompt_text="",
        seed=None,
        input_artifact_ids=("shot-001", "video-source"),
    )
    capability = _variant(
        capability_id="seedance-2-5-edit",
        provider_kind="volcengine_ark_seedance",
        model_id="doubao-seedance-2-5-260628",
        profile_version="seedance-2026-08-19",
        mode=VideoGenerationMode.VIDEO_EDIT,
        output=None,
        output_capability=output_capability_type(
            min_duration_seconds=4,
            max_duration_seconds=30,
            provider_selected_duration=True,
            frame_count_min=None,
            frame_count_max=None,
            frame_count_step=None,
            frame_count_remainder=None,
            dimension_modes=("adaptive",),
            resolution_labels=("1080p",),
            ratios=("adaptive",),
            fps_values=(24,),
            containers=("mov",),
            native_audio_options=(False, True),
        ),
        allowed_image_roles=(),
        required_first_frame=False,
        max_reference_count=0,
        allowed_image_mime_types=(),
        media_capabilities=(
            media_capability_type(
                kind="video",
                roles=("reference_video",),
                min_count=1,
                max_count=10,
                allowed_mime_types=("video/mp4", "video/quicktime"),
                max_size_bytes=200_000_000,
                min_duration_millis=4_000,
                max_duration_millis=30_000,
            ),
        ),
        negative_prompt_supported=False,
        seed_supported=False,
    )
    resolved = ResolvedVideoGenerationRequest.create(
        request=request,
        capability=capability,
        effective_output=output,
        effective_seed=None,
        effective_negative_prompt_text="",
    )

    assert resolved.media_bindings == (video_binding,)
    assert resolved.effective_output.container == "mov"

    preview = _paid_preview(resolved)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved,
        receipt=_paid_submit_receipt(resolved, preview),
    )
    assert submission.expected_container == "mov"
    assert submission.expected_content_type == "video/quicktime"

    oversized = video_binding.model_copy(update={"size_bytes": 200_000_001})
    with pytest.raises(AiVideoError) as exc_info:
        ResolvedVideoGenerationRequest.create(
            request=_request(
                provider_name="seedance",
                provider_kind="volcengine_ark_seedance",
                model_id="doubao-seedance-2-5-260628",
                provider_profile=_profile(version="seedance-2026-08-19"),
                mode=VideoGenerationMode.VIDEO_EDIT,
                image_bindings=(),
                media_bindings=(oversized,),
                output_requirement=output,
                negative_prompt_text="",
                seed=None,
                input_artifact_ids=("shot-001", "video-source"),
            ),
            capability=capability,
            effective_output=output,
            effective_seed=None,
            effective_negative_prompt_text="",
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_flexible_output_rejects_ambiguous_timing_and_container_mime_pairs():
    output_type = getattr(video_contracts, "VideoFlexibleOutputRequirement", None)
    assert output_type is not None

    with pytest.raises(ValidationError, match="timing"):
        output_type(
            timing_mode="exact_seconds",
            duration_seconds=5,
            frame_count=121,
            dimension_mode="exact",
            width=1280,
            height=720,
            resolution_label="720p",
            ratio="16:9",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=False,
        )
    with pytest.raises(ValidationError, match="container"):
        output_type(
            timing_mode="exact_seconds",
            duration_seconds=5,
            dimension_mode="exact",
            width=1280,
            height=720,
            resolution_label="720p",
            ratio="16:9",
            fps=24,
            container="mov",
            mime_type="video/mp4",
            native_audio=False,
        )


def test_resolved_hash_binds_generation_capability_profile_and_effective_settings():
    request = _request()
    baseline = _resolved(request)
    new_generation = _resolved(_request(generation_id="generation-002"))
    new_capability = _resolved(
        request,
        variant=_variant(capability_id="hailuo-i2v-6s-720p-v2"),
    )
    new_profile = _resolved(
        _request(provider_profile=_profile(version="hailuo-v2")),
        variant=_variant(profile_version="hailuo-v2"),
    )
    new_effective_seed = _resolved(request, effective_seed=18)

    assert new_generation.request_input_hash == baseline.request_input_hash
    assert new_generation.resolved_generation_hash != baseline.resolved_generation_hash
    assert new_capability.resolved_generation_hash != baseline.resolved_generation_hash
    assert new_profile.resolved_generation_hash != baseline.resolved_generation_hash
    assert new_effective_seed.resolved_generation_hash != baseline.resolved_generation_hash
    assert baseline.desired_generation_fingerprint == baseline.resolved_generation_hash


def test_resolved_request_round_trip_preserves_prompt_and_hash_rejects_mutation():
    resolved = _resolved()
    assert resolved.prompt_text == "A slow cinematic push toward the city."
    dumped = resolved.model_dump(mode="json")
    assert dumped["prompt_text"] == "A slow cinematic push toward the city."
    rehydrated = ResolvedVideoGenerationRequest.model_validate(dumped)
    assert rehydrated.prompt_text == resolved.prompt_text
    assert rehydrated.resolved_generation_hash == resolved.resolved_generation_hash
    assert rehydrated.desired_generation_fingerprint == resolved.desired_generation_fingerprint

    with pytest.raises(ValidationError, match="resolved_generation_hash"):
        ResolvedVideoGenerationRequest.model_validate({**dumped, "prompt_text": "Different."})
    with pytest.raises(ValidationError, match="resolved_generation_hash"):
        ResolvedVideoGenerationRequest.model_validate(
            {**dumped, "resolved_generation_hash": "0" * 64}
        )


def test_submission_status_and_fetch_identity_do_not_mutate_request_hashes():
    resolved = _resolved()
    preview = _paid_preview(resolved)
    submit_result = VideoSubmitResult.create(
        resolved=resolved,
        external_effect_id="task-1",
        submitted_at=datetime(2026, 8, 18, tzinfo=UTC),
    )
    paid_receipt = _paid_submit_receipt(
        resolved,
        preview,
        external_effect_id=submit_result.external_effect_id,
    )
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved,
        receipt=paid_receipt,
    )
    assert (
        submission.submission_fingerprint
        == "a15c218dff44321c73ca4696465b4db97413d0faf1d30a4d99304a334b9d1ac9"
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 0, 1, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id="file-1",
    )
    receipt = VideoFetchReceipt.create(
        submission=submission,
        observation=observation,
        content_type="video/mp4",
        size_bytes=100,
        artifact_sha256=HASH_A,
        fetched_at=datetime(2026, 8, 18, 0, 2, tzinfo=UTC),
    )

    assert submission.resolved_generation_hash == resolved.resolved_generation_hash
    assert observation.paid_submit_receipt_fingerprint == paid_receipt.submit_receipt_fingerprint
    assert receipt.paid_submit_receipt_fingerprint == paid_receipt.submit_receipt_fingerprint
    assert "external_task_id" not in submission.model_dump()
    assert "external_effect_id" not in submission.model_dump()
    assert resolved.request_input_hash == _request().request_input_hash


def test_authorization_is_separate_from_request_and_resolved_identity():
    resolved = _resolved()
    preview = _paid_preview(resolved)
    first = _paid_authorization(preview)
    second = _paid_authorization(
        preview,
        budget_policy_id="budget-policy-2",
        egress_policy_receipt_id="egress-policy-2",
    )

    assert first.authorization_fingerprint != second.authorization_fingerprint
    assert resolved.request_input_hash == _request().request_input_hash
    assert preview.request_fingerprint == resolved.resolved_generation_hash


def test_local_unmetered_preview_does_not_require_fake_cloud_receipts():
    variant = _variant(
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
    )
    resolved = _resolved(variant=variant)
    preview = VideoGenerationPreview.create(
        resolved=resolved,
        estimated_cost_upper_bound_microunits=None,
        currency=None,
        destination=None,
        egress_item_ids=(),
    )
    assert preview.destination is None
    assert preview.currency is None
    assert preview.egress_item_ids == ()


def test_remote_unmetered_capability_is_rejected_before_provider_submit():
    provider_submit_calls = 0
    with pytest.raises(ValidationError, match="supported pair"):
        _variant(billing_kind=BillingKind.LOCAL_UNMETERED)
    assert provider_submit_calls == 0


def test_core_reuses_paid_provider_authority_instead_of_defining_a_second_gate():
    assert not hasattr(video_contracts, "VideoCallAuthorization")
    assert not hasattr(video_contracts, "DurableVideoSubmitPermit")
    submit_hints = get_type_hints(video_contracts.VideoProvider.submit)
    assert "PaidProviderAuthorizationDecision" in str(submit_hints["authorization"])
    assert "DurablePaidProviderSubmitPermit" in str(submit_hints["permit"])
    assert DurablePaidProviderSubmitPermit is not None


def test_t2v_rejects_image_bindings_and_i2v_requires_capability_roles():
    with pytest.raises(ValidationError, match="text-to-video"):
        _request(mode=VideoGenerationMode.TEXT_TO_VIDEO)

    request = _request(
        image_bindings=(
            _first_frame(),
            VideoImageReferenceBinding(
                role="reference",
                asset_id="image-reference",
                asset_sha256=HASH_B,
                mime_type="image/jpeg",
                width=800,
                height=800,
            ),
        )
    )
    assert len(_resolved(request).image_bindings) == 2
    with pytest.raises(AiVideoError) as exc_info:
        _resolved(request, variant=_variant(max_reference_count=0))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_capability_variant_rejects_unsupported_coupled_output_before_provider_call():
    with pytest.raises(AiVideoError) as exc_info:
        _resolved(_request(output_requirement=_output(duration_seconds=10)))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


@pytest.mark.parametrize(
    ("request_change", "variant_change"),
    [
        ({"negative_prompt_text": "flicker"}, {"negative_prompt_supported": False}),
        ({"seed": 17}, {"seed_supported": False}),
        ({"output_requirement": _output(fps=24)}, {"fps_supported": False}),
    ],
)
def test_negative_prompt_seed_and_fps_are_capability_gated(
    request_change: dict[str, object],
    variant_change: dict[str, object],
):
    with pytest.raises(AiVideoError) as exc_info:
        _resolved(_request(**request_change), variant=_variant(**variant_change))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_request_accepts_minus_one_seed_for_provider_defined_random_sentinel():
    request = _request(seed=-1)

    assert request.seed == -1
    assert _resolved(request, effective_seed=-1).effective_seed == -1


def test_capability_model_has_no_unrestricted_provider_options_mapping():
    with pytest.raises(ValidationError):
        VideoCapabilityVariant(**{**_variant().model_dump(), "provider_options": {"x": 1}})


def test_provider_capabilities_are_sealed_and_registry_fails_closed():
    capabilities = VideoProviderCapabilities.create(
        provider_name="hailuo",
        variants=(_variant(),),
    )
    provider = object()
    registry = VideoProviderRegistry((("hailuo", provider),))
    assert capabilities.provider_name == "hailuo"
    assert registry.resolve("hailuo") is provider

    with pytest.raises(AiVideoError) as exc_info:
        registry.resolve("unknown")
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    with pytest.raises(ValueError, match="duplicate"):
        VideoProviderRegistry((("hailuo", object()), ("hailuo", object())))


def test_failure_certainty_and_retry_safety_are_independent_from_generic_retryable():
    failure = VideoProviderFailure(
        operation="submit",
        failure_kind="provider_unavailable",
        outcome_certainty="outcome_unknown",
        retry_safety="unsafe_same_effect",
        generic_retryable=True,
        public_error_code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
    )
    assert failure.generic_retryable is True
    assert failure.outcome_certainty == "outcome_unknown"
    assert failure.retry_safety == "unsafe_same_effect"
