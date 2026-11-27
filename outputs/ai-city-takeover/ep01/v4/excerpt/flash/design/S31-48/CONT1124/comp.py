#!/usr/bin/env python3
"""comp.py ORIG CAND OUT FEATHER x0 y0 x1 y1 [...]: bounded local composite. Inside the boxes take CAND (resized to
ORIG's size if needed), outside keep ORIG pixel for pixel; box edges feathered by FEATHER px (Gaussian). Prints the
mean |diff| on a 6 px ring just outside each box (seam check) and the sha256 of OUT. Refuses to overwrite OUT."""
import hashlib, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image
o, c, out, f = sys.argv[1], sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]); b = list(map(int, sys.argv[5:]))
if out.exists(): raise SystemExit(f"refusing to overwrite {out}")
A = Image.open(o).convert("RGB"); C = Image.open(c).convert("RGB")
if C.size != A.size: C = C.resize(A.size, Image.LANCZOS)
a = np.asarray(A).astype(np.float32); cc = np.asarray(C).astype(np.float32)
m = np.zeros(a.shape[:2], np.float32)
for i in range(0, len(b), 4):
    x0, y0, x1, y1 = b[i:i + 4]; m[y0:y1, x0:x1] = 1
hard = m.copy()
if f:  # feather inward only (distance to the box edge / FEATHER): outside the boxes stays exactly ORIG
    m = np.clip(cv2.distanceTransform(hard.astype(np.uint8), cv2.DIST_L2, 5) / f, 0, 1).astype(np.float32)
res = a * (1 - m[..., None]) + cc * m[..., None]
ring = (cv2.dilate(hard, np.ones((13, 13), np.uint8)) > 0) & (hard == 0)
seam = float(np.abs(a - cc).mean(-1)[ring].mean()) if ring.any() else 0.0
Image.fromarray(res.round().clip(0, 255).astype(np.uint8)).save(out)
outside = np.asarray(Image.open(out).convert("RGB")).astype(np.int16)[hard == 0] - np.asarray(A).astype(np.int16)[hard == 0]
print(out, "seam_ring_mean_absdiff", round(seam, 2), "outside_identical", bool((outside == 0).all()),
      hashlib.sha256(out.read_bytes()).hexdigest())
