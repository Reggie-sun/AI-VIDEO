#!/usr/bin/env python3
"""Gate for the Jimeng 数字人 pilot takes (OmniHuman 1.5, 大师模式) of IRIS EP01 v3; nothing here calls Jimeng.

  uv run python outputs/ai-city-takeover/ep01/v3/gen/omnihuman.py lint|permit|record <unit>

Paths: the trial folder is outputs/ai-city-takeover/ep01/v3/pilot/oh/ unless OMNI_TRIAL names another one (relative to
the repo root, or absolute). It holds preview-approval.json, continuity-report.json, ledger.json and one folder per unit.
Every path inside the approval (takes.<unit>.image.path, takes.<unit>.audio.path, preview_artifacts[].path) is relative
to the repo root, e.g. outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav.

The browser side is gen/omnihuman.cjs: fill (upload the take's own approved image and audio, pick 大师模式, type the
approved action description, read the price; no submit), submit (one click under an unused permit), fetch.
- lint: the take's image, audio (and its length in seconds) and action text equal the user-approved preview, the
  continuity report names the unit ready, the unit was never submitted, and the ledger has room under the approval's caps.
- permit: after fill, the observed page shows 大师模式, the approved action text, both uploads, an audio length equal to
  the floor or the ceiling of the take's approved seconds (anything else fails closed), and a price within the approved
  per-take and total caps; writes a one-use permit bound to that exact observation, the approval and the price, 20 min.
- record: after submit, books the take in <trial>/ledger.json with the observed price and balances. Any outcome other
  than "submitted" (unknown included) is booked as it is and closes the ledger: no retry, no remint.
The caps are read from the approval's budget on every call: generations (takes in total), cumulative_CRD (credits in
total), operator_ceiling_per_take_CRD (credits per take), retries (extra submits per take; 0 = one submit per take).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import wave

REPO = Path(__file__).resolve().parents[5]
TRIAL = REPO / os.environ.get("OMNI_TRIAL", "outputs/ai-city-takeover/ep01/v3/pilot/oh")
APPROVAL = TRIAL / "preview-approval.json"
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
    return load(APPROVAL)


def ledger() -> dict:                                     # caps always from the approval; the file keeps the takes
    b = approval()["budget"]
    return {"ceilings": {"submits": b["generations"], "credits": b["cumulative_CRD"],
                         "per_take": b["operator_ceiling_per_take_CRD"], "submits_per_take": 1 + b["retries"]},
            "takes": load(LEDGER, {"takes": []})["takes"]}


def spent(book: dict) -> tuple[int, int, bool]:
    takes = book["takes"]
    return len(takes), sum(t.get("price_observed") or book["ceilings"]["per_take"] for t in takes), \
        any(t["outcome"] != "submitted" for t in takes)


def take_room(book: dict, unit: str) -> bool:              # submits already booked for this take stay under its cap
    return sum(t["unit"] == unit for t in book["takes"]) + 1 <= book["ceilings"]["submits_per_take"]


def take(unit: str) -> dict:
    return approval()["takes"].get(unit) or {}


def file_ok(entry: dict) -> bool:                           # an approved input: repo-root path, exact bytes
    rel = (entry or {}).get("path")
    return bool(rel) and (REPO / rel).is_file() and sha(REPO / rel) == entry.get("sha256")


def wav_seconds(path: Path) -> float | None:
    try:
        with wave.open(str(path)) as wav:
            return wav.getnframes() / wav.getframerate()
    except (wave.Error, EOFError, OSError):
        return None


def mmss(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def page_audio(unit: str, shown) -> dict:
    """The page shows the audio length as mm:ss; accept only the floor or the ceiling of the take's approved seconds."""
    secs = (take(unit).get("audio") or {}).get("seconds")
    if not isinstance(secs, (int, float)) or isinstance(secs, bool) or secs <= 0:
        return {"shown": shown, "seconds": secs, "floor": None, "ceil": None, "matched": None}
    lo, hi = mmss(math.floor(secs)), mmss(math.ceil(secs))
    matched = ("exact" if lo == hi else "floor") if shown == lo else "ceil" if shown == hi else None
    return {"shown": shown, "seconds": secs, "floor": lo, "ceil": hi, "matched": matched}


def action_text(unit: str):
    return take(unit).get("action_prompt")


def lint(unit: str) -> dict:
    a = approval()
    t = a["takes"].get(unit) or {}
    image, audio = t.get("image") or {}, t.get("audio") or {}
    root = TRIAL / unit
    root.mkdir(exist_ok=True)
    report = load(REPORT, {})
    book = ledger()
    n, credits, closed = spent(book)
    text = action_text(unit) if t else ""
    seen = {x["sha256"] for x in a["preview_artifacts"]}
    secs = wav_seconds(REPO / audio["path"]) if file_ok(audio) else None
    checks = {
        "unit_in_approved_preview": bool(t),
        "user_approval_quoted": bool(a.get("user_quote")),
        "take_has_own_image_and_audio": bool(image.get("path") and audio.get("path")),
        "approved_inputs_unchanged": file_ok(image) and file_ok(audio)
        and all(file_ok(x) for x in a["preview_artifacts"]),
        "take_inputs_in_preview": image.get("sha256") in seen and audio.get("sha256") in seen,
        "audio_seconds_match_file": secs is not None and isinstance(audio.get("seconds"), (int, float))
        and round(secs, 2) == audio["seconds"],
        "action_text_is_approved_text": text is None or hashlib.sha256(text.encode()).hexdigest()
        == t.get("action_prompt_sha256"),
        "action_text_pure_chinese": text is None or not re.search(r"[A-Za-z]", text),
        "mode_is_master": "大师模式" in a["mode"],
        "continuity_report_ready": report.get("units", {}).get(unit, {}).get("verdict") == "ready",
        "never_submitted": not (root / "submit-intent.json").exists(),
        "ledger_has_room": n + 1 <= book["ceilings"]["submits"] and take_room(book, unit)
        and credits + book["ceilings"]["per_take"] <= book["ceilings"]["credits"] and not closed,
    }
    out = {"unit": unit, "checks": checks, "pass": all(checks.values()), "at": now().isoformat(),
           "approval_sha256": sha(APPROVAL),
           "continuity_report_sha256": sha(REPORT) if REPORT.exists() else None,
           "inputs": {"image": image, "audio": audio},
           "page_audio_accepted": {k: v for k, v in page_audio(unit, None).items() if k in ("seconds", "floor", "ceil")},
           "action_text": text, "ledger": {"takes": n, "credits": credits, "closed": closed}, "caps": book["ceilings"]}
    (root / "lint.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return out


def permit(unit: str) -> dict:
    root = TRIAL / unit
    a = approval()
    lint_now = lint(unit)
    fill = load(root / "fill-observed.json")
    book = ledger()
    n, credits, closed = spent(book)
    t = take(unit)
    text = action_text(unit) or ""
    price = fill.get("price") if fill else None
    rows = (fill or {}).get("rows") or {}
    audio_seen = page_audio(unit, rows.get("speech_audio"))
    inputs = [{"path": x.get("path"), "sha256": x.get("sha256")} for x in (t.get("image") or {}, t.get("audio") or {})]
    checks = {
        "lint_pass": lint_now["pass"],
        "fill_observed": fill is not None,
        "fill_used_the_take_inputs": bool(fill) and fill.get("inputs") == inputs,
        "page_mode_master": bool(fill) and "大师模式" in (fill.get("mode_label") or ""),
        "page_action_row_is_approved_text": bool(fill) and rows.get("action") == text if text
        else bool(fill) and (rows.get("action") in ("", None) or rows.get("action", "").startswith("(可选)")),
        "page_audio_length_is_floor_or_ceil_of_take": bool(fill) and rows.get("speech_text") is None
        and audio_seen["matched"] is not None,
        "page_not_vivid": bool(fill) and not fill.get("vivid"),
        "page_resolution_not_below_1080p": bool(fill) and fill.get("resolution") in (None, "1080P", "2K", "4K"),
        "precise_balance_read": bool(fill) and isinstance(fill.get("balance_precise"), int),
        "page_generate_enabled": bool(fill) and fill.get("generate_enabled") is True,
        "page_has_image_and_audio": bool(fill) and fill.get("image_uploaded") is True and fill.get("audio_uploaded") is True,
        "price_read": isinstance(price, int) and price > 0,
        "price_within_per_take_ceiling": isinstance(price, int) and price <= book["ceilings"]["per_take"],
        "price_within_trial_total": isinstance(price, int) and credits + price <= book["ceilings"]["credits"]
        and n + 1 <= book["ceilings"]["submits"] and take_room(book, unit) and not closed,
        "no_permit_yet": not (root / "permit.json").exists(),
    }
    out = {"unit": unit, "checks": checks, "pass": all(checks.values()), "page_audio": audio_seen}
    if out["pass"]:
        write_once(root / "permit.json", {
            "unit": unit, "one_use": True, "issued_at": now().isoformat(),
            "expires_at": (now() + timedelta(minutes=PERMIT_MINUTES)).isoformat(),
            "fill_observed_sha256": sha(root / "fill-observed.json"), "price": price,
            "page_audio": audio_seen, "approval_sha256": sha(APPROVAL), "user_quote": a["user_quote"]})
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
    print(json.dumps({k: v for k, v in result.items() if k in ("unit", "pass", "outcome", "ledger", "page_audio")}
                     | ({"failed": [k for k, v in result["checks"].items() if not v]} if "checks" in result else {}), ensure_ascii=False))
    raise SystemExit(0 if result.get("pass", True) else 2)
