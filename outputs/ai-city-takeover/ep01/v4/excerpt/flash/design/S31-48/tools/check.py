#!/usr/bin/env python3
"""Review sheet per candidate: full view, 240 px view, face crops vs opening refs, red-pixel report.

usage: check.py OUTDIR CAND.png [OLD.png]  -> OUTDIR/<shot>-<name>.jpg and prints JSON report
Red rule (same as s015–s030 preview): R dominant, G<0.5R, B<0.55R, saturation>0.5, R>90.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

V4 = Path("/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/v4")
REFS = [V4 / "excerpt/flash/design/S15-30/refs/face-P016b.png", V4 / "excerpt/flash/design/S15-30/refs/face-F1a.png"]
CASC = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in
        ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")]


def red_mask(a):
    """Strict rule OR loose hue rule (catches pink/salmon lit lines): hue within 15 deg of red, S>0.35, V>0.35."""
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV_FULL).astype(np.int32)
    hh, ss, vv = hsv[..., 0] * 360 // 256, hsv[..., 1], hsv[..., 2]
    loose = ((hh <= 15) | (hh >= 345)) & (ss > 90) & (vv > 90)
    return strict_red(a) | loose


def strict_red(a):
    a = a.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    return (r > 90) & (r == mx) & (g < 0.5 * r) & (b < 0.55 * r) & (sat > 0.5)


def faces(im):
    g = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY)
    out = []
    for c in CASC:
        for (x, y, w, h) in c.detectMultiScale(g, 1.1, 6, minSize=(40, 40)):
            out.append((int(x), int(y), int(w), int(h)))
        for (x, y, w, h) in c.detectMultiScale(cv2.flip(g, 1), 1.1, 6, minSize=(40, 40)):
            out.append((int(g.shape[1] - x - w), int(y), int(w), int(h)))
    out.sort(key=lambda f: -f[2] * f[3])
    keep = []
    for f in out:
        if all(abs(f[0] - k[0]) > k[2] * 0.5 or abs(f[1] - k[1]) > k[3] * 0.5 for k in keep):
            keep.append(f)
    return keep[:3]


def main():
    outdir = Path(sys.argv[1]); outdir.mkdir(parents=True, exist_ok=True)
    cand = Path(sys.argv[2]); old = Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    im = Image.open(cand).convert("RGB")
    a = np.asarray(im)
    m = red_mask(a)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    blobs = sorted([(int(s[4]), int(s[0]), int(s[1]), int(s[2]), int(s[3])) for s in stats[1:]], reverse=True)
    fs = faces(im)
    # sheet
    W = 1400; s = W / im.width
    big = im.resize((W, int(im.height * s)), Image.LANCZOS)
    dr = ImageDraw.Draw(big)
    for (area, x, y, w, h) in blobs[:12]:
        if area >= 4:
            dr.rectangle([x * s - 6, y * s - 6, (x + w) * s + 6, (y + h) * s + 6], outline=(0, 255, 255), width=2)
    for (x, y, w, h) in fs:
        dr.rectangle([x * s, y * s, (x + w) * s, (y + h) * s], outline=(255, 255, 0), width=1)
    small = im.resize((240, int(im.height * 240 / im.width)), Image.BOX)
    tiles = [small]
    TH = 260
    for (x, y, w, h) in fs[:2]:
        p = int(0.45 * w)
        c = im.crop((max(0, x - p), max(0, y - p), min(im.width, x + w + p), min(im.height, y + h + p)))
        tiles.append(c.resize((int(c.width * TH / c.height), TH), Image.LANCZOS))
    for r in REFS:
        c = Image.open(r).convert("RGB"); tiles.append(c.resize((int(c.width * TH / c.height), TH), Image.LANCZOS))
    if old:
        o = Image.open(old).convert("RGB")
        tiles.append(o.resize((int(o.width * TH / o.height), TH), Image.LANCZOS))
    rowW = sum(t.width for t in tiles) + 8 * len(tiles)
    sheet = Image.new("RGB", (max(W, rowW), big.height + TH + 8), (20, 20, 20))
    sheet.paste(big, (0, 0)); x = 0
    for t in tiles:
        sheet.paste(t, (x, big.height + 8)); x += t.width + 8
    name = f"{cand.parent.name}-{cand.stem}"
    sheet.save(outdir / f"{name}.jpg", quality=90)
    # red crops
    rc = []
    for i, (area, x, y, w, h) in enumerate(blobs[:6]):
        if area < 4:
            continue
        p = 40
        c = im.crop((max(0, x - p), max(0, y - p), min(im.width, x + w + p), min(im.height, y + h + p)))
        c = c.resize((c.width * 3, c.height * 3), Image.NEAREST)
        rc.append(c)
    if rc:
        RW = sum(c.width for c in rc) + 8 * len(rc); RH = max(c.height for c in rc)
        rs = Image.new("RGB", (RW, RH), (20, 20, 20)); x = 0
        for c in rc:
            rs.paste(c, (x, 0)); x += c.width + 8
        rs.save(outdir / f"{name}-red.jpg", quality=90)
    rep = {"file": str(cand), "size": im.size, "red_px": int(m.sum()),
           "red_blobs": [{"area": b[0], "xywh": b[1:]} for b in blobs[:6] if b[0] >= 4],
           "faces": fs}
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
