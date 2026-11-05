#!/usr/bin/env python3
"""Stage 2: frame-difference metrics + cut / gradual-transition candidates.

Input : work/lowres_rgb.npy (from stage 1)
Output: work/metrics.npz  (per-frame metrics)
        work/cut_candidates.json (hard cut + gradual candidates with scores)

Metric i describes the step between frame i and frame i+1; a cut "at i+1" means
frame i+1 is the first frame of the new shot.

Run: python -I scripts/02_cut_candidates.py <analysis_root>
"""
import json
import sys
from pathlib import Path

import numpy as np


def box_down(a, f):
    n, h, w, c = a.shape
    h2, w2 = h // f, w // f
    return a[:, : h2 * f, : w2 * f].reshape(n, h2, f, w2, f, c).mean((2, 4))


def main(root):
    root = Path(root)
    a = np.load(root / "work" / "lowres_rgb.npy", mmap_mode="r")
    n = a.shape[0]
    lo = np.empty((n, 27, 48, 3), np.float32)  # 4x box down kills halftone/grain
    for s in range(0, n, 500):
        lo[s : s + 500] = box_down(np.asarray(a[s : s + 500], np.float32), 4)
    g = lo.mean(-1)
    d_lo = np.abs(np.diff(g, axis=0)).mean((1, 2))  # n-1
    d_col = np.abs(np.diff(lo, axis=0)).mean((1, 2, 3))
    # color histogram (3 x 16 bins) on 4x-down frames
    q = (lo // 16).clip(0, 15).astype(np.int32)
    hist = np.zeros((n, 48), np.float32)
    for ch in range(3):
        for b in range(16):
            hist[:, ch * 16 + b] = (q[..., ch] == b).mean((1, 2))
    d_hist = np.abs(np.diff(hist, axis=0)).sum(1)
    # gradual: distance between frame i and i+k
    gradual = {}
    for k in (6, 12):
        gradual[k] = np.abs(g[k:] - g[:-k]).mean((1, 2))
    # structural change (edges): sobel magnitude correlation drop
    gx = np.abs(np.diff(g, axis=2))[:, :-1, :]
    gy = np.abs(np.diff(g, axis=1))[:, :, :-1]
    edge = gx + gy
    ef = edge.reshape(n, -1)
    ef = ef - ef.mean(1, keepdims=True)
    nrm = np.linalg.norm(ef, axis=1) + 1e-6
    ecorr = (ef[:-1] * ef[1:]).sum(1) / (nrm[:-1] * nrm[1:])  # n-1, 1=same structure
    np.savez(
        root / "work" / "metrics.npz",
        d_lo=d_lo, d_col=d_col, d_hist=d_hist, ecorr=ecorr,
        g6=gradual[6], g12=gradual[12], mean_luma=g.mean((1, 2)),
    )

    # local-contrast score
    def local_ratio(x, half=12):
        out = np.zeros_like(x)
        for i in range(len(x)):
            lo_i, hi_i = max(0, i - half), min(len(x), i + half + 1)
            w = np.concatenate([x[lo_i:i], x[i + 1 : hi_i]])
            out[i] = x[i] / (np.median(w) + 0.75)
        return out

    r = local_ratio(d_lo)
    rh = local_ratio(d_hist * 100)
    cand = []
    for i in range(len(d_lo)):
        score = max(r[i], rh[i] * 0.8) * (1 - 0.5 * max(0.0, ecorr[i]))
        if (d_lo[i] > 7 and r[i] > 3.0) or (d_hist[i] > 0.35 and rh[i] > 3.0) or ecorr[i] < 0.2 and d_lo[i] > 5:
            cand.append(
                dict(
                    first_frame_of_new=i + 1, d_lo=float(d_lo[i]), d_col=float(d_col[i]),
                    d_hist=float(d_hist[i]), ecorr=float(ecorr[i]),
                    ratio_lo=float(r[i]), ratio_hist=float(rh[i]), score=float(score),
                )
            )
    (root / "work" / "cut_candidates.json").write_text(json.dumps(cand, indent=1))
    print("frames", n, "candidates", len(cand))
    print("d_lo percentiles", np.percentile(d_lo, [50, 90, 99, 99.9]).round(2))


if __name__ == "__main__":
    main(sys.argv[1])
