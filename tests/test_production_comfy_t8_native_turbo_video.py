from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pytest
import yaml

from ai_video.comfy_client import JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_t8_native_turbo_profile import (
    T8NativeTurboBinding,
    T8NativeTurboComponent,
    T8NativeTurboLoraSeal,
    T8NativeTurboRuntimeInspection,
    _expected_lora_tensor_shapes,
    load_t8_native_turbo_binding,
    load_t8_native_turbo_execution_profile,
    node_schema_seals,
    validate_t8_native_turbo_lora,
    validate_native_turbo_workflow,
)
from ai_video.production.comfy_t8_native_turbo_video import (
    ComfyUIT8NativeTurboVideoProvider,
    render_t8_native_turbo_workflow,
    t8_native_turbo_capabilities,
)
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    MotionRequirement,
    RoutingOutcome,
    VideoGenerationResolver,
)
from ai_video.production.local_video import (
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
)
from ai_video.production.video import (
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoMediaReferenceBinding,
)
from ai_video.production.video_compiler import CompiledProviderVideoRequest
from ai_video.production.video_requirement import (
    AssetEvidence,
    AudioNeed,
    ContinuityMode as RequirementContinuityMode,
    GenerationMode as RequirementGenerationMode,
    OutputGeometryPolicy,
    OutputNeed,
    SemanticReferenceRole,
)
from ai_video.workflow_loader import load_workflow_template
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_shot_router import (
    _asset,
    _context,
    _lifecycle,
    _policy,
    _verified_requirement,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATHS = {
    task: REPO_ROOT
    / f"workflows/profiles/minimax_h3_t8_{task.lower()}_turbo_native_v2.json"
    for task in ("T2VA", "I2VA", "FL2VA", "Ref2VA")
}
MP4 = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"


def _load(task: str):
    return load_t8_native_turbo_execution_profile(
        PROFILE_PATHS[task], artifact_root=REPO_ROOT
    )


def test_four_mode_specific_profiles_are_distinct_and_truthfully_available() -> None:
    profiles = tuple(_load(task) for task in PROFILE_PATHS)

    assert tuple(profile.task_type for profile in profiles) == (
        "T2VA",
        "I2VA",
        "FL2VA",
        "Ref2VA",
    )
    assert len({profile.capability_id for profile in profiles}) == 4
    assert len({profile.provider_kind for profile in profiles}) == 4
    assert len({profile.model_id for profile in profiles}) == 4
    assert len({profile.profile_content_hash for profile in profiles}) == 4
    assert _load("T2VA").availability == "live-ready"
    assert _load("I2VA").availability == "live-ready"
    assert _load("FL2VA").availability == "live-ready"
    assert _load("Ref2VA").availability == "live-ready"
    assert all(profile.lora.conversion_verified for profile in profiles)
    assert all(profile.lora.value_identity_verified for profile in profiles)
    assert all(not profile.availability_blockers for profile in profiles)


@pytest.mark.parametrize(
    "field",
    (
        "capability_id",
        "provider_kind",
        "model_id",
        "lane_id",
        "neutral_mode",
        "provider_mode",
    ),
)
def test_profile_rejects_resealed_cross_lane_identity(field: str) -> None:
    profile = _load("T2VA")
    other = _load("I2VA")
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values[field] = getattr(other, field)

    with pytest.raises(ValueError, match="profile task identity is not canonical"):
        type(profile).create(**values)


@pytest.mark.parametrize("task", tuple(PROFILE_PATHS))
def test_profiles_seal_one_native_sampler_and_converted_lora(task: str) -> None:
    profile = _load(task)
    workflow = load_workflow_template(REPO_ROOT / profile.workflow_path)
    classes = tuple(node["class_type"] for node in workflow.values())

    assert classes.count("LoraLoaderBypassModelOnly") == 1
    assert classes.count("MiniMaxH3DualClockSamplerT8") == 1
    assert not set(profile.forbidden_nodes).intersection(classes)
    assert workflow["2"]["inputs"] == {
        "model": ["1", 0],
        "lora_name": profile.lora.filename,
        "strength_model": 1.0,
    }
    assert workflow["7"]["inputs"]["steps"] == 4
    assert workflow["7"]["inputs"]["shift_video"] == 12.0
    assert workflow["7"]["inputs"]["shift_audio"] == 3.0
    assert workflow["7"]["inputs"]["sampler_name"] == "dual_clock_euler"
    assert workflow["7"]["inputs"]["scheduler"] == "native_flow"
    assert "_pruned_" not in workflow["1"]["inputs"]["unet_name"]
    assert profile.lora.filename == "minimax_h3_turbo_4step_ema_comfyui.safetensors"
    assert profile.lora.source_repository_id == "DARK-MING/MiniMax-H3-Turbo-Lora"
    assert profile.lora.source_repository_revision == (
        "dff52016c06373336893f94e64b6dfea9a4d2db0"
    )
    assert profile.lora.source_sha256 == (
        "8d645b67e606874e9179b277cea721c1f1e75830532fcc2206e23353cb33edc5"
    )
    assert profile.lora.module_count == 259


def test_ref2va_profile_seals_standalone_reference_audio_only() -> None:
    profile = _load("Ref2VA")
    workflow = load_workflow_template(REPO_ROOT / profile.workflow_path)
    conditioning = workflow["6"]["inputs"]

    assert not any(
        key == "ref_video_audios" or key.startswith("ref_video_audios.")
        for key in conditioning
    )
    assert profile.reference_video_fps == 24
    assert profile.reference_video_min_duration_millis == 2000
    assert profile.reference_video_max_duration_millis == 15000


@pytest.mark.parametrize(
    "forbidden_key",
    (
        "ref_video_audios",
        "ref_video_audios.ref_video_audio_0",
        "ref_video_audios.any_future_relation",
    ),
    ids=("exact-group", "current-autogrow-key", "future-autogrow-key"),
)
def test_ref2va_profile_rejects_video_audio_linkage(forbidden_key: str) -> None:
    profile = _load("Ref2VA")
    workflow = json.loads((REPO_ROOT / profile.workflow_path).read_text())
    workflow["6"]["inputs"][forbidden_key] = ["14", 1]

    with pytest.raises(AiVideoError) as exc_info:
        validate_native_turbo_workflow(
            profile,
            workflow,
            T8NativeTurboBinding.model_validate(
                yaml.safe_load((REPO_ROOT / profile.binding_path).read_bytes())
            ),
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_profile_loader_rejects_larry_sampler_topology() -> None:
    profile = _load("T2VA")
    workflow = json.loads((REPO_ROOT / profile.workflow_path).read_text())
    workflow["7"]["class_type"] = "MiniMaxH3TurboSampler"

    with pytest.raises(AiVideoError) as exc_info:
        validate_native_turbo_workflow(
            profile,
            workflow,
            T8NativeTurboBinding.model_validate(
                yaml.safe_load((REPO_ROOT / profile.binding_path).read_bytes())
            ),
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_profile_files_pin_current_workflow_and_binding_bytes() -> None:
    expected = {
        "T2VA": "ff374a645eb15112b4c9d4341d1c61bcb80f32bdc55f7325cfe1c8153db5d6bf",
        "I2VA": "f73fe4a9adef3275ba4b6c9b3bd0307bed39a40542f80747867f2cb46df3e667",
        "FL2VA": "5fbb4b367eec6854c23d98600d96e366053da07e7635a9e920a6d856172b7a4f",
        "Ref2VA": "0bb8ebf9688369f89d959d8273a81f73dcc6e02e96c1a20a52110583ace7db9d",
    }

    assert {task: _load(task).profile_content_hash for task in PROFILE_PATHS} == expected


def test_node_schema_seal_omits_mutable_runtime_file_inventory() -> None:
    def schema(files: list[str]):
        return {
            "LoadImage": {
                "input": {
                    "required": {
                        "image": [files, {"image_upload": True}],
                    }
                },
                "input_order": {"required": ["image"], "optional": []},
                "output_name": ["IMAGE", "MASK"],
            }
        }

    assert node_schema_seals(schema(["before.png"]), ("LoadImage",)) == (
        node_schema_seals(
            schema(["before.png", "new-upload.png"]), ("LoadImage",)
        )
    )


def _counts(profile):
    constraints = t8_native_turbo_capabilities(
        profile
    ).variants[0].binding_cardinality_constraints
    return {
        tuple(item.roles): (item.min_count, item.max_count) for item in constraints
    }


def test_four_capabilities_expose_exact_mode_and_binding_grammar() -> None:
    t2 = t8_native_turbo_capabilities(_load("T2VA")).variants[0]
    i2 = t8_native_turbo_capabilities(_load("I2VA")).variants[0]
    fl2 = t8_native_turbo_capabilities(_load("FL2VA")).variants[0]
    ref = t8_native_turbo_capabilities(_load("Ref2VA")).variants[0]

    assert (t2.mode, i2.mode, fl2.mode, ref.mode) == (
        VideoGenerationMode.TEXT_TO_VIDEO,
        VideoGenerationMode.IMAGE_TO_VIDEO,
        VideoGenerationMode.IMAGE_TO_VIDEO,
        VideoGenerationMode.REFERENCE_TO_VIDEO,
    )
    assert _counts(_load("T2VA")) == {
        ("first_frame",): (0, 0),
        ("last_frame",): (0, 0),
        ("reference",): (0, 0),
        ("reference_video",): (0, 0),
        ("reference_audio",): (0, 0),
        ("reference", "reference_video", "reference_audio"): (0, 0),
    }
    assert _counts(_load("I2VA"))[("first_frame",)] == (1, 1)
    assert _counts(_load("I2VA"))[
        ("reference", "reference_video", "reference_audio")
    ] == (0, 0)
    assert _counts(_load("FL2VA"))[("last_frame",)] == (1, 1)
    assert _counts(_load("Ref2VA")) == {
        ("first_frame",): (0, 0),
        ("last_frame",): (0, 0),
        ("reference",): (0, 9),
        ("reference_video",): (0, 3),
        ("reference_audio",): (0, 3),
        ("reference", "reference_video", "reference_audio"): (1, 15),
    }


def test_fl2va_compiler_preserves_neutral_first_last_frame_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _load("FL2VA")
    first = _asset("first_frame", "native-v2-first", "8" * 64)
    last = _asset("last_frame", "native-v2-last", "9" * 64)
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
        keyframe=first,
        last_frame=last,
    )
    output = VideoFlexibleOutputRequirement(
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
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        generation_mode=RequirementGenerationMode.FIRST_LAST_FRAME_VIDEO,
        continuity_mode=RequirementContinuityMode.NONE,
        semantic_reference_roles=(
            SemanticReferenceRole.FIRST_FRAME,
            SemanticReferenceRole.LAST_FRAME,
        ),
        asset_evidence=(
            AssetEvidence(
                role=SemanticReferenceRole.FIRST_FRAME,
                asset_id=first.asset_id,
                asset_sha256=first.asset_sha256,
                mime_type=first.mime_type,
                width=first.width,
                height=first.height,
                size_bytes=first.size_bytes,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.LAST_FRAME,
                asset_id=last.asset_id,
                asset_sha256=last.asset_sha256,
                mime_type=last.mime_type,
                width=last.width,
                height=last.height,
                size_bytes=last.size_bytes,
            ),
        ),
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=1344,
            height=768,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    capabilities = t8_native_turbo_capabilities(profile)
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=ProviderProfilePointer(
            profile_id=profile.capability_id,
            profile_version="v2",
            profile_path=Path(
                f"provider-profiles/{profile.profile_content_hash}.json"
            ),
            profile_sha256=profile.profile_content_hash,
        ),
        capabilities=capabilities,
        selected_capability_id=profile.capability_id,
        output_requirement=output,
        lifecycle=_lifecycle(context).model_copy(
            update={
                "input_artifact_ids": (
                    context.target_shot_id,
                    first.asset_id,
                    last.asset_id,
                )
            }
        ),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-t8-native-turbo-video-compiler",
            compiler_version="2",
        ),
    )
    assert routing.decision.outcome is RoutingOutcome.SELECTED
    assert routing.provider_bound_request is not None
    input_root = tmp_path / "inputs"
    input_root.mkdir()
    provider = ComfyUIT8NativeTurboVideoProvider(
        profile,
        artifact_root=REPO_ROOT,
        comfy_root=REPO_ROOT,
        input_root=input_root,
        asset_resolver=lambda *_: input_root / "unused",
        runtime_inspector=lambda: (_ for _ in ()).throw(
            AssertionError("offline compilation must not inspect runtime")
        ),
        transport=object(),
    )
    monkeypatch.setattr(provider, "capabilities", lambda: capabilities)

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert projection.requirement.generation_mode is (
        RequirementGenerationMode.FIRST_LAST_FRAME_VIDEO
    )
    assert compiled.request.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert tuple(item.role for item in compiled.request.image_bindings) == (
        "first_frame",
        "last_frame",
    )


class _NoEffectTransport:
    def __init__(self) -> None:
        self.object_info_calls = 0
        self.uploads: list[Path] = []
        self.posts: list[dict[str, object]] = []

    def get_object_info(self):
        self.object_info_calls += 1
        return {}

    def upload_input(self, path):
        self.uploads.append(Path(path))
        return Path(path).name

    def submit_prompt(self, workflow):
        self.posts.append(workflow)
        return "native-v2-prompt"

    def poll_job(self, prompt_id: str, **_: object) -> JobResult:
        return JobResult(
            JobStatus.COMPLETED,
            prompt_id,
            history={
                "outputs": {
                    "12": {
                        "gifs": [
                            {
                                "filename": "native-v2_00001.mp4",
                                "subfolder": "MiniMaxH3",
                                "type": "output",
                            },
                            {
                                "filename": "native-v2_00001-audio.mp4",
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


def _request(
    profile,
    *,
    image_bindings: tuple[VideoImageReferenceBinding, ...] = (),
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = (),
) -> VideoGenerationRequest:
    mode = t8_native_turbo_capabilities(profile).variants[0].mode
    return VideoGenerationRequest.create(
        generation_id="native-v2-generation",
        provider_name="comfy-local-h3-t8",
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        provider_profile=ProviderProfilePointer(
            profile_id=profile.capability_id,
            profile_version="v2",
            profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
            profile_sha256=profile.profile_content_hash,
        ),
        target_shot_id="shot-1",
        target_shot_revision=1,
        target_shot_content_hash="4" * 64,
        target_asset_role="main",
        target_visual_strategy="generated_video",
        mode=mode,
        prompt_text="cinematic motion with synchronized native ambience",
        negative_prompt_text="",
        image_bindings=image_bindings,
        media_bindings=media_bindings,
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
        seed=7,
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
        input_artifact_ids=(
            "shot-1",
            *(item.asset_id for item in image_bindings),
            *(item.asset_id for item in media_bindings),
        ),
        output_asset_id="native-v2-video",
    )


def test_explicitly_blocked_profile_fails_before_runtime_or_transport_effect(
    tmp_path: Path,
) -> None:
    canonical = _load("Ref2VA")
    values = canonical.model_dump(mode="python", exclude={"profile_content_hash"})
    values.update(
        availability="blocked",
        availability_blockers=("test-blocker",),
    )
    profile = type(canonical).create(**values)
    transport = _NoEffectTransport()
    comfy_root = tmp_path / "ComfyUI"
    input_root = tmp_path / "inputs"
    comfy_root.mkdir()
    input_root.mkdir()
    provider = ComfyUIT8NativeTurboVideoProvider(
        profile,
        artifact_root=REPO_ROOT,
        comfy_root=comfy_root,
        input_root=input_root,
        asset_resolver=lambda *_: input_root / "unused",
        runtime_inspector=lambda: T8NativeTurboRuntimeInspection(
            comfyui_commit=profile.comfyui_commit,
            t8_commit=profile.t8_commit,
            t8_version=profile.t8_version,
            videohelpersuite_commit=profile.videohelpersuite_commit,
            sageattention_version=profile.sageattention_version,
            launch_capabilities=("sage_attention",),
        ),
        transport=transport,
        clock=lambda: datetime(2026, 8, 22, tzinfo=UTC),
    )
    resolved = _resolved(
        profile,
        _request(
            profile,
            image_bindings=(_image("reference", "blocked-reference", "a"),),
        ),
    )

    with pytest.raises(AiVideoError, match="unavailable for production routing"):
        provider.capabilities()

    with pytest.raises(AiVideoError, match="not live-ready"):
        provider.preflight(resolved)

    assert transport.object_info_calls == 0
    assert transport.uploads == []
    assert transport.posts == []


def _image(role: str, asset_id: str, token: str) -> VideoImageReferenceBinding:
    return VideoImageReferenceBinding(
        role=role,
        asset_id=asset_id,
        asset_sha256=token * 64,
        mime_type="image/png",
        width=1344,
        height=768,
        size_bytes=64,
    )


def _resolved(profile, request: VideoGenerationRequest):
    return ResolvedVideoGenerationRequest.create(
        request=request,
        capability=t8_native_turbo_capabilities(profile).variants[0],
        effective_output=request.output_requirement,
        effective_seed=7,
        effective_negative_prompt_text="",
    )


def _render(profile, request, *, images=(), videos=(), audios=()):
    binding = load_t8_native_turbo_binding(
        (REPO_ROOT / profile.binding_path).read_bytes()
    )
    return render_t8_native_turbo_workflow(
        template=load_workflow_template(REPO_ROOT / profile.workflow_path),
        binding=binding,
        request=_resolved(profile, request),
        profile=profile,
        uploaded_images=images,
        uploaded_videos=videos,
        uploaded_audios=audios,
    )


def test_i2va_and_fl2va_bind_exact_first_and_final_frame_nodes() -> None:
    i2 = _load("I2VA")
    first = _image("first_frame", "first", "a")
    i2_workflow = _render(i2, _request(i2, image_bindings=(first,)), images=("first.png",))
    assert i2_workflow["13"]["inputs"]["image"] == "first.png"
    assert i2_workflow["6"]["inputs"]["first_frame"] == ["13", 0]

    fl2 = _load("FL2VA")
    last = _image("last_frame", "last", "b")
    fl2_workflow = _render(
        fl2,
        _request(fl2, image_bindings=(first, last)),
        images=("first.png", "last.png"),
    )
    assert fl2_workflow["13"]["inputs"]["image"] == "first.png"
    assert fl2_workflow["14"]["inputs"]["image"] == "last.png"
    assert fl2_workflow["6"]["inputs"]["last_frame"] == ["14", 0]


def test_ref2va_maps_canonical_ordinals_without_video_audio_linkage() -> None:
    profile = _load("Ref2VA")
    image = _image("reference", "reference-image", "c")
    video = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="reference-video",
        asset_sha256="d" * 64,
        mime_type="video/mp4",
        duration_millis=4000,
        size_bytes=1024,
        width=1344,
        height=768,
        fps=24,
    )
    audio = VideoMediaReferenceBinding(
        kind="audio",
        role="reference_audio",
        asset_id="reference-audio",
        asset_sha256="e" * 64,
        mime_type="audio/wav",
        duration_millis=4000,
        size_bytes=512,
    )
    workflow = _render(
        profile,
        _request(
            profile,
            image_bindings=(image,),
            media_bindings=(video, audio),
        ),
        images=("reference.png",),
        videos=("reference.mp4",),
        audios=("reference.wav",),
    )
    conditioning = workflow["6"]["inputs"]

    assert workflow["13"] == {
        "class_type": "LoadImage",
        "inputs": {"image": "reference.png"},
    }
    assert workflow["14"]["class_type"] == "VHS_LoadVideo"
    assert workflow["14"]["inputs"]["force_rate"] == 24
    assert workflow["15"] == {
        "class_type": "VHS_LoadAudioUpload",
        "inputs": {"audio": "reference.wav"},
    }
    assert conditioning["ref_images.ref_image_0"] == ["13", 0]
    assert conditioning["ref_videos.ref_video_0"] == ["14", 0]
    assert conditioning["ref_audios.ref_audio_0"] == ["15", 0]
    assert not any(
        key == "ref_video_audios" or key.startswith("ref_video_audios.")
        for key in conditioning
    )


class _Permit:
    def __init__(self, intent: str, request: str) -> None:
        self.intent = intent
        self.request = request
        self.consumed = False

    def _consume_local_video_submit_permit(
        self, *, intent_fingerprint: str, request_fingerprint: str
    ) -> bool:
        valid = (intent_fingerprint, request_fingerprint) == (
            self.intent,
            self.request,
        )
        self.consumed = valid
        return valid


def _synthetic_lora_payload(seal: T8NativeTurboLoraSeal) -> bytes:
    header = {
        "__metadata__": {
            "application": "W_eff = W + lora_B @ lora_A",
            "base_model": "MiniMax-H3",
            "comfyui_key_prefix": "diffusion_model.",
            "comfyui_loader": "Load LoRA (Bypass, Model Only) (for debugging)",
            "compatible_base": "MiniMax-H3 non-pruned bf16 or int8_convrot",
            "conversion_source_file": seal.source_filename,
            "conversion_source_sha256": seal.source_sha256,
            "conversion_tool": "convert_minimax_h3_lora_for_comfyui.py",
            "dtype": "bfloat16",
            "format": "pt",
            "incompatible_base": (
                "MiniMax-H3 pruned_* (AdaLN input is 8, LoRA input is 2688)"
            ),
            "sampler_steps": "4",
        },
        **{
            key: {"dtype": "BF16", "shape": list(shape), "data_offsets": [0, 0]}
            for key, shape in _expected_lora_tensor_shapes().items()
        },
    }
    encoded = json.dumps(header, separators=(",", ":")).encode()
    return len(encoded).to_bytes(8, "little") + encoded


def test_lora_header_audit_rejects_conversion_metadata_drift(tmp_path: Path) -> None:
    seal = _load("T2VA").lora
    payload = _synthetic_lora_payload(seal)
    path = tmp_path / seal.filename
    path.write_bytes(payload)
    validate_t8_native_turbo_lora(path, seal)
    header_size = int.from_bytes(payload[:8], "little")
    header = json.loads(payload[8 : 8 + header_size])
    header["__metadata__"]["conversion_source_sha256"] = "0" * 64
    encoded = json.dumps(header, separators=(",", ":")).encode()
    path.write_bytes(len(encoded).to_bytes(8, "little") + encoded)

    with pytest.raises(AiVideoError, match="conversion metadata changed"):
        validate_t8_native_turbo_lora(path, seal)


@pytest.mark.parametrize("drift", ("inventory", "dtype", "shape"))
def test_lora_header_audit_rejects_tensor_schema_drift(
    tmp_path: Path, drift: str
) -> None:
    seal = _load("T2VA").lora
    payload = _synthetic_lora_payload(seal)
    header_size = int.from_bytes(payload[:8], "little")
    header = json.loads(payload[8 : 8 + header_size])
    key = next(key for key in header if key != "__metadata__")
    if drift == "inventory":
        del header[key]
        message = "tensor inventory changed"
    elif drift == "dtype":
        header[key]["dtype"] = "F16"
        message = "tensor schema changed"
    else:
        header[key]["shape"] = [1]
        message = "tensor schema changed"
    encoded = json.dumps(header, separators=(",", ":")).encode()
    path = tmp_path / seal.filename
    path.write_bytes(len(encoded).to_bytes(8, "little") + encoded)

    with pytest.raises(AiVideoError, match=message):
        validate_t8_native_turbo_lora(path, seal)


@pytest.mark.parametrize(
    "payload",
    (
        (1024 * 1024 + 1).to_bytes(8, "little"),
        (32).to_bytes(8, "little") + b'{"truncated":true',
    ),
)
def test_lora_header_audit_rejects_unbounded_or_truncated_header(
    tmp_path: Path, payload: bytes
) -> None:
    seal = _load("T2VA").lora
    path = tmp_path / seal.filename
    path.write_bytes(payload)

    with pytest.raises(AiVideoError, match="LoRA header is invalid"):
        validate_t8_native_turbo_lora(path, seal)


def _live_ready_sandbox(tmp_path: Path, task: str):
    canonical = _load(task)
    comfy_root = tmp_path / "ComfyUI"
    input_root = tmp_path / "inputs"
    comfy_root.mkdir()
    input_root.mkdir()
    source_components = canonical.components or _load("T2VA").components
    components = []
    dirs = {
        "diffusion": "models/diffusion_models",
        "text_encoder": "models/text_encoders",
        "video_vae": "models/vae",
        "audio_vae": "models/vae",
    }
    for index, source in enumerate(source_components):
        filename = source.filename
        if task == "Ref2VA" and source.role == "diffusion":
            filename = "minimax_h3_ref2va_int8_convrot.safetensors"
        payload = f"native-v2-component-{task}-{index}".encode()
        target = comfy_root / dirs[source.role] / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        components.append(
            T8NativeTurboComponent(
                role=source.role,
                filename=filename,
                size_bytes=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                precision=source.precision,
            )
        )
    lora_payload = _synthetic_lora_payload(canonical.lora)
    lora_path = comfy_root / "models/loras" / canonical.lora.filename
    lora_path.parent.mkdir(parents=True, exist_ok=True)
    lora_path.write_bytes(lora_payload)
    lora = T8NativeTurboLoraSeal(
        **{
            **canonical.lora.model_dump(mode="python"),
            "size_bytes": len(lora_payload),
            "sha256": hashlib.sha256(lora_payload).hexdigest(),
            "conversion_verified": True,
        }
    )
    workflow = load_workflow_template(REPO_ROOT / canonical.workflow_path)
    schemas = {}
    for node in workflow.values():
        class_type = node["class_type"]
        names = tuple(node["inputs"])
        schemas[class_type] = {
            "input": {
                "required": {name: ["ANY", {}] for name in names},
                "optional": {},
            },
            "input_order": {"required": list(names), "optional": []},
            "output_name": ["OUT"],
        }
    for class_type, names in {
        "LoadImage": ("image",),
        "VHS_LoadVideo": (
            "video",
            "force_rate",
            "custom_width",
            "custom_height",
            "frame_load_cap",
            "skip_first_frames",
            "select_every_nth",
        ),
        "VHS_LoadAudioUpload": ("audio",),
    }.items():
        schemas.setdefault(
            class_type,
            {
                "input": {
                    "required": {name: ["ANY", {}] for name in names},
                    "optional": {},
                },
                "input_order": {"required": list(names), "optional": []},
                "output_name": ["OUT"],
            },
        )
    values = canonical.model_dump(mode="python", exclude={"profile_content_hash"})
    values.update(
        availability="live-ready",
        availability_blockers=(),
        components=tuple(components),
        lora=lora,
        node_schema_seals=node_schema_seals(schemas, canonical.required_nodes),
    )
    profile = type(canonical).create(**values)
    return profile, comfy_root, input_root, schemas


def test_i2va_preflight_then_consumes_permit_before_upload_and_prompt(
    tmp_path: Path,
) -> None:
    profile, comfy_root, input_root, schemas = _live_ready_sandbox(
        tmp_path, "I2VA"
    )
    payload = b"\x89PNG\r\n\x1a\n" + b"sealed-frame"
    frame = input_root / "first.png"
    frame.write_bytes(payload)
    image = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="first-frame",
        asset_sha256=hashlib.sha256(payload).hexdigest(),
        mime_type="image/png",
        width=1344,
        height=768,
        size_bytes=len(payload),
    )
    transport = _NoEffectTransport()
    transport.get_object_info = lambda: schemas
    provider = ComfyUIT8NativeTurboVideoProvider(
        profile,
        artifact_root=REPO_ROOT,
        comfy_root=comfy_root,
        input_root=input_root,
        asset_resolver=lambda *_: frame,
        runtime_inspector=lambda: T8NativeTurboRuntimeInspection(
            comfyui_commit=profile.comfyui_commit,
            t8_commit=profile.t8_commit,
            t8_version=profile.t8_version,
            videohelpersuite_commit=profile.videohelpersuite_commit,
            sageattention_version=profile.sageattention_version,
            launch_capabilities=("sage_attention",),
        ),
        transport=transport,
        clock=lambda: datetime(2026, 8, 22, tzinfo=UTC),
    )
    resolved = provider.resolve(_request(profile, image_bindings=(image,)))
    provider.preflight(resolved)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="native-v2-attempt",
        request=resolved,
        preview=preview,
        recorded_at=datetime(2026, 8, 22, tzinfo=UTC),
    )
    permit = _Permit(intent.intent_fingerprint, resolved.resolved_generation_hash)

    lora_path = comfy_root / "models/loras" / profile.lora.filename
    original_lora = lora_path.read_bytes()
    lora_path.write_bytes(b"drift-after-intent")
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit_local(resolved, preview, intent, permit)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert permit.consumed is False
    assert transport.uploads == []
    assert transport.posts == []
    lora_path.write_bytes(original_lora)

    result = provider.submit_local(resolved, preview, intent, permit)

    assert permit.consumed is True
    assert transport.uploads == [frame]
    assert len(transport.posts) == 1
    assert transport.posts[0]["13"]["inputs"]["image"] == "first.png"
    assert result.provider_request_id == "native-v2-prompt"
    submission = LocalVideoSubmission.from_submit_result(
        resolved=resolved, result=result
    )
    observation = provider.get_local_status(resolved, submission)
    assert observation.provider_file_id is not None
    assert observation.provider_file_id.endswith("native-v2_00001-audio.mp4:output")
    sink = BytesIO()
    receipt = provider.fetch_local(
        resolved, submission, observation, sink
    )
    assert receipt.artifact_sha256 == hashlib.sha256(MP4.read_bytes()).hexdigest()
    assert sink.getvalue() == MP4.read_bytes()


def test_ref2va_resolution_rejects_non_24_fps_reference_video(
    tmp_path: Path,
) -> None:
    profile, _, _, _ = _live_ready_sandbox(tmp_path, "Ref2VA")
    provider = object.__new__(ComfyUIT8NativeTurboVideoProvider)
    provider.profile = profile
    video = VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="reference-video-30fps",
        asset_sha256="f" * 64,
        mime_type="video/mp4",
        duration_millis=4000,
        size_bytes=1024,
        width=1344,
        height=768,
        fps=30,
    )

    with pytest.raises(AiVideoError, match="outside the sealed V2 profile"):
        provider.resolve(_request(profile, media_bindings=(video,)))
