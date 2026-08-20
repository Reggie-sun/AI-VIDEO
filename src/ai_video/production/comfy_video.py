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
    _git_head,
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
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)
from ai_video.workflow_loader import load_workflow_template
from ai_video.workflow_renderer import _set_path, validate_api_workflow


_SHA256 = r"^[0-9a-f]{64}$"
_REVISION = r"^[0-9a-f]{40}$"


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


class LocalVideoModelComponent(StrictModel):
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


class LocalVideoExecutionProfile(StrictModel):
    schema_version: Literal["1"]
    lane_id: Literal["minimax_h3_fl2va_local"]
    adapter_contract_version: Literal["1"]
    upstream_repository: str = Field(min_length=1)
    upstream_commit: str = Field(pattern=_REVISION)
    upstream_path: Path
    upstream_url: str = Field(min_length=1)
    upstream_sha256: str = Field(pattern=_SHA256)
    upstream_license_id: Literal["MIT"]
    derived_modifications: tuple[str, ...] = Field(min_length=1)
    model_repository_id: Literal["Comfy-Org/MiniMax-H3"]
    model_repository_revision: str = Field(pattern=_REVISION)
    components: tuple[LocalVideoModelComponent, ...] = Field(min_length=4)
    comfyui_commit: str = Field(pattern=_REVISION)
    required_nodes: tuple[str, ...] = Field(min_length=1)
    workflow_path: Path
    workflow_sha256: str = Field(pattern=_SHA256)
    binding_path: Path
    binding_sha256: str = Field(pattern=_SHA256)
    loopback_endpoints: tuple[str, ...] = Field(min_length=1)
    min_width: int = Field(strict=True, gt=0)
    max_width: int = Field(strict=True, gt=0)
    min_height: int = Field(strict=True, gt=0)
    max_height: int = Field(strict=True, gt=0)
    dimension_multiple: int = Field(strict=True, gt=0)
    fps: Literal[24]
    min_frame_count: int = Field(strict=True, gt=0)
    max_frame_count: int = Field(strict=True, gt=0)
    frame_grid_step: int = Field(strict=True, gt=0)
    frame_grid_remainder: int = Field(strict=True, ge=0)
    native_audio_required: Literal[True]
    output_container: Literal["mp4"]
    output_mime_type: Literal["video/mp4"]
    sampler: Literal["res_multistep"]
    scheduler: Literal["simple"]
    steps: int = Field(strict=True, gt=0)
    output_node_id: str = Field(min_length=1)
    optional_last_frame_supported: bool
    optional_lora_enabled: Literal[False]
    remote_refiner_enabled: Literal[False]
    cloud_fallback_enabled: Literal[False]
    profile_content_hash: str = Field(pattern=_SHA256)

    @field_validator("upstream_path", "workflow_path", "binding_path")
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
    def _sealed(self) -> "LocalVideoExecutionProfile":
        roles = tuple(item.role for item in self.components)
        if roles != ("diffusion", "text_encoder", "video_vae", "audio_vae"):
            raise ValueError("H3 profile component roles are not canonical")
        if (
            self.min_width > self.max_width
            or self.min_height > self.max_height
            or self.min_frame_count > self.max_frame_count
            or self.min_frame_count % self.frame_grid_step
            != self.frame_grid_remainder
            or self.max_frame_count % self.frame_grid_step
            != self.frame_grid_remainder
        ):
            raise ValueError("H3 profile bounds are invalid")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if self.profile_content_hash != expected:
            raise ValueError("profile_content_hash does not match the profile")
        return self

    @classmethod
    def create(cls, **values: object) -> "LocalVideoExecutionProfile":
        data = dict(values)
        data.pop("profile_content_hash", None)
        data["components"] = tuple(
            item
            if isinstance(item, LocalVideoModelComponent)
            else LocalVideoModelComponent.model_validate(item)
            for item in data["components"]
        )
        for key in (
            "derived_modifications",
            "required_nodes",
            "loopback_endpoints",
        ):
            data[key] = tuple(data[key])
        for key in ("upstream_path", "workflow_path", "binding_path"):
            data[key] = Path(data[key])
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        return cls.model_validate(data)


class LocalVideoQualityExecutionProfile(LocalVideoExecutionProfile):
    schema_version: Literal["2"]
    lane_id: Literal["minimax_h3_fl2va_quality_local"]
    output_codec: Literal["h264"]
    output_encoding: Literal["re-encode"]
    output_crf: int = Field(strict=True, ge=16, le=18)


class LocalVideoBinding(StrictModel):
    prompt: tuple[str | int, ...]
    first_frame: tuple[str | int, ...]
    last_frame: tuple[str | int, ...]
    last_frame_node_id: str
    last_frame_target: tuple[str | int, ...]
    seed: tuple[str | int, ...]
    width: tuple[str | int, ...]
    height: tuple[str | int, ...]
    length: tuple[str | int, ...]
    frame_count: tuple[str | int, ...]
    steps: tuple[str | int, ...]
    sampler: tuple[str | int, ...]
    output_prefix: tuple[str | int, ...]
    output_node_id: str

    @model_validator(mode="after")
    def _aliases(self) -> "LocalVideoBinding":
        if self.length != self.frame_count:
            raise ValueError("length and frame_count must bind the same H3 input")
        return self


_NODE_CLASSES = {
    "1": "UNETLoader",
    "2": "CLIPLoader",
    "3": "VAELoader",
    "4": "VAELoader",
    "5": "MiniMaxH3ImageToVideo",
    "6": "RandomNoise",
    "7": "BasicGuider",
    "8": "KSamplerSelect",
    "9": "BasicScheduler",
    "10": "SamplerCustomAdvanced",
    "11": "VAEDecode",
    "12": "VAEDecodeAudio",
    "13": "CreateVideo",
    "14": "SaveVideo",
    "15": "LoadImage",
    "16": "LoadImage",
}


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


def load_local_video_execution_profile(
    path: str | Path, *, artifact_root: str | Path
) -> LocalVideoExecutionProfile | LocalVideoQualityExecutionProfile:
    try:
        payload = json.loads(Path(path).read_bytes())
        if not isinstance(payload, dict):
            raise ValueError("profile payload must be a JSON object")
        profile_type = (
            LocalVideoQualityExecutionProfile
            if payload.get("schema_version") == "2"
            else LocalVideoExecutionProfile
        )
        profile = profile_type.model_validate(payload)
    except (OSError, ValueError) as exc:
        raise _invalid("Local video execution profile is invalid.", str(exc)) from exc
    root = Path(artifact_root).resolve(strict=True)
    _read_exact(root, profile.workflow_path, profile.workflow_sha256, "H3 workflow")
    _read_exact(root, profile.binding_path, profile.binding_sha256, "H3 binding")
    return profile


def _load_binding(payload: bytes) -> LocalVideoBinding:
    try:
        return LocalVideoBinding.model_validate(yaml.safe_load(payload))
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise _invalid("Local H3 binding is invalid.", str(exc)) from exc


def _validate_workflow(
    profile: LocalVideoExecutionProfile,
    workflow: dict[str, Any],
    binding: LocalVideoBinding,
) -> None:
    classes = {
        node_id: node.get("class_type")
        for node_id, node in workflow.items()
        if isinstance(node, dict)
    }
    if classes != _NODE_CLASSES:
        raise _invalid("Local H3 workflow topology is not sealed.")
    components = {
        ("diffusion", workflow["1"]["inputs"].get("unet_name")),
        ("text_encoder", workflow["2"]["inputs"].get("clip_name")),
        ("video_vae", workflow["3"]["inputs"].get("vae_name")),
        ("audio_vae", workflow["4"]["inputs"].get("vae_name")),
    }
    if components != {(item.role, item.filename) for item in profile.components}:
        raise _invalid("Local H3 workflow model loaders do not match the profile.")
    expected_binding = {
        "prompt": ("5", "inputs", "prompt"),
        "first_frame": ("15", "inputs", "image"),
        "last_frame": ("16", "inputs", "image"),
        "last_frame_target": ("5", "inputs", "last_frame"),
        "seed": ("6", "inputs", "noise_seed"),
        "width": ("5", "inputs", "width"),
        "height": ("5", "inputs", "height"),
        "length": ("5", "inputs", "length"),
        "steps": ("9", "inputs", "steps"),
        "sampler": ("8", "inputs", "sampler_name"),
        "output_prefix": ("14", "inputs", "filename_prefix"),
    }
    if isinstance(profile, LocalVideoQualityExecutionProfile):
        expected_encoder_inputs: dict[str, object] = {
            "codec": profile.output_codec,
            "codec.encoding": profile.output_encoding,
            "codec.encoding.crf": profile.output_crf,
        }
    else:
        expected_encoder_inputs = {"codec": "auto"}
    if (
        any(getattr(binding, key) != value for key, value in expected_binding.items())
        or binding.output_node_id != profile.output_node_id
        or workflow["8"]["inputs"].get("sampler_name") != profile.sampler
        or workflow["9"]["inputs"].get("scheduler") != profile.scheduler
        or workflow["9"]["inputs"].get("steps") != profile.steps
        or workflow["13"]["inputs"].get("fps") != float(profile.fps)
        or workflow["14"]["inputs"].get("format") != profile.output_container
        or any(
            workflow["14"]["inputs"].get(key) != value
            for key, value in expected_encoder_inputs.items()
        )
    ):
        raise _invalid("Local H3 workflow bindings or native settings changed.")


def render_h3_workflow(
    *,
    template: dict[str, Any],
    binding: LocalVideoBinding,
    request: ResolvedVideoGenerationRequest,
    first_frame_name: str,
    last_frame_name: str | None,
    output_prefix: str,
    steps: int,
    sampler: str,
) -> dict[str, Any]:
    validate_api_workflow(template)
    output = request.effective_output
    if not isinstance(output, VideoFlexibleOutputRequirement):
        raise _invalid("Local H3 requires the frame-count output contract.")
    rendered = json.loads(json.dumps(template))
    values = (
        (binding.prompt, request.prompt_text, "prompt"),
        (binding.first_frame, first_frame_name, "first_frame"),
        (binding.seed, request.effective_seed, "seed"),
        (binding.width, output.width, "width"),
        (binding.height, output.height, "height"),
        (binding.length, output.frame_count, "length"),
        (binding.steps, steps, "steps"),
        (binding.sampler, sampler, "sampler"),
        (binding.output_prefix, output_prefix, "output_prefix"),
    )
    for path, value, label in values:
        _set_path(rendered, list(path), value, label)
    if last_frame_name is None:
        rendered.pop(binding.last_frame_node_id, None)
        target = rendered["5"]["inputs"]
        target.pop("last_frame", None)
    else:
        _set_path(rendered, list(binding.last_frame), last_frame_name, "last_frame")
        _set_path(
            rendered,
            list(binding.last_frame_target),
            [binding.last_frame_node_id, 0],
            "last_frame_target",
        )
    return rendered


class LocalVideoTransport(Protocol):
    def get_object_info(self) -> dict[str, Any]: ...
    def upload_image(self, path: str | Path) -> str: ...
    def submit_prompt(self, workflow: dict[str, Any]) -> str: ...
    def poll_job(
        self, prompt_id: str, *, poll_interval_seconds: float, timeout_seconds: float
    ) -> Any: ...
    def fetch_artifact_bytes(
        self, *, filename: str, subfolder: str, type_: str
    ) -> bytes: ...


ImageResolver = Callable[[str, str], Path]


_COMPONENT_DIRS = {
    "diffusion": Path("models/diffusion_models"),
    "text_encoder": Path("models/text_encoders"),
    "video_vae": Path("models/vae"),
    "audio_vae": Path("models/vae"),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _video_artifact(history: dict[str, Any], output_node_id: str) -> tuple[str, str, str]:
    outputs = history.get("outputs")
    selected = outputs.get(output_node_id) if isinstance(outputs, dict) else None
    candidates = []
    if isinstance(selected, dict):
        for value in selected.values():
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))
    mp4 = [item for item in candidates if str(item.get("filename", "")).lower().endswith(".mp4")]
    if len(mp4) != 1:
        raise _invalid("ComfyUI history must contain one configured MP4 output.")
    item = mp4[0]
    filename = str(item.get("filename", ""))
    subfolder = str(item.get("subfolder", ""))
    type_ = str(item.get("type", "output"))
    if any(":" in value for value in (filename, subfolder, type_)):
        raise _invalid("ComfyUI MP4 locator contains unsupported characters.")
    return filename, subfolder, type_


class ComfyUIVideoProvider:
    def __init__(
        self,
        profile: LocalVideoExecutionProfile,
        *,
        artifact_root: str | Path,
        comfy_root: str | Path,
        image_resolver: ImageResolver,
        image_root: str | Path,
        endpoint: str = "http://127.0.0.1:8188",
        transport: LocalVideoTransport | None = None,
        commit_resolver: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
        poll_interval_seconds: float = 0.25,
        timeout_seconds: float = 3_600.0,
    ) -> None:
        self.profile = profile
        self._root = Path(artifact_root).resolve(strict=True)
        self._comfy_root = Path(comfy_root).resolve(strict=True)
        self._image_root = Path(image_root).resolve(strict=True)
        self._image_resolver = image_resolver
        self._endpoint = validate_loopback_endpoint(endpoint)
        if self._endpoint not in profile.loopback_endpoints:
            raise _invalid("Selected endpoint is not allowed by the H3 profile.")
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
            raise _invalid("Injected ComfyUI endpoint does not match the profile.")
        self._transport = transport
        self._commit_resolver = commit_resolver or (
            lambda: _git_head(self._comfy_root)
        )
        self._clock = clock or (lambda: datetime.now(UTC))
        workflow_payload = _read_exact(
            self._root, profile.workflow_path, profile.workflow_sha256, "H3 workflow"
        )
        binding_payload = _read_exact(
            self._root, profile.binding_path, profile.binding_sha256, "H3 binding"
        )
        if not workflow_payload:
            raise _invalid("Local H3 workflow is empty.")
        self._workflow = load_workflow_template(self._root / profile.workflow_path)
        self._binding = _load_binding(binding_payload)
        _validate_workflow(profile, self._workflow, self._binding)
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._preflighted: set[str] = set()

    def capabilities(self) -> VideoProviderCapabilities:
        output = VideoOutputCapability(
            min_duration_seconds=self.profile.min_frame_count // self.profile.fps,
            max_duration_seconds=(
                self.profile.max_frame_count + self.profile.fps - 1
            )
            // self.profile.fps,
            provider_selected_duration=False,
            timing_modes=("frame_count",),
            frame_count_min=self.profile.min_frame_count,
            frame_count_max=self.profile.max_frame_count,
            frame_count_step=self.profile.frame_grid_step,
            frame_count_remainder=self.profile.frame_grid_remainder,
            dimension_modes=("exact",),
            resolution_labels=("h3_native",),
            ratios=("adaptive",),
            fps_values=(self.profile.fps,),
            containers=(self.profile.output_container,),
            native_audio_options=(True,),
        )
        return VideoProviderCapabilities.create(
            provider_name="comfy-local-h3",
            variants=(
                VideoCapabilityVariant(
                    capability_id="minimax-h3-fl2va-local-v1",
                    provider_kind="minimax_h3_fl2va",
                    model_id="minimax-h3-fl2va",
                    profile_version="v1",
                    execution_kind=VideoExecutionKind.LOCAL,
                    billing_kind=BillingKind.LOCAL_UNMETERED,
                    mode=VideoGenerationMode.IMAGE_TO_VIDEO,
                    output_capability=output,
                    allowed_image_roles=("first_frame", "last_frame"),
                    required_first_frame=True,
                    max_reference_count=0,
                    allowed_image_mime_types=("image/png",),
                    max_image_bytes=104_857_600,
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

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        variants = self.capabilities().variants
        matching = tuple(
            item
            for item in variants
            if item.provider_kind == request.provider_kind
            and item.model_id == request.model_id
            and item.profile_version == request.provider_profile.profile_version
            and item.mode is request.mode
        )
        output = request.output_requirement
        if (
            len(matching) != 1
            or request.provider_name != "comfy-local-h3"
            or request.provider_profile.profile_sha256
            != self.profile.profile_content_hash
            or not isinstance(output, VideoFlexibleOutputRequirement)
            or output.width is None
            or output.height is None
            or not self.profile.min_width <= output.width <= self.profile.max_width
            or not self.profile.min_height <= output.height <= self.profile.max_height
            or output.width % self.profile.dimension_multiple
            or output.height % self.profile.dimension_multiple
            or request.negative_prompt_text
        ):
            raise _invalid("Video request is outside the sealed local H3 profile.")
        return ResolvedVideoGenerationRequest.create(
            request=request,
            capability=matching[0],
            effective_output=output,
            effective_seed=request.seed,
            effective_negative_prompt_text=request.negative_prompt_text,
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

    def preflight(self, request: ResolvedVideoGenerationRequest) -> None:
        if self._commit_resolver() != self.profile.comfyui_commit:
            raise _invalid("ComfyUI commit does not match the sealed H3 profile.")
        for component in self.profile.components:
            path = self._comfy_root / _COMPONENT_DIRS[component.role] / component.filename
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(self._comfy_root)
                stat = resolved.stat()
            except (OSError, RuntimeError, ValueError) as exc:
                raise _invalid("A sealed H3 component could not be reopened.", str(exc)) from exc
            if stat.st_size != component.size_bytes or _sha256_file(resolved) != component.sha256:
                raise _invalid("A sealed H3 component hash is invalid.", component.filename)
        object_info = self._transport.get_object_info()
        missing = sorted(item for item in self.profile.required_nodes if item not in object_info)
        if missing:
            raise _invalid("ComfyUI is missing required native H3 nodes.", ", ".join(missing))
        required_inputs = _missing_required_node_inputs(self._workflow, object_info)
        if required_inputs:
            raise _invalid("ComfyUI H3 node inputs changed.", ", ".join(required_inputs))
        self._preflighted.add(request.resolved_generation_hash)

    def _upload_binding(self, binding) -> str:
        try:
            path = self._image_resolver(binding.asset_id, binding.asset_sha256).resolve(
                strict=True
            )
            path.relative_to(self._image_root)
            payload = path.read_bytes()
        except (OSError, RuntimeError, ValueError) as exc:
            raise _invalid("H3 frame input could not be reopened safely.", str(exc)) from exc
        if (
            hashlib.sha256(payload).hexdigest() != binding.asset_sha256
            or binding.size_bytes is not None
            and len(payload) != binding.size_bytes
        ):
            raise _invalid("H3 frame bytes do not match the request.", binding.asset_id)
        return self._transport.upload_image(path)

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult:
        try:
            if request.resolved_generation_hash not in self._preflighted:
                raise _invalid("Local H3 request has not passed exact preflight.")
            self._preflighted.remove(request.resolved_generation_hash)
            if (
                preview != self.preview(request)
                or intent.request_fingerprint != request.resolved_generation_hash
            ):
                raise _invalid("Local H3 preview or intent identity is invalid.")
            first = next(
                (
                    item
                    for item in request.image_bindings
                    if item.role == "first_frame"
                ),
                None,
            )
            last = next(
                (item for item in request.image_bindings if item.role == "last_frame"),
                None,
            )
            if first is None or (
                last is not None and not self.profile.optional_last_frame_supported
            ):
                raise _invalid("Local H3 frame bindings are unsupported.")
            first_name = self._upload_binding(first)
            last_name = self._upload_binding(last) if last is not None else None
            workflow = render_h3_workflow(
                template=self._workflow,
                binding=self._binding,
                request=request,
                first_frame_name=first_name,
                last_frame_name=last_name,
                output_prefix=(
                    f"video/ai_video_h3_{request.resolved_generation_hash[:16]}"
                ),
                steps=self.profile.steps,
                sampler=self.profile.sampler,
            )
            if not permit._consume_local_video_submit_permit(
                intent_fingerprint=intent.intent_fingerprint,
                request_fingerprint=request.resolved_generation_hash,
            ):
                raise _invalid("Local H3 submit requires the exact durable permit.")
        except AiVideoError as exc:
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Local H3 pre-submit validation failed before any prompt effect.",
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
                "Local H3 prompt submission outcome is unknown; do not resubmit blindly.",
                exc,
            ) from exc

    def get_local_status(
        self, submission: LocalVideoSubmission
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
                user_message="ComfyUI did not return a terminal job result.",
                retryable=False,
            )
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local H3 job outcome is unknown; explicit recovery is required.",
                source,
            )
        filename, subfolder, type_ = _video_artifact(
            job.history, self.profile.output_node_id
        )
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=VideoTaskState.SUCCEEDED,
            progress_milli=1000,
            provider_file_id=f"{subfolder}:{filename}:{type_}",
            observed_at=self._clock(),
        )

    def fetch_local(
        self,
        submission: LocalVideoSubmission,
        observation: LocalVideoTaskObservation,
        sink: BinaryIO,
    ) -> LocalVideoFetchReceipt:
        if observation.state is not VideoTaskState.SUCCEEDED or observation.provider_file_id is None:
            raise _invalid("Local H3 fetch requires a succeeded observation.")
        try:
            subfolder, filename, type_ = observation.provider_file_id.split(":", 2)
        except ValueError as exc:
            raise _invalid("Local H3 output locator is invalid.", str(exc)) from exc
        payload = self._transport.fetch_artifact_bytes(
            filename=filename, subfolder=subfolder, type_=type_
        )
        if not payload or b"ftyp" not in payload[:64]:
            raise _invalid("Local H3 returned non-MP4 bytes.")
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
    "ComfyUIVideoProvider",
    "LocalVideoBinding",
    "LocalVideoExecutionProfile",
    "LocalVideoModelComponent",
    "LocalVideoTransport",
    "load_local_video_execution_profile",
    "render_h3_workflow",
]
