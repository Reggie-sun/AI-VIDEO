#!/usr/bin/env python3
"""Stage 3: group frame-level metric spikes into 'disturbances' (over-detecting on purpose).

A disturbance is a run of consecutive frame steps where the picture changed more than
the noise floor. Each one is later classified by a human/agent look: hard cut, flash,
wipe, dissolve, whip, or an in-shot graphic change that is NOT a shot boundary.

Input : work/metrics.npz
Output: work/disturbances.json  list of
  {dist_id, first_step, last_step, peak_step, first_frame_after (= peak_step+1),
   n_steps, max_d_lo, min_ecorr, max_d_hist, luma_before, luma_after, luma_peak,
   auto_class, chunk}
Step i = change between frame i and i+1.

Run: python -I scripts/03_disturbances.py <analysis_root>
"""
import json
import sys
from pathlib import Path

import numpy as np

N_CHUNKS = 5


def main(root):
    root = Path(root)
    m = np.load(root / "work" / "metrics.npz")
    d, e, h, luma = m["d_lo"], m["ecorr"], m["d_hist"], m["mean_luma"]
    n = len(luma)
    hot = (d > 6) | (h > 0.30) | ((e < 0.6) & (d > 3))
    runs, i = [], 0
    while i < len(hot):
        if hot[i]:
            j = i
            while j + 1 < len(hot) and (hot[j + 1] or (j + 2 < len(hot) and hot[j + 2])):
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    out = []
    chunk_len = int(np.ceil(n / N_CHUNKS))
    for k, (a, b) in enumerate(runs):
        peak = a + int(np.argmax(d[a : b + 1]))
        lb = float(luma[max(a - 1, 0)])
        la = float(luma[min(b + 2, n - 1)])
        lp = float(luma[a : b + 2].max())
        n_steps = b - a + 1
        structural = float(e[a : b + 1].min()) < 0.45 and float(d[a : b + 1].max()) > 10
        if n_steps == 1 and structural:
            auto = "hard_cut"
        elif structural and n_steps <= 3:
            auto = "hard_cut_burst"
        elif lp - max(lb, la) > 35 and n_steps <= 4:
            auto = "flash"
        elif n_steps >= 4 and structural:
            auto = "wipe_or_fast_motion"
        elif n_steps >= 4:
            auto = "gradual_or_motion"
        else:
            auto = "minor_change"
        out.append(
            dict(
                dist_id=f"D{k+1:04d}", first_step=a, last_step=b, peak_step=peak,
                first_frame_after=peak + 1, n_steps=n_steps,
                max_d_lo=round(float(d[a : b + 1].max()), 2),
                min_ecorr=round(float(e[a : b + 1].min()), 3),
                max_d_hist=round(float(h[a : b + 1].max()), 3),
                luma_before=round(lb, 1), luma_after=round(la, 1), luma_peak=round(lp, 1),
                auto_class=auto, chunk=int(peak // chunk_len),
            )
        )
    (root / "work" / "disturbances.json").write_text(json.dumps(out, indent=1))
    from collections import Counter

    print("disturbances", len(out), dict(Counter(o["auto_class"] for o in out)))
    print("per chunk", dict(Counter(o["chunk"] for o in out)), "chunk_len", chunk_len)


if __name__ == "__main__":
    main(sys.argv[1])
