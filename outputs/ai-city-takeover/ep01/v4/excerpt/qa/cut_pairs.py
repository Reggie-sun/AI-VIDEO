#!/usr/bin/env python3
"""Each cut of a window render, the frame before and the frame after side by side (1920x540 per cut, stacked), from the
render itself. Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa/cut_pairs.py <render.mp4> <out.png> <t,t,...> [--window-f0 244]
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OFFSET, FPS = 26.0528, 24


def main() -> int:
    render, out, times = sys.argv[1], Path(sys.argv[2]), [float(t) for t in sys.argv[3].split(",")]
    f0 = int(sys.argv[sys.argv.index("--window-f0") + 1]) if "--window-f0" in sys.argv else 244
    tmp = Path("/tmp/iris-cut-pairs"); tmp.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (1920, 540 * len(times)))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
    for i, t in enumerate(times):
        c = round((t - OFFSET) * FPS) - f0
        for j, n in enumerate((c - 1, c)):
            p = tmp / f"f{n}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", render, "-vf", f"select=eq(n\\,{n})", "-vsync", "0", "-frames:v", "1", str(p)], check=True)
            im = Image.open(p).convert("RGB").resize((960, 540))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 520, 34), fill=(0, 0, 0))
            d.text((8, 5), f"cut {t:.3f} · {'before' if j == 0 else 'after'} · song {OFFSET + (n + f0) / FPS:.3f}", fill=(255, 220, 120), font=font)
            sheet.paste(im, (j * 960, i * 540))
    sheet.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
