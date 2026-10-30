#!/usr/bin/env python3
"""Build the T01 HyperFrames project in this folder (run from the repository root):

  uv run python outputs/ai-city-takeover/phase1-t01/comp/build.py [--guide]

- beats/hits: ../analysis/{beats,hits}.json when the real song has been analysed, otherwise a
  synthetic 120 BPM grid (development only) written to data/.
- music: audio/t01.wav when present (cut from the real song); with --guide and no music, a
  synthesized TEMPORARY guide track is written instead (never delivered as music).
- plates, mask and paths are copied from ../plates; fonts are subset from system OFL faces;
  src/main.js + motion-kit are bundled with esbuild into engine.js; index.html is generated.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

COMP = Path(__file__).resolve().parent
UNIT = COMP.parent
REPO = COMP.parents[3]
KIT = REPO / "motion-kit"
W, H, FPS, DUR = 1920, 1080, 30, 10.0


def synthetic_grid(bpm=120.0, start=-4.0, end=40.0):
    spb = 60.0 / bpm
    n = int(round((end - start) / spb)) + 1
    beats = [round(start + i * spb, 6) for i in range(n)]
    downbeats = beats[::4]
    kick = beats[:]
    snare = [b for i, b in enumerate(beats) if i % 4 in (1, 3)]
    hat = sorted(beats + [round(b + spb / 2, 6) for b in beats])
    return ({"duration": end, "beats": beats, "downbeats": downbeats, "tempo": [{"t": 0, "bpm": bpm}],
             "downbeat_phase": 0, "downbeat_method": "synthetic-development-only"},
            {"kick": kick, "snare": snare, "hat": hat, "hits": [{"t": 6.0, "score": 1.0}],
             "risers": [{"t0": 4.0, "t1": 6.0, "land": 6.0}], "fills": [], "vocal_entries": [], "env24": {}})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guide", action="store_true")
    args = ap.parse_args()
    data = COMP / "data"
    data.mkdir(exist_ok=True)
    music_cfg = {"song_offset": 0.0, "window_bar0": 2, "source": "synthetic-120bpm"}
    real_beats, real_hits = UNIT / "analysis/beats.json", UNIT / "analysis/hits.json"
    window = UNIT / "analysis/window.json"
    if real_beats.exists() and real_hits.exists() and window.exists():
        shutil.copyfile(real_beats, data / "beats.json")
        shutil.copyfile(real_hits, data / "hits.json")
        music_cfg = json.loads(window.read_text())
    else:
        b, h = synthetic_grid()
        (data / "beats.json").write_text(json.dumps(b))
        (data / "hits.json").write_text(json.dumps(h))
    (data / "music.json").write_text(json.dumps(music_cfg, ensure_ascii=False, indent=1))

    plates = COMP / "plates"
    plates.mkdir(exist_ok=True)
    for p in ("P1L", "P2L", "P3L"):
        shutil.copyfile(UNIT / f"plates/work/{p}-dn.png", plates / f"{p}.png")
    shutil.copyfile(UNIT / "plates/work/P2L-interior.png", plates / "P2L-interior.png")
    shutil.copyfile(UNIT / "plates/P3L-paths.json", data / "P3L-paths.json")

    audio = COMP / "audio"
    audio.mkdir(exist_ok=True)
    music = audio / "t01.wav"
    guide = audio / "guide-TEMPORARY.wav"
    if not music.exists() and args.guide:
        subprocess.run([sys.executable, str(KIT / "tools/guide_track.py"), "--beats", str(data / "beats.json"),
                        "--hits", str(data / "hits.json"), "--start", str(music_cfg["song_offset"]),
                        "--dur", str(DUR), "--out", str(guide)], check=True)
    track = "audio/t01.wav" if music.exists() else ("audio/guide-TEMPORARY.wav" if guide.exists() else None)

    subprocess.run([sys.executable, str(KIT / "tools/fonts.py"), "--out", str(COMP / "fonts"),
                    "--scan", str(COMP / "src"), str(KIT / "src")], check=True)
    esbuild = REPO / "node_modules/.bin/esbuild"
    subprocess.run([str(esbuild), str(COMP / "src/main.js"), "--bundle", "--format=iife", "--target=chrome120",
                    f"--outfile={COMP / 'engine.js'}", "--log-level=warning"], check=True)

    audio_tag = (f'  <audio id="music" src="{track}" data-start="0" data-duration="{DUR}" data-track-index="1" '
                 f'data-volume="1" data-timeline-role="music"></audio>\n') if track else ""
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>T01 最后一位人类司机</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-start="0" data-duration="{DUR}" data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{DUR}" data-track-index="0"></canvas>
{audio_tag}</div>
<script src="engine.js"></script>
</body>
</html>
"""
    (COMP / "index.html").write_text(html, encoding="utf-8")
    print(json.dumps({"music": track, "grid": music_cfg["source"], "engine": "engine.js"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
