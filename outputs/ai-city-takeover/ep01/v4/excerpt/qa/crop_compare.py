#!/usr/bin/env python3
"""The same-box crop compare (review/compare3): EV left, ours right, native 1080p crops of 760x430, and the texture
numbers on exactly those crops (qa/texture.py). The boxes were found by template matching the user's evidence sheet
crop-compare.png: EV 84.75 s at (592,120) and 81.25 s at (576,296); ours song 49.72 s at (152,0) and 42.22 s at
(704,152). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa/crop_compare.py <render.mp4> <out.png> [--window-f0 244]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texture import measure  # noqa: E402

EV = "outputs/anabology-opus55-replica/source/2103533196721704960.mp4"
EV_BOXES = [(84.75, (592, 120)), (81.25, (576, 296))]
OUR_BOXES = [(49.72, (152, 0)), (42.22, (704, 152))]
OFFSET, FPS = 26.0528, 24


def grab(src: str, t: float | None, frame: int | None, dst: str) -> None:
    if frame is not None:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"select=eq(n\\,{frame})", "-vsync", "0", "-frames:v", "1", dst], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", src, "-frames:v", "1", dst], check=True)


def main() -> int:
    render, out = sys.argv[1], Path(sys.argv[2])
    f0 = int(sys.argv[sys.argv.index("--window-f0") + 1]) if "--window-f0" in sys.argv else 244
    tmp = Path("/tmp/iris-crop-compare"); tmp.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (1520, 860))
    specs = {"ev": [], "ours": []}
    for row, ((te, be), (to, bo)) in enumerate(zip(EV_BOXES, OUR_BOXES)):
        ev_png, our_png = tmp / f"ev{row}.png", tmp / f"our{row}.png"
        grab(EV, te, None, str(ev_png))
        grab(render, None, round((to - OFFSET) * FPS) - f0, str(our_png))
        for side, png, b, x in (("ev", ev_png, be, 0), ("ours", our_png, bo, 760)):
            im = Image.open(png).convert("RGB")
            sheet.paste(im.crop((b[0], b[1], b[0] + 760, b[1] + 430)), (x, row * 430))
            specs[side].append(f"{png}@{b[0]},{b[1]},760,430")
    sheet.save(out)
    res = {side: [measure(s) for s in v] for side, v in specs.items()}
    keys = ["crisp", "lap", "fine", "detail", "sat", "warm"]
    table = {side: [{k: r[k] for k in keys} | {"screen": r["peak2d"]} for r in rows] for side, rows in res.items()}
    out.with_suffix(".json").write_text(json.dumps(table, indent=1))
    print(json.dumps(table, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
