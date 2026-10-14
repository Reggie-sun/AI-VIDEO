from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from ai_video.comfy_client import JobResult, JobStatus
from ai_video.errors import AiVideoError
from ai_video.production.comfy_image import (
    ComfyLocalImageProvider,
    LocalImageExecutionProfile,
    load_local_image_binding,
    load_local_image_execution_profile,
    load_local_image_workflow,
    validate_profile_request_match,
)
from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageProviderParameters,
    ImageReferenceBinding,
)
from ai_video.production.comfy_image_workflow_contract import (
    validate_sealed_workflow_contract,
)
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)


ROOT = Path(__file__).parents[1]
PROFILE_PATH = ROOT / "workflows/profiles/p7_1_qwen_masked_edit.json"
LEGACY_PROFILE_PATH = ROOT / "workflows/profiles/p7_1_qwen_image_edit_2511.json"
LEGACY_BINDING_PATH = ROOT / "workflows/bindings/p7_1_qwen_image_edit_2511_binding.yaml"
LEGACY_WORKFLOW_PATH = ROOT / "workflows/templates/p7_1_qwen_image_edit_2511_api.json"
MASKED_PROFILE_HASH = "d9179d4f83a5572d09a14778587f9cb836eb603dc0ade6aacfe27650bfbf35b7"
LEGACY_PROFILE_SHA256 = "d02db2ce526f760502d1a78b9f7c0a153e89abacdde2695f6c7e3bd34d87c4f9"
LEGACY_BINDING_SHA256 = "d575b94c3b810742687f05f634aa40e0ded7eb85741b2b74831d4ab6b1cf7f55"
LEGACY_WORKFLOW_SHA256 = "34f1d2a67d049b646eef1c8f0c51aa8c1ad6b9eb5ef176c9ec422c3ff384a85f"


@pytest.fixture()
def sealed_masked_workflow():
    profile = load_local_image_execution_profile(PROFILE_PATH, artifact_root=ROOT)
    binding_payload = (ROOT / profile.binding_path).read_bytes()
    binding = load_local_image_binding(binding_payload)
    workflow = load_local_image_workflow(ROOT / profile.workflow_path)
    return profile, binding, workflow


def test_masked_profile_is_sealed_to_three_ordered_references(sealed_masked_workflow):
    profile, binding, _workflow = sealed_masked_workflow

    assert profile.lane_id == "qwen_image_edit_2511_masked_local"
    assert profile.supported_reference_roles == ("character", "scene", "edit_mask")
    assert profile.min_references == profile.max_references == 3
    assert binding.reference_images == (
        ("41", "inputs", "image"),
        ("83", "inputs", "image"),
        ("84", "inputs", "image"),
    )
    payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    assert payload["profile_content_hash"] == MASKED_PROFILE_HASH


def test_masked_workflow_preserves_legacy_profile_artifact_bytes():
    assert hashlib.sha256(LEGACY_PROFILE_PATH.read_bytes()).hexdigest() == LEGACY_PROFILE_SHA256
    assert hashlib.sha256(LEGACY_BINDING_PATH.read_bytes()).hexdigest() == LEGACY_BINDING_SHA256
    assert hashlib.sha256(LEGACY_WORKFLOW_PATH.read_bytes()).hexdigest() == LEGACY_WORKFLOW_SHA256
    legacy = json.loads(LEGACY_PROFILE_PATH.read_text(encoding="utf-8"))
    assert legacy["lane_id"] == "qwen_image_edit_2511_local"


def test_edit_mask_role_is_exclusive_to_the_sealed_masked_lane(sealed_masked_workflow):
    masked, _binding, _workflow = sealed_masked_workflow
    ordinary = load_local_image_execution_profile(LEGACY_PROFILE_PATH, artifact_root=ROOT)

    def request(profile, roles):
        return SimpleNamespace(
            provider_kind="comfyui_local",
            model_id=profile.profile_id,
            references=tuple(SimpleNamespace(role=role) for role in roles),
            parameters=SimpleNamespace(width=512, height=512),
        )

    with pytest.raises(AiVideoError):
        validate_profile_request_match(masked, request(masked, ("character", "scene")))
    with pytest.raises(AiVideoError):
        validate_profile_request_match(
            ordinary, request(ordinary, ("character", "scene", "edit_mask"))
        )
    validate_profile_request_match(
        masked, request(masked, ("character", "scene", "edit_mask"))
    )


def test_masked_workflow_contract_seals_all_mask_and_composite_edges(sealed_masked_workflow):
    profile, binding, workflow = sealed_masked_workflow

    validate_sealed_workflow_contract(profile, workflow, binding)

    assert workflow["170:160"]["inputs"]["image"] == ["83", 0]
    assert workflow["170:149"]["inputs"]["image1"] == ["170:160", 0]
    assert workflow["170:149"]["inputs"]["image2"] == ["41", 0]
    assert workflow["170:151"]["inputs"]["image1"] == ["170:160", 0]
    assert workflow["170:151"]["inputs"]["image2"] == ["41", 0]
    assert workflow["170:169"]["inputs"]["latent_image"] == ["170:173", 0]
    assert workflow["170:173"]["inputs"]["samples"] == ["170:156", 0]
    assert workflow["170:173"]["inputs"]["mask"] == ["170:172", 0]
    assert workflow["170:172"]["inputs"]["image"] == ["84", 0]
    assert workflow["170:172"]["inputs"]["channel"] == "red"
    assert workflow["170:174"]["inputs"] == {
        "destination": ["83", 0],
        "source": ["170:158", 0],
        "x": 0,
        "y": 0,
        "resize_source": False,
        "mask": ["170:172", 0],
    }
    assert workflow["9"]["inputs"]["images"] == ["170:174", 0]


@pytest.mark.parametrize(
    ("node_id", "input_name", "value"),
    (
        ("170:160", "image", ["84", 0]),
        ("170:160", "crop", "center"),
        ("170:149", "image2", ["83", 0]),
        ("170:147", "conditioning", ["170:151", 0]),
        ("170:169", "positive", ["170:147", 0]),
        ("170:172", "image", ["83", 0]),
        ("170:172", "channel", "alpha"),
        ("170:173", "mask", ["83", 0]),
        ("170:169", "latent_image", ["170:156", 0]),
        ("170:158", "samples", ["170:173", 0]),
        ("170:174", "destination", ["170:158", 0]),
        ("170:174", "source", ["83", 0]),
        ("170:174", "mask", ["84", 0]),
        ("9", "images", ["170:158", 0]),
    ),
)
def test_masked_workflow_contract_rejects_semantic_edge_drift(
    sealed_masked_workflow, node_id, input_name, value
):
    profile, binding, workflow = sealed_masked_workflow
    changed = copy.deepcopy(workflow)
    changed[node_id]["inputs"][input_name] = value

    with pytest.raises(AiVideoError):
        validate_sealed_workflow_contract(profile, changed, binding)


def _png(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _masked_provider(tmp_path: Path, *, mask: bytes, output: bytes):
    source_profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    workflow_bytes = (ROOT / source_profile["workflow_path"]).read_bytes()
    binding_bytes = (ROOT / source_profile["binding_path"]).read_bytes()
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    (artifact_root / "workflow.json").write_bytes(workflow_bytes)
    (artifact_root / "binding.yaml").write_bytes(binding_bytes)
    comfy_root = tmp_path / "comfy"
    comfy_root.mkdir()
    components = []
    for item in source_profile["components"]:
        component = dict(item)
        directory = {
            "diffusion": "diffusion_models",
            "text_encoder": "text_encoders",
            "vae": "vae",
        }[component["role"]]
        component_path = comfy_root / "models" / directory / component["filename"]
        component_path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"fixture-{component['role']}".encode()
        component_path.write_bytes(payload)
        component["size_bytes"] = len(payload)
        component["sha256"] = hashlib.sha256(payload).hexdigest()
        components.append(component)
    source_profile.update(
        {
            "workflow_path": Path("workflow.json"),
            "workflow_sha256": hashlib.sha256(workflow_bytes).hexdigest(),
            "binding_path": Path("binding.yaml"),
            "binding_sha256": hashlib.sha256(binding_bytes).hexdigest(),
            "components": components,
        }
    )
    profile = LocalImageExecutionProfile.create(**source_profile)

    reference_root = tmp_path / "refs"
    reference_root.mkdir()
    source = _png(Image.new("RGB", (256, 256), (32, 64, 96)))
    character = _png(Image.new("RGB", (256, 256), (96, 64, 32)))
    paths = {
        "character": reference_root / "character.png",
        "scene": reference_root / "scene.png",
        "edit_mask": reference_root / "mask.png",
    }
    payloads = {"character": character, "scene": source, "edit_mask": mask}
    references = {}
    for role in ("character", "scene", "edit_mask"):
        payload = payloads[role]
        paths[role].write_bytes(payload)
        references[role] = ImageReferenceBinding(
            role=role,
            asset_id=role,
            asset_sha256=hashlib.sha256(payload).hexdigest(),
            creative_artifact_id="scene-opening" if role != "character" else "lin-yan",
            creative_revision=1,
            creative_content_hash="1" * 64 if role != "character" else "2" * 64,
        )
    request = ImageGenerationRequest.create(
        attempt_id="masked-test-attempt",
        provider_kind="comfyui_local",
        model_id=profile.profile_id,
        target_shot_id="shot-1",
        target_asset_role="visual",
        prompt_text="preserve all scene pixels outside the marked edit area",
        negative_prompt_text="",
        parameters=ImageProviderParameters(
            seed=7,
            width=256,
            height=256,
            output_format="png",
            generation_revision=1,
        ),
        references=(references["character"], references["scene"], references["edit_mask"]),
        base_project=ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{'0' * 64}.yaml"),
            revision=1,
            content_hash="0" * 64,
            file_sha256="1" * 64,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{'1' * 64}.json"),
            revision_id="1" * 64,
            content_hash="1" * 64,
            file_sha256="2" * 64,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            revision_id="2" * 64,
            content_hash="2" * 64,
            path=Path(f"state/dependency_graph.{'2' * 64}.json"),
            file_sha256="3" * 64,
        ),
    )

    class MaskTransport:
        uploaded: list[str] = []
        submitted: list[dict[str, object]] = []
        object_info_calls = 0

        def get_object_info(self):
            self.object_info_calls += 1
            classes = {
                node["class_type"]
                for node in json.loads(workflow_bytes).values()
            }
            return {name: {} for name in classes}

        def upload_image(self, path):
            self.uploaded.append(Path(path).name)
            return Path(path).name

        def submit_prompt(self, workflow):
            self.submitted.append(workflow)
            return "local-prompt"

        def poll_job(self, prompt_id, **_kwargs):
            return JobResult(
                JobStatus.COMPLETED,
                prompt_id,
                history={"outputs": {"9": {"images": [{"filename": "edited.png"}]}}},
            )

        def fetch_artifact_bytes(self, **_kwargs):
            return output

    transport = MaskTransport()
    provider = ComfyLocalImageProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        reference_root=reference_root,
        reference_resolver=lambda reference: paths[reference.role],
        transport=transport,
        commit_resolver=lambda: profile.comfyui_commit,
    )
    permit = SimpleNamespace(calls=0)

    def consume_image_generation_permit(*, request_fingerprint):
        permit.calls += 1
        return request_fingerprint == request.request_fingerprint

    permit._consume_image_generation_permit = consume_image_generation_permit
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=sum(path.stat().st_size for path in paths.values()),
    )
    authorization = ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="Apache-2.0",
        policy_receipt_id="masked-image-test-policy",
    )
    return provider, request, paths, transport, permit, authorization


def test_masked_preflight_checks_mask_bytes_before_runtime_inspection(tmp_path: Path):
    source = Image.new("RGB", (256, 256), (32, 64, 96))
    mask = _png(Image.new("L", (256, 256), 255))
    provider, request, _paths, transport, _permit, _authorization = _masked_provider(
        tmp_path, mask=mask, output=_png(source)
    )

    with pytest.raises(AiVideoError):
        provider.preflight(request)

    assert transport.object_info_calls == 0
    assert transport.uploaded == []
    assert transport.submitted == []


def test_masked_generate_reopens_mask_before_upload_and_permit(tmp_path: Path):
    source = Image.new("RGB", (256, 256), (32, 64, 96))
    mask_image = Image.new("L", (256, 256), 0)
    for x in range(128, 256):
        for y in range(256):
            mask_image.putpixel((x, y), 255)
    provider, request, paths, transport, permit, authorization = _masked_provider(
        tmp_path, mask=_png(mask_image), output=_png(source)
    )
    provider.preflight(request)
    paths["edit_mask"].write_bytes(_png(Image.new("L", (256, 256), 0)))

    with pytest.raises(AiVideoError):
        provider.generate(request, authorization, permit)

    assert transport.uploaded == []
    assert transport.submitted == []
    assert permit.calls == 0


def test_masked_output_rejects_changes_outside_white_mask(tmp_path: Path):
    source = Image.new("RGB", (256, 256), (32, 64, 96))
    mask_image = Image.new("L", (256, 256), 0)
    for x in range(128, 256):
        for y in range(256):
            mask_image.putpixel((x, y), 255)
    changed_output = source.copy()
    changed_output.putpixel((5, 5), (0, 0, 0))
    provider, request, _paths, transport, permit, authorization = _masked_provider(
        tmp_path, mask=_png(mask_image), output=_png(changed_output)
    )
    provider.preflight(request)

    with pytest.raises(AiVideoError):
        provider.generate(request, authorization, permit)

    assert transport.uploaded == ["character.png", "scene.png", "mask.png"]
    assert len(transport.submitted) == 1
    assert permit.calls == 1


def test_masked_provider_returns_exact_composite_when_protected_pixels_match(
    tmp_path: Path,
):
    source = Image.new("RGB", (256, 256), (32, 64, 96))
    mask_image = Image.new("L", (256, 256), 0)
    for x in range(128, 256):
        for y in range(256):
            mask_image.putpixel((x, y), 255)
    source_bytes = _png(source)
    provider, request, _paths, transport, permit, authorization = _masked_provider(
        tmp_path, mask=_png(mask_image), output=source_bytes
    )
    provider.preflight(request)

    result = provider.generate(request, authorization, permit)

    assert result.image_bytes == source_bytes
    assert transport.uploaded == ["character.png", "scene.png", "mask.png"]
    assert transport.submitted[0]["84"]["inputs"]["image"] == "mask.png"
    assert transport.submitted[0]["170:160"]["inputs"]["image"] == ["83", 0]
    assert permit.calls == 1
