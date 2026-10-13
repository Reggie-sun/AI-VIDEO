"""Write-free image activation preparation for the canonical image committer.

The image validator reopens this exact candidate; dependency fingerprints and
invalidation remain exclusively with the existing P5 builder and resolver.
"""
from dataclasses import replace
import hashlib
from pathlib import Path

from ai_video.production._state_commit_common import _canonical_json_bytes, _canonical_yaml_bytes
from ai_video.production._state_commit_contracts import PreparedImageCandidate
from ai_video.production.dependency import build_production_dependency_graph, resolve_dependency_state
from ai_video.production.hashing import seal_artifact
from ai_video.production.image import _reference_graph_input_ids
from ai_video.production.models import (
    ArtifactReference, AssetRecord, AssetSourceKind, AssetType, DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer, RegistrySnapshotPointer,
)
from ai_video.production.paths import canonical_dependency_graph_snapshot_path, canonical_image_asset_path, canonical_image_shot_revision_path
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.remote_image import remote_image_egress


def make_image_candidate_preparer(base_inputs):
    """Prepare one image, one Shot revision, and the normal dependency graph."""
    def prepare(base, request, authorization, result, measured, receipt):
        inputs = replace(base_inputs, project=base)
        shot = next(s for s in base.shots if s.shot_id == request.target_shot_id)
        asset = AssetRecord(asset_id=request.output_asset_id, asset_type=AssetType.IMAGE,
            artifact_path=canonical_image_asset_path(measured.sha256), sha256=measured.sha256,
            size_bytes=measured.size_bytes, mime_type=measured.mime_type, width=measured.width, height=measured.height,
            source_kind=AssetSourceKind.GENERATED, tool=result.adapter,
            input_artifact_ids=(shot.artifact_id, *(identity for ref in request.references
                for identity in _reference_graph_input_ids(ref))),
            input_fingerprint=request.request_fingerprint, creation_receipt_id=receipt.content_hash,
            usage_license=authorization.usage_license, egress=remote_image_egress(authorization.remote_binding),
            cost_receipt_id=receipt.cost_receipt_id)
        registry = base.registry.model_copy(update={"assets": (*base.registry.assets, asset),
            "schema_version": "2.1" if asset.egress.remote and base.registry.schema_version == "2.0"
            else base.registry.schema_version})
        digest = registry_semantic_sha256(registry)
        registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
        registry_bytes = _canonical_json_bytes(registry)
        registry_pointer = RegistrySnapshotPointer(path=Path(f"assets/registry.{digest}.json"),
            revision_id=digest, content_hash=digest, file_sha256=hashlib.sha256(registry_bytes).hexdigest())
        revised = seal_artifact(shot.model_copy(update={"revision": shot.revision + 1,
            "content_hash": "0" * 64, "creation_receipt_id": receipt.content_hash,
            "required_asset_roles": tuple(r.model_copy(update={"asset_ids": (asset.asset_id,)})
                if r.role == request.target_asset_role else r for r in shot.required_asset_roles)}))
        shot_path = canonical_image_shot_revision_path(revised.revision, revised.content_hash)
        project = seal_artifact(base.project.model_copy(update={"revision": base.project.revision + 1,
            "content_hash": "0" * 64, "creation_receipt_id": receipt.content_hash,
            "artifacts": base.project.artifacts.model_copy(update={"shots": tuple(
                ArtifactReference(artifact_id=revised.artifact_id, revision=revised.revision,
                    content_hash=revised.content_hash, path=shot_path) if r.artifact_id == revised.artifact_id else r
                for r in base.project.artifacts.shots)})}))
        project_bytes = _canonical_yaml_bytes(project)
        project_pointer = ProjectSnapshotPointer(
            path=Path(f"state/projects/project.{project.revision}.{project.content_hash}.yaml"),
            revision=project.revision, content_hash=project.content_hash,
            file_sha256=hashlib.sha256(project_bytes).hexdigest())
        candidate = base.model_copy(update={"project": project, "registry": registry,
            "shots": tuple(revised if s.shot_id == revised.shot_id else s for s in base.shots),
            "asset_paths": {**base.asset_paths, asset.asset_id: base.root / asset.artifact_path},
            "manifest": base.manifest.model_copy(update={"active_project": project_pointer,
                "active_registry": registry_pointer})})
        candidate_inputs = replace(inputs, project=candidate)
        graph = build_production_dependency_graph(candidate_inputs)
        graph_bytes = _canonical_json_bytes(graph)
        graph_pointer = DependencyGraphSnapshotPointer(path=canonical_dependency_graph_snapshot_path(graph.revision_id),
            revision_id=graph.revision_id, content_hash=graph.content_hash,
            file_sha256=hashlib.sha256(graph_bytes).hexdigest())
        candidate = candidate.model_copy(update={"dependency_graph": graph,
            "manifest": candidate.manifest.model_copy(update={"active_dependency_graph": graph_pointer})})
        return PreparedImageCandidate(base_inputs=inputs, candidate_project=candidate, candidate_registry=registry,
            candidate_inputs=replace(candidate_inputs, project=candidate), candidate_graph=graph,
            resolution=resolve_dependency_state(graph, base.manifest.dependency_states),
            candidate_project_pointer=project_pointer, candidate_registry_pointer=registry_pointer,
            candidate_graph_pointer=graph_pointer, candidate_project_bytes=project_bytes,
            candidate_registry_bytes=registry_bytes, candidate_graph_bytes=graph_bytes)
    return prepare
