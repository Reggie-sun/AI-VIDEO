#!/usr/bin/env python3
"""Lip-sync measurement for S8a/S8b on the exact MP4, against the sealed vocal reference and timeline
(criteria: outputs/ai-city-takeover/ep01/v2/s8a-lipsync-amendment.md). Run with the video-analysis venv
(OpenCV + librosa); it measures, it does not judge looks.

  python -I lipsync_measure.py <mp4> <reference.wav> <timeline.json> <out-dir> --onsets 0.20,0.85,2.33,3.50
      --silences 0:0.20,4.53:5.0 --pauses 2.17:2.33

Times are clip seconds of the reference (clip t=0 is the reference's first sample).
1. The clip is conformed to 30 fps CFR (ffmpeg fps filter) and decoded at 960x540.
2. Audio offset L: onset-strength cross-correlation of the clip's own audio against the reference (+-0.5 s).
   The mouth is then compared with the reference shifted by L, i.e. as it will sit on the master.
3. Mouth aperture proxy per frame: share of dark pixels in a mouth box placed from the first-frame face
   detection (Haar) and followed by template matching of the nose-lip patch.
4. Reported: aperture-vs-vocal lag (frames), opening delay at each sealed onset, aperture in sealed silences
   and pauses relative to the clip's own closed/open levels, and contact strips around each onset.
"""
import argparse
import json
import subprocess
from pathlib import Path

import cv2
import librosa
import numpy as np

W, H, FPS = 960, 540, 30


def frames_30fps(mp4):
    cmd = ["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def clip_audio(mp4, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def audio_offset(clip, ref, sr):
    hop = sr // 100
    a = librosa.onset.onset_strength(y=clip, sr=sr, hop_length=hop)
    b = librosa.onset.onset_strength(y=ref, sr=sr, hop_length=hop)
    best = (-2.0, 0)
    for lag in range(-50, 51):                               # clip audio = reference delayed by lag * 10 ms
        x = a[max(0, lag):]
        y = b[max(0, -lag):]
        n = min(len(x), len(y))
        if n < 100:
            continue
        c = float(np.corrcoef(x[:n], y[:n])[0, 1])
        if c > best[0]:
            best = (c, lag)
    return best[1] * 10 / 1000, best[0]


def mouth_track(frames):
    gray0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray0, 1.1, 5, minSize=(120, 120))
    if len(faces) == 0:
        raise SystemExit("no frontal face found in the first frame")
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    mouth = (x + int(0.27 * w), y + int(0.66 * h), int(0.46 * w), int(0.26 * h))       # x, y, w, h
    anchor = (x + int(0.30 * w), y + int(0.45 * h), int(0.40 * w), int(0.22 * h))      # nose and upper lip
    ax, ay, aw, ah = anchor
    tmpl = gray0[ay:ay + ah, ax:ax + aw]
    mx, my, mw, mh = mouth
    ref_roi = gray0[my:my + mh, mx:mx + mw].astype(np.float32)
    thresh = float(np.percentile(ref_roi, 50)) * 0.5
    out, boxes = [], []
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        r = cv2.matchTemplate(g[max(0, ay - 40):ay + ah + 40, max(0, ax - 40):ax + aw + 40], tmpl, cv2.TM_CCOEFF_NORMED)
        _, _, _, loc = cv2.minMaxLoc(r)
        dx, dy = loc[0] - min(40, ax), loc[1] - min(40, ay)
        roi = g[my + dy:my + dy + mh, mx + dx:mx + dx + mw].astype(np.float32)
        out.append(float((roi < thresh).mean()))
        boxes.append((mx + dx, my + dy, mw, mh))
    return np.array(out), boxes, {"face": [int(v) for v in (x, y, w, h)], "mouth_box": [int(v) for v in mouth],
                                  "dark_threshold": round(thresh, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4"); ap.add_argument("reference"); ap.add_argument("timeline"); ap.add_argument("out")
    ap.add_argument("--onsets", required=True); ap.add_argument("--silences", required=True)
    ap.add_argument("--pauses", default="")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sr = 16000
    ref, _ = librosa.load(a.reference, sr=sr, mono=True)
    clip = clip_audio(a.mp4, sr)
    lag_s, lag_c = audio_offset(clip, ref, sr)
    frames = frames_30fps(a.mp4)
    ap_, boxes, geo = mouth_track(frames)
    # vocal envelope per 30 fps frame on the reference, moved onto the clip timeline by the measured audio lag
    hop = sr // FPS
    env = librosa.feature.rms(y=ref, frame_length=2 * hop, hop_length=hop)[0]
    env_db = 20 * np.log10(env / env.max() + 1e-9)
    shift = int(round(lag_s * FPS))
    env_clip = np.full(len(ap_), -80.0)
    for i in range(len(ap_)):
        j = i - shift
        if 0 <= j < len(env_db):
            env_clip[i] = env_db[j]
    voc = np.clip((env_clip + 40) / 40, 0, 1)
    sm = np.convolve(ap_, np.ones(3) / 3, mode="same")
    best = max(((float(np.corrcoef(sm[max(0, k):len(sm) + min(0, k)], voc[max(0, -k):len(voc) - max(0, k)])[0, 1]), k)
                for k in range(-8, 9)), key=lambda t: t[0])
    closed, opened = float(np.percentile(sm, 10)), float(np.percentile(sm, 90))
    level = lambda v: round((v - closed) / (opened - closed + 1e-9), 2)               # 0 closed .. 1 open
    span = lambda s: [int(round(float(t) * FPS)) + shift for t in s.split(":")]
    silences = []
    for s in a.silences.split(","):
        i0, i1 = span(s)
        seg = sm[max(0, i0):min(len(sm), i1)]
        silences.append({"clip_seconds": s, "frames": [i0, i1], "median_level": level(float(np.median(seg))) if len(seg) else None,
                         "max_level": level(float(seg.max())) if len(seg) else None})
    pauses = []
    for s in filter(None, a.pauses.split(",")):
        i0, i1 = span(s)
        seg = sm[max(0, i0 - 1):min(len(sm), i1 + 2)]
        vowel = sm[voc > 0.75]
        pauses.append({"clip_seconds": s, "min_level": level(float(seg.min())),
                       "vowel_median_level": level(float(np.median(vowel))) if len(vowel) else None})
    onsets = []
    d = np.diff(sm, prepend=sm[0])
    for t in a.onsets.split(","):
        i = int(round(float(t) * FPS)) + shift
        lo, hi = max(1, i - 6), min(len(d) - 1, i + 6)
        k = lo + int(np.argmax(d[lo:hi + 1]))
        onsets.append({"clip_seconds": float(t), "expected_frame": i, "opening_frame": k, "delta_frames": k - i})
        strip = [cv2.resize(frames[j][boxes[j][1] - 40:boxes[j][1] + boxes[j][3] + 30,
                                      boxes[j][0] - 40:boxes[j][0] + boxes[j][2] + 40], (200, 140))
                 for j in range(max(0, i - 3), min(len(frames), i + 4))]
        cv2.imwrite(str(out / f"onset-{float(t):.2f}.jpg"), np.hstack(strip))
    report = {"mp4": a.mp4, "reference": a.reference, "fps": FPS, "frames": len(ap_),
              "audio_offset": {"clip_audio_lags_reference_seconds": lag_s, "onset_corr": round(lag_c, 3),
                               "frames": shift},
              "geometry": geo,
              "aperture_vs_vocal": {"best_lag_frames": best[1], "corr": round(best[0], 3),
                                    "note": "positive lag: mouth follows the vocal by that many frames"},
              "levels": {"closed_p10": round(closed, 4), "open_p90": round(opened, 4)},
              "silences": silences, "pauses": pauses, "onsets": onsets,
              "per_frame": [{"frame": i, "aperture": round(float(sm[i]), 4), "vocal_db": round(float(env_clip[i]), 1)}
                            for i in range(len(sm))]}
    (out / "lipsync-measure.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "per_frame"}, indent=1))


if __name__ == "__main__":
    main()
