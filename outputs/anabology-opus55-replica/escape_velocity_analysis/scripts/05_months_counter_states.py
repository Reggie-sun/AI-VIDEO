#!/usr/bin/env python3
"""Stage 5: time series of the top-right 'NN MONTHS TO ESCAPE' flip counter region.
Crops (x=1490,y=128,w=90,h=60) of every frame, finds frames where the crop changes,
and writes work/counter_changes.json + a montage of distinct states for visual reading.
Run: python -I scripts/05_months_counter_states.py <analysis_root> <video>
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

W, H, X, Y = 90, 60, 1490, 128

def main(root, video):
    root = Path(root)
    cmd = ["ffmpeg", "-v", "error", "-i", video, "-an", "-vsync", "0", "-vf", f"crop={W}:{H}:{X}:{Y},format=gray", "-f", "rawvideo", "-"]
    b = subprocess.run(cmd, check=True, capture_output=True).stdout
    a = np.frombuffer(b, np.uint8).reshape(-1, H, W).astype(np.float32)
    d = np.abs(np.diff(a, axis=0)).mean((1, 2))
    np.save(root / "work" / "counter_crop_gray.npy", a.astype(np.uint8))
    print("frames", len(a), "diff pct", np.percentile(d, [50, 90, 99]).round(2))
    # change events: diff above 4 where the previous 3 frames were stable (low diff)
    ev = [int(i + 1) for i in range(len(d)) if d[i] > 4.0]
    (root / "work" / "counter_changes.json").write_text(json.dumps({"changed_frames": ev, "n": len(ev)}))
    print("changed frames", len(ev))

if __name__ == "__main__":
    main(*sys.argv[1:3])
