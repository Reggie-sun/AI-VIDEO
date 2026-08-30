"""Seal current Shot 01 request-seam identity drift without importing it.

The accepted v4 evidence owns the last stable dependency hashes.  This driver
compares those hashes with current bytes before importing any request or
Provider module, records the exact drift and live runtime identity, and stops.
It never invokes Provider preflight, persists a request, mints a permit,
submits, generates media, or mutates Production state.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import tomllib
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
PREVIOUS_EVIDENCE_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-source-audio-policy-readiness-accepted-v4.json"
)
PREVIOUS_ENVELOPE_PATH = REPO_ROOT / (
    "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/"
    "key-at-the-waiting-room-shot-01-v4.blocked.json"
)
READINESS_DRIVER_PATH = RUN_ROOT / (
    "shot01_runtime_profile_exact_request_readiness_driver.py"
)
OUTPUT_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-runtime-profile-exact-request-readiness-blocked-v1.json"
)
COMFY_ROOT = Path("/home/reggie/ComfyUI")
T8_ROOT = COMFY_ROOT / "custom_nodes/minimax-h3-audio-T8"
VIDEOHELPERSUITE_ROOT = COMFY_ROOT / "custom_nodes/ComfyUI-VideoHelperSuite"
COMFY_CLIENT_PATH = "src/ai_video/comfy_client.py"

PREVIOUS_EVIDENCE_SHA256 = (
    "55c217616b0967c95a240caf920a1cf7483b4837b59124ad0fda4ca86b6ed45b"
)
PREVIOUS_ENVELOPE_SHA256 = (
    "2ffbb5de9291470ddbd8a7703523aa3bfe710e771ce6bc8f4e6d570998648b39"
)
COMFY_CLIENT_SHA256 = (
    "29be8ddd932f709563dc07c135db8e21bf06f89a3b4ab0d526c6ebd911d0dca4"
)
REQUIRED_COMFYUI_COMMIT = "7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa"
REQUIRED_T8_COMMIT = "977df788fcf8b971dc3d0fc7d6baa79a0edfaf40"
REQUIRED_T8_VERSION = "1.36.2"
REQUIRED_VIDEOHELPERSUITE_COMMIT = "4ee72c065db22c9d96c2427954dc69e7b908444b"
REQUIRED_SAGEATTENTION_VERSION = "2.2.0"
REQUIRED_LAUNCH_CAPABILITIES = ("sage_attention",)
BLOCKER = "CANONICAL_REQUEST_SEAM_DEPENDENCY_IDENTITY_DRIFT"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256(path.read_bytes())


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


def _assert_sha256(path: Path, expected: str) -> bytes:
    payload = path.read_bytes()
    if _sha256(payload) != expected:
        raise RuntimeError(f"accepted parent bytes drifted: {path}")
    return payload


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _run(command: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _git_revision(root: Path) -> str:
    return _run(["git", "-C", str(root), "rev-parse", "HEAD"])


def _git_clean(root: Path) -> bool:
    return not _run(["git", "-C", str(root), "status", "--short"])


def _repo_status(path: str) -> str:
    return _run(["git", "status", "--short", "--", path], cwd=REPO_ROOT)


def _supervisor_status() -> dict[str, object]:
    return json.loads(
        _run(["python", "scripts/comfyui_supervisor.py", "status"], cwd=REPO_ROOT)
    )


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
        raise RuntimeError("canonical supervisor is not active")
    observed = _run(
        [
            "systemctl",
            "--user",
            "show",
            unit,
            "--property=ExecStart",
            "--value",
        ]
    )
    capabilities = []
    if "--use-sage-attention" in observed.split():
        capabilities.append("sage_attention")
    return {
        "inspection_mode": "systemd_exec_start_read_only",
        "exec_start_sha256": _sha256(observed.encode("utf-8")),
        "launch_capabilities": capabilities,
    }


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
    before = _tree_snapshot(PROJECT_ROOT)
    previous_evidence_bytes = _assert_sha256(
        PREVIOUS_EVIDENCE_PATH,
        PREVIOUS_EVIDENCE_SHA256,
    )
    _assert_sha256(PREVIOUS_ENVELOPE_PATH, PREVIOUS_ENVELOPE_SHA256)
    previous = json.loads(previous_evidence_bytes)
    expected = previous.get("source_identity", {}).get("files")
    if not isinstance(expected, dict) or not expected:
        raise RuntimeError("accepted dependency identity map is missing")
    expected = {**expected, COMFY_CLIENT_PATH: COMFY_CLIENT_SHA256}
    current = {
        path: _sha256_file(REPO_ROOT / path)
        for path in sorted(expected)
    }
    drift = {
        path: {
            "accepted_sha256": expected[path],
            "current_sha256": current[path],
            "git_status": _repo_status(path),
        }
        for path in sorted(expected)
        if current[path] != expected[path]
    }
    if not drift:
        raise RuntimeError("request-seam dependency drift is no longer present")

    supervisor_before = _supervisor_status()
    launch_identity = _launch_identity(supervisor_before)
    runtime = {
        "comfyui_commit": _git_revision(COMFY_ROOT),
        "t8_commit": _git_revision(T8_ROOT),
        "t8_version": tomllib.loads(
            (T8_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["version"],
        "videohelpersuite_commit": _git_revision(VIDEOHELPERSUITE_ROOT),
        "sageattention_version": importlib.metadata.version("sageattention"),
        "launch_identity": launch_identity,
        "checkout_clean": {
            "comfyui": _git_clean(COMFY_ROOT),
            "t8": _git_clean(T8_ROOT),
            "videohelpersuite": _git_clean(VIDEOHELPERSUITE_ROOT),
        },
    }
    queue = _queue_snapshot()
    supervisor_after = _supervisor_status()
    if supervisor_before != supervisor_after:
        raise RuntimeError("ComfyUI supervisor identity changed during blocker capture")
    if (
        runtime["comfyui_commit"] != REQUIRED_COMFYUI_COMMIT
        or runtime["t8_commit"] != REQUIRED_T8_COMMIT
        or runtime["t8_version"] != REQUIRED_T8_VERSION
        or runtime["videohelpersuite_commit"] != REQUIRED_VIDEOHELPERSUITE_COMMIT
        or runtime["sageattention_version"] != REQUIRED_SAGEATTENTION_VERSION
        or tuple(launch_identity["launch_capabilities"])
        != REQUIRED_LAUNCH_CAPABILITIES
        or not all(runtime["checkout_clean"].values())
    ):
        raise RuntimeError("runtime identity changed while capturing request-seam drift")
    after = _tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("blocker capture mutated canonical Production state")

    lineage = previous["canonical_lineage"]
    evidence = {
        "schema_version": "drama-m6-d-shot01-runtime-exact-request-readiness-blocked/1",
        "status": "BLOCKED_BEFORE_CANONICAL_PROVIDER_PREFLIGHT",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": previous["target_shot"],
        "last_accepted_lineage": {
            "previous_evidence_path": PREVIOUS_EVIDENCE_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "previous_evidence_sha256": PREVIOUS_EVIDENCE_SHA256,
            "previous_envelope_path": PREVIOUS_ENVELOPE_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "previous_envelope_sha256": PREVIOUS_ENVELOPE_SHA256,
            "request_hash": lineage["request_hash"],
            "verified_projection_hash": lineage["verified_projection_hash"],
            "requirement_hash": lineage["requirement_hash"],
            "prompt_sha256": lineage["prompt_sha256"],
            "provider_bound_request_hash": lineage["provider_bound_request_hash"],
            "compiled_request_hash": lineage["compiled_request_hash"],
            "request_input_hash": lineage["request_input_hash"],
            "resolved_generation_hash": lineage["resolved_generation_hash"],
            "preview_fingerprint": lineage["preview_fingerprint"],
        },
        "runtime_identity": {
            "required": {
                "comfyui_commit": REQUIRED_COMFYUI_COMMIT,
                "t8_commit": REQUIRED_T8_COMMIT,
                "t8_version": REQUIRED_T8_VERSION,
                "videohelpersuite_commit": REQUIRED_VIDEOHELPERSUITE_COMMIT,
                "sageattention_version": REQUIRED_SAGEATTENTION_VERSION,
                "launch_capabilities": list(REQUIRED_LAUNCH_CAPABILITIES),
            },
            "current": runtime,
            "result": "MATCH",
            "supervisor_before": supervisor_before,
            "supervisor_after": supervisor_after,
            "queue_at_capture": queue,
        },
        "dependency_identity_drift": {
            "blocker_id": BLOCKER,
            "strict_check_order": "hash_before_import",
            "current_modules_imported": False,
            "drift": drift,
            "accepted_dependency_count": len(expected),
            "current_exact_request_reopen": "NOT_EVALUATED_DEPENDENCY_DRIFT",
            "canonical_provider_preflight": "NOT_INVOKED_DEPENDENCY_DRIFT",
            "preliminary_unsealed_preflight_observation": (
                "NOT_ACCEPTED_AFTER_INDEPENDENT_PROVENANCE_REVIEW"
            ),
        },
        "submit_readiness": {
            "pre_submit_prerequisite_ready": False,
            "blockers": [BLOCKER],
            "budget": "NOT_APPLICABLE_LOCAL_UNMETERED",
            "cloud_egress": "DENIED_AND_NOT_USED",
            "durable_submit_intent": "NOT_CREATED",
            "one_use_permit": "NOT_MINTED",
            "provider_preflight": "NOT_INVOKED_DEPENDENCY_DRIFT",
            "provider_submit": "NOT_INVOKED",
            "submit_effect_allowed": False,
        },
        "effects": {
            "production_state_files_before": len(before),
            "production_state_files_after": len(after),
            "driver_production_state_writes": 0,
            "driver_video_generation_request_persisted": False,
            "driver_provider_preflight_count": 0,
            "driver_durable_submit_intent_count": 0,
            "driver_permit_mint_count": 0,
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
            "generator_id": "drama-shot01-runtime-request-seam-drift-blocker@1",
            "driver_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "driver_sha256": _sha256_file(Path(__file__)),
            "failed_readiness_driver_path": READINESS_DRIVER_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "failed_readiness_driver_sha256": _sha256_file(READINESS_DRIVER_PATH),
        },
    }
    evidence_bytes = _canonical_json_bytes(evidence)
    _write_immutable(OUTPUT_PATH, evidence_bytes)
    print(OUTPUT_PATH.relative_to(REPO_ROOT).as_posix())
    print(_sha256(evidence_bytes))


if __name__ == "__main__":
    main()
