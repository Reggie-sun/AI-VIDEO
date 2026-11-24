#!/usr/bin/env python3
"""IRIS EP01 s015-s030 v1 (2026-11-23): the Agentcut EV layer for the section picture (section2.py), as
agentcut_v2_layers.py --v3 made it for 0-59.23 s. A separate Agentcut project (the opening's project is not touched):

  /home/reggie/Agentcut/projects/iris-ep01-s015-030/   project.json (24 fps, 1920x1080, 1805 frames), scenes/ (copied
  from escape-velocity-replica; Hud.tsx reads songOffset so its SONG time code, ruler, bar count, ticker and spectrum
  run on from the opening's song frame 1422), assets/fonts, assets/video/iris/<picture>, assets/music/<song 59.25-134.4583>.

Run from the repo root:  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section2_layers.py [--picture <mp4>]

Rules kept from the opening (agentcut_v2_layers.py): every graphic and lyric clip ends at a cut (the script exits if
one crosses a cut); one lyric block on screen; words revealed on their sung frame (song/timing/words.json); chorus lines
as SungLine (low left, L nn label), verse lines as Coverline (cap 45, on a free part of the picture); no text in the
picture except these EV graphics; red only her ear lamp (graphics use the opening's white / amber / ink).
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
from edl import EXC, FPS, MASTER, MASTER_SHA, REPO, V4  # noqa: E402
from section2 import N, OFFSET, RENDER, SF0, SF1, SHOTS, frame_of, sha  # noqa: E402

SRC = Path("/home/reggie/Agentcut/projects/escape-velocity-replica")
PROJ = Path("/home/reggie/Agentcut/projects/iris-ep01-s015-030")
SLUG = PROJ.name
PIC = "assets/video/iris/print-s015-030-v1.mp4"
MUSIC = "assets/music/all-hands-r4-1422-3227.wav"
WHITE, AMBER, INK, DIM = "#EDEBE6", "#F2B134", "#0A0A0A", "#7A5410"
COL = {"color": WHITE, "ink": INK, "accent": AMBER}
CUTS = [frame_of(s["t0"]) for s in SHOTS] + [N]
SHOT_AT = {s["id"]: (frame_of(s["t0"]), frame_of(s["t1"])) for s in SHOTS}


def f(t: float) -> int:
    return frame_of(t)


def st(song_frame: int) -> str:
    s = song_frame // FPS
    return f"{s // 60:02d}:{s % 60:02d}:{song_frame % FPS:02d}"


# ---------------------------------------------------------------- project files
HUD_PATCH = ("  const frame = local + p.clip.from;", "  const frame = local + p.clip.from + (p.songOffset ?? 0);")
# Slam rows may end (until, clip frame): a counter's next number replaces the last on its slam frame, in one slot
SLAM_PATCH = [("type Row = { text: string; at: number; mode: \"slam\" | \"fade\"; cap: number; baseline: number; x?: number };",
               "type Row = { text: string; at: number; mode: \"slam\" | \"fade\"; cap: number; baseline: number; x?: number; until?: number };"),
              ("        if (f < r.at) return null;", "        if (f < r.at || (r.until !== undefined && f >= r.until)) return null;")]


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
    pj.update({"name": "IRIS EP01 · EV 版式 s015–s030（59.23–134.44 s）v1", "durationInFrames": N})
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
        with wave.open(str(MASTER)) as w:                # sample-exact cut: song frames 1422-3226 (59.25-134.4583 s)
            sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
            a, b = SF0 * sr // FPS, SF1 * sr // FPS
            w.setpos(a)
            data = w.readframes(b - a)
        with wave.open(str(mus), "wb") as o:
            o.setnchannels(ch)
            o.setsampwidth(sw)
            o.setframerate(sr)
            o.writeframes(data)


# ---------------------------------------------------------------- HUD spectrum (32 bands, one hex digit each, per song frame)
def spectrum() -> list[str]:
    with wave.open(str(MASTER)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(SF1 * sr // FPS + sr), np.int16).reshape(-1, ch).mean(1).astype(np.float32) / 32768
    nfft = 4096
    edges = np.geomspace(40, 14000, 33)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    win = np.hanning(nfft)
    rows = []
    for fr in range(SF1):
        c = int((fr + 0.5) * sr / FPS)
        seg = x[max(0, c - nfft // 2):c + nfft // 2]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        mag = np.abs(np.fft.rfft(seg * win))
        db = []
        for i in range(32):
            m = (freqs >= edges[i]) & (freqs < edges[i + 1])
            db.append(20 * np.log10(mag[m].mean() + 1e-9) if m.any() else -120)
        v = np.clip((np.array(db) + 10) / 50 * 15, 0, 15)          # -60..-10 dB of the frame's FFT -> 0..15 (hex)
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
    """One clip per shot of `shots` while a line of [t0, t1) is up (from its first word to the next line or its end +
    hold): lines and words at frames relative to the clip, so the block leaves at every cut."""
    lines = lines_in(t0, t1)
    clips = []
    for sid in shots:
        a, b = SHOT_AT[sid]
        on = [(f(l["start"]), min(f(l["end"] + hold), f(lines[k + 1]["start"]) if k + 1 < len(lines) else 10 ** 6), l)
              for k, l in enumerate(lines)]
        for s0, s1, l in on:
            c0, c1 = max(a, s0), min(b, s1)
            if c1 <= c0:
                continue
            props = {"lines": [{"at": f(l["start"]) - c0, "words": [{"text": w["text"], "at": f(w["t"]) - c0} for w in l["words"]],
                                "label": f"L{l['n']:02d} · {st(int(round(l['start'] * FPS)))}"}], **extra}
            if kind == "Coverline":
                props["spots"] = [{"at": 0, **extra["spot"]}]
                props = {k: v for k, v in props.items() if k != "spot"}
            clips.append({"id": f"{kind[:3].lower()}-{sid}-L{l['n']:02d}", "name": f"{sid} L{l['n']:02d}", "from": c0, "duration": c1 - c0,
                          "scene": kind, "note": f"{sid}: line L{l['n']:02d} from {l['start']:.2f} s, to the cut or the next line",
                          "props": props})
    return clips


# ---------------------------------------------------------------- graphics (each inside one shot)
def in_shot(sid: str, t: float, end_t: float | None = None, lead: int = 0) -> tuple[int, int]:
    a, b = SHOT_AT[sid]
    s0 = max(a, f(t) - lead)
    s1 = b if end_t is None else min(b, f(end_t))
    return s0, s1 - s0


def scene(cid: str, sid: str, comp: str, t: float, props: dict, note: str, end_t: float | None = None) -> dict:
    fr, du = in_shot(sid, t, end_t)
    return {"id": cid, "name": cid, "from": fr, "duration": du, "scene": comp, "note": f"{sid}: {note}", "props": {**props, **COL}}


def devices() -> list[dict]:
    D = [
        scene("callout-s015c-pager", "s015c", "Callout", 63.8317,
              {"at": 0, "anchor": {"x": 1130, "y": 640}, "label": {"x": 1330, "y": 300}, "title": "P0 · 10:02", "rows": ["PAGE · ACKNOWLEDGED"]},
              "pager callout on the 4K pager insert (covers 'that's my cue')"),
        scene("cls-s016i-answer", "s016i", "Classifier", 69.80,
              {"targets": [{"at": 0, "box": {"x": 700, "y": 260, "width": 520, "height": 560}, "rows": [{"at": 0, "key": "ANSWER", "value": "HALF", "conf": 0.5}]}]},
              "'half': the swinging handset"),
        scene("cls-s017b-handoff", "s017b", "Classifier", 77.69,
              {"targets": [{"at": 0, "box": {"x": 380, "y": 420, "width": 620, "height": 480}, "rows": [{"at": 0, "key": "ON CALL", "value": "HANDED OVER", "conf": 0.99}]}]},
              "'all': the pager in his palm"),
        scene("look-s019", "s019", "Callout", 86.7846,
              {"at": 0, "anchor": {"x": 1000, "y": 420}, "label": {"x": 360, "y": 330}, "title": "LOOK", "rows": ["BLACK · DOUBLE-BREASTED", "FOR THE HEARING"]},
              "look card on the 86.78 downbeat (the coat on, the door pushed); no number (brief); the label on the dark corridor "
              "upper left (at 1340, 260 it sat on her face, x 1230-1460, y 60-330)"),
        {"id": "strike-s020", "name": "strike-s020", "scene": "Strike", **dict(zip(("from", "duration"), in_shot("s020", 88.6190))),
         "note": "s020: on the 88.62 accent (the curtain drops); struck on 'model.'",
         "props": {"rows": ["THEIR NEXT", "BIG MODEL"], "strike": "BIG MODEL", "at": 0, "strikeAt": f(89.50) - f(88.6190),
                   "x": 1500, "y": 420, "cap": 46, "rotate": 0, "sourcePos": {"x": 1500, "y": 640}, "source": "SAFETY STANDARDS, THEY SAID",
                   "color": "#151515", "accent": AMBER}},
        scene("slam-s021-4000", "s021", "Slam", 93.37,
              {"anchor": "left", "x": 72, "rows": [{"text": "4,000+", "at": 0, "mode": "slam", "cap": 170, "baseline": 700}],
               "detail": {"at": 0, "roll": {"to": 4000, "frames": 12, "prefix": "", "decimals": 0}, "lines": ["APPS · SHIPPED THE NEXT DAY"]}},
              "counter on 'Four thousand' (93.37), with the push step"),
        scene("slam-s022-oath", "s022", "Slam", 95.24,
              {"anchor": "left", "x": 72,
               # one counter slot: each number cuts the last off on its own slam frame; the slot's slam block (box top
               # baseline - 242 px at cap 170) starts 38 px under the title's baseline (300), so it never covers it
               "rows": [{"text": "UNDER OATH", "at": 0, "mode": "fade", "cap": 60, "baseline": 300},
                        {"text": "×1", "at": f(95.9565) - f(95.24), "until": f(96.4209) - f(95.24), "mode": "slam", "cap": 170, "baseline": 580},
                        {"text": "×2", "at": f(96.4209) - f(95.24), "until": f(96.8853) - f(95.24), "mode": "slam", "cap": 170, "baseline": 580},
                        {"text": "×3", "at": f(96.8853) - f(95.24), "mode": "slam", "cap": 170, "baseline": 580}],
               "detail": {"at": f(98.01) - f(95.24), "lines": ["LEFT THE TEST"]}},
              "UNDER OATH · x3 · LEFT THE TEST: the count goes 1-2-3 on the three beats after 'three', 'left the test' on its word"),
        scene("cls-s022b-cards", "s022b", "Classifier", 99.6252,
              {"targets": [{"at": 0, "box": {"x": 300, "y": 360, "width": 900, "height": 520}, "rows": [{"at": 0, "key": "LEFT THE TEST", "value": "×3", "conf": 0.99}]}]},
              "the three cards under her palm"),
        scene("label-s023-visitor", "s023", "Callout", 101.86,
              {"at": 0, "anchor": {"x": 1500, "y": 340}, "label": {"x": 1000, "y": 620}, "title": "VISITOR", "rows": ["MODEL GUEST · NO ACCESS"]},
              "the blank visitor badge on 'Model guests'"),
        scene("slam-s024-allhands", "s024", "Slam", 103.2940,
              {"anchor": "left", "x": 72, "rows": [{"text": "ALL HANDS!", "at": 0, "mode": "fade", "cap": 120, "baseline": 400},
                                                   {"text": "ALL", "at": f(104.35) - f(103.2940), "mode": "fade", "cap": 120, "baseline": 570},
                                                   {"text": "NIGHT!", "at": f(105.09) - f(103.2940), "mode": "fade", "cap": 120, "baseline": 570, "x": 310}]},
              "chorus call, fades (rule 3, as the opening's second call)"),
        scene("cls-s025-hold", "s025", "Classifier", 108.44,
              {"targets": [{"at": 0, "box": {"x": 700, "y": 560, "width": 520, "height": 380}, "rows": [{"at": 0, "key": "HOLDING ON", "value": "TIGHT", "conf": 0.9}]}]},
              "'hold on tight' (the opening's chorus graphic again, on the laptop in her hand), into the 108.81 jolt"),
        scene("hypnogram-s026b", "s026b", "Chart", 112.4542,
              {"at": 0, "mode": "hypnogram", "title": "SLEEP · LAST NIGHT", "stages": ["AWAKE", "REM", "LIGHT", "DEEP"],
               "steps": [2, 3, 3, 2, 1, 2, 3, 2, 2, 1, 2, 3, 2, 0], "drop": "AWAKE", "x": 120, "y": 300, "w": 440},
              "'awake': his eyes open (the opening's hypnogram on the same word); on the soft carriage left of his head (at 1380 "
              "it sat on his hair and ear, his head x 860-1820)"),
        scene("slam-s027-allhands", "s027", "Slam", 116.1230,
              {"anchor": "left", "x": 72, "rows": [{"text": "ALL HANDS!", "at": 0, "mode": "fade", "cap": 120, "baseline": 400},
                                                   {"text": "ALL", "at": f(117.69) - f(116.1230), "mode": "fade", "cap": 120, "baseline": 570},
                                                   {"text": "NIGHT!", "at": f(118.02) - f(116.1230), "mode": "fade", "cap": 120, "baseline": 570, "x": 310}]},
              "second chorus call, fades"),
        scene("callout-s028b-pager", "s028b", "Callout", 121.1617,
              {"at": 0, "anchor": {"x": 960, "y": 560}, "label": {"x": 1300, "y": 280}, "title": "P0 · 10:02", "rows": ["PAGED · AGAIN"]},
              "'pager blew': the lit pager on her waist"),
        scene("slam-s030-sep20", "s030", "Slam", 134.17,
              {"anchor": "left", "x": 72, "rows": [{"text": "SEP 20", "at": 0, "mode": "slam", "cap": 170, "baseline": 700}]},
              "SEP 20 slams on 'September' (134.17), not before"),
    ]
    return D


def main() -> int:
    picture = Path(sys.argv[sys.argv.index("--picture") + 1]).resolve() if "--picture" in sys.argv else RENDER
    if not picture.exists():
        raise SystemExit(f"{picture} missing (render section2 first)")
    n = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames",
                            "-of", "csv=p=0", str(picture)], capture_output=True, text=True, check=True).stdout)
    if n != N:
        raise SystemExit(f"{picture.name}: {n} frames, not {N}")
    setup(picture)
    O = json.loads((SRC / "layers.json").read_text())
    oc = {c["id"]: c for t in O["tracks"] for c in t.get("clips", [])}
    hud0 = oc["hud-main"]["props"]
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())
    hud = {"id": "hud-main", "name": "HUD", "from": 0, "duration": N, "scene": "Hud",
           "note": "the opening's HUD run on: songOffset 1422 (song frames), chapter line hard-switches at 84.02 (look), 103.29 (chorus), 119.78 (pool)",
           "props": {**hud0, "songOffset": SF0,
                     "chapters": hud0["chapters"] + [
                         {"at": SF0, "text": "INCIDENT WEEK · CH 04 / 11 · STREET CALL"},
                         {"at": SF0 + f(84.0214), "text": "INCIDENT WEEK · CH 05 / 11 · THE HEARING"},
                         {"at": SF0 + f(103.2940), "text": "INCIDENT WEEK · CH 06 / 11 · LAST TRAIN"},
                         {"at": SF0 + f(119.7801), "text": "INCIDENT WEEK · CH 07 / 11 · DRY POOL"}],
                     "downbeats": [int(round(x * FPS)) for x in beats["downbeats"] if x < SF1 / FPS + 0.1],
                     "spectrum": spectrum()}}
    chip0 = oc["chip-p0"]["props"]
    chip = {"id": "chip-p0", "name": "chip-p0", "from": 0, "duration": N, "scene": "TicketChip",
            "note": "the opening's chip run on (INC-0902 SEV-HIGH, 13 PAGED, ALL HANDS stamp); +1 on 'pager blew' (61.01, 121.56)",
            "props": {**{k: v for k, v in chip0.items() if k != "keys"},
                      "keys": [{"at": 0, "line": "INC-0902 · SEV-HIGH", "count": 13, "stamp": "ALL HANDS"},
                               {"at": f(61.01), "count": 14}, {"at": f(121.56), "count": 15}]}}
    sung = {"x": 72, "baseline": 997, "cap": 35, "color": WHITE, "accent": AMBER}
    cover = {"cap": 45, "color": WHITE, "accent": AMBER, "accentDim": DIM}
    lyr = []
    lyr += lyric_clips("SungLine", 59.0, 79.0, ["s015a", "s015b", "s015c", "s016a", "s016b", "s016i", "s017p1", "s017a", "s017p2", "s017s", "s017b"], sung)
    lyr += lyric_clips("Coverline", 87.0, 101.5, ["s020"], {**cover, "spot": {"x": 72, "y": 180, "width": 640}})
    # s021: on the empty wall upper left (her face is upper right, her hand reaches to x ~870, the 4,000+ slam's block
    # starts at y 458): x 72-672, y 130 to ~420
    lyr += lyric_clips("Coverline", 87.0, 101.5, ["s021"], {**cover, "spot": {"x": 72, "y": 130, "width": 600}})
    lyr += lyric_clips("Subtitle", 87.0, 101.5, ["s022", "s022b"], {"baseline": 975, "cap": 35, "color": WHITE, "accent": AMBER})
    lyr += lyric_clips("Coverline", 101.5, 103.0, ["s023"], {**cover, "spot": {"x": 72, "y": 180, "width": 640}})
    lyr += lyric_clips("SungLine", 102.8, 125.7, ["s024", "s025", "s026a", "s026b", "s026c", "s027", "s028a", "s028b", "s028c", "s028d"], sung)
    lyr += lyric_clips("Coverline", 125.7, 131.3, ["s029"], {"cap": 60, "color": WHITE, "accent": AMBER, "accentDim": DIM,
                                                             "spot": {"x": 72, "y": 220, "width": 560}}, hold=1.2)
    for c in lyr:
        if c["scene"] == "Subtitle":
            for l in c["props"]["lines"]:
                l.pop("label", None)
    dev = devices()
    for c in lyr + dev:
        a, b = c["from"], c["from"] + c["duration"]
        if c["duration"] <= 0 or any(a < x < b for x in CUTS):
            raise SystemExit(f"{c['id']}: {a}-{b} crosses a cut or is empty")
    # devices that overlap go to a second track
    dev.sort(key=lambda c: c["from"])
    tracks_dev, ends = [[], []], [0, 0]
    for c in dev:
        k = 0 if c["from"] >= ends[0] else 1
        tracks_dev[k].append(c)
        ends[k] = c["from"] + c["duration"]
    layers = {"version": O.get("version", 1), "markers": [
        {"id": "m-0", "frame": 0, "label": "Post-chorus (59.23)", "kind": "section"},
        {"id": "m-1", "frame": f(78.9827), "label": "Instrumental", "kind": "section"},
        {"id": "m-2", "frame": f(88.6190), "label": "Verse 2", "kind": "section"},
        {"id": "m-3", "frame": f(103.2940), "label": "Chorus 2", "kind": "section"},
        {"id": "m-4", "frame": f(119.7801), "label": "Post-chorus 2", "kind": "section"}],
        "tracks": [
            {"id": "hud", "name": "HUD", "kind": "scene", "clips": [hud]},
            {"id": "ticket-chip", "name": "ticket chip", "kind": "scene", "clips": [chip]},
            {"id": "slam", "name": "slam", "kind": "scene", "clips": [c for c in tracks_dev[0] if c["scene"] == "Slam"] + [c for c in tracks_dev[1] if c["scene"] == "Slam"]},
            {"id": "lyrics", "name": "lyrics", "kind": "scene", "clips": lyr},
            {"id": "devices", "name": "devices", "kind": "scene", "clips": [c for c in tracks_dev[0] if c["scene"] != "Slam"]},
            {"id": "devices-b", "name": "devices b", "kind": "scene", "clips": [c for c in tracks_dev[1] if c["scene"] != "Slam"]},
            {"id": "pic-print", "name": "picture", "kind": "video", "clips": [
                {"id": "print-s015-030-v1", "name": "s015-030 picture v1 (section2.py)", "from": 0, "duration": N, "src": PIC, "trimStart": 0,
                 "muted": True, "fit": "cover", "inheritGrade": False, "note": f"AI-VIDEO excerpt section2.py render, sha256 {sha(picture)}"}]},
            {"id": "music", "name": "music", "kind": "audio", "clips": [
                {"id": "song", "from": 0, "duration": N, "src": MUSIC, "volume": 1, "trimStart": 0, "role": "music",
                 "note": "母带原样（song frames 1422-3226 = 59.25-134.4583 s，样本精确裁切），不改电平"}]},
        ]}
    # the kinds of the opening's tracks (kept as they are written there)
    kinds = {t["id"]: t.get("kind") for t in O["tracks"]}
    for t in layers["tracks"]:
        t["kind"] = kinds.get(t["id"].replace("devices-b", "devices"), t["kind"])
    (PROJ / "layers.json").write_text(json.dumps(layers, indent=1, ensure_ascii=False))
    (PROJ / "notes.md").write_text(f"""# IRIS EP01 s015–s030 · EV 版式 v1（2026-11-23）

画面：AI-VIDEO `outputs/ai-city-takeover/ep01/v4/excerpt/section2.py`（opening v3 的印刷引擎、逐镜模糊类、副歌线网/主歌点网），
本项目只叠 EV 版式层（HUD、计数卡、砸字、歌词、标注）与母带。图层由 `section2_layers.py` 生成，手改会被覆盖。

- 帧 k = 歌曲帧 1422 + k（59.25 s 起），共 {N} 帧；HUD 用 songOffset={SF0} 接开头的时间码、标尺、ticker 与频谱。
- 音乐：母带样本精确裁切 59.25–134.4583 s，原样，导出 normalizeLoudness=false。
- 图形都在镜头内，切点处退出；歌词逐词按 words.json。
""")
    print(json.dumps({"project": str(PROJ), "frames": N, "lyrics": len(lyr), "devices": len(dev),
                      "picture_sha256": sha(picture)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
