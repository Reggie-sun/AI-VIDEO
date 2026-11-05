#!/usr/bin/env python3
"""Stage 7: merge verified Phase-A boundaries into the authoritative shot list.

Input : work/phaseA/boundaries_chunk{0..4}.json, work/metrics.npz
Output: work/shots.json  (frame-exact tiling of 0..7352)
        work/boundaries_all.json (flat, sorted)
Run: python -I scripts/07_merge_boundaries.py <analysis_root>
"""
import json
import sys
from pathlib import Path

N_FRAMES = 7353
FPS = 24


def tc(frame):
    s, f = divmod(frame, FPS)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def main(root):
    root = Path(root)
    bs, evs = [], []
    for k in range(5):
        d = json.loads((root / "work" / "phaseA" / f"boundaries_chunk{k}.json").read_text())
        for b in d["boundaries"]:
            b["chunk"] = k
            bs.append(b)
        for e in d["in_shot_events"]:
            e["chunk"] = k
            evs.append(e)
    bs.sort(key=lambda b: b["first_frame_of_new_shot"])
    firsts = [b["first_frame_of_new_shot"] for b in bs]
    assert len(set(firsts)) == len(firsts), "duplicate boundary frames"
    (root / "work" / "boundaries_all.json").write_text(json.dumps(bs, indent=1))
    starts = [0] + firsts
    shots = []
    for i, a in enumerate(starts):
        b_end = (starts[i + 1] - 1) if i + 1 < len(starts) else N_FRAMES - 1
        bin_ = bs[i - 1] if i > 0 else None
        bout = bs[i] if i < len(bs) else None
        sid = f"S{i+1:04d}"
        shot_events = [e for e in evs if a <= e["frame_range"][0] <= b_end]
        shots.append(
            dict(
                shot_id=sid, start_frame=a, end_frame=b_end, duration_frames=b_end - a + 1,
                start_time=round(a / FPS, 4), end_time=round((b_end + 1) / FPS, 4),
                duration_s=round((b_end - a + 1) / FPS, 4), start_tc=tc(a), end_tc=tc(b_end),
                boundary_in_id=bin_["boundary_id"] if bin_ else None,
                boundary_in_type=bin_["type"] if bin_ else "film_start",
                boundary_in_span=bin_["transition_span"] if bin_ else [0, 0],
                boundary_out_id=bout["boundary_id"] if bout else None,
                boundary_out_type=bout["type"] if bout else "film_end",
                is_strobe_burst=bool(bin_ and bin_["type"] == "strobe_burst"),
                strobe_constituents=(bin_ or {}).get("constituent_frames", []),
                in_shot_events=shot_events,
            )
        )
    (root / "work" / "shots.json").write_text(json.dumps(shots, indent=1))
    durs = [s["duration_frames"] for s in shots]
    print("shots", len(shots), "min", min(durs), "max", max(durs), "median", sorted(durs)[len(durs) // 2])
    short = [s["shot_id"] for s in shots if s["duration_frames"] < 3]
    print("sub-3-frame shots:", short)


if __name__ == "__main__":
    main(sys.argv[1])
