from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.dependency import (
    build_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ArtifactReference,
    AssetRegistrySnapshot,
    AssetRoleRequirement,
    AssetType,
    DependencyLifecycle,
    DependencyNodeKind,
    DependencyNodeState,
    ProjectDependencyEvidence,
    VisualStrategy,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    ProductionStateCommitter,
    prepare_dependency_graph_transition,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoOutputRequirement,
)
from ai_video.production.video_pre_generation import (
    VideoPreGenerationDependencyInputs,
    build_video_pre_generation_applied_evidence,
    build_video_pre_generation_dependency_graph,
    generation_target_node_id,
)
import production_project_factory as project_factory


REQUIREMENT_HASH = "d" * 64
PLANNING_REQUEST_HASH = "9" * 64
VERIFIED_PROJECTION_HASH = "8" * 64


def _bootstrap_asset_free_project(root: Path) -> None:
    source = root / "source"
    target = root / "target"
    source.mkdir()
    target.mkdir()
    project_factory.write_production_project(source)
    loaded = load_production_project(source / "project.yaml")
    character = seal_artifact(
        loaded.characters[0].model_copy(
            update={
                "content_hash": project_factory.ZERO_HASH,
                "reference_asset_ids": (),
            }
        )
    )
    scene = seal_artifact(
        loaded.scenes[0].model_copy(
            update={
                "content_hash": project_factory.ZERO_HASH,
                "visual_reference_asset_ids": (),
            }
        )
    )
    shot = seal_artifact(
        loaded.shots[0].model_copy(
            update={
                "content_hash": project_factory.ZERO_HASH,
                "visual_strategy": VisualStrategy.GENERATED_VIDEO,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="final_visual",
                        asset_ids=(),
                        allowed_asset_types=(AssetType.VIDEO,),
                    ),
                ),
                "generated_video_rationale": "Sealed pre-generation target.",
            }
        )
    )

    def ref(model, path: Path) -> ArtifactReference:
        return ArtifactReference(
            artifact_id=model.artifact_id,
            revision=model.revision,
            content_hash=model.content_hash,
            path=path,
        )

    refs = loaded.project.artifacts.model_copy(
        update={
            "characters": (
                ref(character, loaded.project.artifacts.characters[0].path),
            ),
            "scenes": (ref(scene, loaded.project.artifacts.scenes[0].path),),
            "shots": (ref(shot, loaded.project.artifacts.shots[0].path),),
        }
    )
    project = seal_artifact(
        loaded.project.model_copy(
            update={"content_hash": project_factory.ZERO_HASH, "artifacts": refs}
        )
    )
    registry = AssetRegistrySnapshot(
        schema_version="2.0",
        revision_id=project_factory.ZERO_HASH,
        content_hash=project_factory.ZERO_HASH,
        assets=(),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    artifacts_by_path = {
        loaded.project.artifacts.brief.path: loaded.brief,
        loaded.project.artifacts.story.path: loaded.story,
        refs.characters[0].path: character,
        refs.scenes[0].path: scene,
        loaded.project.artifacts.storyboard.path: loaded.storyboard,
        refs.shots[0].path: shot,
    }
    writer = ProductionStateCommitter(target)
    artifacts = tuple(
        writer.prepare_artifact(
            "bootstrap-pending-video",
            path,
            yaml.safe_dump(
                model.model_dump(mode="json"),
                allow_unicode=True,
                sort_keys=True,
            ).encode("utf-8"),
        )
        for path, model in sorted(
            artifacts_by_path.items(), key=lambda item: item[0].as_posix()
        )
    )
    writer.bootstrap_initial_state(
        attempt_id="bootstrap-pending-video",
        project=project,
        registry=registry,
        artifacts=artifacts,
    )


def _activate_pre_generation_graph(root: Path):
    _bootstrap_asset_free_project(root)
    target = root / "target"
    loaded = load_production_project(target / "project.yaml")
    shot = loaded.shots[0]
    inputs = VideoPreGenerationDependencyInputs(
        project=loaded,
        target_shot_id=shot.shot_id,
        target_asset_role="final_visual",
        requirement_hash=REQUIREMENT_HASH,
        planning_request_hash=PLANNING_REQUEST_HASH,
        verified_projection_hash=VERIFIED_PROJECTION_HASH,
    )
    graph = build_video_pre_generation_dependency_graph(inputs)
    applied = build_video_pre_generation_applied_evidence(inputs)
    resolution = resolve_dependency_state(graph, applied)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=resolution.states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    writer = ProductionStateCommitter(target)
    committed = writer.bootstrap_dependency_graph(
        attempt_id="bootstrap-video-pre-generation-graph",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    writer.upgrade_manifest_schema(
        "2.7", expected_manifest_revision=committed.manifest_revision
    )
    return target, inputs, load_production_project(target / "project.yaml")


def _resolved_request(loaded, *, changes: dict[str, object] | None = None):
    shot = loaded.shots[0]
    values: dict[str, object] = {
        "generation_id": "pre-generation-1",
        "provider_name": "fixture-local-video",
        "provider_kind": "fixture_t2v",
        "model_id": "fixture-t2v-1",
        "provider_profile": ProviderProfilePointer(
            profile_id="fixture-t2v-1",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{'a' * 64}.json"),
            profile_sha256="a" * 64,
        ),
        "requirement_hash": REQUIREMENT_HASH,
        "provider_bound_request_hash": "b" * 64,
        "adapter_compiler_id": "fixture-compiler",
        "adapter_compiler_version": "v1",
        "adapter_compiler_hash": "c" * 64,
        "target_shot_id": shot.shot_id,
        "target_shot_revision": shot.revision,
        "target_shot_content_hash": shot.content_hash,
        "target_asset_role": "final_visual",
        "target_visual_strategy": "generated_video",
        "mode": VideoGenerationMode.TEXT_TO_VIDEO,
        "prompt_text": "A sealed fixture prompt.",
        "negative_prompt_text": "",
        "image_bindings": (),
        "output_requirement": VideoOutputRequirement(
            duration_seconds=1,
            width=64,
            height=64,
            fps=24,
            container="mp4",
            mime_type="video/mp4",
            native_audio=False,
        ),
        "seed": 7,
        "base_project": loaded.manifest.active_project,
        "base_registry": loaded.manifest.active_registry,
        "base_dependency_graph": loaded.manifest.active_dependency_graph,
        "input_artifact_ids": (shot.artifact_id,),
        "output_asset_id": "generated-video-shot-1",
    }
    values.update(changes or {})
    request = VideoGenerationRequest.create(**values)
    capability = VideoCapabilityVariant(
        capability_id="fixture-t2v-v1",
        provider_kind="fixture_t2v",
        model_id="fixture-t2v-1",
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        output=request.output_requirement,
        allowed_image_roles=(),
        required_first_frame=False,
        max_reference_count=0,
        allowed_image_mime_types=(),
        max_image_bytes=1,
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    return ResolvedVideoGenerationRequest.create(
        request=request,
        capability=capability,
        effective_output=request.output_requirement,
        effective_seed=request.seed,
        effective_negative_prompt_text="",
    )


def test_pre_generation_graph_is_exact_asset_free_and_submit_ready(
    tmp_path: Path,
) -> None:
    target, inputs, loaded = _activate_pre_generation_graph(tmp_path)
    graph = loaded.dependency_graph
    assert graph is not None
    target_id = generation_target_node_id(
        inputs.target_shot_id, inputs.target_asset_role
    )
    node = next(item for item in graph.nodes if item.node_id == target_id)
    state = next(
        item for item in loaded.manifest.dependency_states if item.node_id == target_id
    )

    assert node.kind is DependencyNodeKind.GENERATION_TARGET
    assert node.artifact_id == loaded.shots[0].artifact_id
    assert {item.kind for item in graph.nodes}.isdisjoint(
        {
            DependencyNodeKind.ASSET,
            DependencyNodeKind.COMPOSITION_SPEC,
            DependencyNodeKind.RESOLVED_TIMELINE,
            DependencyNodeKind.RENDERER_SOURCE,
            DependencyNodeKind.RENDER,
        }
    )
    assert state.lifecycle is DependencyLifecycle.STALE
    assert state.applied_evidence is None
    assert state.blocked_by == ()
    assert all(
        item.lifecycle is DependencyLifecycle.FRESH
        for item in loaded.manifest.dependency_states
        if item.node_id != target_id
    )

    before_manifest = (target / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError, match="execution binding"):
        ProductionStateCommitter(target).begin_video_generation(
            attempt_id="begin-exact-pre-generation",
            request=_resolved_request(loaded),
            execution_binding=None,
        )
    assert (target / "state/manifest.json").read_bytes() == before_manifest


def test_begin_rejects_noncanonical_authoring_graph_before_write(
    tmp_path: Path,
) -> None:
    _bootstrap_asset_free_project(tmp_path)
    target = tmp_path / "target"
    loaded = load_production_project(target / "project.yaml")
    shot = loaded.shots[0]
    inputs = VideoPreGenerationDependencyInputs(
        project=loaded,
        target_shot_id=shot.shot_id,
        target_asset_role="final_visual",
        requirement_hash=REQUIREMENT_HASH,
        planning_request_hash=PLANNING_REQUEST_HASH,
        verified_projection_hash=VERIFIED_PROJECTION_HASH,
    )
    canonical = build_video_pre_generation_dependency_graph(inputs)
    tampered = build_dependency_graph(
        canonical.nodes,
        tuple(
            edge
            for edge in canonical.edges
            if edge.contribution.key != "authoring.scene_visual"
        ),
    )
    desired = desired_fingerprints(tampered)
    applied = tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=tampered.revision_id,
            desired_fingerprint=desired[node.node_id],
            applied_fingerprint=desired[node.node_id],
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=loaded.manifest.active_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            ),
        )
        for node in tampered.nodes
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT
    )
    resolution = resolve_dependency_state(tampered, applied)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=None,
        candidate_graph=tampered,
        candidate_dependency_states=resolution.states,
        expected_desired_fingerprints=desired,
    )
    writer = ProductionStateCommitter(target)
    committed = writer.bootstrap_dependency_graph(
        attempt_id="bootstrap-tampered-pre-generation-graph",
        graph=tampered,
        transition=transition,
        expected_desired_fingerprints=desired,
    )
    writer.upgrade_manifest_schema(
        "2.7", expected_manifest_revision=committed.manifest_revision
    )
    reopened = load_production_project(target / "project.yaml")
    before_manifest = (target / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as exc_info:
        writer.begin_video_generation(
            attempt_id="reject-noncanonical-authoring-graph",
            request=_resolved_request(reopened),
            execution_binding=None,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (target / "state/manifest.json").read_bytes() == before_manifest
    assert tuple((target / "state").rglob("request.*.json")) == ()


@pytest.mark.parametrize(
    "mutation",
    (
        "base_project",
        "base_registry",
        "base_dependency_graph",
        "target_shot_revision",
        "target_shot_content_hash",
        "target_asset_role",
        "requirement_hash",
    ),
)
def test_begin_video_generation_rejects_pre_generation_lineage_drift_before_write(
    tmp_path: Path, mutation: str
) -> None:
    target, _, loaded = _activate_pre_generation_graph(tmp_path)
    current = getattr(loaded.manifest, mutation, None)
    if mutation == "base_project":
        current = loaded.manifest.active_project
        replacement = current.model_copy(
            update={
                "revision": current.revision + 1,
                "content_hash": "e" * 64,
                "path": Path(f"state/projects/project.{current.revision + 1}.{'e' * 64}.yaml"),
                "file_sha256": "e" * 64,
            }
        )
    elif mutation == "base_registry":
        current = loaded.manifest.active_registry
        replacement = current.model_copy(
            update={
                "revision_id": "e" * 64,
                "content_hash": "e" * 64,
                "path": Path(f"assets/registry.{'e' * 64}.json"),
                "file_sha256": "e" * 64,
            }
        )
    elif mutation == "base_dependency_graph":
        current = loaded.manifest.active_dependency_graph
        assert current is not None
        replacement = current.model_copy(
            update={
                "revision_id": "e" * 64,
                "content_hash": "e" * 64,
                "path": Path(f"state/dependency_graph.{'e' * 64}.json"),
                "file_sha256": "e" * 64,
            }
        )
    elif mutation == "target_shot_revision":
        replacement = loaded.shots[0].revision + 1
    elif mutation == "target_shot_content_hash":
        replacement = "e" * 64
    elif mutation == "target_asset_role":
        replacement = "wrong_visual"
    else:
        replacement = "e" * 64

    before_manifest = (target / "state/manifest.json").read_bytes()
    before_receipts = tuple((target / "state").rglob("request.*.json"))
    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(target).begin_video_generation(
            attempt_id=f"reject-{mutation.replace('_', '-')}",
            request=_resolved_request(loaded, changes={mutation: replacement}),
            execution_binding=None,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (target / "state/manifest.json").read_bytes() == before_manifest
    assert tuple((target / "state").rglob("request.*.json")) == before_receipts
