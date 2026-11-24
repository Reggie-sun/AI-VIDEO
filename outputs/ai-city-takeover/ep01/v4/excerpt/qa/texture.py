#!/usr/bin/env python3
"""Picture texture, measured the same way on EV and on ours (2026-11-19; the user: the author's picture is soft, ours
too crisp). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa/texture.py --ev <png...> --ours <png...> [--out <json>]

Per frame (1920x1080, grey = Rec.709 luma of sRGB values):
(a) the print screen, as escape_velocity_analysis/halftone_pitch.json measured it: a full-frame Hann-windowed FFT; the
    spectrum along each axis (|F| over the three rows/columns nearest the axis) in the 3-16 px pitch band; the peak's
    pitch and its prominence = peak / median of the profile within +-20 bins (vis_x, vis_y), and the same along the two
    diagonals (diag_vis, the larger). vis >= ~8 is a clearly visible regular screen. Also the strongest 2-D peak in the
    band (its pitch, angle and prominence against the median of its ring): the screen's real geometry.
(b) the base image's sharpness: `fine`, the mean energy per bin at 0.10-0.22 cyc/px (hair strands, crisp edges)
    with the screen's spikes and their sidebands notched out (0.05 cyc/px discs), over the mean per bin at 0.01-0.10
    cyc/px (x1000 in the summary); and with the screen taken out: the spectrum's energy in 0.04-0.10 cyc/px over 0.01-0.10
    cyc/px (both below the 0.24 cyc/px screen), `detail`; and the Laplacian variance over the luma variance after a
    Gaussian low-pass of sigma 2.0 px (which removes the 4.2 px screen), `lap`.
    `crisp` = var(G2 - G4) / var(G4 - G8) on Gaussian-blurred luma (sigma 2, 4, 8 px): the base's sharpness at the
    2-4 px scale with the screen and the grain already gone (the measure the grade is matched on).
    `sharp`: the base's fine detail measured where a line screen puts no energy - a +-20 deg wedge of the spectrum
    perpendicular to EV's screen frequency, energy per bin at 0.12-0.30 over 0.02-0.06 cyc/px, x1000. The acceptance
    measure (EV's screen is not a pure line screen; this still sees part of it).
    `edge_sigma`: the base's blur in px at 1080p from the width of its strongest edges after a sigma-2 low-pass (the
    acceptance measure for "too crisp"; see the code).
(c) colour: mean HSV saturation and mean (R - B) / 255 over pixels with V > 0.1 (`sat`, `warm`).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


# EV's line screen frequency (cyc/px, image x right / y down), read off the 2-D peak of EV frames 78-94 s (pitch 4.0 px)
SCREEN_F = (0.2375, -0.0778)


def luma(a: np.ndarray) -> np.ndarray:
    return a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def spectrum(g: np.ndarray) -> np.ndarray:
    h, w = g.shape
    win = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    F = np.fft.fftshift(np.fft.fft2((g - g.mean()) * win))
    return np.abs(F)


def axis_peak(prof: np.ndarray, freqs: np.ndarray) -> tuple[float, float]:
    band = (freqs >= 1 / 16) & (freqs <= 1 / 3)
    best = (0.0, 0.0)
    idx = np.nonzero(band)[0]
    for i in idx:
        lo, hi = max(0, i - 20), min(len(prof), i + 21)
        med = float(np.median(prof[lo:hi])) + 1e-9
        r = float(prof[i]) / med
        if r > best[0]:
            best = (r, 1 / freqs[i])
    return round(best[1], 2), round(best[0], 1)


def measure(path: Path) -> dict:
    """path, or 'path@x,y,w,h' for a crop of the 1920x1080 frame (the same-box crop compare)."""
    spec = str(path)
    box = None
    if "@" in spec:
        spec, b = spec.split("@")
        box = [int(v) for v in b.split(",")]
    im = Image.open(spec).convert("RGB").resize((1920, 1080))
    if box:
        im = im.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
    a = np.asarray(im, np.float32) / 255
    g = luma(a)
    S = spectrum(g)
    h, w = S.shape
    cy, cx = h // 2, w // 2
    fx = np.arange(w // 2) / w
    fy = np.arange(h // 2) / h
    px = S[cy - 1:cy + 2, cx:cx + w // 2].mean(0)
    py = S[cy:cy + h // 2, cx - 1:cx + 2].mean(1)
    pitch_x, vis_x = axis_peak(px, fx)
    pitch_y, vis_y = axis_peak(py, fy)
    # diagonals: sample |F| along (k, +-k*h/w scaled to equal cyc/px)
    diag = []
    for sgn in (1, -1):
        # equal cyc/px on both axes: (kx / w, ky / h) with ky = kx * h / w; the frequency along the diagonal is sqrt(2) kx / w
        prof = np.array([S[cy + sgn * int(round(k * h / w)), cx + k] for k in range(int(w // 2 * 0.95))])
        diag.append(axis_peak(prof, np.arange(len(prof)) * math.sqrt(2) / w)[1])
    # 2-D peak in the band
    yy, xx = np.mgrid[-cy:h - cy, -cx:w - cx]
    f2 = np.hypot(xx / w, yy / h)
    ring = (f2 >= 1 / 16) & (f2 <= 1 / 3) & (yy >= 0)
    Sb = np.where(ring, S, 0)
    j = int(np.argmax(Sb))
    py2, px2 = np.unravel_index(j, S.shape)
    fpk = f2[py2, px2]
    shell = ring & (np.abs(f2 - fpk) < 0.004)
    peak2 = {"pitch_px": round(1 / fpk, 2), "angle_deg": round(math.degrees(math.atan2(-(py2 - cy) / h, (px2 - cx) / w)), 1),
             "prominence": round(float(S[py2, px2] / (np.median(S[shell]) + 1e-9)), 1)}
    # (b) sharpness of the base
    E = S ** 2
    e_hi = E[(f2 >= 0.04) & (f2 <= 0.10)].sum()
    e_all = E[(f2 >= 0.01) & (f2 <= 0.10)].sum()
    # fine detail (hair strands, crisp edges) in 0.10-0.22 cyc/px, the print screen taken out: every spike above 15x the
    # band's median (the screen's peaks, its harmonics, both halves) is notched with a 0.05 cyc/px disc, which also
    # takes the sidebands the picture modulates onto the screen; over 0.01-0.10 cyc/px
    band = (f2 >= 0.08) & (f2 <= 0.35)
    med = float(np.median(S[band]))
    spikes = band & (S > 15 * med)
    ys, xs = np.nonzero(spikes)
    order = np.argsort(-S[ys, xs])[:400]
    notch = np.zeros_like(band)
    kept = []
    for i in order:
        fy_, fx_ = (ys[i] - cy) / h, (xs[i] - cx) / w
        if any(abs(fy_ - a) < 0.02 and abs(fx_ - b) < 0.02 for a, b in kept):
            continue
        kept.append((fy_, fx_))
        for sg in (1, -1):
            notch |= np.hypot(xx / w - sg * fx_, yy / h - sg * fy_) < 0.05
        if len(kept) >= 12:
            break
    fine_band = (f2 >= 0.10) & (f2 <= 0.22) & ~notch
    fine = float(E[fine_band].sum() / max(fine_band.sum(), 1) / (E[(f2 >= 0.01) & (f2 <= 0.10)].sum() / max(((f2 >= 0.01) & (f2 <= 0.10)).sum(), 1)))
    gl = np.asarray(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)), np.float32) / 255
    lap = gl[1:-1, 1:-1] * -4 + gl[:-2, 1:-1] + gl[2:, 1:-1] + gl[1:-1, :-2] + gl[1:-1, 2:]
    # base sharpness as a band ratio of a Gaussian scale space, free of the screen and the grain (sigma 2 removes the
    # 4 px screen): var(G2 - G4) / var(G4 - G8). A softer base (a low-res photo upscaled) has less between 2 and 4 px.
    def gb(sig):
        return np.asarray(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sig)), np.float32) / 255
    G2, G4, G8 = gb(2.0), gb(4.0), gb(8.0)
    crisp = float((G2 - G4).var() / max((G4 - G8).var(), 1e-9))
    # base sharpness free of the print screen: a line screen has no energy along its own lines, so measure the spectrum
    # in a +-20 deg wedge perpendicular to the screen's frequency (EV's, fixed: SCREEN_F), mean energy per bin at
    # 0.12-0.30 cyc/px over the mean per bin at 0.02-0.06 cyc/px, x1000 (`sharp`; grain counts, as it reads as crisp)
    ux, uy = -SCREEN_F[1], SCREEN_F[0]
    n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    fxg, fyg = xx / w, yy / h
    cosang = np.abs(fxg * ux + fyg * uy) / np.maximum(f2, 1e-9)
    wedge = cosang > math.cos(math.radians(20))
    hi = wedge & (f2 >= 0.12) & (f2 <= 0.30)
    lo = wedge & (f2 >= 0.02) & (f2 <= 0.06)
    sharp = float(E[hi].mean() / max(E[lo].mean(), 1e-12) * 1000)
    # `soft`: the base's detail below the screen, mean energy per bin at 0.10-0.16 cyc/px over 0.02-0.06 cyc/px, x1000,
    # everywhere except +-0.03 cyc/px round any spike; both sides carry the same kind of screen, so its sidebands count
    # alike. A low-res photo upscaled (EV) has little here; crisp 4K detail (hair, chain) has a lot. The acceptance measure.
    mband = (f2 >= 0.10) & (f2 <= 0.16)
    lband = (f2 >= 0.02) & (f2 <= 0.06)
    spike = (f2 >= 0.06) & (S > 25 * np.median(S[(f2 >= 0.06) & (f2 <= 0.35)]))
    sy_, sx_ = np.nonzero(spike)
    kill = np.zeros_like(spike)
    for y, x in list(zip(sy_, sx_))[:60]:
        kill |= np.hypot((xx - (x - cx)) / w, (yy - (y - cy)) / h) < 0.03
    soft = float(E[mband & ~kill].mean() / max(E[lband].mean(), 1e-12) * 1000)
    # the base's blur as an edge width, screen-proof: on luma blurred with sigma 2 px (which takes the 4 px screen and
    # the grain out), the strongest edges (local gradient maxima in the top 1.5% inside the frame's middle, away from
    # the interface rows) are read as blurred steps: total sigma = contrast / (max gradient * sqrt(2 pi)) with the
    # contrast taken +-8 px across the edge; the base's own sigma = sqrt(total^2 - 2^2). `edge_sigma` (px at 1080p) is
    # their median: the bigger, the softer the picture under the screen.
    gy_, gx_ = np.gradient(G2)
    gm = np.hypot(gx_, gy_)
    H_, W_ = gm.shape
    mid = np.zeros_like(gm, bool)
    mid[int(0.14 * H_):int(0.86 * H_), int(0.06 * W_):int(0.94 * W_)] = True
    mx = np.asarray(Image.fromarray(np.clip(gm / (gm.max() + 1e-9) * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), np.float32) / 255 * (gm.max() + 1e-9)
    cand = mid & (gm >= mx - 1e-6) & (gm > np.percentile(gm[mid], 98.5))
    ys, xs = np.nonzero(cand)
    sig = []
    for y, x in zip(ys[:4000], xs[:4000]):
        ux_, uy_ = gx_[y, x] / gm[y, x], gy_[y, x] / gm[y, x]
        x1, y1, x0, y0 = int(round(x + 8 * ux_)), int(round(y + 8 * uy_)), int(round(x - 8 * ux_)), int(round(y - 8 * uy_))
        if not (0 <= x0 < W_ and 0 <= x1 < W_ and 0 <= y0 < H_ and 0 <= y1 < H_):
            continue
        C = abs(G2[y1, x1] - G2[y0, x0])
        st = C / (gm[y, x] * math.sqrt(2 * math.pi))
        if C > 0.06:
            sig.append(math.sqrt(max(st * st - 4.0, 0.0)))
    edge_sigma = float(np.median(sig)) if sig else float("nan")
    # (c) colour
    mx, mn = a.max(-1), a.min(-1)
    m = mx > 0.1
    sat = float(((mx - mn) / np.maximum(mx, 1e-3))[m].mean())
    warm = float((a[..., 0] - a[..., 2])[m].mean())
    return {"frame": str(path), "pitch_x": pitch_x, "vis_x": vis_x, "pitch_y": pitch_y, "vis_y": vis_y, "diag_vis": max(diag),
            "peak2d": peak2, "detail": round(float(e_hi / max(e_all, 1e-9)), 4), "fine": round(fine * 1000, 3), "crisp": round(crisp, 4), "sharp": round(sharp, 4), "edge_sigma": round(edge_sigma, 3), "soft": round(soft, 4),
            "lap": round(float(lap.var() / max(gl.var(), 1e-9) * 1000), 3), "sat": round(sat, 3), "warm": round(warm, 3)}


def summary(rows: list[dict]) -> dict:
    keys = ["vis_x", "vis_y", "diag_vis", "detail", "fine", "crisp", "sharp", "edge_sigma", "soft", "lap", "sat", "warm"]
    out = {}
    for k in keys:
        v = np.array([r[k] for r in rows], float)
        out[k] = {"median": round(float(np.median(v)), 4), "p10": round(float(np.percentile(v, 10)), 4), "p90": round(float(np.percentile(v, 90)), 4)}
    out["pitch_x"] = {"median": float(np.median([r["pitch_x"] for r in rows]))}
    out["peak2d_pitch"] = {"median": float(np.median([r["peak2d"]["pitch_px"] for r in rows]))}
    pr = np.array([r["peak2d"]["prominence"] for r in rows], float)
    out["screen_prominence"] = {"median": round(float(np.median(pr)), 1), "p10": round(float(np.percentile(pr, 10)), 1), "p90": round(float(np.percentile(pr, 90)), 1)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ev", nargs="*", default=[])
    ap.add_argument("--ours", nargs="*", default=[])
    ap.add_argument("--out")
    a = ap.parse_args()
    res = {}
    for name, files in (("ev", a.ev), ("ours", a.ours)):
        if files:
            rows = [measure(f) for f in files]
            res[name] = {"frames": rows, "summary": summary(rows)}
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v["summary"] for k, v in res.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
