"""Production owner for the deterministic generated-video candidate preparer.

This module converges the test-only ``make_p8_video_candidate_preparer``
fixture into a production owner that the canonical committer can rely on.
The factory must remain deterministic and write-free: no Manifest mutation,
no filesystem side effects, no Provider calls, no secret lookups.

The resulting ``PreparedVideoCandidate`` is consumed by
``ProductionStateCommitter.prepare_video_activation_candidate`` and re-validated
by ``validate_video_activation_candidate`` before any canonical state change
is permitted. ``resolve_video_activation_dependency_state`` is the single
source of truth for dependency resolution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from ai_video.production._state_commit_video_candidate import (
    PreparedVideoCandidate,
    resolve_video_activation_dependency_state,
)
from ai_video.production.dependency import build_production_dependency_graph
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ArtifactReference,
    AssetType,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    VisualStrategy,
)
from ai_video.production.paths import (
    canonical_dependency_graph_snapshot_path,
    canonical_image_shot_revision_path,
)
from ai_video.production.registry import registry_semantic_sha256

if TYPE_CHECKING:
    from ai_video.production.dependency import ProductionDependencyInputs
    from ai_video.production.models import AssetRecord, LoadedProductionProject
    from ai_video.production.video import ResolvedVideoGenerationRequest
    from ai_video.production.video_artifact import (
        MeasuredVideoMetadata,
        VideoProbeReceipt,
        VideoProvenanceReceipt,
    )


_ZERO_HASH = "0" * 64


def _canonical_json_bytes(value: object) -> bytes:
    """Stable JSON encoding that mirrors the committer's ``_canonical_json_bytes``."""

    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def make_video_candidate_preparer(
    base_inputs: "ProductionDependencyInputs",
):
    """Return a deterministic, write-free video candidate preparer closure."""

    def prepare(
        base_project: "LoadedProductionProject",
        request: "ResolvedVideoGenerationRequest",
        measured: "MeasuredVideoMetadata",
        probe_receipt: "VideoProbeReceipt",
        provenance: "VideoProvenanceReceipt",
        asset_record: "AssetRecord",
        continuity_asset_record: "AssetRecord | None" = None,
    ) -> PreparedVideoCandidate:
        if request.activation_scope is None:
            raise ValueError(
                "Video activation request must carry an activation_scope."
            )
        original = request.activation_scope.request
        live_base_inputs = replace(base_inputs, project=base_project)

        appended_assets = (
            (asset_record, continuity_asset_record)
            if continuity_asset_record is not None
            else (asset_record,)
        )
        candidate_registry = base_project.registry.model_copy(
            update={
                "schema_version": "2.2",
                "revision_id": _ZERO_HASH,
                "content_hash": _ZERO_HASH,
                "assets": (*base_project.registry.assets, *appended_assets),
            }
        )
        registry_hash = registry_semantic_sha256(candidate_registry)
        candidate_registry = candidate_registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        )
        registry_bytes = _canonical_json_bytes(candidate_registry.model_dump(mode="json"))
        registry_pointer = RegistrySnapshotPointer(
            path=Path(f"assets/registry.{registry_hash}.json"),
            revision_id=registry_hash,
            content_hash=registry_hash,
            file_sha256=hashlib.sha256(registry_bytes).hexdigest(),
        )

        base_shot = next(
            item
            for item in base_project.shots
            if item.shot_id == original.target_shot_id
        )
        candidate_shot = seal_artifact(
            base_shot.model_copy(
                update={
                    "revision": base_shot.revision + 1,
                    "content_hash": _ZERO_HASH,
                    "creation_receipt_id": provenance.content_hash,
                    "visual_strategy": VisualStrategy.GENERATED_VIDEO,
                    "generated_video_rationale": (
                        f"Sealed generation {request.generation_id}."
                    ),
                    "required_asset_roles": tuple(
                        role.model_copy(
                            update={
                                "asset_ids": (request.output_asset_id,),
                                "allowed_asset_types": (AssetType.VIDEO,),
                            }
                        )
                        if role.role == original.target_asset_role
                        else role
                        for role in base_shot.required_asset_roles
                    ),
                }
            )
        )
        shot_path = canonical_image_shot_revision_path(
            candidate_shot.revision, candidate_shot.content_hash
        )
        shot_bytes = yaml.safe_dump(
            candidate_shot.model_dump(mode="json"),
            sort_keys=True,
            allow_unicode=True,
        ).encode("utf-8")

        candidate_project_artifact = seal_artifact(
            base_project.project.model_copy(
                update={
                    "revision": base_project.project.revision + 1,
                    "content_hash": _ZERO_HASH,
                    "creation_receipt_id": provenance.content_hash,
                    "artifacts": base_project.project.artifacts.model_copy(
                        update={
                            "shots": tuple(
                                ArtifactReference(
                                    artifact_id=candidate_shot.artifact_id,
                                    revision=candidate_shot.revision,
                                    content_hash=candidate_shot.content_hash,
                                    path=shot_path,
                                )
                                if item.artifact_id == candidate_shot.artifact_id
                                else item
                                for item in base_project.project.artifacts.shots
                            )
                        }
                    ),
                }
            )
        )
        project_bytes = yaml.safe_dump(
            candidate_project_artifact.model_dump(mode="json"),
            sort_keys=True,
            allow_unicode=True,
        ).encode("utf-8")
        project_path = Path(
            f"state/projects/project.{candidate_project_artifact.revision}."
            f"{candidate_project_artifact.content_hash}.yaml"
        )
        project_pointer = ProjectSnapshotPointer(
            path=project_path,
            revision=candidate_project_artifact.revision,
            content_hash=candidate_project_artifact.content_hash,
            file_sha256=hashlib.sha256(project_bytes).hexdigest(),
        )

        candidate_project = base_project.model_copy(
            update={
                "project": candidate_project_artifact,
                "shots": tuple(
                    candidate_shot
                    if item.shot_id == candidate_shot.shot_id
                    else item
                    for item in base_project.shots
                ),
                "registry": candidate_registry,
                "asset_paths": {
                    **base_project.asset_paths,
                    asset_record.asset_id: base_project.root / asset_record.artifact_path,
                    **(
                        {
                            continuity_asset_record.asset_id: (
                                base_project.root / continuity_asset_record.artifact_path
                            )
                        }
                        if continuity_asset_record is not None
                        else {}
                    ),
                },
                "manifest": base_project.manifest.model_copy(
                    update={
                        "active_project": project_pointer,
                        "active_registry": registry_pointer,
                    }
                ),
            }
        )

        candidate_inputs = replace(live_base_inputs, project=candidate_project)
        candidate_graph = build_production_dependency_graph(candidate_inputs)
        graph_bytes = _canonical_json_bytes(candidate_graph.model_dump(mode="json"))
        graph_pointer = DependencyGraphSnapshotPointer(
            revision_id=candidate_graph.revision_id,
            content_hash=candidate_graph.content_hash,
            path=canonical_dependency_graph_snapshot_path(candidate_graph.revision_id),
            file_sha256=hashlib.sha256(graph_bytes).hexdigest(),
        )

        candidate_project = candidate_project.model_copy(
            update={
                "manifest": candidate_project.manifest.model_copy(
                    update={"active_dependency_graph": graph_pointer}
                ),
                "dependency_graph": candidate_graph,
            }
        )
        candidate_inputs = replace(candidate_inputs, project=candidate_project)

        resolution = resolve_video_activation_dependency_state(
            graph=candidate_graph,
            base_states=base_project.manifest.dependency_states,
            project_pointer=project_pointer,
            registry_pointer=registry_pointer,
            target_shot_id=original.target_shot_id,
            output_asset_id=request.output_asset_id,
            continuity_asset_id=(
                continuity_asset_record.asset_id
                if continuity_asset_record is not None
                else None
            ),
        )

        return PreparedVideoCandidate(
            base_inputs=live_base_inputs,
            candidate_project=candidate_project,
            candidate_registry=candidate_registry,
            candidate_inputs=candidate_inputs,
            candidate_graph=candidate_graph,
            resolution=resolution,
            candidate_project_pointer=project_pointer,
            candidate_registry_pointer=registry_pointer,
            candidate_graph_pointer=graph_pointer,
            candidate_shot_path=shot_path,
            candidate_shot_bytes=shot_bytes,
            candidate_project_bytes=project_bytes,
            candidate_registry_bytes=registry_bytes,
            candidate_graph_bytes=graph_bytes,
        )

    return prepare


__all__ = ["make_video_candidate_preparer"]
