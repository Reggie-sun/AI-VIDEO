"""P5 transition preparation for one already-materialized production strategy."""

from __future__ import annotations

import hashlib
from dataclasses import replace

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._dependency_authoring import (
    build_authoring_dependency_projection,
    build_authoring_project_evidence_states,
    rebase_authoring_dependency_graph,
)
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    prepare_dependency_graph_transition,
)
from ai_video.production._state_commit_contracts import PreparedArtifact, StateCommitRequest
from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
from ai_video.production.models import LoadedProductionProject


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.DEPENDENCY_GRAPH_INVALID,
        user_message="Production strategy dependency transition is invalid.",
        technical_detail=detail or message,
        retryable=False,
    )


def prepare_strategy_dependency_transition(
    *,
    base_loaded: LoadedProductionProject,
    candidate_loaded: LoadedProductionProject,
    request: StateCommitRequest,
) -> StateCommitRequest:
    """Attach the sole canonical P5 transition to a strategy project commit.

    The caller supplies the exact in-memory candidate that corresponds to the
    prepared Project/Registry snapshots.  This function has no writer or
    lifecycle authority; it uses the existing resolver and StateCommit helper
    to derive the transition and immutable graph artifact.
    """
    base_graph = base_loaded.dependency_graph
    base_pointer = base_loaded.manifest.active_dependency_graph
    if base_graph is None or base_pointer is None:
        raise _invalid("Production strategy materialization requires an active P5 graph.")
    if request.dependency_graph_transition is not None:
        raise _invalid("Production strategy request already has a dependency transition.")
    if request.expected_manifest_revision != base_loaded.manifest.manifest_revision:
        raise _invalid("Production strategy request Manifest revision is stale.")
    if (
        request.next_project.revision != candidate_loaded.project.revision
        or request.next_project.content_hash != candidate_loaded.project.content_hash
        or request.next_registry.revision_id != candidate_loaded.registry.revision_id
        or request.next_registry.content_hash != candidate_loaded.registry.content_hash
    ):
        raise _invalid("Production strategy candidate does not match its commit snapshots.")

    graph = rebase_authoring_dependency_graph(
        existing_graph=base_graph,
        previous_project=base_loaded,
        candidate_project=candidate_loaded,
    )
    desired = desired_fingerprints(graph)
    authoring_states = build_authoring_project_evidence_states(
        graph=graph,
        projection=build_authoring_dependency_projection(candidate_loaded),
        project_pointer=request.next_project,
        desired=desired,
    )
    previous = {
        state.node_id: state for state in base_loaded.manifest.dependency_states
    }
    previous.update({state.node_id: state for state in authoring_states})
    states = resolve_dependency_state(graph, tuple(previous.values())).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=base_loaded.manifest.manifest_revision,
        base_dependency_graph=base_pointer,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired,
    )
    payload = _canonical_json_bytes(graph)
    artifact = PreparedArtifact(
        relative_path=transition.candidate_dependency_graph.path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    existing = {
        item.relative_path: item
        for item in request.artifacts
    }.get(artifact.relative_path)
    if existing is not None and existing != artifact:
        raise _invalid("Production strategy graph artifact conflicts with the commit request.")
    artifacts = request.artifacts if existing is not None else tuple(sorted(
        (*request.artifacts, artifact), key=lambda item: item.relative_path.as_posix()
    ))
    return replace(
        request,
        artifacts=artifacts,
        dependency_graph_transition=transition,
    )
