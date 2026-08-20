from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import Character, Scene, Shot, StrictModel


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"
_UNSEALED_HASH = "0" * 64


def _canonical_hash_without(model: StrictModel, *excluded_fields: str) -> str:
    payload = model.model_dump(mode="json")
    for field in excluded_fields:
        payload.pop(field)
    return canonical_sha256(payload)


class AssetRole(str, Enum):
    CHARACTER_REFERENCE = "character_reference"
    SCENE_REFERENCE = "scene_reference"
    PREVIOUS_SHOT_TERMINAL = "previous_shot_terminal"
    APPROVED_KEYFRAME = "approved_keyframe"
    APPROVED_REUSABLE_PLATE = "approved_reusable_plate"
    EXISTING_VIDEO = "existing_video"


class GenerationMode(str, Enum):
    STATIC_IMAGE = "static_image"
    IMAGE_MOTION = "image_motion"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    FIRST_LAST_FRAME_VIDEO = "first_last_frame_video"
    REFERENCE_TO_VIDEO = "reference_to_video"
    HYBRID = "hybrid"


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


class ReasonCode(str, Enum):
    IMPORTANT_CHARACTER = "important_character"
    IDENTITY_REQUIRED = "identity_required"
    CONTINUITY_REQUIRED = "continuity_required"
    REFERENCE_AVAILABLE = "reference_available"
    TERMINAL_AVAILABLE = "terminal_available"
    NO_CHARACTER_REFERENCE = "no_character_reference"
    NO_SCENE_REFERENCE = "no_scene_reference"
    NO_VISUAL_ANCHOR = "no_visual_anchor"
    FREE_ENVIRONMENT = "free_environment"
    FIRST_SHOT = "first_shot"
    SEMANTIC_JUMP = "semantic_jump"
    MOTION_NONE = "motion_none"
    MOTION_LIGHT = "motion_light"
    MOTION_GRAPHIC = "motion_graphic"
    MOTION_HERO_REQUIRES_POLICY = "motion_hero_requires_policy"
    MISSING_TERMINAL = "missing_terminal"
    MISSING_REFERENCES = "missing_references"
    CONTINUITY_ANGLE_CHANGE = "continuity_angle_change"
    CONTINUITY_SAME_ACTION = "continuity_same_action"
    ACTION_INTENT_REQUIRED = "action_intent_required"
    STRATEGY_MOTION_MISMATCH = "strategy_motion_mismatch"
    CAMERA_MOTION_ONLY = "camera_motion_only"
    FINAL_SHOT_VISUAL_REQUIRED = "final_shot_visual_required"
    FINAL_SHOT_VISUAL_AVAILABLE = "final_shot_visual_available"
    REUSABLE_PLATE_APPROVED = "reusable_plate_approved"
    INTENTIONAL_STATIC = "intentional_static"
    STATIC_FALLBACK_ACCEPTED = "static_fallback_accepted"
    INTENT_EVIDENCE_NOT_CURRENT = "intent_evidence_not_current"
    REVIEW_EVIDENCE_NOT_CURRENT = "review_evidence_not_current"
    REQUEST_NOT_CURRENT = "request_not_current"
    EXISTING_VIDEO_UNSUPPORTED = "existing_video_unsupported"


class PlanWarning(str, Enum):
    MISSING_CHARACTER_REFERENCE = "missing_character_reference"
    MISSING_SCENE_REFERENCE = "missing_scene_reference"
    MISSING_TERMINAL_FRAME = "missing_terminal_frame"
    LOW_CONFIDENCE = "low_confidence"
    FINAL_SHOT_VISUAL_MISSING = "final_shot_visual_missing"
    CAMERA_MOTION_NOT_SUBJECT_MOTION = "camera_motion_not_subject_motion"
    STATIC_FALLBACK_REQUIRES_REVIEW = "static_fallback_requires_review"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class PlanOutcome(str, Enum):
    PROPOSED = "proposed"
    BLOCKED = "blocked"


class ShotIntentEvidence(StrictModel):
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    open_state_ref: str | None = Field(default=None, pattern=_SAFE_ID)
    close_state_ref: str | None = Field(default=None, pattern=_SAFE_ID)
    character_action_required: bool = False
    continuous_action_required: bool = False
    spatial_change_required: bool = False
    state_change_required: bool = False
    subject_motion_directive_present: bool = False
    evidence_unresolved: bool = False

    @property
    def requires_subject_motion(self) -> bool:
        return any(
            (
                self.character_action_required,
                self.continuous_action_required,
                self.spatial_change_required,
                self.state_change_required,
                self.subject_motion_directive_present,
            )
        )


class AvailableAsset(StrictModel):
    role: AssetRole
    asset_id: str = Field(pattern=_SAFE_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    canonical_owner_id: str | None = Field(default=None, pattern=_SAFE_ID)
    mime_type: str = Field(pattern=_MIME_TYPE)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    size_bytes: int | None = Field(default=None, gt=0)


class ReviewDecisionProjection(StrictModel):
    evidence_ref: str = Field(pattern=_SAFE_ID)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    rationale: str = Field(min_length=1)
    allows_intentional_static: bool = False
    allows_static_fallback: bool = False
    allows_reusable_plate: bool = False


class PreviousShotState(StrictModel):
    previous_shot_id: str | None = Field(default=None, pattern=_SAFE_ID)
    previous_shot_content_hash: str | None = Field(default=None, pattern=_SHA256)
    is_same_scene: bool
    is_same_story_beat: bool
    is_same_action: bool
    is_angle_change: bool
    has_terminal_frame_asset_id: str | None = Field(default=None, pattern=_SAFE_ID)
    semantic_jump: bool


class ProductionPolicyInput(StrictModel):
    local_resources_available: bool = True
    remote_authorized: bool = False
    budget_authorized: bool = False
    quality_preference: Literal["draft", "preview", "production", "hero"] = (
        "production"
    )
    accept_static_image_fallback: bool = False


class RequiredAssetRole(StrictModel):
    role: AssetRole
    reason_code: ReasonCode


class CapabilityRequirements(StrictModel):
    needs_character_reference: bool = False
    needs_scene_reference: bool = False
    needs_first_frame: bool = False
    needs_last_frame: bool = False
    needs_terminal_reference: bool = False
    needs_audio_native: bool = False
    needs_continuity_state: bool = False
    max_reference_count: int | None = Field(default=None, ge=0, le=8)
    min_output_duration_seconds: int | None = Field(default=None, ge=1, le=600)
    accepts_local_execution: bool = True
    accepts_remote_execution: bool = True


class VideoPlanningRequest(StrictModel):
    request_id: str = Field(pattern=_SAFE_ID)
    target_shot: Shot
    character_context: tuple[Character, ...]
    scene_context: Scene
    available_assets: tuple[AvailableAsset, ...]
    previous_shot_state: PreviousShotState | None
    shot_intent_evidence: ShotIntentEvidence
    review_decision: ReviewDecisionProjection | None
    production_policy: ProductionPolicyInput
    planning_contract_version: Literal["video-planner/2"]
    request_content_hash: str = Field(pattern=_SHA256)

    @classmethod
    def create(cls, **values: object) -> "VideoPlanningRequest":
        payload = dict(values)
        payload["request_content_hash"] = _UNSEALED_HASH
        draft = cls.model_validate(payload)
        request_content_hash = _canonical_hash_without(
            draft,
            "request_id",
            "request_content_hash",
        )
        return cls.model_validate(
            draft.model_copy(
                update={"request_content_hash": request_content_hash}
            ).model_dump(mode="python")
        )


class VideoGenerationPlan(StrictModel):
    plan_id: str = Field(pattern=_SAFE_ID)
    source_request_content_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    generation_mode: GenerationMode
    continuity_mode: ContinuityMode
    motion_requirement: MotionRequirement
    required_asset_roles: tuple[RequiredAssetRole, ...]
    capability_requirements: CapabilityRequirements
    reason_codes: tuple[ReasonCode, ...] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: tuple[PlanWarning, ...] = ()
    outcome: PlanOutcome
    rationale: str = Field(min_length=1)
    planning_contract_version: Literal["video-planner/2"]
    plan_hash: str = Field(pattern=_SHA256)

    @classmethod
    def create(cls, **values: object) -> "VideoGenerationPlan":
        payload = dict(values)
        source_request_content_hash = payload.get("source_request_content_hash")
        payload["plan_id"] = f"plan-{str(source_request_content_hash)[:24]}"
        payload["plan_hash"] = _UNSEALED_HASH
        draft = cls.model_validate(payload)
        plan_hash = _canonical_hash_without(draft, "plan_hash")
        return cls.model_validate(
            draft.model_copy(update={"plan_hash": plan_hash}).model_dump(
                mode="python"
            )
        )
