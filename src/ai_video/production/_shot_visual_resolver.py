"""Pure authoring proposal resolution for the Shot Router."""

from __future__ import annotations

from ai_video.production._shot_router_contracts import (
    ContinuityMode,
    MotionRequirement,
    RouterContinuityState,
    RouterReasonCode,
    RoutingOutcome,
    ShotRoutingContext,
    ShotVisualRoutingProposal,
    VideoRoutingPolicy,
)
from ai_video.production.models import VisualStrategy
from ai_video.production.video import VideoGenerationMode


class ShotVisualResolver:
    """Resolve an authoring proposal without mutating canonical Shot state."""

    def resolve(
        self,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
    ) -> ShotVisualRoutingProposal:
        if context.continuity_mode is ContinuityMode.MULTI_ANCHOR:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MULTI_ANCHOR_REQUIREMENT_REQUIRED,
                "Multi-anchor continuity requires one sealed provider-neutral C4 requirement.",
            )
        if context.continuity_mode is ContinuityMode.EXACT_TERMINAL:
            if context.upstream_terminal is None:
                return self._blocked(
                    context,
                    policy,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_CONTINUITY_TERMINAL,
                    "Exact-terminal continuity requires the upstream terminal frame.",
                )
            return self._propose(
                context,
                policy,
                VisualStrategy.GENERATED_VIDEO,
                RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME,
                "Continue the action from the exact terminal frame without redrawing it.",
                required_generation_mode=VideoGenerationMode.IMAGE_TO_VIDEO,
                required_binding_roles=("first_frame",),
            )
        if context.continuity_mode is ContinuityMode.REFERENCE:
            blocked = self._reference_inputs_block(context, policy)
            if blocked is not None:
                return blocked
            return self._propose(
                context,
                policy,
                VisualStrategy.GENERATED_VIDEO,
                RouterReasonCode.REFERENCE_CONTINUITY_USES_TERMINAL_REFERENCE,
                "Inherit terminal and canonical state as references while allowing a new framing.",
                required_generation_mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                required_binding_roles=("reference",),
            )
        if (
            context.continuity_mode is ContinuityMode.SEMANTIC
            and context.semantic_continuity_state is None
        ):
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_SEMANTIC_CONTINUITY_STATE,
                "Semantic continuity requires an exact typed continuity-state snapshot.",
            )
        if (
            context.continuity_mode is ContinuityMode.NONE
            and context.approved_existing_video is not None
        ):
            return self._propose(
                context,
                policy,
                VisualStrategy.EXISTING_VIDEO,
                RouterReasonCode.APPROVED_EXISTING_VIDEO,
                "An exact approved video asset already satisfies the Shot.",
            )
        if context.motion_requirement is MotionRequirement.NONE:
            return self._propose(
                context,
                policy,
                VisualStrategy.STATIC_IMAGE,
                RouterReasonCode.NO_MOTION_REQUIRED,
                "The Shot has no visible motion requirement.",
            )
        if context.motion_requirement is MotionRequirement.LIGHT_TRANSFORM:
            return self._propose(
                context,
                policy,
                VisualStrategy.IMAGE_MOTION,
                RouterReasonCode.LIGHT_MOTION_FROM_KEYFRAME,
                "Transform-only motion can preserve an exact image anchor.",
            )
        if context.motion_requirement is MotionRequirement.GRAPHIC:
            return self._propose(
                context,
                policy,
                VisualStrategy.MOTION_GRAPHICS,
                RouterReasonCode.GRAPHIC_MOTION_REQUIRED,
                "The visible motion is graphic rather than performed character action.",
            )
        if context.motion_requirement is MotionRequirement.HERO_OR_REPAIR:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.HERO_SHOT_REQUIRES_HYBRID_OR_V2V,
                "Hero or repair routing requires a future exact media-binding slice.",
            )
        if context.important_character_ids:
            if not context.canonical_character_references:
                return self._blocked(
                    context,
                    policy,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_CHARACTER_REFERENCE,
                    "An important character cannot be routed to unanchored generation.",
                )
            if context.canonical_scene_reference is None:
                return self._blocked(
                    context,
                    policy,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_SCENE_REFERENCE,
                    "The fixed scene identity requires a canonical scene reference.",
                )
            return self._propose(
                context,
                policy,
                VisualStrategy.GENERATED_VIDEO,
                RouterReasonCode.IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR,
                "Important character action requires exact visual anchors before generation.",
            )
        return self._propose(
            context,
            policy,
            VisualStrategy.GENERATED_VIDEO,
            RouterReasonCode.FREE_ENVIRONMENT_MOTION_ENABLES_T2V,
            "Identity-free motion can use text-to-video generation.",
            required_generation_mode=VideoGenerationMode.TEXT_TO_VIDEO,
        )

    def _reference_inputs_block(
        self,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
    ) -> ShotVisualRoutingProposal | None:
        if context.upstream_terminal is None:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_CONTINUITY_TERMINAL,
                "Reference continuity requires the exact upstream terminal evidence.",
            )
        if context.semantic_continuity_state is None:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_SEMANTIC_CONTINUITY_STATE,
                "Reference continuity requires an exact typed continuity-state snapshot.",
            )
        if not context.canonical_character_references:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_CHARACTER_REFERENCE,
                "Reference continuity requires canonical character references.",
            )
        if context.canonical_scene_reference is None:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_SCENE_REFERENCE,
                "Reference continuity requires the canonical scene reference.",
            )
        return None

    def _propose(
        self,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
        strategy: VisualStrategy,
        reason: RouterReasonCode,
        rationale: str,
        *,
        required_generation_mode: VideoGenerationMode | None = None,
        required_binding_roles: tuple[str, ...] = (),
    ) -> ShotVisualRoutingProposal:
        if strategy not in context.allowed_visual_strategies:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.VISUAL_STRATEGY_POLICY_DENIED,
                "The resolved visual strategy is outside the accepted authoring policy.",
            )
        if (
            required_generation_mode is not None
            and required_generation_mode not in context.allowed_generation_modes
        ):
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
                "The required generation mode is outside the accepted routing policy.",
            )
        return ShotVisualRoutingProposal.create(
            target_shot_id=context.target_shot_id,
            target_shot_revision=context.target_shot_revision,
            target_shot_content_hash=context.target_shot_content_hash,
            continuity_mode=context.continuity_mode,
            semantic_continuity_state=self._effective_state(context),
            proposed_visual_strategy=strategy,
            required_generation_mode=required_generation_mode,
            required_binding_roles=required_binding_roles,
            reason_codes=(reason,),
            rationale=rationale,
            policy=policy.identity,
            outcome=RoutingOutcome.PROPOSED,
        )

    def _blocked(
        self,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
        outcome: RoutingOutcome,
        reason: RouterReasonCode,
        rationale: str,
    ) -> ShotVisualRoutingProposal:
        return ShotVisualRoutingProposal.create(
            target_shot_id=context.target_shot_id,
            target_shot_revision=context.target_shot_revision,
            target_shot_content_hash=context.target_shot_content_hash,
            continuity_mode=context.continuity_mode,
            semantic_continuity_state=self._effective_state(context),
            proposed_visual_strategy=None,
            required_generation_mode=None,
            required_binding_roles=(),
            reason_codes=(reason,),
            rationale=rationale,
            policy=policy.identity,
            outcome=outcome,
        )

    @staticmethod
    def _effective_state(
        context: ShotRoutingContext,
    ) -> RouterContinuityState | None:
        if context.continuity_mode not in {
            ContinuityMode.REFERENCE,
            ContinuityMode.SEMANTIC,
        }:
            return None
        return context.semantic_continuity_state
