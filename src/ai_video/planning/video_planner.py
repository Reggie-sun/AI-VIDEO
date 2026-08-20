from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning._planner_models import (
    AssetRole,
    AvailableAsset,
    CapabilityRequirements,
    ContinuityMode,
    GenerationMode,
    MotionRequirement,
    PlanOutcome,
    PlanWarning,
    PreviousShotState,
    ReasonCode,
    RequiredAssetRole,
    ReviewDecisionProjection,
    VideoGenerationPlan,
    VideoPlanningRequest,
    _canonical_hash_without,
)
from ai_video.production.models import AssetType, Shot, VisualStrategy


_CAMERA_TRANSFORM_KINDS = frozenset({"pan", "zoom", "parallax"})
_SUBJECT_MOTION_KINDS = frozenset({"animate"})
_FINAL_VISUAL_ROLE = "final_visual"
_ItemT = TypeVar("_ItemT")


def _append_unique(items: list[_ItemT], value: _ItemT) -> None:
    if value not in items:
        items.append(value)


def _current_review(
    request: VideoPlanningRequest,
) -> ReviewDecisionProjection | None:
    review = request.review_decision
    if review is None:
        return None
    if (
        review.target_shot_id != request.target_shot.shot_id
        or review.target_shot_content_hash != request.target_shot.content_hash
    ):
        return None
    return review


def _has_exact_image_binding(request: VideoPlanningRequest, asset_id: str) -> bool:
    return any(
        requirement.role == _FINAL_VISUAL_ROLE
        and asset_id in requirement.asset_ids
        and AssetType.IMAGE in requirement.allowed_asset_types
        for requirement in request.target_shot.required_asset_roles
    )


def _is_shot_bound_final_visual(
    request: VideoPlanningRequest,
    asset: AvailableAsset,
    *,
    review: ReviewDecisionProjection | None,
) -> bool:
    if asset.canonical_owner_id != request.target_shot.shot_id:
        return False
    if not _has_exact_image_binding(request, asset.asset_id):
        return False
    if asset.role is AssetRole.APPROVED_KEYFRAME:
        return True
    return bool(
        asset.role is AssetRole.APPROVED_REUSABLE_PLATE
        and review is not None
        and review.allows_reusable_plate
        and review.rationale.strip()
    )


def _available_role(request: VideoPlanningRequest, role: AssetRole) -> bool:
    if role is AssetRole.CHARACTER_REFERENCE:
        character_ids = {
            item.character_id
            for item in request.character_context
            if item.character_id in request.target_shot.character_ids
        }
        return any(
            asset.role is role and asset.canonical_owner_id in character_ids
            for asset in request.available_assets
        )
    if role is AssetRole.SCENE_REFERENCE:
        if request.scene_context.scene_id != request.target_shot.scene_id:
            return False
        return any(
            asset.role is role
            and asset.canonical_owner_id == request.target_shot.scene_id
            for asset in request.available_assets
        )
    if role is AssetRole.PREVIOUS_SHOT_TERMINAL:
        state = request.previous_shot_state
        terminal_id = state.has_terminal_frame_asset_id if state else None
        previous_shot_id = state.previous_shot_id if state else None
        return terminal_id is not None and previous_shot_id is not None and any(
            asset.role is role
            and asset.asset_id == terminal_id
            and asset.canonical_owner_id == previous_shot_id
            for asset in request.available_assets
        )
    review = _current_review(request)
    return any(
        asset.role is role
        and _is_shot_bound_final_visual(request, asset, review=review)
        for asset in request.available_assets
    )


def _required_role_is_available(
    request: VideoPlanningRequest,
    requirement: RequiredAssetRole,
) -> bool:
    return _available_role(request, requirement.role)


def _decide_continuity(
    request: VideoPlanningRequest,
    reasons: list[ReasonCode],
) -> ContinuityMode:
    state = request.previous_shot_state
    if state is None:
        _append_unique(reasons, ReasonCode.FIRST_SHOT)
        return ContinuityMode.NONE
    if state.semantic_jump:
        _append_unique(reasons, ReasonCode.SEMANTIC_JUMP)
        return ContinuityMode.SEMANTIC
    if state.is_same_action and not state.is_angle_change:
        _append_unique(reasons, ReasonCode.CONTINUITY_SAME_ACTION)
        return ContinuityMode.EXACT_TERMINAL
    if state.is_angle_change:
        _append_unique(reasons, ReasonCode.CONTINUITY_ANGLE_CHANGE)
        return ContinuityMode.REFERENCE
    _append_unique(reasons, ReasonCode.CONTINUITY_REQUIRED)
    return ContinuityMode.REFERENCE


def _camera_only_directives(request: VideoPlanningRequest) -> bool:
    directives = request.target_shot.motion_directives
    return bool(directives) and all(
        directive.kind in _CAMERA_TRANSFORM_KINDS for directive in directives
    )


def _derive_required_motion(
    request: VideoPlanningRequest,
    reasons: list[ReasonCode],
) -> MotionRequirement:
    evidence = request.shot_intent_evidence
    evidence_current = (
        evidence.target_shot_id == request.target_shot.shot_id
        and evidence.target_shot_content_hash == request.target_shot.content_hash
    )
    if not evidence_current:
        _append_unique(reasons, ReasonCode.INTENT_EVIDENCE_NOT_CURRENT)
        return MotionRequirement.HERO_OR_REPAIR
    if evidence.evidence_unresolved:
        return MotionRequirement.HERO_OR_REPAIR
    if evidence.requires_subject_motion:
        _append_unique(reasons, ReasonCode.ACTION_INTENT_REQUIRED)
        if _camera_only_directives(request):
            _append_unique(reasons, ReasonCode.CAMERA_MOTION_ONLY)
        return MotionRequirement.CHARACTER_ACTION

    directives = request.target_shot.motion_directives
    if directives and any(
        directive.kind in _SUBJECT_MOTION_KINDS for directive in directives
    ):
        _append_unique(reasons, ReasonCode.ACTION_INTENT_REQUIRED)
        return MotionRequirement.CHARACTER_ACTION
    if _camera_only_directives(request):
        _append_unique(reasons, ReasonCode.CAMERA_MOTION_ONLY)
        _append_unique(reasons, ReasonCode.MOTION_LIGHT)
        return MotionRequirement.LIGHT_TRANSFORM
    if request.target_shot.visual_strategy is VisualStrategy.MOTION_GRAPHICS:
        _append_unique(reasons, ReasonCode.MOTION_GRAPHIC)
        return MotionRequirement.GRAPHIC
    if request.target_shot.visual_strategy in {
        VisualStrategy.STATIC_IMAGE,
        VisualStrategy.EXISTING_VIDEO,
    }:
        _append_unique(reasons, ReasonCode.MOTION_NONE)
        return MotionRequirement.NONE
    return MotionRequirement.FREE_COMPLEX


def _declared_mode(strategy: VisualStrategy) -> GenerationMode:
    return {
        VisualStrategy.STATIC_IMAGE: GenerationMode.STATIC_IMAGE,
        VisualStrategy.IMAGE_MOTION: GenerationMode.IMAGE_MOTION,
        VisualStrategy.MOTION_GRAPHICS: GenerationMode.HYBRID,
        VisualStrategy.GENERATED_VIDEO: GenerationMode.REFERENCE_TO_VIDEO,
        VisualStrategy.EXISTING_VIDEO: GenerationMode.HYBRID,
        VisualStrategy.HYBRID: GenerationMode.HYBRID,
    }[strategy]


def _final_visual_role(request: VideoPlanningRequest) -> AssetRole:
    if _available_role(request, AssetRole.APPROVED_KEYFRAME):
        return AssetRole.APPROVED_KEYFRAME
    if _available_role(request, AssetRole.APPROVED_REUSABLE_PLATE):
        return AssetRole.APPROVED_REUSABLE_PLATE
    return AssetRole.APPROVED_KEYFRAME


def _static_lane_decision(
    request: VideoPlanningRequest,
    *,
    motion: MotionRequirement,
    reasons: list[ReasonCode],
    warnings: list[PlanWarning],
) -> tuple[GenerationMode, PlanOutcome, tuple[RequiredAssetRole, ...]]:
    strategy = request.target_shot.visual_strategy
    mode = _declared_mode(strategy)
    final_role = _final_visual_role(request)
    final_visual_ready = _available_role(request, final_role)
    review = _current_review(request)
    required = (
        RequiredAssetRole(
            role=final_role,
            reason_code=ReasonCode.FINAL_SHOT_VISUAL_REQUIRED,
        ),
    )
    _append_unique(reasons, ReasonCode.FINAL_SHOT_VISUAL_REQUIRED)
    if final_visual_ready:
        _append_unique(reasons, ReasonCode.FINAL_SHOT_VISUAL_AVAILABLE)
        if final_role is AssetRole.APPROVED_REUSABLE_PLATE:
            _append_unique(reasons, ReasonCode.REUSABLE_PLATE_APPROVED)
    else:
        _append_unique(warnings, PlanWarning.FINAL_SHOT_VISUAL_MISSING)

    requires_subject_motion = motion is MotionRequirement.CHARACTER_ACTION
    if requires_subject_motion:
        _append_unique(reasons, ReasonCode.STRATEGY_MOTION_MISMATCH)
        if _camera_only_directives(request):
            _append_unique(reasons, ReasonCode.CAMERA_MOTION_ONLY)
            _append_unique(
                warnings,
                PlanWarning.CAMERA_MOTION_NOT_SUBJECT_MOTION,
            )
        fallback_allowed = bool(
            request.production_policy.accept_static_image_fallback
            and final_visual_ready
            and review is not None
            and review.allows_static_fallback
            and review.rationale.strip()
        )
        if fallback_allowed:
            _append_unique(reasons, ReasonCode.STATIC_FALLBACK_ACCEPTED)
            _append_unique(
                warnings,
                PlanWarning.STATIC_FALLBACK_REQUIRES_REVIEW,
            )
            return mode, PlanOutcome.PROPOSED, required
        _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
        return mode, PlanOutcome.BLOCKED, required

    intentional_static_allowed = bool(
        final_visual_ready
        and review is not None
        and review.allows_intentional_static
        and review.rationale.strip()
    )
    if intentional_static_allowed:
        _append_unique(reasons, ReasonCode.INTENTIONAL_STATIC)
        return mode, PlanOutcome.PROPOSED, required
    _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
    return mode, PlanOutcome.BLOCKED, required


def _dynamic_decision(
    request: VideoPlanningRequest,
    *,
    continuity: ContinuityMode,
    motion: MotionRequirement,
    reasons: list[ReasonCode],
    warnings: list[PlanWarning],
) -> tuple[GenerationMode, PlanOutcome, tuple[RequiredAssetRole, ...]]:
    if request.target_shot.visual_strategy is VisualStrategy.EXISTING_VIDEO:
        _append_unique(reasons, ReasonCode.EXISTING_VIDEO_UNSUPPORTED)
        _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
        return GenerationMode.HYBRID, PlanOutcome.BLOCKED, ()
    if motion is MotionRequirement.HERO_OR_REPAIR:
        _append_unique(reasons, ReasonCode.MOTION_HERO_REQUIRES_POLICY)
        _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
        return _declared_mode(request.target_shot.visual_strategy), PlanOutcome.BLOCKED, ()
    if motion is MotionRequirement.GRAPHIC:
        return GenerationMode.HYBRID, PlanOutcome.PROPOSED, ()

    important_character = bool(request.target_shot.character_ids)
    has_character_reference = _available_role(
        request, AssetRole.CHARACTER_REFERENCE
    )
    has_scene_reference = _available_role(request, AssetRole.SCENE_REFERENCE)
    if important_character:
        _append_unique(reasons, ReasonCode.IMPORTANT_CHARACTER)
        _append_unique(reasons, ReasonCode.IDENTITY_REQUIRED)

    if continuity is ContinuityMode.EXACT_TERMINAL:
        required = (
            RequiredAssetRole(
                role=AssetRole.PREVIOUS_SHOT_TERMINAL,
                reason_code=ReasonCode.CONTINUITY_SAME_ACTION,
            ),
        )
        if _available_role(request, AssetRole.PREVIOUS_SHOT_TERMINAL):
            _append_unique(reasons, ReasonCode.TERMINAL_AVAILABLE)
            return GenerationMode.IMAGE_TO_VIDEO, PlanOutcome.PROPOSED, required
        _append_unique(reasons, ReasonCode.MISSING_TERMINAL)
        _append_unique(warnings, PlanWarning.MISSING_TERMINAL_FRAME)
        return GenerationMode.IMAGE_TO_VIDEO, PlanOutcome.BLOCKED, required

    if important_character:
        required = (
            RequiredAssetRole(
                role=AssetRole.CHARACTER_REFERENCE,
                reason_code=ReasonCode.IDENTITY_REQUIRED,
            ),
            RequiredAssetRole(
                role=AssetRole.SCENE_REFERENCE,
                reason_code=ReasonCode.CONTINUITY_REQUIRED,
            ),
        )
        if has_character_reference and has_scene_reference:
            _append_unique(reasons, ReasonCode.REFERENCE_AVAILABLE)
            return GenerationMode.REFERENCE_TO_VIDEO, PlanOutcome.PROPOSED, required
        if not has_character_reference:
            _append_unique(reasons, ReasonCode.NO_CHARACTER_REFERENCE)
            _append_unique(warnings, PlanWarning.MISSING_CHARACTER_REFERENCE)
        if not has_scene_reference:
            _append_unique(reasons, ReasonCode.NO_SCENE_REFERENCE)
            _append_unique(warnings, PlanWarning.MISSING_SCENE_REFERENCE)
        _append_unique(reasons, ReasonCode.NO_VISUAL_ANCHOR)
        return GenerationMode.REFERENCE_TO_VIDEO, PlanOutcome.BLOCKED, required

    _append_unique(reasons, ReasonCode.FREE_ENVIRONMENT)
    return GenerationMode.TEXT_TO_VIDEO, PlanOutcome.PROPOSED, ()


def _capabilities(
    request: VideoPlanningRequest,
    *,
    mode: GenerationMode,
    continuity: ContinuityMode,
) -> CapabilityRequirements:
    return CapabilityRequirements(
        needs_character_reference=mode is GenerationMode.REFERENCE_TO_VIDEO,
        needs_scene_reference=mode is GenerationMode.REFERENCE_TO_VIDEO,
        needs_first_frame=mode
        in {
            GenerationMode.IMAGE_TO_VIDEO,
            GenerationMode.FIRST_LAST_FRAME_VIDEO,
        },
        needs_last_frame=mode is GenerationMode.FIRST_LAST_FRAME_VIDEO,
        needs_terminal_reference=continuity is ContinuityMode.EXACT_TERMINAL,
        needs_continuity_state=continuity is not ContinuityMode.NONE,
        max_reference_count=(
            2 if mode is GenerationMode.REFERENCE_TO_VIDEO else None
        ),
        accepts_local_execution=request.production_policy.local_resources_available,
        accepts_remote_execution=bool(
            request.production_policy.remote_authorized
            and request.production_policy.budget_authorized
        ),
    )


def _confidence(
    *,
    outcome: PlanOutcome,
    reasons: list[ReasonCode],
    warnings: list[PlanWarning],
) -> float:
    if outcome is PlanOutcome.BLOCKED:
        return 0.2 if PlanWarning.REQUIRES_HUMAN_REVIEW in warnings else 0.35
    if ReasonCode.STATIC_FALLBACK_ACCEPTED in reasons:
        return 0.65
    if ReasonCode.INTENTIONAL_STATIC in reasons:
        return 0.8
    return 0.9


def _rationale(reasons: list[ReasonCode], outcome: PlanOutcome) -> str:
    labels = ", ".join(reason.value for reason in reasons)
    return f"{outcome.value} by video-planner/2: {labels}."


class VideoPlanner:
    CONTRACT_VERSION = "video-planner/2"

    def plan(self, request: VideoPlanningRequest) -> VideoGenerationPlan:
        reasons: list[ReasonCode] = []
        warnings: list[PlanWarning] = []

        request_is_current = request.request_content_hash == _canonical_hash_without(
            request,
            "request_id",
            "request_content_hash",
        )
        if not request_is_current:
            _append_unique(reasons, ReasonCode.REQUEST_NOT_CURRENT)
            _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)

        evidence = request.shot_intent_evidence
        evidence_is_current = (
            evidence.target_shot_id == request.target_shot.shot_id
            and evidence.target_shot_content_hash == request.target_shot.content_hash
        )
        if not evidence_is_current:
            _append_unique(reasons, ReasonCode.INTENT_EVIDENCE_NOT_CURRENT)
            _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
        if request.review_decision is not None and _current_review(request) is None:
            _append_unique(reasons, ReasonCode.REVIEW_EVIDENCE_NOT_CURRENT)
            _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
        if evidence.evidence_unresolved:
            _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)

        continuity = _decide_continuity(request, reasons)
        motion = _derive_required_motion(request, reasons)
        camera_only = not request.target_shot.motion_directives or _camera_only_directives(
            request
        )
        static_lane = request.target_shot.visual_strategy is VisualStrategy.STATIC_IMAGE or (
            request.target_shot.visual_strategy is VisualStrategy.IMAGE_MOTION
            and camera_only
        )
        if static_lane:
            mode, outcome, required = _static_lane_decision(
                request,
                motion=motion,
                reasons=reasons,
                warnings=warnings,
            )
        else:
            mode, outcome, required = _dynamic_decision(
                request,
                continuity=continuity,
                motion=motion,
                reasons=reasons,
                warnings=warnings,
            )

        if not request_is_current or not evidence_is_current:
            outcome = PlanOutcome.BLOCKED
        if PlanWarning.REQUIRES_HUMAN_REVIEW in warnings:
            outcome = PlanOutcome.BLOCKED
        return VideoGenerationPlan.create(
            source_request_content_hash=request.request_content_hash,
            target_shot_id=request.target_shot.shot_id,
            target_shot_revision=request.target_shot.revision,
            target_shot_content_hash=request.target_shot.content_hash,
            generation_mode=mode,
            continuity_mode=continuity,
            motion_requirement=motion,
            required_asset_roles=required,
            capability_requirements=_capabilities(
                request,
                mode=mode,
                continuity=continuity,
            ),
            reason_codes=tuple(reasons),
            confidence=_confidence(
                outcome=outcome,
                reasons=reasons,
                warnings=warnings,
            ),
            warnings=tuple(warnings),
            outcome=outcome,
            rationale=_rationale(reasons, outcome),
            planning_contract_version=self.CONTRACT_VERSION,
        )

    @staticmethod
    def derive_previous_shot_state(
        *,
        previous_shot: Shot | None,
        target_shot: Shot,
        is_same_action: bool = False,
        is_angle_change: bool = False,
        semantic_jump: bool = False,
        has_terminal_frame_asset_id: str | None = None,
    ) -> PreviousShotState | None:
        if previous_shot is None:
            return None
        return PreviousShotState(
            previous_shot_id=previous_shot.shot_id,
            previous_shot_content_hash=previous_shot.content_hash,
            is_same_scene=previous_shot.scene_id == target_shot.scene_id,
            is_same_story_beat=(
                previous_shot.storyboard_beat_id
                == target_shot.storyboard_beat_id
            ),
            is_same_action=is_same_action,
            is_angle_change=is_angle_change,
            has_terminal_frame_asset_id=has_terminal_frame_asset_id,
            semantic_jump=semantic_jump,
        )


def _preflight_error(detail: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
        user_message="Video planning preflight blocked downstream execution.",
        technical_detail=detail,
        retryable=False,
    )


def require_current_video_plan(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
) -> None:
    expected_request_hash = _canonical_hash_without(
        current_request,
        "request_id",
        "request_content_hash",
    )
    if current_request.request_content_hash != expected_request_hash:
        raise _preflight_error("current request seal is invalid")
    if plan.plan_hash != _canonical_hash_without(plan, "plan_hash"):
        raise _preflight_error("plan seal is invalid")
    expected_plan_id = f"plan-{plan.source_request_content_hash[:24]}"
    if plan.plan_id != expected_plan_id:
        raise _preflight_error("plan id is not bound to its source request")
    if plan.source_request_content_hash != current_request.request_content_hash:
        raise _preflight_error("plan source request is stale")
    if plan.target_shot_id != current_request.target_shot.shot_id:
        raise _preflight_error("plan target Shot id is stale")
    if plan.target_shot_revision != current_request.target_shot.revision:
        raise _preflight_error("plan target Shot revision is stale")
    if plan.target_shot_content_hash != current_request.target_shot.content_hash:
        raise _preflight_error("plan target Shot content hash is stale")
    if plan.outcome is PlanOutcome.BLOCKED:
        raise _preflight_error("plan outcome is blocked")
    if PlanWarning.REQUIRES_HUMAN_REVIEW in plan.warnings:
        raise _preflight_error("plan still requires human review")
    missing = tuple(
        requirement.role.value
        for requirement in plan.required_asset_roles
        if not _required_role_is_available(current_request, requirement)
    )
    if missing:
        raise _preflight_error(
            f"required current assets are missing or invalid: {', '.join(missing)}"
        )


def prepare_shot_for_existing_production(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
    production_handoff: Callable[..., Any],
) -> Any:
    require_current_video_plan(current_request=current_request, plan=plan)
    return production_handoff(
        current_shot=current_request.target_shot,
        plan_hint=plan,
    )
