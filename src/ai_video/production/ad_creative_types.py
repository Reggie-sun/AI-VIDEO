from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_video.production.commercial_graphics import (
    AdSoundRole,
    GraphicAnimation,
    GraphicRole,
    GraphicTreatment,
)
from ai_video.production.models import CompositionSpec, FixedTransform, SourceReference


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ProtagonistContinuityMode(str, Enum):
    SINGLE_PROTAGONIST = "single_protagonist"
    DECLARED_MONTAGE = "declared_montage"


class AdBeatRole(str, Enum):
    PROBLEM = "problem"
    PRODUCT_INTRODUCTION = "product_introduction"
    DEMONSTRATION = "demonstration"
    PROOF = "proof"
    PAYOFF = "payoff"
    HERO = "hero"
    CTA = "cta"
    BRAND_CLOSURE = "brand_closure"


class ProductPresentationRole(str, Enum):
    INTRO = "intro"
    DEMONSTRATION = "demonstration"
    BENEFIT_PROOF = "benefit_proof"
    HERO_SHOT = "hero_shot"
    CTA_SUPPORT = "cta_support"


class ProductPresentationMode(str, Enum):
    IN_SCENE_PROVIDER = "in_scene_provider"
    GRAPHIC_REVEAL = "graphic_reveal"
    HERO_ASSET = "hero_asset"


class CapabilityClassification(str, Enum):
    SUPPORTED_CURRENTLY = "supported_currently"
    REQUIRES_SOURCE_GENERATION_STRATEGY = "requires_source_generation_strategy"
    REQUIRES_RUNTIME_CAPABILITY = "requires_runtime_capability"
    REQUIRES_HUMAN_DECISION = "requires_human_decision"
    BLOCKED_BY_TRUTH_OR_RIGHTS = "blocked_by_truth_or_rights"


class ProtagonistContinuityPolicy(_StrictModel):
    mode: ProtagonistContinuityMode
    protagonist_ids: tuple[str, ...] = Field(min_length=1)
    allowed_variations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _require_unique_identities(self) -> "ProtagonistContinuityPolicy":
        if len(self.protagonist_ids) != len(set(self.protagonist_ids)):
            raise ValueError("protagonist IDs must be unique")
        if (
            self.mode is ProtagonistContinuityMode.SINGLE_PROTAGONIST
            and len(self.protagonist_ids) != 1
        ):
            raise ValueError("single protagonist policy requires exactly one identity")
        return self


class AdBeatPlan(_StrictModel):
    beat_id: str = Field(min_length=1)
    role: AdBeatRole
    shot_ids: tuple[str, ...] = Field(min_length=1)


class SourceGenerationEvidencePointer(_StrictModel):
    evidence_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    shot_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)


class ProductTransformIntent(_StrictModel):
    transform: FixedTransform = Field(default_factory=FixedTransform)
    opacity_milli: int = Field(default=1000, strict=True, ge=0, le=1000)


class ProductPresentation(_StrictModel):
    presentation_id: str = Field(min_length=1)
    role: ProductPresentationRole
    mode: ProductPresentationMode
    beat_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    composition_layer_id: str | None = None
    source_evidence_id: str | None = None
    product_truth_reference_ids: tuple[str, ...] = Field(min_length=1)
    transform_intent: ProductTransformIntent = Field(default_factory=ProductTransformIntent)
    entrance: GraphicAnimation = GraphicAnimation.NONE
    exit: GraphicAnimation = GraphicAnimation.NONE
    tracking_required: bool = False
    occlusion_required: bool = False
    lighting_match_required: bool = False
    graphic_treatment_ids: tuple[str, ...] = Field(min_length=1)
    sound_cue_ids: tuple[str, ...] = Field(min_length=1)
    capability_classification: CapabilityClassification
    requires_physical_interaction: bool = False

    @model_validator(mode="after")
    def _validate_mode_contract(self) -> "ProductPresentation":
        if self.mode is ProductPresentationMode.IN_SCENE_PROVIDER:
            if self.source_evidence_id is None:
                raise ValueError("in-scene product requires source evidence")
            if self.composition_layer_id is not None:
                raise ValueError("in-scene product cannot declare an overlay layer")
            if self.capability_classification is not (
                CapabilityClassification.REQUIRES_SOURCE_GENERATION_STRATEGY
            ):
                raise ValueError("in-scene product requires source-generation classification")
        elif self.composition_layer_id is None:
            raise ValueError("graphic and hero product presentations require asset and layer")
        elif self.source_evidence_id is not None:
            raise ValueError("graphic product presentation cannot use source evidence")
        complex_runtime_need = (
            self.tracking_required
            or self.occlusion_required
            or self.lighting_match_required
            or self.requires_physical_interaction
        )
        if (
            complex_runtime_need
            and self.mode is not ProductPresentationMode.IN_SCENE_PROVIDER
            and self.capability_classification is not (
                CapabilityClassification.REQUIRES_RUNTIME_CAPABILITY
            )
        ):
            raise ValueError("physical integration must remain a runtime capability gap")
        return self


class AdSoundCue(_StrictModel):
    cue_id: str = Field(min_length=1)
    role: AdSoundRole
    audio_track_id: str | None = None
    synchronized_event_id: str | None = None

    @model_validator(mode="after")
    def _validate_audio_binding(self) -> "AdSoundCue":
        if self.role is AdSoundRole.INTENTIONAL_SILENCE:
            if self.audio_track_id is not None:
                raise ValueError("intentional silence cannot bind an audio track")
        elif self.audio_track_id is None:
            raise ValueError("audible advertising cue requires an audio track")
        return self


class AdCreativePlanProposal(_StrictModel):
    creative_concept: str = Field(min_length=1)
    product_truth_source_ids: tuple[str, ...] = Field(min_length=1)
    claim_reference_ids: tuple[str, ...] = Field(min_length=1)
    source_generation_evidence: tuple[SourceGenerationEvidencePointer, ...] = ()
    protagonist_continuity_policy: ProtagonistContinuityPolicy
    ad_arc: tuple[AdBeatPlan, ...] = Field(min_length=1)
    product_presentations: tuple[ProductPresentation, ...] = Field(min_length=1)
    graphic_treatments: tuple[GraphicTreatment, ...] = Field(min_length=1)
    sound_cues: tuple[AdSoundCue, ...] = Field(min_length=1)
    visual_motif: str = Field(min_length=1)
    hero_shot_presentation_id: str = Field(min_length=1)
    end_card_graphic_ids: tuple[str, ...] = Field(min_length=1)
    cta_graphic_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_whole_ad_bindings(self) -> "AdCreativePlanProposal":
        collections = (
            ("beat", tuple(item.beat_id for item in self.ad_arc)),
            (
                "product presentation",
                tuple(item.presentation_id for item in self.product_presentations),
            ),
            ("graphic", tuple(item.graphic_id for item in self.graphic_treatments)),
            ("sound cue", tuple(item.cue_id for item in self.sound_cues)),
        )
        for label, identities in collections:
            if len(identities) != len(set(identities)):
                raise ValueError(f"{label} IDs must be unique")
        evidence_ids = tuple(item.evidence_id for item in self.source_generation_evidence)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("source generation evidence IDs must be unique")
        beats = {item.beat_id: item for item in self.ad_arc}
        presentations = {item.presentation_id: item for item in self.product_presentations}
        hero = presentations.get(self.hero_shot_presentation_id)
        if hero is None or hero.role is not ProductPresentationRole.HERO_SHOT:
            raise ValueError("hero shot must reference a HERO_SHOT presentation")
        graphics = {item.graphic_id: item for item in self.graphic_treatments}
        if any(
            graphics.get(item) is None
            or graphics[item].role is not GraphicRole.BRAND_END_CARD
            for item in self.end_card_graphic_ids
        ):
            raise ValueError("end card IDs must reference BRAND_END_CARD graphics")
        cta = graphics.get(self.cta_graphic_id)
        if cta is None or cta.role is not GraphicRole.CTA:
            raise ValueError("CTA must reference a CTA graphic")
        if AdBeatRole.BRAND_CLOSURE not in {item.role for item in self.ad_arc}:
            raise ValueError("ad arc requires brand closure")
        truth_ids = set(self.product_truth_source_ids)
        if any(
            not set(item.product_truth_reference_ids).issubset(truth_ids)
            for item in self.product_presentations
        ):
            raise ValueError("product presentation truth references are not declared")
        claim_ids = set(self.claim_reference_ids)
        if any(
            not set(item.claim_reference_ids).issubset(claim_ids)
            for item in self.graphic_treatments
        ):
            raise ValueError("graphic claim references are not declared")
        graphic_ids = set(graphics)
        sound_ids = {item.cue_id for item in self.sound_cues}
        evidence_by_id = {
            item.evidence_id: item for item in self.source_generation_evidence
        }
        for presentation in self.product_presentations:
            beat = beats.get(presentation.beat_id)
            if beat is None or presentation.shot_id not in beat.shot_ids:
                raise ValueError("product presentation beat/Shot binding is invalid")
            if not set(presentation.graphic_treatment_ids).issubset(graphic_ids):
                raise ValueError("product presentation graphic bindings are invalid")
            if not set(presentation.sound_cue_ids).issubset(sound_ids):
                raise ValueError("product presentation sound bindings are invalid")
            if presentation.mode is ProductPresentationMode.IN_SCENE_PROVIDER:
                evidence = evidence_by_id.get(presentation.source_evidence_id or "")
                if (
                    evidence is None
                    or evidence.shot_id != presentation.shot_id
                    or evidence.asset_id != presentation.asset_id
                ):
                    raise ValueError("in-scene product source evidence is not registered")
        event_ids = set(beats) | set(presentations) | graphic_ids
        for graphic in self.graphic_treatments:
            if (
                graphic.synchronized_event_id is not None
                and graphic.synchronized_event_id not in event_ids
            ):
                raise ValueError("graphic synchronization event is not declared")
            if not set(graphic.sound_cue_ids).issubset(sound_ids):
                raise ValueError("graphic sound cue bindings are not declared")
            if graphic.role is not GraphicRole.DIALOGUE_SUBTITLE and not graphic.brand_token_ids:
                raise ValueError("commercial graphic requires a brand token binding")
        for cue in self.sound_cues:
            if cue.synchronized_event_id is not None and cue.synchronized_event_id not in event_ids:
                raise ValueError("sound cue synchronization event is not declared")
        return self


class AdCreativePlan(AdCreativePlanProposal):
    schema_version: Literal["ad-creative-plan/1"] = "ad-creative-plan/1"
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str = Field(min_length=1)
    source_provenance: tuple[SourceReference, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_source_evidence_provenance(self) -> "AdCreativePlan":
        evidence_provenance = {
            (item.reference, item.content_hash)
            for item in self.source_provenance
            if item.kind in {"imported", "derived"}
        }
        if any(
            (item.artifact_id, item.content_hash) not in evidence_provenance
            for item in self.source_generation_evidence
        ):
            raise ValueError("source generation evidence must bind exact provenance")
        return self


class AdShotProposal(_StrictModel):
    shot_id: str = Field(min_length=1)
    beat_ids: tuple[str, ...] = Field(min_length=1)
    product_presentation_ids: tuple[str, ...] = ()
    graphic_ids: tuple[str, ...] = ()
    sound_cue_ids: tuple[str, ...] = ()


class AdCompositionRequirements(_StrictModel):
    graphic_layer_ids: tuple[str, ...] = ()
    commercial_graphic_ids: tuple[str, ...] = ()
    audio_track_ids: tuple[str, ...] = ()


class CompiledAdCreativeHandoff(_StrictModel):
    plan_id: str = Field(min_length=1)
    plan_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    shot_proposals: tuple[AdShotProposal, ...] = Field(min_length=1)
    composition_requirements: AdCompositionRequirements
    composition_spec: CompositionSpec
