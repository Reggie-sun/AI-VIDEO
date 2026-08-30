"""Seal Shot 01 runtime/profile/exact-request readiness without submission.

This driver reopens the accepted timing and SourceAudioPolicy lineage, checks
the current canonical supervisor and queue, and invokes only the selected
provider's read-only component/object-info preflight.  It does not persist a
VideoGenerationRequest, mint a permit, submit, generate media, or mutate
Production state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
SOURCE_AUDIO_DRIVER_PATH = RUN_ROOT / "shot01_source_audio_policy_readiness_driver.py"
TIMING_DRIVER_PATH = RUN_ROOT / "shot01_timing_request_readiness_driver.py"
READINESS_DRIVER_PATH = RUN_ROOT / "provider_request_readiness_driver.py"
PREVIOUS_EVIDENCE_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-source-audio-policy-readiness-accepted-v4.json"
)
PREVIOUS_ENVELOPE_PATH = REPO_ROOT / (
    "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/"
    "key-at-the-waiting-room-shot-01-v4.blocked.json"
)
COMFY_CLIENT_PATH = REPO_ROOT / "src/ai_video/comfy_client.py"
OUTPUT_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-runtime-profile-exact-request-readiness-accepted-v1.json"
)

SOURCE_AUDIO_DRIVER_SHA256 = (
    "1c81b4f2d81f545c13d6538bd1f735f1b54ea06de541daf0be4496085cac45f6"
)
PREVIOUS_EVIDENCE_SHA256 = (
    "55c217616b0967c95a240caf920a1cf7483b4837b59124ad0fda4ca86b6ed45b"
)
PREVIOUS_ENVELOPE_SHA256 = (
    "2ffbb5de9291470ddbd8a7703523aa3bfe710e771ce6bc8f4e6d570998648b39"
)
COMFY_CLIENT_SHA256 = (
    "29be8ddd932f709563dc07c135db8e21bf06f89a3b4ab0d526c6ebd911d0dca4"
)
REQUEST_HASH = "6dd31121a17d0178f4372bb4fa764f350216133b18f91d476675137af1480047"
PROJECTION_HASH = "e201aebeb90a324549138163c0d0f4f93405ad7755f3645b1a9bd99c5413ea21"
REQUIREMENT_HASH = "735c670eeee9bef29f9e9980ae8e476bde7bfff8786a78edf54af644d9eed924"
PROMPT_SHA256 = "e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47"
PROVIDER_BOUND_HASH = "69b470cd4a188fc31a73b04d69c59bba9b0efe8ab1f1eb9bde994f7999e951aa"
COMPILED_REQUEST_HASH = "56a6a21750a93ea392139a1e98a0558d9e7d5ae0576e1210f7b744e3118b7656"
REQUEST_INPUT_HASH = "de4b222eef59e867eaa30c591a10f98808558a19fa9b5d8973c7aece366b27d2"
RESOLVED_HASH = "5a9ee2722103a6cee533b36cd5ca2d6254f3ca2bf4c7e0e22da752bd48fecc95"
PREVIEW_HASH = "4ba6861de793286c47215d480d94237ab7202c966f9c4836716144008d7ecb76"
PROFILE_HASH = "4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7"
REQUIRED_COMFYUI_COMMIT = "7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa"
PREVIOUS_COMFYUI_COMMIT = "e01fb4c56b7a88149d469b99cbbfe3223d715054"
RUNTIME_BLOCKER = "SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
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


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module could not be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_sha256(path: Path, expected: str) -> bytes:
    payload = path.read_bytes()
    if _sha256(payload) != expected:
        raise RuntimeError(f"accepted parent bytes drifted: {path}")
    return payload


def _queue_snapshot() -> dict[str, object]:
    with urlopen("http://127.0.0.1:8188/queue", timeout=5) as response:
        payload = json.load(response)
    running = payload.get("queue_running")
    pending = payload.get("queue_pending")
    if not isinstance(running, list) or not isinstance(pending, list):
        raise RuntimeError("ComfyUI returned an invalid queue snapshot")
    return {
        "running_count": len(running),
        "pending_count": len(pending),
        "empty": not running and not pending,
    }


def main() -> None:
    _assert_sha256(SOURCE_AUDIO_DRIVER_PATH, SOURCE_AUDIO_DRIVER_SHA256)
    previous_evidence_bytes = _assert_sha256(
        PREVIOUS_EVIDENCE_PATH,
        PREVIOUS_EVIDENCE_SHA256,
    )
    previous_envelope_bytes = _assert_sha256(
        PREVIOUS_ENVELOPE_PATH,
        PREVIOUS_ENVELOPE_SHA256,
    )
    previous_evidence = json.loads(previous_evidence_bytes)
    previous_envelope = json.loads(previous_envelope_bytes)
    if (
        previous_evidence.get("remaining_blockers") != [RUNTIME_BLOCKER]
        or previous_envelope.get("decision") != "blocked"
        or previous_envelope.get("submit_readiness", {}).get("blockers")
        != [RUNTIME_BLOCKER]
        or previous_envelope.get("runtime_identity_drift", {}).get(
            "observed_comfyui_commit"
        )
        != PREVIOUS_COMFYUI_COMMIT
    ):
        raise RuntimeError("previous runtime-only stop lineage drifted")
    dependency_hashes = previous_evidence.get("source_identity", {}).get("files")
    if not isinstance(dependency_hashes, dict) or not dependency_hashes:
        raise RuntimeError("previous source dependency lineage is missing")
    for path, expected in sorted(dependency_hashes.items()):
        if not isinstance(path, str) or not isinstance(expected, str):
            raise RuntimeError("previous source dependency lineage is invalid")
        _assert_sha256(REPO_ROOT / path, expected)
    _assert_sha256(COMFY_CLIENT_PATH, COMFY_CLIENT_SHA256)

    source = _load_module(
        SOURCE_AUDIO_DRIVER_PATH,
        "drama_source_audio_runtime_readiness_reopen",
    )
    before = source._tree_snapshot(PROJECT_ROOT)
    timing = _load_module(TIMING_DRIVER_PATH, "drama_timing_runtime_readiness")
    readiness = _load_module(
        READINESS_DRIVER_PATH,
        "drama_provider_runtime_readiness",
    )

    policy, policy_identity = source._load_policy()
    if policy_identity.get("authority_status") != "ACCEPTED_AND_SEALED":
        raise RuntimeError("SourceAudioPolicy is not accepted and sealed")
    exact = source._reopen_exact_request(timing)
    routed = exact["routed"]
    request_preview = routed["request"]
    resolved = routed["resolved"]
    preview = routed["preview"]
    identities = (
        exact["request"].request_content_hash,
        exact["projection"].projection_hash,
        exact["requirement"].requirement_hash,
        exact["prompt"].prompt_sha256,
        routed["provider_bound"].provider_bound_request_hash,
        routed["compiled"].compiled_request_hash,
        request_preview.request_input_hash,
        resolved.resolved_generation_hash,
        preview.preview_fingerprint,
        routed["profile"].profile_content_hash,
    )
    if identities != (
        REQUEST_HASH,
        PROJECTION_HASH,
        REQUIREMENT_HASH,
        PROMPT_SHA256,
        PROVIDER_BOUND_HASH,
        COMPILED_REQUEST_HASH,
        REQUEST_INPUT_HASH,
        RESOLVED_HASH,
        PREVIEW_HASH,
        PROFILE_HASH,
    ):
        raise RuntimeError("canonical exact request lineage drifted")
    if (
        request_preview.output_requirement.native_audio is not True
        or policy["source_audio_policy"]["source_type"] != "GENERATED"
        or policy["source_audio_policy"]["policy"] != "KEEP"
    ):
        raise RuntimeError("accepted SourceAudioPolicy no longer binds the request")

    queue_before = _queue_snapshot()
    if not queue_before["empty"]:
        raise RuntimeError("ComfyUI queue is not empty before exact preflight")
    runtime = timing._runtime_readiness(
        accepted=True,
        readiness_driver=readiness,
        profile=routed["profile"],
        resolved=resolved,
    )
    queue_after = _queue_snapshot()
    if not queue_after["empty"]:
        raise RuntimeError("ComfyUI queue changed during exact preflight")
    if (
        runtime["result"] != "MATCH"
        or runtime["current"]["comfyui_commit"] != REQUIRED_COMFYUI_COMMIT
        or runtime["mismatches"]
        or runtime["missing_launch_capabilities"]
        or not all(runtime["checkout_clean"].values())
        or runtime["canonical_provider_preflight"]
        != "PASS_READ_ONLY_COMPONENT_AND_OBJECT_INFO"
        or runtime["provider_submit_count"] != 0
        or runtime["supervisor_before"] != runtime["supervisor_after"]
    ):
        raise RuntimeError("selected profile runtime or exact preflight is not ready")

    after = source._tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("runtime readiness mutated canonical Production state")

    evidence = {
        "schema_version": "drama-m6-d-shot01-runtime-exact-request-readiness/1",
        "status": "PRE_SUBMIT_PREREQUISITE_ACCEPTED_STOP_BEFORE_SUBMIT",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": policy["target_shot"],
        "accepted_lineage": {
            "previous_runtime_blocked_evidence_path": PREVIOUS_EVIDENCE_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "previous_runtime_blocked_evidence_sha256": PREVIOUS_EVIDENCE_SHA256,
            "previous_runtime_blocked_envelope_path": PREVIOUS_ENVELOPE_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "previous_runtime_blocked_envelope_sha256": PREVIOUS_ENVELOPE_SHA256,
            "source_audio_policy_payload_commit": policy_identity["payload_commit"],
            "source_audio_policy_payload_sha256": policy_identity["payload_sha256"],
            "source_audio_policy_acceptance_sha256": policy_identity[
                "acceptance_sha256"
            ],
            "request_hash": REQUEST_HASH,
            "verified_projection_hash": PROJECTION_HASH,
            "requirement_hash": REQUIREMENT_HASH,
            "prompt_sha256": PROMPT_SHA256,
            "provider_bound_request_hash": PROVIDER_BOUND_HASH,
            "compiled_request_hash": COMPILED_REQUEST_HASH,
            "request_input_hash": REQUEST_INPUT_HASH,
            "resolved_generation_hash": RESOLVED_HASH,
            "preview_fingerprint": PREVIEW_HASH,
            "strict_request_requirement_preview_reopen": True,
        },
        "selected_candidate": {
            "provider_name": routed["family"].capabilities().provider_name,
            "provider_kind": routed["selected"].provider_kind,
            "model_id": routed["selected"].model_id,
            "capability_id": routed["selected"].capability_id,
            "profile_id": "minimax-h3-t8-t2va-quality",
            "profile_version": "v1",
            "profile_content_hash": PROFILE_HASH,
            "workflow_path": routed["profile"].workflow_path.as_posix(),
            "workflow_sha256": routed["profile"].workflow_sha256,
            "binding_path": routed["profile"].binding_path.as_posix(),
            "binding_sha256": routed["profile"].binding_sha256,
            "compiler_id": routed["compiler_contract"].compiler_id,
            "compiler_version": routed["compiler_contract"].compiler_version,
            "compiler_hash": routed["compiler_contract"].compiler_hash,
            "fallback_allowed": False,
        },
        "runtime_transition": {
            "previous_comfyui_commit": PREVIOUS_COMFYUI_COMMIT,
            "required_comfyui_commit": REQUIRED_COMFYUI_COMMIT,
            "current_comfyui_commit": runtime["current"]["comfyui_commit"],
            "current_identity_result": runtime["result"],
            "checkout_clean": runtime["checkout_clean"],
            "launch_identity": runtime["launch_identity"],
            "supervisor_before": runtime["supervisor_before"],
            "supervisor_after": runtime["supervisor_after"],
            "queue_before": queue_before,
            "queue_after": queue_after,
            "resolved_blocker": RUNTIME_BLOCKER,
        },
        "exact_non_persisted_request_preview": {
            "provider_bound_request_hash": PROVIDER_BOUND_HASH,
            "compiled_request_hash": COMPILED_REQUEST_HASH,
            "request_input_hash": REQUEST_INPUT_HASH,
            "resolved_generation_hash": RESOLVED_HASH,
            "preview_fingerprint": PREVIEW_HASH,
            "frame_count": request_preview.output_requirement.frame_count,
            "fps": request_preview.output_requirement.fps,
            "native_audio": request_preview.output_requirement.native_audio,
            "source_audio_policy": "GENERATED + KEEP",
            "persisted": False,
            "historical_six_shot_preview_reused": False,
        },
        "canonical_provider_preflight": {
            "result": runtime["canonical_provider_preflight"],
            "inspection_scope": (
                "sealed components, required object-info nodes and T8 input schema"
            ),
            "provider_preflight_count": 1,
            "provider_submit_count": 0,
        },
        "submit_readiness": {
            "pre_submit_prerequisite_ready": True,
            "pre_submit_prerequisite_blockers": [],
            "budget": "NOT_APPLICABLE_LOCAL_UNMETERED",
            "cloud_egress": "DENIED_AND_NOT_USED",
            "remote_authorization": "NOT_APPLICABLE",
            "durable_submit_intent": "NOT_CREATED_STOP_BOUNDARY",
            "one_use_permit": "NOT_MINTED_STOP_BOUNDARY",
            "submit_effect_allowed": False,
            "submit_effect_blockers": [
                "DURABLE_SUBMIT_INTENT_NOT_CREATED",
                "ONE_USE_PERMIT_NOT_MINTED",
            ],
        },
        "effects": {
            "production_state_files_before": len(before),
            "production_state_files_after": len(after),
            "driver_production_state_writes": 0,
            "driver_video_generation_request_persisted": False,
            "driver_durable_submit_intent_count": 0,
            "driver_permit_mint_count": 0,
            "driver_provider_preflight_count": 1,
            "driver_provider_submit_count": 0,
            "driver_generated_media_count": 0,
            "driver_video_analysis_call_count": 0,
            "driver_manifest_or_registry_writes": 0,
            "driver_candidate_activation_count": 0,
        },
        "status_boundary": {
            "m6_d": "NOT_EVALUATED",
            "execution": "STOP_BEFORE_SUBMIT",
            "next_shot_submit_allowed": False,
            "per_shot_media_gate_entered": False,
            "p6": "NOT_EVALUATED",
            "final_acceptance": "NOT_EVALUATED",
        },
        "source_identity": {
            "actor_identity": "codex_primary_agent",
            "generator_id": "drama-shot01-runtime-exact-request-readiness-driver@1",
            "driver_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "driver_sha256": _sha256(Path(__file__).read_bytes()),
            "executed_dependency_sha256": {
                **dependency_hashes,
                COMFY_CLIENT_PATH.relative_to(REPO_ROOT).as_posix(): (
                    COMFY_CLIENT_SHA256
                ),
            },
        },
    }
    evidence_bytes = _canonical_json_bytes(evidence)
    _write_immutable(OUTPUT_PATH, evidence_bytes)
    print(OUTPUT_PATH.relative_to(REPO_ROOT).as_posix())
    print(_sha256(evidence_bytes))


if __name__ == "__main__":
    main()
