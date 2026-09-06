"""Prepare the one approved local H3 I2VA S01 landscape preview.

This driver only creates canonical Production state.  It never submits to
ComfyUI; ``live_driver.py`` owns the separately requested runtime actions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_video.planning import (
    AssetRole,
    AvailableAsset,
    ProductionPolicyInput,
    ShotIntentEvidence,
    VideoPlanner,
    VideoPlanningRequest,
    require_current_video_plan,
)
from ai_video.production.comfy_t8_native_turbo_profile import (
    load_t8_native_turbo_execution_profile,
)
from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.image_import import (
    HumanImageImportReceipt,
    human_image_import_asset,
)
from ai_video.production.models import (
    ArtifactReference,
    VisualStrategy,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.shot_router import (
    RouterAssetIdentity,
    ShotRoutingContext,
    VideoGenerationLifecycleEnvelope,
)
from ai_video.production.state_commit import (
    ProductionStateCommitter,
    prepare_dependency_graph_transition,
)
from ai_video.production.video import ProviderProfilePointer, VideoFlexibleOutputRequirement, VideoGenerationMode
from ai_video.production.video_pre_generation import (
    VideoPreGenerationDependencyInputs,
    build_video_pre_generation_applied_evidence,
    build_video_pre_generation_dependency_graph,
)
from ai_video.production.video_requirement import (
    AudioNeed,
    ConditioningCompatibilityEvidence,
    ConditioningLane,
    GenerationIntent,
    GenerationOperation,
    OutputNeed,
    ProviderNeutralGenerationIntentProjection,
    QualityNeed,
    SemanticReferenceRole,
)


RUN = Path(__file__).resolve().parent
REPO = RUN.parent.parent
ROOT = RUN / "production"
SOURCE_ROOT = REPO / "runs/jieshi-e01-i2v-20260906-attempt01/production-s01-v1"
PROFILE_PATH = REPO / "workflows/profiles/minimax_h3_t8_i2va_turbo_native_v2.json"
ATTEMPT = "jieshi-s01-h3-horizontal-bootstrap-001"
GRAPH_ATTEMPT = "jieshi-s01-h3-horizontal-graph-001"
GENERATION_ID = "jieshi-s01-h3-horizontal-generation-001"
OUTPUT_ASSET_ID = "jieshi-s01-h3-horizontal-raw-video-001"


def _reference(value, path: Path) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=value.artifact_id,
        revision=value.revision,
        content_hash=value.content_hash,
        path=path,
    )


def _receipt() -> HumanImageImportReceipt:
    path = RUN / "image-import-receipt.json"
    if not path.is_file():
        raise ValueError(
            "image-import-receipt.json is required after the user approves the exact image."
        )
    receipt = HumanImageImportReceipt.model_validate_json(path.read_bytes())
    if (
        receipt.source_surface != "codex_imagegen_tool"
        or receipt.target_kind != "key_shot"
        or receipt.target_artifact_id != "jieshi-e01-S01"
        or receipt.target_asset_role != "first_frame"
    ):
        raise ValueError("Image import receipt is not the approved Codex ImageGen S01 first frame.")
    return receipt


def _bootstrap_and_import():
    from dataclasses import replace
    from ai_video.production.image_import import prepare_human_image_import_commit, validate_human_image_import
    from ai_video.production.state_commit import prepare_project_registry_commit, PreparedArtifact
    from ai_video.production._state_commit_common import _canonical_yaml_bytes

    receipt = _receipt()
    image_bytes = (RUN / "first-frame.png").read_bytes()
    validate_human_image_import(receipt, image_bytes)
    source = load_production_project(SOURCE_ROOT / "project.yaml")
    writer = ProductionStateCommitter(ROOT)
    if not (ROOT / "project.yaml").exists():
        if ROOT.exists() and any(ROOT.iterdir()):
            raise ValueError("Nonempty uninitialized production root requires explicit recovery")
        shot = seal_artifact(source.shots[0].model_copy(update={
            "revision": source.shots[0].revision + 1, "creation_receipt_id": ATTEMPT,
            "duration_policy": source.shots[0].duration_policy.model_copy(update={"seconds": 124/24}),
        }))
        shot_path = Path(f"creative/shots/{shot.artifact_id}-horizontal-r{shot.revision}.yaml")
        project = seal_artifact(source.project.model_copy(update={
            "revision": source.project.revision + 1, "creation_receipt_id": ATTEMPT,
            "title": "界蚀 S01 本地 H3 横屏试片",
            "delivery_profile": source.project.delivery_profile.model_copy(update={"width": 1344, "height": 768, "fps": 24}),
            "artifacts": source.project.artifacts.model_copy(update={"shots": (_reference(shot, shot_path),)}),
        }))
        refs = source.project.artifacts
        models = {refs.brief.path: source.brief, refs.story.path: source.story,
                  refs.storyboard.path: source.storyboard, shot_path: shot}
        models.update({ref.path: item for ref, item in zip(refs.characters, source.characters, strict=True)})
        models.update({ref.path: item for ref, item in zip(refs.scenes, source.scenes, strict=True)})
        artifacts = [writer.prepare_artifact(ATTEMPT, path, _canonical_yaml_bytes(model)) for path, model in models.items()]
        for asset in source.registry.assets:
            artifacts.append(writer.prepare_artifact(ATTEMPT, asset.artifact_path, (SOURCE_ROOT / asset.artifact_path).read_bytes()))
        # Preserve original imported evidence bytes without inventing new source approval.
        for path in (SOURCE_ROOT / "state/images/import-receipts").glob("*.json"):
            artifacts.append(writer.prepare_artifact(ATTEMPT, path.relative_to(SOURCE_ROOT), path.read_bytes()))
        ROOT.mkdir(exist_ok=True)
        writer.bootstrap_initial_state(attempt_id=ATTEMPT, project=project, registry=source.registry, artifacts=tuple(artifacts))
    loaded = load_production_project(ROOT / "project.yaml")
    if loaded.manifest.schema_version == "2.0":
        writer.upgrade_manifest_schema("2.7", expected_manifest_revision=loaded.manifest.manifest_revision)
        loaded = load_production_project(ROOT / "project.yaml")
    asset = human_image_import_asset(receipt)
    if asset.asset_id in {item.asset_id for item in loaded.registry.assets}:
        if asset.asset_id not in next(r.asset_ids for r in loaded.shots[0].required_asset_roles if r.role == "first_frame"):
            raise ValueError("Previously imported first frame is not selected")
        return loaded
    shot = seal_artifact(loaded.shots[0].model_copy(update={
        "revision": loaded.shots[0].revision+1, "creation_receipt_id": receipt.content_hash,
        "required_asset_roles": tuple(r.model_copy(update={"asset_ids": (asset.asset_id,)}) if r.role == "first_frame" else r for r in loaded.shots[0].required_asset_roles),
    }))
    path = Path(f"creative/shots/{shot.artifact_id}-horizontal-r{shot.revision}.yaml")
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision+1, "creation_receipt_id": receipt.content_hash,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": (_reference(shot, path),)}),
    }))
    registry = loaded.registry.model_copy(update={"assets": (*loaded.registry.assets, asset), "revision_id":"0"*64,"content_hash":"0"*64})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id":digest,"content_hash":digest})
    commit = prepare_project_registry_commit(manifest=loaded.manifest,project=project,registry=registry,attempt_id="jieshi-h3-horizontal-image-import-001")
    payload = _canonical_yaml_bytes(shot)
    commit = replace(commit, artifacts=(*commit.artifacts, PreparedArtifact(path,payload,hashlib.sha256(payload).hexdigest())))
    candidate = loaded.model_copy(update={"project":project,"shots":(shot,),"registry":registry,
        "asset_paths":{**loaded.asset_paths,asset.asset_id:ROOT/asset.artifact_path},
        "manifest":loaded.manifest.model_copy(update={"active_project":commit.next_project,"active_registry":commit.next_registry})})
    inputs = resolve_material(candidate)["dependency_inputs"]
    graph = build_video_pre_generation_dependency_graph(inputs)
    states = resolve_dependency_state(graph,build_video_pre_generation_applied_evidence(inputs)).states
    transition = prepare_dependency_graph_transition(expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,candidate_graph=graph,
        candidate_dependency_states=states,expected_desired_fingerprints=desired_fingerprints(graph))
    graph_payload = (json.dumps(graph.model_dump(mode="json"),ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
    commit = replace(commit, dependency_graph_transition=transition, artifacts=(*commit.artifacts,
        PreparedArtifact(transition.candidate_dependency_graph.path,graph_payload,hashlib.sha256(graph_payload).hexdigest())))
    commit = prepare_human_image_import_commit(base=loaded,receipt=receipt,image_bytes=image_bytes,candidate_target=shot,candidate_project=project,base_commit=commit)
    writer.commit(commit)
    return load_production_project(ROOT / "project.yaml")


def ensure_prepared():
    loaded = _bootstrap_and_import()
    writer = ProductionStateCommitter(ROOT)
    material = resolve_material(loaded)
    if loaded.manifest.active_dependency_graph is None:
        graph = build_video_pre_generation_dependency_graph(material["dependency_inputs"])
        states = resolve_dependency_state(graph, build_video_pre_generation_applied_evidence(material["dependency_inputs"])).states
        transition = prepare_dependency_graph_transition(expected_manifest_revision=loaded.manifest.manifest_revision,
            base_dependency_graph=None,candidate_graph=graph,candidate_dependency_states=states,expected_desired_fingerprints=desired_fingerprints(graph))
        writer.bootstrap_dependency_graph(attempt_id=GRAPH_ATTEMPT,graph=graph,transition=transition,expected_desired_fingerprints=desired_fingerprints(graph))
        loaded = load_production_project(ROOT / "project.yaml")
    if loaded.manifest.schema_version != "2.7":
        writer.upgrade_manifest_schema("2.7",expected_manifest_revision=loaded.manifest.manifest_revision)
    return load_prepared()


def resolve_material(loaded):
    shot = next(item for item in loaded.shots if item.shot_id == "S01")
    scene = next(item for item in loaded.scenes if item.scene_id == shot.scene_id)
    first_frame, = (
        item for item in loaded.registry.assets
        if item.asset_id in next(role.asset_ids for role in shot.required_asset_roles if role.role == "first_frame")
    )
    intent = GenerationIntent.model_validate_json((RUN / "intent.json").read_bytes())
    compatibility = ConditioningCompatibilityEvidence(
        lane=ConditioningLane.I2VA, first_anchor_id=first_frame.asset_id,
        same_subject_scale=True, composition_compatible=True,
        screen_order_compatible=True, axis_compatible=True,
        camera_path_reachable=True, character_prop_state_reachable=True,
        action_endpoint_reachable=True, available_duration_seconds=124 / 24,
    )
    projection = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=intent, conditioning_compatibility=compatibility,
        generation_operation=GenerationOperation.AUTO,
        semantic_reference_roles=(SemanticReferenceRole.FIRST_FRAME,),
        output_need=OutputNeed(timing_mode="frame_count", frame_count=124, width=1344,
            height=768, aspect_ratio="16:9", fps=24, container_mime="video/mp4"),
        audio_need=AudioNeed.REQUIRED, quality_need=QualityNeed(objective_tier="preview"),
    )
    planning = VideoPlanningRequest.create(
        request_id="jieshi-s01-h3-horizontal-plan-001", target_shot=shot,
        character_context=tuple(sorted((item for item in loaded.characters if item.character_id in shot.character_ids), key=lambda item: item.character_id)),
        scene_context=scene,
        available_assets=(AvailableAsset(role=AssetRole.APPROVED_KEYFRAME,
            asset_id=first_frame.asset_id, asset_sha256=first_frame.sha256,
            canonical_owner_id=shot.shot_id, canonical_owner_content_hash=shot.content_hash,
            mime_type=first_frame.mime_type, width=first_frame.width, height=first_frame.height,
            size_bytes=first_frame.size_bytes),),
        previous_shot_state=None,
        shot_intent_evidence=ShotIntentEvidence(target_shot_id=shot.shot_id,
            target_shot_content_hash=shot.content_hash, character_action_required=True,
            continuous_action_required=True, state_change_required=True,
            subject_motion_directive_present=True), review_decision=None,
        production_policy=ProductionPolicyInput(local_resources_available=True,
            remote_authorized=False, budget_authorized=False, quality_preference="preview"),
        generation_intent=projection, planning_contract_version="video-planner/3",
    )
    plan = VideoPlanner().plan(planning)
    verified = require_current_video_plan(current_request=planning, plan=plan)
    requirement = verified.requirement
    profile = load_t8_native_turbo_execution_profile(PROFILE_PATH, artifact_root=REPO)
    provider_pointer = ProviderProfilePointer(
        profile_id=profile.capability_id, profile_version="v2",
        profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
        profile_sha256=profile.profile_content_hash,
    )
    policy_data = json.loads((RUN / "budget.json").read_bytes())
    context = ShotRoutingContext(
        activated_shot=shot, target_shot_id=shot.shot_id, target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash, storyboard_revision=loaded.storyboard.revision,
        storyboard_content_hash=loaded.storyboard.content_hash,
        selected_registry_revision_id=loaded.registry.revision_id,
        character_bible_content_hashes=tuple(item.content_hash for item in planning.character_context),
        important_character_ids=shot.character_ids, scene_content_hash=scene.content_hash,
        canonical_character_references=(), canonical_scene_reference=None,
        approved_existing_video=None,
        shot_keyframe=RouterAssetIdentity(role="first_frame", asset_id=first_frame.asset_id,
            asset_sha256=first_frame.sha256, source_registry_revision_id=loaded.registry.revision_id,
            mime_type=first_frame.mime_type, size_bytes=first_frame.size_bytes,
            width=first_frame.width, height=first_frame.height),
        upstream_terminal=None, motion_requirement=requirement.motion_requirement.value,
        continuity_mode="none", semantic_continuity_state=None,
        allowed_visual_strategies=(VisualStrategy.GENERATED_VIDEO,),
        allowed_generation_modes=(VideoGenerationMode.IMAGE_TO_VIDEO,),
    )
    output = VideoFlexibleOutputRequirement(timing_mode="frame_count", frame_count=124,
        dimension_mode="exact", width=1344, height=768, resolution_label="h3_t8_native",
        ratio="16:9", fps=24, container="mp4", mime_type="video/mp4", native_audio=True)
    lifecycle = VideoGenerationLifecycleEnvelope(
        generation_id=GENERATION_ID, target_asset_role="final_visual",
        base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id, first_frame.asset_id), output_asset_id=OUTPUT_ASSET_ID,
    ) if loaded.manifest.active_dependency_graph is not None else None
    return {"planning": planning, "plan": plan, "verified": verified, "profile": profile,
            "routing_inputs": (context, policy_data, provider_pointer, output, lifecycle),
            "dependency_inputs": VideoPreGenerationDependencyInputs(project=loaded,
                target_shot_id=shot.shot_id, target_asset_role="final_visual",
                requirement_hash=requirement.requirement_hash,
                planning_request_hash=planning.request_content_hash,
                verified_projection_hash=verified.projection_hash)}


def load_prepared():
    loaded = load_production_project(ROOT / "project.yaml")
    if loaded.manifest.schema_version != "2.7" or loaded.manifest.active_dependency_graph is None:
        raise ValueError("Production is not prepared through the required dependency graph and schema.")
    return resolve_material(loaded)
