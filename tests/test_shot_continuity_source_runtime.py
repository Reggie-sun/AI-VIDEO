from __future__ import annotations

from argparse import Namespace
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from ai_video.comfy_client import JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.composition import resolve_composition
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    resolve_dependency_state,
)
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    VideoAssetMetadata,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_source_runtime import (
    APPROVED_ENDPOINT_ROLE,
    build_source_closure,
    make_source_production_committer,
    make_source_video_candidate_preparer,
)
from ai_video.production.shot_continuity_source_qualification import (
    ShotContinuitySourceQualificationCaller,
    ShotContinuitySourceQualificationProvider,
)
from ai_video.production.shot_continuity_source_contracts import (
    SourceQualificationInput,
    SourceQualificationPreflightSnapshot,
)
from ai_video.production.shot_continuity_m0_qualification import (
    M0ValidationPreflightSnapshot,
)
from ai_video.production.shot_continuity_m0_policy import M0ValidationPolicyId
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoTaskState,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)
from ai_video.production.video_generation import VideoGenerationService
from scripts.prepare_shot_continuity_p0 import prepare


def _prepare_project(tmp_path: Path):
    image_paths = []
    for ordinal, color in enumerate(("red", "green", "blue", "yellow"), 1):
        source_dir = tmp_path / f"a{ordinal}"
        source_dir.mkdir()
        path = source_dir / "image-01.png"
        Image.new("RGB", (1659, 948), color).save(path)
        (source_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "backend": "chatgpt-web",
                    "mode": "direct-typescript-browser",
                    "prompt": f"rainy station source {ordinal}",
                    "created_at": f"2026-08-24T03:0{ordinal}:00.000Z",
                }
            ),
            encoding="utf-8",
        )
        image_paths.append(path)
    root = tmp_path / "production"
    result = prepare(
        Namespace(
            root=root,
            a1=image_paths[0],
            a2=image_paths[1],
            a3=image_paths[2],
            a4=image_paths[3],
            approved_at="2026-08-24T12:00:00+08:00",
            imported_at="2026-08-24T12:01:00+08:00",
            m0_policy=M0ValidationPolicyId.QUALITY_V1,
        )
    )
    return root, result, load_production_project(root / "project.yaml")


def test_p0_preparation_bootstraps_exact_source_graph_and_candidate_owner(
    tmp_path: Path,
) -> None:
    root, result, project = _prepare_project(tmp_path)
    closure = build_source_closure(project)

    assert project.dependency_graph == closure.graph
    assert project.manifest.active_dependency_graph is not None
    assert (
        result["dependency_graph_content_hash"]
        == project.manifest.active_dependency_graph.content_hash
        == closure.graph.content_hash
    )
    assert project.manifest.dependency_states == resolve_dependency_state(
        closure.graph,
        build_applied_dependency_evidence(closure.inputs, None),
    ).states
    assert tuple(layer.shot_id for layer in closure.inputs.composition_spec.layers) == (
        "rainy-station-1",
        "rainy-station-2",
        "rainy-station-3",
        "rainy-station-4",
    )
    assert {
        layer.asset_role for layer in closure.inputs.composition_spec.layers
    } == {APPROVED_ENDPOINT_ROLE}

    target = next(item for item in project.shots if item.shot_id == "rainy-station-3")
    request = SimpleNamespace(
        activation_scope=SimpleNamespace(
            request=SimpleNamespace(
                target_shot_id=target.shot_id,
                target_asset_role=APPROVED_ENDPOINT_ROLE,
            )
        ),
        output_asset_id="video-shot-rainy-station-3-source-v1",
        generation_id="rainy-station-source-generation-v1",
    )
    video_bytes = (
        b"\x00\x00\x00\x14ftypisom\x00\x00\x00\x00isom"
        b"\x00\x00\x00\x08moov"
    )
    video_path = root / "assets/files/video-shot-rainy-station-3-source-v1.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(video_bytes)
    asset_record = project.registry.assets[0].model_copy(
        update={
            "asset_id": request.output_asset_id,
            "asset_type": AssetType.VIDEO,
            "source_kind": AssetSourceKind.GENERATED,
            "artifact_path": Path(
                "assets/files/video-shot-rainy-station-3-source-v1.mp4"
            ),
            "sha256": hashlib.sha256(video_bytes).hexdigest(),
            "size_bytes": len(video_bytes),
            "mime_type": "video/mp4",
            "duration_seconds": 124 / 24,
            "width": 1344,
            "height": 768,
            "input_fingerprint": "d" * 64,
            "video_metadata": VideoAssetMetadata(
                container_name="mp4",
                codec_name="h264",
                width=1344,
                height=768,
                fps_numerator=24,
                fps_denominator=1,
                duration_milliseconds=5_167,
                frame_count=124,
                probe_receipt_id="probe-source-v1",
                request_receipt_fingerprint="c" * 64,
                resolved_generation_hash="d" * 64,
                provenance_receipt_id="provenance-source-v1",
            ),
        }
    )
    prepared = make_source_video_candidate_preparer(project)(
        project,
        request,
        None,
        None,
        SimpleNamespace(content_hash="a" * 64),
        asset_record,
    )
    candidate = next(
        item
        for item in prepared.candidate_project.shots
        if item.shot_id == target.shot_id
    )
    assert tuple(
        role.asset_ids
        for role in candidate.required_asset_roles
        if role.role == APPROVED_ENDPOINT_ROLE
    ) == ((request.output_asset_id,),)
    candidate_layers = tuple(
        layer
        for layer in prepared.candidate_inputs.composition_spec.layers
        if layer.shot_id == target.shot_id
        and layer.asset_role == APPROVED_ENDPOINT_ROLE
    )
    assert len(candidate_layers) == 1
    assert candidate_layers[0].asset_id == request.output_asset_id
    timeline = resolve_composition(
        prepared.candidate_project,
        prepared.candidate_inputs.composition_spec,
        prepared.candidate_inputs.renderer.version,
    )
    assert next(
        span for span in timeline.visual_spans if span.shot_id == target.shot_id
    ).asset_id == request.output_asset_id
    reopened_candidate_closure = build_source_closure(prepared.candidate_project)
    assert reopened_candidate_closure.inputs == prepared.candidate_inputs
    assert reopened_candidate_closure.graph == prepared.candidate_graph
    assert prepared.candidate_project.manifest.active_project is not None
    assert prepared.candidate_project.manifest.active_registry is not None
    assert prepared.candidate_project.manifest.active_dependency_graph is not None
    assert make_source_production_committer(
        root, project
    )._video_candidate_preparer is not None
    assert result["claims"] == {
        "video_generated": False,
        "winner_selected": False,
        "p6_pass": False,
        "final_acceptance": False,
    }


def _mock_preflight(request: ResolvedVideoGenerationRequest) -> SourceQualificationPreflightSnapshot:
    return SourceQualificationPreflightSnapshot(
        qualification_profile_hash="1" * 64,
        sealed_seed=request.effective_seed,
        p0=M0ValidationPreflightSnapshot(
            candidate_label="m0", qualification_receipt_hash="2" * 64,
            execution_stack_hash="3" * 64,
            source_execution_stack_hash=request.execution_stack_hash,
            profile_hash="4" * 64, compiler_hash="5" * 64,
            workflow_hash="6" * 64, validation_set_hash="7" * 64,
            policy_hashes=("8" * 64,),
            qualification_input_hashes=(("fixture", "9" * 64),),
        ),
        source_execution_stack_hash=request.execution_stack_hash,
        source_profile_hash="a" * 64, source_compiler_hash="b" * 64,
        source_workflow_hash="c" * 64, project_content_hash="d" * 64,
        registry_content_hash="e" * 64, dependency_graph_content_hash="f" * 64,
        m0_node_schema_hashes=(("M0Node", "1" * 64),),
        source_node_schema_hashes=(("SourceNode", "2" * 64),),
        component_hashes=(("diffusion", "3" * 64),),
        inputs=(
            SourceQualificationInput("first.png", b"fixture-first", "4" * 64, 13),
            SourceQualificationInput("last.png", b"fixture-last", "5" * 64, 12),
        ),
    )


class _LifecycleSourceProvider(ShotContinuitySourceQualificationProvider):
    """Lifecycle fixture; real owner proof reopens this mocked closure twice."""

    def validate_pre_effect(self, request: ResolvedVideoGenerationRequest):
        return _mock_preflight(request)


class _UnknownSourceProvider(_LifecycleSourceProvider):
    def __init__(self) -> None:
        self.submit_calls = 0

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview:
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def submit_local(self, request, preview, intent, permit):
        assert isinstance(intent, LocalVideoSubmitIntent)
        assert preview == self.preview(request)
        assert permit._consume_local_video_submit_permit(
            intent_fingerprint=intent.intent_fingerprint,
            request_fingerprint=request.resolved_generation_hash,
        )
        self.submit_calls += 1
        raise AiVideoError(
            code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            user_message="offline source submit outcome is unknown",
            retryable=False,
        )


class _RecordedSourceProvider(_LifecycleSourceProvider):
    def __init__(self, artifact_bytes: bytes) -> None:
        self.artifact_bytes = bytes(artifact_bytes)
        self.submit_calls = 0
        self.status_calls = 0
        self.fetch_calls = 0
        self.status_error: AiVideoError | None = None

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview:
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def submit_local(self, request, preview, intent, permit):
        assert isinstance(intent, LocalVideoSubmitIntent)
        assert preview == self.preview(request)
        assert permit._consume_local_video_submit_permit(
            intent_fingerprint=intent.intent_fingerprint,
            request_fingerprint=request.resolved_generation_hash,
        )
        self.submit_calls += 1
        return LocalVideoSubmitResult.create(
            resolved=request,
            provider_request_id="source-prompt-activate-1",
            submitted_at=datetime(2026, 8, 24, 5, tzinfo=UTC),
        )

    def get_local_status(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
    ) -> LocalVideoTaskObservation:
        assert submission.resolved_generation_hash == request.resolved_generation_hash
        self.status_calls += 1
        if self.status_error is not None:
            raise self.status_error
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=VideoTaskState.SUCCEEDED,
            observed_at=datetime(2026, 8, 24, 5, 1, tzinfo=UTC),
            progress_milli=1000,
            provider_file_id="source-output-activate-1",
        )

    def fetch_local(self, request, submission, observation, sink):
        assert submission.resolved_generation_hash == request.resolved_generation_hash
        self.fetch_calls += 1
        sink.write(self.artifact_bytes)
        return LocalVideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=len(self.artifact_bytes),
            artifact_sha256=hashlib.sha256(self.artifact_bytes).hexdigest(),
            fetched_at=datetime(2026, 8, 24, 5, 2, tzinfo=UTC),
        )


def _resolved_source_request(
    project, *, seal_terminal_frame: bool = True
) -> ResolvedVideoGenerationRequest:
    target = next(item for item in project.shots if item.shot_id == "rainy-station-3")
    frames = tuple(
        next(
            asset
            for asset in project.registry.assets
            if asset.asset_id
            == next(
                role
                for role in shot.required_asset_roles
                if role.role == APPROVED_ENDPOINT_ROLE
            ).asset_ids[0]
        )
        for shot in project.shots[1:3]
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        duration_seconds=None,
        frame_count=124,
        dimension_mode="exact",
        width=1344,
        height=768,
        resolution_label="h3_native",
        ratio="adaptive",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    profile_hash = "a" * 64
    request = VideoGenerationRequest.create(
        generation_id="rainy-station-source-lifecycle-v1",
        provider_name="comfy-local-h3",
        provider_kind="minimax_h3_fl2va",
        model_id="minimax-h3-fl2va",
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-fl2va-rainy-station-source-v1",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile_hash}.json"),
            profile_sha256=profile_hash,
        ),
        requirement_hash="b" * 64,
        provider_bound_request_hash="c" * 64,
        adapter_compiler_id="comfy-local-h3-video-compiler",
        adapter_compiler_version="1",
        adapter_compiler_hash="d" * 64,
        execution_stack_hash="e" * 64,
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        target_asset_role=APPROVED_ENDPOINT_ROLE,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text="Offline source lifecycle contract.",
        negative_prompt_text="",
        image_bindings=tuple(
            VideoImageReferenceBinding(
                role=role,
                asset_id=asset.asset_id,
                asset_sha256=asset.sha256,
                mime_type=asset.mime_type,
                width=asset.width or 1,
                height=asset.height or 1,
                size_bytes=asset.size_bytes,
            )
            for role, asset in zip(("first_frame", "last_frame"), frames, strict=True)
        ),
        seal_terminal_frame=seal_terminal_frame,
        output_requirement=output,
        seed=17,
        base_project=project.manifest.active_project,
        base_registry=project.manifest.active_registry,
        base_dependency_graph=project.manifest.active_dependency_graph,
        input_artifact_ids=tuple(asset.asset_id for asset in frames),
        output_asset_id="video-shot-rainy-station-3-source-v1",
    )
    capability = VideoCapabilityVariant(
        capability_id="minimax-h3-fl2va-local-v1",
        provider_kind="minimax_h3_fl2va",
        model_id="minimax-h3-fl2va",
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        output_capability=VideoOutputCapability(
            min_duration_seconds=1,
            max_duration_seconds=60,
            provider_selected_duration=False,
            timing_modes=("frame_count",),
            frame_count_min=1,
            frame_count_max=1000,
            frame_count_step=1,
            frame_count_remainder=0,
            dimension_modes=("exact",),
            min_width=1,
            max_width=4096,
            min_height=1,
            max_height=4096,
            dimension_multiple=1,
            resolution_labels=("h3_native",),
            ratios=("adaptive",),
            fps_values=(24,),
            containers=("mp4",),
            native_audio_options=(True,),
        ),
        allowed_image_roles=("first_frame", "last_frame"),
        required_first_frame=True,
        max_reference_count=0,
        allowed_image_mime_types=("image/png",),
        max_image_bytes=10_000_000,
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    return ResolvedVideoGenerationRequest.create(
        request=request,
        capability=capability,
        effective_output=output,
        effective_seed=17,
        effective_negative_prompt_text="",
    )


def test_source_request_uses_real_committer_unknown_outcome_without_resubmit(
    tmp_path: Path,
) -> None:
    root, _, project = _prepare_project(tmp_path)
    request = _resolved_source_request(project)
    provider = _UnknownSourceProvider()
    committer = make_source_production_committer(root, project)
    with pytest.raises(AiVideoError) as caught:
        ShotContinuitySourceQualificationCaller(
            committer=committer, provider=provider
        ).qualify(
            attempt_id="source-real-committer",
            resolved_request=request,
        )

    assert caught.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    attempt = committer._read_manifest().attempts[-1]
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.SUBMIT_INTENT
    assert attempt.video_generation_state.local_submit_intent is not None
    assert VideoGenerationService(
        committer=committer, provider=provider
    ).resume_next_action(attempt_id="source-real-committer") == "stop"
    assert provider.submit_calls == 1

    with pytest.raises(AiVideoError):
        ShotContinuitySourceQualificationCaller(
            committer=committer, provider=provider
        ).qualify(
            attempt_id="source-real-committer", resolved_request=request
        )
    assert provider.submit_calls == 1


def test_real_source_provider_invalid_completed_output_is_durable_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai_video.production.shot_continuity_source_qualification as module

    class InvalidCompletedTransport:
        def __init__(self) -> None:
            self.poll_calls = 0

        def poll_job(self, prompt_id: str, **_: object) -> JobResult:
            assert prompt_id == "source-prompt-activate-1"
            self.poll_calls += 1
            return JobResult(
                JobStatus.COMPLETED,
                prompt_id,
                history={"outputs": {}},
            )

    root, _, project = _prepare_project(tmp_path)
    request = _resolved_source_request(project)
    committer = make_source_production_committer(root, project)
    del module, monkeypatch, project, InvalidCompletedTransport
    provider = _RecordedSourceProvider(b"unused")
    provider.status_error = AiVideoError(
        code=ErrorCode.VIDEO_PROVIDER_FAILED,
        user_message="fixture completed output is invalid",
        retryable=False,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    attempt_id = "source-invalid-completed-output"

    ShotContinuitySourceQualificationCaller(
        committer=committer, provider=provider
    ).qualify(
        attempt_id=attempt_id, resolved_request=request
    )
    with pytest.raises(AiVideoError) as caught:
        service.refresh_local_once(attempt_id=attempt_id)

    assert caught.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    attempt = committer._read_manifest().attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.SUBMITTED
    assert service.resume_next_action(attempt_id=attempt_id) == "stop"
    assert provider.status_calls == 1

    with pytest.raises(AiVideoError):
        service.refresh_local_once(attempt_id=attempt_id)
    assert provider.status_calls == 1


def test_source_activation_reloads_the_exact_durable_closure_without_effect_replay(
    tmp_path: Path,
) -> None:
    root, _, project = _prepare_project(tmp_path)
    request = _resolved_source_request(project, seal_terminal_frame=False)
    artifact_bytes = (
        b"\x00\x00\x00\x14ftypisom\x00\x00\x00\x00isom"
        b"\x00\x00\x00\x08moov"
    )
    provider = _RecordedSourceProvider(artifact_bytes)
    committer = make_source_production_committer(root, project)
    attempt_id = "source-activate-equivalence"

    service = VideoGenerationService(committer=committer, provider=provider)
    ShotContinuitySourceQualificationCaller(
        committer=committer, provider=provider
    ).qualify(
        attempt_id=attempt_id, resolved_request=request
    )
    service.refresh_local_once(attempt_id=attempt_id)
    service.fetch_local_once(attempt_id=attempt_id)
    candidate_manifest = committer.prepare_video_activation_candidate(
        attempt_id=attempt_id,
        probe=lambda _fd: {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1344,
                    "height": 768,
                    "avg_frame_rate": "24/1",
                    "duration": "5.166667",
                    "nb_frames": "124",
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"format_name": "mov,mp4", "duration": "5.166667"},
        },
    )
    candidate_attempt = candidate_manifest.attempts[-1]
    candidate_pointers = (
        candidate_attempt.candidate_project,
        candidate_attempt.candidate_registry,
        candidate_attempt.candidate_dependency_graph,
    )

    activated = committer.activate_video_candidate(attempt_id=attempt_id)
    reopened = load_production_project(root / "project.yaml")
    closure = build_source_closure(reopened)

    assert (
        activated.active_project,
        activated.active_registry,
        activated.active_dependency_graph,
    ) == candidate_pointers
    assert reopened.manifest == activated
    assert reopened.dependency_graph == closure.graph
    assert reopened.manifest.active_dependency_graph is not None
    assert (
        reopened.manifest.active_dependency_graph.content_hash
        == closure.graph.content_hash
    )
    target_layer = next(
        layer
        for layer in closure.inputs.composition_spec.layers
        if layer.shot_id == "rainy-station-3"
    )
    assert target_layer.asset_id == request.output_asset_id

    effect_counts = (
        provider.submit_calls,
        provider.status_calls,
        provider.fetch_calls,
    )
    assert committer.replay_active_video_generation(attempt_id=attempt_id) == activated
    assert (
        provider.submit_calls,
        provider.status_calls,
        provider.fetch_calls,
    ) == effect_counts == (1, 1, 1)
