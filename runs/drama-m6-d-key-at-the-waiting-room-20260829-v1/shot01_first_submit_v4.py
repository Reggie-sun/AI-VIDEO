"""One sealed local Shot 01 submit/fetch attempt; no retry or activation."""

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
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
PROJECT = RUN / "production-project"
ATTEMPT = "drama-shot01-first-20260906-v4"
APPROVAL = ROOT / "docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v4.accepted.json"
V9 = ROOT / "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v9.accepted.json"
V9_SHA256 = "c0a505c48d77011143c1d231c56412c869278d9c0988a9e3a702f337278f1dee"
SOURCE_BINDING_ACCEPTANCE_SHA256 = "70dc023257863683157a12b0849f2fd3c6d8fe2d9c9dacf70c95d8ce38797276"
PREFLIGHT_PATH = RUN / "shot01_source_binding_preflight_v1.py"
PREFLIGHT_SHA256 = "8ba4d9ecec4621420709f01bc9441c93f122cb24fbe73db0e438c345c47e73d7"
HISTORICAL_DRIVER_PATH = RUN / "shot01_first_submit_v1.py"
HISTORICAL_DRIVER_SHA256 = "e708c4ac4dcfa840a448edd794fda9155dcbada982e18ab1800abd8442a200df"
SELF_PATH = Path(__file__).relative_to(ROOT).as_posix()
BUDGET = {"max_submits": 1, "max_gpu_jobs": 1, "poll_timeout_seconds": 3600, "retry_count": 0, "remote_egress": False}


class RunCheckError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise RunCheckError(reason)


def _safe_relative(path: str) -> Path:
    value = Path(path)
    _require(not value.is_absolute() and ".." not in value.parts, "unsafe relative path")
    resolved = (ROOT / value).resolve()
    _require(resolved.is_relative_to(ROOT.resolve()), "relative path escapes repository")
    current = ROOT
    for part in value.parts:
        current = current / part
        _require(not current.is_symlink(), "relative path uses symlink")
    return value


def _write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def _event(name: str, value: dict[str, object]) -> Path:
    path = RUN / "evidence" / f"{ATTEMPT}-{name}.json"
    _write_new(path, {"attempt_id": ATTEMPT, "event": name, "at": datetime.now(timezone.utc).isoformat(), **value})
    print(json.dumps({"event": name, "evidence": path.relative_to(ROOT).as_posix()}), flush=True)
    return path


def _git_blob(source_commit: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{source_commit}:{path}"], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def _self_identity(source_commit: str) -> str:
    _require(len(source_commit) == 40 and all(char in "0123456789abcdef" for char in source_commit), "source commit must be full lowercase SHA-1")
    current = (ROOT / _safe_relative(SELF_PATH)).read_bytes()
    _require(current == _git_blob(source_commit, SELF_PATH), "first-submit driver differs from source commit")
    return _sha256(current)


def _load_preflight(source_commit: str) -> ModuleType:
    _require(_sha256(PREFLIGHT_PATH.read_bytes()) == PREFLIGHT_SHA256, "sealed preflight driver drift")
    _require(PREFLIGHT_PATH.read_bytes() == _git_blob(source_commit, PREFLIGHT_PATH.relative_to(ROOT).as_posix()), "preflight driver differs from source commit")
    spec = importlib.util.spec_from_file_location("shot01_v4_preflight", PREFLIGHT_PATH)
    _require(spec is not None and spec.loader is not None, "preflight driver unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _preflight_path(value: str) -> Path:
    relative = Path(value)
    _require(relative.suffix == ".json" and not relative.is_absolute() and ".." not in relative.parts, "preflight must be relative evidence JSON path")
    path = (RUN / "evidence" / relative).resolve()
    _require(path.is_relative_to((RUN / "evidence").resolve()) and path.is_file(), "preflight path unavailable")
    return path


def _v9() -> dict[str, object]:
    data = V9.read_bytes()
    _require(_sha256(data) == V9_SHA256, "V9 prerequisite bytes drift")
    value = json.loads(data)
    _require(value.get("decision") == "accepted_pre_submit_prerequisite_only", "V9 is not accepted pre-submit prerequisite")
    return value


def _binding_stable(value: dict[str, object]) -> dict[str, object]:
    binding = value["source_binding"]
    return {"canonical_source_binding": binding["canonical_source_binding"], "identity": binding["identity"]}


def _preflight_comparable(value: dict[str, object]) -> dict[str, object]:
    identity = dict(value["exact_request_identity"])
    identity["source_binding"] = _binding_stable(identity)
    return {
        "canonical_lineage": value["canonical_lineage"],
        "exact_request_identity": identity,
        "selected_provider": value["selected_provider"],
        "source_audio_policy": value["source_audio_policy"],
        "runtime_current": value["runtime"]["current"],
        "production_tree": value["effects"]["production_tree_sha256_after"],
    }


def _validate_preflight(v9: dict[str, object], preflight_path: Path) -> tuple[dict[str, object], str]:
    data = preflight_path.read_bytes()
    digest = _sha256(data)
    value = json.loads(data)
    _require(value.get("schema_version") == "drama-shot01-source-binding-preflight/1" and value.get("status") == "PASS_READ_ONLY_PROVIDER_PREFLIGHT", "selected preflight is not accepted read-only proof")
    captured = v9["captured_read_only_evidence"]
    expected = {
        "canonical_lineage": captured["canonical_lineage"],
        "exact_request_identity": captured["exact_request_identity"],
        "selected_provider": captured["selected_provider"],
        "source_audio_policy": captured["source_audio_policy"],
        "runtime_current": captured["runtime"]["current"],
        "production_tree": captured["effects"]["production_tree_sha256_after"],
    }
    expected["exact_request_identity"] = dict(expected["exact_request_identity"])
    expected["exact_request_identity"]["source_binding"] = _binding_stable(expected["exact_request_identity"])
    _require(_preflight_comparable(value) == expected, "selected preflight differs from V9 beyond source reseal metadata")
    return value, digest


def _historical_creative_lineage(source_commit: str) -> dict[str, object]:
    relative = HISTORICAL_DRIVER_PATH.relative_to(ROOT).as_posix()
    _require(_sha256(HISTORICAL_DRIVER_PATH.read_bytes()) == HISTORICAL_DRIVER_SHA256, "historical creative lineage driver drift")
    _require(HISTORICAL_DRIVER_PATH.read_bytes() == _git_blob(source_commit, relative), "historical creative lineage driver differs from source commit")
    spec = importlib.util.spec_from_file_location("shot01_v4_historical_creative", HISTORICAL_DRIVER_PATH)
    _require(spec is not None and spec.loader is not None, "historical creative lineage driver unavailable")
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)

    class HistoricalCreativeAdapter:
        @staticmethod
        def sealed(path: Path, expected: str) -> dict[str, object]:
            data = path.read_bytes()
            _require(_sha256(data) == expected, "historical creative sealed bytes drift")
            return json.loads(data)

        @staticmethod
        def git(*args: str) -> bytes:
            return subprocess.check_output(["git", *args], cwd=ROOT)

    return driver.creative_lineage(HistoricalCreativeAdapter())


def _verify_creative(approval: dict[str, object], source_commit: str) -> None:
    current = _historical_creative_lineage(source_commit)
    _require(approval.get("creative_lineage") == current, "approval creative lineage drift")
    _require(approval.get("creative_lineage_sha256") == _sha256(_canonical(current)), "approval creative lineage hash drift")


def _approval(approval_sha256: str, *, source_commit: str, preflight_path: Path, preflight_sha256: str, driver_sha256: str, runtime: dict[str, object]) -> dict[str, object]:
    data = APPROVAL.read_bytes()
    _require(_sha256(data) == approval_sha256, "approval SHA-256 drift")
    value = json.loads(data)
    expected = {
        "decision": "accepted_one_shot_first_submit",
        "attempt_id": ATTEMPT,
        "source_commit": source_commit,
        "driver_sha256": driver_sha256,
        "preflight_path": preflight_path.relative_to(ROOT).as_posix(),
        "preflight_sha256": preflight_sha256,
        "v9_sha256": V9_SHA256,
        "budget": BUDGET,
    }
    _require(all(value.get(key) == expected_value for key, expected_value in expected.items()), "approval identity/budget drift")
    _verify_creative(value, source_commit)
    _require(value.get("runtime_current") == runtime["current"] and value.get("runtime_supervisor") == runtime["supervisor_after"], "approval runtime identity/supervisor drift")
    return value


def _fresh(preflight: ModuleType, source_commit: str, selected: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    _require(selected["source_commit"] == source_commit, "selected preflight source commit drift")
    observations: dict[str, object] = {"check_stage": "fresh_preflight"}
    fresh = preflight.collect(source_commit, observations)
    _require(_preflight_comparable(fresh) == _preflight_comparable(selected), "fresh preflight drift")
    _require(fresh["exact_request_identity"] == selected["exact_request_identity"] and fresh["source_binding"] == selected["source_binding"], "fresh source-binding metadata drift")
    _require(fresh["source_inventory_sha256"] == selected["source_inventory_sha256"] and fresh["source_inventory_file_count"] == selected["source_inventory_file_count"], "fresh source inventory drift")
    _require(fresh["runtime"]["supervisor_after"] == selected["runtime"]["supervisor_after"], "fresh runtime supervisor drift")
    return fresh, observations


def _queue(http: object) -> None:
    response = http.get("http://127.0.0.1:8188/queue")
    response.raise_for_status()
    value = response.json()
    _require(value.get("queue_running") == [] and value.get("queue_pending") == [], "ComfyUI queue is occupied")


def _execute(source_commit: str, preflight: ModuleType, selected: dict[str, object], selected_sha256: str, preflight_path: Path, approval_sha256: str, approval: dict[str, object], driver_sha256: str, state: dict[str, object]) -> None:
    state["check_stage"] = "fresh_preflight"
    fresh, observations = _fresh(preflight, source_commit, selected)
    _approval(approval_sha256, source_commit=source_commit, preflight_path=preflight_path, preflight_sha256=selected_sha256, driver_sha256=driver_sha256, runtime=fresh["runtime"])
    state["check_stage"] = "formal_reopen"
    loader = preflight._load(preflight._inventory(source_commit), "shot01_v4_binding", preflight.LOADER_PATH)
    exact = loader.reopen_exact_request(expected_acceptance_sha256=SOURCE_BINDING_ACCEPTANCE_SHA256, source_commit=source_commit)
    lineage = preflight._assert_request(exact)
    _require(lineage == fresh["canonical_lineage"] and preflight._exact_identity(exact) == fresh["exact_request_identity"], "formal request differs from fresh preflight")
    _require(preflight._selected_provider(exact) == fresh["selected_provider"] and exact["source_audio_policy"] == fresh["source_audio_policy"], "provider/audio differs from fresh preflight")
    from ai_video.comfy_client import ComfyClient
    from ai_video.production.comfy_t8_video import render_t8_workflow
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    import httpx

    transport = {"posts": 0, "prompt_id": None, "file_id": None}
    graph: object | None = None

    def runtime_inspector():
        runtime, inspection, _, supervisor = preflight._check_runtime(preflight._load(preflight._inventory(source_commit), "shot01_v4_runtime", preflight.READINESS_PATH), exact["routed"]["profile"])
        _require(runtime["current"] == fresh["runtime"]["current"] and supervisor == fresh["runtime"]["supervisor_after"], "runtime drift before Provider action")
        return inspection

    def guard(request: object) -> None:
        state["check_stage"] = "pre_submit_guard"
        _require(request == exact["routed"]["resolved"], "durable request drift")
        current = loader.reopen_exact_request(expected_acceptance_sha256=SOURCE_BINDING_ACCEPTANCE_SHA256, source_commit=source_commit)
        _require(preflight._assert_request(current) == fresh["canonical_lineage"], "authoritative lineage drift before submit")
        _require(current["routed"]["resolved"] == exact["routed"]["resolved"] == request, "durable request does not equal current resolved request")
        _require(preflight._exact_identity(current) == fresh["exact_request_identity"] and preflight._selected_provider(current) == fresh["selected_provider"] and current["source_audio_policy"] == fresh["source_audio_policy"], "authoritative source binding drift before submit")
        _require(_sha256(preflight._canonical(preflight._inventory(source_commit))) == fresh["source_inventory_sha256"], "source inventory drift before submit")
        _require(_self_identity(source_commit) == driver_sha256, "driver drift before submit")
        current_v9 = _v9()
        current_selected, current_selected_sha256 = _validate_preflight(current_v9, preflight_path)
        _require(current_selected_sha256 == selected_sha256 and current_selected == selected, "selected preflight bytes drift before submit")
        _approval(approval_sha256, source_commit=source_commit, preflight_path=preflight_path, preflight_sha256=current_selected_sha256, driver_sha256=driver_sha256, runtime=fresh["runtime"])
        runtime_inspector()
        _queue(http)
        state["guard_passed"] = True

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=30, event_hooks={"request": []}) as http:
        def http_guard(request: object) -> None:
            _require(request.url.scheme == "http" and request.url.host == "127.0.0.1" and request.url.port == 8188, "egress denied")
            if request.method == "POST":
                _require(request.url.path == "/prompt" and not request.url.query and transport["posts"] == 0 and json.loads(request.content) == {"prompt": graph}, "second or drifted prompt submit denied")
                state["guard_passed"] = False
                guard(exact["routed"]["resolved"])
                _require(state.get("guard_passed") is True, "prompt submit guard did not pass")
                transport["posts"] += 1
                state["provider_post_count"] = transport["posts"]
                return
            _require(request.method == "GET", "HTTP method denied")
            if request.url.path == "/view":
                subfolder, filename, kind = str(transport["file_id"]).split(":")
                _require(dict(request.url.params) == {"filename": filename, "subfolder": subfolder, "type": kind}, "fetch file identity drift")
                return
            allowed = {"/queue", "/object_info"}
            if transport["prompt_id"]:
                allowed.add("/history/" + str(transport["prompt_id"]))
            _require(request.url.path in allowed and not request.url.query, "GET endpoint denied")

        http.event_hooks["request"].append(http_guard)
        readiness = preflight._load(preflight._inventory(source_commit), "shot01_v4_runtime_provider", preflight.READINESS_PATH)
        provider = readiness.ComfyUIT8VideoProvider(exact["routed"]["profile"], artifact_root=ROOT, comfy_root=readiness.COMFY_ROOT, runtime_inspector=runtime_inspector, transport=ComfyClient("http://127.0.0.1:8188", http_client=http), timeout_seconds=3600)
        state["check_stage"] = "provider_preflight"
        graph = render_t8_workflow(template=provider._workflow, binding=provider._binding, request=exact["routed"]["resolved"], profile=exact["routed"]["profile"], output_prefix=f"MiniMaxH3/ai_video_h3_t8_{exact['routed']['resolved'].resolved_generation_hash[:16]}")
        _require(provider.preview(exact["routed"]["resolved"]) == exact["routed"]["preview"], "Provider preview drift")
        _queue(http)
        provider.preflight(exact["routed"]["resolved"])
        _queue(http)
        before_tree = preflight._tree(PROJECT)
        _require(_sha256(preflight._canonical(before_tree)) == fresh["effects"]["production_tree_sha256_after"], "Production state drift before intent")
        state["check_stage"] = "before_intent"
        guard(exact["routed"]["resolved"])
        v9_source_commit = _v9()["captured_read_only_evidence"]["exact_request_identity"]["source_binding"]["source_commit"]
        _event("started", {"approval_sha256": approval_sha256, "driver_sha256": driver_sha256, "preflight_observations": observations, "source_reseal": {"v9_source_commit": v9_source_commit, "selected_source_commit": selected["source_binding"]["source_commit"], "fresh_source_commit": fresh["source_binding"]["source_commit"], "canonical_source_binding_unchanged": True, "binding_identity_unchanged": True}, "submitted_graph_sha256": _sha256(_canonical(graph)), "budget": BUDGET})
        service = VideoGenerationService(committer=ProductionStateCommitter(PROJECT), provider=provider)
        state["check_stage"] = "durable_intent"
        service.start(attempt_id=ATTEMPT, request=exact["routed"]["resolved"])
        started = time.monotonic()
        submission = service.submit_local_once(attempt_id=ATTEMPT, pre_submit_guard=guard)
        transport["prompt_id"] = submission.provider_request_id
        state["check_stage"] = "submitted"
        _event("submitted", {"provider_request_id": submission.provider_request_id, "provider_post_count": transport["posts"]})
        state["check_stage"] = "terminal_observation"
        terminal = service.refresh_local_once(attempt_id=ATTEMPT)
        _event("terminal", {"observation": terminal.model_dump(mode="json"), "elapsed_seconds": time.monotonic() - started})
        _require(terminal.state.value == "succeeded", "terminal outcome is not succeeded; no retry")
        transport["file_id"] = terminal.provider_file_id
        state["check_stage"] = "fetch"
        candidate = service.fetch_local_once(attempt_id=ATTEMPT)
        media = PROJECT / candidate.relative_path
        state["check_stage"] = "fetched"
        _event("fetched", {"media_path": Path(candidate.relative_path).as_posix(), "media_sha256": _sha256(media.read_bytes()), "byte_size": media.stat().st_size, "fetch_receipt": candidate.receipt.model_dump(mode="json"), "provider_post_count": transport["posts"], "media_gate": "NOT_EVALUATED", "activation": False, "next_shot_submit_allowed": False})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--preflight", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-approved-sha256")
    mode.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    for marker in ("invoked", "started", "stopped", "fetched"):
        _require(not (RUN / "evidence" / f"{ATTEMPT}-{marker}.json").exists(), f"attempt replay denied: {marker}")
    driver_sha256 = _self_identity(args.source_commit)
    preflight_path = _preflight_path(args.preflight)
    v9 = _v9()
    selected, selected_sha256 = _validate_preflight(v9, preflight_path)
    if args.validate_only:
        print(json.dumps({"decision": "VALIDATED_NO_EFFECT", "attempt_id": ATTEMPT, "preflight_sha256": selected_sha256}), flush=True)
        return 0
    approval = _approval(args.execute_approved_sha256, source_commit=args.source_commit, preflight_path=preflight_path, preflight_sha256=selected_sha256, driver_sha256=driver_sha256, runtime=selected["runtime"])
    _event("invoked", {"approval_sha256": args.execute_approved_sha256, "driver_sha256": driver_sha256, "preflight_sha256": selected_sha256, "v9_sha256": V9_SHA256})
    state: dict[str, object] = {"check_stage": "load_preflight", "provider_post_count": 0}
    try:
        preflight = _load_preflight(args.source_commit)
        sys.addaudithook(preflight._no_network)
        _execute(args.source_commit, preflight, selected, selected_sha256, preflight_path, args.execute_approved_sha256, approval, driver_sha256, state)
    except Exception as error:
        code = getattr(error, "code", None)
        message = getattr(error, "user_message", None)
        _event("stopped", {"failure_class": type(error).__name__, "failure_code": getattr(code, "value", None), "reason": str(error) if isinstance(error, RunCheckError) else message if isinstance(message, str) else "EXECUTION_STOPPED_CHECK_EXACT_EVIDENCE", "check_stage": state["check_stage"], "provider_post_count": state["provider_post_count"], "retry_allowed": False, "next_shot_submit_allowed": False})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
