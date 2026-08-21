from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ai_video.comfy_client import JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_video import (
    ComfyUIVideoProvider,
    LocalVideoExecutionProfile,
    load_local_video_execution_profile,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.local_video import (
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
)
from ai_video.production.video import (
    ContinuityArtifactIdentity,
    ContinuityConstraintSet,
    ContinuityReferenceBinding,
    ProviderProfilePointer,
    TerminalFrameEvidence,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoTaskState,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from production_project_factory import make_p8_video_generation_base


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "workflows/profiles/minimax_h3_fl2va.json"
QUALITY_PROFILE_PATH = (
    REPO_ROOT / "workflows/profiles/minimax_h3_fl2va_quality.json"
)
MP4 = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"


@dataclass
class Permit:
    intent_fingerprint: str
    request_fingerprint: str
    consumed: bool = False

    def _consume_local_video_submit_permit(self, **binding: str) -> bool:
        expected = {
            "intent_fingerprint": self.intent_fingerprint,
            "request_fingerprint": self.request_fingerprint,
        }
        if self.consumed or binding != expected:
            return False
        self.consumed = True
        return True


class Transport:
    def __init__(
        self,
        payload: bytes,
        *,
        submit_error: Exception | None = None,
        prompt_id: object = "prompt-1",
        job_status: JobStatus = JobStatus.COMPLETED,
    ) -> None:
        self.payload = payload
        self.submit_error = submit_error
        self.prompt_id = prompt_id
        self.job_status = job_status
        self.uploaded: list[bytes] = []
        self.workflows: list[dict] = []

    def get_object_info(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        return {
            name: {"input": {"required": {}}}
            for name in profile["required_nodes"]
        }

    def upload_image(self, path):
        data = Path(path).read_bytes()
        self.uploaded.append(data)
        return f"uploaded-{len(self.uploaded)}.png"

    def submit_prompt(self, workflow):
        self.workflows.append(workflow)
        if self.submit_error is not None:
            raise self.submit_error
        return self.prompt_id

    def poll_job(self, prompt_id, **_):
        if self.job_status is JobStatus.FAILED:
            return JobResult(
                JobStatus.FAILED,
                prompt_id,
                error=AiVideoError(
                    code=ErrorCode.COMFY_JOB_FAILED,
                    user_message="ComfyUI generation failed.",
                    retryable=False,
                ),
            )
        if self.job_status is JobStatus.TIMEOUT:
            return JobResult(
                JobStatus.TIMEOUT,
                prompt_id,
                error=AiVideoError(
                    code=ErrorCode.COMFY_JOB_TIMEOUT,
                    user_message="ComfyUI generation timed out.",
                    retryable=True,
                ),
            )
        return JobResult(
            JobStatus.COMPLETED,
            prompt_id,
            history={
                "outputs": {
                    "14": {
                        "videos": [
                            {
                                "filename": "h3-output.mp4",
                                "subfolder": "video",
                                "type": "output",
                            }
                        ]
                    }
                }
            },
        )

    def fetch_artifact_bytes(self, **_):
        return self.payload


def _profile_and_comfy_root(
    tmp_path: Path, profile_path: Path = PROFILE_PATH
):
    artifact_root = tmp_path / "artifact-root"
    canonical = load_local_video_execution_profile(
        profile_path, artifact_root=REPO_ROOT
    )
    raw = canonical.model_dump(mode="json")
    workflow = artifact_root / canonical.workflow_path
    binding = artifact_root / canonical.binding_path
    workflow.parent.mkdir(parents=True)
    binding.parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / canonical.workflow_path, workflow)
    shutil.copyfile(REPO_ROOT / canonical.binding_path, binding)
    comfy_root = tmp_path / "ComfyUI"
    components = []
    directories = {
        "diffusion": "diffusion_models",
        "text_encoder": "text_encoders",
        "video_vae": "vae",
        "audio_vae": "vae",
    }
    for index, component in enumerate(raw["components"]):
        payload = f"component-{index}".encode()
        path = comfy_root / "models" / directories[component["role"]] / component["filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        components.append(
            {
                **component,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    profile = type(canonical).create(
        **{
            **raw,
            "components": components,
            "workflow_sha256": hashlib.sha256(workflow.read_bytes()).hexdigest(),
            "binding_sha256": hashlib.sha256(binding.read_bytes()).hexdigest(),
            "comfyui_commit": "b" * 40,
        }
    )
    return artifact_root, comfy_root, profile


def _request(
    root: Path,
    profile: LocalVideoExecutionProfile,
    *,
    last: bool,
    seed: int | None = 19,
    width: int = 608,
    height: int = 352,
):
    inputs = make_p8_video_generation_base(root, schema_version="2.8")
    shot = inputs.project.shots[0]
    source = inputs.project.registry.assets[0]
    first = VideoImageReferenceBinding(
        role="first_frame",
        asset_id=source.asset_id,
        asset_sha256=source.sha256,
        mime_type=source.mime_type,
        width=source.width or 64,
        height=source.height or 64,
        size_bytes=source.size_bytes,
    )
    images = (
        first,
        *(
            (
                VideoImageReferenceBinding(
                    role="last_frame",
                    asset_id=source.asset_id,
                    asset_sha256=source.sha256,
                    mime_type=source.mime_type,
                    width=source.width or 64,
                    height=source.height or 64,
                    size_bytes=source.size_bytes,
                ),
            )
            if last
            else ()
        ),
    )
    terminal = TerminalFrameEvidence.create(
        source_shot_id="source-shot",
        source_shot_revision=1,
        source_shot_content_hash="a" * 64,
        source_video_asset_id="source-video",
        source_video_sha256="b" * 64,
        source_generation_id="source-generation",
        source_request_input_hash="c" * 64,
        source_resolved_generation_hash="d" * 64,
        source_provenance_receipt_id="source-provenance",
        extraction_receipt_id="e" * 64,
        source_registry=inputs.project.manifest.active_registry,
        source_container_name="mp4",
        source_codec_name="h264",
        source_width=source.width or 64,
        source_height=source.height or 64,
        source_fps_numerator=24,
        source_fps_denominator=1,
        source_duration_milliseconds=1000,
        source_frame_count=24,
        frame_index=23,
        timestamp_numerator=23,
        timestamp_denominator=24,
        selection_rule="generated_candidate_terminal",
        extraction_contract_version="v1",
        extractor_name="ffmpeg",
        extractor_version="test",
        extracted_asset_id=source.asset_id,
        extracted_sha256=source.sha256,
        extracted_mime_type="image/png",
        extracted_size_bytes=source.size_bytes,
        extracted_width=source.width or 64,
        extracted_height=source.height or 64,
        extracted_color_space="rgb24",
    )
    constraints = ContinuityConstraintSet.create(
        scene_identity=ContinuityArtifactIdentity(
            artifact_id="scene-1", revision=1, content_hash="1" * 64
        ),
        character_identities=(
            ContinuityArtifactIdentity(
                artifact_id="character-1", revision=1, content_hash="2" * 64
            ),
        ),
        camera_axis="same-axis",
        framing="same-framing",
        lighting="same-lighting",
        color="same-color",
        motion_direction="forward",
        exit_state="walking",
        entrance_state="walking",
    )
    continuity = ContinuityReferenceBinding.create(
        role="first_frame",
        terminal_frame=terminal,
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        constraints=constraints,
    )
    request = VideoGenerationRequest.create(
        generation_id="h3-adapter-test",
        provider_name="comfy-local-h3",
        provider_kind="minimax_h3_fl2va",
        model_id="minimax-h3-fl2va",
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-fl2va",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
            profile_sha256=profile.profile_content_hash,
        ),
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        target_asset_role=shot.required_asset_roles[0].role,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text="Continue naturally from the exact frame.",
        negative_prompt_text="",
        image_bindings=images,
        continuity_binding=continuity,
        output_requirement=VideoFlexibleOutputRequirement(
            timing_mode="frame_count",
            frame_count=124,
            dimension_mode="exact",
            width=width,
            height=height,
            resolution_label="h3_native",
            ratio="adaptive",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=True,
        ),
        seed=seed,
        base_project=inputs.project.manifest.active_project,
        base_registry=inputs.project.manifest.active_registry,
        base_dependency_graph=inputs.project.manifest.active_dependency_graph,
        input_artifact_ids=(
            shot.artifact_id,
            "source-shot",
            "source-video",
            source.asset_id,
            "scene-1",
            "character-1",
        ),
        output_asset_id="h3-adapter-output",
    )
    return inputs, request, source


@pytest.mark.parametrize("last", (False, True))
@pytest.mark.parametrize("seed", (19, None))
def test_comfy_h3_binds_exact_frames_and_preserves_optional_last(
    tmp_path: Path, last: bool, seed: int | None
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    project_root = tmp_path / "project"
    inputs, request, source = _request(project_root, profile, last=last, seed=seed)
    transport = Transport(MP4.read_bytes())
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=project_root,
        image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
        transport=transport,
        commit_resolver=lambda: "b" * 40,
        clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
        poll_interval_seconds=0,
    )
    resolved = provider.resolve(request)
    provider.preflight(resolved)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="adapter-test",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    result = provider.submit_local(
        resolved,
        preview,
        intent,
        Permit(intent.intent_fingerprint, resolved.resolved_generation_hash),
    )
    workflow = transport.workflows[-1]

    assert hashlib.sha256(transport.uploaded[0]).hexdigest() == source.sha256
    expected_seed = (
        seed
        if seed is not None
        else int(request.request_input_hash[:16], 16) & ((1 << 63) - 1)
    )
    assert resolved.effective_seed == expected_seed
    assert workflow["6"]["inputs"]["noise_seed"] == expected_seed
    assert workflow["5"]["inputs"]["first_frame"] == ["15", 0]
    assert ("last_frame" in workflow["5"]["inputs"]) is last
    assert ("16" in workflow) is last
    assert len(transport.uploaded) == (2 if last else 1)
    submission = LocalVideoSubmission.from_submit_result(
        resolved=resolved, result=result
    )
    observation = provider.get_local_status(resolved, submission)
    from io import BytesIO

    sink = BytesIO()
    receipt = provider.fetch_local(resolved, submission, observation, sink)
    assert sink.getvalue() == MP4.read_bytes()
    assert receipt.artifact_sha256 == hashlib.sha256(MP4.read_bytes()).hexdigest()


def test_h3_profile_and_artifacts_fail_closed_on_tampering(tmp_path: Path) -> None:
    canonical = load_local_video_execution_profile(PROFILE_PATH, artifact_root=REPO_ROOT)
    assert canonical.upstream_repository == "https://github.com/Comfy-Org/workflow_templates"
    assert canonical.upstream_commit == "0e0f4577453136eaa1c0e9d4b700e3e5ce5bb416"
    assert canonical.upstream_path == Path("templates/video_minimax_h3_i2v.json")
    assert canonical.upstream_sha256 == "313b029321a8be303e827dad471bff3022ca564c8bf8c6198a3e70b65c599671"
    assert canonical.upstream_license_id == "MIT"
    raw = canonical.model_dump(mode="json")
    raw["upstream_commit"] = "f" * 40
    with pytest.raises(ValueError):
        LocalVideoExecutionProfile.model_validate(raw)


@pytest.mark.parametrize("payload", ("null", "[]", "42"))
def test_h3_profile_rejects_non_object_json(
    tmp_path: Path, payload: str
) -> None:
    candidate = tmp_path / "profile.json"
    candidate.write_text(payload, encoding="utf-8")

    with pytest.raises(AiVideoError) as exc_info:
        load_local_video_execution_profile(candidate, artifact_root=REPO_ROOT)
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_h3_quality_profile_is_additive_and_old_profile_hashes_are_unchanged() -> None:
    assert hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest() == (
        "efca71d54bdd9f8a935c1911429d00b38e351e497df35db630b4bdab320f1d1c"
    )
    assert hashlib.sha256(
        (REPO_ROOT / "workflows/templates/minimax_h3_fl2va_api.json").read_bytes()
    ).hexdigest() == "c736a12f35fd89f10a8db86f0769a85ca7bceb80d16feab62a1666cfd078737b"
    assert hashlib.sha256(
        (REPO_ROOT / "workflows/bindings/minimax_h3_fl2va_binding.yaml").read_bytes()
    ).hexdigest() == "e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c"
    old_profile = load_local_video_execution_profile(
        PROFILE_PATH, artifact_root=REPO_ROOT
    )
    assert old_profile.profile_content_hash == (
        "456b59c7a907d4b07c7d951d63ec03cbd0fb5c64638dbc8dad870aca09e2b604"
    )

    quality = load_local_video_execution_profile(
        QUALITY_PROFILE_PATH, artifact_root=REPO_ROOT
    )
    assert quality.lane_id == "minimax_h3_fl2va_quality_local"
    assert quality.workflow_path == Path(
        "workflows/templates/minimax_h3_fl2va_quality_api.json"
    )
    assert quality.binding_path == Path(
        "workflows/bindings/minimax_h3_fl2va_quality_binding.yaml"
    )


def test_h3_quality_profile_renders_1344x672_with_explicit_h264_crf17(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(
        tmp_path, QUALITY_PROFILE_PATH
    )
    project_root = tmp_path / "project"
    inputs, request, _ = _request(
        project_root, profile, last=False, width=1344, height=672
    )
    transport = Transport(MP4.read_bytes())
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=project_root,
        image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
        transport=transport,
        commit_resolver=lambda: "b" * 40,
        clock=lambda: datetime(2026, 8, 20, tzinfo=UTC),
        poll_interval_seconds=0,
    )
    resolved = provider.resolve(request)
    provider.preflight(resolved)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="adapter-quality-test",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 20, tzinfo=UTC),
    )
    provider.submit_local(
        resolved,
        preview,
        intent,
        Permit(intent.intent_fingerprint, resolved.resolved_generation_hash),
    )

    workflow = transport.workflows[-1]
    assert workflow["5"]["inputs"]["width"] == 1344
    assert workflow["5"]["inputs"]["height"] == 672
    assert workflow["14"]["inputs"]["codec"] == "h264"
    assert workflow["14"]["inputs"]["codec.encoding"] == "re-encode"
    assert workflow["14"]["inputs"]["codec.encoding.crf"] == 17


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("output_codec", "auto"),
        ("output_encoding", "auto"),
        ("output_crf", 15),
        ("output_crf", 19),
    ),
)
def test_h3_quality_profile_rejects_illegal_encoder_parameters(
    tmp_path: Path, field: str, value: object
) -> None:
    raw = json.loads(QUALITY_PROFILE_PATH.read_text(encoding="utf-8"))
    raw[field] = value
    raw["profile_content_hash"] = canonical_sha256(
        {key: item for key, item in raw.items() if key != "profile_content_hash"}
    )
    candidate = tmp_path / "quality-profile.json"
    candidate.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with pytest.raises(AiVideoError) as exc_info:
        load_local_video_execution_profile(candidate, artifact_root=REPO_ROOT)
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_h3_quality_profile_rejects_resealed_workflow_with_wrong_crf(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(
        tmp_path, QUALITY_PROFILE_PATH
    )
    workflow_path = artifact_root / profile.workflow_path
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["14"]["inputs"]["codec.encoding.crf"] = 23
    workflow_path.write_text(
        json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values["workflow_sha256"] = hashlib.sha256(workflow_path.read_bytes()).hexdigest()
    resealed = type(profile).create(**values)

    with pytest.raises(AiVideoError) as exc_info:
        ComfyUIVideoProvider(
            resealed,
            artifact_root=artifact_root,
            comfy_root=comfy_root,
            image_root=tmp_path,
            image_resolver=lambda *_: tmp_path / "missing",
            transport=Transport(MP4.read_bytes()),
            commit_resolver=lambda: "b" * 40,
        )
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


@pytest.mark.parametrize("artifact", ("workflow", "binding"))
def test_h3_sealed_workflow_and_binding_tampering_fail_closed(
    tmp_path: Path, artifact: str
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    relative = profile.workflow_path if artifact == "workflow" else profile.binding_path
    target = artifact_root / relative
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(AiVideoError):
        ComfyUIVideoProvider(
            profile,
            artifact_root=artifact_root,
            comfy_root=comfy_root,
            image_root=tmp_path,
            image_resolver=lambda *_: tmp_path / "missing",
            transport=Transport(MP4.read_bytes()),
            commit_resolver=lambda: "b" * 40,
        )


def test_h3_endpoint_has_no_remote_fallback(tmp_path: Path) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    with pytest.raises(AiVideoError):
        ComfyUIVideoProvider(
            profile,
            artifact_root=artifact_root,
            comfy_root=comfy_root,
            image_root=tmp_path,
            image_resolver=lambda *_: tmp_path / "missing",
            endpoint="https://api.minimax.io:443",
            transport=Transport(MP4.read_bytes()),
            commit_resolver=lambda: "b" * 40,
        )


def test_h3_submit_ambiguity_and_terminal_job_failure_are_normalized(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    project_root = tmp_path / "project"
    inputs, request, _ = _request(project_root, profile, last=False)

    def make_provider(transport: Transport) -> ComfyUIVideoProvider:
        return ComfyUIVideoProvider(
            profile,
            artifact_root=artifact_root,
            comfy_root=comfy_root,
            image_root=project_root,
            image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
            transport=transport,
            commit_resolver=lambda: "b" * 40,
            clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
            poll_interval_seconds=0,
        )

    submit_transport = Transport(
        MP4.read_bytes(),
        submit_error=AiVideoError(
            code=ErrorCode.COMFY_SUBMISSION_FAILED,
            user_message="Could not submit workflow to ComfyUI.",
            retryable=True,
        ),
    )
    provider = make_provider(submit_transport)
    resolved = provider.resolve(request)
    provider.preflight(resolved)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="adapter-submit-failure",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    permit = Permit(intent.intent_fingerprint, resolved.resolved_generation_hash)
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit_local(resolved, preview, intent, permit)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert permit.consumed is True
    assert len(submit_transport.workflows) == 1

    failed_provider = make_provider(
        Transport(MP4.read_bytes(), job_status=JobStatus.FAILED)
    )
    failed_resolved = failed_provider.resolve(request)
    submission = LocalVideoSubmission.from_submit_result(
        resolved=failed_resolved,
        result=LocalVideoSubmitResult.create(
            resolved=failed_resolved,
            provider_request_id="failed-prompt",
            submitted_at=datetime(2026, 8, 19, tzinfo=UTC),
        ),
    )
    observation = failed_provider.get_local_status(failed_resolved, submission)
    assert observation.state is VideoTaskState.FAILED
    assert observation.provider_file_id is None


def test_h3_invalid_post_submit_prompt_identity_is_outcome_unknown(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    project_root = tmp_path / "project"
    inputs, request, _ = _request(project_root, profile, last=False)
    transport = Transport(MP4.read_bytes(), prompt_id="invalid prompt id")
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=project_root,
        image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
        transport=transport,
        commit_resolver=lambda: "b" * 40,
        clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
    )
    resolved = provider.resolve(request)
    provider.preflight(resolved)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="adapter-invalid-prompt-id",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    permit = Permit(intent.intent_fingerprint, resolved.resolved_generation_hash)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit_local(resolved, preview, intent, permit)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert permit.consumed is True
    assert len(transport.workflows) == 1


def test_h3_unexpected_post_submit_transport_error_is_outcome_unknown(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    project_root = tmp_path / "project"
    inputs, request, _ = _request(project_root, profile, last=False)
    transport = Transport(
        MP4.read_bytes(), submit_error=RuntimeError("unexpected transport failure")
    )
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=project_root,
        image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
        transport=transport,
        commit_resolver=lambda: "b" * 40,
        clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
    )
    resolved = provider.resolve(request)
    provider.preflight(resolved)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="adapter-unexpected-submit-error",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    permit = Permit(intent.intent_fingerprint, resolved.resolved_generation_hash)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit_local(resolved, preview, intent, permit)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert permit.consumed is True
    assert len(transport.workflows) == 1


def test_h3_poll_timeout_is_outcome_unknown(tmp_path: Path) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    project_root = tmp_path / "project"
    inputs, request, _ = _request(project_root, profile, last=False)
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=project_root,
        image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
        transport=Transport(MP4.read_bytes(), job_status=JobStatus.TIMEOUT),
        commit_resolver=lambda: "b" * 40,
    )
    resolved = provider.resolve(request)
    submission = LocalVideoSubmission.from_submit_result(
        resolved=resolved,
        result=LocalVideoSubmitResult.create(
            resolved=resolved,
            provider_request_id="timed-out-prompt",
            submitted_at=datetime(2026, 8, 19, tzinfo=UTC),
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.get_local_status(resolved, submission)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN


def test_h3_missing_preflight_is_known_no_effect(tmp_path: Path) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    project_root = tmp_path / "project"
    inputs, request, _ = _request(project_root, profile, last=False)
    transport = Transport(MP4.read_bytes())
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=project_root,
        image_resolver=lambda asset_id, _: inputs.project.asset_paths[asset_id],
        transport=transport,
        commit_resolver=lambda: "b" * 40,
    )
    resolved = provider.resolve(request)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="missing-preflight",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    permit = Permit(intent.intent_fingerprint, resolved.resolved_generation_hash)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit_local(resolved, preview, intent, permit)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert permit.consumed is False
    assert transport.uploaded == []
    assert transport.workflows == []
