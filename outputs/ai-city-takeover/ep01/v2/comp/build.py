#!/usr/bin/env python3
"""Build the IRIS EP01 v2 HyperFrames project in this folder (run from the repository root):

  uv run python outputs/ai-city-takeover/ep01/v2/comp/build.py [--chorus comp/chorus.json]

Animatic stage: every shot is a still plate (keyframes, the reused A01-v2 frame and A02) moved by the
2.5D camera, with all graphics, lyrics and the approved song. Generated video
shots replace the stills later without changing timing.
- data: beat map of the approved song bed, lyric words, cut and cue times (events.json)
- audio: the approved song mix (song/mix/IRIS-01-v2.wav)
- fonts: CJK + Latin display faces (+ c14: Nimbus Sans Bold, the headline lyric face) subset to the glyphs in src and motion-kit
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

COMP = Path(__file__).resolve().parent
V2 = COMP.parent
EP01 = V2.parent
REPO = COMP.parents[4]
KIT = REPO / "motion-kit"
W, H, FPS, DUR = 1920, 1080, 30, 30.5
KEYFRAMES = ("K1a", "K1b", "K3", "K4", "K5", "K5b", "K7", "K8b", "K9b", "K9e", "P7", "P8b", "P8c")


def events(data: Path, chorus: dict, inserts: list) -> dict:
    """Cut times and graphic cues (comp seconds, frame-quantised). The engine reads the cuts from here,
    and qa.py checks each cue against the rendered frames: one timing source for both. A chorus pass (chorus.json)
    adds a cut for each later segment: on a lyric line's vocal entry, two frames early like the other vocal cuts, or
    on the last eighth note before a take stops being in sync (the author's EV cut, from the take's sync.json)."""
    beats = json.loads((data / "beats.json").read_text())
    lines = json.loads((data / "words.json").read_text())["lines"]
    down, bt = beats["downbeats"], beats["beats"]
    def q(t):
        return math.ceil(t * FPS - 1e-6) / FPS

    def beat(bar, k):
        return bt[bt.index(down[bar]) + k]

    def vocal(i):                                                     # a vocal entry cuts two frames early
        return lines[i]["start"] - 2 / FPS

    def word(i, j, end=False):
        return lines[i]["words"][j]["end" if end else "start"]

    # c3: back to c1's cut on "woke" (c2 moved it to beat(1, 3), 3.37 s: "节奏变快了"); S1v3's in-point puts the
    # eye opening before it instead (seq.py)
    cut = {"S2": word(1, 4), "S3": beat(2, 2), "S4": beat(4, 1), "S5": down[6], "S6": down[7], "S7": beat(7, 3),
           "S8a": vocal(11), "S8b": vocal(13), "S9a": vocal(15), "S9b": vocal(16)}
    # c10 (user on c9: 「对比原作者还是太单调,元素太少,片段太少,内容太少,也不够高级」): inserts on the words they explain,
    # two frames early like the vocal cuts: the resolver diagram on "misconfigured", the city on "It reached the
    # internet", the eleven-day count on "Eleven", her last look on "through", back to the chip on "cache"
    def early(li, wi):
        return word(li, wi) - 2 / FPS

    cut.update({"S3d": early(3, 2), "S4c": vocal(5), "S5d": vocal(7), "S9h": early(16, 4), "S9b2": early(16, 6)})
    eighths = sorted(bt + [(a + b) / 2 for a, b in zip(bt, bt[1:])])
    for p in chorus["passes"]:
        segs = {s["shot"]: s for s in p["segments"]}
        for seg in p["segments"][1:]:
            start = seg["start"]
            if "at_line" in start:
                cut[seg["shot"]] = vocal(start["at_line"])
            elif "at_word" in start:                                  # a cutaway on one word, two frames early
                cut[seg["shot"]] = word(*start["at_word"]) - 2 / FPS
            else:                                                     # the author's cut: the last eighth before drift
                take = segs[start["eighth_before_sync_end_of"]]
                until = json.loads((V2 / take["sync"]).read_text())["synced_until"]["song_s"]
                cut[seg["shot"]] = max(e for e in eighths if e <= until)
    ev = {f"cut_{k}": {"t": q(v), "what": f"cut to {k}"} for k, v in cut.items()}
    # c12 (user on c11: 「還不夠，繼續加」): inserts cut away and back without moving a c11 cut (inserts.json); the back cut
    # is cut_<id>_back unless the insert runs into a c11 cut
    def at(spec):
        if "at_word" in spec:
            return word(*spec["at_word"]) - 2 / FPS
        if "at_beat" in spec:                                         # c13: a half index is the eighth between two beats
            b = spec["at_beat"]
            return bt[int(b)] + (b - int(b)) * (bt[int(b) + 1] - bt[int(b)])
        if spec["cut"] in cut:
            return cut[spec["cut"]]
        return at(next(i for i in inserts if i["id"] == spec["cut"])["start"])   # c13: runs into the next insert
    for ins in inserts:
        t0, t1 = q(at(ins["start"])), q(at(ins["end"]))
        if not 0.3 - 1e-6 <= t1 - t0 <= 0.8 + 1e-6:
            raise SystemExit(f"{ins['id']}: {t1 - t0:.3f} s, inserts are 0.3-0.8 s")
        ev[f"cut_{ins['id']}"] = {"t": t0, "what": f"insert {ins['id']} ({ins['kind']} {ins.get('take') or ins.get('plate')})"}
        if "cut" not in ins["end"]:
            ev[f"cut_{ins['id']}_back"] = {"t": t1, "what": f"back from insert {ins['id']}"}
    # the camera's one impact: the first track hit after the chorus cut (hits.json, 19.06 s, the song's strongest);
    # motion-kit/src/beatcam.js shows it one frame early by design, so qa.py should read it at -1 frame
    hits = json.loads((data / "hits.json").read_text())["hits"]
    entry = min((h["t"] for h in hits if h["t"] >= q(cut["S8a"])), default=None)
    if entry is not None:
        ev["chorus_impact"] = {"t": q(entry), "what": "impact on the chorus entry hit (picture one frame early)"}
    around = max(word(6, 2), cut["S5"] + 2 / FPS)
    # ROIs (screen px) bound each cue to where its graphic lands, so lyric changes elsewhere do not count
    ev.update({
        "s1_timecode": {"t": q(beat(0, 1)), "what": "03:47 lands on beat 1", "roi": [1160, 400, 560, 260]},
        "s2_title": {"t": q(cut["S2"]), "what": "title slams in with the cut", "roi": [110, 380, 620, 130]},
        "s2_date": {"t": q(word(2, 0)), "what": "incident date OSD on 'September'", "roi": [1300, 70, 540, 60]},
        "s3_model": {"t": q(word(2, 3)), "what": "研究模型 on 'training'", "roi": [230, 250, 260, 70]},
        "s3_resolver": {"t": q(word(3, 1)), "what": "DNS 解析器 on 'resolver'", "roi": [800, 300, 300, 380]},
        "s3d_error": {"t": q(word(3, 2)), "what": "resolver node turns red on 'misconfigured'", "roi": [810, 400, 300, 280]},
        "s4_reach": {"t": q(word(5, 1)), "what": "the probe breaches the glass on 'reached'", "roi": [60, 500, 110, 120]},
        "s5d_count": {"t": q(word(7, 0)), "what": "the eleven-day count starts on 'Eleven'", "roi": [560, 180, 800, 600]},
        "s5_window": {"t": q(around), "what": "far window lights on 'around'", "roi": [330, 300, 100, 90]},
        "s6_pause": {"t": q(cut["S6"] + 1 / FPS), "what": "最强模型训练 暂停 11 天", "roi": [120, 220, 600, 180]},
        "s7_offline": {"t": q(cut["S7"]), "what": "离线 with the cut", "roi": [120, 160, 380, 140]},
        "s9a_shut": {"t": q(word(15, 4, end=True)), "what": "door shut, 已修复 tag", "roi": [600, 120, 420, 120]},
        "s9b_redteam": {"t": q(cut["S9b"] + 1 / FPS), "what": "另一项红队测试", "roi": [1160, 190, 650, 140]},
        "s9b_card": {"t": q(min(word(16, 6, end=True), DUR - 0.4)), "what": "03:48 card", "roi": [1550, 480, 330, 110]},
    })
    # c11 (ev-gap-c10.md, all nine items approved): the kinetic words land on their sung/spoken word; the inversion turns
    # on the beat of "The door is closed" and back 1.5 beats later (s9a_invert_end). main.js reads these times.
    the = word(15, 1)
    bi = min(range(len(bt)), key=lambda i: abs(bt[i] - the))
    # back to dark ground on the "and" after the next beat (1.5 beats): clear of the shut cue and of the S9b cut
    # (c11 first render: turning back on the shut itself made cut_S9b read 3 frames early in qa.py)
    ev.update({
        "k_still": {"t": q(word(8, 5)), "what": "STILL on 'still'", "roi": [1250, 430, 520, 230]},
        "k_offline": {"t": q(word(9, 5)), "what": "OFFLINE on 'offline'", "roi": [1300, 520, 520, 200]},
        "s9a_invert": {"t": q(bt[bi]), "what": "white-ground inversion on the beat of 'The door'"},
        "s9a_invert_end": {"t": q(bt[bi + 1] + (bt[bi + 2] - bt[bi + 1]) / 2), "what": "back to the dark ground 1.5 beats later"},
        "k_closed": {"t": q(word(15, 4)), "what": "CLOSED on 'closed' (inverted ground)", "roi": [1120, 420, 600, 240]},
    })
    return ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chorus", type=Path, default=COMP / "chorus.json", help="chorus edit (seq.py reads the same file)")
    ap.add_argument("--inserts", type=Path, default=COMP / "inserts.json", help="c12 inserts; --inserts none rebuilds c11")
    ap.add_argument("--main", type=Path, default=COMP / "src/main.js", help="scene code (c11: src/main-c11.js)")
    args = ap.parse_args()
    chorus = json.loads(args.chorus.read_text())
    ins = json.loads(args.inserts.read_text()) if args.inserts.name != "none" else {"inserts": [], "pips": []}
    data = COMP / "data"
    data.mkdir(exist_ok=True)
    for name in ("beats", "hits"):
        shutil.copyfile(V2 / f"song/bed-01/beatmap/{name}.json", data / f"{name}.json")
    (data / "music.json").write_text(json.dumps({"song_offset": 0.0, "window_bar0": 0, "source": "IRIS-01-v2"}))
    shutil.copyfile(V2 / "timing/words.json", data / "words.json")
    (data / "events.json").write_text(json.dumps({"events": events(data, chorus, ins["inserts"])}, ensure_ascii=False, indent=1))
    shots = {s["shot"]: {k: s[k] for k in ("kind", "plate", "from", "to", "scrim", "sung", "span", "in") if k in s}
             for p in chorus["passes"] for s in p["segments"]}
    (data / "chorus.json").write_text(json.dumps({"shots": shots}, ensure_ascii=False, indent=1))
    (data / "inserts.json").write_text(json.dumps({"inserts": {i["id"]: {k: i[k] for k in ("kind", "plate", "from", "to", "mark") if k in i}
                                                               for i in ins["inserts"]},
                                                   "pips": {p["id"]: {k: p[k] for k in ("kind", "plate", "crop", "to", "frames") if k in p}
                                                            for p in ins["pips"]}}, ensure_ascii=False, indent=1))

    plates = COMP / "plates"
    plates.mkdir(exist_ok=True)
    for k in KEYFRAMES:
        shutil.copyfile(V2 / f"keyframes/raw/{k}-a.png", plates / f"{k}.png")
    shutil.copyfile(EP01 / "reference-package/A02-v1.png", plates / "A02.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.0", "-i", str(EP01 / "shots/A01-v2.mp4"),
                    "-frames:v", "1", str(plates / "A01v2.png")], check=True)

    audio = COMP / "audio"
    audio.mkdir(exist_ok=True)
    shutil.copyfile(V2 / "song/mix/IRIS-01-v2.wav", audio / "IRIS-01-v2.wav")

    subprocess.run([sys.executable, str(KIT / "tools/fonts.py"), "--out", str(COMP / "fonts"), "--latin", "--grotesk",
                    "--scan", str(COMP / "src"), str(KIT / "src"), str(data / "words.json")], check=True)
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(args.main), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={COMP / 'engine.js'}", "--log-level=warning"], check=True)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>IRIS 01 Looked Outside</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-start="0" data-duration="{DUR}" data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{DUR}" data-track-index="0"></canvas>
  <audio id="music" src="audio/IRIS-01-v2.wav" data-start="0" data-duration="{DUR}" data-track-index="1" data-volume="1" data-timeline-role="music"></audio>
</div>
<script src="engine.js"></script>
</body>
</html>
"""
    (COMP / "index.html").write_text(html, encoding="utf-8")
    print(json.dumps({"plates": len(KEYFRAMES) + 2, "duration": DUR}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
