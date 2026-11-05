#!/usr/bin/env python3
"""Post-media evidence for one lip-sync trial take (plan 2026-11-02-iris-ep01-lipsync-trial.md section 4).
Run from the repository root with the video-analysis venv (OpenCV + librosa):

  ~/.local/share/ai-video/video-analysis-mcp/bin/python -I outputs/ai-city-takeover/ep01/v2/trial/lipsync-ev/evidence.py LSen1

1. the sync check (motion-kit/tools/sync_check.py): the take's soundtrack against the window it was sent;
2. the mouth timeline (qa/lipsync_review.py) around the measured word onsets, the mouth box from face detection;
3. the review video: the take with the master laid over at the reference mapping (clip 0 s = song 17.97 s),
   normal speed. The verdict on the mouth is the user's; this script only measures.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import cv2

HERE = Path(__file__).resolve().parent
V2 = HERE.parents[1]
REPO = HERE.parents[5]
SONG_T0 = 17.97
ONSETS = {"I": 18.60, "didn't": 19.28, "run": 19.50, "I (just)": 20.72, "just": 20.91, "looked": 21.41, "outside": 21.91,
          "I (pass 2)": 22.61}
UV = ["uv", "run", "python"]
VA = [str(Path.home() / ".local/share/ai-video/video-analysis-mcp/bin/python"), "-I"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mouth_box(mp4: Path) -> list[int]:
    """Face detection on a frame 1.5 s in; the mouth box is the lower part of the largest face."""
    cap = cv2.VideoCapture(str(mp4))
    cap.set(cv2.CAP_PROP_POS_MSEC, 1500)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("cannot read a frame")
    frame = cv2.resize(frame, (1920, 1080))
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(160, 160))
    if not len(faces):
        raise SystemExit("no face found; give the mouth box by hand")
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return [int(x + 0.18 * w), int(y + 0.58 * h), int(0.64 * w), int(0.5 * h)]


def main(unit: str) -> int:
    files = sorted((V2 / "gen" / unit / "project/state/video-generation/fetch/files").glob("*.mp4"))
    if len(files) != 1:
        raise SystemExit(f"{unit}: expected one fetched MP4, found {len(files)}")
    mp4 = files[0]
    out = HERE / unit
    out.mkdir(exist_ok=True)
    window = HERE / "window-17.97-22.97.wav"
    manifest = {"song": str(V2.relative_to(REPO) / "song/mix/IRIS-01-v2.wav"),
                "words": str(V2.relative_to(REPO) / "timing/words.json"),
                "takes": [{"name": unit, "take": str(mp4.relative_to(REPO)), "window": str(window.relative_to(REPO)),
                           "song_t0": SONG_T0, "film": [18.8667, 22.5667],
                           "prior": {"lag_s": 0.0, "why": "reference mapping (clip 0 s = song 17.97 s)"}}]}
    (out / "sync-take.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    subprocess.run([*UV, "motion-kit/tools/sync_check.py", "--manifest", str(out / "sync-take.json"), "--out", str(out / "sync"),
                    "--review"], cwd=REPO, check=True)
    box = mouth_box(mp4)
    onsets = ",".join(f"{t - SONG_T0:.3f}" for t in ONSETS.values())
    subprocess.run([*VA, str(V2 / "qa/lipsync_review.py"), str(mp4), str(window), str(out / "lipsync"), "--mouth",
                    ",".join(map(str, box)), "--onsets", onsets, "--zero", str(SONG_T0)], cwd=REPO, check=True)
    review = V2 / "renders/review" / f"trial-{unit}-{sha(mp4)[:12]}-ref-master.mp4"
    dur = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0",
                          str(mp4)], capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-ss", f"{SONG_T0}", "-t", dur, "-i",
                    str(V2 / "song/mix/IRIS-01-v2.wav"), "-map", "0:v:0", "-map", "1:a:0", "-vf", "fps=30", "-c:v", "libx264",
                    "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
                    str(review)], check=True)
    summary = {"unit": unit, "take": str(mp4.relative_to(REPO)), "take_sha256": sha(mp4), "mouth_box": box,
               "onsets_clip_s": {k: round(t - SONG_T0, 3) for k, t in ONSETS.items()},
               "sync": str((out / "sync" / unit / "sync.json").relative_to(REPO)),
               "lipsync": str((out / "lipsync").relative_to(REPO)),
               "review_ref_master": {"path": str(review.relative_to(REPO)), "sha256": sha(review)}}
    (out / "evidence.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
