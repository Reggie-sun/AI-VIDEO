#!/usr/bin/env python3
"""The viewing-scale compare: top row 4 EV frames, bottom row 4 of ours, each 640 px wide (the size the user watches at).
Run from the repository root:  uv run python .../qa/view640.py <render.mp4> <out.png>"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

EV = "outputs/anabology-opus55-replica/source/2103533196721704960.mp4"
EV_T = [74.0, 80.0, 86.0, 92.0]
OUR_T = [4.8, 13.2, 17.4, 21.6]          # render time: s011 walk, s012 close-up, s013 sung take, s014 walk-off


def main():
    render, out = sys.argv[1], Path(sys.argv[2])
    tmp = Path("/tmp/iris-view640"); tmp.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (2560, 720))
    for row, (src, ts) in enumerate(((EV, EV_T), (render, OUR_T))):
        for i, t in enumerate(ts):
            p = tmp / f"r{row}{i}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", src, "-frames:v", "1", str(p)], check=True)
            sheet.paste(Image.open(p).convert("RGB").resize((640, 360), Image.LANCZOS), (i * 640, row * 360))
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
