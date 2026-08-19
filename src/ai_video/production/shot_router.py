"""Deterministic, provider-neutral Shot routing with no external effects."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel, VisualStrategy
from ai_video.production.video import (
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoOutputRequirement,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"


class _RouterModel(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class RoutingOutcome(str, Enum):
    PROPOSED = "proposed"
    SELECTED = "selected"
    BLOCKED_MISSING_INPUT = "blocked_missing_input"
    BLOCKED_CAPABILITY = "blocked_capability"
    BLOCKED_POLICY = "blocked_policy"
    BLOCKED_AUTHORIZATION = "blocked_authorization"


class ContinuityIntent(str, Enum):
    NONE = "none"
    CONTINUOUS_TAKE = "continuous_take"
    HARD_CUT = "hard_cut"


class MotionRequirement(str, Enum):
    NONE = "none"
    LIGHT_TRANSFORM = "light_transform"
    GRAPHIC = "graphic"
    CHARACTER_ACTION = "character_action"
    FREE_COMPLEX = "free_complex"
    HERO_OR_REPAIR = "hero_or_repair"


class RouterReasonCode(str, Enum):
    APPROVED_EXISTING_VIDEO = "APPROVED_EXISTING_VIDEO"
    NO_MOTION_REQUIRED = "NO_MOTION_REQUIRED"
    LIGHT_MOTION_FROM_KEYFRAME = "LIGHT_MOTION_FROM_KEYFRAME"
    GRAPHIC_MOTION_REQUIRED = "GRAPHIC_MOTION_REQUIRED"
    IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR = (
        "IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR"
    )
    CONTINUOUS_TAKE_USES_TERMINAL_FIRST_FRAME = (
        "CONTINUOUS_TAKE_USES_TERMINAL_FIRST_FRAME"
    )
    CANONICAL_REFERENCES_ENABLE_R2V = "CANONICAL_REFERENCES_ENABLE_R2V"
    FREE_ENVIRONMENT_MOTION_ENABLES_T2V = (
        "FREE_ENVIRONMENT_MOTION_ENABLES_T2V"
    )
    HERO_SHOT_REQUIRES_HYBRID_OR_V2V = "HERO_SHOT_REQUIRES_HYBRID_OR_V2V"
    MISSING_CHARACTER_REFERENCE = "MISSING_CHARACTER_REFERENCE"
    MISSING_SCENE_REFERENCE = "MISSING_SCENE_REFERENCE"
    MISSING_CONTINUITY_TERMINAL = "MISSING_CONTINUITY_TERMINAL"
    MISSING_SHOT_KEYFRAME = "MISSING_SHOT_KEYFRAME"
    PROVIDER_CAPABILITY_DENIED = "PROVIDER_CAPABILITY_DENIED"
    LOCAL_RESOURCE_POLICY_DENIED = "LOCAL_RESOURCE_POLICY_DENIED"
    REMOTE_AUTHORIZATION_REQUIRED = "REMOTE_AUTHORIZATION_REQUIRED"
    BUDGET_POLICY_DENIED = "BUDGET_POLICY_DENIED"
    VISUAL_STRATEGY_POLICY_DENIED = "VISUAL_STRATEGY_POLICY_DENIED"
    ROUTER_REQUIRES_GENERATED_VIDEO_SHOT = (
        "ROUTER_REQUIRES_GENERATED_VIDEO_SHOT"
    )
    HARD_CUT_CONTINUITY_QUALITY_UNACCEPTED = (
        "HARD_CUT_CONTINUITY_QUALITY_UNACCEPTED"
    )


class RouterAssetIdentity(_RouterModel):
    role: Literal[
        "existing_video",
        "character_reference",
        "scene_reference",
        "first_frame",
        "continuity_terminal",
        "reference_video",
        "reference_audio",
    ]
    asset_id: str = Field(pattern=_SAFE_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    size_bytes: int | None = Field(default=None, strict=True, gt=0)
    width: int | None = Field(default=None, strict=True, gt=0)
    height: int | None = Field(default=None, strict=True, gt=0)


class RouterPolicyIdentity(_RouterModel):
    policy_id: str = Field(pattern=_SAFE_ID)
    policy_version: str = Field(pattern=_SAFE_ID)
    policy_sha256: str = Field(pattern=_SHA256)


class VideoRoutingPolicy(_RouterModel):
    identity: RouterPolicyIdentity
    local_resources_available: bool = Field(strict=True)
    remote_authorized: bool = Field(strict=True)
    budget_authorized: bool = Field(strict=True)


class ShotRoutingContext(_RouterModel):
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    storyboard_revision: int = Field(strict=True, ge=1)
    storyboard_content_hash: str = Field(pattern=_SHA256)
    character_bible_content_hashes: tuple[str, ...]
    scene_content_hash: str = Field(pattern=_SHA256)
    important_character_ids: tuple[str, ...]
    canonical_character_references: tuple[RouterAssetIdentity, ...]
    canonical_scene_reference: RouterAssetIdentity | None
    approved_existing_video: RouterAssetIdentity | None
    shot_keyframe: RouterAssetIdentity | None
    upstream_terminal: RouterAssetIdentity | None
    motion_requirement: MotionRequirement
    continuity_intent: ContinuityIntent
    allowed_visual_strategies: tuple[VisualStrategy, ...] = Field(min_length=1)
    allowed_generation_modes: tuple[VideoGenerationMode, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_exact_context(self) -> "ShotRoutingContext":
        for value in self.character_bible_content_hashes:
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError("character Bible hashes must be lowercase SHA-256")
        for values, label in (
            (self.character_bible_content_hashes, "character Bible hashes"),
            (self.important_character_ids, "important character IDs"),
            (self.allowed_visual_strategies, "allowed visual strategies"),
            (self.allowed_generation_modes, "allowed generation modes"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{label} must be unique")
        identities = (
            *self.canonical_character_references,
            *(
                (self.canonical_scene_reference,)
                if self.canonical_scene_reference is not None
                else ()
            ),
            *((self.approved_existing_video,) if self.approved_existing_video else ()),
            *((self.shot_keyframe,) if self.shot_keyframe else ()),
            *((self.upstream_terminal,) if self.upstream_terminal else ()),
        )
        if len({(item.role, item.asset_id) for item in identities}) != len(identities):
            raise ValueError("routing asset role and ID pairs must be unique")
        for reference in self.canonical_character_references:
            self._require_asset(reference, "character_reference", "character reference")
        if self.canonical_scene_reference is not None:
            self._require_asset(
                self.canonical_scene_reference,
                "scene_reference",
                "scene reference",
            )
        if self.approved_existing_video is not None:
            self._require_asset(
                self.approved_existing_video,
                "existing_video",
                "approved existing video",
            )
            if self.approved_existing_video.mime_type != "video/mp4":
                raise ValueError("approved existing video must use video/mp4 MIME")
        if self.shot_keyframe is not None:
            self._require_asset(self.shot_keyframe, "first_frame", "Shot keyframe")
        if self.upstream_terminal is not None:
            self._require_asset(
                self.upstream_terminal,
                "continuity_terminal",
                "upstream terminal",
            )
        return self

    @staticmethod
    def _require_asset(
        asset: RouterAssetIdentity,
        expected_role: str,
        label: str,
    ) -> None:
        if asset.role != expected_role:
            raise ValueError(f"{label} must use role {expected_role}")
        if any(
            value is None for value in (asset.size_bytes, asset.width, asset.height)
        ):
            raise ValueError(f"{label} requires measured size and dimensions")


class ShotVisualRoutingProposal(_RouterModel):
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    proposed_visual_strategy: VisualStrategy | None
    required_generation_mode: VideoGenerationMode | None
    required_binding_roles: tuple[str, ...]
    reason_codes: tuple[RouterReasonCode, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    policy: RouterPolicyIdentity
    outcome: Literal[
        RoutingOutcome.PROPOSED,
        RoutingOutcome.BLOCKED_MISSING_INPUT,
        RoutingOutcome.BLOCKED_POLICY,
        RoutingOutcome.BLOCKED_AUTHORIZATION,
    ]
    proposal_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_proposal(self) -> "ShotVisualRoutingProposal":
        if self.outcome is RoutingOutcome.PROPOSED:
            if self.proposed_visual_strategy is None:
                raise ValueError("proposed routing outcome requires a visual strategy")
        elif self.proposed_visual_strategy is not None:
            raise ValueError("blocked routing outcome cannot propose a visual strategy")
        if self.proposal_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"proposal_hash"})
        ):
            raise ValueError("proposal hash does not match visual routing proposal")
        return self

    @classmethod
    def create(cls, **values: object) -> "ShotVisualRoutingProposal":
        data = dict(values)
        candidate = cls.model_construct(**data, proposal_hash="0" * 64)
        data["proposal_hash"] = canonical_sha256(
            candidate.model_dump(
                mode="json",
                exclude={"proposal_hash"},
                warnings=False,
            )
        )
        return cls.model_validate(data)


class VideoGenerationRoutingDecision(_RouterModel):
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    required_mode: VideoGenerationMode | None
    selected_mode: VideoGenerationMode | None
    required_binding_roles: tuple[str, ...]
    input_assets: tuple[RouterAssetIdentity, ...]
    provider_name: str = Field(pattern=_SAFE_ID)
    provider_profile: ProviderProfilePointer
    provider_capabilities_fingerprint: str = Field(pattern=_SHA256)
    selected_capability_id: str = Field(pattern=_SAFE_ID)
    selected_capability_fingerprint: str | None = Field(
        default=None,
        pattern=_SHA256,
    )
    execution_kind: VideoExecutionKind | None
    output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement
    reason_codes: tuple[RouterReasonCode, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    policy: RouterPolicyIdentity
    outcome: Literal[
        RoutingOutcome.SELECTED,
        RoutingOutcome.BLOCKED_MISSING_INPUT,
        RoutingOutcome.BLOCKED_CAPABILITY,
        RoutingOutcome.BLOCKED_POLICY,
        RoutingOutcome.BLOCKED_AUTHORIZATION,
    ]
    semantic_routing_hash: str = Field(pattern=_SHA256)
    audit_decision_hash: str = Field(pattern=_SHA256)

    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema": "ai-video-shot-routing-semantic/1",
            "target_shot_id": self.target_shot_id,
            "target_shot_revision": self.target_shot_revision,
            "target_shot_content_hash": self.target_shot_content_hash,
            "required_mode": (
                self.required_mode.value if self.required_mode is not None else None
            ),
            "required_binding_roles": self.required_binding_roles,
            "input_assets": tuple(
                asset.model_dump(mode="json") for asset in self.input_assets
            ),
            "provider_name": self.provider_name,
            "provider_profile": self.provider_profile.model_dump(mode="json"),
            "selected_capability_id": self.selected_capability_id,
            "selected_capability_fingerprint": self.selected_capability_fingerprint,
            "execution_kind": (
                self.execution_kind.value
                if self.execution_kind is not None
                else None
            ),
            "output_requirement": self.output_requirement.model_dump(mode="json"),
        }

    @model_validator(mode="after")
    def _validate_decision(self) -> "VideoGenerationRoutingDecision":
        if self.outcome is RoutingOutcome.SELECTED and self.selected_mode is None:
            raise ValueError("selected routing outcome requires a generation mode")
        if self.outcome is not RoutingOutcome.SELECTED and self.selected_mode is not None:
            raise ValueError("blocked routing outcome cannot select a generation mode")
        if (
            self.selected_mode is not None
            and self.selected_mode is not self.required_mode
        ):
            raise ValueError("selected generation mode must match the required mode")
        if self.outcome is RoutingOutcome.SELECTED and (
            self.selected_capability_fingerprint is None
            or self.execution_kind is None
        ):
            raise ValueError("selected routing outcome requires an exact capability")
        if self.semantic_routing_hash != canonical_sha256(self.semantic_payload()):
            raise ValueError("semantic routing hash does not match decision")
        audit_payload = {
            "schema": "ai-video-shot-routing-audit/1",
            "semantic_routing_hash": self.semantic_routing_hash,
            "policy": self.policy.model_dump(mode="json"),
            "reason_codes": tuple(reason.value for reason in self.reason_codes),
            "rationale": self.rationale,
            "outcome": self.outcome.value,
            "selected_mode": (
                self.selected_mode.value if self.selected_mode is not None else None
            ),
            "provider_capabilities_fingerprint": (
                self.provider_capabilities_fingerprint
            ),
        }
        if self.audit_decision_hash != canonical_sha256(audit_payload):
            raise ValueError("audit decision hash does not match decision")
        return self

    @classmethod
    def create(cls, **values: object) -> "VideoGenerationRoutingDecision":
        data = dict(values)
        candidate = cls.model_construct(
            **data,
            semantic_routing_hash="0" * 64,
            audit_decision_hash="0" * 64,
        )
        semantic_hash = canonical_sha256(candidate.semantic_payload())
        data["semantic_routing_hash"] = semantic_hash
        data["audit_decision_hash"] = canonical_sha256(
            {
                "schema": "ai-video-shot-routing-audit/1",
                "semantic_routing_hash": semantic_hash,
                "policy": candidate.policy.model_dump(mode="json"),
                "reason_codes": tuple(
                    reason.value for reason in candidate.reason_codes
                ),
                "rationale": candidate.rationale,
                "outcome": candidate.outcome.value,
                "selected_mode": (
                    candidate.selected_mode.value
                    if candidate.selected_mode is not None
                    else None
                ),
                "provider_capabilities_fingerprint": (
                    candidate.provider_capabilities_fingerprint
                ),
            }
        )
        return cls.model_validate(data)


class ShotVisualResolver:
    """Resolve an authoring proposal without mutating canonical Shot state."""

    def resolve(
        self,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
    ) -> ShotVisualRoutingProposal:
        if context.continuity_intent is ContinuityIntent.HARD_CUT:
            return self._blocked(
                context,
                policy,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.HARD_CUT_CONTINUITY_QUALITY_UNACCEPTED,
                "C2 hard-cut character continuity has not passed subjective quality acceptance.",
            )
        if context.approved_existing_video is not None:
            return self._propose(
                context,
                policy,
                VisualStrategy.EXISTING_VIDEO,
                RouterReasonCode.APPROVED_EXISTING_VIDEO,
                "An exact approved video asset already satisfies the Shot.",
            )
        if context.continuity_intent is ContinuityIntent.CONTINUOUS_TAKE:
            if context.upstream_terminal is None:
                return self._blocked(
                    context,
                    policy,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_CONTINUITY_TERMINAL,
                    "Continuous-take routing requires the exact upstream terminal frame.",
                )
            return self._propose(
                context,
                policy,
                VisualStrategy.GENERATED_VIDEO,
                RouterReasonCode.CONTINUOUS_TAKE_USES_TERMINAL_FIRST_FRAME,
                "Continue the action from the exact terminal frame without redrawing it.",
                required_generation_mode=VideoGenerationMode.IMAGE_TO_VIDEO,
                required_binding_roles=("first_frame",),
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
            proposed_visual_strategy=None,
            required_generation_mode=None,
            required_binding_roles=(),
            reason_codes=(reason,),
            rationale=rationale,
            policy=policy.identity,
            outcome=outcome,
        )


class VideoGenerationResolver:
    """Resolve one exact selected capability without provider fallback."""

    def resolve(
        self,
        *,
        context: ShotRoutingContext,
        activated_visual_strategy: VisualStrategy,
        policy: VideoRoutingPolicy,
        provider_profile: ProviderProfilePointer,
        capabilities: VideoProviderCapabilities,
        selected_capability_id: str,
        output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement,
    ) -> VideoGenerationRoutingDecision:
        base: dict[str, object] = {
            "target_shot_id": context.target_shot_id,
            "target_shot_revision": context.target_shot_revision,
            "target_shot_content_hash": context.target_shot_content_hash,
            "provider_name": capabilities.provider_name,
            "provider_profile": provider_profile,
            "provider_capabilities_fingerprint": (
                capabilities.capabilities_fingerprint
            ),
            "selected_capability_id": selected_capability_id,
            "selected_capability_fingerprint": None,
            "execution_kind": None,
            "output_requirement": output_requirement,
            "policy": policy.identity,
        }
        if context.continuity_intent is ContinuityIntent.HARD_CUT:
            return self._blocked(
                base,
                RoutingOutcome.BLOCKED_POLICY,
                RouterReasonCode.HARD_CUT_CONTINUITY_QUALITY_UNACCEPTED,
                "C2 hard-cut character continuity has not passed subjective quality acceptance.",
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
                "selected_capability_fingerprint": canonical_sha256(
                    selected.model_dump(mode="json")
                ),
                "execution_kind": selected.execution_kind,
            }
        )
        if activated_visual_strategy not in {
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
        if context.continuity_intent is ContinuityIntent.CONTINUOUS_TAKE:
            if context.upstream_terminal is None:
                return self._blocked(
                    base,
                    RoutingOutcome.BLOCKED_MISSING_INPUT,
                    RouterReasonCode.MISSING_CONTINUITY_TERMINAL,
                    "Continuous-take routing requires the exact upstream terminal frame.",
                )
            required_mode = VideoGenerationMode.IMAGE_TO_VIDEO
            required_roles = ("first_frame",)
            inputs = (context.upstream_terminal,)
            reason = RouterReasonCode.CONTINUOUS_TAKE_USES_TERMINAL_FIRST_FRAME
            rationale = "Continue from the exact upstream terminal without an intermediate redraw."
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
            reason = RouterReasonCode.FREE_ENVIRONMENT_MOTION_ENABLES_T2V
            rationale = "The Shot has no important identity or continuity edge."

        if (
            required_mode not in context.allowed_generation_modes
            or selected.mode is not required_mode
            or not self._supports_roles(selected, required_roles)
            or not self._supports_assets(selected, inputs)
            or not self._supports_output(selected, output_requirement)
            or provider_profile.profile_version != selected.profile_version
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

    @staticmethod
    def _canonical_references(
        context: ShotRoutingContext,
    ) -> tuple[RouterAssetIdentity, ...]:
        references = (
            *context.canonical_character_references,
            context.canonical_scene_reference,
        )
        return tuple(sorted(references, key=lambda asset: asset.asset_id))

    @staticmethod
    def _supports_roles(
        capability: VideoCapabilityVariant,
        required_roles: tuple[str, ...],
    ) -> bool:
        if len(required_roles) > capability.max_reference_count:
            return False
        if capability.required_first_frame and (
            not required_roles or required_roles[0] != "first_frame"
        ):
            return False
        return all(role in capability.allowed_image_roles for role in required_roles)

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
        return all(
            asset.mime_type in capability.allowed_image_mime_types
            and asset.size_bytes is not None
            and asset.size_bytes <= capability.max_image_bytes
            and asset.width is not None
            and asset.width >= capability.min_image_width
            and asset.height is not None
            and asset.height >= capability.min_image_height
            for asset in assets
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
