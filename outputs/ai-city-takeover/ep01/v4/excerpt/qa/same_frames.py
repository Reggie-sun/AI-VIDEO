#!/usr/bin/env python3
"""Two window renders at the same song times, one row each, 640 px wide per frame (the viewing size).
  uv run python .../qa/same_frames.py <top.mp4> <bottom.mp4> <out.png> [44.0,49.5,53.5,56.0]"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

OFFSET, FPS, F0 = 26.0528, 24, 244


def main():
    a, b, out = sys.argv[1:4]
    times = [float(t) for t in (sys.argv[4] if len(sys.argv) > 4 else "44.0,49.5,53.5,56.0").split(",")]
    tmp = Path("/tmp/iris-same"); tmp.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (640 * len(times), 720))
    for row, src in enumerate((a, b)):
        for i, t in enumerate(times):
            n = round((t - OFFSET) * FPS) - F0
            p = tmp / f"{row}{i}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"select=eq(n\\,{n})", "-vsync", "0", "-frames:v", "1", str(p)], check=True)
            sheet.paste(Image.open(p).convert("RGB").resize((640, 360), Image.LANCZOS), (i * 640, row * 360))
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
