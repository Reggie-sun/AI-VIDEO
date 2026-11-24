#!/usr/bin/env python3
"""Agentcut bake (2026-11-20): the v4r10c print over the stills of the Agentcut replica's song 0-36.2 s (project
escape-velocity-replica, track pic-motion, clips that start before song frame 869). Run from the repository root, after
build.py (any version: engine.js carries src/bake.js):

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/bake_agentcut.py
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition-bake-000-869.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-agentcut-print-000-869.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  node outputs/ai-city-takeover/ep01/v4/excerpt/snap.mjs --comp composition-bake-stills.html --edl data/edl-bake-stills.json \\
      --shots --out <dir>        # <key>-a.png: each still at rest (cover, no push) through the same print, grain frozen

Writes (nothing else is touched):
- media/agentcut-bake/: copies of the clips' stills and mosaic pictures (SHA-256 in the edl).
- data/edl-bake-000-869.json + composition-bake-000-869.html: song frames 0-868, one shot per pic-motion clip with its
  StillMove props (bake.js draws the camera); the levels per still as build.py's levels(); version 15 (main.js's v4r10c
  grade with the print trim), picture only, no audio.
- data/edl-bake-stills.json + composition-bake-stills.html: one frame per still, no push.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import levels, sha  # noqa: E402
from edl import EXC, FPS, H, W  # noqa: E402

PROJECT = Path("/home/reggie/Agentcut/projects/escape-velocity-replica")
END_F = 869                                   # song frame of the v4r10c window's first frame (s010)
DST = EXC / "media/agentcut-bake"


def composition(tag: str, frames: int) -> str:
    dur = frames / FPS
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 Agentcut bake {tag}</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-start="0" data-duration="{dur:.6f}" data-ex-edl="data/edl-bake-{tag}.json" data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{dur:.6f}" data-track-index="0"></canvas>
</div>
<script src="engine.js"></script>
</body>
</html>
"""


def edl(shots: list[dict], images: dict, lv: dict, frames: int, src: dict) -> dict:
    return {"version": 15, "bake": True, "picture_only": True, "fps": FPS, "W": W, "H": H, "offset": 0.0, "end": frames / FPS,
            "frames": frames, "shots": shots, "images": images, "levels": lv, "lines": [], "beats": [], "downbeats": [],
            "snare": [], "kick": [], "tracks": {}, "source": src}


def main() -> int:
    layers = json.loads((PROJECT / "layers.json").read_text())
    clips = sorted((c for t in layers["tracks"] if t["id"] == "pic-motion" for c in t["clips"] if c["from"] < END_F),
                   key=lambda c: c["from"])
    DST.mkdir(parents=True, exist_ok=True)
    images, src_sha, shots, size_of = {}, {}, [], {}
    from PIL import Image
    for c in clips:
        p = c["props"]
        if c["from"] + c["duration"] > END_F:
            raise SystemExit(f"{c['id']} runs past song frame {END_F}")
        keys = {}
        for role in ("src", "mosaic"):
            if p.get(role):
                a = PROJECT / p[role]
                key = a.stem
                shutil.copy2(a, DST / a.name)
                images[key] = f"media/agentcut-bake/{a.name}"
                src_sha[key] = {"agentcut": p[role], "sha256": sha(a)}
                with Image.open(a) as im:
                    size_of[key] = list(im.size)
                keys[role] = key
        if p.get("mosaic") and size_of[keys["mosaic"]] != size_of[keys["src"]]:
            raise SystemExit(f"{c['id']}: mosaic size differs from its still")
        shots.append({"id": c["id"].replace("move-", ""), "agentcut_clip": c["id"], "f0": c["from"], "f1": c["from"] + c["duration"],
                      "kind": "still", "stills": [[keys["src"], 0]],
                      "move": {"src": keys["src"], "mosaic": keys.get("mosaic"), "size": size_of[keys["src"]],
                               "push": p["push"], "cuts": p["cuts"]}})
    for a, b in zip(shots, shots[1:]):
        if a["f1"] != b["f0"]:
            raise SystemExit(f"gap or overlap between {a['id']} and {b['id']}")
    if shots[0]["f0"] != 0 or shots[-1]["f1"] != END_F:
        raise SystemExit("the shots do not cover song frames 0-868")
    lv = levels(shots, images)
    for s in shots:                           # a mosaic frame takes its still's levels
        if s["move"]["mosaic"]:
            lv[s["move"]["mosaic"]] = lv[s["move"]["src"]]
    (EXC / "data/edl-bake-000-869.json").write_text(json.dumps(edl(shots, images, lv, END_F, src_sha), indent=1))
    (EXC / "composition-bake-000-869.html").write_text(composition("000-869", END_F), encoding="utf-8")

    rest = []
    for i, s in enumerate(shots):
        k = s["move"]["src"]
        rest.append({"id": k, "f0": i, "f1": i + 1, "kind": "still", "stills": [[k, 0]],
                     "move": {"src": k, "mosaic": None, "size": s["move"]["size"],
                              "push": {"from": 0, "to": 1, "scale": 1, "ox": 960, "oy": 540}, "cuts": []}})
    still_images = {s["id"]: images[s["id"]] for s in rest}
    (EXC / "data/edl-bake-stills.json").write_text(json.dumps(
        edl(rest, still_images, {k: lv[k] for k in still_images}, len(rest), {k: src_sha[k] for k in still_images}), indent=1))
    (EXC / "composition-bake-stills.html").write_text(composition("stills", len(rest)), encoding="utf-8")
    print(json.dumps({"shots": [(s["id"], s["f0"], s["f1"]) for s in shots], "levels": lv}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
