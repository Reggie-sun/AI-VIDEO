#!/usr/bin/env python3
"""Stage 1: ffprobe the source, hash it, decode every frame at low resolution.

Outputs (under work/):
  lowres_rgb.npy   uint8 [N,H,W,3]  every frame, 192x108
  frame_pts.json   per-frame pts (seconds) from ffprobe
and (under analysis root):
  manifest.json    source facts. Written only here; later stages append keys via update_manifest.

Run:  python -I scripts/01_probe_and_decode.py <analysis_root> <video_path>
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 192, 108


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def main(root, video):
    root, video = Path(root), Path(video)
    work = root / "work"
    work.mkdir(exist_ok=True)
    probe = json.loads(
        sh(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)])
    )
    vs = next(s for s in probe["streams"] if s["codec_type"] == "video")
    aus = [s for s in probe["streams"] if s["codec_type"] == "audio"]

    # exact per-frame pts
    pkt = sh(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0", str(video),
        ]
    ).split()
    pts = [float(x) for x in pkt]
    (work / "frame_pts.json").write_text(json.dumps(pts))

    # decode all frames to raw rgb at WxH
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(video), "-an", "-vsync", "0",
        "-vf", f"scale={W}:{H}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
    ]
    p = subprocess.run(cmd, check=True, capture_output=True)
    arr = np.frombuffer(p.stdout, np.uint8)
    n = arr.size // (W * H * 3)
    arr = arr[: n * W * H * 3].reshape(n, H, W, 3)
    np.save(work / "lowres_rgb.npy", arr)

    num, den = vs["r_frame_rate"].split("/")
    fps = int(num) / int(den)
    manifest = {
        "schema": "ev-manifest/v1",
        "source_video": {
            "path_from_repo_root": str(video.relative_to(Path.cwd())) if video.is_absolute() and Path.cwd() in video.parents else str(video),
            "sha256": sha256(video),
            "size_bytes": video.stat().st_size,
            "container": probe["format"]["format_name"],
            "duration_s": float(probe["format"]["duration"]),
            "bit_rate": int(probe["format"]["bit_rate"]),
            "video": {
                "codec": vs["codec_name"], "profile": vs.get("profile"),
                "width": vs["width"], "height": vs["height"],
                "r_frame_rate": vs["r_frame_rate"], "avg_frame_rate": vs["avg_frame_rate"], "fps": fps,
                "pix_fmt": vs["pix_fmt"], "color_space": vs.get("color_space"),
                "color_range": vs.get("color_range"), "color_transfer": vs.get("color_transfer"),
                "color_primaries": vs.get("color_primaries"),
                "nb_frames_reported": vs.get("nb_frames"), "nb_frames_decoded": int(n),
                "pts_count": len(pts),
            },
            "audio": [
                {
                    "codec": a["codec_name"], "sample_rate": int(a["sample_rate"]),
                    "channels": a["channels"], "channel_layout": a.get("channel_layout"),
                    "bit_rate": a.get("bit_rate"), "duration_s": float(a.get("duration", 0)),
                }
                for a in aus
            ],
        },
        "lowres_cache": {"file": "work/lowres_rgb.npy", "width": W, "height": H, "frames": int(n)},
        "frame_index_convention": "frame_index is 0-based; time = frame_index / fps; shot end_frame is inclusive.",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(json.dumps({k: manifest["source_video"][k] for k in ("duration_s",)}), n, fps)


if __name__ == "__main__":
    main(*sys.argv[1:3])
