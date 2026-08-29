"""Seal one versioned Shot 01 timing repair and exact request preview.

The driver reopens the accepted v1 authoring lineage, applies only the
authorized 124-frame timing delta through the canonical Planner projection,
and then uses the exact Router -> adapter compiler -> resolver -> preview
seams.  It never persists a VideoGenerationRequest, starts ComfyUI, mints a
permit, submits a prompt, generates media, or mutates Production state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType

from ai_video.planning import (
    VideoPlanner,
    VideoPlanningRequest,
    require_current_video_plan,
)
from ai_video.production._h3_prompt import H3PromptCompilation, compile_h3_prompt
from ai_video.production._shot_router_contracts import (
    AdapterCompilerContract,
    ContinuityMode,
    MotionRequirement,
    ProviderBoundVideoRequest,
    RouterPolicyIdentity,
    RoutingOutcome,
    ShotRoutingContext,
    VideoGenerationLifecycleEnvelope,
    VideoRoutingPolicy,
)
from ai_video.production._video_requirement_routing import (
    requirement_output_matches,
)
from ai_video.production.comfy_t8_video import (
    ComfyUIT8VideoProvider,
    T8RuntimeInspection,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.video import (
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
)
from ai_video.production.video_compiler import (
    CompiledProviderVideoRequest,
    require_compiled_provider_request,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import (
    GenerationIntent,
    OutputNeed,
    ProviderNeutralGenerationIntentProjection,
    ProviderNeutralVideoRequirement,
    VerifiedGenerationRequirementProjection,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
AUTHORING_DRIVER_PATH = RUN_ROOT / "authoring_to_request_driver.py"
READINESS_DRIVER_PATH = RUN_ROOT / "provider_request_readiness_driver.py"
REPAIR_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
    "key-at-the-waiting-room-shot-01-v2.proposed.json"
)
ACCEPTANCE_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
    "key-at-the-waiting-room-shot-01-v2.accepted.json"
)
CANDIDATE_EVIDENCE_PATH = (
    RUN_ROOT / "evidence/drama-shot-01-timing-request-readiness-candidate-v1.json"
)
ACCEPTED_EVIDENCE_PATH = (
    RUN_ROOT / "evidence/drama-shot-01-timing-request-readiness-accepted-v1.json"
)

PARENT_ACCEPTANCE_SHA256 = (
    "8b50b61b152b59542fc4521c870cc060b9b6469fc18db5e3a14248cf05de7efd"
)
PARENT_AUTHORING_EVIDENCE_SHA256 = (
    "1e38b731b31b4866720d5b80bfb2dd40da04ebe56dea8656f3d7219d15298cb6"
)
PARENT_BLOCKED_ENVELOPE_SHA256 = (
    "3e28032c7977579d2d53cf3650352c603547d219022429cdb5a886407c86bbcf"
)
PARENT_BLOCKED_EVIDENCE_SHA256 = (
    "f214645086e11c41d698190ac0ff4418278da9c02aae6ca1605b964d304b2cb1"
)
PARENT_REQUEST_HASH = (
    "01c329aa22b898521d0611bd4fbcfcbba912babb81b4ce85a88582985704fe7c"
)
PARENT_PROJECTION_HASH = (
    "f2292b67f3616a5b4757c6c3e45301b971230bb59a3b683207d8a6d6cb412b1d"
)
PARENT_REQUIREMENT_HASH = (
    "d234cd95b712ca8d966132d28c6ee15a49831b412305b795c8c8eb9a2491b34d"
)
PARENT_PROMPT_SHA256 = (
    "3676c9998a63e7ddc024faff7d18f07f5e48722046ee7193201f490ee57c750d"
)
ACTIVE_GRAPH_HASH = (
    "761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1"
)
EXPECTED_FAMILY_FINGERPRINT = (
    "d3b8e5cc31570763aae6f7454ca794737634c345ec3ea6bbbcaadc36196381dd"
)
SELECTED_CAPABILITY_ID = "minimax-h3-t8-t2va-quality-v1"
SELECTED_PROFILE_ID = "minimax-h3-t8-t2va-quality"
SELECTED_COMPILER_ID = "comfy-local-h3-t8-video-compiler"
SELECTED_COMPILER_VERSION = "3"
SOURCE_AUDIO_BLOCKER = "SOURCE_AUDIO_POLICY_NOT_SEALED_FOR_NATIVE_AUDIO_REQUEST"
RUNTIME_IDENTITY_BLOCKER = "SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH"

SOURCE_PATHS = (
    "src/ai_video/planning/_current_plan_projection.py",
    "src/ai_video/planning/_planner_models.py",
    "src/ai_video/planning/video_planner.py",
    "src/ai_video/production/_h3_prompt.py",
    "src/ai_video/production/_shot_router_contracts.py",
    "src/ai_video/production/_video_requirement_routing.py",
    "src/ai_video/production/comfy_t8_video.py",
    "src/ai_video/production/local_h3_provider_family.py",
    "src/ai_video/production/shot_router.py",
    "src/ai_video/production/video.py",
    "src/ai_video/production/video_compiler.py",
    "src/ai_video/production/video_requirement.py",
    "workflows/profiles/minimax_h3_t8_t2va_quality.json",
    "workflows/templates/minimax_h3_t8_t2va_quality_api.json",
    "workflows/bindings/minimax_h3_t8_t2va_quality_binding.yaml",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_immutable(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimeError(f"immutable evidence path has other bytes: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load driver module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_blob_oid(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _assert_path_hash(path: str, expected: str) -> None:
    actual = _sha256((REPO_ROOT / path).read_bytes())
    if actual != expected:
        raise RuntimeError(f"immutable parent lineage drifted: {path}: {actual}")


def _validate_repair(payload: dict[str, object]) -> None:
    expected = {
        "schema_version": "drama-shot-timing-repair-overlay/1",
        "record_kind": "drama_shot_timing_repair_overlay",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "overlay_version": 2,
        "status": "proposed",
        "domain_id": "drama",
        "lane_id": "M6-D",
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise RuntimeError("timing repair overlay identity is not canonical")
    target = payload.get("target_shot")
    if target != {
        "shot_id": "drama.shot.waiting-room.001",
        "revision": 1,
        "content_hash": "4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b",
    }:
        raise RuntimeError("timing repair target Shot identity drifted")
    lineage = payload.get("parent_lineage")
    if not isinstance(lineage, dict) or {
        "accepted_execution_intent_envelope_sha256": PARENT_ACCEPTANCE_SHA256,
        "accepted_authoring_evidence_sha256": PARENT_AUTHORING_EVIDENCE_SHA256,
        "blocked_readiness_envelope_sha256": PARENT_BLOCKED_ENVELOPE_SHA256,
        "blocked_readiness_evidence_sha256": PARENT_BLOCKED_EVIDENCE_SHA256,
        "parent_request_hash": PARENT_REQUEST_HASH,
        "parent_verified_projection_hash": PARENT_PROJECTION_HASH,
        "parent_requirement_hash": PARENT_REQUIREMENT_HASH,
        "parent_prompt_sha256": PARENT_PROMPT_SHA256,
        "active_pre_generation_graph_hash": ACTIVE_GRAPH_HASH,
    }.items() - lineage.items():
        raise RuntimeError("timing repair parent lineage is not exact")
    repair = payload.get("timing_repair")
    if not isinstance(repair, dict):
        raise RuntimeError("timing repair payload is missing")
    parent_output = OutputNeed.model_validate(repair.get("parent_output_need"))
    repaired_output = OutputNeed.model_validate(repair.get("repaired_output_need"))
    if (
        parent_output.timing_mode != "fixed"
        or parent_output.duration_seconds != 5.0
        or repaired_output.timing_mode != "frame_count"
        or repaired_output.frame_count != 124
        or repaired_output.fps != 24
        or repair.get("repaired_shot_duration_seconds") != 124 / 24
    ):
        raise RuntimeError("timing repair does not express exact 124-frame H3 timing")
    unchanged = payload.get("unchanged_contract")
    if not isinstance(unchanged, dict) or (
        unchanged.get("source_audio_policy_changed") is not False
        or unchanged.get("source_audio_policy_after_repair") is not None
        or unchanged.get("non_timing_execution_intent_changed") is not False
        or unchanged.get(
            "fixture_baseline_story_scene_character_shot_semantic_bytes_changed"
        )
        is not False
    ):
        raise RuntimeError("timing repair exceeds its authorized semantic boundary")


def _load_repair() -> tuple[dict[str, object], dict[str, object]]:
    if not (REPO_ROOT / ACCEPTANCE_PATH).exists():
        payload_bytes = (REPO_ROOT / REPAIR_PATH).read_bytes()
        payload = json.loads(payload_bytes)
        _validate_repair(payload)
        return payload, {
            "authority_status": "PROPOSED_PENDING_DELEGATED_ACCEPTANCE",
            "payload_path": REPAIR_PATH.as_posix(),
            "payload_sha256": _sha256(payload_bytes),
            "acceptance_path": None,
            "acceptance_sha256": None,
        }

    acceptance_bytes = (REPO_ROOT / ACCEPTANCE_PATH).read_bytes()
    acceptance = json.loads(acceptance_bytes)
    expected = {
        "schema_version": "drama-shot-timing-repair-acceptance/1",
        "record_kind": "drama_shot_timing_repair_acceptance",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "overlay_version": 2,
        "status": "accepted",
        "domain_id": "drama",
        "lane_id": "M6-D",
    }
    if any(acceptance.get(key) != value for key, value in expected.items()):
        raise RuntimeError("timing repair acceptance identity is not canonical")
    accepted = acceptance.get("accepted_timing_repair_payload")
    if not isinstance(accepted, dict):
        raise RuntimeError("accepted timing repair payload binding is missing")
    payload_bytes = _git_blob(str(accepted["commit"]), str(accepted["path"]))
    if (
        len(payload_bytes) != accepted.get("byte_size")
        or _sha256(payload_bytes) != accepted.get("accepted_record_sha256")
        or _git_blob_oid(str(accepted["commit"]), str(accepted["path"]))
        != accepted.get("git_blob_oid")
    ):
        raise RuntimeError("accepted timing repair bytes do not match immutable Git identity")
    payload = json.loads(payload_bytes)
    _validate_repair(payload)
    return payload, {
        "authority_status": "ACCEPTED_AND_SEALED",
        "payload_path": accepted["path"],
        "payload_commit": accepted["commit"],
        "payload_git_blob_oid": accepted["git_blob_oid"],
        "payload_byte_size": accepted["byte_size"],
        "payload_sha256": accepted["accepted_record_sha256"],
        "acceptance_path": ACCEPTANCE_PATH.as_posix(),
        "acceptance_sha256": _sha256(acceptance_bytes),
    }


def _apply_generation_intent_repair(
    parent: GenerationIntent,
    repair: dict[str, object],
) -> GenerationIntent:
    values = parent.model_dump(mode="python")
    replacements = repair.get("generation_intent_replacements")
    if not isinstance(replacements, list) or len(replacements) != 3:
        raise RuntimeError("timing repair must contain exactly three intent replacements")
    expected_paths = (
        "pacing.cadence",
        "pacing.shot_duration_seconds",
        "lighting_intent.continuity_state",
    )
    for item, expected_path in zip(replacements, expected_paths, strict=True):
        if not isinstance(item, dict) or item.get("field") != expected_path:
            raise RuntimeError("timing repair intent replacement order is not canonical")
        owner, field = expected_path.split(".", 1)
        section = values.get(owner)
        if not isinstance(section, dict) or section.get(field) != item.get("from"):
            raise RuntimeError(f"timing repair parent value drifted: {expected_path}")
        section[field] = item.get("to")
    repaired = GenerationIntent.model_validate(values)
    if repaired.pacing.shot_duration_seconds != 124 / 24:
        raise RuntimeError("repaired generation intent duration is not exact")
    return repaired


def _new_request_and_projection(
    *,
    original_request: VideoPlanningRequest,
    parent_projection: ProviderNeutralGenerationIntentProjection,
    generation_intent: GenerationIntent,
    output_need: OutputNeed,
) -> tuple[VideoPlanningRequest, VerifiedGenerationRequirementProjection]:
    projection_values = {
        field: getattr(parent_projection, field)
        for field in type(parent_projection).model_fields
        if field not in {"projection_hash", "generation_intent", "output_need"}
    }
    projection_values.update(
        generation_intent=generation_intent,
        output_need=output_need,
    )
    generation_projection = ProviderNeutralGenerationIntentProjection.create(
        **projection_values
    )
    request_values = original_request.model_dump(
        mode="python",
        exclude={"request_content_hash", "generation_intent"},
    )
    request_values.update(
        request_id="drama-m6-d-shot-001-timing-repair-v2",
        generation_intent=generation_projection,
    )
    request = VideoPlanningRequest.create(**request_values)
    plan = VideoPlanner().plan(request)
    projection = require_current_video_plan(current_request=request, plan=plan)
    return request, VerifiedGenerationRequirementProjection.model_validate(
        projection.model_dump(mode="python")
    )


def _prompt_delta(parent_prompt: str, repaired_prompt: str) -> dict[str, object]:
    substitutions = (
        ("through the 5.000s endpoint", "through the 5.167s endpoint"),
        ("3.900-5.000s breath pause", "3.900-5.167s breath pause"),
        ("duration 5.000s", "duration 5.167s"),
    )
    expected = parent_prompt
    for old, new in substitutions:
        if expected.count(old) != 1:
            raise RuntimeError(f"parent prompt timing token is not unique: {old}")
        expected = expected.replace(old, new)
    if repaired_prompt != expected:
        raise RuntimeError("timing repair changed provider prompt outside exact timing tokens")
    return {
        "only_timing_tokens_changed": True,
        "substitutions": [
            {"from": old, "to": new} for old, new in substitutions
        ],
    }


def _route_compile_resolve_preview(
    *,
    readiness_driver: ModuleType,
    loaded: object,
    projection: VerifiedGenerationRequirementProjection,
) -> dict[str, object]:
    family, profile = readiness_driver._provider_family()
    capabilities = family.capabilities()
    if capabilities.capabilities_fingerprint != EXPECTED_FAMILY_FINGERPRINT:
        raise RuntimeError("Local H3 family capability snapshot drifted")
    selected = next(
        variant
        for variant in capabilities.variants
        if variant.capability_id == SELECTED_CAPABILITY_ID
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=profile.frame_count,
        dimension_mode="exact",
        width=profile.width,
        height=profile.height,
        resolution_label="h3_t8_native",
        ratio="16:9",
        fps=profile.fps,
        container=profile.output_container,
        mime_type=profile.output_mime_type,
        native_audio=True,
    )
    shot = loaded.shots[0]
    scene = loaded.scenes[0]
    context = ShotRoutingContext(
        activated_shot=shot,
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        storyboard_revision=loaded.storyboard.revision,
        storyboard_content_hash=loaded.storyboard.content_hash,
        selected_registry_revision_id=loaded.manifest.active_registry.revision_id,
        character_bible_content_hashes=(),
        important_character_ids=(),
        scene_content_hash=scene.content_hash,
        canonical_character_references=(),
        canonical_scene_reference=None,
        approved_existing_video=None,
        shot_keyframe=None,
        upstream_terminal=None,
        motion_requirement=MotionRequirement.CHARACTER_ACTION,
        continuity_mode=ContinuityMode.NONE,
        semantic_continuity_state=None,
        allowed_visual_strategies=(shot.visual_strategy,),
        allowed_generation_modes=(VideoGenerationMode.TEXT_TO_VIDEO,),
    )
    policy_payload = {
        "schema": "drama-m6-d-shot01-routing-policy/2",
        "provider_name": capabilities.provider_name,
        "selected_capability_id": SELECTED_CAPABILITY_ID,
        "local_resources_available": True,
        "remote_authorized": False,
        "budget_authorized": False,
        "fallback_allowed": False,
    }
    policy = VideoRoutingPolicy(
        identity=RouterPolicyIdentity(
            policy_id="drama-m6-d-shot01-local-h3-quality-v2",
            policy_version="2",
            policy_sha256=canonical_sha256(policy_payload),
        ),
        local_resources_available=True,
        remote_authorized=False,
        budget_authorized=False,
    )
    lifecycle = VideoGenerationLifecycleEnvelope(
        generation_id="drama-m6-d-shot-001-readiness-v2",
        target_asset_role="final_visual",
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id,),
        output_asset_id="drama.shot.waiting-room.001.generated.v2",
    )
    profile_pointer = ProviderProfilePointer(
        profile_id=SELECTED_PROFILE_ID,
        profile_version="v1",
        profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
        profile_sha256=profile.profile_content_hash,
    )
    compiler_contract = AdapterCompilerContract.create(
        compiler_id=SELECTED_COMPILER_ID,
        compiler_version=SELECTED_COMPILER_VERSION,
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=policy,
        provider_profile=profile_pointer,
        capabilities=capabilities,
        selected_capability_id=SELECTED_CAPABILITY_ID,
        output_requirement=output,
        lifecycle=lifecycle,
        compiler_contract=compiler_contract,
    )
    if (
        routing.decision.outcome is not RoutingOutcome.SELECTED
        or routing.provider_bound_request is None
        or not requirement_output_matches(projection.requirement, output)
    ):
        raise RuntimeError("repaired requirement did not reach the exact selected capability")
    provider_bound = ProviderBoundVideoRequest.model_validate(
        routing.provider_bound_request.model_dump(mode="python")
    )
    compiled = require_compiled_provider_request(
        family.compile_request(provider_bound, projection.requirement)
    )
    compiled = CompiledProviderVideoRequest.model_validate(
        compiled.model_dump(mode="python")
    )
    request = VideoGenerationRequest.model_validate(
        compiled.request.model_dump(mode="python")
    )
    resolved = family.resolve(request)
    resolved = ResolvedVideoGenerationRequest.model_validate(
        resolved.model_dump(mode="python")
    )
    preview = family.preview(resolved)
    preview = VideoGenerationPreview.model_validate(preview.model_dump(mode="python"))
    if (
        request.output_requirement != output
        or resolved.effective_output != output
        or preview.resolved_generation_hash != resolved.resolved_generation_hash
        or output.native_audio is not True
        or request.image_bindings
        or request.media_bindings
    ):
        raise RuntimeError("exact request preview drifted from the selected T2VA output")
    return {
        "family": family,
        "profile": profile,
        "selected": selected,
        "output": output,
        "routing": routing,
        "provider_bound": provider_bound,
        "compiled": compiled,
        "request": request,
        "resolved": resolved,
        "preview": preview,
        "policy": policy,
        "compiler_contract": compiler_contract,
    }


def _runtime_readiness(
    *,
    accepted: bool,
    readiness_driver: ModuleType,
    profile: object,
    resolved: ResolvedVideoGenerationRequest,
) -> dict[str, object]:
    supervisor_before = readiness_driver._supervisor_status()
    runtime = readiness_driver._runtime_identity(profile, supervisor_before)
    matches = (
        runtime["result"] == "MATCH"
        and not runtime["mismatches"]
        and not runtime["missing_launch_capabilities"]
        and all(runtime["checkout_clean"].values())
    )
    preflight = (
        "DEFERRED_PENDING_TIMING_REPAIR_ACCEPTANCE"
        if matches
        else "NOT_INVOKED_RUNTIME_IDENTITY_MISMATCH"
    )
    if accepted and matches:
        current = runtime["current"]
        inspection = T8RuntimeInspection(
            comfyui_commit=current["comfyui_commit"],
            t8_commit=current["t8_commit"],
            t8_version=current["t8_version"],
            videohelpersuite_commit=current["videohelpersuite_commit"],
            sageattention_version=current["sageattention_version"],
            launch_capabilities=tuple(current["launch_capabilities"]),
        )
        exact_provider = ComfyUIT8VideoProvider(
            profile,
            artifact_root=REPO_ROOT,
            comfy_root=readiness_driver.COMFY_ROOT,
            runtime_inspector=lambda: inspection,
        )
        exact_provider.preflight(resolved)
        preflight = "PASS_READ_ONLY_COMPONENT_AND_OBJECT_INFO"
    supervisor_after = readiness_driver._supervisor_status()
    if supervisor_before != supervisor_after:
        raise RuntimeError("ComfyUI supervisor identity changed during read-only inspection")
    return {
        **runtime,
        "readiness": "MATCH" if matches else "MISMATCH",
        "canonical_provider_preflight": preflight,
        "supervisor_before": supervisor_before,
        "supervisor_after": supervisor_after,
        "comfyui_lifecycle_changed": False,
        "provider_submit_count": 0,
    }


def main() -> None:
    before = _tree_snapshot(PROJECT_ROOT)
    for path, expected in (
        (
            "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
            "key-at-the-waiting-room-shot-01-v1.accepted.json",
            PARENT_ACCEPTANCE_SHA256,
        ),
        (
            "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
            "drama-shot-01-authoring-to-request-accepted-v1.json",
            PARENT_AUTHORING_EVIDENCE_SHA256,
        ),
        (
            "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/"
            "key-at-the-waiting-room-shot-01-v1.blocked.json",
            PARENT_BLOCKED_ENVELOPE_SHA256,
        ),
        (
            "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
            "drama-shot-01-provider-profile-runtime-request-readiness-blocked-v1.json",
            PARENT_BLOCKED_EVIDENCE_SHA256,
        ),
    ):
        _assert_path_hash(path, expected)

    authoring_driver = _load_module(
        AUTHORING_DRIVER_PATH,
        "drama_m6_d_authoring_to_request_driver_for_timing_repair",
    )
    readiness_driver = _load_module(
        READINESS_DRIVER_PATH,
        "drama_m6_d_provider_readiness_driver_for_timing_repair",
    )
    repair, repair_identity = _load_repair()
    accepted = repair_identity["authority_status"] == "ACCEPTED_AND_SEALED"

    materialization_bytes = authoring_driver.MATERIALIZATION_PATH.read_bytes()
    materialization = json.loads(materialization_bytes)
    parent_overlay, parent_overlay_identity = authoring_driver._load_overlay()
    authoring_driver._assert_source_binding(
        parent_overlay,
        materialization_bytes,
        materialization,
    )
    if (
        parent_overlay_identity["acceptance_sha256"] != PARENT_ACCEPTANCE_SHA256
        or parent_overlay.get("source_audio_policy") is not None
    ):
        raise RuntimeError("parent execution-intent or source-audio boundary drifted")

    loaded = load_production_project(PROJECT_ROOT / "project.yaml")
    original_request = VideoPlanningRequest.model_validate(
        materialization["planner"]["request"]
    )
    parent_intent = GenerationIntent.model_validate(parent_overlay["generation_intent"])
    parent_request, parent_projection = authoring_driver._new_request_and_projection(
        original_request,
        parent_intent,
    )
    parent_requirement = ProviderNeutralVideoRequirement.model_validate(
        parent_projection.requirement.model_dump(mode="python")
    )
    parent_prompt = compile_h3_prompt(parent_requirement)
    if (
        not isinstance(parent_prompt, H3PromptCompilation)
        or parent_request.request_content_hash != PARENT_REQUEST_HASH
        or parent_projection.projection_hash != PARENT_PROJECTION_HASH
        or parent_requirement.requirement_hash != PARENT_REQUIREMENT_HASH
        or parent_prompt.prompt_sha256 != PARENT_PROMPT_SHA256
        or loaded.manifest.active_dependency_graph.content_hash != ACTIVE_GRAPH_HASH
    ):
        raise RuntimeError("accepted parent authoring lineage drifted")

    timing = repair["timing_repair"]
    if not isinstance(timing, dict):
        raise RuntimeError("timing repair payload is invalid")
    repaired_intent = _apply_generation_intent_repair(parent_intent, timing)
    repaired_output = OutputNeed.model_validate(timing["repaired_output_need"])
    request, projection = _new_request_and_projection(
        original_request=original_request,
        parent_projection=parent_request.generation_intent,
        generation_intent=repaired_intent,
        output_need=repaired_output,
    )
    requirement = ProviderNeutralVideoRequirement.model_validate(
        projection.requirement.model_dump(mode="python")
    )
    prompt = compile_h3_prompt(requirement)
    if not isinstance(prompt, H3PromptCompilation):
        raise RuntimeError("repaired canonical requirement no longer compiles to H3")
    exact_dialogue = repaired_intent.dialogue_intent.verbatim_text
    if exact_dialogue is None:
        raise RuntimeError("repaired intent lost exact dialogue")
    prompt_audit = authoring_driver._prompt_audit(prompt.prompt_text, exact_dialogue)
    prompt_delta = _prompt_delta(parent_prompt.prompt_text, prompt.prompt_text)
    if (
        requirement.output_need != repaired_output
        or requirement.output_need.frame_count != 124
        or requirement.output_need.fps != 24
        or repaired_intent.pacing.shot_duration_seconds != 124 / 24
    ):
        raise RuntimeError("Planner did not preserve the exact repaired timing")

    routed = _route_compile_resolve_preview(
        readiness_driver=readiness_driver,
        loaded=loaded,
        projection=projection,
    )
    compiled = routed["compiled"]
    request_preview = routed["request"]
    resolved = routed["resolved"]
    preview = routed["preview"]
    if (
        compiled.provider_native_prompt != prompt.prompt_text
        or compiled.request.prompt_text != prompt.prompt_text
        or resolved.prompt_text != prompt.prompt_text
    ):
        raise RuntimeError("canonical adapter changed the exact repaired H3 prompt")
    runtime = _runtime_readiness(
        accepted=accepted,
        readiness_driver=readiness_driver,
        profile=routed["profile"],
        resolved=resolved,
    )

    after = _tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("timing/readiness driver mutated canonical Production state")

    prior_evidence = {
        "parent_authoring_accepted_v1": {
            "path": repair["parent_lineage"]["accepted_authoring_evidence_path"],
            "sha256": PARENT_AUTHORING_EVIDENCE_SHA256,
            "overwritten": False,
        },
        "parent_readiness_blocked_v1": {
            "path": repair["parent_lineage"]["blocked_readiness_evidence_path"],
            "sha256": PARENT_BLOCKED_EVIDENCE_SHA256,
            "overwritten": False,
        },
        "historical_preview_request_reused": False,
    }
    blockers = []
    if not accepted:
        blockers.append("TIMING_REPAIR_OVERLAY_ACCEPTANCE_PENDING")
    if runtime["readiness"] != "MATCH":
        blockers.append(RUNTIME_IDENTITY_BLOCKER)
    blockers.append(SOURCE_AUDIO_BLOCKER)
    evidence = {
        "schema_version": "drama-m6-d-shot01-timing-request-readiness/1",
        "status": (
            "EXACT_REQUEST_PREVIEW_READY_PRE_SUBMIT_BLOCKED"
            if accepted
            else "CANDIDATE_TIMING_REPAIR_COMPILES_AND_ROUTES_PENDING_ACCEPTANCE"
        ),
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": repair["target_shot"],
        "repair_identity": repair_identity,
        "prior_evidence_preserved": prior_evidence,
        "canonical_lineage": {
            "parent_request_hash": PARENT_REQUEST_HASH,
            "parent_verified_projection_hash": PARENT_PROJECTION_HASH,
            "parent_requirement_hash": PARENT_REQUIREMENT_HASH,
            "parent_prompt_sha256": PARENT_PROMPT_SHA256,
            "new_request_id": request.request_id,
            "new_request_hash": request.request_content_hash,
            "new_generation_intent_hash": request.generation_intent.projection_hash,
            "new_plan_hash": projection.plan_hash,
            "new_verified_projection_hash": projection.projection_hash,
            "new_requirement_id": requirement.requirement_id,
            "new_requirement_hash": requirement.requirement_hash,
            "new_prompt_sha256": prompt.prompt_sha256,
            "active_pre_generation_graph_hash": ACTIVE_GRAPH_HASH,
            "strict_request_reopen": True,
            "strict_requirement_reopen": True,
            "strict_verified_projection_reopen": True,
        },
        "timing_repair": {
            "parent_output_need": timing["parent_output_need"],
            "repaired_output_need": requirement.output_need.model_dump(mode="json"),
            "effective_duration_seconds": 124 / 24,
            "profile_frame_count": routed["profile"].frame_count,
            "profile_fps": routed["profile"].fps,
            "canonical_requirement_output_matches": True,
            "non_timing_execution_intent_changed": False,
        },
        "h3_compilation": {
            "compiler": "ai_video.production._h3_prompt.compile_h3_prompt",
            "compiler_contract": "h3-three-field-v1",
            "prompt_text": prompt.prompt_text,
            "prompt_sha256": prompt.prompt_sha256,
            "prompt_audit": prompt_audit,
            "parent_to_repaired_delta": prompt_delta,
        },
        "candidate_selection": {
            "selection_intent": "one explicit quality-first local H3 candidate; no ranking or fallback",
            "provider_name": routed["family"].capabilities().provider_name,
            "provider_kind": routed["selected"].provider_kind,
            "model_id": routed["selected"].model_id,
            "profile_id": SELECTED_PROFILE_ID,
            "profile_version": "v1",
            "profile_content_hash": routed["profile"].profile_content_hash,
            "capability_id": routed["selected"].capability_id,
            "family_capabilities_fingerprint": EXPECTED_FAMILY_FINGERPRINT,
            "compiler_id": routed["compiler_contract"].compiler_id,
            "compiler_version": routed["compiler_contract"].compiler_version,
            "compiler_hash": routed["compiler_contract"].compiler_hash,
            "workflow_path": routed["profile"].workflow_path.as_posix(),
            "workflow_sha256": routed["profile"].workflow_sha256,
            "binding_path": routed["profile"].binding_path.as_posix(),
            "binding_sha256": routed["profile"].binding_sha256,
            "selection_status": "SELECTED_EXACT_NO_FALLBACK",
        },
        "router_decision": routed["routing"].decision.model_dump(mode="json"),
        "exact_non_persisted_request_preview": {
            "status": "CREATED_IN_MEMORY_ONLY",
            "provider_bound_request_hash": routed[
                "provider_bound"
            ].provider_bound_request_hash,
            "compiled_request_hash": compiled.compiled_request_hash,
            "payload_projection_hash": compiled.payload_projection_hash,
            "request_input_hash": request_preview.request_input_hash,
            "resolved_generation_hash": resolved.resolved_generation_hash,
            "desired_generation_fingerprint": resolved.desired_generation_fingerprint,
            "preview_fingerprint": preview.preview_fingerprint,
            "generation_id": request_preview.generation_id,
            "provider_name": request_preview.provider_name,
            "provider_kind": request_preview.provider_kind,
            "model_id": request_preview.model_id,
            "mode": request_preview.mode.value,
            "effective_output": resolved.effective_output.model_dump(mode="json"),
            "image_binding_count": len(request_preview.image_bindings),
            "media_binding_count": len(request_preview.media_bindings),
            "prompt_sha256": prompt.prompt_sha256,
            "persisted_to_production_state": False,
        },
        "source_audio_resolution": {
            "accepted_authoring_policy": None,
            "request_native_audio": request_preview.output_requirement.native_audio,
            "selected_capability_native_audio_options": list(
                routed["selected"].output_capability.native_audio_options
            ),
            "status": "BLOCKED_EXPLICIT_POLICY_NOT_SEALED",
            "blocker_id": SOURCE_AUDIO_BLOCKER,
            "default_or_inference_used": False,
            "generated_keep_assumed": False,
        },
        "runtime_identity": runtime,
        "submit_readiness": {
            "budget": "NOT_APPLICABLE_LOCAL_UNMETERED",
            "cloud_egress": "DENIED_AND_NOT_USED",
            "remote_authorization": "NOT_APPLICABLE",
            "durable_submit_intent": "NOT_CREATED",
            "one_use_permit": "NOT_MINTED",
            "provider_submit": "NOT_INVOKED",
            "ready": False,
            "blockers": blockers,
        },
        "source_identity": {
            "driver_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "driver_sha256": _sha256(Path(__file__).read_bytes()),
            "files": {
                path: _sha256((REPO_ROOT / path).read_bytes())
                for path in SOURCE_PATHS
            },
        },
        "effects": {
            "production_state_files_before": len(before),
            "production_state_files_after": len(after),
            "driver_production_state_writes": 0,
            "driver_video_generation_request_persisted": False,
            "driver_provider_submit_count": 0,
            "driver_permit_mint_count": 0,
            "driver_generated_media_count": 0,
            "driver_video_analysis_call_count": 0,
            "driver_manifest_or_registry_writes": 0,
            "driver_candidate_activation_count": 0,
        },
        "m6_d_status": "NOT_EVALUATED",
        "execution_status": "STOP_BEFORE_SUBMIT",
        "next_shot_submit_allowed": False,
        "remaining_blockers": blockers,
    }
    output_path = ACCEPTED_EVIDENCE_PATH if accepted else CANDIDATE_EVIDENCE_PATH
    evidence_bytes = _canonical_json_bytes(evidence)
    _write_immutable(output_path, evidence_bytes)
    print(output_path.relative_to(REPO_ROOT).as_posix())
    print(_sha256(evidence_bytes))


if __name__ == "__main__":
    main()
