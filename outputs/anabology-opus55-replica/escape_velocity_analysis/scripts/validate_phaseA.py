#!/usr/bin/env python3
"""Validate work/phaseA/boundaries_chunk<k>.json against disturbances and protocol.

Run: python -I scripts/validate_phaseA.py <analysis_root> <k>
Exit 1 on error.
"""
import json
import sys
from pathlib import Path

TYPES = {
    "hard_cut", "flash_cut", "whip_cut", "dissolve", "fade_black", "fade_white", "shape_wipe",
    "light_wipe", "glitch_cut", "match_cut", "zoom_punch_cut", "strobe_burst", "other",
}
EVT = {"flash", "light_leak", "glitch", "hud_swap", "text_swap", "zoom_punch", "camera_whip",
       "speed_ramp", "strobe_pulse", "other"}
N_CHUNKS, N_FRAMES = 5, 7353


def main(root, k):
    root, k = Path(root), int(k)
    errs = []
    f = root / "work" / "phaseA" / f"boundaries_chunk{k}.json"
    try:
        d = json.loads(f.read_text())
    except Exception as ex:  # noqa: BLE001
        print("ERROR cannot parse", f, ex)
        return 1
    chunk_len = -(-N_FRAMES // N_CHUNKS)
    lo, hi = k * chunk_len, min((k + 1) * chunk_len, N_FRAMES)
    if d.get("chunk") != k or d.get("frame_range") != [lo, hi]:
        errs.append(f"chunk/frame_range mismatch, expected {k} {[lo, hi]}")
    dist = {x["dist_id"]: x for x in json.loads((root / "work" / "disturbances.json").read_text()) if x["chunk"] == k}
    seen = {}
    ids = set()
    prev = -1
    for b in d.get("boundaries", []):
        bid = b.get("boundary_id")
        if bid in ids:
            errs.append(f"duplicate {bid}")
        ids.add(bid)
        ff = b.get("first_frame_of_new_shot")
        if not isinstance(ff, int) or not (lo <= ff < hi) or ff <= 0:
            errs.append(f"{bid}: first_frame_of_new_shot {ff} outside chunk")
            continue
        if ff <= prev:
            errs.append(f"{bid}: not sorted ({ff} <= {prev})")
        prev = ff
        if b.get("type") not in TYPES:
            errs.append(f"{bid}: bad type {b.get('type')}")
        sp = b.get("transition_span")
        if not (isinstance(sp, list) and len(sp) == 2 and sp[0] <= sp[1]):
            errs.append(f"{bid}: bad transition_span")
        if b.get("type") == "strobe_burst" and not b.get("constituent_frames"):
            errs.append(f"{bid}: strobe_burst needs constituent_frames")
        c = b.get("confidence")
        if not isinstance(c, (int, float)) or not 0 <= c <= 1:
            errs.append(f"{bid}: confidence")
        for did in b.get("dist_ids", []):
            seen.setdefault(did, []).append(bid)
    for e in d.get("in_shot_events", []):
        if e.get("type") not in EVT:
            errs.append(f"in_shot_event bad type {e.get('type')}")
        fr = e.get("frame_range")
        if not (isinstance(fr, list) and len(fr) == 2 and fr[0] <= fr[1]):
            errs.append(f"in_shot_event bad frame_range {fr}")
        for did in e.get("dist_ids", []):
            seen.setdefault(did, []).append("evt")
    for r in d.get("rejected_disturbances", []):
        seen.setdefault(r.get("dist_id"), []).append("rej")
    for did in dist:
        if did not in seen:
            errs.append(f"{did} not accounted for")
    for did, where in seen.items():
        if did not in dist:
            errs.append(f"{did} unknown for chunk {k}")
        if len(where) > 1 and not all(w.startswith("B") for w in where):
            errs.append(f"{did} classified in multiple places {where}")
    for key in ("chunk_content_summary", "missed_cut_search", "unresolved"):
        if key not in d:
            errs.append(f"missing {key}")
    for e in errs:
        print("ERROR", e)
    print("chunk", k, "boundaries", len(d.get("boundaries", [])), "events", len(d.get("in_shot_events", [])),
          "rejected", len(d.get("rejected_disturbances", [])), "errors", len(errs))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
