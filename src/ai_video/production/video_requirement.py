from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Any, Literal

from pydantic import Field, ValidationInfo, field_validator, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import Character, Scene, Shot, StrictModel


_REQUIREMENT_CONTRACT_VERSION = "provider-neutral-video-requirement/1"
_UNSEALED_HASH = "0" * 64
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"

UNSPECIFIED: Literal["unspecified"] = "unspecified"


class GenerationMode(str, Enum):
    STATIC_IMAGE = "static_image"
    IMAGE_MOTION = "image_motion"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    FIRST_LAST_FRAME_VIDEO = "first_last_frame_video"
    REFERENCE_TO_VIDEO = "reference_to_video"
    VIDEO_EDIT = "video_edit"
    VIDEO_EXTEND = "video_extend"
    HYBRID = "hybrid"


class GenerationOperation(str, Enum):
    AUTO = "auto"
    VIDEO_EDIT = "video_edit"
    VIDEO_EXTEND = "video_extend"


class ContinuityMode(str, Enum):
    EXACT_TERMINAL = "exact_terminal"
    REFERENCE = "reference"
    SEMANTIC = "semantic"
    NONE = "none"


class MotionRequirement(str, Enum):
    NONE = "none"
    LIGHT_TRANSFORM = "light_transform"
    GRAPHIC = "graphic"
    CHARACTER_ACTION = "character_action"
    FREE_COMPLEX = "free_complex"
    HERO_OR_REPAIR = "hero_or_repair"


class ContinuityStateKind(str, Enum):
    UNSPECIFIED = UNSPECIFIED
    TYPED_REF = "typed_ref"
    TYPED_TEXT = "typed_text"
    TYPED_HASH = "typed_hash"


class IdentityPreservation(str, Enum):
    UNSPECIFIED = UNSPECIFIED
    EXACT = "exact"
    BOUNDED_VARIATION = "bounded_variation"


class OutputGeometryPolicy(str, Enum):
    EXACT = "exact"
    ADAPTIVE = "adaptive"


class AudioNeed(str, Enum):
    FORBIDDEN = "forbidden"
    OPTIONAL = "optional"
    REQUIRED = "required"


class ExpressionStrength(str, Enum):
    SEMANTIC_PROMPT_ALLOWED = "semantic_prompt_allowed"
    NATIVE_CONTROL_REQUIRED = "native_control_required"


class SemanticReferenceRole(str, Enum):
    IDENTITY = "identity"
    SCENE = "scene"
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"
    CONTINUITY_TERMINAL = "continuity_terminal"
    VIDEO_REFERENCE = "video_reference"
    AUDIO_REFERENCE = "audio_reference"


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise ValueError("provider-neutral requirement text must use Unicode NFC")
    return value


class TypedStateReference(StrictModel):
    kind: ContinuityStateKind = ContinuityStateKind.UNSPECIFIED
    state_ref: str | None = Field(default=None, pattern=_SAFE_ID)
    state_text: str | None = None
    state_hash: str | None = Field(default=None, pattern=_SHA256)
    required_change: bool = False

    @model_validator(mode="after")
    def _validate_state_payload(self) -> "TypedStateReference":
        if self.kind is ContinuityStateKind.UNSPECIFIED:
            if any(
                value is not None
                for value in (self.state_ref, self.state_text, self.state_hash)
            ):
                raise ValueError(
                    "UNSPECIFIED state kind cannot carry state_ref/text/hash payload"
                )
            return self
        expected = {
            ContinuityStateKind.TYPED_REF: self.state_ref,
            ContinuityStateKind.TYPED_TEXT: self.state_text,
            ContinuityStateKind.TYPED_HASH: self.state_hash,
        }.get(self.kind)
        if expected is None:
            raise ValueError(f"{self.kind.value} state kind requires its typed payload")
        populated = sum(
            value is not None
            for value in (self.state_ref, self.state_text, self.state_hash)
        )
        if populated != 1:
            raise ValueError("typed state kind requires exactly one matching payload")
        return self


class IdentityContinuity(StrictModel):
    character_ids: tuple[str, ...] = ()
    preservation: IdentityPreservation = IdentityPreservation.UNSPECIFIED
    allowed_variation: tuple[str, ...] = ()

    @field_validator("character_ids")
    @classmethod
    def _canonicalize_character_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(value))

    @field_validator("allowed_variation")
    @classmethod
    def _canonicalize_allowed_variation(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def _require_evidence_for_exact(self) -> "IdentityContinuity":
        if self.preservation is IdentityPreservation.EXACT and not self.character_ids:
            raise ValueError(
                "EXACT identity preservation requires at least one character_id"
            )
        return self


class SceneContinuity(StrictModel):
    scene_id: str = Field(pattern=_SAFE_ID)
    time_of_day: str | None = None
    mood: str | None = None
    state_constraints: tuple[str, ...] = ()


class SpaceContinuity(StrictModel):
    subject_position: str = UNSPECIFIED
    screen_direction: str = UNSPECIFIED
    entrance_state: str | None = None
    exit_state: str | None = None
    crossing_policy: str = UNSPECIFIED


class AxisContinuity(StrictModel):
    camera_axis: str = UNSPECIFIED
    framing_continuity: str = UNSPECIFIED
    crossing_policy: str = UNSPECIFIED


class ActionEndpoint(StrictModel):
    state_ref: str | None = Field(default=None, pattern=_SAFE_ID)
    state_text: str | None = None
    state_hash: str | None = Field(default=None, pattern=_SHA256)
    required_change: bool = False

    @model_validator(mode="after")
    def _validate_endpoint_identity(self) -> "ActionEndpoint":
        populated = sum(
            value is not None
            for value in (self.state_ref, self.state_text, self.state_hash)
        )
        if populated > 1:
            raise ValueError("action endpoint allows at most one typed identity")
        return self


class SubjectAction(StrictModel):
    start_state: str = UNSPECIFIED
    progression: str = UNSPECIFIED
    endpoint: ActionEndpoint = Field(default_factory=ActionEndpoint)


class MotionEnvelope(StrictModel):
    onset: str = UNSPECIFIED
    peak: str = UNSPECIFIED
    settle: str = UNSPECIFIED
    direction: str = UNSPECIFIED
    amplitude_class: str = UNSPECIFIED


class Pacing(StrictModel):
    cadence: str = UNSPECIFIED
    tempo_class: str = UNSPECIFIED
    shot_duration_seconds: float | None = Field(default=None, gt=0)


class CameraIntent(StrictModel):
    movement: str = UNSPECIFIED
    stability: str = UNSPECIFIED
    framing_intent: str = UNSPECIFIED
    expression_strength: ExpressionStrength = (
        ExpressionStrength.SEMANTIC_PROMPT_ALLOWED
    )


class CameraEndpoint(StrictModel):
    start_framing: str = UNSPECIFIED
    end_framing: str = UNSPECIFIED
    position_lock: bool = False
    orientation_lock: bool = False


class GenerationIntent(StrictModel):
    open_state: TypedStateReference = Field(default_factory=TypedStateReference)
    close_state: TypedStateReference = Field(default_factory=TypedStateReference)
    identity_continuity: IdentityContinuity = Field(
        default_factory=IdentityContinuity
    )
    scene_continuity: SceneContinuity | None = None
    space_continuity: SpaceContinuity = Field(default_factory=SpaceContinuity)
    axis_continuity: AxisContinuity = Field(default_factory=AxisContinuity)
    subject_action: SubjectAction = Field(default_factory=SubjectAction)
    motion_envelope: MotionEnvelope = Field(default_factory=MotionEnvelope)
    pacing: Pacing = Field(default_factory=Pacing)
    camera_intent: CameraIntent = Field(default_factory=CameraIntent)
    camera_endpoint: CameraEndpoint = Field(default_factory=CameraEndpoint)


class OutputNeed(StrictModel):
    timing_mode: Literal[
        "fixed",
        "content_driven",
        "voice_driven",
        "provider_selected",
        "frame_count",
    ] = "fixed"
    duration_seconds: float | None = Field(default=None, gt=0, le=600)
    frame_count: int | None = Field(default=None, strict=True, gt=0, le=144_000)
    geometry_policy: OutputGeometryPolicy = OutputGeometryPolicy.EXACT
    width: int | None = Field(default=None, gt=0, le=8192)
    height: int | None = Field(default=None, gt=0, le=8192)
    aspect_ratio: str | None = None
    fps: int | None = Field(default=None, gt=0, le=240)
    container_mime: str | None = Field(default=None, pattern=_MIME_TYPE)

    @model_validator(mode="after")
    def _validate_timing(self) -> "OutputNeed":
        if self.timing_mode == "frame_count":
            if self.frame_count is None or self.duration_seconds is not None:
                raise ValueError("frame_count timing requires only frame_count")
        elif self.frame_count is not None:
            raise ValueError("non-frame_count timing cannot carry frame_count")
        return self


class QualityNeed(StrictModel):
    objective_tier: Literal["draft", "preview", "production", "hero"] = "production"
    minimum_raster: str | None = None
    minimum_codec: str | None = None
    native_enforcement_required: bool = False


class CapabilityNeed(StrictModel):
    needs_identity_reference: bool = False
    needs_scene_reference: bool = False
    needs_first_frame: bool = False
    needs_last_frame: bool = False
    needs_terminal_reference: bool = False
    needs_native_audio: bool = False
    needs_continuity_state: bool = False
    max_reference_count: int | None = Field(default=None, ge=0, le=30)
    accepts_local_execution: bool = True
    accepts_remote_execution: bool = True


class AssetEvidence(StrictModel):
    role: SemanticReferenceRole
    asset_id: str = Field(pattern=_SAFE_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    canonical_owner_id: str | None = Field(default=None, pattern=_SAFE_ID)
    canonical_owner_content_hash: str | None = Field(default=None, pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    size_bytes: int | None = Field(default=None, gt=0)
    duration_millis: int | None = Field(default=None, strict=True, gt=0)
    fps: int | None = Field(default=None, strict=True, gt=0, le=240)


class ReviewEvidenceLink(StrictModel):
    evidence_ref: str = Field(pattern=_SAFE_ID)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    review_decision_hash: str | None = Field(default=None, pattern=_SHA256)


class ProviderNeutralGenerationIntentProjection(StrictModel):
    generation_intent: GenerationIntent
    generation_operation: GenerationOperation = GenerationOperation.AUTO
    semantic_reference_roles: tuple[SemanticReferenceRole, ...] = ()
    media_reference_asset_ids: tuple[str, ...] = ()
    output_need: OutputNeed
    audio_need: AudioNeed
    quality_need: QualityNeed
    projection_hash: str = Field(pattern=_SHA256)

    @field_validator("semantic_reference_roles")
    @classmethod
    def _canonicalize_semantic_roles(
        cls, value: tuple[SemanticReferenceRole, ...]
    ) -> tuple[SemanticReferenceRole, ...]:
        return tuple(sorted(set(value), key=lambda role: role.value))

    @field_validator("media_reference_asset_ids")
    @classmethod
    def _canonicalize_media_asset_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(re.fullmatch(_SAFE_ID, item) is None for item in value):
            raise ValueError("media reference asset IDs must use safe exact identities")
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def _validate_media_selection_roles(
        self,
    ) -> "ProviderNeutralGenerationIntentProjection":
        media_roles = {
            SemanticReferenceRole.VIDEO_REFERENCE,
            SemanticReferenceRole.AUDIO_REFERENCE,
        }
        if (
            self.media_reference_asset_ids
            and not media_roles.intersection(self.semantic_reference_roles)
            and self.generation_operation is GenerationOperation.AUTO
        ):
            raise ValueError(
                "exact media selection requires a media role or video operation"
            )
        return self

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema": "provider-neutral-generation-intent/1",
            **self.model_dump(mode="json", exclude={"projection_hash"}),
        }

    @model_validator(mode="after")
    def _validate_projection_hash(
        self,
    ) -> "ProviderNeutralGenerationIntentProjection":
        if self.projection_hash != canonical_sha256(self._hash_payload()):
            raise ValueError("projection_hash does not match generation intent")
        return self

    @classmethod
    def create(
        cls,
        **values: object,
    ) -> "ProviderNeutralGenerationIntentProjection":
        data = dict(values)
        data["semantic_reference_roles"] = tuple(
            sorted(
                {
                    SemanticReferenceRole(role)
                    for role in data.get("semantic_reference_roles", ())
                },
                key=lambda role: role.value,
            )
        )
        data["media_reference_asset_ids"] = tuple(
            sorted(set(data.get("media_reference_asset_ids", ())))
        )
        candidate = cls.model_construct(**data, projection_hash=_UNSEALED_HASH)
        data["projection_hash"] = canonical_sha256(candidate._hash_payload())
        return cls.model_validate(data)


class ProviderNeutralVideoRequirement(StrictModel):
    contract_version: Literal[_REQUIREMENT_CONTRACT_VERSION] = (
        _REQUIREMENT_CONTRACT_VERSION
    )
    requirement_id: str = Field(pattern=_SAFE_ID)
    requirement_hash: str = Field(pattern=_SHA256)
    source_request_content_hash: str = Field(pattern=_SHA256)
    intent_evidence_hash: str = Field(pattern=_SHA256)
    generation_intent_hash: str = Field(pattern=_SHA256)
    target_shot: Shot
    scene: Scene
    characters: tuple[Character, ...] = ()
    review_evidence: ReviewEvidenceLink | None = None
    asset_evidence: tuple[AssetEvidence, ...] = Field(default_factory=tuple)
    generation_mode: GenerationMode
    continuity_mode: ContinuityMode
    motion_requirement: MotionRequirement
    generation_intent: GenerationIntent
    semantic_reference_roles: tuple[SemanticReferenceRole, ...] = ()
    capability_need: CapabilityNeed = Field(default_factory=CapabilityNeed)
    output_need: OutputNeed = Field(default_factory=OutputNeed)
    audio_need: AudioNeed = AudioNeed.OPTIONAL
    quality_need: QualityNeed = Field(default_factory=QualityNeed)

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema": _REQUIREMENT_CONTRACT_VERSION,
            **self.model_dump(
                mode="json",
                exclude={"contract_version", "requirement_id", "requirement_hash"},
            ),
        }

    @classmethod
    def create(cls, **values: object) -> "ProviderNeutralVideoRequirement":
        payload: dict[str, object] = dict(values)
        payload.setdefault("contract_version", _REQUIREMENT_CONTRACT_VERSION)
        payload["requirement_id"] = "video-requirement-unsealed"
        payload["requirement_hash"] = _UNSEALED_HASH

        draft = cls.model_validate(payload, context={"allow_unsealed": True})
        requirement_hash = canonical_sha256(draft._hash_payload())
        requirement_id = f"video-requirement-{requirement_hash[:24]}"
        sealed_payload = draft.model_dump(mode="python")
        sealed_payload["requirement_id"] = requirement_id
        sealed_payload["requirement_hash"] = requirement_hash
        return cls.model_validate(sealed_payload)

    @model_validator(mode="after")
    def _validate_seal(
        self,
        validation_info: ValidationInfo,
    ) -> "ProviderNeutralVideoRequirement":
        if (
            self.requirement_hash == _UNSEALED_HASH
            and validation_info.context
            and validation_info.context.get("allow_unsealed") is True
        ):
            return self
        expected_hash = canonical_sha256(self._hash_payload())
        if self.requirement_hash != expected_hash:
            raise ValueError("requirement_hash does not match requirement content")
        if self.requirement_id != f"video-requirement-{expected_hash[:24]}":
            raise ValueError("requirement_id does not match requirement_hash")
        return self

    @field_validator("characters")
    @classmethod
    def _canonicalize_characters(
        cls, value: tuple[Character, ...]
    ) -> tuple[Character, ...]:
        return tuple(
            sorted(value, key=lambda character: character.character_id)
        )

    @field_validator("asset_evidence")
    @classmethod
    def _canonicalize_asset_evidence(
        cls, value: tuple[AssetEvidence, ...]
    ) -> tuple[AssetEvidence, ...]:
        return tuple(
            sorted(
                value,
                key=lambda asset: (asset.role.value, asset.asset_id),
            )
        )

    @field_validator("semantic_reference_roles")
    @classmethod
    def _canonicalize_semantic_roles(
        cls, value: tuple[SemanticReferenceRole, ...]
    ) -> tuple[SemanticReferenceRole, ...]:
        return tuple(sorted(set(value), key=lambda role: role.value))

    @model_validator(mode="after")
    def _enforce_asset_role_binding(self) -> "ProviderNeutralVideoRequirement":
        asset_roles = {asset.role for asset in self.asset_evidence}
        semantic_roles = set(self.semantic_reference_roles)
        if semantic_roles != asset_roles:
            raise ValueError(
                "semantic reference roles and asset evidence roles must match exactly"
            )
        if self.target_shot.scene_id != self.scene.scene_id:
            raise ValueError("requirement Scene must match the exact target Shot")
        character_ids = tuple(character.character_id for character in self.characters)
        if tuple(sorted(self.target_shot.character_ids)) != character_ids:
            raise ValueError("requirement Characters must match the exact target Shot")
        intent = self.generation_intent
        if (
            intent.scene_continuity is not None
            and intent.scene_continuity.scene_id != self.scene.scene_id
        ):
            raise ValueError("typed scene continuity must match requirement Scene")
        declared_characters = tuple(sorted(intent.identity_continuity.character_ids))
        if declared_characters and declared_characters != character_ids:
            raise ValueError("typed identity continuity must match requirement Characters")
        return self

    @model_validator(mode="after")
    def _enforce_recursive_forbidden_fields(
        self,
    ) -> "ProviderNeutralVideoRequirement":
        forbidden_tokens = (
            "provider_name",
            "model_id",
            "endpoint_id",
            "profile_id",
            "workflow_hash",
            "workflow_node_id",
            "prompt_text",
            "payload",
            "skill_name",
            "asset_uri",
            "permit_id",
            "fallback_order",
            "submit_url",
            "signed_url",
            "candidate_index",
        )
        for token in forbidden_tokens:
            if token in self.model_fields_set:
                raise ValueError(
                    f"forbidden field {token!r} cannot appear on"
                    " ProviderNeutralVideoRequirement"
                )
        payload = self.model_dump(mode="python")
        _reject_forbidden_paths(payload, forbidden_tokens)
        _require_recursive_nfc(payload)
        return self


class VerifiedGenerationRequirementProjection(StrictModel):
    """Cycle-neutral result of the Planning freshness boundary."""

    requirement: ProviderNeutralVideoRequirement
    plan_hash: str = Field(pattern=_SHA256)
    verified_source_request_content_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    projection_hash: str = Field(pattern=_SHA256)

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema": "verified-generation-requirement-projection/1",
            **self.model_dump(mode="json", exclude={"projection_hash"}),
        }

    @model_validator(mode="after")
    def _validate_projection(self) -> "VerifiedGenerationRequirementProjection":
        shot = self.requirement.target_shot
        if (
            self.verified_source_request_content_hash
            != self.requirement.source_request_content_hash
            or self.target_shot_id != shot.shot_id
            or self.target_shot_revision != shot.revision
            or self.target_shot_content_hash != shot.content_hash
        ):
            raise ValueError("verified requirement projection lineage is inconsistent")
        if self.projection_hash != canonical_sha256(self._hash_payload()):
            raise ValueError("projection_hash does not match verified requirement")
        return self

    @classmethod
    def create(cls, **values: object) -> "VerifiedGenerationRequirementProjection":
        data = dict(values)
        candidate = cls.model_construct(**data, projection_hash=_UNSEALED_HASH)
        data["projection_hash"] = canonical_sha256(candidate._hash_payload())
        return cls.model_validate(data)


def _reject_forbidden_paths(node: Any, forbidden_tokens: tuple[str, ...]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in forbidden_tokens:
                raise ValueError(
                    f"forbidden path key {key!r} detected in requirement payload"
                )
            _reject_forbidden_paths(value, forbidden_tokens)
        return
    if isinstance(node, list | tuple):
        for item in node:
            _reject_forbidden_paths(item, forbidden_tokens)
        return
    if hasattr(node, "model_dump") and callable(node.model_dump):
        _reject_forbidden_paths(node.model_dump(mode="python"), forbidden_tokens)


def _require_recursive_nfc(node: Any) -> None:
    if isinstance(node, str):
        _normalize_text(node)
        return
    if isinstance(node, dict):
        for key, value in node.items():
            _normalize_text(str(key))
            _require_recursive_nfc(value)
        return
    if isinstance(node, list | tuple):
        for item in node:
            _require_recursive_nfc(item)


__all__ = [
    "UNSPECIFIED",
    "ActionEndpoint",
    "AssetEvidence",
    "AudioNeed",
    "AxisContinuity",
    "CameraEndpoint",
    "CameraIntent",
    "CapabilityNeed",
    "ContinuityMode",
    "ContinuityStateKind",
    "ExpressionStrength",
    "GenerationIntent",
    "GenerationMode",
    "GenerationOperation",
    "IdentityContinuity",
    "IdentityPreservation",
    "MotionEnvelope",
    "MotionRequirement",
    "OutputGeometryPolicy",
    "OutputNeed",
    "Pacing",
    "ProviderNeutralGenerationIntentProjection",
    "ProviderNeutralVideoRequirement",
    "QualityNeed",
    "ReviewEvidenceLink",
    "SceneContinuity",
    "SemanticReferenceRole",
    "SpaceContinuity",
    "SubjectAction",
    "TypedStateReference",
    "VerifiedGenerationRequirementProjection",
]
