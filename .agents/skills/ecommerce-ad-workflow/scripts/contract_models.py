"""Strict ecommerce advertising authoring contract models."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


SHA256_PATTERN = r"^[0-9a-f]{64}$"

NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]
Identifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=120,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$",
    ),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        strict=True,
    )


class RightsStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


class ClaimType(str, Enum):
    FACT = "FACT"
    BENEFIT = "BENEFIT"
    COMPARISON = "COMPARISON"
    MEDICAL_OR_THERAPEUTIC = "MEDICAL_OR_THERAPEUTIC"


class ProductSourceAsset(StrictModel):
    asset_id: Identifier
    source_kind: Literal["IMAGE", "VIDEO", "BRAND_GUIDE", "PAGE_SNAPSHOT"]
    reference: NonEmptyText
    rights_status: RightsStatus


class ProductInput(StrictModel):
    sku_id: Identifier
    name: NonEmptyText
    source_assets: tuple[ProductSourceAsset, ...] = Field(min_length=1)
    landing_page_reference: NonEmptyText | None


class TruthSource(StrictModel):
    source_id: Identifier
    source_kind: Literal[
        "PRODUCT_ASSET", "PRODUCT_PAGE", "BRAND_DOCUMENT", "USER_ATTESTATION"
    ]
    reference: NonEmptyText
    rights_status: RightsStatus


class ProductFact(StrictModel):
    fact_id: Identifier
    statement: NonEmptyText
    source_ids: tuple[Identifier, ...] = Field(min_length=1)


class AllowedClaim(StrictModel):
    claim_id: Identifier
    text: NonEmptyText
    claim_type: ClaimType
    fact_ids: tuple[Identifier, ...] = Field(min_length=1)
    source_ids: tuple[Identifier, ...] = Field(min_length=1)


class ProhibitedClaim(StrictModel):
    claim_id: Identifier
    text: NonEmptyText
    claim_type: ClaimType
    reason: NonEmptyText


class ProductTruthInput(StrictModel):
    sources: tuple[TruthSource, ...] = Field(min_length=1)
    facts: tuple[ProductFact, ...] = Field(min_length=1)
    allowed_claims: tuple[AllowedClaim, ...] = Field(min_length=1)
    prohibited_claims: tuple[ProhibitedClaim, ...] = Field(min_length=1)
    required_disclaimers: tuple[NonEmptyText, ...]


class AudienceInput(StrictModel):
    target_consumer: NonEmptyText
    context: NonEmptyText
    pain_point: NonEmptyText
    desired_outcome: NonEmptyText


class PlatformInput(StrictModel):
    platform: NonEmptyText
    placement: NonEmptyText
    constraints: tuple[NonEmptyText, ...]


class EcommerceAdInput(StrictModel):
    schema_version: Literal["ecommerce-ad-workflow/input/1"]
    delivery_intent: Literal["video"]
    product: ProductInput
    product_truth: ProductTruthInput
    audience: AudienceInput
    platform: PlatformInput
    objective: Literal["AWARENESS", "CONSIDERATION", "CONVERSION"]
    duration_seconds: float = Field(ge=6.0, le=60.0)
    aspect_ratio: Literal["9:16"]
    language: NonEmptyText
    style: NonEmptyText
    ad_format: Literal[
        "product_demo",
        "presenter_spokesperson",
        "lifestyle_use_case",
        "comparison",
        "problem_solution",
        "motion_graphics_product",
    ]
    references: tuple[NonEmptyText, ...]
    constraints: tuple[NonEmptyText, ...]


class ProductTruthSnapshot(StrictModel):
    sku_id: Identifier
    product_name: NonEmptyText
    source_assets: tuple[ProductSourceAsset, ...] = Field(min_length=1)
    sources: tuple[TruthSource, ...] = Field(min_length=1)
    facts: tuple[ProductFact, ...] = Field(min_length=1)
    allowed_claims: tuple[AllowedClaim, ...] = Field(min_length=1)
    prohibited_claims: tuple[ProhibitedClaim, ...] = Field(min_length=1)
    required_disclaimers: tuple[NonEmptyText, ...]


class ClaimLedgerEntry(StrictModel):
    claim_id: Identifier
    status: Literal["USED", "NOT_USED", "PROHIBITED"]
    fact_ids: tuple[Identifier, ...]
    source_ids: tuple[Identifier, ...]
    used_at: tuple[Identifier, ...]
    spoken_form: NonEmptyText | None
    visual_form: NonEmptyText | None


class AdStrategy(StrictModel):
    strategy_id: Identifier
    audience: NonEmptyText
    pain_point: NonEmptyText
    angle: NonEmptyText
    promise: NonEmptyText
    proof_boundary: NonEmptyText
    objection_handling: NonEmptyText
    objective: Literal["AWARENESS", "CONSIDERATION", "CONVERSION"]


class HookComponent(StrictModel):
    component_id: Identifier
    kind: Literal["VISUAL", "DIALOGUE_OR_VO", "COPY", "AUDIO"]
    cue_seconds: float = Field(ge=0.0)
    content: NonEmptyText
    claim_ids: tuple[Identifier, ...]
    bound_ids: tuple[Identifier, ...] = Field(min_length=1)


class HookContract(StrictModel):
    components: tuple[HookComponent, ...] = Field(min_length=1)
    product_presence: Literal["NONE", "TEASE", "EXPLICIT"]
    promise_claim_ids: tuple[Identifier, ...] = Field(min_length=1)
    promise_boundary: NonEmptyText
    first_payoff_deadline_seconds: float = Field(gt=0.0)
    platform_constraints: tuple[NonEmptyText, ...]


class AdBeat(StrictModel):
    beat_id: Identifier
    role: Literal[
        "HOOK",
        "PROBLEM",
        "PRODUCT_INTRO",
        "DEMONSTRATION",
        "BENEFIT_PROOF",
        "HERO",
        "CTA_CLOSE",
    ]
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    duration_seconds: float = Field(gt=0.0)
    duration_basis: Literal[
        "HOOK_DENSITY",
        "DEMO_COMPLEXITY",
        "PROOF_READABILITY",
        "CTA_DWELL",
        "INTENTIONAL_EQUAL_RHYTHM",
    ]
    pacing_rationale: NonEmptyText
    message: NonEmptyText
    shot_ids: tuple[Identifier, ...] = Field(min_length=1)
    presentation_ids: tuple[Identifier, ...]
    copy_ids: tuple[Identifier, ...]
    audio_event_ids: tuple[Identifier, ...] = Field(min_length=1)


class ProductPresentation(StrictModel):
    presentation_id: Identifier
    role: Literal["INTRO", "DEMONSTRATION", "BENEFIT_PROOF", "HERO_SHOT", "CTA_SUPPORT"]
    mode: Literal[
        "IN_SCENE_GENERATED",
        "GRAPHIC_REVEAL",
        "DEDICATED_HERO_SHOT",
        "PHYSICAL_INTERACTION_REQUIRED",
    ]
    beat_id: Identifier
    shot_id: Identifier
    start_seconds: float = Field(ge=0.0)
    duration_seconds: float = Field(gt=0.0)
    product_source_asset_id: Identifier
    talent_interaction: Literal["NONE", "POINTS_NEAR", "PHYSICAL_CONTACT"]
    occlusion_required: bool
    lighting_shadow_required: bool
    copy_cue_ids: tuple[Identifier, ...]
    audio_cue_ids: tuple[Identifier, ...]
    fallback_policy: Literal[
        "NONE", "REQUIRE_REAPPROVAL_GRAPHIC", "REQUIRE_REAPPROVAL_HERO"
    ]
    capability_requirement_ids: tuple[Identifier, ...]


class TalentPlan(StrictModel):
    talent_id: Identifier
    role: NonEmptyText
    appearance: NonEmptyText
    wardrobe: NonEmptyText
    performance: NonEmptyText
    continuity_anchors: tuple[NonEmptyText, ...] = Field(min_length=1)


class SetPlan(StrictModel):
    set_id: Identifier
    location: NonEmptyText
    lighting: NonEmptyText
    brand_palette: tuple[NonEmptyText, ...] = Field(min_length=1)
    product_surface: NonEmptyText
    continuity_anchors: tuple[NonEmptyText, ...] = Field(min_length=1)


class CopyGraphic(StrictModel):
    copy_id: Identifier
    role: Literal[
        "DIALOGUE_SUBTITLE",
        "HEADLINE",
        "BENEFIT_CALLOUT",
        "PRODUCT_LABEL",
        "PROOF_LABEL",
        "CTA",
        "BRAND_END_CARD",
    ]
    text: NonEmptyText
    priority: int = Field(ge=1, le=10)
    beat_id: Identifier
    shot_id: Identifier
    safe_area_intent: NonEmptyText
    avoidance_intent: NonEmptyText
    entrance_intent: NonEmptyText
    exit_intent: NonEmptyText
    keyword_emphasis: tuple[NonEmptyText, ...]
    brand_token_reference: NonEmptyText
    synchronized_event_ids: tuple[Identifier, ...] = Field(min_length=1)
    treatment_id: Identifier


class AudioEvent(StrictModel):
    event_id: Identifier
    kind: Literal["DIALOGUE", "VOICE_OVER", "MUSIC", "SFX", "INTENTIONAL_SILENCE"]
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    beat_ids: tuple[Identifier, ...] = Field(min_length=1)
    shot_ids: tuple[Identifier, ...]
    source_requirement: NonEmptyText
    speaker_id: Identifier | None
    verbatim_line: NonEmptyText | None
    on_camera: bool
    lip_sync_required: bool
    energy: NonEmptyText
    ducking_required: bool
    synchronized_event_ids: tuple[Identifier, ...]
    silence_rationale: NonEmptyText | None


class SourceAudioPolicy(StrictModel):
    shot_id: Identifier
    source_type: Literal["NATIVE", "GENERATED", "NONE"]
    policy: Literal["KEEP", "MUTE", "REPLACE", "TRIM_THEN_MIX"]
    trim_start_seconds: float | None
    lead_in_noise_risk: bool
    p6_measurement_required: bool
    measurement_requirement: NonEmptyText | None


class AudioPlan(StrictModel):
    events: tuple[AudioEvent, ...] = Field(min_length=1)
    source_audio_policies: tuple[SourceAudioPolicy, ...] = Field(min_length=1)


class StoryboardGroup(StrictModel):
    group_id: Identifier
    beat_id: Identifier
    shot_ids: tuple[Identifier, ...] = Field(min_length=1)
    commercial_intent: NonEmptyText


class ShotIntent(StrictModel):
    shot_id: Identifier
    beat_id: Identifier
    purpose: NonEmptyText
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    duration_basis: Literal[
        "HOOK_DENSITY",
        "DEMO_COMPLEXITY",
        "PROOF_READABILITY",
        "CTA_DWELL",
        "INTENTIONAL_EQUAL_RHYTHM",
    ]
    product_state: NonEmptyText
    talent_action: NonEmptyText
    camera_intent: NonEmptyText
    presentation_ids: tuple[Identifier, ...]
    copy_ids: tuple[Identifier, ...]
    audio_event_ids: tuple[Identifier, ...] = Field(min_length=1)
    visual_strategy_need: NonEmptyText


class CTAPlan(StrictModel):
    spoken_text: NonEmptyText | None
    visual_text: NonEmptyText
    destination_action: NonEmptyText
    beat_id: Identifier
    shot_id: Identifier
    cta_copy_id: Identifier
    end_card_copy_id: Identifier


class CreativeVariant(StrictModel):
    variant_id: Identifier
    changed_variable: Literal[
        "HOOK",
        "OPENING_VISUAL",
        "ADVERTISING_ANGLE",
        "PROOF_ORDER",
        "CTA",
        "PRESENTER_PROFILE",
        "PACING",
        "DURATION_CUT",
    ]
    baseline_value: NonEmptyText
    variant_value: NonEmptyText
    held_constants: tuple[Literal[
        "claim_ledger",
        "cta_destination",
        "delivery_intent",
        "objective",
        "platform_constraints",
        "product_identity",
        "product_truth",
        "rights",
        "unchanged_strategy_fields",
    ], ...] = Field(min_length=9, max_length=9)
    hypothesis: NonEmptyText
    required_new_assets: tuple[NonEmptyText, ...]


class CreativeVariantMatrix(StrictModel):
    master_strategy_id: Identifier
    variants: tuple[CreativeVariant, ...] = Field(min_length=1)


class RuntimeProposal(StrictModel):
    proposal_id: Identifier
    target: Literal[
        "ProductionBrief",
        "Character",
        "Scene",
        "Storyboard",
        "Shot",
        "AudioTrackSpec",
        "CaptionTrack",
    ]
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    summary: NonEmptyText


class RuntimeRequirement(StrictModel):
    requirement_id: Identifier
    capability: Literal[
        "product_source_asset",
        "product_source_generation",
        "physical_product_interaction",
        "advertising_copy_graphics",
        "audio_authoring",
        "dialogue_caption_binding",
    ]
    classification: Literal[
        "SUPPORTED_CURRENTLY",
        "REQUIRES_SOURCE_GENERATION_STRATEGY",
        "REQUIRES_RUNTIME_CAPABILITY",
        "REQUIRES_HUMAN_DECISION",
        "BLOCKED_BY_TRUTH_OR_RIGHTS",
    ]
    rationale: NonEmptyText


class ClassifiedGap(StrictModel):
    gap_id: Identifier
    classification: Literal[
        "SUPPORTED_CURRENTLY",
        "REQUIRES_SOURCE_GENERATION_STRATEGY",
        "REQUIRES_RUNTIME_CAPABILITY",
        "REQUIRES_HUMAN_DECISION",
        "BLOCKED_BY_TRUTH_OR_RIGHTS",
    ]
    requirement_ids: tuple[Identifier, ...] = Field(min_length=1)
    blocker_code: NonEmptyText | None
    rationale: NonEmptyText


class RuntimeHandoff(StrictModel):
    delivery_intent: Literal["video"]
    proposals: tuple[RuntimeProposal, ...] = Field(min_length=1)
    requirements: tuple[RuntimeRequirement, ...] = Field(min_length=1)
    classified_gaps: tuple[ClassifiedGap, ...] = Field(min_length=1)


class AdQCFinding(StrictModel):
    code: Identifier
    status: Literal["PASS", "BLOCKER"]
    related_ids: tuple[Identifier, ...] = Field(min_length=1)
    message: NonEmptyText


class AdQCReport(StrictModel):
    ready: bool
    findings: tuple[AdQCFinding, ...] = Field(min_length=1)


class EcommerceAdProductionPackage(StrictModel):
    schema_version: Literal["ecommerce-ad-workflow/package/1"]
    package_id: str = Field(pattern=SHA256_PATTERN)
    source_input_hash: str = Field(pattern=SHA256_PATTERN)
    duration_seconds: float = Field(ge=6.0, le=60.0)
    aspect_ratio: Literal["9:16"]
    product_truth: ProductTruthSnapshot
    claim_ledger: tuple[ClaimLedgerEntry, ...] = Field(min_length=1)
    ad_strategy: AdStrategy
    hook_contract: HookContract
    ad_beats: tuple[AdBeat, ...] = Field(min_length=1)
    product_presentation: tuple[ProductPresentation, ...] = Field(min_length=1)
    talent_plan: tuple[TalentPlan, ...] = Field(min_length=1)
    set_plan: tuple[SetPlan, ...] = Field(min_length=1)
    copy_graphics_plan: tuple[CopyGraphic, ...] = Field(min_length=1)
    audio_plan: AudioPlan
    storyboard: tuple[StoryboardGroup, ...] = Field(min_length=1)
    shot_intents: tuple[ShotIntent, ...] = Field(min_length=1)
    cta: CTAPlan
    creative_variant_matrix: CreativeVariantMatrix
    runtime_handoff: RuntimeHandoff
    ad_qc_report: AdQCReport
    unresolved_items: tuple[NonEmptyText, ...]
