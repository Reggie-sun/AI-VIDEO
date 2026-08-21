"""Sealed local T8-native H3 Turbo V2 video adapter."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Protocol

import httpx

from ai_video.comfy_client import ComfyClient
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import (
    _missing_required_node_inputs,
    validate_loopback_endpoint,
)
from ai_video.production.comfy_t8_native_turbo_profile import (
    T8NativeTurboBinding,
    T8NativeTurboExecutionProfile,
    T8NativeTurboRuntimeInspection,
    load_t8_native_turbo_binding,
    node_schema_seals,
)
from ai_video.production.comfy_t8_video import ComfyUIT8VideoProvider
from ai_video.production.local_video import (
    DurableLocalVideoSubmitPermit,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
)
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.video import (
    BillingKind,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoProviderCapabilities,
)
from ai_video.production.video_compiler import (
    ProviderRequestCompilationResult,
    compile_provider_video_request,
)
from ai_video.production.video_contracts import (
    VideoBindingCardinalityConstraint,
    VideoFlexibleOutputRequirement,
    VideoMediaCapability,
    VideoOutputCapability,
)
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
from ai_video.workflow_loader import load_workflow_template
from ai_video.workflow_renderer import _set_path


_PROVIDER_NAME = "comfy-local-h3-t8"
_COMPILER_ID = "comfy-local-h3-t8-native-turbo-video-compiler"
_MAX_DETERMINISTIC_SEED = (1 << 63) - 1
_COMPONENT_DIRS = {
    "diffusion": Path("models/diffusion_models"),
    "text_encoder": Path("models/text_encoders"),
    "video_vae": Path("models/vae"),
    "audio_vae": Path("models/vae"),
}


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
    detail = (
        f"{source.code.value}: {source.user_message}"
        if isinstance(source, AiVideoError)
        else f"{type(source).__name__}: local response failed validation"
    )
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=detail,
        retryable=False,
        cause=source,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _effective_seed(request: VideoGenerationRequest) -> int:
    if request.seed is not None:
        return request.seed
    return int(request.request_input_hash[:16], 16) & _MAX_DETERMINISTIC_SEED


class T8NativeTurboTransport(Protocol):
    def get_object_info(self) -> dict[str, Any]: ...
    def upload_input(self, path: str | Path) -> str: ...
    def submit_prompt(self, workflow: dict[str, Any]) -> str: ...
    def poll_job(
        self, prompt_id: str, *, poll_interval_seconds: float, timeout_seconds: float
    ) -> Any: ...
    def fetch_artifact_bytes(
        self, *, filename: str, subfolder: str, type_: str
    ) -> bytes: ...


AssetResolver = Callable[[str, str], Path]


def _read_sealed(root: Path, relative: Path, sha256: str, label: str) -> bytes:
    try:
        path = (root / relative).resolve(strict=True)
        path.relative_to(root)
        payload = path.read_bytes()
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid(f"{label} could not be reopened safely.", str(exc)) from exc
    if hashlib.sha256(payload).hexdigest() != sha256:
        raise _invalid(f"{label} hash does not match the sealed profile.")
    return payload


def _constraints(task_type: str) -> tuple[VideoBindingCardinalityConstraint, ...]:
    bounds = {
        "T2VA": (0, 0, 0, 0, 0, 0, 0),
        "I2VA": (1, 0, 0, 0, 0, 0, 0),
        "FL2VA": (1, 1, 0, 0, 0, 0, 0),
        "Ref2VA": (0, 0, 9, 3, 3, 1, 15),
    }[task_type]
    first, last, image, video, audio, group_min, group_max = bounds
    roles = (
        "first_frame",
        "last_frame",
        "reference",
        "reference_video",
        "reference_audio",
    )
    maxima = (first, last, image, video, audio)
    constraints = tuple(
        VideoBindingCardinalityConstraint(
            roles=(role,),
            min_count=(
                value
                if task_type in {"I2VA", "FL2VA"}
                and role in {"first_frame", "last_frame"}
                else 0
            ),
            max_count=value,
        )
        for role, value in zip(roles, maxima, strict=True)
    )
    if task_type == "Ref2VA":
        constraints += (
            VideoBindingCardinalityConstraint(
                roles=("reference", "reference_video", "reference_audio"),
                min_count=group_min,
                max_count=group_max,
            ),
        )
    else:
        constraints += (
            VideoBindingCardinalityConstraint(
                roles=("reference", "reference_video", "reference_audio"),
                min_count=0,
                max_count=0,
            ),
        )
    return constraints


def t8_native_turbo_capabilities(
    profile: T8NativeTurboExecutionProfile,
) -> VideoProviderCapabilities:
    output = VideoOutputCapability(
        min_duration_seconds=profile.frame_count // profile.fps,
        max_duration_seconds=(profile.frame_count + profile.fps - 1) // profile.fps,
        provider_selected_duration=False,
        timing_modes=("frame_count",),
        frame_count_min=profile.frame_count,
        frame_count_max=profile.frame_count,
        frame_count_step=17,
        frame_count_remainder=5,
        dimension_modes=("exact",),
        min_width=profile.width,
        max_width=profile.width,
        min_height=profile.height,
        max_height=profile.height,
        dimension_multiple=32,
        resolution_labels=("h3_t8_native",),
        ratios=("16:9",),
        fps_values=(profile.fps,),
        containers=(profile.output_container,),
        native_audio_options=(True,),
    )
    allowed_roles = {
        "T2VA": (),
        "I2VA": ("first_frame",),
        "FL2VA": ("first_frame", "last_frame"),
        "Ref2VA": ("reference",),
    }[profile.task_type]
    media = ()
    if profile.task_type == "Ref2VA":
        media = (
            VideoMediaCapability(
                kind="video",
                roles=("reference_video",),
                min_count=0,
                max_count=3,
                allowed_mime_types=profile.reference_video_mime_types,
                max_size_bytes=profile.max_reference_video_bytes,
                min_duration_millis=profile.reference_video_min_duration_millis,
                max_duration_millis=profile.reference_video_max_duration_millis,
            ),
            VideoMediaCapability(
                kind="audio",
                roles=("reference_audio",),
                min_count=0,
                max_count=3,
                allowed_mime_types=profile.reference_audio_mime_types,
                max_size_bytes=profile.max_reference_audio_bytes,
                min_duration_millis=1,
                max_duration_millis=profile.reference_video_max_duration_millis,
            ),
        )
    return VideoProviderCapabilities.create(
        provider_name=_PROVIDER_NAME,
        variants=(
            VideoCapabilityVariant(
                capability_id=profile.capability_id,
                provider_kind=profile.provider_kind,
                model_id=profile.model_id,
                profile_version=profile.profile_version,
                execution_kind=VideoExecutionKind.LOCAL,
                billing_kind=BillingKind.LOCAL_UNMETERED,
                mode=VideoGenerationMode(profile.provider_mode),
                output_capability=output,
                allowed_image_roles=allowed_roles,
                required_first_frame=profile.task_type in {"I2VA", "FL2VA"},
                max_reference_count=9 if profile.task_type == "Ref2VA" else 0,
                allowed_image_mime_types=(
                    profile.image_mime_types if allowed_roles else ()
                ),
                max_image_bytes=profile.max_image_bytes,
                min_image_width=1,
                min_image_height=1,
                media_capabilities=media,
                binding_cardinality_constraints=_constraints(profile.task_type),
                negative_prompt_supported=False,
                seed_supported=True,
                fps_supported=True,
                idempotent_submit=False,
                lookup_supported=False,
            ),
        ),
    )


def render_t8_native_turbo_workflow(
    *,
    template: dict[str, Any],
    binding: T8NativeTurboBinding,
    request: ResolvedVideoGenerationRequest,
    profile: T8NativeTurboExecutionProfile,
    uploaded_images: tuple[str, ...],
    uploaded_videos: tuple[str, ...],
    uploaded_audios: tuple[str, ...],
) -> dict[str, Any]:
    rendered = json.loads(json.dumps(template))
    output = request.effective_output
    if not isinstance(output, VideoFlexibleOutputRequirement):
        raise _invalid("T8-native Turbo V2 requires the frame-count contract.")
    for path, value, label in (
        (binding.task_type, profile.task_type, "task_type"),
        (binding.prompt, request.prompt_text, "prompt"),
        (binding.seed, request.effective_seed, "seed"),
        (binding.width, output.width, "width"),
        (binding.height, output.height, "height"),
        (binding.length, output.frame_count, "length"),
        (binding.steps, profile.steps, "steps"),
        (binding.sampler, profile.sampler, "sampler"),
        (binding.scheduler, profile.scheduler, "scheduler"),
        (
            binding.output_prefix,
            f"MiniMaxH3/ai_video_h3_t8_native_v2_{request.resolved_generation_hash[:16]}",
            "output_prefix",
        ),
    ):
        _set_path(rendered, list(path), value, label)
    if profile.task_type in {"I2VA", "FL2VA"}:
        frame_names = tuple(
            name
            for item, name in zip(request.image_bindings, uploaded_images, strict=True)
            if item.role in {"first_frame", "last_frame"}
        )
        for node_id, name in zip(
            tuple(
                node
                for node in (binding.first_frame_node_id, binding.last_frame_node_id)
                if node is not None
            ),
            frame_names,
            strict=True,
        ):
            rendered[node_id]["inputs"]["image"] = name
    if profile.task_type == "Ref2VA":
        conditioning = rendered[binding.conditioning_node_id]["inputs"]
        next_id = binding.dynamic_node_start
        groups = (
            ("ref_image", "LoadImage", "image", uploaded_images),
            ("ref_video", "VHS_LoadVideo", "video", uploaded_videos),
            ("ref_audio", "VHS_LoadAudioUpload", "audio", uploaded_audios),
        )
        for prefix, class_type, input_name, names in groups:
            for ordinal, name in enumerate(names, start=1):
                node_id = str(next_id)
                next_id += 1
                inputs: dict[str, Any] = {input_name: name}
                if class_type == "VHS_LoadVideo":
                    inputs.update(
                        force_rate=profile.reference_video_fps,
                        custom_width=0,
                        custom_height=0,
                        frame_load_cap=0,
                        skip_first_frames=0,
                        select_every_nth=1,
                    )
                rendered[node_id] = {"class_type": class_type, "inputs": inputs}
                conditioning[f"{prefix}_{ordinal}"] = [node_id, 0]
        conditioning.pop("ref_video_audios", None)
    return rendered


class ComfyUIT8NativeTurboVideoProvider(ComfyUIT8VideoProvider):
    """One exact profile instance exposes one additive V2 child capability."""

    def __init__(
        self,
        profile: T8NativeTurboExecutionProfile,
        *,
        artifact_root: str | Path,
        comfy_root: str | Path,
        input_root: str | Path,
        asset_resolver: AssetResolver,
        runtime_inspector: Callable[[], T8NativeTurboRuntimeInspection],
        endpoint: str = "http://127.0.0.1:8188",
        transport: T8NativeTurboTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        poll_interval_seconds: float = 0.25,
        timeout_seconds: float = 3_600.0,
    ) -> None:
        self.profile = profile
        self._root = Path(artifact_root).resolve(strict=True)
        self._comfy_root = Path(comfy_root).resolve(strict=True)
        self._input_root = Path(input_root).resolve(strict=True)
        self._asset_resolver = asset_resolver
        self._endpoint = validate_loopback_endpoint(endpoint)
        if self._endpoint not in profile.loopback_endpoints:
            raise _invalid("Selected endpoint is not allowed by the V2 profile.")
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
            raise _invalid("Injected endpoint does not match the V2 profile.")
        self._transport = transport
        self._runtime_inspector = runtime_inspector
        self._clock = clock or (lambda: datetime.now(UTC))
        _read_sealed(
            self._root,
            profile.workflow_path,
            profile.workflow_sha256,
            "V2 workflow",
        )
        binding_payload = _read_sealed(
            self._root,
            profile.binding_path,
            profile.binding_sha256,
            "V2 binding",
        )
        self._workflow = load_workflow_template(self._root / profile.workflow_path)
        self._binding = load_t8_native_turbo_binding(binding_payload)
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds

    def capabilities(self) -> VideoProviderCapabilities:
        if (
            self.profile.availability != "live-ready"
            or self.profile.availability_blockers
            or not self.profile.lora.conversion_verified
            or not self.profile.components
        ):
            raise _invalid(
                "T8-native Turbo V2 capability is unavailable for production routing.",
                ", ".join(self.profile.availability_blockers),
            )
        return t8_native_turbo_capabilities(self.profile)

    def _validate_resolved_identity(
        self, request: ResolvedVideoGenerationRequest
    ) -> None:
        capability = t8_native_turbo_capabilities(self.profile).variants[0]
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != capability.provider_kind
            or request.model_id != capability.model_id
            or request.provider_profile.profile_version != "v2"
            or request.provider_profile.profile_sha256
            != self.profile.profile_content_hash
            or request.capability_id != capability.capability_id
            or request.execution_kind is not VideoExecutionKind.LOCAL
            or request.billing_kind is not BillingKind.LOCAL_UNMETERED
            or request.mode is not capability.mode
        ):
            raise _invalid("Resolved request is not owned by this sealed V2 capability.")

    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
    ) -> ProviderRequestCompilationResult:
        return compile_provider_video_request(
            provider_bound=provider_bound,
            requirement=requirement,
            compiler_id=_COMPILER_ID,
            compiler_version="2",
            capabilities=self.capabilities(),
        )

    def resolve(
        self, request: VideoGenerationRequest
    ) -> ResolvedVideoGenerationRequest:
        capability = self.capabilities().variants[0]
        output = request.output_requirement
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != capability.provider_kind
            or request.model_id != capability.model_id
            or request.provider_profile.profile_version != "v2"
            or request.provider_profile.profile_sha256
            != self.profile.profile_content_hash
            or request.mode is not capability.mode
            or not isinstance(output, VideoFlexibleOutputRequirement)
            or not capability.output_capability
            or not capability.output_capability.supports(output)
            or request.negative_prompt_text
            or any(
                item.kind == "video" and item.fps != self.profile.reference_video_fps
                for item in request.media_bindings
            )
        ):
            raise _invalid("Video request is outside the sealed V2 profile.")
        return ResolvedVideoGenerationRequest.create(
            request=request,
            capability=capability,
            effective_output=output,
            effective_seed=_effective_seed(request),
            effective_negative_prompt_text="",
        )

    def preflight(self, request: ResolvedVideoGenerationRequest) -> None:
        self._validate_resolved_identity(request)
        if (
            self.profile.availability != "live-ready"
            or self.profile.availability_blockers
            or not self.profile.lora.conversion_verified
            or not self.profile.components
        ):
            raise _invalid(
                "T8-native Turbo V2 capability is not live-ready.",
                ", ".join(self.profile.availability_blockers),
            )
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
            raise _invalid("Local V2 runtime does not match the sealed profile.")
        sealed = tuple(
            (
                self._comfy_root / _COMPONENT_DIRS[item.role] / item.filename,
                item.size_bytes,
                item.sha256,
            )
            for item in self.profile.components
        ) + (
            (
                self._comfy_root / "models/loras" / self.profile.lora.filename,
                self.profile.lora.size_bytes,
                self.profile.lora.sha256,
            ),
        )
        for path, size, sha256 in sealed:
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(self._comfy_root)
            except (OSError, RuntimeError, ValueError) as exc:
                raise _invalid("A sealed V2 component could not be reopened.", str(exc)) from exc
            if resolved.stat().st_size != size or _sha256_file(resolved) != sha256:
                raise _invalid("A sealed V2 component identity changed.", path.name)
        object_info = self._transport.get_object_info()
        if _missing_required_node_inputs(self._workflow, object_info):
            raise _invalid("ComfyUI V2 required node inputs changed.")
        if (
            node_schema_seals(object_info, self.profile.required_nodes)
            != self.profile.node_schema_seals
        ):
            raise _invalid("ComfyUI V2 node schemas changed.")

    def _input_path(self, binding: Any) -> Path:
        try:
            path = self._asset_resolver(binding.asset_id, binding.asset_sha256).resolve(
                strict=True
            )
            path.relative_to(self._input_root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise _invalid("V2 input could not be reopened safely.", str(exc)) from exc
        if (
            binding.size_bytes is not None
            and path.stat().st_size != binding.size_bytes
        ) or _sha256_file(path) != binding.asset_sha256:
            raise _invalid("V2 input bytes do not match the request.", binding.asset_id)
        head = path.read_bytes()[:64]
        if binding.mime_type == "image/png" and not head.startswith(b"\x89PNG\r\n\x1a\n"):
            raise _invalid("V2 image input is not a PNG.", binding.asset_id)
        if binding.mime_type == "video/mp4" and b"ftyp" not in head:
            raise _invalid("V2 video input is not an MP4.", binding.asset_id)
        if binding.mime_type == "audio/wav" and not (
            head.startswith(b"RIFF") and head[8:12] == b"WAVE"
        ):
            raise _invalid("V2 audio input is not WAV bytes.", binding.asset_id)
        if binding.mime_type == "audio/mpeg" and not (
            head.startswith(b"ID3")
            or len(head) >= 2
            and head[0] == 0xFF
            and head[1] & 0xE0 == 0xE0
        ):
            raise _invalid("V2 audio input is not MPEG audio bytes.", binding.asset_id)
        if binding.mime_type == "audio/mp4" and b"ftyp" not in head:
            raise _invalid("V2 audio input is not MP4 audio bytes.", binding.asset_id)
        return path

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: Any,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult:
        try:
            self.preflight(request)
            if (
                preview != self.preview(request)
                or intent.request_fingerprint != request.resolved_generation_hash
            ):
                raise _invalid("V2 preview or intent identity is invalid.")
            image_paths = tuple(self._input_path(item) for item in request.image_bindings)
            media_paths = tuple(self._input_path(item) for item in request.media_bindings)
            if not permit._consume_local_video_submit_permit(
                intent_fingerprint=intent.intent_fingerprint,
                request_fingerprint=request.resolved_generation_hash,
            ):
                raise _invalid("V2 submit requires the exact durable permit.")
        except AiVideoError as exc:
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Local V2 validation failed before input upload and prompt submission.",
                exc,
            ) from exc
        try:
            image_names = tuple(self._transport.upload_input(path) for path in image_paths)
            video_names = tuple(
                self._transport.upload_input(path)
                for item, path in zip(request.media_bindings, media_paths, strict=True)
                if item.kind == "video"
            )
            audio_names = tuple(
                self._transport.upload_input(path)
                for item, path in zip(request.media_bindings, media_paths, strict=True)
                if item.kind == "audio"
            )
            workflow = render_t8_native_turbo_workflow(
                template=self._workflow,
                binding=self._binding,
                request=request,
                profile=self.profile,
                uploaded_images=image_names,
                uploaded_videos=video_names,
                uploaded_audios=audio_names,
            )
            prompt_id = self._transport.submit_prompt(workflow)
            return LocalVideoSubmitResult.create(
                resolved=request,
                provider_request_id=prompt_id,
                submitted_at=self._clock(),
            )
        except Exception as exc:
            raise _provider_failure(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local V2 submission outcome is unknown; do not retry blindly.",
                exc,
            ) from exc


__all__ = [
    "ComfyUIT8NativeTurboVideoProvider",
    "T8NativeTurboTransport",
    "render_t8_native_turbo_workflow",
    "t8_native_turbo_capabilities",
]
