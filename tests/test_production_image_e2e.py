from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

import ai_video.production.image as image_mod
import ai_video.production as production_mod
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
    DependencyNodeKind,
    DependencyNodeState,
    DependencySemanticRole,
    ProjectDependencyEvidence,
    RegistryDependencyEvidence,
    ToolIdentity,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import ProductionStateCommitter
import production_project_factory as project_factory
from production_project_factory import make_p5_selective_rebuild_fixture
from test_production_state_commit import (
    make_image_call_bundle,
    make_image_provider_result,
)


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


def test_p7_package_exports_only_safe_image_generation_contracts():
    expected = {
        "ImageAssetProvider",
        "ImageGenerationRequest",
        "ImageGenerationPreview",
        "ImageGenerationAuthorization",
        "ImageProviderParameters",
        "ImageReferenceBinding",
        "ImageProviderResult",
        "ImageLocalResourceEvidence",
    }

    assert expected.issubset(set(production_mod.__all__))
    assert not {
        "DurableImageSubmitPermit",
        "PreparedImageCandidate",
        "ImageActivationCandidate",
        "RemoteImageProvider",
    } & set(production_mod.__all__)


def test_regenerated_shot_history_survives_idempotent_recovery(tmp_path):
    """A refreshed P5 pre-state permits exact same-role regeneration history."""

    project_factory.write_production_project(tmp_path)
    base_inputs = project_factory.make_p7_image_generation_base(tmp_path)
    provider_calls = 0
    preparer_calls = 0
    manifest_writes = 0
    prepare = project_factory.make_p7_image_candidate_preparer(base_inputs)

    class _Provider:
        def generate(self, request, authorization, permit):
            nonlocal provider_calls
            provider_calls += 1
            assert permit._consume_image_generation_permit(
                request_fingerprint=request.request_fingerprint
            )
            return make_image_provider_result(
                request,
                authorization,
                project_factory._p7_png(
                    rgba=(
                        b"\x11\x22\x33\xff"
                        if provider_calls == 1
                        else b"\x44\x55\x66\xff"
                    )
                ),
            )

    def counted_prepare(*args):
        nonlocal preparer_calls
        preparer_calls += 1
        return prepare(*args)

    class _CountingCommitter(ProductionStateCommitter):
        def _write_manifest_atomic(self, manifest, *, on_replace=None):
            nonlocal manifest_writes
            manifest_writes += 1
            return super()._write_manifest_atomic(manifest, on_replace=on_replace)

    writer = _CountingCommitter(
        tmp_path,
        image_candidate_preparer=counted_prepare,
    )
    first_request, first_preview, first_authorization = make_image_call_bundle(
        tmp_path,
        attempt_id="image-e2e-regeneration-1",
        prompt_text="Hero enters the archive room",
    )
    first = writer.generate_image_asset(
        first_request, first_preview, first_authorization, _Provider()
    )

    # P5's fixed-owner public result API reopens each active Project/Registry
    # artifact before marking the ready node fresh. Applying one frontier node
    # recomputes the graph, which can expose the next ready stale node.
    while True:
        graph = load_production_project(tmp_path / "project.yaml").dependency_graph
        assert graph is not None
        nodes = {item.node_id: item for item in graph.nodes}
        ready = next(
            (
                state
                for state in first.dependency_states
                if state.lifecycle is DependencyLifecycle.STALE
                and nodes[state.node_id].kind
                in {DependencyNodeKind.CREATIVE_ARTIFACT, DependencyNodeKind.ASSET}
            ),
            None,
        )
        if ready is None:
            break
        node = nodes[ready.node_id]
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT:
            evidence = ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=first.active_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=ready.desired_fingerprint,
            )
        else:
            evidence = RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=first.active_registry,
                artifact_id=node.artifact_id,
                artifact_fingerprint=ready.desired_fingerprint,
            )
        first = writer.record_dependency_node_applied(
            expected_manifest_revision=first.manifest_revision,
            active_dependency_graph=first.active_dependency_graph,
            candidate_dependency_graph=first.active_dependency_graph,
            node_id=ready.node_id,
            desired_fingerprint=ready.desired_fingerprint,
            evidence=evidence,
        )

    replay_writes_before = manifest_writes
    assert writer.generate_image_asset(
        first_request, first_preview, first_authorization, _Provider()
    ) == first
    assert (provider_calls, preparer_calls, manifest_writes) == (
        1,
        1,
        replay_writes_before,
    )

    second_request, second_preview, second_authorization = make_image_call_bundle(
        tmp_path,
        attempt_id="image-e2e-regeneration-2",
        prompt_text="Hero re-enters the archive under emergency lighting",
    )
    second = writer.generate_image_asset(
        second_request, second_preview, second_authorization, _Provider()
    )

    assert first_request.request_fingerprint != second_request.request_fingerprint
    assert first_request.output_asset_id != second_request.output_asset_id
    assert (provider_calls, preparer_calls) == (2, 2)

    revision_before = second.manifest_revision
    selected_before = (
        second.active_project,
        second.active_registry,
        second.active_dependency_graph,
        second.active_render_state,
        second.dependency_states,
    )
    writes_before = manifest_writes
    report = writer.recover()
    recovered = load_production_project(tmp_path / "project.yaml")
    replay = writer.generate_image_asset(
        second_request, second_preview, second_authorization, _Provider()
    )

    assert report.manifest_revision_before == revision_before
    assert report.manifest_revision_after == revision_before
    assert recovered.manifest.manifest_revision == revision_before
    assert (
        recovered.manifest.active_project,
        recovered.manifest.active_registry,
        recovered.manifest.active_dependency_graph,
        recovered.manifest.active_render_state,
        recovered.manifest.dependency_states,
    ) == selected_before
    assert replay == recovered.manifest
    assert (provider_calls, preparer_calls, manifest_writes) == (
        2,
        2,
        writes_before,
    )

    image_attempts = tuple(
        item
        for item in recovered.manifest.attempts
        if item.operation == "image_generation"
    )
    assert len(image_attempts) == 2
    assert all(item.candidate_artifacts_hash for item in image_attempts)
    proof_paths = {item.path for item in report.items}
    request_paths = {
        path
        for path in proof_paths
        if path.as_posix().startswith("state/images/requests/")
    }
    result_paths = {
        path
        for path in proof_paths
        if path.as_posix().startswith("state/images/results/")
    }
    receipt_paths = {
        path
        for path in proof_paths
        if path.as_posix().startswith("state/images/receipts/")
    }
    shot_paths = {
        path
        for path in proof_paths
        if path.as_posix().startswith("creative/shots/shot.")
    }
    candidate_project_paths = {
        item.candidate_project.path for item in image_attempts
    }
    candidate_registry_paths = {
        item.candidate_registry.path for item in image_attempts
    }
    candidate_graph_paths = {
        item.candidate_dependency_graph.path for item in image_attempts
    }
    generated_records = tuple(
        item
        for item in recovered.registry.assets
        if item.asset_id
        in {first_request.output_asset_id, second_request.output_asset_id}
    )
    image_paths = {item.artifact_path for item in generated_records}
    exact_proof_paths = (
        request_paths
        | result_paths
        | receipt_paths
        | shot_paths
        | candidate_project_paths
        | candidate_registry_paths
        | candidate_graph_paths
        | image_paths
    )
    assert all(
        len(paths) == 2
        for paths in (
            request_paths,
            result_paths,
            receipt_paths,
            shot_paths,
            candidate_project_paths,
            candidate_registry_paths,
            candidate_graph_paths,
            image_paths,
        )
    )
    assert len(exact_proof_paths) == 16
    assert exact_proof_paths <= proof_paths
    registry_ids = {item.asset_id for item in recovered.registry.assets}
    assert {first_request.output_asset_id, second_request.output_asset_id} <= registry_ids
    shot = next(item for item in recovered.shots if item.shot_id == "shot-1")
    role = next(item for item in shot.required_asset_roles if item.role == "still")
    assert role.asset_ids == (second_request.output_asset_id,)
