"""Sealed local-only T8 T2VA adapter for the Production Shot Router."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Callable, Literal, Protocol

import httpx
import yaml
from pydantic import Field, field_validator, model_validator

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import (
    _missing_required_node_inputs,
    validate_loopback_endpoint,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.local_video import (
    DurableLocalVideoSubmitPermit,
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.models import StrictModel
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.video import (
    BillingKind,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoProviderCapabilities,
    VideoTaskState,
)
from ai_video.production.video_compiler import (
    ProviderRequestCompilationResult,
    compile_provider_video_request,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
from ai_video.workflow_loader import load_workflow_template
from ai_video.workflow_renderer import _set_path, validate_api_workflow


_SHA256 = r"^[0-9a-f]{64}$"
_REVISION = r"^[0-9a-f]{40}$"
_VERSION = r"^[0-9]+(?:\.[0-9]+){1,3}$"
_MAX_DETERMINISTIC_SEED = (1 << 63) - 1
_PROVIDER_NAME = "comfy-local-h3-t8"
_CAPABILITY_ID = "minimax-h3-t8-t2va-quality-v1"
_PROVIDER_KIND = "minimax_h3_t8_t2va"
_MODEL_ID = "minimax-h3-t8-t2va-quality"
_COMPILER_ID = "comfy-local-h3-t8-video-compiler"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _provider_failure(
    code: ErrorCode, message: str, source: BaseException
) -> AiVideoError:
    if isinstance(source, AiVideoError):
        detail = f"{source.code.value}: {source.user_message}"
    else:
        detail = f"{type(source).__name__}: local response failed validation"
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=detail,
        retryable=False,
        cause=source,
    )


def _effective_seed(request: VideoGenerationRequest) -> int:
    if request.seed is not None:
        return request.seed
    return int(request.request_input_hash[:16], 16) & _MAX_DETERMINISTIC_SEED


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class T8ModelComponent(StrictModel):
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


class T8RuntimeInspection(StrictModel):
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


class T8ExecutionProfile(StrictModel):
    schema_version: Literal["1"]
    lane_id: Literal["minimax_h3_t8_t2va_quality_local"]
    adapter_contract_version: Literal["1"]
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
    components: tuple[T8ModelComponent, ...] = Field(min_length=4, max_length=4)
    lora_enabled: Literal[False]
    lora: None
    required_nodes: tuple[str, ...] = Field(min_length=1)
    required_t8_nodes: tuple[str, ...] = Field(min_length=1)
    t8_node_input_schema_sha256: str = Field(pattern=_SHA256)
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
    sampler: Literal["res_multistep"]
    scheduler: Literal["simple"]
    steps: Literal[20]
    shift_video: Literal[12.0]
    shift_audio: Literal[3.0]
    output_crf: Literal[17]
    output_node_id: Literal["11"]
    final_av_filename_suffix: Literal["-audio.mp4"]
    reject_video_only_sibling: Literal[True]
    remote_provider_enabled: Literal[False]
    cloud_fallback_enabled: Literal[False]
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
    def _sealed(self) -> "T8ExecutionProfile":
        if tuple(item.role for item in self.components) != (
            "diffusion",
            "text_encoder",
            "video_vae",
            "audio_vae",
        ):
            raise ValueError("T8 profile component roles are not canonical")
        if tuple(self.required_t8_nodes) != (
            "MiniMaxH3AudioConditioningT8",
            "MiniMaxH3DualClockSamplerT8",
            "MiniMaxH3AVDecodeT8",
        ):
            raise ValueError("T8 profile node inventory is not canonical")
        if not set(self.required_t8_nodes).issubset(self.required_nodes):
            raise ValueError("T8 node inventory must be required by the workflow")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if self.profile_content_hash != expected:
            raise ValueError("profile_content_hash does not match the profile")
        return self

    @classmethod
    def create(cls, **values: object) -> "T8ExecutionProfile":
        data = dict(values)
        data.pop("profile_content_hash", None)
        data["components"] = tuple(
            item
            if isinstance(item, T8ModelComponent)
            else T8ModelComponent.model_validate(item)
            for item in data["components"]
        )
        for key in (
            "required_launch_capabilities",
            "required_nodes",
            "required_t8_nodes",
            "loopback_endpoints",
        ):
            data[key] = tuple(data[key])
        for key in ("workflow_path", "binding_path"):
            data[key] = Path(data[key])
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        return cls.model_validate(data)


class T8Binding(StrictModel):
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
    output_node_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _aliases(self) -> "T8Binding":
        if self.length != self.frame_count:
            raise ValueError("length and frame_count must bind the same T8 input")
        return self


_NODE_CLASSES = {
    "1": "UNETLoader",
    "2": "CLIPLoader",
    "3": "VAELoader",
    "4": "VAELoader",
    "5": "MiniMaxH3AudioConditioningT8",
    "6": "MiniMaxH3DualClockSamplerT8",
    "7": "RandomNoise",
    "8": "BasicGuider",
    "9": "SamplerCustomAdvanced",
    "10": "MiniMaxH3AVDecodeT8",
    "11": "VHS_VideoCombine",
}


def t8_node_input_schema_sha256(
    object_info: dict[str, Any],
    required_t8_nodes: tuple[str, ...],
    *,
    frozen_file_chooser_inventory: dict[
        str, dict[str, tuple[str, ...]]
    ] | None = None,
) -> str:
    """Hash the exact T8 node input/output schema without executing a workflow."""

    frozen_inventory = frozen_file_chooser_inventory or {}
    if not set(frozen_inventory).issubset(required_t8_nodes):
        raise _invalid("A frozen T8 file chooser references an unsealed node.")
    projection: dict[str, object] = {}
    for node_name in required_t8_nodes:
        node = object_info.get(node_name)
        if not isinstance(node, dict):
            raise _invalid("ComfyUI is missing a sealed T8 node.", node_name)
        input_schema = json.loads(json.dumps(node.get("input")))
        input_order = node.get("input_order")
        output_name = node.get("output_name")
        if (
            not isinstance(input_schema, dict)
            or not isinstance(input_order, dict)
            or not isinstance(output_name, list)
        ):
            raise _invalid("A sealed T8 node schema is malformed.", node_name)
        required = input_schema.get("required")
        for field, frozen_choices in frozen_inventory.get(node_name, {}).items():
            if (
                not isinstance(required, dict)
                or not isinstance(required.get(field), list)
                or not required[field]
                or not isinstance(required[field][0], list)
                or not required[field][0]
                or not all(
                    isinstance(item, str) and item for item in required[field][0]
                )
                or len(set(required[field][0])) != len(required[field][0])
                or not frozen_choices
                or not all(isinstance(item, str) and item for item in frozen_choices)
                or len(set(frozen_choices)) != len(frozen_choices)
            ):
                raise _invalid(
                    "A sealed T8 runtime file chooser is malformed.",
                    f"{node_name}.{field}",
                )
            required[field][0] = list(frozen_choices)
        projection[node_name] = {
            "input": input_schema,
            "input_order": input_order,
            "output_name": output_name,
        }
    return canonical_sha256(
        {"schema": "minimax-h3-t8-node-inputs/1", "nodes": projection}
    )


def load_t8_video_execution_profile(
    path: str | Path, *, artifact_root: str | Path
) -> T8ExecutionProfile:
    try:
        payload = json.loads(Path(path).read_bytes())
        if not isinstance(payload, dict):
            raise ValueError("profile payload must be a JSON object")
        profile = T8ExecutionProfile.model_validate(payload)
    except (OSError, ValueError) as exc:
        raise _invalid("T8 video execution profile is invalid.", str(exc)) from exc
    root = Path(artifact_root).resolve(strict=True)
    _read_exact(root, profile.workflow_path, profile.workflow_sha256, "T8 workflow")
    _read_exact(root, profile.binding_path, profile.binding_sha256, "T8 binding")
    return profile


def _load_binding(payload: bytes) -> T8Binding:
    try:
        return T8Binding.model_validate(yaml.safe_load(payload))
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise _invalid("Local T8 binding is invalid.", str(exc)) from exc


def _validate_workflow(
    profile: T8ExecutionProfile,
    workflow: dict[str, Any],
    binding: T8Binding,
) -> None:
    classes = {
        node_id: node.get("class_type")
        for node_id, node in workflow.items()
        if isinstance(node, dict)
    }
    if classes != _NODE_CLASSES:
        raise _invalid("Local T8 workflow topology is not sealed.")
    components = {
        ("diffusion", workflow["1"]["inputs"].get("unet_name")),
        ("text_encoder", workflow["2"]["inputs"].get("clip_name")),
        ("video_vae", workflow["3"]["inputs"].get("vae_name")),
        ("audio_vae", workflow["4"]["inputs"].get("vae_name")),
    }
    if components != {(item.role, item.filename) for item in profile.components}:
        raise _invalid("Local T8 workflow model loaders do not match the profile.")
    expected_binding = {
        "prompt": ("5", "inputs", "prompt"),
        "seed": ("7", "inputs", "noise_seed"),
        "width": ("5", "inputs", "width"),
        "height": ("5", "inputs", "height"),
        "length": ("5", "inputs", "length"),
        "steps": ("6", "inputs", "steps"),
        "sampler": ("6", "inputs", "sampler_name"),
        "scheduler": ("6", "inputs", "scheduler"),
        "output_prefix": ("11", "inputs", "filename_prefix"),
    }
    conditioning = workflow["5"]["inputs"]
    sampling = workflow["6"]["inputs"]
    output = workflow["11"]["inputs"]
    if (
        any(getattr(binding, key) != value for key, value in expected_binding.items())
        or binding.output_node_id != profile.output_node_id
        or conditioning.get("task_type") != "T2VA"
        or conditioning.get("audio_mode") != "native"
        or conditioning.get("width") != profile.width
        or conditioning.get("height") != profile.height
        or conditioning.get("length") != profile.frame_count
        or any(
            name in conditioning
            for name in (
                "drive_audio",
                "final_audio",
                "first_frame",
                "last_frame",
                "ref_images",
                "ref_videos",
                "ref_video_audios",
                "ref_audios",
            )
        )
        or sampling.get("steps") != profile.steps
        or sampling.get("sampler_name") != profile.sampler
        or sampling.get("scheduler") != profile.scheduler
        or sampling.get("shift_video") != profile.shift_video
        or sampling.get("shift_audio") != profile.shift_audio
        or output.get("images") != ["10", 0]
        or output.get("audio") != ["10", 1]
        or output.get("frame_rate") != float(profile.fps)
        or output.get("format") != "video/h264-mp4"
        or output.get("pix_fmt") != "yuv420p"
        or output.get("crf") != profile.output_crf
        or output.get("save_output") is not True
    ):
        raise _invalid("Local T8 workflow bindings or AV settings changed.")


def render_t8_workflow(
    *,
    template: dict[str, Any],
    binding: T8Binding,
    request: ResolvedVideoGenerationRequest,
    output_prefix: str,
    profile: T8ExecutionProfile,
) -> dict[str, Any]:
    validate_api_workflow(template)
    output = request.effective_output
    if not isinstance(output, VideoFlexibleOutputRequirement):
        raise _invalid("Local T8 requires the exact frame-count output contract.")
    rendered = json.loads(json.dumps(template))
    values = (
        (binding.prompt, request.prompt_text, "prompt"),
        (binding.seed, request.effective_seed, "seed"),
        (binding.width, output.width, "width"),
        (binding.height, output.height, "height"),
        (binding.length, output.frame_count, "length"),
        (binding.steps, profile.steps, "steps"),
        (binding.sampler, profile.sampler, "sampler"),
        (binding.scheduler, profile.scheduler, "scheduler"),
        (binding.output_prefix, output_prefix, "output_prefix"),
    )
    for path, value, label in values:
        _set_path(rendered, list(path), value, label)
    return rendered


class T8VideoTransport(Protocol):
    def get_object_info(self) -> dict[str, Any]: ...
    def submit_prompt(self, workflow: dict[str, Any]) -> str: ...
    def poll_job(
        self, prompt_id: str, *, poll_interval_seconds: float, timeout_seconds: float
    ) -> Any: ...
    def fetch_artifact_bytes(
        self, *, filename: str, subfolder: str, type_: str
    ) -> bytes: ...


_COMPONENT_DIRS = {
    "diffusion": Path("models/diffusion_models"),
    "text_encoder": Path("models/text_encoders"),
    "video_vae": Path("models/vae"),
    "audio_vae": Path("models/vae"),
}


def _final_av_artifact(
    history: dict[str, Any], profile: T8ExecutionProfile
) -> tuple[str, str, str]:
    outputs = history.get("outputs")
    selected = (
        outputs.get(profile.output_node_id) if isinstance(outputs, dict) else None
    )
    candidates: list[dict[str, object]] = []
    if isinstance(selected, dict):
        for value in selected.values():
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))
    mp4 = tuple(
        item
        for item in candidates
        if str(item.get("filename", "")).lower().endswith(".mp4")
    )
    final_av = tuple(
        item
        for item in mp4
        if str(item.get("filename", ""))
        .lower()
        .endswith(profile.final_av_filename_suffix)
    )
    if len(final_av) != 1:
        raise _invalid("T8 history must contain exactly one final *-audio.mp4 output.")
    item = final_av[0]
    filename = str(item.get("filename", ""))
    subfolder = str(item.get("subfolder", ""))
    type_ = str(item.get("type", "output"))
    if any(":" in value for value in (filename, subfolder, type_)):
        raise _invalid("T8 MP4 locator contains unsupported characters.")
    return filename, subfolder, type_


class ComfyUIT8VideoProvider:
    def __init__(
        self,
        profile: T8ExecutionProfile,
        *,
        artifact_root: str | Path,
        comfy_root: str | Path,
        runtime_inspector: Callable[[], T8RuntimeInspection],
        endpoint: str = "http://127.0.0.1:8188",
        transport: T8VideoTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        poll_interval_seconds: float = 0.25,
        timeout_seconds: float = 3_600.0,
    ) -> None:
        self.profile = profile
        self._root = Path(artifact_root).resolve(strict=True)
        self._comfy_root = Path(comfy_root).resolve(strict=True)
        self._endpoint = validate_loopback_endpoint(endpoint)
        if self._endpoint not in profile.loopback_endpoints:
            raise _invalid("Selected endpoint is not allowed by the T8 profile.")
        if transport is None:
            transport = ComfyClient(
                self._endpoint,
                http_client=httpx.Client(
                    timeout=30, trust_env=False, follow_redirects=False
                ),
            )
        elif isinstance(transport, ComfyClient) and (
            validate_loopback_endpoint(transport.base_url) != self._endpoint
        ):
            raise _invalid("Injected ComfyUI endpoint does not match the T8 profile.")
        self._transport = transport
        self._runtime_inspector = runtime_inspector
        self._clock = clock or (lambda: datetime.now(UTC))
        workflow_payload = _read_exact(
            self._root, profile.workflow_path, profile.workflow_sha256, "T8 workflow"
        )
        binding_payload = _read_exact(
            self._root, profile.binding_path, profile.binding_sha256, "T8 binding"
        )
        if not workflow_payload:
            raise _invalid("Local T8 workflow is empty.")
        self._workflow = load_workflow_template(self._root / profile.workflow_path)
        self._binding = _load_binding(binding_payload)
        _validate_workflow(profile, self._workflow, self._binding)
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._preflighted: set[str] = set()

    def capabilities(self) -> VideoProviderCapabilities:
        output = VideoOutputCapability(
            min_duration_seconds=self.profile.frame_count // self.profile.fps,
            max_duration_seconds=(self.profile.frame_count + self.profile.fps - 1)
            // self.profile.fps,
            provider_selected_duration=False,
            timing_modes=("frame_count",),
            frame_count_min=self.profile.frame_count,
            frame_count_max=self.profile.frame_count,
            frame_count_step=17,
            frame_count_remainder=5,
            dimension_modes=("exact",),
            min_width=self.profile.width,
            max_width=self.profile.width,
            min_height=self.profile.height,
            max_height=self.profile.height,
            dimension_multiple=32,
            resolution_labels=("h3_t8_native",),
            ratios=("16:9",),
            fps_values=(self.profile.fps,),
            containers=(self.profile.output_container,),
            native_audio_options=(True,),
        )
        return VideoProviderCapabilities.create(
            provider_name=_PROVIDER_NAME,
            variants=(
                VideoCapabilityVariant(
                    capability_id=_CAPABILITY_ID,
                    provider_kind=_PROVIDER_KIND,
                    model_id=_MODEL_ID,
                    profile_version="v1",
                    execution_kind=VideoExecutionKind.LOCAL,
                    billing_kind=BillingKind.LOCAL_UNMETERED,
                    mode=VideoGenerationMode.TEXT_TO_VIDEO,
                    output_capability=output,
                    allowed_image_roles=(),
                    required_first_frame=False,
                    max_reference_count=0,
                    allowed_image_mime_types=(),
                    max_image_bytes=1,
                    min_image_width=1,
                    min_image_height=1,
                    negative_prompt_supported=False,
                    seed_supported=True,
                    fps_supported=True,
                    idempotent_submit=False,
                    lookup_supported=False,
                ),
            ),
        )

    def _validate_resolved_identity(
        self, request: ResolvedVideoGenerationRequest
    ) -> None:
        capability = self.capabilities().variants[0]
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != capability.provider_kind
            or request.model_id != capability.model_id
            or request.provider_profile.profile_version != capability.profile_version
            or request.provider_profile.profile_sha256
            != self.profile.profile_content_hash
            or request.capability_id != capability.capability_id
            or request.execution_kind is not capability.execution_kind
            or request.billing_kind is not capability.billing_kind
            or request.mode is not capability.mode
        ):
            raise _invalid(
                "Resolved request is not owned by the sealed T8 quality capability."
            )

    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
    ) -> ProviderRequestCompilationResult:
        return compile_provider_video_request(
            provider_bound=provider_bound,
            requirement=requirement,
            compiler_id=_COMPILER_ID,
            compiler_version="1",
            capabilities=self.capabilities(),
        )

    def resolve(
        self, request: VideoGenerationRequest
    ) -> ResolvedVideoGenerationRequest:
        matching = tuple(
            item
            for item in self.capabilities().variants
            if item.provider_kind == request.provider_kind
            and item.model_id == request.model_id
            and item.profile_version == request.provider_profile.profile_version
            and item.mode is request.mode
        )
        output = request.output_requirement
        if (
            len(matching) != 1
            or request.provider_name != _PROVIDER_NAME
            or request.provider_profile.profile_sha256
            != self.profile.profile_content_hash
            or not isinstance(output, VideoFlexibleOutputRequirement)
            or output.timing_mode != "frame_count"
            or output.frame_count != self.profile.frame_count
            or output.dimension_mode != "exact"
            or output.width != self.profile.width
            or output.height != self.profile.height
            or output.resolution_label != "h3_t8_native"
            or output.ratio != "16:9"
            or output.fps != self.profile.fps
            or output.container != self.profile.output_container
            or output.mime_type != self.profile.output_mime_type
            or output.native_audio is not True
            or request.image_bindings
            or request.media_bindings
            or request.negative_prompt_text
        ):
            raise _invalid("Video request is outside the sealed local T8 profile.")
        return ResolvedVideoGenerationRequest.create(
            request=request,
            capability=matching[0],
            effective_output=output,
            effective_seed=_effective_seed(request),
            effective_negative_prompt_text=request.negative_prompt_text,
        )

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview:
        self._validate_resolved_identity(request)
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def preflight(self, request: ResolvedVideoGenerationRequest) -> None:
        self._validate_resolved_identity(request)
        runtime = self._runtime_inspector()
        if (
            runtime.comfyui_commit != self.profile.comfyui_commit
            or runtime.t8_commit != self.profile.t8_commit
            or runtime.t8_version != self.profile.t8_version
            or runtime.videohelpersuite_commit != self.profile.videohelpersuite_commit
            or runtime.sageattention_version != self.profile.sageattention_version
            or not set(self.profile.required_launch_capabilities).issubset(
                runtime.launch_capabilities
            )
        ):
            raise _invalid("Local T8 runtime does not match the sealed profile.")
        for component in self.profile.components:
            path = (
                self._comfy_root / _COMPONENT_DIRS[component.role] / component.filename
            )
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(self._comfy_root)
                stat = resolved.stat()
            except (OSError, RuntimeError, ValueError) as exc:
                raise _invalid(
                    "A sealed T8 component could not be reopened.", str(exc)
                ) from exc
            if (
                stat.st_size != component.size_bytes
                or _sha256_file(resolved) != component.sha256
            ):
                raise _invalid(
                    "A sealed T8 component hash is invalid.", component.filename
                )
        object_info = self._transport.get_object_info()
        missing = sorted(
            item for item in self.profile.required_nodes if item not in object_info
        )
        if missing:
            raise _invalid("ComfyUI is missing required T8 nodes.", ", ".join(missing))
        required_inputs = _missing_required_node_inputs(self._workflow, object_info)
        if required_inputs:
            raise _invalid(
                "ComfyUI T8 node inputs changed.", ", ".join(required_inputs)
            )
        if (
            t8_node_input_schema_sha256(object_info, self.profile.required_t8_nodes)
            != self.profile.t8_node_input_schema_sha256
        ):
            raise _invalid("ComfyUI T8 input schema does not match the sealed profile.")
        self._preflighted.add(request.resolved_generation_hash)

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult:
        try:
            self._validate_resolved_identity(request)
            if request.resolved_generation_hash not in self._preflighted:
                raise _invalid("Local T8 request has not passed exact preflight.")
            self._preflighted.remove(request.resolved_generation_hash)
            if (
                preview != self.preview(request)
                or intent.request_fingerprint != request.resolved_generation_hash
            ):
                raise _invalid("Local T8 preview or intent identity is invalid.")
            workflow = render_t8_workflow(
                template=self._workflow,
                binding=self._binding,
                request=request,
                output_prefix=(
                    f"MiniMaxH3/ai_video_h3_t8_{request.resolved_generation_hash[:16]}"
                ),
                profile=self.profile,
            )
            if not permit._consume_local_video_submit_permit(
                intent_fingerprint=intent.intent_fingerprint,
                request_fingerprint=request.resolved_generation_hash,
            ):
                raise _invalid("Local T8 submit requires the exact durable permit.")
        except AiVideoError as exc:
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Local T8 pre-submit validation failed before any prompt effect.",
                exc,
            ) from exc
        try:
            prompt_id = self._transport.submit_prompt(workflow)
            return LocalVideoSubmitResult.create(
                resolved=request,
                provider_request_id=prompt_id,
                submitted_at=self._clock(),
            )
        except Exception as exc:
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local T8 prompt submission outcome is unknown; do not resubmit blindly.",
                exc,
            ) from exc

    def get_local_status(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
    ) -> LocalVideoTaskObservation:
        job = self._transport.poll_job(
            submission.provider_request_id,
            poll_interval_seconds=self._poll_interval_seconds,
            timeout_seconds=self._timeout_seconds,
        )
        if job.status is JobStatus.FAILED:
            return LocalVideoTaskObservation.create(
                submission=submission,
                state=VideoTaskState.FAILED,
                observed_at=self._clock(),
            )
        if job.status is not JobStatus.COMPLETED or not isinstance(job.history, dict):
            source = job.error or AiVideoError(
                code=ErrorCode.COMFY_JOB_TIMEOUT,
                user_message="ComfyUI did not return a terminal T8 job result.",
                retryable=False,
            )
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local T8 job outcome is unknown; explicit recovery is required.",
                source,
            )
        filename, subfolder, type_ = _final_av_artifact(job.history, self.profile)
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=VideoTaskState.SUCCEEDED,
            progress_milli=1000,
            provider_file_id=f"{subfolder}:{filename}:{type_}",
            observed_at=self._clock(),
        )

    def fetch_local(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
        observation: LocalVideoTaskObservation,
        sink: BinaryIO,
    ) -> LocalVideoFetchReceipt:
        if (
            observation.state is not VideoTaskState.SUCCEEDED
            or observation.provider_file_id is None
        ):
            raise _invalid("Local T8 fetch requires a succeeded observation.")
        try:
            subfolder, filename, type_ = observation.provider_file_id.split(":", 2)
        except ValueError as exc:
            raise _invalid("Local T8 output locator is invalid.", str(exc)) from exc
        if not filename.lower().endswith(self.profile.final_av_filename_suffix):
            raise _invalid("Local T8 fetch requires the final *-audio.mp4 artifact.")
        payload = self._transport.fetch_artifact_bytes(
            filename=filename, subfolder=subfolder, type_=type_
        )
        if not payload or b"ftyp" not in payload[:64]:
            raise _invalid("Local T8 returned non-MP4 bytes.")
        sink.write(payload)
        return LocalVideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=len(payload),
            artifact_sha256=hashlib.sha256(payload).hexdigest(),
            fetched_at=self._clock(),
        )


__all__ = [
    "ComfyUIT8VideoProvider",
    "T8Binding",
    "T8ExecutionProfile",
    "T8ModelComponent",
    "T8RuntimeInspection",
    "T8VideoTransport",
    "load_t8_video_execution_profile",
    "render_t8_workflow",
    "t8_node_input_schema_sha256",
]
