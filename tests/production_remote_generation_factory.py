"""Canonical project plus actual remote adapter decision fixtures (no transport)."""

import hashlib
from dataclasses import replace
from pathlib import Path

from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator, GenerationHistory, RegisteredGenerationTarget,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.video_requirement import (
    AmbienceIntent, AssetEvidence, AudioNeed, CapabilityNeed, GenerationMode,
    OutputGeometryPolicy, OutputNeed, Pacing, ProviderNeutralVideoRequirement, SemanticReferenceRole,
    VerifiedGenerationRequirementProjection,
)
from ai_video.production.models import (
    AssetRecord, AssetSourceKind, AssetType, ToolIdentity,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact, ProductionStateCommitter, _canonical_json_bytes,
    prepare_dependency_graph_transition, prepare_project_registry_commit,
)
from ai_video.production.project import load_production_project
from ai_video.production.video import VideoGenerationMode, VideoImageReferenceBinding
from test_production_shot_router import _asset
from ai_video.production.dependency import (
    build_production_dependency_graph, desired_fingerprints,
    resolve_dependency_state,
)
from production_project_factory import make_p8_video_generation_base
from production_generation_execution_factory import (
    activate_fixture_generation_qa_policy,
    activate_generated_video_shot,
)
from test_production_generation_decision import setup_decision
from tests.test_production_video_intent_validation import _complete_intent


def _register_remote_inputs(*, root, inputs, project, bindings, input_bytes):
    if not bindings:
        return project
    records = []
    artifacts = []
    for binding in bindings:
        raw = input_bytes[binding.asset_id]
        if hashlib.sha256(raw).hexdigest() != binding.asset_sha256 or len(raw) != binding.size_bytes:
            raise ValueError("fixture input bytes do not match the declared binding")
        is_image = isinstance(binding, VideoImageReferenceBinding)
        suffix = ".png" if is_image else ".mp4"
        path = Path(f"assets/files/{binding.asset_sha256}{suffix}")
        common = dict(
            asset_id=binding.asset_id,
            artifact_path=path,
            sha256=binding.asset_sha256,
            size_bytes=binding.size_bytes,
            mime_type=binding.mime_type,
            width=binding.width,
            height=binding.height,
            source_kind=AssetSourceKind.IMPORTED if is_image else AssetSourceKind.GENERATED,
            tool=ToolIdentity(name="vidu-test-input", version="1"),
            input_artifact_ids=(project.shots[0].artifact_id,),
            input_fingerprint=(canonical_sha256({"binding": binding.asset_id})
                               if is_image else "d" * 64),
            creation_receipt_id=f"fixture-{binding.asset_id}",
            usage_license="test-only",
        )
        if is_image:
            records.append(AssetRecord(asset_type=AssetType.IMAGE, **common))
        else:
            records.append(AssetRecord(
                asset_type=AssetType.VIDEO,
                duration_seconds=binding.duration_millis / 1000,
                source_kind=AssetSourceKind.IMPORTED,
                **{key: value for key, value in common.items() if key != "source_kind"},
            ))
        artifacts.append(PreparedArtifact(path, raw, hashlib.sha256(raw).hexdigest()))
    registry = project.registry.model_copy(update={
        "revision_id": "0" * 64, "content_hash": "0" * 64,
        "assets": (*project.registry.assets, *records),
    })
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": registry_hash, "content_hash": registry_hash})
    request = prepare_project_registry_commit(
        manifest=project.manifest, project=project.project, registry=registry,
        attempt_id="fixture-remote-generation-inputs",
    )
    candidate = project.model_copy(update={
        "registry": registry,
        "manifest": project.manifest.model_copy(update={"active_registry": request.next_registry}),
    })
    graph = build_production_dependency_graph(replace(inputs, project=candidate))
    states = resolve_dependency_state(graph, project.manifest.dependency_states).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=project.manifest.manifest_revision,
        base_dependency_graph=project.manifest.active_dependency_graph,
        candidate_graph=graph, candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_bytes = _canonical_json_bytes(graph)
    ProductionStateCommitter(root).commit(replace(
        request,
        dependency_graph_transition=transition,
        artifacts=tuple(sorted((*request.artifacts, *artifacts, PreparedArtifact(
            transition.candidate_dependency_graph.path, graph_bytes,
            hashlib.sha256(graph_bytes).hexdigest(),
        )), key=lambda item: item.relative_path.as_posix())),
    ))
    return load_production_project(root / "project.yaml")


def prepare_remote_generation(*, root, provider, request, compiler_id, compiler_version="2", input_bytes=None):
    """Author/activate the fixture Shot, then use the common production caller."""
    inputs = activate_generated_video_shot(
        root=root, inputs=make_p8_video_generation_base(root, schema_version="2.7"))
    project = inputs.project
    supplied = (*request.image_bindings, *request.media_bindings)
    if supplied:
        if input_bytes is None or set(input_bytes) != {item.asset_id for item in supplied}:
            raise ValueError("fixture remote inputs require exact bytes for every binding")
        project = _register_remote_inputs(
            root=root, inputs=inputs, project=project,
            bindings=supplied, input_bytes=input_bytes,
        )
    inputs = activate_fixture_generation_qa_policy(
        root=root,
        inputs=replace(inputs, project=project),
        output=request.output_requirement,
    )
    project = inputs.project
    shot = project.shots[0]
    scene = next(item for item in project.scenes if item.scene_id == shot.scene_id)
    setup = setup_decision(remote=True)
    context_updates = {
        "activated_shot": shot, "target_shot_id": shot.shot_id,
        "target_shot_revision": shot.revision, "target_shot_content_hash": shot.content_hash,
        "selected_registry_revision_id": project.manifest.active_registry.revision_id,
        "scene_content_hash": scene.content_hash,
    }
    output = request.output_requirement
    intent = _complete_intent().model_copy(update={
        "pacing": Pacing(shot_duration_seconds=output.duration_seconds),
        **({"ambience_intent": AmbienceIntent(environment_bed="none", explicitly_silent=True)}
           if not output.native_audio else {}),
    })
    if request.mode is VideoGenerationMode.REFERENCE_TO_VIDEO:
        role = SemanticReferenceRole.SCENE
        image = request.image_bindings[0]
        asset = _asset("scene_reference", image.asset_id, image.asset_sha256,
                       mime_type=image.mime_type, size_bytes=image.size_bytes,
                       width=image.width, height=image.height,
                       registry_revision_id=project.manifest.active_registry.revision_id).model_copy(
                           update={
                               "asset_id": image.asset_id,
                               "canonical_owner_id": shot.scene_id,
                               "canonical_owner_content_hash": scene.content_hash,
                           })
        context_updates["canonical_scene_reference"] = asset
        semantic_roles = (role,)
        evidence = (AssetEvidence(role=role, asset_id=asset.asset_id, asset_sha256=asset.asset_sha256,
                                  mime_type=asset.mime_type, width=asset.width, height=asset.height,
                                  size_bytes=asset.size_bytes),)
        capability_need = CapabilityNeed(needs_scene_reference=True, max_reference_count=1,
                                         accepts_remote_execution=True)
    elif request.mode is VideoGenerationMode.VIDEO_EXTEND:
        role = SemanticReferenceRole.VIDEO_REFERENCE
        binding = request.media_bindings[0]
        asset = _asset("reference_video", binding.asset_id, binding.asset_sha256,
                       mime_type=binding.mime_type, size_bytes=binding.size_bytes,
                       width=binding.width, height=binding.height,
                       duration_millis=binding.duration_millis, fps=binding.fps,
                       registry_revision_id=project.manifest.active_registry.revision_id).model_copy(
                           update={"asset_id": binding.asset_id})
        context_updates["reference_videos"] = (asset,)
        semantic_roles = (role,)
        evidence = (AssetEvidence(role=role, asset_id=asset.asset_id, asset_sha256=asset.asset_sha256,
                                  mime_type=asset.mime_type, width=asset.width, height=asset.height,
                                  size_bytes=asset.size_bytes, duration_millis=asset.duration_millis, fps=asset.fps),)
        capability_need = CapabilityNeed(accepts_remote_execution=True)
    else:
        semantic_roles, evidence, capability_need = (), (), CapabilityNeed(accepts_remote_execution=True)
    context = setup["context"].model_copy(update={
        **context_updates,
        "allowed_generation_modes": (request.mode,),
    })
    requirement = ProviderNeutralVideoRequirement.create(
        contract_version="provider-neutral-video-requirement/4",
        source_request_content_hash=canonical_sha256({"fixture_request": request.request_input_hash}),
        intent_evidence_hash=canonical_sha256({"shot": shot.content_hash}),
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        target_shot=shot, scene=scene,
        characters=tuple(c for c in project.characters if c.character_id in shot.character_ids),
        generation_mode=GenerationMode(request.mode.value), continuity_mode="none",
        motion_requirement="free_complex", generation_intent=intent,
        semantic_reference_roles=semantic_roles, asset_evidence=evidence, capability_need=capability_need,
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            geometry_policy=OutputGeometryPolicy(getattr(output, "dimension_mode", "exact")),
            width=output.width,
            height=output.height,
            aspect_ratio=getattr(output, "ratio", None),
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.REQUIRED if output.native_audio else AudioNeed.FORBIDDEN,
        quality_need=setup["projection"].requirement.quality_need,
    )
    projection = VerifiedGenerationRequirementProjection.create(
        requirement=requirement, plan_hash=canonical_sha256({"plan": shot.content_hash}),
        verified_source_request_content_hash=requirement.source_request_content_hash,
        target_shot_id=shot.shot_id, target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
    )
    lifecycle = setup["lifecycle"].model_copy(update={
        "generation_id": request.generation_id, "output_asset_id": request.output_asset_id,
        "target_asset_role": shot.required_asset_roles[0].role,
        "base_project": project.manifest.active_project,
        "base_registry": project.manifest.active_registry,
        "base_dependency_graph": project.manifest.active_dependency_graph,
        "input_artifact_ids": (shot.artifact_id, *(item.asset_id for item in supplied)),
    })
    acceptance = project.qa_policy.domain_acceptance
    assert acceptance is not None
    current = dict(projection=projection, context=context, policy=setup["policy"],
                   lifecycle=lifecycle, acceptance=acceptance)
    capabilities = provider.capabilities()
    limits = setup["inputs"].limits.model_copy(update={"allowed_remote_candidates": tuple(
        f"{capabilities.provider_name}/{v.capability_id}" for v in capabilities.variants
        if v.model_id == request.model_id)})
    prepared = GenerationFeedbackOrchestrator(
        targets=(RegisteredGenerationTarget(provider, request.provider_profile,
                 AdapterCompilerContract.create(compiler_id=compiler_id, compiler_version=compiler_version), output),),
        context_loader=lambda: current, history_loader=GenerationHistory,
        policy=DecisionPolicy(allow_bounded_exploration=True),
    ).prepare(limits=limits)
    assert prepared.execution_binding is not None, prepared
    return prepared
