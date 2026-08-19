from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Literal, Protocol
from urllib.parse import urlsplit

import httpx
import yaml
from pydantic import Field, field_validator, model_validator

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image import (
    ImageGenerationReferenceBinding,
    ImageGenerationAuthorization,
    ImageGenerationRequest,
    ImageLocalResourceEvidence,
    ImageProviderResult,
)
from ai_video.production.models import StrictModel, ToolIdentity
from ai_video.workflow_loader import load_workflow_template
from ai_video.workflow_renderer import _set_path, validate_api_workflow


_PROFILE_ID_PREFIX = "local-image-profile:sha256:"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_REVISION_PATTERN = r"^[0-9a-f]{40}$"
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        ErrorCode.IMAGE_REQUEST_INVALID,
        message,
        detail,
        retryable=False,
    )


def validate_loopback_endpoint(value: str) -> str:
    """Return a canonical loopback HTTP origin or fail before transport use."""

    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise _invalid("Local image endpoint is invalid.", str(exc)) from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOOPBACK_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or port is None
    ):
        raise _invalid(
            "Local image endpoint must be a literal loopback HTTP origin with an explicit port.",
            value,
        )
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    return f"http://{host}:{port}"


class LocalImageModelComponent(StrictModel):
    role: Literal["diffusion", "text_encoder", "vae", "lora"]
    filename: str = Field(min_length=1)
    source_repository_id: str = Field(min_length=1)
    source_revision: str = Field(pattern=_REVISION_PATTERN)
    size_bytes: int = Field(strict=True, gt=0)
    sha256: str = Field(pattern=_SHA256_PATTERN)
    precision: str = Field(min_length=1)
    quantization: str | None = None

    @field_validator("filename")
    @classmethod
    def _clean_filename(cls, value: str) -> str:
        if Path(value).name != value or value in {".", ".."}:
            raise ValueError("component filename must be a clean basename")
        return value


class LocalImageRequiredNode(StrictModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class LocalImageExecutionProfile(StrictModel):
    schema_version: Literal["1"]
    lane_id: Literal["qwen_image_edit_2511_local", "flux2_klein_4b_local"]
    adapter_contract_version: Literal["1"]
    model_repository_id: str = Field(min_length=1)
    model_repository_revision: str = Field(pattern=_REVISION_PATTERN)
    model_card_url: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    license_source_url: str = Field(min_length=1)
    components: tuple[LocalImageModelComponent, ...] = Field(min_length=3)
    comfyui_commit: str = Field(pattern=_REVISION_PATTERN)
    required_nodes: tuple[LocalImageRequiredNode, ...] = Field(min_length=1)
    workflow_source_url: str = Field(min_length=1)
    workflow_source_revision: str = Field(min_length=1)
    workflow_path: Path
    workflow_sha256: str = Field(pattern=_SHA256_PATTERN)
    binding_path: Path
    binding_sha256: str = Field(pattern=_SHA256_PATTERN)
    supported_reference_roles: tuple[
        Literal["character", "scene", "style", "continuity_terminal"], ...
    ]
    min_references: int = Field(strict=True, ge=1)
    max_references: int = Field(strict=True, ge=1)
    min_width: int = Field(strict=True, gt=0)
    max_width: int = Field(strict=True, gt=0)
    min_height: int = Field(strict=True, gt=0)
    max_height: int = Field(strict=True, gt=0)
    sampler: str = Field(min_length=1)
    scheduler: str = Field(min_length=1)
    steps: int = Field(strict=True, gt=0)
    guidance: float = Field(gt=0)
    output_node_id: str = Field(min_length=1)
    output_mime_type: Literal["image/png"]
    loopback_endpoints: tuple[str, ...] = Field(min_length=1)
    optional_lora_enabled: bool = False
    profile_content_hash: str = Field(pattern=_SHA256_PATTERN)

    @property
    def profile_id(self) -> str:
        return profile_id_for(self.profile_content_hash)

    @field_validator("workflow_path", "binding_path")
    @classmethod
    def _clean_relative_path(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts or value == Path("."):
            raise ValueError("profile artifact paths must be clean and relative")
        return value

    @field_validator("loopback_endpoints")
    @classmethod
    def _loopback_only(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        canonical = tuple(validate_loopback_endpoint(value) for value in values)
        if len(set(canonical)) != len(canonical):
            raise ValueError("profile loopback endpoints must be unique")
        return canonical

    @model_validator(mode="after")
    def _sealed_and_supported(self) -> "LocalImageExecutionProfile":
        roles = tuple(component.role for component in self.components)
        if roles[:3] != ("diffusion", "text_encoder", "vae") or len(set(roles)) != len(roles):
            raise ValueError("profile components require canonical diffusion/text_encoder/vae roles")
        if self.min_references > self.max_references:
            raise ValueError("profile reference bounds are invalid")
        if self.min_width > self.max_width or self.min_height > self.max_height:
            raise ValueError("profile dimension bounds are invalid")
        if self.lane_id == "qwen_image_edit_2511_local":
            if self.model_repository_id != "Qwen/Qwen-Image-Edit-2511":
                raise ValueError("Qwen lane requires the exact official repository")
            diffusion = self.components[0]
            if diffusion.precision.lower() != "bf16" or self.optional_lora_enabled or "lora" in roles:
                raise ValueError("Qwen profile requires declared BF16 diffusion with LoRA disabled")
        else:
            if self.model_repository_id != "black-forest-labs/FLUX.2-klein-4B":
                raise ValueError("FLUX lane requires the exact distilled 4B repository")
            if any(component.quantization not in {None, "none"} for component in self.components):
                raise ValueError("FLUX distilled 4B profile rejects undeclared quantization")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if expected != self.profile_content_hash:
            raise ValueError("profile_content_hash does not match the sealed profile")
        return self

    @classmethod
    def create(cls, **values: object) -> "LocalImageExecutionProfile":
        data = dict(values)
        data.pop("profile_content_hash", None)
        data["components"] = tuple(
            item
            if isinstance(item, LocalImageModelComponent)
            else LocalImageModelComponent.model_validate(item)
            for item in data["components"]
        )
        data["required_nodes"] = tuple(
            item
            if isinstance(item, LocalImageRequiredNode)
            else LocalImageRequiredNode.model_validate(item)
            for item in data["required_nodes"]
        )
        data["supported_reference_roles"] = tuple(data["supported_reference_roles"])
        data["loopback_endpoints"] = tuple(
            validate_loopback_endpoint(item) for item in data["loopback_endpoints"]
        )
        data["workflow_path"] = Path(data["workflow_path"])
        data["binding_path"] = Path(data["binding_path"])
        data["guidance"] = float(data["guidance"])
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        return cls.model_validate(data)


def profile_id_for(content_hash: str) -> str:
    if len(content_hash) != 64 or any(char not in "0123456789abcdef" for char in content_hash):
        raise ValueError("profile content hash must be lowercase SHA-256")
    return f"{_PROFILE_ID_PREFIX}{content_hash}"


def _read_exact(root: Path, relative: Path, expected_sha256: str, label: str) -> bytes:
    try:
        path = (root / relative).resolve(strict=True)
        path.relative_to(root.resolve(strict=True))
        payload = path.read_bytes()
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid(f"{label} could not be reopened safely.", str(exc)) from exc
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise _invalid(f"{label} digest does not match the sealed profile.")
    return payload


def load_local_image_execution_profile(
    path: str | Path,
    *,
    artifact_root: str | Path | None = None,
) -> LocalImageExecutionProfile:
    profile_path = Path(path)
    try:
        profile = LocalImageExecutionProfile.model_validate_json(profile_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise _invalid("Local image execution profile is invalid.", str(exc)) from exc
    root = Path(artifact_root) if artifact_root is not None else profile_path.parent
    _read_exact(root, profile.workflow_path, profile.workflow_sha256, "Profile workflow")
    _read_exact(root, profile.binding_path, profile.binding_sha256, "Profile binding")
    return profile


class LocalImageBinding(StrictModel):
    positive_prompt: tuple[str | int, ...]
    negative_prompt: tuple[str | int, ...]
    seed: tuple[str | int, ...]
    width: tuple[str | int, ...]
    height: tuple[str | int, ...]
    reference_images: tuple[tuple[str | int, ...], ...] = Field(min_length=1)
    output_prefix: tuple[str | int, ...]
    output_node_id: str = Field(min_length=1)


def load_local_image_binding(payload: bytes) -> LocalImageBinding:
    try:
        return LocalImageBinding.model_validate(yaml.safe_load(payload))
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise _invalid("Local image workflow binding is invalid.", str(exc)) from exc


def load_local_image_workflow(path: str | Path) -> dict[str, Any]:
    return load_workflow_template(path)


_SEALED_NODE_CLASSES = {
    "qwen_image_edit_2511_local": {
        "170:145": "ModelSamplingAuraFlow",
        "170:146": "VAELoader",
        "170:147": "FluxKontextMultiReferenceLatentMethod",
        "170:148": "FluxKontextMultiReferenceLatentMethod",
        "170:149": "TextEncodeQwenImageEditPlus",
        "170:151": "TextEncodeQwenImageEditPlus",
        "170:152": "CFGNorm",
        "170:156": "VAEEncode",
        "170:158": "VAEDecode",
        "170:160": "ImageScale",
        "170:161": "UNETLoader",
        "170:162": "CLIPLoader",
        "170:169": "KSampler",
        "41": "LoadImage",
        "83": "LoadImage",
        "9": "SaveImage",
    },
    "flux2_klein_4b_local": {
        "76": "LoadImage",
        "81": "LoadImage",
        "92:101": "KSamplerSelect",
        "92:102": "Flux2Scheduler",
        "92:103": "CFGGuider",
        "92:104": "SamplerCustomAdvanced",
        "92:105": "VAEDecode",
        "92:106": "RandomNoise",
        "92:107": "UNETLoader",
        "92:108": "CLIPLoader",
        "92:109": "CLIPTextEncode",
        "92:110": "VAELoader",
        "92:111": "ImageScale",
        "92:112:115": "ReferenceLatent",
        "92:112:116": "VAEEncode",
        "92:112:117": "ReferenceLatent",
        "92:113": "EmptyFlux2LatentImage",
        "92:114": "GetImageSize",
        "92:84:118": "ReferenceLatent",
        "92:84:119": "VAEEncode",
        "92:84:120": "ReferenceLatent",
        "92:85": "ImageScaleToTotalPixels",
        "92:86": "CLIPTextEncode",
        "94": "SaveImage",
    },
}


def _input_edge(workflow: dict[str, Any], node_id: str, input_name: str) -> Any:
    return workflow.get(node_id, {}).get("inputs", {}).get(input_name)


def _loader_consumers(
    workflow: dict[str, Any], loader_ids: set[str]
) -> set[tuple[str, str, str]]:
    consumers = set()
    for node_id, node in workflow.items():
        inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
        for input_name, value in inputs.items():
            if (
                isinstance(value, list)
                and len(value) == 2
                and value[0] in loader_ids
            ):
                consumers.add((node_id, input_name, value[0]))
    return consumers


def _validate_sealed_workflow_contract(
    profile: LocalImageExecutionProfile,
    workflow: dict[str, Any],
    binding: LocalImageBinding,
) -> None:
    actual_node_classes = {
        node_id: node.get("class_type")
        for node_id, node in workflow.items()
        if isinstance(node, dict)
    }
    if actual_node_classes != _SEALED_NODE_CLASSES[profile.lane_id]:
        raise _invalid("Local image workflow node topology is not sealed.")

    loader_contract = {
        "UNETLoader": ("diffusion", "unet_name"),
        "CLIPLoader": ("text_encoder", "clip_name"),
        "VAELoader": ("vae", "vae_name"),
        "LoraLoaderModelOnly": ("lora", "lora_name"),
    }
    actual_components = []
    for node in workflow.values():
        if not isinstance(node, dict) or node.get("class_type") not in loader_contract:
            continue
        role, input_name = loader_contract[node["class_type"]]
        filename = node.get("inputs", {}).get(input_name)
        if not isinstance(filename, str):
            raise _invalid("Local image workflow model loader is malformed.")
        actual_components.append((role, filename))
    expected_components = [
        (component.role, component.filename) for component in profile.components
    ]
    if sorted(actual_components) != sorted(expected_components):
        raise _invalid(
            "Local image workflow model loaders do not match the sealed components."
        )
    if profile.lane_id == "qwen_image_edit_2511_local":
        expected_binding = {
            "positive_prompt": ("170:151", "inputs", "prompt"),
            "negative_prompt": ("170:149", "inputs", "prompt"),
            "seed": ("170:169", "inputs", "seed"),
            "width": ("170:160", "inputs", "width"),
            "height": ("170:160", "inputs", "height"),
            "reference_images": (
                ("41", "inputs", "image"),
                ("83", "inputs", "image"),
            ),
        }
        settings = (
            workflow.get("170:169", {}).get("inputs", {}).get("sampler_name")
            == profile.sampler
            and workflow.get("170:169", {}).get("inputs", {}).get("scheduler")
            == profile.scheduler
            and workflow.get("170:169", {}).get("inputs", {}).get("steps")
            == profile.steps
            and workflow.get("170:169", {}).get("inputs", {}).get("cfg")
            == profile.guidance
        )
        model_edges = (
            _input_edge(workflow, "170:145", "model") == ["170:161", 0]
            and _input_edge(workflow, "170:152", "model") == ["170:145", 0]
            and _input_edge(workflow, "170:169", "model") == ["170:152", 0]
        )
        loader_consumers = {
            ("170:145", "model", "170:161"),
            ("170:149", "clip", "170:162"),
            ("170:149", "vae", "170:146"),
            ("170:151", "clip", "170:162"),
            ("170:151", "vae", "170:146"),
            ("170:156", "vae", "170:146"),
            ("170:158", "vae", "170:146"),
        }
        loader_ids = {"170:161", "170:162", "170:146"}
    else:
        expected_binding = {
            "positive_prompt": ("92:109", "inputs", "text"),
            "negative_prompt": ("92:86", "inputs", "text"),
            "seed": ("92:106", "inputs", "noise_seed"),
            "width": ("92:111", "inputs", "width"),
            "height": ("92:111", "inputs", "height"),
            "reference_images": (
                ("76", "inputs", "image"),
                ("81", "inputs", "image"),
            ),
        }
        settings = (
            profile.scheduler == "flux2_distilled"
            and workflow.get("92:101", {}).get("inputs", {}).get("sampler_name")
            == profile.sampler
            and workflow.get("92:102", {}).get("inputs", {}).get("steps")
            == profile.steps
            and workflow.get("92:103", {}).get("inputs", {}).get("cfg")
            == profile.guidance
        )
        model_edges = _input_edge(workflow, "92:103", "model") == ["92:107", 0]
        loader_consumers = {
            ("92:103", "model", "92:107"),
            ("92:105", "vae", "92:110"),
            ("92:109", "clip", "92:108"),
            ("92:112:116", "vae", "92:110"),
            ("92:84:119", "vae", "92:110"),
            ("92:86", "clip", "92:108"),
        }
        loader_ids = {"92:107", "92:108", "92:110"}
    actual_binding = {
        key: getattr(binding, key) for key in expected_binding
    }
    if (
        actual_binding != expected_binding
        or not settings
        or not model_edges
        or _loader_consumers(workflow, loader_ids) != loader_consumers
    ):
        raise _invalid(
            "Local image workflow does not implement the sealed request semantics."
        )


def render_image_workflow(
    *,
    template: dict[str, Any],
    binding: LocalImageBinding,
    request: ImageGenerationRequest,
    reference_names: tuple[str, ...],
    output_prefix: str,
) -> dict[str, Any]:
    validate_api_workflow(template)
    if len(reference_names) != len(binding.reference_images):
        raise _invalid("Workflow reference slots do not match the exact request.")
    rendered = json.loads(json.dumps(template))
    values = (
        (binding.positive_prompt, request.prompt_text, "positive_prompt"),
        (binding.negative_prompt, request.negative_prompt_text, "negative_prompt"),
        (binding.seed, request.parameters.seed, "seed"),
        (binding.width, request.parameters.width, "width"),
        (binding.height, request.parameters.height, "height"),
        (binding.output_prefix, output_prefix, "output_prefix"),
    )
    for path, value, label in values:
        _set_path(rendered, list(path), value, label)
    for index, (path, name) in enumerate(zip(binding.reference_images, reference_names, strict=True)):
        _set_path(rendered, list(path), name, f"reference_images[{index}]")
    node = rendered.get(binding.output_node_id)
    if not isinstance(node, dict) or node.get("class_type") != "SaveImage":
        raise _invalid("Configured image output node is not SaveImage.")
    return rendered


class ComfyImageArtifact(StrictModel):
    filename: str = Field(min_length=1)
    subfolder: str = ""
    type: str = "output"


def collect_save_image_output(
    history: dict[str, Any], output_node_id: str
) -> ComfyImageArtifact:
    outputs = history.get("outputs")
    if not isinstance(outputs, dict):
        raise _invalid("ComfyUI history is missing image outputs.")
    unexpected = [
        node_id
        for node_id, value in outputs.items()
        if node_id != output_node_id
        and isinstance(value, dict)
        and isinstance(value.get("images"), list)
        and value["images"]
    ]
    selected = outputs.get(output_node_id)
    images = selected.get("images") if isinstance(selected, dict) else None
    if unexpected or not isinstance(images, list) or len(images) != 1:
        raise _invalid("ComfyUI history must contain exactly one configured image output.")
    item = images[0]
    try:
        artifact = ComfyImageArtifact.model_validate(item)
    except ValueError as exc:
        raise _invalid("ComfyUI image output metadata is malformed.", str(exc)) from exc
    if Path(artifact.filename).suffix.lower() != ".png":
        raise _invalid("ComfyUI image output must be PNG.")
    return artifact


def validate_profile_request_match(
    profile: LocalImageExecutionProfile,
    request: ImageGenerationRequest,
) -> None:
    if request.provider_kind != "comfyui_local" or request.model_id != profile.profile_id:
        raise _invalid("Image request does not match the sealed local execution profile.")
    count = len(request.references)
    roles = tuple(reference.role for reference in request.references)
    if (
        not profile.min_references <= count <= profile.max_references
        or any(role not in profile.supported_reference_roles for role in roles)
        or not profile.min_width <= request.parameters.width <= profile.max_width
        or not profile.min_height <= request.parameters.height <= profile.max_height
    ):
        raise _invalid("Image request is outside the sealed profile bounds.")


class LocalImageTransport(Protocol):
    def get_object_info(self) -> dict[str, Any]: ...
    def upload_image(self, path: str | Path) -> str: ...
    def submit_prompt(self, workflow: dict[str, Any]) -> str: ...
    def poll_job(
        self, prompt_id: str, *, poll_interval_seconds: float, timeout_seconds: float
    ) -> Any: ...
    def fetch_artifact_bytes(
        self, *, filename: str, subfolder: str, type_: str
    ) -> bytes: ...


ReferenceResolver = Callable[[ImageGenerationReferenceBinding], Path]
CommitResolver = Callable[[], str]


_COMPONENT_DIRECTORIES = {
    "diffusion": Path("models/diffusion_models"),
    "text_encoder": Path("models/text_encoders"),
    "vae": Path("models/vae"),
    "lora": Path("models/loras"),
}


def _git_head(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise _invalid("ComfyUI checkout identity could not be verified.", str(exc)) from exc
    return result.stdout.strip()


def _missing_required_node_inputs(
    workflow: dict[str, Any], object_info: dict[str, Any]
) -> list[str]:
    missing = []
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue
        node_info = object_info.get(node.get("class_type"))
        required = (
            node_info.get("input", {}).get("required", {})
            if isinstance(node_info, dict)
            else {}
        )
        inputs = node.get("inputs", {})
        if not isinstance(required, dict) or not isinstance(inputs, dict):
            continue
        missing.extend(
            f"{node_id}.{input_name}"
            for input_name in required
            if input_name not in inputs
        )
    return sorted(missing)


class ComfyLocalImageProvider:
    def __init__(
        self,
        profile: LocalImageExecutionProfile,
        *,
        artifact_root: str | Path,
        comfy_root: str | Path,
        reference_resolver: ReferenceResolver,
        reference_root: str | Path | None = None,
        endpoint: str = "http://127.0.0.1:8188",
        transport: LocalImageTransport | None = None,
        commit_resolver: CommitResolver | None = None,
        poll_interval_seconds: float = 0.25,
        timeout_seconds: float = 1_800.0,
    ) -> None:
        self.profile = profile
        self._root = Path(artifact_root).resolve(strict=True)
        self._comfy_root = Path(comfy_root).resolve(strict=True)
        self._reference_root = (
            Path(reference_root).resolve(strict=True)
            if reference_root is not None
            else self._root
        )
        self._reference_resolver = reference_resolver
        self._endpoint = validate_loopback_endpoint(endpoint)
        if self._endpoint not in profile.loopback_endpoints:
            raise _invalid("Selected loopback endpoint is not allowed by the profile.")
        if transport is None:
            http = httpx.Client(
                timeout=30,
                trust_env=False,
                follow_redirects=False,
            )
            transport = ComfyClient(self._endpoint, http_client=http)
        elif isinstance(transport, ComfyClient):
            if validate_loopback_endpoint(transport.base_url) != self._endpoint:
                raise _invalid("Injected Comfy transport endpoint does not match the profile.")
        self._transport = transport
        self._commit_resolver = commit_resolver or (lambda: _git_head(self._comfy_root))
        workflow_payload = _read_exact(
            self._root, profile.workflow_path, profile.workflow_sha256, "Profile workflow"
        )
        binding_payload = _read_exact(
            self._root, profile.binding_path, profile.binding_sha256, "Profile binding"
        )
        # Use the production loader for both API and UI workflow formats.
        workflow_path = self._root / profile.workflow_path
        self._workflow = load_local_image_workflow(workflow_path)
        if not workflow_payload:
            raise _invalid("Profile workflow is empty.")
        self._binding = load_local_image_binding(binding_payload)
        if self._binding.output_node_id != profile.output_node_id:
            raise _invalid("Binding output node does not match the sealed profile.")
        _validate_sealed_workflow_contract(profile, self._workflow, self._binding)
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._preflighted_requests: set[str] = set()

    def preflight(self, request: ImageGenerationRequest) -> None:
        """Prove the sealed local runtime before any durable submit evidence exists."""

        validate_profile_request_match(self.profile, request)
        commit = self._commit_resolver()
        if commit != self.profile.comfyui_commit:
            raise _invalid(
                "ComfyUI checkout does not match the sealed execution profile.",
                f"expected={self.profile.comfyui_commit} actual={commit}",
            )
        for component in self.profile.components:
            relative = _COMPONENT_DIRECTORIES[component.role] / component.filename
            try:
                path = (self._comfy_root / relative).resolve(strict=True)
                path.relative_to(self._comfy_root)
                stat = path.stat()
                actual_sha256 = _sha256_file(path)
            except (OSError, RuntimeError, ValueError) as exc:
                raise _invalid(
                    "A sealed local image component could not be reopened safely.",
                    str(exc),
                ) from exc
            if stat.st_size != component.size_bytes or actual_sha256 != component.sha256:
                raise _invalid(
                    "A local image component does not match the sealed execution profile.",
                    component.filename,
                )
        object_info = self._transport.get_object_info()
        workflow_nodes = {
            node.get("class_type")
            for node in self._workflow.values()
            if isinstance(node, dict)
        }
        required_nodes = {item.name for item in self.profile.required_nodes}
        missing = sorted(
            node
            for node in workflow_nodes | required_nodes
            if not isinstance(node, str) or node not in object_info
        )
        if missing:
            raise _invalid(
                "ComfyUI is missing nodes required by the sealed workflow.",
                ", ".join(str(item) for item in missing),
            )
        missing_inputs = _missing_required_node_inputs(self._workflow, object_info)
        if missing_inputs:
            raise _invalid(
                "ComfyUI node inputs do not match the sealed workflow.",
                ", ".join(missing_inputs),
            )
        self._preflighted_requests.add(request.request_fingerprint)

    def generate(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        permit: object,
    ) -> ImageProviderResult:
        validate_profile_request_match(self.profile, request)
        if request.request_fingerprint not in self._preflighted_requests:
            raise _invalid("Local image generation has not passed exact preflight.")
        self._preflighted_requests.remove(request.request_fingerprint)
        if (
            authorization.request_fingerprint != request.request_fingerprint
            or not authorization.local_only
            or not authorization.provider_enabled
        ):
            raise _invalid("Image authorization does not match the local request.")
        reference_names: list[str] = []
        for reference in request.references:
            try:
                path = self._reference_resolver(reference).resolve(strict=True)
                path.relative_to(self._reference_root)
                payload = path.read_bytes()
            except (OSError, RuntimeError, ValueError) as exc:
                raise _invalid(
                    "Image reference could not be reopened safely.", str(exc)
                ) from exc
            if hashlib.sha256(payload).hexdigest() != reference.asset_sha256:
                raise _invalid("Image reference bytes do not match the request.", reference.asset_id)
            reference_names.append(self._transport.upload_image(path))
        workflow = render_image_workflow(
            template=self._workflow,
            binding=self._binding,
            request=request,
            reference_names=tuple(reference_names),
            output_prefix=f"p7_1_{request.request_fingerprint[:16]}",
        )
        consume = getattr(permit, "_consume_image_generation_permit", None)
        if not callable(consume) or not consume(
            request_fingerprint=request.request_fingerprint
        ):
            raise _invalid("Local image generation requires the exact durable permit.")
        started = time.monotonic()
        prompt_id = self._transport.submit_prompt(workflow)
        job = self._transport.poll_job(
            prompt_id,
            poll_interval_seconds=self._poll_interval_seconds,
            timeout_seconds=self._timeout_seconds,
        )
        if job.status is not JobStatus.COMPLETED or not isinstance(job.history, dict):
            raise job.error or AiVideoError(
                ErrorCode.IMAGE_PROVIDER_FAILED,
                "Local ComfyUI image generation did not complete.",
                retryable=False,
            )
        artifact = collect_save_image_output(job.history, self.profile.output_node_id)
        image_bytes = self._transport.fetch_artifact_bytes(
            filename=artifact.filename,
            subfolder=artifact.subfolder,
            type_=artifact.type,
        )
        if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise _invalid("Local ComfyUI returned non-PNG bytes.")
        elapsed_ms = max(0, int((time.monotonic() - started) * 1_000))
        return ImageProviderResult.create(
            request=request,
            authorization=authorization,
            image_bytes=image_bytes,
            content_type="image/png",
            provider_request_id=prompt_id,
            adapter=ToolIdentity(
                name="comfyui-local-image",
                version=self.profile.profile_content_hash[:16],
            ),
            resource_evidence=ImageLocalResourceEvidence(
                elapsed_milliseconds=elapsed_ms,
                device_kind="unknown",
                measured_peak_memory_bytes=None,
            ),
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


__all__ = [
    "ComfyImageArtifact",
    "ComfyLocalImageProvider",
    "LocalImageBinding",
    "LocalImageExecutionProfile",
    "LocalImageModelComponent",
    "LocalImageRequiredNode",
    "LocalImageTransport",
    "collect_save_image_output",
    "load_local_image_binding",
    "load_local_image_execution_profile",
    "load_local_image_workflow",
    "profile_id_for",
    "render_image_workflow",
    "validate_loopback_endpoint",
    "validate_profile_request_match",
]
