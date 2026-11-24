#!/usr/bin/env python3
"""The texture numbers for the review page (qa/v4r3/texture.json): qa/texture.py on 13 EV frames (70-94 s, every 2 s)
and on 12 frames of the v4r2 and v4r3 renders at the same frame numbers, plus the same-box crop compare
(qa/crop_compare.py -> review/compare3/crop-compare-v4r3.png). Run from the repository root after the v4r3 render."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texture import measure, summary  # noqa: E402

EXC = Path(__file__).resolve().parents[1]
EV = "outputs/anabology-opus55-replica/source/2103533196721704960.mp4"
FRAMES = [85, 100, 120, 140, 160, 190, 215, 240, 262, 290, 320, 345]


def frames(src: str, tag: str) -> list[str]:
    out = []
    for f in FRAMES:
        p = f"/tmp/iris-tex-{tag}-{f}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"select=eq(n\\,{f})", "-vsync", "0", "-frames:v", "1", p], check=True)
        out.append(p)
    return out


TAGS = sys.argv[1:] or ["v4r2", "v4r3"]            # the last one is the version reported (qa/<last>/texture.json)


def main() -> int:
    ev = []
    for t in range(70, 95, 2):
        p = f"/tmp/iris-tex-ev-{t}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", EV, "-frames:v", "1", p], check=True)
        ev.append(p)
    res = {"ev": {"summary": summary([measure(p) for p in ev])}}
    for tag in TAGS:
        res[tag] = {"summary": summary([measure(p) for p in frames(str(EXC / f"renders/IRIS-EP01-v4-excerpt-{tag}-036-051.mp4"), tag)])}
    crops = {}
    for tag in TAGS:
        out = str(EXC / f"review/compare3/crop-compare-{tag}.png") if tag != "v4r2" else "/tmp/iris-cc-v4r2.png"
        r = subprocess.run([sys.executable, str(EXC / "qa/crop_compare.py"), str(EXC / f"renders/IRIS-EP01-v4-excerpt-{tag}-036-051.mp4"), out],
                           capture_output=True, text=True, check=True)
        t = json.loads(r.stdout)
        crops["ev"], crops[tag] = t["ev"], t["ours"]
    res["crops"] = {k: [{kk: v[kk] for kk in ("crisp", "sat", "warm")} for v in rows] for k, rows in crops.items()}
    # acceptance (coordinator 2026-11-19): sharpness (lap: Laplacian variance after the sigma-2 low-pass that removes the
    # screen), saturation and warmth, full-frame medians, within +-20% of EV's
    last = TAGS[-1]
    gate = {}
    for key in ("lap", "sat", "warm", "crisp", "screen_prominence"):
        e, o = res["ev"]["summary"][key]["median"], res[last]["summary"][key]["median"]
        gate[key] = {"ev": e, "ours": o, "ratio": round(o / e, 3), "within_20pct": abs(o / e - 1) <= 0.2}
    res["gate"] = gate
    (EXC / f"qa/{last}/texture.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(gate, indent=1))
    print(json.dumps({k: (v["summary"] if "summary" in v else None) for k, v in res.items() if k != "crops"}, indent=1)[:3000])
    print(json.dumps(res["crops"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
