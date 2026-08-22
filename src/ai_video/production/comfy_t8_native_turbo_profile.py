"""Sealed profiles for additive T8-native H3 Turbo V2 lanes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import validate_loopback_endpoint
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.workflow_loader import load_workflow_template


_SHA256 = r"^[0-9a-f]{64}$"
_REVISION = r"^[0-9a-f]{40}$"
_VERSION = r"^[0-9]+(?:\.[0-9]+){1,3}$"
_COMMON_CLASSES = (
    "UNETLoader",
    "LoraLoaderBypassModelOnly",
    "CLIPLoader",
    "VAELoader",
    "MiniMaxH3AudioConditioningT8",
    "MiniMaxH3DualClockSamplerT8",
    "RandomNoise",
    "BasicGuider",
    "SamplerCustomAdvanced",
    "MiniMaxH3AVDecodeT8",
    "VHS_VideoCombine",
)
_FORBIDDEN_CLASSES = (
    "MiniMaxH3TurboLoRA",
    "MiniMaxH3TurboSampler",
    "BasicScheduler",
    "KSamplerSelect",
    "LoraLoader",
    "LoraLoaderModelOnly",
)
_RUNTIME_FILE_CHOOSERS = {
    "UNETLoader": ("unet_name",),
    "LoraLoaderBypassModelOnly": ("lora_name",),
    "CLIPLoader": ("clip_name",),
    "VAELoader": ("vae_name",),
    "LoadImage": ("image",),
    "VHS_LoadVideo": ("video",),
    "VHS_LoadAudioUpload": ("audio",),
}
_TASK_IDENTITIES = {
    "T2VA": (
        "minimax-h3-t8-t2va-turbo-native-v2",
        "minimax_h3_t8_t2va_turbo_native",
        "minimax-h3-t8-t2va-turbo-native",
        "minimax_h3_t8_t2va_turbo_native_v2_local",
        "text_to_video",
        "text_to_video",
    ),
    "I2VA": (
        "minimax-h3-t8-i2va-turbo-native-v2",
        "minimax_h3_t8_i2va_turbo_native",
        "minimax-h3-t8-i2va-turbo-native",
        "minimax_h3_t8_i2va_turbo_native_v2_local",
        "image_to_video",
        "image_to_video",
    ),
    "FL2VA": (
        "minimax-h3-t8-fl2va-turbo-native-v2",
        "minimax_h3_t8_fl2va_turbo_native",
        "minimax-h3-t8-fl2va-turbo-native",
        "minimax_h3_t8_fl2va_turbo_native_v2_local",
        "first_last_frame_video",
        "image_to_video",
    ),
    "Ref2VA": (
        "minimax-h3-t8-ref2va-turbo-native-v2",
        "minimax_h3_t8_ref2va_turbo_native",
        "minimax-h3-t8-ref2va-turbo-native",
        "minimax_h3_t8_ref2va_turbo_native_v2_local",
        "reference_to_video",
        "reference_to_video",
    ),
}

_LORA_MAIN_SHAPES = {
    "adaln_proj.linear": ((16, 2688), (96768, 16)),
    "attn.qkv_proj": ((64, 5376), (21504, 64)),
    "attn.out_proj": ((64, 7168), (5376, 64)),
    "mlp.fc1": ((64, 5376), (28672, 64)),
    "mlp.fc2": ((64, 14336), (5376, 64)),
}
_LORA_REFINER_SHAPES = {
    key: value for key, value in _LORA_MAIN_SHAPES.items() if key != "adaln_proj.linear"
}
_LORA_FINAL_SHAPES = ((16, 2688), (10752, 16))
_MAX_SAFETENSORS_HEADER_BYTES = 1024 * 1024


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _read_exact(root: Path, relative: Path, digest: str, label: str) -> bytes:
    try:
        path = (root / relative).resolve(strict=True)
        path.relative_to(root.resolve(strict=True))
        payload = path.read_bytes()
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid(f"{label} could not be reopened safely.", str(exc)) from exc
    if hashlib.sha256(payload).hexdigest() != digest:
        raise _invalid(f"{label} hash does not match the sealed profile.")
    return payload


class T8NativeTurboComponent(StrictModel):
    role: Literal["diffusion", "text_encoder", "video_vae", "audio_vae"]
    filename: str = Field(min_length=1)
    size_bytes: int = Field(strict=True, gt=0)
    sha256: str = Field(pattern=_SHA256)
    precision: str = Field(min_length=1)

    @field_validator("filename")
    @classmethod
    def _basename(cls, value: str) -> str:
        if Path(value).name != value or value in {".", ".."}:
            raise ValueError("component filename must be a clean basename")
        return value


class T8NativeTurboLoraSeal(StrictModel):
    filename: Literal["minimax_h3_turbo_4step_ema_comfyui.safetensors"]
    size_bytes: int = Field(strict=True, gt=0)
    sha256: str = Field(pattern=_SHA256)
    strength: Literal[1.0]
    source_repository_id: Literal["DARK-MING/MiniMax-H3-Turbo-Lora"]
    source_repository_revision: str = Field(pattern=_REVISION)
    tensor_count: Literal[518]
    tensor_dtype: Literal["BF16"]
    module_count: Literal[259]
    source_filename: Literal["minimax_h3_turbo_4step_ema.safetensors"]
    source_size_bytes: int = Field(strict=True, gt=0)
    source_sha256: str = Field(pattern=_SHA256)
    converter_repository: Literal[
        "https://github.com/T8mars/comfyui-minimax-h3-audio-T8"
    ]
    converter_commit: str = Field(pattern=_REVISION)
    converter_sha256: str = Field(pattern=_SHA256)
    conversion_contract: Literal["t8-h3-lora-conversion/1"]
    value_identity_verified: bool
    conversion_verified: bool


class T8NativeTurboNodeSchemaSeal(StrictModel):
    node_name: str = Field(min_length=1)
    schema_sha256: str = Field(pattern=_SHA256)


class T8NativeTurboRuntimeInspection(StrictModel):
    comfyui_commit: str = Field(pattern=_REVISION)
    t8_commit: str = Field(pattern=_REVISION)
    t8_version: str = Field(pattern=_VERSION)
    videohelpersuite_commit: str = Field(pattern=_REVISION)
    sageattention_version: str = Field(pattern=_VERSION)
    launch_capabilities: tuple[str, ...]

    @field_validator("launch_capabilities")
    @classmethod
    def _unique_capabilities(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("runtime launch capabilities must be unique")
        return values


class T8NativeTurboBinding(StrictModel):
    task_type: tuple[str | int, ...]
    prompt: tuple[str | int, ...]
    seed: tuple[str | int, ...]
    width: tuple[str | int, ...]
    height: tuple[str | int, ...]
    length: tuple[str | int, ...]
    frame_count: tuple[str | int, ...]
    steps: tuple[str | int, ...]
    sampler: tuple[str | int, ...]
    scheduler: tuple[str | int, ...]
    output_prefix: tuple[str | int, ...]
    conditioning_node_id: str = Field(min_length=1)
    first_frame_node_id: str | None = None
    last_frame_node_id: str | None = None
    dynamic_node_start: int = Field(strict=True, ge=1)
    output_node_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _aliases(self) -> "T8NativeTurboBinding":
        if self.length != self.frame_count:
            raise ValueError("length and frame_count must bind the same input")
        return self


class T8NativeTurboExecutionProfile(StrictModel):
    schema_version: Literal["2"]
    capability_id: str = Field(min_length=1)
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    profile_version: Literal["v2"]
    lane_id: str = Field(min_length=1)
    task_type: Literal["T2VA", "I2VA", "FL2VA", "Ref2VA"]
    neutral_mode: Literal[
        "text_to_video", "image_to_video", "first_last_frame_video", "reference_to_video"
    ]
    provider_mode: Literal["text_to_video", "image_to_video", "reference_to_video"]
    availability: Literal["blocked", "offline-only", "live-ready"]
    availability_blockers: tuple[str, ...]
    t8_repository: Literal["https://github.com/T8mars/comfyui-minimax-h3-audio-T8"]
    t8_commit: str = Field(pattern=_REVISION)
    t8_version: str = Field(pattern=_VERSION)
    t8_license_id: Literal["GPL-3.0-or-later"]
    adapter_implementation_origin: Literal["AI-VIDEO"]
    comfyui_commit: str = Field(pattern=_REVISION)
    videohelpersuite_commit: str = Field(pattern=_REVISION)
    sageattention_version: str = Field(pattern=_VERSION)
    sageattention_source_commit: str = Field(pattern=_REVISION)
    required_launch_capabilities: tuple[Literal["sage_attention"], ...]
    model_repository_id: Literal["Comfy-Org/MiniMax-H3"]
    model_repository_revision: str = Field(pattern=_REVISION)
    components: tuple[T8NativeTurboComponent, ...]
    lora: T8NativeTurboLoraSeal
    required_nodes: tuple[str, ...] = Field(min_length=1)
    forbidden_nodes: tuple[str, ...] = Field(min_length=1)
    node_schema_seals: tuple[T8NativeTurboNodeSchemaSeal, ...] = Field(min_length=1)
    workflow_path: Path
    workflow_sha256: str = Field(pattern=_SHA256)
    binding_path: Path
    binding_sha256: str = Field(pattern=_SHA256)
    loopback_endpoints: tuple[str, ...] = Field(min_length=1)
    width: Literal[1344]
    height: Literal[768]
    frame_count: Literal[124]
    fps: Literal[24]
    native_audio_required: Literal[True]
    output_container: Literal["mp4"]
    output_mime_type: Literal["video/mp4"]
    sampler: Literal["dual_clock_euler"]
    scheduler: Literal["native_flow"]
    steps: Literal[4]
    shift_video: Literal[12.0]
    shift_audio: Literal[3.0]
    output_crf: Literal[17]
    output_node_id: Literal["12"]
    final_av_filename_suffix: Literal["-audio.mp4"]
    reject_video_only_sibling: Literal[True]
    remote_provider_enabled: Literal[False]
    cloud_fallback_enabled: Literal[False]
    image_mime_types: tuple[Literal["image/png"], ...]
    max_image_bytes: int = Field(strict=True, gt=0)
    reference_video_mime_types: tuple[Literal["video/mp4"], ...]
    max_reference_video_bytes: int = Field(strict=True, gt=0)
    reference_video_min_duration_millis: Literal[2000]
    reference_video_max_duration_millis: Literal[15000]
    reference_video_fps: Literal[24]
    reference_audio_mime_types: tuple[
        Literal["audio/wav", "audio/mpeg", "audio/mp4"], ...
    ]
    max_reference_audio_bytes: int = Field(strict=True, gt=0)
    profile_content_hash: str = Field(pattern=_SHA256)

    @field_validator("workflow_path", "binding_path")
    @classmethod
    def _relative(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts or value == Path("."):
            raise ValueError("profile paths must be clean and relative")
        return value

    @field_validator("loopback_endpoints")
    @classmethod
    def _loopback(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        canonical = tuple(validate_loopback_endpoint(value) for value in values)
        if len(set(canonical)) != len(canonical):
            raise ValueError("profile loopback endpoints must be unique")
        return canonical

    @model_validator(mode="after")
    def _sealed(self) -> "T8NativeTurboExecutionProfile":
        identity = (
            self.capability_id,
            self.provider_kind,
            self.model_id,
            self.lane_id,
            self.neutral_mode,
            self.provider_mode,
        )
        if identity != _TASK_IDENTITIES[self.task_type]:
            raise ValueError("profile task identity is not canonical")
        component_roles = tuple(item.role for item in self.components)
        if self.task_type == "Ref2VA":
            if component_roles not in {
                (),
                ("diffusion", "text_encoder", "video_vae", "audio_vae"),
            }:
                raise ValueError("Ref2VA component roles are not canonical")
        elif component_roles != (
            "diffusion",
            "text_encoder",
            "video_vae",
            "audio_vae",
        ):
            raise ValueError("profile component roles are not canonical")
        if self.components and "_pruned_" in self.components[0].filename:
            raise ValueError("T8-native Turbo V2 forbids pruned diffusion models")
        if tuple(self.forbidden_nodes) != _FORBIDDEN_CLASSES:
            raise ValueError("forbidden node inventory is not canonical")
        if not set(_COMMON_CLASSES).issubset(self.required_nodes):
            raise ValueError("required native T8 backbone is incomplete")
        if len(set(self.required_nodes)) != len(self.required_nodes):
            raise ValueError("required node inventory must be unique")
        sealed_names = tuple(item.node_name for item in self.node_schema_seals)
        if len(set(sealed_names)) != len(sealed_names) or set(sealed_names) != set(
            self.required_nodes
        ):
            raise ValueError("node schema seals must cover every required node exactly")
        if self.availability == "live-ready" and (
            self.availability_blockers
            or not self.lora.conversion_verified
            or not self.lora.value_identity_verified
            or not self.components
        ):
            raise ValueError("live-ready profile still has unresolved asset gates")
        if self.availability == "blocked" and not self.availability_blockers:
            raise ValueError("blocked profile requires at least one explicit blocker")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if self.profile_content_hash != expected:
            raise ValueError("profile_content_hash does not match the profile")
        return self

    @classmethod
    def create(cls, **values: object) -> "T8NativeTurboExecutionProfile":
        data = dict(values)
        data.pop("profile_content_hash", None)
        for key in ("workflow_path", "binding_path"):
            data[key] = Path(data[key])
        for key in (
            "availability_blockers",
            "required_launch_capabilities",
            "required_nodes",
            "forbidden_nodes",
            "loopback_endpoints",
            "image_mime_types",
            "reference_video_mime_types",
            "reference_audio_mime_types",
        ):
            data[key] = tuple(data[key])
        data["components"] = tuple(
            item
            if isinstance(item, T8NativeTurboComponent)
            else T8NativeTurboComponent.model_validate(item)
            for item in data["components"]
        )
        data["lora"] = (
            data["lora"]
            if isinstance(data["lora"], T8NativeTurboLoraSeal)
            else T8NativeTurboLoraSeal.model_validate(data["lora"])
        )
        data["node_schema_seals"] = tuple(
            item
            if isinstance(item, T8NativeTurboNodeSchemaSeal)
            else T8NativeTurboNodeSchemaSeal.model_validate(item)
            for item in data["node_schema_seals"]
        )
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        return cls.model_validate(data)


def _expected_lora_tensor_shapes() -> dict[str, tuple[int, ...]]:
    modules: dict[str, tuple[tuple[int, ...], tuple[int, ...]]] = {}
    for block in range(50):
        for name, shapes in _LORA_MAIN_SHAPES.items():
            modules[f"blocks.{block}.{name}"] = shapes
    for block in range(2):
        for name, shapes in _LORA_REFINER_SHAPES.items():
            modules[f"token_refiner.blocks.{block}.{name}"] = shapes
    modules["final_layer.adaln_proj.linear"] = _LORA_FINAL_SHAPES
    return {
        f"diffusion_model.{module}.lora_{side}.weight": shape
        for module, shapes in modules.items()
        for side, shape in zip(("A", "B"), shapes, strict=True)
    }


def validate_t8_native_turbo_lora(
    path: str | Path, seal: T8NativeTurboLoraSeal
) -> None:
    """Validate the bounded safetensors schema sealed by Gate 0A."""
    try:
        with Path(path).open("rb") as handle:
            header_size = int.from_bytes(handle.read(8), "little")
            if not 0 < header_size <= _MAX_SAFETENSORS_HEADER_BYTES:
                raise ValueError("safetensors header size is outside the bounded contract")
            header = json.loads(handle.read(header_size))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise _invalid("The sealed V2 LoRA header is invalid.", str(exc)) from exc
    if not isinstance(header, dict):
        raise _invalid("The sealed V2 LoRA header is invalid.")
    metadata = header.pop("__metadata__", None)
    expected_metadata = {
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
    }
    if metadata != expected_metadata:
        raise _invalid("The sealed V2 LoRA conversion metadata changed.")
    expected = _expected_lora_tensor_shapes()
    if len(header) != seal.tensor_count or set(header) != set(expected):
        raise _invalid("The sealed V2 LoRA tensor inventory changed.")
    for key, shape in expected.items():
        descriptor = header[key]
        if not isinstance(descriptor, dict) or (
            descriptor.get("dtype") != seal.tensor_dtype
            or descriptor.get("shape") != list(shape)
        ):
            raise _invalid("The sealed V2 LoRA tensor schema changed.", key)


def node_schema_seals(
    object_info: dict[str, Any], required_nodes: tuple[str, ...]
) -> tuple[T8NativeTurboNodeSchemaSeal, ...]:
    result = []
    for node_name in required_nodes:
        node = object_info.get(node_name)
        if not isinstance(node, dict):
            raise _invalid("ComfyUI is missing a sealed V2 node.", node_name)
        input_schema = json.loads(json.dumps(node.get("input")))
        if not isinstance(input_schema, dict):
            raise _invalid("A sealed V2 node schema is malformed.", node_name)
        for section in ("required", "optional"):
            fields = input_schema.get(section)
            if not isinstance(fields, dict):
                continue
            for field in _RUNTIME_FILE_CHOOSERS.get(node_name, ()):
                spec = fields.get(field)
                if (
                    isinstance(spec, list)
                    and spec
                    and isinstance(spec[0], list)
                ):
                    spec[0] = ["<runtime-file-inventory>"]
        projection = {
            "input": input_schema,
            "input_order": node.get("input_order"),
            "output_name": node.get("output_name"),
        }
        if not all(projection.values()):
            raise _invalid("A sealed V2 node schema is malformed.", node_name)
        result.append(
            T8NativeTurboNodeSchemaSeal(
                node_name=node_name,
                schema_sha256=canonical_sha256(projection),
            )
        )
    return tuple(result)


def load_t8_native_turbo_binding(payload: bytes) -> T8NativeTurboBinding:
    try:
        return T8NativeTurboBinding.model_validate(yaml.safe_load(payload))
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise _invalid("T8-native Turbo V2 binding is invalid.", str(exc)) from exc


def validate_native_turbo_workflow(
    profile: T8NativeTurboExecutionProfile,
    workflow: dict[str, Any],
    binding: T8NativeTurboBinding,
) -> None:
    classes = tuple(
        node.get("class_type") for node in workflow.values() if isinstance(node, dict)
    )
    if any(name in classes for name in profile.forbidden_nodes):
        raise _invalid("T8-native Turbo V2 workflow contains a forbidden node.")
    if classes.count("LoraLoaderBypassModelOnly") != 1 or classes.count(
        "MiniMaxH3DualClockSamplerT8"
    ) != 1:
        raise _invalid("T8-native Turbo V2 requires one LoRA and one sampling owner.")
    if not set(_COMMON_CLASSES).issubset(classes):
        raise _invalid("T8-native Turbo V2 workflow node inventory is incomplete.")
    conditioning = workflow[binding.conditioning_node_id]["inputs"]
    sampler = workflow["7"]["inputs"]
    lora = workflow["2"]["inputs"]
    output = workflow[binding.output_node_id]["inputs"]
    unet = workflow["1"]["inputs"].get("unet_name")
    media_keys = {
        "first_frame",
        "last_frame",
        "ref_images",
        "ref_videos",
        "ref_video_audios",
        "ref_audios",
    }
    expected_media = {
        "T2VA": set(),
        "I2VA": {"first_frame"},
        "FL2VA": {"first_frame", "last_frame"},
        "Ref2VA": set(),
    }[profile.task_type]
    has_video_audio_linkage = any(
        key == "ref_video_audios" or key.startswith("ref_video_audios.")
        for key in conditioning
    )
    if (
        conditioning.get("task_type") != profile.task_type
        or conditioning.get("audio_mode") != "native"
        or {key for key in media_keys if key in conditioning} != expected_media
        or has_video_audio_linkage
        or not isinstance(unet, str)
        or "_pruned_" in unet
        or profile.components
        and unet != profile.components[0].filename
        or lora.get("lora_name") != profile.lora.filename
        or lora.get("strength_model") != profile.lora.strength
        or sampler.get("steps") != profile.steps
        or sampler.get("shift_video") != profile.shift_video
        or sampler.get("shift_audio") != profile.shift_audio
        or sampler.get("sampler_name") != profile.sampler
        or sampler.get("scheduler") != profile.scheduler
        or output.get("images") != ["11", 0]
        or output.get("audio") != ["11", 1]
        or output.get("frame_rate") != float(profile.fps)
        or output.get("format") != "video/h264-mp4"
        or output.get("pix_fmt") != "yuv420p"
        or output.get("crf") != profile.output_crf
        or output.get("save_output") is not True
    ):
        raise _invalid("T8-native Turbo V2 workflow settings changed.")
    if profile.task_type == "I2VA" and binding.first_frame_node_id is None:
        raise _invalid("I2VA binding is missing its exact first-frame node.")
    if profile.task_type == "FL2VA" and (
        binding.first_frame_node_id is None or binding.last_frame_node_id is None
    ):
        raise _invalid("FL2VA binding is missing exact terminal nodes.")
    if profile.task_type in {"T2VA", "Ref2VA"} and (
        binding.first_frame_node_id is not None or binding.last_frame_node_id is not None
    ):
        raise _invalid("This V2 lane cannot bind first or last frames.")


def load_t8_native_turbo_execution_profile(
    path: str | Path, *, artifact_root: str | Path
) -> T8NativeTurboExecutionProfile:
    try:
        payload = json.loads(Path(path).read_bytes())
        if not isinstance(payload, dict):
            raise ValueError("profile payload must be a JSON object")
        profile = T8NativeTurboExecutionProfile.model_validate(payload)
    except (OSError, ValueError) as exc:
        raise _invalid("T8-native Turbo V2 profile is invalid.", str(exc)) from exc
    root = Path(artifact_root).resolve(strict=True)
    workflow_payload = _read_exact(
        root, profile.workflow_path, profile.workflow_sha256, "V2 workflow"
    )
    binding_payload = _read_exact(
        root, profile.binding_path, profile.binding_sha256, "V2 binding"
    )
    if not workflow_payload:
        raise _invalid("T8-native Turbo V2 workflow is empty.")
    workflow = load_workflow_template(root / profile.workflow_path)
    validate_native_turbo_workflow(
        profile, workflow, load_t8_native_turbo_binding(binding_payload)
    )
    return profile


__all__ = [
    "T8NativeTurboBinding",
    "T8NativeTurboComponent",
    "T8NativeTurboExecutionProfile",
    "T8NativeTurboLoraSeal",
    "T8NativeTurboNodeSchemaSeal",
    "T8NativeTurboRuntimeInspection",
    "load_t8_native_turbo_execution_profile",
    "load_t8_native_turbo_binding",
    "node_schema_seals",
    "validate_t8_native_turbo_lora",
    "validate_native_turbo_workflow",
]
