from __future__ import annotations

from typing import Literal

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ad_creative_types import (
    AdCompositionRequirements,
    AdCreativePlan,
    AdCreativePlanProposal,
    AdShotProposal,
    AdSoundRole,
    CapabilityClassification,
    CompiledAdCreativeHandoff,
    ProductPresentationMode,
)
from ai_video.production.commercial_graphics import (
    AdvertisingSoundCueProjection,
    GraphicLayerAnimation,
    GraphicRole,
)
from ai_video.production.commercial_execution import project_commercial_executions
from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
)
from ai_video.production.hashing import seal_artifact, verify_artifact_hash
from ai_video.production.models import CompositionSpec, SourceReference


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        ErrorCode.COMPOSITION_INVALID,
        message,
        retryable=False,
    )


def _preflight_blocked(message: str) -> AiVideoError:
    return AiVideoError(
        ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
        message,
        retryable=False,
    )


def create_ad_creative_plan(
    proposal: AdCreativePlanProposal,
    *,
    artifact_id: str,
    revision: int,
    creation_receipt_id: str,
    source_provenance: tuple[SourceReference, ...],
    schema_version: Literal["ad-creative-plan/1", "ad-creative-plan/2"] = "ad-creative-plan/2",
) -> AdCreativePlan:
    try:
        proposal = AdCreativePlanProposal.model_validate(
            proposal.model_dump(mode="python")
        )
        provisional = AdCreativePlan(
            **proposal.model_dump(mode="python"),
            schema_version=schema_version,
            artifact_id=artifact_id,
            revision=revision,
            content_hash="0" * 64,
            creation_receipt_id=creation_receipt_id,
            source_provenance=source_provenance,
        )
        return AdCreativePlan.model_validate(
            seal_artifact(provisional).model_dump(mode="python")
        )
    except ValidationError as exc:
        raise _invalid(f"Accepted ad authoring proposal is invalid: {exc}") from exc


def compile_ad_creative_plan(
    plan: AdCreativePlan,
    base_composition: CompositionSpec,
) -> CompositionSpec:
    try:
        plan = AdCreativePlan.model_validate(plan.model_dump(mode="python"))
        base_composition = CompositionSpec.model_validate(
            base_composition.model_dump(mode="python")
        )
    except ValidationError as exc:
        raise _invalid(f"AdCreativePlan or base CompositionSpec is invalid: {exc}") from exc
    if not verify_artifact_hash(plan):
        raise _invalid("AdCreativePlan content hash is invalid.")
    if not verify_artifact_hash(base_composition):
        raise _invalid("Base CompositionSpec content hash is invalid.")

    shot_ids = set(base_composition.shot_ids)
    for beat in plan.ad_arc:
        if not set(beat.shot_ids).issubset(shot_ids):
            raise _invalid("Ad beat references an unordered Shot.")
    projected_shot_order = tuple(
        dict.fromkeys(shot_id for beat in plan.ad_arc for shot_id in beat.shot_ids)
    )
    if projected_shot_order != base_composition.shot_ids:
        raise _invalid("Ad beat Shot order must match CompositionSpec Shot order.")
    layer_by_id = {item.layer_id: item for item in base_composition.layers}
    graphic_layer_ids: list[str] = []
    graphic_layer_animations: list[GraphicLayerAnimation] = []
    for presentation in plan.product_presentations:
        if presentation.shot_id not in shot_ids:
            raise _invalid("Product presentation references an unordered Shot.")
        if (
            presentation.mode is not ProductPresentationMode.IN_SCENE_PROVIDER
            and (
                presentation.requires_physical_interaction
                or presentation.tracking_required
                or presentation.occlusion_required
                or presentation.lighting_match_required
            )
        ):
            raise _invalid(
                "Physical interaction remains unsupported by the canonical composition path."
            )
        if presentation.mode is ProductPresentationMode.IN_SCENE_PROVIDER:
            if presentation.capability_classification is not (
                CapabilityClassification.REQUIRES_SOURCE_GENERATION_STRATEGY
            ):
                raise _invalid("In-scene product source strategy is unresolved.")
            if plan.schema_version == "ad-creative-plan/1":
                if not any(
                    layer.shot_id == presentation.shot_id
                    and layer.asset_id == presentation.asset_id
                    for layer in base_composition.layers
                ):
                    raise _invalid(
                        "In-scene product source evidence does not match a Shot source asset."
                    )
            continue
        if presentation.capability_classification is not (
            CapabilityClassification.SUPPORTED_CURRENTLY
        ):
            raise _invalid("Product presentation has an unresolved capability gap.")
        assert presentation.composition_layer_id is not None
        layer = layer_by_id.get(presentation.composition_layer_id)
        if (
            layer is None
            or layer.shot_id != presentation.shot_id
            or layer.asset_id != presentation.asset_id
        ):
            raise _invalid("Product presentation does not match its composition layer.")
        if (
            layer.transform != presentation.transform_intent.transform
            or layer.opacity_milli != presentation.transform_intent.opacity_milli
        ):
            raise _invalid("Product presentation transform does not match its composition layer.")
        graphic_layer_ids.append(layer.layer_id)
        graphic_layer_animations.append(
            GraphicLayerAnimation(
                layer_id=layer.layer_id,
                entrance=presentation.entrance,
                exit=presentation.exit,
            )
        )

    caption_ids = {item.binding_id for item in base_composition.caption_tracks}
    commercial_graphics = []
    event_ids = {item.beat_id for item in plan.ad_arc}
    event_ids.update(item.presentation_id for item in plan.product_presentations)
    event_ids.update(item.graphic_id for item in plan.graphic_treatments)
    for graphic in plan.graphic_treatments:
        if graphic.shot_id not in shot_ids:
            raise _invalid("Graphic treatment references an unordered Shot.")
        if graphic.role is GraphicRole.DIALOGUE_SUBTITLE:
            if graphic.caption_binding_id not in caption_ids:
                raise _invalid("Dialogue subtitle does not match a CaptionTrack binding.")
            continue
        commercial_graphics.append(graphic)

    audio_ids = {item.track_id for item in base_composition.audio_tracks}
    sound_cue_projections: list[AdvertisingSoundCueProjection] = []
    for cue in plan.sound_cues:
        if cue.role is not AdSoundRole.INTENTIONAL_SILENCE and (
            cue.audio_track_id not in audio_ids
        ):
            raise _invalid("Advertising sound cue does not match an audio track.")
        if cue.synchronized_event_id is not None and (
            cue.synchronized_event_id not in event_ids
        ):
            raise _invalid("Advertising sound cue references an unknown event.")
        sound_cue_projections.append(
            AdvertisingSoundCueProjection(
                cue_id=cue.cue_id,
                role=cue.role,
                audio_track_id=cue.audio_track_id,
                synchronized_event_id=cue.synchronized_event_id,
            )
        )

    source_provenance = tuple(
        dict.fromkeys(
            (
                *base_composition.source_provenance,
                SourceReference(
                    kind="derived",
                    reference=plan.artifact_id,
                    content_hash=plan.content_hash,
                ),
            )
        )
    )
    compiled = base_composition.model_copy(
        update={
            "schema_version": "2.2",
            "revision": base_composition.revision + 1,
            "content_hash": "0" * 64,
            "creation_receipt_id": f"compile-{plan.content_hash}",
            "source_provenance": source_provenance,
            "graphic_layer_ids": tuple(graphic_layer_ids),
            "graphic_layer_animations": tuple(graphic_layer_animations),
            "commercial_graphics": tuple(commercial_graphics),
            "advertising_sound_cues": tuple(sound_cue_projections),
            "ad_creative_plan_id": plan.artifact_id,
            "ad_creative_plan_hash": plan.content_hash,
        }
    )
    try:
        return CompositionSpec.model_validate(
            seal_artifact(compiled).model_dump(mode="python")
        )
    except ValidationError as exc:
        raise _invalid(f"Compiled CompositionSpec is invalid: {exc}") from exc


def compile_ad_creative_handoff(
    plan: AdCreativePlan,
    base_composition: CompositionSpec,
    *,
    approved_commercial_sources: tuple[ApprovedCommercialSourceBinding, ...] = (),
) -> CompiledAdCreativeHandoff:
    composition = compile_ad_creative_plan(plan, base_composition)
    projections = (
        project_commercial_executions(plan)
        if plan.schema_version == "ad-creative-plan/2"
        else ()
    )
    approvals = tuple(
        sorted(
            (
                ApprovedCommercialSourceBinding.model_validate(
                    item.model_dump(mode="python")
                )
                for item in approved_commercial_sources
            ),
            key=lambda item: item.target_shot_id,
        )
    )
    if any(
        len(values) != len(set(values))
        for values in (
            tuple(item.approval_id for item in approvals),
            tuple(item.content_hash for item in approvals),
            tuple(item.execution_projection_hash for item in approvals),
            tuple(item.target_shot_id for item in approvals),
        )
    ):
        raise _preflight_blocked(
            "Commercial source approvals must be unique per identity, projection, and Shot."
        )
    interaction_by_hash = {
        item.projection_hash: item
        for item in projections
        if item.primary_class.value == "product_interaction"
    }
    approval_by_projection = {
        item.execution_projection_hash: item for item in approvals
    }
    if set(interaction_by_hash) != set(approval_by_projection):
        raise _preflight_blocked(
            "Current product-interaction handoff requires one exact approved commercial source per Shot."
        )
    if any(
        approval.ad_creative_plan_hash != plan.content_hash
        or approval.target_shot_id
        != interaction_by_hash[projection_hash].target_shot_id
        for projection_hash, approval in approval_by_projection.items()
    ):
        raise _preflight_blocked(
            "Commercial source approval does not bind the exact current AdCreativePlan projection."
        )
    shot_proposals: list[AdShotProposal] = []
    for shot_id in composition.shot_ids:
        beat_ids = tuple(
            item.beat_id for item in plan.ad_arc if shot_id in item.shot_ids
        )
        product_ids = tuple(
            item.presentation_id
            for item in plan.product_presentations
            if item.shot_id == shot_id
        )
        graphic_ids = tuple(
            item.graphic_id
            for item in plan.graphic_treatments
            if item.shot_id == shot_id
        )
        synchronized_event_ids = set(beat_ids) | set(product_ids) | set(graphic_ids)
        explicit_sound_cue_ids = {
            cue_id
            for item in plan.product_presentations
            if item.shot_id == shot_id
            for cue_id in item.sound_cue_ids
        }
        explicit_sound_cue_ids.update(
            cue_id
            for item in plan.graphic_treatments
            if item.shot_id == shot_id
            for cue_id in item.sound_cue_ids
        )
        shot_proposals.append(
            AdShotProposal(
                shot_id=shot_id,
                beat_ids=beat_ids,
                product_presentation_ids=product_ids,
                graphic_ids=graphic_ids,
                sound_cue_ids=tuple(
                    item.cue_id
                    for item in plan.sound_cues
                    if item.cue_id in explicit_sound_cue_ids
                    or item.synchronized_event_id in synchronized_event_ids
                ),
            )
        )
    return CompiledAdCreativeHandoff(
        plan_id=plan.artifact_id,
        plan_content_hash=plan.content_hash,
        shot_proposals=tuple(shot_proposals),
        composition_requirements=AdCompositionRequirements(
            graphic_layer_ids=composition.graphic_layer_ids,
            commercial_graphic_ids=tuple(
                item.graphic_id for item in composition.commercial_graphics
            ),
            audio_track_ids=tuple(
                item.audio_track_id
                for item in composition.advertising_sound_cues
                if item.audio_track_id is not None
            ),
        ),
        composition_spec=composition,
        commercial_execution_projections=projections,
        approved_commercial_sources=approvals,
    )
