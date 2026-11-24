#!/usr/bin/env python3
"""Whole-frame compare for the interface's legibility under the print (v4r4): ours at 1080p beside EV at 1080p, two
pairs (ours song 49.72 s / EV 88.0 s: a singing face with the interface; ours 44.4 s / EV 46.0 s: the expanded panel),
and a 1:1 strip of the top-left interface of each (600x320). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa/fullframe_compare.py <render.mp4> <out.png> [--window-f0 244]
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

EV = "outputs/anabology-opus55-replica/source/2103533196721704960.mp4"
OFFSET, FPS = 26.0528, 24
PAIRS = [(49.72, 88.0), (44.40, 46.0)]


def main() -> int:
    render, out = sys.argv[1], Path(sys.argv[2])
    f0 = int(sys.argv[sys.argv.index("--window-f0") + 1]) if "--window-f0" in sys.argv else 244
    tmp = Path("/tmp/iris-fullframe"); tmp.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (3840, 2160 + 320))
    for row, (to, te) in enumerate(PAIRS):
        o, e = tmp / f"o{row}.png", tmp / f"e{row}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", render, "-vf", f"select=eq(n\\,{round((to - OFFSET) * FPS) - f0})", "-vsync", "0",
                        "-frames:v", "1", str(o)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(te), "-i", EV, "-frames:v", "1", str(e)], check=True)
        sheet.paste(Image.open(o).convert("RGB"), (0, row * 1080))
        sheet.paste(Image.open(e).convert("RGB"), (1920, row * 1080))
        if row == 0:
            sheet.paste(Image.open(o).convert("RGB").crop((0, 0, 600, 320)), (0, 2160))
            sheet.paste(Image.open(e).convert("RGB").crop((0, 0, 600, 320)), (1920, 2160))
            sheet.paste(Image.open(o).convert("RGB").crop((1320, 0, 1920, 320)), (620, 2160))
            sheet.paste(Image.open(e).convert("RGB").crop((1320, 0, 1920, 320)), (2540, 2160))
    sheet.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
