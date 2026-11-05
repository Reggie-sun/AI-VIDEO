#!/usr/bin/env python3
"""Stage 4 (v2): halftone dot pitch over time. Full-frame FFT, every 24th frame (1 Hz), full-res gray.

For each sampled frame: Hann-windowed 2D FFT of the 1920x1080 gray frame. A square dot screen puts energy on the kx axis (ky~0) at
multiples of 1920/pitch and on the ky axis (kx~0) at multiples of 1080/pitch. We take the strongest local peak (prominence vs the
local median) on each axis in the 3..16 px pitch band and report pitch_x, pitch_y, and a visibility score (peak / local median).
A diagonal-screen check is made by also scanning the 45-degree diagonal (pitch*sqrt(2) rotated screens).
Run: python -I scripts/04_halftone_pitch.py <analysis_root> <video>
Output: halftone_pitch.json
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H, STEP = 1920, 1080, 24


def analyse(g):
    g = g.astype(np.float32)
    g -= g.mean()
    win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
    F = np.abs(np.fft.rfft2(g * win))  # H x (W/2+1)
    # kx axis: rows ky in [0..2], columns kx
    ax = F[0:3, :].max(0)
    ay = F[:, 0:3].max(1)[: H // 2]

    def best(arr, n, lo_p=3.0, hi_p=16.0):
        ks = np.arange(len(arr))
        lo, hi = int(n / hi_p), int(n / lo_p)
        seg = arr[lo:hi]
        k = int(np.argmax(seg)) + lo
        # local median prominence
        a, b = max(0, k - 30), min(len(arr), k + 30)
        med = float(np.median(arr[a:b])) + 1e-6
        return n / k, float(arr[k] / med)

    px, vx = best(ax, W)
    py, vy = best(ay, H)
    # diagonal: sample F along kx == ky line (rotated screen)
    d = np.array([F[min(k, F.shape[0] - 1), min(k, F.shape[1] - 1)] for k in range(0, 540)])
    kd = int(np.argmax(d[30:300])) + 30
    med = float(np.median(d[max(0, kd - 30) : kd + 30])) + 1e-6
    return px, vx, py, vy, float(d[kd] / med), kd


def main(root, video):
    root = Path(root)
    cmd = ["ffmpeg", "-v", "error", "-i", video, "-an", "-vsync", "0", "-vf", f"select=not(mod(n\\,{STEP})),format=gray", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, i = [], 0
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H:
            break
        g = np.frombuffer(b, np.uint8).reshape(H, W)
        px, vx, py, vy, vd, kd = analyse(g)
        out.append({"frame": i * STEP, "t": round(i * STEP / 24, 2), "pitch_x_px": round(px, 2), "vis_x": round(vx, 1), "pitch_y_px": round(py, 2), "vis_y": round(vy, 1), "diag_vis": round(vd, 1)})
        i += 1
    p.wait()
    meta = {"schema": "ev-halftone-pitch/v2", "method": "full-frame Hann FFT, axis peaks in 3-16 px pitch band, prominence = peak/local median; vis >= ~8 means a clearly visible regular dot screen", "step_frames": STEP, "samples": out}
    (root / "halftone_pitch.json").write_text(json.dumps(meta, indent=1))
    print(len(out), out[:2], out[-2:])


if __name__ == "__main__":
    main(*sys.argv[1:3])
