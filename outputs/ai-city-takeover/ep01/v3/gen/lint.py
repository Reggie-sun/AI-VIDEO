#!/usr/bin/env python3
"""Pre-submit lint for one IRIS EP01 v3 Seedance unit; writes <unit>/pre-submit-lint.json, which operator.py requires.

  uv run python outputs/ai-city-takeover/ep01/v3/gen/lint.py <unit>

Every check reads the unit's sealed files; nothing is called and nothing is changed. A unit is ready only when
all checks pass and a continuity report (continuity-supervisor, before any paid preview/permit/POST) names it ready.
Paths as in unit.py: approval and continuity report in pilot/sd/ (SD_PILOT), unit folders and ledgers in gen/
(SD_UNITS), or all of them in one SD_TRIAL folder; every path inside the approval and the bound is relative to the repo
root, except bound["ledger"], which is relative to the unit folders' parent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

P = Path(__file__).resolve().parent
REPO = P.parents[4]
sys.path.insert(0, str(P))

import unit as U  # noqa: E402

REMOVAL = re.compile(r"去除水印|去掉水印|删除标识|remove (the )?(watermark|label|logo)", re.I)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lint(name: str) -> dict:
    spec, root = U.SPECS[name], U.UNITS / name
    bound = json.loads((root / "operator-bound.json").read_text())
    profile = json.loads((root / "profile.json").read_text())
    selections = json.loads((root / "source-selections.json").read_text())
    approval = U.approval()
    prepared = json.loads((root / "prepare-result.json").read_text())
    request = prepared["resolved_request"]
    compiled = (root / "compiled-native-prompt.zh.txt").read_text(encoding="utf-8").rstrip("\n")
    approved_shas = {a["sha256"] for a in approval["preview_artifacts"]}
    images = [x for x in selections if x.get("kind") != "audio"]
    audios = [x for x in selections if x.get("kind") == "audio"]
    gen = approval.get("generation", {})
    budget = approval.get("budget", {})
    ledger_path = U.UNITS / bound["ledger"]
    book = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"submits": []}
    spent = [s for s in book["submits"] if s["outcome"] != "known_no_effect"]
    report_path = U.REPORT
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    unit_report = report.get("units", {}).get(name, {})
    checks = {
        "exact_image_order": [b["asset_id"] for b in request["image_bindings"]] == [x["asset_id"] for x in images],
        "audio_binding": [b["asset_id"] for b in request["media_bindings"]] == [x["asset_id"] for x in audios]
        and all(sha(REPO / x["path"]) == x["sha256"] for x in audios),
        "every_input_in_user_preview": all(x["sha256"] in approved_shas for x in selections),
        "prompt_language_policy": U.prompt_language_ok(spec, compiled),
        "prompt_is_user_approved_text": compiled == approval["prompts"][name]["text"],
        "directed_behaviour_in_text": all(x in compiled for x in spec["intent"]["open_event"]),
        "no_platform_label_removal": not REMOVAL.search(compiled),
        "bound_output": (profile.get("model_id"), profile.get("input_mode", "multimodal"), profile.get("duration_seconds"),
                         profile.get("resolution"), profile.get("aspect_ratio"))
        == (gen.get("model"), gen.get("mode"), gen.get("seconds"), gen.get("resolution"), gen.get("aspect"))
        == tuple(spec["generation"][k] for k in ("model", "mode", "seconds", "resolution", "aspect"))
        and gen == spec["generation"],
        "operator_ceiling_matches_preview": profile.get("credit_upper_bound") == bound["operator_ceiling"]
        == budget.get("operator_ceiling_per_unit_CRD"),
        "bound_matches_approval": bound.get("unit") == name and bound.get("user_quote") == approval["user_quote"]
        and (U.REPO / bound.get("preview_approval", "")).resolve() == U.APPROVAL.resolve()
        and bound.get("cumulative_submit_ceiling") == budget.get("generations")
        and bound.get("cumulative_operator_credit_ceiling") == budget.get("cumulative_CRD"),
        "cumulative_budget_left": len(spent) + 1 <= bound["cumulative_submit_ceiling"]
        and sum(s["operator_ceiling"] for s in spent) + bound["operator_ceiling"] <= bound["cumulative_operator_credit_ceiling"],
        "continuity_report_ready": unit_report.get("verdict") == "ready",
    }
    return {"unit": name, "checks": checks, "pass": all(checks.values()),
            "request_hash": request["resolved_generation_hash"], "compiled_prompt_sha256": hashlib.sha256(compiled.encode()).hexdigest(),
            "approval_sha256": sha(U.APPROVAL),
            "continuity_report": {"path": str(report_path.relative_to(REPO)) if report_path.is_relative_to(REPO) else str(report_path),
                                  "sha256": sha(report_path) if report_path.exists() else None, "unit": unit_report},
            "budget": {"operator_ceiling_CRD": bound["operator_ceiling"], "spent_submits": len(spent),
                       "cumulative_ceilings": [bound["cumulative_submit_ceiling"], bound["cumulative_operator_credit_ceiling"]]},
            "new_calls": 0}


if __name__ == "__main__":
    out = lint(sys.argv[1])
    (U.UNITS / sys.argv[1] / "pre-submit-lint.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"unit": out["unit"], "pass": out["pass"], "failed": [k for k, v in out["checks"].items() if not v]}))
    raise SystemExit(0 if out["pass"] else 2)
