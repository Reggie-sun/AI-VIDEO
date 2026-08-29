"""Truthful asset-free dependency readiness for one generated-video Shot."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_video.production._dependency_authoring import (
    build_authoring_dependency_projection,
)
from ai_video.production._dependency_primitives import (
    fingerprint_items as _items,
    fingerprint_value as _fp,
    shot_projection_node_id,
)
from ai_video.production.dependency import (
    build_dependency_graph,
    desired_fingerprints,
)
from ai_video.production.models import (
    AssetType,
    DependencyEdge,
    DependencyGraphSnapshot,
    DependencyLifecycle,
    DependencyNode,
    DependencyNodeKind,
    DependencyNodeState,
    DependencyReason,
    DependencySemanticRole,
    FingerprintContribution,
    LoadedProductionProject,
    ProjectDependencyEvidence,
    VisualStrategy,
)
from ai_video.production.video import ResolvedVideoGenerationRequest


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class VideoPreGenerationDependencyInputs:
    project: LoadedProductionProject
    target_shot_id: str
    target_asset_role: str
    requirement_hash: str
    planning_request_hash: str
    verified_projection_hash: str


def generation_target_node_id(shot_id: str, asset_role: str) -> str:
    """Return the canonical pending generation-target node identity."""

    if not shot_id or not asset_role:
        raise ValueError("generation target requires non-empty Shot and asset role")
    return f"generation-target:{shot_id}:{asset_role}"


def _validated_target(inputs: VideoPreGenerationDependencyInputs):
    if any(
        _SHA256.fullmatch(value) is None
        for value in (
            inputs.requirement_hash,
            inputs.planning_request_hash,
            inputs.verified_projection_hash,
        )
    ):
        raise ValueError("pre-generation lineage hashes must be SHA-256 values")
    project = inputs.project
    if (
        project.manifest.active_project.revision != project.project.revision
        or project.manifest.active_project.content_hash != project.project.content_hash
        or project.manifest.active_registry.revision_id != project.registry.revision_id
        or project.manifest.active_registry.content_hash != project.registry.content_hash
    ):
        raise ValueError("pre-generation project and Registry must be active and exact")
    shots = tuple(
        shot for shot in project.shots if shot.shot_id == inputs.target_shot_id
    )
    if len(shots) != 1:
        raise ValueError("pre-generation target Shot identity is ambiguous")
    shot = shots[0]
    roles = tuple(
        role
        for role in shot.required_asset_roles
        if role.role == inputs.target_asset_role
    )
    if (
        shot.visual_strategy is not VisualStrategy.GENERATED_VIDEO
        or len(roles) != 1
        or roles[0].asset_ids
        or roles[0].allowed_asset_types != (AssetType.VIDEO,)
    ):
        raise ValueError(
            "pre-generation target must be one empty generated-video role"
        )
    return shot


def build_video_pre_generation_dependency_graph(
    inputs: VideoPreGenerationDependencyInputs,
) -> DependencyGraphSnapshot:
    """Build one exact pending-video target without inventing media or render state."""

    shot = _validated_target(inputs)
    authoring = build_authoring_dependency_projection(inputs.project)
    target_id = generation_target_node_id(
        inputs.target_shot_id, inputs.target_asset_role
    )
    target = DependencyNode(
        node_id=target_id,
        kind=DependencyNodeKind.GENERATION_TARGET,
        semantic_role=DependencySemanticRole.VISUAL,
        artifact_id=shot.artifact_id,
        artifact_revision=shot.revision,
        contributions=_items(
            **{
                "generation_target.asset_role": _fp(
                    "ai-video-generation-target-asset-role/1",
                    inputs.target_asset_role,
                ),
                "generation_target.planning_request": inputs.planning_request_hash,
                "generation_target.requirement": inputs.requirement_hash,
                "generation_target.verified_projection": inputs.verified_projection_hash,
            }
        ),
    )
    source_id = authoring.shot_projection_ids[
        (inputs.target_shot_id, DependencySemanticRole.VISUAL)
    ]
    edge = DependencyEdge(
        source_node_id=source_id,
        target_node_id=target_id,
        reason=DependencyReason.GENERATION_INPUT,
        contribution=FingerprintContribution(
            key="video.pre_generation_target",
            fingerprint=_fp(
                "ai-video-edge-video.pre_generation_target/1",
                {
                    "shot_id": inputs.target_shot_id,
                    "shot_revision": shot.revision,
                    "shot_content_hash": shot.content_hash,
                    "asset_role": inputs.target_asset_role,
                    "requirement_hash": inputs.requirement_hash,
                },
            ),
        ),
    )
    return build_dependency_graph(
        (*authoring.nodes, target),
        (*authoring.edges, edge),
    )


def build_video_pre_generation_applied_evidence(
    inputs: VideoPreGenerationDependencyInputs,
) -> tuple[DependencyNodeState, ...]:
    """Project only exact current authoring bytes as applied evidence."""

    graph = build_video_pre_generation_dependency_graph(inputs)
    desired = desired_fingerprints(graph)
    pointer = inputs.project.manifest.active_project
    return tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[node.node_id],
            applied_fingerprint=desired[node.node_id],
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            ),
        )
        for node in graph.nodes
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT
    )


def verify_current_video_generation_lineage(
    project: LoadedProductionProject,
    request: ResolvedVideoGenerationRequest,
) -> None:
    """Fail closed before request persistence when current lineage drifted."""

    graph = project.dependency_graph
    targets = (
        ()
        if graph is None
        else tuple(
            node
            for node in graph.nodes
            if node.kind is DependencyNodeKind.GENERATION_TARGET
        )
    )
    if not targets:
        return
    scope = request.activation_scope
    if scope is None:
        raise ValueError("pre-generation request requires an activation scope")
    sealed = scope.request
    if (
        sealed.base_project != project.manifest.active_project
        or sealed.base_registry != project.manifest.active_registry
        or sealed.base_dependency_graph != project.manifest.active_dependency_graph
    ):
        raise ValueError("video request base Project, Registry, or graph is stale")
    shots = tuple(
        shot for shot in project.shots if shot.shot_id == sealed.target_shot_id
    )
    if len(shots) != 1:
        raise ValueError("video request target Shot is not current and unique")
    shot = shots[0]
    roles = tuple(
        role
        for role in shot.required_asset_roles
        if role.role == sealed.target_asset_role
    )
    if (
        sealed.target_shot_revision != shot.revision
        or sealed.target_shot_content_hash != shot.content_hash
        or shot.visual_strategy is not VisualStrategy.GENERATED_VIDEO
        or len(roles) != 1
        or roles[0].asset_ids
        or roles[0].allowed_asset_types != (AssetType.VIDEO,)
    ):
        raise ValueError("video request target Shot or role is stale")

    assert graph is not None
    expected_id = generation_target_node_id(
        sealed.target_shot_id, sealed.target_asset_role
    )
    if len(targets) != 1 or targets[0].node_id != expected_id:
        raise ValueError("active pre-generation target is not exact and unique")
    target = targets[0]
    contributions = {item.key: item.fingerprint for item in target.contributions}
    if (
        sealed.requirement_hash is None
        or target.artifact_id != shot.artifact_id
        or target.artifact_revision != shot.revision
        or contributions.get("generation_target.asset_role")
        != _fp("ai-video-generation-target-asset-role/1", sealed.target_asset_role)
        or contributions.get("generation_target.requirement")
        != sealed.requirement_hash
        or set(contributions)
        != {
            "generation_target.asset_role",
            "generation_target.planning_request",
            "generation_target.requirement",
            "generation_target.verified_projection",
        }
    ):
        raise ValueError("video request does not match the active generation target")
    expected = build_video_pre_generation_dependency_graph(
        VideoPreGenerationDependencyInputs(
            project=project,
            target_shot_id=sealed.target_shot_id,
            target_asset_role=sealed.target_asset_role,
            requirement_hash=sealed.requirement_hash,
            planning_request_hash=contributions[
                "generation_target.planning_request"
            ],
            verified_projection_hash=contributions[
                "generation_target.verified_projection"
            ],
        )
    )
    if graph != expected:
        raise ValueError("active pre-generation graph is not canonical and exact")
    states = tuple(
        state
        for state in project.manifest.dependency_states
        if state.node_id == expected_id
    )
    if (
        len(states) != 1
        or states[0].graph_revision_id != graph.revision_id
        or states[0].desired_fingerprint
        != desired_fingerprints(graph)[expected_id]
        or states[0].lifecycle is not DependencyLifecycle.STALE
        or states[0].applied_evidence is not None
        or states[0].blocked_by
    ):
        raise ValueError("active generation target is not submit-ready")
    active_states = {
        state.node_id: state
        for state in project.manifest.dependency_states
        if state.node_id in {node.node_id for node in graph.nodes}
    }
    if set(active_states) != {node.node_id for node in graph.nodes} or any(
        state.lifecycle is not DependencyLifecycle.FRESH
        for node_id, state in active_states.items()
        if node_id != expected_id
    ):
        raise ValueError("active pre-generation authoring state is not fully fresh")
