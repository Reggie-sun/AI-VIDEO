#!/usr/bin/env python3
"""Frame evidence for a lip-sync gate (S8a/S8b): what a reviewer needs to judge the mouth against the master vocal.
Run with the video-analysis venv (OpenCV + librosa). It prepares evidence; the verdict is the reviewer's.

  python -I lipsync_review.py <mp4> <reference.wav> <out-dir> --mouth X,Y,W,H --onsets 0.00,0.65,... [--zero 18.60]

- mouth-timeline.jpg: every 2nd frame at 30 fps CFR, mouth crop with two level bars: the clip's own audio
  (orange, left) and the sealed reference vocal (blue, right).
- onsets.jpg: the 11 frames around each sealed onset (clip seconds), with the reference level per frame.
- dtw.json: where each reference time lands in the clip's own audio (MFCC DTW), i.e. how the model re-timed its
  own singing; the mouth may follow either track, which the frames decide.
"""
import argparse
import json
import subprocess
from pathlib import Path

import cv2
import librosa
import numpy as np

SR, FPS = 16000, 30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4"); ap.add_argument("reference"); ap.add_argument("out")
    ap.add_argument("--mouth", required=True, help="crop X,Y,W,H in 1920x1080 px around mouth and chin")
    ap.add_argument("--onsets", required=True)
    ap.add_argument("--zero", type=float, default=0.0, help="master seconds at clip t=0 (labels only)")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    x, y, w, h = (int(v) for v in a.mouth.split(","))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.mp4, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 1080, 1920, 3)
    rawa = subprocess.run(["ffmpeg", "-v", "error", "-i", a.mp4, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                          capture_output=True, check=True).stdout
    clip = np.frombuffer(rawa, np.float32)
    ref, _ = librosa.load(a.reference, sr=SR, mono=True)
    hop = SR // FPS

    def level(sig):
        r = librosa.feature.rms(y=sig, frame_length=2 * hop, hop_length=hop)[0]
        return 20 * np.log10(r / r.max() + 1e-9)
    ec, er = level(clip), level(ref)
    bar = lambda v, x0, wd: int(max(0.0, (v + 40) / 40) * wd)

    tiles = []
    for i in range(0, len(fr), 2):
        im = cv2.resize(fr[i][y:y + h, x:x + w], (150, int(150 * h / w)))
        b = np.zeros((30, 150, 3), np.uint8)
        cv2.rectangle(b, (0, 0), (bar(ec[i] if i < len(ec) else -80, 0, 74), 11), (0, 200, 255), -1)
        cv2.rectangle(b, (76, 0), (76 + bar(er[i] if i < len(er) else -80, 0, 74), 11), (255, 160, 0), -1)
        cv2.putText(b, f"{i / FPS:.2f}", (2, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        tiles.append(np.vstack([im, b]))
    rows = [np.hstack(tiles[r:r + 13] + [np.zeros_like(tiles[0])] * (13 - len(tiles[r:r + 13]))) for r in range(0, len(tiles), 13)]
    cv2.imwrite(str(out / "mouth-timeline.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])

    rows = []
    for t in (float(v) for v in a.onsets.split(",")):
        c = int(round(t * FPS)); strip = []
        for i in range(max(0, c - 5), min(len(fr), c + 6)):
            im = cv2.resize(fr[i][y:y + h, x:x + w], (156, int(156 * h / w)))
            b = np.zeros((24, 156, 3), np.uint8)
            cv2.rectangle(b, (0, 0), (bar(er[i] if i < len(er) else -80, 0, 156), 8), (255, 160, 0), -1)
            cv2.putText(b, f"{i / FPS:.3f}{' *' if i == c else ''}", (2, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
            strip.append(np.vstack([im, b]))
        label = np.zeros((20, 156 * len(strip), 3), np.uint8)
        cv2.putText(label, f"onset clip {t:.2f} s = master {a.zero + t:.2f} s", (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        rows.append(np.vstack([label, np.hstack(strip)]))
    wmax = max(r.shape[1] for r in rows)
    cv2.imwrite(str(out / "onsets.jpg"), np.vstack([np.pad(r, ((0, 0), (0, wmax - r.shape[1]), (0, 0))) for r in rows]),
                [cv2.IMWRITE_JPEG_QUALITY, 90])

    feat = lambda s: librosa.feature.mfcc(y=s, sr=SR, n_mfcc=20, hop_length=160, n_fft=1024)
    n = min(len(clip), len(ref))
    _, wp = librosa.sequence.dtw(X=feat(ref[:n]), Y=feat(clip[:n]), metric="cosine")
    wp = wp[::-1]
    dtw = {}
    for t in np.arange(0.0, n / SR - 0.05, 0.25):
        js = wp[wp[:, 0] == int(t * 100)][:, 1]
        if len(js):
            dtw[f"{t:.2f}"] = round(float(js.mean()) / 100 - float(t), 2)
    (out / "dtw.json").write_text(json.dumps({"clip_audio_minus_reference_seconds_at_reference_time": dtw}, indent=1))
    print(json.dumps({"frames": len(fr), "dtw_offsets": dtw}))


if __name__ == "__main__":
    main()
