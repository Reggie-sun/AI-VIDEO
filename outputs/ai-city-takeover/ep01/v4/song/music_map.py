#!/usr/bin/env python3
"""Sections on the bar grid for the chosen take -> music-map.json (schema iris-music-map/1, same as ep01/v2/song-v3).

  ~/miniconda3/bin/python -I outputs/ai-city-takeover/ep01/v4/song/music_map.py

A section starts on the downbeat nearest to (and not more than half a bar after) its first sung word, so pickups
("All hands!" sung just before the one) land in the section they introduce. It ends where the next one starts.
Per section: bar number (1-based), bar count, first vocal, mix RMS, and the strong hits (score >= 0.6) inside it.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MASTER = HERE / "master/all-hands-r4-edc6c6bf.wav"


def main() -> None:
    import librosa

    beats = json.loads((HERE / "beatmap/beats.json").read_text())
    hits = json.loads((HERE / "beatmap/hits.json").read_text())["hits"]
    lines = json.loads((HERE / "timing/words.json").read_text())["lines"]
    db = np.array(beats["downbeats"])
    dur = beats["duration"]
    bar_s = float(np.median(np.diff(db)))
    # extend the grid back to 0 so bar numbers count from the top of the song
    grid = list(db)
    while grid[0] - bar_s > -0.05:
        grid.insert(0, grid[0] - bar_s)
    grid = np.array([max(0.0, g) for g in grid])

    groups: list[dict] = []
    for ln in lines:
        if groups and groups[-1]["section"] == ln["section"]:
            groups[-1]["end"] = ln["end"]
        else:
            groups.append({"section": ln["section"], "first_vocal": ln["start"], "end": ln["end"]})

    def snap(t: float) -> int:
        cand = np.nonzero(grid <= t + bar_s / 2)[0]
        return int(cand[np.argmin(np.abs(grid[cand] - t))])

    starts = [snap(g["first_vocal"]) for g in groups]
    y, sr = librosa.load(str(MASTER), sr=22050, mono=True)

    def rms(a: float, b: float) -> float:
        seg = y[int(a * sr):int(b * sr)]
        return round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)

    sections = []
    for i, g in enumerate(groups):
        b0 = starts[i]
        b1 = starts[i + 1] if i + 1 < len(groups) else len(grid)
        t0 = float(grid[b0])
        t1 = float(grid[b1]) if b1 < len(grid) else dur
        sections.append({"section": g["section"], "bar": b0 + 1, "bars": b1 - b0, "t0": round(t0, 2), "t1": round(t1, 2),
                         "first_vocal": round(g["first_vocal"], 2), "last_vocal": round(g["end"], 2), "rms_db": rms(t0, t1),
                         "strong_hits": [round(h["t"], 2) for h in hits if t0 <= h["t"] < t1 and h["score"] >= 0.6]})
    pre_t1 = sections[0]["t0"]
    out = {"schema": "iris-music-map/1", "song": str(MASTER.relative_to(HERE.parents[4])),
           "bpm_global": beats["bpm_global"], "bar_s": round(bar_s, 4), "downbeat_phase": beats["downbeat_phase"],
           "bars_total": len(grid), "duration": dur,
           "pre": {"section": "Intro (instrumental)", "bar": 1, "bars": starts[0], "t0": 0.0, "t1": pre_t1,
                   "rms_db": rms(0.0, pre_t1), "strong_hits": [round(h["t"], 2) for h in hits if h["t"] < pre_t1 and h["score"] >= 0.6]},
           "sections": sections}
    (HERE / "music-map.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"bpm {out['bpm_global']}  bar {out['bar_s']}s  bars {out['bars_total']}")
    p = out["pre"]
    print(f"  bar {p['bar']:3}  x{p['bars']:2}  {p['t0']:6.1f}-{p['t1']:6.1f}  {p['rms_db']:6}  {p['section']}")
    for s in sections:
        print(f"  bar {s['bar']:3}  x{s['bars']:2}  {s['t0']:6.1f}-{s['t1']:6.1f}  {s['rms_db']:6}  {s['section']}  (vocal {s['first_vocal']})")


if __name__ == "__main__":
    main()
