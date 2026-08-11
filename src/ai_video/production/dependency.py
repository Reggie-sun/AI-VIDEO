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
    AssetRecord,
    AssetSourceKind,
    AssetType,
    CompositionSpec,
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
    RegistryDependencyEvidence,
    RenderDependencyEvidence,
    RendererIdentity,
    RendererSourceReceipt,
    RenderReceipt,
    RenderStateSnapshot,
    ResolvedTimeline,
    Shot,
    StateCommitStatus,
)
from ai_video.production.audio import VoiceGenerationRequest
from ai_video.production.paths import canonical_dependency_graph_snapshot_path

__all__ = [
    "DependencyResolution",
    "AppliedProductionEvidence",
    "ProductionDependencyInputs",
    "RenderExecutionUnit",
    "SelectiveRebuildDecision",
    "asset_node_id",
    "build_dependency_graph",
    "build_applied_dependency_evidence",
    "build_production_dependency_graph",
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
    "voice_semantic_projection_fingerprint",
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
        predecessors = incoming_for_topo[edge.target_node_id]
        if edge.source_node_id not in predecessors:
            predecessors.append(edge.source_node_id)
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
        predecessors = incoming[edge.target_node_id]
        if edge.source_node_id not in predecessors:
            predecessors.append(edge.source_node_id)
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


@dataclass(frozen=True)
class ProductionDependencyInputs:
    project: LoadedProductionProject
    composition_spec: CompositionSpec
    renderer: RendererIdentity
    voice_requests: tuple[VoiceGenerationRequest, ...]
    resolver_contract_fingerprint: str
    source_materializer_contract_fingerprint: str
    render_contract_fingerprint: str
    caption_style_fingerprints: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class AppliedProductionEvidence:
    timeline: ResolvedTimeline | None = None
    source_receipt: RendererSourceReceipt | None = None
    render_receipt: RenderReceipt | None = None
    render_state: RenderStateSnapshot | None = None


def voice_semantic_projection_fingerprint(request: VoiceGenerationRequest) -> str:
    """Hash only immutable voice semantics, excluding authorization lifecycle."""

    return canonical_sha256(
        {
            "schema": "ai-video-voice-semantic/1",
            "provider_kind": request.provider_kind,
            "model_id": request.model_id,
            "audio_kind": request.audio_kind.value,
            "script_hash": request.script_hash,
            "speaker_id": request.speaker_id,
            "voice_id": request.voice_id,
            "language": request.language,
            "output_container": request.output_container,
            "output_codec": request.output_codec,
            "output_sample_rate_hz": request.output_sample_rate_hz,
            "output_channels": request.output_channels,
            "provider_parameters": request.provider_parameters.model_dump(mode="json"),
            "input_artifact_ids": request.input_artifact_ids,
            "input_fingerprint": request.input_fingerprint,
        }
    )


def _fp(schema: str, value: object) -> str:
    return canonical_sha256({"schema": schema, "value": value})


def _items(**values: str) -> tuple[FingerprintContribution, ...]:
    return tuple(
        FingerprintContribution(key=key, fingerprint=fingerprint)
        for key, fingerprint in sorted(values.items())
    )


def _asset_role(asset: AssetRecord) -> DependencySemanticRole:
    if asset.asset_type in {AssetType.IMAGE, AssetType.VIDEO}:
        return DependencySemanticRole.VISUAL
    if asset.asset_type is AssetType.VOICE:
        return DependencySemanticRole.VOICE
    if asset.asset_type in {AssetType.MUSIC, AssetType.SFX}:
        return DependencySemanticRole.AUDIO
    if asset.asset_type is AssetType.CAPTION:
        return DependencySemanticRole.CAPTION
    return DependencySemanticRole.NONE


def _shot_projection_fingerprints(shot: Shot) -> dict[DependencySemanticRole, str]:
    return {
        DependencySemanticRole.VOICE: _fp(
            "ai-video-shot-voice/1",
            {
                "dialogue": shot.dialogue,
                "narration": shot.narration,
                "duration_policy": shot.duration_policy.model_dump(mode="json"),
            },
        ),
        DependencySemanticRole.VISUAL: _fp(
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
        DependencySemanticRole.COMPOSITION: _fp(
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


def build_production_dependency_graph(
    inputs: ProductionDependencyInputs,
) -> DependencyGraphSnapshot:
    """Map verified P2/P3/P4 inputs into a pure desired dependency DAG."""

    project = inputs.project
    spec = inputs.composition_spec
    nodes: list[DependencyNode] = []
    edges: list[DependencyEdge] = []
    node_by_id: dict[str, DependencyNode] = {}

    def add_node(node: DependencyNode) -> None:
        if node.node_id in node_by_id:
            raise _graph_invalid("production dependency node identity is ambiguous")
        node_by_id[node.node_id] = node
        nodes.append(node)

    def add_edge(source_id: str, target_id: str, reason: DependencyReason, key: str, value: object) -> None:
        edges.append(
            DependencyEdge(
                source_node_id=source_id,
                target_node_id=target_id,
                reason=reason,
                contribution=FingerprintContribution(
                    key=key,
                    fingerprint=_fp(f"ai-video-edge-{key}/1", value),
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
                contributions=_items(**{f"{kind}.semantic": artifact.content_hash}),
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
        projections = _shot_projection_fingerprints(shot)
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
                    contributions=_items(**{f"shot.{role.value}": fingerprint}),
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

    requests_by_shot: dict[str, VoiceGenerationRequest] = {}
    for request in inputs.voice_requests:
        matching = [
            shot.shot_id
            for shot in project.shots
            if shot.shot_id in request.input_artifact_ids
            or shot.artifact_id in request.input_artifact_ids
        ]
        if len(matching) != 1 or matching[0] in requests_by_shot:
            raise _graph_invalid("voice request must bind exactly one Shot projection")
        requests_by_shot[matching[0]] = request

    tracks_by_asset = {track.asset_id: track for track in spec.audio_tracks}
    assets_by_id = {asset.asset_id: asset for asset in project.registry.assets}
    caption_bindings_by_asset = {
        binding.caption_asset_id: binding for binding in spec.caption_tracks
    }
    style_fingerprints = dict(inputs.caption_style_fingerprints)
    if len(style_fingerprints) != len(inputs.caption_style_fingerprints):
        raise _graph_invalid("caption style fingerprints must have unique reference IDs")
    for asset in project.registry.assets:
        role = _asset_role(asset)
        track = tracks_by_asset.get(asset.asset_id)
        request = (
            requests_by_shot.get(track.shot_id)
            if track is not None and track.shot_id is not None
            else None
        )
        contribution_values: dict[str, str] = {
            "asset.inputs": _fp(
                "ai-video-asset-inputs/1",
                {
                    "input_artifact_ids": (
                        request.input_artifact_ids
                        if request is not None
                        else asset.input_artifact_ids
                    ),
                    "input_fingerprint": (
                        request.input_fingerprint
                        if request is not None
                        else asset.input_fingerprint
                    ),
                },
            )
        }
        if role is DependencySemanticRole.VOICE and request is not None:
            contribution_values["voice.semantic"] = voice_semantic_projection_fingerprint(request)
        elif role is DependencySemanticRole.CAPTION and asset.caption_metadata is not None:
            metadata = asset.caption_metadata
            binding = caption_bindings_by_asset.get(asset.asset_id)
            contribution_values["caption.timing"] = metadata.timing_fingerprint
            if metadata.style_reference_id is None:
                if binding is not None and binding.style_reference is not None:
                    raise _graph_invalid(
                        "caption metadata and CompositionSpec style identity must match"
                    )
                contribution_values["caption.style"] = _fp(
                    "ai-video-caption-style-none/1", None
                )
            else:
                style_reference = binding.style_reference if binding is not None else None
                if (
                    style_reference is None
                    or style_reference.artifact_id != metadata.style_reference_id
                    or style_reference.content_hash != metadata.style_content_hash
                ):
                    raise _graph_invalid(
                        "caption metadata and CompositionSpec style identity must match"
                    )
                style_fingerprint = style_fingerprints.get(
                    metadata.style_reference_id
                )
                if style_fingerprint is None:
                    raise _graph_invalid(
                        "caption style requires a verified P4 style fingerprint"
                    )
                contribution_values["caption.style"] = style_fingerprint
        else:
            contribution_values["asset.bytes"] = asset.sha256
        if asset.audio_metadata is not None:
            metadata = asset.audio_metadata
            audio_contract = (
                {
                    "audio_kind": request.audio_kind.value,
                    "script_hash": request.script_hash,
                    "voice_id": request.voice_id,
                    "language": request.language,
                    "sample_rate_hz": request.output_sample_rate_hz,
                    "channels": request.output_channels,
                    "input_artifact_ids": request.input_artifact_ids,
                    "input_fingerprint": request.input_fingerprint,
                }
                if request is not None
                else {
                    "audio_kind": metadata.audio_kind.value,
                    "script_hash": metadata.script_hash,
                    "voice_id": metadata.voice_id,
                    "language": metadata.language,
                    "duration_samples": metadata.duration_samples,
                    "sample_rate_hz": metadata.sample_rate_hz,
                    "channels": metadata.channels,
                    "input_artifact_ids": metadata.source.input_artifact_ids,
                    "input_fingerprint": metadata.source.input_fingerprint,
                }
            )
            contribution_values["audio.contract"] = _fp(
                "ai-video-audio-contract/1", audio_contract
            )
        add_node(
            DependencyNode(
                node_id=asset_node_id(asset.asset_id),
                kind=DependencyNodeKind.ASSET,
                semantic_role=role,
                artifact_id=asset.asset_id,
                artifact_revision=None,
                contributions=tuple(
                    FingerprintContribution(key=key, fingerprint=value)
                    for key, value in sorted(contribution_values.items())
                ),
            )
        )

    for shot in project.shots:
        for requirement in shot.required_asset_roles:
            for asset_id in requirement.asset_ids:
                asset = assets_by_id[asset_id]
                if _asset_role(asset) is not DependencySemanticRole.VISUAL:
                    continue
                reason = (
                    DependencyReason.GENERATION_INPUT
                    if asset.source_kind is AssetSourceKind.GENERATED
                    else DependencyReason.ASSET_BINDING
                )
                add_edge(
                    shot_projection_ids[(shot.shot_id, DependencySemanticRole.VISUAL)],
                    asset_node_id(asset_id),
                    reason,
                    "asset.visual_input",
                    {"shot_id": shot.shot_id, "asset_id": asset_id},
                )
    for track in spec.audio_tracks:
        asset = assets_by_id[track.asset_id]
        if track.shot_id is not None and _asset_role(asset) is DependencySemanticRole.VOICE:
            add_edge(
                shot_projection_ids[(track.shot_id, DependencySemanticRole.VOICE)],
                asset_node_id(asset.asset_id),
                DependencyReason.GENERATION_INPUT,
                "voice.request",
                {
                    "shot_id": track.shot_id,
                    "semantic": (
                        voice_semantic_projection_fingerprint(requests_by_shot[track.shot_id])
                        if track.shot_id in requests_by_shot
                        else asset.input_fingerprint
                    ),
                },
            )

    for asset in project.registry.assets:
        if asset.caption_metadata is None:
            continue
        source_id = asset.caption_metadata.source_audio_asset_id
        if source_id in assets_by_id:
            add_edge(
                asset_node_id(source_id),
                asset_node_id(asset.asset_id),
                DependencyReason.AUDIO_SOURCE,
                "caption.audio_source",
                {
                    "source_audio_asset_id": source_id,
                    "source_audio_sha256": asset.caption_metadata.source_audio_sha256,
                },
            )

    composition_id = composition_node_id(spec.composition_id)
    add_node(
        DependencyNode(
            node_id=composition_id,
            kind=DependencyNodeKind.COMPOSITION_SPEC,
            semantic_role=DependencySemanticRole.COMPOSITION,
            artifact_id=spec.artifact_id,
            artifact_revision=spec.revision,
            contributions=_items(
                **{
                    "composition.caption": _fp(
                        "ai-video-composition-caption/1",
                        tuple(item.model_dump(mode="json") for item in spec.caption_tracks),
                    ),
                    "composition.content": spec.content_hash,
                    "composition.delivery": _fp(
                        "ai-video-composition-delivery/1",
                        spec.delivery_profile.model_dump(mode="json"),
                    ),
                    "composition.mix": _fp(
                        "ai-video-composition-mix/1",
                        tuple(item.model_dump(mode="json") for item in spec.audio_tracks),
                    ),
                    "composition.renderer": _fp(
                        "ai-video-composition-renderer/1",
                        spec.requested_renderer.value,
                    ),
                }
            ),
        )
    )
    for shot_id in spec.shot_ids:
        add_edge(
            shot_projection_ids[(shot_id, DependencySemanticRole.COMPOSITION)],
            composition_id,
            DependencyReason.COMPOSITION_RESOLUTION,
            "composition.shot",
            shot_id,
        )
    used_asset_ids = {
        *(layer.asset_id for layer in spec.layers),
        *(track.asset_id for track in spec.audio_tracks),
        *(binding.caption_asset_id for binding in spec.caption_tracks),
    }
    for asset_id in sorted(used_asset_ids):
        asset = assets_by_id[asset_id]
        role = _asset_role(asset)
        reasons = {
            DependencySemanticRole.VISUAL: (DependencyReason.ASSET_BINDING,),
            DependencySemanticRole.VOICE: (DependencyReason.AUDIO_SOURCE,),
            DependencySemanticRole.AUDIO: (DependencyReason.AUDIO_SOURCE,),
            DependencySemanticRole.CAPTION: (
                DependencyReason.ALIGNMENT_TIMING,
                DependencyReason.CAPTION_STYLE,
            ),
        }.get(role, ())
        for reason in reasons:
            add_edge(
                asset_node_id(asset_id),
                composition_id,
                reason,
                f"composition.{reason.value}",
                {"asset_id": asset_id, "reason": reason.value},
            )

    timeline_id = timeline_node_id(spec.composition_id)
    source_id = renderer_source_node_id(spec.composition_id)
    render_id = render_node_id(spec.composition_id)
    add_node(
        DependencyNode(
            node_id=timeline_id,
            kind=DependencyNodeKind.RESOLVED_TIMELINE,
            semantic_role=DependencySemanticRole.TIMELINE,
            artifact_id=spec.composition_id,
            artifact_revision=None,
            contributions=_items(
                **{
                    "renderer.identity": _fp(
                        "ai-video-renderer-identity/1",
                        inputs.renderer.model_dump(mode="json"),
                    ),
                    "timeline.contract": inputs.resolver_contract_fingerprint,
                }
            ),
        )
    )
    add_node(
        DependencyNode(
            node_id=source_id,
            kind=DependencyNodeKind.RENDERER_SOURCE,
            semantic_role=DependencySemanticRole.RENDERER_SOURCE,
            artifact_id=spec.composition_id,
            artifact_revision=None,
            contributions=_items(
                **{
                    "renderer.identity": _fp(
                        "ai-video-renderer-identity/1",
                        inputs.renderer.model_dump(mode="json"),
                    ),
                    "renderer.source.contract": inputs.source_materializer_contract_fingerprint,
                }
            ),
        )
    )
    add_node(
        DependencyNode(
            node_id=render_id,
            kind=DependencyNodeKind.RENDER,
            semantic_role=DependencySemanticRole.RENDER,
            artifact_id=spec.composition_id,
            artifact_revision=None,
            contributions=_items(
                **{
                    "render.contract": inputs.render_contract_fingerprint,
                    "renderer.identity": _fp(
                        "ai-video-renderer-identity/1",
                        inputs.renderer.model_dump(mode="json"),
                    ),
                }
            ),
        )
    )
    add_edge(
        composition_id,
        timeline_id,
        DependencyReason.COMPOSITION_RESOLUTION,
        "timeline.composition",
        spec.content_hash,
    )
    add_edge(
        timeline_id,
        source_id,
        DependencyReason.TIMELINE_MATERIALIZATION,
        "renderer.timeline",
        inputs.resolver_contract_fingerprint,
    )
    for asset_id in sorted(used_asset_ids):
        asset = assets_by_id[asset_id]
        role = _asset_role(asset)
        reasons = {
            DependencySemanticRole.VISUAL: (DependencyReason.ASSET_BINDING,),
            DependencySemanticRole.VOICE: (DependencyReason.ASSET_BINDING,),
            DependencySemanticRole.AUDIO: (DependencyReason.ASSET_BINDING,),
            DependencySemanticRole.CAPTION: (
                DependencyReason.ALIGNMENT_TIMING,
                DependencyReason.CAPTION_STYLE,
            ),
        }.get(role, ())
        for reason in reasons:
            add_edge(
                asset_node_id(asset_id),
                source_id,
                reason,
                f"renderer.{reason.value}",
                {"asset_id": asset_id, "reason": reason.value},
            )
    add_edge(
        source_id,
        render_id,
        DependencyReason.RENDER_EXECUTION,
        "render.source",
        inputs.source_materializer_contract_fingerprint,
    )
    add_edge(
        timeline_id,
        render_id,
        DependencyReason.RENDER_EXECUTION,
        "render.timeline",
        inputs.resolver_contract_fingerprint,
    )
    return build_dependency_graph(nodes, edges)


def build_applied_dependency_evidence(
    inputs: ProductionDependencyInputs,
    applied: AppliedProductionEvidence | None,
) -> tuple[DependencyNodeState, ...]:
    """Build verified applied states separately from desired graph inputs."""

    graph = build_production_dependency_graph(inputs)
    desired = desired_fingerprints(graph)
    project = inputs.project
    active_project_matches = (
        project.manifest.active_project.revision == project.project.revision
        and project.manifest.active_project.content_hash == project.project.content_hash
    )
    active_registry_matches = (
        project.manifest.active_registry.revision_id == project.registry.revision_id
        and project.manifest.active_registry.content_hash == project.registry.content_hash
    )
    request_by_shot: dict[str, VoiceGenerationRequest] = {}
    for request in inputs.voice_requests:
        for shot in project.shots:
            if (
                shot.shot_id in request.input_artifact_ids
                or shot.artifact_id in request.input_artifact_ids
            ):
                request_by_shot[shot.shot_id] = request
    track_by_asset = {
        track.asset_id: track for track in inputs.composition_spec.audio_tracks
    }
    asset_by_id = {asset.asset_id: asset for asset in project.registry.assets}
    states: list[DependencyNodeState] = []
    for node in graph.nodes:
        evidence = None
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT and active_project_matches:
            evidence = ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=project.manifest.active_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            )
        elif node.kind is DependencyNodeKind.ASSET and active_registry_matches:
            asset = asset_by_id[node.artifact_id]
            track = track_by_asset.get(asset.asset_id)
            request = (
                request_by_shot.get(track.shot_id)
                if track is not None and track.shot_id is not None
                else None
            )
            metadata = asset.audio_metadata
            if request is not None:
                matching_attempts = tuple(
                    attempt
                    for attempt in project.manifest.attempts
                    if attempt.status is StateCommitStatus.SUCCEEDED
                    and attempt.voice_request is not None
                    and asset.asset_id in attempt.candidate_audio_asset_ids
                    and attempt.voice_request.request_fingerprint
                    == request.voice_request_fingerprint
                )
                receipt = (
                    matching_attempts[0].voice_request
                    if len(matching_attempts) == 1
                    else None
                )
                if (
                    receipt is None
                    or metadata is None
                    or receipt.script_hash != request.script_hash
                    or receipt.provider_kind != request.provider_kind
                    or receipt.model_id != request.model_id
                    or receipt.voice_id != request.voice_id
                    or receipt.language != request.language
                    or metadata.script_hash != request.script_hash
                    or metadata.voice_id != request.voice_id
                    or metadata.language != request.language
                    or metadata.sample_rate_hz != request.output_sample_rate_hz
                    or metadata.channels != request.output_channels
                    or metadata.source.input_artifact_ids
                    != request.input_artifact_ids
                    or metadata.source.input_fingerprint != request.input_fingerprint
                    or (
                        asset.egress.remote
                        and asset.egress.request_fingerprint
                        != request.voice_request_fingerprint
                    )
                ):
                    continue
            evidence = RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=project.manifest.active_registry,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            )
        if evidence is not None:
            states.append(
                DependencyNodeState(
                    node_id=node.node_id,
                    graph_revision_id=graph.revision_id,
                    desired_fingerprint=desired[node.node_id],
                    applied_fingerprint=desired[node.node_id],
                    lifecycle=DependencyLifecycle.FRESH,
                    applied_evidence=evidence,
                )
            )

    if applied is None or applied.render_state is None:
        return tuple(sorted(states, key=lambda state: state.node_id))
    state = applied.render_state
    pointer = project.manifest.active_render_state
    if pointer is None or project.render_state != state:
        raise _resolution_invalid("applied render state must be the verified active state")
    if state.project != project.manifest.active_project or state.registry != project.manifest.active_registry:
        raise _resolution_invalid("applied render state project or registry identity is stale")
    render_evidence_ids: list[str] = []
    if applied.timeline is not None:
        timeline = applied.timeline
        if (
            timeline.composition_spec_id != inputs.composition_spec.artifact_id
            or timeline.composition_spec_revision != inputs.composition_spec.revision
            or timeline.composition_spec_hash != inputs.composition_spec.content_hash
            or timeline.renderer != inputs.renderer
            or state.timeline_fingerprint != timeline.composition_fingerprint
        ):
            raise _resolution_invalid("applied timeline does not match desired composition")
        render_evidence_ids.extend(
            [
                composition_node_id(inputs.composition_spec.composition_id),
                timeline_node_id(inputs.composition_spec.composition_id),
            ]
        )
    if applied.source_receipt is not None:
        source = applied.source_receipt
        if (
            applied.timeline is None
            or source.timeline_fingerprint != state.timeline_fingerprint
            or source.source_sha256 != state.source_sha256
            or source.source_bundle != state.source_bundle
        ):
            raise _resolution_invalid("applied renderer source receipt does not match state")
        render_evidence_ids.append(renderer_source_node_id(inputs.composition_spec.composition_id))
    if applied.render_receipt is not None:
        receipt = applied.render_receipt
        if (
            applied.source_receipt is None
            or receipt.timeline_fingerprint != state.timeline_fingerprint
            or receipt.source_sha256 != state.source_sha256
            or receipt.source_bundle_sha256 != state.source_bundle_sha256
            or receipt.output_sha256 != state.output.file_sha256
        ):
            raise _resolution_invalid("applied render receipt does not match state")
        render_evidence_ids.append(render_node_id(inputs.composition_spec.composition_id))
    for node_id in render_evidence_ids:
        node = next(node for node in graph.nodes if node.node_id == node_id)
        states.append(
            DependencyNodeState(
                node_id=node_id,
                graph_revision_id=graph.revision_id,
                desired_fingerprint=desired[node_id],
                applied_fingerprint=desired[node_id],
                lifecycle=DependencyLifecycle.FRESH,
                applied_evidence=RenderDependencyEvidence(
                    owner="render_state",
                    pointer=pointer,
                    artifact_id=node.artifact_id,
                    artifact_fingerprint=desired[node_id],
                ),
            )
        )
    return tuple(sorted(states, key=lambda state: state.node_id))


# Silence the unused-import linter for the re-export helper; the symbol is
# pulled in directly above for callers that prefer ``dependency.canonical_*``.
_ = canonical_dependency_graph_snapshot_path
