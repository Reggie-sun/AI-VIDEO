"""Thin operator wiring over existing generation, committer and Jimeng owners.

Usage: python execute.py <SHOT> <prepare|start|submit|poll|fetch>. One attempt per Shot root,
no retry; unknown outcomes stop for explicit recovery.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

from ai_video.canvas_planning import canvas_feedback_context
from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator, RegisteredGenerationTarget, create_generation_candidates,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.jimeng import JimengVideoProvider
from ai_video.production.jimeng_browser import JimengBrowserTransport
from ai_video.production.jimeng_contracts import JimengProfile, JIMENG_ORIGIN
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import (
    PaidProviderCallPreview, PaidProviderAuthorizationDecision, SecretReference,
)
from ai_video.production.project import load_production_project
from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance
from ai_video.production.shot_router import AdapterCompilerContract, VideoRoutingPolicy, RouterPolicyIdentity
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService

HERE = Path(__file__).resolve().parent
SHOT, ACTION = sys.argv[1], sys.argv[2]
V = HERE / SHOT
ROOT = Path.cwd() / "runs/shizhen-opening-dispatch-20261030" / SHOT
ATTEMPT = f"shizhen-dispatch-{SHOT}-preview-001"
CEILING = 1500 * 1_000_000
sys.path.insert(0, str(Path.cwd() / "runs/shizhen-episode01-jimeng25-20261025-001"))
from execute_repair import _jsonable  # noqa: E402


def dump(name, value):
    with (V / name).open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def stack():
    loaded = load_production_project(ROOT / "project.yaml")
    local = [a for a in loaded.manifest.attempts if a.operation == "video_generation"]
    assert len(local) <= 1 and all(a.attempt_id == ATTEMPT for a in local)
    assert all(a.status.value not in {"outcome_unknown", "interrupted"} and (
        a.paid_provider_state is None or a.paid_provider_state.phase.value != "outcome_unknown") for a in local)
    raw = (V / "operator-bound.json").read_bytes()
    bound = json.loads(raw)
    assert bound["max_submit_count"] == 1 and bound["automatic_retries"] == 0
    profile = JimengProfile.model_validate_json((V / "profile.json").read_bytes())
    row = json.loads((V / "row.json").read_text())
    mode = {"D6": "first_last_frame", "D2r1": "first_frame", "D4r1": "first_frame"}.get(SHOT, "multimodal")
    assert (profile.model_id, profile.input_mode, profile.duration_seconds, profile.resolution) == (
        "seedance_2.0_vip", mode, row["generation"]["output_need"]["duration_seconds"], "1080p")
    authorized = {}
    committer = ProductionStateCommitter(ROOT, paid_provider_authorizer=lambda p: authorized.get(p.preview_fingerprint))

    def reference(binding):
        asset = next(x for x in loaded.registry.assets if x.asset_id == binding.asset_id)
        data = loaded.asset_paths[asset.asset_id].read_bytes()
        assert hashlib.sha256(data).hexdigest() == binding.asset_sha256 and len(data) == binding.size_bytes
        return data

    provider = JimengVideoProvider(profile=profile, transport=JimengBrowserTransport(
        profile_dir=Path("/home/reggie/.local/share/ai-video/playwright-mcp/profile"),
        playwright_module=Path("/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright")),
        reference_resolver=reference, committer=committer)
    target = RegisteredGenerationTarget(provider=provider, profile=profile.pointer(),
        compiler_contract=AdapterCompilerContract.create(compiler_id=profile.compiler_id, compiler_version="1"),
        output_requirement=profile.output())
    routing = VideoRoutingPolicy(identity=RouterPolicyIdentity(
        policy_id="shizhen-cold-open-qualification", policy_version="1",
        policy_sha256=canonical_sha256({"operator_bound_sha256": hashlib.sha256(raw).hexdigest(), "shot_id": SHOT})),
        local_resources_available=False, remote_authorized=True, budget_authorized=True,
        execution_purpose="qualification")

    def context(current):
        return canvas_feedback_context(loaded=current, row=row, policy=routing)

    task = f"shizhen-dispatch-{SHOT}-preview"
    candidates, _ = create_generation_candidates(
        projection=context(loaded)["projection"], targets=(target,),
        acceptance=selected_shot_generation_acceptance(loaded, SHOT), final_output_goal=loaded.qa_policy.final_output,
        source_project=loaded, generation_id=context(loaded)["lifecycle"].generation_id, task_id=task)
    limits = ExecutionLimits(task_id=task, generation_forbidden=False,
        allowed_remote_candidates=tuple(x.candidate_id for x in candidates), paid_submit_ceiling=1,
        paid_submits_used=sum(a.paid_provider_state is not None for a in local), local_batch_limit=1,
        local_batch_used=0, local_total_used=0, local_resource_available=False)
    orchestrator = GenerationFeedbackOrchestrator.for_project(committer=committer, targets=(target,),
        context_loader=context, policy=DecisionPolicy(max_resamples=0, allow_bounded_exploration=True))
    return dict(loaded=loaded, local=local, profile=profile, provider=provider, committer=committer, bound=bound,
                boundraw=raw, authorized=authorized, orchestrator=orchestrator, limits=limits)


def paid(s, request):
    preview = s["provider"].preview(request)
    assert preview.estimated_cost_upper_bound_microunits == CEILING
    return PaidProviderCallPreview.create(
        attempt_id=ATTEMPT, operation="video_generation", provider_kind="jimeng", model_id="seedance_2.0_vip",
        request_fingerprint=request.resolved_generation_hash, billing_mode="remote_metered", currency="CRD",
        estimated_cost_upper_bound_microunits=CEILING, destination=JIMENG_ORIGIN, method="POST",
        egress_items=s["provider"].egress_items(request), retention_mode="provider_standard",
        provider_policy_snapshot_id=f"shizhen-dispatch-{SHOT}",
        secret_reference=SecretReference(kind="secret_store", reference_id="JIMENG_BROWSER_SESSION"))


def lint(prepared, request, prompt):
    data = json.loads((V / "data.json").read_text())
    body = re.sub(r"\{\{image:\d+\}\}", "", prompt)
    output = prepared.compilation.request.output_requirement
    checks = {
        "exact_inputs": [x.asset_id for x in request.image_bindings] == (
            [x["asset_id"] for x in data["images"]]),
        "exact_authored_prompt": prompt.strip() == (V / "native-prompt.zh.txt").read_text().strip(),
        "pure_chinese_body": not re.search(r"[A-Za-z]", body),
        "no_captions_or_music": "字幕" in prompt and "配乐" in prompt,
        "no_scene_dialogue": "无对白" in prompt or "无其他对白" in prompt,
        "duration": output.duration_seconds == json.loads((V / "row.json").read_text())["generation"]["output_need"]["duration_seconds"],
        "1080p": output.resolution_label == "1080p",
        "native_audio": output.native_audio,
    }
    if SHOT in {"D2r1", "D4r1"}:
        checks["first_frame_role"] = [x.role for x in request.image_bindings] == ["first_frame"]
        checks["no_markers"] = "{{image:" not in prompt
    elif SHOT == "D6":
        checks["first_last_roles"] = [x.role for x in request.image_bindings] == ["first_frame", "last_frame"]
    else:
        checks["one_bound_marker"] = "{{image:0}}" in prompt and "{{image:1}}" not in prompt
    return checks


def main():
    s = stack()
    service = VideoGenerationService(committer=s["committer"], provider=s["provider"])
    if ACTION == "prepare":
        assert not s["local"]
        prepared = s["orchestrator"].prepare(limits=s["limits"])
        if prepared.execution_binding is None or prepared.resolved_request is None:
            (V / "prepare-blocker.json").write_text(json.dumps({"decision": _jsonable(prepared.decision),
                "compilation": _jsonable(prepared.compilation)}, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({"executable": False, "disposition": prepared.decision.disposition,
                              "unsupported": getattr(prepared.compilation, "unsupported_field_paths", None),
                              "rationale": getattr(prepared.decision, "rationale", None)}, ensure_ascii=False))
            return
        request = prepared.resolved_request
        prompt = prepared.compilation.request.prompt_text
        for binding in (*request.image_bindings, *request.media_bindings):
            s["provider"]._reference_resolver(binding)
        checks = lint(prepared, request, prompt)
        (V / "prompt-lint.json").write_text(json.dumps(checks, indent=2) + "\n")
        if not all(checks.values()):
            raise RuntimeError("Native prompt lint failed: " + json.dumps(checks))
        preview = paid(s, request)
        (V / "prepare.json").write_text(json.dumps({
            "execution_binding": _jsonable(prepared.execution_binding),
            "compiled_request": _jsonable(prepared.compilation.request), "resolved_request": _jsonable(request),
            "paid_provider_preview": _jsonable(preview), "new_video_calls": 0}, ensure_ascii=False, indent=2) + "\n")
        (V / "compiled-native-prompt.zh.txt").write_text(prompt + "\n")
        print(json.dumps({"executable": True, "lint": checks, "prompt_chars": len(prompt)}))
    elif ACTION == "start":
        assert not s["local"]
        prepared = s["orchestrator"].prepare(limits=s["limits"])
        assert prepared.execution_binding.binding_hash == json.loads((V / "prepare.json").read_text())["execution_binding"]["binding_hash"]
        manifest = service.start(attempt_id=ATTEMPT, request=prepared.resolved_request,
                                 execution_binding=prepared.execution_binding)
        print(json.dumps({"started": True, "manifest_revision": manifest.manifest_revision}))
    elif ACTION == "submit":
        assert len(s["local"]) == 1 and s["local"][0].paid_provider_state is None
        _, state = service._state(ATTEMPT)
        assert state.phase.value == "request"
        request = s["committer"]._reopen_video_request(state.request)
        preview = paid(s, request)
        bound = s["bound"]
        issued, expires = datetime.fromisoformat(bound["issued_at"]), datetime.fromisoformat(bound["expires_at"])
        assert issued <= datetime.now(timezone.utc) < expires
        receipt = "dispatch-bound-" + hashlib.sha256(s["boundraw"]).hexdigest()[:16]
        auth = PaidProviderAuthorizationDecision.create(
            attempt_id=ATTEMPT, preview_fingerprint=preview.preview_fingerprint, explicit_opt_in=True,
            actor=ActorIdentity(actor_id="user", actor_kind="human"), opt_in_policy_receipt_id=receipt,
            budget_policy_id="shizhen-dispatch-1500-internal-CRD", budget_currency="CRD",
            project_budget_ceiling_microunits=CEILING, per_call_ceiling_microunits=CEILING, egress_authorized=True,
            egress_policy_receipt_id=receipt, live_test_authorized=True, live_authorization_receipt_id=receipt,
            issued_at=issued, expires_at=expires, max_submit_count=1)
        s["authorized"][preview.preview_fingerprint] = auth
        dump("submit-intent.json", {"attempt_id": ATTEMPT, "request_hash": request.resolved_generation_hash,
                                    "preview_fingerprint": preview.preview_fingerprint,
                                    "created_at": datetime.now(timezone.utc).isoformat()})
        result = service.submit_once(attempt_id=ATTEMPT, paid_preview=preview,
                                     reservation_id=f"shizhen-dispatch-{SHOT}-reservation-001")
        dump("submit-result.json", _jsonable(result))
        print(json.dumps({"accepted": True, "shot": SHOT}))
    elif ACTION == "poll":
        result = service.refresh_once(attempt_id=ATTEMPT)
        print(json.dumps({"shot": SHOT, "state": result.state.value, "progress_milli": result.progress_milli}))
    elif ACTION == "fetch":
        result = service.fetch_once(attempt_id=ATTEMPT)
        value = {"artifact_path": str(result.relative_path), "sha256": result.receipt.artifact_sha256,
                 "bytes": result.receipt.size_bytes}
        dump("fetch-result.json", value)
        print(json.dumps(value))
    else:
        raise ValueError("prepare/start/submit/poll/fetch")


if __name__ == "__main__":
    main()
