#!/usr/bin/env python3
"""IRIS EP01 s031-s048 review cut v1 (2026-11-26): song 134.4435-209.3395 s, the takes and stills the user chose for
s031-s048 (pilot/s031-048/HANDOFF-2026-11-24.md "剪辑用法（2026-11-26）"; outputs/ai-city-takeover/logs/decisions.md
2026-11-24..26), through the same print as s015-s030 (section2.py: per-shot blur classes, the verse dot screen),
picture only; the EV graphics, lyrics and the song are the Agentcut layer (section3_layers.py). Run from the repo root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3.py --prep [ids...]   # media/s3/<id>, data/media-s3/<id>.json
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3.py --blur [ids...]   # media/s3blur/<id> (classes B/C/D/E)
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3.py --build           # data/edl-s031-048-v1.json, composition, engine.js
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-s031-048-v1.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-s031-048-v1-picture.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu

Frames: section frame k shows song frame 3227 + k (the 0-134 v1 film ends on song frame 3226; round(24 * 134.4435) =
3227); 1797 frames to song frame 5024 = round(24 * 209.3395). Every cut is a beat of beats.json (|cut - beat| <= 0.03 s
and the cut frame's time within 0.03 s of it).

Pictures (all repairs in the prepared pictures; takes and plates untouched): as section2.py (clips decoded at 2304x1296
from the whole 4K frame or a digital crop, clip time c(t) = c0 + (t - t0) or piecewise "knots"; saturated reds outside
her matte to orange; stills drawn per frame through their move), plus:
- s039: the door-crack red line is the user's exception (「留红光，和 s002 一样算例外」): the orange repair is undone in
  the box under the door (KEEP_RED); everywhere else as every other shot.
- s037d: the microwave window (lit in SG16y; INS37 unplugged it) darkened in a fixed feathered box (MW_BOX).
- s046b: MO15 a-1's stopwatch, a 3.5x crop of the 4K take; on 'clocks' (202.24) a post push-in and micro-shake stand
  for the press (the take's hand never presses: decisions 2026-11-25 「用 a-1，按表后期做」).
- s035b: the brass canister (S035B/canister-2-2944, keyed off its grey ground) falls into the basket, landing on 155.26.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep_media as pm  # noqa: E402
from edl import EXC, FPS, H, REPO, V4, W  # noqa: E402
from section2 import LAND, SHAKE, SMEAR, decode, sha, still_view  # noqa: E402

SF0, SF1 = 3227, 5024                    # song frames shown: 3227 .. 5023
N = SF1 - SF0                            # 1797
OFFSET = SF0 / FPS
SEQ_W, SEQ_H = pm.SEQ_W, pm.SEQ_H
PIL_ = V4 / "pilot"
FETCH = "project/state/video-generation/fetch/files"
MEDIA = EXC / "media/s3"
BLUR = EXC / "media/s3blur"
META = EXC / "data/media-s3"
EDL = EXC / "data/edl-s031-048-v1.json"
COMP = "composition-s031-048-v1.html"
RENDER = EXC / "renders/IRIS-EP01-s031-048-v1-picture.mp4"
DES = EXC / "flash/design/S31-48"

TAKES = {   # key: (take folder, unit, SHA-256 of the fetched mp4; checked in full on every --prep)
    "SG12b1": ("SG12-b-1", "SG12", "efd0b7a0abc0c14ef3346cf2505e2df596f058be02af7b5dbe6161a4561fa137"),
    "SG12a1": ("SG12-a-1", "SG12", "2a8b972e2909dd526051dfe1c188447116451f046ad395c66af40c5419e6b126"),
    "INS33a2": ("INS33-a-2", "INS33", "88667acdbd2b0893f852ac1d7c93a399686fdc5cc78bb236a920167f675f24e7"),
    "SG16xr2": ("SG16x-r-2", "SG16x", "d16b18f28a6bdeb4921c05c1172b09ecf615906d4c51031f1fd328f901a4fa86"),
    "INS37a1": ("INS37-a-1", "INS37", "6dd35e2799abee41dd250afa9192393c29b06eca0ecb9d2dde949b81222d2dd7"),
    "SG16yr2": ("SG16y-r-2", "SG16y", "b33c935adbcfdc09af927a0a28d37c200bd276ae5ee868457a52a180a0ea61d7"),
    "SG17Bp1": ("SG17B-p-1", "SG17B", "4de4bdb69755bece72ac46228e9631b6b5abfaeecfb4dca3951afa6072d700f2"),
    "SG17Ap2": ("SG17A-p-2", "SG17A", "b63f349bbe6b004b2429b165818da1624a13d67470d3cc0c9cde4996f3db047f"),
    "SG18xr1": ("SG18x-r-1", "SG18x", "d5dee82a57d635cb7098b4ec5a01ed6ac912a8ccd6902450543dc7b9a633a05c"),
    "INS41a1": ("INS41-a-1", "INS41", "5ed36dd46265638ec1c19a5ae0f6ad58fb27a99e49f4f92d84ab58c62b35f96d"),
    "SG18yr3": ("SG18y-r-3", "SG18y", "1afce3556edffd98ee5fb927482378b590df3cba694a10e5dfca9aa7724376ac"),
    "SG19a2": ("SG19-a-2", "SG19", "697c36de92d21875d69e03bdb4d308dfba2f36583f5a28fe23dcaec5e9b64197"),
    "MO15a1": ("MO15-a-1", "MO15", "031e2e2ddf0b43492df715cd5612be928389a0d6c823fff5c49d788fcd03d8dd"),
    "SG20xr1": ("SG20x-r-1", "SG20x", "cd4119ce1f587ac5abfc7528b492d557ab6a71998c0737f58fdf11e9593e36e3"),
}
# the stills: the S31-48 recommended picks (2944 wide) the user approved (「全按推荐」, r2 「图用推荐」); s036 P036/x
STILLS = {
    "S031B": "S031B/a-2944.png", "P032fix": "P032/a-fix-2944.png", "P032palm": "P032/a-palm-2944.png",
    "S033A": "S033A/a-2944.png", "P034": "P034/a-2944.png", "S035A": "S035A/a-2944.png", "S035B": "S035B/a-2944.png",
    "CANISTER": "S035B/canister-2-2944.png", "P036x": "P036/x.png", "S037A": "S037A/a-2944.png", "P038": "P038/a-2944.png",
    "S038B": "S038B/b-2944.png", "P040": "P040/a-2944.png", "S040Ba": "S040B/a2-fix-2944.png", "S040Bb": "S040B/b2-2944.png",
    "P043": "P043/a-2944.png", "P044": "P044/a-2944.png", "P045": "P045/c-2944.png", "P047": "CONT1124/p047-rb-c-2944.png",
}


def take_path(key: str) -> Path:
    folder, unit, h = TAKES[key]
    return PIL_ / f"sd-{folder}" / unit / FETCH / f"{h}.mp4"


def sync(song_t0: float, lag: float):
    """gate placement: song = song_t0 + clip - lag, so clip = song - song_t0 + lag"""
    return lambda t: t - song_t0 + lag


SG12_B1 = sync(133.873, 0.425)        # decisions 2026-11-25: b-1 s031a local lag +0.425 (clip 0.996-2.818)
SG12_A1 = sync(133.873, 0.267)        # a-1 lip span 140.05-141.29, lag about 0.267
SG16X = 161.338                       # SG16x window t0; per-sentence lags 0.41 / 0.57 / 0.90
L1, L2, L3 = 0.41, 0.57, 0.90
SG17B = sync(170.1094, 0.875)         # strict 170.804-172.024
SG17A = sync(170.1094, 0.600)         # strict 172.389-173.779
SG20X0 = 205.819                      # SG20x window t0, lag 0.425; the first picture held 0.153 s before clip 0

# id, song t0, t1, source, clip map (c0 or knots [(song, clip), ...]), crop, blur class, why
SHOTS = [
    {"id": "s031a", "t0": 134.4435, "t1": 136.2663, "src": "SG12b1", "c0": SG12_B1(134.4435), "cls": "A",
     "why": "SG12 b-1 clip 0.996-2.818 (local lag +0.425): 'ber twentieth. The search tool', the belt pulled on the bar line"},
    {"id": "s031b", "t0": 136.2663, "t1": 139.9234, "src": "still:S031B", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "A",
     "why": "what she sees: the three vending machines (one line, one still); names and error codes are graphics"},
    {"id": "s031c", "t0": 139.9234, "t1": 141.2934, "src": "SG12a1", "c0": SG12_A1(139.9234), "cls": "A",
     "why": "A-B-A back: SG12 a-1 lip span 140.05-141.29 (lag 0.267) 'No luck'; her turn left leads into s032 (user)"},
    {"id": "s032", "t0": 141.2934, "t1": 144.4978, "src": "still:P032palm",
     "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "xfade": {"img": "P032fix", "t": 141.7578, "frames": 5}}, "cls": "B",
     "why": "the guard's palm and her at the gate; the focus pulls palm -> her face on the 141.758 bar line (two plates)"},
    {"id": "s033a", "t0": 144.4978, "t1": 147.2493, "src": "still:S033A", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "A",
     "why": "the archive aisle, wide and still; the route map is drawn by the graphics"},
    {"id": "s033b", "t0": 147.2493, "t1": 149.0837, "src": "INS33a2", "c0": 1.41, "cls": "B",
     "why": "INS33 a-2 clip 1.41-3.25: the canister pushed in, the lid shut, her palm flat on it ('slipped through')"},
    {"id": "s034", "t0": 149.0837, "t1": 151.8237, "src": "still:P034", "move": {"zoom": [1.04, 1.04], "center": [0.5, 0.5], "jolt": 149.0837}, "cls": "A",
     "why": "149.084 hit: one jolt (shake + smear envelope, impact sharp), then still; the spec table is a graphic"},
    {"id": "s035a", "t0": 151.8237, "t1": 154.5752, "src": "still:S035A", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "step": [152.7409, 1.04]}, "cls": "A",
     "why": "the empty basket; one 1.04 push step on the 152.741 bar line with the clock counter"},
    {"id": "s035b", "t0": 154.5752, "t1": 155.9336, "src": "still:S035B", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "drop": 155.24, "land": 155.24}, "cls": "B",
     "why": "the canister drops into the basket and lands on 'call' (155.24), one landing shake (as s030)"},
    {"id": "s036a", "t0": 155.9336, "t1": 156.8508, "src": "still:P036x", "move": {"zoom": [1.0, 1.08], "center": [0.62, 0.42], "span": [155.9336, 159.5907]}, "cls": "A",
     "why": "SG15 dropped (user 「改静图 + 图形，不再拍」): the first-frame still P036/x, slow push; 'Ten oh two' off screen"},
    {"id": "s036b", "t0": 156.8508, "t1": 157.7680, "src": "black", "cls": "F",
     "why": "pure graphic frame on 'P zero': black, no screen; the P0 ticket is the Agentcut layer"},
    {"id": "s036c", "t0": 157.7680, "t1": 159.5907, "src": "still:P036x", "move": {"zoom": [1.0, 1.08], "center": [0.62, 0.42], "span": [155.9336, 159.5907]}, "cls": "A",
     "why": "back to the still, the push run on by song time; 'Pager screams. Out of my way' off screen"},
    {"id": "s037a", "t0": 159.5907, "t1": 161.4135, "src": "still:S037A", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "B",
     "why": "the engineer frozen with the phone; she soft behind; timestamps are graphics"},
    {"id": "s037b", "t0": 161.4135, "t1": 163.7007, "src": "SG16xr2", "cls": "A",
     "knots": [[161.4135, 161.4135 - SG16X + L1], [161.92, 161.92 - SG16X + L1], [162.26, 162.26 - SG16X + L2],
               [162.95, 162.95 - SG16X + L2], [163.15, 163.15 - SG16X + L3], [163.7007, 163.7007 - SG16X + L3]],
     "why": "SG16x r-2 aligned per sentence (user 「用 r-2 逐句对齐」): Stop it? lag 0.41, Let it stay? 0.57, It doesn't 0.90; "
            "the stretched pauses taken up in the gaps (1.47x, 2.65x)"},
    {"id": "s037c1", "t0": 163.7007, "t1": 164.1883, "src": "INS37a1", "c0": 1.25, "cls": "D",
     "why": "INS37 a-1 clip 1.25-1.74: his finger on stop (the 163.70 hit); insert -> D"},
    {"id": "s037c2", "t0": 164.1883, "t1": 165.0707, "src": "INS37a1", "c0": 3.10, "cls": "D",
     "why": "jump cut on the 164.188 beat to clip 3.10-3.98: the plug pulled, the light out (user 「用 a-1 跳切」)"},
    {"id": "s037d", "t0": 165.0707, "t1": 166.4755, "src": "SG16yr2", "c0": 1.367, "mw_dark": True, "cls": "A",
     "why": "SG16y r-2 clip 1.367-2.772 (lag 1.37): 'at twelve thirty-four'; the microwave window darkened (it was unplugged)"},
    {"id": "s038a", "t0": 166.4755, "t1": 168.2866, "src": "still:P038", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "A",
     "why": "on the stairs with the two half pages; the timeline graphic"},
    {"id": "s038b", "t0": 168.2866, "t1": 169.2154, "src": "still:S038B", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "B", "dither": True,
     "why": "insert on 'Half': the two half pages; the section's one photocopy dither (EV S0039)"},
    {"id": "s038c", "t0": 169.2154, "t1": 170.1094, "src": "still:P038", "move": {"zoom": [1.1, 1.1], "center": [0.60, 0.40]}, "cls": "A",
     "why": "back to s038a, cropped 1.1x ('Nothing more')"},
    {"id": "s039a", "t0": 170.1094, "t1": 171.9554, "src": "SG17Bp1", "c0": SG17B(170.1094), "keep_red": True, "cls": "A",
     "why": "SG17B p-1 first line (strict 170.804-172.024, lag 0.875): 'Bet it couldn't reach outside'"},
    {"id": "s039b", "t0": 171.9554, "t1": 173.7781, "src": "SG17Ap2", "c0": SG17A(171.9554), "keep_red": True, "cls": "A",
     "why": "jump cut on the 171.955 beat (between the lines) to SG17A p-2 (strict 172.389-173.779, lag 0.600): 'They found a gap instead'"},
    {"id": "s040a", "t0": 173.7781, "t1": 176.5181, "src": "still:P040", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "A",
     "why": "the guard booth, his mug already in her hand; the quote is a graphic"},
    {"id": "s040b", "t0": 176.5181, "t1": 178.3293, "src": "still:S040Ba",
     "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "swap": {"img": "S040Bb", "t": 177.4353}, "dim": {"t": 177.69, "to": 0.35, "frames": 5}}, "cls": "A",
     "why": "the monitor: the camera switches on the 177.435 beat, the screen goes dark on 'Eleven' (177.69)"},
    {"id": "s041a", "t0": 178.3293, "t1": 181.0228, "src": "SG18xr1", "c0": 1.120, "cls": "D", "coarse": True,
     "why": "SG18x r-1 clip 1.120-3.814: 'the lights go low' (strict); bridge D (light sigma: the lips must read); coarse dots pulse on the beats"},
    {"id": "s041b", "t0": 181.0228, "t1": 183.7627, "src": "INS41a1", "c0": 0.95, "cls": "C",
     "why": "INS41 a-1 clip 0.95-3.69: the cloth pulled down over the mannequin ('Top models paused'); C: the falling cloth smears"},
    {"id": "s041c", "t0": 183.7627, "t1": 185.5855, "src": "SG18yr3", "c0": 0.098, "cls": "D",
     "why": "SG18y r-3 clip 0.098-1.920 (lag 0): 'show', still through the breath, 'Octo-'"},
    {"id": "s042", "t0": 185.5855, "t1": 188.3603, "src": "SG19a2", "c0": 1.517, "cls": "A",
     "why": "SG19 a-2 clip 1.517-4.292: the quick change done by the 185.585 cut, the cloth falling; 'ber one, back to play'"},
    {"id": "s043", "t0": 188.3603, "t1": 192.9230, "src": "still:P043", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "E",
     "why": "the still wide shot in the breath: the window row, nothing moves; tags are graphics"},
    {"id": "s044", "t0": 192.9230, "t1": 195.6629, "src": "still:P044", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "A",
     "why": "192.923 hit, new paragraph: the binder handed over; RT-DRILL box"},
    {"id": "s045", "t0": 195.6629, "t1": 198.8673, "src": "still:P045", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "step": [196.5801, 1.03]}, "cls": "A",
     "why": "two booths from above (the copy's face hidden); one 1.03 push step on the 196.580 bar line"},
    {"id": "s046a", "t0": 198.8673, "t1": 201.5956, "src": "MO15a1", "c0": 0.0, "cls": "A", "mosaic": 199.73,
     "why": "MO15 a-1 clip 0-2.73: the hangers pushed (user 「用 a-1」); a 2-frame mosaic on 'kicks' (EV S0023)"},
    {"id": "s046b", "t0": 201.5956, "t1": 202.9656, "src": "MO15a1", "c0": 2.7283, "crop": (0.88, 0.14, 3.5), "press": 202.24, "cls": "B",
     "why": "3.5x crop of the same take (clip 2.73-4.10; her face out of frame): the stopwatch; the press made in post on 'clocks' (push-in + micro-shake)"},
    {"id": "s047", "t0": 202.9656, "t1": 205.2412, "src": "still:P047", "move": {"zoom": [1.0, 1.04], "center": [0.6, 0.6]}, "cls": "A",
     "why": "CONT1124/p047-rb-c: the strip under the partition, a slow push"},
    {"id": "s048", "t0": 205.2412, "t1": 208.4107, "src": "SG20xr1", "cls": "B",
     "knots": [[205.2412, 0.0], [SG20X0 - 0.425, 0.0], [208.4107, 208.4107 - SG20X0 + 0.425]],
     "why": "SG20x r-1 (lag 0.425; the first picture held 0.153 s): 'they were told which crack', two cracks on her lips"},
    {"id": "s048p", "t0": 208.4107, "t1": 209.3395, "src": "still:P047", "move": {"zoom": [2.5, 2.5], "center": [0.76, 0.88]}, "cls": "B",
     "why": "the paper strip close-up (p047 crop) covers the third 'crack' (r-1's mouth shut there; user 「r-1 + 纸条插镜盖住第三个 crack」)"},
]

KEEP_RED = (0.0, 0.84, 0.42, 1.0)        # s039: the door-crack line, fractions x0, y0, x1, y1 (measured 0.04-0.65 x, 0.92-1.0 y)
MW_BOX = (0.400, 0.459, 0.487, 0.566)     # s037d SG16y r-2: the lit microwave window (read off clip 1.4 and 2.7)
PRESS = {0: (0.0, 7.0), 1: (-5.0, -4.0), 2: (2.0, 2.0)}       # s046b micro-shake (px at 2304) by frame after the press


def frame_of(t: float) -> int:
    """section frame of song time t"""
    return int(round(t * FPS)) - SF0


def clip_time(s: dict, t: float) -> float:
    if "knots" in s:
        xs, ys = zip(*s["knots"])
        return float(np.interp(t, xs, ys))
    return s["c0"] + (t - s["t0"]) * s.get("speed", 1.0)


def keep_red(orig: np.ndarray, out: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = KEEP_RED
    o = out.copy()
    hh, ww = o.shape[:2]
    o[int(y0 * hh):int(y1 * hh), int(x0 * ww):int(x1 * ww)] = orig[int(y0 * hh):int(y1 * hh), int(x0 * ww):int(x1 * ww)]
    return o


def mw_dark(rgb: np.ndarray) -> np.ndarray:
    """the microwave window to the unplugged look of INS37 (dark glass, the mug a faint grey): 0.18 of the light, 35% of
    its colour, in the window box feathered 10 px"""
    hh, ww = rgb.shape[:2]
    x0, y0, x1, y1 = MW_BOX
    m = np.zeros((hh, ww), np.float32)
    m[int(y0 * hh):int(y1 * hh), int(x0 * ww):int(x1 * ww)] = 1
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    a = rgb.astype(np.float32) / 255
    d = a * 0.18
    g = d @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    d = g[..., None] + (d - g[..., None]) * 0.35
    out = a * (1 - m[..., None]) + d * m[..., None]
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def press(rgb: np.ndarray, j: int) -> np.ndarray:
    """s046b: frame j after the press: a push-in to 1.12 over 3 frames (ease out) round the stopwatch, with the shake"""
    if j < 0:
        return rgb
    z = 1.0 + 0.12 * (1 - (1 - min(1.0, (j + 1) / 3)) ** 2)
    dx, dy = PRESS.get(j, (0.0, 0.0))
    cx, cy = 0.63 * SEQ_W, 0.30 * SEQ_H                 # the stopwatch in the 3.5x crop
    cw, ch = SEQ_W / z, SEQ_H / z
    x0 = min(max(0, cx - cw / 2), SEQ_W - cw) - dx / z
    y0 = min(max(0, cy - ch / 2), SEQ_H - ch) - dy / z
    return np.asarray(Image.fromarray(rgb).transform((SEQ_W, SEQ_H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC))


def canister_layer() -> Image.Image:
    """the canister keyed off its light grey ground (the median of the border), cropped, at 0.26 of the picture width"""
    a = np.asarray(Image.open(DES / STILLS["CANISTER"]).convert("RGB"), np.float32) / 255
    border = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    bg = np.median(border, 0)
    dist = np.abs(a - bg).max(-1)
    al = np.clip((dist - 0.05) / 0.07, 0, 1)
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2)))
    ys, xs = np.nonzero(al > 128)
    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8)).convert("RGBA")
    im.putalpha(Image.fromarray(al))
    im = im.crop((xs.min() - 4, ys.min() - 4, xs.max() + 4, ys.max() + 4)).rotate(-14, Image.BICUBIC, expand=True)
    w = int(0.26 * SEQ_W)
    return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)


def drop_canister(bg: np.ndarray, can: Image.Image, t: float, land: float) -> np.ndarray:
    """the canister falls (gravity, 0.30 s from above the frame) and rests in the basket from `land`; the fall smeared"""
    fall = 0.30
    if t < land - fall:
        return bg
    yc0, yc1, xc = -0.30 * SEQ_H, 0.45 * SEQ_H, 0.50 * SEQ_W
    pos = lambda tt: yc0 + (yc1 - yc0) * min(1.0, max(0.0, (tt - land + fall) / fall)) ** 2
    out = Image.fromarray(bg).convert("RGBA")
    taps = [t - k / FPS / 5 for k in range(5)] if t < land else [t]
    acc = np.zeros((SEQ_H, SEQ_W, 4), np.float32)
    for tt in taps:
        layer = Image.new("RGBA", (SEQ_W, SEQ_H), (0, 0, 0, 0))
        layer.paste(can, (int(xc - can.width / 2), int(pos(tt) - can.height / 2)), can)
        acc += np.asarray(layer, np.float32)
    lay = Image.fromarray((acc / len(taps)).astype(np.uint8), "RGBA")
    return np.asarray(Image.alpha_composite(out, lay).convert("RGB"))


def load_still(key: str) -> Image.Image:
    return Image.open(DES / STILLS[key]).convert("RGB")


def prep_still(s: dict, d: Path) -> dict:
    key = s["src"].split(":", 1)[1]
    img = load_still(key)
    mv = s["move"]
    f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
    n = f1 - f0
    moving = mv["zoom"][0] != mv["zoom"][1] or any(k in mv for k in ("step", "jolt", "land", "xfade", "swap", "dim", "drop"))
    alt = load_still(mv["xfade"]["img"]) if "xfade" in mv else load_still(mv["swap"]["img"]) if "swap" in mv else None
    can = canister_layer() if "drop" in mv else None
    log, orange, done = [], None, {}
    sp0, sp1 = (frame_of(mv["span"][0]), frame_of(mv["span"][1])) if "span" in mv else (f0, f1)
    for k in range(n if moving else 1):
        f = f0 + k
        t = (SF0 + f) / FPS
        u = (f - sp0) / max(1, sp1 - 1 - sp0)
        if mv.get("ease"):
            u = 0.5 - 0.5 * np.cos(np.pi * u)
        z = mv["zoom"][0] + (mv["zoom"][1] - mv["zoom"][0]) * u
        cx, cy = mv["center"]
        if "step" in mv and f >= frame_of(mv["step"][0]):
            z *= mv["step"][1]
        shake, smear, prev = (0.0, 0.0), 0.0, (0.0, 0.0)
        for kk, table in (("jolt", SHAKE), ("land", LAND)):
            if kk in mv:
                j = f - frame_of(mv[kk])
                if j in table:
                    shake = table[j]
                    smear = SMEAR.get(j, 0.0) * (1.0 if kk == "jolt" else 0.5)
                    prev = table.get(j - 1, (0.0, 0.0))

        def view(im: Image.Image, sx: float, sy: float) -> np.ndarray:
            v = still_view(im, z, cx, cy, sx, sy).astype(np.float32)
            if alt is not None and "xfade" in mv:
                w = np.clip((f - frame_of(mv["xfade"]["t"]) + 1) / mv["xfade"]["frames"], 0, 1)
                if w > 0:
                    v = v * (1 - w) + still_view(alt, z, cx, cy, sx, sy).astype(np.float32) * w
            if alt is not None and "swap" in mv and f >= frame_of(mv["swap"]["t"]):
                v = still_view(alt, z, cx, cy, sx, sy).astype(np.float32)
            if can is not None:
                v = drop_canister(np.clip(v + 0.5, 0, 255).astype(np.uint8), can, t, mv["drop"]).astype(np.float32)
            if "dim" in mv:
                g = np.clip((f - frame_of(mv["dim"]["t"]) + 1) / mv["dim"]["frames"], 0, 1)
                v = v * (1 - g * (1 - mv["dim"]["to"]))
            return v

        xw = float(np.clip((f - frame_of(mv["xfade"]["t"]) + 1) / mv["xfade"]["frames"], 0, 1)) if "xfade" in mv else 0.0
        dg = float(np.clip((f - frame_of(mv["dim"]["t"]) + 1) / mv["dim"]["frames"], 0, 1)) if "dim" in mv else 0.0
        ck = (round(z, 6), shake, smear, xw, "swap" in mv and f >= frame_of(mv["swap"]["t"]), dg,
               round(t, 4) if can is not None and t >= mv["drop"] - 0.30 else None)
        if ck in done:                                   # the same picture as an earlier frame (a held still between steps)
            Image.fromarray(done[ck]).save(d / f"{k:04d}.jpg", quality=93, subsampling=0)
            log.append({"k": k, "zoom": round(z, 4), "shake": shake, "smear": smear})
            continue
        if smear > 0:
            taps = 15
            acc = np.zeros((SEQ_H, SEQ_W, 3), np.float32)
            for tt in np.linspace(0, 1, taps):
                acc += view(img, prev[0] + (shake[0] - prev[0]) * (1 - smear + smear * tt), prev[1] + (shake[1] - prev[1]) * (1 - smear + smear * tt))
            rgb = np.clip(acc / taps + 0.5, 0, 255).astype(np.uint8)
        else:
            rgb = np.clip(view(img, *shake) + 0.5, 0, 255).astype(np.uint8)
        rgb, st = pm.tail_lights_to_orange(rgb)
        if orange is None:
            orange = st
        done[ck] = rgb
        Image.fromarray(rgb).save(d / f"{k:04d}.jpg", quality=93, subsampling=0)
        log.append({"k": k, "zoom": round(z, 4), "shake": shake, "smear": smear})
    srcs = [DES / STILLS[key]] + ([DES / STILLS[mv.get("xfade", mv.get("swap", {})).get("img")]] if alt is not None else []) \
        + ([DES / STILLS["CANISTER"]] if can is not None else [])
    return {"still": str(srcs[0].relative_to(REPO)), "still_sha256": sha(srcs[0]),
            "stills": [{"path": str(p.relative_to(REPO)), "sha256": sha(p)} for p in srcs], "frames": n, "pictures": n if moving else 1,
            "fixed": not moving, "move": mv, "orange_first": orange, "log": [r for r in log if r["shake"] != (0.0, 0.0)][:12]}


def prep_black(s: dict, d: Path) -> dict:
    Image.new("RGB", (SEQ_W, SEQ_H), (0, 0, 0)).save(d / "0000.jpg", quality=93, subsampling=0)
    return {"black": True, "frames": frame_of(s["t1"]) - frame_of(s["t0"]), "pictures": 1, "fixed": True}


def prep_clip(s: dict, d: Path) -> dict:
    clip = take_path(s["src"])
    if not clip.exists():
        raise SystemExit(f"{s['id']}: take missing {clip}")
    h = sha(clip)
    if h != TAKES[s["src"]][2]:
        raise SystemExit(f"{s['id']}: SHA-256 differs")
    pts = pm.probe_pts(clip)
    worst = max(abs(p - k / 24.0) for k, p in enumerate(pts))
    if worst > 1 / 120 + 1e-3:
        raise SystemExit(f"{s['id']}: pictures are not a steady 24/s (worst {worst:.4f})")
    f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
    fmap = []
    for f in range(f0, f1):
        t = (SF0 + f) / FPS
        c = clip_time(s, t)
        fmap.append({"f": f, "t": round(t, 4), "clip_t": round(c, 4), "idx": min(len(pts) - 1, max(0, int(round(c * 24))))})
    wanted = {m["idx"] for m in fmap}
    cache, hue = {}, {}
    for i, rgb in decode(clip, wanted, s.get("crop")):
        out, st = pm.tail_lights_to_orange(rgb)
        if s.get("keep_red"):
            out = keep_red(rgb, out)
        if s.get("mw_dark"):
            out = mw_dark(out)
        hue[i] = st
        cache[i] = out.copy()
    if wanted - set(cache):
        raise SystemExit(f"{s['id']}: pictures not decoded {sorted(wanted - set(cache))[:5]}")
    for k, m in enumerate(fmap):
        rgb = cache[m["idx"]]
        if s.get("press"):
            rgb = press(rgb, m["f"] - frame_of(s["press"]))
        Image.fromarray(rgb).save(d / f"{k:04d}.jpg", quality=93, subsampling=0)
    return {"clip": str(clip.relative_to(REPO)), "clip_sha256": h, "pictures": len(pts), "frames": len(fmap),
            "first": fmap[0], "last": fmap[-1], "crop": s.get("crop"), "knots": s.get("knots"),
            "repeats": sum(1 for a, b in zip(fmap, fmap[1:]) if a["idx"] == b["idx"]),
            "skips": sum(1 for a, b in zip(fmap, fmap[1:]) if b["idx"] - a["idx"] > 1),
            "map": [m["idx"] for m in fmap], "orange_px_max": max(v["shifted_px"] for v in hue.values()),
            "keep_red_box": KEEP_RED if s.get("keep_red") else None, "mw_box": MW_BOX if s.get("mw_dark") else None,
            "press": s.get("press")}


def prep(want: list[str]) -> int:
    META.mkdir(parents=True, exist_ok=True)
    for s in SHOTS:
        if want and s["id"] not in want:
            continue
        d = MEDIA / s["id"]
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        m = prep_black(s, d) if s["src"] == "black" else prep_still(s, d) if s["src"].startswith("still:") else prep_clip(s, d)
        m = {"shot": s["id"], "t0": s["t0"], "t1": s["t1"], "why": s["why"], **m}
        (META / f"{s['id']}.json").write_text(json.dumps(m, indent=1))
        print(s["id"], {k: m.get(k) for k in ("frames", "pictures", "repeats", "skips", "orange_px_max")}, flush=True)
    return 0


# ---------------------------------------------------------------- blur classes (section2.py's, on these pictures)
B_CFG = {   # u2netp matte on the whole picture (section2's fix: the region follows the subject), background sigma (2304 px)
    "s032": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 16.0,     # the palm first (u2netp's subject on the whole picture), then
             "after": {"t": 141.7578, "frames": 5, "region": (0.55, 0.0, 0.90, 1.0)}},   # her: the focus pull with the plates
    "s033b": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 16.0},
    "s035b": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 14.0},
    "s037a": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 16.0},
    "s038b": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 14.0},
    "s046b": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 16.0},
    "s048": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 16.0},
    "s048p": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 14.0},
}
C_CFG = {"s041b": {"iso": 5.0, "flow": {"q": 2, "bs": 32, "step": 8}, "ramp": [(0, 1.6), (200, 1.6)]}}
D_SIGMA, E_SIGMA = 9.0, 13.0
D_SIGMA_SUNG = {"s041a": 4.5, "s041c": 4.5}      # bridge D on a singing face: lighter so the lips read


def blur_c(sid: str, files: list[Path], dst: Path, k0: int = 0, k1: int | None = None) -> dict:
    """prep_blur_v3.do_c (no matte; the ramp's constant gain) on pictures k0..k1 of the shot, so a long shot can be done
    in parts (--blur-c <id> <k0> <k1>): flow to the next picture, the shutter along it, the iso blur where it moves"""
    import prep_blur_v3 as PB
    c = C_CFG[sid]
    n = len(files)
    xs, ys = zip(*c["ramp"])
    gains = np.interp(np.arange(n), xs, ys)
    imgs = {}
    ld = lambda k: imgs.setdefault(k, PB.load(files[k]))
    for k in range(k0, n if k1 is None else min(n, k1)):
        im, g = ld(k), float(gains[k])
        fa, fb = (im, ld(k + 1)) if k + 1 < n else (ld(k - 1), im)
        v = PB.flow(fa, fb, **c["flow"])
        out = PB.shutter(im, v, g)
        mag = np.hypot(v[..., 0], v[..., 1])
        w = np.clip(mag * g / 40.0, 0, 1)
        iso = np.asarray(Image.fromarray(out).filter(ImageFilter.GaussianBlur(c["iso"])), np.float32)
        out = np.clip(out * (1 - w[..., None]) + iso * w[..., None] + 0.5, 0, 255).astype(np.uint8)
        PB.save(out, dst / files[k].name)
    return {"class": "C", "pictures": n, "ramp": c["ramp"], "iso_px": c["iso"], "done": [k0, n if k1 is None else min(n, k1)]}


def blur(want: list[str]) -> int:
    import prep_blur_v3 as PB
    import prep_dof as PD
    out = {}
    for s in SHOTS:
        sid, cls = s["id"], s["cls"]
        if want and sid not in want:
            continue
        if cls in ("A", "F"):
            continue
        src = MEDIA / sid
        files = sorted(src.glob("*.jpg"))
        dst = BLUR / sid
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        if cls == "B":
            c = B_CFG[sid]
            imgs = [PB.load(f) for f in files]
            mats = [PB.region_matte(i, c["region"]) for i in imgs]
            if "after" in c:                          # the matte follows the focus pull (the still's xfade)
                a = c["after"]
                for k, im in enumerate(imgs):
                    w = float(np.clip((frame_of(s["t0"]) + k - frame_of(a["t"]) + 1) / a["frames"], 0, 1))
                    if w > 0:
                        mats[k] = mats[k] * (1 - w) + PB.region_matte(im, a["region"]) * w
            for k, (f, im) in enumerate(zip(files, imgs)):
                m = np.mean(mats[max(0, k - 1):k + 2], 0)
                PB.save(PD.dof(im, m, c.get("protect"), c["bg"]), dst / f.name)
            out[sid] = {"class": "B", "pictures": len(files), "bg_sigma_px": c["bg"], "region": c["region"],
                        "matte_share_0": round(float((mats[0] > 0.5).mean()), 4)}
        elif cls in ("D", "E"):
            sg = D_SIGMA_SUNG.get(sid, D_SIGMA) if cls == "D" else E_SIGMA
            g = ImageFilter.GaussianBlur(sg)
            for f in files:
                PB.save(np.asarray(Image.open(f).convert("RGB").filter(g)), dst / f.name)
            out[sid] = {"class": cls, "pictures": len(files), "sigma_px": sg}
        elif cls == "C":
            out[sid] = blur_c(sid, files, dst)
        out[sid]["sha256_0000"] = sha(dst / "0000.jpg")
        (EXC / "data/blur-s3").mkdir(exist_ok=True)
        (EXC / "data/blur-s3" / f"{sid}.json").write_text(json.dumps(out[sid], indent=1))
        print(sid, out[sid], flush=True)
    return 0


# ---------------------------------------------------------------- EDL / composition
A_GRADE = {"uSoftMix": 0.2, "uCapSoft": 1}
D_GRADE = {"uSoftMix": 1.0, "uToneBP": -0.012, "uToneWP": 1.2, "uContrast": 0.95, "uCapSoft": 1}
E_GRADE = {"uCapSoft": 1}
DOTS = {"uLineAM": 0, "uDotAM": 0.42, "uDotPitch": 4.2, "uDotAng": 0.0}               # verse dots (opening_v2.py DOTS)
COARSE_DOTS = {"uLineAM": 0, "uDotAM": 0.42, "uDotPitch": 7.2, "uDotAng": 1.3788}     # opening_v2.py COARSE_DOTS


def check_cuts(beats: list[float]) -> list[dict]:
    out = []
    for s in SHOTS[1:]:
        t = s["t0"]
        nb = min(beats, key=lambda b: abs(b - t))
        f = frame_of(t)
        ft = (SF0 + f) / FPS
        row = {"cut": s["id"], "t": t, "beat": nb, "dt": round(t - nb, 4), "frame": f, "song_frame": SF0 + f,
               "frame_t": round(ft, 4), "frame_dt_beat": round(ft - nb, 4)}
        if abs(t - nb) > 0.03 or abs(ft - nb) > 0.03:
            raise SystemExit(f"cut {s['id']} at {t} is {t - nb:+.4f} s from the beat {nb}")
        out.append(row)
    return out


def fx_of(s: dict, beats: list[float]) -> list[dict]:
    f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
    fx = []
    if s["src"] == "black":
        fx.append({"f0": f0, "f1": f1, "grade": {"uBlack": 1}})
    if s.get("dither"):
        fx.append({"f0": f0, "f1": f1, "grade": {"uDither": 1, "uDotAM": 0}})
    if s.get("mosaic"):
        m = frame_of(s["mosaic"])
        fx.append({"f0": m, "f1": m + 2, "grade": {"uMosaic": 20}})
    if s.get("coarse"):
        for b in beats:
            g = frame_of(b)
            if f0 < g < f1 - 1:
                fx.append({"f0": g, "f1": g + 2, "grade": COARSE_DOTS})
    return fx


def build() -> int:
    from build import levels
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())["beats"]
    cuts = check_cuts(beats)
    shots, lv = [], {}
    for s in SHOTS:
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        m = json.loads((META / f"{s['id']}.json").read_text())
        if m["frames"] != f1 - f0:
            raise SystemExit(f"{s['id']}: {m['frames']} prepared frames for {f1 - f0} (rerun --prep)")
        d = BLUR / s["id"] if (BLUR / s["id"]).exists() and s["cls"] not in ("A", "F") else MEDIA / s["id"]
        n = len(list(d.glob("*.jpg")))
        if n != (1 if m.get("fixed") else m["frames"]):
            raise SystemExit(f"{s['id']}: {d} holds {n} pictures, not {1 if m.get('fixed') else m['frames']}")
        seq = {"dir": str(d.relative_to(EXC)), "count": n}
        if m.get("fixed"):
            seq["fixed"] = 0
        row = {"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": f0, "f1": f1, "kind": "clip", "chapter": "c5",
               "take": s["src"], "take_sha256": m.get("clip_sha256") or m.get("still_sha256"), "seq": seq,
               "blur": {"cls": s["cls"], "grade": D_GRADE if s["cls"] == "D" else E_GRADE if s["cls"] in ("E", "F") else A_GRADE}}
        if s["src"] != "black":
            row["screen"] = DOTS
        fx = fx_of(s, beats)
        if fx:
            row["fx"] = fx
        shots.append(row)
        lv.update(levels([{**row, "seq": {**seq, "count": n}}], {}))
    if shots[0]["f0"] != 0 or shots[-1]["f1"] != N or any(a["f1"] != b["f0"] for a, b in zip(shots, shots[1:])):
        raise SystemExit(f"the shots do not tile section frames 0-{N - 1}")
    edl = {"version": 16, "opening": True, "opening_v2": True, "opening_v3": True, "section": "s031-048-v1", "picture_only": True,
           "fps": FPS, "W": W, "H": H, "offset": OFFSET, "end": SF1 / FPS, "frames": N, "song_frame0": SF0, "shots": shots,
           "images": {}, "levels": lv, "lines": [], "beats": [], "downbeats": [], "snare": [], "kick": [], "tracks": {}, "cuts": cuts}
    EDL.write_text(json.dumps(edl, indent=1))
    dur = N / FPS
    (EXC / COMP).write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 s031-s048 picture v1 (song frames {SF0}-{SF1 - 1}, s015-030 print)</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-start="0" data-duration="{dur:.6f}" data-ex-edl="data/{EDL.name}" data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{dur:.6f}" data-track-index="0"></canvas>
</div>
<script src="engine.js"></script>
</body>
</html>
""", encoding="utf-8")
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(EXC / "src/main.js"), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={EXC / 'engine.js'}", "--log-level=warning"], check=True)
    print(json.dumps({"shots": len(shots), "frames": N, "classes": {s["id"]: s["cls"] for s in SHOTS},
                      "cuts_max_frame_dt": max(abs(c["frame_dt_beat"]) for c in cuts)}, indent=1))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--prep" in sys.argv:
        raise SystemExit(prep(args))
    if "--blur-c" in sys.argv:                       # <id> <k0> <k1>: part of a C shot (the folder is kept)
        sid, k0, k1 = args[0], int(args[1]), int(args[2])
        fs = sorted((MEDIA / sid).glob("*.jpg"))
        (BLUR / sid).mkdir(parents=True, exist_ok=True)
        r = blur_c(sid, fs, BLUR / sid, k0, k1)
        if len(list((BLUR / sid).glob("*.jpg"))) == len(fs):
            r["sha256_0000"] = sha(BLUR / sid / "0000.jpg")
            r["done"] = [0, len(fs)]
            (EXC / "data/blur-s3").mkdir(exist_ok=True)
            (EXC / "data/blur-s3" / f"{sid}.json").write_text(json.dumps(r, indent=1))
        print(sid, r, flush=True)
        raise SystemExit(0)
    if "--blur" in sys.argv:
        raise SystemExit(blur(args))
    if "--build" in sys.argv:
        raise SystemExit(build())
    raise SystemExit(__doc__)
