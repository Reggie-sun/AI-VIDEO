#!/usr/bin/env python3
"""IRIS EP01 opening v2 picture (2026-11-21, pilot/opening/plan/v2.html and plan/index.html, approved "按 v2 做"):
song 0-59.2341 s (1422 frames, frame n = song n/24) on the prepared pictures of opening.py (the ten chosen takes, their
red repairs) and the v4r11 chorus picture, with the shot motion and the screens measured on EV
(outputs/anabology-opus55-replica/escape_velocity_analysis/texture_study/REPORT.md). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening_v2.py --build    # EDLs, compositions, engine.js
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-opening-v2.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v2-opening-picture-000-979.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-v4r11-picture-v2.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v2-chorus-picture-036-059.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening_v2.py --join     # renders/IRIS-EP01-v2-picture-000-1422.mp4

Motion (v2.html): s003, s007, s009 and s010 are stills - one prepared picture of the chosen take (its first picture: the
take's own 4K first frame through the same prep and red repairs as the video, the board plates p0NN-w1 are 1671x941),
pushed at most 1 %/s; s007 holds and steps in twice (1.05x, 1.10x) on the beats after "$6,000", each step under one
mosaic frame (EV S0023 f762 / f773). s004 plays its lip-synced span to song 14.3333 s (f344, the span's end, clip 3.02 s)
and then holds the picture where she holds the handset up (prepared picture 80, song f387). s010's last 23 frames
(956-978, from the 39.8454 beat) are black, no screen (EV S0011/S0012); the ALL slam is drawn on them in Agentcut.

Screens (REPORT.md 2.1): song frames 0-955 an AM dot screen 4.2 px on a 0/90 deg grid (EV class A); 979-1421 the v4r11
line screen (4.0 px, the measured 3.99 px / 18.2 deg, class C). One-offs, one each: s005 song 417-427 photocopy dither
(K, 11 frames, on the PARTIAL ANSWER bubble), s007 636 / 647 mosaic 20 px (D), s010 956-978 black (J0), s011 the coarse
line screen 5.95 px / 17.6 deg (C2), s013a a coarse dot screen 7.2 px at 79 deg broken off on its beats (B). The v4r11
softening is kept (no uniform softening is added). The engine reads these as shot.still / shot.hold / shot.screen /
shot.fx (src/main.js, src/opening.js, src/shaders.js); earlier EDLs carry none of them.

v2c (2026-11-21, s014 reshot): the v2 chorus EDL with s014a + s014b (MO07-s-2, a jump on 57.3765) replaced by one span
of MO07 r6-2 (edl.S014_V2C, prepared by prep_media.py --v2c into media/seq/s014r6) for song 55.0777-58.7697; s014c and
every screen as v2. The opening render (0-978) is v2's, reused:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/prep_media.py --v2c
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening_v2.py --build-c  # data/edl-v4r11-picture-v2c.json
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-v4r11-picture-v2c.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v2c-chorus-picture-036-059.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening_v2.py --join-c   # renders/IRIS-EP01-v2c-picture-000-1422.mp4

v3 (2026-11-21, v2d review: "14s这里静止很奇怪，然后56s那里那个动作我没看懂。还有就是还是都是一个模糊程度，太单调"):
- s004 plays its take through (no hold; the lip-synced span is the same pictures).
- s014 split on the 56.9237 beat (song frame 1366, edl.S014_SPLIT): s014p 55.0777-56.9237 the punch-in on the pager press
  from the take's 4K pictures (media/hr3/seq/s014p, shots8.js s014p, a slow push 1.96x -> 2.0x of the wide following her),
  s014a 56.9237-58.7697 the wide (r6-2 pictures 44-87) for the turn, the sleeve and the walk away.
- every shot carries a blur class (shot.blur, BLUR_OPEN / BLUR_CHORUS below; blur_study/REPORT.md's A-E): its grade in
  shot.blur.grade (main.js) and, for B / C / E, its pictures from prep_blur_v3.py (media/blur3). Screens and one-offs as v2.

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/prep_blur_v3.py
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening_v2.py --build-3  # data/edl-opening-v3.json, data/edl-v4r11-picture-v3.json
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-opening-v3.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v3-opening-picture-000-979.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-v4r11-picture-v3.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v3-chorus-picture-036-059.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/opening_v2.py --join-3   # renders/IRIS-EP01-v3-picture-000-1422.mp4
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, FPS, H, OFFSET as OFFSET_C, REPO, V4, W  # noqa: E402
from opening import END_F, META, SHOTS, check_cuts, frame_of, sha  # noqa: E402

# uDotAM 0.42: at 0.3 the dots measured on the Agentcut export (H.264 ~6.2 Mbit/s) fell below REPORT.md's detection
# threshold in the moving shots (s005 prominence 677, s006 931; the picture itself 17,000-21,000); two axes share the
# energy one line screen (uLineAM 0.3) puts on one
DOTS = {"uLineAM": 0, "uDotAM": 0.42, "uDotPitch": 4.2, "uDotAng": 0.0}
COARSE_LINES = {"uLinePitch": 5.95, "uLineAng": -0.3072}                # wave vector 17.6 deg (the engine's y is down)
COARSE_DOTS = {"uLineAM": 0, "uDotAM": 0.42, "uDotPitch": 7.2, "uDotAng": 1.3788}    # grid at 79 deg as REPORT.md measures it
NO_SCREEN = {"uLineAM": 0, "uDotAM": 0}
BLACK_F = 956                                  # 39.8454 beat
MOSAIC_F = (636, 647)                          # beats 26.5056 / 26.97 after 'grand' (26.293, the $6,000 slam f631)
DITHER = (417, 428)                            # 'PARTIAL ANSWER' bubble 17.355 s, 11 frames
HOLD = {"f": 344, "idx": 80}
MOTION = {
    "s003": {"still": {"zoom": [1.0, 1.025], "center": [1152, 648]}},
    "s007": {"still": {"zoom": [1.0, 1.0], "center": [1152, 648]},
             "fx": [{"f0": MOSAIC_F[0], "f1": 714, "zoom": 1.05}, {"f0": MOSAIC_F[1], "f1": 714, "zoom": 1.10 / 1.05},
                    *({"f0": f, "f1": f + 1, "grade": {"uMosaic": 20}} for f in MOSAIC_F)]},
    "s009": {"still": {"zoom": [1.0, 1.025], "center": [1900, 600]}},
    "s010": {"still": {"zoom": [1.0, 1.0315], "center": [1270, 300]},
             "fx": [{"f0": BLACK_F, "f1": END_F, "grade": {"uBlack": 1}}]},
    "s005": {"fx": [{"f0": DITHER[0], "f1": DITHER[1], "grade": {"uDither": 1, "uDotAM": 0}}]},
    "s004": {"hold": HOLD},
}
CHORUS_OFF = 625                                # v4r11 picture EDL: excerpt frame + 625 = song frame
B_OFF = (1233, 1244, 1245)                      # s013a's beats 51.3858 / 51.8502 (song frames): 1 and 2 frames off
CHORUS = {"s011": {"screen": COARSE_LINES},
          "s013a": {"screen": COARSE_DOTS, "fx": [{"f0": f - CHORUS_OFF, "f1": f - CHORUS_OFF + 1, "grade": NO_SCREEN} for f in B_OFF]}}
OPEN_RENDER = EXC / "renders/IRIS-EP01-v2-opening-picture-000-979.mp4"
CHORUS_RENDER = EXC / "renders/IRIS-EP01-v2-chorus-picture-036-059.mp4"
JOINED = EXC / "renders/IRIS-EP01-v2-picture-000-1422.mp4"
CHORUS_RENDER_C = EXC / "renders/IRIS-EP01-v2c-chorus-picture-036-059.mp4"
JOINED_C = EXC / "renders/IRIS-EP01-v2c-picture-000-1422.mp4"
OPEN_RENDER_3 = EXC / "renders/IRIS-EP01-v3-opening-picture-000-979.mp4"
CHORUS_RENDER_3 = EXC / "renders/IRIS-EP01-v3-chorus-picture-036-059.mp4"
JOINED_3 = EXC / "renders/IRIS-EP01-v3-picture-000-1422.mp4"

# v3 blur classes (blur_study/REPORT.md; EV 0-120 s: A 62.5 %, B 14.5 %, C/C* 5.7 %, D 9 %, E 3.1 %). A: the v4r11 print's
# uniform softening (uSoftMix 1: the picture replaced by its half / quarter size copies) taken down so the shot is sharp
# at the viewing scale; B / C / E carry their class in their pictures (prep_blur_v3.py) under A's print; D: the soft base
# at full strength over a softened picture (prep_blur_v3.py D), darker and flatter (as EV's S0054 / S0056 / S0063 and
# S0049 / S0051).
A_GRADE = {"uSoftMix": 0.2}
D_GRADE = {"uSoftMix": 1.0, "uToneBP": -0.012, "uToneWP": 1.2, "uContrast": 0.95}
E_GRADE = {}                                    # E: the v4r11 print as it was over the defocused picture
BLUR_OPEN = {
    "s001": {"cls": "A", "grade": A_GRADE},
    "s002": {"cls": "B", "dir": "media/blur3/s002", "grade": A_GRADE},
    "s003": {"cls": "B", "dir": "media/blur3/s003", "grade": A_GRADE},
    "s004": {"cls": "A", "grade": A_GRADE},
    "s005": {"cls": "B", "dir": "media/blur3/s005", "grade": A_GRADE},
    "s006": {"cls": "C", "dir": "media/blur3/s006", "grade": A_GRADE},
    "s007": {"cls": "E", "dir": "media/blur3/s007-E", "grade": E_GRADE},
    "s008": {"cls": "A", "grade": A_GRADE},
    "s009": {"cls": "B", "dir": "media/blur3/s009", "grade": A_GRADE},
    "s010": {"cls": "A", "grade": A_GRADE},
}
BLUR_CHORUS = {
    "s011": {"cls": "A", "grade": A_GRADE},
    "s012a": {"cls": "B", "images": {"p012w1-engineer": "media/blur3/stills/p012w1-engineer.png"}, "grade": A_GRADE},
    "s012b": {"cls": "A", "dir": "media/seq/s012b", "grade": A_GRADE},      # v4r11's dof11 (B) back to the clean take
    "s012c": {"cls": "D", "dir": "media/blur3/s012c-D", "grade": D_GRADE},
    "s012d": {"cls": "A", "grade": A_GRADE},
    "s013a": {"cls": "B", "images": {"INS13-a": "media/blur3/stills/INS13-a.png"}, "grade": A_GRADE},
    "s013b": {"cls": "A", "dir": "media/seq/s013b", "grade": A_GRADE},      # as s012b
    "s014p": {"cls": "A", "grade": A_GRADE},
    "s014a": {"cls": "C", "dir": "media/blur3/s014a", "grade": A_GRADE},
    "s014c": {"cls": "D", "images": {"INS14-b": "media/blur3/stills/INS14-b-D.png"}, "grade": D_GRADE},
}
# s014p's view (shots8.js s014p): excerpt frames, the 2304 picture's px; her body's centre x 1201-1218 and her head top
# y 113-144 over r6-2 pictures 0-43 (u2netp): the window 1152x648 at z 2 holds her head (looking down), the right hand
# and the pager on the waist chain (y ~560-640) and the badge
PUNCH = [{"f": 697, "cx": 1204, "cy": 405, "z": 1.96}, {"f": 740, "cx": 1212, "cy": 400, "z": 2.0}]


def comp(name: str, edl: str, dur: float, offset: str = "") -> None:
    (EXC / name).write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 {name} (opening v2)</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-start="0" data-duration="{dur:.6f}" data-ex-edl="{edl}"{offset} data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{dur:.6f}" data-track-index="0"></canvas>
</div>
<script src="engine.js"></script>
</body>
</html>
""", encoding="utf-8")


def build() -> int:
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())["beats"]
    cuts = check_cuts(beats)
    marks = {}
    for f in (BLACK_F, *MOSAIC_F, *B_OFF[:2], CHORUS_OFF + 0):
        nb = min(beats, key=lambda b: abs(b - f / FPS))
        marks[f] = round(f / FPS - nb, 4)
    for f in (BLACK_F, *MOSAIC_F, *B_OFF[:2]):
        if abs(marks[f]) > 0.03:
            raise SystemExit(f"frame {f} is {marks[f]:+.4f} s from its beat")
    D = json.loads((EXC / "data/edl-opening-picture.json").read_text())
    meta = {p.stem: json.loads(p.read_text()) for p in META.glob("*.json")}
    for s, src in zip(D["shots"], SHOTS):
        if meta[src["media_id"]]["frames"] != s["f1"] - s["f0"]:
            raise SystemExit(f"{s['id']}: prepared pictures differ from opening.py")
        s.update(MOTION.get(s["id"], {}))
        if "still" in s:
            s["seq"] = {**s["seq"], "fixed": 0}
        s["screen"] = DOTS
        if s["id"] == "s004" and not (HOLD["f"] < s["f1"] and HOLD["idx"] < s["seq"]["count"]):
            raise SystemExit("s004 hold outside the shot")
    D.update({"opening_v2": True, "beat_marks": marks})
    (EXC / "data/edl-opening-v2.json").write_text(json.dumps(D, indent=1))
    comp("composition-opening-v2.html", "data/edl-opening-v2.json", END_F / FPS)
    C = json.loads((EXC / "data/edl-v4r11-picture.json").read_text())
    for s in C["shots"]:
        s.update(CHORUS.get(s["id"], {}))
    (EXC / "data/edl-v4r11-picture-v2.json").write_text(json.dumps(C, indent=1))
    src = (EXC / "composition-v4r11-picture.html").read_text()
    if src.count("data/edl-v4r11-picture.json") != 1:
        raise SystemExit("composition-v4r11-picture.html: EDL reference not found once")
    (EXC / "composition-v4r11-picture-v2.html").write_text(src.replace("data/edl-v4r11-picture.json", "data/edl-v4r11-picture-v2.json"))
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(EXC / "src/main.js"), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={EXC / 'engine.js'}", "--log-level=warning"], check=True)
    print(json.dumps({"cuts": cuts, "beat_marks": marks}, indent=1))
    return 0


def build_c() -> int:
    """v2c: data/edl-v4r11-picture-v2.json with s014a/s014b replaced by the one r6-2 span (levels as build.py's)."""
    from build import levels
    from edl import S014_OFFSET, S014_V2C, frame_of as excerpt_frame     # excerpt frames (song frame - 625), not opening.frame_of
    C = json.loads((EXC / "data/edl-v4r11-picture-v2.json").read_text())
    ids = [s["id"] for s in C["shots"]]
    if ids[-3:] != ["s014a", "s014b", "s014c"]:
        raise SystemExit(f"unexpected chorus shots {ids[-3:]}")
    s = S014_V2C
    f0, f1 = excerpt_frame(s["t0"]), excerpt_frame(s["t1"])
    meta = json.loads((EXC / "data/media-v2c.json").read_text())["shots"][s["media_id"]]
    if meta["frames"] != f1 - f0 or (f0, f1) != (C["shots"][-3]["f0"], C["shots"][-2]["f1"]):
        raise SystemExit("s014 r6-2 pictures do not span s014a + s014b")
    row = {"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": f0, "f1": f1, "chapter": "c3", "kind": "clip",
           "seq": {"dir": f"media/seq/{s['media_id']}", "count": f1 - f0}}
    C["shots"][-3:-1] = [row]
    C["levels"].pop("s014b")
    C["levels"].update(levels([row], {}))
    C["cuts"] = [c for c in C["cuts"] if c["cut"] != "s014b"]
    C["v2c"] = {"s014": s["clip"], "material_offset_s": S014_OFFSET}
    (EXC / "data/edl-v4r11-picture-v2c.json").write_text(json.dumps(C, indent=1))
    src = (EXC / "composition-v4r11-picture-v2.html").read_text()
    if src.count("data/edl-v4r11-picture-v2.json") != 1:
        raise SystemExit("composition-v4r11-picture-v2.html: EDL reference not found once")
    (EXC / "composition-v4r11-picture-v2c.html").write_text(src.replace("data/edl-v4r11-picture-v2.json", "data/edl-v4r11-picture-v2c.json"))
    print(json.dumps({"s014a": row, "levels": C["levels"]["s014a"], "cuts": [c["cut"] for c in C["cuts"]]}, indent=1))
    return 0


def build_3() -> int:
    """v3: the v2 opening EDL and the v2c chorus EDL with s004's hold gone, s014 split on 56.9237 and the blur classes."""
    from edl import S014_SPLIT, frame_of as excerpt_frame
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())["beats"]
    if min(abs(b - S014_SPLIT) for b in beats) > 1e-4:
        raise SystemExit("56.9237 is not a beat")
    D = json.loads((EXC / "data/edl-opening-v2.json").read_text())
    for s in D["shots"]:
        b = BLUR_OPEN[s["id"]]
        s.pop("hold", None)
        if "dir" in b:
            n = len(list((EXC / b["dir"]).glob("*.jpg")))
            if n != (1 if "still" in s else s["seq"]["count"]):
                raise SystemExit(f"{s['id']}: {b['dir']} holds {n} pictures")
            s["seq"] = {**s["seq"], "dir": b["dir"]}
        s["blur"] = {"cls": b["cls"], "grade": b["grade"]}
    D["opening_v3"] = True
    (EXC / "data/edl-opening-v3.json").write_text(json.dumps(D, indent=1))
    comp("composition-opening-v3.html", "data/edl-opening-v3.json", END_F / FPS)
    C = json.loads((EXC / "data/edl-v4r11-picture-v2c.json").read_text())
    sp = excerpt_frame(S014_SPLIT)                                   # 741 (song frame 1366)
    rows = []
    for s in C["shots"]:
        if s["id"] == "s014a":
            if not (s["f0"] < sp < s["f1"]) or s["seq"]["count"] != s["f1"] - s["f0"]:
                raise SystemExit("s014a does not span the split")
            n_p = len(list((EXC / "media/hr3/seq/s014p").glob("*.jpg")))
            if n_p != sp - s["f0"]:
                raise SystemExit(f"media/hr3/seq/s014p holds {n_p} pictures, not {sp - s['f0']}")
            rows.append({**s, "id": "s014p", "t1": S014_SPLIT, "f1": sp, "seq": {"dir": "media/hr3/seq/s014p", "count": n_p},
                         "punch": {"keys": PUNCH}})
            rows.append({**s, "t0": S014_SPLIT, "f0": sp, "seq": {"dir": s["seq"]["dir"], "count": s["f1"] - sp}})
        else:
            rows.append(s)
    for s in rows:
        b = BLUR_CHORUS.get(s["id"])
        if not b:
            continue
        if "dir" in b:
            s["seq"] = {**s["seq"], "dir": b["dir"]}
        for k, v in b.get("images", {}).items():
            C["images"][k] = v
        s["blur"] = {"cls": b["cls"], "grade": b["grade"]}
    n_w = len(list((EXC / "media/blur3/s014a").glob("*.jpg")))
    if n_w != rows[-2]["seq"]["count"]:
        raise SystemExit(f"media/blur3/s014a holds {n_w} pictures")
    C["shots"] = rows
    C["levels"]["s014p"] = C["levels"]["s014a"]                     # the same take, the same levels across the cut
    i = next(j for j, c in enumerate(C["cuts"]) if c["cut"] == "s014c")
    C["cuts"][i - 1] = {**C["cuts"][i - 1], "cut": "s014p"}
    C["cuts"].insert(i, {"cut": "s014a", "t": S014_SPLIT, "beat": S014_SPLIT, "dt": 0.0, "frame": sp, "frame_t": round(OFFSET_C + sp / FPS, 4),
                         "frame_dt_beat": round(OFFSET_C + sp / FPS - S014_SPLIT, 4)})
    C["v3"] = {"split": S014_SPLIT, "punch": PUNCH, "blur": {k: v["cls"] for k, v in BLUR_CHORUS.items()}}
    (EXC / "data/edl-v4r11-picture-v3.json").write_text(json.dumps(C, indent=1))
    src = (EXC / "composition-v4r11-picture-v2c.html").read_text()
    if src.count("data/edl-v4r11-picture-v2c.json") != 1:
        raise SystemExit("composition-v4r11-picture-v2c.html: EDL reference not found once")
    (EXC / "composition-v4r11-picture-v3.html").write_text(src.replace("data/edl-v4r11-picture-v2c.json", "data/edl-v4r11-picture-v3.json"))
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(EXC / "src/main.js"), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={EXC / 'engine.js'}", "--log-level=warning"], check=True)
    print(json.dumps({"opening": {s["id"]: s["blur"]["cls"] for s in D["shots"]},
                      "chorus": [(s["id"], s["f0"], s["f1"], s.get("blur", {}).get("cls")) for s in rows], "cuts": C["cuts"][-4:]}, indent=1))
    return 0


def join(chorus: Path = CHORUS_RENDER, joined: Path = JOINED, opening: Path | None = None) -> int:
    """Opening v2 (song frames 0-978) and the chorus v2 picture's frames 110-552 (song frames 979-1421), as opening.py."""
    CHORUS_RENDER, JOINED = chorus, joined
    OPEN_RENDER = opening or globals()["OPEN_RENDER"]
    if JOINED.exists():
        raise SystemExit(f"{JOINED.name} exists (not overwritten)")
    n = lambda p: int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                                      "stream=nb_read_frames", "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True).stdout)
    if n(OPEN_RENDER) != END_F or n(CHORUS_RENDER) != 553:
        raise SystemExit("frame counts differ from 979 / 553")
    fc = (f"[0:v]trim=start_frame=0:end_frame={END_F},setpts=PTS-STARTPTS[a];"
          f"[1:v]trim=start_frame={END_F - 869}:end_frame=553,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(OPEN_RENDER), "-i", str(CHORUS_RENDER), "-filter_complex", fc, "-map", "[v]",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-colorspace", "bt709", "-r", "24", "-movflags", "+faststart", str(JOINED)], check=True)
    if n(JOINED) != 1422:
        raise SystemExit(f"{JOINED.name}: {n(JOINED)} frames, not 1422")
    print(json.dumps({"joined": str(JOINED.relative_to(REPO)), "frames": 1422, "sha256": sha(JOINED),
                      "opening": {"file": str(OPEN_RENDER.relative_to(REPO)), "sha256": sha(OPEN_RENDER)},
                      "chorus": {"file": str(CHORUS_RENDER.relative_to(REPO)), "sha256": sha(CHORUS_RENDER)}}, indent=1))
    return 0


if __name__ == "__main__":
    if "--build" in sys.argv:
        raise SystemExit(build())
    if "--join" in sys.argv:
        raise SystemExit(join())
    if "--build-c" in sys.argv:
        raise SystemExit(build_c())
    if "--join-c" in sys.argv:
        raise SystemExit(join(CHORUS_RENDER_C, JOINED_C))
    if "--build-3" in sys.argv:
        raise SystemExit(build_3())
    if "--join-3" in sys.argv:
        raise SystemExit(join(CHORUS_RENDER_3, JOINED_3, OPEN_RENDER_3))
    raise SystemExit(__doc__)
