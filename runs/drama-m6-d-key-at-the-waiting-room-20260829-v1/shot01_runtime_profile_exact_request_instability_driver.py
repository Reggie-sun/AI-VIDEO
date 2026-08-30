"""Seal two-snapshot request-seam instability without importing Product code."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
BLOCKER_DRIVER_PATH = RUN_ROOT / (
    "shot01_runtime_profile_exact_request_readiness_blocker_driver.py"
)
PREVIOUS_OBSERVATION_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-runtime-profile-exact-request-readiness-blocked-v1.json"
)
OUTPUT_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-runtime-profile-exact-request-readiness-blocked-v2.json"
)

BLOCKER_DRIVER_SHA256 = (
    "e5e2eefc4176cd885a67bac778cfdb3089cf0110dab36c566908a17300ccf919"
)
PREVIOUS_OBSERVATION_SHA256 = (
    "d8f73639958447b8d138995b7a8a234e6f5e344217b68417fea0cd9dac675d2f"
)
BLOCKER = "CANONICAL_REQUEST_SEAM_DEPENDENCY_IDENTITY_UNSTABLE"


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
        raise RuntimeError(f"observation source bytes drifted: {path}")
    return payload


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("drama_runtime_drift_observer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module could not be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    _assert_sha256(BLOCKER_DRIVER_PATH, BLOCKER_DRIVER_SHA256)
    previous_bytes = _assert_sha256(
        PREVIOUS_OBSERVATION_PATH,
        PREVIOUS_OBSERVATION_SHA256,
    )
    previous = json.loads(previous_bytes)
    blocker = _load_module(BLOCKER_DRIVER_PATH)
    _assert_sha256(
        blocker.PREVIOUS_EVIDENCE_PATH,
        blocker.PREVIOUS_EVIDENCE_SHA256,
    )
    before = blocker._tree_snapshot(PROJECT_ROOT)

    accepted_dependencies = previous["dependency_identity_drift"][
        "accepted_dependency_count"
    ]
    previous_drift = previous["dependency_identity_drift"]["drift"]
    expected = json.loads(blocker.PREVIOUS_EVIDENCE_PATH.read_bytes())[
        "source_identity"
    ]["files"]
    expected = {**expected, blocker.COMFY_CLIENT_PATH: blocker.COMFY_CLIENT_SHA256}
    if len(expected) != accepted_dependencies:
        raise RuntimeError("accepted dependency count changed")

    def snapshot() -> dict[str, str]:
        return {
            path: _sha256_file(REPO_ROOT / path)
            for path in sorted(expected)
        }

    first = snapshot()
    supervisor_before = blocker._supervisor_status()
    launch = blocker._launch_identity(supervisor_before)
    runtime = {
        "comfyui_commit": blocker._git_revision(blocker.COMFY_ROOT),
        "t8_commit": blocker._git_revision(blocker.T8_ROOT),
        "t8_version": blocker.tomllib.loads(
            (blocker.T8_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["version"],
        "videohelpersuite_commit": blocker._git_revision(
            blocker.VIDEOHELPERSUITE_ROOT
        ),
        "sageattention_version": blocker.importlib.metadata.version("sageattention"),
        "launch_identity": launch,
        "checkout_clean": {
            "comfyui": blocker._git_clean(blocker.COMFY_ROOT),
            "t8": blocker._git_clean(blocker.T8_ROOT),
            "videohelpersuite": blocker._git_clean(blocker.VIDEOHELPERSUITE_ROOT),
        },
    }
    queue = blocker._queue_snapshot()
    supervisor_after = blocker._supervisor_status()
    second = snapshot()
    if first != second:
        raise RuntimeError("dependency bytes changed within the second observation")
    if supervisor_before != supervisor_after:
        raise RuntimeError("supervisor changed within the second observation")
    if (
        runtime["comfyui_commit"] != blocker.REQUIRED_COMFYUI_COMMIT
        or runtime["t8_commit"] != blocker.REQUIRED_T8_COMMIT
        or runtime["t8_version"] != blocker.REQUIRED_T8_VERSION
        or runtime["videohelpersuite_commit"]
        != blocker.REQUIRED_VIDEOHELPERSUITE_COMMIT
        or runtime["sageattention_version"]
        != blocker.REQUIRED_SAGEATTENTION_VERSION
        or tuple(launch["launch_capabilities"])
        != blocker.REQUIRED_LAUNCH_CAPABILITIES
        or not all(runtime["checkout_clean"].values())
    ):
        raise RuntimeError("runtime identity no longer matches the selected profile")

    current_drift = {
        path: {
            "accepted_sha256": expected[path],
            "observed_sha256": first[path],
            "git_status": blocker._repo_status(path),
        }
        for path in sorted(expected)
        if first[path] != expected[path]
    }
    changed_between_observations = {
        path: {
            "first_observed_sha256": item["current_sha256"],
            "second_observed_sha256": first[path],
        }
        for path, item in sorted(previous_drift.items())
        if path in first and first[path] != item["current_sha256"]
    }
    if not current_drift or not changed_between_observations:
        raise RuntimeError("two-snapshot dependency instability is not demonstrated")
    if any(not item["git_status"].startswith("M ") for item in current_drift.values()):
        raise RuntimeError("current drift is not an uncommitted working-tree change")

    after = blocker._tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("instability capture mutated canonical Production state")

    evidence = {
        "schema_version": "drama-m6-d-shot01-runtime-request-seam-instability/1",
        "status": "BLOCKED_DEPENDENCY_IDENTITY_UNSTABLE",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": previous["target_shot"],
        "last_accepted_lineage": previous["last_accepted_lineage"],
        "runtime_identity": {
            "required": previous["runtime_identity"]["required"],
            "second_observation": runtime,
            "result": "MATCH",
            "supervisor_before": supervisor_before,
            "supervisor_after": supervisor_after,
            "queue_at_capture": queue,
        },
        "dependency_identity_instability": {
            "blocker_id": BLOCKER,
            "accepted_dependency_count": len(expected),
            "first_observation_path": PREVIOUS_OBSERVATION_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "first_observation_sha256": PREVIOUS_OBSERVATION_SHA256,
            "changed_between_observations": changed_between_observations,
            "second_observation_drift": current_drift,
            "second_observation_stable_within_capture": True,
            "current_exact_request_reopen": "NOT_EVALUATED_DEPENDENCY_UNSTABLE",
            "canonical_provider_preflight": "NOT_INVOKED_DEPENDENCY_UNSTABLE",
            "current_exact_hash_claim": False,
            "stop_condition": (
                "dependency owner must commit stable bytes before exact reopen"
            ),
        },
        "submit_readiness": {
            "pre_submit_prerequisite_ready": False,
            "blockers": [BLOCKER],
            "budget": "NOT_APPLICABLE_LOCAL_UNMETERED",
            "cloud_egress": "DENIED_AND_NOT_USED",
            "durable_submit_intent": "NOT_CREATED",
            "one_use_permit": "NOT_MINTED",
            "provider_preflight": "NOT_INVOKED_DEPENDENCY_UNSTABLE",
            "provider_submit": "NOT_INVOKED",
            "submit_effect_allowed": False,
        },
        "effects": previous["effects"],
        "status_boundary": previous["status_boundary"],
        "source_identity": {
            "actor_identity": "codex_primary_agent",
            "generator_id": "drama-shot01-runtime-request-seam-instability@1",
            "driver_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "driver_sha256": _sha256_file(Path(__file__)),
            "first_observation_driver_path": BLOCKER_DRIVER_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "first_observation_driver_sha256": BLOCKER_DRIVER_SHA256,
        },
    }
    evidence_bytes = _canonical_json_bytes(evidence)
    _write_immutable(OUTPUT_PATH, evidence_bytes)
    print(OUTPUT_PATH.relative_to(REPO_ROOT).as_posix())
    print(_sha256(evidence_bytes))


if __name__ == "__main__":
    main()
