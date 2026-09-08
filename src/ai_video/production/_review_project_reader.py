"""Strict reader for active P6 review and Final Acceptance state."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from ai_video.production.caption_quality import reopen_caption_review_chain
from ai_video.production.hashing import canonical_sha256
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports
from ai_video.production.models import LoadedProductionProject, QaLayer


def load_active_review_state(
    root: Path, bundle: LoadedProductionProject
) -> LoadedProductionProject:
    """Reopen current QA policy, review chains, and final acceptance exactly."""
    from ai_video.production.project import (
        _invalid,
        _load_exact_render_state,
        load_final_acceptance_receipt,
        load_qa_policy,
        load_review_receipt,
    )

    manifest = bundle.manifest
    if not (
        manifest.schema_version == "2.4"
        or (
            manifest_supports(
                manifest.schema_version, ManifestCapability.IMAGE_STATE
            )
            and manifest.active_qa_policy is not None
        )
    ):
        return bundle
    if manifest.active_qa_policy is None:
        raise _invalid(f"Manifest {manifest.schema_version} requires an active QA policy.")
    qa_policy = load_qa_policy(root, manifest.active_qa_policy)
    if qa_policy.caption_policy is not None and not manifest_supports(
        manifest.schema_version, ManifestCapability.CAPTION_REVIEW
    ):
        raise _invalid(
            "Caption-aware QA policy requires the Manifest caption review capability."
        )
    current_render = (
        _load_exact_render_state(bundle, manifest.active_render_state)
        if manifest.active_render_state is not None
        else None
    )
    review_bundle = bundle.model_copy(
        update={"render_state": current_render, "qa_policy": qa_policy}
    )
    for receipt_pointer in manifest.active_review_receipts:
        receipt = load_review_receipt(root, receipt_pointer)
        if (
            current_render is None
            or receipt.qa_policy != manifest.active_qa_policy
            or receipt.dependency_graph_revision_id
            != manifest.active_dependency_graph.revision_id
            or receipt.render_state != manifest.active_render_state
            or receipt.render_output_sha256 != current_render.output.file_sha256
            or receipt.timeline_fingerprint != current_render.timeline_fingerprint
        ):
            raise _invalid("Active Review Receipt is stale.")
        if receipt_pointer.layer is QaLayer.CAPTION:
            try:
                reopen_caption_review_chain(
                    project=review_bundle,
                    receipt_pointer=receipt_pointer,
                )
            except (OSError, ValidationError, ValueError) as exc:
                raise _invalid(
                    "Active CAPTION Review Receipt chain is invalid.", str(exc)
                ) from exc
        if receipt_pointer.layer is QaLayer.SEMANTIC and qa_policy.final_output is not None:
            from ai_video.production.final_output_review import reopen_review_verdict

            reopen_review_verdict(root, receipt_pointer)
    acceptance = manifest.final_acceptance_state
    if acceptance is not None and acceptance.active_receipt is not None:
        final_receipt = load_final_acceptance_receipt(root, acceptance.active_receipt)
        if qa_policy.final_output is not None:
            from ai_video.production.final_output_review import require_closed_repairs

            require_closed_repairs(root, manifest)
        required_layers = {
            item for item in qa_policy.required_layers if item.value != "final_acceptance"
        }
        selected_layers = {
            item.layer for item in final_receipt.required_review_receipts
        }
        dependency_states_hash = canonical_sha256(
            {
                "dependency_states": [
                    item.model_dump(mode="json") for item in manifest.dependency_states
                ]
            }
        )
        if (
            current_render is None
            or final_receipt.dependency_graph != manifest.active_dependency_graph
            or final_receipt.render_state != manifest.active_render_state
            or final_receipt.qa_policy != manifest.active_qa_policy
            or final_receipt.dependency_states_hash != dependency_states_hash
            or final_receipt.render_output_sha256 != current_render.output.file_sha256
            or final_receipt.timeline_fingerprint != current_render.timeline_fingerprint
            or selected_layers != required_layers
            or set(final_receipt.required_review_receipts)
            != {
                item
                for item in manifest.active_review_receipts
                if item.layer in required_layers
            }
        ):
            raise _invalid("Final Acceptance Receipt is stale.")
    return bundle.model_copy(update={"qa_policy": qa_policy})
