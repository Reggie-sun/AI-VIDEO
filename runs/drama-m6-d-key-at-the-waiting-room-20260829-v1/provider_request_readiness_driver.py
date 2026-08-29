"""Seal one read-only Shot 01 Provider/request readiness decision.

This driver reopens the accepted authoring projection and current Production
state, asks the canonical Router about one explicit Local H3 Quality v1
candidate, and stops before request compilation whenever routing is blocked.
It never starts ComfyUI, contacts a transport, persists a video request, mints
a permit, submits a Provider effect, or writes Production state.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import subprocess
import tomllib
from pathlib import Path
from types import ModuleType

from ai_video.planning import VideoPlanningRequest
from ai_video.production._h3_prompt import H3PromptCompilation, compile_h3_prompt
from ai_video.production._shot_router_contracts import (
    AdapterCompilerContract,
    ContinuityMode,
    MotionRequirement,
    RouterPolicyIdentity,
    RoutingOutcome,
    ShotRoutingContext,
    VideoGenerationLifecycleEnvelope,
    VideoRoutingPolicy,
)
from ai_video.production._video_requirement_routing import (
    requirement_output_matches,
)
from ai_video.production.comfy_t8_native_turbo_profile import (
    load_t8_native_turbo_execution_profile,
)
from ai_video.production.comfy_t8_native_turbo_video import (
    ComfyUIT8NativeTurboVideoProvider,
)
from ai_video.production.comfy_t8_turbo_video import (
    ComfyUIT8TurboVideoProvider,
    load_t8_turbo_video_execution_profile,
)
from ai_video.production.comfy_t8_video import (
    ComfyUIT8VideoProvider,
    T8ExecutionProfile,
    load_t8_video_execution_profile,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily
from ai_video.production.project import load_production_project
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.video import ProviderProfilePointer, VideoGenerationMode
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import GenerationIntent


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
AUTHORING_DRIVER_PATH = RUN_ROOT / "authoring_to_request_driver.py"
ACCEPTED_AUTHORING_EVIDENCE_PATH = (
    RUN_ROOT / "evidence/drama-shot-01-authoring-to-request-accepted-v1.json"
)
OUTPUT_PATH = (
    RUN_ROOT
    / "evidence/drama-shot-01-provider-profile-runtime-request-readiness-blocked-v1.json"
)
PROFILE_PATH = (
    REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_quality.json"
)
COMFY_ROOT = Path("/home/reggie/ComfyUI")

EXPECTED_OVERLAY_SHA256 = (
    "8b50b61b152b59542fc4521c870cc060b9b6469fc18db5e3a14248cf05de7efd"
)
EXPECTED_AUTHORING_EVIDENCE_SHA256 = (
    "1e38b731b31b4866720d5b80bfb2dd40da04ebe56dea8656f3d7219d15298cb6"
)
EXPECTED_REQUEST_HASH = (
    "01c329aa22b898521d0611bd4fbcfcbba912babb81b4ce85a88582985704fe7c"
)
EXPECTED_PROJECTION_HASH = (
    "f2292b67f3616a5b4757c6c3e45301b971230bb59a3b683207d8a6d6cb412b1d"
)
EXPECTED_REQUIREMENT_HASH = (
    "d234cd95b712ca8d966132d28c6ee15a49831b412305b795c8c8eb9a2491b34d"
)
EXPECTED_PROMPT_SHA256 = (
    "3676c9998a63e7ddc024faff7d18f07f5e48722046ee7193201f490ee57c750d"
)
EXPECTED_GRAPH_HASH = (
    "761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1"
)
EXPECTED_FAMILY_FINGERPRINT = (
    "d3b8e5cc31570763aae6f7454ca794737634c345ec3ea6bbbcaadc36196381dd"
)
SELECTED_CAPABILITY_ID = "minimax-h3-t8-t2va-quality-v1"
SELECTED_PROFILE_ID = "minimax-h3-t8-t2va-quality"
SELECTED_COMPILER_ID = "comfy-local-h3-t8-video-compiler"
SELECTED_COMPILER_VERSION = "3"
BLOCKER_ID = "FIXED_5S_REQUIREMENT_NOT_EXPRESSIBLE_BY_SELECTED_T8_PROFILE"

SOURCE_PATHS = (
    "src/ai_video/production/_h3_prompt.py",
    "src/ai_video/production/_shot_router_contracts.py",
    "src/ai_video/production/_video_requirement_routing.py",
    "src/ai_video/production/comfy_t8_video.py",
    "src/ai_video/production/local_h3_provider_family.py",
    "src/ai_video/production/shot_router.py",
    "src/ai_video/production/video_compiler.py",
    "src/ai_video/production/video_contracts.py",
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


def _load_authoring_driver() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "drama_m6_d_authoring_to_request_driver",
        AUTHORING_DRIVER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("accepted authoring driver could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_revision(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _git_clean(root: Path) -> bool:
    return not subprocess.run(
        ["git", "-C", str(root), "status", "--short"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _t8_version(root: Path) -> str:
    payload = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    version = payload.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError("T8 checkout version is not explicit")
    return version


def _supervisor_status() -> dict[str, object]:
    result = subprocess.run(
        ["python", "scripts/comfyui_supervisor.py", "status"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def _no_runtime() -> object:
    raise AssertionError("blocked readiness must not inspect a live runtime")


def _no_asset(_asset_id: str) -> object:
    raise AssertionError("T2VA readiness must not resolve media assets")


def _provider_family() -> tuple[LocalH3VideoProviderFamily, T8ExecutionProfile]:
    quality_profile = load_t8_video_execution_profile(
        PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    children: list[object] = [
        ComfyUIT8VideoProvider(
            quality_profile,
            artifact_root=REPO_ROOT,
            comfy_root=COMFY_ROOT,
            runtime_inspector=_no_runtime,
            transport=object(),
        )
    ]
    turbo_profile = load_t8_turbo_video_execution_profile(
        REPO_ROOT / "workflows/profiles/minimax_h3_t8_t2va_turbo.json",
        artifact_root=REPO_ROOT,
    )
    children.append(
        ComfyUIT8TurboVideoProvider(
            turbo_profile,
            artifact_root=REPO_ROOT,
            comfy_root=COMFY_ROOT,
            runtime_inspector=_no_runtime,
            transport=object(),
        )
    )
    for task in ("t2va", "i2va", "fl2va", "ref2va"):
        profile = load_t8_native_turbo_execution_profile(
            REPO_ROOT
            / f"workflows/profiles/minimax_h3_t8_{task}_turbo_native_v2.json",
            artifact_root=REPO_ROOT,
        )
        children.append(
            ComfyUIT8NativeTurboVideoProvider(
                profile,
                artifact_root=REPO_ROOT,
                comfy_root=COMFY_ROOT,
                input_root=COMFY_ROOT / "input",
                asset_resolver=_no_asset,
                runtime_inspector=_no_runtime,
                transport=object(),
            )
        )
    family = LocalH3VideoProviderFamily(children)
    if family.capabilities().capabilities_fingerprint != EXPECTED_FAMILY_FINGERPRINT:
        raise RuntimeError("current Local H3 family snapshot drifted")
    return family, quality_profile


def _launch_identity(supervisor: dict[str, object]) -> dict[str, object]:
    unit = supervisor.get("unit")
    main_pid = supervisor.get("main_pid")
    if (
        supervisor.get("active_state") != "active"
        or not isinstance(unit, str)
        or not unit
        or not isinstance(main_pid, int)
        or main_pid <= 0
    ):
        return {
            "inspection_mode": "systemd_exec_start_read_only",
            "result": "NOT_EVALUATED_INACTIVE",
            "launch_capabilities": [],
            "exec_start_sha256": None,
        }
    result = subprocess.run(
        [
            "systemctl",
            "--user",
            "show",
            unit,
            "--property=ExecStart",
            "--property=MainPID",
            "--property=InvocationID",
            "--value",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    observed = result.stdout.strip()
    capabilities = []
    if "--use-sage-attention" in observed.split():
        capabilities.append("sage_attention")
    return {
        "inspection_mode": "systemd_exec_start_read_only",
        "result": "OBSERVED",
        "launch_capabilities": capabilities,
        "exec_start_sha256": _sha256(observed.encode("utf-8")),
    }


def _runtime_identity(
    profile: T8ExecutionProfile,
    supervisor: dict[str, object],
) -> dict[str, object]:
    t8_root = COMFY_ROOT / "custom_nodes/minimax-h3-audio-T8"
    videohelpersuite_root = COMFY_ROOT / "custom_nodes/ComfyUI-VideoHelperSuite"
    launch = _launch_identity(supervisor)
    current = {
        "comfyui_commit": _git_revision(COMFY_ROOT),
        "t8_commit": _git_revision(t8_root),
        "t8_version": _t8_version(t8_root),
        "videohelpersuite_commit": _git_revision(videohelpersuite_root),
        "sageattention_version": importlib.metadata.version("sageattention"),
        "launch_capabilities": launch["launch_capabilities"],
    }
    required = {
        "comfyui_commit": profile.comfyui_commit,
        "t8_commit": profile.t8_commit,
        "t8_version": profile.t8_version,
        "videohelpersuite_commit": profile.videohelpersuite_commit,
        "sageattention_version": profile.sageattention_version,
        "launch_capabilities": list(profile.required_launch_capabilities),
    }
    mismatches = {
        key: {"required": value, "current": current[key]}
        for key, value in required.items()
        if current[key] != value
    }
    checkout_clean = {
        "comfyui": _git_clean(COMFY_ROOT),
        "t8": _git_clean(t8_root),
        "videohelpersuite": _git_clean(videohelpersuite_root),
    }
    missing_launch_capabilities = sorted(
        set(profile.required_launch_capabilities)
        - set(current["launch_capabilities"])
    )
    matches = (
        not mismatches
        and all(checkout_clean.values())
        and not missing_launch_capabilities
        and launch["result"] == "OBSERVED"
    )
    return {
        "inspection_mode": (
            "read_only_checkout_package_and_systemd_launch_identity"
        ),
        "required": required,
        "current": current,
        "checkout_clean": checkout_clean,
        "launch_identity": launch,
        "missing_launch_capabilities": missing_launch_capabilities,
        "mismatches": mismatches,
        "result": "MATCH" if matches else "MISMATCH",
        "canonical_provider_preflight": (
            "NOT_INVOKED_NO_RESOLVED_REQUEST"
        ),
    }


def main() -> None:
    before = _tree_snapshot(PROJECT_ROOT)
    authoring_evidence_bytes = ACCEPTED_AUTHORING_EVIDENCE_PATH.read_bytes()
    if _sha256(authoring_evidence_bytes) != EXPECTED_AUTHORING_EVIDENCE_SHA256:
        raise RuntimeError("accepted authoring evidence bytes drifted")
    accepted_authoring = json.loads(authoring_evidence_bytes)

    authoring_driver = _load_authoring_driver()
    materialization_bytes = authoring_driver.MATERIALIZATION_PATH.read_bytes()
    materialization = json.loads(materialization_bytes)
    overlay, overlay_identity = authoring_driver._load_overlay()
    authoring_driver._assert_source_binding(
        overlay,
        materialization_bytes,
        materialization,
    )
    if overlay_identity.get("acceptance_sha256") != EXPECTED_OVERLAY_SHA256:
        raise RuntimeError("accepted execution-intent envelope bytes drifted")

    loaded = load_production_project(PROJECT_ROOT / "project.yaml")
    original_request = VideoPlanningRequest.model_validate(
        materialization["planner"]["request"]
    )
    request, projection = authoring_driver._new_request_and_projection(
        original_request,
        GenerationIntent.model_validate(overlay["generation_intent"]),
    )
    requirement = projection.requirement
    prompt = compile_h3_prompt(requirement)
    if not isinstance(prompt, H3PromptCompilation):
        raise RuntimeError("accepted requirement no longer compiles to H3")
    if (
        request.request_content_hash != EXPECTED_REQUEST_HASH
        or projection.projection_hash != EXPECTED_PROJECTION_HASH
        or requirement.requirement_hash != EXPECTED_REQUIREMENT_HASH
        or prompt.prompt_sha256 != EXPECTED_PROMPT_SHA256
        or loaded.manifest.active_dependency_graph.content_hash
        != EXPECTED_GRAPH_HASH
        or accepted_authoring["new_canonical_projection"]["request_hash"]
        != EXPECTED_REQUEST_HASH
    ):
        raise RuntimeError("accepted Shot 01 authoring lineage drifted")

    family, profile = _provider_family()
    capabilities = family.capabilities()
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
        "schema": "drama-m6-d-shot01-routing-policy/1",
        "provider_name": capabilities.provider_name,
        "selected_capability_id": SELECTED_CAPABILITY_ID,
        "local_resources_available": True,
        "remote_authorized": False,
        "budget_authorized": False,
        "fallback_allowed": False,
    }
    policy = VideoRoutingPolicy(
        identity=RouterPolicyIdentity(
            policy_id="drama-m6-d-shot01-local-h3-quality-v1",
            policy_version="1",
            policy_sha256=canonical_sha256(policy_payload),
        ),
        local_resources_available=True,
        remote_authorized=False,
        budget_authorized=False,
    )
    lifecycle = VideoGenerationLifecycleEnvelope(
        generation_id="drama-m6-d-shot-001-readiness-v1",
        target_asset_role="final_visual",
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id,),
        output_asset_id="drama.shot.waiting-room.001.generated.v1",
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
        routing.decision.outcome is not RoutingOutcome.BLOCKED_CAPABILITY
        or routing.provider_bound_request is not None
        or requirement_output_matches(requirement, output)
        or routing.decision.reason_codes[0].value != "PROVIDER_CAPABILITY_DENIED"
    ):
        raise RuntimeError("current Router no longer reproduces the sealed readiness stop")

    supervisor_before = _supervisor_status()
    runtime = _runtime_identity(profile, supervisor_before)
    if (
        runtime["result"] != "MATCH"
        or runtime["mismatches"]
        or runtime["missing_launch_capabilities"]
        or not all(runtime["checkout_clean"].values())
    ):
        raise RuntimeError("current runtime identity does not satisfy the selected profile")
    supervisor_after = _supervisor_status()
    if supervisor_before != supervisor_after:
        raise RuntimeError("ComfyUI supervisor identity changed during inspection")

    after = _tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("readiness driver mutated canonical Production state")

    evidence = {
        "schema_version": "drama-m6-d-shot01-pre-submit-readiness/1",
        "status": "BLOCKED_BEFORE_EXACT_REQUEST_PREVIEW",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": {
            "shot_id": shot.shot_id,
            "revision": shot.revision,
            "content_hash": shot.content_hash,
        },
        "canonical_lineage": {
            "accepted_overlay_sha256": EXPECTED_OVERLAY_SHA256,
            "accepted_authoring_evidence_sha256": (
                EXPECTED_AUTHORING_EVIDENCE_SHA256
            ),
            "project_content_hash": loaded.project.content_hash,
            "registry_content_hash": loaded.registry.content_hash,
            "active_pre_generation_graph_hash": EXPECTED_GRAPH_HASH,
            "request_hash": request.request_content_hash,
            "verified_projection_hash": projection.projection_hash,
            "requirement_hash": requirement.requirement_hash,
            "prompt_sha256": prompt.prompt_sha256,
            "prompt_unchanged": True,
            "strict_reopen": True,
        },
        "creative_skill_preflight": {
            "open_video_scope": "ordered Shot and handoff boundary only",
            "h3_video_mode": "T2VA",
            "required_media_inputs": [],
            "open_state": requirement.generation_intent.open_state.model_dump(
                mode="json"
            ),
            "close_state": requirement.generation_intent.close_state.model_dump(
                mode="json"
            ),
            "screen_axis": requirement.generation_intent.axis_continuity.model_dump(
                mode="json"
            ),
            "action_direction": (
                requirement.generation_intent.motion_envelope.direction
            ),
            "camera_endpoint": (
                requirement.generation_intent.camera_endpoint.model_dump(mode="json")
            ),
            "prompt_change": "none",
            "executable_lint": "compile_h3_prompt current exact PASS",
        },
        "candidate_selection": {
            "selection_intent": "one explicit quality-first local H3 candidate; no ranking or fallback",
            "provider_name": capabilities.provider_name,
            "provider_kind": selected.provider_kind,
            "model_id": selected.model_id,
            "profile_id": SELECTED_PROFILE_ID,
            "profile_version": profile_pointer.profile_version,
            "profile_content_hash": profile.profile_content_hash,
            "capability_id": selected.capability_id,
            "capability_fingerprint": routing.decision.selected_capability_fingerprint,
            "family_capabilities_fingerprint": capabilities.capabilities_fingerprint,
            "compiler_id": compiler_contract.compiler_id,
            "compiler_version": compiler_contract.compiler_version,
            "compiler_hash": compiler_contract.compiler_hash,
            "workflow_path": profile.workflow_path.as_posix(),
            "workflow_sha256": profile.workflow_sha256,
            "binding_path": profile.binding_path.as_posix(),
            "binding_sha256": profile.binding_sha256,
            "selection_status": "BLOCKED_BY_ROUTER",
        },
        "router_decision": routing.decision.model_dump(mode="json"),
        "exact_mismatch": {
            "blocker_id": BLOCKER_ID,
            "accepted_requirement_output_need": (
                requirement.output_need.model_dump(mode="json")
            ),
            "selected_profile_output_requirement": output.model_dump(mode="json"),
            "canonical_requirement_output_matches": False,
            "impact": "Router emits no ProviderBoundVideoRequest; compile, resolve and preview remain unreachable.",
        },
        "runtime_identity": {
            **runtime,
            "readiness": "MATCH",
            "profile_path": PROFILE_PATH.relative_to(REPO_ROOT).as_posix(),
            "profile_content_hash": profile.profile_content_hash,
            "workflow_and_binding_reopened": True,
            "component_and_object_info_preflight": (
                "NOT_INVOKED_NO_RESOLVED_REQUEST"
            ),
            "supervisor_before": supervisor_before,
            "supervisor_after": supervisor_after,
        },
        "exact_request_preview": {
            "status": "NOT_CREATED_ROUTER_BLOCKED",
            "provider_bound_request_hash": None,
            "compiled_request_hash": None,
            "resolved_generation_hash": None,
            "preview_fingerprint": None,
            "persisted": False,
        },
        "source_audio_resolution": {
            "accepted_sound_requirement": {
                "required_dialogue": (
                    requirement.generation_intent.dialogue_intent.verbatim_text
                ),
                "required_ambience": (
                    requirement.generation_intent.ambience_intent.environment_bed
                ),
                "music": requirement.generation_intent.music_intent.mode,
            },
            "requirement_audio_need": requirement.audio_need.value,
            "selected_capability_native_audio_options": list(
                selected.output_capability.native_audio_options
                if selected.output_capability is not None
                else ()
            ),
            "source_type": None,
            "source_audio_policy": None,
            "exact_request_native_audio_binding": None,
            "status": "BLOCKED_NO_PROVIDER_BOUND_REQUEST",
            "default_or_inference_used": False,
        },
        "submit_readiness": {
            "budget": "NOT_APPLICABLE_LOCAL_UNMETERED",
            "cloud_egress": "DENIED_AND_NOT_USED",
            "remote_authorization": "NOT_APPLICABLE",
            "durable_submit_intent": "NOT_CREATED",
            "one_use_permit": "NOT_MINTED",
            "provider_preflight": "NOT_INVOKED",
            "ready": False,
        },
        "source_identity": {
            "driver_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "driver_sha256": _sha256(Path(__file__).read_bytes()),
            "files": {
                path: _sha256((REPO_ROOT / path).read_bytes())
                for path in SOURCE_PATHS
            },
        },
        "historical_evidence_preserved": {
            "authoring_to_request_accepted_v1": {
                "path": ACCEPTED_AUTHORING_EVIDENCE_PATH.relative_to(
                    REPO_ROOT
                ).as_posix(),
                "sha256": EXPECTED_AUTHORING_EVIDENCE_SHA256,
                "overwritten": False,
            },
            "historical_preview_request_reused": False,
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
        "next_shot_submit_allowed": False,
        "remaining_blockers": [BLOCKER_ID],
    }
    evidence_bytes = _canonical_json_bytes(evidence)
    _write_immutable(OUTPUT_PATH, evidence_bytes)
    print(OUTPUT_PATH.relative_to(REPO_ROOT).as_posix())
    print(_sha256(evidence_bytes))


if __name__ == "__main__":
    main()
