"""Shared creative and Shot dependency projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._dependency_primitives import (
    creative_node_id,
    fingerprint_items,
    fingerprint_value,
    shot_projection_node_id,
)
from ai_video.production.models import (
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
    ProjectSnapshotPointer,
    Shot,
)


@dataclass(frozen=True)
class AuthoringDependencyProjection:
    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]
    shot_projection_ids: dict[tuple[str, DependencySemanticRole], str]


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.DEPENDENCY_GRAPH_INVALID,
        user_message="Dependency graph validation failed.",
        technical_detail=message,
        retryable=False,
    )


def shot_projection_fingerprints(
    shot: Shot,
) -> dict[DependencySemanticRole, str]:
    return {
        DependencySemanticRole.VOICE: fingerprint_value(
            "ai-video-shot-voice/1",
            {
                "dialogue": shot.dialogue,
                "narration": shot.narration,
                "duration_policy": shot.duration_policy.model_dump(mode="json"),
            },
        ),
        DependencySemanticRole.VISUAL: fingerprint_value(
            "ai-video-shot-visual/1",
            {
                "intent": shot.intent,
                "character_ids": shot.character_ids,
                "continuity_constraints": shot.continuity_constraints,
                "visual_strategy": shot.visual_strategy.value,
                "required_asset_roles": tuple(
                    item.model_dump(mode="json") for item in shot.required_asset_roles
                ),
                "motion_directives": tuple(
                    item.model_dump(mode="json") for item in shot.motion_directives
                ),
                "generated_video_rationale": shot.generated_video_rationale,
                "hybrid_layers": tuple(
                    item.model_dump(mode="json") for item in shot.hybrid_layers
                ),
            },
        ),
        DependencySemanticRole.COMPOSITION: fingerprint_value(
            "ai-video-shot-composition/1",
            {
                "scene_id": shot.scene_id,
                "storyboard_beat_id": shot.storyboard_beat_id,
                "duration_policy": shot.duration_policy.model_dump(mode="json"),
                "composition_directives": tuple(
                    item.model_dump(mode="json")
                    for item in shot.composition_directives
                ),
            },
        ),
    }


def build_authoring_dependency_projection(
    project: LoadedProductionProject,
) -> AuthoringDependencyProjection:
    """Build the shared creative/Shot prefix for full and pre-generation DAGs."""

    nodes: list[DependencyNode] = []
    edges: list[DependencyEdge] = []
    node_ids: set[str] = set()

    def add_node(node: DependencyNode) -> None:
        if node.node_id in node_ids:
            raise _invalid("production dependency node identity is ambiguous")
        node_ids.add(node.node_id)
        nodes.append(node)

    def add_edge(
        source_id: str,
        target_id: str,
        reason: DependencyReason,
        key: str,
        value: object,
    ) -> None:
        edges.append(
            DependencyEdge(
                source_node_id=source_id,
                target_node_id=target_id,
                reason=reason,
                contribution=FingerprintContribution(
                    key=key,
                    fingerprint=fingerprint_value(f"ai-video-edge-{key}/1", value),
                ),
            )
        )

    creative = (
        ("brief", project.brief),
        ("story", project.story),
        *(("character", item) for item in project.characters),
        *(("scene", item) for item in project.scenes),
        ("storyboard", project.storyboard),
    )
    creative_ids: dict[tuple[str, str], str] = {}
    for kind, artifact in creative:
        node_id = creative_node_id(kind, artifact.artifact_id)
        creative_ids[(kind, artifact.artifact_id)] = node_id
        add_node(
            DependencyNode(
                node_id=node_id,
                kind=DependencyNodeKind.CREATIVE_ARTIFACT,
                semantic_role=DependencySemanticRole.NONE,
                artifact_id=artifact.artifact_id,
                artifact_revision=artifact.revision,
                contributions=fingerprint_items(
                    **{f"{kind}.semantic": artifact.content_hash}
                ),
            )
        )

    add_edge(
        creative_ids[("brief", project.brief.artifact_id)],
        creative_ids[("story", project.story.artifact_id)],
        DependencyReason.AUTHORING_INPUT,
        "authoring.brief_story",
        project.project.artifacts.brief.model_dump(mode="json"),
    )
    add_edge(
        creative_ids[("story", project.story.artifact_id)],
        creative_ids[("storyboard", project.storyboard.artifact_id)],
        DependencyReason.AUTHORING_INPUT,
        "authoring.story_storyboard",
        project.project.artifacts.story.model_dump(mode="json"),
    )

    character_by_domain_id = {item.character_id: item for item in project.characters}
    scene_by_domain_id = {item.scene_id: item for item in project.scenes}
    storyboard_id = creative_ids[("storyboard", project.storyboard.artifact_id)]
    shot_projection_ids: dict[tuple[str, DependencySemanticRole], str] = {}
    for scene in project.scenes:
        scene_node_id = creative_ids[("scene", scene.artifact_id)]
        for participant_id in scene.participant_ids:
            character = character_by_domain_id[participant_id]
            add_edge(
                creative_ids[("character", character.artifact_id)],
                scene_node_id,
                DependencyReason.AUTHORING_INPUT,
                "authoring.character_scene",
                {"character_id": participant_id, "scene_id": scene.scene_id},
            )

    for shot in project.shots:
        projections = shot_projection_fingerprints(shot)
        for role, fingerprint in projections.items():
            node_id = shot_projection_node_id(shot.shot_id, role.value)
            shot_projection_ids[(shot.shot_id, role)] = node_id
            add_node(
                DependencyNode(
                    node_id=node_id,
                    kind=DependencyNodeKind.CREATIVE_ARTIFACT,
                    semantic_role=role,
                    artifact_id=shot.artifact_id,
                    artifact_revision=shot.revision,
                    contributions=fingerprint_items(
                        **{f"shot.{role.value}": fingerprint}
                    ),
                )
            )
        scene = scene_by_domain_id[shot.scene_id]
        add_edge(
            creative_ids[("scene", scene.artifact_id)],
            shot_projection_ids[(shot.shot_id, DependencySemanticRole.VISUAL)],
            DependencyReason.AUTHORING_INPUT,
            "authoring.scene_visual",
            {"scene_id": shot.scene_id, "shot_id": shot.shot_id},
        )
        add_edge(
            storyboard_id,
            shot_projection_ids[(shot.shot_id, DependencySemanticRole.COMPOSITION)],
            DependencyReason.AUTHORING_INPUT,
            "authoring.storyboard_composition",
            {"beat_id": shot.storyboard_beat_id, "shot_id": shot.shot_id},
        )

    return AuthoringDependencyProjection(
        nodes=tuple(nodes),
        edges=tuple(edges),
        shot_projection_ids=shot_projection_ids,
    )


def rebase_authoring_dependency_graph(
    *,
    existing_graph: DependencyGraphSnapshot,
    previous_project: LoadedProductionProject,
    candidate_project: LoadedProductionProject,
) -> DependencyGraphSnapshot:
    """Replace the creative prefix without retiring registered asset nodes.

    A strategy materialization changes the Project's Shot authoring before a
    new CompositionSpec exists.  The old render-domain graph must therefore be
    retired, while immutable registered assets remain available to a later
    composition owner.  Lifecycle is intentionally not assigned here: the
    dependency resolver derives stale, blocked, and superseded states from the
    returned graph and the prior Manifest states.
    """
    # Local import avoids a module import cycle: dependency.py consumes this
    # projection module to build normal P5 graphs.
    from ai_video.production.dependency import build_dependency_graph

    previous = build_authoring_dependency_projection(previous_project)
    candidate = build_authoring_dependency_projection(candidate_project)
    old_by_id = {node.node_id: node for node in previous.nodes}
    new_by_id = {node.node_id: node for node in candidate.nodes}

    # A node with the same stable ID but changed contribution represents a new
    # immutable creative version.  Its previous descendants cannot continue as
    # the active composition/render unit.
    replaced_authoring_ids = {
        node_id
        for node_id, old_node in old_by_id.items()
        if new_by_id.get(node_id) != old_node
    }
    outgoing: dict[str, list[str]] = {}
    for edge in existing_graph.edges:
        outgoing.setdefault(edge.source_node_id, []).append(edge.target_node_id)

    affected: set[str] = set()
    pending = sorted(replaced_authoring_ids)
    while pending:
        node_id = pending.pop()
        if node_id in affected:
            continue
        affected.add(node_id)
        pending.extend(outgoing.get(node_id, ()))

    existing_by_id = {node.node_id: node for node in existing_graph.nodes}
    retired_non_assets = {
        node_id
        for node_id in affected
        if node_id in existing_by_id
        and existing_by_id[node_id].kind is not DependencyNodeKind.ASSET
    }
    old_authoring_ids = set(old_by_id)
    retained_nodes = tuple(
        node
        for node in existing_graph.nodes
        if node.node_id not in old_authoring_ids
        and node.node_id not in retired_non_assets
    )
    retained_ids = {node.node_id for node in retained_nodes}
    unchanged_authoring_ids = {node_id for node_id, node in old_by_id.items()
                               if new_by_id.get(node_id) == node}
    surviving_ids = retained_ids | unchanged_authoring_ids
    retained_edges = tuple(
        edge
        for edge in existing_graph.edges
        if edge.source_node_id in surviving_ids and edge.target_node_id in surviving_ids
        and (edge.source_node_id in retained_ids or edge.target_node_id in retained_ids)
    )
    return build_dependency_graph(
        nodes=(*retained_nodes, *candidate.nodes),
        edges=(*retained_edges, *candidate.edges),
    )


def build_authoring_project_evidence_states(
    *,
    graph: DependencyGraphSnapshot,
    projection: AuthoringDependencyProjection,
    project_pointer: ProjectSnapshotPointer,
    desired: Mapping[str, str],
) -> tuple[DependencyNodeState, ...]:
    """Bind current creative nodes to the exact candidate Project snapshot.

    This is the authoring counterpart of the Project evidence construction in
    ``build_applied_dependency_evidence``.  It is deliberately limited to
    immutable creative artifacts; asset and render states remain owned by their
    existing evidence paths.
    """
    graph_nodes = {node.node_id: node for node in graph.nodes}
    states: list[DependencyNodeState] = []
    for projected in projection.nodes:
        node = graph_nodes.get(projected.node_id)
        fingerprint = desired.get(projected.node_id)
        if node != projected or fingerprint is None:
            raise _invalid("candidate authoring projection is not present in the graph")
        states.append(
            DependencyNodeState(
                node_id=node.node_id,
                graph_revision_id=graph.revision_id,
                desired_fingerprint=fingerprint,
                applied_fingerprint=fingerprint,
                lifecycle=DependencyLifecycle.FRESH,
                applied_evidence=ProjectDependencyEvidence(
                    owner="project_snapshot",
                    pointer=project_pointer,
                    artifact_id=node.artifact_id,
                    artifact_fingerprint=fingerprint,
                ),
            )
        )
    return tuple(sorted(states, key=lambda state: state.node_id))
