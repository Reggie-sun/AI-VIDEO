"""Deterministic, provider-neutral Shot routing with no external effects."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production._video_requirement_routing import (
    as_capability_blocked,
    effective_policy_for_requirement,
    requirement_bindings,
    requirement_mode,
    requirement_output_matches,
    validate_provider_bound_projection,
    validate_requirement_asset_lineage,
)
from ai_video.production._video_capability_fingerprint import (
    binding_roles_satisfy_variant,
    capability_variant_fingerprint,
)
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    Shot,
    StrictModel,
    VisualStrategy,
)
from ai_video.production.video import (
    BillingKind,
    ContinuityReferenceBinding,
    HardCutKeyframeBinding,
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
    ContinuityMode as RequirementContinuityMode,
    ExpressionStrength,
    ProviderNeutralVideoRequirement,
    VerifiedGenerationRequirementProjection,
)


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


class RouterReasonCode(str, Enum):
    APPROVED_EXISTING_VIDEO = "APPROVED_EXISTING_VIDEO"
    NO_MOTION_REQUIRED = "NO_MOTION_REQUIRED"
    LIGHT_MOTION_FROM_KEYFRAME = "LIGHT_MOTION_FROM_KEYFRAME"
    GRAPHIC_MOTION_REQUIRED = "GRAPHIC_MOTION_REQUIRED"
    IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR = (
        "IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR"
    )
    EXACT_TERMINAL_USES_FIRST_FRAME = (
        "EXACT_TERMINAL_USES_FIRST_FRAME"
    )
    REFERENCE_CONTINUITY_USES_TERMINAL_REFERENCE = (
        "REFERENCE_CONTINUITY_USES_TERMINAL_REFERENCE"
    )
    SEMANTIC_CONTINUITY_USES_STATE_ONLY = (
        "SEMANTIC_CONTINUITY_USES_STATE_ONLY"
    )
    NO_CONTINUITY = "NO_CONTINUITY"
    CANONICAL_REFERENCES_ENABLE_R2V = "CANONICAL_REFERENCES_ENABLE_R2V"
    FREE_ENVIRONMENT_MOTION_ENABLES_T2V = (
        "FREE_ENVIRONMENT_MOTION_ENABLES_T2V"
    )
    HERO_SHOT_REQUIRES_HYBRID_OR_V2V = "HERO_SHOT_REQUIRES_HYBRID_OR_V2V"
    MISSING_CHARACTER_REFERENCE = "MISSING_CHARACTER_REFERENCE"
    MISSING_SCENE_REFERENCE = "MISSING_SCENE_REFERENCE"
    MISSING_CONTINUITY_TERMINAL = "MISSING_CONTINUITY_TERMINAL"
    MISSING_SEMANTIC_CONTINUITY_STATE = "MISSING_SEMANTIC_CONTINUITY_STATE"
    MISSING_SHOT_KEYFRAME = "MISSING_SHOT_KEYFRAME"
    PROVIDER_CAPABILITY_DENIED = "PROVIDER_CAPABILITY_DENIED"
    LOCAL_RESOURCE_POLICY_DENIED = "LOCAL_RESOURCE_POLICY_DENIED"
    REMOTE_AUTHORIZATION_REQUIRED = "REMOTE_AUTHORIZATION_REQUIRED"
    BUDGET_POLICY_DENIED = "BUDGET_POLICY_DENIED"
    VISUAL_STRATEGY_POLICY_DENIED = "VISUAL_STRATEGY_POLICY_DENIED"
    ROUTER_REQUIRES_GENERATED_VIDEO_SHOT = (
        "ROUTER_REQUIRES_GENERATED_VIDEO_SHOT"
    )


class RouterAssetIdentity(_RouterModel):
    role: Literal[
        "existing_video",
        "character_reference",
        "scene_reference",
        "first_frame",
        "last_frame",
        "continuity_terminal",
        "reference_video",
        "reference_audio",
    ]
    asset_id: str = Field(pattern=_SAFE_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    source_registry_revision_id: str = Field(pattern=_SHA256)
    canonical_owner_kind: Literal["character", "scene"] | None = None
    canonical_owner_id: str | None = Field(default=None, pattern=_SAFE_ID)
    canonical_owner_content_hash: str | None = Field(default=None, pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    size_bytes: int | None = Field(default=None, strict=True, gt=0)
    width: int | None = Field(default=None, strict=True, gt=0)
    height: int | None = Field(default=None, strict=True, gt=0)
    duration_millis: int | None = Field(default=None, strict=True, gt=0)
    fps: int | None = Field(default=None, strict=True, gt=0, le=240)

    @model_validator(mode="after")
    def _validate_canonical_owner(self) -> "RouterAssetIdentity":
        owner_values = (
            self.canonical_owner_kind,
            self.canonical_owner_id,
            self.canonical_owner_content_hash,
        )
        if any(value is not None for value in owner_values) and any(
            value is None for value in owner_values
        ):
            raise ValueError("canonical asset owner identity must be fully specified")
        expected_owner = {
            "character_reference": "character",
            "scene_reference": "scene",
        }.get(self.role)
        if expected_owner is None and any(value is not None for value in owner_values):
            raise ValueError("non-canonical routing assets cannot claim an artifact owner")
        if expected_owner is not None and self.canonical_owner_kind != expected_owner:
            raise ValueError(f"{self.role} requires a canonical {expected_owner} owner")
        if self.role == "reference_video" and any(
            value is None
            for value in (
                self.size_bytes,
                self.width,
                self.height,
                self.duration_millis,
                self.fps,
            )
        ):
            raise ValueError("video reference requires exact measured metadata")
        if self.role == "reference_audio" and (
            self.size_bytes is None
            or self.duration_millis is None
            or any(value is not None for value in (self.width, self.height, self.fps))
        ):
            raise ValueError("audio reference requires exact audio-only metadata")
        return self


class RouterContinuityState(_RouterModel):
    """Exact semantic state inherited without requiring upstream pixels."""

    state_id: str = Field(pattern=_SAFE_ID)
    state_revision: int = Field(strict=True, ge=1)
    character_identity_hashes: tuple[str, ...]
    story_state_hash: str = Field(pattern=_SHA256)
    wardrobe_state_hashes: tuple[str, ...]
    injury_state_hashes: tuple[str, ...]
    prop_state_hashes: tuple[str, ...]
    scene_state_hash: str | None = Field(default=None, pattern=_SHA256)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hash_sets(self) -> "RouterContinuityState":
        for values, label in (
            (self.character_identity_hashes, "character identity hashes"),
            (self.wardrobe_state_hashes, "wardrobe state hashes"),
            (self.injury_state_hashes, "injury state hashes"),
            (self.prop_state_hashes, "prop state hashes"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{label} must be unique")
            if tuple(sorted(values)) != values:
                raise ValueError(f"{label} must use canonical sorted order")
            if any(
                len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in values
            ):
                raise ValueError(f"{label} must be lowercase SHA-256")
        expected = canonical_sha256(
            {
                "schema": "ai-video-router-continuity-state/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("continuity state hash does not match content")
        return self

    @property
    def shot_constraint_token(self) -> str:
        return f"continuity-state:{self.content_hash}"

    @classmethod
    def create(cls, **values: object) -> "RouterContinuityState":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "ai-video-router-continuity-state/1",
                **candidate.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class RouterPolicyIdentity(_RouterModel):
    policy_id: str = Field(pattern=_SAFE_ID)
    policy_version: str = Field(pattern=_SAFE_ID)
    policy_sha256: str = Field(pattern=_SHA256)


class VideoRoutingPolicy(_RouterModel):
    identity: RouterPolicyIdentity
    local_resources_available: bool = Field(strict=True)
    remote_authorized: bool = Field(strict=True)
    budget_authorized: bool = Field(strict=True)


class AdapterCompilerContract(_RouterModel):
    compiler_id: str = Field(pattern=_SAFE_ID)
    compiler_version: str = Field(pattern=_SAFE_ID)
    compiler_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hash(self) -> "AdapterCompilerContract":
        expected = canonical_sha256(
            {
                "schema": "ai-video-adapter-compiler-contract/1",
                "compiler_id": self.compiler_id,
                "compiler_version": self.compiler_version,
            }
        )
        if self.compiler_hash != expected:
            raise ValueError("compiler hash does not match compiler identity")
        return self

    @classmethod
    def create(cls, *, compiler_id: str, compiler_version: str) -> "AdapterCompilerContract":
        return cls(
            compiler_id=compiler_id,
            compiler_version=compiler_version,
            compiler_hash=canonical_sha256(
                {
                    "schema": "ai-video-adapter-compiler-contract/1",
                    "compiler_id": compiler_id,
                    "compiler_version": compiler_version,
                }
            ),
        )


class VideoGenerationLifecycleEnvelope(_RouterModel):
    generation_id: str = Field(pattern=_SAFE_ID)
    target_asset_role: str = Field(pattern=_SAFE_ID)
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    base_dependency_graph: DependencyGraphSnapshotPointer
    input_artifact_ids: tuple[str, ...]
    output_asset_id: str = Field(pattern=_SAFE_ID)
    continuity_binding: ContinuityReferenceBinding | None = None
    hard_cut_keyframe_binding: HardCutKeyframeBinding | None = None
    seal_terminal_frame: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def _validate_inputs(self) -> "VideoGenerationLifecycleEnvelope":
        if not self.input_artifact_ids:
            raise ValueError("lifecycle envelope requires input artifact identities")
        if len(set(self.input_artifact_ids)) != len(self.input_artifact_ids):
            raise ValueError("lifecycle input artifact identities must be unique")
        if (
            self.continuity_binding is not None
            and self.hard_cut_keyframe_binding is not None
        ):
            raise ValueError(
                "lifecycle envelope cannot combine continuation and hard-cut bindings"
            )
        return self


class ShotRoutingContext(_RouterModel):
    activated_shot: Shot
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    storyboard_revision: int = Field(strict=True, ge=1)
    storyboard_content_hash: str = Field(pattern=_SHA256)
    selected_registry_revision_id: str = Field(pattern=_SHA256)
    character_bible_content_hashes: tuple[str, ...]
    scene_content_hash: str = Field(pattern=_SHA256)
    important_character_ids: tuple[str, ...]
    canonical_character_references: tuple[RouterAssetIdentity, ...]
    canonical_scene_reference: RouterAssetIdentity | None
    approved_existing_video: RouterAssetIdentity | None
    shot_keyframe: RouterAssetIdentity | None
    upstream_terminal: RouterAssetIdentity | None
    last_frame: RouterAssetIdentity | None = None
    reference_videos: tuple[RouterAssetIdentity, ...] = ()
    reference_audios: tuple[RouterAssetIdentity, ...] = ()
    motion_requirement: MotionRequirement
    continuity_mode: ContinuityMode
    semantic_continuity_state: RouterContinuityState | None
    allowed_visual_strategies: tuple[VisualStrategy, ...] = Field(min_length=1)
    allowed_generation_modes: tuple[VideoGenerationMode, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_exact_context(self) -> "ShotRoutingContext":
        if (
            not verify_artifact_hash(self.activated_shot)
            or self.activated_shot.shot_id != self.target_shot_id
            or self.activated_shot.revision != self.target_shot_revision
            or self.activated_shot.content_hash != self.target_shot_content_hash
        ):
            raise ValueError("routing target must match the exact sealed activated Shot")
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
        if len(self.character_bible_content_hashes) != len(
            self.important_character_ids
        ):
            raise ValueError("important Character IDs and Bible hashes must align")
        if not set(self.important_character_ids).issubset(
            self.activated_shot.character_ids
        ):
            raise ValueError("important Character IDs must belong to the target Shot")
        if (
            self.continuity_mode
            in {ContinuityMode.REFERENCE, ContinuityMode.SEMANTIC}
            and self.semantic_continuity_state is not None
            and self.semantic_continuity_state.shot_constraint_token
            not in self.activated_shot.continuity_constraints
        ):
            raise ValueError(
                "continuity state must be materialized in the activated target Shot"
            )
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
            *((self.last_frame,) if self.last_frame else ()),
            *self.reference_videos,
            *self.reference_audios,
        )
        if any(
            item.source_registry_revision_id != self.selected_registry_revision_id
            for item in identities
        ):
            raise ValueError("routing assets must use the exact selected Registry revision")
        if len({(item.role, item.asset_id) for item in identities}) != len(identities):
            raise ValueError("routing asset role and ID pairs must be unique")
        canonical_references = (
            *self.canonical_character_references,
            *((self.canonical_scene_reference,) if self.canonical_scene_reference else ()),
        )
        if len({item.asset_id for item in canonical_references}) != len(
            canonical_references
        ):
            raise ValueError("canonical routing reference asset IDs must be unique")
        for reference in self.reference_videos:
            self._require_asset(reference, "reference_video", "video reference")
        for reference in self.reference_audios:
            self._require_asset(reference, "reference_audio", "audio reference")
        if (
            self.continuity_mode is ContinuityMode.REFERENCE
            and self.upstream_terminal is not None
            and self.upstream_terminal.asset_id
            in {item.asset_id for item in canonical_references}
        ):
            raise ValueError(
                "reference continuity inputs must project to unique request bindings"
            )
        character_owners = dict(
            zip(
                self.important_character_ids,
                self.character_bible_content_hashes,
                strict=True,
            )
        )
        for reference in self.canonical_character_references:
            self._require_asset(reference, "character_reference", "character reference")
            if (
                reference.canonical_owner_id not in character_owners
                or character_owners[reference.canonical_owner_id]
                != reference.canonical_owner_content_hash
            ):
                raise ValueError(
                    "character reference must match an exact important Character"
                )
        if self.canonical_scene_reference is not None:
            self._require_asset(
                self.canonical_scene_reference,
                "scene_reference",
                "scene reference",
            )
            if (
                self.canonical_scene_reference.canonical_owner_id
                != self.activated_shot.scene_id
                or self.canonical_scene_reference.canonical_owner_content_hash
                != self.scene_content_hash
            ):
                raise ValueError("scene reference must match the exact target Scene")
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
        if self.last_frame is not None:
            self._require_asset(self.last_frame, "last_frame", "last frame")
        return self

    @staticmethod
    def _require_asset(
        asset: RouterAssetIdentity,
        expected_role: str,
        label: str,
    ) -> None:
        if asset.role != expected_role:
            raise ValueError(f"{label} must use role {expected_role}")
        if expected_role == "reference_audio":
            if asset.size_bytes is None or asset.duration_millis is None:
                raise ValueError(
                    f"{label} requires measured size and duration"
                )
            return
        if any(
            value is None for value in (asset.size_bytes, asset.width, asset.height)
        ):
            raise ValueError(f"{label} requires measured size and dimensions")


class ShotVisualRoutingProposal(_RouterModel):
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    continuity_mode: ContinuityMode
    semantic_continuity_state: RouterContinuityState | None
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
    continuity_mode: ContinuityMode
    semantic_continuity_state: RouterContinuityState | None
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
    requirement_hash: str | None = Field(default=None, pattern=_SHA256)
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
        payload: dict[str, object] = {
            "schema": (
                "ai-video-shot-routing-semantic/3"
                if self.requirement_hash is not None
                else "ai-video-shot-routing-semantic/2"
            ),
            "target_shot_id": self.target_shot_id,
            "target_shot_revision": self.target_shot_revision,
            "target_shot_content_hash": self.target_shot_content_hash,
            "continuity_mode": self.continuity_mode.value,
            "semantic_continuity_state": (
                self.semantic_continuity_state.model_dump(mode="json")
                if self.semantic_continuity_state is not None
                else None
            ),
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
        if self.requirement_hash is not None:
            payload["requirement_hash"] = self.requirement_hash
        return payload

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
        projected_bindings = tuple(
            (role, asset.asset_id)
            for role, asset in zip(
                self.required_binding_roles,
                self.input_assets,
                strict=True,
            )
        )
        if len(set(projected_bindings)) != len(projected_bindings):
            raise ValueError("routing decision must project unique request bindings")
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


class ProviderBoundVideoRequest(_RouterModel):
    """Prompt-free sealed projection owned by the Shot Router."""

    plan_hash: str = Field(pattern=_SHA256)
    requirement_hash: str = Field(pattern=_SHA256)
    verified_projection_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    semantic_routing_hash: str = Field(pattern=_SHA256)
    audit_decision_hash: str = Field(pattern=_SHA256)
    provider_name: str = Field(pattern=_SAFE_ID)
    provider_kind: str = Field(pattern=_SAFE_ID)
    model_id: str = Field(pattern=_SAFE_ID)
    provider_profile: ProviderProfilePointer
    capability_id: str = Field(pattern=_SAFE_ID)
    capability_fingerprint: str = Field(pattern=_SHA256)
    execution_kind: VideoExecutionKind
    billing_kind: BillingKind
    mode: VideoGenerationMode
    binding_roles: tuple[
        Literal[
            "first_frame",
            "last_frame",
            "reference",
            "reference_video",
            "reference_audio",
        ],
        ...,
    ]
    input_assets: tuple[RouterAssetIdentity, ...]
    output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement
    lifecycle: VideoGenerationLifecycleEnvelope
    compiler_contract: AdapterCompilerContract
    expression_strength: ExpressionStrength
    provider_bound_request_hash: str = Field(pattern=_SHA256)

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema": "provider-bound-video-request/1",
            **self.model_dump(
                mode="json",
                exclude={"provider_bound_request_hash"},
            ),
        }

    @model_validator(mode="after")
    def _validate_bound_request(self) -> "ProviderBoundVideoRequest":
        validate_provider_bound_projection(self)
        if self.provider_bound_request_hash != canonical_sha256(self._hash_payload()):
            raise ValueError("provider-bound request hash does not match projection")
        return self

    @classmethod
    def create(cls, **values: object) -> "ProviderBoundVideoRequest":
        data = dict(values)
        candidate = cls.model_construct(
            **data,
            provider_bound_request_hash="0" * 64,
        )
        data["provider_bound_request_hash"] = canonical_sha256(
            candidate._hash_payload()
        )
        return cls.model_validate(data)


class RequirementRoutingResult(_RouterModel):
    decision: VideoGenerationRoutingDecision
    provider_bound_request: ProviderBoundVideoRequest | None = None

    @model_validator(mode="after")
    def _validate_outcome(self) -> "RequirementRoutingResult":
        selected = self.decision.outcome is RoutingOutcome.SELECTED
        if selected != (self.provider_bound_request is not None):
            raise ValueError(
                "selected requirement routing must have exactly one provider-bound request"
            )
        return self


class ShotVisualResolver:
    """Resolve an authoring proposal without mutating canonical Shot state."""

    def resolve(
        self,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
    ) -> ShotVisualRoutingProposal:
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
        unsupported = (
            requirement.continuity_mode.value != context.continuity_mode.value
            or expected_mode is not decision.required_mode
            or not requirement_output_matches(
                requirement,
                output_requirement,
            )
            or requirement.generation_intent.camera_intent.expression_strength
            is ExpressionStrength.NATIVE_CONTROL_REQUIRED
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
