#!/usr/bin/env python3
"""Extract full-resolution (1920x1080) frames and optional crops for close inspection.

Run: python -I scripts/extract_full.py <analysis_root> <out_dir_relative_to_root> <frame>[,<frame>...] [crop=x,y,w,h[,scale]]
  Frames are 0-based. Crop is in 1920x1080 pixel coordinates; optional integer upscale (default 1, use 2-3 for small HUD text).
  Writes <root>/<out_dir>/f<frame>.jpg (or f<frame>_crop_<x>_<y>.png).
Examples:
  ... extract_full.py <root> work/full 1500,1512
  ... extract_full.py <root> work/full 1500 crop=1480,120,260,100,3
"""
import subprocess
import sys
from pathlib import Path

VIDEO = "outputs/anabology-opus55-replica/source/2103533196721704960.mp4"


def main(root, outdir, frames, crop=None):
    root = Path(root)
    out = root / outdir
    out.mkdir(parents=True, exist_ok=True)
    repo = root.parents[2]  # <repo>/outputs/anabology-opus55-replica/escape_velocity_analysis
    video = str(repo / VIDEO)
    for f in [int(x) for x in frames.split(",")]:
        vf = f"select=eq(n\\,{f})"
        if crop:
            p = [int(x) for x in crop.split("=")[1].split(",")]
            x, y, w, h = p[:4]
            sc = p[4] if len(p) > 4 else 1
            vf += f",crop={w}:{h}:{x}:{y}" + (f",scale={w*sc}:{h*sc}:flags=neighbor" if sc > 1 else "")
            dst = out / f"f{f}_crop_{x}_{y}.png"
        else:
            dst = out / f"f{f}.jpg"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", vf, "-vsync", "0", "-frames:v", "1"]
        cmd += (["-q:v", "2"] if dst.suffix == ".jpg" else []) + [str(dst)]
        subprocess.run(cmd, check=True)
        print(dst)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4] if len(a) > 4 else None)
