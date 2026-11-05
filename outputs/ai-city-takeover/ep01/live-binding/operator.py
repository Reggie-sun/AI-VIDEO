"""Bounded EP01 source operation; all lifecycle changes use existing owners."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import sys

from ai_video.production.jimeng_browser import JimengBrowserTransport
from ai_video.production.jimeng_contracts import JIMENG_ORIGIN
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision, PaidProviderCallPreview, SecretReference,
)
from ai_video.production.project import load_production_project
from scripts.jimeng_feedback_driver import create_runtime, load_configuration


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / "generation/project"
CONFIG = HERE.parent / "generation/driver-config.json"


def jsonable(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(type(value).__name__)


def seal(root, name, value):
    with (root / name).open("x", encoding="utf-8") as handle:
        json.dump(jsonable(value), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main(action, unit_root=None):
    unit_root = Path(unit_root).resolve(strict=True) if unit_root else HERE
    bound_bytes = (unit_root / "operator-bound.json").read_bytes()
    bound = json.loads(bound_bytes)
    attempt_id = bound["attempt_id"]
    if bound["max_submit_count"] != 1 or bound["automatic_retries"] != 0:
        raise ValueError("This operator permits one submit without automatic retries")
    project = (unit_root / bound.get("project_path", "../generation/project")).resolve(strict=True)
    config_path = (unit_root / bound.get("configuration_path", "../generation/driver-config.json")).resolve(strict=True)
    config = load_configuration(config_path)
    loaded = load_production_project(project / "project.yaml")
    ancestor = bound.get("ancestor")
    if ancestor is not None:
        previous = load_production_project(Path(ancestor["project_root"]) / "project.yaml")
        prior = next(a for a in previous.manifest.attempts if a.attempt_id == ancestor["attempt_id"])
        fetch = prior.video_generation_state.fetch_receipt
        gate = json.loads(Path(ancestor["gate_path"]).read_text())
        if (prior.status.value in {"outcome_unknown", "interrupted"}
                or fetch is None or fetch.artifact_sha256 != ancestor["artifact_sha256"]
                or gate.get("artifact_sha256") != ancestor["artifact_sha256"]
                or gate.get("verdict") != "FAIL"
                or bound.get("cumulative_attempt_ceiling") != 2
                or bound.get("cumulative_operator_credit_ceiling") != 500
                or ancestor.get("observed_cost_credits") != 198
                or bound["operator_ceiling"] > 250):
            raise ValueError("Repair requires the exact known failed source and preserved cumulative bounds")
    prior_sources = bound.get("prior_sources", [])
    if prior_sources:
        if (bound.get("scope_kind") != "next_shot" or len(prior_sources) != 2
                or bound.get("cumulative_attempt_ceiling") != 3
                or bound.get("cumulative_operator_credit_ceiling") != 750
                or bound["operator_ceiling"] > 250 or prior_sources[-1]["gate_verdict"] != "PASS"):
            raise ValueError("Next Shot requires the accepted prior source and a bounded third unit")
        for source in prior_sources:
            previous = load_production_project(Path(source["project_root"]) / "project.yaml")
            prior = next(a for a in previous.manifest.attempts if a.attempt_id == source["attempt_id"])
            fetch = prior.video_generation_state.fetch_receipt
            gate_bytes = Path(source["gate_path"]).read_bytes()
            gate = json.loads(gate_bytes)
            if (prior.status.value in {"outcome_unknown", "interrupted"}
                    or fetch is None or fetch.artifact_sha256 != source["artifact_sha256"]
                    or hashlib.sha256(gate_bytes).hexdigest() != source["gate_sha256"]
                    or gate.get("artifact_sha256") != source["artifact_sha256"]
                    or gate.get("verdict") != source["gate_verdict"]
                    or source.get("observed_cost_credits") != 198):
                raise ValueError("Prior source identity, result or cumulative cost changed")
    attempts = [a for a in loaded.manifest.attempts if a.operation == "video_generation"]
    if len(attempts) > 1 or any(a.attempt_id != attempt_id for a in attempts):
        raise ValueError("Unexpected source attempt; inspect before continuing")
    if any(a.status.value in {"outcome_unknown", "interrupted"} or
           (a.paid_provider_state and a.paid_provider_state.phase.value == "outcome_unknown")
           for a in attempts):
        raise ValueError("Unknown outcome: observe/recover through the canonical owner")
    authorizations = {}
    live = action in {"submit", "poll", "fetch"}
    runtime = create_runtime(project_root=project, configuration=config,
        transport=JimengBrowserTransport(
            profile_dir=Path("/home/reggie/.local/share/ai-video/playwright-mcp/profile"),
            playwright_module=Path("/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright")) if live else None,
        paid_provider_authorizer=lambda p: authorizations.get(p.preview_fingerprint))

    def paid_preview(request):
        preview = runtime.provider.preview(request)
        ceiling = bound["operator_ceiling"] * 1_000_000
        if preview.estimated_cost_upper_bound_microunits != ceiling:
            raise ValueError("Sealed operator ceiling differs from provider preview")
        return PaidProviderCallPreview.create(attempt_id=attempt_id,
            operation="video_generation", provider_kind="jimeng", model_id=config.jimeng_profile.model_id,
            request_fingerprint=request.resolved_generation_hash, billing_mode="remote_metered",
            currency=bound["operator_currency"], estimated_cost_upper_bound_microunits=ceiling,
            destination=JIMENG_ORIGIN, method="POST", egress_items=runtime.provider.egress_items(request),
            retention_mode="provider_standard", provider_policy_snapshot_id=bound.get("policy_id", "iris-ep01-approved-source-001"),
            secret_reference=SecretReference(kind="secret_store", reference_id="JIMENG_BROWSER_SESSION"))

    if action == "prepare":
        if attempts:
            raise ValueError("Attempt already exists; inspect instead of preparing another")
        prepared = runtime.prepare()
        if prepared.resolved_request is None or prepared.execution_binding is None:
            print(json.dumps({"executable": False, "decision": jsonable(prepared.decision)}, ensure_ascii=False))
            return 2
        seal(unit_root, "prepared.json", {"execution_binding": prepared.execution_binding,
            "resolved_request": prepared.resolved_request,
            "compiled_request": prepared.compilation.request,
            "paid_provider_preview": paid_preview(prepared.resolved_request)})
        print(json.dumps({"executable": True, "new_video_calls": 0}))
    elif action == "start":
        if attempts:
            raise ValueError("Attempt already exists")
        frozen = json.loads((unit_root / "prepared.json").read_text())
        prepared = runtime.prepare()
        if prepared.execution_binding is None or prepared.execution_binding.binding_hash != frozen["execution_binding"]["binding_hash"]:
            raise ValueError("Prepared binding changed")
        result = runtime.start(prepared=prepared, attempt_id=attempt_id)
        print(json.dumps({"started": True, "manifest_revision": result.manifest_revision}))
    elif action == "submit":
        if len(attempts) != 1 or attempts[0].paid_provider_state is not None:
            raise ValueError("One fresh started attempt required; never repeat a paid submit")
        issued = datetime.fromisoformat(bound["issued_at"])
        expires = datetime.fromisoformat(bound["expires_at"])
        if not issued <= datetime.now(timezone.utc) < expires:
            raise ValueError("Operator window expired; inspect and seal a fresh finite window")
        _, state = runtime.service._state(attempt_id)
        if state.phase.value != "request":
            raise ValueError("Attempt is not in request phase")
        request = runtime.committer._reopen_video_request(state.request)
        preview = paid_preview(request)
        receipt = "iris-ep01-bound-" + hashlib.sha256(bound_bytes).hexdigest()[:16]
        ceiling = bound["operator_ceiling"] * 1_000_000
        authorization = PaidProviderAuthorizationDecision.create(attempt_id=attempt_id,
            preview_fingerprint=preview.preview_fingerprint, explicit_opt_in=True,
            actor=ActorIdentity(actor_id="user", actor_kind="human"),
            opt_in_policy_receipt_id=receipt, budget_policy_id="iris-ep01-a01-250-CRD",
            budget_currency=bound["operator_currency"], project_budget_ceiling_microunits=ceiling,
            per_call_ceiling_microunits=ceiling, egress_authorized=True,
            egress_policy_receipt_id=receipt, live_test_authorized=True,
            live_authorization_receipt_id=receipt, issued_at=issued, expires_at=expires,
            max_submit_count=1)
        authorizations[preview.preview_fingerprint] = authorization
        seal(unit_root, "submit-intent.json", {"attempt_id": attempt_id,
            "request_hash": request.resolved_generation_hash,
            "preview_fingerprint": preview.preview_fingerprint,
            "created_at": datetime.now(timezone.utc).isoformat(), "max_submit_count": 1})
        result = runtime.submit_once(attempt_id=attempt_id, paid_preview=preview,
            reservation_id=bound.get("reservation_id", "iris-ep01-a01-reservation-001"))
        seal(unit_root, "submit-result.json", result)
        print(json.dumps({"submitted": True, "automatic_retries": 0}))
    elif action == "poll":
        result = runtime.refresh_once(attempt_id=attempt_id)
        print(json.dumps({"state": result.state.value, "progress_milli": result.progress_milli}))
    elif action == "fetch":
        result = runtime.fetch_once(attempt_id=attempt_id)
        seal(unit_root, "fetch-result.json", result)
        print(json.dumps({"artifact_path": str(result.relative_path),
            "sha256": result.receipt.artifact_sha256, "bytes": result.receipt.size_bytes}))
    else:
        raise ValueError("prepare/start/submit/poll/fetch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
