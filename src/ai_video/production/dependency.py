"""Pure immutable dependency graph resolver.

This module owns typed DAG construction, deterministic desired
fingerprints, Manifest lifecycle propagation, and selective rebuild
decisions. It must remain free of filesystem writes, network access,
and runtime side effects. ``ProductionStateCommitter`` is the unique
owner of durable graph write, activation, and explicit recovery.

Public surface:

* :func:`dependency_graph_semantic_sha256`
* :func:`build_dependency_graph`
* :func:`desired_fingerprints`
* :func:`resolve_dependency_state`
* :func:`select_rebuild_nodes`
* :func:`canonical_dependency_graph_snapshot_path` (re-exported from
  :mod:`ai_video.production.paths`)
* Node ID grammar helpers: :func:`creative_node_id`,
  :func:`shot_projection_node_id`, :func:`asset_node_id`,
  :func:`composition_node_id`, :func:`timeline_node_id`,
  :func:`renderer_source_node_id`, :func:`render_node_id`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
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
)
from ai_video.production.paths import canonical_dependency_graph_snapshot_path

__all__ = [
    "DependencyResolution",
    "RenderExecutionUnit",
    "SelectiveRebuildDecision",
    "asset_node_id",
    "build_dependency_graph",
    "canonical_dependency_graph_snapshot_path",
    "composition_node_id",
    "creative_node_id",
    "dependency_graph_semantic_sha256",
    "desired_fingerprints",
    "render_node_id",
    "renderer_source_node_id",
    "resolve_dependency_state",
    "select_rebuild_nodes",
    "shot_projection_node_id",
    "timeline_node_id",
]


# Module-level constant probed by the mtime-independence test. Importing
# ``time.time`` here keeps ``_EPOCH`` swappable while ensuring the
# module never reads the clock for production code paths.
_EPOCH: Final[float] = 0.0


# ---------------------------------------------------------------------------
# Canonical node ID helpers (no parsing here; resolver never depends on them)
# ---------------------------------------------------------------------------


def creative_node_id(artifact_kind: str, artifact_id: str) -> str:
    """Return the canonical node id for a non-Shot creative artifact."""

    if not artifact_kind or not artifact_id:
        raise ValueError("creative_node_id requires non-empty kind and id")
    return f"creative:{artifact_kind}:{artifact_id}"


def shot_projection_node_id(shot_id: str, semantic_role: str) -> str:
    """Return the canonical node id for one Shot semantic projection."""

    if not shot_id or not semantic_role:
        raise ValueError("shot_projection_node_id requires non-empty shot id and role")
    return f"creative:shot:{shot_id}:{semantic_role}"


def asset_node_id(asset_id: str) -> str:
    """Return the canonical node id for an immutable asset record."""

    if not asset_id:
        raise ValueError("asset_node_id requires non-empty asset id")
    return f"asset:{asset_id}"


def composition_node_id(composition_id: str) -> str:
    """Return the canonical node id for a CompositionSpec."""

    if not composition_id:
        raise ValueError("composition_node_id requires non-empty composition id")
    return f"composition:{composition_id}"


def timeline_node_id(composition_id: str) -> str:
    """Return the canonical node id for a resolved timeline."""

    if not composition_id:
        raise ValueError("timeline_node_id requires non-empty composition id")
    return f"timeline:{composition_id}"


def renderer_source_node_id(composition_id: str) -> str:
    """Return the canonical node id for the renderer source of a composition."""

    if not composition_id:
        raise ValueError("renderer_source_node_id requires non-empty composition id")
    return f"renderer-source:{composition_id}"


def render_node_id(composition_id: str) -> str:
    """Return the canonical node id for the render of a composition."""

    if not composition_id:
        raise ValueError("render_node_id requires non-empty composition id")
    return f"render:{composition_id}"


# ---------------------------------------------------------------------------
# Typed compatibility allowlist
# ---------------------------------------------------------------------------


_EDGE_ALLOWLIST: Final[frozenset[tuple[DependencyNodeKind, DependencySemanticRole, DependencyReason, DependencyNodeKind, DependencySemanticRole]]] = (
    frozenset(
        {
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.NONE, DependencyReason.AUTHORING_INPUT, DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.NONE),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.NONE, DependencyReason.AUTHORING_INPUT, DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.VOICE),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.NONE, DependencyReason.AUTHORING_INPUT, DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.VISUAL),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.NONE, DependencyReason.AUTHORING_INPUT, DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.VOICE, DependencyReason.GENERATION_INPUT, DependencyNodeKind.ASSET, DependencySemanticRole.VOICE),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.VISUAL, DependencyReason.GENERATION_INPUT, DependencyNodeKind.ASSET, DependencySemanticRole.VISUAL),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.VISUAL, DependencyReason.ASSET_BINDING, DependencyNodeKind.ASSET, DependencySemanticRole.VISUAL),
            (DependencyNodeKind.CREATIVE_ARTIFACT, DependencySemanticRole.COMPOSITION, DependencyReason.COMPOSITION_RESOLUTION, DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.VOICE, DependencyReason.AUDIO_SOURCE, DependencyNodeKind.ASSET, DependencySemanticRole.CAPTION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.VOICE, DependencyReason.AUDIO_SOURCE, DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.AUDIO, DependencyReason.AUDIO_SOURCE, DependencyNodeKind.ASSET, DependencySemanticRole.CAPTION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.AUDIO, DependencyReason.AUDIO_SOURCE, DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.CAPTION, DependencyReason.ALIGNMENT_TIMING, DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.CAPTION, DependencyReason.CAPTION_STYLE, DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.ASSET, DependencySemanticRole.VISUAL, DependencyReason.ASSET_BINDING, DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION),
            (DependencyNodeKind.COMPOSITION_SPEC, DependencySemanticRole.COMPOSITION, DependencyReason.COMPOSITION_RESOLUTION, DependencyNodeKind.RESOLVED_TIMELINE, DependencySemanticRole.TIMELINE),
            (DependencyNodeKind.RESOLVED_TIMELINE, DependencySemanticRole.TIMELINE, DependencyReason.TIMELINE_MATERIALIZATION, DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE),
            (DependencyNodeKind.ASSET, DependencySemanticRole.VISUAL, DependencyReason.ASSET_BINDING, DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE),
            (DependencyNodeKind.ASSET, DependencySemanticRole.VOICE, DependencyReason.ASSET_BINDING, DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE),
            (DependencyNodeKind.ASSET, DependencySemanticRole.AUDIO, DependencyReason.ASSET_BINDING, DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE),
            (DependencyNodeKind.ASSET, DependencySemanticRole.CAPTION, DependencyReason.ALIGNMENT_TIMING, DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE),
            (DependencyNodeKind.ASSET, DependencySemanticRole.CAPTION, DependencyReason.CAPTION_STYLE, DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE),
            (DependencyNodeKind.RENDERER_SOURCE, DependencySemanticRole.RENDERER_SOURCE, DependencyReason.RENDER_EXECUTION, DependencyNodeKind.RENDER, DependencySemanticRole.RENDER),
            (DependencyNodeKind.RESOLVED_TIMELINE, DependencySemanticRole.TIMELINE, DependencyReason.RENDER_EXECUTION, DependencyNodeKind.RENDER, DependencySemanticRole.RENDER),
        }
    )
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


def _graph_invalid(message: str, *, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.DEPENDENCY_GRAPH_INVALID,
        user_message="Dependency graph validation failed.",
        technical_detail=detail or message,
        retryable=False,
    )


def _resolution_invalid(message: str, *, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.DEPENDENCY_RESOLUTION_INVALID,
        user_message="Dependency resolution input is invalid.",
        technical_detail=detail or message,
        retryable=False,
    )


# ---------------------------------------------------------------------------
# Internal validation helpers
# ---------------------------------------------------------------------------


def _node_sort_key(node: DependencyNode) -> str:
    return node.node_id


def _edge_sort_key(edge: DependencyEdge) -> tuple[str, str, str, str]:
    return (
        edge.target_node_id,
        edge.source_node_id,
        edge.reason.value,
        edge.contribution.key,
    )


def _canonicalize_nodes(nodes: Iterable[DependencyNode]) -> tuple[DependencyNode, ...]:
    canonical = tuple(sorted(nodes, key=_node_sort_key))
    return canonical


def _canonicalize_edges(edges: Iterable[DependencyEdge]) -> tuple[DependencyEdge, ...]:
    return tuple(sorted(edges, key=_edge_sort_key))


def _topological_order(node_ids: Sequence[str], incoming: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    """Return a deterministic canonical topological order over ``node_ids``.

    ``incoming[node_id]`` is the list of source node ids that point to
    ``node_id``. The result is unique because Kahn's algorithm always
    pops the smallest available id next.
    """

    in_degree: dict[str, int] = {node_id: len(incoming.get(node_id, ())) for node_id in node_ids}
    reverse: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for target, sources in incoming.items():
        for source in sources:
            if source in reverse:
                reverse[source].append(target)
    for key in reverse:
        reverse[key].sort()

    ready: list[str] = sorted([node_id for node_id, degree in in_degree.items() if degree == 0])
    ordered: list[str] = []
    while ready:
        ready.sort()
        node_id = ready.pop(0)
        ordered.append(node_id)
        for successor in reverse.get(node_id, ()):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                ready.append(successor)
    if len(ordered) != len(node_ids):
        raise _graph_invalid(
            "dependency graph contains a cycle",
            detail="graph has a cycle; topological order not possible",
        )
    return tuple(ordered)


def _validate_graph_structure(graph: DependencyGraphSnapshot) -> None:
    if graph.revision_id != graph.content_hash:
        raise _graph_invalid(
            "graph revision_id must equal content_hash",
            detail=f"revision_id={graph.revision_id!r} content_hash={graph.content_hash!r}",
        )
    expected = canonical_sha256(
        {
            "schema_version": graph.schema_version,
            "nodes": _nodes_payload(graph),
            "edges": _edges_payload(graph),
        }
    )
    if graph.revision_id != expected:
        raise _graph_invalid(
            "graph revision_id does not match semantic hash",
            detail=f"revision_id={graph.revision_id!r} expected={expected!r}",
        )
    _validate_graph_semantics(graph.nodes, graph.edges)


def _nodes_payload(graph: DependencyGraphSnapshot) -> tuple[dict, ...]:
    nodes = _canonicalize_nodes(graph.nodes)
    return tuple(_node_payload(node) for node in nodes)


def _edges_payload(graph: DependencyGraphSnapshot) -> tuple[dict, ...]:
    edges = _canonicalize_edges(graph.edges)
    return tuple(_edge_payload(edge) for edge in edges)


def _node_payload(node: DependencyNode) -> dict:
    return {
        "node_id": node.node_id,
        "kind": node.kind.value,
        "semantic_role": node.semantic_role.value,
        "artifact_id": node.artifact_id,
        "artifact_revision": node.artifact_revision,
        "contributions": [
            {"key": item.key, "fingerprint": item.fingerprint}
            for item in node.contributions
        ],
    }


def _edge_payload(edge: DependencyEdge) -> dict:
    return {
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "reason": edge.reason.value,
        "contribution": {
            "key": edge.contribution.key,
            "fingerprint": edge.contribution.fingerprint,
        },
    }


def _validate_graph_semantics(
    nodes: Sequence[DependencyNode],
    edges: Sequence[DependencyEdge],
) -> None:
    node_by_id = {node.node_id: node for node in nodes}
    if len(node_by_id) != len(nodes):
        raise _graph_invalid("dependency graph node IDs must be unique")

    edge_keys = [
        (
            edge.target_node_id,
            edge.source_node_id,
            edge.reason.value,
            edge.contribution.key,
        )
        for edge in edges
    ]
    if len(edge_keys) != len(set(edge_keys)):
        raise _graph_invalid("dependency graph edges must be unique")

    incoming: dict[str, list[str]] = {node_id: [] for node_id in node_by_id}
    source_to_renders: dict[str, list[str]] = {
        node.node_id: []
        for node in nodes
        if node.kind is DependencyNodeKind.RENDERER_SOURCE
    }
    render_to_sources: dict[str, list[str]] = {
        node.node_id: []
        for node in nodes
        if node.kind is DependencyNodeKind.RENDER
    }
    for edge in edges:
        if edge.source_node_id == edge.target_node_id:
            raise _graph_invalid(
                "dependency graph rejected self-edge",
                detail=f"node_id={edge.source_node_id!r}",
            )
        if edge.source_node_id not in node_by_id or edge.target_node_id not in node_by_id:
            raise _graph_invalid(
                "dependency graph edge references missing endpoint",
                detail=(
                    f"source={edge.source_node_id!r} "
                    f"target={edge.target_node_id!r}"
                ),
            )

        source = node_by_id[edge.source_node_id]
        target = node_by_id[edge.target_node_id]
        compatibility = (
            source.kind,
            source.semantic_role,
            edge.reason,
            target.kind,
            target.semantic_role,
        )
        if compatibility not in _EDGE_ALLOWLIST:
            raise _graph_invalid(
                "dependency graph rejected untyped combination",
                detail=(
                    f"source_kind={source.kind.value!r} "
                    f"source_role={source.semantic_role.value!r} "
                    f"reason={edge.reason.value!r} "
                    f"target_kind={target.kind.value!r} "
                    f"target_role={target.semantic_role.value!r}"
                ),
            )
        incoming[target.node_id].append(source.node_id)
        if (
            source.kind is DependencyNodeKind.RENDERER_SOURCE
            and target.kind is DependencyNodeKind.RENDER
            and edge.reason is DependencyReason.RENDER_EXECUTION
        ):
            source_to_renders[source.node_id].append(target.node_id)
            render_to_sources[target.node_id].append(source.node_id)

    _topological_order(sorted(node_by_id), incoming)
    for source_id, render_ids in source_to_renders.items():
        if len(render_ids) != 1:
            raise _graph_invalid(
                "renderer source must bind exactly one render",
                detail=f"source={source_id!r} renders={sorted(render_ids)!r}",
            )
    for render_id, source_ids in render_to_sources.items():
        if len(source_ids) != 1:
            raise _graph_invalid(
                "render must bind exactly one renderer source",
                detail=f"render={render_id!r} sources={sorted(source_ids)!r}",
            )


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def dependency_graph_semantic_sha256(graph: DependencyGraphSnapshot) -> str:
    """Return the canonical semantic hash of ``graph``.

    The hash is independent of ``revision_id``, ``content_hash``,
    filesystem mtime, and the order in which the graph was built. It is
    used both to derive the snapshot's ``revision_id`` and to verify
    that callers do not hand the resolver a tampered graph.
    """

    _validate_graph_structure(graph)
    payload = {
        "schema_version": graph.schema_version,
        "nodes": _nodes_payload(graph),
        "edges": _edges_payload(graph),
    }
    return canonical_sha256(payload)


def build_dependency_graph(
    nodes: Sequence[DependencyNode] | Iterable[DependencyNode],
    edges: Sequence[DependencyEdge] | Iterable[DependencyEdge],
) -> DependencyGraphSnapshot:
    """Construct a canonical, immutable : dependency graph snapshot.

    The builder canonicalizes node and edge order, rejects self-edges,
    dangling endpoints, cycles, and edges whose typed (kind, role,
    reason) combination is not in the allowlist. The resulting
    snapshot has ``revision_id == content_hash ==
    dependency_graph_semantic_sha256(snapshot)``.
    """

    canonical_node_list = _canonicalize_nodes(nodes)
    canonical_edge_list = _canonicalize_edges(edges)
    _validate_graph_semantics(canonical_node_list, canonical_edge_list)

    payload = {
        "schema_version": "2.0",
        "nodes": tuple(_node_payload(node) for node in canonical_node_list),
        "edges": tuple(_edge_payload(edge) for edge in canonical_edge_list),
    }
    revision_id = canonical_sha256(payload)
    snapshot = DependencyGraphSnapshot(
        schema_version="2.0",
        revision_id=revision_id,
        content_hash=revision_id,
        nodes=canonical_node_list,
        edges=canonical_edge_list,
    )
    return snapshot


def desired_fingerprints(graph: DependencyGraphSnapshot) -> MappingProxyType[str, str]:
    """Return the deterministic desired fingerprint for each active node.

    The mapping is canonical (sorted node ids by construction) and
    read-only. Computation uses the canonical topological order of the
    graph and propagates the source's already-computed desired
    fingerprint via the :data:`ai-video-dependency-desired/1` payload
    schema.
    """

    _validate_graph_structure(graph)

    node_ids = sorted(node.node_id for node in graph.nodes)
    incoming_for_topo: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    incoming_edges: dict[str, list[DependencyEdge]] = {node_id: [] for node_id in node_ids}
    for edge in graph.edges:
        incoming_for_topo[edge.target_node_id].append(edge.source_node_id)
        incoming_edges[edge.target_node_id].append(edge)
    topo = _topological_order(node_ids, incoming_for_topo)

    node_by_id = {node.node_id: node for node in graph.nodes}
    desired: dict[str, str] = {}
    for node_id in topo:
        node = node_by_id[node_id]
        node_incoming = sorted(
            incoming_edges[node_id],
            key=lambda edge: (edge.source_node_id, edge.reason.value, edge.contribution.key),
        )
        incoming_payload: list[dict] = []
        for edge in node_incoming:
            incoming_payload.append(
                {
                    "source_node_id": edge.source_node_id,
                    "source_desired_fingerprint": desired[edge.source_node_id],
                    "reason": edge.reason.value,
                    "key": edge.contribution.key,
                    "fingerprint": edge.contribution.fingerprint,
                }
            )
        payload = {
            "schema": "ai-video-dependency-desired/1",
            "node_id": node.node_id,
            "kind": node.kind.value,
            "semantic_role": node.semantic_role.value,
            "contributions": [
                {"key": item.key, "fingerprint": item.fingerprint}
                for item in node.contributions
            ],
            "incoming": incoming_payload,
        }
        desired[node.node_id] = canonical_sha256(payload)
    return MappingProxyType(desired)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyResolution:
    """Immutable resolution of ``graph`` against ``previous`` states."""

    graph: DependencyGraphSnapshot
    states: tuple[DependencyNodeState, ...]
    by_id: MappingProxyType[str, DependencyNodeState]
    ready_node_ids: tuple[str, ...]
    affected_node_ids: tuple[str, ...]
    exact_replay: bool


@dataclass(frozen=True)
class RenderExecutionUnit:
    """A typed, atomic execution unit handed off to a domain owner."""

    name: str
    kind: str
    node_ids: tuple[str, ...]
    ready: bool


@dataclass(frozen=True)
class SelectiveRebuildDecision:
    """Pure decision derived from a :class:`DependencyResolution`."""

    affected_node_ids: tuple[str, ...]
    ready_node_ids: tuple[str, ...]
    execution_units: tuple[RenderExecutionUnit, ...]


# ---------------------------------------------------------------------------
# Resolution internals
# ---------------------------------------------------------------------------


def _coerce_previous(previous: object) -> tuple[DependencyNodeState, ...]:
    if previous is None:
        return ()
    if not isinstance(previous, (tuple, list)):
        raise _resolution_invalid(
            "previous states must be a sequence of DependencyNodeState",
            detail=f"got {type(previous).__name__}",
        )
    states: list[DependencyNodeState] = []
    for index, item in enumerate(previous):
        if not isinstance(item, DependencyNodeState):
            raise _resolution_invalid(
                "previous state at index is not DependencyNodeState",
                detail=f"index={index} type={type(item).__name__}",
            )
        states.append(item)
    return tuple(states)


def _fresh_state(
    node: DependencyNode,
    graph_revision_id: str,
    desired_fingerprint: str,
    previous: DependencyNodeState | None,
) -> DependencyNodeState:
    return DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph_revision_id,
        desired_fingerprint=desired_fingerprint,
        applied_fingerprint=desired_fingerprint,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=previous.applied_evidence if previous is not None else None,
        blocked_by=(),
        error_code=None,
        error_message=None,
    )


def _stale_state(
    node: DependencyNode,
    graph_revision_id: str,
    desired_fingerprint: str,
    previous: DependencyNodeState | None,
) -> DependencyNodeState:
    applied_fingerprint = previous.applied_fingerprint if previous is not None else None
    applied_evidence = previous.applied_evidence if previous is not None else None
    return DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph_revision_id,
        desired_fingerprint=desired_fingerprint,
        applied_fingerprint=applied_fingerprint,
        lifecycle=DependencyLifecycle.STALE,
        applied_evidence=applied_evidence,
        blocked_by=(),
        error_code=None,
        error_message=None,
    )


def _blocked_state(
    node: DependencyNode,
    graph_revision_id: str,
    desired_fingerprint: str,
    previous: DependencyNodeState | None,
    blocked_by: tuple[str, ...],
) -> DependencyNodeState:
    return DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph_revision_id,
        desired_fingerprint=desired_fingerprint,
        applied_fingerprint=previous.applied_fingerprint if previous is not None else None,
        lifecycle=DependencyLifecycle.BLOCKED,
        applied_evidence=previous.applied_evidence if previous is not None else None,
        blocked_by=blocked_by,
        error_code=None,
        error_message=None,
    )


def _superseded_state(previous: DependencyNodeState) -> DependencyNodeState:
    return DependencyNodeState(
        node_id=previous.node_id,
        graph_revision_id=previous.graph_revision_id,
        desired_fingerprint=previous.desired_fingerprint,
        applied_fingerprint=previous.applied_fingerprint,
        lifecycle=DependencyLifecycle.SUPERSEDED,
        applied_evidence=previous.applied_evidence,
        blocked_by=(),
        error_code=None,
        error_message=None,
    )


def _failed_state(
    node: DependencyNode,
    graph_revision_id: str,
    desired_fingerprint: str,
    previous: DependencyNodeState,
) -> DependencyNodeState:
    return DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph_revision_id,
        desired_fingerprint=desired_fingerprint,
        applied_fingerprint=previous.applied_fingerprint,
        lifecycle=DependencyLifecycle.FAILED,
        applied_evidence=previous.applied_evidence,
        blocked_by=(),
        error_code=previous.error_code,
        error_message=previous.error_message,
    )


def resolve_dependency_state(
    graph: DependencyGraphSnapshot,
    previous: Sequence[DependencyNodeState] | Iterable[DependencyNodeState] | None = (),
) -> DependencyResolution:
    """Resolve the immutable Manifest lifecycle for ``graph``.

    Lifecycle rules (six transition rules; the enum still has five
    values):

    * ``fresh``: ``applied_fingerprint == desired_fingerprint`` and the
      previous state carried ``applied_evidence`` and all required
      predecessors are fresh.
    * ``stale``: ``desired != applied`` (or applied is missing) and all
      required predecessors are fresh. Ready frontier.
    * ``failed``: previous state was failed with the same desired
      fingerprint; preserved verbatim. Resolver never auto-retries.
    * ``blocked``: at least one required predecessor is not fresh.
      ``blocked_by`` lists the canonical predecessor ids.
    * ``superseded``: previous state for a node no longer in the active
      graph; preserved with its origin graph revision.
    """

    _validate_graph_structure(graph)
    previous_states = _coerce_previous(previous)

    previous_by_id: dict[str, DependencyNodeState] = {}
    for state in previous_states:
        if state.node_id in previous_by_id:
            raise _resolution_invalid(
                "duplicate previous state for node_id",
                detail=f"node_id={state.node_id!r}",
            )
        previous_by_id[state.node_id] = state

    desired_map = desired_fingerprints(graph)
    node_by_id: dict[str, DependencyNode] = {node.node_id: node for node in graph.nodes}
    active_ids = set(node_by_id)

    incoming_for_topo: dict[str, list[str]] = {node_id: [] for node_id in active_ids}
    for edge in graph.edges:
        incoming_for_topo[edge.target_node_id].append(edge.source_node_id)
    topo = _topological_order(sorted(active_ids), incoming_for_topo)

    new_states: dict[str, DependencyNodeState] = {}
    for node_id in topo:
        node = node_by_id[node_id]
        new_desired = desired_map[node_id]
        prev = previous_by_id.get(node_id)

        predecessor_ids = incoming_for_topo[node_id]
        non_fresh_pred_ids = sorted(
            pred_id
            for pred_id in predecessor_ids
            if new_states[pred_id].lifecycle is not DependencyLifecycle.FRESH
        )
        all_preds_fresh = not non_fresh_pred_ids

        # Rule 5: failed same-desired stays failed (no auto retry).
        if (
            prev is not None
            and prev.lifecycle is DependencyLifecycle.FAILED
            and prev.desired_fingerprint == new_desired
        ):
            new_states[node_id] = _failed_state(node, graph.revision_id, new_desired, prev)
            continue

        if all_preds_fresh:
            # Rule 1: fresh only if applied evidence is present.
            if (
                prev is not None
                and prev.lifecycle is DependencyLifecycle.FRESH
                and prev.applied_fingerprint == new_desired
                and prev.applied_evidence is not None
            ):
                new_states[node_id] = _fresh_state(node, graph.revision_id, new_desired, prev)
                continue
            # Rule 2: stale ready frontier.
            new_states[node_id] = _stale_state(node, graph.revision_id, new_desired, prev)
            continue

        # Rule 4: blocked with canonical blocked_by ids.
        new_states[node_id] = _blocked_state(
            node, graph.revision_id, new_desired, prev, tuple(non_fresh_pred_ids)
        )

    superseded_states: list[DependencyNodeState] = []
    for node_id, prev in previous_by_id.items():
        if node_id in active_ids:
            continue
        superseded_states.append(_superseded_state(prev))

    all_states = sorted(
        list(new_states.values()) + superseded_states,
        key=lambda state: state.node_id,
    )

    affected_ids = sorted(
        state.node_id
        for state in all_states
        if state.node_id in active_ids
        and state.lifecycle in (DependencyLifecycle.STALE, DependencyLifecycle.BLOCKED)
    )

    ready_ids = sorted(
        state.node_id
        for state in new_states.values()
        if state.lifecycle is DependencyLifecycle.STALE
        and all(
            new_states[pred_id].lifecycle is DependencyLifecycle.FRESH
            for pred_id in incoming_for_topo[state.node_id]
        )
    )

    exact_replay = _is_exact_replay(graph, new_states, superseded_states, previous_by_id)

    return DependencyResolution(
        graph=graph,
        states=tuple(all_states),
        by_id=MappingProxyType({state.node_id: state for state in all_states}),
        ready_node_ids=tuple(ready_ids),
        affected_node_ids=tuple(affected_ids),
        exact_replay=exact_replay,
    )


def _is_exact_replay(
    graph: DependencyGraphSnapshot,
    new_active_states: Mapping[str, DependencyNodeState],
    superseded_states: Sequence[DependencyNodeState],
    previous_by_id: Mapping[str, DependencyNodeState],
) -> bool:
    active_ids = {node.node_id for node in graph.nodes}
    superseded_ids = {state.node_id for state in superseded_states}

    for node_id, state in new_active_states.items():
        previous = previous_by_id.get(node_id)
        if previous is None or previous != state:
            return False

    for state in superseded_states:
        previous = previous_by_id.get(state.node_id)
        if previous is None or previous != state:
            return False

    for node_id in previous_by_id:
        if node_id not in active_ids and node_id not in superseded_ids:
            return False
    return True


# ---------------------------------------------------------------------------
# Selective rebuild decisions
# ---------------------------------------------------------------------------


def _source_render_pairs(graph: DependencyGraphSnapshot) -> dict[str, str]:
    pairs: dict[str, str] = {}
    node_by_id = {node.node_id: node for node in graph.nodes}
    for edge in graph.edges:
        if edge.reason is not DependencyReason.RENDER_EXECUTION:
            continue
        source = node_by_id[edge.source_node_id]
        target = node_by_id[edge.target_node_id]
        if (
            source.kind is DependencyNodeKind.RENDERER_SOURCE
            and target.kind is DependencyNodeKind.RENDER
        ):
            pairs[target.node_id] = source.node_id
    return pairs


def select_rebuild_nodes(resolution: DependencyResolution) -> SelectiveRebuildDecision:
    """Translate a :class:`DependencyResolution` into pure rebuild units.

    Atomic rule: a single :class:`RenderExecutionUnit` named
    ``render_with_hyperframes`` covers one ``renderer_source`` node and
    its matching ``render`` node. The unit forms when either node is in
    the ready frontier *and* every *external* predecessor of the
    render node (i.e. every predecessor other than the source itself) is
    fresh. The render node may itself be ``blocked`` because its source
    predecessor is stale; the unit still binds both nodes so the
    renderer applies them atomically.
    """

    _validate_graph_structure(resolution.graph)
    _validate_resolution(resolution)
    graph = resolution.graph
    pairs = _source_render_pairs(graph)

    ready_set = set(resolution.ready_node_ids)
    fresh_states: dict[str, DependencyNodeState] = {
        node_id: state
        for node_id, state in resolution.by_id.items()
        if state.lifecycle is DependencyLifecycle.FRESH
    }

    incoming_for_render: dict[str, tuple[str, ...]] = {node_id: () for node_id in pairs}
    raw_incoming: dict[str, list[str]] = {node_id: [] for node_id in pairs}
    for edge in graph.edges:
        if edge.target_node_id in raw_incoming:
            raw_incoming[edge.target_node_id].append(edge.source_node_id)
    for render_id in pairs:
        incoming_for_render[render_id] = tuple(sorted(raw_incoming[render_id]))

    handled: set[str] = {
        node_id
        for render_id, source_id in pairs.items()
        for node_id in (source_id, render_id)
    }
    units: list[RenderExecutionUnit] = []

    for render_id, source_id in sorted(pairs.items()):
        if source_id not in ready_set and render_id not in ready_set:
            continue
        if any(
            resolution.by_id[node_id].lifecycle is DependencyLifecycle.FAILED
            for node_id in (source_id, render_id)
        ):
            continue
        # The pair is executable atomically only when all of the render's
        # external predecessors (everyone except the source) are fresh.
        external_preds = [
            pred_id for pred_id in incoming_for_render[render_id] if pred_id != source_id
        ]
        if any(fresh_states.get(pred_id) is None for pred_id in external_preds):
            continue
        units.append(
            RenderExecutionUnit(
                name="render_with_hyperframes",
                kind="render_with_hyperframes",
                node_ids=tuple(sorted([source_id, render_id])),
                ready=True,
            )
        )

    node_by_id = {node.node_id: node for node in graph.nodes}
    for node_id in resolution.ready_node_ids:
        if node_id in handled:
            continue
        node = node_by_id[node_id]
        units.append(
            RenderExecutionUnit(
                name=f"{node.kind.value}:{node_id}",
                kind=node.kind.value,
                node_ids=(node_id,),
                ready=True,
            )
        )

    units.sort(key=lambda unit: (unit.kind, unit.node_ids))

    return SelectiveRebuildDecision(
        affected_node_ids=resolution.affected_node_ids,
        ready_node_ids=resolution.ready_node_ids,
        execution_units=tuple(units),
    )


def _validate_resolution(resolution: DependencyResolution) -> None:
    """Reject inconsistent caller-constructed resolution values."""

    active_ids = {node.node_id for node in resolution.graph.nodes}
    state_ids = [state.node_id for state in resolution.states]
    if state_ids != sorted(state_ids) or len(state_ids) != len(set(state_ids)):
        raise _resolution_invalid("resolution states must have unique canonical node ids")

    state_by_id = {state.node_id: state for state in resolution.states}
    if dict(resolution.by_id) != state_by_id:
        raise _resolution_invalid("resolution by_id does not match states")
    if not active_ids.issubset(state_by_id):
        raise _resolution_invalid("resolution is missing active graph node states")

    for node_id, state in state_by_id.items():
        if node_id in active_ids:
            if (
                state.graph_revision_id != resolution.graph.revision_id
                or state.lifecycle is DependencyLifecycle.SUPERSEDED
            ):
                raise _resolution_invalid("active node state is not bound to active graph")
        elif state.lifecycle is not DependencyLifecycle.SUPERSEDED:
            raise _resolution_invalid("inactive node state must be superseded")

    incoming: dict[str, list[str]] = {node_id: [] for node_id in active_ids}
    for edge in resolution.graph.edges:
        incoming[edge.target_node_id].append(edge.source_node_id)
    expected_desired = desired_fingerprints(resolution.graph)
    for node_id in active_ids:
        state = state_by_id[node_id]
        if state.desired_fingerprint != expected_desired[node_id]:
            raise _resolution_invalid("active state desired fingerprint is inconsistent")
        if (
            state.lifecycle is DependencyLifecycle.STALE
            and state.applied_fingerprint == state.desired_fingerprint
        ):
            raise _resolution_invalid("stale state already has desired fingerprint applied")
        non_fresh_predecessors = tuple(
            sorted(
                source_id
                for source_id in incoming[node_id]
                if state_by_id[source_id].lifecycle is not DependencyLifecycle.FRESH
            )
        )
        if state.lifecycle is DependencyLifecycle.BLOCKED:
            if state.blocked_by != non_fresh_predecessors:
                raise _resolution_invalid("blocked state predecessor set is inconsistent")
        elif state.lifecycle in (DependencyLifecycle.FRESH, DependencyLifecycle.STALE):
            if non_fresh_predecessors:
                raise _resolution_invalid("ready state has non-fresh predecessor")

    expected_ready = tuple(
        sorted(
            node_id
            for node_id in active_ids
            if state_by_id[node_id].lifecycle is DependencyLifecycle.STALE
            and all(
                state_by_id[source_id].lifecycle is DependencyLifecycle.FRESH
                for source_id in incoming[node_id]
            )
        )
    )
    expected_affected = tuple(
        sorted(
            node_id
            for node_id in active_ids
            if state_by_id[node_id].lifecycle
            in (DependencyLifecycle.STALE, DependencyLifecycle.BLOCKED)
        )
    )
    if resolution.ready_node_ids != expected_ready:
        raise _resolution_invalid("resolution ready frontier is inconsistent")
    if resolution.affected_node_ids != expected_affected:
        raise _resolution_invalid("resolution affected set is inconsistent")


# Silence the unused-import linter for the re-export helper; the symbol is
# pulled in directly above for callers that prefer ``dependency.canonical_*``.
_ = canonical_dependency_graph_snapshot_path
