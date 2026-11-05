#!/usr/bin/env python3
"""Screen-space anchors measured on the generated shots, so graphics sit on what the camera filmed
(run after seq.py, from the repository root, with the video-analysis venv for OpenCV):

  ~/.local/share/ai-video/video-analysis-mcp/bin/python -I outputs/ai-city-takeover/ep01/v2/comp/tracks.py

- S3: the misconfigured resolver is the red door gap at the end of the aisle. Per frame, the bounding box of the
  red light left of x=1000 (the right-hand red streak is a reflection on rack glass).
- S7: the translucent panes slide fast (up to ~900 px/s), so a stamp cannot ride a pane and stay readable. Each beat
  stamp flashes where a bright low-saturation pane clear of IRIS's face is at that beat (the candidate nearest an
  alternating left/right spot); main.js keeps it short so it reads as a tag, not a sticker left behind.
- S8a (when the chorus plays a take): her face, per frame, for the detector that locks on "I didn't run" and the
  probe that leaves her eyes on "I just looked outside". OpenCV's frontal-face cascade, the largest face, a 7-frame
  median, gaps filled from the nearest found frame. Video px of the take (the comp's camera maps them to the screen).
- c11 (face bracket on every shot where she appears, ev-gap-c10.md item 9): the same face track for S7, S9h and S8a2,
  and one face box per still plate she is on (P7, K5, K5b): the frontal cascade, else the profile cascade (K5b is a
  three-quarter profile). Plate px; main.js maps them through its camera.
Writes data/tracks.json (screen px at 1920x1080, one entry per sequence frame).
"""
import json
from pathlib import Path

import cv2
import numpy as np

COMP = Path(__file__).resolve().parent
SEQ = COMP / "seq"


def frames(shot):
    spec = json.loads((SEQ / "sequences.json").read_text())[shot]
    for i in range(spec["count"]):
        yield i, cv2.imread(str(SEQ / shot / f"{i:04d}.jpg"))


def red_gap(img):
    b, g, r = (img[..., c].astype(np.int16) for c in range(3))
    mask = ((r > 110) & (r - g > 55) & (r - b > 55)).astype(np.uint8)
    mask[:, 1000:] = 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    tall = [k for k in range(1, n) if stats[k][cv2.CC_STAT_HEIGHT] > 2.5 * stats[k][cv2.CC_STAT_WIDTH]
            and stats[k][cv2.CC_STAT_HEIGHT] > 80]                 # the gap is a tall thin strip; the floor glow is not
    if not tall:
        return None
    k = max(tall, key=lambda k: stats[k][cv2.CC_STAT_HEIGHT])
    x, y, w, h, _ = stats[k]
    return [int(x), int(y), int(w), int(h)]


STAMP_LIFE = 16                                                 # frames a stamp stays on its pane
FACE = (820, 0, 1400, 640)                                      # IRIS's face and hair in the S7 frames
SPOTS = [(330, 300), (1620, 420), (420, 820), (1600, 260), (300, 560), (1560, 720), (260, 200), (1650, 560)]
SAFE = (130, 80, 1790, 800)        # stamp centres: the 172x56 box at slam scale 1.35 stays on screen and above the lyric scrim


def pane_candidates(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    v = cv2.blur(hsv[..., 2], (41, 41))
    sat = cv2.blur(hsv[..., 1], (41, 41))
    mask = ((v > 120) & (sat < 60)).astype(np.uint8)
    n, _, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for k in range(1, n):
        x, y, w, h, a = stats[k]
        cx, cy = cent[k]
        if a < 15000 or (FACE[0] < cx < FACE[2] and cy < FACE[3]):
            continue
        # a pane near the frame edge still takes a stamp if the point pulled into SAFE lies on that pane
        px, py = int(np.clip(cx, SAFE[0], SAFE[2])), int(np.clip(cy, SAFE[1], SAFE[3]))
        if mask[py, px]:
            out.append((float(px), float(py)))
    return out


def follow(imgs, start, center, life):
    """Template-match a patch around center from frame start through start+life (clamped to the clip)."""
    g = [cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for im in imgs]
    pw, ph = 220, 140
    cx, cy = center
    track = [[round(cx), round(cy)]]
    for i in range(start + 1, min(len(g), start + life)):
        x0, y0 = int(np.clip(cx - pw / 2, 0, g[i].shape[1] - pw)), int(np.clip(cy - ph / 2, 0, g[i].shape[0] - ph))
        tmpl = g[i - 1][y0:y0 + ph, x0:x0 + pw]
        sx0, sy0 = max(0, x0 - 90), max(0, y0 - 90)
        area = g[i][sy0:y0 + ph + 90, sx0:x0 + pw + 90]
        _, _, _, loc = cv2.minMaxLoc(cv2.matchTemplate(area, tmpl, cv2.TM_CCOEFF_NORMED))
        cx, cy = sx0 + loc[0] + pw / 2, sy0 + loc[1] + ph / 2
        track.append([round(cx), round(cy)])
    return track


def face_track(shot):
    """[x, y, w, h] of the largest frontal face per frame, median-smoothed over 7 frames, gaps filled."""
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    raw = []
    for _, img in frames(shot):
        faces = cascade.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(140, 140))
        raw.append(max(faces, key=lambda f: f[2] * f[3]).tolist() if len(faces) else None)
    found = [i for i, f in enumerate(raw) if f]
    if not found:
        return None
    filled = [raw[i] or raw[min(found, key=lambda j: abs(j - i))] for i in range(len(raw))]
    arr = np.array(filled, float)
    smooth = [np.median(arr[max(0, i - 3):i + 4], axis=0) for i in range(len(arr))]
    return {"boxes": [[round(v) for v in b] for b in smooth], "found": f"{len(found)}/{len(raw)}"}


def plate_face(name, path=None, min_size=100):
    """[x, y, w, h] of the largest face on a still plate (or on one image at path): frontal cascade first, then the profile
    cascade."""
    g = cv2.cvtColor(cv2.imread(str(path or COMP / "plates" / f"{name}.png")), cv2.COLOR_BGR2GRAY)
    for xml, n in (("haarcascade_frontalface_default.xml", 6), ("haarcascade_profileface.xml", 5)):
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + xml).detectMultiScale(g, 1.1, n, minSize=(min_size, min_size))
        if len(faces):
            return [int(v) for v in max(faces, key=lambda f: f[2] * f[3])]
    return None


def main():
    out = {"S3_gap": [red_gap(img) for _, img in frames("S3")]}
    seqs = json.loads((SEQ / "sequences.json").read_text())
    for shot in ("S8a", "S8a2", "S7", "S9h"):
        if shot in seqs:
            out[f"{shot}_face"] = face_track(shot)
    out["plate_faces"] = {p: plate_face(p) for p in ("P7", "K5", "K5b", "P8c")}
    # c12: the take inserts she is in hold still enough for one face box, measured on their first frame (video px;
    # min 150 px: at 100 px the profile cascade takes a lamp on the bridge in S5r)
    out["insert_faces"] = {s: plate_face(s, SEQ / s / "0000.jpg", 150) for s in ("I6",) if s in seqs}
    seq = json.loads((SEQ / "sequences.json").read_text())["S7"]
    imgs = [img for _, img in frames("S7")]
    beats = json.loads((COMP / "data/beats.json").read_text())["beats"]
    t0, t1 = seq["comp_start"], seq["comp_end"]
    b0 = max(i for i, b in enumerate(beats) if b <= t0 + 1e-6)
    stamps = []
    for i, tb in enumerate(beats[b0 + 1:b0 + 1 + len(SPOTS)]):
        if tb >= t1:
            break
        f = round((tb - t0) * 30)
        cands = [c for c in pane_candidates(imgs[f]) if not (FACE[0] - 60 < c[0] < FACE[2] + 60 and c[1] < FACE[3] + 40)]
        if not cands:
            continue
        sx, sy = SPOTS[i]
        c = min(cands, key=lambda p: (p[0] - sx) ** 2 + (p[1] - sy) ** 2)
        tr = follow(imgs, f, c, STAMP_LIFE)
        stamps.append({"t": tb, "frame": f, "at": [round(c[0]), round(c[1])],
                       "pane_travel_px": round(sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in zip(tr, tr[1:])))})
    out["S7_stamps"] = stamps
    (COMP / "data/tracks.json").write_text(json.dumps(out) + "\n")
    gaps = [g for g in out["S3_gap"] if g]
    print(json.dumps({"S3_found": f"{len(gaps)}/{len(out['S3_gap'])}", "S3_first": gaps[0] if gaps else None,
                      "S3_last": gaps[-1] if gaps else None,
                      "S7_stamps": [(s["frame"], s["at"], s["pane_travel_px"]) for s in stamps],
                      **{f"{k}": out[k]["found"] for k in ("S8a_face", "S8a2_face", "S7_face", "S9h_face") if out.get(k)},
                      "plate_faces": out["plate_faces"], "insert_faces": out["insert_faces"]}))


if __name__ == "__main__":
    main()
