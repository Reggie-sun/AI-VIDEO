"""Pure validation contracts for deterministic generated-video candidates."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai_video.production.dependency import (
    DependencyResolution,
    ProductionDependencyInputs,
    asset_node_id,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
    shot_projection_node_id,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    ArtifactReference,
    AssetRecord,
    AssetRegistrySnapshot,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyLifecycle,
    DependencyNodeState,
    DependencySemanticRole,
    LoadedProductionProject,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    RegistryDependencyEvidence,
    RegistrySnapshotPointer,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_artifact import (
    MeasuredVideoMetadata,
    VideoProbeReceipt,
    VideoProvenanceReceipt,
)
from ai_video.production.video_candidate_composition import (
    video_candidate_dependency_inputs_are_exact,
)

from ._state_commit_common import _state_invalid


@dataclass(frozen=True)
class PreparedVideoCandidate:
    base_inputs: ProductionDependencyInputs
    candidate_project: LoadedProductionProject
    candidate_registry: AssetRegistrySnapshot
    candidate_inputs: ProductionDependencyInputs
    candidate_graph: DependencyGraphSnapshot
    resolution: DependencyResolution
    candidate_project_pointer: ProjectSnapshotPointer
    candidate_registry_pointer: RegistrySnapshotPointer
    candidate_graph_pointer: DependencyGraphSnapshotPointer
    candidate_shot_path: Path
    candidate_shot_bytes: bytes
    candidate_project_bytes: bytes
    candidate_registry_bytes: bytes
    candidate_graph_bytes: bytes


class VideoCandidatePreparer(Protocol):
    def __call__(
        self,
        base_project: LoadedProductionProject,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        probe_receipt: VideoProbeReceipt,
        provenance: VideoProvenanceReceipt,
        asset_record: AssetRecord,
        continuity_asset_record: AssetRecord | None = None,
    ) -> PreparedVideoCandidate: ...


def _verify_prepared_candidate(candidate: PreparedVideoCandidate) -> None:
    if (
        not candidate.candidate_shot_bytes
        or not candidate.candidate_project_bytes
        or not candidate.candidate_registry_bytes
        or not candidate.candidate_graph_bytes
        or hashlib.sha256(candidate.candidate_project_bytes).hexdigest()
        != candidate.candidate_project_pointer.file_sha256
        or hashlib.sha256(candidate.candidate_registry_bytes).hexdigest()
        != candidate.candidate_registry_pointer.file_sha256
        or hashlib.sha256(candidate.candidate_graph_bytes).hexdigest()
        != candidate.candidate_graph_pointer.file_sha256
    ):
        raise _state_invalid("Video candidate prepared bytes are not exact.")


def resolve_video_activation_dependency_state(
    *,
    graph: DependencyGraphSnapshot,
    base_states: tuple[DependencyNodeState, ...],
    project_pointer: ProjectSnapshotPointer,
    registry_pointer: RegistrySnapshotPointer,
    target_shot_id: str,
    output_asset_id: str,
    continuity_asset_id: str | None = None,
) -> DependencyResolution:
    """Apply the exact generated asset and target visual in a restart-safe form."""

    desired = desired_fingerprints(graph)
    node_by_id = {item.node_id: item for item in graph.nodes}
    visual_node_id = shot_projection_node_id(
        target_shot_id, DependencySemanticRole.VISUAL.value
    )
    asset_ids = [asset_node_id(output_asset_id)]
    if continuity_asset_id is not None:
        asset_ids.append(asset_node_id(continuity_asset_id))
    if visual_node_id not in node_by_id or any(
        node_id not in node_by_id for node_id in asset_ids
    ):
        raise _state_invalid("Video activation target dependency nodes are missing.")
    seeds = [
        item
        for item in base_states
        if item.node_id not in {visual_node_id, *asset_ids}
    ]
    owned_nodes = [(visual_node_id, project_pointer, "project_snapshot")]
    owned_nodes.extend(
        (node_id, registry_pointer, "registry_snapshot")
        for node_id in asset_ids
    )
    for node_id, pointer, owner in owned_nodes:
        node = node_by_id[node_id]
        evidence = (
            ProjectDependencyEvidence(
                owner=owner,
                pointer=pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node_id],
            )
            if owner == "project_snapshot"
            else RegistryDependencyEvidence(
                owner=owner,
                pointer=pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node_id],
            )
        )
        seeds.append(
            DependencyNodeState(
                node_id=node_id,
                graph_revision_id=graph.revision_id,
                desired_fingerprint=desired[node_id],
                applied_fingerprint=desired[node_id],
                lifecycle=DependencyLifecycle.FRESH,
                applied_evidence=evidence,
            )
        )
    return resolve_dependency_state(
        graph,
        tuple(sorted(seeds, key=lambda item: item.node_id)),
    )


def validate_video_activation_candidate(
    *,
    base_project: LoadedProductionProject,
    request: ResolvedVideoGenerationRequest,
    asset_record: AssetRecord,
    continuity_asset_record: AssetRecord | None,
    prepared: PreparedVideoCandidate,
) -> PreparedVideoCandidate:
    scope = request.activation_scope
    if scope is None:
        raise _state_invalid("Video activation request has no durable authoring scope.")
    original = scope.request
    if (
        original.base_project != base_project.manifest.active_project
        or original.base_registry != base_project.manifest.active_registry
        or original.base_dependency_graph
        != base_project.manifest.active_dependency_graph
        or prepared.base_inputs.project != base_project
    ):
        raise _state_invalid("Video activation base identity is not exact.")
    base_shots = {item.shot_id: item for item in base_project.shots}
    next_shots = {item.shot_id: item for item in prepared.candidate_project.shots}
    base_shot = base_shots.get(original.target_shot_id)
    if (
        base_shot is None
        or base_shot.revision != original.target_shot_revision
        or base_shot.content_hash != original.target_shot_content_hash
        or set(base_shots) != set(next_shots)
    ):
        raise _state_invalid("Video activation target Shot identity is invalid.")
    roles = tuple(
        item
        for item in base_shot.required_asset_roles
        if item.role == original.target_asset_role
    )
    if len(roles) != 1:
        raise _state_invalid("Video activation target role is ambiguous.")
    candidate_shot = next_shots[original.target_shot_id]
    if (
        candidate_shot.revision != base_shot.revision + 1
        or candidate_shot.visual_strategy.value != original.target_visual_strategy
        or not candidate_shot.generated_video_rationale
        or tuple(
            item.asset_ids
            for item in candidate_shot.required_asset_roles
            if item.role == original.target_asset_role
        )
        != ((request.output_asset_id,),)
        or any(
            next_shots[shot_id] != shot
            for shot_id, shot in base_shots.items()
            if shot_id != original.target_shot_id
        )
        or not verify_artifact_hash(candidate_shot)
    ):
        raise _state_invalid("Video candidate changed content outside its sealed scope.")

    base_assets = base_project.registry.assets
    registry = prepared.candidate_registry
    appended_assets = (
        (asset_record, continuity_asset_record)
        if continuity_asset_record is not None
        else (asset_record,)
    )
    if (
        registry.schema_version != "2.2"
        or registry.assets[: len(base_assets)] != base_assets
        or registry.assets[len(base_assets) :] != appended_assets
        or registry_semantic_sha256(registry) != registry.content_hash
        or registry.revision_id != registry.content_hash
    ):
        raise _state_invalid("Video candidate Registry must append one exact asset.")
    candidate = prepared.candidate_project
    if (
        candidate.registry != registry
        or candidate.root != base_project.root
        or candidate.brief != base_project.brief
        or candidate.story != base_project.story
        or candidate.characters != base_project.characters
        or candidate.scenes != base_project.scenes
        or candidate.storyboard != base_project.storyboard
        or candidate.render_state != base_project.render_state
        or not verify_artifact_hash(candidate.project)
        or dict(candidate.asset_paths)
        != {
            **base_project.asset_paths,
            request.output_asset_id: base_project.root / asset_record.artifact_path,
            **(
                {
                    continuity_asset_record.asset_id: (
                        base_project.root / continuity_asset_record.artifact_path
                    )
                }
                if continuity_asset_record is not None
                else {}
            ),
        }
    ):
        raise _state_invalid("Video candidate changed unrelated project content.")
    refs = {item.artifact_id: item for item in candidate.project.artifacts.shots}
    candidate_ref = refs.get(candidate_shot.artifact_id)
    if candidate_ref is None or candidate_ref != ArtifactReference(
        artifact_id=candidate_shot.artifact_id,
        revision=candidate_shot.revision,
        content_hash=candidate_shot.content_hash,
        path=prepared.candidate_shot_path,
    ):
        raise _state_invalid("Video candidate project does not select the target Shot.")

    if not video_candidate_dependency_inputs_are_exact(
        candidate_inputs=prepared.candidate_inputs,
        base_inputs=prepared.base_inputs,
        candidate_project=candidate,
        base_project=base_project,
        target_shot_id=original.target_shot_id,
        target_asset_role=original.target_asset_role,
        output_asset_id=request.output_asset_id,
    ):
        raise _state_invalid("Video candidate dependency inputs are not exact.")
    expected_graph = build_production_dependency_graph(prepared.candidate_inputs)
    expected_resolution = resolve_video_activation_dependency_state(
        graph=expected_graph,
        base_states=base_project.manifest.dependency_states,
        project_pointer=prepared.candidate_project_pointer,
        registry_pointer=prepared.candidate_registry_pointer,
        target_shot_id=original.target_shot_id,
        output_asset_id=request.output_asset_id,
        continuity_asset_id=(
            continuity_asset_record.asset_id
            if continuity_asset_record is not None
            else None
        ),
    )
    if (
        prepared.candidate_graph != expected_graph
        or prepared.resolution != expected_resolution
        or candidate.dependency_graph != expected_graph
        or prepared.candidate_graph_pointer.revision_id != expected_graph.revision_id
        or prepared.candidate_graph_pointer.content_hash != expected_graph.content_hash
        or candidate.manifest.active_project != prepared.candidate_project_pointer
        or candidate.manifest.active_registry != prepared.candidate_registry_pointer
        or candidate.manifest.active_dependency_graph
        != prepared.candidate_graph_pointer
    ):
        raise _state_invalid("Video candidate graph is not exact P5 output.")
    _verify_prepared_candidate(prepared)
    return prepared


__all__ = [
    "PreparedVideoCandidate",
    "VideoCandidatePreparer",
    "resolve_video_activation_dependency_state",
    "validate_video_activation_candidate",
]
