#!/usr/bin/env python3
"""Audit a storyboard (author's board/shots.json format) against the song before the director sees it.

  python3 -I motion-kit/tools/board_audit.py --board BOARD.json --words timing/words.json --beats beatmap/beats.json \
      [--music-map music-map.json] [--lead 0.70] [--sung-max 110] [--motion-max 140] [--banned WORD ...] [--json OUT]

Gates (wiki_storyboard "The audit"); exit 1 when any FAILS:
  tile          shots cover 0..duration with no gap or overlap (> 0.01 s)
  cuts          every cut within 0.03 s of a beat (or a shot's declared `hit`)
  words_typed   every sung word starts in a shot whose `type` lists its line
  graphics      every lyric line has at least one device whose `line` is it; >= 6 kinds; never one kind on 3 lines in a row
  lead_share    seconds with lead_on_screen >= --lead of the song; no stretch without her longer than two bars
  budget        planned sung / motion clip seconds within the caps
  clip_windows  sung clip 4-8 s and starting in a word gap; motion clip 4-12 s
  plates_unique a plate used by two non-adjacent shots; two clips starting from the same plate
  treatments    a 2.5D (plate3d) shot without a treatment, or the same treatment on two 2.5D shots in a row
  todo          a TODO / placeholder, or a shot without a framing
  banned        a banned word anywhere in the board
Report only (no fail): cuts on bar lines vs off, pieces under 1 s, 4+ equal-length pieces in a row, server-room shots.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
from pathlib import Path

FRAMINGS = {"ECU", "CU", "MCU", "MS", "MWS", "WS", "FS", "EWS", "OTS"}


def near(sorted_vals: list[float], t: float) -> float:
    i = bisect.bisect_left(sorted_vals, t)
    return min((abs(sorted_vals[j] - t) for j in (i - 1, i) if 0 <= j < len(sorted_vals)), default=1e9)


def audit(board: dict, words: dict, beats: dict, lead: float, sung_max: float, motion_max: float, banned: list[str]) -> dict:
    shots = sorted(board["shots"], key=lambda s: s["t0"])
    dur = float(board.get("duration") or beats["duration"])
    bt = sorted(beats["beats"])
    db = sorted(beats["downbeats"])
    bar = (db[-1] - db[0]) / (len(db) - 1)
    lines = words["lines"]
    fails: dict[str, list] = {}
    report: dict[str, object] = {}

    def fail(gate: str, msg) -> None:
        fails.setdefault(gate, []).append(msg)

    # tile
    if abs(shots[0]["t0"]) > 0.01:
        fail("tile", f"first shot starts at {shots[0]['t0']}")
    for a, b in zip(shots, shots[1:]):
        if abs(a["t1"] - b["t0"]) > 0.01:
            fail("tile", f"{a['id']}->{b['id']}: {a['t1']} vs {b['t0']}")
    if abs(shots[-1]["t1"] - dur) > 0.05:
        fail("tile", f"last shot ends at {shots[-1]['t1']}, song {dur}")

    # cuts
    on_bar = off_bar = 0
    for s in shots[1:]:
        d = near(bt, s["t0"])
        if d > 0.03 and not (s.get("hit") is not None and abs(s["hit"] - s["t0"]) <= 0.03):
            fail("cuts", f"{s['id']} at {s['t0']:.3f}: {d:.3f} s from a beat")
        if near(db, s["t0"]) <= 0.03:
            on_bar += 1
        else:
            off_bar += 1
    report["cuts_on_bar_lines"] = on_bar
    report["cuts_off_bar_lines"] = off_bar

    # words typed
    def shot_at(t: float):
        i = bisect.bisect_right([s["t0"] for s in shots], t) - 1
        return shots[max(0, i)]
    for li, ln in enumerate(lines):
        for w in ln["words"]:
            s = shot_at(w["start"])
            typed = {t.get("line") for t in s.get("type") or []}
            if li not in typed:
                fail("words_typed", f"line {li} word {w['text']!r} @{w['start']:.2f} in {s['id']} (types {sorted(x for x in typed if x is not None)})")
                break

    # graphics
    kind_of_line: dict[int, set] = {}
    kinds = set()
    for s in shots:
        for d in s.get("devices") or []:
            if d.get("line") is not None:
                kind_of_line.setdefault(int(d["line"]), set()).add(d.get("kind"))
                kinds.add(d.get("kind"))
    for li in range(len(lines)):
        if li not in kind_of_line:
            fail("graphics", f"line {li} has no explaining graphic: {lines[li]['en']!r}")
    if len(kinds) < 6:
        fail("graphics", f"only {len(kinds)} graphic kinds: {sorted(map(str, kinds))}")
    for li in range(len(lines) - 2):
        common = kind_of_line.get(li, set()) & kind_of_line.get(li + 1, set()) & kind_of_line.get(li + 2, set())
        if common and all(len(kind_of_line.get(li + k, set())) == 1 for k in range(3)):
            fail("graphics", f"lines {li}-{li + 2} all use only {sorted(common)}")
    report["graphic_kinds"] = sorted(map(str, kinds))

    # lead share
    on = sum(s["t1"] - s["t0"] for s in shots if s.get("lead_on_screen"))
    report["lead_share"] = round(on / dur, 3)
    if on / dur < lead:
        fail("lead_share", f"{on / dur:.1%} < {lead:.0%}")
    run = 0.0
    for s in shots:
        run = 0.0 if s.get("lead_on_screen") else run + (s["t1"] - s["t0"])
        if run > 2 * bar + 0.03:
            fail("lead_share", f"{run:.2f} s without her ending at {s['id']}")
            run = -1e9

    # clips: window per clip id over its shots
    clips: dict[str, dict] = {}
    for s in shots:
        if s.get("motion_tier") in ("sung", "motion") and s.get("clip"):
            c = clips.setdefault(s["clip"], {"tier": s["motion_tier"], "t0": s["t0"], "t1": s["t1"], "shots": [], "plates": set()})
            c["t0"], c["t1"] = min(c["t0"], s["t0"]), max(c["t1"], s["t1"])
            c["shots"].append(s["id"])
            c["plates"].add(s.get("plate"))
        elif s.get("motion_tier") in ("sung", "motion"):
            fail("clip_windows", f"{s['id']} is {s['motion_tier']} without a clip id")
    # a board may declare each clip's own generation window (longer than the part a shot plays): it wins
    for c in board.get("clips") or []:
        w = c.get("window") or c
        cid = c.get("id") or c.get("clip")
        if cid in clips and "t0" in w and "t1" in w:
            clips[cid]["t0"], clips[cid]["t1"] = float(w["t0"]), float(w["t1"])
    sung = sum(c["t1"] - c["t0"] for c in clips.values() if c["tier"] == "sung")
    motion = sum(c["t1"] - c["t0"] for c in clips.values() if c["tier"] == "motion")
    report.update(sung_s=round(sung, 2), motion_s=round(motion, 2), clips=len(clips))
    if sung > sung_max:
        fail("budget", f"sung {sung:.1f} s > {sung_max}")
    if motion > motion_max:
        fail("budget", f"motion {motion:.1f} s > {motion_max}")
    all_words = [w for ln in lines for w in ln["words"]]
    for cid, c in clips.items():
        d = c["t1"] - c["t0"]
        lo, hi = (4.0, 8.0) if c["tier"] == "sung" else (4.0, 12.0)
        if not lo - 0.03 <= d <= hi + 0.03:
            fail("clip_windows", f"{cid} ({c['tier']}) {d:.2f} s outside {lo:g}-{hi:g}")
        if c["tier"] == "sung" and any(w["start"] + 0.05 < c["t0"] < w["end"] - 0.05 for w in all_words):
            fail("clip_windows", f"{cid} starts at {c['t0']:.2f} inside a word")

    # plates unique
    idx = {s["id"]: i for i, s in enumerate(shots)}
    users: dict[str, list[int]] = {}
    for s in shots:
        if s.get("plate"):
            users.setdefault(s["plate"], []).append(idx[s["id"]])
    for p, us in users.items():
        if any(b - a > 1 for a, b in zip(us, us[1:])):
            fail("plates_unique", f"plate {p} on non-adjacent shots {[shots[i]['id'] for i in us]}")
    start_plate: dict[str, str] = {}
    for cid, c in clips.items():
        first = shots[min(idx[x] for x in c["shots"])].get("plate")
        if first and first in start_plate:
            fail("plates_unique", f"clips {start_plate[first]} and {cid} both start from plate {first}")
        elif first:
            start_plate[first] = cid

    # treatments
    prev = None
    for s in shots:
        if s.get("motion_tier") == "plate3d":
            if not s.get("treatment"):
                fail("treatments", f"{s['id']} plate3d without treatment")
            elif s["treatment"] == prev:
                fail("treatments", f"{s['id']} repeats treatment {prev!r}")
            prev = s.get("treatment")

    # todo / framing / banned
    text = json.dumps(board, ensure_ascii=False)
    for s in shots:
        if s.get("framing") not in FRAMINGS and s.get("lead_on_screen", True) and s.get("plate"):
            fail("todo", f"{s['id']} framing {s.get('framing')!r}")
    if re.search(r"\bTODO\b|\bTBD\b|placeholder", text, re.I):
        fail("todo", "TODO/TBD/placeholder in board")
    for w in banned:
        if re.search(re.escape(w), text, re.I):
            fail("banned", w)

    # pacing report
    lens = [round(s["t1"] - s["t0"], 2) for s in shots]
    report["shots"] = len(shots)
    report["mean_s"] = round(sum(lens) / len(lens), 2)
    report["pieces_under_1s"] = [s["id"] for s in shots if s["t1"] - s["t0"] < 1.0]
    same = [shots[i]["id"] for i in range(len(lens) - 3) if len({lens[i + k] for k in range(4)}) == 1]
    report["four_equal_in_a_row_from"] = same
    report["server_room_shots"] = [s["id"] for s in shots if re.search(r"机房|服务器|server|data ?cent", (s.get("set") or "") + (s.get("prompt") or ""), re.I)]
    return {"pass": not fails, "fails": fails, "report": report}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, required=True)
    ap.add_argument("--words", type=Path, required=True)
    ap.add_argument("--beats", type=Path, required=True)
    ap.add_argument("--lead", type=float, default=0.70)
    ap.add_argument("--sung-max", type=float, default=110.0)
    ap.add_argument("--motion-max", type=float, default=140.0)
    ap.add_argument("--banned", nargs="*", default=[])
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    r = audit(json.loads(a.board.read_text()), json.loads(a.words.read_text()), json.loads(a.beats.read_text()),
              a.lead, a.sung_max, a.motion_max, a.banned)
    out = json.dumps(r, ensure_ascii=False, indent=1)
    if a.json:
        a.json.write_text(out + "\n")
    print(json.dumps({"pass": r["pass"], "fails": {k: len(v) for k, v in r["fails"].items()}, **{k: r["report"][k] for k in
                      ("shots", "mean_s", "lead_share", "sung_s", "motion_s", "clips", "cuts_on_bar_lines", "cuts_off_bar_lines")}},
                     ensure_ascii=False))
    for g, msgs in r["fails"].items():
        for m in msgs[:5]:
            print(f"  FAIL {g}: {m}")
        if len(msgs) > 5:
            print(f"  FAIL {g}: … {len(msgs) - 5} more")
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
