from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from ai_video.planning._asset_readiness import (
    asset_matches_role as _asset_matches_role,
    available_role as _available_role,
    current_review as _current_review,
    media_selection_is_complete as _media_selection_is_complete,
)
from ai_video.planning._current_plan_projection import (
    verify_current_generation_requirement_projection,
)
from ai_video.planning._planner_models import (
    AssetRole,
    CapabilityRequirements,
    ContinuityMode,
    CurrentPlanProjectionFailure,
    GenerationMode,
    MotionRequirement,
    PlanOutcome,
    PlanWarning,
    PreviousShotState,
    ReasonCode,
    RequiredAssetRole,
    VideoGenerationPlan,
    VideoPlanningRequest,
    _canonical_hash_without,
)
from ai_video.production.models import Shot, VisualStrategy
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import (
    AssetEvidence as RequirementAssetEvidence,
    CapabilityNeed,
    ContinuityMode as RequirementContinuityMode,
    GenerationMode as RequirementGenerationMode,
    GenerationOperation,
    MotionRequirement as RequirementMotionRequirement,
    ProviderNeutralVideoRequirement,
    ReviewEvidenceLink,
    SemanticReferenceRole,
    VerifiedGenerationRequirementProjection,
)


_CAMERA_TRANSFORM_KINDS = frozenset({"pan", "zoom", "parallax"})
_SUBJECT_MOTION_KINDS = frozenset({"animate"})
_ItemT = TypeVar("_ItemT")


def _append_unique(items: list[_ItemT], value: _ItemT) -> None:
    if value not in items:
        items.append(value)


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
    declared_roles = (
        request.generation_intent.semantic_reference_roles
        if request.generation_intent is not None
        else ()
    )
    generation_operation = (
        request.generation_intent.generation_operation
        if request.generation_intent is not None
        else GenerationOperation.AUTO
    )
    if declared_roles or generation_operation is not GenerationOperation.AUTO:
        roles = list(declared_roles)
        if generation_operation is not GenerationOperation.AUTO and (
            SemanticReferenceRole.VIDEO_REFERENCE not in roles
        ):
            roles.append(SemanticReferenceRole.VIDEO_REFERENCE)
        if (
            continuity is ContinuityMode.EXACT_TERMINAL
            and SemanticReferenceRole.CONTINUITY_TERMINAL not in roles
        ):
            roles.append(SemanticReferenceRole.CONTINUITY_TERMINAL)
        if important_character:
            for role in (
                SemanticReferenceRole.IDENTITY,
                SemanticReferenceRole.SCENE,
            ):
                if role not in roles:
                    roles.append(role)
            _append_unique(reasons, ReasonCode.IMPORTANT_CHARACTER)
            _append_unique(reasons, ReasonCode.IDENTITY_REQUIRED)
        required = tuple(
            RequiredAssetRole(
                role=_asset_role(role),
                reason_code=(
                    ReasonCode.IDENTITY_REQUIRED
                    if role is SemanticReferenceRole.IDENTITY
                    else ReasonCode.CONTINUITY_REQUIRED
                    if role
                    in {
                        SemanticReferenceRole.SCENE,
                        SemanticReferenceRole.CONTINUITY_TERMINAL,
                    }
                    else ReasonCode.REFERENCE_AVAILABLE
                ),
            )
            for role in roles
        )
        missing = tuple(
            item for item in required if not _available_role(request, item.role)
        )
        if missing or not _media_selection_is_complete(request, required):
            _append_unique(reasons, ReasonCode.MISSING_REFERENCES)
            _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
            return (
                GenerationMode(generation_operation.value)
                if generation_operation is not GenerationOperation.AUTO
                else GenerationMode.REFERENCE_TO_VIDEO,
                PlanOutcome.BLOCKED,
                required,
            )
        _append_unique(reasons, ReasonCode.REFERENCE_AVAILABLE)
        return (
            GenerationMode(generation_operation.value)
            if generation_operation is not GenerationOperation.AUTO
            else GenerationMode.REFERENCE_TO_VIDEO,
            PlanOutcome.PROPOSED,
            required,
        )

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


def _rationale(
    reasons: list[ReasonCode],
    outcome: PlanOutcome,
    *,
    contract_version: str,
) -> str:
    labels = ", ".join(reason.value for reason in reasons)
    return f"{outcome.value} by {contract_version}: {labels}."


def _semantic_role(role: AssetRole) -> SemanticReferenceRole:
    return {
        AssetRole.CHARACTER_REFERENCE: SemanticReferenceRole.IDENTITY,
        AssetRole.SCENE_REFERENCE: SemanticReferenceRole.SCENE,
        AssetRole.PREVIOUS_SHOT_TERMINAL: SemanticReferenceRole.CONTINUITY_TERMINAL,
        AssetRole.APPROVED_KEYFRAME: SemanticReferenceRole.FIRST_FRAME,
        AssetRole.APPROVED_REUSABLE_PLATE: SemanticReferenceRole.FIRST_FRAME,
        AssetRole.EXISTING_VIDEO: SemanticReferenceRole.VIDEO_REFERENCE,
        AssetRole.REFERENCE_AUDIO: SemanticReferenceRole.AUDIO_REFERENCE,
        AssetRole.LAST_FRAME: SemanticReferenceRole.LAST_FRAME,
    }[role]


def _asset_role(role: SemanticReferenceRole) -> AssetRole:
    return {
        SemanticReferenceRole.IDENTITY: AssetRole.CHARACTER_REFERENCE,
        SemanticReferenceRole.SCENE: AssetRole.SCENE_REFERENCE,
        SemanticReferenceRole.FIRST_FRAME: AssetRole.APPROVED_KEYFRAME,
        SemanticReferenceRole.LAST_FRAME: AssetRole.LAST_FRAME,
        SemanticReferenceRole.CONTINUITY_TERMINAL: AssetRole.PREVIOUS_SHOT_TERMINAL,
        SemanticReferenceRole.VIDEO_REFERENCE: AssetRole.EXISTING_VIDEO,
        SemanticReferenceRole.AUDIO_REFERENCE: AssetRole.REFERENCE_AUDIO,
    }[role]


def _build_generation_requirement(
    request: VideoPlanningRequest,
    *,
    mode: GenerationMode,
    continuity: ContinuityMode,
    motion: MotionRequirement,
    required: tuple[RequiredAssetRole, ...],
) -> ProviderNeutralVideoRequirement:
    projection = request.generation_intent
    if projection is None:
        raise _preflight_error("video-planner/3 requires typed generation intent")
    required_roles = tuple(
        sorted(
            {
                *(_semantic_role(item.role) for item in required),
                *projection.semantic_reference_roles,
            },
            key=lambda role: role.value,
        )
    )
    required_role_set = set(required_roles)
    evidence = tuple(
        RequirementAssetEvidence(
            role=_semantic_role(asset.role),
            asset_id=asset.asset_id,
            asset_sha256=asset.asset_sha256,
            canonical_owner_id=asset.canonical_owner_id,
            canonical_owner_content_hash=asset.canonical_owner_content_hash,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            size_bytes=asset.size_bytes,
            duration_millis=asset.duration_millis,
            fps=asset.fps,
        )
        for asset in request.available_assets
        if _semantic_role(asset.role) in required_role_set
        and any(
            _available_role(request, item.role)
            and _asset_matches_role(request, asset, item.role)
            for item in required
            if _semantic_role(item.role) is _semantic_role(asset.role)
        )
    )
    evidenced_roles = {asset.role for asset in evidence}
    semantic_roles = tuple(
        role for role in required_roles if role in evidenced_roles
    )
    review = _current_review(request)
    review_link = (
        ReviewEvidenceLink(
            evidence_ref=review.evidence_ref,
            target_shot_id=review.target_shot_id,
            target_shot_content_hash=review.target_shot_content_hash,
            review_decision_hash=canonical_sha256(review.model_dump(mode="json")),
        )
        if review is not None
        else None
    )
    return ProviderNeutralVideoRequirement.create(
        source_request_content_hash=request.request_content_hash,
        intent_evidence_hash=canonical_sha256(
            request.shot_intent_evidence.model_dump(mode="json")
        ),
        generation_intent_hash=projection.projection_hash,
        target_shot=request.target_shot,
        scene=request.scene_context,
        characters=tuple(
            character
            for character in request.character_context
            if character.character_id in request.target_shot.character_ids
        ),
        review_evidence=review_link,
        asset_evidence=evidence,
        generation_mode=RequirementGenerationMode(mode.value),
        continuity_mode=RequirementContinuityMode(continuity.value),
        motion_requirement=RequirementMotionRequirement(motion.value),
        generation_intent=projection.generation_intent,
        semantic_reference_roles=semantic_roles,
        capability_need=CapabilityNeed(
            needs_identity_reference=(SemanticReferenceRole.IDENTITY in semantic_roles),
            needs_scene_reference=(SemanticReferenceRole.SCENE in semantic_roles),
            needs_first_frame=bool(
                {SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.CONTINUITY_TERMINAL}
                & set(semantic_roles)
            ),
            needs_last_frame=SemanticReferenceRole.LAST_FRAME in semantic_roles,
            needs_terminal_reference=(
                continuity is ContinuityMode.EXACT_TERMINAL
            ),
            needs_native_audio=projection.audio_need.value == "required",
            needs_continuity_state=continuity is not ContinuityMode.NONE,
            max_reference_count=(
                sum(
                    item.role
                    in {
                        SemanticReferenceRole.IDENTITY,
                        SemanticReferenceRole.SCENE,
                    }
                    for item in evidence
                )
                or None
            ),
            accepts_local_execution=(
                request.production_policy.local_resources_available
            ),
            accepts_remote_execution=bool(
                request.production_policy.remote_authorized
                and request.production_policy.budget_authorized
            ),
        ),
        output_need=projection.output_need,
        audio_need=projection.audio_need,
        quality_need=projection.quality_need,
    )


def _typed_generation_intent_is_sufficient(
    request: VideoPlanningRequest,
    mode: GenerationMode,
) -> bool:
    if mode in {GenerationMode.STATIC_IMAGE, GenerationMode.IMAGE_MOTION}:
        return True
    projection = request.generation_intent
    if projection is None:
        return False
    intent = projection.generation_intent
    return any(
        value != "unspecified"
        for value in (
            intent.subject_action.progression,
            intent.motion_envelope.onset,
            intent.motion_envelope.peak,
            intent.motion_envelope.settle,
            intent.camera_intent.movement,
        )
    )


class VideoPlanner:
    CONTRACT_VERSION = "video-planner/3"

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
        if (
            request.planning_contract_version == self.CONTRACT_VERSION
            and not _typed_generation_intent_is_sufficient(request, mode)
        ):
            _append_unique(reasons, ReasonCode.ACTION_INTENT_REQUIRED)
            _append_unique(warnings, PlanWarning.REQUIRES_HUMAN_REVIEW)
            outcome = PlanOutcome.BLOCKED
        requirement = (
            _build_generation_requirement(
                request,
                mode=mode,
                continuity=continuity,
                motion=motion,
                required=required,
            )
            if request.planning_contract_version == self.CONTRACT_VERSION
            else None
        )
        plan_values: dict[str, object] = {
            "source_request_content_hash": request.request_content_hash,
            "target_shot_id": request.target_shot.shot_id,
            "target_shot_revision": request.target_shot.revision,
            "target_shot_content_hash": request.target_shot.content_hash,
            "generation_requirement": requirement,
            "reason_codes": tuple(reasons),
            "confidence": _confidence(
                outcome=outcome,
                reasons=reasons,
                warnings=warnings,
            ),
            "warnings": tuple(warnings),
            "outcome": outcome,
            "rationale": _rationale(
                reasons,
                outcome,
                contract_version=request.planning_contract_version,
            ),
            "planning_contract_version": request.planning_contract_version,
        }
        if request.planning_contract_version == "video-planner/2":
            plan_values.update(
                generation_mode=mode,
                continuity_mode=continuity,
                motion_requirement=motion,
                required_asset_roles=required,
                capability_requirements=_capabilities(
                    request,
                    mode=mode,
                    continuity=continuity,
                ),
            )
        return VideoGenerationPlan.create(
            **plan_values,
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


def _verify_current_generation_requirement_projection(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
) -> VerifiedGenerationRequirementProjection | CurrentPlanProjectionFailure:
    return verify_current_generation_requirement_projection(
        current_request=current_request,
        plan=plan,
        derive_plan=VideoPlanner().plan,
    )


def require_current_video_plan(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
) -> VerifiedGenerationRequirementProjection:
    from ai_video.quality_gates import (
        ShotReadinessGate,
        ShotReadinessRequest,
        require_ready,
    )

    readiness_request = ShotReadinessRequest.create(
        request_id=f"readiness-{current_request.target_shot.shot_id}",
        current_request=current_request,
        plan=plan,
    )
    return require_ready(ShotReadinessGate().evaluate(readiness_request))


def prepare_shot_for_existing_production(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
    production_handoff: Callable[..., Any],
) -> Any:
    projection = require_current_video_plan(
        current_request=current_request,
        plan=plan,
    )
    return production_handoff(
        current_shot=current_request.target_shot,
        generation_requirement=projection,
    )
