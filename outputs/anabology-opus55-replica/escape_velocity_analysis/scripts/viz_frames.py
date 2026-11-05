#!/usr/bin/env python3
"""Make a labelled contact sheet from frame indices (uses work/f960 dump).

Run: python -I scripts/viz_frames.py <analysis_root> <out.jpg> <cols> <tile_w> <idx1,idx2,...>
Tiles are labelled `frame / time`. Use `a:b:s` for ranges (inclusive b, step s).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse(spec):
    out = []
    for tok in spec.split(","):
        if ":" in tok:
            a, b, s = (int(x) for x in tok.split(":"))
            out += list(range(a, b + 1, s))
        else:
            out.append(int(tok))
    return out


def main(root, out, cols, tile_w, spec):
    root = Path(root)
    cols, tile_w = int(cols), int(tile_w)
    idx = parse(spec)
    tile_h = tile_w * 9 // 16
    rows = (len(idx) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", max(11, tile_w // 28))
    except OSError:
        font = ImageFont.load_default()
    for k, i in enumerate(idx):
        im = Image.open(root / "work" / "f960" / f"{i:05d}.jpg").convert("RGB").resize((tile_w, tile_h), Image.LANCZOS)
        x, y = (k % cols) * tile_w, (k // cols) * tile_h
        sheet.paste(im, (x, y))
        label = f"{i} {i/24:.2f}s"
        d.rectangle([x, y, x + len(label) * (tile_w // 28 + 4) + 6, y + tile_w // 22 + 6], fill=(0, 0, 0))
        d.text((x + 3, y + 2), label, fill=(255, 235, 60), font=font)
    sheet.save(out, quality=88)


if __name__ == "__main__":
    main(*sys.argv[1:6])
