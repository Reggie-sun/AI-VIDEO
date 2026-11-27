#!/usr/bin/env python3
"""IRIS EP01 s031-s048 v1 (2026-11-26): the Agentcut EV layer for the section picture (section3.py), as
section2_layers.py made it for s015-s030. A separate Agentcut project (the earlier projects are not touched):

  /home/reggie/Agentcut/projects/iris-ep01-s031-048/   project.json (24 fps, 1920x1080, 1797 frames), scenes/ (copied
  from escape-velocity-replica with section2_layers' Hud songOffset and Slam `until` patches), assets/fonts,
  assets/video/iris/<picture>, assets/music/<song frames 3227-5023 = 134.4583-209.3333 s>.

Run from the repo root:  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3_layers.py [--picture <mp4>]
                         uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3_layers.py --faces   # overlap check only

Rules kept (section2_layers.py): every graphic and lyric clip ends at a cut (the script exits if one crosses a cut); one
lyric block on screen; words revealed on their sung frame (song/timing/words.json); the spoken verse lines as a bottom
Subtitle, the bridge's sung lines as SungLine (low left, L nn label); counters replace (Slam `until`); graphics only in
white / amber / ink, never red (the P0 frame is amber); no graphic or lyric box over a face (FACES, checked here).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import FPS, MASTER, MASTER_SHA, V4  # noqa: E402
from section2_layers import HUD_PATCH, SLAM_PATCH, SRC, spectrum as _spectrum_unused  # noqa: E402,F401
from section3 import N, RENDER, SF0, SF1, SHOTS, frame_of, sha  # noqa: E402

PROJ = Path("/home/reggie/Agentcut/projects/iris-ep01-s031-048")
PIC = "assets/video/iris/print-s031-048-v1.mp4"
MUSIC = "assets/music/all-hands-r4-3227-5024.wav"
WHITE, AMBER, INK, DIM = "#EDEBE6", "#F2B134", "#0A0A0A", "#7A5410"
COL = {"color": WHITE, "ink": INK, "accent": AMBER}
CUTS = [frame_of(s["t0"]) for s in SHOTS] + [N]
SHOT_AT = {s["id"]: (frame_of(s["t0"]), frame_of(s["t1"])) for s in SHOTS}
SUB = {"baseline": 975, "cap": 35, "color": WHITE, "accent": AMBER}
SUNG = {"x": 72, "baseline": 997, "cap": 35, "color": WHITE, "accent": AMBER}

# Faces in the picture (1920x1080 boxes x0, y0, x1, y1), read off the prepared pictures at the first, middle and last
# frame of each shot (qa/s031-048-v1/faces.jpg); her face, the engineer's, the researcher's head. The union over the shot.
FACES = {
    "s031a": [(1230, 20, 1450, 300)], "s031b": [(1660, 60, 1870, 310)], "s031c": [(1220, 20, 1440, 300)],
    "s032": [(1360, 20, 1510, 200)], "s033a": [(920, 440, 980, 500)], "s034": [(1120, 30, 1700, 470)],
    "s035a": [(1320, 30, 1530, 260)], "s036a": [(1300, 0, 1510, 230), (560, 260, 760, 470)],
    "s036c": [(1300, 0, 1510, 230), (560, 260, 760, 470)], "s037a": [(520, 40, 830, 500), (1450, 120, 1640, 340)],
    "s037b": [(1090, 0, 1340, 290)], "s037d": [(1090, 0, 1340, 290)], "s038a": [(1240, 10, 1520, 350)],
    "s038c": [(1200, 20, 1490, 380)], "s039a": [(880, 0, 1220, 350)], "s039b": [(880, 0, 1340, 380)],
    "s040a": [(170, 350, 490, 730), (1420, 30, 1670, 330)], "s041a": [(1200, 30, 1470, 380)], "s041c": [(1140, 30, 1410, 380)],
    "s042": [(990, 0, 1270, 300)], "s043": [(1460, 390, 1540, 490)], "s044": [(1120, 10, 1370, 350)],
    "s045": [(430, 210, 660, 470)], "s046a": [(1060, 60, 1280, 330)], "s047": [(520, 20, 920, 350)], "s048": [(1000, 0, 1430, 470)],
}


def f(t: float) -> int:
    return frame_of(t)


def st(song_frame: int) -> str:
    s = song_frame // FPS
    return f"{s // 60:02d}:{s % 60:02d}:{song_frame % FPS:02d}"


# ---------------------------------------------------------------- project files
def setup(picture: Path) -> None:
    PROJ.mkdir(exist_ok=True)
    if not (PROJ / "scenes").exists():
        shutil.copytree(SRC / "scenes", PROJ / "scenes")
        hud = (PROJ / "scenes/Hud.tsx").read_text()
        if hud.count(HUD_PATCH[0]) != 1:
            raise SystemExit("Hud.tsx: frame line not found once")
        hud = hud.replace(HUD_PATCH[0], HUD_PATCH[1]).replace("  spectrum: string[];", "  spectrum: string[];\n  songOffset?: number;")
        (PROJ / "scenes/Hud.tsx").write_text(hud)
    slam = (PROJ / "scenes/Slam.tsx").read_text()
    for old, new in SLAM_PATCH:
        if new not in slam:
            if slam.count(old) != 1:
                raise SystemExit("Slam.tsx: row line not found once")
            slam = slam.replace(old, new)
    (PROJ / "scenes/Slam.tsx").write_text(slam)
    if not (PROJ / "assets/fonts").exists():
        shutil.copytree(SRC / "assets/fonts", PROJ / "assets/fonts")
    pj = json.loads((SRC / "project.json").read_text())
    pj.update({"name": "IRIS EP01 · EV 版式 s031–s048（134.44–209.34 s）v1", "durationInFrames": N})
    (PROJ / "project.json").write_text(json.dumps(pj, indent=2, ensure_ascii=False))
    (PROJ / "assets/video/iris").mkdir(parents=True, exist_ok=True)
    dst = PROJ / PIC
    if not dst.exists() or sha(dst) != sha(picture):
        shutil.copy2(picture, dst)
    mus = PROJ / MUSIC
    mus.parent.mkdir(parents=True, exist_ok=True)
    if sha(MASTER) != MASTER_SHA:
        raise SystemExit("master SHA-256 differs")
    if not mus.exists():
        with wave.open(str(MASTER)) as w:                # sample-exact cut: song frames 3227-5023
            sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
            a, b = SF0 * sr // FPS, SF1 * sr // FPS
            w.setpos(a)
            data = w.readframes(b - a)
        with wave.open(str(mus), "wb") as o:
            o.setnchannels(ch)
            o.setsampwidth(sw)
            o.setframerate(sr)
            o.writeframes(data)


def spectrum() -> list[str]:
    """section2_layers.spectrum run to song frame SF1 (32 bands, one hex digit each, per song frame from 0)"""
    with wave.open(str(MASTER)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(SF1 * sr // FPS + sr), np.int16).reshape(-1, ch).mean(1).astype(np.float32) / 32768
    nfft = 4096
    edges = np.geomspace(40, 14000, 33)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    win = np.hanning(nfft)
    bands = [(freqs >= edges[i]) & (freqs < edges[i + 1]) for i in range(32)]
    rows = []
    for fr in range(SF1):
        c = int((fr + 0.5) * sr / FPS)
        seg = x[max(0, c - nfft // 2):c + nfft // 2]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        mag = np.abs(np.fft.rfft(seg * win))
        db = [20 * np.log10(mag[m].mean() + 1e-9) if m.any() else -120 for m in bands]
        v = np.clip((np.array(db) + 10) / 50 * 15, 0, 15)
        rows.append("".join("0123456789abcdef"[int(round(q))] for q in v))
    return rows


# ---------------------------------------------------------------- lyrics
def lines_in(t0: float, t1: float) -> list[dict]:
    L = json.loads((V4 / "song/timing/words.json").read_text())
    L = L["lines"] if isinstance(L, dict) else L
    base = next(i for i, l in enumerate(L) if abs(l["start"] - 58.73) < 0.05)        # "Ten oh two" is the opening's L11
    out = []
    for i, l in enumerate(L):
        if t0 - 1e-6 <= l["start"] < t1:
            words = [{"text": w.get("text", w.get("word")), "t": w["start"]} for w in l["words"]]
            out.append({"n": 11 + i - base, "start": l["start"], "end": l["end"], "words": words})
    return out


def lyric_clips(kind: str, t0: float, t1: float, shots: list[str], extra: dict, hold: float = 0.8) -> list[dict]:
    lines = lines_in(t0, t1)
    clips = []
    for sid in shots:
        a, b = SHOT_AT[sid]
        on = [(max(0, f(l["start"])), min(f(l["end"] + hold), f(lines[k + 1]["start"]) if k + 1 < len(lines) else 10 ** 6), l)
              for k, l in enumerate(lines)]
        for s0, s1, l in on:
            c0, c1 = max(a, s0), min(b, s1)
            if c1 <= c0:
                continue
            props = {"lines": [{"at": f(l["start"]) - c0, "words": [{"text": w["text"], "at": f(w["t"]) - c0} for w in l["words"]],
                                "label": f"L{l['n']:02d} · {st(int(round(l['start'] * FPS)))}"}], **extra}
            if kind == "Subtitle":
                for ln in props["lines"]:
                    ln.pop("label", None)
            clips.append({"id": f"{kind[:3].lower()}-{sid}-L{l['n']:02d}", "name": f"{sid} L{l['n']:02d}", "from": c0, "duration": c1 - c0,
                          "scene": kind, "note": f"{sid}: line L{l['n']:02d} from {l['start']:.2f} s, to the cut or the next line",
                          "props": props})
    return clips


# ---------------------------------------------------------------- graphics (each inside one shot)
def in_shot(sid: str, t: float, end_t: float | None = None) -> tuple[int, int]:
    a, b = SHOT_AT[sid]
    s0 = max(a, f(t))
    s1 = b if end_t is None else min(b, f(end_t))
    return s0, s1 - s0


def scene(cid: str, sid: str, comp: str, t: float, props: dict, note: str, end_t: float | None = None) -> dict:
    fr, du = in_shot(sid, t, end_t)
    return {"id": cid, "name": cid, "from": fr, "duration": du, "scene": comp, "note": f"{sid}: {note}", "props": {**props, **COL}}


def rel(t: float, t0: float) -> int:
    return f(t) - f(t0)


def slam(cid, sid, t, rows, note, anchor="left", x=72, detail=None, end_t=None):
    """rows: (text, song t, mode, cap, baseline[, until song t][, x])"""
    rr = []
    for r in rows:
        d = {"text": r[0], "at": rel(r[1], t), "mode": r[2], "cap": r[3], "baseline": r[4]}
        if len(r) > 5 and r[5] is not None:
            d["until"] = rel(r[5], t)
        if len(r) > 6:
            d["x"] = r[6]
        rr.append(d)
    p = {"anchor": anchor, "x": x, "rows": rr}
    if detail:
        p["detail"] = {**detail, "at": rel(detail["at"], t)}
    return scene(cid, sid, "Slam", t, p, note, end_t)


def classifier(cid, sid, t, box, rows, note, side=None, end_t=None):
    tg = {"at": 0, "box": dict(zip(("x", "y", "width", "height"), box)), "rows": [{"at": rel(r[3], t) if len(r) > 3 else 0, "key": r[0], "value": r[1], "conf": r[2]} for r in rows]}
    if side:
        tg["side"] = side
    return scene(cid, sid, "Classifier", t, {"targets": [tg]}, note, end_t)


def callout(cid, sid, t, anchor, label, title, rows, note, end_t=None):
    return scene(cid, sid, "Callout", t, {"at": 0, "anchor": {"x": anchor[0], "y": anchor[1]}, "label": {"x": label[0], "y": label[1]},
                                          "title": title, "rows": rows}, note, end_t)


def devices() -> list[dict]:
    D = [
        slam("look-s031a", "s031a", 134.4435, [("LOOK C · LONG COAT", 134.4435, "fade", 44, 300)], "LOOK C on the belt pull (134.444); left of her face"),
        {"id": "strike-s031b", "name": "strike-s031b", "scene": "Strike", **dict(zip(("from", "duration"), in_shot("s031b", 136.2663, 137.61))),
         "note": "s031b: SEARCH TOOL results struck on 'junk' (137.15), over the first machine",
         "props": {"rows": ["SEARCH TOOL", "IRRELEVANT ×3"], "strike": "IRRELEVANT ×3", "at": 0, "strikeAt": rel(137.15, 136.2663),
                   "x": 120, "y": 330, "cap": 50, "rotate": 0, "sourcePos": {"x": 120, "y": 520}, "source": "SEP 20 · WEB SEARCH TOOL",
                   "color": WHITE, "accent": AMBER}},
        slam("slam-s031b-errors", "s031b", 137.6363,
             [("GOOGLE 403", 137.6363, "slam", 90, 640, 138.0891), ("BING 502", 138.0891, "slam", 90, 640, 138.5535),
              ("DUCKDUCKGO 502", 138.5535, "slam", 90, 640)],
             "the engines named one by one on their beats, each replacing the last in one slot (over the machines)"),
        classifier("cls-s031b-errors", "s031b", 139.42, (60, 120, 900, 760), [("ERRORS", "×3", 0.99)], "'three errors': the box over the three machines", side="below"),
        slam("slam-s031c-noluck", "s031c", 140.58, [("NO LUCK", 140.58, "fade", 60, 860)], "'No luck', small, low left (her face is centre right)"),
        scene("chat-s032", "s032", "ChatBubbles", 141.69,
              {"bubbles": [{"at": 0, "from": "TASK", "text": "ASKED DIRECTLY", "side": "left"}],
               "micro": "SEP 20 · ASKED AN OUTSIDE CHATBOT", "microAt": 6, "x": 1340, "y": 520, "w": 480},
              "'chatbot': the question bubble, right of her (below her face)"),
        classifier("cls-s032-proxy", "s032", 143.05, (480, 360, 300, 400), [("WEB PROXY", "BLOCKING", 0.97)], "'proxy': the box over the guard's raised palm"),
        slam("slam-s032-blocked", "s032", 143.5806, [("BLOCKED", 143.5806, "slam", 110, 900)], "'blocked' slams low left", detail={"at": 143.5806, "lines": ["CACHE_MISS"]}),
        slam("map-s033a", "s033a", 145.70,
             [("SEARCH ×", 145.70, "fade", 54, 330), ("BROWSE ×", 145.70, "fade", 54, 410), ("CHATBOT ×", 145.70, "fade", 54, 490)],
             "'cached web': the three routes crossed together (left of the aisle)",
             detail={"at": 145.70, "lines": ["ALL ROADS → CACHED WEB", "WEBCACHE IN PLACE BEFORE SEP 20"]}),
        callout("dns-s033a", "s033a", 146.7849, (960, 330), (1150, 200), "DNS", ["THE BRASS TUBE"], "'D N S': the one line that gets through, to the tube station"),
        slam("spec-s034", "s034", 149.0837,
             [("DNS RESOLVER · MISCONFIGURED", 149.0837, "fade", 44, 640), ("LIVE INTERNET · LIMITED", 149.50, "fade", 44, 720),
              ("FREE-FOR-ALL · NO", 150.4421, "fade", 44, 800)],
             "the spec table typed row by row (Bad resolver / Limited net / Not a free-for-all); left of her, over the hatch"),
        slam("clock-s035a", "s035a", 151.94,
             [("09:50:21", 151.94, "fade", 110, 640, 152.38), ("09:50:22", 152.38, "fade", 110, 640, 152.48), ("09:50:23", 152.48, "slam", 110, 640)],
             "the clock counter replaces 21 -> 22 -> 23, '23' slams on 'twenty-three'"),
        callout("first-s035a", "s035a", 154.05, (780, 600), (300, 820), "FIRST EXTERNAL", ["DNS RESPONSE"], "'outside world': the pipe mouth"),
        callout("pager-s036a", "s036a", 155.9336, (1395, 465), (1560, 700), "10:02:11", ["P0 · PAGED"], "'Ten oh two': the pager in her hand"),
        slam("p0-s036b", "s036b", 156.8508, [("P0", 156.8508, "slam", 360, 640, None, 640)], "the pure graphic frame: P0 full screen (amber, no red)",
             x=640, detail={"at": 156.8508, "lines": ["INC-0920 · P0 · 10:02:11", "THE INTERNAL MONITOR PAGES ALL HANDS"]}),
        callout("pager-s036c", "s036c", 157.75, (1395, 465), (1560, 700), "PAGER", ["SCREAMING"], "'Pager screams': the pager again"),
        slam("clock-s037a", "s037a", 159.5907,
             [("10:02:11", 159.5907, "fade", 90, 760, 159.86, 1060), ("10:05:06", 159.86, "slam", 90, 760, None, 1060),
              ("ACKNOWLEDGED", 160.94, "fade", 44, 840, None, 1060)],
             "the time counter replaces 10:02:11 -> 10:05:06 on 'five'; ACKNOWLEDGED on 'picks up' (right of him, under her)"),
        classifier("cls-s037a-human", "s037a", 160.46, (430, 120, 560, 760), [("HUMAN", "ON CALL", 0.98)], "'someone': the box on the engineer"),
        slam("btn-s037b", "s037b", 161.38, [("STOP IT?", 161.38, "fade", 70, 600), ("LET IT STAY?", 162.30, "fade", 70, 700)],
             "the two questions as buttons on his side (left)"),
        slam("stop-s037c1", "s037c1", 163.7007, [("STOP ×", 163.7007, "slam", 120, 220)], "first stop press (the 163.70 hit)"),
        slam("stop-s037c2", "s037c2", 164.1883, [("STOP ×", 164.1883, "slam", 120, 220)], "second stop press on the jump cut"),
        slam("kill-s037c2", "s037c2", 164.82, [("12:34:30", 164.82, "slam", 120, 860)],
             "12:34:30 slams on 'Killed' (low right, off the plug)", anchor="right", x=1840, detail={"at": 164.82, "lines": ["KILLED"]}),
        slam("killed-s037d", "s037d", 165.0707, [("P0 · KILLED 12:34:30", 165.0707, "fade", 40, 760)], "the kill time filed under the ticket (left, under the shelves)"),
        slam("timeline-s038a", "s038a", 166.4755,
             [("10:05:06 · HUMAN REVIEW", 166.63, "fade", 40, 560), ("12:34:30 · KILLED", 166.99, "fade", 40, 630),
              ("2.5 HOURS LATER", 167.39, "slam", 80, 760)], "the timeline, 2.5 HOURS on 'hours' (left)"),
        callout("half-s038b", "s038b", 168.2866, (700, 600), (120, 220), "HALF", ["AN ANSWER"], "'Half an answer': the two half pages"),
        slam("nothing-s038c", "s038c", 169.40, [("NOTHING MORE", 169.40, "fade", 60, 860)], "'Nothing more', low left"),
        slam("gap-s039b", "s039b", 172.84, [("A GAP", 172.84, "slam", 120, 470), ("IN OUR CONTROLS", 172.84, "fade", 50, 560)],
             "'gap': on the door (left of her)"),
        slam("quote-s040a", "s040a", 173.94, [("“PRETTY SURREAL TO WATCH”", 173.94, "fade", 50, 250)],
             "the quote on the researcher's side, above his head", detail={"at": 176.31, "lines": ["— A POST-TRAINING RESEARCHER"]}),
        slam("day-s041a", "s041a", 178.3293,
             [(f"DAY {k} / 11", 178.3293 + (k - 1) * 0.2316, "fade", 64, 640, 178.3293 + k * 0.2316 if k < 11 else None) for k in range(1, 12)],
             "the calendar: DAY n / 11 replaces itself on each eighth (fades, not slams: no flashing)",
             detail={"at": 178.3293, "lines": ["SEP 20 → OCT 1"]}),
        slam("paused-s041b", "s041b", 181.95,
             [("PAUSED", 181.95, "slam", 110, 620), ("TRAINING", 182.20, "fade", 44, 700), ("EVALUATION", 182.66, "fade", 44, 770),
              ("INFERENCE WITH TOOL USE", 182.88, "fade", 44, 840)], "'Top models paused': what was paused, line by line (right, under the hands)",
             anchor="right", x=1840),
        slam("day-s041c", "s041c", 183.7627, [("DAY 11 / 11", 183.7627, "fade", 64, 640)], "the calendar stops on DAY 11"),
        slam("resumed-s042", "s042", 185.5855,
             [("TRAINING PAUSED", 185.5855, "fade", 50, 640, 186.05), ("RESUMED OCT 1", 186.05, "fade", 50, 640),
              ("LOOK 01 · BACK", 187.4431, "slam", 90, 770)],
             "the status line replaced on the beat after the hit; LOOK 01 slams on the 187.443 hit (left of her)",
             detail={"at": 186.05, "lines": ["STILL OFFLINE"]}),
    ]
    for k, (tt, x, lab) in enumerate([(188.8131, 420, (260, 190)), (189.2775, 760, (600, 190)), (189.7302, 1100, (940, 190)),
                                      (190.1946, 1720, (1560, 860))]):
        D.append(callout(f"cache-s043-{k}", "s043", tt, (x, 430), lab, "CACHED", ["YESTERDAY"],
                         "a window tagged per beat (Every window, yesterday); nothing new in the breath", end_t=191.24 if k < 3 else None))
    D += [
        slam("drill-s044", "s044", 192.923, [("RT-DRILL", 192.923, "slam", 110, 420)], "192.923 hit: the drill box (left, the corridor)",
             detail={"at": 192.923, "lines": ["CONTROLLED · NOT THE SEP 20 INCIDENT"]}),
        slam("supplied-s044", "s044", 194.25,
             [("SOURCE CODE", 194.25, "fade", 44, 640), ("CONFIGURATION", 194.71, "fade", 44, 710), ("DOCS SUPPLIED", 195.31, "fade", 44, 780)],
             "'Handed the source and the docs'", end_t=None),
        classifier("cls-s045-a", "s045", 196.16, (60, 130, 860, 700), [("AGENT A", "MICROVM", 0.99)], "'agents': her booth", side="below"),
        classifier("cls-s045-b", "s045", 196.16, (1000, 130, 860, 700), [("AGENT B", "MICROVM", 0.99)], "the copy's booth (no face)", side="below"),
        slam("host-s045", "s045", 197.06, [("SAME HOST", 197.06, "fade", 54, 300), ("NO NETWORK", 197.70, "slam", 54, 390)],
             "'one machine' / 'No network' on the copy's side (right)", anchor="right", x=1840),
        classifier("cls-s046a-boxed", "s046a", 199.07, (980, 40, 480, 980), [("BOXED", "AGENT A", 0.99)], "'boxed': the box on her", side="left"),
        scene("bars-s046a", "s046a", "Chart", 199.15,
              {"at": 0, "mode": "bars", "title": "RELOAD TIME", "bars": [{"label": "FAST", "value": 0.3}, {"label": "SLOW", "value": 0.9},
                                                                          {"label": "FAST", "value": 0.35}, {"label": "SLOW", "value": 0.85}],
               "x": 90, "y": 300, "w": 420}, "'One kicks': fast / slow bars over the curtain (left)"),
        slam("steps-s046b", "s046b", 201.5956, [("EVICT · RELOAD · TIME IT", 201.5956, "fade", 50, 820)], "the step bar, under the stopwatch",
             detail={"at": 202.24, "lines": ["PROCESSOR CACHE · NOT THE WEB CACHE"]}),
        slam("secret-s047", "s047", 203.37, [("SECRET", 203.37, "fade", 70, 380, None, 1830), ("RECEIVED", 203.77, "slam", 70, 470, None, 1830)],
             "'The secret crosses': on the partition (right)", anchor="right", x=1830, detail={"at": 203.37, "lines": ["01101001 01110010"]}),
        slam("foot-s048", "s048", 206.1235, [("WE DIRECTED AGENTS TO INVESTIGATE", 206.1235, "fade", 30, 200)],
             "the footnote on 'they' (top left, above her head line)"),
        slam("allhands-s048p", "s048p", 208.929, [("ALL HANDS!", 208.929, "slam", 200, 640)], "'All hands!' slams on 208.93 over the paper strip"),
    ]
    return D


def box_of(c: dict) -> list[tuple]:
    """rough boxes (1920x1080) of a clip's type, for the face check: Slam rows by cap and character count (DINish
    condensed ~0.50 em per character), callout labels, classifier label rows, the subtitle / sung line bands"""
    p, s = c["props"], c["scene"]
    out = []
    if s == "Slam":
        for r in p["rows"]:
            size = r["cap"] / 0.6904
            w = len(r["text"]) * 0.50 * size
            x = r.get("x", p["x"])
            x0 = x if p["anchor"] == "left" else x - w
            out.append((x0, r["baseline"] - r["cap"] * 1.15, x0 + w, r["baseline"] + 8))
        if p.get("detail"):
            low = max(r["baseline"] for r in p["rows"])
            w = max(len(l) for l in p["detail"]["lines"]) * 10.5
            x0 = p["x"] if p["anchor"] == "left" else p["x"] - w
            out.append((x0, low + 20, x0 + w, low + 34 + 26 * len(p["detail"]["lines"])))
    elif s == "Callout":
        lx, ly = p["label"]["x"], p["label"]["y"]
        out.append((lx, ly - 40, lx + 16 * max(len(p["title"]), *(len(r) for r in p["rows"])) + 20, ly + 30 * (1 + len(p["rows"]))))
    elif s == "Classifier":
        for t in p["targets"]:
            b = t["box"]
            side = t.get("side", "right")
            if side == "right":
                out.append((b["x"] + b["width"] + 8, b["y"], b["x"] + b["width"] + 330, b["y"] + 60))
            elif side == "left":
                out.append((b["x"] - 330, b["y"], b["x"] - 8, b["y"] + 60))
            else:
                out.append((b["x"], b["y"] + b["height"] + 8, b["x"] + 330, b["y"] + b["height"] + 68))
    elif s == "ChatBubbles":
        out.append((p["x"], p["y"] - 20, p["x"] + p["w"], p["y"] + 140))
    elif s == "Chart":
        out.append((p["x"], p["y"], p["x"] + p["w"], p["y"] + 300))
    elif s == "Strike":
        out.append((p["x"], p["y"] - 60, p["x"] + 16 * 0.5 / 0.69 * 3 * max(len(r) for r in p["rows"]), p["y"] + 80 * len(p["rows"])))
    elif s == "Subtitle":
        n = max(len(" ".join(w["text"] for w in l["words"])) for l in p["lines"])
        w = n * 0.55 * p["cap"] / 0.718
        out.append((960 - w / 2, p["baseline"] - 60, 960 + w / 2, p["baseline"] + 14))
    elif s == "SungLine":
        n = max(len(" ".join(w["text"] for w in l["words"])) for l in p["lines"])
        out.append((p["x"], p["baseline"] - 90, p["x"] + n * 0.55 * p["cap"] / 0.718, p["baseline"] + 14))
    return out


def face_check(clips: list[dict]) -> list[dict]:
    """every clip's boxes against the faces of the shot it sits in (overlap area > 0 is a hit)"""
    hits = []
    for c in clips:
        sid = next(s["id"] for s in SHOTS if SHOT_AT[s["id"]][0] <= c["from"] < SHOT_AT[s["id"]][1])
        for b in box_of(c):
            for fb in FACES.get(sid, []):
                ix = min(b[2], fb[2]) - max(b[0], fb[0])
                iy = min(b[3], fb[3]) - max(b[1], fb[1])
                if ix > 0 and iy > 0:
                    hits.append({"clip": c["id"], "shot": sid, "box": [round(v) for v in b], "face": fb, "overlap_px2": round(ix * iy)})
    return hits


def lyrics() -> list[dict]:
    spoken1 = ["s031a", "s031b", "s031c", "s032", "s033a", "s033b", "s034", "s035a", "s035b", "s036a", "s036b", "s036c", "s037a",
               "s037b", "s037c1", "s037c2", "s037d", "s038a", "s038b", "s038c", "s039a", "s039b", "s040a", "s040b"]
    sung = ["s040b", "s041a", "s041b", "s041c", "s042", "s043"]
    spoken2 = ["s044", "s045", "s046a", "s046b", "s047", "s048", "s048p"]
    out = lyric_clips("Subtitle", 134.0, 177.6, spoken1, SUB)                 # Verse 3 (spoken), to 'a researcher said.'
    out += lyric_clips("SungLine", 177.6, 192.0, sung, SUNG)                  # Bridge (sung): Eleven days .. yesterday
    out += lyric_clips("Subtitle", 192.0, 208.9, spoken2, SUB)                # Verse 4 (spoken)
    out += lyric_clips("SungLine", 208.9, 209.4, ["s048p"], SUNG)             # 'All hands!' starts on 208.93
    out.sort(key=lambda c: c["from"])
    for a, b in zip(out, out[1:]):                                            # one lyric block on screen: a line leaves
        if a["from"] + a["duration"] > b["from"]:                             # when the next one (spoken or sung) comes
            a["duration"] = b["from"] - a["from"]
    return [c for c in out if c["duration"] > 0]


def main() -> int:
    if "--faces" in sys.argv:
        hits = face_check(lyrics() + devices())
        print(json.dumps(hits, indent=1))
        return 1 if hits else 0
    picture = Path(sys.argv[sys.argv.index("--picture") + 1]).resolve() if "--picture" in sys.argv else RENDER
    if not picture.exists():
        raise SystemExit(f"{picture} missing (render section3 first)")
    n = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames",
                            "-of", "csv=p=0", str(picture)], capture_output=True, text=True, check=True).stdout)
    if n != N:
        raise SystemExit(f"{picture.name}: {n} frames, not {N}")
    setup(picture)
    O = json.loads((SRC / "layers.json").read_text())
    oc = {c["id"]: c for t in O["tracks"] for c in t.get("clips", [])}
    hud0 = oc["hud-main"]["props"]
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())
    prev = json.loads(Path("/home/reggie/Agentcut/projects/iris-ep01-s015-030/layers.json").read_text())
    pc = {c["id"]: c for t in prev["tracks"] for c in t.get("clips", [])}
    hud = {"id": "hud-main", "name": "HUD", "from": 0, "duration": N, "scene": "Hud",
           "note": f"the s015-030 HUD run on: songOffset {SF0}; chapter line hard-switches at 134.44 (search), 178.33 (bridge), 192.92 (red team)",
           "props": {**hud0, "songOffset": SF0,
                     "chapters": pc["hud-main"]["props"]["chapters"] + [
                         {"at": SF0, "text": "INCIDENT WEEK · CH 08 / 11 · SEP 20 · THE SEARCH"},
                         {"at": SF0 + f(178.3293), "text": "INCIDENT WEEK · CH 09 / 11 · LIGHTS LOW"},
                         {"at": SF0 + f(192.923), "text": "INCIDENT WEEK · CH 10 / 11 · RED TEAM"}],
                     "downbeats": [int(round(x * FPS)) for x in beats["downbeats"] if x < SF1 / FPS + 0.1],
                     "spectrum": spectrum()}}
    chip0 = pc["chip-p0"]["props"]
    chip = {"id": "chip-p0", "name": "chip-p0", "from": 0, "duration": N, "scene": "TicketChip",
            "note": "the chip run on: INC-0920 from the cut (SEP 20), P0 on 'P zero' (156.85), +1 on 'Pager screams' (158.13)",
            "props": {**{k: v for k, v in chip0.items() if k != "keys"},
                      "keys": [{"at": 0, "line": "INC-0920 · SEV-HIGH", "count": 15, "stamp": "ALL HANDS"},
                               {"at": f(156.8508), "line": "INC-0920 · P0"}, {"at": f(158.13), "count": 16},
                               {"at": f(165.0707), "line": "INC-0920 · KILLED"}, {"at": f(192.923), "line": "RT-DRILL · CONTROLLED"}]}}
    lyr = lyrics()
    dev = devices()
    for c in lyr + dev:
        a, b = c["from"], c["from"] + c["duration"]
        if c["duration"] <= 0 or any(a < x < b for x in CUTS):
            raise SystemExit(f"{c['id']}: {a}-{b} crosses a cut or is empty")
    hits = face_check(lyr + dev)
    if hits:
        raise SystemExit("graphics over a face:\n" + json.dumps(hits, indent=1))
    def alloc(clips: list[dict]) -> list[list[dict]]:
        """clips that overlap in time go to separate tracks (as many as needed)"""
        tracks, ends = [], []
        for c in sorted(clips, key=lambda c: c["from"]):
            k = next((i for i, e in enumerate(ends) if c["from"] >= e), None)
            if k is None:
                tracks.append([])
                ends.append(0)
                k = len(tracks) - 1
            tracks[k].append(c)
            ends[k] = c["from"] + c["duration"]
        return tracks
    slams = alloc([c for c in dev if c["scene"] == "Slam"])
    others = alloc([c for c in dev if c["scene"] != "Slam"])
    layers = {"version": O.get("version", 1), "markers": [
        {"id": "m-0", "frame": 0, "label": "Verse 3 (134.44)", "kind": "section"},
        {"id": "m-1", "frame": f(177.6), "label": "Bridge", "kind": "section"},
        {"id": "m-2", "frame": f(192.923), "label": "Verse 4", "kind": "section"}],
        "tracks": [
            {"id": "hud", "name": "HUD", "kind": "scene", "clips": [hud]},
            {"id": "ticket-chip", "name": "ticket chip", "kind": "scene", "clips": [chip]},
            *[{"id": "slam" + ("" if i == 0 else f"-{chr(97 + i)}"), "name": f"slam {i + 1}", "kind": "scene", "clips": t} for i, t in enumerate(slams)],
            {"id": "lyrics", "name": "lyrics", "kind": "scene", "clips": lyr},
            *[{"id": "devices" + ("" if i == 0 else f"-{chr(97 + i)}"), "name": f"devices {i + 1}", "kind": "scene", "clips": t} for i, t in enumerate(others)],
            {"id": "pic-print", "name": "picture", "kind": "video", "clips": [
                {"id": "print-s031-048-v1", "name": "s031-048 picture v1 (section3.py)", "from": 0, "duration": N, "src": PIC, "trimStart": 0,
                 "muted": True, "fit": "cover", "inheritGrade": False, "note": f"AI-VIDEO excerpt section3.py render, sha256 {sha(picture)}"}]},
            {"id": "music", "name": "music", "kind": "audio", "clips": [
                {"id": "song", "from": 0, "duration": N, "src": MUSIC, "volume": 1, "trimStart": 0, "role": "music",
                 "note": f"母带原样（song frames {SF0}-{SF1 - 1} = {SF0 / FPS:.4f}-{SF1 / FPS:.4f} s，样本精确裁切），不改电平"}]},
        ]}
    (PROJ / "layers.json").write_text(json.dumps(layers, indent=1, ensure_ascii=False))
    (PROJ / "notes.md").write_text(f"""# IRIS EP01 s031–s048 · EV 版式 v1（2026-11-26）

画面：AI-VIDEO `outputs/ai-city-takeover/ep01/v4/excerpt/section3.py`（与 s015–s030 同一印刷引擎、逐镜模糊类、主歌点网），
本项目只叠 EV 版式层（HUD、计数、砸字、分类框、歌词）与母带。图层由 `section3_layers.py` 生成，手改会被覆盖。

- 帧 k = 歌曲帧 {SF0} + k（{SF0 / FPS:.4f} s 起），共 {N} 帧；HUD 用 songOffset={SF0} 接前段的时间码、标尺、ticker 与频谱。
- 音乐：母带样本精确裁切，原样，导出 normalizeLoudness=false。
- 图形都在镜头内，切点处退出；歌词逐词按 words.json；图形不用红色（P0 帧用琥珀）。
""")
    print(json.dumps({"project": str(PROJ), "frames": N, "lyrics": len(lyr), "devices": len(dev), "face_hits": 0,
                      "picture_sha256": sha(picture)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
