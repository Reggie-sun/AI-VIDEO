"""One authorized canonical Shot 01 attempt; no retry, activation or Shot 02."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
SOURCE_COMMIT = "7148b548f08b036bdd0d59dd25e0c829ee1573b4"
ATTEMPT = "drama-shot01-first-20260905-v1"
PREVIEW = RUN / "evidence/drama-shot01-first-submit-preflight-v3.json"
APPROVAL = ROOT / "docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v1.accepted.json"
HELPER = RUN / "shot01_committed_seam_readiness_v1.py"
HELPER_SHA = "f4d2c29da3e550b6f8b95b612cc20b3d0e4ed7bbede8bbf85f91350670d0a847"
V6 = ROOT / "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v6.accepted.json"
V6_SHA = "4db6a56bf8c043a308d989be38af726f2003e94686e75fbd88209c1692aa245f"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def write_new(path: Path, value: object) -> None:
    with path.open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def event(name: str, value: dict) -> None:
    payload = {"attempt_id": ATTEMPT, "event": name, "at": datetime.now(timezone.utc).isoformat(), **value}
    path = RUN / f"evidence/{ATTEMPT}-{name}.json"
    write_new(path, payload)
    print(json.dumps({"event": name, "evidence": str(path.relative_to(ROOT)),
                      **{k: v for k, v in value.items() if k != "fresh_preflight"}}), flush=True)


def creative_lineage(module) -> dict:
    prefix = "docs/superpowers/artifacts/drama/b-d0/"
    package_path = prefix + "authoring-package/key-at-the-waiting-room-v3.proposed.json"
    package = module.sealed(ROOT / package_path, "a5ec4f78b05ce189d9eaa0cf694ffaba0747b499f4e85fd1ac1ac4221ec61331")
    accept_path = prefix + "authoring-package/key-at-the-waiting-room-v3.accepted.json"
    module.sealed(ROOT / accept_path, "f81365c1d084d6c096d7bcbf83c06beff75100f34b6ed90bafc9341dfb247cac")
    hashes = {package_path: sha((ROOT / package_path).read_bytes()), accept_path: sha((ROOT / accept_path).read_bytes())}
    for name in ("fixture_selection_binding", "baseline_selection_binding"):
        binding = package[name]
        for kind in ("accepted_payload", "acceptance_record"):
            path, expected = binding[kind + "_path"], binding[kind + "_sha256"]
            require(module.git("show", binding[kind + "_commit"] + ":" + path) == (ROOT / path).read_bytes(), "creative committed bytes drift")
            module.sealed(ROOT / path, expected)
            hashes[path] = expected
    semantic = package["authoring_payload_source"]
    require(module.git("show", semantic["commit"] + ":" + semantic["path"]) == (ROOT / semantic["path"]).read_bytes(), "semantic committed bytes drift")
    module.sealed(ROOT / semantic["path"], semantic["sha256"])
    hashes[semantic["path"]] = semantic["sha256"]
    rubric = package["contract_binding"]
    require(sha(module.git("show", rubric["spec_commit"] + ":" + rubric["spec_path"])) == rubric["spec_sha256"], "historical rubric drift")
    baseline = json.loads((ROOT / package["baseline_selection_binding"]["accepted_payload_path"]).read_bytes())
    for ref in baseline["reference_set"]:
        path = ROOT / ref["repository_or_explicit_external_identity"]
        require(not path.is_symlink() and path.resolve().is_relative_to(ROOT), "baseline containment")
        require(path.stat().st_size == ref["media_identity"]["byte_size"] and sha(path.read_bytes()) == ref["media_identity"]["sha256"], "baseline media drift")
        hashes[path.relative_to(ROOT).as_posix()] = ref["media_identity"]["sha256"]
    return {"files": hashes, "semantic_rubric": rubric,
            "provider_reference_handoff": "NONE_T2VA_FIRST_SHOT",
            "prompt_changes": "NONE_ACCEPTED_NATIVE_COMPILATION",
            "required_human_findings": ["DRAMA-MEDIA-SHOT-" + item + "-001" for item in
                                        ("NARRATIVE", "DIALOGUE", "PERFORMANCE", "BLOCKING", "EMOTION")],
            "human_verdict": "NOT_EVALUATED", "next_shot_submit_allowed": False}


def load_helper():
    require(sha(HELPER.read_bytes()) == HELPER_SHA, "sealed readiness helper drift")
    require(sha(V6.read_bytes()) == V6_SHA, "v6 parent drift")
    spec = importlib.util.spec_from_file_location("shot01_first_submit_readiness", HELPER)
    require(spec is not None and spec.loader is not None, "helper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # New explicitly versioned observation; old helper/output/v6 bytes stay sealed.
    # The full before-import/after-reopen Git inventory guard still runs unchanged.
    module.SOURCE_COMMIT = SOURCE_COMMIT
    sys.addaudithook(module.no_network)
    return module


def capture(module) -> dict:
    lineage = creative_lineage(module)
    value = module.collect()
    return {"schema_version": "drama-shot01-first-submit-preflight/1", "attempt_id": ATTEMPT,
            "driver_sha256": sha(Path(__file__).read_bytes()), "source_commit": SOURCE_COMMIT,
            "parent_v6_sha256": V6_SHA, "helper_sha256": HELPER_SHA,
            "source_reseal": "NEW_PINNED_COMMIT_OBSERVATION_NOT_V6_REPLAY", "creative_lineage": lineage,
            "budget": {"max_submits": 1, "max_gpu_jobs": 1, "poll_timeout_seconds": 3600,
                       "retry_count": 0, "remote_egress": False}, "readiness": value}


def execute(module, approval_sha256: str) -> None:
    approval_bytes = APPROVAL.read_bytes()
    require(sha(approval_bytes) == approval_sha256, "approval identity drift")
    approval = json.loads(approval_bytes)
    require(approval["decision"] == "accepted_one_shot_first_submit", "not accepted")
    require(approval["attempt_id"] == ATTEMPT and approval["max_submits"] == 1, "scope drift")
    require(approval["driver_sha256"] == sha(Path(__file__).read_bytes()), "driver drift")
    require(approval["preflight_sha256"] == sha(PREVIEW.read_bytes()), "preflight bytes drift")
    require(not (RUN / f"evidence/{ATTEMPT}-started.json").exists(), "attempt already entered; no replay")
    previous = json.loads(PREVIEW.read_bytes())
    fresh = capture(module)
    for key in ("attempt_id", "source_commit", "budget", "driver_sha256", "parent_v6_sha256", "creative_lineage"):
        require(fresh[key] == previous[key], f"preflight identity drift: {key}")
    for key in ("canonical_identity", "selected_provider", "source_audio_policy", "source_identity"):
        require(fresh["readiness"][key] == previous["readiness"][key], f"readiness drift: {key}")
    runtime = fresh["readiness"]["runtime"]
    for key in ("current", "supervisor_after"):
        require(runtime[key] == previous["readiness"]["runtime"][key], "accepted runtime identity drift")
    source = module.load("first_submit_source", "shot01_source_audio_policy_readiness_driver.py")
    timing = module.load("first_submit_timing", "shot01_timing_request_readiness_driver.py")
    inspector = module.load("first_submit_runtime", "provider_request_readiness_driver.py")
    exact = source._reopen_exact_request(timing)
    routed = exact["routed"]
    resolved = routed["resolved"]
    require(resolved.resolved_generation_hash == previous["readiness"]["canonical_identity"]["resolved_generation_hash"], "resolved drift")
    require(exact["runtime"]["supervisor_after"] == runtime["supervisor_after"], "runtime changed during reopen")
    from ai_video.comfy_client import ComfyClient
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.comfy_t8_video import render_t8_workflow
    import httpx

    transport_state = {"posts": 0, "prompt_id": None, "file_id": None}
    graph = None

    def runtime_inspection():
        supervisor = inspector._supervisor_status()
        require(supervisor == runtime["supervisor_after"], "supervisor drift")
        current = inspector._runtime_identity(routed["profile"], supervisor)
        require(current["result"] == "MATCH" and current["current"] == runtime["current"], "runtime drift")
        pid = supervisor["main_pid"]
        require(Path(f"/proc/{pid}/exe").resolve() == Path(sys.executable).resolve(), "runtime interpreter mismatch")
        require(Path(f"/proc/{pid}/cwd").resolve() == Path("/home/reggie/ComfyUI"), "runtime cwd mismatch")
        listener = subprocess.check_output(["ss", "-ltnp", "sport = :8188"], text=True)
        require(f"pid={pid}," in listener and "127.0.0.1:8188" in listener, "runtime listener mismatch")
        return timing.T8RuntimeInspection(**current["current"])

    def http_guard(request):
        require(request.url.scheme == "http" and request.url.host == "127.0.0.1" and request.url.port == 8188, "egress denied")
        path = request.url.path
        if request.method == "POST":
            require(path == "/prompt" and transport_state["posts"] == 0, "additional submit denied")
            require(json.loads(request.content) == {"prompt": graph}, "submitted graph drift")
            transport_state["posts"] += 1
        else:
            require(request.method == "GET", "HTTP method denied")
            allowed = {"/queue", "/object_info"}
            if transport_state["prompt_id"]:
                allowed.add("/history/" + transport_state["prompt_id"])
            if path == "/view":
                subfolder, filename, kind = transport_state["file_id"].split(":")
                require(dict(request.url.params) == {"filename": filename, "subfolder": subfolder, "type": kind}, "fetch identity drift")
            else:
                require(path in allowed and not request.url.query, "GET endpoint denied")

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=30, event_hooks={"request": [http_guard]}) as http:
        def queue_empty():
            response = http.get("http://127.0.0.1:8188/queue")
            response.raise_for_status()
            q = response.json()
            require(q.get("queue_running") == [] and q.get("queue_pending") == [], "shared queue occupied")

        provider = timing.ComfyUIT8VideoProvider(routed["profile"], artifact_root=ROOT,
                    comfy_root=Path("/home/reggie/ComfyUI"), runtime_inspector=runtime_inspection,
                    transport=ComfyClient("http://127.0.0.1:8188", http_client=http), timeout_seconds=3600)
        graph = render_t8_workflow(template=provider._workflow, binding=provider._binding,
                    request=resolved, profile=routed["profile"],
                    output_prefix=f"MiniMaxH3/ai_video_h3_t8_{resolved.resolved_generation_hash[:16]}")
        require(provider.preview(resolved) == routed["preview"], "live preview drift")
        queue_empty()
        provider.preflight(resolved)
        inventory = module.committed_snapshot()

        def guard(request):
            require(request == resolved, "durable request drift")
            require(module.committed_snapshot() == inventory, "source drift before effect")
            require(creative_lineage(module) == fresh["creative_lineage"], "creative identity drift before effect")
            runtime_inspection()
            queue_empty()

        guard(resolved)
        require(sha(module.canonical(source._tree_snapshot(source.PROJECT_ROOT))) ==
                fresh["readiness"]["effects"]["production_tree_sha256_after"], "Production state drift")
        event("started", {"approval_sha256": approval_sha256, "fresh_preflight": fresh,
                          "submitted_graph_sha256": sha(canonical(graph)), "budget": previous["budget"]})
        service = VideoGenerationService(committer=ProductionStateCommitter(source.PROJECT_ROOT), provider=provider)
        service.start(attempt_id=ATTEMPT, request=resolved)
        submitted_at = time.monotonic()
        submission = service.submit_local_once(attempt_id=ATTEMPT, pre_submit_guard=guard)
        transport_state["prompt_id"] = submission.provider_request_id
        event("submitted", {"provider_request_id": submission.provider_request_id})
        observation = service.refresh_local_once(attempt_id=ATTEMPT)
        event("terminal", {"observation": observation.model_dump(mode="json"), "elapsed_seconds": time.monotonic() - submitted_at})
        require(observation.state.value == "succeeded", "terminal attempt did not succeed; no retry")
        transport_state["file_id"] = observation.provider_file_id
        candidate = service.fetch_local_once(attempt_id=ATTEMPT)
        path = source.PROJECT_ROOT / candidate.relative_path
        event("fetched", {"media_path": str(path), "media_sha256": sha(path.read_bytes()),
                          "byte_size": path.stat().st_size, "fetch_receipt": candidate.receipt.model_dump(mode="json"),
                          "provider_post_count": transport_state["posts"], "media_gate": "NOT_EVALUATED",
                          "next_shot_submit_allowed": False, "activation": False})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-approved-sha256")
    args = parser.parse_args()
    if args.execute_approved_sha256:
        for marker in ("invoked", "started", "stopped"):
            if (RUN / f"evidence/{ATTEMPT}-{marker}.json").exists():
                print(json.dumps({"decision": "REPLAY_DENIED", "marker": marker}), flush=True)
                raise SystemExit(1)
        # Exclusive durable entry before helper loading or any runtime inspection.
        # A crash before started/stopped is still a consumed orchestration invocation.
        event("invoked", {"approval_sha256": args.execute_approved_sha256})
        try:
            module = load_helper()
            execute(module, args.execute_approved_sha256)
        except Exception as exc:
            event("stopped", {"error_type": type(exc).__name__,
                  "reason": getattr(exc, "user_message", "Execution stopped; inspect exact checkpoint, do not retry."),
                  "next_shot_submit_allowed": False, "retry_allowed": False})
            raise SystemExit(1) from None
    else:
        module = load_helper()
        require(not PREVIEW.exists(), "immutable preflight already exists")
        value = capture(module)
        write_new(PREVIEW, value)
        print(json.dumps({"preflight_path": str(PREVIEW.relative_to(ROOT)), "sha256": sha(PREVIEW.read_bytes())}), flush=True)


if __name__ == "__main__":
    main()
