"""Pure dependency graph resolver tests.

These tests cover the immutable resolver defined in
``src/ai_video/production/dependency.py``. The module owns typed DAG
construction, deterministic desired fingerprints, Manifest lifecycle
propagation, and selective rebuild decisions. It must remain free of
filesystem writes, network access, and runtime side effects.
"""

from __future__ import annotations

from dataclasses import replace
import socket
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Iterable

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import dependency as dep_mod
from ai_video.production.captions import caption_style_fingerprint
from ai_video.production.audio import (
    AudioKind,
    VoiceGenerationRequest,
    VoiceProviderParameters,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    AudioAssetMetadata,
    AudioChannelLayout,
    AudioLoudnessMetadata,
    AudioSource,
    DependencyEdge,
    DependencyGraphSnapshot,
    DependencyLifecycle,
    DependencyNode,
    DependencyNodeKind,
    DependencyNodeState,
    DependencyReason,
    DependencySemanticRole,
    EgressMetadata,
    FingerprintContribution,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    RegistryDependencyEvidence,
    RegistrySnapshotPointer,
    RenderDependencyEvidence,
    RendererSourceReceipt,
    RenderReceipt,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ResolvedTimeline,
    StateCommitAttempt,
    StateCommitStatus,
    ToolIdentity,
    VoiceRequestReceipt,
)
from production_project_factory import (
    make_p4_composition_fixture,
    make_p5_dependency_inputs,
    make_p5_selective_rebuild_fixture,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64
THREE_HASH = "3" * 64
FOUR_HASH = "4" * 64
FIVE_HASH = "5" * 64
SIX_HASH = "6" * 64
SEVEN_HASH = "7" * 64


# ---------------------------------------------------------------------------
# Local fixture helpers
# ---------------------------------------------------------------------------


def make_project_pointer(content_hash: str = ZERO_HASH) -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash=content_hash,
        file_sha256=ONE_HASH,
    )


def make_registry_pointer(
    *, revision_id: str = ZERO_HASH, file_sha256: str = ONE_HASH
) -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{revision_id}.json"),
        revision_id=revision_id,
        content_hash=revision_id,
        file_sha256=file_sha256,
    )


def make_render_state_pointer(content_hash: str = THREE_HASH) -> RenderStateSnapshotPointer:
    return RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{content_hash}.json"),
        revision=1,
        content_hash=content_hash,
        file_sha256=ZERO_HASH,
    )


def make_node(
    *,
    node_id: str = "creative:story:story-1",
    kind: DependencyNodeKind = DependencyNodeKind.CREATIVE_ARTIFACT,
    semantic_role: DependencySemanticRole = DependencySemanticRole.NONE,
    artifact_id: str = "story-1",
    artifact_revision: int | None = 1,
    contributions: tuple[FingerprintContribution, ...] = (
        FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),
    ),
) -> DependencyNode:
    return DependencyNode(
        node_id=node_id,
        kind=kind,
        semantic_role=semantic_role,
        artifact_id=artifact_id,
        artifact_revision=artifact_revision,
        contributions=contributions,
    )


def make_edge(
    *,
    source_node_id: str,
    target_node_id: str,
    reason: DependencyReason = DependencyReason.AUTHORING_INPUT,
    key: str = "k",
    fingerprint: str = ZERO_HASH,
) -> DependencyEdge:
    return DependencyEdge(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        reason=reason,
        contribution=FingerprintContribution(key=key, fingerprint=fingerprint),
    )


# ---------------------------------------------------------------------------
# Canonical node ID helpers
# ---------------------------------------------------------------------------


def test_canonical_node_id_helpers_match_required_grammar():
    assert dep_mod.creative_node_id("story", "story-1") == "creative:story:story-1"
    assert (
        dep_mod.shot_projection_node_id("shot-1", "voice")
        == "creative:shot:shot-1:voice"
    )
    assert (
        dep_mod.shot_projection_node_id("shot-1", "visual")
        == "creative:shot:shot-1:visual"
    )
    assert (
        dep_mod.shot_projection_node_id("shot-1", "composition")
        == "creative:shot:shot-1:composition"
    )
    assert dep_mod.asset_node_id("voice-1") == "asset:voice-1"
    assert dep_mod.composition_node_id("composition-1") == "composition:composition-1"
    assert dep_mod.timeline_node_id("composition-1") == "timeline:composition-1"
    assert (
        dep_mod.renderer_source_node_id("composition-1")
        == "renderer-source:composition-1"
    )
    assert dep_mod.render_node_id("composition-1") == "render:composition-1"


# ---------------------------------------------------------------------------
# Canonical dependency graph snapshot path
# ---------------------------------------------------------------------------


def test_canonical_dependency_graph_snapshot_path_is_exact():
    path = dep_mod.canonical_dependency_graph_snapshot_path(ZERO_HASH)
    assert path == Path(f"state/dependency_graph.{ZERO_HASH}.json")


def test_canonical_dependency_graph_snapshot_path_rejects_non_sha256():
    with pytest.raises(ValueError):
        dep_mod.canonical_dependency_graph_snapshot_path("not-a-hash")


# ---------------------------------------------------------------------------
# Semantic hash and tamper detection
# ---------------------------------------------------------------------------


def _empty_graph() -> DependencyGraphSnapshot:
    return dep_mod.build_dependency_graph(nodes=(), edges=())


def _self_consistent_snapshot(
    nodes: tuple[DependencyNode, ...],
    edges: tuple[DependencyEdge, ...],
) -> DependencyGraphSnapshot:
    canonical_nodes = tuple(sorted(nodes, key=lambda node: node.node_id))
    canonical_edges = tuple(
        sorted(
            edges,
            key=lambda edge: (
                edge.target_node_id,
                edge.source_node_id,
                edge.reason.value,
                edge.contribution.key,
            ),
        )
    )
    payload = {
        "schema_version": "2.0",
        "nodes": tuple(node.model_dump(mode="json") for node in canonical_nodes),
        "edges": tuple(edge.model_dump(mode="json") for edge in canonical_edges),
    }
    revision_id = canonical_sha256(payload)
    return DependencyGraphSnapshot(
        revision_id=revision_id,
        content_hash=revision_id,
        nodes=canonical_nodes,
        edges=canonical_edges,
    )


def test_dependency_graph_semantic_hash_excludes_identity_fields():
    graph = _empty_graph()
    payload = {
        "schema_version": "2.0",
        "nodes": (),
        "edges": (),
    }
    expected = canonical_sha256(payload)
    assert dep_mod.dependency_graph_semantic_sha256(graph) == expected
    assert graph.revision_id == graph.content_hash == expected


def test_dependency_graph_semantic_hash_is_canonical_path_independent():
    graph_a = _empty_graph()
    graph_b = dep_mod.build_dependency_graph(nodes=(), edges=())
    assert dep_mod.dependency_graph_semantic_sha256(graph_a) == dep_mod.dependency_graph_semantic_sha256(
        graph_b
    )


def test_dependency_graph_semantic_hash_independent_of_input_tuple_order():
    nodes_forward = (
        make_node(node_id="creative:story:story-1"),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    nodes_reverse = (nodes_forward[1], nodes_forward[0])
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
        ),
    )
    graph_forward = dep_mod.build_dependency_graph(nodes_forward, edges)
    graph_reverse = dep_mod.build_dependency_graph(nodes_reverse, edges)
    assert (
        dep_mod.dependency_graph_semantic_sha256(graph_forward)
        == dep_mod.dependency_graph_semantic_sha256(graph_reverse)
    )


def test_dependency_graph_semantic_hash_independent_of_mtime(monkeypatch):
    graph = _empty_graph()
    baseline = dep_mod.dependency_graph_semantic_sha256(graph)
    monkeypatch.setattr(dep_mod, "_EPOCH", 1_700_000_000.0, raising=False)
    assert dep_mod.dependency_graph_semantic_sha256(graph) == baseline


def test_public_functions_reject_tampered_graph():
    tampered = DependencyGraphSnapshot(
        schema_version="2.0",
        revision_id=ONE_HASH,
        content_hash=ONE_HASH,
        nodes=(),
        edges=(),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.desired_fingerprints(tampered)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


@pytest.mark.parametrize("invalid_shape", ["typed", "dangling", "cycle"])
def test_public_functions_reject_self_consistent_semantically_invalid_graph(invalid_shape):
    voice = make_node(
        node_id="creative:shot:shot-1:voice",
        semantic_role=DependencySemanticRole.VOICE,
    )
    visual = make_node(
        node_id="asset:image-1",
        kind=DependencyNodeKind.ASSET,
        semantic_role=DependencySemanticRole.VISUAL,
        artifact_id="image-1",
    )
    if invalid_shape == "typed":
        nodes = (voice, visual)
        edges = (
            make_edge(
                source_node_id=voice.node_id,
                target_node_id=visual.node_id,
                reason=DependencyReason.GENERATION_INPUT,
            ),
        )
    elif invalid_shape == "dangling":
        nodes = (voice,)
        edges = (
            make_edge(
                source_node_id=voice.node_id,
                target_node_id="asset:missing",
                reason=DependencyReason.GENERATION_INPUT,
            ),
        )
    else:
        first = make_node(node_id="creative:story:story-1")
        second = make_node(node_id="creative:story:story-2", artifact_id="story-2")
        nodes = (first, second)
        edges = (
            make_edge(source_node_id=first.node_id, target_node_id=second.node_id),
            make_edge(source_node_id=second.node_id, target_node_id=first.node_id),
        )
    graph = _self_consistent_snapshot(nodes, edges)

    for public_function in (
        dep_mod.dependency_graph_semantic_sha256,
        dep_mod.desired_fingerprints,
    ):
        with pytest.raises(AiVideoError) as exc_info:
            public_function(graph)
        assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


# ---------------------------------------------------------------------------
# Build dependency graph: canonicalization, validation, allowlist
# ---------------------------------------------------------------------------


def test_build_dependency_graph_canonicalizes_node_order():
    nodes = (
        make_node(node_id="creative:story:story-2", artifact_id="story-2"),
        make_node(node_id="creative:story:story-1"),
    )
    graph = dep_mod.build_dependency_graph(nodes, ())
    assert tuple(n.node_id for n in graph.nodes) == (
        "creative:story:story-1",
        "creative:story:story-2",
    )


def test_build_dependency_graph_canonicalizes_edge_order():
    nodes = (
        make_node(node_id="creative:story:story-1"),
        make_node(node_id="creative:story:story-2", artifact_id="story-2"),
        make_node(node_id="creative:story:story-3", artifact_id="story-3"),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-2",
            target_node_id="creative:story:story-3",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
        ),
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    assert tuple((e.source_node_id, e.target_node_id) for e in graph.edges) == (
        ("creative:story:story-1", "creative:story:story-2"),
        ("creative:story:story-2", "creative:story:story-3"),
    )


def test_build_dependency_graph_rejects_self_edge():
    nodes = (make_node(),)
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-1",
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(nodes, edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_rejects_dangling_edge():
    nodes = (make_node(),)
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:scene:scene-99",
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(nodes, edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_rejects_cycle():
    nodes = (
        make_node(node_id="creative:story:story-1"),
        make_node(node_id="creative:story:story-2", artifact_id="story-2"),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
        ),
        make_edge(
            source_node_id="creative:story:story-2",
            target_node_id="creative:story:story-1",
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(nodes, edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_accepts_story_to_storyboard():
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.NONE,
        ),
        make_node(
            node_id="creative:storyboard:storyboard-1",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.NONE,
            artifact_id="storyboard-1",
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:storyboard:storyboard-1",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    assert len(graph.edges) == 1


def test_build_dependency_graph_accepts_scene_to_shot_visual():
    nodes = (
        make_node(
            node_id="creative:scene:scene-1",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.NONE,
            artifact_id="scene-1",
        ),
        make_node(
            node_id="creative:shot:shot-1:visual",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.VISUAL,
            artifact_id="shot-1",
            artifact_revision=None,
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:scene:scene-1",
            target_node_id="creative:shot:shot-1:visual",
            reason=DependencyReason.AUTHORING_INPUT,
            key="scene.body",
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    assert len(graph.edges) == 1


def test_build_dependency_graph_accepts_storyboard_to_shot_composition_authoring_input():
    nodes = (
        make_node(
            node_id="creative:storyboard:storyboard-1",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.NONE,
            artifact_id="storyboard-1",
        ),
        make_node(
            node_id="creative:shot:shot-1:composition",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.COMPOSITION,
            artifact_id="shot-1",
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:storyboard:storyboard-1",
            target_node_id="creative:shot:shot-1:composition",
            reason=DependencyReason.AUTHORING_INPUT,
            key="storyboard.frames",
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    assert len(graph.edges) == 1


def test_build_dependency_graph_rejects_wrong_creative_target_role():
    # creative NONE + AUTHORING_INPUT -> creative TIMELINE is not in the allowlist.
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.NONE,
        ),
        make_node(
            node_id="creative:story:story-2",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.TIMELINE,
            artifact_id="story-2",
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(nodes, edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_rejects_voice_creative_to_visual_asset():
    nodes = (
        make_node(
            node_id="creative:shot:shot-1:voice",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="shot-1",
        ),
        make_node(
            node_id="asset:visual-1",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VISUAL,
            artifact_id="visual-1",
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:shot:shot-1:voice",
            target_node_id="asset:visual-1",
            reason=DependencyReason.GENERATION_INPUT,
            key="voice.semantic",
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(nodes, edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_rejects_untyped_combo_even_with_safe_id_strings():
    # Names look compatible but typed roles are wrong; must be rejected by typed check.
    nodes = (
        make_node(
            node_id="creative:shot:shot-1:voice",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="shot-1",
        ),
        make_node(
            node_id="asset:voice-1",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="voice-1",
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:shot:shot-1:voice",
            target_node_id="asset:voice-1",
            # Wrong reason; should be GENERATION_INPUT.
            reason=DependencyReason.AUDIO_SOURCE,
            key="voice.semantic",
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(nodes, edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_revision_id_equals_content_hash_equals_semantic():
    nodes = (
        make_node(node_id="creative:story:story-1"),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    expected = dep_mod.dependency_graph_semantic_sha256(graph)
    assert graph.revision_id == graph.content_hash == expected


@pytest.mark.parametrize(
    "source_kind,source_role,reason,target_kind,target_role",
    [
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
    ],
)
def test_build_dependency_graph_accepts_full_typed_allowlist(
    source_kind,
    source_role,
    reason,
    target_kind,
    target_role,
):
    # Hand-picked ids/names per slot to satisfy validators without naming collisions.
    if target_kind is DependencyNodeKind.CREATIVE_ARTIFACT and target_role is DependencySemanticRole.VISUAL:
        # Need shot projection (creative:shot:..:visual).
        target_id = "creative:shot:shot-1:visual"
    elif target_kind is DependencyNodeKind.CREATIVE_ARTIFACT and target_role is DependencySemanticRole.COMPOSITION:
        target_id = "creative:shot:shot-1:composition"
    elif target_kind is DependencyNodeKind.CREATIVE_ARTIFACT and target_role is DependencySemanticRole.VOICE:
        target_id = "creative:shot:shot-1:voice"
    elif target_kind is DependencyNodeKind.CREATIVE_ARTIFACT and target_role is DependencySemanticRole.NONE:
        target_id = "creative:story:story-1"
    else:
        target_id = f"{target_kind.value}:k-1"

    if source_kind is DependencyNodeKind.CREATIVE_ARTIFACT and source_role is DependencySemanticRole.VOICE:
        source_id = "creative:shot:shot-1:voice"
    elif source_kind is DependencyNodeKind.CREATIVE_ARTIFACT and source_role is DependencySemanticRole.VISUAL:
        source_id = "creative:shot:shot-1:visual"
    elif source_kind is DependencyNodeKind.CREATIVE_ARTIFACT and source_role is DependencySemanticRole.COMPOSITION:
        source_id = "creative:shot:shot-1:composition"
    elif source_kind is DependencyNodeKind.CREATIVE_ARTIFACT and source_role is DependencySemanticRole.NONE:
        source_id = "creative:story:story-1"
    elif source_kind is DependencyNodeKind.COMPOSITION_SPEC:
        source_id = "composition:composition-1"
    elif source_kind is DependencyNodeKind.RESOLVED_TIMELINE:
        source_id = "timeline:composition-1"
    elif source_kind is DependencyNodeKind.RENDERER_SOURCE:
        source_id = "renderer-source:composition-1"
    elif source_kind is DependencyNodeKind.ASSET:
        if source_role is DependencySemanticRole.VOICE:
            source_id = "asset:voice-1"
        elif source_role is DependencySemanticRole.VISUAL:
            source_id = "asset:visual-1"
        elif source_role is DependencySemanticRole.AUDIO:
            source_id = "asset:audio-1"
        elif source_role is DependencySemanticRole.CAPTION:
            source_id = "asset:caption-1"
        else:
            source_id = "asset:asset-1"
    else:
        source_id = "creative:story:story-1"

    # Skip self-loop collisions when both sides share an identifier shape.
    if source_id == target_id:
        return

    nodes = [
        make_node(node_id=source_id, kind=source_kind, semantic_role=source_role),
        make_node(node_id=target_id, kind=target_kind, semantic_role=target_role, artifact_id=target_id),
    ]
    edges = [
        make_edge(
            source_node_id=source_id,
            target_node_id=target_id,
            reason=reason,
            key="typed",
        ),
    ]
    if (
        target_kind is DependencyNodeKind.RENDER
        and source_kind is not DependencyNodeKind.RENDERER_SOURCE
    ):
        renderer_source = make_node(
            node_id="renderer-source:composition-1",
            kind=DependencyNodeKind.RENDERER_SOURCE,
            semantic_role=DependencySemanticRole.RENDERER_SOURCE,
            artifact_id="composition-1",
        )
        nodes.append(renderer_source)
        edges.append(
            make_edge(
                source_node_id=renderer_source.node_id,
                target_node_id=target_id,
                reason=DependencyReason.RENDER_EXECUTION,
                key="renderer.source.contract",
            )
        )
    if target_kind is DependencyNodeKind.RENDERER_SOURCE:
        render = make_node(
            node_id="render:composition-1",
            kind=DependencyNodeKind.RENDER,
            semantic_role=DependencySemanticRole.RENDER,
            artifact_id="composition-1",
        )
        nodes.append(render)
        edges.append(
            make_edge(
                source_node_id=target_id,
                target_node_id=render.node_id,
                reason=DependencyReason.RENDER_EXECUTION,
                key="renderer.source.contract",
            )
        )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    assert graph.revision_id == graph.content_hash


def test_build_dependency_graph_rejects_render_without_renderer_source():
    timeline = make_node(
        node_id="timeline:composition-1",
        kind=DependencyNodeKind.RESOLVED_TIMELINE,
        semantic_role=DependencySemanticRole.TIMELINE,
        artifact_id="composition-1",
    )
    render = make_node(
        node_id="render:composition-1",
        kind=DependencyNodeKind.RENDER,
        semantic_role=DependencySemanticRole.RENDER,
        artifact_id="composition-1",
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph(
            (timeline, render),
            (
                make_edge(
                    source_node_id=timeline.node_id,
                    target_node_id=render.node_id,
                    reason=DependencyReason.RENDER_EXECUTION,
                ),
            ),
        )
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_build_dependency_graph_rejects_multiple_renderer_sources_for_one_render():
    render = make_node(
        node_id="render:composition-1",
        kind=DependencyNodeKind.RENDER,
        semantic_role=DependencySemanticRole.RENDER,
        artifact_id="composition-1",
    )
    sources = tuple(
        make_node(
            node_id=f"renderer-source:composition-{index}",
            kind=DependencyNodeKind.RENDERER_SOURCE,
            semantic_role=DependencySemanticRole.RENDERER_SOURCE,
            artifact_id=f"composition-{index}",
        )
        for index in (1, 2)
    )
    edges = tuple(
        make_edge(
            source_node_id=source.node_id,
            target_node_id=render.node_id,
            reason=DependencyReason.RENDER_EXECUTION,
            key=f"renderer.source.{index}",
        )
        for index, source in enumerate(sources, start=1)
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_dependency_graph((*sources, render), edges)
    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


# ---------------------------------------------------------------------------
# Desired fingerprints
# ---------------------------------------------------------------------------


def _simple_two_node_graph() -> DependencyGraphSnapshot:
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=ONE_HASH,
        ),
    )
    return dep_mod.build_dependency_graph(nodes, edges)


def test_desired_fingerprints_use_exact_canonical_formula():
    graph = _simple_two_node_graph()
    desired = dep_mod.desired_fingerprints(graph)
    source_node = graph.nodes[0]
    target_node = graph.nodes[1]
    payload_target = {
        "schema": "ai-video-dependency-desired/1",
        "node_id": target_node.node_id,
        "kind": target_node.kind.value,
        "semantic_role": target_node.semantic_role.value,
        "contributions": [
            {"key": "story.body", "fingerprint": ONE_HASH},
        ],
        "incoming": [
            {
                "source_node_id": source_node.node_id,
                "source_desired_fingerprint": desired[source_node.node_id],
                "reason": "authoring_input",
                "key": "story.body",
                "fingerprint": ONE_HASH,
            },
        ],
    }
    expected_target = canonical_sha256(payload_target)
    assert desired[target_node.node_id] == expected_target


def test_desired_fingerprints_is_read_only():
    graph = _simple_two_node_graph()
    desired = dep_mod.desired_fingerprints(graph)
    assert isinstance(desired, MappingProxyType)
    with pytest.raises(TypeError):
        desired["creative:story:story-1"] = "0" * 64  # type: ignore[index]


def test_desired_fingerprints_propagation_stops_when_source_unchanged():
    # Two independent graphs that differ only downstream of an unchanged source
    # produce the same desired fingerprint for the source.
    base_nodes = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    base_edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=ONE_HASH,
        ),
    )
    g1 = dep_mod.build_dependency_graph(base_nodes, base_edges)

    altered_nodes = base_nodes + (
        make_node(
            node_id="creative:story:story-3",
            artifact_id="story-3",
            contributions=(FingerprintContribution(key="story.body", fingerprint=TWO_HASH),),
        ),
    )
    altered_edges = base_edges + (
        make_edge(
            source_node_id="creative:story:story-2",
            target_node_id="creative:story:story-3",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=TWO_HASH,
        ),
    )
    g2 = dep_mod.build_dependency_graph(altered_nodes, altered_edges)

    d1 = dep_mod.desired_fingerprints(g1)
    d2 = dep_mod.desired_fingerprints(g2)
    assert d1["creative:story:story-1"] == d2["creative:story:story-1"]


def test_desired_fingerprints_semantic_role_is_identity():
    graph_a = _simple_two_node_graph()
    desired_a = dep_mod.desired_fingerprints(graph_a)

    # Swap semantic_role on target -> should produce a different desired fingerprint.
    nodes_b = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            semantic_role=DependencySemanticRole.VOICE,
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    edges_b = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=ONE_HASH,
        ),
    )
    graph_b = dep_mod.build_dependency_graph(nodes_b, edges_b)
    desired_b = dep_mod.desired_fingerprints(graph_b)
    assert (
        desired_a["creative:story:story-2"]
        != desired_b["creative:story:story-2"]
    )


def test_desired_fingerprints_dialogue_projection_isolation():
    # Voice node changes its contribution; visual projection node and its asset
    # must keep their desired fingerprints.
    shot_voice_a = make_node(
        node_id="creative:shot:shot-1:voice",
        kind=DependencyNodeKind.CREATIVE_ARTIFACT,
        semantic_role=DependencySemanticRole.VOICE,
        artifact_id="shot-1",
        artifact_revision=None,
        contributions=(FingerprintContribution(key="dialogue", fingerprint=ZERO_HASH),),
    )
    shot_visual = make_node(
        node_id="creative:shot:shot-1:visual",
        kind=DependencyNodeKind.CREATIVE_ARTIFACT,
        semantic_role=DependencySemanticRole.VISUAL,
        artifact_id="shot-1",
        artifact_revision=None,
        contributions=(FingerprintContribution(key="visual", fingerprint=ZERO_HASH),),
    )
    voice_asset = make_node(
        node_id="asset:voice-1",
        kind=DependencyNodeKind.ASSET,
        semantic_role=DependencySemanticRole.VOICE,
        artifact_id="voice-1",
        contributions=(FingerprintContribution(key="voice.semantic", fingerprint=ZERO_HASH),),
    )
    visual_asset = make_node(
        node_id="asset:visual-1",
        kind=DependencyNodeKind.ASSET,
        semantic_role=DependencySemanticRole.VISUAL,
        artifact_id="visual-1",
        contributions=(FingerprintContribution(key="asset.bytes", fingerprint=ZERO_HASH),),
    )
    edges = (
        make_edge(
            source_node_id="creative:shot:shot-1:voice",
            target_node_id="asset:voice-1",
            reason=DependencyReason.GENERATION_INPUT,
            key="voice.semantic",
        ),
        make_edge(
            source_node_id="creative:shot:shot-1:visual",
            target_node_id="asset:visual-1",
            reason=DependencyReason.GENERATION_INPUT,
            key="asset.bytes",
        ),
    )
    graph_a = dep_mod.build_dependency_graph(
        (shot_voice_a, shot_visual, voice_asset, visual_asset),
        edges,
    )
    desired_a = dep_mod.desired_fingerprints(graph_a)

    shot_voice_b = make_node(
        node_id="creative:shot:shot-1:voice",
        kind=DependencyNodeKind.CREATIVE_ARTIFACT,
        semantic_role=DependencySemanticRole.VOICE,
        artifact_id="shot-1",
        artifact_revision=None,
        contributions=(FingerprintContribution(key="dialogue", fingerprint=ONE_HASH),),
    )
    graph_b = dep_mod.build_dependency_graph(
        (shot_voice_b, shot_visual, voice_asset, visual_asset),
        edges,
    )
    desired_b = dep_mod.desired_fingerprints(graph_b)
    assert desired_a["creative:shot:shot-1:voice"] != desired_b["creative:shot:shot-1:voice"]
    assert desired_a["creative:shot:shot-1:visual"] == desired_b["creative:shot:shot-1:visual"]
    assert desired_a["asset:visual-1"] == desired_b["asset:visual-1"]


def test_desired_fingerprints_independent_of_mtime(monkeypatch):
    graph = _simple_two_node_graph()
    baseline = dep_mod.desired_fingerprints(graph)
    monkeypatch.setattr(dep_mod, "_EPOCH", 1_700_000_000.0, raising=False)
    assert dep_mod.desired_fingerprints(graph) == baseline


# ---------------------------------------------------------------------------
# Resolution lifecycle rules
# ---------------------------------------------------------------------------


def _graph_with_two_nodes() -> DependencyGraphSnapshot:
    return _simple_two_node_graph()


def _project_evidence(applied: str) -> ProjectDependencyEvidence:
    return ProjectDependencyEvidence(
        owner="project_snapshot",
        pointer=make_project_pointer(),
        artifact_id="story-1",
        artifact_fingerprint=applied,
    )


def _registry_evidence(applied: str) -> RegistryDependencyEvidence:
    return RegistryDependencyEvidence(
        owner="registry_snapshot",
        pointer=make_registry_pointer(),
        artifact_id="asset-1",
        artifact_fingerprint=applied,
    )


def test_resolve_dependency_state_initial_marks_ready_with_no_predecessors():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    state = resolution.by_id["creative:story:story-1"]
    assert state.lifecycle is DependencyLifecycle.STALE
    assert "creative:story:story-1" in resolution.ready_node_ids
    assert "creative:story:story-1" in resolution.affected_node_ids


def test_resolve_dependency_state_marks_blocked_when_predecessor_stale():
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=ONE_HASH,
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    assert "creative:story:story-2" not in resolution.ready_node_ids
    assert "creative:story:story-2" in resolution.affected_node_ids
    state = resolution.by_id["creative:story:story-2"]
    assert state.lifecycle is DependencyLifecycle.BLOCKED
    assert state.blocked_by == ("creative:story:story-1",)


def test_resolve_dependency_state_blocked_by_is_canonical():
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
        make_node(
            node_id="creative:story:story-3",
            artifact_id="story-3",
            contributions=(FingerprintContribution(key="story.body", fingerprint=TWO_HASH),),
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-2",
            target_node_id="creative:story:story-3",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=TWO_HASH,
        ),
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-3",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=TWO_HASH,
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    state = resolution.by_id["creative:story:story-3"]
    assert state.lifecycle is DependencyLifecycle.BLOCKED
    assert state.blocked_by == ("creative:story:story-1", "creative:story:story-2")


def test_resolve_dependency_state_fresh_is_kept_when_predecessors_fresh():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    previous_state = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired,
        applied_fingerprint=desired,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=_project_evidence(desired),
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_state,))
    new_state = resolution.by_id["creative:story:story-1"]
    assert new_state.lifecycle is DependencyLifecycle.FRESH
    assert new_state.applied_fingerprint == desired
    assert "creative:story:story-1" not in resolution.ready_node_ids
    assert "creative:story:story-1" not in resolution.affected_node_ids


def test_resolve_dependency_state_changed_desired_becomes_stale():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    previous_state = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ONE_HASH,
        applied_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=_project_evidence(ONE_HASH),
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_state,))
    new_state = resolution.by_id["creative:story:story-1"]
    assert new_state.lifecycle is DependencyLifecycle.STALE
    assert new_state.applied_fingerprint == ONE_HASH
    assert new_state.applied_evidence == previous_state.applied_evidence
    assert new_state.desired_fingerprint == desired


def test_resolve_dependency_state_keeps_unrelated_node_fresh_across_graph_revision():
    before = dep_mod.build_dependency_graph(
        (
            make_node(node_id="creative:story:story-1"),
            make_node(node_id="creative:story:story-2", artifact_id="story-2"),
        ),
        (),
    )
    before_desired = dep_mod.desired_fingerprints(before)
    previous = tuple(
        DependencyNodeState(
            node_id=node_id,
            graph_revision_id=before.revision_id,
            desired_fingerprint=fingerprint,
            applied_fingerprint=fingerprint,
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=_project_evidence(fingerprint),
        )
        for node_id, fingerprint in before_desired.items()
    )
    after = dep_mod.build_dependency_graph(
        (
            make_node(
                node_id="creative:story:story-1",
                contributions=(
                    FingerprintContribution(key="story.body", fingerprint=TWO_HASH),
                ),
            ),
            make_node(node_id="creative:story:story-2", artifact_id="story-2"),
        ),
        (),
    )

    resolution = dep_mod.resolve_dependency_state(after, previous)

    assert resolution.by_id["creative:story:story-1"].lifecycle is DependencyLifecycle.STALE
    unchanged = resolution.by_id["creative:story:story-2"]
    assert unchanged.lifecycle is DependencyLifecycle.FRESH
    assert unchanged.graph_revision_id == after.revision_id
    assert resolution.ready_node_ids == ("creative:story:story-1",)
    assert resolution.affected_node_ids == ("creative:story:story-1",)


def test_resolve_dependency_state_same_desired_failed_stays_failed():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    previous_state = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FAILED,
        applied_evidence=None,
        error_code="render_failed",
        error_message="renderer timeout",
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_state,))
    new_state = resolution.by_id["creative:story:story-1"]
    assert new_state.lifecycle is DependencyLifecycle.FAILED
    assert new_state.error_code == "render_failed"
    assert new_state.error_message == "renderer timeout"
    # Failed nodes are not in ready/affected when desired hasn't changed.
    assert "creative:story:story-1" not in resolution.ready_node_ids
    assert "creative:story:story-1" not in resolution.affected_node_ids


def test_resolve_dependency_state_same_desired_failed_survives_unrelated_graph_revision():
    before = dep_mod.build_dependency_graph(
        (
            make_node(node_id="creative:story:story-1"),
            make_node(node_id="creative:story:story-2", artifact_id="story-2"),
        ),
        (),
    )
    desired = dep_mod.desired_fingerprints(before)["creative:story:story-1"]
    failed = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=before.revision_id,
        desired_fingerprint=desired,
        applied_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.FAILED,
        applied_evidence=_project_evidence(ONE_HASH),
        error_code="render_failed",
        error_message="terminal failure",
    )
    after = dep_mod.build_dependency_graph(
        (
            make_node(node_id="creative:story:story-1"),
            make_node(
                node_id="creative:story:story-2",
                artifact_id="story-2",
                contributions=(
                    FingerprintContribution(key="story.body", fingerprint=TWO_HASH),
                ),
            ),
        ),
        (),
    )

    resolution = dep_mod.resolve_dependency_state(after, (failed,))

    retained = resolution.by_id["creative:story:story-1"]
    assert retained.lifecycle is DependencyLifecycle.FAILED
    assert retained.graph_revision_id == after.revision_id
    assert retained.error_code == "render_failed"
    assert "creative:story:story-1" not in resolution.ready_node_ids
    assert "creative:story:story-1" not in resolution.affected_node_ids


def test_resolve_dependency_state_changed_desired_failed_resets_to_stale():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    previous_state = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=ONE_HASH,  # stale desired
        applied_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.FAILED,
        applied_evidence=None,
        error_code="render_failed",
        error_message="renderer timeout",
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_state,))
    new_state = resolution.by_id["creative:story:story-1"]
    # desired changed -> fallback lifecycle rules apply.
    assert new_state.lifecycle in {
        DependencyLifecycle.STALE,
        DependencyLifecycle.BLOCKED,
    }
    assert new_state.error_code is None
    assert new_state.error_message is None


def test_resolve_dependency_state_superseded_for_previous_nodes_not_in_active_graph():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    previous_state = DependencyNodeState(
        node_id="creative:story:story-retired",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ONE_HASH,
        applied_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=_project_evidence(ONE_HASH),
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_state,))
    superseded = resolution.by_id["creative:story:story-retired"]
    assert superseded.lifecycle is DependencyLifecycle.SUPERSEDED
    assert superseded.graph_revision_id == ONE_HASH
    assert superseded.applied_fingerprint == ONE_HASH
    assert superseded not in resolution.ready_node_ids


@pytest.mark.parametrize(
    "lifecycle,extra",
    [
        (DependencyLifecycle.STALE, {}),
        (DependencyLifecycle.BLOCKED, {"blocked_by": ("creative:story:upstream",)}),
        (
            DependencyLifecycle.FAILED,
            {"error_code": "generation_failed", "error_message": "terminal failure"},
        ),
    ],
)
def test_resolve_dependency_state_supersedes_never_applied_nodes(lifecycle, extra):
    previous = DependencyNodeState(
        node_id="creative:story:retired",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=TWO_HASH,
        lifecycle=lifecycle,
        **extra,
    )

    resolution = dep_mod.resolve_dependency_state(_empty_graph(), (previous,))

    superseded = resolution.by_id[previous.node_id]
    assert superseded.lifecycle is DependencyLifecycle.SUPERSEDED
    assert superseded.applied_fingerprint is None
    assert superseded.applied_evidence is None


def test_resolve_dependency_state_same_node_reenters_uses_active_state():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    # Previous superseded entry for the same logical node id.
    superseded_previous = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ONE_HASH,
        applied_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.SUPERSEDED,
        applied_evidence=_project_evidence(ONE_HASH),
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(superseded_previous,))
    # Only one entry for the node id; it must be the active state.
    state = resolution.by_id["creative:story:story-1"]
    assert state.lifecycle in {DependencyLifecycle.STALE, DependencyLifecycle.BLOCKED, DependencyLifecycle.FRESH}
    assert state.desired_fingerprint == desired
    # No duplicate history.
    matches = [s for s in resolution.states if s.node_id == "creative:story:story-1"]
    assert len(matches) == 1


def test_resolve_dependency_state_exact_replay_returns_no_op():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    previous_state = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired,
        applied_fingerprint=desired,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=_project_evidence(desired),
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_state,))
    assert resolution.exact_replay is True
    assert resolution.ready_node_ids == ()
    assert resolution.affected_node_ids == ()


def test_resolve_dependency_state_affected_includes_transitive_blocked():
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
        make_node(
            node_id="creative:story:story-3",
            artifact_id="story-3",
            contributions=(FingerprintContribution(key="story.body", fingerprint=TWO_HASH),),
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=ONE_HASH,
        ),
        make_edge(
            source_node_id="creative:story:story-2",
            target_node_id="creative:story:story-3",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=TWO_HASH,
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    assert "creative:story:story-1" in resolution.affected_node_ids
    assert "creative:story:story-2" in resolution.affected_node_ids
    assert "creative:story:story-3" in resolution.affected_node_ids
    # Ready frontier is only the source.
    assert resolution.ready_node_ids == ("creative:story:story-1",)


def test_resolve_dependency_state_ready_frontier_only_when_predecessor_fresh():
    nodes = (
        make_node(
            node_id="creative:story:story-1",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),),
        ),
        make_node(
            node_id="creative:story:story-2",
            artifact_id="story-2",
            contributions=(FingerprintContribution(key="story.body", fingerprint=ONE_HASH),),
        ),
    )
    edges = (
        make_edge(
            source_node_id="creative:story:story-1",
            target_node_id="creative:story:story-2",
            reason=DependencyReason.AUTHORING_INPUT,
            key="story.body",
            fingerprint=ONE_HASH,
        ),
    )
    graph = dep_mod.build_dependency_graph(nodes, edges)
    desired_source = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    # Caller marked story-1 applied -> previous says source is fresh.
    previous_source = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired_source,
        applied_fingerprint=desired_source,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=_project_evidence(desired_source),
    )
    resolution = dep_mod.resolve_dependency_state(graph, previous=(previous_source,))
    assert resolution.by_id["creative:story:story-1"].lifecycle is DependencyLifecycle.FRESH
    target_state = resolution.by_id["creative:story:story-2"]
    assert target_state.lifecycle is DependencyLifecycle.STALE
    assert resolution.ready_node_ids == ("creative:story:story-2",)


def test_resolve_dependency_state_invalid_previous_state_shape_raises():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.resolve_dependency_state(graph, previous=("not a state",))  # type: ignore[arg-type]
    assert exc_info.value.code is ErrorCode.DEPENDENCY_RESOLUTION_INVALID


def test_resolve_dependency_state_rejects_duplicate_previous_node_ids():
    nodes = (make_node(node_id="creative:story:story-1"),)
    graph = dep_mod.build_dependency_graph(nodes, ())
    desired = dep_mod.desired_fingerprints(graph)["creative:story:story-1"]
    state_a = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired,
        applied_fingerprint=desired,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=_project_evidence(desired),
    )
    state_b = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.resolve_dependency_state(graph, previous=(state_a, state_b))
    assert exc_info.value.code is ErrorCode.DEPENDENCY_RESOLUTION_INVALID


def test_resolve_dependency_state_states_tuple_is_canonical_and_read_only():
    graph = _graph_with_two_nodes()
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    ids = tuple(s.node_id for s in resolution.states)
    assert ids == tuple(sorted(ids))
    # MappingProxyType for by_id
    assert isinstance(resolution.by_id, MappingProxyType)


# ---------------------------------------------------------------------------
# Side-effect isolation
# ---------------------------------------------------------------------------


def test_resolver_does_not_write_filesystem(monkeypatch, tmp_path: Path):
    def _explode(*args: object, **kwargs: object) -> object:
        raise AssertionError("filesystem write attempted")

    monkeypatch.setattr(Path, "write_text", _explode)
    monkeypatch.setattr(Path, "write_bytes", _explode)
    monkeypatch.setattr(Path, "open", _explode)
    graph = _graph_with_two_nodes()
    # Calling the public surface should not trigger any write.
    dep_mod.desired_fingerprints(graph)
    dep_mod.resolve_dependency_state(graph, previous=())


def test_resolver_does_not_open_network(monkeypatch):
    def _explode(*args: object, **kwargs: object) -> object:
        raise AssertionError("network socket attempted")

    monkeypatch.setattr(socket, "socket", _explode)
    monkeypatch.setattr(socket, "create_connection", _explode)
    graph = _graph_with_two_nodes()
    dep_mod.desired_fingerprints(graph)
    dep_mod.resolve_dependency_state(graph, previous=())


def test_resolver_module_does_not_import_side_effecting_modules():
    # The pure resolver must not pull in state_commit, paths internals, or os at module load.
    src = Path(dep_mod.__file__).read_text(encoding="utf-8")
    forbidden = [
        "import state_commit",
        "from ai_video.production.state_commit",
        "from ai_video.production import state_commit",
        "import os",
        "from ai_video.production import paths",
        "from ai_video.production.state_recovery",
    ]
    for token in forbidden:
        assert token not in src, f"dependency.py must not reference {token!r}"


# ---------------------------------------------------------------------------
# Selective rebuild decisions
# ---------------------------------------------------------------------------


def _render_pipeline_graph() -> DependencyGraphSnapshot:
    # composition -> renderer-source -> render (one composition).
    nodes = (
        make_node(
            node_id="composition:composition-1",
            kind=DependencyNodeKind.COMPOSITION_SPEC,
            semantic_role=DependencySemanticRole.COMPOSITION,
            artifact_id="composition-1",
        ),
        make_node(
            node_id="timeline:composition-1",
            kind=DependencyNodeKind.RESOLVED_TIMELINE,
            semantic_role=DependencySemanticRole.TIMELINE,
            artifact_id="composition-1",
        ),
        make_node(
            node_id="renderer-source:composition-1",
            kind=DependencyNodeKind.RENDERER_SOURCE,
            semantic_role=DependencySemanticRole.RENDERER_SOURCE,
            artifact_id="composition-1",
        ),
        make_node(
            node_id="render:composition-1",
            kind=DependencyNodeKind.RENDER,
            semantic_role=DependencySemanticRole.RENDER,
            artifact_id="composition-1",
        ),
    )
    edges = (
        make_edge(
            source_node_id="composition:composition-1",
            target_node_id="timeline:composition-1",
            reason=DependencyReason.COMPOSITION_RESOLUTION,
            key="composition.fingerprint",
        ),
        make_edge(
            source_node_id="timeline:composition-1",
            target_node_id="renderer-source:composition-1",
            reason=DependencyReason.TIMELINE_MATERIALIZATION,
            key="timeline.contract",
        ),
        make_edge(
            source_node_id="renderer-source:composition-1",
            target_node_id="render:composition-1",
            reason=DependencyReason.RENDER_EXECUTION,
            key="renderer.source.contract",
        ),
        make_edge(
            source_node_id="timeline:composition-1",
            target_node_id="render:composition-1",
            reason=DependencyReason.RENDER_EXECUTION,
            key="timeline.contract",
        ),
    )
    return dep_mod.build_dependency_graph(nodes, edges)


def test_select_rebuild_nodes_groups_renderer_source_and_render_as_one_unit():
    graph = _render_pipeline_graph()
    # Caller has applied composition and timeline.
    previous_composition = DependencyNodeState(
        node_id="composition:composition-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=dep_mod.desired_fingerprints(graph)["composition:composition-1"],
        applied_fingerprint=dep_mod.desired_fingerprints(graph)["composition:composition-1"],
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=ProjectDependencyEvidence(
            owner="project_snapshot",
            pointer=make_project_pointer(),
            artifact_id="composition-1",
            artifact_fingerprint=dep_mod.desired_fingerprints(graph)["composition:composition-1"],
        ),
    )
    previous_timeline = DependencyNodeState(
        node_id="timeline:composition-1",
        graph_revision_id=graph.revision_id,
        desired_fingerprint=dep_mod.desired_fingerprints(graph)["timeline:composition-1"],
        applied_fingerprint=dep_mod.desired_fingerprints(graph)["timeline:composition-1"],
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RenderDependencyEvidence(
            owner="render_state",
            pointer=make_render_state_pointer(),
            artifact_id="composition-1",
            artifact_fingerprint=dep_mod.desired_fingerprints(graph)["timeline:composition-1"],
        ),
    )
    resolution = dep_mod.resolve_dependency_state(
        graph, previous=(previous_composition, previous_timeline)
    )
    # renderer-source becomes stale/ready because no previous applied evidence;
    # render is blocked because its source predecessor is stale. The durable
    # render unit includes composition and timeline even when they were fresh,
    # because final activation re-proves all four nodes atomically.
    assert resolution.ready_node_ids == ("renderer-source:composition-1",)
    render_state = resolution.by_id["render:composition-1"]
    assert render_state.lifecycle is DependencyLifecycle.BLOCKED
    decision = dep_mod.select_rebuild_nodes(resolution)
    unit_kinds = tuple(unit.kind for unit in decision.execution_units)
    assert unit_kinds == ("render_with_hyperframes",)
    render_unit = decision.execution_units[0]
    assert render_unit.node_ids == (
        "composition:composition-1",
        "render:composition-1",
        "renderer-source:composition-1",
        "timeline:composition-1",
    )
    assert render_unit.ready is True


def test_select_rebuild_nodes_batches_composition_timeline_and_render_domain():
    graph = _render_pipeline_graph()

    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    decision = dep_mod.select_rebuild_nodes(resolution)

    assert resolution.ready_node_ids == ("composition:composition-1",)
    assert decision.execution_units == (
        dep_mod.RenderExecutionUnit(
            name="render_with_hyperframes",
            kind="render_with_hyperframes",
            node_ids=(
                "composition:composition-1",
                "render:composition-1",
                "renderer-source:composition-1",
                "timeline:composition-1",
            ),
            ready=True,
        ),
    )


def test_select_rebuild_nodes_groups_fresh_source_and_stale_render_atomically():
    before = _render_pipeline_graph()
    desired_before = dep_mod.desired_fingerprints(before)
    previous = tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=before.revision_id,
            desired_fingerprint=desired_before[node.node_id],
            applied_fingerprint=desired_before[node.node_id],
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=_project_evidence(desired_before[node.node_id]),
        )
        for node in before.nodes
    )
    changed_nodes = tuple(
        node.model_copy(
            update={
                "contributions": (
                    FingerprintContribution(
                        key="render.output.contract",
                        fingerprint=TWO_HASH,
                    ),
                )
            }
        )
        if node.node_id == "render:composition-1"
        else node
        for node in before.nodes
    )
    after = dep_mod.build_dependency_graph(changed_nodes, before.edges)

    resolution = dep_mod.resolve_dependency_state(after, previous)
    decision = dep_mod.select_rebuild_nodes(resolution)

    assert resolution.ready_node_ids == ("render:composition-1",)
    assert decision.execution_units == (
        dep_mod.RenderExecutionUnit(
            name="render_with_hyperframes",
            kind="render_with_hyperframes",
            node_ids=(
                "composition:composition-1",
                "render:composition-1",
                "renderer-source:composition-1",
                "timeline:composition-1",
            ),
            ready=True,
        ),
    )


def test_select_rebuild_nodes_never_emits_unpaired_renderer_nodes():
    graph = _render_pipeline_graph()
    resolution = dep_mod.resolve_dependency_state(graph, previous=())

    decision = dep_mod.select_rebuild_nodes(resolution)

    assert all(
        unit.kind not in {"renderer_source", "render"}
        for unit in decision.execution_units
    )


def test_select_rebuild_nodes_does_not_auto_retry_failed_render_pair():
    graph = _render_pipeline_graph()
    desired = dep_mod.desired_fingerprints(graph)
    previous = (
        *tuple(
            DependencyNodeState(
                node_id=node_id,
                graph_revision_id=graph.revision_id,
                desired_fingerprint=desired[node_id],
                applied_fingerprint=desired[node_id],
                lifecycle=DependencyLifecycle.FRESH,
                applied_evidence=_project_evidence(desired[node_id]),
            )
            for node_id in (
                "composition:composition-1",
                "timeline:composition-1",
            )
        ),
        DependencyNodeState(
            node_id="render:composition-1",
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired["render:composition-1"],
            lifecycle=DependencyLifecycle.FAILED,
            error_code="render_failed",
            error_message="terminal failure",
        ),
    )

    resolution = dep_mod.resolve_dependency_state(graph, previous)
    decision = dep_mod.select_rebuild_nodes(resolution)

    assert resolution.ready_node_ids == ("renderer-source:composition-1",)
    assert resolution.by_id["render:composition-1"].lifecycle is DependencyLifecycle.FAILED
    assert decision.execution_units == ()


def test_select_rebuild_nodes_does_not_auto_retry_failed_renderer_source_pair():
    graph = _render_pipeline_graph()
    desired = dep_mod.desired_fingerprints(graph)
    previous = tuple(
        DependencyNodeState(
            node_id=node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[node_id],
            applied_fingerprint=(
                desired[node_id]
                if node_id != "renderer-source:composition-1"
                else None
            ),
            lifecycle=(
                DependencyLifecycle.FAILED
                if node_id == "renderer-source:composition-1"
                else DependencyLifecycle.FRESH
            ),
            applied_evidence=(
                None
                if node_id == "renderer-source:composition-1"
                else _project_evidence(desired[node_id])
            ),
            error_code=(
                "source_failed"
                if node_id == "renderer-source:composition-1"
                else None
            ),
            error_message=(
                "terminal failure"
                if node_id == "renderer-source:composition-1"
                else None
            ),
        )
        for node_id in (
            "composition:composition-1",
            "timeline:composition-1",
            "renderer-source:composition-1",
        )
    )

    resolution = dep_mod.resolve_dependency_state(graph, previous)
    decision = dep_mod.select_rebuild_nodes(resolution)

    assert resolution.ready_node_ids == ()
    assert resolution.by_id["renderer-source:composition-1"].lifecycle is DependencyLifecycle.FAILED
    assert decision.execution_units == ()


def test_select_rebuild_nodes_groups_other_kinds_individually():
    nodes = (
        make_node(node_id="creative:story:story-1"),
        make_node(node_id="asset:voice-1", kind=DependencyNodeKind.ASSET, semantic_role=DependencySemanticRole.VOICE, artifact_id="voice-1"),
        make_node(
            node_id="composition:composition-1",
            kind=DependencyNodeKind.COMPOSITION_SPEC,
            semantic_role=DependencySemanticRole.COMPOSITION,
            artifact_id="composition-1",
        ),
        make_node(
            node_id="timeline:composition-1",
            kind=DependencyNodeKind.RESOLVED_TIMELINE,
            semantic_role=DependencySemanticRole.TIMELINE,
            artifact_id="composition-1",
        ),
    )
    edges = ()
    graph = dep_mod.build_dependency_graph(nodes, edges)
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    decision = dep_mod.select_rebuild_nodes(resolution)
    # Four ready nodes -> four individual execution units.
    assert len(decision.execution_units) == 4
    kinds = sorted({unit.kind for unit in decision.execution_units})
    assert kinds == ["asset", "composition_spec", "creative_artifact", "resolved_timeline"]


def test_select_rebuild_nodes_is_pure():
    graph = _render_pipeline_graph()
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    decision_a = dep_mod.select_rebuild_nodes(resolution)
    decision_b = dep_mod.select_rebuild_nodes(resolution)
    assert decision_a == decision_b


def test_select_rebuild_nodes_preserves_canonical_ids_and_tuples():
    graph = _render_pipeline_graph()
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    decision = dep_mod.select_rebuild_nodes(resolution)
    assert tuple(decision.affected_node_ids) == tuple(sorted(decision.affected_node_ids))
    assert tuple(decision.ready_node_ids) == tuple(sorted(decision.ready_node_ids))
    for unit in decision.execution_units:
        assert tuple(unit.node_ids) == tuple(sorted(unit.node_ids))


def test_select_rebuild_nodes_rejects_tampered_resolution():
    graph = _render_pipeline_graph()
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.select_rebuild_nodes(
            dep_mod.DependencyResolution(
                graph=dep_mod.build_dependency_graph((), ()),
                states=resolution.states,
                by_id=resolution.by_id,
                ready_node_ids=resolution.ready_node_ids,
                affected_node_ids=resolution.affected_node_ids,
                exact_replay=resolution.exact_replay,
            )
        )
    assert exc_info.value.code is ErrorCode.DEPENDENCY_RESOLUTION_INVALID


def test_select_rebuild_nodes_rejects_wrong_desired_fingerprint():
    graph = dep_mod.build_dependency_graph((make_node(),), ())
    resolution = dep_mod.resolve_dependency_state(graph, previous=())
    forged_state = resolution.states[0].model_copy(
        update={"desired_fingerprint": ONE_HASH}
    )
    forged = dep_mod.DependencyResolution(
        graph=graph,
        states=(forged_state,),
        by_id=MappingProxyType({forged_state.node_id: forged_state}),
        ready_node_ids=resolution.ready_node_ids,
        affected_node_ids=resolution.affected_node_ids,
        exact_replay=False,
    )

    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.select_rebuild_nodes(forged)

    assert exc_info.value.code is ErrorCode.DEPENDENCY_RESOLUTION_INVALID


# ---------------------------------------------------------------------------
# Production P2/P3/P4 input mapping
# ---------------------------------------------------------------------------


def _production_node(graph, node_id):
    return next(node for node in graph.nodes if node.node_id == node_id)


def _production_contributions(graph, node_id):
    return {
        item.key: item.fingerprint
        for item in _production_node(graph, node_id).contributions
    }


def _copy_voice_request(request, **updates):
    excluded = {
        "script_hash",
        "provider_parameters_hash",
        "voice_request_fingerprint",
    }
    data = {
        field_name: getattr(request, field_name)
        for field_name in type(request).model_fields
        if field_name not in excluded
    }
    data.update(updates)
    return type(request).create(**data)


def test_production_graph_maps_p4_nodes_edges_without_timing_derivation(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)

    graph = dep_mod.build_production_dependency_graph(inputs)

    assert _production_node(graph, "creative:shot:shot-1:voice").semantic_role is DependencySemanticRole.VOICE
    assert _production_node(graph, "asset:voice-dialogue").semantic_role is DependencySemanticRole.VOICE
    assert _production_node(graph, "asset:caption-asset-1").semantic_role is DependencySemanticRole.CAPTION
    assert _production_node(graph, "composition:main").kind is DependencyNodeKind.COMPOSITION_SPEC
    assert _production_node(graph, "timeline:main").kind is DependencyNodeKind.RESOLVED_TIMELINE
    assert "timeline.contract" in _production_contributions(graph, "timeline:main")
    assert not hasattr(graph, "total_frames")
    assert not hasattr(graph, "total_samples")
    edge_index = {
        (edge.source_node_id, edge.target_node_id, edge.reason)
        for edge in graph.edges
    }
    assert (
        "creative:shot:shot-1:voice",
        "asset:voice-dialogue",
        DependencyReason.GENERATION_INPUT,
    ) in edge_index
    assert (
        "asset:voice-dialogue",
        "asset:caption-asset-1",
        DependencyReason.AUDIO_SOURCE,
    ) in edge_index
    assert (
        "renderer-source:main",
        "render:main",
        DependencyReason.RENDER_EXECUTION,
    ) in edge_index


def test_selective_rebuild_fixture_maps_two_caption_styles_and_render_evidence(
    tmp_path,
):
    inputs, applied = make_p5_selective_rebuild_fixture(tmp_path)

    graph = dep_mod.build_production_dependency_graph(inputs)
    states = dep_mod.build_applied_dependency_evidence(inputs, applied)
    state_ids = {state.node_id for state in states}

    assert [
        (binding.caption_asset_id, binding.shot_id)
        for binding in inputs.composition_spec.caption_tracks
    ] == [
        ("caption-asset-1", "shot-1"),
        ("caption-asset-2", "shot-2"),
    ]
    assert {style_id for style_id, _ in inputs.caption_style_fingerprints} == {
        "caption-style-1",
        "caption-style-2",
    }
    assert _production_node(
        graph, "asset:caption-asset-2"
    ).semantic_role is DependencySemanticRole.CAPTION
    assert {
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }.issubset(state_ids)


def test_voice_semantic_projection_excludes_authorization_and_budget_rotation(tmp_path):
    request = make_p5_dependency_inputs(tmp_path).voice_requests[0]
    rotated = _copy_voice_request(
        request,
        request_id="request-rotated",
        attempt_id="attempt-rotated",
        pricing_snapshot_id="pricing-rotated",
        budget_reservation_receipt_id="budget-rotated",
        egress_authorization_receipt_id="egress-rotated",
    )

    assert rotated.voice_request_fingerprint != request.voice_request_fingerprint
    assert (
        dep_mod.voice_semantic_projection_fingerprint(rotated)
        == dep_mod.voice_semantic_projection_fingerprint(request)
    )


def test_voice_semantic_projection_changes_for_script_and_settings(tmp_path):
    request = make_p5_dependency_inputs(tmp_path).voice_requests[0]
    changed_script = _copy_voice_request(request, script_text="Changed exact script")
    changed_settings = _copy_voice_request(
        request,
        provider_parameters=request.provider_parameters.model_copy(
            update={"stability_milli": 700}
        ),
    )

    baseline = dep_mod.voice_semantic_projection_fingerprint(request)
    assert dep_mod.voice_semantic_projection_fingerprint(changed_script) != baseline
    assert dep_mod.voice_semantic_projection_fingerprint(changed_settings) != baseline


def test_voice_authorization_rotation_does_not_change_desired_graph(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    request = inputs.voice_requests[0]
    rotated = _copy_voice_request(
        request,
        pricing_snapshot_id="pricing-rotated",
        budget_reservation_receipt_id="budget-rotated",
        egress_authorization_receipt_id="egress-rotated",
    )

    before = dep_mod.build_production_dependency_graph(inputs)
    after = dep_mod.build_production_dependency_graph(
        replace(inputs, voice_requests=(rotated,))
    )

    assert after == before


def test_unbound_voice_asset_fallback_requires_exact_request_fingerprint(
    tmp_path,
):
    inputs = make_p5_dependency_inputs(tmp_path)
    request = inputs.voice_requests[0]
    changed_request = _copy_voice_request(
        request,
        provider_parameters=request.provider_parameters.model_copy(
            update={"stability_milli": 900}
        ),
    )
    source_asset = next(
        item for item in inputs.project.registry.assets
        if item.asset_id == "voice-dialogue"
    )
    metadata = source_asset.audio_metadata
    assert metadata is not None
    unbound = source_asset.model_copy(
        update={
            "asset_id": "voice-unbound",
            "source_kind": AssetSourceKind.GENERATED,
            "input_artifact_ids": request.input_artifact_ids,
            "input_fingerprint": request.input_fingerprint,
            "creation_receipt_id": "voice-unbound-receipt",
            "egress": EgressMetadata(
                remote=True,
                destination="https://api.fixture.invalid",
                authorization_receipt_id="egress-original",
                request_fingerprint=request.voice_request_fingerprint,
                payload_fingerprint=request.script_hash,
                retention_mode="zero_retention",
                provider_policy_snapshot_id="fixture-policy",
            ),
            "audio_metadata": metadata.model_copy(
                update={
                    "script_hash": changed_request.script_hash,
                    "voice_id": changed_request.voice_id,
                    "language": changed_request.language,
                    "sample_rate_hz": changed_request.output_sample_rate_hz,
                    "channels": changed_request.output_channels,
                    "source": metadata.source.model_copy(
                        update={
                            "input_artifact_ids": changed_request.input_artifact_ids,
                            "input_fingerprint": changed_request.input_fingerprint,
                        }
                    ),
                }
            ),
        }
    )
    project = inputs.project.model_copy(
        update={
            "registry": inputs.project.registry.model_copy(
                update={
                    "assets": (*inputs.project.registry.assets, unbound),
                }
            )
        }
    )

    graph = dep_mod.build_production_dependency_graph(
        replace(inputs, project=project, voice_requests=(changed_request,))
    )

    contributions = _production_contributions(graph, "asset:voice-unbound")
    assert "voice.semantic" not in contributions
    assert "asset.bytes" in contributions


def test_audio_mix_changes_downstream_without_changing_audio_asset_desired(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    before_graph = dep_mod.build_production_dependency_graph(inputs)
    before = dep_mod.desired_fingerprints(before_graph)
    tracks = tuple(
        track.model_copy(update={"gain_millidb": track.gain_millidb - 1_000})
        if track.track_id == "bgm"
        else track
        for track in inputs.composition_spec.audio_tracks
    )
    changed_inputs = replace(
        inputs,
        composition_spec=inputs.composition_spec.model_copy(
            update={"audio_tracks": tracks}
        ),
    )
    after = dep_mod.desired_fingerprints(
        dep_mod.build_production_dependency_graph(changed_inputs)
    )

    assert after["asset:bgm-theme"] == before["asset:bgm-theme"]
    for node_id in ("composition:main", "timeline:main", "renderer-source:main", "render:main"):
        assert after[node_id] != before[node_id]


def test_caption_style_and_timing_are_independent_contributions(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    graph = dep_mod.build_production_dependency_graph(inputs)
    before = _production_contributions(graph, "asset:caption-asset-1")
    after = _production_contributions(
        dep_mod.build_production_dependency_graph(
            replace(
                inputs,
                caption_style_fingerprints=(("caption-style-1", FOUR_HASH),),
            )
        ),
        "asset:caption-asset-1",
    )

    assert after["caption.style"] != before["caption.style"]
    assert after["caption.timing"] == before["caption.timing"]


def test_caption_style_contribution_has_exact_p4_fingerprint_origin(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    binding = inputs.composition_spec.caption_tracks[0]
    assert binding.style_reference is not None
    style_bytes = (tmp_path / binding.style_reference.path).read_bytes()

    graph = dep_mod.build_production_dependency_graph(inputs)

    assert _production_contributions(
        graph, "asset:caption-asset-1"
    )["caption.style"] == caption_style_fingerprint(
        binding.style_reference,
        style_bytes,
    )


def test_caption_style_contribution_rejects_metadata_binding_identity_drift(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    caption_assets = tuple(
        asset.model_copy(
            update={
                "caption_metadata": asset.caption_metadata.model_copy(
                    update={"style_reference_id": "other-style"}
                )
            }
        )
        if asset.asset_id == "caption-asset-1"
        else asset
        for asset in inputs.project.registry.assets
    )
    changed_inputs = replace(
        inputs,
        project=inputs.project.model_copy(
            update={
                "registry": inputs.project.registry.model_copy(
                    update={"assets": caption_assets}
                )
            }
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_production_dependency_graph(changed_inputs)

    assert exc_info.value.code is ErrorCode.DEPENDENCY_GRAPH_INVALID


def test_generated_image_record_uses_generic_future_extension_seam(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    assets = tuple(
        asset.model_copy(
            update={
                "source_kind": AssetSourceKind.GENERATED,
                "tool": ToolIdentity(name="future-local-fixture", version="1"),
            }
        )
        if asset.asset_id == "image-shot-1"
        else asset
        for asset in inputs.project.registry.assets
    )
    changed_project = inputs.project.model_copy(
        update={"registry": inputs.project.registry.model_copy(update={"assets": assets})}
    )

    graph = dep_mod.build_production_dependency_graph(
        replace(inputs, project=changed_project)
    )

    assert any(
        edge.source_node_id == "creative:shot:shot-1:visual"
        and edge.target_node_id == "asset:image-shot-1"
        and edge.reason is DependencyReason.GENERATION_INPUT
        for edge in graph.edges
    )
    assert "image_provider" not in dep_mod.__all__
    assert "submit_image" not in dep_mod.__all__


def test_applied_evidence_bootstraps_precise_pre_render_frontier(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    graph = dep_mod.build_production_dependency_graph(inputs)

    states = dep_mod.build_applied_dependency_evidence(inputs, applied=None)
    resolution = dep_mod.resolve_dependency_state(graph, states)

    assert resolution.ready_node_ids == ("asset:voice-dialogue",)
    assert resolution.by_id["asset:voice-dialogue"].lifecycle is DependencyLifecycle.STALE
    assert resolution.by_id["asset:caption-asset-1"].blocked_by == (
        "asset:voice-dialogue",
    )
    assert resolution.by_id["composition:main"].blocked_by == (
        "asset:caption-asset-1",
        "asset:voice-dialogue",
    )
    assert resolution.by_id["timeline:main"].lifecycle is DependencyLifecycle.BLOCKED


def test_production_builder_and_empty_applied_evidence_are_receipt_independent(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    graph = dep_mod.build_production_dependency_graph(inputs)

    assert dep_mod.build_applied_dependency_evidence(inputs, None) == (
        dep_mod.build_applied_dependency_evidence(
            inputs, dep_mod.AppliedProductionEvidence()
        )
    )
    assert dep_mod.build_production_dependency_graph(inputs) == graph


def test_shot_dialogue_mutation_does_not_invalidate_visual_projection(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    before = dep_mod.desired_fingerprints(
        dep_mod.build_production_dependency_graph(inputs)
    )
    shots = tuple(
        shot.model_copy(update={"dialogue": "Changed dialogue"})
        if shot.shot_id == "shot-1"
        else shot
        for shot in inputs.project.shots
    )
    changed_project = inputs.project.model_copy(update={"shots": shots})
    after = dep_mod.desired_fingerprints(
        dep_mod.build_production_dependency_graph(
            replace(inputs, project=changed_project)
        )
    )

    assert after["creative:shot:shot-1:voice"] != before["creative:shot:shot-1:voice"]
    assert after["asset:voice-dialogue"] != before["asset:voice-dialogue"]
    assert after["creative:shot:shot-1:visual"] == before["creative:shot:shot-1:visual"]
    assert after["asset:image-shot-1"] == before["asset:image-shot-1"]


def test_voice_activation_output_record_does_not_feed_back_into_desired(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    before = dep_mod.build_production_dependency_graph(inputs)
    assets = tuple(
        asset.model_copy(
            update={
                "source_kind": AssetSourceKind.GENERATED,
                "tool": ToolIdentity(name="different-output-adapter", version="99"),
                "sha256": FIVE_HASH,
                "size_bytes": asset.size_bytes + 1,
                "audio_metadata": asset.audio_metadata.model_copy(
                    update={"duration_samples": asset.audio_metadata.duration_samples + 1}
                ),
            }
        )
        if asset.asset_id == "voice-dialogue"
        else asset
        for asset in inputs.project.registry.assets
    )
    changed_project = inputs.project.model_copy(
        update={"registry": inputs.project.registry.model_copy(update={"assets": assets})}
    )

    after = dep_mod.build_production_dependency_graph(
        replace(inputs, project=changed_project)
    )

    assert after == before


def test_candidate_bundle_does_not_fabricate_active_applied_evidence(tmp_path):
    inputs = make_p5_dependency_inputs(tmp_path)
    candidate = inputs.project.model_copy(
        update={
            "project": inputs.project.project.model_copy(
                update={"content_hash": FIVE_HASH}
            ),
            "registry": inputs.project.registry.model_copy(
                update={"revision_id": SIX_HASH, "content_hash": SIX_HASH}
            ),
        }
    )
    candidate_inputs = replace(inputs, project=candidate)

    graph = dep_mod.build_production_dependency_graph(candidate_inputs)
    states = dep_mod.build_applied_dependency_evidence(candidate_inputs, None)

    assert graph.nodes
    assert states == ()


def _inputs_with_matching_voice_attempt(inputs):
    request = inputs.voice_requests[0]
    assets = tuple(
        asset.model_copy(
            update={
                "source_kind": AssetSourceKind.GENERATED,
                "audio_metadata": asset.audio_metadata.model_copy(
                    update={
                        "script_hash": request.script_hash,
                        "voice_id": request.voice_id,
                        "language": request.language,
                        "sample_rate_hz": request.output_sample_rate_hz,
                        "channels": request.output_channels,
                        "source": asset.audio_metadata.source.model_copy(
                            update={
                                "input_artifact_ids": request.input_artifact_ids,
                                "input_fingerprint": request.input_fingerprint,
                            }
                        ),
                    }
                ),
            }
        )
        if asset.asset_id == "voice-dialogue"
        else asset
        for asset in inputs.project.registry.assets
    )
    receipt = VoiceRequestReceipt(
        request_id=request.request_id,
        attempt_id=request.attempt_id,
        request_fingerprint=request.voice_request_fingerprint,
        script_hash=request.script_hash,
        provider_kind=request.provider_kind,
        model_id=request.model_id,
        voice_id=request.voice_id,
        language=request.language,
        pricing_snapshot_id=request.pricing_snapshot_id,
        budget_reservation_receipt_id=request.budget_reservation_receipt_id,
        egress_authorization_receipt_id=request.egress_authorization_receipt_id,
        destination="https://api.fixture.invalid",
    )
    attempt = StateCommitAttempt(
        attempt_id=request.attempt_id,
        operation="voice_generation",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=inputs.project.manifest.manifest_revision,
        base_project=inputs.project.manifest.active_project,
        base_registry=inputs.project.manifest.active_registry,
        candidate_registry=inputs.project.manifest.active_registry,
        candidate_artifacts_hash=ZERO_HASH,
        voice_request=receipt,
        voice_phase="activate",
        candidate_audio_asset_ids=("voice-dialogue",),
        started_at="2026-08-11T00:00:00Z",
        finished_at="2026-08-11T00:00:01Z",
    )
    project = inputs.project.model_copy(
        update={
            "registry": inputs.project.registry.model_copy(update={"assets": assets}),
            "manifest": inputs.project.manifest.model_copy(
                update={"attempts": (*inputs.project.manifest.attempts, attempt)}
            ),
        }
    )
    return replace(inputs, project=project)


def test_voice_applied_evidence_requires_exact_durable_request_proof(tmp_path):
    inputs = _inputs_with_matching_voice_attempt(make_p5_dependency_inputs(tmp_path))
    exact_states = {
        state.node_id: state
        for state in dep_mod.build_applied_dependency_evidence(inputs, None)
    }
    request = inputs.voice_requests[0]
    changed_request = _copy_voice_request(
        request,
        provider_parameters=request.provider_parameters.model_copy(
            update={"stability_milli": 900}
        ),
    )
    changed_states = {
        state.node_id: state
        for state in dep_mod.build_applied_dependency_evidence(
            replace(inputs, voice_requests=(changed_request,)),
            None,
        )
    }

    assert "asset:voice-dialogue" in exact_states
    assert "asset:voice-dialogue" not in changed_states


def _inputs_with_render_evidence(inputs):
    timeline_fingerprint = TWO_HASH
    source_sha256 = THREE_HASH
    bundle_sha256 = FOUR_HASH
    output_sha256 = FIVE_HASH
    source_bundle = SimpleNamespace(bundle_sha256=bundle_sha256)
    timeline = ResolvedTimeline.model_construct(
        composition_spec_id=inputs.composition_spec.artifact_id,
        composition_spec_revision=inputs.composition_spec.revision,
        composition_spec_hash=inputs.composition_spec.content_hash,
        renderer=inputs.renderer,
        composition_fingerprint=timeline_fingerprint,
    )
    state = RenderStateSnapshot.model_construct(
        project=inputs.project.manifest.active_project,
        registry=inputs.project.manifest.active_registry,
        timeline_fingerprint=timeline_fingerprint,
        source_sha256=source_sha256,
        source_bundle=source_bundle,
        source_bundle_sha256=bundle_sha256,
        output=SimpleNamespace(file_sha256=output_sha256),
    )
    source = RendererSourceReceipt.model_construct(
        timeline_fingerprint=timeline_fingerprint,
        source_sha256=source_sha256,
        source_bundle=source_bundle,
    )
    render = RenderReceipt.model_construct(
        timeline_fingerprint=timeline_fingerprint,
        source_sha256=source_sha256,
        source_bundle_sha256=bundle_sha256,
        output_sha256=output_sha256,
    )
    pointer = make_render_state_pointer()
    project = inputs.project.model_copy(
        update={
            "manifest": inputs.project.manifest.model_copy(
                update={"active_render_state": pointer}
            ),
            "render_state": state,
        }
    )
    return (
        replace(inputs, project=project),
        dep_mod.AppliedProductionEvidence(
            timeline=timeline,
            source_receipt=source,
            render_receipt=render,
            render_state=state,
        ),
    )


def test_non_empty_render_evidence_maps_only_to_applied_states(tmp_path):
    inputs, applied = _inputs_with_render_evidence(make_p5_dependency_inputs(tmp_path))
    graph = dep_mod.build_production_dependency_graph(inputs)

    states = dep_mod.build_applied_dependency_evidence(inputs, applied)
    by_id = {state.node_id: state for state in states}

    for node_id in (
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    ):
        assert by_id[node_id].lifecycle is DependencyLifecycle.FRESH
        assert isinstance(by_id[node_id].applied_evidence, RenderDependencyEvidence)
    assert dep_mod.build_production_dependency_graph(inputs) == graph


@pytest.mark.parametrize("missing", ["timeline", "source_receipt", "render_receipt"])
def test_partial_render_evidence_cannot_create_fresh_intermediate_nodes(
    tmp_path, missing
):
    inputs, applied = _inputs_with_render_evidence(make_p5_dependency_inputs(tmp_path))

    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_applied_dependency_evidence(
            inputs,
            replace(applied, **{missing: None}),
        )

    assert exc_info.value.code is ErrorCode.DEPENDENCY_RESOLUTION_INVALID


def test_tampered_render_evidence_is_rejected_without_changing_desired(tmp_path):
    inputs, applied = _inputs_with_render_evidence(make_p5_dependency_inputs(tmp_path))
    graph = dep_mod.build_production_dependency_graph(inputs)
    tampered = replace(
        applied,
        source_receipt=applied.source_receipt.model_copy(
            update={"timeline_fingerprint": SEVEN_HASH}
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        dep_mod.build_applied_dependency_evidence(inputs, tampered)

    assert exc_info.value.code is ErrorCode.DEPENDENCY_RESOLUTION_INVALID
    assert dep_mod.build_production_dependency_graph(inputs) == graph
