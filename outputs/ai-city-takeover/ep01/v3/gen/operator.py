#!/usr/bin/env python3
"""One-use Jimeng operation for an IRIS EP01 v3 Seedance unit; every lifecycle change goes through the existing owners.

  uv run python outputs/ai-city-takeover/ep01/v3/gen/operator.py prepare|start|submit|poll|fetch <unit>

Bound: <units>/<unit>/operator-bound.json (one submit, no automatic retries, finite window, operator ceiling).
Cumulative bound: the bound must name its ledger ("ledger", relative to the unit folders' parent) and the approval's
caps ("cumulative_submit_ceiling" = budget.generations, "cumulative_operator_credit_ceiling" = budget.cumulative_CRD;
lint.py checks both against pilot/sd/preview-approval.json); there are no default ceilings, so a round's history
is never rewritten. Submit also refuses when the approval changed after the lint. Unknown outcomes stop; recovery
stays with the canonical committer. Paths as in unit.py (SD_PILOT, SD_UNITS, SD_TRIAL). Adapted from ep01/v2/gen/operator.py.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import sys

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parents[4]))
sys.path.insert(0, str(P))

import unit as U  # noqa: E402
from ai_video.production.jimeng_browser import JimengBrowserTransport  # noqa: E402
from ai_video.production.jimeng_contracts import JIMENG_ORIGIN  # noqa: E402
from ai_video.production.models import ActorIdentity  # noqa: E402
from ai_video.production.paid_provider import (PaidProviderAuthorizationDecision, PaidProviderCallPreview,  # noqa: E402
                                               SecretReference)
from ai_video.production.project import load_production_project  # noqa: E402
from scripts.jimeng_feedback_driver import create_runtime, load_configuration  # noqa: E402

PROFILE_DIR = Path("/home/reggie/.local/share/ai-video/playwright-mcp/profile")
PLAYWRIGHT = Path("/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright")


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


def seal(root: Path, name: str, value) -> None:
    with (root / name).open("x", encoding="utf-8") as handle:     # never overwrite an earlier record
        json.dump(jsonable(value), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def ledger(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"schema": "iris-v3-paid-ledger/1", "submits": []}


def main(action: str, unit: str) -> int:
    root = U.UNITS / unit
    bound_bytes = (root / "operator-bound.json").read_bytes()
    bound = json.loads(bound_bytes)
    attempt_id = bound["attempt_id"]
    if not all(isinstance(bound.get(k), str if k == "ledger" else int)
               for k in ("ledger", "cumulative_submit_ceiling", "cumulative_operator_credit_ceiling")):
        raise ValueError("the bound must name its ledger and the approval's cumulative ceilings; there are no defaults")
    LEDGER = U.UNITS / bound["ledger"]
    submit_ceiling = bound["cumulative_submit_ceiling"]
    credit_ceiling = bound["cumulative_operator_credit_ceiling"]
    if bound["max_submit_count"] != 1 or bound["automatic_retries"] != 0 or bound["unit"] != unit:
        raise ValueError("this operator permits one submit for its own unit, without automatic retries")
    project = (root / "project").resolve(strict=True)
    config = load_configuration(root / "driver-config.json")
    loaded = load_production_project(project / "project.yaml")
    attempts = [a for a in loaded.manifest.attempts if a.operation == "video_generation"]
    if len(attempts) > 1 or any(a.attempt_id != attempt_id for a in attempts):
        raise ValueError("unexpected attempt in the unit project; inspect before continuing")
    if any(a.status.value in {"outcome_unknown", "interrupted"}
           or (a.paid_provider_state and a.paid_provider_state.phase.value == "outcome_unknown") for a in attempts):
        raise ValueError("unknown outcome: observe and recover through the canonical owner only")
    authorizations = {}
    live = action in {"submit", "poll", "fetch"}
    runtime = create_runtime(project_root=project, configuration=config,
        transport=JimengBrowserTransport(profile_dir=PROFILE_DIR, playwright_module=PLAYWRIGHT) if live else None,
        paid_provider_authorizer=lambda p: authorizations.get(p.preview_fingerprint))
    ceiling = bound["operator_ceiling"] * 1_000_000

    def paid_preview(request):
        preview = runtime.provider.preview(request)
        if preview.estimated_cost_upper_bound_microunits != ceiling:
            raise ValueError("sealed operator ceiling differs from the provider preview")
        return PaidProviderCallPreview.create(attempt_id=attempt_id, operation="video_generation", provider_kind="jimeng",
            model_id=config.jimeng_profile.model_id, request_fingerprint=request.resolved_generation_hash,
            billing_mode="remote_metered", currency=bound["operator_currency"], estimated_cost_upper_bound_microunits=ceiling,
            destination=JIMENG_ORIGIN, method="POST", egress_items=runtime.provider.egress_items(request),
            retention_mode="provider_standard", provider_policy_snapshot_id=bound["policy_id"],
            secret_reference=SecretReference(kind="secret_store", reference_id="JIMENG_BROWSER_SESSION"))

    if action == "prepare":
        if attempts:
            raise ValueError("attempt already exists; inspect instead of preparing another")
        prepared = runtime.prepare()
        if prepared.resolved_request is None or prepared.execution_binding is None:
            print(json.dumps({"executable": False, "decision": jsonable(prepared.decision)}, ensure_ascii=False))
            return 2
        seal(root, "prepared.json", {"execution_binding": prepared.execution_binding,
             "resolved_request": prepared.resolved_request, "compiled_request": prepared.compilation.request,
             "paid_provider_preview": paid_preview(prepared.resolved_request)})
        print(json.dumps({"executable": True, "new_video_calls": 0}))
    elif action == "start":
        if attempts:
            raise ValueError("attempt already exists")
        frozen = json.loads((root / "prepared.json").read_text())
        prepared = runtime.prepare()
        if prepared.execution_binding is None or prepared.execution_binding.binding_hash != frozen["execution_binding"]["binding_hash"]:
            raise ValueError("prepared binding changed")
        result = runtime.start(prepared=prepared, attempt_id=attempt_id)
        print(json.dumps({"started": True, "manifest_revision": result.manifest_revision}))
    elif action == "submit":
        if len(attempts) != 1 or attempts[0].paid_provider_state is not None:
            raise ValueError("one fresh started attempt required; never repeat a paid submit")
        if not (root / "pre-submit-lint.json").is_file() or not json.loads((root / "pre-submit-lint.json").read_text()).get("pass"):
            raise ValueError("pre-submit lint missing or not passed")
        if json.loads((root / "pre-submit-lint.json").read_text()).get("approval_sha256") != hashlib.sha256(
                U.APPROVAL.read_bytes()).hexdigest():
            raise ValueError("the approval changed after the lint; re-lint before any submit")
        book = ledger(LEDGER)
        spent = [s for s in book["submits"] if s["outcome"] != "known_no_effect"]   # sealed no-effect receipts cost nothing
        if (len(spent) + 1 > submit_ceiling
                or sum(s["operator_ceiling"] for s in spent) + bound["operator_ceiling"] > credit_ceiling):
            raise ValueError("cumulative budget would be exceeded; stop and report")
        issued, expires = datetime.fromisoformat(bound["issued_at"]), datetime.fromisoformat(bound["expires_at"])
        if not issued <= datetime.now(timezone.utc) < expires:
            raise ValueError("operator window expired; seal a fresh finite window")
        _, state = runtime.service._state(attempt_id)
        if state.phase.value != "request":
            raise ValueError("attempt is not in the request phase")
        request = runtime.committer._reopen_video_request(state.request)
        linted = json.loads((root / "pre-submit-lint.json").read_text()).get("request_hash")
        if linted and linted != request.resolved_generation_hash:       # what is sent must be what the lint passed
            raise ValueError("request hash differs from the linted request; re-lint before any submit")
        preview = paid_preview(request)
        receipt = "iris-v3-bound-" + hashlib.sha256(bound_bytes).hexdigest()[:16]
        authorizations[preview.preview_fingerprint] = PaidProviderAuthorizationDecision.create(attempt_id=attempt_id,
            preview_fingerprint=preview.preview_fingerprint, explicit_opt_in=True,
            actor=ActorIdentity(actor_id="user", actor_kind="human"), opt_in_policy_receipt_id=receipt,
            budget_policy_id=bound["policy_id"], budget_currency=bound["operator_currency"],
            project_budget_ceiling_microunits=ceiling, per_call_ceiling_microunits=ceiling, egress_authorized=True,
            egress_policy_receipt_id=receipt, live_test_authorized=True, live_authorization_receipt_id=receipt,
            issued_at=issued, expires_at=expires, max_submit_count=1)
        seal(root, "submit-intent.json", {"attempt_id": attempt_id, "request_hash": request.resolved_generation_hash,
             "preview_fingerprint": preview.preview_fingerprint, "created_at": datetime.now(timezone.utc).isoformat(),
             "max_submit_count": 1})
        book["submits"].append({"unit": unit, "attempt_id": attempt_id, "operator_ceiling": bound["operator_ceiling"],
                                "intent_at": datetime.now(timezone.utc).isoformat(), "outcome": "submitting"})
        LEDGER.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n")
        result = runtime.submit_once(attempt_id=attempt_id, paid_preview=preview, reservation_id=bound["reservation_id"])
        seal(root, "submit-result.json", result)
        book["submits"][-1]["outcome"] = "submitted"
        LEDGER.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps({"submitted": True, "automatic_retries": 0}))
    elif action == "poll":
        result = runtime.refresh_once(attempt_id=attempt_id)
        print(json.dumps({"state": result.state.value, "progress_milli": result.progress_milli}))
    elif action == "fetch":
        result = runtime.fetch_once(attempt_id=attempt_id)
        seal(root, "fetch-result.json", result)
        print(json.dumps({"artifact_path": str(result.relative_path), "sha256": result.receipt.artifact_sha256,
                          "bytes": result.receipt.size_bytes}))
    else:
        raise ValueError("prepare/start/submit/poll/fetch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
