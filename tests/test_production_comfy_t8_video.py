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
from ai_video.production.comfy_t8_video import (
    ComfyUIT8VideoProvider,
    T8ExecutionProfile,
    T8ModelComponent,
    T8RuntimeInspection,
    load_t8_video_execution_profile,
    t8_node_input_schema_sha256,
)
from ai_video.production.local_video import (
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
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
PROFILE_PATH = REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_quality.json"
MP4 = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"


def _object_info() -> dict[str, object]:
    required_inputs = {
        "UNETLoader": ("unet_name", "weight_dtype"),
        "CLIPLoader": ("clip_name", "type"),
        "VAELoader": ("vae_name",),
        "MiniMaxH3AudioConditioningT8": (
            "clip",
            "video_vae",
            "audio_vae",
            "prompt",
            "width",
            "height",
            "length",
            "task_type",
            "audio_mode",
            "audio_denoise_strength",
            "add_source_as_reference",
            "prompt_primary_audio_ordinal",
            "strict_prompt_tags",
            "ref_image_size",
            "reference_video_policy",
        ),
        "MiniMaxH3DualClockSamplerT8": (
            "model",
            "av_latent",
            "steps",
            "shift_video",
            "shift_audio",
        ),
        "RandomNoise": ("noise_seed",),
        "BasicGuider": ("model", "conditioning"),
        "SamplerCustomAdvanced": (
            "noise",
            "guider",
            "sampler",
            "sigmas",
            "latent_image",
        ),
        "MiniMaxH3AVDecodeT8": ("av_latent", "video_vae", "audio_vae"),
        "VHS_VideoCombine": (
            "images",
            "frame_rate",
            "loop_count",
            "filename_prefix",
            "format",
            "pingpong",
            "save_output",
        ),
    }
    optional_inputs = {
        "CLIPLoader": ("device",),
        "MiniMaxH3AudioConditioningT8": (
            "drive_audio",
            "final_audio",
            "first_frame",
            "last_frame",
            "ref_images",
            "ref_videos",
            "ref_video_audios",
            "ref_audios",
        ),
        "MiniMaxH3DualClockSamplerT8": ("sampler_name", "scheduler"),
        "VHS_VideoCombine": ("audio", "meta_batch", "vae"),
    }
    output_names = {
        "MiniMaxH3AudioConditioningT8": (
            "positive",
            "av_latent",
            "mux_audio",
            "conditioned_prompt",
            "media_map_json",
            "report",
        ),
        "MiniMaxH3DualClockSamplerT8": ("model", "sampler", "sigmas"),
        "MiniMaxH3AVDecodeT8": (
            "frames",
            "generated_audio",
            "video_latent",
            "audio_latent",
        ),
    }
    result: dict[str, object] = {}
    for node, names in required_inputs.items():
        result[node] = {
            "input": {
                "required": {name: ["ANY", {}] for name in names},
                "optional": {
                    name: ["ANY", {}] for name in optional_inputs.get(node, ())
                },
            },
            "input_order": {
                "required": list(names),
                "optional": list(optional_inputs.get(node, ())),
            },
            "output_name": list(output_names.get(node, ())),
        }
    return result


class Transport:
    def __init__(
        self,
        *,
        artifacts: tuple[str, ...] | None = None,
        object_info: dict[str, object] | None = None,
    ) -> None:
        self.workflows: list[dict[str, object]] = []
        self.artifacts = artifacts or (
            "ai_video_t8_00001.mp4",
            "ai_video_t8_00001-audio.mp4",
        )
        self.fetched: list[str] = []
        self.object_info = object_info or _object_info()

    def get_object_info(self) -> dict[str, object]:
        return self.object_info

    def submit_prompt(self, workflow: dict[str, object]) -> str:
        self.workflows.append(workflow)
        return "t8-prompt-1"

    def poll_job(self, prompt_id: str, **_: object) -> JobResult:
        assert prompt_id == "t8-prompt-1"
        return JobResult(
            JobStatus.COMPLETED,
            prompt_id,
            history={
                "outputs": {
                    "11": {
                        "gifs": [
                            {
                                "filename": filename,
                                "subfolder": "MiniMaxH3",
                                "type": "output",
                            }
                            for filename in self.artifacts
                        ]
                    }
                }
            },
        )

    def fetch_artifact_bytes(
        self, *, filename: str, subfolder: str, type_: str
    ) -> bytes:
        assert subfolder == "MiniMaxH3"
        assert type_ == "output"
        self.fetched.append(filename)
        return MP4.read_bytes()


class Permit:
    def __init__(self, intent: str, request: str) -> None:
        self.intent = intent
        self.request = request
        self.consumed = False

    def _consume_local_video_submit_permit(
        self, *, intent_fingerprint: str, request_fingerprint: str
    ) -> bool:
        if self.consumed:
            return False
        self.consumed = True
        return (intent_fingerprint, request_fingerprint) == (
            self.intent,
            self.request,
        )


def _sandbox(tmp_path: Path) -> tuple[Path, Path, T8ExecutionProfile]:
    canonical = load_t8_video_execution_profile(PROFILE_PATH, artifact_root=REPO_ROOT)
    artifact_root = tmp_path / "artifacts"
    comfy_root = tmp_path / "ComfyUI"
    for relative in (canonical.workflow_path, canonical.binding_path):
        target = artifact_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)

    components = []
    component_dirs = {
        "diffusion": "models/diffusion_models",
        "text_encoder": "models/text_encoders",
        "video_vae": "models/vae",
        "audio_vae": "models/vae",
    }
    for index, component in enumerate(canonical.components, start=1):
        payload = f"t8-component-{index}".encode()
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

    values = canonical.model_dump(mode="python", exclude={"profile_content_hash"})
    values["components"] = tuple(components)
    values["t8_node_input_schema_sha256"] = t8_node_input_schema_sha256(
        _object_info(), canonical.required_t8_nodes
    )
    return artifact_root, comfy_root, T8ExecutionProfile.create(**values)


def _request(profile: T8ExecutionProfile) -> VideoGenerationRequest:
    project_hash = "1" * 64
    registry_hash = "2" * 64
    graph_hash = "3" * 64
    return VideoGenerationRequest.create(
        generation_id="t8-generation-1",
        provider_name="comfy-local-h3-t8",
        provider_kind="minimax_h3_t8_t2va",
        model_id="minimax-h3-t8-t2va-quality",
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-t8-t2va-quality",
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
        prompt_text="integrated_multimodal_description: cinematic rain\n"
        "overall_soundscape: clear synchronized rain\n"
        "non_diegetic_music: none",
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
            content_hash=project_hash,
            file_sha256="5" * 64,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{registry_hash}.json"),
            revision_id=registry_hash,
            content_hash=registry_hash,
            file_sha256="6" * 64,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            path=Path(f"state/dependency_graph.{graph_hash}.json"),
            revision_id=graph_hash,
            content_hash=graph_hash,
            file_sha256="7" * 64,
        ),
        input_artifact_ids=("shot-1",),
        output_asset_id="t8-video-1",
    )


def _provider(
    tmp_path: Path, *, transport: Transport | None = None
) -> tuple[ComfyUIT8VideoProvider, Transport, T8ExecutionProfile]:
    artifact_root, comfy_root, profile = _sandbox(tmp_path)
    selected_transport = transport or Transport()
    provider = ComfyUIT8VideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        transport=selected_transport,
        runtime_inspector=lambda: T8RuntimeInspection(
            comfyui_commit=profile.comfyui_commit,
            t8_commit=profile.t8_commit,
            t8_version=profile.t8_version,
            videohelpersuite_commit=profile.videohelpersuite_commit,
            sageattention_version=profile.sageattention_version,
            launch_capabilities=("sage_attention",),
        ),
        clock=lambda: datetime(2026, 8, 21, tzinfo=UTC),
        poll_interval_seconds=0,
    )
    return provider, selected_transport, profile


def test_t8_capability_is_one_explicit_local_t2va_native_audio_lane(
    tmp_path: Path,
) -> None:
    provider, _, _ = _provider(tmp_path)
    capabilities = provider.capabilities()
    assert capabilities.provider_name == "comfy-local-h3-t8"
    assert len(capabilities.variants) == 1
    variant = capabilities.variants[0]
    assert variant.capability_id == "minimax-h3-t8-t2va-quality-v1"
    assert variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert variant.execution_kind is VideoExecutionKind.LOCAL
    assert variant.billing_kind is BillingKind.LOCAL_UNMETERED
    assert variant.output_capability is not None
    assert variant.output_capability.native_audio_options == (True,)
    assert variant.allowed_image_roles == ()
    assert variant.max_reference_count == 0


def test_t8_profile_seals_exact_runtime_workflow_models_and_audio_semantics() -> None:
    profile = load_t8_video_execution_profile(PROFILE_PATH, artifact_root=REPO_ROOT)
    assert (
        profile.profile_content_hash
        == "4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7"
    )
    assert profile.t8_commit == "977df788fcf8b971dc3d0fc7d6baa79a0edfaf40"
    assert profile.t8_version == "1.36.2"
    assert profile.comfyui_commit == "7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa"
    assert profile.videohelpersuite_commit == "4ee72c065db22c9d96c2427954dc69e7b908444b"
    assert profile.sageattention_version == "2.2.0"
    assert (
        profile.sageattention_source_commit
        == "d1a57a546c3d395b1ffcbeecc66d81db76f3b4b5"
    )
    assert profile.required_launch_capabilities == ("sage_attention",)
    assert (
        profile.model_repository_revision == "dc559027db79c174125df4d827db55cd11178860"
    )
    assert tuple(
        (item.role, item.filename, item.size_bytes, item.sha256)
        for item in profile.components
    ) == (
        (
            "diffusion",
            "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
            20_970_379_616,
            "e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a",
        ),
        (
            "text_encoder",
            "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
            15_687_142_551,
            "35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6",
        ),
        (
            "video_vae",
            "minimax_h3_video_vae_fp16.safetensors",
            5_207_808_496,
            "7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522",
        ),
        (
            "audio_vae",
            "minimax_h3_audio_vae_fp32.safetensors",
            605_254_808,
            "8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48",
        ),
    )
    assert (
        profile.t8_node_input_schema_sha256
        == "f788ee99f1f916f10c5e2bd5f089101c7bcb0cc6c7686edeb37f83dbc030f9d7"
    )
    assert profile.width == 1344
    assert profile.height == 768
    assert profile.frame_count == 124
    assert profile.native_audio_required is True
    assert profile.final_av_filename_suffix == "-audio.mp4"
    assert profile.reject_video_only_sibling is True
    assert profile.lora_enabled is False
    assert profile.lora is None
    assert (
        profile.workflow_sha256
        == hashlib.sha256((REPO_ROOT / profile.workflow_path).read_bytes()).hexdigest()
    )
    assert (
        profile.workflow_sha256
        == "6a508f8522694297c2e3ce1157dd1b235cd34514d85bf3c2908f55020cd990a5"
    )
    assert (
        profile.binding_sha256
        == hashlib.sha256((REPO_ROOT / profile.binding_path).read_bytes()).hexdigest()
    )
    assert (
        profile.binding_sha256
        == "3af2ab9928d832253e22aaf14f47bf70ef80949f56a1664817accb8acacfd564"
    )


def test_t8_preflight_is_exact_and_precedes_local_permit_consumption(
    tmp_path: Path,
) -> None:
    provider, transport, profile = _provider(tmp_path)
    request = provider.resolve(_request(profile))
    provider.preflight(request)
    preview = provider.preview(request)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="t8-attempt",
        request=request,
        preview=preview,
        recorded_at=datetime(2026, 8, 21, tzinfo=UTC),
    )
    permit = Permit(intent.intent_fingerprint, request.resolved_generation_hash)
    provider.submit_local(request, preview, intent, permit)
    workflow = transport.workflows[-1]
    assert permit.consumed is True
    assert workflow["5"]["inputs"]["prompt"] == request.prompt_text
    assert workflow["5"]["inputs"]["width"] == 1344
    assert workflow["5"]["inputs"]["height"] == 768
    assert workflow["5"]["inputs"]["length"] == 124
    assert workflow["5"]["inputs"]["task_type"] == "T2VA"
    assert workflow["5"]["inputs"]["audio_mode"] == "native"
    assert workflow["6"]["inputs"]["steps"] == 20
    assert workflow["6"]["inputs"]["sampler_name"] == "res_multistep"
    assert workflow["6"]["inputs"]["scheduler"] == "simple"
    assert workflow["11"]["inputs"]["audio"] == ["10", 1]


@pytest.mark.parametrize(
    "inspection_update",
    (
        {"t8_commit": "f" * 40},
        {"t8_version": "0.0.0"},
        {"comfyui_commit": "f" * 40},
        {"videohelpersuite_commit": "f" * 40},
        {"sageattention_version": "0.0.0"},
        {"launch_capabilities": ()},
    ),
)
def test_t8_preflight_rejects_runtime_seal_drift_before_submit(
    tmp_path: Path, inspection_update: dict[str, object]
) -> None:
    artifact_root, comfy_root, profile = _sandbox(tmp_path)
    transport = Transport()
    values = {
        "comfyui_commit": profile.comfyui_commit,
        "t8_commit": profile.t8_commit,
        "t8_version": profile.t8_version,
        "videohelpersuite_commit": profile.videohelpersuite_commit,
        "sageattention_version": profile.sageattention_version,
        "launch_capabilities": ("sage_attention",),
        **inspection_update,
    }
    provider = ComfyUIT8VideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        transport=transport,
        runtime_inspector=lambda: T8RuntimeInspection(**values),
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(provider.resolve(_request(profile)))
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.workflows == []


@pytest.mark.parametrize("drift", ("component", "node_schema"))
def test_t8_preflight_rejects_component_or_node_schema_drift(
    tmp_path: Path,
    drift: str,
) -> None:
    artifact_root, comfy_root, profile = _sandbox(tmp_path)
    object_info = _object_info()
    if drift == "component":
        component = profile.components[0]
        (comfy_root / "models/diffusion_models" / component.filename).write_bytes(
            b"corrupt"
        )
    else:
        t8_node = object_info[profile.required_t8_nodes[0]]
        assert isinstance(t8_node, dict)
        t8_node["output_name"] = ["changed"]
    transport = Transport(object_info=object_info)
    provider = ComfyUIT8VideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        transport=transport,
        runtime_inspector=lambda: T8RuntimeInspection(
            comfyui_commit=profile.comfyui_commit,
            t8_commit=profile.t8_commit,
            t8_version=profile.t8_version,
            videohelpersuite_commit=profile.videohelpersuite_commit,
            sageattention_version=profile.sageattention_version,
            launch_capabilities=("sage_attention",),
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(provider.resolve(_request(profile)))
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.workflows == []


def test_t8_selects_only_final_audio_artifact_and_fetches_it(tmp_path: Path) -> None:
    provider, transport, profile = _provider(tmp_path)
    request = provider.resolve(_request(profile))
    provider.preflight(request)
    preview = provider.preview(request)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="t8-attempt",
        request=request,
        preview=preview,
        recorded_at=datetime(2026, 8, 21, tzinfo=UTC),
    )
    result = provider.submit_local(
        request,
        preview,
        intent,
        Permit(intent.intent_fingerprint, request.resolved_generation_hash),
    )
    submission = LocalVideoSubmission.from_submit_result(
        resolved=request, result=result
    )
    observation = provider.get_local_status(submission)
    assert observation.state is VideoTaskState.SUCCEEDED
    assert observation.provider_file_id is not None
    assert "-audio.mp4" in observation.provider_file_id
    sink = BytesIO()
    receipt = provider.fetch_local(submission, observation, sink)
    assert transport.fetched == ["ai_video_t8_00001-audio.mp4"]
    assert sink.getvalue() == MP4.read_bytes()
    assert receipt.artifact_sha256 == hashlib.sha256(MP4.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "artifacts",
    (
        ("ai_video_t8_00001.mp4",),
        ("ai_video_t8_00001-audio.mp4", "other-audio.mp4"),
    ),
)
def test_t8_rejects_video_only_or_ambiguous_audio_outputs(
    tmp_path: Path, artifacts: tuple[str, ...]
) -> None:
    provider, _, profile = _provider(tmp_path, transport=Transport(artifacts=artifacts))
    request = provider.resolve(_request(profile))
    submission = LocalVideoSubmission.from_submit_result(
        resolved=request,
        result=LocalVideoSubmitResult.create(
            resolved=request,
            provider_request_id="t8-prompt-1",
            submitted_at=datetime(2026, 8, 21, tzinfo=UTC),
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.get_local_status(submission)
    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_t8_endpoint_has_no_remote_or_provider_fallback(tmp_path: Path) -> None:
    artifact_root, comfy_root, profile = _sandbox(tmp_path)
    with pytest.raises(AiVideoError):
        ComfyUIT8VideoProvider(
            profile,
            artifact_root=artifact_root,
            comfy_root=comfy_root,
            endpoint="https://api.minimax.io:443",
            transport=Transport(),
            runtime_inspector=lambda: T8RuntimeInspection(
                comfyui_commit=profile.comfyui_commit,
                t8_commit=profile.t8_commit,
                t8_version=profile.t8_version,
                videohelpersuite_commit=profile.videohelpersuite_commit,
                sageattention_version=profile.sageattention_version,
                launch_capabilities=("sage_attention",),
            ),
        )

    provider, _, _ = _provider(tmp_path / "second")
    wrong = _request(profile).model_copy(update={"provider_name": "comfy-local-h3"})
    with pytest.raises(AiVideoError):
        provider.resolve(wrong)


def test_t8_profile_rejects_resealed_workflow_or_schema_drift(tmp_path: Path) -> None:
    artifact_root, comfy_root, profile = _sandbox(tmp_path)
    workflow_path = artifact_root / profile.workflow_path
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["11"]["inputs"].pop("audio")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values["workflow_sha256"] = hashlib.sha256(workflow_path.read_bytes()).hexdigest()
    resealed = T8ExecutionProfile.create(**values)
    with pytest.raises(AiVideoError):
        ComfyUIT8VideoProvider(
            resealed,
            artifact_root=artifact_root,
            comfy_root=comfy_root,
            transport=Transport(),
            runtime_inspector=lambda: T8RuntimeInspection(
                comfyui_commit=profile.comfyui_commit,
                t8_commit=profile.t8_commit,
                t8_version=profile.t8_version,
                videohelpersuite_commit=profile.videohelpersuite_commit,
                sageattention_version=profile.sageattention_version,
                launch_capabilities=("sage_attention",),
            ),
        )
