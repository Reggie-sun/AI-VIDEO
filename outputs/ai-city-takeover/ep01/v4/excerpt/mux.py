#!/usr/bin/env python3
"""Final mux of the excerpt. Run from the repository root after the HyperFrames render:

  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/hf-render.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/mux.py [--v2 | --v3]   (vN: -c composition-vN.html -o renders/hf-render-vN.mp4)

Why: HyperFrames' own AAC track starts 1024 samples (21.3 ms, the encoder priming) late against the master, measured by
cross-correlation in qa.py, because its mux carries no edit list for the priming. The picture is HyperFrames' bitstream
copied unchanged; the sound is the master's samples for the window (audio/master-026-059.wav, cut without resample or
level change) encoded once to AAC-LC 320 kb/s by ffmpeg, whose mux trims the priming. The HyperFrames file is removed
after its SHA-256 is recorded in renders/render-provenance.json.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, FPS, FRAMES, V4R1_F0, V4R1_F1, V4R7_F1  # noqa: E402


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    tag = "-v4r11" if "--v4r11" in sys.argv else "-v4r10c" if "--v4r10c" in sys.argv else "-v4r10b" if "--v4r10b" in sys.argv else "-v4r10" if "--v4r10" in sys.argv else "-v4r9" if "--v4r9" in sys.argv else "-v4r8" if "--v4r8" in sys.argv else "-v4r7" if "--v4r7" in sys.argv else "-v4r6" if "--v4r6" in sys.argv else "-v4r5" if "--v4r5" in sys.argv else "-v4r4" if "--v4r4" in sys.argv else "-v4r3" if "--v4r3" in sys.argv else "-v4r2" if "--v4r2" in sys.argv else "-v4r1" if "--v4r1" in sys.argv else "-v3" if "--v3" in sys.argv else "-v2" if "--v2" in sys.argv else ""
    hf = EXC / f"renders/hf-render{tag}.mp4"
    out = EXC / (f"renders/IRIS-EP01-v4-excerpt{tag}-036-059.mp4" if tag in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else f"renders/IRIS-EP01-v4-excerpt{tag}-036-051.mp4" if tag.startswith("-v4r") else f"renders/IRIS-EP01-v4-excerpt-026-059{tag}.mp4")
    wav = EXC / ("audio/master-v4r7-036-059.wav" if tag in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else "audio/master-v4r1-036-051.wav" if tag.startswith("-v4r") else "audio/master-026-059.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(hf), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-t", f"{((V4R7_F1 if tag in ('-v4r7', '-v4r8', '-v4r9', '-v4r10', '-v4r10b', '-v4r10c', '-v4r11') else V4R1_F1) - V4R1_F0 if tag.startswith('-v4r') else FRAMES) / FPS:.6f}", "-movflags", "+faststart",
                    str(out)], check=True)
    prov = {"hyperframes_render": {"file": hf.name, "sha256": sha(hf), "bytes": hf.stat().st_size},
            "audio_source": {"file": str(wav.relative_to(EXC)), "sha256": sha(wav)},
            "final": {"file": out.name, "sha256": sha(out), "bytes": out.stat().st_size},
            "how": "video stream copied from the HyperFrames render; AAC-LC 320k encoded by ffmpeg from the master slice"}
    (EXC / f"renders/render-provenance{tag}.json").write_text(json.dumps(prov, indent=1))
    hf.unlink()
    print(json.dumps(prov, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
