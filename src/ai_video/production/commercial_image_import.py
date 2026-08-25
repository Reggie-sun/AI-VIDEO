from __future__ import annotations

import hashlib
from dataclasses import replace

from ai_video.production.commercial_reference import (
    ProductReferenceSet,
    validate_product_reference_set_against_registry,
)
from ai_video.production.image_import import (
    CommercialImageImportReceipt,
    _invalid,
    commercial_image_import_asset,
    validate_commercial_image_import,
)
from ai_video.production.models import AssetRegistrySnapshot, LoadedProductionProject
from ai_video.production.paths import canonical_commercial_image_import_receipt_path

from ._state_commit_common import _canonical_json_bytes
from ._state_commit_contracts import PreparedArtifact, StateCommitRequest


def prepare_commercial_image_import_commit(
    *,
    base: LoadedProductionProject,
    product_reference_set: ProductReferenceSet,
    receipt: CommercialImageImportReceipt,
    image_bytes: bytes,
    base_commit: StateCommitRequest,
) -> StateCommitRequest:
    """Append one exact commercial keyframe through the canonical Registry writer."""

    validate_commercial_image_import(receipt, image_bytes)
    try:
        validate_product_reference_set_against_registry(
            product_reference_set,
            base.registry,
        )
    except ValueError as exc:
        raise _invalid(
            "Commercial import ProductReferenceSet is not current.", str(exc)
        ) from exc
    characters = {item.artifact_id: item for item in base.characters}
    scenes = {item.artifact_id: item for item in base.scenes}
    shot = next(
        (item for item in base.shots if item.shot_id == receipt.target_shot_id),
        None,
    )
    if (
        receipt.target_kind != "commercial_interaction_keyframe"
        or receipt.product_reference_set != product_reference_set
        or shot is None
        or shot.content_hash != receipt.target_shot_content_hash
        or any(item not in characters for item in receipt.character_reference_ids)
        or any(item not in scenes for item in receipt.scene_reference_ids)
    ):
        raise _invalid("Commercial import creative lineage is not active and exact.")
    asset = commercial_image_import_asset(receipt)
    registry_artifact = next(
        (
            item
            for item in base_commit.artifacts
            if item.relative_path == base_commit.next_registry.path
        ),
        None,
    )
    if (
        base_commit.operation != "commit_project_registry"
        or base_commit.expected_manifest_revision != base.manifest.manifest_revision
        or base_commit.next_project.revision != base.project.revision
        or base_commit.next_project.content_hash != base.project.content_hash
        or base_commit.dependency_graph_transition is None
        or registry_artifact is None
    ):
        raise _invalid("Commercial import must reuse one exact Registry/Graph commit.")
    candidate_registry = AssetRegistrySnapshot.model_validate_json(
        registry_artifact.payload
    )
    if (
        candidate_registry.assets != (*base.registry.assets, asset)
        or base_commit.next_registry.content_hash != candidate_registry.content_hash
    ):
        raise _invalid("Commercial import Registry must append its exact imported asset.")
    receipt_payload = _canonical_json_bytes(receipt)
    additions = (
        PreparedArtifact(
            canonical_commercial_image_import_receipt_path(receipt.content_hash),
            receipt_payload,
            hashlib.sha256(receipt_payload).hexdigest(),
        ),
        PreparedArtifact(asset.artifact_path, image_bytes, receipt.output_sha256),
    )
    paths = {item.relative_path for item in base_commit.artifacts}
    if any(item.relative_path in paths for item in additions):
        raise _invalid("Commercial import evidence collides with candidate artifacts.")
    return replace(
        base_commit,
        artifacts=tuple(
            sorted(
                (*base_commit.artifacts, *additions),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
    )
