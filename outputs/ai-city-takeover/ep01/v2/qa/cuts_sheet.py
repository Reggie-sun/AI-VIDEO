"""Frames -6, -1, 0, +6 around every cut of a render (cut frames from comp/data/events.json), one row per cut:

  uv run python outputs/ai-city-takeover/ep01/v2/qa/cuts_sheet.py RENDER.mp4 comp/data/events.json OUT.jpg
"""
import json
import math
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
video, events, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ev = json.loads(events.read_text())["events"]
cuts = sorted(((math.ceil(v["t"] * 30 - 1e-6), k[4:]) for k, v in ev.items() if k.startswith("cut_")))
offs = (-6, -1, 0, 6)
frames = sorted({f + o for f, _ in cuts for o in offs})
tmp = out.parent / "_cutframes"
tmp.mkdir(parents=True, exist_ok=True)
expr = "+".join(f"eq(n\\,{f})" for f in frames)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"select='{expr}',scale=384:216", "-vsync", "0",
                str(tmp / "%04d.jpg")], check=True)
got = sorted(tmp.glob("*.jpg"))
im = {f: Image.open(p).convert("RGB") for f, p in zip(frames, got)}
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
sheet = Image.new("RGB", (len(offs) * 386 + 120, len(cuts) * 218), (12, 12, 12))
d = ImageDraw.Draw(sheet)
for r, (f, name) in enumerate(cuts):
    d.text((6, r * 218 + 90), f"{name}\n{f / 30:.3f}s\nf{f}", fill=(255, 220, 0), font=font)
    for c, o in enumerate(offs):
        sheet.paste(im[f + o], (120 + c * 386, r * 218))
        d.text((124 + c * 386, r * 218 + 2), f"{o:+d}", fill=(255, 255, 255), font=font)
sheet.save(out, quality=86)
for p in got:
    p.unlink()
tmp.rmdir()
print(out, len(cuts), "cuts")
