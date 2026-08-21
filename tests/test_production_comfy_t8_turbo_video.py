from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pytest

from ai_video.comfy_client import JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_t8_turbo_video import (
    ComfyUIT8TurboVideoProvider,
    T8TurboExecutionProfile,
    T8TurboLoraComponent,
    T8TurboRuntimeInspection,
    load_t8_turbo_video_execution_profile,
    t8_turbo_capabilities,
)
from ai_video.production.comfy_t8_video import (
    T8ModelComponent,
    t8_node_input_schema_sha256,
)
from ai_video.production.local_video import (
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
)
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoTaskState,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_turbo.json"
QUALITY_PROFILE_PATH = (
    REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_quality.json"
)
MP4 = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"


def _object_info(template: dict[str, object]) -> dict[str, object]:
    output_names = {
        "MiniMaxH3AudioConditioningT8": [
            "positive",
            "av_latent",
            "mux_audio",
            "conditioned_prompt",
            "media_map_json",
            "report",
        ],
        "MiniMaxH3TurboLoRA": ["MODEL"],
        "MiniMaxH3TurboSampler": ["SAMPLER"],
        "MiniMaxH3AVDecodeT8": [
            "frames",
            "generated_audio",
            "video_latent",
            "audio_latent",
        ],
    }
    result: dict[str, object] = {}
    for node in template.values():
        assert isinstance(node, dict)
        class_type = node["class_type"]
        inputs = node["inputs"]
        assert isinstance(class_type, str)
        assert isinstance(inputs, dict)
        names = tuple(inputs)
        result[class_type] = {
            "input": {
                "required": {name: ["ANY", {}] for name in names},
                "optional": {},
            },
            "input_order": {"required": list(names), "optional": []},
            "output_name": output_names.get(class_type, []),
        }
    return result


class Transport:
    def __init__(self, object_info: dict[str, object]) -> None:
        self.object_info = object_info
        self.workflows: list[dict[str, object]] = []

    def get_object_info(self) -> dict[str, object]:
        return self.object_info

    def submit_prompt(self, workflow: dict[str, object]) -> str:
        self.workflows.append(workflow)
        return "turbo-prompt-1"

    def poll_job(self, prompt_id: str, **_: object) -> JobResult:
        return JobResult(
            JobStatus.COMPLETED,
            prompt_id,
            history={
                "outputs": {
                    "13": {
                        "gifs": [
                            {
                                "filename": "turbo_00001.mp4",
                                "subfolder": "MiniMaxH3",
                                "type": "output",
                            },
                            {
                                "filename": "turbo_00001-audio.mp4",
                                "subfolder": "MiniMaxH3",
                                "type": "output",
                            },
                        ]
                    }
                }
            },
        )

    def fetch_artifact_bytes(self, **_: str) -> bytes:
        return MP4.read_bytes()


class Permit:
    def __init__(self, intent: str, request: str) -> None:
        self.intent = intent
        self.request = request
        self.consumed = False

    def _consume_local_video_submit_permit(
        self, *, intent_fingerprint: str, request_fingerprint: str
    ) -> bool:
        self.consumed = True
        return (intent_fingerprint, request_fingerprint) == (
            self.intent,
            self.request,
        )


def _sandbox(
    tmp_path: Path,
) -> tuple[Path, Path, T8TurboExecutionProfile, Transport]:
    canonical = load_t8_turbo_video_execution_profile(
        PROFILE_PATH, artifact_root=REPO_ROOT
    )
    artifact_root = tmp_path / "artifacts"
    comfy_root = tmp_path / "ComfyUI"
    for relative in (canonical.workflow_path, canonical.binding_path):
        target = artifact_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)
    template = json.loads((artifact_root / canonical.workflow_path).read_text())
    object_info = _object_info(template)
    components = []
    component_dirs = {
        "diffusion": "models/diffusion_models",
        "text_encoder": "models/text_encoders",
        "video_vae": "models/vae",
        "audio_vae": "models/vae",
    }
    for index, component in enumerate(canonical.components, start=1):
        payload = f"turbo-component-{index}".encode()
        path = comfy_root / component_dirs[component.role] / component.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        components.append(
            T8ModelComponent(
                role=component.role,
                filename=component.filename,
                size_bytes=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                precision=component.precision,
            )
        )
    lora_payload = b"sealed-turbo-lora"
    lora_path = comfy_root / "models/loras" / canonical.lora.filename
    lora_path.parent.mkdir(parents=True, exist_ok=True)
    lora_path.write_bytes(lora_payload)
    values = canonical.model_dump(mode="python", exclude={"profile_content_hash"})
    values["components"] = tuple(components)
    values["lora"] = T8TurboLoraComponent(
        filename=canonical.lora.filename,
        size_bytes=len(lora_payload),
        sha256=hashlib.sha256(lora_payload).hexdigest(),
        strength=1.0,
        low_vram=False,
    )
    values["turbo_node_input_schema_sha256"] = t8_node_input_schema_sha256(
        object_info, canonical.required_turbo_nodes
    )
    profile = T8TurboExecutionProfile.create(**values)
    return artifact_root, comfy_root, profile, Transport(object_info)


def _request(profile: T8TurboExecutionProfile) -> VideoGenerationRequest:
    return VideoGenerationRequest.create(
        generation_id="turbo-generation-1",
        provider_name="comfy-local-h3-t8",
        provider_kind="minimax_h3_t8_t2va_turbo",
        model_id="minimax-h3-t8-t2va-turbo",
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-t8-t2va-turbo",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
            profile_sha256=profile.profile_content_hash,
        ),
        target_shot_id="shot-1",
        target_shot_revision=1,
        target_shot_content_hash="4" * 64,
        target_asset_role="main",
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        prompt_text="cinematic rain with synchronized native ambience",
        negative_prompt_text="",
        image_bindings=(),
        output_requirement=VideoFlexibleOutputRequirement(
            timing_mode="frame_count",
            frame_count=124,
            dimension_mode="exact",
            width=1344,
            height=768,
            resolution_label="h3_t8_native",
            ratio="16:9",
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=True,
        ),
        seed=123456789,
        base_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=1,
            content_hash="1" * 64,
            file_sha256="5" * 64,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{'2' * 64}.json"),
            revision_id="2" * 64,
            content_hash="2" * 64,
            file_sha256="6" * 64,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            path=Path(f"state/dependency_graph.{'3' * 64}.json"),
            revision_id="3" * 64,
            content_hash="3" * 64,
            file_sha256="7" * 64,
        ),
        input_artifact_ids=("shot-1",),
        output_asset_id="turbo-video-1",
    )


def _provider(
    tmp_path: Path,
) -> tuple[ComfyUIT8TurboVideoProvider, Transport, T8TurboExecutionProfile]:
    artifact_root, comfy_root, profile, transport = _sandbox(tmp_path)
    provider = ComfyUIT8TurboVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        transport=transport,
        runtime_inspector=lambda: T8TurboRuntimeInspection(
            comfyui_commit=profile.comfyui_commit,
            t8_commit=profile.t8_commit,
            t8_version=profile.t8_version,
            turbo_commit=profile.turbo_commit,
            turbo_version=profile.turbo_version,
            videohelpersuite_commit=profile.videohelpersuite_commit,
            sageattention_version=profile.sageattention_version,
            launch_capabilities=("sage_attention",),
        ),
        clock=lambda: datetime(2026, 8, 21, tzinfo=UTC),
    )
    return provider, transport, profile


def test_turbo_profile_is_additive_and_preserves_the_quality_seal() -> None:
    profile = load_t8_turbo_video_execution_profile(
        PROFILE_PATH, artifact_root=REPO_ROOT
    )

    assert (
        hashlib.sha256(QUALITY_PROFILE_PATH.read_bytes()).hexdigest()
        == "0ff305dabe60f4591d6e121444024a377e0de41123a3284955cf9ad158f81bb1"
    )
    assert profile.steps == 6
    assert profile.scheduler == "simple"
    assert profile.lora.filename == "minimax_h3_turbo_v4_step600_ema.safetensors"
    assert profile.lora.strength == 1.0
    assert profile.lora.low_vram is False
    assert profile.native_audio_required is True
    assert profile.output_crf == 17
    assert profile.turbo_commit == "4274783a23afcfdbea3b4876cb79effd6c510785"
    assert profile.turbo_version == "1.2.3"
    assert (
        profile.lora.sha256
        == "5f3a626cd72c93a8b9318d6760c510bc5092d2ab13aaba1f932c5bab07a416d3"
    )
    assert profile.lora.size_bytes == 779_849_816
    assert (
        profile.turbo_node_input_schema_sha256
        == "76b696b1b6550558893c0a2ab611f73b66bff34681a0aee518afcca37c364071"
    )


def test_turbo_capability_is_a_distinct_explicit_local_lane() -> None:
    profile = load_t8_turbo_video_execution_profile(
        PROFILE_PATH, artifact_root=REPO_ROOT
    )
    capabilities = t8_turbo_capabilities(profile)
    assert capabilities.provider_name == "comfy-local-h3-t8"
    assert len(capabilities.variants) == 1
    variant = capabilities.variants[0]
    assert variant.capability_id == "minimax-h3-t8-t2va-turbo-v1"
    assert variant.provider_kind == "minimax_h3_t8_t2va_turbo"
    assert variant.model_id == "minimax-h3-t8-t2va-turbo"
    assert variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert variant.execution_kind is VideoExecutionKind.LOCAL
    assert variant.billing_kind is BillingKind.LOCAL_UNMETERED
    assert variant.output_capability is not None
    assert variant.output_capability.native_audio_options == (True,)


def test_turbo_preflight_and_submit_render_the_exact_six_step_graph(
    tmp_path: Path,
) -> None:
    provider, transport, profile = _provider(tmp_path)
    request = provider.resolve(_request(profile))
    provider.preflight(request)
    preview = provider.preview(request)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="turbo-attempt",
        request=request,
        preview=preview,
        recorded_at=datetime(2026, 8, 21, tzinfo=UTC),
    )
    permit = Permit(intent.intent_fingerprint, request.resolved_generation_hash)

    result = provider.submit_local(request, preview, intent, permit)

    assert permit.consumed is True
    workflow = transport.workflows[-1]
    assert workflow["5"]["inputs"]["prompt"] == request.prompt_text
    assert workflow["5"]["inputs"]["task_type"] == "T2VA"
    assert workflow["5"]["inputs"]["audio_mode"] == "native"
    assert workflow["6"]["class_type"] == "MiniMaxH3TurboLoRA"
    assert workflow["6"]["inputs"]["lora_name"] == profile.lora.filename
    assert workflow["6"]["inputs"]["strength"] == 1.0
    assert workflow["6"]["inputs"]["low_vram"] is False
    assert workflow["7"]["class_type"] == "MiniMaxH3TurboSampler"
    assert workflow["8"]["inputs"]["steps"] == 6
    assert workflow["8"]["inputs"]["scheduler"] == "simple"
    assert workflow["13"]["inputs"]["audio"] == ["12", 1]
    assert workflow["13"]["inputs"]["crf"] == 17
    submission = LocalVideoSubmission.from_submit_result(
        resolved=request, result=result
    )
    observation = provider.get_local_status(submission)
    assert observation.state is VideoTaskState.SUCCEEDED
    assert observation.provider_file_id is not None
    assert observation.provider_file_id.endswith("turbo_00001-audio.mp4:output")
    sink = BytesIO()
    receipt = provider.fetch_local(submission, observation, sink)
    assert receipt.artifact_sha256 == hashlib.sha256(MP4.read_bytes()).hexdigest()
    assert sink.getvalue() == MP4.read_bytes()


def test_turbo_preflight_rejects_lora_drift_before_permit_or_submit(
    tmp_path: Path,
) -> None:
    provider, transport, profile = _provider(tmp_path)
    lora_path = tmp_path / "ComfyUI/models/loras" / profile.lora.filename
    lora_path.write_bytes(b"corrupt")

    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(provider.resolve(_request(profile)))

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.workflows == []


def test_turbo_resolution_fails_closed_instead_of_falling_back_to_quality(
    tmp_path: Path,
) -> None:
    provider, _, profile = _provider(tmp_path)
    quality_request = _request(profile).model_copy(
        update={
            "provider_kind": "minimax_h3_t8_t2va",
            "model_id": "minimax-h3-t8-t2va-quality",
        }
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(quality_request)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_turbo_preflight_rejects_a_foreign_resolved_capability(
    tmp_path: Path,
) -> None:
    provider, transport, profile = _provider(tmp_path)
    resolved = provider.resolve(_request(profile))
    foreign = resolved.model_copy(
        update={"capability_id": "minimax-h3-t8-t2va-quality-v1"}
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(foreign)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.workflows == []


def test_turbo_provider_family_surface_is_exported_from_production_package() -> None:
    from ai_video.production import (
        ComfyUIT8TurboVideoProvider as PublicTurboProvider,
    )
    from ai_video.production import (
        LocalH3VideoProviderFamily as PublicH3Family,
    )

    assert PublicTurboProvider is ComfyUIT8TurboVideoProvider
    assert PublicH3Family.__name__ == "LocalH3VideoProviderFamily"
