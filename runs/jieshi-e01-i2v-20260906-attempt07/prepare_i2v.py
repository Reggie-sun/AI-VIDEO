"""Bind registered S01 input and prepare one canonical Vidu request; no network."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import yaml

from ai_video.planning import AssetRole, AvailableAsset, VideoPlanner, VideoPlanningRequest, require_current_video_plan
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import ArtifactReference, AssetRoleRequirement, AssetType
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, prepare_project_registry_commit, prepare_dependency_graph_transition
from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
from ai_video.production.video_pre_generation import VideoPreGenerationDependencyInputs, build_video_pre_generation_dependency_graph, build_video_pre_generation_applied_evidence
from ai_video.production.shot_router import VideoGenerationResolver, ShotRoutingContext, VideoRoutingPolicy, RouterPolicyIdentity, RouterAssetIdentity, VideoGenerationLifecycleEnvelope, AdapterCompilerContract
from ai_video.production.video import VideoFlexibleOutputRequirement
from ai_video.production.video_compiler import require_compiled_provider_request
from ai_video.production.video_requirement import ProviderNeutralGenerationIntentProjection
from ai_video.production.video_requirement import SemanticReferenceRole
from ai_video.production.vidu import ViduVideoProvider
from ai_video.production.vidu_profile import ViduProviderProfile

RUN = Path(__file__).resolve().parent
SOURCE_RUN = RUN.parent / "jieshi-e01-i2v-20260906-attempt01"
ROOT = RUN / "production-s01-v7"
PREP = RUN / "preparation-v1"
SOURCE_SHA = "4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb"
ATTEMPT = "jieshi-s01-repair-first-frame-attempt07"


def save(name, value):
    data = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    (PREP / name).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def forbidden(*args, **kwargs):
    raise RuntimeError("Offline preparation cannot access transport or credentials")


def planning(loaded, source):
    prior = VideoPlanningRequest.model_validate_json((SOURCE_RUN / "planning-request-v2.json").read_bytes())
    shot = loaded.shots[0]
    intent_data = {key: getattr(prior.generation_intent, key) for key in type(prior.generation_intent).model_fields if key != "projection_hash"}
    # Raster is sealed by output_requirement.resolution_label and measured after fetch.
    # The compiler does not implement the separate quality.minimum_raster hint.
    intent_data["quality_need"] = prior.generation_intent.quality_need.model_copy(update={"minimum_raster": None})
    intent_data["audio_need"] = type(prior.generation_intent.audio_need)("required")
    intent_data["semantic_reference_roles"] = (SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.LAST_FRAME)
    endpoint_role = next(r for r in shot.required_asset_roles if r.role == "last_frame")
    endpoint, = (a for a in loaded.registry.assets if a.asset_id in endpoint_role.asset_ids)
    if endpoint.sha256 != "059bb2b261883190168057b35baafc90011866acba9fb64b1c9c186122861330":
        raise RuntimeError("Approved repaired endpoint must be canonically imported before planning")
    gi = prior.generation_intent.generation_intent
    draft = json.loads((RUN / "request-draft.json").read_text())
    scene = gi.scene_continuity.model_copy(update={"state_constraints": (draft["prompt_draft"],), "time_of_day": "深夜"})
    intent_data["generation_intent"] = gi.model_copy(update={
        "scene_continuity": scene,
        "subject_action": gi.subject_action.model_copy(update={"progression": draft["action_progression"]}),
        "camera_intent": gi.camera_intent.model_copy(update={
            "stability": draft["camera_stability"], "framing_intent": draft["camera_framing"],
        }),
    })
    intent = ProviderNeutralGenerationIntentProjection.create(**intent_data)
    data = prior.model_dump()
    data.update(
        request_id="jieshi-e01-s01-i2v-plan-attempt07",
        generation_intent=intent,
        production_policy=prior.production_policy.model_copy(update={"remote_authorized": True, "budget_authorized": True}),
        target_shot=shot,
        available_assets=(AvailableAsset(
            role=AssetRole.APPROVED_KEYFRAME, asset_id=source.asset_id,
            asset_sha256=source.sha256, canonical_owner_id=shot.shot_id,
            canonical_owner_content_hash=shot.content_hash, mime_type=source.mime_type,
            width=941, height=1672, size_bytes=source.size_bytes,
        ), AvailableAsset(
            role=AssetRole.LAST_FRAME, asset_id=endpoint.asset_id,
            asset_sha256=endpoint.sha256, canonical_owner_id=shot.shot_id,
            canonical_owner_content_hash=shot.content_hash, mime_type=endpoint.mime_type,
            width=endpoint.width, height=endpoint.height, size_bytes=endpoint.size_bytes,
        )),
        shot_intent_evidence=prior.shot_intent_evidence.model_copy(update={
            "target_shot_content_hash": shot.content_hash,
        }),
    )
    data.pop("request_content_hash")
    request = VideoPlanningRequest.create(**data)
    plan = VideoPlanner().plan(request)
    verified = require_current_video_plan(current_request=request, plan=plan)
    return request, plan, verified


def main():
    PREP.mkdir(exist_ok=False)
    loaded = load_production_project(ROOT / "project.yaml")
    source, = (a for a in loaded.registry.assets if a.sha256 == SOURCE_SHA)
    assert hashlib.sha256((ROOT / source.artifact_path).read_bytes()).hexdigest() == SOURCE_SHA
    assert not any(a.attempt_id == ATTEMPT for a in loaded.manifest.attempts)
    old_shot = loaded.shots[0]
    assert old_shot.shot_id == "S01"
    bound = tuple(r for r in old_shot.required_asset_roles if r.role == "first_frame")
    if bound:
        assert len(bound) == 1 and bound[0].asset_ids == (source.asset_id,)
        shot, project = old_shot, loaded.project
        path = project.artifacts.shots[0].path
    else:
        assert len(old_shot.required_asset_roles) == 1
        shot = seal_artifact(old_shot.model_copy(update={
            "revision": old_shot.revision + 1,
            "creation_receipt_id": ATTEMPT,
            "required_asset_roles": (*old_shot.required_asset_roles, AssetRoleRequirement(
                role="first_frame", asset_ids=(source.asset_id,), allowed_asset_types=(AssetType.IMAGE,),
            )),
        }))
        path = Path("creative/shots") / f"{shot.artifact_id}-r{shot.revision}.yaml"
        ref = ArtifactReference(artifact_id=shot.artifact_id, revision=shot.revision, content_hash=shot.content_hash, path=path)
        project = seal_artifact(loaded.project.model_copy(update={
            "revision": loaded.project.revision + 1, "creation_receipt_id": ATTEMPT,
            "artifacts": loaded.project.artifacts.model_copy(update={"shots": (ref,)}),
        }))
    commit = prepare_project_registry_commit(manifest=loaded.manifest, project=project, registry=loaded.registry, attempt_id=ATTEMPT)
    candidate = loaded.model_copy(update={
        "project": project, "shots": (shot,), "dependency_graph": None,
        "manifest": loaded.manifest.model_copy(update={"active_project": commit.next_project, "active_registry": commit.next_registry}),
    })
    request, plan, verified = planning(candidate, source)
    inputs = VideoPreGenerationDependencyInputs(
        project=candidate, target_shot_id="S01", target_asset_role="final_visual",
        requirement_hash=verified.requirement.requirement_hash,
        planning_request_hash=request.request_content_hash, verified_projection_hash=verified.projection_hash,
    )
    graph = build_video_pre_generation_dependency_graph(inputs)
    states = resolve_dependency_state(graph, build_video_pre_generation_applied_evidence(inputs)).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph, candidate_graph=graph,
        candidate_dependency_states=states, expected_desired_fingerprints=desired_fingerprints(graph),
    )
    shot_bytes = yaml.safe_dump(shot.model_dump(mode="json"), allow_unicode=True, sort_keys=True).encode()
    graph_bytes = (json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    artifacts = (*commit.artifacts, PreparedArtifact(path, shot_bytes, hashlib.sha256(shot_bytes).hexdigest()),
                 PreparedArtifact(transition.candidate_dependency_graph.path, graph_bytes, hashlib.sha256(graph_bytes).hexdigest()))
    commit = replace(commit, artifacts=tuple(sorted(artifacts, key=lambda a: a.relative_path.as_posix())), dependency_graph_transition=transition)
    writer = ProductionStateCommitter(ROOT)
    writer.commit(commit)
    loaded = load_production_project(ROOT / "project.yaml")
    reopened = planning(loaded, source)
    assert reopened == (request, plan, verified)
    for name, obj in (("planning-request.json", request), ("video-plan.json", plan), ("verified-requirement.json", verified)):
        save(name, obj)
    if loaded.manifest.schema_version == "2.5":
        writer.upgrade_manifest_schema("2.7", expected_manifest_revision=loaded.manifest.manifest_revision)
        loaded = load_production_project(ROOT / "project.yaml")
    finish_request(loaded, source, request, verified)


def finish_request(loaded, source, request, verified):
    shot = loaded.shots[0]
    profile = ViduProviderProfile.model_validate_json((RUN / "provider-profile.json").read_bytes())
    provider = ViduVideoProvider(profile=profile, transport=None, credential=forbidden)
    policy_data = {"user_instruction": "继续生成", "provider": "vidu", "model": "viduq3-pro",
                   "max_submit_count": 1, "scope": "S01 real first-frame I2V", "input_sha256": SOURCE_SHA}
    endpoint_role = next(r for r in shot.required_asset_roles if r.role == "last_frame")
    endpoint, = (a for a in loaded.registry.assets if a.asset_id in endpoint_role.asset_ids)
    policy_data.update(user_instruction="继续,一直到成功为止", scope="S01 first-last-frame repair", endpoint_sha256=endpoint.sha256)
    context = ShotRoutingContext(
        activated_shot=shot, target_shot_id=shot.shot_id, target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash, storyboard_revision=loaded.storyboard.revision,
        storyboard_content_hash=loaded.storyboard.content_hash, selected_registry_revision_id=loaded.registry.revision_id,
        character_bible_content_hashes=tuple(c.content_hash for c in request.character_context),
        important_character_ids=shot.character_ids, scene_content_hash=request.scene_context.content_hash,
        canonical_character_references=(), canonical_scene_reference=None, approved_existing_video=None,
        shot_keyframe=RouterAssetIdentity(role="first_frame", asset_id=source.asset_id,
            asset_sha256=source.sha256, source_registry_revision_id=loaded.registry.revision_id,
            mime_type=source.mime_type, size_bytes=source.size_bytes, width=941, height=1672),
        last_frame=RouterAssetIdentity(role="last_frame", asset_id=endpoint.asset_id,
            asset_sha256=endpoint.sha256, source_registry_revision_id=loaded.registry.revision_id,
            mime_type=endpoint.mime_type, size_bytes=endpoint.size_bytes, width=endpoint.width, height=endpoint.height),
        upstream_terminal=None, motion_requirement="character_action", continuity_mode="none",
        semantic_continuity_state=None, allowed_visual_strategies=("generated_video",),
        allowed_generation_modes=("image_to_video",),
    )
    output = VideoFlexibleOutputRequirement.model_validate_json((SOURCE_RUN / "output-requirement.json").read_bytes())
    output = output.model_copy(update={"native_audio": True})
    lifecycle = VideoGenerationLifecycleEnvelope(
        generation_id="jieshi-e01-s01-vidu-i2v-attempt07", target_asset_role="final_visual",
        base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id, source.asset_id, endpoint.asset_id), output_asset_id="jieshi-e01-s01-vidu-video-attempt07",
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=verified, context=context,
        policy=VideoRoutingPolicy(identity=RouterPolicyIdentity(policy_id="jieshi-s01-i2v-attempt07", policy_version="1", policy_sha256=canonical_sha256(policy_data)),
            local_resources_available=True, remote_authorized=True, budget_authorized=True),
        provider_profile=profile.pointer(), capabilities=provider.capabilities(), selected_capability_id="viduq3-pro-i2v-v1",
        output_requirement=output, lifecycle=lifecycle,
        compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="2"),
    )
    save("routing.json", routing)
    assert routing.provider_bound_request is not None, "Router blocked; inspect routing.json"
    compilation = provider.compile_request(routing.provider_bound_request, verified.requirement)
    save("compilation-result.json", compilation)
    compiled = require_compiled_provider_request(compilation)
    resolved = provider.resolve(compiled.request)
    for name, obj in (("compiled-request.json", compiled), ("resolved-request.json", resolved), ("provider-profile.json", profile), ("route-policy.json", policy_data), ("video-preview.json", provider.preview(resolved))):
        save(name, obj)
    profile_path = ROOT / profile.pointer().profile_path
    profile_path.parent.mkdir(exist_ok=True)
    profile_payload = json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if profile_path.exists():
        assert profile_path.read_text() == profile_payload
    else:
        profile_path.write_text(profile_payload)
    print(json.dumps({"status": "exact_i2v_request_ready", "request_hash": resolved.resolved_generation_hash,
                      "input_sha256": SOURCE_SHA, "source_inputs": len(resolved.image_bindings), "max_submit_count": 1}))


if __name__ == "__main__":
    main()
