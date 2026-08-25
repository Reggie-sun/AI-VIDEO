from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
    CommercialSourceCandidate,
    CommercialSourcePreparationRequest,
)
from ai_video.production.commercial_visual_review import CommercialSourceReviewReceipt
from ai_video.production.commercial_visual_review import (
    CommercialVisualEvidence,
    adjudicate_commercial_visual_evidence,
)
from ai_video.production.commercial_dependency import (
    validate_commercial_source_dependency_graph,
)
from ai_video.production.dependency import asset_node_id, creative_node_id
from ai_video.production.commercial_reference import (
    validate_product_reference_set_against_registry,
)
from ai_video.production.image_import import (
    COMMERCIAL_IMAGE_IMPORT_TOOL,
    CommercialImageImportReceipt,
    validate_commercial_image_import,
)
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    CommercialSourceDependencyEvidence,
    CommercialSourceLifecycle,
    DependencyLifecycle,
    LoadedProductionProject,
    QaVerdict,
    AssetRegistrySnapshot,
    canonical_registry_snapshot_path,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_commercial_source_candidate_path,
    canonical_commercial_source_evidence_path,
    canonical_commercial_image_import_receipt_path,
    canonical_commercial_source_request_path,
    canonical_commercial_source_review_path,
    resolve_contained_path,
)
from ai_video.production.registry import registry_semantic_sha256


ModelT = TypeVar("ModelT", bound=BaseModel)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _read_model(
    root: Path,
    path: Path,
    model_type: type[ModelT],
    *,
    allowed_root: Path | None = None,
) -> tuple[ModelT, str]:
    owner_root = allowed_root or root / "state/commercial-source"
    try:
        resolved = resolve_contained_path(
            root,
            path,
            allowed_root=owner_root,
        )
        snapshot = _read_regular_file_nofollow(
            resolved,
            contained_by=owner_root,
        )
        model = model_type.model_validate_json(snapshot.data)
    except (OSError, ValueError, ValidationError) as exc:
        raise _invalid(
            "Active commercial source evidence could not be reopened.", str(exc)
        ) from exc
    return model, snapshot.file_sha256


def verify_active_commercial_source_approvals(
    bundle: LoadedProductionProject,
) -> None:
    manifest = bundle.manifest
    if manifest.schema_version != "2.12":
        return
    root = bundle.root
    registry_assets = {item.asset_id: item for item in bundle.registry.assets}
    shots = {item.shot_id: item for item in bundle.shots}
    characters = {item.artifact_id: item for item in bundle.characters}
    scenes = {item.artifact_id: item for item in bundle.scenes}
    reopened: dict[
        str,
        tuple[
            CommercialSourcePreparationRequest,
            CommercialSourceCandidate | None,
            CommercialSourceReviewReceipt | None,
        ],
    ] = {}
    for attempt in manifest.commercial_source_attempts:
        request, _ = _read_model(
            root, attempt.request_path, CommercialSourcePreparationRequest
        )
        if (
            attempt.request_path
            != canonical_commercial_source_request_path(request.request_fingerprint)
            or request.request_fingerprint != attempt.request_fingerprint
            or request.request_id != attempt.request_id
            or request.target_shot_id != attempt.target_shot_id
            or request.target_shot_content_hash != attempt.target_shot_content_hash
            or request.product_reference_set_hash
            != attempt.product_reference_set_hash
        ):
            raise _invalid("Commercial source attempt request lineage is inconsistent.")
        historical_registry, _ = _read_model(
            root,
            canonical_registry_snapshot_path(
                request.product_reference_set.registry_revision_id
            ),
            AssetRegistrySnapshot,
            allowed_root=root / "assets",
        )
        try:
            if (
                historical_registry.revision_id
                != request.product_reference_set.registry_revision_id
                or historical_registry.content_hash
                != request.product_reference_set.registry_content_hash
                or registry_semantic_sha256(historical_registry)
                != historical_registry.content_hash
            ):
                raise ValueError("historical Registry identity mismatch")
            validate_product_reference_set_against_registry(
                request.product_reference_set,
                historical_registry,
            )
        except ValueError as exc:
            raise _invalid(
                "Commercial ProductReferenceSet history is invalid.", str(exc)
            ) from exc
        if attempt.lifecycle is not CommercialSourceLifecycle.STALE:
            try:
                validate_product_reference_set_against_registry(
                    request.product_reference_set,
                    bundle.registry,
                    require_registry_identity=False,
                )
            except ValueError as exc:
                raise _invalid(
                    "Current commercial product reference bytes are stale.", str(exc)
                ) from exc
            shot = shots.get(request.target_shot_id)
            if (
                request.base_project_content_hash != bundle.project.content_hash
                or request.base_registry_revision_id != bundle.registry.revision_id
                or request.base_registry_content_hash != bundle.registry.content_hash
                or (
                    attempt.lifecycle is not CommercialSourceLifecycle.APPROVED
                    and (
                        bundle.dependency_graph is None
                        or request.base_dependency_graph_content_hash
                        != bundle.dependency_graph.content_hash
                    )
                )
                or shot is None
                or shot.revision != request.target_shot_revision
                or shot.content_hash != request.target_shot_content_hash
                or any(
                    (current := characters.get(reference.artifact_id)) is None
                    or current.revision != reference.revision
                    or current.content_hash != reference.content_hash
                    for reference in request.character_references
                )
                or any(
                    (current := scenes.get(reference.artifact_id)) is None
                    or current.revision != reference.revision
                    or current.content_hash != reference.content_hash
                    for reference in request.scene_references
                )
            ):
                raise _invalid("Current commercial creative lineage is stale.")
        candidate: CommercialSourceCandidate | None = None
        receipt: CommercialSourceReviewReceipt | None = None
        if attempt.candidate_record_hash is not None:
            candidate, _ = _read_model(
                root,
                canonical_commercial_source_candidate_path(
                    attempt.candidate_record_hash
                ),
                CommercialSourceCandidate,
            )
            if (
                canonical_sha256(candidate.model_dump(mode="json"))
                != attempt.candidate_record_hash
                or candidate.request_hash != request.request_fingerprint
                or candidate.asset_id != attempt.candidate_asset_id
                or candidate.asset_sha256 != attempt.candidate_sha256
            ):
                raise _invalid("Commercial source candidate lineage is inconsistent.")
            import_receipt, _ = _read_model(
                root,
                canonical_commercial_image_import_receipt_path(
                    candidate.import_receipt_hash
                ),
                CommercialImageImportReceipt,
            )
            asset = registry_assets.get(candidate.asset_id)
            if attempt.lifecycle is not CommercialSourceLifecycle.STALE:
                try:
                    if (
                        import_receipt != candidate.import_receipt
                        or asset is None
                        or asset.sha256 != candidate.asset_sha256
                        or asset.creation_receipt_id != import_receipt.content_hash
                        or asset.tool != COMMERCIAL_IMAGE_IMPORT_TOOL
                    ):
                        raise ValueError("Registry/import identity mismatch")
                    image_bytes = _read_regular_file_nofollow(
                        bundle.asset_paths[candidate.asset_id],
                        contained_by=root / "assets",
                    ).data
                    validate_commercial_image_import(import_receipt, image_bytes)
                except (KeyError, OSError, ValueError, AiVideoError) as exc:
                    detail = (
                        exc.technical_detail
                        if isinstance(exc, AiVideoError)
                        else str(exc)
                    )
                    raise _invalid(
                        "Current commercial import evidence is invalid.", detail
                    ) from exc
        if attempt.review_receipt_hash is not None:
            if attempt.review_evidence_hash is None or candidate is None:
                raise _invalid("Commercial review is missing candidate evidence.")
            evidence, _ = _read_model(
                root,
                canonical_commercial_source_evidence_path(
                    attempt.review_evidence_hash
                ),
                CommercialVisualEvidence,
            )
            receipt, _ = _read_model(
                root,
                canonical_commercial_source_review_path(
                    attempt.review_receipt_hash
                ),
                CommercialSourceReviewReceipt,
            )
            if (
                not verify_artifact_hash(evidence)
                or evidence.content_hash != attempt.review_evidence_hash
                or receipt.content_hash != attempt.review_receipt_hash
            ):
                raise _invalid("Commercial review evidence seal is invalid.")
            if attempt.lifecycle is not CommercialSourceLifecycle.STALE:
                if bundle.qa_policy is None:
                    raise _invalid("Current commercial review policy is missing.")
                expected_receipt = adjudicate_commercial_visual_evidence(
                    evidence,
                    policy=bundle.qa_policy,
                )
                if receipt != expected_receipt:
                    raise _invalid("Current commercial review verdict is stale.")
        reopened[attempt.attempt_id] = (request, candidate, receipt)
    for pointer in manifest.active_commercial_source_approvals:
        approval, approval_file_hash = _read_model(
            root, pointer.path, ApprovedCommercialSourceBinding
        )
        if (
            approval_file_hash != pointer.file_sha256
            or approval.content_hash != pointer.content_hash
            or not verify_artifact_hash(approval)
            or approval.approval_id != pointer.approval_id
            or approval.target_shot_id != pointer.target_shot_id
        ):
            raise _invalid("Active commercial source approval pointer is inconsistent.")
        attempt = next(
            (
                item
                for item in manifest.commercial_source_attempts
                if item.active_approval == pointer
            ),
            None,
        )
        if attempt is None or attempt.lifecycle is not CommercialSourceLifecycle.APPROVED:
            raise _invalid("Active commercial source approval has no approved attempt.")
        request, candidate, receipt = reopened[attempt.attempt_id]
        if (
            approval.source_request_hash != request.request_fingerprint
            or approval.ad_creative_plan_hash != request.ad_creative_plan_hash
            or approval.execution_projection_hash != request.execution_projection_hash
            or approval.product_reference_set_id != request.product_reference_set_id
            or approval.product_reference_set_hash != request.product_reference_set_hash
            or approval.product_reference_set != request.product_reference_set
            or approval.product_source_asset_hashes
            != request.product_reference_asset_hashes
            or approval.character_reference_ids != request.character_reference_ids
            or approval.character_references != request.character_references
            or approval.scene_reference_ids != request.scene_reference_ids
            or approval.scene_references != request.scene_references
            or approval.wardrobe_requirement_hash
            != request.wardrobe_requirement_hash
            or approval.accessory_requirement_hash
            != request.accessory_requirement_hash
        ):
            raise _invalid("Active commercial source request lineage is inconsistent.")
        if candidate is None:
            raise _invalid("Active commercial source approval is missing its candidate.")
        if (
            approval.keyframe_asset_id != candidate.asset_id
            or approval.keyframe_sha256 != candidate.asset_sha256
        ):
            raise _invalid("Active commercial source candidate lineage is inconsistent.")
        if (
            receipt is None
            or receipt.verdict is not QaVerdict.PASS
            or receipt.receipt_id != approval.review_receipt_id
            or receipt.content_hash != approval.review_receipt_hash
            or receipt.source_request_hash != request.request_fingerprint
            or receipt.candidate_asset_id != candidate.asset_id
            or receipt.candidate_sha256 != candidate.asset_sha256
        ):
            raise _invalid("Active commercial source review lineage is inconsistent.")
        keyframe = registry_assets.get(approval.keyframe_asset_id)
        if keyframe is None or keyframe.sha256 != approval.keyframe_sha256:
            raise _invalid("Active commercial keyframe bytes are stale.")
        if bundle.dependency_graph is None:
            raise _invalid("Active commercial dependency graph is missing.")
        try:
            validate_commercial_source_dependency_graph(
                bundle.dependency_graph,
                product_reference_set=approval.product_reference_set,
                keyframe_asset_id=approval.keyframe_asset_id,
                keyframe_sha256=approval.keyframe_sha256,
            )
        except ValueError as exc:
            raise _invalid(
                "Active commercial dependency graph is stale.", str(exc)
            ) from exc
        state_by_id = {
            item.node_id: item for item in manifest.dependency_states
        }
        for node_id in (
            creative_node_id(
                "product-reference-set", approval.product_reference_set_id
            ),
            asset_node_id(approval.keyframe_asset_id),
        ):
            state = state_by_id.get(node_id)
            if (
                state is None
                or state.lifecycle is not DependencyLifecycle.FRESH
                or not isinstance(
                    state.applied_evidence,
                    CommercialSourceDependencyEvidence,
                )
                or state.applied_evidence.pointer != pointer
            ):
                raise _invalid(
                    "Active commercial dependency evidence is not fresh and exact."
                )


def reopen_active_commercial_source_approval(
    bundle: LoadedProductionProject,
    *,
    target_shot_id: str,
) -> ApprovedCommercialSourceBinding:
    """Reopen one Manifest-selected approval after the full durable-chain check."""

    verify_active_commercial_source_approvals(bundle)
    pointers = tuple(
        item
        for item in bundle.manifest.active_commercial_source_approvals
        if item.target_shot_id == target_shot_id
    )
    if len(pointers) != 1:
        raise _invalid(
            "Commercial Planner requires one exact active source approval."
        )
    pointer = pointers[0]
    approval, file_hash = _read_model(
        bundle.root,
        pointer.path,
        ApprovedCommercialSourceBinding,
    )
    if (
        file_hash != pointer.file_sha256
        or approval.approval_id != pointer.approval_id
        or approval.target_shot_id != pointer.target_shot_id
        or approval.content_hash != pointer.content_hash
        or not verify_artifact_hash(approval)
    ):
        raise _invalid("Active commercial source approval could not be reopened exactly.")
    return approval
