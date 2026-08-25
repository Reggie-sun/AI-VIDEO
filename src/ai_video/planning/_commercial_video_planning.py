from __future__ import annotations

from ai_video.planning._planner_models import (
    AssetRole,
    AvailableAsset,
    VideoPlanningRequest,
)
from ai_video.production.commercial_execution import (
    CommercialExecutionProjection,
    CommercialShotClass,
)
from ai_video.production._commercial_project_reader import (
    reopen_active_commercial_source_approval,
)
from ai_video.production.commercial_reference import (
    ProductReferenceSet,
    validate_product_reference_set_against_registry,
)
from ai_video.production.commercial_source_preparation import (
    CommercialCreativeReference,
)
from ai_video.production.models import AssetType, LoadedProductionProject
from ai_video.production.project import load_production_project
from ai_video.production.video_requirement import (
    ApprovedCommercialSourceLink,
    ProductFidelityRequirement,
    ProductFidelityStrategy,
    ProviderNeutralGenerationIntentProjection,
    SemanticReferenceRole,
)


def commercial_requirement_values(
    request: VideoPlanningRequest,
) -> dict[str, object]:
    approval = request.approved_commercial_source
    references = request.product_reference_set
    if approval is None or references is None:
        return {}
    return {
        "contract_version": "provider-neutral-video-requirement/3",
        "commercial_execution_class": "product_interaction",
        "product_fidelity_requirement": ProductFidelityRequirement(
            product_id=references.product_id,
            sku_id=references.sku_id,
            product_reference_set_id=references.artifact_id,
            product_reference_set_hash=references.content_hash,
            product_source_asset_hashes=tuple(
                sorted(item.asset_sha256 for item in references.assets)
            ),
            strategy=ProductFidelityStrategy.APPROVED_FIRST_FRAME,
            packaging_form=references.packaging_form,
            bottle_silhouette=references.bottle_silhouette,
            dominant_color=references.dominant_color,
            cap_color=references.cap_color,
            logo_label_identity=references.logo_label_identity,
            protected_text_zones=tuple(sorted(references.protected_text_zones)),
        ),
        "approved_commercial_source": ApprovedCommercialSourceLink(
            approval_id=approval.approval_id,
            approval_content_hash=approval.content_hash,
            source_request_hash=approval.source_request_hash,
            target_shot_id=approval.target_shot_id,
            target_shot_content_hash=approval.target_shot_content_hash,
            keyframe_asset_id=approval.keyframe_asset_id,
            keyframe_sha256=approval.keyframe_sha256,
            product_reference_set_id=approval.product_reference_set_id,
            product_reference_set_hash=approval.product_reference_set_hash,
            product_source_asset_hashes=approval.product_source_asset_hashes,
            character_reference_ids=tuple(sorted(approval.character_reference_ids)),
            scene_reference_ids=tuple(sorted(approval.scene_reference_ids)),
            wardrobe_requirement_hash=approval.wardrobe_requirement_hash,
            accessory_requirement_hash=approval.accessory_requirement_hash,
            review_receipt_id=approval.review_receipt_id,
            review_receipt_hash=approval.review_receipt_hash,
        ),
        "source_strategy": ProductFidelityStrategy.APPROVED_FIRST_FRAME,
    }


def build_commercial_video_planning_request(
    *,
    base_request: VideoPlanningRequest,
    execution_projection: CommercialExecutionProjection,
    loaded_project: LoadedProductionProject,
) -> VideoPlanningRequest:
    """Project one exact approved commercial source into current Planner input."""

    checked_request = VideoPlanningRequest.model_validate(
        base_request.model_dump(mode="python")
    )
    projection = CommercialExecutionProjection.model_validate(
        execution_projection.model_dump(mode="python")
    )
    supplied_loaded = LoadedProductionProject.model_validate(
        loaded_project.model_dump(mode="python")
    )
    loaded = load_production_project(supplied_loaded.root / "project.yaml")
    if loaded != supplied_loaded:
        raise ValueError("Commercial Planner loaded project is stale")
    approval = reopen_active_commercial_source_approval(
        loaded,
        target_shot_id=checked_request.target_shot.shot_id,
    )
    references = ProductReferenceSet.model_validate(
        approval.product_reference_set.model_dump(mode="python")
    )
    selected_registry = loaded.registry
    selected_manifest = loaded.manifest
    validate_product_reference_set_against_registry(
        references,
        selected_registry,
        require_registry_identity=False,
    )
    active_approval = next(
        (
            item
            for item in selected_manifest.active_commercial_source_approvals
            if item.target_shot_id == approval.target_shot_id
        ),
        None,
    )
    if projection.primary_class is not CommercialShotClass.PRODUCT_INTERACTION:
        raise ValueError("Commercial Planner handoff requires PRODUCT_INTERACTION")
    if (
        projection.target_shot_id != checked_request.target_shot.shot_id
        or approval.target_shot_id != checked_request.target_shot.shot_id
        or approval.target_shot_content_hash
        != checked_request.target_shot.content_hash
        or approval.ad_creative_plan_hash != projection.ad_creative_plan_hash
        or approval.execution_projection_hash != projection.projection_hash
        or approval.product_reference_set_id != references.artifact_id
        or approval.product_reference_set_hash != references.content_hash
        or approval.product_source_asset_hashes
        != tuple(sorted(item.asset_sha256 for item in references.assets))
        or approval.character_references
        != tuple(
            sorted(
                (
                    CommercialCreativeReference(
                        artifact_id=item.artifact_id,
                        revision=item.revision,
                        content_hash=item.content_hash,
                    )
                    for item in checked_request.character_context
                ),
                key=lambda item: item.artifact_id,
            )
        )
        or approval.scene_references
        != (
            CommercialCreativeReference(
                artifact_id=checked_request.scene_context.artifact_id,
                revision=checked_request.scene_context.revision,
                content_hash=checked_request.scene_context.content_hash,
            ),
        )
        or projection.product_id != references.product_id
        or selected_manifest.schema_version != "2.12"
        or active_approval is None
        or active_approval.approval_id != approval.approval_id
        or active_approval.content_hash != approval.content_hash
    ):
        raise ValueError("Commercial Planner handoff lineage is not exact")
    assets = {item.asset_id: item for item in selected_registry.assets}
    keyframe = assets.get(approval.keyframe_asset_id)
    if (
        keyframe is None
        or keyframe.asset_type is not AssetType.IMAGE
        or keyframe.sha256 != approval.keyframe_sha256
        or any(
            value is None
            for value in (keyframe.width, keyframe.height, keyframe.size_bytes)
        )
    ):
        raise ValueError("Approved commercial keyframe is not registered exactly")
    if checked_request.generation_intent is None:
        raise ValueError("Commercial Planner handoff requires typed generation intent")
    intent = checked_request.generation_intent
    commercial_intent = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=intent.generation_intent,
        generation_operation=intent.generation_operation,
        semantic_reference_roles=(SemanticReferenceRole.FIRST_FRAME,),
        media_reference_asset_ids=(),
        output_need=intent.output_need,
        audio_need=intent.audio_need,
        quality_need=intent.quality_need,
    )
    keyframe_asset = AvailableAsset(
        role=AssetRole.APPROVED_KEYFRAME,
        asset_id=keyframe.asset_id,
        asset_sha256=keyframe.sha256,
        canonical_owner_id=checked_request.target_shot.shot_id,
        canonical_owner_content_hash=checked_request.target_shot.content_hash,
        mime_type=keyframe.mime_type,
        width=keyframe.width,
        height=keyframe.height,
        size_bytes=keyframe.size_bytes,
    )
    payload = checked_request.model_dump(
        mode="python", exclude={"request_content_hash"}
    )
    payload.update(
        available_assets=(keyframe_asset,),
        generation_intent=commercial_intent,
        commercial_execution_projection=projection,
        approved_commercial_source=approval,
        product_reference_set=references,
        selected_commercial_registry=selected_registry,
        active_commercial_source_approval=active_approval,
    )
    return VideoPlanningRequest.create(**payload)
