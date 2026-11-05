#!/usr/bin/env python3
"""Every-frame mouth close-ups around a lip-sync landmark, for the per-shot gate (it shows, it does not judge).
Run with the video-analysis venv (OpenCV):

  python -I mouth_strip.py <mp4> <out.jpg> --from 2.067 --to 2.633 [--box X,Y,W,H] [--at 2.0]

The clip is conformed to 30 fps CFR with ffmpeg's fps filter (nearest frame, as seq.py does for the film), so the
labels are the clip times the film will show. Without --box the mouth box is placed from the largest Haar face
found in the frame at --at (default --from); it prints the box so later strips can reuse it.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

FPS = 30


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("out")
    ap.add_argument("--from", dest="t0", type=float, required=True)
    ap.add_argument("--to", dest="t1", type=float, required=True)
    ap.add_argument("--box")
    ap.add_argument("--at", type=float)
    a = ap.parse_args()
    first, last = round(a.t0 * FPS), round(a.t1 * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["ffmpeg", "-v", "error", "-i", a.mp4, "-vf", f"fps={FPS}", "-q:v", "2",
                        "-start_number", "0", f"{tmp}/%04d.jpg"], check=True)
        frame = lambda k: cv2.imread(f"{tmp}/{k:04d}.jpg")
        if a.box:
            bx, by, bw, bh = (int(v) for v in a.box.split(","))
        else:
            g = cv2.cvtColor(frame(round((a.at if a.at is not None else a.t0) * FPS)), cv2.COLOR_BGR2GRAY)
            faces = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") \
                .detectMultiScale(g, 1.1, 5, minSize=(150, 150))
            if len(faces) == 0:
                raise SystemExit("no face found; pass --box")
            x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])
            bx, by, bw, bh = x + fw // 5, y + int(fh * 0.62), int(fw * 0.6), int(fh * 0.38)
        print(f"mouth box {bx},{by},{bw},{bh}")
        tiles = []
        for k in range(first, last + 1):
            f = frame(k)
            if f is None:
                break
            c = cv2.resize(f[by:by + bh, bx:bx + bw], (260, int(260 * bh / bw)))
            cv2.putText(c, f"{k / FPS:.3f}", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
            tiles.append(c)
    while len(tiles) % 6:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
    cv2.imwrite(a.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
