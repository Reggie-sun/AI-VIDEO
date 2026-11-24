#!/usr/bin/env python3
"""QA of the IRIS EP01 opening v2 review film (song 0-59.2341 s, 1422 frames), the measurements of
texture_study/REPORT.md applied to v2. Run from the repository root after qa_opening.py (spec, sound, cuts, lips,
flash, red) and texture_study/work/frame_metrics.py on the film and on the picture:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa_opening_v2.py --film <mp4> --picture <mp4> \\
      --film-metrics <jsonl> --picture-metrics <jsonl> --layers <layers.json> --out <dir> [--v2c | --v2d]

--v2c: s014 is one shot (MO07 r6-2, id s014a) from 1322 to 1410; the 1377 cut and s014b are gone.
--v3: v2c's cuts plus 56.9237 (frame 1366): s014p (the punch-in) 1322-1365, s014a (the wide) 1366-1409; the motion
classes read off data/edl-opening-v3.json (s004 no longer holds).

Writes <out>/qa_v2.json and <out>/contact.jpg (one frame per shot), <out>/ev_compare.jpg (3 EV / IRIS pairs, 5 with --v2c):
- texture: per frame REPORT.md 1.1's label (frame_metrics: screen dot / line / none, pitch, angle, mosaic, black),
  per shot the main screen, its pitch and angle medians, the frames of every other label; dither = frames whose
  full-resolution luma has < 25 % of its pixels between 48 and 207 and > 10 % each below 48 and above 207 (near
  binary, both inks) on the picture.
- motion: per shot the median luma change between frames (picture, 480x270 grey, 3x3 box) and the source class from
  the EDL (still / hold / black / video), the still and video shares of the 1422 frames.
- graphics: REPORT.md 1.3's ink (film vs picture, 4x down, max channel difference > 45, resident HUD zones and the
  chip masked), per shot the mean of the 32 px block area (+1 block), ink share per 3x3 cell, the event clips per shot
  from layers.json (tracks slam, lyrics, devices*) and clips that run over a cut.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

arg = lambda k: sys.argv[sys.argv.index(k) + 1]
FILM, PIC, OUT = Path(arg("--film")), Path(arg("--picture")), Path(arg("--out"))
FM, PM, LAYERS = Path(arg("--film-metrics")), Path(arg("--picture-metrics")), Path(arg("--layers"))
EV = Path("outputs/anabology-opus55-replica/source/2103533196721704960.mp4")
EDL = Path("outputs/ai-city-takeover/ep01/v4/excerpt/data/edl-opening-v2.json")
W, H, N = 1920, 1080, 1422
CUTS = [0, 99, 231, 307, 406, 493, 625, 714, 791, 869, 979, 1078, 1123, 1178, 1211, 1222, 1255, 1322, 1377, 1410, 1422]
IDS = ["s001", "s002", "s003", "s004", "s005", "s006", "s007", "s008", "s009", "s010", "s011", "s012a", "s012b", "s012c",
       "s012d", "s013a", "s013b", "s014a", "s014b", "s014c"]
if "--v2c" in sys.argv or "--v2d" in sys.argv or "--v3" in sys.argv:      # --v2d: v2c's picture and cuts, the v2d layout (labels only)
    CUTS.remove(1377)
    IDS.remove("s014b")
if "--v3" in sys.argv:
    EDL = Path("outputs/ai-city-takeover/ep01/v4/excerpt/data/edl-opening-v3.json")
    CUTS.insert(CUTS.index(1410), 1366)
    IDS.insert(IDS.index("s014a"), "s014p")
STILL_CHORUS = {"s012a", "s012d", "s013a", "s014c"}          # v4r11's own stills / freeze (REPORT.md 4.2)


def label(r):  # REPORT.md 1.1 / summarize.py
    L = {"black": r["ymean"] < 15 and r["chroma"] < 3}
    if r["scr_prom"] >= 1000 and r["scr_cov"] >= 0.5:
        dot = r["scr_orth"] >= 0.3 * r["scr_prom"]
        L.update(screen="dot" if dot else "line", ang=round(r["scr_ang"] % 90 if dot else r["scr_ang"], 1), pitch=r["scr_pitch"],
                 orth=round(r["scr_orth"] / r["scr_prom"], 3))
    else:
        L["screen"] = "none"
    lx, ly = r["mos_lag_x"], r["mos_lag_y"]
    if r["mos_r_x"] >= 0.4 and r["mos_r_y"] >= 0.4 and (abs(lx - ly) <= 2 or abs(lx - 2 * ly) <= 2 or abs(ly - 2 * lx) <= 2):
        L["mosaic"] = min(lx, ly)
    return L


def frames(p: Path, w: int, h: int, pix="rgb24", ch=3):
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(p), "-map", "0:v", "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo",
                           "-pix_fmt", pix, "-"], stdout=subprocess.PIPE)
    n = w * h * ch
    while (b := pr.stdout.read(n)) and len(b) == n:
        yield np.frombuffer(b, np.uint8).reshape(h, w, ch) if ch > 1 else np.frombuffer(b, np.uint8).reshape(h, w)
    pr.wait()


def shot_of(f):
    return next(i for i in range(len(IDS)) if CUTS[i] <= f < CUTS[i + 1])


def texture() -> dict:
    out = {}
    for name, path in (("film", FM), ("picture", PM)):
        L = [label(json.loads(x)) for x in path.read_text().splitlines()]
        rows = {}
        for i, sid in enumerate(IDS):
            seg = L[CUTS[i]:CUTS[i + 1]]
            kinds = {}
            for j, l in enumerate(seg):
                kinds.setdefault(l["screen"], []).append(CUTS[i] + j)
            main = max(kinds, key=lambda k: len(kinds[k]))
            sc = [l for l in seg if l["screen"] == main]
            rows[sid] = {"frames": [CUTS[i], CUTS[i + 1] - 1], "screen": main, "share": round(len(sc) / len(seg), 3),
                         "pitch_px": float(np.median([l["pitch"] for l in sc])) if main != "none" else None,
                         "angle_deg": float(np.median([l["ang"] for l in sc])) if main != "none" else None,
                         "orth_ratio": float(np.median([l["orth"] for l in sc])) if main != "none" else None,
                         "other": {k: v for k, v in kinds.items() if k != main},
                         "mosaic": [CUTS[i] + j for j, l in enumerate(seg) if "mosaic" in l],
                         "black": [CUTS[i] + j for j, l in enumerate(seg) if l["black"]]}
        out[name] = rows
    return out


def picture_pass() -> tuple[list, list]:
    """Near-binary share (full res luma 48-207 < 25 %) and the blurred grey frame change, per picture frame."""
    binary, d, prev = [], [], None
    for a in frames(PIC, W, H, "gray", 1):
        mid, lo, hi = ((a >= 48) & (a <= 207)).mean(), (a < 48).mean(), (a > 207).mean()
        binary.append(round(float(mid), 3) if min(lo, hi) > 0.1 else 1.0)     # both inks present (not a dark frame)
        s = a.reshape(270, 4, 480, 4).mean((1, 3))
        s = (s + np.roll(s, 1, 0) + np.roll(s, -1, 0)) / 3
        s = (s + np.roll(s, 1, 1) + np.roll(s, -1, 1)) / 3
        d.append(0.0 if prev is None else float(np.abs(s - prev).mean()))
        prev = s
    return binary, d


def motion(d: list) -> dict:
    E = {s["id"]: s for s in json.loads(EDL.read_text())["shots"]}
    rows, cls_frames = {}, {"still": 0, "hold": 0, "black": 0, "video": 0}
    for i, sid in enumerate(IDS):
        a, z = CUTS[i], CUTS[i + 1]
        e = E.get(sid, {})
        for f in range(a, z):
            if sid == "s010" and f >= 956:
                c = "black"
            elif "still" in e or sid in STILL_CHORUS:
                c = "still"
            elif "hold" in e and f >= e["hold"]["f"]:
                c = "hold"
            else:
                c = "video"
            cls_frames[c] += 1
        st = e.get("still")
        rows[sid] = {"median_change": round(float(np.median(d[a + 1:z])), 3) if z - a > 1 else None,
                     "source": "still" if (st or sid in STILL_CHORUS) else "video" + (" + hold" if "hold" in e else ""),
                     "push_pct_per_s": round((st["zoom"][1] - st["zoom"][0]) / st["zoom"][0] * 100 / ((z - a - 1) / 24), 2) if st else None}
    share = {k: round(v / N, 4) for k, v in cls_frames.items()}
    share["non_video"] = round(1 - cls_frames["video"] / N, 4)
    return {"shots": rows, "frames": cls_frames, "share": share}


def graphics() -> dict:
    hud = np.zeros((270, 480), bool)
    def z(x0, y0, x1, y1): hud[y0 // 4:(y1 + 3) // 4, x0 // 4:(x1 + 3) // 4] = True
    z(0, 0, 60, 60); z(1860, 0, 1920, 60); z(0, 1020, 1920, 1080); z(60, 40, 620, 76); z(1540, 36, 1830, 116)
    z(0, 200, 72, 1040); z(1540, 980, 1830, 1014); z(1590, 120, 1830, 212)    # + the chip (1594-1824 x 124-207)
    area, cells = [], []
    for a, b in zip(frames(FILM, 480, 270), frames(PIC, 480, 270)):
        m = (np.abs(a.astype(np.int16) - b.astype(np.int16)).max(2) > 45) & ~hud
        blk = m[:264, :].reshape(33, 8, 60, 8).any((1, 3))
        g = blk.copy()
        g[1:] |= blk[:-1]; g[:-1] |= blk[1:]; g[:, 1:] |= g[:, :-1].copy(); g[:, :-1] |= g[:, 1:].copy()
        area.append(float(g.mean()))
        c = np.array([[m[r * 90:(r + 1) * 90, k * 160:(k + 1) * 160].sum() for k in range(3)] for r in range(3)], float)
        cells.append(c)
    L = json.loads(LAYERS.read_text())
    clips = [c for t in L["tracks"] if not t.get("hidden") and (t["id"] in ("slam", "lyrics") or t["id"].startswith("devices"))
             for c in t["clips"]]
    rows, cross = {}, []
    for c in clips:
        e = c["from"] + c["duration"]
        if e > CUTS[shot_of(c["from"]) + 1]:
            cross.append(c["id"])
    for i, sid in enumerate(IDS):
        a, b = CUTS[i], CUTS[i + 1]
        cs = sum(cells[a:b]); cs = cs / max(cs.sum(), 1)
        n = [c["id"] for c in clips if a <= c["from"] < b]
        rows[sid] = {"events": len(n), "ids": n, "area_mean": round(float(np.mean(area[a:b])), 4),
                     "cells": [[round(float(x), 3) for x in r] for r in cs], "bottom_right": bool(any(c[2, 2] > 0 for c in cells[a:b]))}
    ev = [r["events"] for r in rows.values()]
    tot = sum(cells); tot = tot / tot.sum()
    stills = [r["area_mean"] for s, r in rows.items() if s in ("s003", "s007", "s009", "s010", "s012a", "s013a")]
    return {"shots": rows, "events_median": float(np.median(ev)), "events_iqr": [float(np.percentile(ev, 25)), float(np.percentile(ev, 75))],
            "area_median": round(float(np.median([r["area_mean"] for r in rows.values()])), 4),
            "area_median_stills": round(float(np.median(stills)), 4),
            "cells_all": [[round(float(x), 3) for x in r] for r in tot],
            "shots_with_bottom_right": sum(r["bottom_right"] for r in rows.values()), "clips_over_cut": cross,
            "chip_px": [230, 83], "chip_share": round(230 * 83 / (W * H), 4)}


def grab(p: Path, f: int, w=W, h=H) -> Image.Image:
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", f"select=eq(n\\,{f}),scale={w}:{h}", "-vsync", "0", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(b, np.uint8).reshape(h, w, 3))


def sheets() -> None:
    mids = [(a + b) // 2 for a, b in zip(CUTS, CUTS[1:])]
    mids[3], mids[9] = 380, 920
    S = Image.new("RGB", (384 * 5, 236 * 4), "black"); d = ImageDraw.Draw(S)
    for i, (sid, f) in enumerate(zip(IDS, mids)):
        x, y = (i % 5) * 384, (i // 5) * 236
        S.paste(grab(FILM, f).resize((384, 216)), (x, y + 20)); d.text((x + 4, y + 4), f"{sid}  f{f}", fill="yellow")
    S.save(OUT / "contact.jpg", quality=82)
    pairs = [("A dots 4.2 px", 470, 160, (860, 420)), ("J0 black + type", 262, 965, None), ("D mosaic 20 px", 762, 636, None)]
    if "--v2c" in sys.argv or "--v2d" in sys.argv or "--v3" in sys.argv:     # + EV's chorus line screen (C, its strongest frame f2150) on s014 r6-2 at the sleeve-out beat
        pairs += [("C lines 3.99 px / s014 r6-2", 2150, 1377, None), ("C lines 3.99 px", 2150, 1377, (1000, 420))]
    C = Image.new("RGB", (1280, len(pairs) * 380), "black"); d = ImageDraw.Draw(C)
    for k, (name, fe, fi, crop) in enumerate(pairs):
        a, b = grab(EV, fe), grab(FILM, fi)
        if crop:
            x, y = crop
            a, b = a.crop((x, y, x + 160, y + 90)).resize((640, 360), Image.NEAREST), b.crop((x, y, x + 160, y + 90)).resize((640, 360), Image.NEAREST)
        else:
            a, b = a.resize((640, 360)), b.resize((640, 360))
        C.paste(a, (0, k * 380 + 20)); C.paste(b, (640, k * 380 + 20))
        d.text((4, k * 380 + 4), f"EV f{fe}  |  {name}" + ("  (4x crop)" if crop else ""), fill="yellow")
        d.text((644, k * 380 + 4), f"IRIS {'v3' if '--v3' in sys.argv else 'v2d' if '--v2d' in sys.argv else 'v2c' if '--v2c' in sys.argv else 'v2'} f{fi}", fill="yellow")
    C.save(OUT / "ev_compare.jpg", quality=85)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    binary, d = picture_pass()
    tex = texture()
    dither = [f for f, v in enumerate(binary) if v < 0.25 and not (956 <= f < 979)]
    res = {"film": str(FILM), "texture": tex, "dither_frames": dither, "motion": motion(d), "graphics": graphics()}
    (OUT / "qa_v2.json").write_text(json.dumps(res, indent=1))
    sheets()
    g = res["graphics"]
    print(json.dumps({"dither": dither, "motion_share": res["motion"]["share"], "events_median": g["events_median"],
                      "events_iqr": g["events_iqr"], "area_median": g["area_median"], "area_median_stills": g["area_median_stills"],
                      "cells_all": g["cells_all"], "bottom_right": g["shots_with_bottom_right"], "over_cut": g["clips_over_cut"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
