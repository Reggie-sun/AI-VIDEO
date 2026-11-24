#!/usr/bin/env python3
"""Structure at viewing scale (the coordinator's measure, 2026-11-19): each frame to grey, BOX-downscaled to width 240
and 160 (the print screen averages out), 1/24 of each edge cropped off, then mean |grad| / std. EV: 17 frames at 70-94 s
every 1.5 s; ours: 17 frames at render time 3.6-22.8 s every 1.2 s. Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa/grad.py <render.mp4> [<render.mp4> ...] [--out <json>]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

EV = "outputs/anabology-opus55-replica/source/2103533196721704960.mp4"
EV_T = [70 + 1.5 * i for i in range(17)]
OUR_T = [3.6 + 1.2 * i for i in range(17)]
WIDTHS = (240, 160)


def grab(src, t, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", dst], check=True)


def grad(path, width):
    im = Image.open(path).convert("L")
    h = round(im.height * width / im.width)
    a = np.asarray(im.resize((width, h), Image.BOX), np.float64)
    cx, cy = round(width / 24), round(h / 24)
    a = a[cy:h - cy, cx:width - cx]
    gy, gx = np.gradient(a)
    return float(np.hypot(gx, gy).mean() / (a.std() + 1e-9))


def quantiles(path):
    """Luminance quantiles p2 / p10 / p50 / p90 on grey at 480 px wide, 1/24 edges off (the coordinator's measure)."""
    im = Image.open(path).convert("L")
    h = round(im.height * 480 / im.width)
    a = np.asarray(im.resize((480, h), Image.BOX), np.float64)
    a = a[round(h / 24):h - round(h / 24), 20:460]
    return [float(np.percentile(a, q)) for q in (2, 10, 50, 90)]


def sat_warm(path):
    a = np.asarray(Image.open(path).convert("RGB").resize((480, 270), Image.BOX), np.float32) / 255
    mx, mn = a.max(-1), a.min(-1)
    m = mx > 0.1
    return float(((mx - mn) / np.maximum(mx, 1e-3))[m].mean()), float((a[..., 0] - a[..., 2])[m].mean())


def measure(src, times, tag):
    tmp = Path("/tmp/iris-grad"); tmp.mkdir(exist_ok=True)
    rows = []
    for i, t in enumerate(times):
        p = str(tmp / f"{tag}-{i:02d}.png")
        grab(src, t, p)
        s, w = sat_warm(p)
        qs = quantiles(p)
        rows.append({"t": round(t, 3), **{f"grad{wd}": round(grad(p, wd), 4) for wd in WIDTHS}, "sat": round(s, 4), "warm": round(w, 4),
                     **{f"p{q}": round(v, 1) for q, v in zip((2, 10, 50, 90), qs)}})
    med = {k: round(float(np.median([r[k] for r in rows])), 4) for k in rows[0] if k != "t"}
    return {"frames": rows, "median": med}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out in args:
        args.remove(out)
    res = {"ev": measure(EV, EV_T, "ev")}
    for r in args:
        res[Path(r).stem] = measure(r, OUR_T, Path(r).stem)
    for k, v in res.items():
        print(k, v["median"])
    if out:
        Path(out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
