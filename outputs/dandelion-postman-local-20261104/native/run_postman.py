"""Single postman qualification attempt through the shared Jimeng runtime.

prepare is local only. All other commands require --live. No retries, recovery,
activation or acceptance are implemented here; canonical owners retain state.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
UNIT = HERE.parent / "production"
ROOT = REPO / "runs/dandelion-postman-local-20261104"
ATTEMPT = "dandelion-postman-local-001"
CEILING = 1500 * 1_000_000
QUOTE = "那你用我现在的体系做一个呢"


class BoundaryError(Exception):
    """Messages in this class contain only operator-controlled descriptions."""


def require(condition, message):
    if not condition:
        raise BoundaryError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def plain(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def read_json(path):
    require(not path.is_symlink(), "Symlink evidence is not allowed")
    return json.loads(path.read_bytes())


def seal(path, value):
    # Exclusive, fsynced creation also serves as the operator's no-repeat latch.
    with path.open("x", encoding="utf-8") as handle:
        json.dump(plain(value), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def bound_times(bound):
    require(bound.get("authorization_quote") == QUOTE, "Authorization quote differs")
    require(bound.get("authority") == "current-task-parent-bounded-operator"
            and bound.get("scope") == "postman only, qualification, no activation",
            "Operator scope differs")
    for key, expected in (("max_submit_count", 1), ("automatic_retries", 0),
                          ("per_call_credit_upper_bound", 1500), ("quote_credits", 396)):
        require(type(bound.get(key)) is int and bound[key] == expected, "Operator limits differ")
    issued = datetime.fromisoformat(bound["issued_at"])
    expires = datetime.fromisoformat(bound["expires_at"])
    require(issued.tzinfo is not None and expires.tzinfo is not None,
            "Operator timestamps must have timezones")
    require(issued <= datetime.now(timezone.utc) < expires, "Operator bound expired or not yet valid")
    return issued, expires


def paid_preview(runtime, request):
    from ai_video.production.jimeng_contracts import JIMENG_ORIGIN
    from ai_video.production.paid_provider import PaidProviderCallPreview, SecretReference
    return PaidProviderCallPreview.create(
        attempt_id=ATTEMPT, operation="video_generation", provider_kind="jimeng",
        model_id="seedance_2.0_vip", request_fingerprint=request.resolved_generation_hash,
        billing_mode="remote_metered", currency="CRD",
        estimated_cost_upper_bound_microunits=CEILING, destination=JIMENG_ORIGIN,
        method="POST", egress_items=runtime.provider.egress_items(request),
        retention_mode="provider_standard", provider_policy_snapshot_id="postman-jimeng-20261104",
        secret_reference=SecretReference(kind="secret_store", reference_id="JIMENG_BROWSER_SESSION"))


def snapshot(runtime, prepared, config_sha):
    require(prepared.execution_binding is not None and prepared.resolved_request is not None,
            "Canonical preparation is not executable; inspect canonical decision evidence")
    return plain({"attempt_id": ATTEMPT, "configuration_sha256": config_sha,
        "execution_binding": prepared.execution_binding,
        "compiled_request": prepared.compilation.request,
        "resolved_request": prepared.resolved_request,
        "provider_preview": runtime.preview(prepared),
        "paid_provider_preview": paid_preview(runtime, prepared.resolved_request)})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "start", "submit", "poll", "fetch"))
    parser.add_argument("--live", action="store_true", help="explicitly enable existing browser transport")
    parser.add_argument("--configuration", type=Path, default=UNIT / "driver-configuration.json")
    args = parser.parse_args(argv)
    require(args.action == "prepare" or args.live, "This action requires explicit --live")
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    from scripts.jimeng_feedback_driver import create_runtime, load_configuration
    from ai_video.production.jimeng_contracts import JimengProfile
    from ai_video.production.project import load_production_project

    configuration = load_configuration(args.configuration)
    profile = configuration.jimeng_profile
    require(profile == JimengProfile.model_validate(read_json(HERE / "profile.json")),
            "Driver profile differs from the sealed native target")
    require((profile.model_id, profile.input_mode, profile.duration_seconds, profile.resolution,
             profile.aspect_ratio, profile.credit_upper_bound)
            == ("seedance_2.0_vip", "multimodal", 12, "1080p", "16:9", 1500),
            "Only the bounded postman model/output is supported")
    require(configuration.row["shot"]["shot_id"] == "postman"
            and configuration.routing_policy.execution_purpose == "qualification",
            "Only postman qualification is allowed")
    config_sha = digest(args.configuration.read_bytes())
    loaded = load_production_project(ROOT / "project.yaml")
    attempts = [a for a in loaded.manifest.attempts if a.operation == "video_generation"]
    require(len(attempts) <= 1 and all(a.attempt_id == ATTEMPT for a in attempts),
            "Unexpected video attempt exists")
    require(all(a.status.value not in {"outcome_unknown", "interrupted"} and
                (a.paid_provider_state is None or a.paid_provider_state.phase.value != "outcome_unknown")
                for a in attempts), "Unknown/interrupted outcome requires canonical recovery")
    transport = None
    if args.live and args.action != "prepare":
        from ai_video.production.jimeng_browser import JimengBrowserTransport
        profile_dir = Path("/home/reggie/.local/share/ai-video/playwright-mcp/profile")
        module = Path("/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright")
        require(profile_dir.is_dir() and module.is_dir(), "Existing browser runtime is unavailable")
        transport = JimengBrowserTransport(profile_dir=profile_dir, playwright_module=module)
    authorized = {}
    runtime = create_runtime(project_root=ROOT, configuration=configuration, transport=transport,
        paid_provider_authorizer=lambda preview: authorized.get(preview.preview_fingerprint))
    prepared_path = UNIT / "prepare.json"

    if args.action in {"prepare", "start"}:
        require(not attempts, "Preparation/start requires no existing video attempt")
        current = snapshot(runtime, runtime.prepare(), config_sha) if args.action == "prepare" else None
        if args.action == "prepare":
            if prepared_path.exists():
                require(read_json(prepared_path) == current, "Existing preparation differs; no overwrite")
            else:
                seal(prepared_path, current)
            return {"ok": True, "action": "prepare", "executable": True,
                    "prepare_sha256": digest(prepared_path.read_bytes()), "network_calls": 0}
        prepared = runtime.prepare()
        require(snapshot(runtime, prepared, config_sha) == read_json(prepared_path),
                "Fresh preparation differs from sealed request/prompt/assets")
        result = runtime.start(prepared=prepared, attempt_id=ATTEMPT)
        return {"ok": True, "action": "start", "manifest_revision": result.manifest_revision}

    require(len(attempts) == 1, "Exactly one started attempt is required")
    frozen = read_json(prepared_path)
    require(frozen["configuration_sha256"] == config_sha, "Configuration changed after prepare")
    attempt, state = runtime.service._state(ATTEMPT)
    request = runtime.committer._reopen_video_request(state.request)
    require(plain(request) == frozen["resolved_request"], "Started request differs from preparation")
    for binding in (*request.image_bindings, *request.media_bindings):
        runtime.reference_resolver(binding)
    require(plain(runtime.committer._reopen_generation_execution_binding(state.execution_binding))
            == frozen["execution_binding"], "Started execution binding differs")

    if args.action == "submit":
        require(state.phase.value == "request" and attempt.paid_provider_state is None,
                "Submit is no longer the next action; never retry")
        preview = paid_preview(runtime, request)
        require(plain(preview) == frozen["paid_provider_preview"] and
                plain({"provider_preview": runtime.provider.preview(request),
                       "egress_items": runtime.provider.egress_items(request)}) == frozen["provider_preview"],
                "Fresh provider preview/egress differs")
        boundraw = (UNIT / "operator-bound.json").read_bytes()
        issued, expires = bound_times(json.loads(boundraw))
        prepare_bound = read_json(UNIT / "prepare-bound.json")
        require(prepare_bound == {"attempt_id": ATTEMPT,
                    "prepare_sha256": digest(prepared_path.read_bytes()),
                    "operator_bound_sha256": digest(boundraw)}, "Parent prepare binding differs")
        from ai_video.production.models import ActorIdentity
        from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
        receipt = "postman-bound-" + digest(boundraw)[:16]
        auth = PaidProviderAuthorizationDecision.create(
            attempt_id=ATTEMPT, preview_fingerprint=preview.preview_fingerprint, explicit_opt_in=True,
            actor=ActorIdentity(actor_id="user", actor_kind="human"), opt_in_policy_receipt_id=receipt,
            budget_policy_id="postman-1500-internal-CRD", budget_currency="CRD",
            project_budget_ceiling_microunits=CEILING, per_call_ceiling_microunits=CEILING,
            egress_authorized=True, egress_policy_receipt_id=receipt, live_test_authorized=True,
            live_authorization_receipt_id=receipt, issued_at=issued, expires_at=expires, max_submit_count=1)
        authorized[preview.preview_fingerprint] = auth
        seal(UNIT / "submit-intent.json", {"attempt_id": ATTEMPT,
            "request_hash": request.resolved_generation_hash,
            "preview_fingerprint": preview.preview_fingerprint,
            "authorization_fingerprint": auth.authorization_fingerprint,
            "created_at": datetime.now(timezone.utc).isoformat()})
        runtime.submit_once(attempt_id=ATTEMPT, paid_preview=preview,
                            reservation_id="dandelion-postman-local-reservation-001")
        _, durable = runtime.service._state(ATTEMPT)
        result = {"ok": True, "action": "submit", "durable_phase": durable.phase.value}
        seal(UNIT / "submit-result.json", result)
        return result
    if args.action == "poll":
        result = runtime.refresh_once(attempt_id=ATTEMPT)
        status = {"ok": True, "action": "poll", "state": result.state.value,
                  "progress_milli": result.progress_milli}
        seal(UNIT / ("poll-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"), status)
        return status
    result = runtime.fetch_once(attempt_id=ATTEMPT)
    status = {"ok": True, "action": "fetch", "artifact_path": str(result.relative_path),
              "sha256": result.receipt.artifact_sha256, "bytes": result.receipt.size_bytes,
              "quality": "NOT_EVALUATED", "activation": "not_performed"}
    seal(UNIT / "fetch-result.json", status)
    return status


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False))
    except Exception as exc:
        # Never echo provider response, arbitrary exception text or traceback.
        code = getattr(getattr(exc, "code", None), "value", None)
        message = str(exc) if isinstance(exc, BoundaryError) else "Operation stopped; inspect canonical evidence; do not retry submission"
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "code": code,
                          "message": message}, ensure_ascii=False))
        sys.exit(1)
