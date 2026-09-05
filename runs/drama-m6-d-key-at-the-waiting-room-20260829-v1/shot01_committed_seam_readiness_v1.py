"""Exact Shot 01 reopen and GET-only canonical preflight; never submit."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
SOURCE_COMMIT = "3bd41443ab295289fe61a26846bfaab1a327622b"
PARENT = ROOT / "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v5.blocked.json"
PARENT_HASH = "febf132fd11284c471ee7ce4df82b9cd519484256e782ed40e44df7e016b02b1"
PREVIOUS = RUN / "evidence/drama-shot-01-source-audio-policy-readiness-accepted-v4.json"
PREVIOUS_HASH = "55c217616b0967c95a240caf920a1cf7483b4837b59124ad0fda4ca86b6ed45b"
OUTPUT = RUN / "evidence/drama-shot-01-committed-seam-readiness-v2.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sealed(path: Path, expected: str) -> dict:
    data = path.read_bytes()
    require(digest(data) == expected, f"sealed bytes drifted: {path}")
    return json.loads(data)


def committed_snapshot() -> dict[str, str]:
    prefixes = ("src", "workflows", RUN.relative_to(ROOT).as_posix())
    entries = git("ls-tree", "-rz", SOURCE_COMMIT, "--", *prefixes).split(b"\0")
    result = {}
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        require(kind == b"blob" and mode in (b"100644", b"100755"), "unsupported source entry")
        path = raw_path.decode()
        data = (ROOT / path).read_bytes()
        require(not (ROOT / path).is_symlink(), f"source symlink: {path}")
        require(data == git("cat-file", "blob", oid.decode()), f"committed source drift: {path}")
        result[path] = digest(data)
    # Untracked importable modules must not supplement the pinned source inventory.
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.py")}
    require(actual <= result.keys(), "uncommitted Python module in source tree")
    return result


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, RUN / filename)
    require(spec is not None and spec.loader is not None, "driver loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def no_network(event: str, args: tuple) -> None:
    if event == "socket.getaddrinfo":
        require(args[0] == "127.0.0.1" and args[1] == 8188, "non-loopback DNS prohibited")
    if event in ("socket.connect", "socket.connect_ex"):
        require(args[1] == ("127.0.0.1", 8188), "non-loopback connection prohibited")
    if event == "socket.sendto":
        raise RuntimeError("datagram effects prohibited")


def collect() -> dict:
    parent = sealed(PARENT, PARENT_HASH)
    previous = sealed(PREVIOUS, PREVIOUS_HASH)
    before = committed_snapshot()  # Verify all Product/helper bytes before their first import.
    for path, expected in previous["source_identity"]["files"].items():
        if not path.startswith("src/"):
            require(digest((ROOT / path).read_bytes()) == expected, f"immutable parent drift: {path}")
    source = load("committed_source_audio", "shot01_source_audio_policy_readiness_driver.py")
    timing = load("committed_timing", "shot01_timing_request_readiness_driver.py")
    production_before = source._tree_snapshot(source.PROJECT_ROOT)
    policy, policy_identity = source._load_policy()
    require(policy_identity["authority_status"] == "ACCEPTED_AND_SEALED", "unaccepted audio policy")
    require(policy_identity == previous["policy_identity"], "accepted audio policy identity drift")
    exact = source._reopen_exact_request(timing)
    routed = exact["routed"]
    observed = {
        "request_hash": exact["request"].request_content_hash,
        "verified_projection_hash": exact["projection"].projection_hash,
        "requirement_hash": exact["requirement"].requirement_hash,
        "prompt_sha256": exact["prompt"].prompt_sha256,
        "provider_bound_request_hash": routed["provider_bound"].provider_bound_request_hash,
        "compiled_request_hash": routed["compiled"].compiled_request_hash,
        "request_input_hash": routed["request"].request_input_hash,
        "resolved_generation_hash": routed["resolved"].resolved_generation_hash,
        "preview_fingerprint": routed["preview"].preview_fingerprint,
    }
    require(all(parent["accepted_lineage"][k] == v for k, v in observed.items()), "exact request identity drift")
    loaded = timing.load_production_project(source.PROJECT_ROOT / "project.yaml")
    require(loaded.manifest.active_dependency_graph.content_hash == timing.ACTIVE_GRAPH_HASH, "active graph drift")
    shot = loaded.shots[0]
    require({"shot_id": shot.shot_id, "revision": shot.revision, "content_hash": shot.content_hash} == parent["target_shot"], "Shot identity drift")
    audio = policy["source_audio_policy"]
    requirement = exact["requirement"]
    prompt = exact["prompt"].prompt_text
    require(audio["source_type"] == "GENERATED" and audio["policy"] == "KEEP", "audio selection drift")
    require(audio["request_native_audio_required"] is True and routed["request"].output_requirement.native_audio is True, "native audio drift")
    require(tuple(routed["selected"].output_capability.native_audio_options) == (True,), "native audio capability drift")
    require(requirement.audio_need.value == "required", "audio requirement drift")
    require(audio["required_dialogue"] == requirement.generation_intent.dialogue_intent.verbatim_text == source.EXACT_DIALOGUE, "dialogue drift")
    require(audio["required_ambience"] == requirement.generation_intent.ambience_intent.environment_bed, "ambience drift")
    require(audio["music"] == requirement.generation_intent.music_intent.mode, "music drift")
    require(len(prompt.splitlines()) == 3 and prompt.count(source.EXACT_DIALOGUE) == 1, "prompt grammar drift")
    require(routed["family"].capabilities().provider_name == source.EXPECTED_PROVIDER, "provider drift")
    require(routed["selected"].model_id == source.EXPECTED_MODEL and routed["selected"].capability_id == source.EXPECTED_CAPABILITY, "route drift")
    require(routed["profile"].profile_content_hash == "4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7", "profile drift")
    require(not routed["policy"].remote_authorized and not routed["policy"].budget_authorized, "remote policy drift")
    runtime = exact["runtime"]
    require(runtime["supervisor_before"] == runtime["supervisor_after"], "supervisor drift")
    require(runtime["supervisor_after"]["active_state"] == "active", "canonical supervisor inactive")
    require(all(runtime["checkout_clean"].values()), "dirty runtime checkout")
    require(runtime["current"] == runtime["required"] and runtime["result"] == "MATCH", "runtime identity mismatch")
    pid = runtime["supervisor_after"]["main_pid"]
    listener = subprocess.check_output(["ss", "-ltnp", "sport = :8188"], text=True)
    require(f"pid={pid}," in listener and "127.0.0.1:8188" in listener, "listener owner mismatch")
    from ai_video.comfy_client import ComfyClient
    import httpx

    requests = []
    responses = []

    def guard(request):
        require(request.method == "GET" and str(request.url) in {
            "http://127.0.0.1:8188/system_stats", "http://127.0.0.1:8188/object_info",
            "http://127.0.0.1:8188/queue",
        }, "HTTP effect not allowed")
        requests.append({"method": request.method, "url": str(request.url)})

    def capture(response):
        response.read()
        responses.append({"url": str(response.request.url), "status": response.status_code,
                          "sha256": digest(response.content), "byte_size": len(response.content)})

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=30,
                      event_hooks={"request": [guard], "response": [capture]}) as http:
        def queue():
            response = http.get("http://127.0.0.1:8188/queue")
            response.raise_for_status()
            value = response.json()
            require(value.get("queue_running") == [] and value.get("queue_pending") == [], "ComfyUI queue not empty")
            return {"running": 0, "pending": 0}

        queue_before = queue()
        inspection = timing.T8RuntimeInspection(**runtime["current"])
        provider = timing.ComfyUIT8VideoProvider(
            routed["profile"], artifact_root=ROOT, comfy_root=Path("/home/reggie/ComfyUI"),
            runtime_inspector=lambda: inspection,
            transport=ComfyClient("http://127.0.0.1:8188", http_client=http),
        )
        provider.preflight(routed["resolved"])
        queue_after = queue()
    readiness = load("committed_runtime_after", "provider_request_readiness_driver.py")
    supervisor_after = readiness._supervisor_status()
    require(supervisor_after == runtime["supervisor_after"], "supervisor changed during preflight")
    runtime_after = readiness._runtime_identity(routed["profile"], supervisor_after)
    require(runtime_after["current"] == runtime["current"] and runtime_after["result"] == "MATCH", "runtime drift after preflight")
    runtime["canonical_provider_preflight"] = "PASS_READ_ONLY_COMPONENT_AND_OBJECT_INFO"
    after = committed_snapshot()
    require(before == after, "source snapshot changed during inspection")
    require(production_before == source._tree_snapshot(source.PROJECT_ROOT), "Production state changed")
    imported = {}
    for module in tuple(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if path and Path(path).resolve().is_relative_to(ROOT / "src"):
            relative = Path(path).resolve().relative_to(ROOT).as_posix()
            require(relative in before, "imported module outside committed inventory")
            imported[relative] = before[relative]
    return {
        "schema_version": "drama-shot01-committed-seam-readiness/1",
        "decision": "pre_submit_prerequisite_ready",
        "blockers": [],
        "resolved_historical_blocker": "CANONICAL_REQUEST_SEAM_DEPENDENCY_IDENTITY_UNSTABLE",
        "source_identity": {"commit": SOURCE_COMMIT, "inventory_sha256": digest(canonical(before)), "inventory_file_count": len(before), "verified_before_import": True, "verified_after_reopen": True, "imported_product_files": imported, "changed_since_v4": {p: {"previous": h, "current": before[p]} for p, h in previous["source_identity"]["files"].items() if p in before and before[p] != h}, "driver_path": Path(__file__).relative_to(ROOT).as_posix(), "driver_sha256": digest(Path(__file__).read_bytes()), "python_executable": sys.executable, "python_version": sys.version.split()[0]},
        "parent": {"path": PARENT.relative_to(ROOT).as_posix(), "sha256": PARENT_HASH, "accepted_evidence_path": PREVIOUS.relative_to(ROOT).as_posix(), "accepted_evidence_sha256": PREVIOUS_HASH},
        "canonical_identity": {"target_shot": parent["target_shot"], "project": loaded.manifest.active_project.model_dump(mode="json"), "registry": loaded.manifest.active_registry.model_dump(mode="json"), "active_graph_hash": timing.ACTIVE_GRAPH_HASH, **observed},
        "offline_exact_reopen": "PASS",
        "selected_provider": {"provider": source.EXPECTED_PROVIDER, "model": source.EXPECTED_MODEL, "capability": source.EXPECTED_CAPABILITY, "profile_hash": routed["profile"].profile_content_hash, "workflow_sha256": routed["profile"].workflow_sha256, "binding_sha256": routed["profile"].binding_sha256, "compiler": routed["compiler_contract"].model_dump(mode="json"), "output": routed["request"].output_requirement.model_dump(mode="json"), "fallback_allowed": False},
        "source_audio_policy": {"selection": "GENERATED + KEEP", "identity": policy_identity, "native_audio": True, "sound_facts_match": True},
        "runtime": runtime,
        "canonical_provider_preflight": "PASS_READ_ONLY_COMPONENT_AND_OBJECT_INFO",
        "read_only_transport": {"requests": requests, "responses": responses, "queue_before": queue_before, "queue_after": queue_after, "listener_pid": pid},
        "submit_readiness": {"pre_submit_prerequisite_ready": True, "budget": "NOT_APPLICABLE_LOCAL_UNMETERED", "cloud_egress": "DENIED_AND_NOT_USED", "durable_submit_intent": "NOT_CREATED", "one_use_permit": "NOT_MINTED", "submit_effect_allowed": False, "submit_effect_blockers": ["DURABLE_SUBMIT_INTENT_NOT_CREATED", "ONE_USE_PERMIT_NOT_MINTED"]},
        "effects": {"production_tree_sha256_before": digest(canonical(production_before)), "production_tree_sha256_after": digest(canonical(production_before)), "production_files": len(production_before), "provider_preflight": 1, "provider_submit": 0, "request_persistence": 0, "permit_mint": 0, "runtime_lifecycle": 0, "media": 0, "video_analysis": 0, "production_writes": 0},
        "status_boundary": parent["status_boundary"],
    }


def main() -> None:
    sys.addaudithook(no_network)
    payload = canonical(collect())
    if OUTPUT.exists():
        require(OUTPUT.read_bytes() == payload, "immutable evidence bytes differ")
    else:
        with OUTPUT.open("xb") as stream:
            stream.write(payload)
    print(json.dumps({"path": OUTPUT.relative_to(ROOT).as_posix(), "sha256": digest(payload), "decision": "pre_submit_prerequisite_ready"}))


if __name__ == "__main__":
    main()
