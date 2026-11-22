from __future__ import annotations

from ai_video.production.generation_preflight.models import VideoPlanningRequest
from ai_video.production.video_requirement import (
    ApprovedCommercialSourceLink,
    ProductFidelityRequirement,
    ProductFidelityStrategy,
)


def commercial_requirement_values(
    request: VideoPlanningRequest,
) -> dict[str, object]:
    approval = request.approved_commercial_source
    references = request.product_reference_set
    if approval is None or references is None:
        return {}
    return {
        "contract_version": ("provider-neutral-video-requirement/4"
            if request.generation_intent is not None
            and request.generation_intent.generation_intent.primary_camera_motion is not None
            else "provider-neutral-video-requirement/3"),
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
