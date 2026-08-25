from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai_video.production.ad_creative_types import (
    AdCreativePlan,
    AdSoundRole,
    ProductPresentationMode,
)
from ai_video.production.commercial_graphics import GraphicRole
from ai_video.production.commercial_graphics import (
    AdvertisingSoundCueProjection,
    GraphicLayerAnimation,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import CompositionSpec
from ai_video.production.commercial_execution import project_commercial_executions
from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class AdCreativeReviewDimension(str, Enum):
    PRODUCT_INTEGRATION = "product_integration"
    COMMERCIAL_TYPOGRAPHY = "commercial_typography"
    AD_ARC = "ad_arc"
    SOUND_SYNCHRONIZATION = "sound_synchronization"
    BRAND_CLOSURE = "brand_closure"


class AdCreativeReviewFinding(_StrictModel):
    code: str = Field(min_length=1)
    dimension: AdCreativeReviewDimension
    message: str = Field(min_length=1)


class AdCreativeReviewReport(_StrictModel):
    plan_id: str = Field(min_length=1)
    composition_id: str = Field(min_length=1)
    checked_dimensions: tuple[AdCreativeReviewDimension, ...] = Field(min_length=1)
    findings: tuple[AdCreativeReviewFinding, ...]
    is_ready: bool
    requires_source_preparation: bool = False
    source_preparation_ready: bool = True
    production_verdict: Literal[None] = None


_DIMENSIONS = tuple(AdCreativeReviewDimension)


def _diagnostic_artifact_id(value: object, *, fallback: str) -> str:
    artifact_id = getattr(value, "artifact_id", None)
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return fallback


def _commercial_approval_cardinality_is_unique(
    approvals: tuple[ApprovedCommercialSourceBinding, ...],
) -> bool:
    return all(
        len(values) == len(set(values))
        for values in (
            tuple(item.approval_id for item in approvals),
            tuple(item.content_hash for item in approvals),
            tuple(item.execution_projection_hash for item in approvals),
            tuple(item.target_shot_id for item in approvals),
        )
    )


def review_ad_creative_plan(
    plan: AdCreativePlan,
    composition: CompositionSpec,
    *,
    approved_commercial_sources: tuple[ApprovedCommercialSourceBinding, ...] = (),
) -> AdCreativeReviewReport:
    findings: list[AdCreativeReviewFinding] = []

    def add(
        code: str,
        dimension: AdCreativeReviewDimension,
        message: str,
    ) -> None:
        findings.append(
            AdCreativeReviewFinding(
                code=code,
                dimension=dimension,
                message=message,
            )
        )

    schema_invalid = False
    try:
        AdCreativePlan.model_validate(plan.model_dump(mode="python", warnings=False))
    except ValidationError:
        schema_invalid = True
        add(
            "ad_plan_schema_invalid",
            AdCreativeReviewDimension.AD_ARC,
            "AdCreativePlan fails public-boundary schema validation.",
        )
    try:
        CompositionSpec.model_validate(
            composition.model_dump(mode="python", warnings=False)
        )
    except ValidationError:
        schema_invalid = True
        add(
            "composition_schema_invalid",
            AdCreativeReviewDimension.PRODUCT_INTEGRATION,
            "CompositionSpec fails public-boundary schema validation.",
        )

    if schema_invalid:
        return AdCreativeReviewReport(
            plan_id=_diagnostic_artifact_id(
                plan,
                fallback="invalid-ad-creative-plan",
            ),
            composition_id=_diagnostic_artifact_id(
                composition,
                fallback="invalid-composition-spec",
            ),
            checked_dimensions=_DIMENSIONS,
            findings=tuple(findings),
            is_ready=False,
            production_verdict=None,
        )

    if not verify_artifact_hash(plan):
        add(
            "ad_plan_hash_invalid",
            AdCreativeReviewDimension.AD_ARC,
            "AdCreativePlan content hash is invalid.",
        )
    if not verify_artifact_hash(composition):
        add(
            "composition_hash_invalid",
            AdCreativeReviewDimension.PRODUCT_INTEGRATION,
            "CompositionSpec content hash is invalid.",
        )

    if (
        composition.ad_creative_plan_id != plan.artifact_id
        or composition.ad_creative_plan_hash != plan.content_hash
        or not any(
            item.kind == "derived"
            and item.reference == plan.artifact_id
            and item.content_hash == plan.content_hash
            for item in composition.source_provenance
        )
    ):
        add(
            "ad_plan_binding_mismatch",
            AdCreativeReviewDimension.AD_ARC,
            "CompositionSpec does not bind the exact AdCreativePlan identity.",
        )

    graphic_layers = set(composition.graphic_layer_ids)
    expected_shot_ids = tuple(
        dict.fromkeys(
            shot_id for beat in plan.ad_arc for shot_id in beat.shot_ids
        )
    )
    if composition.shot_ids != expected_shot_ids:
        add(
            "ad_arc_shot_projection_mismatch",
            AdCreativeReviewDimension.AD_ARC,
            "Composition Shot order/coverage does not match the advertising arc.",
        )
    expected_graphic_layer_ids = tuple(
        item.composition_layer_id
        for item in plan.product_presentations
        if item.mode is not ProductPresentationMode.IN_SCENE_PROVIDER
        and item.composition_layer_id is not None
    )
    if composition.graphic_layer_ids != expected_graphic_layer_ids:
        add(
            "product_graphic_layer_projection_mismatch",
            AdCreativeReviewDimension.PRODUCT_INTEGRATION,
            "Product graphic layers do not exactly match AdCreativePlan.",
        )
    missing_product_layer = any(
        item.mode is not ProductPresentationMode.IN_SCENE_PROVIDER
        and item.composition_layer_id not in graphic_layers
        for item in plan.product_presentations
    )
    if missing_product_layer:
        add(
            "product_graphic_layer_missing",
            AdCreativeReviewDimension.PRODUCT_INTEGRATION,
            "A product graphic presentation is missing its canonical graphic layer.",
        )
    composition_layers = {item.layer_id: item for item in composition.layers}
    product_projection_mismatch = False
    for item in plan.product_presentations:
        if item.mode is ProductPresentationMode.IN_SCENE_PROVIDER:
            if plan.schema_version == "ad-creative-plan/1" and not any(
                layer.shot_id == item.shot_id and layer.asset_id == item.asset_id
                for layer in composition.layers
            ):
                product_projection_mismatch = True
            continue
        layer = composition_layers.get(item.composition_layer_id or "")
        if (
            layer is None
            or layer.shot_id != item.shot_id
            or layer.asset_id != item.asset_id
            or layer.transform != item.transform_intent.transform
            or layer.opacity_milli != item.transform_intent.opacity_milli
        ):
            product_projection_mismatch = True
    if product_projection_mismatch:
        add(
            "product_presentation_projection_mismatch",
            AdCreativeReviewDimension.PRODUCT_INTEGRATION,
            "Product presentation semantics do not match CompositionSpec.",
        )
    expected_animations = tuple(
        GraphicLayerAnimation(
            layer_id=item.composition_layer_id,
            entrance=item.entrance,
            exit=item.exit,
        )
        for item in plan.product_presentations
        if item.mode is not ProductPresentationMode.IN_SCENE_PROVIDER
        and item.composition_layer_id is not None
    )
    if composition.graphic_layer_animations != expected_animations:
        add(
            "product_graphic_animation_mismatch",
            AdCreativeReviewDimension.PRODUCT_INTEGRATION,
            "Product graphic animation projection does not match AdCreativePlan.",
        )

    expected_graphics = tuple(
        item.graphic_id
        for item in plan.graphic_treatments
        if item.role is not GraphicRole.DIALOGUE_SUBTITLE
    )
    actual_graphics = tuple(item.graphic_id for item in composition.commercial_graphics)
    expected_graphic_models = tuple(
        item
        for item in plan.graphic_treatments
        if item.role is not GraphicRole.DIALOGUE_SUBTITLE
    )
    if (
        actual_graphics != expected_graphics
        or composition.commercial_graphics != expected_graphic_models
    ):
        add(
            "commercial_graphic_projection_mismatch",
            AdCreativeReviewDimension.COMMERCIAL_TYPOGRAPHY,
            "Commercial graphic projection does not match AdCreativePlan.",
        )

    audio_tracks = {item.track_id for item in composition.audio_tracks}
    if any(
        item.role is not AdSoundRole.INTENTIONAL_SILENCE
        and item.audio_track_id not in audio_tracks
        for item in plan.sound_cues
    ):
        add(
            "sound_cue_projection_incomplete",
            AdCreativeReviewDimension.SOUND_SYNCHRONIZATION,
            "Advertising sound cue is missing its canonical audio track.",
        )
    expected_sound_cues = tuple(
        AdvertisingSoundCueProjection(
            cue_id=item.cue_id,
            role=item.role,
            audio_track_id=item.audio_track_id,
            synchronized_event_id=item.synchronized_event_id,
        )
        for item in plan.sound_cues
    )
    if composition.advertising_sound_cues != expected_sound_cues:
        add(
            "sound_cue_semantic_projection_mismatch",
            AdCreativeReviewDimension.SOUND_SYNCHRONIZATION,
            "Advertising sound cue semantics do not match AdCreativePlan.",
        )

    requires_source_preparation = bool(
        plan.schema_version == "ad-creative-plan/2"
        and any(
            item.mode is ProductPresentationMode.IN_SCENE_PROVIDER
            for item in plan.product_presentations
        )
    )
    source_preparation_ready = not requires_source_preparation
    if requires_source_preparation:
        interactions = {
            item.projection_hash: item
            for item in project_commercial_executions(plan)
            if item.primary_class.value == "product_interaction"
        }
        approval_items = tuple(approved_commercial_sources)
        approvals = {
            item.execution_projection_hash: item
            for item in approval_items
        }
        source_preparation_ready = bool(
            _commercial_approval_cardinality_is_unique(approval_items)
            and set(interactions) == set(approvals)
            and all(
                approval.ad_creative_plan_hash == plan.content_hash
                and approval.target_shot_id
                == interactions[projection_hash].target_shot_id
                for projection_hash, approval in approvals.items()
            )
        )
    return AdCreativeReviewReport(
        plan_id=plan.artifact_id,
        composition_id=composition.artifact_id,
        checked_dimensions=_DIMENSIONS,
        findings=tuple(findings),
        is_ready=not findings,
        requires_source_preparation=requires_source_preparation,
        source_preparation_ready=source_preparation_ready,
        production_verdict=None,
    )
