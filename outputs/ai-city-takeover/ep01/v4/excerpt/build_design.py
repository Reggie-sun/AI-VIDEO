#!/usr/bin/env python3
"""Design frames for the excerpt (2026-11-19, reviews/2026-11-19-codex-excerpt-gaps-r3.md section 3). Run from the
repository root after build.py (fonts) and prep_media.py --v4r1 (the walk pictures):

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/build_design.py

Three full composites, rendered by the excerpt engine (src/design.js) one frame each, each frame at its own song time:
1. 49.89 'awake'  - flash/design/D1-b.png (new plate: closed-eye singing close-up, the engineer's shoulder and laptop)
2. 42.77 'NIGHT'  - the walk take as placed in v4r1 (media/seq/s011, the picture where her body and sleeve read)
3. 35.78 'NOT'    - X09b, the de-reddened W1 still (media/stills-w1)
Writes data/edl-design.json, composition-design.html, design/frame-*.png and design/index.html (each frame beside the
v4r1 / v3 frame at the same moment, the EV strip below).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, FPS, H, MASTER, OFFSET, REPO, V4, V4R1_F0, W, frame_of  # noqa: E402

SONG = V4 / "song"
WALK_PIC = 6                  # media/seq/s011/0006.jpg: clip picture 12 (0.50 s), whole body, the sleeve out
FRAMES = [("d1", "frame-1-awake", 49.89, "D1-b", "flash/design/D1-b.png"),
          ("d2", "frame-2-night", 43.15, "walk", f"media/seq/s011/{WALK_PIC:04d}.jpg"),
          ("d3", "frame-3-not", 35.78, "X09b", "media/stills-w1/X09b.png")]


def levels(path: Path) -> list[float]:
    a = np.asarray(Image.open(path).convert("RGB").resize((480, 270)), np.float32) / 255
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    v = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32)).ravel()
    b, w = float(np.percentile(v, 0.5)), float(np.percentile(v, 99.5))
    sc = max(0.85, min(1.2, (0.80 - 0.004) / max(w - b, 1e-3)))
    return [round(b, 5), round(sc, 4), 0.004]


def meter_at(t: float) -> list[float]:
    with wave.open(str(MASTER)) as r:
        sr = r.getframerate()
        r.setpos(int((t - 0.025) * sr))
        x = np.frombuffer(r.readframes(int(0.05 * sr)), np.int16).reshape(-1, 2).astype(np.float32) / 32768
    return [round(float(20 * np.log10(np.sqrt((x[:, c] ** 2).mean()) + 1e-9)), 1) for c in (0, 1)]


V2 = "--v2" in sys.argv          # 2026-11-19: the console restyled in EV's interface language, under the print layer
SUF = "-v2" if V2 else ""


def wave_at(t: float, n: int = 56, step: float = 0.045) -> list[float]:
    """The master's level as n bars of `step` s ending at t (dBFS, both channels): the tiny waveform under the title."""
    with wave.open(str(MASTER)) as r:
        sr = r.getframerate()
        a = int((t - n * step) * sr)
        r.setpos(a)
        x = np.frombuffer(r.readframes(int(n * step * sr)), np.int16).reshape(-1, 2).astype(np.float32).mean(1) / 32768
    m = int(step * sr)
    return [round(float(20 * np.log10(np.sqrt((x[i * m:(i + 1) * m] ** 2).mean()) + 1e-9)), 1) for i in range(n)]


def main() -> int:
    edl = json.loads((EXC / "data/edl-v4r1.json").read_text())
    images = {key: path for _, _, _, key, path in FRAMES}
    shots = [{"id": sid, "t0": t, "t1": t, "f0": i, "f1": i + 1, "kind": "still", "chapter": "c3" if t >= 40.7859 else "c2",
              "stills": [[key, 0]]} for i, (sid, _, t, key, _) in enumerate(FRAMES)]
    d = {**edl, "version": "design", "shots": shots, "images": images, "frames": len(FRAMES),
         "frame_song": [t for _, _, t, _, _ in FRAMES], "levels": {key: levels(EXC / p) for _, _, _, key, p in FRAMES},
         "meter": [meter_at(t) for _, _, t, _, _ in FRAMES], "window_f0": 0, "tracks": {}}
    if V2:
        d["style"] = 2
        d["wave"] = [wave_at(t) for _, _, t, _, _ in FRAMES]
    (EXC / f"data/edl-design{SUF}.json").write_text(json.dumps(d, indent=1))
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(EXC / "src/main.js"), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={EXC / 'engine.js'}", "--log-level=warning"], check=True)
    html = (EXC / "composition-v4r1.html").read_text()
    html = html.replace('data-ex-edl="data/edl-v4r1.json"', f'data-ex-edl="data/edl-design{SUF}.json"')
    import re
    html = re.sub(r' data-ex-offset="[^"]*"', "", html)
    (EXC / f"composition-design{SUF}.html").write_text(html)
    out = EXC / "design"
    out.mkdir(exist_ok=True)
    tmp = Path("/tmp/iris-design-frames")
    shutil.rmtree(tmp, ignore_errors=True)
    subprocess.run(["node", str(EXC / "snap.mjs"), "--comp", f"composition-design{SUF}.html", "--edl", f"data/edl-design{SUF}.json",
                    "--shots", "--out", str(tmp)], check=True)
    for sid, name, *_ in FRAMES:
        shutil.copy2(tmp / f"{sid}-a.png", out / f"{name}{SUF}.png")
    # before: the v4r1 frame at the same song time (frames 1, 2) and the v3 frame (frame 3)
    pairs = []
    for sid, name, t, *_ in FRAMES:
        if t >= 36.2195:
            src, f = EXC / "renders/IRIS-EP01-v4-excerpt-v4r1-036-051.mp4", frame_of(t) - V4R1_F0
            label = f"v4r1 at song {t:.2f} s"
        else:
            src, f = EXC / "renders/IRIS-EP01-v4-excerpt-026-059-v3.mp4", frame_of(t)
            label = f"v3 at song {t:.2f} s"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", f"select=eq(n\\,{f})", "-vsync", "0", "-frames:v", "1",
                        str(out / f"{name}-before.png")], check=True)
        pairs.append((name, t, label))
    shutil.copy2(EXC / "review/compare2/ev-strip.jpg", out / "ev-strip.jpg")
    notes = {"frame-1-awake": "49.89 'awake': her closed-eye singing face first, the engineer second, his sleep line leaping from the laptop edge to AWAKE third. Roster shrunk, his seat selected. One lyric line.",
             "frame-2-night": "43.15 (≈42.77; the SEV flap has settled on HIGH) 'NIGHT': the walk take's picture where her whole body and the long sleeve read (clip 0.50 s; at 42.77 itself the take shows only torso and legs). Roster expanded in the perspective of the two rows, far groups lit, the nearest group lighting; amber in the wet floor; the big word small.",
             "frame-3-not": "35.78 the struck NOT: the light-box macro, cold white glass, the old scratch, her fingertip, one warm reflection along the scratch; NOT struck by the real scratch; ticket narrowed."}
    if V2:
        cards = "".join(f"""<section><h2>{n.replace('-', ' ')}</h2><p>{notes[n]}</p>
<figure><img src="{n}-v2.png"><figcaption><b>v2</b> · the console in EV's interface language (no filled boxes; hairlines, mono micro-type, tiles; under the print layer)</figcaption></figure>
<div class="pair"><figure><img src="{n}.png"><figcaption>v1 design frame (rejected: web-UI chips)</figcaption></figure>
<figure><img src="{n}-before.png"><figcaption>before: {lab}</figcaption></figure></div></section>""" for n, t, lab in pairs)
    else:
        cards = "".join(f"""<section><h2>{n.replace('-', ' ')}</h2><p>{notes[n]}</p><div class="pair"><figure><img src="{n}.png"><figcaption>design frame</figcaption></figure>
<figure><img src="{n}-before.png"><figcaption>before: {lab}</figcaption></figure></div></section>""" for n, t, lab in pairs)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>IRIS EP01 v4 excerpt · design frames</title>
<style>body{{margin:0;background:#0b0c0d;color:#e8e4da;font:15px/1.5 "IBM Plex Mono",monospace}}main{{max-width:2000px;margin:0 auto;padding:28px}}
h1,h2{{font-family:"Nimbus Sans",Helvetica,Arial,sans-serif}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start;margin-top:14px}}figure{{margin:0}}img{{width:100%;display:block}}
figcaption{{font-size:13px;opacity:.75;margin-top:4px}}section{{margin-bottom:40px}}</style></head><body><main>
<h1>IRIS EP01 v4 · excerpt · three design frames (stills, 1920×1080)</h1>
<p>Full composites from the excerpt engine (src/design.js): the on-call console (ticket card, chapter flap, corner marks, SONG / BAR with a master-level meter, the seat roster), one readable result per line, amber only from a source, red only her left-ear lamp. Not a video; each frame beside the v4r1 / v3 frame at the same moment.</p>
{cards}<h2>ESCAPE VELOCITY reference strip</h2><img src="ev-strip.jpg"></main></body></html>"""
    (out / "index.html").write_text(page, encoding="utf-8")
    print(json.dumps({"frames": [str(out / f"{n}{SUF}.png") for n, *_ in pairs], "levels": d["levels"], "meter": d["meter"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
