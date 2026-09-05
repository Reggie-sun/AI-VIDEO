"""One GET-only Shot 01 preflight from the formal v3 source-binding loader."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
PROJECT = RUN / "production-project"
ACCEPTANCE_SHA256 = "70dc023257863683157a12b0849f2fd3c6d8fe2d9c9dacf70c95d8ce38797276"
ACCEPTED_PROMPT_SHA256 = "e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47"
EXACT_DIALOGUE = "钥匙还在。回去，一起开门。"
LOADER_PATH = (RUN.relative_to(ROOT) / "shot01_authoring_source_binding_v3.py").as_posix()
READINESS_PATH = (RUN.relative_to(ROOT) / "provider_request_readiness_driver.py").as_posix()
SELF_PATH = Path(__file__).relative_to(ROOT).as_posix()
SUPERVISOR_PATH = "scripts/comfyui_supervisor.py"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


class PreflightCheckError(RuntimeError):
    """A safe, named check failure that may be included in blocked evidence."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise PreflightCheckError(reason)


def _no_network(event: str, args: tuple[object, ...]) -> None:
    if event == "socket.getaddrinfo":
        _require(args[0] == "127.0.0.1" and args[1] == 8188, "non-loopback DNS blocked")
    if event in ("socket.connect", "socket.connect_ex"):
        _require(args[1] == ("127.0.0.1", 8188), "non-loopback socket blocked")
    if event == "socket.sendto":
        raise PreflightCheckError("datagram network blocked")


def _safe(path: str) -> Path:
    value = Path(path)
    _require(not value.is_absolute() and ".." not in value.parts, "unsafe source path")
    resolved = (ROOT / value).resolve()
    _require(resolved.is_relative_to(ROOT.resolve()), "source path escapes repository")
    current = ROOT
    for part in value.parts:
        current = current / part
        _require(not current.is_symlink(), "source path uses symlink")
    return value


def _inventory(source_commit: str) -> dict[str, str]:
    _require(len(source_commit) == 40 and all(char in "0123456789abcdef" for char in source_commit), "source commit must be a full lowercase SHA-1")
    required = (LOADER_PATH, READINESS_PATH, SELF_PATH, SUPERVISOR_PATH)
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", source_commit, "--", "src", "workflows", *required],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    inventory: dict[str, str] = {}
    for entry in result.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        _require(kind == b"blob" and mode in (b"100644", b"100755"), "unsupported pinned entry")
        path = raw_path.decode("utf-8")
        current = ROOT / _safe(path)
        committed = subprocess.run(
            ["git", "cat-file", "blob", oid.decode("ascii")],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        _require(current.read_bytes() == committed, f"pinned source drift: {path}")
        inventory[path] = _sha256(committed)
    _require(all(path in inventory for path in required), "preflight helper inventory is incomplete")
    modules = {item.relative_to(ROOT).as_posix() for item in (ROOT / "src").rglob("*.py")}
    _require(modules <= inventory.keys(), "uncommitted Product module supplements source commit")
    return inventory


def _load(inventory: dict[str, str], name: str, path: str) -> ModuleType:
    _require(path in inventory, f"unverified helper import: {path}")
    target = ROOT / _safe(path)
    _require(_sha256(target.read_bytes()) == inventory[path], f"helper drift before import: {path}")
    spec = importlib.util.spec_from_file_location(name, target)
    _require(spec is not None and spec.loader is not None, f"cannot import helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _check_runtime(readiness: ModuleType, profile: object) -> tuple[dict[str, object], object, str, dict[str, object]]:
    supervisor = readiness._supervisor_status()
    runtime = readiness._runtime_identity(profile, supervisor)
    _require(supervisor.get("active_state") == "active" and supervisor.get("sub_state") == "running", "ComfyUI is not active")
    _require(runtime["result"] == "MATCH" and not runtime["mismatches"] and not runtime["missing_launch_capabilities"], "profile/runtime identity mismatch")
    _require(all(runtime["checkout_clean"].values()), "runtime checkout is dirty")
    pid = supervisor.get("main_pid")
    _require(isinstance(pid, int) and pid > 0 and supervisor.get("invocation_id"), "runtime PID/invocation unavailable")
    _require(Path(f"/proc/{pid}/exe").resolve() == Path(sys.executable).resolve(), "runtime interpreter drift")
    _require(Path(f"/proc/{pid}/cwd").resolve() == readiness.COMFY_ROOT.resolve(), "runtime cwd drift")
    listener = subprocess.check_output(["ss", "-ltnp", "sport = :8188"], text=True)
    _require(f"pid={pid}," in listener and "127.0.0.1:8188" in listener, "runtime listener ownership drift")
    from ai_video.production.comfy_t8_video import T8RuntimeInspection

    inspection = T8RuntimeInspection(**runtime["current"])
    return runtime, inspection, listener, supervisor


def _assert_request(exact: dict[str, object]) -> dict[str, object]:
    from ai_video.production.project import load_production_project
    from ai_video.production.video_pre_generation import verify_current_video_generation_lineage

    request = exact["request"]
    projection = exact["projection"]
    requirement = exact["requirement"]
    prompt = exact["prompt"]
    routed = exact["routed"]
    binding = exact["source_binding"]
    canonical = binding["canonical_source_binding"]
    loaded = load_production_project(PROJECT / "project.yaml")
    shot = loaded.shots[0]
    _require(canonical["active_pre_generation_graph_hash"] == loaded.manifest.active_dependency_graph.content_hash, "source-binding graph drift")
    _require(canonical["project_content_hash"] == loaded.project.content_hash and canonical["registry_content_hash"] == loaded.registry.content_hash, "source-binding Project/Registry drift")
    _require({"shot_id": shot.shot_id, "revision": shot.revision, "content_hash": shot.content_hash} == {"shot_id": "drama.shot.waiting-room.001", "revision": 1, "content_hash": "4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b"}, "Shot 01 identity drift")
    lines = prompt.prompt_text.splitlines()
    _require(prompt.prompt_sha256 == ACCEPTED_PROMPT_SHA256, "accepted native H3 prompt hash drift")
    _require(len(lines) == 3 and lines[0].startswith("integrated_multimodal_description: ") and lines[1].startswith("overall_soundscape: ") and lines[2].startswith("non_diegetic_music: ") and prompt.prompt_text.count(EXACT_DIALOGUE) == 1, "native H3 prompt grammar drift")
    audio = exact["source_audio_policy"]
    _require(audio["selection"] == "GENERATED + KEEP" and audio["native_audio"] is True and audio["sound_facts_match"] is True, "source-audio binding drift")
    _require(requirement.audio_need.value == "required" and requirement.generation_intent.dialogue_intent.verbatim_text == EXACT_DIALOGUE, "required source audio drift")
    _require(routed["request"].output_requirement.native_audio is True and tuple(routed["selected"].output_capability.native_audio_options) == (True,), "native-audio capability drift")
    verify_current_video_generation_lineage(loaded, routed["resolved"])
    return {
        "target_shot": {"shot_id": shot.shot_id, "revision": shot.revision, "content_hash": shot.content_hash},
        "project_content_hash": loaded.project.content_hash,
        "registry_content_hash": loaded.registry.content_hash,
        "active_graph_hash": loaded.manifest.active_dependency_graph.content_hash,
        "planning_request_hash": request.request_content_hash,
        "requirement_hash": requirement.requirement_hash,
        "verified_projection_hash": projection.projection_hash,
        "prompt_sha256": prompt.prompt_sha256,
        "resolved_generation_hash": routed["resolved"].resolved_generation_hash,
    }


def _exact_identity(exact: dict[str, object]) -> dict[str, object]:
    routed = exact["routed"]
    return {
        "request_hash": exact["request"].request_content_hash,
        "projection_hash": exact["projection"].projection_hash,
        "requirement_hash": exact["requirement"].requirement_hash,
        "prompt_sha256": exact["prompt"].prompt_sha256,
        "provider_bound_request_hash": routed["provider_bound"].provider_bound_request_hash,
        "compiled_request_hash": routed["compiled"].compiled_request_hash,
        "request_input_hash": routed["request"].request_input_hash,
        "resolved_generation_hash": routed["resolved"].resolved_generation_hash,
        "preview_fingerprint": routed["preview"].preview_fingerprint,
        "source_binding": exact["source_binding"],
        "source_audio_policy": exact["source_audio_policy"],
    }


def _selected_provider(exact: dict[str, object]) -> dict[str, object]:
    routed = exact["routed"]
    profile = routed["profile"]
    selected = routed["selected"]
    return {
        "provider": routed["family"].capabilities().provider_name,
        "model": selected.model_id,
        "capability": selected.capability_id,
        "profile_hash": profile.profile_content_hash,
        "workflow_sha256": profile.workflow_sha256,
        "binding_sha256": profile.binding_sha256,
        "compiler": routed["compiler_contract"].model_dump(mode="json"),
        "output": routed["request"].output_requirement.model_dump(mode="json"),
        "fallback_allowed": False,
    }


def _output_path(value: str) -> Path:
    relative = Path(value)
    _require(relative.suffix == ".json" and not relative.is_absolute() and ".." not in relative.parts, "output must be a relative evidence JSON path")
    output = (RUN / "evidence" / relative).resolve()
    _require(output.is_relative_to((RUN / "evidence").resolve()), "output escapes evidence directory")
    return output


def _write_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_canonical(value))
        stream.flush()


def collect(source_commit: str, observations: dict[str, object]) -> dict[str, object]:
    observations["check_stage"] = "source_inventory_before_import"
    inventory_before = _inventory(source_commit)
    observations["source_inventory_sha256"] = _sha256(_canonical(inventory_before))
    loader = _load(inventory_before, "shot01_source_binding", LOADER_PATH)
    readiness = _load(inventory_before, "shot01_runtime_readiness", READINESS_PATH)
    production_before = _tree(PROJECT)
    observations["production_tree_sha256_before"] = _sha256(_canonical(production_before))
    observations["check_stage"] = "formal_reopen_before_get"
    exact = loader.reopen_exact_request(
        expected_acceptance_sha256=ACCEPTANCE_SHA256,
        source_commit=source_commit,
    )
    lineage = _assert_request(exact)
    identity_before = _exact_identity(exact)
    observations["canonical_identity_before"] = identity_before
    observations["selected_provider"] = _selected_provider(exact)
    observations["check_stage"] = "runtime_before_get"
    runtime_before, inspection, listener, supervisor_before = _check_runtime(readiness, exact["routed"]["profile"])
    observations["runtime_before"] = {**runtime_before, "supervisor": supervisor_before}
    from ai_video.comfy_client import ComfyClient
    import httpx

    requests: list[str] = []
    responses: list[dict[str, object]] = []
    allowed = {
        "http://127.0.0.1:8188/system_stats",
        "http://127.0.0.1:8188/object_info",
        "http://127.0.0.1:8188/queue",
    }

    def request_guard(request: object) -> None:
        _require(request.method == "GET" and str(request.url) in allowed, "non-canonical HTTP request blocked")
        requests.append(str(request.url))
        observations["transport_request_count"] = len(requests)

    def response_capture(response: object) -> None:
        response.read()
        responses.append({"url": str(response.request.url), "status": response.status_code, "sha256": _sha256(response.content), "byte_size": len(response.content)})
        observations["transport_responses"] = responses

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=30, event_hooks={"request": [request_guard], "response": [response_capture]}) as http:
        def queue() -> dict[str, int]:
            response = http.get("http://127.0.0.1:8188/queue")
            response.raise_for_status()
            body = response.json()
            _require(body.get("queue_running") == [] and body.get("queue_pending") == [], "ComfyUI queue is occupied")
            return {"running": 0, "pending": 0}

        queue_before = queue()
        provider = readiness.ComfyUIT8VideoProvider(
            exact["routed"]["profile"],
            artifact_root=ROOT,
            comfy_root=readiness.COMFY_ROOT,
            runtime_inspector=lambda: inspection,
            transport=ComfyClient("http://127.0.0.1:8188", http_client=http),
        )
        provider.preflight(exact["routed"]["resolved"])
        queue_after = queue()
    runtime_after, _, _, supervisor_after = _check_runtime(readiness, exact["routed"]["profile"])
    observations["runtime_after"] = {**runtime_after, "supervisor": supervisor_after}
    _require(runtime_before == runtime_after and supervisor_before == supervisor_after, "runtime identity changed during GET-only preflight")
    _require(_tree(PROJECT) == production_before, "GET-only preflight changed Production state")
    observations["production_tree_sha256_after"] = _sha256(_canonical(_tree(PROJECT)))
    observations["check_stage"] = "formal_reopen_after_get"
    exact_after = loader.reopen_exact_request(
        expected_acceptance_sha256=ACCEPTANCE_SHA256,
        source_commit=source_commit,
    )
    _require(_exact_identity(exact_after) == identity_before, "formal source-binding request identity changed during GET-only preflight")
    _require(_assert_request(exact_after) == lineage, "formal source-binding lineage changed during GET-only preflight")
    observations["check_stage"] = "source_inventory_after_get"
    inventory_after = _inventory(source_commit)
    _require(inventory_after == inventory_before, "source inventory changed during GET-only preflight")
    return {
        "schema_version": "drama-shot01-source-binding-preflight/1",
        "status": "PASS_READ_ONLY_PROVIDER_PREFLIGHT",
        "source_commit": source_commit,
        "source_inventory_sha256": _sha256(_canonical(inventory_before)),
        "source_inventory_file_count": len(inventory_before),
        "driver_sha256": _sha256(Path(__file__).read_bytes()),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "source_binding": exact["source_binding"],
        "canonical_lineage": lineage,
        "exact_request_identity": identity_before,
        "selected_provider": _selected_provider(exact),
        "source_audio_policy": exact["source_audio_policy"],
        "runtime": {**runtime_after, "supervisor_before": supervisor_before, "supervisor_after": supervisor_after},
        "transport": {"allowed_get_urls": sorted(allowed), "requests": requests, "responses": responses, "queue_before": queue_before, "queue_after": queue_after, "listener": listener},
        "effects": {"production_tree_sha256_before": _sha256(_canonical(production_before)), "production_tree_sha256_after": _sha256(_canonical(production_before)), "provider_preflight": 1, "provider_submit": 0, "request_persistence": 0, "permit_mint": 0, "candidate_activation": False, "media": 0, "video_analysis": 0, "runtime_lifecycle": 0},
        "status_boundary": {"execution": "STOP_BEFORE_SUBMIT", "m6_d": "NOT_EVALUATED", "next_shot_submit_allowed": False, "P6": "NOT_EVALUATED", "final_acceptance": "NOT_EVALUATED"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = _output_path(args.output)
    _require(not output.exists(), "preflight output already exists; replay denied")
    sys.addaudithook(_no_network)
    observations: dict[str, object] = {"check_stage": "not_started", "driver_sha256": _sha256(Path(__file__).read_bytes())}
    try:
        payload = collect(args.source_commit, observations)
    except Exception as error:
        _write_once(output, {"schema_version": "drama-shot01-source-binding-preflight/1", "status": "BLOCKED_READ_ONLY_PREFLIGHT", "source_commit": args.source_commit, "observed_at": datetime.now(timezone.utc).isoformat(), "driver_sha256": observations["driver_sha256"], "blocker": "READ_ONLY_PREFLIGHT_CHECK_FAILED", "check_stage": observations["check_stage"], "failure_class": type(error).__name__, "reason": str(error) if isinstance(error, PreflightCheckError) else "DEPENDENCY_CHECK_FAILED", "observations": observations, "retry_allowed": False, "status_boundary": {"execution": "STOP_BEFORE_SUBMIT", "m6_d": "NOT_EVALUATED", "next_shot_submit_allowed": False}})
        return 1
    _write_once(output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
