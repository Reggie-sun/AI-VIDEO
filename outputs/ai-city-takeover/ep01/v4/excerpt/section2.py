#!/usr/bin/env python3
"""IRIS EP01 s015-s030 review cut v1 (2026-11-23): song 59.2341-134.4435 s, the takes and stills the user chose for
s015-s030 (pilot/s015-030/HANDOFF-2026-11-23.md; outputs/ai-city-takeover/logs/decisions.md 2026-11-21..23), through
the opening v3 print (opening_v2.py --build-3: per-shot blur classes, the chorus line screen, the verse dot screen),
picture only; the EV graphics, lyrics and the song are the Agentcut layer (section2_layers.py). Run from the repo root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section2.py --prep [ids...]   # media/s2/<id>, data/media-s2/<id>.json
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section2.py --blur [ids...]   # media/s2blur/<id> (classes B/C/D/E)
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section2.py --build           # data/edl-s015-030-v1.json, composition, engine.js
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-s015-030-v1.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-s015-030-v1-picture.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu

Frames: section frame k shows song frame 1422 + k (song time (1422 + k) / 24, as the opening v3 film's frame 1421 is the
last before the s015 cut, round(24 * 59.2341) = 1422); 1805 frames to song frame 3227 = round(24 * 134.4435). Every cut
is a beat of beats.json (|cut - beat| <= 0.03 s and the cut frame's time within 0.03 s of it).

Pictures (all repairs in the prepared pictures; takes and plates untouched):
- clips: the take's pictures (a steady 24/s on its 60 fps header, checked as prep_media.prep_clip) at clip time
  c(t) = c0 + (t - t0) * speed (or piecewise "knots"), decoded at 2304x1296 from the whole 3840x2160 frame or from a
  digital crop of it ("crop": centre x, y as fractions, zoom; zoom 2 = the author's lossless 2x of a 4K source).
- red: prep_media.tail_lights_to_orange on every picture (saturated reds outside her grown matte to orange: only her
  left ear lamp stays red); s029 SG11 m-1's pager LED (inside her matte, in her hand) by a local bounded repair
  (pager_red_to_amber: the LED's magenta-side red in the pager's region below her head set to amber 38 deg; her skin,
  hue >= 0, is left alone), recorded per picture.
- stills: the 1672x941 plate drawn per frame at 2304x1296 through its move (zoom / centre / shake), so a move is in the
  pictures; s025's jolt and s030's landing shake add the author's smear envelope (impact sharp, +1 full, +2 0.45).
- s028's floodlights: the first picture held 5 frames, dark for 3, on with one flicker on the 119.7801 accent.
"""
from __future__ import annotations

import hashlib
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

SF0, SF1 = 1422, 3227                    # song frames shown: 1422 .. 3226
N = SF1 - SF0                            # 1805
OFFSET = SF0 / FPS                       # 59.25
SEQ_W, SEQ_H = pm.SEQ_W, pm.SEQ_H
PIL_ = V4 / "pilot"
FETCH = "project/state/video-generation/fetch/files"
MEDIA = EXC / "media/s2"
BLUR = EXC / "media/s2blur"
META = EXC / "data/media-s2"
EDL = EXC / "data/edl-s015-030-v1.json"
COMP = "composition-s015-030-v1.html"
RENDER = EXC / "renders/IRIS-EP01-s015-030-v1-picture.mp4"
PLATES = V4 / "board/plates"
P018E = EXC / "flash/design/S15-30/P018E/w1-local-car.png"   # p018-w1 with only the car box from P018E/a.png (w1-local-car.json)

TAKES = {
    "SG05m2": ("SG05-m-2", "SG05", "98f78c78a45a8bbb6fd628e9a804429272a002ff6c734fa03b1a02661490cf05"),
    "SG06p1": ("SG06-p-1", "SG06", "335ce608b539e909bff4441b9801d23c0ee54bef4a643ae1ebdcf1c849c8a003"),
    "SG07m1": ("SG07-m-1", "SG07", "d1740013cbd0c2199358c3b68d47dd624e36d609ad064602e407d21e1cd0e55b"),
    "SG07m2": ("SG07-m-2", "SG07", "8a72e1fc311d7634bdca4201de2e163209218e4c56173ac728aca62b6e290cb9"),
    "MO09n1": ("MO09-n-1", "MO09", "47af56000c1461585e72cb8470eb9a38388151b10a628117004b437d38e7efb1"),
    "MO10n2": ("MO10-n-2", "MO10", "a440c0e92229ee18aaece587f6fec3241446b7e74477174902c3177566004129"),
    "SG08m1": ("SG08-m-1", "SG08", "5e2a2e336d5cc3ae7badad683a2459db1bd33cba6808203d1bede982e09cbf09"),
    "SG09m2": ("SG09-m-2", "SG09", "32ca57af7e818e94cf5955c67f3f5931d28521036dda1400f2439d2d35e20c15"),
    "SG10m2": ("SG10-m-2", "SG10", "bfcd2a3ba6bf8d2db424238ac733f06ccfd645e4438a5e00e8082b3a516bf4bf"),
    "MO12p2": ("MO12-p-2", "MO12", "d916bd083352d65d4e010db4c4bfd2c8935ea165d23ffcd10937b801d66a7759"),
    "MO13n1": ("MO13-n-1", "MO13", "47c40d7a1b9a60c02cd432e5262b2bec2f557e5401b84e7cd9f71ac8af5499a6"),
    "SG11m1": ("SG11-m-1", "SG11", "90e1af07bc7a3be8e84e5d22ec4ab86eea4ec405789711ca3a93ebbc0fcaa186"),
}
INS16 = ("pilot/sd-INS16-n-2/INS16/repair/INS16-n-2-amber.mp4", "128bacdb")


def take_path(key: str) -> Path:
    if key == "INS16":
        return V4 / INS16[0]
    folder, unit, h = TAKES[key]
    return PIL_ / f"sd-{folder}" / unit / FETCH / f"{h}.mp4"


# Song-time placements (sync.json "placement": song = song_t0 + clip - lag, so clip = song - song_t0 + lag)
def sync(song_t0: float, lag: float):
    return lambda t: t - song_t0 + lag


SG05_A = sync(58.7, 0.986)            # decisions 2026-11-22: lag 0.986 holds song 58.3-62.1
SG05_B = sync(58.7, 1.49)             # lag 1.49 holds 61.8-63.6
SG06 = sync(65.517, 0.0001)           # synced to clip 2.15 (song 67.67), then +0.227 (the take runs 0.227 s ahead)
SG07_M1 = sync(71.1808, -0.2249)      # m-1 span clip 0.75-1.73 = song 72.156-73.136
SG07_M2 = sync(71.1808, -2.449)       # m-2 placement (clip 0 = 73.6298); its mouth holds 75.13-77.60
SG08 = sync(94.507, -0.3499)          # copy (waveform) placement; she does not open her mouth (user: not lip-synced)
SG09 = sync(102.64, 0.5)              # lag 0.5: 103.29-106.50
SG10_B = sync(109.56, 1.22)           # B span 113.37-116.12, lag 1.22
SG10 = sync(109.56, 1.183)            # placement (clip 0 = 108.377) for the engineer's pictures

# id, song t0, t1, source, clip map (c0 = clip time at t0; or knots [(song, clip), ...]), crop, blur class, why
SHOTS = [
    {"id": "s015a", "t0": 59.2341, "t1": 61.9741, "src": "SG05m2", "c0": SG05_A(59.2341), "cls": "A",
     "why": "sung: lag 0.986 span (Ten oh two... pager blew); the face must read"},
    {"id": "s015b", "t0": 61.9741, "t1": 63.8317, "src": "SG05m2", "c0": SG05_B(61.9741), "cls": "A",
     "why": "sung: lag 1.49 span (P zero, baby); jump cut on the 61.9741 beat"},
    {"id": "s015c", "t0": 63.8317, "t1": 65.6660, "src": "SG05m2", "c0": 3.0, "crop": (0.60, 0.75, 2.0), "cls": "D",
     "why": "cover for 'that's my cue' (mouth off-sync): 4K 2x crop of the pager in her hand at her waist; inserts are D in EV"},
    {"id": "s016a", "t0": 65.6660, "t1": 67.5004, "src": "SG06p1", "c0": SG06(65.6660), "cls": "A",
     "why": "sung at the payphone (Phoned a friend), sync to clip 2.15"},
    {"id": "s016b", "t0": 67.5004, "t1": 69.3464, "src": "SG06p1", "c0": SG06(67.5004) + 0.227, "cls": "A",
     "why": "jump cut on the 67.5004 beat to the take's +0.227 s (it runs ahead after clip 2.2): through D N S"},
    {"id": "s016i", "t0": 69.3464, "t1": 71.1808, "src": "INS16", "c0": 0.0, "cls": "D",
     "why": "INS16 amber repair (128bacdb) clip 0-1.83: the handset swinging on 'Got half an answer'; insert -> D"},
    {"id": "s017p1", "t0": 71.1808, "t1": 72.0980, "src": "SG07m2", "c0": 0.30, "crop": (0.27, 0.55, 2.0), "cls": "B",
     "why": "the engineer's open palm and laptop on the kerb (A of A-B-A; 'couldn't guess'), 2x crop; his hand sharp, street soft"},
    {"id": "s017a", "t0": 72.0980, "t1": 73.0151, "src": "SG07m1", "c0": SG07_M1(72.0980), "cls": "A",
     "why": "m-1 A span (72.16-73.14): she sings 'Pick up' to him"},
    {"id": "s017p2", "t0": 73.0151, "t1": 75.3139, "src": "SG07m2", "c0": 0.30 + (73.0151 - 71.1808), "crop": (0.27, 0.55, 2.0), "cls": "B",
     "why": "back to his palm, the take run on by song time (A-B-A) over 'pick up, it's your call' and the breath"},
    {"id": "s017s", "t0": 75.3139, "t1": 77.6011, "src": "SG07m2", "c0": SG07_M2(75.3139), "cls": "A",
     "why": "m-2 lip-synced span (P zero. That's): she sings to him, the camera still"},
    {"id": "s017b", "t0": 77.6011, "t1": 78.9827, "src": "SG07m2", "c0": 6.90, "crop": (0.32, 0.62, 2.0), "cls": "A",
     "why": "accent 77.60: the pager pressed into his palm, fingers close (clip 6.9-8.28), 2x crop; the action must read"},
    {"id": "s018", "t0": 78.9827, "t1": 84.0214, "src": "still:P018", "move": {"zoom": [1.12, 1.0], "center": [0.55, 0.5], "ease": True}, "cls": "A",
     "why": "instrumental: EV S0002 high overhead still, slow pull-out to show the scale"},
    {"id": "s019", "t0": 84.0214, "t1": 87.7018, "src": "MO09n1", "c0": 0.0, "speed": 4.0 / (87.7018 - 84.0214), "cls": "C",
     "why": "the quick change (n-1 clip 0-4.0 at 1.09x): the strip-off and the coat thrown on smeared, as EV's fast moves"},
    {"id": "s020", "t0": 87.7018, "t1": 91.3821, "src": "MO10n2", "c0": 0.0, "cls": "A", "dots_from": 88.6190,
     "why": "the curtain drops on the 88.62 accent, cut where the board starts to fall (clip 3.68); verse dots from 88.62"},
    {"id": "s021", "t0": 91.3821, "t1": 95.0393, "src": "still:p021-b1", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "step": [93.37, 1.06]}, "cls": "B", "dots": True,
     "why": "still for a line a graphic tells better (Four thousand apps); one 1.06 push step on 'Four' with the counter"},
    {"id": "s022", "t0": 95.0393, "t1": 99.6252, "src": "SG08m1", "c0": SG08(95.0393), "cls": "B", "dots": True,
     "why": "witness box, not lip-synced (user): she pats the cards square; the gallery behind soft"},
    {"id": "s022b", "t0": 99.6252, "t1": 101.4480, "src": "SG08m1", "c0": SG08(99.6252), "crop": (0.25, 0.75, 2.0), "cls": "D", "dots": True,
     "why": "the cards under her palm (2x crop) on 'They stopped...'; insert -> D"},
    {"id": "s023", "t0": 101.4480, "t1": 103.2940, "src": "still:p023-b1", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5]}, "cls": "B", "dots": True,
     "why": "one line, one still: the blank visitor badge (Model guests); no move"},
    {"id": "s024", "t0": 103.2940, "t1": 106.4983, "src": "SG09m2", "c0": SG09(103.2940), "cls": "A",
     "why": "chorus accent: All hands! sung at the strap (lag 0.5, 103.29-106.50)"},
    {"id": "s025", "t0": 106.4983, "t1": 110.6199, "src": "still:p025-b1", "move": {"zoom": [1.04, 1.04], "center": [0.5, 0.5], "jolt": 108.8087}, "cls": "C",
     "why": "still from 106.50 (covers 'Ev-'); the train jolts on the 108.81 downbeat (shake + smear envelope), otherwise still"},
    {"id": "s026a", "t0": 110.6199, "t1": 112.4542, "src": "SG10m2", "c0": SG10(110.6199), "crop": (0.30, 0.38, 2.0), "cls": "A",
     "why": "the engineer asleep (2x crop, her mouth not shown) on 'reason you're'"},
    {"id": "s026b", "t0": 112.4542, "t1": 113.3714, "src": "SG10m2", "c0": 4.40, "crop": (0.33, 0.33, 2.5), "cls": "A",
     "why": "'awake': he opens his eyes (clip 4.4-5.3), the A-B-A insert"},
    {"id": "s026c", "t0": 113.3714, "t1": 116.1230, "src": "SG10m2", "c0": SG10_B(113.3714), "cls": "A",
     "why": "back to her singing 'I'm the call you had to take' (B span, lag 1.22)"},
    {"id": "s027", "t0": 116.1230, "t1": 119.7801, "src": "MO12p2", "c0": 0.0, "cls": "C",
     "why": "All hands: she walks away down the platform (clip 0-3.66); EV's walk-away shots carry a light shutter smear"},
    {"id": "s028a", "t0": 119.7801, "t1": 121.1617, "src": "MO13n1", "knots": [[119.7801, 0.0], [119.7801 + 5 / 24, 0.0], [121.1617, 121.1617 - 119.7801 - 5 / 24]],
     "lights": True, "cls": "A", "why": "accent 119.78: the floodlights come on (held first picture, dark 3 frames, one flicker), then she starts"},
    {"id": "s028b", "t0": 121.1617, "t1": 122.0557, "src": "MO13n1", "c0": 1.20, "crop": (0.66, 0.60, 3.0), "cls": "D",
     "why": "'pager blew': the lit pager on her waist (3x crop of the take, before the reverse walk); insert -> D"},
    {"id": "s028c", "t0": 122.0557, "t1": 123.9017, "src": "MO13n1", "c0": 3.60, "cls": "A",
     "why": "back to the stair: she climbs (clip 3.6-5.45; the reverse walk 1.4-3.6 cut out)"},
    {"id": "s028d", "t0": 123.9017, "t1": 125.7244, "src": "MO13n1", "knots": [[123.9017, 3.60 + (123.9017 - 122.0557)], [124.5357, 6.08], [125.7244, 6.08]], "cls": "E",
     "why": "she leaves the frame top right; the empty stair held to the 125.72 cut, whole frame out of focus (E)"},
    {"id": "s029", "t0": 125.7244, "t1": 131.2392, "src": "SG11m1", "knots": [[125.7244, 2.0], [128.8432, 4.3], [131.2392, 6.696]], "pager_red": True, "cls": "A",
     "why": "not lip-synced (user): her silent stand (clip 2.0-4.3 slowed to 0.74x, mouth shut), then the reach and the release at 1x, the pager let go on 130.76"},
    {"id": "s030", "t0": 131.2392, "t1": SF1 / FPS, "src": "still:p030", "move": {"zoom": [1.0, 1.0], "center": [0.5, 0.5], "land": 131.6920}, "cls": "B",
     "why": "the pager on the dry pool floor: one landing shake on 131.69; SEP 20 on 'September' 134.17 (graphic)"},
]


def frame_of(t: float) -> int:
    """section frame of song time t"""
    return int(round(t * FPS)) - SF0


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def clip_time(s: dict, t: float) -> float:
    if "knots" in s:
        xs, ys = zip(*s["knots"])
        return float(np.interp(t, xs, ys))
    return s["c0"] + (t - s["t0"]) * s.get("speed", 1.0)


def decode(clip: Path, wanted: set[int], crop=None):
    """(index, rgb SEQ_HxSEQ_W) for the wanted pictures; crop (cx, cy, zoom) of the source frame first."""
    w0, h0 = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                      "-of", "csv=p=0", str(clip)], capture_output=True, text=True, check=True).stdout.strip().split(","))
    vf = ""
    if crop:
        cx, cy, z = crop
        cw, ch = int(round(w0 / z / 2)) * 2, int(round(h0 / z / 2)) * 2
        x = int(min(max(0, cx * w0 - cw / 2), w0 - cw))
        y = int(min(max(0, cy * h0 - ch / 2), h0 - ch))
        vf = f"crop={cw}:{ch}:{x}:{y},"
    vf += (f"scale={SEQ_W}:{SEQ_H}:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix=bt709:in_range=tv:"
           f"out_range=pc,format=rgb24")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(clip), "-vf", vf, "-vsync", "passthrough", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = SEQ_W * SEQ_H * 3
    i, last = 0, max(wanted)
    while i <= last:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        if i in wanted:
            yield i, np.frombuffer(buf, np.uint8).reshape(SEQ_H, SEQ_W, 3)
        i += 1
    p.stdout.close()
    p.kill()
    p.wait()


def pager_red_to_amber(rgb: np.ndarray) -> tuple[np.ndarray, dict]:
    """s029 SG11 m-1: the pager's LED (a few px of saturated red in her hand, inside her matte, so tail_lights_to_orange
    keeps it) set to amber (38 deg). The LED is on the magenta side of red (hue -26..-1 measured, saturation only
    0.40-0.51 as it is motion-smeared), her skin and fingertip rims on the warm side (0..+15), so the weight is by signed
    hue. Bounded to the frame below her head and left of her face (the pager travels from her coat to her
    outstretched left-of-frame hand); the ear lamp (on her head, right of her face) is outside it."""
    a = rgb.astype(np.float32) / 255
    h, s, v = pm.rgb_to_hsv(a)
    hs = np.where(h > 180, h - 360, h)               # signed hue
    hh, ww = rgb.shape[:2]
    region = np.zeros((hh, ww), bool)
    region[int(0.55 * hh):, :] = True                 # below her chin (her lips sit at 0.42-0.45 of the height)
    region[:, : int(0.40 * ww)] = True                # her outstretched arm, left of her face
    w = np.clip((0.5 - hs) / 3, 0, 1) * np.clip((hs + 32) / 6, 0, 1) * np.clip((s - 0.30) / 0.08, 0, 1) * np.clip((v - 0.30) / 0.08, 0, 1) * region
    w0 = w
    core = w > 0.5
    if core.sum() == 0:
        return rgb, {"pager_px": 0}
    w = np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
    w = np.maximum(w, w0)                             # the LED's own pixels keep their full weight
    w = np.where((hs > 3) | (hs < -40), 0.0, w)       # the halo only on red: never her skin (warm side), the dark plastic
    hn = hs + (38.0 - hs) * w
    out = pm.hsv_to_rgb(hn % 360, s, v)
    out = a * (1 - w[..., None]) + out * w[..., None]
    ys, xs = np.nonzero(core)                         # the LED's own pixels (the dilated, blurred weight can peak under 0.5)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), {"pager_px": int(core.sum()),
                                                              "box": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}


def lights(rgb: np.ndarray, level: float) -> np.ndarray:
    """s028's floodlights: level 0 = off (lamps and their spill dark), 1 = on (the picture), >1 a flare."""
    a = rgb.astype(np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    glow = np.asarray(Image.fromarray(((lum > 0.80) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
    glow = np.clip(glow * 3, 0, 1)
    if level >= 1:
        out = a * (1 + (level - 1) * (0.4 + glow[..., None]))
    else:
        off = a * (0.30 - 0.26 * glow[..., None])
        out = off + (a - off) * level
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


LIGHT_LEVELS = [0.0, 0.0, 0.0, 1.25, 0.55]           # frames 0-4 of s028a, then 1


def still_view(img: Image.Image, z: float, cx: float, cy: float, dx: float = 0.0, dy: float = 0.0) -> np.ndarray:
    """the plate's window (zoom z round the centre cx, cy as fractions, shifted dx, dy output px) at SEQ size"""
    w, h = img.size
    cw, ch = w / z, h / z
    x0 = min(max(0, cx * w - cw / 2), w - cw) - dx * cw / SEQ_W
    y0 = min(max(0, cy * h - ch / 2), h - ch) - dy * ch / SEQ_H
    return np.asarray(img.transform((SEQ_W, SEQ_H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC))


SHAKE = {0: (0.0, -30.0), 1: (22.0, 14.0), 2: (-9.0, -6.0), 3: (3.0, 2.0)}     # jolt offsets (px at 2304) by frame after impact
LAND = {0: (0.0, 14.0), 1: (0.0, -8.0), 2: (0.0, 3.0)}
SMEAR = {1: 1.0, 2: 0.45}                                                       # author: impact sharp, +1 full, +2 0.45


def prep_still(s: dict, d: Path) -> dict:
    name = s["src"].split(":", 1)[1]
    src = P018E if name == "P018" and P018E.exists() else PLATES / ("p018-w1.png" if name == "P018" else f"{name}.png")
    img = Image.open(src).convert("RGB")
    mv = s["move"]
    f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
    n = f1 - f0
    moving = mv["zoom"][0] != mv["zoom"][1] or "step" in mv or "jolt" in mv or "land" in mv
    log = []
    orange = None
    for k in range(n if moving else 1):
        u = k / max(1, n - 1)
        if mv.get("ease"):
            u = 0.5 - 0.5 * np.cos(np.pi * u)
        z = mv["zoom"][0] + (mv["zoom"][1] - mv["zoom"][0]) * u
        cx, cy = mv["center"]
        if "step" in mv and k >= frame_of(mv["step"][0]) - f0:
            z *= mv["step"][1]
        shake, smear = (0.0, 0.0), 0.0
        for key, table in (("jolt", SHAKE), ("land", LAND)):
            if key in mv:
                j = k - (frame_of(mv[key]) - f0)
                if j in table:
                    shake = table[j]
                    smear = SMEAR.get(j, 0.0) * (1.0 if key == "jolt" else 0.5)
                    prev = table.get(j - 1, (0.0, 0.0))
        if smear > 0:
            taps = 15
            acc = np.zeros((SEQ_H, SEQ_W, 3), np.float32)
            for t in np.linspace(0, 1, taps):
                sx = prev[0] + (shake[0] - prev[0]) * (1 - smear + smear * t)
                sy = prev[1] + (shake[1] - prev[1]) * (1 - smear + smear * t)
                acc += still_view(img, z, cx, cy, sx, sy)
            rgb = (acc / taps + 0.5).astype(np.uint8)
        else:
            rgb = still_view(img, z, cx, cy, *shake)
        rgb, st = pm.tail_lights_to_orange(rgb)
        if orange is None:
            orange = st
        Image.fromarray(rgb).save(d / f"{k:04d}.jpg", quality=93, subsampling=0)
        log.append({"k": k, "zoom": round(z, 4), "shake": shake, "smear": smear})
    return {"still": str(src.relative_to(REPO)), "still_sha256": sha(src), "frames": n, "pictures": n if moving else 1,
            "fixed": not moving, "move": mv, "orange_first": orange, "log": [r for r in log if r["shake"] != (0.0, 0.0)][:12]}


def prep_clip(s: dict, d: Path) -> dict:
    clip = take_path(s["src"])
    if not clip.exists():
        raise SystemExit(f"{s['id']}: take missing {clip}")
    h = sha(clip)
    want = TAKES[s["src"]][2] if s["src"] in TAKES else INS16[1]
    if not h.startswith(want):
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
    cache, hue, pager = {}, {}, {}
    for i, rgb in decode(clip, wanted, s.get("crop")):
        rgb, st = pm.tail_lights_to_orange(rgb)
        hue[i] = st
        if s.get("pager_red"):
            rgb, pst = pager_red_to_amber(rgb)
            pager[i] = pst
        cache[i] = rgb.copy()
    if wanted - set(cache):
        raise SystemExit(f"{s['id']}: pictures not decoded {sorted(wanted - set(cache))[:5]}")
    for k, m in enumerate(fmap):
        rgb = cache[m["idx"]]
        if s.get("lights"):
            rgb = lights(rgb, LIGHT_LEVELS[k] if k < len(LIGHT_LEVELS) else 1.0)
        Image.fromarray(rgb).save(d / f"{k:04d}.jpg", quality=93, subsampling=0)
    return {"clip": str(clip.relative_to(REPO)), "clip_sha256": h, "pictures": len(pts), "frames": len(fmap),
            "first": fmap[0], "last": fmap[-1], "crop": s.get("crop"), "speed": s.get("speed", 1.0), "knots": s.get("knots"),
            "repeats": sum(1 for a, b in zip(fmap, fmap[1:]) if a["idx"] == b["idx"]),
            "skips": sum(1 for a, b in zip(fmap, fmap[1:]) if b["idx"] - a["idx"] > 1),
            "map": [m["idx"] for m in fmap], "orange_px_max": max(v["shifted_px"] for v in hue.values()),
            "pager_red": {str(k): v for k, v in pager.items()} or None}


def prep(want: list[str]) -> int:
    META.mkdir(parents=True, exist_ok=True)
    for s in SHOTS:
        if want and s["id"] not in want:
            continue
        d = MEDIA / s["id"]
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        m = prep_still(s, d) if s["src"].startswith("still:") else prep_clip(s, d)
        m = {"shot": s["id"], "t0": s["t0"], "t1": s["t1"], "why": s["why"], **m}
        (META / f"{s['id']}.json").write_text(json.dumps(m, indent=1))
        print(s["id"], {k: m.get(k) for k in ("frames", "pictures", "repeats", "skips", "orange_px_max")}, flush=True)
    return 0


# ---------------------------------------------------------------- blur classes (prep_blur_v3.py's, on these pictures)
# The matte region follows the subject where it is in the prepared pictures: u2netp on the whole picture isolates the
# subject in every B shot here (its > 0.5 box measured 2026-11-23 on the prepared pictures, fractions x0, y0, x1, y1:
# s017p1/p2 him, face to laptop and the fingertips 0.00-0.82 x; s021 her 0.34-0.95 x; s022 her and her arm on the desk
# 0.12-1.00 x; s023 her 0.65-0.88 x). The first regions (0.30-0.80, 0.82-1.0, ...) cut off s021's head and missed s023's
# figure entirely, so both went soft with the background.
B_CFG = {   # matte region (fractions of the picture), background sigma (2304 px), protect boxes
    "s017p1": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 18.0},
    "s017p2": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 18.0},
    "s021": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 18.0},
    "s022": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 18.0},
    "s023": {"region": (0.0, 0.0, 1.0, 1.0), "bg": 16.0},       # her and the badge sharp; the gallery soft
    "s030": {"none": True},            # the plate's own shallow focus; nothing added
}
C_CFG = {
    "s019": {"matte": "box", "iso": 7.0, "flow": {"q": 2, "bs": 32, "step": 8}, "ramp": [(0, 2.5), (200, 2.5)]},
    "s027": {"matte": "box", "iso": 5.0, "flow": {"q": 2, "bs": 32, "step": 8}, "ramp": [(0, 1.6), (200, 1.6)]},
    "s025": {"none": True},            # the jolt's smear is drawn in prep_still
}
D_SIGMA, E_SIGMA = 9.0, 13.0


def blur(want: list[str]) -> int:
    import prep_blur_v3 as PB
    import prep_dof as PD
    out = {}
    for s in SHOTS:
        sid, cls = s["id"], s["cls"]
        if want and sid not in want:
            continue
        src = MEDIA / sid
        files = sorted(src.glob("*.jpg"))
        dst = BLUR / sid
        if cls == "A" or B_CFG.get(sid, {}).get("none") or C_CFG.get(sid, {}).get("none"):
            continue
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        if cls == "B":
            c = B_CFG[sid]
            imgs = [PB.load(f) for f in files]
            mats = [PB.region_matte(i, c["region"]) for i in imgs]
            for k, (f, im) in enumerate(zip(files, imgs)):
                m = np.mean(mats[max(0, k - 1):k + 2], 0)
                PB.save(PD.dof(im, m, c.get("protect"), c["bg"]), dst / f.name)
            out[sid] = {"class": "B", "pictures": len(files), "bg_sigma_px": c["bg"], "region": c["region"]}
        elif cls in ("D", "E"):
            g = ImageFilter.GaussianBlur(D_SIGMA if cls == "D" else E_SIGMA)
            for f in files:
                PB.save(np.asarray(Image.open(f).convert("RGB").filter(g)), dst / f.name)
            out[sid] = {"class": cls, "pictures": len(files), "sigma_px": D_SIGMA if cls == "D" else E_SIGMA}
        elif cls == "C":
            PB.SEQ, PB.OUT = MEDIA, BLUR
            PB.C[sid] = {"seq": sid, **C_CFG[sid]}
            r = PB.do_c(sid)
            out[sid] = {k: r[k] for k in ("class", "pictures", "ramp", "iso_px")}
        out[sid]["sha256_0000"] = sha(dst / "0000.jpg")
        (EXC / "data/blur-s2").mkdir(exist_ok=True)
        (EXC / "data/blur-s2" / f"{sid}.json").write_text(json.dumps(out[sid], indent=1))     # one file per shot: parallel runs
        print(sid, out[sid], flush=True)
    return 0


# ---------------------------------------------------------------- EDL / composition
A_GRADE = {"uSoftMix": 0.2, "uCapSoft": 1}           # uCapSoft: the red caps on a continuous hue weight (shaders.js)
D_GRADE = {"uSoftMix": 1.0, "uToneBP": -0.012, "uToneWP": 1.2, "uContrast": 0.95, "uCapSoft": 1}
E_GRADE = {"uCapSoft": 1}
DOTS = {"uLineAM": 0, "uDotAM": 0.42, "uDotPitch": 4.2, "uDotAng": 0.0}      # opening_v2.py DOTS (verse)


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
        d = BLUR / s["id"] if (BLUR / s["id"]).exists() else MEDIA / s["id"]
        n = len(list(d.glob("*.jpg")))
        if n != (1 if m.get("fixed") else m["frames"]):
            raise SystemExit(f"{s['id']}: {d} holds {n} pictures, not {1 if m.get('fixed') else m['frames']}")
        seq = {"dir": str(d.relative_to(EXC)), "count": n}
        if m.get("fixed"):
            seq["fixed"] = 0
        row = {"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": f0, "f1": f1, "kind": "clip", "chapter": "c4",
               "take": s["src"], "take_sha256": m.get("clip_sha256") or m.get("still_sha256"), "seq": seq,
               "blur": {"cls": s["cls"], "grade": D_GRADE if s["cls"] == "D" else E_GRADE if s["cls"] == "E" else A_GRADE}}
        if s.get("dots"):
            row["screen"] = DOTS
        if s.get("dots_from"):
            row["fx"] = [{"f0": frame_of(s["dots_from"]), "f1": f1, "grade": DOTS}]
        shots.append(row)
        lv.update(levels([{**row, "seq": {**seq, "count": n}}], {}))
    if shots[0]["f0"] != 0 or shots[-1]["f1"] != N or any(a["f1"] != b["f0"] for a, b in zip(shots, shots[1:])):
        raise SystemExit("the shots do not tile section frames 0-1804")
    edl = {"version": 16, "opening": True, "opening_v2": True, "opening_v3": True, "section": "s015-030-v1", "picture_only": True,
           "fps": FPS, "W": W, "H": H, "offset": OFFSET, "end": SF1 / FPS, "frames": N, "song_frame0": SF0, "shots": shots,
           "images": {}, "levels": lv, "lines": [], "beats": [], "downbeats": [], "snare": [], "kick": [], "tracks": {}, "cuts": cuts}
    EDL.write_text(json.dumps(edl, indent=1))
    dur = N / FPS
    (EXC / COMP).write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 s015-s030 picture v1 (song frames {SF0}-{SF1 - 1}, opening v3 print)</title>
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
    if "--blur" in sys.argv:
        raise SystemExit(blur(args))
    if "--build" in sys.argv:
        raise SystemExit(build())
    raise SystemExit(__doc__)
