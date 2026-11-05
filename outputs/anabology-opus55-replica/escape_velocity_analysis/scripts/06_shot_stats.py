#!/usr/bin/env python3
"""Stage 6: objective per-shot measurements (palette, luma, camera-motion estimate) + keyframes + filmstrips.

Input : work/shots.json (list of {shot_id,start_frame,end_frame,...}), work/f960/*.jpg
Output: work/shot_stats.json
        keyframes/<shot_id>_f<frame>.jpg   first, 25%, middle, 75%, last (+ extra change frames if listed in shot['key_frames'])
        contactsheets/<shot_id>.jpg        filmstrip, up to 24 evenly spaced frames, 6 columns

Camera motion: Farneback flow on 192x108 gray between frame pairs (central region), dominant similarity
transform by RANSAC. Values are normalised: pan as fraction of frame width/height per second, zoom as
fractional scale change per second (positive = push in / enlarge). They describe the image (including any
2.5D or generated motion), not a physical camera. HUD pixels are static and may bias magnitudes toward 0.

Run: python -I scripts/06_shot_stats.py <analysis_root>
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 24.0


def load(root, i, size=None):
    im = cv2.imread(str(root / "work" / "f960" / f"{i:05d}.jpg"))
    if size:
        im = cv2.resize(im, size, interpolation=cv2.INTER_AREA)
    return im


def palette(root, frames, k=6):
    px = []
    for i in frames:
        im = load(root, i, (96, 54))
        im = im[5:48, 4:92]  # drop HUD bands (top/bottom) and side margins
        px.append(im.reshape(-1, 3))
    px = np.concatenate(px).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, lab, cen = cv2.kmeans(px, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    frac = np.bincount(lab.ravel(), minlength=k) / len(lab)
    order = np.argsort(-frac)
    out = []
    for j in order:
        b, g, r = cen[j].round().astype(int)
        out.append({"hex": f"#{r:02X}{g:02X}{b:02X}", "fraction": round(float(frac[j]), 3), "method": "measured_kmeans"})
    return out


def motion(root, a, b):
    n = b - a + 1
    if n < 3:
        return None
    idx = np.linspace(a, b - 1, min(n - 1, 16)).round().astype(int)
    shifts = []
    for i in idx:
        g0 = cv2.cvtColor(load(root, int(i), (192, 108)), cv2.COLOR_BGR2GRAY)
        g1 = cv2.cvtColor(load(root, int(i) + 1, (192, 108)), cv2.COLOR_BGR2GRAY)
        fl = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        ys, xs = np.mgrid[12:90:6, 16:176:8]
        p0 = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
        d = fl[ys.ravel(), xs.ravel()]
        p1 = p0 + d
        M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=0.6)
        if M is None:
            continue
        s = float(np.hypot(M[0, 0], M[1, 0]))
        cx, cy = 96.0, 54.0
        tx = M[0, 2] + (M[0, 0] - 1) * cx + M[0, 1] * cy
        ty = M[1, 2] + M[1, 0] * cx + (M[1, 1] - 1) * cy
        shifts.append((tx / 192.0, ty / 108.0, s - 1.0, float(np.median(np.hypot(d[:, 0], d[:, 1]))) / 192.0))
    if not shifts:
        return None
    s = np.array(shifts)
    med = np.median(s, 0)
    return {
        "pan_x_frac_per_s": round(float(med[0] * FPS), 4), "pan_y_frac_per_s": round(float(med[1] * FPS), 4),
        "zoom_per_s": round(float(med[2] * FPS), 4), "median_flow_frac_per_s": round(float(med[3] * FPS), 4),
        "pairs_measured": len(shifts),
    }


def filmstrip(root, sid, a, b, outdir, max_tiles=24, cols=6, tw=320):
    n = b - a + 1
    idx = sorted(set(np.linspace(a, b, min(n, max_tiles)).round().astype(int).tolist()))
    th = tw * 9 // 16
    rows = (len(idx) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    for k, i in enumerate(idx):
        im = Image.open(root / "work" / "f960" / f"{i:05d}.jpg").convert("RGB").resize((tw, th), Image.LANCZOS)
        x, y = (k % cols) * tw, (k // cols) * th
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 96, y + 16], fill=(0, 0, 0))
        d.text((x + 3, y + 2), f"{i} {i/24:.2f}s", fill=(255, 235, 60), font=font)
    sheet.save(outdir / f"{sid}.jpg", quality=85)


def main(root):
    root = Path(root)
    shots = json.loads((root / "work" / "shots.json").read_text())
    kdir, cdir = root / "keyframes", root / "contactsheets"
    kdir.mkdir(exist_ok=True)
    cdir.mkdir(exist_ok=True)
    metrics = np.load(root / "work" / "metrics.npz")
    luma = metrics["mean_luma"]
    out = {}
    for s in shots:
        a, b = s["start_frame"], s["end_frame"]
        n = b - a + 1
        picks = sorted(set([a, a + n // 4, a + n // 2, a + (3 * n) // 4, b] + list(s.get("key_frames", []))))
        picks = [p for p in picks if a <= p <= b]
        for p in picks:
            dst = kdir / f"{s['shot_id']}_f{p:05d}.jpg"
            if not dst.exists():
                dst.write_bytes((root / "work" / "f960" / f"{p:05d}.jpg").read_bytes())
        sample = sorted(set(np.linspace(a, b, min(n, 6)).round().astype(int).tolist()))
        pal = palette(root, sample)
        ys = luma[a : b + 1]
        out[s["shot_id"]] = {
            "keyframes": [f"keyframes/{s['shot_id']}_f{p:05d}.jpg" for p in picks],
            "palette": pal,
            "luma_mean_first_mid_last": [round(float(ys[0]), 1), round(float(ys[len(ys) // 2]), 1), round(float(ys[-1]), 1)],
            "luma_p5_p95": [round(float(np.percentile(ys, 5)), 1), round(float(np.percentile(ys, 95)), 1)],
            "motion": motion(root, a, b),
            "contactsheet": f"contactsheets/{s['shot_id']}.jpg",
        }
        filmstrip(root, s["shot_id"], a, b, cdir)
    (root / "work" / "shot_stats.json").write_text(json.dumps(out, indent=1))
    print("shots", len(out))


if __name__ == "__main__":
    main(sys.argv[1])
