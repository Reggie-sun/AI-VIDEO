"""Read-only freshness checks for approved repair evidence."""

from __future__ import annotations

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    ApprovedRepairReceipt,
    ProductionManifest,
    RenderStateSnapshot,
)


def approved_repair_is_current(
    manifest: ProductionManifest,
    receipt: ApprovedRepairReceipt,
    *,
    current_render: RenderStateSnapshot | None,
) -> bool:
    """Return whether an Approved Repair Receipt binds current P5/P6 state."""

    return (
        current_render is not None
        and manifest.active_dependency_graph == receipt.dependency_graph
        and canonical_sha256(
            {
                "dependency_states": [
                    item.model_dump(mode="json") for item in manifest.dependency_states
                ]
            }
        )
        == receipt.dependency_states_hash
        and manifest.active_render_state == receipt.render_state
        and current_render.output.file_sha256 == receipt.render_output_sha256
        and current_render.timeline_fingerprint == receipt.timeline_fingerprint
        and manifest.active_qa_policy == receipt.qa_policy
        and tuple(item.review_id for item in manifest.active_review_receipts)
        == receipt.review_receipt_ids
    )


__all__ = ["approved_repair_is_current"]
