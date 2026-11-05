#!/usr/bin/env python3
"""Gate for the Jimeng 数字人 trial units (OmniHuman 1.5, 大师模式) of IRIS EP01 v2; nothing here calls Jimeng.

  uv run python outputs/ai-city-takeover/ep01/v2/gen/omnihuman.py lint|permit|record <unit>

The browser side is gen/omnihuman.cjs: fill (upload the approved image and audio, pick 大师模式, type the approved
action description, read the price; no submit), submit (one click under an unused permit), fetch.
- lint: the unit's inputs and action text equal the user-approved preview (trial/omnihuman/preview-approval.json),
  the continuity report names the unit ready, the unit was never submitted, and the trial ledger has room.
- permit: after fill, the observed page shows 大师模式, the approved action text, both uploads, and a price within the
  approved per-take ceiling and the ledger total; writes a one-use permit bound to that exact observation, valid 20 min.
- record: after submit, books the take in trial/omnihuman/ledger.json with the observed price and balances. An
  unknown outcome is booked as unknown and closes the trial: no retry, no remint.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

V2 = Path(__file__).resolve().parents[1]
TRIAL = V2 / os.environ.get("OMNI_TRIAL", "trial/omnihuman")    # a later trial names its own folder
LEDGER = TRIAL / "ledger.json"
REPORT = TRIAL / "continuity-report.json"
PERMIT_MINUTES = 20


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> datetime:
    return datetime.now(timezone.utc)


def load(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_once(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as handle:              # never overwrite an earlier record
        json.dump(value, handle, ensure_ascii=False, indent=1)
        handle.write("\n")


def approval() -> dict:
    return load(TRIAL / "preview-approval.json")


def ledger() -> dict:
    a = approval()["budget"]
    return load(LEDGER, {"ceilings": {"submits": a["generations"], "credits": a["cumulative_CRD"],
                                      "per_take": a["operator_ceiling_per_take_CRD"]}, "takes": []})


def spent(book: dict) -> tuple[int, int, bool]:
    takes = book["takes"]
    return len(takes), sum(t.get("price_observed") or book["ceilings"]["per_take"] for t in takes), \
        any(t["outcome"] != "submitted" for t in takes)


def action_text(unit: str):
    return approval()["takes"][unit]["action_prompt"]


def lint(unit: str) -> dict:
    a = approval()
    root = TRIAL / unit
    root.mkdir(exist_ok=True)
    report = load(REPORT, {})
    book = ledger()
    n, credits, closed = spent(book)
    text = action_text(unit) if unit in a["takes"] else ""
    checks = {
        "unit_in_approved_preview": unit in a["takes"],
        "user_approval_quoted": bool(a.get("user_quote")),
        "approved_inputs_unchanged": all(sha(V2 / x["path"]) == x["sha256"] for x in a["preview_artifacts"]),
        "action_text_is_approved_text": text is None or hashlib.sha256(text.encode()).hexdigest()
        == a["takes"][unit].get("action_prompt_sha256"),
        "action_text_pure_chinese": text is None or not re.search(r"[A-Za-z]", text),
        "mode_is_master": "大师模式" in a["mode"],
        "continuity_report_ready": report.get("units", {}).get(unit, {}).get("verdict") == "ready",
        "never_submitted": not (root / "submit-intent.json").exists(),
        "ledger_has_room": n + 1 <= book["ceilings"]["submits"]
        and credits + book["ceilings"]["per_take"] <= book["ceilings"]["credits"] and not closed,
    }
    out = {"unit": unit, "checks": checks, "pass": all(checks.values()), "at": now().isoformat(),
           "approval_sha256": sha(TRIAL / "preview-approval.json"),
           "continuity_report_sha256": sha(REPORT) if REPORT.exists() else None,
           "inputs": a["preview_artifacts"], "action_text": text, "ledger": {"takes": n, "credits": credits}}
    (root / "lint.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return out


def permit(unit: str) -> dict:
    root = TRIAL / unit
    a = approval()
    lint_now = lint(unit)
    fill = load(root / "fill-observed.json")
    book = ledger()
    n, credits, closed = spent(book)
    text = action_text(unit) or ""
    price = fill.get("price") if fill else None
    checks = {
        "lint_pass": lint_now["pass"],
        "fill_observed": fill is not None,
        "page_mode_master": bool(fill) and "大师模式" in (fill.get("mode_label") or ""),
        "page_action_row_is_approved_text": bool(fill) and (fill.get("rows") or {}).get("action") == text if text
        else bool(fill) and ((fill.get("rows") or {}).get("action") in ("", None)
                             or (fill.get("rows") or {}).get("action", "").startswith("(可选)")),
        "page_speech_is_the_uploaded_audio": bool(fill) and (fill.get("rows") or {}).get("speech_text") is None
        and (fill.get("rows") or {}).get("speech_audio") == "00:05",
        "page_not_vivid": bool(fill) and not fill.get("vivid"),
        "page_resolution_not_below_1080p": bool(fill) and fill.get("resolution") in (None, "1080P", "2K", "4K"),
        "precise_balance_read": bool(fill) and isinstance(fill.get("balance_precise"), int),
        "page_generate_enabled": bool(fill) and fill.get("generate_enabled") is True,
        "page_has_image_and_audio": bool(fill) and fill.get("image_uploaded") is True and fill.get("audio_uploaded") is True,
        "price_read": isinstance(price, int) and price > 0,
        "price_within_per_take_ceiling": isinstance(price, int) and price <= book["ceilings"]["per_take"],
        "price_within_trial_total": isinstance(price, int) and credits + price <= book["ceilings"]["credits"]
        and n + 1 <= book["ceilings"]["submits"] and not closed,
        "no_permit_yet": not (root / "permit.json").exists(),
    }
    out = {"unit": unit, "checks": checks, "pass": all(checks.values())}
    if out["pass"]:
        write_once(root / "permit.json", {
            "unit": unit, "one_use": True, "issued_at": now().isoformat(),
            "expires_at": (now() + timedelta(minutes=PERMIT_MINUTES)).isoformat(),
            "fill_observed_sha256": sha(root / "fill-observed.json"), "price": price,
            "approval_sha256": sha(TRIAL / "preview-approval.json"), "user_quote": a["user_quote"]})
    return out


def record(unit: str) -> dict:
    root = TRIAL / unit
    sub = load(root / "submitted.json")
    intent = load(root / "submit-intent.json")
    if not intent:
        raise SystemExit(f"{unit}: no submit intent, nothing to record")
    book = ledger()
    if any(t["unit"] == unit for t in book["takes"]):
        raise SystemExit(f"{unit}: already booked")
    outcome = (sub or {}).get("outcome", "unknown")
    book["takes"].append({"unit": unit, "outcome": outcome, "price_observed": (intent or {}).get("price"),
                          "balance_before": (sub or intent).get("balance_before"), "balance_after": (sub or {}).get("balance_after"),
                          "booked_at": now().isoformat()})
    LEDGER.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n")
    return {"unit": unit, "outcome": outcome, "ledger": spent(book)}


if __name__ == "__main__":
    action, unit = sys.argv[1], sys.argv[2]
    result = {"lint": lint, "permit": permit, "record": record}[action](unit)
    print(json.dumps({k: v for k, v in result.items() if k in ("unit", "pass", "outcome", "ledger")}
                     | ({"failed": [k for k, v in result["checks"].items() if not v]} if "checks" in result else {}), ensure_ascii=False))
    raise SystemExit(0 if result.get("pass", True) else 2)
