from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from ai_video.comfy_client import ComfyClient, JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import (
    ComfyLocalImageProvider,
    LocalImageExecutionProfile,
    collect_save_image_output,
    load_local_image_binding,
    load_local_image_execution_profile,
    load_local_image_workflow,
    render_image_workflow,
    validate_loopback_endpoint,
    validate_profile_request_match,
)
from ai_video.production.image import (
    ContinuityTerminalImageReferenceBinding,
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageProviderParameters,
    ImageReferenceBinding,
)
from ai_video.production.video import ContinuityConstraintSet, TerminalFrameEvidence
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures/p7_1"
QWEN_PROFILE = FIXTURES / "qwen_profile.json"
FLUX_PROFILE = FIXTURES / "flux_profile.json"
REAL_QWEN_PROFILE = ROOT / "workflows/profiles/p7_1_qwen_image_edit_2511.json"
REAL_FLUX_PROFILE = ROOT / "workflows/profiles/p7_1_flux2_klein_4b.json"
REAL_HARD_CUT_PROFILE = ROOT / "workflows/profiles/p7_1_qwen_hard_cut_keyframe.json"
PNG = b"\x89PNG\r\n\x1a\nfixture-png"
HASHES = tuple(f"{index}" * 64 for index in range(4))


def _profile_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("profile_content_hash", None)
    return payload


def _runtime_profile(
    root: Path, *, source: Path = REAL_QWEN_PROFILE
) -> LocalImageExecutionProfile:
    payload = _profile_payload(source)
    workflow_source = ROOT / str(payload["workflow_path"])
    binding_source = ROOT / str(payload["binding_path"])
    workflow = root / "workflow.json"
    binding = root / "binding.yaml"
    workflow.write_bytes(workflow_source.read_bytes())
    binding.write_bytes(binding_source.read_bytes())
    components = []
    for item in payload["components"]:
        component = dict(item)
        directory = {
            "diffusion": "diffusion_models",
            "text_encoder": "text_encoders",
            "vae": "vae",
            "lora": "loras",
        }[component["role"]]
        component_path = root / "comfy/models" / directory / component["filename"]
        component_path.parent.mkdir(parents=True, exist_ok=True)
        component_bytes = f"fixture-{component['role']}".encode()
        component_path.write_bytes(component_bytes)
        component["size_bytes"] = len(component_bytes)
        component["sha256"] = hashlib.sha256(component_bytes).hexdigest()
        components.append(component)
    payload.update(
        {
            "workflow_path": Path("workflow.json"),
            "workflow_sha256": hashlib.sha256(workflow.read_bytes()).hexdigest(),
            "binding_path": Path("binding.yaml"),
            "binding_sha256": hashlib.sha256(binding.read_bytes()).hexdigest(),
            "components": components,
        }
    )
    return LocalImageExecutionProfile.create(**payload)


def _request(profile: LocalImageExecutionProfile, root: Path) -> tuple[ImageGenerationRequest, dict[str, Path]]:
    refs = root / "refs"
    refs.mkdir(exist_ok=True)
    paths = {
        "character-ref": refs / "character.png",
        "scene-ref": refs / "scene.png",
    }
    paths["character-ref"].write_bytes(b"character-reference")
    paths["scene-ref"].write_bytes(b"scene-reference")
    request = ImageGenerationRequest.create(
        attempt_id="p7-1-attempt",
        provider_kind="comfyui_local",
        model_id=profile.profile_id,
        target_shot_id="shot-1",
        target_asset_role="visual",
        prompt_text="A hero enters the archive",
        negative_prompt_text="blur",
        parameters=ImageProviderParameters(
            seed=7,
            width=512,
            height=512,
            output_format="png",
            generation_revision=1,
        ),
        references=(
            ImageReferenceBinding(
                role="character",
                creative_artifact_id="character-hero",
                creative_revision=1,
                creative_content_hash=HASHES[0],
                asset_id="character-ref",
                asset_sha256=hashlib.sha256(paths["character-ref"].read_bytes()).hexdigest(),
            ),
            ImageReferenceBinding(
                role="scene",
                creative_artifact_id="scene-archive",
                creative_revision=1,
                creative_content_hash=HASHES[1],
                asset_id="scene-ref",
                asset_sha256=hashlib.sha256(paths["scene-ref"].read_bytes()).hexdigest(),
            ),
        ),
        base_project=ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{HASHES[0]}.yaml"),
            revision=1,
            content_hash=HASHES[0],
            file_sha256=HASHES[1],
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{HASHES[1]}.json"),
            revision_id=HASHES[1],
            content_hash=HASHES[1],
            file_sha256=HASHES[2],
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            revision_id=HASHES[2],
            content_hash=HASHES[2],
            path=Path(f"state/dependency_graph.{HASHES[2]}.json"),
            file_sha256=HASHES[3],
        ),
    )
    return request, paths


def _hard_cut_request(
    profile: LocalImageExecutionProfile, root: Path
) -> tuple[ImageGenerationRequest, dict[str, Path]]:
    ordinary, paths = _request(profile, root)
    terminal_path = paths.pop("scene-ref")
    terminal = TerminalFrameEvidence.create(
        source_shot_id="shot-0",
        source_shot_revision=1,
        source_shot_content_hash=HASHES[0],
        source_video_asset_id="video-shot-0",
        source_video_sha256=HASHES[1],
        source_generation_id="generation-shot-0",
        source_request_input_hash=HASHES[2],
        source_resolved_generation_hash=HASHES[3],
        source_provenance_receipt_id="provenance-shot-0",
        extraction_receipt_id=HASHES[3],
        source_registry=ordinary.base_registry,
        source_container_name="mp4",
        source_codec_name="h264",
        source_width=512,
        source_height=512,
        source_fps_numerator=24,
        source_fps_denominator=1,
        source_duration_milliseconds=5167,
        source_frame_count=124,
        frame_index=123,
        timestamp_numerator=123,
        timestamp_denominator=24,
        selection_rule="generated_candidate_terminal",
        extraction_contract_version="terminal-frame-v1",
        extractor_name="ffmpeg",
        extractor_version="7.1",
        extracted_asset_id="terminal-ref",
        extracted_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
        extracted_mime_type="image/png",
        extracted_size_bytes=len(terminal_path.read_bytes()),
        extracted_width=512,
        extracted_height=512,
        extracted_color_space="unmeasured",
    )
    constraints = ContinuityConstraintSet.create(
        scene_identity={
            "artifact_id": "scene-archive",
            "revision": 1,
            "content_hash": HASHES[1],
        },
        character_identities=(
            {
                "artifact_id": "character-hero",
                "revision": 1,
                "content_hash": HASHES[0],
            },
        ),
        camera_axis="same-side",
        framing="medium-hard-cut",
        lighting="window-left",
        color="neutral-warm",
        motion_direction="left-to-right",
        exit_state="hand-on-chair",
        entrance_state="hand-on-chair-continuing",
    )
    terminal_binding = ContinuityTerminalImageReferenceBinding.create(
        role="continuity_terminal",
        terminal_frame=terminal,
        asset_id=terminal.extracted_asset_id,
        asset_sha256=terminal.extracted_sha256,
        target_shot_id=ordinary.target_shot_id,
        target_shot_revision=1,
        target_shot_content_hash=HASHES[0],
        constraints=constraints,
    )
    values = ordinary.model_dump(
        mode="json",
        exclude={"request_id", "request_fingerprint", "output_asset_id"},
    )
    values["references"] = (ordinary.references[0], terminal_binding)
    request = ImageGenerationRequest.create(**values)
    paths[terminal.extracted_asset_id] = terminal_path
    return request, paths


def _authorization(request: ImageGenerationRequest) -> ImageGenerationAuthorization:
    preview = ImageGenerationPreview.create(request=request, reference_total_bytes=1)
    return ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="fixture-only",
        policy_receipt_id="policy-p7-1",
    )


class _Permit:
    def __init__(self) -> None:
        self.calls = 0

    def _consume_image_generation_permit(self, *, request_fingerprint: str) -> bool:
        self.calls += 1
        return self.calls == 1 and len(request_fingerprint) == 64


class _FakeTransport:
    def __init__(self, *, history: dict[str, object] | None = None) -> None:
        self.uploaded: list[str] = []
        self.submitted: list[dict[str, object]] = []
        self.fetches = 0
        self.history = history or {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "result.png", "subfolder": "", "type": "output"}
                    ]
                }
            }
        }

    def get_object_info(self) -> dict[str, object]:
        names = {
            "CFGNorm",
            "CLIPLoader",
            "ComfySwitchNode",
            "FluxKontextMultiReferenceLatentMethod",
            "ImageScale",
            "KSampler",
            "LoadImage",
            "LoraLoaderModelOnly",
            "ModelSamplingAuraFlow",
            "PrimitiveBoolean",
            "PrimitiveFloat",
            "PrimitiveInt",
            "SaveImage",
            "TextEncodeQwenImageEditPlus",
            "UNETLoader",
            "VAEDecode",
            "VAEEncode",
            "VAELoader",
        }
        return {name: {} for name in names}

    def upload_image(self, path: str | Path) -> str:
        name = Path(path).name
        self.uploaded.append(name)
        return name

    def submit_prompt(self, workflow: dict[str, object]) -> str:
        self.submitted.append(workflow)
        return "prompt-p7-1"

    def poll_job(self, prompt_id: str, **_: object) -> JobResult:
        return JobResult(JobStatus.COMPLETED, prompt_id, history=self.history)

    def fetch_artifact_bytes(self, **_: object) -> bytes:
        self.fetches += 1
        return PNG


def _provider(
    root: Path,
    profile: LocalImageExecutionProfile,
    paths: dict[str, Path],
    transport: object,
) -> ComfyLocalImageProvider:
    return ComfyLocalImageProvider(
        profile,
        artifact_root=root,
        comfy_root=root / "comfy",
        reference_resolver=lambda reference: paths[reference.asset_id],
        transport=transport,
        commit_resolver=lambda: profile.comfyui_commit,
    )


def test_realistic_fixture_profiles_are_sealed_and_reopen_exact_files() -> None:
    qwen = load_local_image_execution_profile(QWEN_PROFILE, artifact_root=ROOT)
    flux = load_local_image_execution_profile(FLUX_PROFILE, artifact_root=ROOT)
    assert qwen.profile_id == "local-image-profile:sha256:" + qwen.profile_content_hash
    assert flux.model_repository_id == "black-forest-labs/FLUX.2-klein-4B"


def test_additive_hard_cut_profile_accepts_character_and_terminal_only(
    tmp_path: Path,
) -> None:
    profile = load_local_image_execution_profile(
        REAL_HARD_CUT_PROFILE, artifact_root=ROOT
    )
    request, _ = _hard_cut_request(profile, tmp_path)

    validate_profile_request_match(profile, request)
    assert profile.supported_reference_roles == (
        "character",
        "continuity_terminal",
    )
    assert profile.max_references == 2


def test_ordinary_profile_denies_hard_cut_before_upload_or_submit(
    tmp_path: Path,
) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _hard_cut_request(profile, tmp_path)
    transport = _FakeTransport()
    provider = _provider(tmp_path, profile, paths, transport)

    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(request)

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert transport.uploaded == []
    assert transport.submitted == []


@pytest.mark.parametrize(
    ("profile_path", "model_node", "model_filename", "output_node"),
    (
        (
            REAL_QWEN_PROFILE,
            "170:161",
            "qwen_image_edit_2511_bf16.safetensors",
            "9",
        ),
        (
            REAL_FLUX_PROFILE,
            "92:107",
            "flux-2-klein-4b.safetensors",
            "94",
        ),
    ),
)
def test_real_profiles_reopen_reviewed_official_derivatives_and_bind_two_refs(
    tmp_path: Path,
    profile_path: Path,
    model_node: str,
    model_filename: str,
    output_node: str,
) -> None:
    profile = load_local_image_execution_profile(profile_path, artifact_root=ROOT)
    request, _ = _request(profile, tmp_path)
    workflow = load_local_image_workflow(ROOT / profile.workflow_path)
    binding = load_local_image_binding((ROOT / profile.binding_path).read_bytes())

    rendered = render_image_workflow(
        template=workflow,
        binding=binding,
        request=request,
        reference_names=("character.png", "scene.png"),
        output_prefix="p7-1-static",
    )

    assert rendered[model_node]["inputs"]["unet_name"] == model_filename
    assert rendered[output_node]["class_type"] == "SaveImage"
    assert len(binding.reference_images) == 2
    assert request.prompt_text in json.dumps(rendered, sort_keys=True)
    assert request.negative_prompt_text in json.dumps(rendered, sort_keys=True)
    assert request.parameters.seed in {
        rendered.get("170:169", {}).get("inputs", {}).get("seed"),
        rendered.get("92:106", {}).get("inputs", {}).get("noise_seed"),
    }
    size_node = rendered["170:160" if profile.lane_id.startswith("qwen") else "92:111"]
    assert size_node["inputs"]["width"] == request.parameters.width
    assert size_node["inputs"]["height"] == request.parameters.height
    if profile.lane_id.startswith("qwen"):
        assert rendered["170:169"]["inputs"]["sampler_name"] == profile.sampler
        assert rendered["170:169"]["inputs"]["scheduler"] == profile.scheduler
        assert rendered["170:169"]["inputs"]["steps"] == profile.steps
        assert rendered["170:169"]["inputs"]["cfg"] == profile.guidance
    else:
        assert rendered["92:101"]["inputs"]["sampler_name"] == profile.sampler
        assert rendered["92:102"]["inputs"]["steps"] == profile.steps
        assert rendered["92:103"]["inputs"]["cfg"] == profile.guidance
    assert profile.optional_lora_enabled is False


def test_flux_workflow_uses_current_total_pixel_scale_input_contract() -> None:
    profile = load_local_image_execution_profile(REAL_FLUX_PROFILE, artifact_root=ROOT)
    workflow = load_local_image_workflow(ROOT / profile.workflow_path)

    inputs = workflow["92:85"]["inputs"]

    assert inputs["resolution_steps"] == 1
    assert "resolution" not in inputs


def test_preflight_rejects_missing_live_required_node_input(tmp_path: Path) -> None:
    profile = _runtime_profile(tmp_path, source=REAL_FLUX_PROFILE)
    workflow_path = tmp_path / profile.workflow_path
    stale_workflow = load_local_image_workflow(workflow_path)
    stale_workflow["92:85"]["inputs"].pop("resolution_steps")
    stale_workflow["92:85"]["inputs"]["resolution"] = 1
    workflow_path.write_text(
        json.dumps(stale_workflow, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    profile_values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    profile_values["workflow_sha256"] = hashlib.sha256(
        workflow_path.read_bytes()
    ).hexdigest()
    profile = LocalImageExecutionProfile.create(**profile_values)
    request, paths = _request(profile, tmp_path)
    transport = _FakeTransport()
    workflow = load_local_image_workflow(workflow_path)
    object_info = {
        node["class_type"]: {}
        for node in workflow.values()
        if isinstance(node, dict) and isinstance(node.get("class_type"), str)
    }
    object_info["ImageScaleToTotalPixels"] = {
        "input": {
            "required": {
                "resolution_steps": ["INT", {"default": 1, "min": 1, "max": 256}]
            }
        }
    }
    transport.get_object_info = lambda: object_info  # type: ignore[method-assign]
    provider = _provider(tmp_path, profile, paths, transport)

    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(request)

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert "92:85.resolution_steps" in (exc_info.value.technical_detail or "")
    assert transport.uploaded == []
    assert transport.submitted == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model_repository_revision", "main"),
        ("comfyui_commit", "HEAD"),
    ],
)
def test_profile_rejects_mutable_revisions(field: str, value: str) -> None:
    payload = _profile_payload(QWEN_PROFILE)
    payload[field] = value
    with pytest.raises(ValueError):
        LocalImageExecutionProfile.create(**payload)


def test_profile_rejects_missing_component_integrity_and_license() -> None:
    for mutation in ("size", "sha", "license"):
        payload = _profile_payload(QWEN_PROFILE)
        if mutation == "size":
            payload["components"][0]["size_bytes"] = 0  # type: ignore[index]
        elif mutation == "sha":
            payload["components"][0]["sha256"] = ""  # type: ignore[index]
        else:
            payload["license_source_url"] = ""
        with pytest.raises(ValueError):
            LocalImageExecutionProfile.create(**payload)


def test_profile_rejects_tampered_hash_and_disallowed_lane_variants() -> None:
    profile = load_local_image_execution_profile(QWEN_PROFILE, artifact_root=ROOT)
    with pytest.raises(ValueError):
        type(profile).model_validate(
            {**profile.model_dump(mode="python"), "sampler": "changed"}
        )
    qwen = _profile_payload(QWEN_PROFILE)
    qwen["optional_lora_enabled"] = True
    with pytest.raises(ValueError):
        LocalImageExecutionProfile.create(**qwen)
    flux = _profile_payload(FLUX_PROFILE)
    flux["model_repository_id"] = "black-forest-labs/FLUX.2-klein-base-4B"
    with pytest.raises(ValueError):
        LocalImageExecutionProfile.create(**flux)
    flux = _profile_payload(FLUX_PROFILE)
    flux["components"][0]["quantization"] = "gguf"  # type: ignore[index]
    with pytest.raises(ValueError):
        LocalImageExecutionProfile.create(**flux)


@pytest.mark.parametrize(
    "endpoint",
    ["http://127.0.0.1:8188", "http://localhost:8188", "http://[::1]:8188"],
)
def test_loopback_endpoint_accepts_only_literal_local_origins(endpoint: str) -> None:
    assert validate_loopback_endpoint(endpoint) == endpoint


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://127.0.0.1:8188",
        "http://127.0.0.2:8188",
        "http://0x7f000001:8188",
        "http://127.0.0.1.example:8188",
        "http://127.0.0.1:8188/path",
        "http://127.0.0.1",
    ],
)
def test_loopback_endpoint_rejects_noncanonical_or_nonlocal(endpoint: str) -> None:
    with pytest.raises(AiVideoError) as exc:
        validate_loopback_endpoint(endpoint)
    assert exc.value.code is ErrorCode.IMAGE_REQUEST_INVALID


def test_profile_request_match_is_exact(tmp_path: Path) -> None:
    profile = _runtime_profile(tmp_path)
    request, _ = _request(profile, tmp_path)
    validate_profile_request_match(profile, request)
    with pytest.raises(AiVideoError):
        validate_profile_request_match(
            profile,
            request.model_copy(update={"model_id": "local-image-profile:sha256:" + "f" * 64}),
        )


def test_fake_provider_consumes_once_uploads_in_order_and_returns_one_png(
    tmp_path: Path,
) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    transport = _FakeTransport()
    permit = _Permit()
    provider = _provider(tmp_path, profile, paths, transport)
    provider.preflight(request)
    result = provider.generate(
        request, _authorization(request), permit
    )
    assert permit.calls == 1
    assert transport.uploaded == ["character.png", "scene.png"]
    assert len(transport.submitted) == 1
    assert transport.fetches == 1
    assert result.image_bytes == PNG
    assert result.provider_request_id == "prompt-p7-1"


def test_hard_cut_provider_uploads_exact_terminal_as_second_reference(
    tmp_path: Path,
) -> None:
    profile = _runtime_profile(tmp_path, source=REAL_HARD_CUT_PROFILE)
    request, paths = _hard_cut_request(profile, tmp_path)
    terminal = request.references[1]
    transport = _FakeTransport()
    provider = _provider(tmp_path, profile, paths, transport)

    provider.preflight(request)
    provider.generate(request, _authorization(request), _Permit())

    assert transport.uploaded == ["character.png", "scene.png"]
    assert hashlib.sha256(paths[terminal.asset_id].read_bytes()).hexdigest() == (
        terminal.asset_sha256
    )
    assert len(transport.submitted) == 1


def test_fake_provider_is_network_free(tmp_path: Path) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    with (
        patch.object(socket.socket, "connect", side_effect=AssertionError("network")) as connect,
        patch.object(socket, "create_connection", side_effect=AssertionError("network")) as create,
    ):
        provider = _provider(tmp_path, profile, paths, _FakeTransport())
        provider.preflight(request)
        provider.generate(
            request, _authorization(request), _Permit()
        )
    connect.assert_not_called()
    create.assert_not_called()


@pytest.mark.parametrize("failure", ["component", "commit", "node"])
def test_preflight_fails_before_upload_or_prompt(
    tmp_path: Path, failure: str
) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    transport = _FakeTransport()
    commit = profile.comfyui_commit
    if failure == "component":
        component = profile.components[0]
        path = tmp_path / "comfy/models/diffusion_models" / component.filename
        path.write_bytes(b"tampered")
    elif failure == "commit":
        commit = "f" * 40
    else:
        transport.get_object_info = lambda: {}  # type: ignore[method-assign]
    provider = ComfyLocalImageProvider(
        profile,
        artifact_root=tmp_path,
        comfy_root=tmp_path / "comfy",
        reference_resolver=lambda reference: paths[reference.asset_id],
        transport=transport,
        commit_resolver=lambda: commit,
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.preflight(request)

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert transport.uploaded == []
    assert transport.submitted == []


def test_generate_rejects_bypass_of_mandatory_preflight(tmp_path: Path) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    transport = _FakeTransport()

    with pytest.raises(AiVideoError) as exc_info:
        _provider(tmp_path, profile, paths, transport).generate(
            request, _authorization(request), _Permit()
        )

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert transport.submitted == []


def test_resealed_profile_cannot_redirect_request_semantics(tmp_path: Path) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    binding = tmp_path / "binding.yaml"
    binding.write_text(
        binding.read_text(encoding="utf-8").replace(
            'width: ["170:160", "inputs", "width"]',
            'width: ["170:160", "inputs", "height"]',
        ),
        encoding="utf-8",
    )
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values["binding_sha256"] = hashlib.sha256(binding.read_bytes()).hexdigest()
    redirected = LocalImageExecutionProfile.create(**values)

    with pytest.raises(AiVideoError) as exc_info:
        _provider(tmp_path, redirected, paths, _FakeTransport())

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert request.provider_kind == "comfyui_local"


def test_resealed_profile_cannot_bind_installed_component_unused_by_workflow(
    tmp_path: Path,
) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    payload = b"installed-but-not-bound"
    filename = "flux-2-klein-4b.safetensors"
    installed = tmp_path / "comfy/models/diffusion_models" / filename
    installed.write_bytes(payload)
    components = (
        profile.components[0].model_copy(
            update={
                "filename": filename,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ),
        *profile.components[1:],
    )
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values["components"] = components
    mismatched = LocalImageExecutionProfile.create(**values)

    with pytest.raises(AiVideoError) as exc_info:
        _provider(tmp_path, mismatched, paths, _FakeTransport())

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert request.provider_kind == "comfyui_local"


def test_resealed_profile_cannot_add_loader_and_redirect_active_model(
    tmp_path: Path,
) -> None:
    profile = _runtime_profile(tmp_path)
    workflow_path = tmp_path / "workflow.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["undeclared-loader"] = {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "undeclared.safetensors"},
    }
    workflow["170:169"]["inputs"]["model"] = ["undeclared-loader", 0]
    workflow_path.write_text(
        json.dumps(workflow, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values["workflow_sha256"] = hashlib.sha256(workflow_path.read_bytes()).hexdigest()
    redirected = LocalImageExecutionProfile.create(**values)

    with pytest.raises(AiVideoError) as exc_info:
        _provider(tmp_path, redirected, {}, _FakeTransport())

    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID


def test_workflow_loader_handles_api_and_ui_formats(tmp_path: Path) -> None:
    assert "9" in load_local_image_workflow(FIXTURES / "qwen_workflow_api.json")
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "inputs": [{"name": "image", "widget": {"name": "image"}, "link": None}],
                "widgets_values": ["reference.png"],
            }
        ],
        "links": [],
    }
    path = tmp_path / "ui.json"
    path.write_text(json.dumps(ui), encoding="utf-8")
    assert load_local_image_workflow(path)["1"]["inputs"]["image"] == "reference.png"


def test_binding_mutates_only_declared_paths_and_missing_path_fails(tmp_path: Path) -> None:
    profile = _runtime_profile(tmp_path, source=QWEN_PROFILE)
    request, _ = _request(profile, tmp_path)
    template = load_local_image_workflow(tmp_path / "workflow.json")
    binding = load_local_image_binding((tmp_path / "binding.yaml").read_bytes())
    rendered = render_image_workflow(
        template=template,
        binding=binding,
        request=request,
        reference_names=("character-upload.png", "scene-upload.png"),
        output_prefix="p7-test",
    )
    assert rendered["3"]["inputs"]["text"] == request.prompt_text
    assert rendered["4"]["inputs"]["text"] == request.negative_prompt_text
    assert rendered["10"]["inputs"]["image"] == "character-upload.png"
    assert rendered["11"]["inputs"]["image"] == "scene-upload.png"
    assert template["10"]["inputs"]["image"] == "character.png"
    broken = binding.model_copy(update={"positive_prompt": ("missing", "inputs", "text")})
    with pytest.raises(AiVideoError) as exc:
        render_image_workflow(
            template=template,
            binding=broken,
            request=request,
            reference_names=("a.png", "b.png"),
            output_prefix="p7-test",
        )
    assert exc.value.code is ErrorCode.BINDING_INVALID


@pytest.mark.parametrize(
    "history",
    [
        {},
        {"outputs": {"8": {"images": [{"filename": "x.png"}]}}},
        {"outputs": {"9": {"images": [{"filename": "a.png"}, {"filename": "b.png"}]}}},
        {"outputs": {"9": {"images": [{"filename": "x.jpg"}]}}},
        {"outputs": {"9": {"images": [{"filename": "x.png"}]}, "8": {"images": [{"filename": "y.png"}]}}},
    ],
)
def test_save_image_output_fails_closed(history: dict[str, object]) -> None:
    with pytest.raises(AiVideoError):
        collect_save_image_output(history, "9")


def _mock_client(log: list[str], *, redirect_prompt: bool = False) -> ComfyClient:
    uploads = iter(("character-upload.png", "scene-upload.png"))

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request.url.path)
        if request.url.path == "/object_info":
            return httpx.Response(200, json=_FakeTransport().get_object_info())
        if request.url.path == "/upload/image":
            return httpx.Response(200, json={"name": next(uploads)})
        if request.url.path == "/prompt":
            if redirect_prompt:
                return httpx.Response(302, headers={"location": "http://example.com/prompt"})
            return httpx.Response(200, json={"prompt_id": "prompt-httpx"})
        if request.url.path == "/history/prompt-httpx":
            return httpx.Response(
                200,
                json={
                    "prompt-httpx": {
                        "outputs": {
                            "9": {
                                "images": [
                                    {"filename": "result.png", "subfolder": "", "type": "output"}
                                ]
                            }
                        }
                    }
                },
            )
        if request.url.path == "/view":
            return httpx.Response(200, content=PNG)
        return httpx.Response(404)

    http = httpx.Client(
        transport=httpx.MockTransport(handler),
        trust_env=False,
        follow_redirects=False,
    )
    return ComfyClient("http://127.0.0.1:8188", http_client=http)


def test_httpx_transport_sequence_ignores_proxy_env_and_rejects_redirects(
    tmp_path: Path,
) -> None:
    profile = _runtime_profile(tmp_path)
    request, paths = _request(profile, tmp_path)
    log: list[str] = []
    with patch.dict("os.environ", {"HTTP_PROXY": "http://proxy.invalid:3128"}):
        provider = _provider(tmp_path, profile, paths, _mock_client(log))
        provider.preflight(request)
        result = provider.generate(
            request, _authorization(request), _Permit()
        )
    assert result.image_bytes == PNG
    assert log == [
        "/object_info",
        "/upload/image",
        "/upload/image",
        "/prompt",
        "/history/prompt-httpx",
        "/view",
    ]

    redirected: list[str] = []
    with pytest.raises(AiVideoError) as exc:
        provider = _provider(
            tmp_path,
            profile,
            paths,
            _mock_client(redirected, redirect_prompt=True),
        )
        provider.preflight(request)
        provider.generate(request, _authorization(request), _Permit())
    assert exc.value.code is ErrorCode.COMFY_SUBMISSION_FAILED
    assert redirected[-1] == "/prompt"
