"""Pure provider request compilation from a sealed Router projection."""

from __future__ import annotations

import hashlib
import unicodedata
from enum import Enum
from typing import Literal, Protocol, runtime_checkable

from pydantic import ConfigDict, Field, ValidationError, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._video_requirement_routing import (
    native_binding_role,
    requirement_mode,
    requirement_output_matches,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
)
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production._video_continuity import (
    C4MultiAnchorBinding,
    ContinuityReferenceBinding,
    HardCutKeyframeBinding,
)
from ai_video.production.video import (
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationRequest,
    VideoGenerationMode,
    VideoImageReferenceBinding,
    VideoOutputRecoveryStrategy,
    VideoOutputRequirement,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoMediaReferenceBinding,
)
from ai_video.production.video_requirement import (
    ActionEndpoint,
    ExpressionStrength,
    ProviderNeutralVideoRequirement,
    TypedStateReference,
)


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_ROLE_ORDER = {"first_frame": 0, "last_frame": 1, "reference": 2}
_MEDIA_ROLE_ORDER = {"reference_video": 0, "reference_audio": 1}


class _CompilerModel(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class ProviderRequirementUnsupportedReason(str, Enum):
    REFERENCE_ROLE_UNSUPPORTED = "REFERENCE_ROLE_UNSUPPORTED"
    NATIVE_CONTROL_UNSUPPORTED = "NATIVE_CONTROL_UNSUPPORTED"
    OUTPUT_UNSUPPORTED = "OUTPUT_UNSUPPORTED"
    AUDIO_UNSUPPORTED = "AUDIO_UNSUPPORTED"
    PROMPT_EXPRESSION_UNSUPPORTED = "PROMPT_EXPRESSION_UNSUPPORTED"
    COMPILER_VERSION_UNSUPPORTED = "COMPILER_VERSION_UNSUPPORTED"
    LINEAGE_MISMATCH = "LINEAGE_MISMATCH"
    OUTPUT_LOCATOR_NOT_RECOVERABLE = "OUTPUT_LOCATOR_NOT_RECOVERABLE"


class ProviderRequirementUnsupported(_CompilerModel):
    outcome: Literal["unsupported"] = "unsupported"
    requirement_hash: str = Field(pattern=_SHA256)
    provider_bound_request_hash: str = Field(pattern=_SHA256)
    selected_capability_id: str = Field(pattern=_SAFE_ID)
    reason: ProviderRequirementUnsupportedReason
    unsupported_field_paths: tuple[str, ...] = Field(min_length=1)
    retryable: Literal[False] = False
    prompt_text: None = None
    payload: None = None


class ProviderNativePrompt(_CompilerModel):
    grammar_contract: str = Field(pattern=_SAFE_ID)
    prompt_text: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_prompt_hash(self) -> "ProviderNativePrompt":
        expected = hashlib.sha256(self.prompt_text.encode("utf-8")).hexdigest()
        if self.prompt_sha256 != expected:
            raise ValueError("native prompt hash does not match exact UTF-8 bytes")
        return self


class CompiledProviderVideoRequest(_CompilerModel):
    outcome: Literal["compiled"] = "compiled"
    requirement_hash: str = Field(pattern=_SHA256)
    provider_bound_request_hash: str = Field(pattern=_SHA256)
    adapter_compiler_id: str = Field(pattern=_SAFE_ID)
    adapter_compiler_version: str = Field(pattern=_SAFE_ID)
    adapter_compiler_hash: str = Field(pattern=_SHA256)
    provider_native_prompt: str = Field(min_length=1)
    request: VideoGenerationRequest
    payload_projection_hash: str = Field(pattern=_SHA256)
    compiled_request_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hashes(self) -> "CompiledProviderVideoRequest":
        payload_hash = canonical_sha256(
            {
                "schema": "provider-video-payload-projection/1",
                "request_input_hash": self.request.request_input_hash,
            }
        )
        if self.payload_projection_hash != payload_hash:
            raise ValueError("payload projection hash does not match request")
        expected = canonical_sha256(
            {
                "schema": "compiled-provider-video-request/1",
                **self.model_dump(
                    mode="json",
                    exclude={"compiled_request_hash"},
                ),
            }
        )
        if self.compiled_request_hash != expected:
            raise ValueError("compiled request hash does not match compilation")
        return self

    @classmethod
    def create(cls, **values: object) -> "CompiledProviderVideoRequest":
        data = dict(values)
        candidate = cls.model_construct(**data, compiled_request_hash="0" * 64)
        data["compiled_request_hash"] = canonical_sha256(
            {
                "schema": "compiled-provider-video-request/1",
                **candidate.model_dump(
                    mode="json",
                    exclude={"compiled_request_hash"},
                    warnings=False,
                ),
            }
        )
        return cls.model_validate(data)


ProviderRequestCompilationResult = (
    CompiledProviderVideoRequest | ProviderRequirementUnsupported
)


@runtime_checkable
class ProviderVideoRequestCompiler(Protocol):
    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
    ) -> ProviderRequestCompilationResult: ...


def require_compiled_provider_request(
    result: ProviderRequestCompilationResult,
) -> CompiledProviderVideoRequest:
    if isinstance(result, ProviderRequirementUnsupported):
        raise AiVideoError(
            code=ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            user_message="Selected video Provider cannot express the sealed requirement.",
            technical_detail=(
                f"{result.reason.value}: "
                f"{', '.join(result.unsupported_field_paths)}"
            ),
            retryable=False,
        )
    return result


class VideoGenerationRequestCompilation(_CompilerModel):
    """Typed, hash-bound input to the sole request constructor owner."""

    compilation_kind: Literal[
        "provider_neutral",
        "qualification",
        "c4_qualification",
    ]
    generation_id: str = Field(pattern=_SAFE_ID)
    provider_name: str = Field(pattern=_SAFE_ID)
    provider_kind: str = Field(pattern=_SAFE_ID)
    model_id: str = Field(pattern=_SAFE_ID)
    provider_profile: ProviderProfilePointer
    requirement_hash: str = Field(pattern=_SHA256)
    provider_bound_request_hash: str = Field(pattern=_SHA256)
    adapter_compiler_id: str = Field(pattern=_SAFE_ID)
    adapter_compiler_version: str = Field(pattern=_SAFE_ID)
    adapter_compiler_hash: str = Field(pattern=_SHA256)
    execution_stack_hash: str | None = Field(default=None, pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    target_asset_role: str = Field(pattern=_SAFE_ID)
    mode: VideoGenerationMode
    prompt_text: str = Field(min_length=1)
    negative_prompt_text: str = ""
    image_bindings: tuple[VideoImageReferenceBinding, ...]
    c4_multi_anchor_binding: C4MultiAnchorBinding | None = None
    continuity_binding: ContinuityReferenceBinding | None = None
    hard_cut_keyframe_binding: HardCutKeyframeBinding | None = None
    seal_terminal_frame: bool = Field(default=False, strict=True)
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = ()
    output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement
    seed: int | None = Field(default=None, strict=True, ge=-1)
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    base_dependency_graph: DependencyGraphSnapshotPointer
    input_artifact_ids: tuple[str, ...] = Field(min_length=1)
    output_asset_id: str = Field(pattern=_SAFE_ID)
    compilation_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_compilation(self) -> "VideoGenerationRequestCompilation":
        if self.compilation_kind == "qualification" and (
            self.execution_stack_hash is None
            or self.mode is not VideoGenerationMode.IMAGE_TO_VIDEO
            or tuple(item.role for item in self.image_bindings)
            != ("first_frame", "last_frame")
            or self.c4_multi_anchor_binding is not None
            or self.continuity_binding is not None
            or self.hard_cut_keyframe_binding is not None
            or not self.seal_terminal_frame
            or self.media_bindings
            or self.negative_prompt_text
            or self.seed is None
            or self.seed < 0
        ):
            raise ValueError(
                "qualification compilation requires one exact sealed FL2VA shape"
            )
        if self.compilation_kind == "c4_qualification" and (
            self.execution_stack_hash is None
            or self.mode is not VideoGenerationMode.IMAGE_TO_VIDEO
            or tuple(item.role for item in self.image_bindings)
            != ("first_frame", "last_frame", "reference")
            or self.c4_multi_anchor_binding is None
            or self.c4_multi_anchor_binding.tier.value != "motion_boundary"
            or self.continuity_binding is not None
            or self.hard_cut_keyframe_binding is not None
            or not self.seal_terminal_frame
            or tuple((item.kind, item.role) for item in self.media_bindings)
            != (("video", "reference_video"),)
            or self.negative_prompt_text
            or self.seed is None
            or self.seed < 0
        ):
            raise ValueError(
                "C4 qualification compilation requires one exact sealed "
                "four-anchor motion-boundary shape"
            )
        expected = canonical_sha256(
            {
                "schema": "video-generation-request-compilation/1",
                **self.model_dump(mode="json", exclude={"compilation_hash"}),
            }
        )
        if self.compilation_hash != expected:
            raise ValueError("compilation_hash does not match request compilation")
        return self

    @classmethod
    def create(
        cls,
        *,
        compilation_kind: Literal[
            "provider_neutral",
            "qualification",
            "c4_qualification",
        ],
        **values: object,
    ) -> "VideoGenerationRequestCompilation":
        data = {"compilation_kind": compilation_kind, **values}
        candidate = cls.model_construct(**data, compilation_hash="0" * 64)
        data["compilation_hash"] = canonical_sha256(
            {
                "schema": "video-generation-request-compilation/1",
                **candidate.model_dump(
                    mode="json",
                    exclude={"compilation_hash"},
                    warnings=False,
                ),
            }
        )
        return cls.model_validate(data)


def compile_video_generation_request(
    projection: VideoGenerationRequestCompilation,
) -> VideoGenerationRequest:
    """Construct one request only from a validated, hash-bound projection."""

    reopened = VideoGenerationRequestCompilation.model_validate(
        projection.model_dump(mode="python")
    )
    values = reopened.model_dump(
        mode="python",
        exclude={"compilation_kind", "compilation_hash"},
    )
    return VideoGenerationRequest.create(
        target_visual_strategy="generated_video",
        **values,
    )


def compile_provider_video_request(
    *,
    provider_bound: ProviderBoundVideoRequest,
    requirement: ProviderNeutralVideoRequirement,
    compiler_id: str,
    compiler_version: str,
    capabilities: VideoProviderCapabilities,
    supports_native_control: bool = False,
    native_prompt: ProviderNativePrompt | None = None,
) -> ProviderRequestCompilationResult:
    """Compile mechanical provider grammar without selecting or invoking a Provider."""

    try:
        ProviderBoundVideoRequest.model_validate(
            provider_bound.model_dump(mode="python")
        )
        ProviderNeutralVideoRequirement.model_validate(
            requirement.model_dump(mode="python")
        )
    except ValidationError:
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH,
            ("requirement_hash",),
        )

    contract = provider_bound.compiler_contract
    if (
        contract.compiler_id != compiler_id
        or contract.compiler_version != compiler_version
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.COMPILER_VERSION_UNSUPPORTED,
            ("compiler_contract",),
        )
    if requirement.requirement_hash != provider_bound.requirement_hash:
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH,
            ("requirement_hash",),
        )
    if (
        requirement.contract_version == "provider-neutral-video-requirement/4"
        and native_prompt is None
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
            ("generation_intent",),
        )
    expected_bindings = tuple(
        (native_binding_role(item.role), item.asset_id, item.asset_sha256)
        for item in requirement.asset_evidence
    )
    if requirement.c4_multi_anchor_binding is not None:
        native_order = {
            "first_frame": 0,
            "last_frame": 1,
            "reference": 2,
            "reference_video": 3,
            "reference_audio": 4,
        }
        expected_bindings = tuple(
            sorted(
                expected_bindings,
                key=lambda item: (native_order[item[0]], item[1]),
            )
        )
    actual_bindings = tuple(
        (role, item.asset_id, item.asset_sha256)
        for role, item in zip(
            provider_bound.binding_roles,
            provider_bound.input_assets,
            strict=True,
        )
    )
    if (
        requirement.target_shot.shot_id != provider_bound.target_shot_id
        or requirement.target_shot.revision != provider_bound.target_shot_revision
        or requirement.target_shot.content_hash
        != provider_bound.target_shot_content_hash
        or requirement_mode(requirement.generation_mode) is not provider_bound.mode
        or expected_bindings != actual_bindings
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH,
            ("requirement_projection",),
        )
    if not requirement_output_matches(
        requirement,
        provider_bound.output_requirement,
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.OUTPUT_UNSUPPORTED,
            ("output_need",),
        )
    selected = tuple(
        variant
        for variant in capabilities.variants
        if variant.capability_id == provider_bound.capability_id
    )
    if len(selected) != 1:
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH,
            ("selection",),
        )
    capability = selected[0]
    if (
        provider_bound.provider_name != capabilities.provider_name
        or provider_bound.provider_kind != capability.provider_kind
        or provider_bound.model_id != capability.model_id
        or provider_bound.provider_profile.profile_version
        != capability.profile_version
        or provider_bound.execution_kind is not capability.execution_kind
        or provider_bound.billing_kind is not capability.billing_kind
        or provider_bound.mode is not capability.mode
        or provider_bound.capability_fingerprint
        != _capability_fingerprint(capability)
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH,
            ("selection",),
        )
    if (
        capability.execution_kind is VideoExecutionKind.REMOTE
        and capability.output_recovery_strategy
        not in {
            VideoOutputRecoveryStrategy.DURABLE_FILE_ID,
            VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
        }
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.OUTPUT_LOCATOR_NOT_RECOVERABLE,
            ("selection.output_recovery_strategy",),
        )
    if (
        requirement.generation_intent.camera_intent.expression_strength
        is ExpressionStrength.NATIVE_CONTROL_REQUIRED
        and not supports_native_control
    ):
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.NATIVE_CONTROL_UNSUPPORTED,
            ("generation_intent.camera_intent.expression_strength",),
        )
    quality = requirement.quality_need
    unsupported_quality = tuple(
        path
        for path, present in (
            (
                "quality_need.native_enforcement_required",
                quality.native_enforcement_required,
            ),
            ("quality_need.minimum_raster", quality.minimum_raster is not None),
            ("quality_need.minimum_codec", quality.minimum_codec is not None),
        )
        if present
    )
    if unsupported_quality:
        return _unsupported(
            provider_bound,
            requirement,
            ProviderRequirementUnsupportedReason.OUTPUT_UNSUPPORTED,
            unsupported_quality,
        )

    bindings = tuple(
        sorted(
            (
                VideoImageReferenceBinding(
                    role=role,
                    asset_id=asset.asset_id,
                    asset_sha256=asset.asset_sha256,
                    mime_type=asset.mime_type,
                    width=_required_measurement(asset.width, "width"),
                    height=_required_measurement(asset.height, "height"),
                    size_bytes=asset.size_bytes,
                )
                for role, asset in zip(
                    provider_bound.binding_roles,
                    provider_bound.input_assets,
                    strict=True,
                )
                if role in {"first_frame", "last_frame", "reference"}
            ),
            key=lambda item: (_ROLE_ORDER[item.role], item.asset_id),
        )
    )
    media_bindings = tuple(
        sorted(
            (
                VideoMediaReferenceBinding(
                    kind="video" if role == "reference_video" else "audio",
                    role=role,
                    asset_id=asset.asset_id,
                    asset_sha256=asset.asset_sha256,
                    mime_type=asset.mime_type,
                    duration_millis=_required_measurement(
                        asset.duration_millis,
                        "duration_millis",
                    ),
                    size_bytes=_required_measurement(asset.size_bytes, "size_bytes"),
                    width=asset.width,
                    height=asset.height,
                    fps=asset.fps,
                )
                for role, asset in zip(
                    provider_bound.binding_roles,
                    provider_bound.input_assets,
                    strict=True,
                )
                if role in {"reference_video", "reference_audio"}
            ),
            key=lambda item: (_MEDIA_ROLE_ORDER[item.role], item.asset_id),
        )
    )
    lifecycle = provider_bound.lifecycle
    prompt = (
        native_prompt.prompt_text
        if native_prompt is not None
        else _compile_neutral_prompt(requirement)
    )
    projection = VideoGenerationRequestCompilation.create(
        compilation_kind="provider_neutral",
        generation_id=lifecycle.generation_id,
        provider_name=provider_bound.provider_name,
        provider_kind=provider_bound.provider_kind,
        model_id=provider_bound.model_id,
        provider_profile=provider_bound.provider_profile,
        requirement_hash=requirement.requirement_hash,
        provider_bound_request_hash=provider_bound.provider_bound_request_hash,
        adapter_compiler_id=contract.compiler_id,
        adapter_compiler_version=contract.compiler_version,
        adapter_compiler_hash=contract.compiler_hash,
        execution_stack_hash=None,
        target_shot_id=provider_bound.target_shot_id,
        target_shot_revision=provider_bound.target_shot_revision,
        target_shot_content_hash=provider_bound.target_shot_content_hash,
        target_asset_role=lifecycle.target_asset_role,
        mode=provider_bound.mode,
        prompt_text=prompt,
        negative_prompt_text="",
        image_bindings=bindings,
        c4_multi_anchor_binding=requirement.c4_multi_anchor_binding,
        continuity_binding=lifecycle.continuity_binding,
        hard_cut_keyframe_binding=lifecycle.hard_cut_keyframe_binding,
        seal_terminal_frame=lifecycle.seal_terminal_frame,
        media_bindings=media_bindings,
        output_requirement=provider_bound.output_requirement,
        seed=None,
        base_project=lifecycle.base_project,
        base_registry=lifecycle.base_registry,
        base_dependency_graph=lifecycle.base_dependency_graph,
        input_artifact_ids=lifecycle.input_artifact_ids,
        output_asset_id=lifecycle.output_asset_id,
    )
    request = compile_video_generation_request(projection)
    payload_hash = canonical_sha256(
        {
            "schema": "provider-video-payload-projection/1",
            "request_input_hash": request.request_input_hash,
        }
    )
    return CompiledProviderVideoRequest.create(
        requirement_hash=requirement.requirement_hash,
        provider_bound_request_hash=provider_bound.provider_bound_request_hash,
        adapter_compiler_id=contract.compiler_id,
        adapter_compiler_version=contract.compiler_version,
        adapter_compiler_hash=contract.compiler_hash,
        provider_native_prompt=prompt,
        request=request,
        payload_projection_hash=payload_hash,
    )


def _capability_fingerprint(capability: VideoCapabilityVariant) -> str:
    from ai_video.production._video_capability_fingerprint import (
        project_capability_variant,
    )

    return canonical_sha256(project_capability_variant(capability))


def _compile_neutral_prompt(requirement: ProviderNeutralVideoRequirement) -> str:
    intent = requirement.generation_intent
    scene = intent.scene_continuity
    fields: tuple[tuple[str, str], ...] = (
        ("generation_mode", requirement.generation_mode.value),
        ("continuity_mode", requirement.continuity_mode.value),
        ("motion_requirement", requirement.motion_requirement.value),
        ("audio_need", requirement.audio_need.value),
        ("open_state", _state_value(intent.open_state)),
        ("close_state", _state_value(intent.close_state)),
        (
            "identity_characters",
            _tuple_value(intent.identity_continuity.character_ids),
        ),
        ("identity_preservation", intent.identity_continuity.preservation.value),
        (
            "identity_allowed_variation",
            _tuple_value(intent.identity_continuity.allowed_variation),
        ),
        ("scene_id", scene.scene_id if scene is not None else "unspecified"),
        ("scene_time", scene.time_of_day if scene is not None else "unspecified"),
        ("scene_mood", scene.mood if scene is not None else "unspecified"),
        (
            "scene_constraints",
            _tuple_value(scene.state_constraints)
            if scene is not None
            else "unspecified",
        ),
        ("space_subject_position", intent.space_continuity.subject_position),
        ("space_screen_direction", intent.space_continuity.screen_direction),
        ("space_entrance", intent.space_continuity.entrance_state or "unspecified"),
        ("space_exit", intent.space_continuity.exit_state or "unspecified"),
        ("space_crossing", intent.space_continuity.crossing_policy),
        ("axis_camera", intent.axis_continuity.camera_axis),
        ("axis_framing", intent.axis_continuity.framing_continuity),
        ("axis_crossing", intent.axis_continuity.crossing_policy),
        ("action_start", intent.subject_action.start_state),
        ("action_progression", intent.subject_action.progression),
        ("action_endpoint", _endpoint_value(intent.subject_action.endpoint)),
        (
            "action_endpoint_change",
            str(intent.subject_action.endpoint.required_change).lower(),
        ),
        ("motion_onset", intent.motion_envelope.onset),
        ("motion_peak", intent.motion_envelope.peak),
        ("motion_settle", intent.motion_envelope.settle),
        ("motion_direction", intent.motion_envelope.direction),
        ("motion_amplitude", intent.motion_envelope.amplitude_class),
        ("camera_movement", intent.camera_intent.movement),
        ("camera_stability", intent.camera_intent.stability),
        ("camera_framing", intent.camera_intent.framing_intent),
        ("camera_start", intent.camera_endpoint.start_framing),
        ("camera_end", intent.camera_endpoint.end_framing),
        ("camera_position_lock", str(intent.camera_endpoint.position_lock).lower()),
        (
            "camera_orientation_lock",
            str(intent.camera_endpoint.orientation_lock).lower(),
        ),
        ("pacing_cadence", intent.pacing.cadence),
        ("pacing_tempo", intent.pacing.tempo_class),
        (
            "pacing_duration",
            str(intent.pacing.shot_duration_seconds or "unspecified"),
        ),
        (
            "semantic_reference_roles",
            _tuple_value(
                tuple(role.value for role in requirement.semantic_reference_roles)
            ),
        ),
        ("quality_objective", requirement.quality_need.objective_tier),
    )
    fidelity = requirement.product_fidelity_requirement
    approval = requirement.approved_commercial_source
    if fidelity is not None and approval is not None:
        fields = (
            *fields,
            ("commercial_execution_class", requirement.commercial_execution_class or "unspecified"),
            ("product_id", fidelity.product_id),
            ("product_sku_id", fidelity.sku_id),
            ("product_reference_set_id", fidelity.product_reference_set_id),
            ("product_reference_set_hash", fidelity.product_reference_set_hash),
            (
                "product_source_asset_hashes",
                _tuple_value(fidelity.product_source_asset_hashes),
            ),
            ("product_source_strategy", fidelity.strategy.value),
            ("product_packaging_form", fidelity.packaging_form),
            ("product_bottle_silhouette", fidelity.bottle_silhouette),
            ("product_dominant_color", fidelity.dominant_color),
            ("product_cap_color", fidelity.cap_color),
            ("product_logo_label_identity", fidelity.logo_label_identity),
            (
                "product_protected_text_zones",
                _tuple_value(fidelity.protected_text_zones),
            ),
            ("commercial_source_approval_id", approval.approval_id),
            ("commercial_source_approval_hash", approval.approval_content_hash),
            ("approved_first_frame_asset_id", approval.keyframe_asset_id),
            ("approved_first_frame_sha256", approval.keyframe_sha256),
        )
    return unicodedata.normalize(
        "NFC",
        "; ".join(f"{name}={value}" for name, value in fields),
    )


def _tuple_value(values: tuple[str, ...]) -> str:
    return ",".join(values) if values else "none"


def _state_value(state: TypedStateReference) -> str:
    kind = state.kind.value
    value = state.state_ref or state.state_text or state.state_hash or "unspecified"
    return f"{kind}:{value}:change={str(state.required_change).lower()}"


def _endpoint_value(endpoint: ActionEndpoint) -> str:
    return endpoint.state_ref or endpoint.state_text or endpoint.state_hash or "unspecified"


def _required_measurement(value: int | None, label: str) -> int:
    if value is None:
        raise ValueError(f"provider-bound image {label} is missing")
    return value


def _unsupported(
    provider_bound: ProviderBoundVideoRequest,
    requirement: ProviderNeutralVideoRequirement,
    reason: ProviderRequirementUnsupportedReason,
    paths: tuple[str, ...],
) -> ProviderRequirementUnsupported:
    return ProviderRequirementUnsupported(
        requirement_hash=requirement.requirement_hash,
        provider_bound_request_hash=provider_bound.provider_bound_request_hash,
        selected_capability_id=provider_bound.capability_id,
        reason=reason,
        unsupported_field_paths=paths,
    )


__all__ = [
    "CompiledProviderVideoRequest",
    "ProviderRequestCompilationResult",
    "ProviderRequirementUnsupported",
    "ProviderRequirementUnsupportedReason",
    "ProviderVideoRequestCompiler",
    "VideoGenerationRequestCompilation",
    "compile_provider_video_request",
    "compile_video_generation_request",
    "require_compiled_provider_request",
]
