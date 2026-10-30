#!/usr/bin/env python3
"""Snap hand-drawn rough polylines onto the light trails of a plate.

Each rough path (plate px, in travel direction) is resampled every `step` px; every sample
moves along its normal to the strongest ridge of the trail map (smoothed redness) within
`radius` px. Samples with no trail nearby are kept but flagged. The result is smoothed and
written as JSON with per-path arc length, plus a check image with direction arrows.

Usage:
  uv run python motion-kit/tools/snap_paths.py --trail work/P3L-red.npy --plate work/P3L-dn.png \
      --rough paths-rough.json --out paths.json --check measure/P3L-paths-check.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def box_blur(a: np.ndarray, k: int) -> np.ndarray:
    pad = np.pad(a, k, mode="edge")
    c = np.cumsum(np.cumsum(pad, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * k + 1
    s = c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]
    return s[: a.shape[0], : a.shape[1]] / (n * n)


def resample(pts: np.ndarray, step: float) -> np.ndarray:
    seg = np.diff(pts, axis=0)
    d = np.concatenate([[0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
    s = np.arange(0, d[-1] + 1e-6, step)
    return np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], 1)


def follow(ridge: np.ndarray, start, dir, max_len=900.0, step=5.0, search=5, lost=0.05, patience=6):
    """Walk along a trail: step forward along the smoothed tangent, re-snap across it."""
    p = np.array(start, dtype=float)
    t = np.array(dir, dtype=float)
    t /= np.hypot(*t)
    pts, misses, walked = [p.copy()], 0, 0.0
    h, w = ridge.shape
    while walked < max_len:
        q = p + t * step
        nrm = np.array([-t[1], t[0]])
        best, bv = q, -1.0
        for o in range(-search, search + 1):
            c = q + nrm * o
            v = sample(ridge, *c) - 0.004 * abs(o)
            if v > bv:
                bv, best = v, c
        misses = misses + 1 if sample(ridge, *best) < lost else 0
        if misses > patience or not (0 <= best[0] < w and 0 <= best[1] < h):
            break
        nt = best - p
        nt /= np.hypot(*nt) + 1e-9
        t = 0.7 * t + 0.3 * nt
        t /= np.hypot(*t)
        p = best
        pts.append(p.copy())
        walked += step
    while misses > 0 and len(pts) > 2:
        pts.pop()
        misses -= 1
    return np.array(pts)


def sample(m: np.ndarray, x: float, y: float) -> float:
    h, w = m.shape
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < w and 0 <= yi < h:
        return float(m[yi, xi])
    return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trail", type=Path, required=True)
    ap.add_argument("--plate", type=Path, required=True)
    ap.add_argument("--rough", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--check", type=Path, required=True)
    ap.add_argument("--step", type=float, default=6.0)
    ap.add_argument("--radius", type=int, default=12)
    args = ap.parse_args()

    red = np.load(args.trail)
    ridge = box_blur(red, 1)
    rough = json.loads(args.rough.read_text())
    out = {"plate": str(args.plate), "units": "plate px", "paths": []}
    for path in rough["paths"]:
        if "follow" in path:
            pts = follow(ridge, **path["follow"])
        else:
            pts = resample(np.array(path["points"], dtype=float), args.step)
        snapped, strength = [], []
        for i, (x, y) in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            t = b - a
            t = t / (np.hypot(*t) + 1e-9)
            nrm = np.array([-t[1], t[0]])
            best, bv = (x, y), -1.0
            for o in range(-args.radius, args.radius + 1):
                px, py = x + nrm[0] * o, y + nrm[1] * o
                v = sample(ridge, px, py) - 0.002 * abs(o)
                if v > bv:
                    bv, best = v, (px, py)
            snapped.append(best)
            strength.append(sample(ridge, *best))
        sp = np.array(snapped)
        k = 3
        sm = sp.copy()
        for i in range(len(sp)):
            sm[i] = sp[max(0, i - k): i + k + 1].mean(0)
        seg = np.diff(sm, axis=0)
        arc = np.concatenate([[0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
        on = [round(float(s), 3) for s in strength]
        out["paths"].append({
            "id": path["id"], "note": path.get("note", ""),
            "points": [[round(float(x), 1), round(float(y), 1)] for x, y in sm],
            "arc": [round(float(a), 1) for a in arc],
            "strength": on,
            "coverage": round(float(np.mean(np.array(on) > 0.06)), 3),
        })
    args.out.write_text(json.dumps(out, indent=1))

    im = Image.open(args.plate).convert("RGB")
    im = Image.eval(im, lambda v: min(255, int(v * 1.6)))
    d = ImageDraw.Draw(im)
    for p in out["paths"]:
        pts = [tuple(q) for q in p["points"]]
        d.line(pts, fill=(0, 255, 120), width=2)
        for j in range(8, len(pts), 18):
            x0, y0 = pts[j - 4]
            x1, y1 = pts[j]
            d.line([(x0, y0), (x1, y1)], fill=(255, 255, 0), width=4)
        d.text((pts[0][0] + 4, pts[0][1] - 14), f"{p['id']} {p['coverage']:.2f}", fill=(255, 255, 255))
    im.save(args.check)
    for p in out["paths"]:
        print(f"{p['id']:4s} n={len(p['points']):3d} len={p['arc'][-1]:7.1f} coverage={p['coverage']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
