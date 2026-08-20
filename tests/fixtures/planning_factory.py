from __future__ import annotations

from ai_video.planning import (
    AssetRole,
    AvailableAsset,
    CapabilityRequirements,
    ContinuityMode,
    GenerationMode,
    MotionRequirement,
    PlanOutcome,
    PlanWarning,
    PreviousShotState,
    ProductionPolicyInput,
    ReasonCode,
    ReviewDecisionProjection,
    ShotIntentEvidence,
    VideoGenerationPlan,
    VideoPlanningRequest,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetType,
    Character,
    DurationPolicy,
    MotionDirective,
    Scene,
    Shot,
    SourceReference,
    VisualStrategy,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64


def _provenance() -> tuple[SourceReference, ...]:
    return (SourceReference(kind="user_input", reference="planning-fixture"),)


def make_character(*, character_id: str = "hero") -> Character:
    return seal_artifact(
        Character(
            artifact_id=f"character-{character_id}",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"receipt-character-{character_id}",
            source_provenance=_provenance(),
            character_id=character_id,
            name="Hero",
            identity="The canonical lead character",
            appearance_bible="Blue jacket and silver badge",
            reference_asset_ids=(f"reference-{character_id}",),
        )
    )


def make_scene(*, scene_id: str = "room") -> Scene:
    return seal_artifact(
        Scene(
            artifact_id=f"scene-{scene_id}",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"receipt-scene-{scene_id}",
            source_provenance=_provenance(),
            scene_id=scene_id,
            location="Investigation room",
            time="Night",
            mood="Mysterious",
            participant_ids=("hero",),
            continuity_constraints=("preserve screen direction",),
            visual_reference_asset_ids=(f"reference-{scene_id}",),
        )
    )


def make_shot(
    *,
    shot_id: str = "shot-1",
    revision: int = 1,
    visual_strategy: VisualStrategy = VisualStrategy.STATIC_IMAGE,
    character_ids: tuple[str, ...] = ("hero",),
    final_visual_asset_id: str = "keyframe-shot-1",
    final_visual_role: str = "final_visual",
    intent: str = "Hold on the hero before the action begins.",
    motion_directives: tuple[MotionDirective, ...] = (),
    continuity_constraints: tuple[str, ...] = (),
    scene_id: str = "room",
    storyboard_beat_id: str = "beat-1",
) -> Shot:
    return seal_artifact(
        Shot(
            artifact_id=f"artifact-{shot_id}",
            revision=revision,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"receipt-{shot_id}-{revision}",
            source_provenance=_provenance(),
            shot_id=shot_id,
            scene_id=scene_id,
            storyboard_beat_id=storyboard_beat_id,
            intent=intent,
            duration_policy=DurationPolicy(mode="fixed", seconds=3),
            character_ids=character_ids,
            continuity_constraints=continuity_constraints,
            visual_strategy=visual_strategy,
            required_asset_roles=(
                AssetRoleRequirement(
                    role=final_visual_role,
                    asset_ids=(final_visual_asset_id,),
                    allowed_asset_types=(AssetType.IMAGE,),
                ),
            ),
            motion_directives=motion_directives,
        )
    )


def make_motion_directive(
    kind: str = "animate", *, preset: str = "subject"
) -> MotionDirective:
    return MotionDirective.model_validate(
        {"kind": kind, "parameters": {"preset": preset}}
    )


def make_intent_evidence(
    *,
    target_shot: Shot | None = None,
    open_state_ref: str | None = None,
    close_state_ref: str | None = None,
    character_action_required: bool = False,
    continuous_action_required: bool = False,
    spatial_change_required: bool = False,
    state_change_required: bool = False,
    subject_motion_directive_present: bool = False,
    evidence_unresolved: bool = False,
) -> ShotIntentEvidence:
    shot = target_shot or make_shot()
    return ShotIntentEvidence(
        target_shot_id=shot.shot_id,
        target_shot_content_hash=shot.content_hash,
        open_state_ref=open_state_ref,
        close_state_ref=close_state_ref,
        character_action_required=character_action_required,
        continuous_action_required=continuous_action_required,
        spatial_change_required=spatial_change_required,
        state_change_required=state_change_required,
        subject_motion_directive_present=subject_motion_directive_present,
        evidence_unresolved=evidence_unresolved,
    )


def make_available_asset(
    *,
    role: AssetRole = AssetRole.APPROVED_KEYFRAME,
    asset_id: str = "keyframe-shot-1",
    asset_sha256: str = ONE_HASH,
    canonical_owner_id: str | None = "shot-1",
    mime_type: str = "image/png",
) -> AvailableAsset:
    return AvailableAsset(
        role=role,
        asset_id=asset_id,
        asset_sha256=asset_sha256,
        canonical_owner_id=canonical_owner_id,
        mime_type=mime_type,
        width=1920,
        height=1080,
        size_bytes=1024,
    )


def make_review_decision(
    *,
    target_shot: Shot | None = None,
    rationale: str = "Director approved the intentional static treatment.",
    allows_intentional_static: bool = True,
    allows_static_fallback: bool = False,
    allows_reusable_plate: bool = False,
) -> ReviewDecisionProjection:
    shot = target_shot or make_shot()
    return ReviewDecisionProjection(
        evidence_ref="review-evidence-1",
        target_shot_id=shot.shot_id,
        target_shot_content_hash=shot.content_hash,
        rationale=rationale,
        allows_intentional_static=allows_intentional_static,
        allows_static_fallback=allows_static_fallback,
        allows_reusable_plate=allows_reusable_plate,
    )


def make_policy(
    *, accept_static_image_fallback: bool = False
) -> ProductionPolicyInput:
    return ProductionPolicyInput(
        local_resources_available=True,
        remote_authorized=False,
        budget_authorized=False,
        quality_preference="production",
        accept_static_image_fallback=accept_static_image_fallback,
    )


def make_previous_state(
    *,
    previous_shot_id: str | None = "shot-0",
    previous_shot_content_hash: str | None = TWO_HASH,
    is_same_scene: bool = True,
    is_same_story_beat: bool = True,
    is_same_action: bool = False,
    is_angle_change: bool = False,
    has_terminal_frame_asset_id: str | None = None,
    semantic_jump: bool = False,
) -> PreviousShotState:
    return PreviousShotState(
        previous_shot_id=previous_shot_id,
        previous_shot_content_hash=previous_shot_content_hash,
        is_same_scene=is_same_scene,
        is_same_story_beat=is_same_story_beat,
        is_same_action=is_same_action,
        is_angle_change=is_angle_change,
        has_terminal_frame_asset_id=has_terminal_frame_asset_id,
        semantic_jump=semantic_jump,
    )


def make_request(**overrides: object) -> VideoPlanningRequest:
    target_shot = overrides.pop("target_shot", make_shot())
    assert isinstance(target_shot, Shot)
    values: dict[str, object] = {
        "request_id": "request-shot-1-attempt-1",
        "target_shot": target_shot,
        "character_context": (make_character(),),
        "scene_context": make_scene(),
        "available_assets": (make_available_asset(),),
        "previous_shot_state": None,
        "shot_intent_evidence": make_intent_evidence(target_shot=target_shot),
        "review_decision": make_review_decision(target_shot=target_shot),
        "production_policy": make_policy(),
        "planning_contract_version": "video-planner/2",
    }
    values.update(overrides)
    return VideoPlanningRequest.create(**values)


def make_plan(
    *, request: VideoPlanningRequest | None = None, **overrides: object
) -> VideoGenerationPlan:
    current_request = request or make_request()
    values: dict[str, object] = {
        "source_request_content_hash": current_request.request_content_hash,
        "target_shot_id": current_request.target_shot.shot_id,
        "target_shot_revision": current_request.target_shot.revision,
        "target_shot_content_hash": current_request.target_shot.content_hash,
        "generation_mode": GenerationMode.STATIC_IMAGE,
        "continuity_mode": ContinuityMode.NONE,
        "motion_requirement": MotionRequirement.NONE,
        "required_asset_roles": (),
        "capability_requirements": CapabilityRequirements(),
        "reason_codes": (ReasonCode.FIRST_SHOT,),
        "confidence": 0.75,
        "warnings": (),
        "outcome": PlanOutcome.PROPOSED,
        "rationale": "The sealed request has a deterministic schema-only proposal.",
        "planning_contract_version": "video-planner/2",
    }
    values.update(overrides)
    return VideoGenerationPlan.create(**values)
