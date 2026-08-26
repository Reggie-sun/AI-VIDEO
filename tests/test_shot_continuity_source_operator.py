from __future__ import annotations

from argparse import Namespace
from datetime import UTC, datetime
import hashlib
import importlib
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.continuity_evaluator import SampledRgbFrame
from ai_video.production._video_continuity import (
    ContinuityArtifactIdentity,
    ContinuityConstraintSet,
    ContinuityReferenceBinding,
    TerminalFrameEvidence,
)
from ai_video.production.models import (
    ProductionManifest,
    SourceBoundaryEvaluationPhase,
    ToolIdentity,
)
from ai_video.production.paths import (
    canonical_source_boundary_review_evidence_path,
    canonical_source_boundary_review_receipt_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_source_review import (
    SourceBoundaryHumanDecisionV1,
    SourceBoundaryMeasurementContractV1,
    SourceBoundaryReviewEvidence,
    SourceBoundaryReviewerV1,
    adjudicate_source_boundary_review,
    is_source_boundary_qualification_request,
)
from ai_video.production.shot_continuity_source_qualification import (
    ShotContinuitySourceQualificationProfile,
    load_source_qualification_profile,
)
from ai_video.production.shot_continuity_source_runtime import (
    APPROVED_ENDPOINT_ROLE,
    make_source_production_committer,
)
from ai_video.production.shot_continuity_m0_policy import M0ValidationPolicyId
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationRequest,
    VideoGenerationPreview,
    VideoTaskState,
)
from ai_video.production.video_artifact import TerminalFrameExtractionResult
from scripts.prepare_shot_continuity_p0 import prepare


REPO_ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION_PROFILE = Path(
    "workflows/qualification/minimax_h3_fl2va_rainy_station_source_v1_profile.json"
)


def _operator_module():
    try:
        return importlib.import_module(
            "ai_video.production.shot_continuity_source_operator"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"source qualification operator is missing: {exc}")


def _script_module():
    try:
        return importlib.import_module("scripts.execute_shot_continuity_source")
    except ModuleNotFoundError as exc:
        pytest.fail(f"source qualification operator script is missing: {exc}")


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
                    "created_at": f"2026-08-25T03:0{ordinal}:00.000Z",
                }
            ),
            encoding="utf-8",
        )
        image_paths.append(path)
    root = tmp_path / "production"
    prepare(
        Namespace(
            root=root,
            a1=image_paths[0],
            a2=image_paths[1],
            a3=image_paths[2],
            a4=image_paths[3],
            approved_at="2026-08-25T12:00:00+08:00",
            imported_at="2026-08-25T12:01:00+08:00",
            m0_policy=M0ValidationPolicyId.QUALITY_V1,
        )
    )
    return root, load_production_project(root / "project.yaml")


def _profile_for(project) -> tuple[ShotContinuitySourceQualificationProfile, str]:
    sealed, document_hash = load_source_qualification_profile(
        QUALIFICATION_PROFILE,
        artifact_root=REPO_ROOT,
    )
    registry = {item.asset_id: item for item in project.registry.assets}
    frames = []
    for shot in project.shots[1:3]:
        asset_id = next(
            role.asset_ids[0]
            for role in shot.required_asset_roles
            if role.role == APPROVED_ENDPOINT_ROLE
        )
        frames.append(registry[asset_id])
    target = project.shots[2]
    values = sealed.model_dump(
        mode="python",
        exclude={
            "prompt_sha256",
            "sealed_seed",
            "output_contract_hash",
            "profile_content_hash",
        },
    )
    values.update(
        {
            "project_content_hash": project.project.content_hash,
            "registry_content_hash": project.registry.content_hash,
            "target_shot_revision": target.revision,
            "target_shot_content_hash": target.content_hash,
            "first_frame_asset_id": frames[0].asset_id,
            "first_frame_sha256": frames[0].sha256,
            "first_frame_size_bytes": frames[0].size_bytes,
            "first_frame_width": frames[0].width,
            "first_frame_height": frames[0].height,
            "last_frame_asset_id": frames[1].asset_id,
            "last_frame_sha256": frames[1].sha256,
            "last_frame_size_bytes": frames[1].size_bytes,
            "last_frame_width": frames[1].width,
            "last_frame_height": frames[1].height,
        }
    )
    return ShotContinuitySourceQualificationProfile.create(**values), document_hash


def _bind_profile_to_p0(
    root: Path,
    profile: ShotContinuitySourceQualificationProfile,
) -> ShotContinuitySourceQualificationProfile:
    committer = make_source_production_committer(
        root,
        load_production_project(root / "project.yaml"),
    )
    source_stack = committer.reopen_p0_qualification_source_stacks()[0]
    values = profile.model_dump(
        mode="python",
        exclude={"profile_content_hash"},
    )
    values.update(
        {
            "source_execution_stack_hash": source_stack.execution_stack_hash,
        }
    )
    return ShotContinuitySourceQualificationProfile.create(**values)


class _RecordedProvider:
    def __init__(self) -> None:
        self.preflight_calls = 0
        self.submit_calls = 0
        self.poll_calls = 0
        self.fetch_calls = 0
        self.on_preflight = None

    def validate_pre_effect(self, request: ResolvedVideoGenerationRequest):
        self.preflight_calls += 1
        if self.on_preflight is not None:
            self.on_preflight()
        return SimpleNamespace(
            qualification_profile_hash="1" * 64,
            source_execution_stack_hash=request.execution_stack_hash,
            sealed_seed=request.effective_seed,
            p0=SimpleNamespace(
                candidate_label="m0",
                qualification_receipt_hash="2" * 64,
                execution_stack_hash="3" * 64,
                source_execution_stack_hash=request.execution_stack_hash,
                profile_hash="4" * 64,
                compiler_hash="5" * 64,
                workflow_hash="6" * 64,
                validation_set_hash="7" * 64,
                policy_hashes=("8" * 64,),
                qualification_input_hashes=(("inventory", "9" * 64),),
            ),
            source_profile_hash="a" * 64,
            source_compiler_hash="b" * 64,
            source_workflow_hash="c" * 64,
            project_content_hash="d" * 64,
            registry_content_hash="e" * 64,
            dependency_graph_content_hash="f" * 64,
            m0_node_schema_hashes=(("M0Node", "1" * 64),),
            source_node_schema_hashes=(("SourceNode", "2" * 64),),
            component_hashes=(("diffusion", "3" * 64),),
            inputs=(
                SimpleNamespace(
                    file_name="a2.png",
                    data=b"SENSITIVE-A2-BYTES",
                    file_sha256="4" * 64,
                    size_bytes=18,
                ),
                SimpleNamespace(
                    file_name="a3.png",
                    data=b"SENSITIVE-A3-BYTES",
                    file_sha256="5" * 64,
                    size_bytes=18,
                ),
            ),
        )

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
            provider_request_id="source-operator-prompt-1",
            submitted_at=datetime(2026, 8, 25, 4, tzinfo=UTC),
        )

    def get_local_status(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
    ) -> LocalVideoTaskObservation:
        self.poll_calls += 1
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=VideoTaskState.SUCCEEDED,
            progress_milli=1000,
            provider_file_id="video:source-operator.mp4:output",
            observed_at=datetime(2026, 8, 25, 4, 1, tzinfo=UTC),
        )

    def fetch_local(self, request, submission, observation, sink):
        payload = b"\x00\x00\x00\x14ftypisomsource-operator"
        self.fetch_calls += 1
        sink.write(payload)
        return LocalVideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=len(payload),
            artifact_sha256=hashlib.sha256(payload).hexdigest(),
            fetched_at=datetime(2026, 8, 25, 4, 2, tzinfo=UTC),
        )


def _source_probe(_held_fd: int) -> dict[str, object]:
    return {
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
    }


class _ExactAnchorSampler:
    def __init__(self, first: bytes, last: bytes) -> None:
        self.identity = ToolIdentity(name="ffmpeg", version="test-1")
        self._pixels = (first, last)

    def sample(self, _held_fd, measured, frame_indices):
        assert frame_indices == (0, 123)
        return tuple(
            SampledRgbFrame(
                frame_index=frame_index,
                width=measured.width,
                height=measured.height,
                pixels=pixels,
            )
            for frame_index, pixels in zip(
                frame_indices,
                self._pixels,
                strict=True,
            )
        )


def _resized_rgb(payload: bytes) -> bytes:
    with Image.open(BytesIO(payload)) as image:
        return image.convert("RGB").resize((1344, 768)).tobytes()


def _terminal_png(payload: bytes) -> bytes:
    with Image.open(BytesIO(payload)) as image:
        output = BytesIO()
        image.convert("RGB").resize((1344, 768)).save(output, format="PNG")
        return output.getvalue()


def _fake_continuity_binding(project, profile) -> ContinuityReferenceBinding:
    scene = ContinuityArtifactIdentity(
        artifact_id="fake-source-scene",
        revision=1,
        content_hash="a" * 64,
    )
    character = ContinuityArtifactIdentity(
        artifact_id="fake-source-character",
        revision=1,
        content_hash="b" * 64,
    )
    constraints = ContinuityConstraintSet.create(
        scene_identity=scene,
        character_identities=(character,),
        camera_axis="screen-right",
        framing="medium-wide",
        lighting="rainy-day",
        color="cool",
        motion_direction="screen-right",
        exit_state="walking",
        entrance_state="walking",
    )
    terminal = TerminalFrameEvidence.create(
        source_shot_id=profile.last_frame_asset_id,
        source_shot_revision=1,
        source_shot_content_hash="c" * 64,
        source_video_asset_id=profile.last_frame_asset_id,
        source_video_sha256=profile.last_frame_sha256,
        source_generation_id="fake-source-generation",
        source_request_input_hash="d" * 64,
        source_resolved_generation_hash="e" * 64,
        source_provenance_receipt_id="fake-source-provenance",
        extraction_receipt_id="f" * 64,
        source_registry=project.manifest.active_registry,
        source_container_name="mp4",
        source_codec_name="h264",
        source_width=profile.first_frame_width,
        source_height=profile.first_frame_height,
        source_fps_numerator=24,
        source_fps_denominator=1,
        source_duration_milliseconds=1000,
        source_frame_count=2,
        frame_index=1,
        timestamp_numerator=1,
        timestamp_denominator=24,
        selection_rule="generated_candidate_terminal",
        extraction_contract_version="1",
        extractor_name="fake-extractor",
        extractor_version="1",
        extracted_asset_id=profile.first_frame_asset_id,
        extracted_sha256=profile.first_frame_sha256,
        extracted_mime_type="image/png",
        extracted_size_bytes=profile.first_frame_size_bytes,
        extracted_width=profile.first_frame_width,
        extracted_height=profile.first_frame_height,
        extracted_color_space="srgb",
    )
    return ContinuityReferenceBinding.create(
        role="first_frame",
        terminal_frame=terminal,
        target_shot_id=profile.target_shot_id,
        target_shot_revision=profile.target_shot_revision,
        target_shot_content_hash=profile.target_shot_content_hash,
        constraints=constraints,
    )


def _reach_source_boundary_candidate(tmp_path: Path):
    module = _operator_module()
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    profile = _bind_profile_to_p0(root, profile)
    request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-boundary-lifecycle-v1",
    )
    provider = _RecordedProvider()
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=provider,
        request=request,
        attempt_id="rainy-station-source-boundary-lifecycle-attempt-v1",
    )
    operator.submit(require_new_attempt=True)
    operator.poll()
    operator.fetch()
    operator.upgrade_manifest_214()
    committer = operator.committer
    manifest = committer._read_manifest()
    attempt = next(
        item for item in manifest.attempts if item.attempt_id == operator.attempt_id
    )
    state = attempt.video_generation_state
    assert state is not None and state.local_fetch_receipt is not None
    fetch = committer._reopen_local_video_fetch(state.local_fetch_receipt)
    p0_receipt, _, _, _, _ = committer.reopen_p0_qualification_prepared()
    current = load_production_project(root / "project.yaml")
    first_bytes = current.asset_paths[profile.first_frame_asset_id].read_bytes()
    last_bytes = current.asset_paths[profile.last_frame_asset_id].read_bytes()
    sampler = _ExactAnchorSampler(
        _resized_rgb(first_bytes),
        _resized_rgb(last_bytes),
    )
    contract = SourceBoundaryMeasurementContractV1.create(
        p0_qualification_receipt_hash=p0_receipt.content_hash,
        p0_rubric_hash=p0_receipt.rubric_hash,
        first_frame_asset_id=profile.first_frame_asset_id,
        first_frame_sha256=profile.first_frame_sha256,
        last_frame_asset_id=profile.last_frame_asset_id,
        last_frame_sha256=profile.last_frame_sha256,
        sample_width=1344,
        sample_height=768,
        decoder=sampler.identity,
    )
    human = SourceBoundaryHumanDecisionV1.create(
        resolved_generation_hash=request.resolved_generation_hash,
        artifact_sha256=fetch.artifact_sha256,
        reviewer=ToolIdentity(name="human-test", version="2026-08-26"),
        raw_full_speed_reviewed=True,
        identity_match=True,
        camera_axis_match=True,
        framing_match=True,
        motion_direction_match=True,
        action_phase_match=True,
        entrance_exit_match=True,
        no_unexpected_stop_or_reentry=True,
        pacing_waiver=True,
        rationale="Exact fixture output accepted with pacing waiver.",
    )
    reviewer = SourceBoundaryReviewerV1(
        source_profile_content_hash=profile.profile_content_hash,
        source_execution_stack_hash=profile.source_execution_stack_hash,
        measurement_contract=contract,
        human_decision=human,
        evaluator=ToolIdentity(
            name="ai-video-source-boundary-review",
            version="1",
        ),
        sampler=sampler,
        first_anchor_bytes=first_bytes,
        last_anchor_bytes=last_bytes,
    )
    terminal = _terminal_png(last_bytes)

    def terminal_extractor(_source, _index):
        return TerminalFrameExtractionResult(
            png_bytes=terminal,
            extractor_name="fixture-extractor",
            extractor_version="1",
        )

    candidate = committer.prepare_video_activation_candidate(
        attempt_id=operator.attempt_id,
        probe=_source_probe,
        source_boundary_reviewer=reviewer,
        terminal_frame_extractor=terminal_extractor,
    )
    return root, committer, operator.attempt_id, reviewer, terminal_extractor, candidate


def test_builder_uses_exact_active_lineage_without_fixture_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _operator_module()
    compiler = importlib.import_module("ai_video.production.video_compiler")
    captured = []
    real_compile = compiler.compile_video_generation_request

    def _compile(projection):
        captured.append(projection)
        return real_compile(projection)

    monkeypatch.setattr(module, "compile_video_generation_request", _compile)
    _, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)

    first = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v1",
    )
    second = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v1",
    )

    assert first == second
    assert len(captured) == 2
    assert all(
        isinstance(item, compiler.VideoGenerationRequestCompilation)
        and item.compilation_kind == "qualification"
        for item in captured
    )
    tampered = captured[0].model_dump(mode="python")
    tampered["prompt_text"] = "drifted after compilation"
    with pytest.raises(ValueError, match="compilation_hash"):
        compiler.VideoGenerationRequestCompilation.model_validate(tampered)
    copied_without_validation = captured[0].model_copy(
        update={"prompt_text": "model-copy drift"}
    )
    with pytest.raises(ValueError, match="compilation_hash"):
        real_compile(copied_without_validation)
    assert first.activation_scope is not None
    assert (
        first.activation_scope.request.base_project == project.manifest.active_project
    )
    assert (
        first.activation_scope.request.base_registry == project.manifest.active_registry
    )
    assert (
        first.activation_scope.request.base_dependency_graph
        == project.manifest.active_dependency_graph
    )
    assert first.requirement_hash not in {"1" * 64, "b" * 64}
    assert first.provider_bound_request_hash not in {"2" * 64, "c" * 64}
    assert tuple(item.asset_id for item in first.image_bindings) == (
        profile.first_frame_asset_id,
        profile.last_frame_asset_id,
    )
    assert first.effective_seed == profile.sealed_seed
    assert first.effective_output.frame_count == 124
    assert first.effective_output.width == 1344
    assert first.effective_output.height == 768
    assert first.effective_output.fps == 24


def test_fake_continuity_binding_cannot_bypass_source_boundary_p6(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _operator_module()
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    profile = _bind_profile_to_p0(root, profile)
    fake_binding = _fake_continuity_binding(project, profile)
    resolved_type = ResolvedVideoGenerationRequest

    def create_with_fake_binding(**values):
        original = values["request"]
        request_values = original.model_dump(
            mode="python",
            exclude={"request_input_hash"},
        )
        request_values["continuity_binding"] = fake_binding
        values["request"] = VideoGenerationRequest.create(**request_values)
        return resolved_type.create(**values)

    monkeypatch.setattr(
        module,
        "ResolvedVideoGenerationRequest",
        SimpleNamespace(create=create_with_fake_binding),
    )
    request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-fake-continuity-v1",
    )
    assert is_source_boundary_qualification_request(request)
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=_RecordedProvider(),
        request=request,
        attempt_id="rainy-station-source-fake-continuity-attempt-v1",
    )
    operator.submit(require_new_attempt=True)
    operator.poll()
    operator.fetch()
    operator.upgrade_manifest_214()
    manifest_path = root / "state/manifest.json"
    before = manifest_path.read_bytes()
    probe_calls = 0

    def counted_probe(held_fd):
        nonlocal probe_calls
        probe_calls += 1
        return _source_probe(held_fd)

    with pytest.raises(AiVideoError, match="must not include continuity"):
        operator.committer.prepare_video_activation_candidate(
            attempt_id=operator.attempt_id,
            probe=counted_probe,
            source_boundary_reviewer=object(),
        )

    assert probe_calls == 0
    assert manifest_path.read_bytes() == before


def test_operator_keeps_preflight_read_only_and_stops_fetch_at_validate(
    tmp_path: Path,
) -> None:
    module = _operator_module()
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v1",
    )
    provider = _RecordedProvider()
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=provider,
        request=request,
        attempt_id="rainy-station-source-a2-a3-attempt-v1",
    )
    manifest_path = root / "state/manifest.json"
    before = manifest_path.read_bytes()

    preflight = operator.preflight(require_new_attempt=True)

    assert preflight["durable_state_unchanged"] is True
    assert preflight["next_action"] == "submit"
    assert manifest_path.read_bytes() == before
    assert provider.submit_calls == provider.poll_calls == provider.fetch_calls == 0
    serialized = json.dumps(script_json := _script_module()._jsonable(preflight))
    assert "SENSITIVE" not in serialized
    assert script_json["preflight"]["inputs"] == [
        {"file_name": "a2.png", "file_sha256": "4" * 64, "size_bytes": 18},
        {"file_name": "a3.png", "file_sha256": "5" * 64, "size_bytes": 18},
    ]

    outcome = operator.submit(require_new_attempt=True)
    assert outcome.provider_request_id == "source-operator-prompt-1"
    assert operator.status()["next_action"] == "poll"
    assert provider.submit_calls == 1

    with pytest.raises(AiVideoError) as caught:
        operator.submit(require_new_attempt=True)
    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert provider.submit_calls == 1

    observation = operator.poll()
    assert observation.state is VideoTaskState.SUCCEEDED
    assert operator.status()["next_action"] == "fetch"

    fetched = operator.fetch()
    assert fetched.relative_path.suffix == ".mp4"
    assert operator.status()["next_action"] == "validate"
    assert provider.poll_calls == provider.fetch_calls == 1
    assert not any(
        item.status.value == "succeeded"
        for item in load_production_project(root / "project.yaml").manifest.attempts
        if item.attempt_id == "rainy-station-source-a2-a3-attempt-v1"
    )

    current = operator.committer._read_manifest()
    operator.committer.upgrade_manifest_schema(
        "2.14", expected_manifest_revision=current.manifest_revision
    )
    before_boundary = operator.committer._read_manifest()
    with pytest.raises(AiVideoError, match="source boundary P6") as boundary_caught:
        operator.committer.prepare_video_activation_candidate(
            attempt_id=operator.attempt_id,
            probe=lambda _fd: pytest.fail("generic probe must not run before P6"),
        )
    assert boundary_caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert operator.committer._read_manifest() == before_boundary

    replacement_request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v2",
    )
    replacement = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(
            root, load_production_project(root / "project.yaml")
        ),
        provider=provider,
        request=replacement_request,
        attempt_id="rainy-station-source-a2-a3-attempt-v2",
    )
    with pytest.raises(AiVideoError) as replacement_caught:
        replacement.submit(require_new_attempt=True)
    assert replacement_caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert provider.submit_calls == 1


def test_preflight_detects_non_state_bundle_mutation(tmp_path: Path) -> None:
    module = _operator_module()
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    provider = _RecordedProvider()
    provider.on_preflight = lambda: (root / "project.yaml").write_bytes(
        b"mutated outside state"
    )
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=provider,
        request=module.build_source_qualification_request(
            project=project,
            profile=profile,
            profile_document_hash=document_hash,
            generation_id="rainy-station-source-mutation-test-v1",
        ),
        attempt_id="rainy-station-source-mutation-attempt-v1",
    )

    with pytest.raises(AiVideoError) as caught:
        operator.preflight(require_new_attempt=True)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_cli_json_serialization_rejects_binary_or_unknown_objects() -> None:
    script = _script_module()

    with pytest.raises(ValueError, match="binary"):
        script._jsonable(b"raw")
    with pytest.raises(ValueError, match="unsupported"):
        script._jsonable(object())


def test_cli_main_sanitizes_unsupported_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script = _script_module()
    monkeypatch.setattr(script, "execute", lambda _: object())
    monkeypatch.setattr(
        "sys.argv",
        [
            "execute_shot_continuity_source.py",
            "status",
            "--root",
            "/tmp/source-root",
            "--artifact-root",
            "/tmp/artifact-root",
            "--comfy-root",
            "/tmp/comfy-root",
            "--generation-id",
            "source-generation-v1",
            "--attempt-id",
            "source-attempt-v1",
        ],
    )

    assert script.main() == 2
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert '"error_code": "source_operator_invalid"' in captured.err


def test_cli_exposes_only_explicit_local_actions() -> None:
    script = _script_module()
    parser = script._parser()
    base = [
        "preflight",
        "--root",
        "/tmp/source-root",
        "--artifact-root",
        "/tmp/artifact-root",
        "--comfy-root",
        "/tmp/comfy-root",
        "--generation-id",
        "source-generation-v1",
        "--attempt-id",
        "source-attempt-v1",
        "--require-new-attempt",
    ]

    assert parser.parse_args(base).action == "preflight"
    for forbidden in ("--retry", "--endpoint", "--model", "--prompt", "--seed"):
        with pytest.raises(SystemExit):
            parser.parse_args([*base, forbidden, "override"])


def test_cli_dispatches_exactly_one_action() -> None:
    script = _script_module()
    calls: list[tuple[str, bool]] = []

    class _Operator:
        def preflight(self, *, require_new_attempt: bool):
            calls.append(("preflight", require_new_attempt))
            return {"next_action": "submit"}

    args = script._parser().parse_args(
        [
            "preflight",
            "--root",
            "/tmp/source-root",
            "--artifact-root",
            "/tmp/artifact-root",
            "--comfy-root",
            "/tmp/comfy-root",
            "--generation-id",
            "source-generation-v1",
            "--attempt-id",
            "source-attempt-v1",
            "--require-new-attempt",
        ]
    )

    result = script.execute(args, opener=lambda **_: _Operator())

    assert result == {"next_action": "submit"}
    assert calls == [("preflight", True)]


def test_source_boundary_candidate_activates_reopens_and_replays(
    tmp_path: Path,
) -> None:
    root, committer, attempt_id, _, _, candidate = _reach_source_boundary_candidate(
        tmp_path
    )

    assert candidate.active_project != candidate.attempts[-1].candidate_project
    assert load_production_project(root / "project.yaml").manifest == candidate

    activated = committer.activate_video_candidate(attempt_id=attempt_id)
    assert activated.active_p0_qualification_prepared is None
    assert committer.replay_active_video_generation(attempt_id=attempt_id) == activated
    assert load_production_project(root / "project.yaml").manifest == activated


def test_strict_reader_and_activation_reject_semantic_source_tamper(
    tmp_path: Path,
) -> None:
    root, committer, attempt_id, _, _, candidate = _reach_source_boundary_candidate(
        tmp_path
    )
    attempt = next(item for item in candidate.attempts if item.attempt_id == attempt_id)
    state = attempt.video_generation_state
    assert state is not None and state.source_boundary_evaluation is not None
    evaluation = state.source_boundary_evaluation
    assert evaluation.evidence is not None and evaluation.receipt is not None
    evidence = committer._reopen_source_boundary_review_evidence(evaluation.evidence)
    values = evidence.model_dump(mode="python", exclude={"content_hash"})
    values["measured_metadata_hash"] = "f" * 64
    drifted_evidence = SourceBoundaryReviewEvidence.create(**values)
    drifted_receipt = adjudicate_source_boundary_review(drifted_evidence)
    evidence_path = canonical_source_boundary_review_evidence_path(
        drifted_evidence.content_hash
    )
    receipt_path = canonical_source_boundary_review_receipt_path(
        drifted_receipt.content_hash
    )
    evidence_bytes = drifted_evidence.model_dump_json().encode("utf-8")
    receipt_bytes = drifted_receipt.model_dump_json().encode("utf-8")
    (root / evidence_path).write_bytes(evidence_bytes)
    (root / receipt_path).write_bytes(receipt_bytes)
    drifted_evaluation = evaluation.model_copy(
        update={
            "evidence": evaluation.evidence.model_copy(
                update={
                    "path": evidence_path,
                    "content_hash": drifted_evidence.content_hash,
                    "file_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
                }
            ),
            "receipt": evaluation.receipt.model_copy(
                update={
                    "path": receipt_path,
                    "content_hash": drifted_receipt.content_hash,
                    "evidence_content_hash": drifted_evidence.content_hash,
                    "file_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
                }
            ),
        }
    )
    drifted_state = state.model_copy(
        update={"source_boundary_evaluation": drifted_evaluation}
    )
    drifted_attempt = attempt.model_copy(
        update={"video_generation_state": drifted_state}
    )
    drifted_manifest = ProductionManifest.model_validate(
        candidate.model_copy(
            update={
                "manifest_revision": candidate.manifest_revision + 1,
                "attempts": tuple(
                    drifted_attempt if item.attempt_id == attempt_id else item
                    for item in candidate.attempts
                ),
            }
        ).model_dump(mode="python")
    )
    manifest_path = root / "state/manifest.json"
    manifest_path.write_text(drifted_manifest.model_dump_json(), encoding="utf-8")
    before_activation = manifest_path.read_bytes()

    with pytest.raises(AiVideoError, match="Source boundary"):
        load_production_project(root / "project.yaml")
    with pytest.raises(AiVideoError, match="Source boundary"):
        committer.activate_video_candidate(attempt_id=attempt_id)

    assert manifest_path.read_bytes() == before_activation


@pytest.mark.parametrize(
    ("motion_direction_match", "expected_verdict"),
    (
        (True, "pass"),
        (False, "fail"),
        (None, "not_evaluated"),
    ),
)
def test_intent_only_source_review_requires_explicit_evidence_recovery(
    tmp_path: Path,
    motion_direction_match: bool | None,
    expected_verdict: str,
) -> None:
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    profile = _bind_profile_to_p0(root, profile)
    module = _operator_module()
    request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-boundary-recovery-v1",
    )
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=_RecordedProvider(),
        request=request,
        attempt_id="rainy-station-source-boundary-recovery-attempt-v1",
    )
    operator.submit(require_new_attempt=True)
    operator.poll()
    operator.fetch()
    operator.upgrade_manifest_214()

    class _CaptureThenFail:
        def __init__(self, wrapped) -> None:
            self.wrapped = wrapped
            self.recovered = None
            self.calls = 0

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

        def create_intent(self, *args):
            return self.wrapped.create_intent(*args)

        def __call__(self, *args):
            self.calls += 1
            self.recovered = self.wrapped(*args)
            raise RuntimeError("simulated crash after evaluator outcome")

    current = load_production_project(root / "project.yaml")
    local_profile, _ = _profile_for(current)
    local_profile = _bind_profile_to_p0(root, local_profile)
    state = operator.committer._read_manifest().attempts[-1].video_generation_state
    assert state is not None and state.local_fetch_receipt is not None
    fetch = operator.committer._reopen_local_video_fetch(state.local_fetch_receipt)
    p0, _, _, _, _ = operator.committer.reopen_p0_qualification_prepared()
    first = current.asset_paths[local_profile.first_frame_asset_id].read_bytes()
    last = current.asset_paths[local_profile.last_frame_asset_id].read_bytes()
    sampler = _ExactAnchorSampler(_resized_rgb(first), _resized_rgb(last))
    local_reviewer = SourceBoundaryReviewerV1(
        source_profile_content_hash=local_profile.profile_content_hash,
        source_execution_stack_hash=local_profile.source_execution_stack_hash,
        measurement_contract=SourceBoundaryMeasurementContractV1.create(
            p0_qualification_receipt_hash=p0.content_hash,
            p0_rubric_hash=p0.rubric_hash,
            first_frame_asset_id=local_profile.first_frame_asset_id,
            first_frame_sha256=local_profile.first_frame_sha256,
            last_frame_asset_id=local_profile.last_frame_asset_id,
            last_frame_sha256=local_profile.last_frame_sha256,
            sample_width=1344,
            sample_height=768,
            decoder=sampler.identity,
        ),
        human_decision=SourceBoundaryHumanDecisionV1.create(
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=fetch.artifact_sha256,
            reviewer=ToolIdentity(name="human-test", version="2026-08-26"),
            raw_full_speed_reviewed=True,
            identity_match=True,
            camera_axis_match=True,
            framing_match=True,
            motion_direction_match=motion_direction_match,
            action_phase_match=True,
            entrance_exit_match=True,
            no_unexpected_stop_or_reentry=True,
            pacing_waiver=True,
            rationale="Exact fixture output accepted with pacing waiver.",
        ),
        evaluator=ToolIdentity(
            name="ai-video-source-boundary-review",
            version="1",
        ),
        sampler=sampler,
        first_anchor_bytes=first,
        last_anchor_bytes=last,
    )
    failing = _CaptureThenFail(local_reviewer)
    calls = 0

    def counted_probe(held_fd):
        nonlocal calls
        calls += 1
        return _source_probe(held_fd)

    with pytest.raises(RuntimeError, match="simulated crash"):
        operator.committer.prepare_video_activation_candidate(
            attempt_id=operator.attempt_id,
            probe=counted_probe,
            source_boundary_reviewer=failing,
        )
    assert failing.recovered is not None and calls == 1 and failing.calls == 1
    intent_state = (
        operator.committer._read_manifest().attempts[-1].video_generation_state
    )
    assert (
        intent_state is not None
        and intent_state.source_boundary_evaluation is not None
        and intent_state.source_boundary_evaluation.phase
        is SourceBoundaryEvaluationPhase.INTENT
    )
    with pytest.raises(AiVideoError) as replay:
        operator.committer.prepare_video_activation_candidate(
            attempt_id=operator.attempt_id,
            probe=counted_probe,
            source_boundary_reviewer=failing,
        )
    assert replay.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert calls == 2 and failing.calls == 1

    operator.committer.recover_source_boundary_review(
        attempt_id=operator.attempt_id,
        recovered_evidence=failing.recovered,
        probe=counted_probe,
    )
    assert calls == 3 and failing.calls == 1
    recovered_manifest = load_production_project(root / "project.yaml").manifest
    recovered_state = recovered_manifest.attempts[-1].video_generation_state
    assert (
        recovered_state is not None
        and recovered_state.phase.value == "validate"
        and recovered_state.source_boundary_evaluation is not None
        and recovered_state.source_boundary_evaluation.receipt is not None
        and recovered_state.source_boundary_evaluation.receipt.verdict.value
        == expected_verdict
    )
    operator.committer.recover()
    assert failing.calls == 1
    terminal = _terminal_png(last)

    def prepare_recovered():
        return operator.committer.prepare_video_activation_candidate(
            attempt_id=operator.attempt_id,
            probe=counted_probe,
            source_boundary_reviewer=None,
            terminal_frame_extractor=lambda _source, _index: (
                TerminalFrameExtractionResult(
                    png_bytes=terminal,
                    extractor_name="fixture-extractor",
                    extractor_version="1",
                )
            ),
        )

    if expected_verdict == "pass":
        candidate = prepare_recovered()
        assert candidate.attempts[-1].video_generation_state.phase.value == "candidate"
    else:
        with pytest.raises(AiVideoError, match="Source boundary"):
            prepare_recovered()
        assert (
            operator.committer._read_manifest()
            .attempts[-1]
            .video_generation_state.phase.value
            == "validate"
        )
    assert calls == 4 and failing.calls == 1
