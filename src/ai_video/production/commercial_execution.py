from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import StrictModel
from ai_video.production.video import GeneratedCommercialShotBinding
from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
)
from ai_video.production.commercial_video_validation import commercial_source_hashes

if TYPE_CHECKING:
    from ai_video.production.ad_creative_types import AdCreativePlan


class CommercialShotClass(str, Enum):
    CHARACTER_PERFORMANCE = "character_performance"
    LIFESTYLE = "lifestyle"
    PRODUCT_INTERACTION = "product_interaction"
    PRODUCT_HERO = "product_hero"
    PROOF_GRAPHIC = "proof_graphic"
    END_CARD = "end_card"


class CommercialExecutionDisposition(str, Enum):
    EXISTING_CHARACTER_SCENE_PLANNING = "existing_character_scene_planning"
    APPROVED_COMMERCIAL_SOURCE_THEN_I2V = "approved_commercial_source_then_i2v"
    CONTROLLED_PRODUCT_COMPOSITION = "controlled_product_composition"
    COMPOSITOR_ONLY = "compositor_only"


class CommercialExecutionProjection(StrictModel):
    schema_version: Literal["commercial-execution-projection/1"] = "commercial-execution-projection/1"
    ad_creative_plan_id: str = Field(min_length=1)
    ad_creative_plan_revision: int = Field(strict=True, ge=1)
    ad_creative_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    primary_class: CommercialShotClass
    product_id: str | None = Field(default=None, min_length=1)
    product_reference_requirement_id: str | None = Field(default=None, min_length=1)
    source_requirement_id: str | None = Field(default=None, min_length=1)
    character_requirement_ids: tuple[str, ...]
    scene_requirement_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    wardrobe_requirement_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    accessory_requirement_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    recommended_disposition: CommercialExecutionDisposition
    requires_source_materialization: bool
    requires_source_review: bool
    invoke_video_provider: bool
    graphic_ids: tuple[str, ...]
    sound_cue_ids: tuple[str, ...]
    projection_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_projection(self) -> "CommercialExecutionProjection":
        if self.primary_class is CommercialShotClass.PRODUCT_INTERACTION:
            if not all(
                (
                    self.product_id,
                    self.product_reference_requirement_id,
                    self.source_requirement_id,
                )
            ):
                raise ValueError("Product interaction projection requires product and source identities")
            if not (
                self.requires_source_materialization
                and self.requires_source_review
                and self.invoke_video_provider
            ):
                raise ValueError("Product interaction projection requires approved source then I2V")
        if self.primary_class in {
            CommercialShotClass.PRODUCT_HERO,
            CommercialShotClass.PROOF_GRAPHIC,
            CommercialShotClass.END_CARD,
        } and self.invoke_video_provider:
            raise ValueError("Deterministic commercial lanes cannot invoke Video Provider")
        expected = canonical_sha256(self.model_dump(mode="json", exclude={"projection_hash"}))
        if self.projection_hash != expected:
            raise ValueError("Commercial execution projection hash does not match")
        return self


def _shot_class(plan: "AdCreativePlan", shot_id: str) -> tuple[
    CommercialShotClass,
    object | None,
]:
    from ai_video.production.ad_creative_types import (
        AdBeatRole,
        ProductPresentationMode,
        ProductPresentationRole,
    )
    from ai_video.production.commercial_graphics import GraphicRole

    presentations = tuple(
        item for item in plan.product_presentations if item.shot_id == shot_id
    )
    interaction = tuple(
        item for item in presentations
        if item.mode is ProductPresentationMode.IN_SCENE_PROVIDER
    )
    hero = tuple(
        item for item in presentations
        if item.role is ProductPresentationRole.HERO_SHOT
        or item.mode is ProductPresentationMode.HERO_ASSET
    )
    graphics = tuple(item for item in plan.graphic_treatments if item.shot_id == shot_id)
    proof = tuple(item for item in graphics if item.role is GraphicRole.PROOF_LABEL)
    end = tuple(
        item for item in graphics
        if item.role in {GraphicRole.CTA, GraphicRole.BRAND_END_CARD}
    )
    primary_signals = tuple(
        item
        for item in (
            (CommercialShotClass.PRODUCT_INTERACTION, interaction[0]) if interaction else None,
            (CommercialShotClass.PRODUCT_HERO, hero[0]) if hero else None,
            (CommercialShotClass.PROOF_GRAPHIC, None) if proof else None,
            (CommercialShotClass.END_CARD, None) if end else None,
        )
        if item is not None
    )
    if len(primary_signals) > 1:
        # End-card graphics may accompany the dedicated hero Shot, but a proof or
        # physical interaction lane cannot be guessed by enum precedence.
        classes = {item[0] for item in primary_signals}
        if classes == {CommercialShotClass.PRODUCT_HERO, CommercialShotClass.END_CARD}:
            return CommercialShotClass.PRODUCT_HERO, hero[0]
        raise ValueError(f"Shot {shot_id} has contradictory commercial primary responsibilities")
    if primary_signals:
        return primary_signals[0]
    beat_roles = {
        beat.role for beat in plan.ad_arc if shot_id in beat.shot_ids
    }
    if beat_roles & {AdBeatRole.PAYOFF, AdBeatRole.PRODUCT_INTRODUCTION}:
        return CommercialShotClass.LIFESTYLE, None
    return CommercialShotClass.CHARACTER_PERFORMANCE, None


def project_commercial_executions(
    plan: "AdCreativePlan",
) -> tuple[CommercialExecutionProjection, ...]:
    from ai_video.production.ad_creative_types import AdCreativePlan

    checked = AdCreativePlan.model_validate(plan.model_dump(mode="python"))
    if checked.schema_version != "ad-creative-plan/2" or not verify_artifact_hash(checked):
        raise ValueError("Commercial execution projection requires a sealed current AdCreativePlan")
    shot_ids = tuple(
        dict.fromkeys(shot_id for beat in checked.ad_arc for shot_id in beat.shot_ids)
    )
    projections: list[CommercialExecutionProjection] = []
    for shot_id in shot_ids:
        primary_class, presentation = _shot_class(checked, shot_id)
        interaction = primary_class is CommercialShotClass.PRODUCT_INTERACTION
        if interaction:
            disposition = CommercialExecutionDisposition.APPROVED_COMMERCIAL_SOURCE_THEN_I2V
        elif primary_class is CommercialShotClass.PRODUCT_HERO:
            disposition = CommercialExecutionDisposition.CONTROLLED_PRODUCT_COMPOSITION
        elif primary_class in {CommercialShotClass.PROOF_GRAPHIC, CommercialShotClass.END_CARD}:
            disposition = CommercialExecutionDisposition.COMPOSITOR_ONLY
        else:
            disposition = CommercialExecutionDisposition.EXISTING_CHARACTER_SCENE_PLANNING
        product_id = getattr(presentation, "product_id", None)
        product_requirement_id = getattr(
            presentation, "product_reference_requirement_id", None
        )
        source_requirement_id = getattr(presentation, "source_requirement_id", None)
        base = {
            "schema_version": "commercial-execution-projection/1",
            "ad_creative_plan_id": checked.artifact_id,
            "ad_creative_plan_revision": checked.revision,
            "ad_creative_plan_hash": checked.content_hash,
            "target_shot_id": shot_id,
            "primary_class": primary_class,
            "product_id": product_id,
            "product_reference_requirement_id": product_requirement_id,
            "source_requirement_id": source_requirement_id,
            "character_requirement_ids": checked.protagonist_continuity_policy.protagonist_ids,
            "scene_requirement_fingerprint": canonical_sha256({"shot_id": shot_id, "dimension": "scene"}),
            "wardrobe_requirement_fingerprint": canonical_sha256(
                {
                    "shot_id": shot_id,
                    "dimension": "wardrobe",
                    "allowed_variations": checked.protagonist_continuity_policy.allowed_variations,
                }
            ),
            "accessory_requirement_fingerprint": canonical_sha256({"shot_id": shot_id, "dimension": "accessory"}),
            "recommended_disposition": disposition,
            "requires_source_materialization": interaction,
            "requires_source_review": interaction,
            "invoke_video_provider": interaction or primary_class in {
                CommercialShotClass.CHARACTER_PERFORMANCE,
                CommercialShotClass.LIFESTYLE,
            },
            "graphic_ids": tuple(item.graphic_id for item in checked.graphic_treatments if item.shot_id == shot_id),
            "sound_cue_ids": tuple(
                cue.cue_id
                for cue in checked.sound_cues
                if cue.synchronized_event_id is None
                or cue.synchronized_event_id in {
                    shot_id,
                    *(beat.beat_id for beat in checked.ad_arc if shot_id in beat.shot_ids),
                }
            ),
        }
        base["projection_hash"] = canonical_sha256(base)
        projections.append(CommercialExecutionProjection.model_validate(base))
    return tuple(projections)


def project_generated_commercial_shot_binding(
    projection: CommercialExecutionProjection,
    *,
    profile,
    applicable_requirement_ids: tuple[str, ...],
    approved_source: ApprovedCommercialSourceBinding | None,
    expected_actor_ids: tuple[str, ...],
    output_asset_id: str,
) -> GeneratedCommercialShotBinding:
    """Project exact authoring/profile identities into one video request binding."""

    from ai_video.production.ecommerce_media_acceptance import (
        EcommerceAcceptanceProfile,
    )

    selected_projection = CommercialExecutionProjection.model_validate(
        projection.model_dump(mode="json")
    )
    selected_profile = EcommerceAcceptanceProfile.model_validate(
        profile.model_dump(mode="json")
    )
    selected = set(applicable_requirement_ids)
    canonical_requirements = tuple(
        requirement_id
        for requirement_id in selected_profile.shot_requirement_ids
        if requirement_id in selected
    )
    if canonical_requirements != applicable_requirement_ids:
        raise ValueError(
            "Commercial Shot requirements must be exact and ordered by selected profile"
        )
    if not set(selected_projection.character_requirement_ids).issubset(
        expected_actor_ids
    ):
        raise ValueError("Commercial binding omits an expected authoring actor")
    checked_approval = (
        ApprovedCommercialSourceBinding.model_validate(
            approved_source.model_dump(mode="python")
        )
        if approved_source is not None
        else None
    )
    if selected_projection.requires_source_review and checked_approval is None:
        raise ValueError("Commercial interaction binding requires approved source")
    product_truth_hashes, product_reference_hashes, source_approval_hashes = (
        commercial_source_hashes(checked_approval)
        if checked_approval is not None
        else ((), (), ())
    )
    if checked_approval is not None and (
        checked_approval.ad_creative_plan_hash
        != selected_projection.ad_creative_plan_hash
        or checked_approval.execution_projection_hash
        != selected_projection.projection_hash
        or checked_approval.target_shot_id != selected_projection.target_shot_id
    ):
        raise ValueError("Approved source does not match commercial projection")
    return GeneratedCommercialShotBinding.create(
        ad_creative_plan_id=selected_projection.ad_creative_plan_id,
        ad_creative_plan_hash=selected_projection.ad_creative_plan_hash,
        commercial_execution_projection_hash=selected_projection.projection_hash,
        target_shot_id=selected_projection.target_shot_id,
        profile_content_hash=selected_profile.content_hash,
        applicable_requirement_ids=applicable_requirement_ids,
        product_truth_hashes=product_truth_hashes,
        product_reference_hashes=product_reference_hashes,
        source_approval_hashes=source_approval_hashes,
        expected_actor_ids=expected_actor_ids,
        output_asset_id=output_asset_id,
    )
