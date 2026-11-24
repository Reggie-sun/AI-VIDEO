#!/usr/bin/env python3
"""IRIS EP01 opening picture (2026-11-21): song 0-40.7859 s (song frames 0-978) cut from the ten Seedance takes chosen
for s001-s010 (pilot/opening; outputs/ai-city-takeover/logs/decisions.md 2026-11-20/21), through the v4r11 print, picture
only; then joined to the v4r11 picture of song frames 979-1421 for the Agentcut replica. Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening.py --prep [ids...]   # media/seq/o0NN, data/media-opening/<id>.json
                                                                                         (one process per shot can run in parallel)
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening.py --build           # data/edl-opening-picture.json, composition, engine.js
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-opening-picture.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v4r11-opening-picture-000-979.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening.py --join            # renders/IRIS-EP01-v4r11-picture-000-1422.mp4

Frames are song frames: frame n shows song time n/24 (offset 0); a song time t shows on frame round(24 t). Every cut is a
beat of beats.json within 0.03 s, and its frame within 0.03 s of that beat (as build.py's check_cuts).

Cuts (decided 2026-11-21): s003/s004 on the 12.7826 beat - s003 (MO19-o-1) runs on through "Incident Week" (its wide
shot, her mouth not readable), s004 (SG01-o-2) starts inside its lip-synced span (clip 1.32-3.02 = song 12.62-14.32;
its pictures before clip 1.32 move the mouth in the silence after "Week", so the earlier 12.3298 beat is not used) and
plays on to 16.9041 for "A training run phoned a friend" (voice over her taking the handset); s004 is placed by its
sync lag (song = clip + 11.15 + 0.1499). s008/s009 on the 32.9723 beat: the last beat before "Bus stop" is voiced
(vocal stem onset 32.975; SG02-o-1's sync holds to song 32.897 and parts at 32.949), so "Average Individual. That's me."
is on s008 (song = clip + 29.529 + 0.0499) and "Bus stop" on s009, whose take starts at clip 0 on the cut frame; the
name sticker's lettering (the take's last 0.4 s) is never shown.

Picture repairs, all in the prepared pictures (prep_media.prep_clip; the takes are untouched): non-lamp reds to orange
(prep_media.tail_lights_to_orange: saturated reds rotated +30 deg outside her grown matte, so the ear lamp keeps its
red) on s002, s006, s008, s009, s010; s006's lit green/teal shop signs blurred (their letter-like strokes), detected per
picture in the upper half of the frame, outside her matte. s002's fire-door gap light is the board's one red besides
the lamp (board s002 action/prompt; excerpt/flash/opening-seedance.md), so there only the red right of the door's strip
(its spill on the pillar's side, 3.5-4.0 s) is pulled to orange.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep_media as pm  # noqa: E402
from edl import EXC, FPS, H, REPO, V4, W  # noqa: E402

PILOT = "pilot/sd-{}/{}/project/state/video-generation/fetch/files/{}.mp4"
CUT_S004, CUT_S009 = 12.7826, 32.9723
SHOTS = [
    # id, media id, take, song t0, t1, clip_song_start (song time of clip 0), extra
    {"id": "s001", "media_id": "o001", "t0": 0.0, "t1": 4.1215, "take": ("MO01-o-1", "MO01", "1919303fe678205c21941a2a58697b0f5a8202f54d433364ba9a9b7a62d3845b")},
    {"id": "s002", "media_id": "o002", "t0": 4.1215, "t1": 9.6131, "take": ("MO02-o-1", "MO02", "8e57fdd03f9da609c302893ad0564643b12a0c0df0c8ca0fb58e96135fb6721d"),
     "tail_lights_to_orange": True, "door_red_kept": True},
    {"id": "s003", "media_id": "o003", "t0": 9.6131, "t1": CUT_S004, "take": ("MO19-o-1", "MO19", "7adb869a3863f16ff834c3c6d5f0a6bc31c22f5f8434de4f2281778011d9ca78")},
    {"id": "s004", "media_id": "o004", "t0": CUT_S004, "t1": 16.9041, "take": ("SG01-o-2", "SG01", "b068e9ab3d4d7190cecdd64c341ace9af16713a934473ca3992764418d0db82e"),
     "clip_song_start": 11.15, "lag": 0.1499},
    {"id": "s005", "media_id": "o005", "t0": 16.9041, "t1": 20.5264, "take": ("MO20-o-2", "MO20", "cb59d6a5ea6322b36bfe0ce9e55065c3cce00b49a93e9a04f0f69e3ea468ed6d")},
    {"id": "s006", "media_id": "o006", "t0": 20.5264, "t1": 26.0528, "take": ("MO03-o-1", "MO03", "491541c03c516d5f8a31ab5b9e1486f7de2f0473cb42bd43c3ccddb63e22959a"),
     "tail_lights_to_orange": True, "blur_signs": True},
    {"id": "s007", "media_id": "o007", "t0": 26.0528, "t1": 29.7448, "take": ("MO04-o-1", "MO04", "884a280941e0e8205f296ecd6bab408c2258a2eb89a1db2fdbf1029037e405db")},
    {"id": "s008", "media_id": "o008", "t0": 29.7448, "t1": CUT_S009, "take": ("SG02-o-1", "SG02", "05c8945ab6f2593e67816e1071879fdb783263dae0eddc424a2fd09fc106e931"),
     "clip_song_start": 29.529, "lag": 0.0499, "tail_lights_to_orange": True},
    {"id": "s009", "media_id": "o009", "t0": CUT_S009, "t1": 36.1999, "take": ("MO21-o-2", "MO21", "d12ddf9caf1c0a883cc00cd1e2cba7abd75f170033138b5a3007d073aa395a1a"), "tail_lights_to_orange": True},
    {"id": "s010", "media_id": "o010", "t0": 36.1999, "t1": 40.7859, "take": ("MO05-o-1", "MO05", "f66648c784447cc38c8e62398097b151e71bfa7582b69b441ec4236d37eefcea"), "tail_lights_to_orange": True},
]
END_F = 979                                    # song frame of the s011 cut (40.7859 s): the v4r11 picture from here
V4R11_PICTURE = EXC / "renders/IRIS-EP01-v4-excerpt-v4r11-picture-036-059.mp4"   # its frame n = song frame n + 869
V4R11_PICTURE_SHA = "633e62dd"
RENDER = EXC / "renders/IRIS-EP01-v4r11-opening-picture-000-979.mp4"
JOINED = EXC / "renders/IRIS-EP01-v4r11-picture-000-1422.mp4"
META = EXC / "data/media-opening"            # one JSON per prepared shot


def frame_of(t: float) -> int:
    return int(round(t * FPS))


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def blur_signs(rgb: np.ndarray) -> tuple[np.ndarray, dict]:
    """Blur the lit green/teal signs (hue 75-175 deg, saturated, bright) in the upper half of the picture, outside her
    matte: the mask grown 14 px and feathered, a 10 px Gaussian of the picture inside it."""
    a = rgb.astype(np.float32) / 255
    h, s, v = pm.rgb_to_hsv(a)
    sign = (h > 75) & (h < 175) & (s > 0.35) & (v > 0.45)
    sign[int(0.5 * rgb.shape[0]):] = False
    small = np.asarray(Image.fromarray(rgb).resize((pm.SEQ_W // 2, pm.SEQ_H // 2), Image.BILINEAR))
    her = pm.matte(small) > 0.35
    her = np.asarray(Image.fromarray((her * 255).astype(np.uint8)).resize((pm.SEQ_W, pm.SEQ_H), Image.NEAREST)) > 0
    sign &= ~her
    m = pm.feather(pm.grow(sign.astype(np.float32), 14), 6)[..., None]
    bl = np.asarray(Image.fromarray(rgb).filter(ImageFilter.GaussianBlur(10)), np.float32)
    out = rgb.astype(np.float32) * (1 - m) + bl * m
    return (np.clip(out, 0, 255) + 0.5).astype(np.uint8), {"sign_px": int(sign.sum()), "blurred_px": int((m[..., 0] > 0.5).sum())}


def door_red_kept(rgb: np.ndarray, out: np.ndarray) -> tuple[np.ndarray, dict]:
    """Keep the fire-door strip and its floor light red: the orange is taken only right of the strip (the column with
    the most saturated-red pixels) plus 230 px; nothing is changed on a picture without the strip."""
    a = rgb.astype(np.float32) / 255
    h, s, v = pm.rgb_to_hsv(a)
    red = (np.minimum(h, 360 - h) < 16) & (s > 0.5) & (v > 0.4)
    col = red.sum(0)
    if col.max() < 20:
        return rgb, {"door_x": None}
    x0 = int(np.argmax(col)) + 230
    res = rgb.copy()
    res[:, x0:] = out[:, x0:]
    return res, {"door_x": x0 - 230}


def prep(want: list[str]) -> int:
    # song frames: prep_clip resolves frames with prep_media's OFFSET / frame_of, set here to song time 0
    pm.OFFSET, pm.frame_of = 0.0, frame_of
    META.mkdir(parents=True, exist_ok=True)
    orange = pm.tail_lights_to_orange
    for s in SHOTS:
        if want and s["id"] not in want and s["media_id"] not in want:
            continue
        unit, name, h = s["take"]
        row = {**s, "clip": PILOT.format(unit, name, h)}
        row.setdefault("clip_song_start", frame_of(s["t0"]) / FPS)     # clip 0 on the shot's first frame
        if (V4 / row["clip"]).exists() is False or sha(V4 / row["clip"]) != h:
            raise SystemExit(f"{s['id']}: take missing or SHA-256 differs")
        if s.get("blur_signs"):
            def both(rgb, *th):
                out, st = orange(rgb, *th)
                out, st2 = blur_signs(out)
                return out, {**st, **st2}
            pm.tail_lights_to_orange = both
        if s.get("door_red_kept"):
            def door(rgb, *th):
                out, st = orange(rgb, *th)
                out, st2 = door_red_kept(rgb, out)
                return out, {**st, **st2}
            pm.tail_lights_to_orange = door
        try:
            m = {"shot": s["id"], **pm.prep_clip(row, EXC / "media")}
        finally:
            pm.tail_lights_to_orange = orange
        (META / f"{s['media_id']}.json").write_text(json.dumps(m, indent=1))
        print(s["id"], s["media_id"], {k: m[k] for k in ("frames", "first", "last", "repeats", "skips")}, flush=True)
    return 0


def check_cuts(beats: list[float]) -> list[dict]:
    out = []
    for s in SHOTS[1:] + [{"id": "end", "t0": 40.7859}]:
        t = s["t0"]
        nb = min(beats, key=lambda b: abs(b - t))
        f = frame_of(t)
        row = {"cut": s["id"], "t": t, "beat": nb, "dt": round(t - nb, 4), "frame": f, "frame_t": round(f / FPS, 4),
               "frame_dt_beat": round(f / FPS - nb, 4)}
        if abs(t - nb) > 0.03 or abs(f / FPS - nb) > 0.03:
            raise SystemExit(f"cut {s['id']} at {t} is {t - nb:+.4f} s from the beat {nb}")
        out.append(row)
    return out


def build() -> int:
    from build import levels
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())["beats"]
    cuts = check_cuts(beats)
    meta = {p.stem: json.loads(p.read_text()) for p in META.glob("*.json")}
    shots = []
    for s in SHOTS:
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        m = meta[s["media_id"]]
        if m["frames"] != f1 - f0:
            raise SystemExit(f"{s['id']}: {m['frames']} prepared pictures for {f1 - f0} frames (rerun --prep)")
        shots.append({"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": f0, "f1": f1, "kind": "clip", "chapter": "c1",
                      "take": s["take"][0], "take_sha256": s["take"][2],
                      "seq": {"dir": f"media/seq/{s['media_id']}", "count": f1 - f0}})
    if shots[0]["f0"] != 0 or shots[-1]["f1"] != END_F or any(a["f1"] != b["f0"] for a, b in zip(shots, shots[1:])):
        raise SystemExit("the shots do not tile song frames 0-978")
    edl = {"version": 16, "opening": True, "picture_only": True, "fps": FPS, "W": W, "H": H, "offset": 0.0, "end": END_F / FPS,
           "frames": END_F, "shots": shots, "images": {}, "levels": levels(shots, {}), "lines": [], "beats": [], "downbeats": [],
           "snare": [], "kick": [], "tracks": {}, "cuts": cuts}
    (EXC / "data/edl-opening-picture.json").write_text(json.dumps(edl, indent=1))
    dur = END_F / FPS
    (EXC / "composition-opening-picture.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 opening picture 000-979 (v4r11 print)</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-start="0" data-duration="{dur:.6f}" data-ex-edl="data/edl-opening-picture.json" data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{dur:.6f}" data-track-index="0"></canvas>
</div>
<script src="engine.js"></script>
</body>
</html>
""", encoding="utf-8")
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(EXC / "src/main.js"), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={EXC / 'engine.js'}", "--log-level=warning"], check=True)
    print(json.dumps({"cuts": cuts, "levels": edl["levels"]}, indent=1))
    return 0


def join() -> int:
    """The opening render (song frames 0-978) and the v4r11 picture's frames 110-552 (song frames 979-1421), one
    picture-only H.264 at the renders' settings (CRF 16, yuv420p, 24 fps)."""
    if not sha(V4R11_PICTURE).startswith(V4R11_PICTURE_SHA):
        raise SystemExit("v4r11 picture SHA-256 differs")
    if JOINED.exists():
        raise SystemExit(f"{JOINED.name} exists (not overwritten)")
    n = lambda p: int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                                      "stream=nb_read_frames", "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True).stdout)
    if n(RENDER) != END_F or n(V4R11_PICTURE) != 553:
        raise SystemExit("frame counts differ from 979 / 553")
    fc = (f"[0:v]trim=start_frame=0:end_frame={END_F},setpts=PTS-STARTPTS[a];"
          f"[1:v]trim=start_frame={END_F - 869}:end_frame=553,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(RENDER), "-i", str(V4R11_PICTURE), "-filter_complex", fc, "-map", "[v]",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-colorspace", "bt709", "-r", "24", "-movflags", "+faststart", str(JOINED)], check=True)
    if n(JOINED) != 1422:
        raise SystemExit(f"{JOINED.name}: {n(JOINED)} frames, not 1422")
    print(json.dumps({"joined": str(JOINED.relative_to(REPO)), "frames": n(JOINED), "sha256": sha(JOINED),
                      "opening": {"file": str(RENDER.relative_to(REPO)), "sha256": sha(RENDER)},
                      "v4r11_picture": {"file": str(V4R11_PICTURE.relative_to(REPO)), "sha256": sha(V4R11_PICTURE), "frames_used": [END_F - 869, 552]}}, indent=1))
    return 0


if __name__ == "__main__":
    if "--prep" in sys.argv:
        raise SystemExit(prep([a for a in sys.argv[1:] if not a.startswith("--")]))
    if "--build" in sys.argv:
        raise SystemExit(build())
    if "--join" in sys.argv:
        raise SystemExit(join())
    raise SystemExit(__doc__)
