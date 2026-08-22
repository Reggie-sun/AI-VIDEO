"""Deterministic, provider-neutral Shot routing with no external effects."""

from __future__ import annotations

from ai_video.production._shot_router_contracts import (
    AdapterCompilerContract,
    ContinuityMode,
    MotionRequirement,
    ProviderBoundVideoRequest,
    RequirementRoutingResult,
    RouterAssetIdentity,
    RouterContinuityState,
    RouterPolicyIdentity,
    RouterReasonCode,
    RoutingOutcome,
    ShotRoutingContext,
    ShotVisualRoutingProposal,
    VideoGenerationLifecycleEnvelope,
    VideoGenerationRoutingDecision,
    VideoRoutingPolicy,
)
from ai_video.production._shot_visual_resolver import ShotVisualResolver
from ai_video.production._video_capability_fingerprint import (
    binding_roles_satisfy_variant,
    capability_variant_fingerprint,
)
from ai_video.production._video_requirement_routing import (
    as_capability_blocked,
    effective_policy_for_requirement,
    enforce_c4_requirement_gate,
    requirement_bindings,
    requirement_mode,
    requirement_output_matches,
    requirement_route_is_unsupported,
    validate_requirement_asset_lineage,
)
from ai_video.production.models import VisualStrategy
from ai_video.production.video import (
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoOutputRequirement,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoMediaReferenceBinding,
    media_bindings_satisfy_capabilities,
)
from ai_video.production.video_requirement import (
    VerifiedGenerationRequirementProjection,
)


class VideoGenerationResolver:
    """Resolve one exact selected capability without provider fallback."""

    def resolve(
        self,
        *,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
        provider_profile: ProviderProfilePointer,
        capabilities: VideoProviderCapabilities,
        selected_capability_id: str,
        output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement,
        requirement_hash: str | None = None,
        requirement_mode: VideoGenerationMode | None = None,
        requirement_binding_roles: tuple[str, ...] | None = None,
        requirement_input_assets: tuple[RouterAssetIdentity, ...] | None = None,
    ) -> VideoGenerationRoutingDecision:
        base: dict[str, object] = {
            "target_shot_id": context.target_shot_id,
            "target_shot_revision": context.target_shot_revision,
            "target_shot_content_hash": context.target_shot_content_hash,
            "continuity_mode": context.continuity_mode,
            "semantic_continuity_state": (
                context.semantic_continuity_state
                if context.continuity_mode
                in {ContinuityMode.REFERENCE, ContinuityMode.SEMANTIC}
                else None
            ),
            "provider_name": capabilities.provider_name,
            "provider_profile": provider_profile,
            "provider_capabilities_fingerprint": (
                capabilities.capabilities_fingerprint
            ),
            "selected_capability_id": selected_capability_id,
            "selected_capability_fingerprint": None,
            "requirement_hash": requirement_hash,
            "execution_kind": None,
            "output_requirement": output_requirement,
            "policy": policy.identity,
        }
        if (
            context.continuity_mode is ContinuityMode.MULTI_ANCHOR
            and requirement_mode is None
        ):
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_CAPABILITY,
                RouterReasonCode.MULTI_ANCHOR_REQUIREMENT_REQUIRED,
                "Multi-anchor continuity cannot route without one sealed C4 requirement.",
            )
        if (
            context.continuity_mode
            in {ContinuityMode.EXACT_TERMINAL, ContinuityMode.REFERENCE}
            and context.upstream_terminal is None
        ):
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_CONTINUITY_TERMINAL,
                "The selected continuity mode requires upstream terminal evidence.",
            )
        if (
            context.continuity_mode
            in {ContinuityMode.REFERENCE, ContinuityMode.SEMANTIC}
            and context.semantic_continuity_state is None
        ):
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_MISSING_INPUT,
                RouterReasonCode.MISSING_SEMANTIC_CONTINUITY_STATE,
                "The selected continuity mode requires a typed continuity-state snapshot.",
            )
        selected = next(
            (
                variant
                for variant in capabilities.variants
                if variant.capability_id == selected_capability_id
            ),
            None,
        )
        if selected is None:
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_CAPABILITY,
                RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
                "The exact capability ID is absent from the sealed snapshot.",
            )
        base.update(
            {
                "selected_capability_id": selected.capability_id,
                "selected_capability_fingerprint": capability_variant_fingerprint(
                    selected
                ),
                "execution_kind": selected.execution_kind,
            }
        )
        if context.activated_shot.visual_strategy not in {
            VisualStrategy.GENERATED_VIDEO,
            VisualStrategy.HYBRID,
        }:
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.ROUTER_REQUIRES_GENERATED_VIDEO_SHOT,
                "Video generation routing only consumes an activated generated-video Shot.",
            )
        if context.motion_requirement is MotionRequirement.HERO_OR_REPAIR:
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.HERO_SHOT_REQUIRES_HYBRID_OR_V2V,
                "Hero or repair routing requires a future exact media-binding slice.",
            )
        required_mode: VideoGenerationMode
        required_roles: tuple[str, ...]
        inputs: tuple[RouterAssetIdentity, ...]
        reason: RouterReasonCode
        rationale: str
        if requirement_mode is not None:
            required_mode = requirement_mode
            required_roles = requirement_binding_roles or ()
            inputs = requirement_input_assets or ()
            reason = RouterReasonCode.CANONICAL_REFERENCES_ENABLE_R2V
            rationale = "Bind the verified neutral requirement to the exact capability."
        elif context.continuity_mode is ContinuityMode.EXACT_TERMINAL:
            assert context.upstream_terminal is not None
            required_mode = VideoGenerationMode.IMAGE_TO_VIDEO
            required_roles = ("first_frame",)
            inputs = (context.upstream_terminal,)
            reason = RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME
            rationale = "Continue from the exact upstream terminal without an intermediate redraw."
        elif context.continuity_mode is ContinuityMode.REFERENCE:
            assert context.upstream_terminal is not None
            if not context.canonical_character_references:
                return self._blocked(
                    base,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_CHARACTER_REFERENCE,
                    "Reference continuity requires an exact character reference.",
                )
            if context.canonical_scene_reference is None:
                return self._blocked(
                    base,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_SCENE_REFERENCE,
                    "Reference continuity requires an exact scene reference.",
                )
            required_mode = VideoGenerationMode.REFERENCE_TO_VIDEO
            inputs = self._continuity_references(context)
            required_roles = ("reference",) * len(inputs)
            reason = RouterReasonCode.REFERENCE_CONTINUITY_USES_TERMINAL_REFERENCE
            rationale = (
                "Use terminal and canonical assets as references without binding terminal "
                "pixels as the next first frame."
            )
        elif context.important_character_ids:
            if selected.mode is VideoGenerationMode.REFERENCE_TO_VIDEO:
                if not context.canonical_character_references:
                    return self._blocked(
                        base,
                        RoutingOutcome.BLOCKED_MISSING_INPUT,
                        RouterReasonCode.MISSING_CHARACTER_REFERENCE,
                        "Reference-to-video requires an exact character reference.",
                    )
                if context.canonical_scene_reference is None:
                    return self._blocked(
                        base,
                        RoutingOutcome.BLOCKED_MISSING_INPUT,
                        RouterReasonCode.MISSING_SCENE_REFERENCE,
                        "Reference-to-video requires an exact scene reference.",
                    )
                required_mode = VideoGenerationMode.REFERENCE_TO_VIDEO
                inputs = self._canonical_references(context)
                required_roles = ("reference",) * len(inputs)
                reason = RouterReasonCode.CANONICAL_REFERENCES_ENABLE_R2V
                rationale = "The exact selected capability can consume canonical references."
            elif selected.mode is VideoGenerationMode.IMAGE_TO_VIDEO:
                if context.shot_keyframe is None:
                    return self._blocked(
                        base,
                        RoutingOutcome.BLOCKED_MISSING_INPUT,
                        RouterReasonCode.MISSING_SHOT_KEYFRAME,
                        "The exact I2V capability requires an activated anchored Shot keyframe.",
                    )
                required_mode = VideoGenerationMode.IMAGE_TO_VIDEO
                required_roles = ("first_frame",)
                inputs = (context.shot_keyframe,)
                reason = RouterReasonCode.IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR
                rationale = "The important character is anchored by the exact Shot keyframe."
            else:
                if not context.canonical_character_references:
                    return self._blocked(
                        base,
                        RoutingOutcome.BLOCKED_MISSING_INPUT,
                        RouterReasonCode.MISSING_CHARACTER_REFERENCE,
                        "Important character routing requires an exact character reference.",
                    )
                if context.canonical_scene_reference is None:
                    return self._blocked(
                        base,
                        RoutingOutcome.BLOCKED_MISSING_INPUT,
                        RouterReasonCode.MISSING_SCENE_REFERENCE,
                        "Important character routing requires an exact scene reference.",
                    )
                required_mode = VideoGenerationMode.REFERENCE_TO_VIDEO
                inputs = self._canonical_references(context)
                required_roles = ("reference",) * len(inputs)
                reason = RouterReasonCode.CANONICAL_REFERENCES_ENABLE_R2V
                rationale = "Canonical references require an exact R2V capability."
        else:
            required_mode = VideoGenerationMode.TEXT_TO_VIDEO
            required_roles = ()
            inputs = ()
            reason = (
                RouterReasonCode.SEMANTIC_CONTINUITY_USES_STATE_ONLY
                if context.continuity_mode is ContinuityMode.SEMANTIC
                else RouterReasonCode.NO_CONTINUITY
            )
            rationale = (
                "Use typed story state without consuming upstream terminal pixels."
                if context.continuity_mode is ContinuityMode.SEMANTIC
                else "The Shot starts an independent visual state."
            )

        if context.continuity_mode is ContinuityMode.SEMANTIC:
            reason = RouterReasonCode.SEMANTIC_CONTINUITY_USES_STATE_ONLY
            rationale = "Use typed continuity state without consuming upstream terminal pixels."

        if (
            required_mode not in context.allowed_generation_modes
            or selected.mode is not required_mode
            or not self._supports_roles(selected, required_roles)
            or not self._supports_assets(selected, inputs)
            or not self._supports_output(selected, output_requirement)
            or provider_profile.profile_version != selected.profile_version
            or not binding_roles_satisfy_variant(selected, required_roles)
        ):
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_CAPABILITY,
                RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
                "The exact selected capability does not satisfy the resolved requirement.",
                required_mode=required_mode,
                required_binding_roles=required_roles,
                input_assets=inputs,
            )
        if selected.execution_kind is VideoExecutionKind.LOCAL:
            if not policy.local_resources_available:
                return self._blocked(
                    base,
                    RoutingOutcome.BLOCKED_POLICY,
                    RouterReasonCode.LOCAL_RESOURCE_POLICY_DENIED,
                    "The exact local capability is unavailable under the resource policy.",
                    required_mode=required_mode,
                    required_binding_roles=required_roles,
                    input_assets=inputs,
                )
        else:
            if not policy.remote_authorized:
                return self._blocked(
                    base,
                    RoutingOutcome.BLOCKED_AUTHORIZATION,
                    RouterReasonCode.REMOTE_AUTHORIZATION_REQUIRED,
                    "The exact remote capability lacks task-scoped authorization.",
                    required_mode=required_mode,
                    required_binding_roles=required_roles,
                    input_assets=inputs,
                )
            if not policy.budget_authorized:
                return self._blocked(
                    base,
                    RoutingOutcome.BLOCKED_POLICY,
                    RouterReasonCode.BUDGET_POLICY_DENIED,
                    "The exact remote capability lacks an accepted budget decision.",
                    required_mode=required_mode,
                    required_binding_roles=required_roles,
                    input_assets=inputs,
                )
        return VideoGenerationRoutingDecision.create(
            **base,
            required_mode=required_mode,
            selected_mode=required_mode,
            required_binding_roles=required_roles,
            input_assets=inputs,
            reason_codes=(reason,),
            rationale=rationale,
            outcome=RoutingOutcome.SELECTED,
        )

    def resolve_requirement(
        self,
        *,
        projection: VerifiedGenerationRequirementProjection,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
        provider_profile: ProviderProfilePointer,
        capabilities: VideoProviderCapabilities,
        selected_capability_id: str,
        output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement,
        lifecycle: VideoGenerationLifecycleEnvelope,
        compiler_contract: AdapterCompilerContract,
    ) -> RequirementRoutingResult:
        """Bind one verified neutral requirement to one exact capability."""

        requirement = projection.requirement
        if (
            projection.target_shot_id != context.target_shot_id
            or projection.target_shot_revision != context.target_shot_revision
            or projection.target_shot_content_hash != context.target_shot_content_hash
            or requirement.target_shot.content_hash
            != context.target_shot_content_hash
        ):
            raise ValueError("verified requirement does not match current routing target")
        if lifecycle.base_registry.revision_id != context.selected_registry_revision_id:
            raise ValueError("lifecycle Registry snapshot is not current for routing")

        effective_policy = effective_policy_for_requirement(requirement, policy)

        expected_mode = requirement_mode(requirement.generation_mode)
        binding_projection = requirement_bindings(requirement, context)
        if expected_mode is None or binding_projection is None:
            decision = self.resolve(
                context=context,
                policy=effective_policy,
                provider_profile=provider_profile,
                capabilities=capabilities,
                selected_capability_id=selected_capability_id,
                output_requirement=output_requirement,
                requirement_hash=requirement.requirement_hash,
            )
            if decision.outcome is RoutingOutcome.SELECTED:
                decision = as_capability_blocked(
                    decision,
                    reason_code=RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
                    outcome=RoutingOutcome.BLOCKED_CAPABILITY,
                    rationale="The neutral generation mode or bindings are unsupported.",
                )
            return RequirementRoutingResult(decision=decision)
        native_roles, input_assets = binding_projection
        decision = self.resolve(
            context=context,
            policy=effective_policy,
            provider_profile=provider_profile,
            capabilities=capabilities,
            selected_capability_id=selected_capability_id,
            output_requirement=output_requirement,
            requirement_hash=requirement.requirement_hash,
            requirement_mode=expected_mode,
            requirement_binding_roles=native_roles,
            requirement_input_assets=input_assets,
        )
        decision = enforce_c4_requirement_gate(
            requirement, context, capabilities, selected_capability_id, decision
        )
        unsupported = requirement_route_is_unsupported(
            requirement, context, expected_mode, decision, output_requirement
        )
        if unsupported and decision.outcome is RoutingOutcome.SELECTED:
            decision = as_capability_blocked(
                decision,
                reason_code=RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
                outcome=RoutingOutcome.BLOCKED_CAPABILITY,
                rationale=(
                    "The exact selected capability cannot express the sealed neutral requirement."
                ),
            )
        if decision.outcome is not RoutingOutcome.SELECTED:
            return RequirementRoutingResult(decision=decision)

        selected = next(
            variant
            for variant in capabilities.variants
            if variant.capability_id == selected_capability_id
        )
        assert decision.selected_capability_fingerprint is not None
        assert decision.selected_mode is not None
        assert decision.execution_kind is not None
        validate_requirement_asset_lineage(requirement, decision)
        bound = ProviderBoundVideoRequest.create(
            plan_hash=projection.plan_hash,
            requirement_hash=requirement.requirement_hash,
            verified_projection_hash=projection.projection_hash,
            target_shot_id=context.target_shot_id,
            target_shot_revision=context.target_shot_revision,
            target_shot_content_hash=context.target_shot_content_hash,
            semantic_routing_hash=decision.semantic_routing_hash,
            audit_decision_hash=decision.audit_decision_hash,
            provider_name=capabilities.provider_name,
            provider_kind=selected.provider_kind,
            model_id=selected.model_id,
            provider_profile=provider_profile,
            capability_id=selected.capability_id,
            capability_fingerprint=decision.selected_capability_fingerprint,
            execution_kind=selected.execution_kind,
            billing_kind=selected.billing_kind,
            mode=decision.selected_mode,
            binding_roles=decision.required_binding_roles,
            input_assets=decision.input_assets,
            output_requirement=output_requirement,
            lifecycle=lifecycle,
            compiler_contract=compiler_contract,
            expression_strength=(
                requirement.generation_intent.camera_intent.expression_strength
            ),
        )
        return RequirementRoutingResult(
            decision=decision,
            provider_bound_request=bound,
        )

    @staticmethod
    def _canonical_references(
        context: ShotRoutingContext,
    ) -> tuple[RouterAssetIdentity, ...]:
        references = (
            *context.canonical_character_references,
            context.canonical_scene_reference,
        )
        return tuple(sorted(references, key=lambda asset: asset.asset_id))

    @classmethod
    def _continuity_references(
        cls,
        context: ShotRoutingContext,
    ) -> tuple[RouterAssetIdentity, ...]:
        assert context.upstream_terminal is not None
        return tuple(
            sorted(
                (context.upstream_terminal, *cls._canonical_references(context)),
                key=lambda asset: asset.asset_id,
            )
        )

    @staticmethod
    def _supports_roles(
        capability: VideoCapabilityVariant,
        required_roles: tuple[str, ...],
    ) -> bool:
        reference_count = sum(1 for role in required_roles if role == "reference")
        if reference_count > capability.max_reference_count:
            return False
        if capability.required_first_frame and (
            not required_roles or required_roles[0] != "first_frame"
        ):
            return False
        image_roles = tuple(
            role
            for role in required_roles
            if role in {"first_frame", "last_frame", "reference"}
        )
        media_roles = tuple(
            role
            for role in required_roles
            if role in {"reference_video", "reference_audio"}
        )
        return bool(
            len(image_roles) + len(media_roles) == len(required_roles)
            and all(role in capability.allowed_image_roles for role in image_roles)
            and all(
                any(
                    role in media_capability.roles
                    for media_capability in capability.media_capabilities
                )
                for role in media_roles
            )
        )

    @staticmethod
    def _supports_output(
        capability: VideoCapabilityVariant,
        output: VideoOutputRequirement | VideoFlexibleOutputRequirement,
    ) -> bool:
        if capability.output is not None:
            return capability.output == output
        return bool(
            capability.output_capability is not None
            and isinstance(output, VideoFlexibleOutputRequirement)
            and capability.output_capability.supports(output)
        )

    @staticmethod
    def _supports_assets(
        capability: VideoCapabilityVariant,
        assets: tuple[RouterAssetIdentity, ...],
    ) -> bool:
        image_assets = tuple(
            asset
            for asset in assets
            if asset.role not in {"reference_video", "reference_audio"}
        )
        media_assets = tuple(
            asset
            for asset in assets
            if asset.role in {"reference_video", "reference_audio"}
        )
        images_supported = all(
            asset.mime_type in capability.allowed_image_mime_types
            and asset.size_bytes is not None
            and asset.size_bytes <= capability.max_image_bytes
            and asset.width is not None
            and asset.width >= capability.min_image_width
            and asset.height is not None
            and asset.height >= capability.min_image_height
            for asset in image_assets
        )
        media_bindings = tuple(
            VideoMediaReferenceBinding(
                kind="video" if asset.role == "reference_video" else "audio",
                role=asset.role,
                asset_id=asset.asset_id,
                asset_sha256=asset.asset_sha256,
                mime_type=asset.mime_type,
                duration_millis=asset.duration_millis or 0,
                size_bytes=asset.size_bytes or 0,
                width=asset.width,
                height=asset.height,
                fps=asset.fps,
            )
            for asset in media_assets
        )
        return bool(
            images_supported
            and media_bindings_satisfy_capabilities(
                media_bindings,
                capability.media_capabilities,
            )
        )

    @staticmethod
    def _blocked(
        base: dict[str, object],
        outcome: RoutingOutcome,
        reason: RouterReasonCode,
        rationale: str,
        *,
        required_mode: VideoGenerationMode | None = None,
        required_binding_roles: tuple[str, ...] = (),
        input_assets: tuple[RouterAssetIdentity, ...] = (),
    ) -> VideoGenerationRoutingDecision:
        return VideoGenerationRoutingDecision.create(
            **base,
            required_mode=required_mode,
            selected_mode=None,
            required_binding_roles=required_binding_roles,
            input_assets=input_assets,
            reason_codes=(reason,),
            rationale=rationale,
            outcome=outcome,
        )
