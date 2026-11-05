#!/usr/bin/env python3
"""Decode full-res review frames in one pass; never generate or alter source media."""
import json
import hashlib
import subprocess
import sys
from pathlib import Path


def main(root):
    root = Path(root).resolve()
    shots = json.loads((root / "work/shots.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    video = root.parents[2] / manifest["source_video"]["path_from_repo_root"]
    with video.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != manifest["source_video"]["sha256"]:
        raise RuntimeError("source SHA differs from manifest; do not decode or reuse cache")
    frames = set()
    for s in shots:
        a, b = s["start_frame"], s["end_frame"]
        frames.update((a, (a+b)//2, b))
        if b-a < 12:
            frames.update(range(a, b+1))
        else:
            frames.update(range(a, min(a+9, b+1), 2))
            frames.update(range(max(a, b-8), b+1, 2))
    frames = sorted(frames)
    out = root / "work/full_batch"
    out.mkdir(exist_ok=True)
    index = out / "index.json"
    old = json.loads(index.read_text()) if index.exists() else {}
    if (old.get("source_sha256") == actual and old.get("frames") == frames
            and all((out/f"{f:05d}.jpg").exists() for f in frames)):
        print("exact requested review frames already present", len(frames))
        return
    temp = out / "decode"
    temp.mkdir(exist_ok=True)
    select = "+".join(f"eq(n\\,{f})" for f in frames)
    subprocess.run(["ffmpeg", "-v", "error", "-threads", "2", "-i", str(video),
                    "-vf", "select="+select, "-vsync", "0", "-q:v", "2", "-start_number", "0",
                    str(temp/"frame_%06d.jpg")], check=True)
    decoded = sorted(temp.glob("frame_*.jpg"))
    if len(decoded) != len(frames):
        raise RuntimeError(f"selected frames mismatch: {len(decoded)} != {len(frames)}")
    for path, f in zip(decoded, frames):
        path.replace(out/f"{f:05d}.jpg")
    temp.rmdir()
    (out/"index.json").write_text(json.dumps(dict(source_sha256=manifest["source_video"]["sha256"],
        width=1920, height=1080, frames=frames, method="single ffmpeg decode; select by decoded frame index"), indent=1)+"\n")
    print("full-resolution review frames", len(frames))


if __name__ == "__main__":
    main(sys.argv[1])
