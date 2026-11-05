#!/usr/bin/env python3
"""Net camera drift of a clip: robust similarity transform from frame 0 to later frames (ORB + RANSAC),
reported as scale (%) and shift (px at 1920 wide). Run with the video-analysis venv (OpenCV)."""
import sys
import cv2
import numpy as np

cap = cv2.VideoCapture(sys.argv[1])
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
orb = cv2.ORB_create(4000)
k0, d0 = orb.detectAndCompute(frames[0], None)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
for i in [int(x) for x in sys.argv[2:]] or range(0, len(frames), 24):
    i = min(i, len(frames) - 1)
    k1, d1 = orb.detectAndCompute(frames[i], None)
    m = sorted(bf.match(d0, d1), key=lambda x: x.distance)[:800]
    a = np.float32([k0[x.queryIdx].pt for x in m]); b = np.float32([k1[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    s = float(np.hypot(M[0, 0], M[1, 0]))
    print(f"frame {i:3d}: scale {100 * (s - 1):+.2f}%  shift x {M[0, 2]:+.1f}px y {M[1, 2]:+.1f}px  inliers {int(inl.sum())}/{len(m)}")
