"""Explicit one-action local H3 runtime driver for the prepared S01 preview."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import httpx

from ai_video.production.comfy_t8_native_turbo_profile import T8NativeTurboRuntimeInspection
from ai_video.production.comfy_t8_native_turbo_video import ComfyUIT8NativeTurboVideoProvider
from ai_video.production.project import load_production_project
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    RouterPolicyIdentity,
    VideoGenerationResolver,
    VideoRoutingPolicy,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_compiler import require_compiled_provider_request
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.video import ResolvedVideoGenerationRequest

import prepare_project


RUN = Path(__file__).resolve().parent
ROOT = RUN / "production"
COMFY = Path("/home/reggie/ComfyUI")
ATTEMPT = "jieshi-s01-h3-horizontal-video-001"


def save(name, value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode()+b"\n"
    path = RUN / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"Immutable evidence changed: {name}")
    else:
        with path.open("xb") as handle:
            handle.write(payload)


def budget_guard():
    budget = json.loads((RUN / "budget.json").read_bytes())
    elapsed = (datetime.now(UTC)-datetime.fromisoformat(budget["started_at"])).total_seconds()
    if not budget["local_only"] or elapsed >= budget["task_elapsed_ceiling_seconds"]:
        raise ValueError("Local task scope or elapsed budget expired")
    loaded = load_production_project(ROOT / "project.yaml")
    if any(a.attempt_id == ATTEMPT for a in loaded.manifest.attempts):
        raise ValueError("Attempt already started; use explicit poll/fetch, never resubmit")


def inspect_runtime() -> T8NativeTurboRuntimeInspection:
    def revision(path: Path) -> str:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    t8 = COMFY / "custom_nodes/minimax-h3-audio-T8"
    version = tomllib.loads((t8 / "pyproject.toml").read_text())["project"]["version"]
    sage = subprocess.check_output(
        ["/home/reggie/miniconda3/bin/python", "-c", "import importlib.metadata; print(importlib.metadata.version('sageattention'))"], text=True
    ).strip()
    response = httpx.get("http://127.0.0.1:8188/system_stats", timeout=10, trust_env=False)
    response.raise_for_status()
    argv = response.json()["system"]["argv"]
    return T8NativeTurboRuntimeInspection(
        comfyui_commit=revision(COMFY), t8_commit=revision(t8), t8_version=version,
        videohelpersuite_commit=revision(COMFY / "custom_nodes/ComfyUI-VideoHelperSuite"),
        sageattention_version=sage,
        launch_capabilities=("sage_attention",) if "--use-sage-attention" in argv else (),
    )


def provider(*, polling=False):
    loaded = load_production_project(ROOT / "project.yaml")
    resolver = lambda asset_id, sha256: loaded.asset_paths[asset_id] if next(
        item for item in loaded.registry.assets if item.asset_id == asset_id
    ).sha256 == sha256 else (_ for _ in ()).throw(ValueError("asset identity mismatch"))
    timeout = 3600.0
    if polling:
        budget=json.loads((RUN/"budget.json").read_bytes())
        started=json.loads((RUN/"submit-started.json").read_bytes())
        now=datetime.now(UTC)
        timeout=min(budget["gpu_generation_ceiling_seconds"]-(now-datetime.fromisoformat(started["started_at"])).total_seconds(),
                    budget["task_elapsed_ceiling_seconds"]-(now-datetime.fromisoformat(budget["started_at"])).total_seconds())
        if timeout <= 0:
            raise ValueError("Generation deadline reached; parent must stop owned local work and retain unknown outcome")
    return ComfyUIT8NativeTurboVideoProvider(
        prepare_project.load_t8_native_turbo_execution_profile(prepare_project.PROFILE_PATH, artifact_root=prepare_project.REPO), artifact_root=prepare_project.REPO, comfy_root=COMFY,
        input_root=ROOT, asset_resolver=resolver, runtime_inspector=inspect_runtime,
        endpoint="http://127.0.0.1:8188", poll_interval_seconds=3, timeout_seconds=timeout,
    )


def _material_and_provider():
    material = prepare_project.load_prepared()
    selected = provider()
    context, policy_data, pointer, output, lifecycle = material["routing_inputs"]
    routing = VideoGenerationResolver().resolve_requirement(
        projection=material["verified"], context=context,
        policy=VideoRoutingPolicy(
            identity=RouterPolicyIdentity(
                policy_id="jieshi-s01-h3-horizontal-local-only", policy_version="1",
                policy_sha256=prepare_project.canonical_sha256(policy_data)),
            local_resources_available=True, remote_authorized=False, budget_authorized=False),
        provider_profile=pointer, capabilities=selected.capabilities(),
        selected_capability_id=material["profile"].capability_id,
        output_requirement=output, lifecycle=lifecycle,
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-t8-native-turbo-video-compiler", compiler_version="2"),
    )
    if routing.provider_bound_request is None:
        raise ValueError("Native I2VA routing blocked; no runtime action is allowed.")
    result = selected.compile_request(routing.provider_bound_request, material["verified"].requirement)
    if result.outcome != "compiled":
        (RUN / "compilation-blocker.json").write_text(result.model_dump_json(indent=2)+"\n")
    compiled = require_compiled_provider_request(result)
    resolved = selected.resolve(compiled.request)
    for name,value in (("planning.json",material["planning"]),("plan.json",material["plan"]),("verified.json",material["verified"]),("routing.json",routing),("compilation.json",compiled),("resolved.json",resolved)):
        save(name,value)
    save("production/"+str(pointer.profile_path),material["profile"])
    return selected, resolved


def _queue_is_empty(_request=None) -> None:
    response = httpx.get("http://127.0.0.1:8188/queue", timeout=10, trust_env=False)
    response.raise_for_status()
    queue = response.json()
    if queue["queue_running"] or queue["queue_pending"]:
        raise RuntimeError("ComfyUI queue is occupied; no submission was attempted.")


def main(action: str) -> None:
    if action == "prepare":
        material = prepare_project.ensure_prepared()
        _material_and_provider()
        print(json.dumps({"prepared": True, "request_hash": material["planning"].request_content_hash}))
        return
    selected = provider(polling=action == "poll")
    request = ResolvedVideoGenerationRequest.model_validate_json((RUN / "resolved.json").read_bytes())
    if action == "preflight":
        selected.preflight(request)
        _queue_is_empty()
        save("runtime.json",inspect_runtime())
        save("preview.json",selected.preview(request))
        print(json.dumps({"preflight": "passed", "request_hash": request.resolved_generation_hash}))
        return
    service = VideoGenerationService(committer=ProductionStateCommitter(ROOT), provider=selected)
    if action == "submit":
        if not (RUN / "preview.json").exists():
            raise ValueError("Completed preflight evidence is required")
        budget_guard()
        _queue_is_empty()
        service.start(attempt_id=ATTEMPT, request=request)
        save("submit-started.json",{"started_at":datetime.now(UTC).isoformat(),"request_hash":request.resolved_generation_hash})
        submission = service.submit_local_once(
            attempt_id=ATTEMPT,
            pre_submit_guard=lambda current: _queue_is_empty(current),
        )
        save("submission.json",submission)
        print(submission.model_dump_json())
    elif action == "poll":
        status = service.refresh_local_once(attempt_id=ATTEMPT)
        if status.state.value in {"succeeded","failed"}:
            save("outcome.json",status)
        print(status.model_dump_json())
    else:
        fetched = service.fetch_local_once(attempt_id=ATTEMPT)
        path=ROOT/fetched.relative_path
        save("fetched.json",{"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"size_bytes":path.stat().st_size})
        save("fetch-receipt.json",fetched.receipt)
        print(json.dumps({"relative_path": str(fetched.relative_path), "receipt": fetched.receipt.model_dump(mode="json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "preflight", "submit", "poll", "fetch"))
    main(parser.parse_args().action)
