"""Pure active Shot projection checks for historical project evidence."""

from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.dependency import (
    _shot_projection_fingerprints,
    build_dependency_graph,
    desired_fingerprints,
)
from ai_video.production.models import (
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyNode,
    DependencyNodeState,
    DependencySemanticRole,
    FingerprintContribution,
    LoadedProductionProject,
    ProjectDependencyEvidence,
    Shot,
    StateCommitStatus,
    VersionedArtifact,
)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        retryable=False,
    )


def matching_evidence_artifacts(
    artifacts: tuple[VersionedArtifact, ...], artifact_id: str
) -> tuple[VersionedArtifact, ...]:
    """Return exact artifact/Shot identity matches from reopened project bytes."""

    return tuple(
        artifact
        for artifact in artifacts
        if artifact.artifact_id == artifact_id
        or (isinstance(artifact, Shot) and artifact.shot_id == artifact_id)
    )


def historical_origin_graph_pointer(
    bundle: LoadedProductionProject,
    evidence: ProjectDependencyEvidence,
) -> DependencyGraphSnapshotPointer | None:
    """Select the unique durable graph provenance for historical evidence."""

    if evidence.pointer.revision >= bundle.manifest.active_project.revision:
        return None
    attempts = tuple(
        attempt
        for attempt in bundle.manifest.attempts
        if attempt.status is StateCommitStatus.SUCCEEDED
        and attempt.base_project == evidence.pointer
        and attempt.candidate_project is not None
        and attempt.candidate_project.revision > evidence.pointer.revision
        and attempt.base_dependency_graph is not None
        and attempt.candidate_dependency_graph is not None
    )
    if len(attempts) != 1:
        raise _invalid("Historical Shot dependency evidence provenance is invalid.")
    return attempts[0].base_dependency_graph


def verify_active_shot_projection_evidence(
    bundle: LoadedProductionProject,
    evidence: ProjectDependencyEvidence,
    node: DependencyNode,
    graph: DependencyGraphSnapshot | None,
    state: DependencyNodeState | None,
    origin: Shot,
    origin_graph: DependencyGraphSnapshot | None,
) -> None:
    """Verify exact historical applied identity against one active Shot node."""

    if node.semantic_role not in SHOT_PROJECTION_ROLES:
        raise _invalid("Shot dependency evidence semantic role is invalid.")
    if graph is None or state is None or origin_graph is None:
        raise _invalid("Active Shot dependency evidence requires graph state.")
    active_nodes = tuple(item for item in graph.nodes if item.node_id == node.node_id)
    active_desired = desired_fingerprints(graph)
    if (
        len(active_nodes) != 1
        or active_nodes[0] != node
        or state.node_id != node.node_id
        or state.graph_revision_id != graph.revision_id
        or state.desired_fingerprint != active_desired[node.node_id]
        or state.applied_evidence != evidence
        or state.applied_fingerprint != evidence.artifact_fingerprint
    ):
        raise _invalid("Shot dependency evidence state binding is invalid.")

    current_matches = tuple(
        current
        for current in bundle.shots
        if current.artifact_id == evidence.artifact_id
        or current.shot_id == evidence.artifact_id
    )
    if len(current_matches) != 1:
        raise _invalid("Current Shot dependency artifact is ambiguous.")
    current = current_matches[0]
    if (
        node.artifact_revision != current.revision
        or evidence.pointer.revision > bundle.manifest.active_project.revision
        or origin.revision > current.revision
        or (
            evidence.pointer.revision == bundle.manifest.active_project.revision
            and evidence.pointer != bundle.manifest.active_project
        )
        or (origin.revision == current.revision and origin != current)
    ):
        raise _invalid("Project dependency evidence chronology is invalid.")

    key = f"shot.{node.semantic_role.value}"
    current_expected = {
        key: _shot_projection_fingerprints(current)[node.semantic_role]
    }
    contributions = {item.key: item.fingerprint for item in node.contributions}
    if contributions != current_expected:
        raise _invalid("Project dependency evidence projection is invalid.")

    origin_expected = {key: _shot_projection_fingerprints(origin)[node.semantic_role]}
    origin_node = node.model_copy(
        update={
            "artifact_revision": origin.revision,
            "contributions": tuple(
                FingerprintContribution(key=item_key, fingerprint=fingerprint)
                for item_key, fingerprint in sorted(origin_expected.items())
            ),
        }
    )
    historical_nodes = tuple(
        item for item in origin_graph.nodes if item.node_id == node.node_id
    )
    if (
        len(historical_nodes) != 1
        or historical_nodes[0] != origin_node
        or desired_fingerprints(origin_graph).get(node.node_id)
        != evidence.artifact_fingerprint
    ):
        raise _invalid("Historical Shot dependency evidence is invalid.")
    hypothetical_graph = build_dependency_graph(
        tuple(
            origin_node if item.node_id == node.node_id else item
            for item in graph.nodes
        ),
        graph.edges,
    )
    # A changed local projection must still bind under the current incoming
    # desired dependencies. An unchanged projection may instead use its exact
    # durable origin graph when an upstream dependency moved.
    if (
        desired_fingerprints(hypothetical_graph)[node.node_id]
        != evidence.artifact_fingerprint
        and origin_expected != current_expected
    ):
        raise _invalid("Historical Shot dependency evidence is invalid.")


def verify_active_versioned_artifact_evidence(
    bundle: LoadedProductionProject,
    evidence: ProjectDependencyEvidence,
    node: DependencyNode,
    graph: DependencyGraphSnapshot | None,
    state: DependencyNodeState | None,
    origin: VersionedArtifact,
    current: VersionedArtifact,
    origin_graph: DependencyGraphSnapshot | None,
) -> None:
    """Verify current and historical Character/Scene applied evidence exactly."""

    if graph is None or state is None or origin_graph is None:
        raise _invalid("Active project dependency evidence requires graph state.")
    kind = node.node_id.split(":", 2)[1] if ":" in node.node_id else ""
    key = f"{kind}.semantic"
    current_expected = {key: current.content_hash}
    contributions = {item.key: item.fingerprint for item in node.contributions}
    active_nodes = tuple(item for item in graph.nodes if item.node_id == node.node_id)
    if (
        len(active_nodes) != 1
        or active_nodes[0] != node
        or state.node_id != node.node_id
        or state.graph_revision_id != graph.revision_id
        or state.desired_fingerprint != desired_fingerprints(graph)[node.node_id]
        or state.applied_evidence != evidence
        or state.applied_fingerprint != evidence.artifact_fingerprint
        or node.artifact_revision != current.revision
        or contributions != current_expected
        or evidence.pointer.revision > bundle.manifest.active_project.revision
        or origin.revision > current.revision
        or (
            evidence.pointer.revision == bundle.manifest.active_project.revision
            and evidence.pointer != bundle.manifest.active_project
        )
        or (origin.revision == current.revision and origin != current)
    ):
        raise _invalid("Project dependency evidence state binding is invalid.")
    origin_nodes = tuple(item for item in origin_graph.nodes if item.node_id == node.node_id)
    if (
        len(origin_nodes) != 1
        or origin_nodes[0].artifact_revision != origin.revision
        or {item.key: item.fingerprint for item in origin_nodes[0].contributions}
        != {key: origin.content_hash}
        or desired_fingerprints(origin_graph).get(node.node_id)
        != evidence.artifact_fingerprint
    ):
        raise _invalid("Historical project dependency evidence is invalid.")
SHOT_PROJECTION_ROLES = frozenset(
    {
        DependencySemanticRole.VOICE,
        DependencySemanticRole.VISUAL,
        DependencySemanticRole.COMPOSITION,
    }
)
