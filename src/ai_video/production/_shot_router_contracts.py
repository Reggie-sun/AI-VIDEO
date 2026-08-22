"""Immutable contracts for deterministic, provider-neutral Shot routing."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production._video_requirement_routing import (
    validate_provider_bound_projection,
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
    VideoExecutionKind,
    VideoGenerationMode,
    VideoOutputRequirement,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import ExpressionStrength



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
    MULTI_ANCHOR_REQUIREMENT_REQUIRED = "MULTI_ANCHOR_REQUIREMENT_REQUIRED"
    C4_REGISTRY_REVISION_MISMATCH = "C4_REGISTRY_REVISION_MISMATCH"
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
