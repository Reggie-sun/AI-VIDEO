from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

import ai_video.production.image as image_mod
from ai_video.production.dependency import (
    DependencyResolution,
    ProductionDependencyInputs,
    asset_node_id,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
    shot_projection_node_id,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.image import (
    ImageGenerationRequest,
    ImageProviderParameters,
    ImageReferenceBinding,
)
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyLifecycle,
    DependencyNodeState,
    DependencySemanticRole,
    ProjectDependencyEvidence,
    ToolIdentity,
)
from ai_video.production.registry import registry_semantic_sha256
from production_project_factory import make_p5_selective_rebuild_fixture


@dataclass(frozen=True)
class P7ReuseFixture:
    requests: tuple[ImageGenerationRequest, ImageGenerationRequest]
    inputs: ProductionDependencyInputs
    base_graph: DependencyGraphSnapshot
    previous_states: tuple[DependencyNodeState, ...]
    base_asset_ids: frozenset[str]


@dataclass(frozen=True)
class ExplicitImageReplacement:
    new_request: ImageGenerationRequest
    registry: AssetRegistrySnapshot
    graph: DependencyGraphSnapshot
    resolution: DependencyResolution
    base_asset_ids: frozenset[str]


def _fresh_states(inputs: ProductionDependencyInputs, graph: DependencyGraphSnapshot):
    desired = desired_fingerprints(graph)
    return tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[node.node_id],
            applied_fingerprint=desired[node.node_id],
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=inputs.project.manifest.active_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            ),
        )
        for node in graph.nodes
    )


def _request(
    inputs: ProductionDependencyInputs,
    graph_pointer: DependencyGraphSnapshotPointer,
    *,
    shot_id: str,
    prompt_text: str,
    references: tuple[ImageReferenceBinding, ...],
) -> ImageGenerationRequest:
    return ImageGenerationRequest.create(
        attempt_id=f"attempt-{shot_id}",
        provider_kind="fake-local",
        model_id="fixture-image-model-1",
        target_shot_id=shot_id,
        target_asset_role="still",
        prompt_text=prompt_text,
        negative_prompt_text="blur, watermark",
        parameters=ImageProviderParameters(
            seed=11,
            width=2,
            height=1,
            output_format="png",
            generation_revision=1,
        ),
        references=references,
        base_project=inputs.project.manifest.active_project,
        base_registry=inputs.project.manifest.active_registry,
        base_dependency_graph=graph_pointer,
    )


@pytest.fixture
def p7_reuse_fixture(tmp_path) -> P7ReuseFixture:
    inputs, _ = make_p5_selective_rebuild_fixture(tmp_path)
    base_graph = build_production_dependency_graph(inputs)
    graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=base_graph.revision_id,
        content_hash=base_graph.content_hash,
        path=Path(f"state/dependency_graph.{base_graph.revision_id}.json"),
        file_sha256=hashlib.sha256(b"p7-reuse-base-graph").hexdigest(),
    )
    assets = {asset.asset_id: asset for asset in inputs.project.registry.assets}
    character = inputs.project.characters[0]
    scene = inputs.project.scenes[0]
    character_asset = assets[character.reference_asset_ids[0]]
    scene_asset = assets[scene.visual_reference_asset_ids[0]]
    references = (
        ImageReferenceBinding(
            role="character",
            creative_artifact_id=character.artifact_id,
            creative_revision=character.revision,
            creative_content_hash=character.content_hash,
            asset_id=character_asset.asset_id,
            asset_sha256=character_asset.sha256,
        ),
        ImageReferenceBinding(
            role="scene",
            creative_artifact_id=scene.artifact_id,
            creative_revision=scene.revision,
            creative_content_hash=scene.content_hash,
            asset_id=scene_asset.asset_id,
            asset_sha256=scene_asset.sha256,
        ),
    )
    requests = (
        _request(
            inputs,
            graph_pointer,
            shot_id="shot-1",
            prompt_text="Hero enters the archive",
            references=references,
        ),
        _request(
            inputs,
            graph_pointer,
            shot_id="shot-2",
            prompt_text="Hero finds the hidden record",
            references=references,
        ),
    )
    return P7ReuseFixture(
        requests=requests,
        inputs=inputs,
        base_graph=base_graph,
        previous_states=_fresh_states(inputs, base_graph),
        base_asset_ids=frozenset(assets),
    )


def explicitly_replace_shot_1_request(
    fixture: P7ReuseFixture,
) -> ExplicitImageReplacement:
    old_request = fixture.requests[0]
    new_request = ImageGenerationRequest.create(
        attempt_id="attempt-shot-1-explicit-replacement",
        provider_kind=old_request.provider_kind,
        model_id=old_request.model_id,
        target_shot_id=old_request.target_shot_id,
        target_asset_role=old_request.target_asset_role,
        prompt_text="Hero enters the archive under emergency lighting",
        negative_prompt_text=old_request.negative_prompt_text,
        parameters=old_request.parameters,
        references=old_request.references,
        base_project=old_request.base_project,
        base_registry=old_request.base_registry,
        base_dependency_graph=old_request.base_dependency_graph,
    )
    output_sha256 = hashlib.sha256(b"explicit-shot-1-output").hexdigest()
    output = AssetRecord(
        asset_id=new_request.output_asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=Path(f"assets/files/{output_sha256}.png"),
        sha256=output_sha256,
        size_bytes=len(b"explicit-shot-1-output"),
        mime_type="image/png",
        width=2,
        height=1,
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="fake-local-image", version="1"),
        input_artifact_ids=tuple(item.asset_id for item in new_request.references),
        input_fingerprint=new_request.request_fingerprint,
        creation_receipt_id=new_request.request_fingerprint,
        usage_license="project-owned-fixture",
    )
    registry = fixture.inputs.project.registry.model_copy(
        update={
            "revision_id": "0" * 64,
            "content_hash": "0" * 64,
            "assets": (*fixture.inputs.project.registry.assets, output),
        }
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    shots = []
    for shot in fixture.inputs.project.shots:
        if shot.shot_id != "shot-1":
            shots.append(shot)
            continue
        requirements = tuple(
            item.model_copy(update={"asset_ids": (new_request.output_asset_id,)})
            if item.role == new_request.target_asset_role
            else item
            for item in shot.required_asset_roles
        )
        shots.append(
            seal_artifact(
                shot.model_copy(
                    update={
                        "revision": shot.revision + 1,
                        "content_hash": "0" * 64,
                        "creation_receipt_id": new_request.request_fingerprint,
                        "required_asset_roles": requirements,
                    }
                )
            )
        )
    project = fixture.inputs.project.model_copy(
        update={"registry": registry, "shots": tuple(shots)}
    )
    changed_inputs = replace(fixture.inputs, project=project)
    graph = build_production_dependency_graph(changed_inputs)
    resolution = resolve_dependency_state(graph, fixture.previous_states)
    return ExplicitImageReplacement(
        new_request=new_request,
        registry=registry,
        graph=graph,
        resolution=resolution,
        base_asset_ids=fixture.base_asset_ids,
    )


def generated_asset_ids(candidate: ExplicitImageReplacement) -> set[str]:
    return {
        asset.asset_id
        for asset in candidate.registry.assets
        if asset.asset_id not in candidate.base_asset_ids
        and asset.asset_type is AssetType.IMAGE
        and asset.source_kind is AssetSourceKind.GENERATED
    }


def unrelated_voice_caption_nodes_remain_fresh(
    candidate: ExplicitImageReplacement,
) -> bool:
    protected = {
        node.node_id
        for node in candidate.graph.nodes
        if node.semantic_role
        in {DependencySemanticRole.VOICE, DependencySemanticRole.CAPTION}
    }
    affected = set(candidate.resolution.affected_node_ids)
    return (
        protected.isdisjoint(affected)
        and all(
            candidate.resolution.by_id[node_id].lifecycle
            is DependencyLifecycle.FRESH
            for node_id in protected
        )
        and shot_projection_node_id("shot-2", "visual") not in affected
        and asset_node_id(candidate.new_request.output_asset_id) in affected
    )


def test_image_requests_reuse_stable_character_scene_references(p7_reuse_fixture):
    shot_1, shot_2 = p7_reuse_fixture.requests

    assert shot_1.references == shot_2.references
    assert shot_1.target_shot_id != shot_2.target_shot_id
    assert shot_1.output_asset_id != shot_2.output_asset_id


def test_explicit_new_shot_1_prompt_changes_only_shot_1_output(p7_reuse_fixture):
    candidate = explicitly_replace_shot_1_request(p7_reuse_fixture)

    assert (
        candidate.new_request.output_asset_id
        != p7_reuse_fixture.requests[0].output_asset_id
    )
    assert generated_asset_ids(candidate) == {candidate.new_request.output_asset_id}
    assert unrelated_voice_caption_nodes_remain_fresh(candidate)


def test_p7_pure_lane_has_no_renderer_review_video_or_remote_provider():
    exported = set(image_mod.__all__)

    assert "ImageAssetProvider" in exported
    assert not {
        "VideoProvider",
        "RemoteImageProvider",
        "render_with_hyperframes",
    } & exported
