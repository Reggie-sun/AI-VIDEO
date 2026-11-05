#!/usr/bin/env python3
"""Per-shot gate evidence: decode the project-local video-analysis MCP frames into a sheet and add a
first/mid/last strip and a 4 fps strip of the exact MP4.

  uv run python outputs/ai-city-takeover/ep01/v2/qa/gate_sheet.py <mcp-extract-frames.json> <gate-dir> <mp4>
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

src, gate, mp4 = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
gate.mkdir(parents=True, exist_ok=True)
frames = json.loads(src.read_text())["frames"]
ims = []
for i, f in enumerate(frames):
    p = gate / f"mcp-frame-{i:02d}.jpg"
    p.write_bytes(base64.b64decode(f["base64"]))
    ims.append(Image.open(p))
w, h = ims[0].size
cols = 4
sheet = Image.new("RGB", (cols * w, (len(ims) + cols - 1) // cols * h), "black")
for i, im in enumerate(ims):
    sheet.paste(im, (i % cols * w, i // cols * h))
sheet.save(gate / "mcp-sheet.jpg", quality=85)
count = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-count_frames", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", mp4], capture_output=True, text=True, check=True).stdout)
last, mid = count - 1, (count - 1) // 2
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf",
                f"select='eq(n\\,0)+eq(n\\,{mid})+eq(n\\,{last})',scale=640:-1,tile=3x1", "-vsync", "vfr",
                "-frames:v", "1", str(gate / "first-mid-last.jpg")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=4,scale=320:-1,tile=6x4", "-frames:v", "1",
                str(gate / "quarter-second-sheet.jpg")], check=True)
print(json.dumps({"mcp_frames": len(ims), "frames": count, "sheet": str(gate / "mcp-sheet.jpg")}))
