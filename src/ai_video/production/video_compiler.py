"""Pure provider request compilation from a sealed Router projection."""

from __future__ import annotations

import unicodedata
from enum import Enum
from typing import Literal, Protocol, runtime_checkable

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._video_requirement_routing import (
    native_binding_role,
    requirement_mode,
    requirement_output_matches,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.video import (
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import VideoMediaReferenceBinding
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


def compile_provider_video_request(
    *,
    provider_bound: ProviderBoundVideoRequest,
    requirement: ProviderNeutralVideoRequirement,
    compiler_id: str,
    compiler_version: str,
    capabilities: VideoProviderCapabilities,
    supports_native_control: bool = False,
) -> ProviderRequestCompilationResult:
    """Compile mechanical provider grammar without selecting or invoking a Provider."""

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
    expected_bindings = tuple(
        (native_binding_role(item.role), item.asset_id, item.asset_sha256)
        for item in requirement.asset_evidence
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
    prompt = _compile_neutral_prompt(requirement)
    request = VideoGenerationRequest.create(
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
        target_shot_id=provider_bound.target_shot_id,
        target_shot_revision=provider_bound.target_shot_revision,
        target_shot_content_hash=provider_bound.target_shot_content_hash,
        target_asset_role=lifecycle.target_asset_role,
        target_visual_strategy="generated_video",
        mode=provider_bound.mode,
        prompt_text=prompt,
        negative_prompt_text="",
        image_bindings=bindings,
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
    fields = (
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
    "compile_provider_video_request",
    "require_compiled_provider_request",
]
