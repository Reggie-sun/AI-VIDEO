from __future__ import annotations

from ai_video.production.commercial_reference import ProductReferenceSet
from ai_video.production.dependency import (
    asset_node_id,
    build_dependency_graph,
    creative_node_id,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.models import (
    CommercialSourceApprovalPointer,
    CommercialSourceDependencyEvidence,
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


def _edge_key(edge: DependencyEdge) -> tuple[str, str, str, str]:
    return (
        edge.source_node_id,
        edge.target_node_id,
        edge.reason.value,
        edge.contribution.key,
    )


def extend_commercial_source_dependency_graph(
    graph: DependencyGraphSnapshot,
    *,
    product_reference_set: ProductReferenceSet,
    keyframe_asset_id: str,
    keyframe_sha256: str,
    generated_shot_asset_id: str | None = None,
    generated_shot_fingerprint: str | None = None,
) -> DependencyGraphSnapshot:
    """Add the exact ProductReferenceSet -> keyframe -> Shot visual chain."""

    references = ProductReferenceSet.model_validate(
        product_reference_set.model_dump(mode="python")
    )
    if (generated_shot_asset_id is None) != (generated_shot_fingerprint is None):
        raise ValueError("Generated Shot identity and fingerprint must be provided together")
    for value, label in (
        (keyframe_sha256, "commercial keyframe SHA-256"),
        *((
            (generated_shot_fingerprint, "generated Shot fingerprint"),
        ) if generated_shot_fingerprint is not None else ()),
    ):
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError(f"{label} must be lowercase SHA-256")
    product_set_node_id = creative_node_id(
        "product-reference-set", references.artifact_id
    )
    keyframe_node_id = asset_node_id(keyframe_asset_id)
    generated_node_id = (
        asset_node_id(generated_shot_asset_id)
        if generated_shot_asset_id is not None
        else None
    )
    node_by_id = {item.node_id: item for item in graph.nodes}
    product_asset_node_ids = tuple(
        asset_node_id(binding.asset_id) for binding in references.assets
    )
    if keyframe_node_id in product_asset_node_ids:
        raise ValueError("Commercial keyframe must be distinct from ProductReferenceSet assets")
    missing_registered = tuple(
        node_id
        for node_id in (
            *product_asset_node_ids,
            keyframe_node_id,
            *((generated_node_id,) if generated_node_id is not None else ()),
        )
        if node_id not in node_by_id
    )
    if missing_registered:
        raise ValueError("Commercial dependency inputs must already be registered graph assets")
    additions = [
        DependencyNode(
            node_id=product_set_node_id,
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.VISUAL,
            artifact_id=references.artifact_id,
            artifact_revision=references.revision,
            contributions=(
                FingerprintContribution(
                    key="product_reference_set",
                    fingerprint=references.content_hash,
                ),
            ),
        ),
    ]
    for binding, node_id in zip(references.assets, product_asset_node_ids, strict=True):
        node = node_by_id[node_id]
        if node.artifact_id != binding.asset_id:
            raise ValueError("Product reference graph asset identity is inconsistent")
    keyframe_node = node_by_id[keyframe_node_id]
    if keyframe_node.artifact_id != keyframe_asset_id:
        raise ValueError("Commercial keyframe graph asset identity is inconsistent")
    if generated_node_id is not None:
        generated_node = node_by_id[generated_node_id]
        if generated_node.artifact_id != generated_shot_asset_id:
            raise ValueError("Generated Shot graph asset identity is inconsistent")
    edge_additions = [
        DependencyEdge(
            source_node_id=product_set_node_id,
            target_node_id=keyframe_node_id,
            reason=DependencyReason.GENERATION_INPUT,
            contribution=FingerprintContribution(
                key="product_reference_set",
                fingerprint=references.content_hash,
            ),
        ),
        *(
            DependencyEdge(
                source_node_id=asset_node_id(binding.asset_id),
                target_node_id=keyframe_node_id,
                reason=DependencyReason.GENERATION_INPUT,
                contribution=FingerprintContribution(
                    key=f"product_reference_asset:{binding.asset_id}",
                    fingerprint=binding.asset_sha256,
                ),
            )
            for binding in references.assets
        ),
        *(
            (
                DependencyEdge(
                    source_node_id=keyframe_node_id,
                    target_node_id=generated_node_id,
                    reason=DependencyReason.GENERATION_INPUT,
                    contribution=FingerprintContribution(
                        key="approved_commercial_keyframe",
                        fingerprint=keyframe_sha256,
                    ),
                ),
            )
            if generated_node_id is not None
            else ()
        ),
    ]
    for node in additions:
        current = node_by_id.get(node.node_id)
        if current is not None and current != node:
            raise ValueError(
                f"Commercial dependency node {node.node_id!r} collides with different truth"
            )
        node_by_id[node.node_id] = node
    edge_by_key = {_edge_key(item): item for item in graph.edges}
    for edge in edge_additions:
        key = _edge_key(edge)
        current = edge_by_key.get(key)
        if current is not None and current != edge:
            raise ValueError("Commercial dependency edge collides with different truth")
        edge_by_key[key] = edge
    return build_dependency_graph(node_by_id.values(), edge_by_key.values())


def validate_commercial_source_dependency_graph(
    graph: DependencyGraphSnapshot,
    *,
    product_reference_set: ProductReferenceSet,
    keyframe_asset_id: str,
    keyframe_sha256: str,
) -> None:
    """Require the exact registered ProductReferenceSet -> keyframe prefix."""

    expected = extend_commercial_source_dependency_graph(
        graph,
        product_reference_set=product_reference_set,
        keyframe_asset_id=keyframe_asset_id,
        keyframe_sha256=keyframe_sha256,
    )
    if expected != graph:
        raise ValueError("Commercial dependency graph is missing the exact source chain")


def resolve_commercial_source_approval_states(
    graph: DependencyGraphSnapshot,
    previous_states: tuple[DependencyNodeState, ...],
    *,
    approval: CommercialSourceApprovalPointer,
    product_reference_set: ProductReferenceSet,
    keyframe_asset_id: str,
) -> tuple[DependencyNodeState, ...]:
    """Apply one exact approval as evidence for its source-chain nodes."""

    references = ProductReferenceSet.model_validate(
        product_reference_set.model_dump(mode="python")
    )
    desired = desired_fingerprints(graph)
    node_by_id = {item.node_id: item for item in graph.nodes}
    product_node_id = creative_node_id(
        "product-reference-set", references.artifact_id
    )
    keyframe_node_id = asset_node_id(keyframe_asset_id)
    applied_states: list[DependencyNodeState] = [
        item
        for item in previous_states
        if item.node_id not in {product_node_id, keyframe_node_id}
    ]
    for node_id in (product_node_id, keyframe_node_id):
        node = node_by_id.get(node_id)
        fingerprint = desired.get(node_id)
        if node is None or fingerprint is None:
            raise ValueError("Commercial approval dependency node is missing")
        applied_states.append(
            DependencyNodeState(
                node_id=node_id,
                graph_revision_id=graph.revision_id,
                desired_fingerprint=fingerprint,
                applied_fingerprint=fingerprint,
                lifecycle=DependencyLifecycle.FRESH,
                applied_evidence=CommercialSourceDependencyEvidence(
                    owner="commercial_source_approval",
                    pointer=approval,
                    artifact_id=node.artifact_id,
                    artifact_fingerprint=fingerprint,
                ),
            )
        )
    return resolve_dependency_state(graph, tuple(applied_states)).states
