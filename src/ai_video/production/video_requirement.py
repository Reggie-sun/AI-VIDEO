from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Any, Literal

from pydantic import (
    AliasChoices,
    Field,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    field_validator,
    model_serializer,
    model_validator,
)

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import Character, Scene, Shot, StrictModel
from ai_video.production._video_continuity import C4MultiAnchorBinding


_REQUIREMENT_CONTRACT_VERSION = "provider-neutral-video-requirement/1"
_C4_REQUIREMENT_CONTRACT_VERSION = "provider-neutral-video-requirement/2"
_COMMERCIAL_REQUIREMENT_CONTRACT_VERSION = "provider-neutral-video-requirement/3"
_CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION = "provider-neutral-video-requirement/4"
_UNSEALED_HASH = "0" * 64
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"
_LANGUAGE_TAG = (
    r"^[a-z]{2,3}"
    r"(?:-[A-Z][a-z]{3})?"
    r"(?:-(?:[A-Z]{2}|[0-9]{3}))?"
    r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*$"
)

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
    TEXT_TO_VIDEO = "text_to_video"
    VIDEO_EDIT = "video_edit"
    VIDEO_EXTEND = "video_extend"


class ContinuityMode(str, Enum):
    MULTI_ANCHOR = "multi_anchor"
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


class CameraMovementKind(str, Enum):
    LOCKED = "locked"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRUCK_LEFT = "truck_left"
    TRUCK_RIGHT = "truck_right"
    PEDESTAL_UP = "pedestal_up"
    PEDESTAL_DOWN = "pedestal_down"
    ORBIT_LEFT = "orbit_left"
    ORBIT_RIGHT = "orbit_right"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"


class CameraAmplitudeClass(str, Enum):
    SUBTLE = "subtle"
    MODERATE = "moderate"
    PRONOUNCED = "pronounced"


class CameraSpeedClass(str, Enum):
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"


class CameraMotionStartState(str, Enum):
    STATIONARY = "stationary"
    IN_MOTION = "in_motion"


class CameraMotionEndState(str, Enum):
    SETTLED = "settled"
    CONTINUING = "continuing"


class CameraSubjectRelationKind(str, Enum):
    FIXED_FRAME = "fixed_frame"
    MAINTAIN_OFFSET = "maintain_offset"
    FOLLOW = "follow"
    LEAD = "lead"
    REVEAL = "reveal"


class ConditioningLane(str, Enum):
    I2VA = "i2va"
    FL2VA = "fl2va"


class ConditioningCompatibilityEvidence(StrictModel):
    lane: ConditioningLane
    first_anchor_id: str = Field(pattern=_SAFE_ID)
    last_anchor_id: str | None = Field(default=None, pattern=_SAFE_ID)
    same_subject_scale: bool | None = None
    composition_compatible: bool | None = None
    screen_order_compatible: bool | None = None
    axis_compatible: bool | None = None
    camera_path_reachable: bool | None = None
    character_prop_state_reachable: bool | None = None
    action_endpoint_reachable: bool | None = None
    available_duration_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def _validate_lane_shape(self) -> "ConditioningCompatibilityEvidence":
        if self.lane is ConditioningLane.I2VA:
            if self.last_anchor_id is not None:
                raise ValueError("I2VA cannot carry a last anchor")
            return self
        if self.last_anchor_id is None:
            raise ValueError("FL2VA requires an approved last anchor")
        return self


class SemanticReferenceRole(str, Enum):
    IDENTITY = "identity"
    SCENE = "scene"
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"
    CONTINUITY_TERMINAL = "continuity_terminal"
    APPROVED_ENDPOINT = "approved_endpoint"
    CONTINUITY_MOTION_TAIL = "continuity_motion_tail"
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


class CameraMotionContract(StrictModel):
    movement_kind: CameraMovementKind
    direction: str = Field(min_length=1)
    amplitude_class: CameraAmplitudeClass
    speed_class: CameraSpeedClass
    start_motion_state: CameraMotionStartState
    end_motion_state: CameraMotionEndState

    @model_validator(mode="after")
    def _validate_locked_state(self) -> "CameraMotionContract":
        if self.movement_kind is CameraMovementKind.LOCKED and (
            self.start_motion_state is not CameraMotionStartState.STATIONARY
            or self.end_motion_state is not CameraMotionEndState.SETTLED
            or self.amplitude_class is not CameraAmplitudeClass.SUBTLE
            or self.speed_class is not CameraSpeedClass.VERY_SLOW
        ):
            raise ValueError(
                "locked camera requires canonical subtle/very_slow stationary-to-settled state"
            )
        expected_direction = {
            CameraMovementKind.LOCKED: "none",
            CameraMovementKind.PAN_LEFT: "left",
            CameraMovementKind.PAN_RIGHT: "right",
            CameraMovementKind.TILT_UP: "up",
            CameraMovementKind.TILT_DOWN: "down",
            CameraMovementKind.DOLLY_IN: "forward",
            CameraMovementKind.DOLLY_OUT: "backward",
            CameraMovementKind.TRUCK_LEFT: "left",
            CameraMovementKind.TRUCK_RIGHT: "right",
            CameraMovementKind.PEDESTAL_UP: "up",
            CameraMovementKind.PEDESTAL_DOWN: "down",
            CameraMovementKind.ORBIT_LEFT: "left",
            CameraMovementKind.ORBIT_RIGHT: "right",
            CameraMovementKind.CRANE_UP: "up",
            CameraMovementKind.CRANE_DOWN: "down",
        }[self.movement_kind]
        if self.direction != expected_direction:
            raise ValueError(
                f"{self.movement_kind.value} camera requires {expected_direction} direction"
            )
        return self


class CameraSubjectRelation(StrictModel):
    subject_id: str = Field(pattern=_SAFE_ID)
    relation_kind: CameraSubjectRelationKind
    start_relation: str = Field(min_length=1)
    end_relation: str = Field(min_length=1)

    @model_validator(mode="after")
    def _reject_secondary_camera_motion(self) -> "CameraSubjectRelation":
        from ai_video.production._video_intent_validation import (
            validate_camera_subject_relation,
        )

        diagnostics = validate_camera_subject_relation(self)
        if diagnostics:
            raise ValueError(
                "camera-subject relation cannot add a secondary camera motion: "
                + ", ".join(diagnostics)
            )
        return self


class PerformanceIntent(StrictModel):
    trigger: str = Field(min_length=1)
    visible_response: str = Field(min_length=1)
    gaze_target: str = Field(min_length=1)
    body_behavior: str = Field(min_length=1)
    hand_behavior: str = Field(min_length=1)
    terminal_performance_state: str = Field(min_length=1)


class VisualTreatment(StrictModel):
    medium_look: str = Field(min_length=1)
    palette: str = Field(min_length=1)
    material_treatment: str = Field(min_length=1)
    prohibited_visual_drift: tuple[str, ...] = Field(min_length=1)


class LightingIntent(StrictModel):
    motivated_source: str = Field(min_length=1)
    direction: str = Field(min_length=1)
    exposure_priority: str = Field(min_length=1)
    continuity_state: str = Field(min_length=1)


class AmbienceIntent(StrictModel):
    environment_bed: str = Field(min_length=1)
    foley_cues: tuple[str, ...] = ()
    explicitly_silent: bool = False

    @model_validator(mode="after")
    def _validate_silence(self) -> "AmbienceIntent":
        if self.explicitly_silent and (
            self.environment_bed != "none" or self.foley_cues
        ):
            raise ValueError("silent ambience cannot carry environment or foley")
        return self


class DialogueIntent(StrictModel):
    mode: Literal["none", "dialogue"]
    language: str | None = Field(
        default=None,
        pattern=_LANGUAGE_TAG,
        description=(
            "Canonical BCP-47 core language tag without extensions or private-use; "
            "historical dialogue may omit it for read compatibility, but provider "
            "compilers must fail closed"
        ),
    )
    speaker_id: str | None = Field(default=None, pattern=_SAFE_ID)
    verbatim_text: str | None = None
    start_seconds: float | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, gt=0)
    on_screen: bool | None = None
    response_obligation: str | None = None
    lip_sync_required: bool = False

    @field_validator("language")
    @classmethod
    def _validate_canonical_language_variants(cls, value: str | None) -> str | None:
        if value is None:
            return None
        subtags = value.split("-")[1:]
        index = 0
        if subtags and re.fullmatch(r"[A-Z][a-z]{3}", subtags[0]):
            index += 1
        if index < len(subtags) and re.fullmatch(
            r"(?:[A-Z]{2}|[0-9]{3})", subtags[index]
        ):
            index += 1
        variants = subtags[index:]
        if any(variant != variant.lower() for variant in variants):
            raise ValueError("language variants must use canonical lowercase")
        if len(variants) != len(set(variants)):
            raise ValueError("language variants must be unique")
        return value

    @model_validator(mode="after")
    def _validate_dialogue_boundary(self) -> "DialogueIntent":
        payload = (
            self.language,
            self.speaker_id,
            self.verbatim_text,
            self.start_seconds,
            self.end_seconds,
            self.on_screen,
            self.response_obligation,
        )
        if self.mode == "none":
            if any(value is not None for value in payload) or self.lip_sync_required:
                raise ValueError("none dialogue boundary cannot carry dialogue facts")
            return self
        historical_payload = payload[1:]
        if any(value is None for value in historical_payload):
            raise ValueError("dialogue mode requires complete sealed dialogue facts")
        assert self.start_seconds is not None and self.end_seconds is not None
        if self.end_seconds <= self.start_seconds:
            raise ValueError("dialogue time window must be positive")
        return self


class MusicIntent(StrictModel):
    mode: Literal["none", "music"]
    instrumentation: str | None = None
    tempo_rhythm: str | None = None
    dynamics: str | None = None

    @model_validator(mode="after")
    def _validate_music_boundary(self) -> "MusicIntent":
        payload = (self.instrumentation, self.tempo_rhythm, self.dynamics)
        if self.mode == "none":
            if any(value is not None for value in payload):
                raise ValueError("none music boundary cannot carry score facts")
        elif any(value is None for value in payload):
            raise ValueError("music mode requires complete sealed score facts")
        return self


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
    performance_intent: PerformanceIntent | None = None
    visual_treatment: VisualTreatment | None = None
    lighting_intent: LightingIntent | None = None
    ambience_intent: AmbienceIntent | None = None
    dialogue_intent: DialogueIntent | None = None
    music_intent: MusicIntent | None = None
    primary_camera_motion: CameraMotionContract | None = Field(
        default=None,
        validation_alias=AliasChoices("primary_camera_motion", "camera_motion"),
    )
    camera_subject_relation: CameraSubjectRelation | None = None

    @model_validator(mode="after")
    def _validate_camera_relation(self) -> "GenerationIntent":
        motion = self.primary_camera_motion
        relation = self.camera_subject_relation
        if (
            motion is not None
            and motion.movement_kind is CameraMovementKind.LOCKED
            and relation is not None
            and relation.relation_kind
            not in {
                CameraSubjectRelationKind.FIXED_FRAME,
                CameraSubjectRelationKind.MAINTAIN_OFFSET,
            }
        ):
            raise ValueError("locked camera relation cannot add a second motion")
        return self

    @model_serializer(mode="wrap")
    def _serialize_versioned_camera_contract(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        for field in (
            "performance_intent",
            "visual_treatment",
            "lighting_intent",
            "ambience_intent",
            "dialogue_intent",
            "music_intent",
            "primary_camera_motion",
            "camera_subject_relation",
        ):
            if getattr(self, field) is None:
                data.pop(field, None)
        dialogue = data.get("dialogue_intent")
        if (
            isinstance(dialogue, dict)
            and self.dialogue_intent is not None
            and self.dialogue_intent.language is None
        ):
            dialogue.pop("language", None)
        return data

    @property
    def camera_motion(self) -> CameraMotionContract | None:
        """Compatibility accessor for the uncommitted camera-v1 draft."""

        return self.primary_camera_motion


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


class ProductFidelityStrategy(str, Enum):
    APPROVED_FIRST_FRAME = "approved_first_frame"


class ProductFidelityRequirement(StrictModel):
    schema_version: Literal["product-fidelity-requirement/1"] = (
        "product-fidelity-requirement/1"
    )
    product_id: str = Field(pattern=_SAFE_ID)
    sku_id: str = Field(pattern=_SAFE_ID)
    product_reference_set_id: str = Field(pattern=_SAFE_ID)
    product_reference_set_hash: str = Field(pattern=_SHA256)
    product_source_asset_hashes: tuple[str, ...] = Field(min_length=1)
    strategy: ProductFidelityStrategy = ProductFidelityStrategy.APPROVED_FIRST_FRAME
    packaging_form: str = Field(min_length=1)
    bottle_silhouette: str = Field(min_length=1)
    dominant_color: str = Field(min_length=1)
    cap_color: str = Field(min_length=1)
    logo_label_identity: str = Field(min_length=1)
    protected_text_zones: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_canonical_product_truth(self) -> "ProductFidelityRequirement":
        if (
            self.product_source_asset_hashes
            != tuple(sorted(set(self.product_source_asset_hashes)))
            or any(re.fullmatch(_SHA256, item) is None for item in self.product_source_asset_hashes)
        ):
            raise ValueError("Product source hashes must be unique, ordered SHA-256 values")
        if self.protected_text_zones != tuple(sorted(set(self.protected_text_zones))):
            raise ValueError("Product protected text zones must be unique and ordered")
        return self


class ApprovedCommercialSourceLink(StrictModel):
    schema_version: Literal["approved-commercial-source-link/1"] = (
        "approved-commercial-source-link/1"
    )
    approval_id: str = Field(pattern=_SAFE_ID)
    approval_content_hash: str = Field(pattern=_SHA256)
    source_request_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    keyframe_asset_id: str = Field(pattern=_SAFE_ID)
    keyframe_sha256: str = Field(pattern=_SHA256)
    product_reference_set_id: str = Field(pattern=_SAFE_ID)
    product_reference_set_hash: str = Field(pattern=_SHA256)
    product_source_asset_hashes: tuple[str, ...] = Field(min_length=1)
    character_reference_ids: tuple[str, ...] = Field(min_length=1)
    scene_reference_ids: tuple[str, ...] = Field(min_length=1)
    wardrobe_requirement_hash: str = Field(pattern=_SHA256)
    accessory_requirement_hash: str = Field(pattern=_SHA256)
    review_receipt_id: str = Field(pattern=_SAFE_ID)
    review_receipt_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_canonical_identities(self) -> "ApprovedCommercialSourceLink":
        for values, label in (
            (self.product_source_asset_hashes, "product source hashes"),
            (self.character_reference_ids, "Character reference IDs"),
            (self.scene_reference_ids, "Scene reference IDs"),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"{label} must be unique and ordered")
        return self


class CapabilityNeed(StrictModel):
    needs_identity_reference: bool = False
    needs_scene_reference: bool = False
    needs_first_frame: bool = False
    needs_last_frame: bool = False
    needs_terminal_reference: bool = False
    needs_native_audio: bool = False
    needs_continuity_state: bool = False
    needs_product_fidelity: bool = False
    max_reference_count: int | None = Field(default=None, ge=0, le=30)
    accepts_local_execution: bool = True
    accepts_remote_execution: bool = True

    @model_serializer(mode="wrap")
    def _serialize_additive_product_need(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if not self.needs_product_fidelity:
            data.pop("needs_product_fidelity", None)
        return data


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
    conditioning_compatibility: ConditioningCompatibilityEvidence | None = None
    generation_operation: GenerationOperation = GenerationOperation.AUTO
    semantic_reference_roles: tuple[SemanticReferenceRole, ...] = ()
    media_reference_asset_ids: tuple[str, ...] = ()
    output_need: OutputNeed
    audio_need: AudioNeed
    quality_need: QualityNeed
    projection_hash: str = Field(pattern=_SHA256)

    @model_serializer(mode="wrap")
    def _serialize_versioned_conditioning(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if (
            self.generation_intent.primary_camera_motion is None
            or self.generation_operation is GenerationOperation.TEXT_TO_VIDEO
        ):
            data.pop("conditioning_compatibility", None)
        return data

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
        if (
            self.generation_operation is GenerationOperation.TEXT_TO_VIDEO
            and (self.semantic_reference_roles or self.media_reference_asset_ids)
        ):
            raise ValueError(
                "text-to-video generation cannot carry media reference roles or assets"
            )
        if (
            self.generation_intent.primary_camera_motion is not None
            and self.conditioning_compatibility is None
            and self.generation_operation is not GenerationOperation.TEXT_TO_VIDEO
        ):
            raise ValueError("rich generation intent requires conditioning compatibility")
        if (
            (
                self.generation_intent.primary_camera_motion is None
                or self.generation_operation is GenerationOperation.TEXT_TO_VIDEO
            )
            and self.conditioning_compatibility is not None
        ):
            raise ValueError(
                "historical or text-to-video intent cannot carry conditioning compatibility"
            )
        if self.generation_intent.primary_camera_motion is not None:
            from ai_video.production._video_intent_validation import (
                validate_conditioning_compatibility,
                validate_generation_intent_for_continuity,
            )

            diagnostics = validate_generation_intent_for_continuity(
                self.generation_intent,
                audio_need=self.audio_need,
            )
            if diagnostics:
                raise ValueError(
                    "projection requires complete rich generation intent: "
                    + ", ".join(diagnostics)
                )
            if self.generation_operation is not GenerationOperation.TEXT_TO_VIDEO:
                conditioning_diagnostics = validate_conditioning_compatibility(
                    self.conditioning_compatibility
                )
                if conditioning_diagnostics:
                    raise ValueError(
                        "projection requires compatible conditioning: "
                        + ", ".join(conditioning_diagnostics)
                    )
        return self

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema": (
                "provider-neutral-generation-intent/3"
                if self.generation_operation is GenerationOperation.TEXT_TO_VIDEO
                else "provider-neutral-generation-intent/2"
                if self.generation_intent.primary_camera_motion is not None
                else "provider-neutral-generation-intent/1"
            ),
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
    contract_version: Literal[
        _REQUIREMENT_CONTRACT_VERSION,
        _C4_REQUIREMENT_CONTRACT_VERSION,
        _COMMERCIAL_REQUIREMENT_CONTRACT_VERSION,
        _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION,
    ] = (
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
    c4_multi_anchor_binding: C4MultiAnchorBinding | None = None
    generation_mode: GenerationMode
    continuity_mode: ContinuityMode
    motion_requirement: MotionRequirement
    generation_intent: GenerationIntent
    conditioning_compatibility: ConditioningCompatibilityEvidence | None = None
    semantic_reference_roles: tuple[SemanticReferenceRole, ...] = ()
    capability_need: CapabilityNeed = Field(default_factory=CapabilityNeed)
    output_need: OutputNeed = Field(default_factory=OutputNeed)
    audio_need: AudioNeed = AudioNeed.OPTIONAL
    quality_need: QualityNeed = Field(default_factory=QualityNeed)
    commercial_execution_class: Literal["product_interaction"] | None = None
    product_fidelity_requirement: ProductFidelityRequirement | None = None
    approved_commercial_source: ApprovedCommercialSourceLink | None = None
    source_strategy: ProductFidelityStrategy | None = None

    @model_serializer(mode="wrap")
    def _serialize_additive_commercial_contract(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.contract_version != _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION:
            data.pop("conditioning_compatibility", None)
        commercial_present = any(
            value is not None
            for value in (
                self.commercial_execution_class,
                self.product_fidelity_requirement,
                self.approved_commercial_source,
                self.source_strategy,
            )
        )
        if (
            self.contract_version
            not in {
                _COMMERCIAL_REQUIREMENT_CONTRACT_VERSION,
                _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION,
            }
            or not commercial_present
        ):
            for field in (
                "commercial_execution_class",
                "product_fidelity_requirement",
                "approved_commercial_source",
                "source_strategy",
            ):
                data.pop(field, None)
        return data

    def _hash_payload(self) -> dict[str, object]:
        payload = self.model_dump(
            mode="json",
            exclude={"contract_version", "requirement_id", "requirement_hash"},
        )
        if self.c4_multi_anchor_binding is None:
            payload.pop("c4_multi_anchor_binding", None)
        return {
            "schema": self.contract_version,
            **payload,
        }

    @classmethod
    def create(cls, **values: object) -> "ProviderNeutralVideoRequirement":
        payload: dict[str, object] = dict(values)
        generation_intent = payload.get("generation_intent")
        primary_camera_motion = (
            generation_intent.primary_camera_motion
            if isinstance(generation_intent, GenerationIntent)
            else (
                generation_intent.get("primary_camera_motion")
                or generation_intent.get("camera_motion")
                if isinstance(generation_intent, dict)
                else None
            )
        )
        payload.setdefault(
            "contract_version",
            (
                _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION
                if primary_camera_motion is not None
                else (
                    _C4_REQUIREMENT_CONTRACT_VERSION
                    if payload.get("c4_multi_anchor_binding") is not None
                    else _REQUIREMENT_CONTRACT_VERSION
                )
            ),
        )
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
        if intent.primary_camera_motion is None:
            if self.contract_version == _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION:
                raise ValueError("camera-complete v4 requirement requires camera_motion")
        elif self.contract_version != _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION:
            raise ValueError("primary_camera_motion requires the v4 requirement")
        if self.contract_version == _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION:
            from ai_video.production._video_intent_validation import (
                validate_generation_intent_for_continuity,
                validate_requirement_conditioning_compatibility,
            )

            diagnostics = validate_generation_intent_for_continuity(
                intent,
                audio_need=self.audio_need,
            )
            if diagnostics:
                raise ValueError(
                    "v4 requires complete rich generation intent: "
                    + ", ".join(diagnostics)
                )
            conditioning_diagnostics = validate_requirement_conditioning_compatibility(
                self
            )
            if conditioning_diagnostics:
                raise ValueError(
                    "v4 requires compatible conditioning: "
                    + ", ".join(conditioning_diagnostics)
                )
        elif self.conditioning_compatibility is not None:
            raise ValueError("conditioning compatibility requires the v4 requirement")
        if (
            intent.scene_continuity is not None
            and intent.scene_continuity.scene_id != self.scene.scene_id
        ):
            raise ValueError("typed scene continuity must match requirement Scene")
        declared_characters = tuple(sorted(intent.identity_continuity.character_ids))
        if declared_characters and declared_characters != character_ids:
            raise ValueError("typed identity continuity must match requirement Characters")
        c4_binding = self.c4_multi_anchor_binding
        if c4_binding is None:
            if self.contract_version not in {
                _REQUIREMENT_CONTRACT_VERSION,
                _COMMERCIAL_REQUIREMENT_CONTRACT_VERSION,
                _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION,
            }:
                raise ValueError("C4 requirement contract requires a C4 binding")
            if self.continuity_mode is ContinuityMode.MULTI_ANCHOR:
                raise ValueError("multi-anchor continuity requires a C4 binding")
            return self._validate_commercial_product_fidelity()
        if (
            self.contract_version
            not in {
                _C4_REQUIREMENT_CONTRACT_VERSION,
                _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION,
            }
            or self.continuity_mode is not ContinuityMode.MULTI_ANCHOR
            or self.generation_mode is not GenerationMode.IMAGE_TO_VIDEO
        ):
            raise ValueError("C4 binding requires the v2 I2V multi-anchor contract")
        boundary = c4_binding.semantic_boundary
        if (
            boundary.target_shot_id != self.target_shot.shot_id
            or boundary.target_shot_revision != self.target_shot.revision
            or boundary.target_shot_content_hash != self.target_shot.content_hash
        ):
            raise ValueError("C4 requirement target does not match the exact Shot")
        identity = c4_binding.identity_anchor
        exact_characters = {
            (item.artifact_id, item.revision, item.content_hash)
            for item in self.characters
        }
        if (
            identity.character_artifact_id,
            identity.character_revision,
            identity.character_content_hash,
        ) not in exact_characters:
            raise ValueError(
                "C4 identity anchor does not match an exact requirement Character"
            )
        expected = {
            SemanticReferenceRole.CONTINUITY_TERMINAL: (
                c4_binding.terminal.extracted_asset_id,
                c4_binding.terminal.extracted_sha256,
            ),
            SemanticReferenceRole.IDENTITY: (
                c4_binding.identity_anchor.asset_id,
                c4_binding.identity_anchor.asset_sha256,
            ),
            SemanticReferenceRole.APPROVED_ENDPOINT: (
                c4_binding.approved_endpoint.asset_id,
                c4_binding.approved_endpoint.asset_sha256,
            ),
        }
        if c4_binding.motion_tail is not None:
            expected[SemanticReferenceRole.CONTINUITY_MOTION_TAIL] = (
                c4_binding.motion_tail.extracted_asset_id,
                c4_binding.motion_tail.extracted_sha256,
            )
        selected = {
            item.role: (item.asset_id, item.asset_sha256)
            for item in self.asset_evidence
        }
        if len(self.asset_evidence) != len(expected) or selected != expected:
            raise ValueError("C4 requirement evidence does not match exact anchors")
        return self

    def _validate_commercial_product_fidelity(
        self,
    ) -> "ProviderNeutralVideoRequirement":
        commercial_values = (
            self.commercial_execution_class,
            self.product_fidelity_requirement,
            self.approved_commercial_source,
            self.source_strategy,
        )
        commercial_present = any(value is not None for value in commercial_values)
        if not commercial_present:
            if self.contract_version == _COMMERCIAL_REQUIREMENT_CONTRACT_VERSION:
                raise ValueError("Commercial v3 requirement requires complete product lineage")
            if self.capability_need.needs_product_fidelity:
                raise ValueError("Product fidelity requires complete commercial lineage")
            return self
        if self.contract_version not in {
            _COMMERCIAL_REQUIREMENT_CONTRACT_VERSION,
            _CAMERA_COMPLETE_REQUIREMENT_CONTRACT_VERSION,
        }:
            if any(value is not None for value in commercial_values):
                raise ValueError("Historical requirement contracts cannot carry commercial fields")
            if self.capability_need.needs_product_fidelity:
                raise ValueError("Historical requirement contracts cannot require product fidelity")
            return self
        if any(value is None for value in commercial_values):
            raise ValueError("Commercial v3 requirement requires complete product lineage")
        fidelity = self.product_fidelity_requirement
        approval = self.approved_commercial_source
        assert fidelity is not None and approval is not None
        if (
            self.commercial_execution_class != "product_interaction"
            or self.generation_mode is not GenerationMode.IMAGE_TO_VIDEO
            or self.source_strategy is not ProductFidelityStrategy.APPROVED_FIRST_FRAME
            or fidelity.strategy is not ProductFidelityStrategy.APPROVED_FIRST_FRAME
            or not self.capability_need.needs_product_fidelity
        ):
            raise ValueError("Commercial product interaction requires approved-first-frame I2V")
        first_frames = tuple(
            item
            for item in self.asset_evidence
            if item.role is SemanticReferenceRole.FIRST_FRAME
        )
        if (
            len(self.asset_evidence) != 1
            or len(first_frames) != 1
            or first_frames[0].asset_id != approval.keyframe_asset_id
            or first_frames[0].asset_sha256 != approval.keyframe_sha256
            or self.semantic_reference_roles != (SemanticReferenceRole.FIRST_FRAME,)
        ):
            raise ValueError("Commercial v3 Provider input must be the exact approved first frame")
        if (
            approval.target_shot_id != self.target_shot.shot_id
            or approval.target_shot_content_hash != self.target_shot.content_hash
            or approval.product_reference_set_id != fidelity.product_reference_set_id
            or approval.product_reference_set_hash != fidelity.product_reference_set_hash
            or approval.product_source_asset_hashes != fidelity.product_source_asset_hashes
            or approval.character_reference_ids
            != tuple(sorted(item.artifact_id for item in self.characters))
            or approval.scene_reference_ids != (self.scene.artifact_id,)
            or fidelity.product_id in set(approval.character_reference_ids)
            or fidelity.product_id in set(approval.scene_reference_ids)
        ):
            raise ValueError("Commercial v3 product, Shot, Character, or Scene lineage is inconsistent")
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
    "AmbienceIntent",
    "AxisContinuity",
    "CameraAmplitudeClass",
    "CameraEndpoint",
    "CameraIntent",
    "CameraMotionContract",
    "CameraMotionEndState",
    "CameraMotionStartState",
    "CameraMovementKind",
    "CameraSpeedClass",
    "CameraSubjectRelation",
    "CameraSubjectRelationKind",
    "CapabilityNeed",
    "ConditioningCompatibilityEvidence",
    "ConditioningLane",
    "ContinuityMode",
    "ContinuityStateKind",
    "DialogueIntent",
    "ExpressionStrength",
    "GenerationIntent",
    "GenerationMode",
    "GenerationOperation",
    "IdentityContinuity",
    "IdentityPreservation",
    "LightingIntent",
    "MusicIntent",
    "MotionEnvelope",
    "MotionRequirement",
    "OutputGeometryPolicy",
    "OutputNeed",
    "Pacing",
    "PerformanceIntent",
    "ProviderNeutralGenerationIntentProjection",
    "ProviderNeutralVideoRequirement",
    "QualityNeed",
    "ReviewEvidenceLink",
    "SceneContinuity",
    "SemanticReferenceRole",
    "SpaceContinuity",
    "SubjectAction",
    "TypedStateReference",
    "VisualTreatment",
    "VerifiedGenerationRequirementProjection",
]
