"""Per-bar picture motion of c1 / c2 / c3 (motion-kit qa.py motion_per_bar) beside the music per bar (mix RMS dB and
the mid-band envelope of hits.json), toolkit §22. Run from the repository root after qa.py has written
qa/film-{c1,c2,c3}/report.json:

  uv run python outputs/ai-city-takeover/ep01/v2/qa/pace_vs.py [CANDIDATE=c3]

Writes qa/film-<CANDIDATE>/pace-vs-c1.json (c1, the previous cut and the candidate)."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
V = Path("outputs/ai-city-takeover/ep01/v2")
CAND = sys.argv[1] if len(sys.argv) > 1 else "c3"
PREV = f"c{int(CAND[1:]) - 1}"
rep = {c: json.loads((V / f"qa/film-{c}/report.json").read_text()) for c in ("c1", PREV, CAND)}
beats = json.loads((V / "comp/data/beats.json").read_text())
hits = json.loads((V / "comp/data/hits.json").read_text())
down = beats["downbeats"]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(V / "song/mix/IRIS-01-v2.wav"), "-ac", "1", "-ar", "16000",
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32)
mid = np.array(hits["env24"]["mid"])
SECTION = {1: "開場", 2: "開場", **{b: "主歌" for b in range(3, 11)}, **{b: "副歌" for b in range(11, 15)}, 15: "尾段", 16: "尾段"}
rows = []
for i, b in enumerate(rep["c1"]["motion_per_bar"]):
    bar = b["bar"]
    t0, t1 = down[bar - 1], down[bar] if bar < len(down) else 30.5
    seg = x[int(t0 * 16000):int(t1 * 16000)]
    rms_db = 20 * np.log10(np.sqrt(np.mean(seg.astype(np.float64) ** 2)) + 1e-9)
    m = {c: next(r["motion"] for r in rep[c]["motion_per_bar"] if r["bar"] == bar) for c in rep}
    rows.append({"bar": bar, "t0": round(t0, 3), "t1": round(t1, 3), "section": SECTION.get(bar, ""),
                 "mix_rms_db": round(float(rms_db), 1), "mid_env": round(float(mid[int(t0 * 24):int(t1 * 24)].mean()), 2),
                 "c1": m["c1"], PREV: m[PREV], CAND: m[CAND], f"{CAND}_minus_c1": round(m[CAND] - m["c1"], 3)})
out = V / f"qa/film-{CAND}/pace-vs-c1.json"
out.write_text(json.dumps({"method": "motion = qa.py motion_per_bar (192x108 grey mean abs frame difference, cuts included); "
                           "music = mix RMS per bar and the mid-band (150-4000 Hz) envelope of hits.json", "bars": rows},
                          ensure_ascii=False, indent=1) + "\n")
for r in rows:
    print(f"{r['bar']:2d} {r['t0']:6.2f}-{r['t1']:6.2f} {r['section']:2s} rms {r['mix_rms_db']:6.1f} mid {r['mid_env']:.2f} | "
          f"c1 {r['c1']:5.2f} {PREV} {r[PREV]:5.2f} {CAND} {r[CAND]:5.2f}  Δ{CAND}-c1 {r[f'{CAND}_minus_c1']:+.2f}")
