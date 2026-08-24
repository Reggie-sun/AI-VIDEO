"""Offline-only M0 execution sources for Shot Continuity qualification."""

from __future__ import annotations

import base64
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.video_execution_stack import (
    ExecutionStackMaterialization,
    GenerationExecutionStackIdentity,
    RuntimeSeal,
)
from ai_video.workflow_renderer import _set_path

if TYPE_CHECKING:
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video import ResolvedVideoGenerationRequest


_SHA256 = r"^[0-9a-f]{64}$"
_FORBIDDEN_WORKFLOW_CLASSES = {
    "LoraLoader",
    "LoraLoaderModelOnly",
    "LoraLoaderBypassModelOnly",
    "MiniMaxH3HybridModelLoaderT8Advanced",
    "MiniMaxH3TurboLoRA",
    "MiniMaxH3TurboSampler",
}
_REQUIRED_WORKFLOW_CLASSES = (
    "UNETLoader",
    "CLIPLoader",
    "VAELoader",
    "MiniMaxH3AudioConditioningT8",
    "MiniMaxH3DualClockSamplerT8",
    "RandomNoise",
    "BasicGuider",
    "SamplerCustomAdvanced",
    "MiniMaxH3AVDecodeT8",
    "VHS_VideoCombine",
    "LoadImage",
    "VHS_LoadVideo",
)
_RUNTIME_FILE_CHOOSERS = {
    "UNETLoader": ("unet_name",),
    "CLIPLoader": ("clip_name",),
    "VAELoader": ("vae_name",),
    "LoadImage": ("image",),
    "VHS_LoadVideo": ("video",),
}
_M0_SEED_FIELDS = (
    "candidate_id",
    "initial_execution_stack_hash",
    "m1_execution_stack_hash",
    "prepared_receipt_hash",
    "project_content_hash",
    "registry_content_hash",
    "prompt_sha256",
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class M0QualificationComponent(StrictModel):
    kind: Literal["checkpoint", "artifact"]
    component_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    size_bytes: int = Field(strict=True, gt=0)
    sha256: str = Field(pattern=_SHA256)

    @field_validator("filename")
    @classmethod
    def _clean_filename(cls, value: str) -> str:
        if Path(value).name != value or value in {".", ".."}:
            raise ValueError("M0 component filename must be a clean basename")
        return value


class M0QualificationNodeSchemaSeal(StrictModel):
    node_name: str = Field(min_length=1)
    schema_sha256: str = Field(pattern=_SHA256)


class M0QualificationProfile(StrictModel):
    schema_version: Literal["1"]
    status: Literal["qualification_candidate"]
    candidate_label: Literal["m0"]
    provider_kind: Literal["comfy-local-h3-t8"]
    deployment_identity: Literal["loopback-127.0.0.1-8188"]
    model_id: Literal["minimax-h3-t8-hybrid-stock20"]
    capability_id: Literal["c4-native-boundary-motion-qualification-candidate"]
    candidate_id: Literal["minimax-h3-t8-c4-motion-ref2va-stock20-v1"]
    contract_version: Literal["1"]
    initial_execution_stack_hash: str = Field(pattern=_SHA256)
    m1_execution_stack_hash: str = Field(pattern=_SHA256)
    prepared_receipt_hash: str = Field(pattern=_SHA256)
    project_content_hash: str = Field(pattern=_SHA256)
    registry_content_hash: str = Field(pattern=_SHA256)
    prompt_sha256: str = Field(pattern=_SHA256)
    seed_derivation: Literal[
        "content-addressed-m0-closure-sha256-low63-v1"
    ]
    sealed_seed: int = Field(strict=True, ge=0, le=(1 << 63) - 1)
    task_type: Literal["Hybrid"]
    components: tuple[M0QualificationComponent, ...] = Field(min_length=4, max_length=4)
    runtime_seals: tuple[RuntimeSeal, ...] = Field(min_length=3, max_length=3)
    node_schema_seals: tuple[M0QualificationNodeSchemaSeal, ...] = Field(
        min_length=12,
        max_length=12,
    )
    workflow_path: Path
    workflow_sha256: str = Field(pattern=_SHA256)
    binding_path: Path
    binding_sha256: str = Field(pattern=_SHA256)
    width: Literal[1344]
    height: Literal[768]
    frame_count: Literal[124]
    fps: Literal[24]
    sampler: Literal["dual_clock_euler"]
    scheduler: Literal["native_flow"]
    steps: Literal[20]
    shift_video: Literal[12.0]
    shift_audio: Literal[3.0]
    turbo_lora: Literal[False]
    native_audio: Literal[True]
    output_container: Literal["mp4"]
    output_crf: Literal[17]
    output_contract_hash: str = Field(pattern=_SHA256)
    remote_provider_enabled: Literal[False]
    cloud_fallback_enabled: Literal[False]

    @field_validator("workflow_path", "binding_path")
    @classmethod
    def _relative_source_path(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("M0 qualification sources require contained relative paths")
        return value

    @model_validator(mode="after")
    def _exact_node_schema_coverage(self) -> "M0QualificationProfile":
        if tuple(item.node_name for item in self.node_schema_seals) != (
            _REQUIRED_WORKFLOW_CLASSES
        ):
            raise ValueError(
                "M0 node schema seals must cover every required node exactly"
            )
        if self.sealed_seed != derive_m0_qualification_seed(
            self.model_dump(mode="python")
        ):
            raise ValueError(
                "M0 sealed seed does not match the content-addressed closure"
            )
        return self


def derive_m0_qualification_seed(values: Mapping[str, object]) -> int:
    """Derive one stable non-negative seed without inspecting generated media."""

    try:
        payload = {field: values[field] for field in _M0_SEED_FIELDS}
    except KeyError as exc:
        raise ValueError("M0 seed derivation closure is incomplete") from exc
    digest = canonical_sha256(
        {
            "schema": "ai-video-m0-sealed-seed/1",
            **payload,
        }
    )
    return int(digest[:16], 16) & ((1 << 63) - 1)


class M0QualificationBinding(StrictModel):
    task_type: tuple[str | int, ...]
    prompt: tuple[str | int, ...]
    seed: tuple[str | int, ...]
    first_frame: tuple[str | int, ...]
    last_frame: tuple[str | int, ...]
    reference: tuple[str | int, ...]
    reference_video: tuple[str | int, ...]
    output_prefix: tuple[str | int, ...]
    conditioning_node_id: Literal["6"]
    sampler_node_id: Literal["7"]
    output_node_id: Literal["12"]


class M0QualificationCompileInputs(StrictModel):
    prompt: str = Field(min_length=1)
    seed: int = Field(strict=True, ge=0, le=(1 << 63) - 1)
    first_frame: str = Field(min_length=1)
    last_frame: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    reference_video: str = Field(min_length=1)

    @field_validator(
        "first_frame", "last_frame", "reference", "reference_video"
    )
    @classmethod
    def _safe_uploaded_name(cls, value: str) -> str:
        path = Path(value)
        lowered = value.lower()
        if (
            path.is_absolute()
            or ".." in path.parts
            or any(token in lowered for token in ("api_key", "secret=", "file://"))
        ):
            raise ValueError("M0 qualification input must be a safe uploaded name")
        return value


@dataclass(frozen=True)
class M0QualificationExecutionSources:
    profile: M0QualificationProfile
    profile_document_hash: str
    binding: M0QualificationBinding
    workflow: dict[str, Any]
    materialization: ExecutionStackMaterialization


@dataclass(frozen=True)
class M0ValidationPreflightSnapshot:
    candidate_label: Literal["m0"]
    qualification_receipt_hash: str
    execution_stack_hash: str
    source_execution_stack_hash: str
    profile_hash: str
    compiler_hash: str
    workflow_hash: str
    validation_set_hash: str
    policy_hashes: tuple[str, ...]
    qualification_input_hashes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class M0ValidationPreSubmitGuard:
    """Bind one durable resolved request to the freshly reopened M0 stack."""

    committer: ProductionStateCommitter
    profile_path: str | Path
    artifact_root: str | Path

    def __call__(self, request: ResolvedVideoGenerationRequest) -> None:
        snapshot = reopen_m0_validation_preflight(
            committer=self.committer,
            profile_path=self.profile_path,
            artifact_root=self.artifact_root,
        )
        sources = load_m0_qualification_execution_sources(
            profile_path=self.profile_path,
            artifact_root=self.artifact_root,
        )
        if request.execution_stack_hash != snapshot.execution_stack_hash:
            raise _invalid(
                "M0 resolved request does not bind the reopened execution stack."
            )
        if (
            sources.materialization.profile_hash != snapshot.profile_hash
            or sources.materialization.compiler_hash != snapshot.compiler_hash
            or sources.materialization.workflow_hash != snapshot.workflow_hash
        ):
            raise _invalid("M0 execution sources drifted after the guarded reopen.")
        _validate_m0_resolved_request(request, sources)


def _value(value: object) -> object:
    return getattr(value, "value", value)


def _validate_m0_resolved_request(
    request: ResolvedVideoGenerationRequest,
    sources: M0QualificationExecutionSources,
) -> None:
    """Reject any M0 request drift before preview, intent, permit, or POST."""

    profile = sources.profile
    try:
        provider_profile = request.provider_profile
        if (
            request.provider_name != profile.provider_kind
            or request.provider_kind != profile.provider_kind
            or request.model_id != profile.model_id
            or request.capability_id != profile.capability_id
        ):
            raise _invalid("M0 resolved request candidate identity does not match.")
        if (
            provider_profile.profile_id != profile.candidate_id
            or provider_profile.profile_version != f"v{profile.contract_version}"
            or provider_profile.profile_sha256 != sources.profile_document_hash
        ):
            raise _invalid("M0 resolved request profile identity does not match.")
        if request.adapter_compiler_hash != sources.materialization.compiler_hash:
            raise _invalid("M0 resolved request compiler hash does not match.")

        c4 = request.c4_multi_anchor_binding
        if (
            _value(request.execution_kind) != "local"
            or _value(request.billing_kind) != "local_unmetered"
            or _value(request.mode) != "image_to_video"
            or c4 is None
            or _value(c4.tier) != "motion_boundary"
        ):
            raise _invalid(
                "M0 resolved request must use the local motion-boundary contract."
            )
        if (
            tuple(item.role for item in request.image_bindings)
            != ("first_frame", "last_frame", "reference")
            or tuple((item.kind, item.role) for item in request.media_bindings)
            != (("video", "reference_video"),)
            or c4.motion_tail is None
        ):
            raise _invalid("M0 resolved request does not contain exact four-anchor input.")
        if (
            hashlib.sha256(request.prompt_text.encode("utf-8")).hexdigest()
            != profile.prompt_sha256
            or request.effective_negative_prompt_text
        ):
            raise _invalid("M0 resolved request prompt does not match.")
        if (
            isinstance(request.effective_seed, bool)
            or not isinstance(request.effective_seed, int)
            or request.effective_seed < 0
            or request.effective_seed != profile.sealed_seed
        ):
            raise _invalid(
                "M0 resolved request requires the exact content-addressed sealed seed."
            )

        output = request.effective_output
        if (
            getattr(output, "timing_mode", None) != "frame_count"
            or getattr(output, "frame_count", None) != profile.frame_count
            or getattr(output, "duration_seconds", None) is not None
            or getattr(output, "dimension_mode", None) != "exact"
            or output.width != profile.width
            or output.height != profile.height
            or output.fps != profile.fps
            or output.container != profile.output_container
            or output.mime_type != "video/mp4"
            or output.native_audio is not profile.native_audio
        ):
            raise _invalid("M0 resolved request output contract does not match.")
    except AttributeError as exc:
        raise _invalid("M0 resolved request is incomplete.", str(exc)) from exc


def _profile_source_bundle(profile_bytes: bytes, binding_bytes: bytes) -> bytes:
    return json.dumps(
        {
            "binding_bytes_base64": base64.b64encode(binding_bytes).decode("ascii"),
            "profile_bytes_base64": base64.b64encode(profile_bytes).decode("ascii"),
            "schema_version": "1",
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _read_exact(root: Path, relative: Path, expected_hash: str, label: str) -> bytes:
    try:
        reopened = _read_regular_file_nofollow(root / relative, contained_by=root)
    except (OSError, ValueError) as exc:
        raise _invalid(f"M0 qualification {label} could not be reopened.", str(exc)) from exc
    if reopened.file_sha256 != expected_hash:
        raise _invalid(f"M0 qualification {label} hash does not match.")
    return reopened.data


def m0_node_schema_seals(
    object_info: dict[str, Any],
) -> tuple[M0QualificationNodeSchemaSeal, ...]:
    """Seal exact M0 node schemas without mutable runtime file inventories."""

    result = []
    for node_name in _REQUIRED_WORKFLOW_CLASSES:
        node = object_info.get(node_name)
        if not isinstance(node, dict):
            raise _invalid("M0 ComfyUI node schema is incomplete.", node_name)
        input_schema = json.loads(json.dumps(node.get("input")))
        if not isinstance(input_schema, dict):
            raise _invalid("M0 ComfyUI node schema is malformed.", node_name)
        for section in ("required", "optional"):
            fields = input_schema.get(section)
            if not isinstance(fields, dict):
                continue
            for field in _RUNTIME_FILE_CHOOSERS.get(node_name, ()):
                spec = fields.get(field)
                if isinstance(spec, list) and spec and isinstance(spec[0], list):
                    spec[0] = ["<runtime-file-inventory>"]
        projection = {
            "input": input_schema,
            "input_order": node.get("input_order"),
            "output_name": node.get("output_name"),
        }
        if not all(projection.values()):
            raise _invalid("M0 ComfyUI node schema is malformed.", node_name)
        result.append(
            M0QualificationNodeSchemaSeal(
                node_name=node_name,
                schema_sha256=canonical_sha256(projection),
            )
        )
    return tuple(result)


def validate_m0_live_node_schemas(
    object_info: dict[str, Any],
    sources: M0QualificationExecutionSources,
) -> None:
    """Reject live ComfyUI schema drift before any M0 submit effect."""

    if m0_node_schema_seals(object_info) != sources.profile.node_schema_seals:
        raise _invalid("M0 live ComfyUI node schema does not match the sealed profile.")


def _validate_workflow(
    profile: M0QualificationProfile,
    workflow: dict[str, Any],
    binding: M0QualificationBinding,
) -> None:
    expected_binding = M0QualificationBinding(
        task_type=("6", "inputs", "task_type"),
        prompt=("6", "inputs", "prompt"),
        seed=("8", "inputs", "noise_seed"),
        first_frame=("13", "inputs", "image"),
        last_frame=("14", "inputs", "image"),
        reference=("15", "inputs", "image"),
        reference_video=("16", "inputs", "video"),
        output_prefix=("12", "inputs", "filename_prefix"),
        conditioning_node_id="6",
        sampler_node_id="7",
        output_node_id="12",
    )
    classes = tuple(
        node.get("class_type") for node in workflow.values() if isinstance(node, dict)
    )
    conditioning = workflow.get(binding.conditioning_node_id, {}).get("inputs", {})
    sampler = workflow.get(binding.sampler_node_id, {}).get("inputs", {})
    output = workflow.get(binding.output_node_id, {}).get("inputs", {})
    media_keys = {
        "first_frame",
        "last_frame",
        "ref_images.ref_image_0",
        "ref_videos.ref_video_0",
    }
    actual_media_keys = {
        key
        for key in conditioning
        if key in media_keys
        or key.startswith("ref_video_audios")
        or key.startswith("ref_audios")
    }
    expected_class_counts = Counter(
        {
            "UNETLoader": 1,
            "CLIPLoader": 1,
            "VAELoader": 2,
            "MiniMaxH3AudioConditioningT8": 1,
            "MiniMaxH3DualClockSamplerT8": 1,
            "RandomNoise": 1,
            "BasicGuider": 1,
            "SamplerCustomAdvanced": 1,
            "MiniMaxH3AVDecodeT8": 1,
            "VHS_VideoCombine": 1,
            "LoadImage": 3,
            "VHS_LoadVideo": 1,
        }
    )
    expected_node_classes = {
        "1": "UNETLoader",
        "3": "CLIPLoader",
        "4": "VAELoader",
        "5": "VAELoader",
        "6": "MiniMaxH3AudioConditioningT8",
        "7": "MiniMaxH3DualClockSamplerT8",
        "8": "RandomNoise",
        "9": "BasicGuider",
        "10": "SamplerCustomAdvanced",
        "11": "MiniMaxH3AVDecodeT8",
        "12": "VHS_VideoCombine",
        "13": "LoadImage",
        "14": "LoadImage",
        "15": "LoadImage",
        "16": "VHS_LoadVideo",
    }
    if (
        set(classes) != set(_REQUIRED_WORKFLOW_CLASSES)
        or Counter(classes) != expected_class_counts
        or {
            node_id: node.get("class_type")
            for node_id, node in workflow.items()
            if isinstance(node, dict)
        }
        != expected_node_classes
        or any(name in classes for name in _FORBIDDEN_WORKFLOW_CLASSES)
        or binding != expected_binding
        or workflow.get("1", {}).get("inputs", {}).get("unet_name")
        != profile.components[0].filename
        or workflow.get("3", {}).get("inputs", {}).get("clip_name")
        != profile.components[1].filename
        or workflow.get("4", {}).get("inputs", {}).get("vae_name")
        != profile.components[2].filename
        or workflow.get("5", {}).get("inputs", {}).get("vae_name")
        != profile.components[3].filename
        or conditioning.get("task_type") != "Hybrid"
        or conditioning.get("audio_mode") != "native"
        or conditioning.get("width") != profile.width
        or conditioning.get("height") != profile.height
        or conditioning.get("length") != profile.frame_count
        or actual_media_keys != media_keys
        or sampler
        != {
            "av_latent": ["6", 1],
            "model": ["1", 0],
            "sampler_name": profile.sampler,
            "scheduler": profile.scheduler,
            "shift_audio": profile.shift_audio,
            "shift_video": profile.shift_video,
            "steps": profile.steps,
        }
        or workflow.get("9", {}).get("inputs")
        != {"conditioning": ["6", 0], "model": ["7", 0]}
        or workflow.get("10", {}).get("inputs")
        != {
            "guider": ["9", 0],
            "latent_image": ["6", 1],
            "noise": ["8", 0],
            "sampler": ["7", 1],
            "sigmas": ["7", 2],
        }
        or workflow.get("11", {}).get("inputs")
        != {
            "audio_vae": ["5", 0],
            "av_latent": ["10", 0],
            "video_vae": ["4", 0],
        }
        or output.get("images") != ["11", 0]
        or output.get("audio") != ["11", 1]
        or output.get("frame_rate") != float(profile.fps)
        or output.get("format") != "video/h264-mp4"
        or output.get("crf") != profile.output_crf
        or output.get("save_output") is not True
    ):
        raise _invalid("M0 qualification workflow does not match the sealed contract.")


def load_m0_qualification_execution_sources(
    *,
    profile_path: str | Path,
    artifact_root: str | Path,
) -> M0QualificationExecutionSources:
    root = Path(artifact_root).resolve(strict=True)
    requested_profile = Path(profile_path).resolve(strict=True)
    try:
        requested_profile.relative_to(root)
        profile_snapshot = _read_regular_file_nofollow(
            requested_profile,
            contained_by=root,
        )
        profile = M0QualificationProfile.model_validate_json(profile_snapshot.data)
        workflow_bytes = _read_exact(
            root, profile.workflow_path, profile.workflow_sha256, "workflow"
        )
        binding_bytes = _read_exact(
            root, profile.binding_path, profile.binding_sha256, "binding"
        )
        workflow = json.loads(workflow_bytes)
        binding = M0QualificationBinding.model_validate(yaml.safe_load(binding_bytes))
        compiler_snapshot = _read_regular_file_nofollow(
            Path(__file__),
            contained_by=root,
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        if isinstance(exc, AiVideoError):
            raise
        raise _invalid("M0 qualification execution sources are invalid.", str(exc)) from exc
    if not isinstance(workflow, dict):
        raise _invalid("M0 qualification workflow must be a JSON object.")
    _validate_workflow(profile, workflow, binding)
    materialization = ExecutionStackMaterialization.from_bytes(
        candidate_label="m0",
        profile_bytes=_profile_source_bundle(
            profile_snapshot.data,
            binding_bytes,
        ),
        compiler_bytes=compiler_snapshot.data,
        workflow_bytes=workflow_bytes,
    )
    return M0QualificationExecutionSources(
        profile=profile,
        profile_document_hash=profile_snapshot.file_sha256,
        binding=binding,
        workflow=workflow,
        materialization=materialization,
    )


def validate_m0_sources_against_stack(
    sources: M0QualificationExecutionSources,
    stack: GenerationExecutionStackIdentity,
    *,
    allow_materialized_source_reseal: bool = False,
) -> None:
    profile = sources.profile
    components = tuple(
        (item.kind, item.component_id, item.presence, item.content_hash)
        for item in stack.components
    )
    expected_components = tuple(
        (item.kind, item.component_id, "present", item.sha256)
        for item in profile.components
    )
    materialized_hashes = (
        stack.profile_hash,
        stack.compiler_hash,
        stack.workflow_hash,
    )
    expected_hashes = (
        sources.materialization.profile_hash,
        sources.materialization.compiler_hash,
        sources.materialization.workflow_hash,
    )
    if (
        profile.candidate_label != "m0"
        or stack.candidate_id != profile.candidate_id
        or stack.contract_version != profile.contract_version
        or stack.provider_kind != profile.provider_kind
        or stack.deployment_identity != profile.deployment_identity
        or stack.model_id != profile.model_id
        or stack.capability_id != profile.capability_id
        or components != expected_components
        or stack.runtime_seals != profile.runtime_seals
        or stack.sampler_identity != profile.sampler
        or stack.scheduler_identity != profile.scheduler
        or stack.output_contract_hash != profile.output_contract_hash
        or stack.materialization_status == "unmaterialized"
        and (
            stack.execution_stack_hash != profile.initial_execution_stack_hash
            or materialized_hashes != ("none", "none", "none")
        )
        or stack.materialization_status == "materialized"
        and materialized_hashes != expected_hashes
        and not allow_materialized_source_reseal
    ):
        raise _invalid("M0 qualification sources do not match the selected stack identity.")


def reopen_m0_validation_preflight(
    *,
    committer: ProductionStateCommitter,
    profile_path: str | Path,
    artifact_root: str | Path,
) -> M0ValidationPreflightSnapshot:
    """Reopen the exact M0 qualification bundle immediately before any effect."""

    sources = load_m0_qualification_execution_sources(
        profile_path=profile_path,
        artifact_root=artifact_root,
    )
    receipt, stacks, policies, validation_set, inputs = (
        committer.reopen_p0_qualification_prepared(
            required_materialized_candidates=("m0",)
        )
    )
    source_stacks = committer.reopen_p0_qualification_source_stacks()
    if source_stacks:
        source_stacks = committer.reopen_p0_qualification_source_stacks(
            require_materialized=True
        )
    m0, m1 = stacks
    source_stack_hash = (
        source_stacks[0].execution_stack_hash
        if source_stacks
        else m0.execution_stack_hash
    )
    validate_m0_sources_against_stack(sources, m0)
    profile = sources.profile
    try:
        calibration = next(
            item.payload
            for item in inputs
            if item.input_kind == "calibration_fixture"
        )
        hybrid = next(
            item
            for item in m1.components
            if item.component_id == "hybrid-artifact-candidate-v1"
        )
    except StopIteration as exc:
        raise _invalid("M0 validation target is incomplete.") from exc
    if (
        receipt.project.content_hash != profile.project_content_hash
        or receipt.registry.content_hash != profile.registry_content_hash
        or m1.execution_stack_hash != profile.m1_execution_stack_hash
        or m1.materialization_status != "unmaterialized"
        or hybrid.presence != "absent"
        or hybrid.content_hash != "none"
        or calibration.get("prompt_sha256") != profile.prompt_sha256
        or calibration.get("task_type") != profile.task_type
        or calibration.get("steps") != profile.steps
        or calibration.get("sampler") != profile.sampler
        or calibration.get("scheduler") != profile.scheduler
        or calibration.get("turbo_lora") is not profile.turbo_lora
        or any(
            policy.source_execution_stack_hash != source_stack_hash
            or policy.destination_execution_stack_hash != m0.execution_stack_hash
            for policy in policies
        )
        or any(
            item.execution_stack_hashes
            != tuple(sorted({source_stack_hash, m0.execution_stack_hash}))
            for item in inputs
        )
    ):
        raise _invalid(
            "M0 validation target does not match the frozen qualification bundle."
        )
    return M0ValidationPreflightSnapshot(
        candidate_label="m0",
        qualification_receipt_hash=receipt.content_hash,
        execution_stack_hash=m0.execution_stack_hash,
        source_execution_stack_hash=source_stack_hash,
        profile_hash=m0.profile_hash,
        compiler_hash=m0.compiler_hash,
        workflow_hash=m0.workflow_hash,
        validation_set_hash=validation_set.content_hash,
        policy_hashes=tuple(item.policy_hash for item in policies),
        qualification_input_hashes=tuple(
            (item.input_kind, item.content_hash) for item in inputs
        ),
    )


def compile_m0_qualification_workflow(
    *,
    sources: M0QualificationExecutionSources,
    inputs: M0QualificationCompileInputs,
) -> dict[str, Any]:
    if hashlib.sha256(inputs.prompt.encode("utf-8")).hexdigest() != (
        sources.profile.prompt_sha256
    ):
        raise _invalid("M0 qualification prompt does not match the frozen prompt hash.")
    rendered = json.loads(json.dumps(sources.workflow))
    binding = sources.binding
    prefix_hash = canonical_sha256(inputs.model_dump(mode="json"))[:16]
    for path, value, label in (
        (binding.task_type, "Hybrid", "task_type"),
        (binding.prompt, inputs.prompt, "prompt"),
        (binding.seed, inputs.seed, "seed"),
        (binding.first_frame, inputs.first_frame, "first_frame"),
        (binding.last_frame, inputs.last_frame, "last_frame"),
        (binding.reference, inputs.reference, "reference"),
        (binding.reference_video, inputs.reference_video, "reference_video"),
        (
            binding.output_prefix,
            f"MiniMaxH3/ai_video_shot_continuity_m0_{prefix_hash}",
            "output_prefix",
        ),
    ):
        _set_path(rendered, list(path), value, label)
    _validate_workflow(sources.profile, rendered, binding)
    return rendered


__all__ = [
    "M0QualificationCompileInputs",
    "M0QualificationExecutionSources",
    "M0QualificationProfile",
    "derive_m0_qualification_seed",
    "M0ValidationPreSubmitGuard",
    "M0ValidationPreflightSnapshot",
    "compile_m0_qualification_workflow",
    "load_m0_qualification_execution_sources",
    "reopen_m0_validation_preflight",
    "validate_m0_sources_against_stack",
]
