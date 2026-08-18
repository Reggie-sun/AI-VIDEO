"""Offline acceptance matrix for P5 precise selective rebuild decisions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ai_video.production import dependency as dep_mod
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    DependencyLifecycle,
    DependencyNodeKind,
    DependencyNodeState,
    ProjectDependencyEvidence,
    RegistryDependencyEvidence,
    RenderDependencyEvidence,
    RendererKind,
    ToolIdentity,
    VideoAssetMetadata,
    VisualStrategy,
)
from production_project_factory import make_p5_selective_rebuild_fixture


EXPECTED_NODE_IDS = frozenset(
    {
        "asset:ambience-room",
        "asset:bgm-theme",
        "asset:caption-asset-1",
        "asset:caption-asset-2",
        "asset:image-shot-1",
        "asset:image-shot-2",
        "asset:sfx-hit",
        "asset:voice-dialogue",
        "asset:voice-narration",
        "composition:main",
        "creative:brief:brief-main",
        "creative:character:character-hero",
        "creative:scene:scene-room",
        "creative:shot:shot-1:composition",
        "creative:shot:shot-1:visual",
        "creative:shot:shot-1:voice",
        "creative:shot:shot-2:composition",
        "creative:shot:shot-2:visual",
        "creative:shot:shot-2:voice",
        "creative:story:story-main",
        "creative:storyboard:storyboard-main",
        "render:main",
        "renderer-source:main",
        "timeline:main",
    }
)

SCRIPT_REBUILD = frozenset(
    {
        "creative:shot:shot-1:voice",
        "asset:voice-dialogue",
        "asset:caption-asset-1",
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }
)
VOICE_REBUILD = SCRIPT_REBUILD - {"creative:shot:shot-1:voice"}
CAPTION_2_REBUILD = frozenset(
    {
        "asset:caption-asset-2",
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }
)
COMPOSITION_REBUILD = frozenset(
    {"composition:main", "timeline:main", "renderer-source:main", "render:main"}
)
VISUAL_2_REBUILD = COMPOSITION_REBUILD | {"asset:image-shot-2"}
SOURCE_REBUILD = frozenset({"renderer-source:main", "render:main"})
RENDER_REBUILD = frozenset({"render:main"})


MUTATION_MATRIX_CASES = (
    (
        "script",
        SCRIPT_REBUILD,
        frozenset(
            {
                "creative:shot:shot-1:visual",
                "asset:image-shot-1",
                "asset:voice-narration",
                "asset:caption-asset-2",
            }
        ),
        ("creative:shot:shot-1:voice",),
    ),
    (
        "voice_settings",
        VOICE_REBUILD,
        frozenset(
            {
                "creative:shot:shot-1:voice",
                "creative:shot:shot-1:visual",
                "asset:image-shot-1",
                "asset:voice-narration",
            }
        ),
        ("asset:voice-dialogue",),
    ),
    (
        "alignment_receipt_only",
        frozenset(),
        EXPECTED_NODE_IDS,
        (),
    ),
    (
        "alignment_policy",
        CAPTION_2_REBUILD,
        frozenset(
            {
                "asset:caption-asset-1",
                "asset:voice-dialogue",
                "asset:voice-narration",
                "asset:image-shot-2",
            }
        ),
        ("asset:caption-asset-2",),
    ),
    (
        "caption_timing",
        CAPTION_2_REBUILD,
        frozenset(
            {
                "asset:caption-asset-1",
                "asset:voice-dialogue",
                "asset:voice-narration",
                "asset:image-shot-2",
            }
        ),
        ("asset:caption-asset-2",),
    ),
    (
        "caption_style",
        CAPTION_2_REBUILD,
        frozenset(
            {
                "asset:caption-asset-1",
                "asset:voice-dialogue",
                "asset:voice-narration",
                "asset:image-shot-2",
            }
        ),
        ("asset:caption-asset-2",),
    ),
    (
        "audio_mix",
        COMPOSITION_REBUILD,
        frozenset(
            {
                "asset:bgm-theme",
                "asset:sfx-hit",
                "asset:voice-dialogue",
                "asset:voice-narration",
                "asset:caption-asset-1",
                "asset:caption-asset-2",
            }
        ),
        ("composition:main",),
    ),
    (
        "visual_asset",
        VISUAL_2_REBUILD,
        frozenset(
            {
                "asset:image-shot-1",
                "creative:shot:shot-2:visual",
                "asset:voice-dialogue",
                "asset:caption-asset-2",
            }
        ),
        ("asset:image-shot-2",),
    ),
    (
        "composition_spec",
        COMPOSITION_REBUILD,
        frozenset(
            {
                "asset:image-shot-1",
                "asset:image-shot-2",
                "asset:voice-dialogue",
                "asset:caption-asset-2",
            }
        ),
        ("composition:main",),
    ),
    (
        "renderer_source_contract",
        SOURCE_REBUILD,
        frozenset(
            {
                "composition:main",
                "timeline:main",
                "asset:image-shot-1",
                "asset:voice-dialogue",
            }
        ),
        ("renderer-source:main",),
    ),
    (
        "renderer_render_contract",
        RENDER_REBUILD,
        frozenset(
            {
                "composition:main",
                "timeline:main",
                "renderer-source:main",
                "asset:image-shot-1",
            }
        ),
        ("render:main",),
    ),
)


def _copy_voice_request(request, **updates):
    derived = {
        "script_hash",
        "provider_parameters_hash",
        "voice_request_fingerprint",
    }
    data = {
        field_name: getattr(request, field_name)
        for field_name in type(request).model_fields
        if field_name not in derived
    }
    data.update(updates)
    return type(request).create(**data)


def _replace_registry_asset(inputs, asset_id: str, update):
    assets = tuple(
        update(asset) if asset.asset_id == asset_id else asset
        for asset in inputs.project.registry.assets
    )
    project = inputs.project.model_copy(
        update={
            "registry": inputs.project.registry.model_copy(update={"assets": assets})
        }
    )
    return replace(inputs, project=project)


def _mutate(inputs, mutation: str):
    if mutation == "script":
        shots = tuple(
            shot.model_copy(update={"dialogue": "Changed exact dialogue"})
            if shot.shot_id == "shot-1"
            else shot
            for shot in inputs.project.shots
        )
        return replace(
            inputs,
            project=inputs.project.model_copy(update={"shots": shots}),
        )
    if mutation == "voice_settings":
        request = inputs.voice_requests[0]
        changed = _copy_voice_request(
            request,
            provider_parameters=request.provider_parameters.model_copy(
                update={"stability_milli": 701}
            ),
        )
        return replace(inputs, voice_requests=(changed,))
    if mutation == "alignment_receipt_only":
        return _replace_registry_asset(
            inputs,
            "caption-asset-2",
            lambda asset: asset.model_copy(
                update={
                    "caption_metadata": asset.caption_metadata.model_copy(
                        update={"alignment_receipt_id": "alignment-narration-replayed"}
                    )
                }
            ),
        )
    if mutation == "alignment_policy":
        return _replace_registry_asset(
            inputs,
            "caption-asset-2",
            lambda asset: asset.model_copy(
                update={
                    "caption_metadata": asset.caption_metadata.model_copy(
                        update={
                            "alignment_receipt_id": "alignment-narration-policy-v2",
                            "timing_fingerprint": "9" * 64,
                        }
                    )
                }
            ),
        )
    if mutation == "caption_timing":
        return _replace_registry_asset(
            inputs,
            "caption-asset-2",
            lambda asset: asset.model_copy(
                update={
                    "caption_metadata": asset.caption_metadata.model_copy(
                        update={"timing_fingerprint": "a" * 64}
                    )
                }
            ),
        )
    if mutation == "caption_style":
        return replace(
            inputs,
            caption_style_fingerprints=tuple(
                (style_id, "b" * 64)
                if style_id == "caption-style-2"
                else (style_id, fingerprint)
                for style_id, fingerprint in inputs.caption_style_fingerprints
            ),
        )
    if mutation == "audio_mix":
        tracks = tuple(
            track.model_copy(update={"gain_millidb": track.gain_millidb - 1_000})
            if track.track_id == "bgm"
            else track
            for track in inputs.composition_spec.audio_tracks
        )
        spec = seal_artifact(
            inputs.composition_spec.model_copy(
                update={"content_hash": "0" * 64, "audio_tracks": tracks}
            )
        )
        return replace(inputs, composition_spec=spec)
    if mutation == "visual_asset":
        return _replace_registry_asset(
            inputs,
            "image-shot-2",
            lambda asset: asset.model_copy(update={"sha256": "c" * 64}),
        )
    if mutation == "composition_spec":
        delivery = inputs.composition_spec.delivery_profile.model_copy(
            update={"width": 1_920}
        )
        spec = seal_artifact(
            inputs.composition_spec.model_copy(
                update={"content_hash": "0" * 64, "delivery_profile": delivery}
            )
        )
        return replace(inputs, composition_spec=spec)
    if mutation == "renderer_source_contract":
        return replace(inputs, source_materializer_contract_fingerprint="d" * 64)
    if mutation == "renderer_render_contract":
        return replace(inputs, render_contract_fingerprint="e" * 64)
    raise AssertionError(f"unknown fixture mutation: {mutation}")


def _evidence_for(inputs, node, fingerprint):
    if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT:
        return ProjectDependencyEvidence(
            owner="project_snapshot",
            pointer=inputs.project.manifest.active_project,
            artifact_id=node.artifact_id,
            artifact_fingerprint=fingerprint,
        )
    if node.kind is DependencyNodeKind.ASSET:
        return RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=inputs.project.manifest.active_registry,
            artifact_id=node.artifact_id,
            artifact_fingerprint=fingerprint,
        )
    pointer = inputs.project.manifest.active_render_state
    assert pointer is not None
    return RenderDependencyEvidence(
        owner="render_state",
        pointer=pointer,
        artifact_id=node.artifact_id,
        artifact_fingerprint=fingerprint,
    )


def _all_fresh_states(inputs, applied, graph):
    desired = dep_mod.desired_fingerprints(graph)
    verified = {
        state.node_id: state
        for state in dep_mod.build_applied_dependency_evidence(inputs, applied)
    }
    states = []
    for node in graph.nodes:
        evidence = (
            verified[node.node_id].applied_evidence
            if node.node_id in verified
            else _evidence_for(inputs, node, desired[node.node_id])
        )
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
    return tuple(states)


def _resolve_mutation(tmp_path: Path, mutation: str):
    inputs, applied = make_p5_selective_rebuild_fixture(tmp_path)
    before = dep_mod.build_production_dependency_graph(inputs)
    previous = _all_fresh_states(inputs, applied, before)
    changed_inputs = _mutate(inputs, mutation)
    after = dep_mod.build_production_dependency_graph(changed_inputs)
    return changed_inputs, after, dep_mod.resolve_dependency_state(after, previous)


@pytest.mark.parametrize(
    ("mutation", "must_rebuild", "must_not_rebuild", "first_ready"),
    MUTATION_MATRIX_CASES,
)
def test_required_mutation_matrix_is_precise(
    tmp_path,
    mutation,
    must_rebuild,
    must_not_rebuild,
    first_ready,
):
    _, graph, resolution = _resolve_mutation(tmp_path, mutation)
    decision = dep_mod.select_rebuild_nodes(resolution)

    assert {node.node_id for node in graph.nodes} == EXPECTED_NODE_IDS
    assert set(decision.affected_node_ids) == must_rebuild
    assert set(decision.affected_node_ids).isdisjoint(must_not_rebuild)
    assert decision.ready_node_ids == first_ready
    assert {
        node_id
        for node_id, state in resolution.by_id.items()
        if state.lifecycle is DependencyLifecycle.FRESH
    } == EXPECTED_NODE_IDS - must_rebuild
    assert resolution.exact_replay is (mutation == "alignment_receipt_only")


def test_generated_video_trim_only_stales_existing_composition_closure(tmp_path):
    inputs, applied = make_p5_selective_rebuild_fixture(tmp_path)
    video_metadata = VideoAssetMetadata(
        container_name="mp4",
        codec_name="h264",
        width=1280,
        height=720,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=3000,
        frame_count=72,
        probe_receipt_id="probe-video-shot-2",
        request_receipt_fingerprint="1" * 64,
        resolved_generation_hash="2" * 64,
        provenance_receipt_id="provenance-video-shot-2",
    )
    assets = tuple(
        asset.model_copy(
            update={
                "asset_type": AssetType.VIDEO,
                "mime_type": "video/mp4",
                "video_metadata": video_metadata,
            }
        )
        if asset.asset_id == "image-shot-2"
        else asset
        for asset in inputs.project.registry.assets
    )
    shots = tuple(
        shot.model_copy(
            update={
                "visual_strategy": VisualStrategy.GENERATED_VIDEO,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="still",
                        asset_ids=("image-shot-2",),
                        allowed_asset_types=(AssetType.VIDEO,),
                    ),
                ),
            }
        )
        if shot.shot_id == "shot-2"
        else shot
        for shot in inputs.project.shots
    )
    baseline_inputs = replace(
        inputs,
        project=inputs.project.model_copy(
            update={
                "registry": inputs.project.registry.model_copy(
                    update={"assets": assets}
                ),
                "shots": shots,
            }
        ),
    )
    before = dep_mod.build_production_dependency_graph(baseline_inputs)
    previous = _all_fresh_states(baseline_inputs, applied, before)
    layers = tuple(
        layer.model_copy(update={"trim_start_frame": 12, "trim_duration_frames": 48})
        if layer.shot_id == "shot-2"
        else layer
        for layer in baseline_inputs.composition_spec.layers
    )
    changed_spec = seal_artifact(
        baseline_inputs.composition_spec.model_copy(
            update={"content_hash": "0" * 64, "layers": layers}
        )
    )
    changed_inputs = replace(baseline_inputs, composition_spec=changed_spec)
    after = dep_mod.build_production_dependency_graph(changed_inputs)
    resolution = dep_mod.resolve_dependency_state(after, previous)

    decision = dep_mod.select_rebuild_nodes(resolution)

    assert set(decision.affected_node_ids) == COMPOSITION_REBUILD


def test_same_desired_failure_stays_failed_and_blocks_transitive_dependents(tmp_path):
    _, graph, resolution = _resolve_mutation(tmp_path, "script")
    failed_id = "creative:shot:shot-1:voice"
    failed = resolution.by_id[failed_id].model_copy(
        update={
            "lifecycle": DependencyLifecycle.FAILED,
            "error_code": "VOICE_GENERATION_FAILED",
            "error_message": "fixture failure",
        }
    )
    previous = tuple(
        failed if state.node_id == failed_id else state for state in resolution.states
    )

    replay = dep_mod.resolve_dependency_state(graph, previous)
    decision = dep_mod.select_rebuild_nodes(replay)

    assert replay.by_id[failed_id] == failed
    assert replay.by_id["asset:voice-dialogue"].lifecycle is DependencyLifecycle.BLOCKED
    assert replay.by_id["asset:voice-dialogue"].blocked_by == (failed_id,)
    assert replay.by_id["render:main"].lifecycle is DependencyLifecycle.BLOCKED
    assert all(failed_id not in unit.node_ids for unit in decision.execution_units)


def test_new_desired_clears_old_failure_without_auto_retrying_same_desired(tmp_path):
    inputs, graph, resolution = _resolve_mutation(tmp_path, "script")
    failed_id = "creative:shot:shot-1:voice"
    failed = resolution.by_id[failed_id].model_copy(
        update={
            "lifecycle": DependencyLifecycle.FAILED,
            "error_code": "VOICE_GENERATION_FAILED",
            "error_message": "fixture failure",
        }
    )
    previous = tuple(
        failed if state.node_id == failed_id else state for state in resolution.states
    )
    shots = tuple(
        shot.model_copy(update={"dialogue": "A second changed dialogue"})
        if shot.shot_id == "shot-1"
        else shot
        for shot in inputs.project.shots
    )
    next_inputs = replace(
        inputs,
        project=inputs.project.model_copy(update={"shots": shots}),
    )
    next_graph = dep_mod.build_production_dependency_graph(next_inputs)

    changed = dep_mod.resolve_dependency_state(next_graph, previous)

    assert next_graph.revision_id != graph.revision_id
    assert changed.by_id[failed_id].lifecycle is DependencyLifecycle.STALE
    assert changed.by_id[failed_id].error_code is None
    assert changed.ready_node_ids == (failed_id,)


def test_applying_each_ready_node_advances_only_the_precise_frontier(tmp_path):
    inputs, graph, resolution = _resolve_mutation(tmp_path, "script")
    expected_frontiers = (
        ("creative:shot:shot-1:voice",),
        ("asset:voice-dialogue",),
        ("asset:caption-asset-1",),
    )
    node_by_id = {node.node_id: node for node in graph.nodes}

    for expected in expected_frontiers:
        assert resolution.ready_node_ids == expected
        node_id = expected[0]
        current = resolution.by_id[node_id]
        applied = DependencyNodeState(
            node_id=node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=current.desired_fingerprint,
            applied_fingerprint=current.desired_fingerprint,
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=_evidence_for(
                inputs,
                node_by_id[node_id],
                current.desired_fingerprint,
            ),
        )
        previous = tuple(
            applied if state.node_id == node_id else state
            for state in resolution.states
        )
        resolution = dep_mod.resolve_dependency_state(graph, previous)

    decision = dep_mod.select_rebuild_nodes(resolution)
    assert resolution.ready_node_ids == ("composition:main",)
    assert [
        (unit.kind, unit.node_ids) for unit in decision.execution_units
    ] == [
        (
            "render_with_hyperframes",
            (
                "composition:main",
                "render:main",
                "renderer-source:main",
                "timeline:main",
            ),
        )
    ]


def test_exact_replay_has_no_execution_unit_or_state_advance(tmp_path):
    inputs, applied = make_p5_selective_rebuild_fixture(tmp_path)
    graph = dep_mod.build_production_dependency_graph(inputs)
    previous = _all_fresh_states(inputs, applied, graph)

    resolution = dep_mod.resolve_dependency_state(graph, previous)
    decision = dep_mod.select_rebuild_nodes(resolution)

    assert resolution.exact_replay is True
    assert resolution.states == previous
    assert decision.affected_node_ids == ()
    assert decision.ready_node_ids == ()
    assert decision.execution_units == ()


def test_scope_boundaries_remain_absent_and_generated_image_uses_asset_seam(tmp_path):
    inputs, _ = make_p5_selective_rebuild_fixture(tmp_path)
    generated = _replace_registry_asset(
        inputs,
        "image-shot-2",
        lambda asset: asset.model_copy(
            update={
                "source_kind": AssetSourceKind.GENERATED,
                "tool": ToolIdentity(name="future-local-fixture", version="1"),
            }
        ),
    )
    graph = dep_mod.build_production_dependency_graph(generated)

    assert inputs.renderer.kind is RendererKind.HYPERFRAMES
    assert inputs.composition_spec.requested_renderer is RendererKind.HYPERFRAMES
    assert {node.kind for node in graph.nodes} == set(DependencyNodeKind)
    forbidden = ("qa", "review", "repair", "provider", "cloud", "remotion")
    assert not any(
        token in node.node_id.lower()
        for node in graph.nodes
        for token in forbidden
    )
    assert "image_provider" not in dep_mod.__all__
    assert "video_provider" not in dep_mod.__all__
    assert any(
        edge.source_node_id == "creative:shot:shot-2:visual"
        and edge.target_node_id == "asset:image-shot-2"
        for edge in graph.edges
    )
