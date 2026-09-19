from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

from ai_video.production.commercial_execution import (
    project_generated_commercial_shot_binding,
)
from ai_video.production.composition_contracts import RendererIdentity, RendererKind
from ai_video.production.dependency import (
    ProductionDependencyInputs,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.ecommerce_job import (
    EcommerceProductionJobService,
    EcommerceShotExecutionInput,
    EcommerceShotExecutionPlan,
)
from ai_video.production.ecommerce_job_contracts import EcommerceJobNextAction
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ai_video.production.ecommerce_media_acceptance import (
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.hyperframes import probe_clip_fd
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    EgressMetadata,
    ToolIdentity,
)
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_dependency_graph_transition,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoOutputRequirement,
    VideoProviderCapabilities,
)
from ai_video.production.video_candidate_composition import (
    build_video_candidate_composition_spec,
)
from ai_video.production.video_generation import VideoGenerationService
from production_generation_execution_factory import (
    activate_fixture_generation_qa_policy,
    prepare_generation_execution,
)
from production_project_factory import make_p8_video_candidate_preparer
from test_production_commercial_visual_review import (
    REVIEW_TOOL,
    _policy as _commercial_policy,
)
from test_production_ecommerce_job import (
    _request,
    _two_shot_execution,
    _two_shot_runtime_handoff,
)
from test_production_generated_video_e2e import (
    COMMERCIAL_EVALUATOR,
    FIXTURE,
    _CountingCommercialShotReviewer,
)
from test_production_local_video_state import LocalVideoProviderDouble


OUTPUT = VideoOutputRequirement(
    duration_seconds=1,
    width=64,
    height=64,
    fps=24,
    container="mp4",
    mime_type="video/mp4",
    native_audio=False,
)


def _bootstrapped_canonical_job(root: Path):
    handoff = _two_shot_runtime_handoff()
    request = _request(root, handoff, attempts=2)
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id=request.expected_project_id,
    )
    assets = []
    prepared = []
    for shot_id in ("shot-hero", "shot-proof"):
        payload = f"offline-placeholder:{shot_id}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        asset = AssetRecord(
            asset_id=f"image-{shot_id}",
            asset_type=AssetType.IMAGE,
            artifact_path=canonical_image_asset_path(digest),
            sha256=digest,
            size_bytes=len(payload),
            mime_type="image/png",
            width=64,
            height=64,
            source_kind=AssetSourceKind.IMPORTED,
            tool=ToolIdentity(name="fixture", version="1"),
            input_fingerprint=digest,
            creation_receipt_id=f"fixture-{shot_id}",
            usage_license="fixture",
            egress=EgressMetadata(remote=False),
        )
        assets.append(asset)
        prepared.append(PreparedArtifact(asset.artifact_path, payload, digest))
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=tuple(assets),
    )
    registry_hash = registry_semantic_sha256(registry)
    compiled = replace(
        compiled,
        registry=registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        ),
        artifacts=(*compiled.artifacts, *prepared),
    )
    bootstrap_ecommerce_production_project(
        root,
        attempt_id="ecommerce-canonical-two-shot-bootstrap",
        compiled=compiled,
    )
    skeleton = _two_shot_execution(handoff, project_root=root.resolve())
    base_spec = skeleton.handoff.composition_spec
    canonical_spec = seal_artifact(
        base_spec.model_copy(
            update={
                "revision": base_spec.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "ecommerce-canonical-two-shot-composition",
                "layers": tuple(
                    layer.model_copy(update={"asset_role": "final_visual"})
                    for layer in base_spec.layers
                ),
            }
        )
    )
    skeleton = replace(
        skeleton,
        handoff=skeleton.handoff.model_copy(
            update={"composition_spec": canonical_spec}
        ),
    )
    return handoff, request, skeleton


def _dependency_inputs(root: Path, execution) -> ProductionDependencyInputs:
    return ProductionDependencyInputs(
        project=load_production_project(root / "project.yaml"),
        composition_spec=execution.handoff.composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(),
    )


def _activate_offline_ecommerce_policy(
    root: Path,
    inputs: ProductionDependencyInputs,
) -> ProductionDependencyInputs:
    committer = ProductionStateCommitter(root)
    manifest = committer._read_manifest()
    graph = build_production_dependency_graph(inputs)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=manifest.manifest_revision,
        base_dependency_graph=manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=resolve_dependency_state(graph, ()).states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    committer.bootstrap_dependency_graph(
        attempt_id="bootstrap-ecommerce-job-canonical-e2e-graph",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    current = committer._read_manifest()
    committer.upgrade_manifest_schema(
        "2.13",
        expected_manifest_revision=current.manifest_revision,
    )
    inputs = replace(
        inputs,
        project=load_production_project(root / "project.yaml"),
    )
    profile = create_qingyan_ecommerce_acceptance_profile()
    policy = _commercial_policy()
    policy = seal_artifact(
        policy.model_copy(
            update={
                "artifact_id": "qa-policy-ecommerce-job-canonical-e2e",
                "revision": policy.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "qa-policy-ecommerce-job-canonical-e2e",
                "semantic_authorities": (REVIEW_TOOL, COMMERCIAL_EVALUATOR),
                "domain_acceptance": DomainAcceptancePolicy(
                    domain_id="ecommerce",
                    profile_id=profile.profile_id,
                    profile_version=profile.profile_version,
                    profile_content_hash=profile.content_hash,
                    profile_payload=profile.model_dump(mode="json"),
                    measurement_contract_version=profile.measurement_contract_version,
                    required_requirement_ids=profile.required_requirement_ids,
                ),
            }
        )
    )
    current = committer._read_manifest()
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=current.manifest_revision,
        attempt_id="activate-ecommerce-job-canonical-e2e-policy",
    )
    refreshed = replace(
        inputs,
        project=load_production_project(root / "project.yaml"),
    )
    return activate_fixture_generation_qa_policy(
        root=root,
        inputs=refreshed,
        output=OUTPUT,
    )


def _real_input(
    *,
    root: Path,
    execution,
    shot_id: str,
    composition_spec,
) -> tuple[EcommerceShotExecutionInput, LocalVideoProviderDouble]:
    loaded = load_production_project(root / "project.yaml")
    inputs = ProductionDependencyInputs(
        project=loaded,
        composition_spec=composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(),
    )
    shot = next(item for item in loaded.shots if item.shot_id == shot_id)
    projection = next(
        item
        for item in execution.handoff.commercial_execution_projections
        if item.target_shot_id == shot_id
    )
    profile = create_qingyan_ecommerce_acceptance_profile()
    output_asset_id = f"canonical-ecommerce-{shot_id}-video"
    commercial_binding = project_generated_commercial_shot_binding(
        projection,
        profile=profile,
        applicable_requirement_ids=(
            "shot.identity.main_character",
            "shot.motion.required",
            "shot.camera.intent",
        ),
        approved_source=None,
        expected_actor_ids=projection.character_requirement_ids,
        output_asset_id=output_asset_id,
    )
    provider_kind = "offline-local-ecommerce"
    model_id = "offline-local-fixture"
    request = VideoGenerationRequest.create(
        generation_id=f"canonical-ecommerce-{shot_id}-generation",
        provider_name=provider_kind,
        provider_kind=provider_kind,
        model_id=model_id,
        provider_profile=ProviderProfilePointer(
            profile_id="offline-local-ecommerce-profile",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{'a' * 64}.json"),
            profile_sha256="a" * 64,
        ),
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        target_asset_role=shot.required_asset_roles[0].role,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        prompt_text=f"Render deterministic offline Ecommerce Shot {shot_id}.",
        negative_prompt_text="",
        image_bindings=(),
        commercial_binding=commercial_binding,
        output_requirement=OUTPUT,
        seed=19,
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id,),
        output_asset_id=output_asset_id,
    )
    variant = VideoCapabilityVariant(
        capability_id="offline-local-ecommerce-t2v",
        provider_kind=provider_kind,
        model_id=model_id,
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        output=OUTPUT,
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
    provider = LocalVideoProviderDouble(
        capabilities=VideoProviderCapabilities.create(
            provider_name=provider_kind,
            variants=(variant,),
        ),
        artifact_bytes=FIXTURE.read_bytes(),
        native_prompt_text=request.prompt_text,
    )
    prepared = prepare_generation_execution(
        project=loaded,
        provider=provider,
        request=provider.resolve(request),
        task_id=f"canonical-ecommerce-{shot_id}",
        compiler_id="local-video-state-fixture",
        compiler_version="1",
    )
    service = VideoGenerationService(
        committer=ProductionStateCommitter(
            root,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    )
    return (
        EcommerceShotExecutionInput(
            shot_id=shot_id,
            attempt_id=f"canonical-ecommerce-{shot_id}-attempt",
            service=service,
            request=prepared.resolved,
            lane="local",
            commercial_reviewer=_CountingCommercialShotReviewer(),
            probe=probe_clip_fd,
            execution_binding=prepared.binding,
        ),
        provider,
    )


def test_canonical_two_shot_reopen_resumes_second_and_replay_has_zero_effects(
    tmp_path: Path,
) -> None:
    handoff, request, skeleton = _bootstrapped_canonical_job(tmp_path)
    inputs = _activate_offline_ecommerce_policy(
        tmp_path,
        _dependency_inputs(tmp_path, skeleton),
    )
    base_spec = inputs.composition_spec
    first_input, first_provider = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-hero",
        composition_spec=base_spec,
    )
    second_declared, _ = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-proof",
        composition_spec=base_spec,
    )
    first_factory_calls: list[str] = []

    def interrupt_after_first(shot_id: str):
        first_factory_calls.append(shot_id)
        if shot_id == "shot-proof":
            loaded = load_production_project(tmp_path / "project.yaml")
            assert any(
                item.asset_id == "canonical-ecommerce-shot-hero-video"
                for item in loaded.registry.assets
            )
            raise ValueError("simulated process interruption before Shot 2 binding")
        return first_input

    first_plan = replace(
        skeleton,
        shots=(first_input, second_declared),
        input_factory=interrupt_after_first,
    )
    interrupted = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=first_plan,
    )

    assert interrupted.next_action is EcommerceJobNextAction.BLOCKED
    assert first_factory_calls == ["shot-hero", "shot-proof"]
    assert first_provider.submit_calls == 1
    assert first_provider.fetch_calls == 1

    after_first_spec = build_video_candidate_composition_spec(
        base_spec,
        target_shot_id="shot-hero",
        target_asset_role=first_input.request.activation_scope.request.target_asset_role,
        output_asset_id="canonical-ecommerce-shot-hero-video",
    )
    reopened_first, _ = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-hero",
        composition_spec=after_first_spec,
    )
    reopened_second, second_provider = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-proof",
        composition_spec=after_first_spec,
    )
    resumed_factory_calls: list[str] = []

    def resume_second_only(shot_id: str):
        assert shot_id != "shot-hero"
        resumed_factory_calls.append(shot_id)
        return reopened_second

    resumed_plan = replace(
        skeleton,
        shots=(reopened_first, reopened_second),
        input_factory=resume_second_only,
    )
    reopened_job = EcommerceProductionJobService()
    before_resume = reopened_job.inspect(
        request,
        handoff,
        shot_execution=resumed_plan,
    )
    resumed = reopened_job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=resumed_plan,
    )

    assert before_resume.next_action is EcommerceJobNextAction.GENERATE_SHOT
    assert before_resume.next_shot_id == "shot-proof"
    assert resumed.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert resumed_factory_calls == ["shot-proof"]
    assert second_provider.submit_calls == 1
    assert second_provider.fetch_calls == 1

    manifest_before_replay = (tmp_path / "state/manifest.json").read_bytes()
    replay_factory_calls: list[str] = []
    replay_plan = replace(
        resumed_plan,
        input_factory=lambda shot_id: replay_factory_calls.append(shot_id),
    )
    replay = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=replay_plan,
    )

    assert replay.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert replay_factory_calls == []
    assert first_provider.submit_calls == 1
    assert first_provider.fetch_calls == 1
    assert second_provider.submit_calls == 1
    assert second_provider.fetch_calls == 1
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before_replay
    final = load_production_project(tmp_path / "project.yaml")
    assert {
        item.asset_id
        for item in final.registry.assets
        if item.asset_id.startswith("canonical-ecommerce-")
    } == {
        "canonical-ecommerce-shot-hero-video",
        "canonical-ecommerce-shot-proof-video",
    }
