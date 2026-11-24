#!/usr/bin/env python3
"""Build the HyperFrames project of the IRIS EP01 v4 finished excerpt (song 26.0528-59.2341 s) in this folder. Run from
the repository root, after prep_media.py:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/build.py [--v2 | --v3]
  npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v4/excerpt -c composition.html \\
      -o outputs/ai-city-takeover/ep01/v4/excerpt/renders/hf-render.mp4 -f 24 --quality high --crf 16 -w 4 --browser-gpu
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/mux.py        # the master's AAC, priming trimmed
  node outputs/ai-city-takeover/ep01/v4/excerpt/snap.mjs --marks outputs/ai-city-takeover/ep01/v4/excerpt/qa/marks.json
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa.py
  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/review.py     # index.html (review page), qa/QA.md

v2 (--v2, 2026-11-18): the stills-first re-edit (edl.SHOTS_V2, src/shots2.js) -> data/edl-v2.json and
composition-v2.html (render with -c composition-v2.html, mux.py --v2, snap.mjs --comp composition-v2.html, qa.py --v2).

v4r10c-picture (--v4r10c-picture, 2026-11-20): v4r10c with the overlay layer left empty (no console, type or devices; the
picture's own feed/emit layers kept) and no audio element, one frame longer (to song frame 1421) -> data/edl-v4r10c-picture.json
and composition-v4r10c-picture.html, rendered straight to renders/ (no mux), for the Agentcut replica's picture track.

v4r11 (--v4r11 / --v4r11-picture, 2026-11-20): v4r10c with EV's measured use of softness (blur_study/REPORT.md): the
clean pictures (media/seq, the stills as prepared) with no depth of field, except the shots listed in data/dof-v4r11.json
(prep_dof.py --v11: background only, figure untouched); s012d's crop from the 4K take (prep_hr11.py, media/hr11); the
print's uniform softening, mist and bloom taken down (src/main.js GRADE_V4R11). --v4r11-picture as --v4r10c-picture.

Writes:
- data/edl.json: the shots resolved to frames (24 fps, nearest frame), the clip sequences and plate layers, the lyric
  lines with a word inside the window (timing/words.json, unchanged), the beat map's beats/downbeats and the snares,
  the s008 sticker track. Checks first that every cut is within 0.03 s of a beat (beats.json) and lands on a frame
  within half a frame of its time.
- audio/master-026-059.wav: the master's samples for the excerpt window, copied as they are (no resample, no level
  change); the master's SHA-256 is checked.
- fonts/: the author's three faces subset to the characters the project draws (DINish Condensed Black, IBM Plex Mono
  from their official releases, Nimbus Sans Bold from URW base35), with their licences and fonts.json.
- engine.js (esbuild bundle of src/main.js) and composition.html (the composition: one canvas and the audio; index.html is
  the review page written by review.py).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from fontTools import subset as ftsubset

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import END, EXC, FPS, FRAMES, H, MASTER, MASTER_SHA, OFFSET, REPO, SHOTS, SHOTS_V2, SHOTS_V4R1, SHOTS_V4R2, SHOTS_V4R5, SHOTS_V4R6, SHOTS_V4R7, STILLS, V4, V4R1_F0, V4R1_F1, V4R7_F1, W, frame_of  # noqa: E402

PICTURE = "--v4r10c-picture" in sys.argv or "--v4r11-picture" in sys.argv   # no overlay layer (picture only, no audio)
V11 = "--v4r11" in sys.argv or "--v4r11-picture" in sys.argv
VER = 16 if V11 else 15 if "--v4r10c" in sys.argv or PICTURE else 14 if "--v4r10b" in sys.argv else 13 if "--v4r10" in sys.argv else 12 if "--v4r9" in sys.argv else 11 if "--v4r8" in sys.argv else 10 if "--v4r7" in sys.argv else 9 if "--v4r6" in sys.argv else 8 if "--v4r5" in sys.argv else 7 if "--v4r4" in sys.argv else 6 if "--v4r3" in sys.argv else 5 if "--v4r2" in sys.argv else 4 if "--v4r1" in sys.argv else 3 if "--v3" in sys.argv else 2 if "--v2" in sys.argv else 1
V2 = VER >= 2                                           # the stills-first edit (v2, and v3 = v2 in wardrobe W1)
TAG = {1: "", 2: "-v2", 3: "-v3", 4: "-v4r1", 5: "-v4r2", 6: "-v4r3", 7: "-v4r4", 8: "-v4r5", 9: "-v4r6", 10: "-v4r7", 11: "-v4r8", 12: "-v4r9", 13: "-v4r10", 14: "-v4r10b", 15: "-v4r10c", 16: "-v4r11"}[VER] + ("-picture" if PICTURE else "")
WIN_F1 = V4R7_F1 if VER >= 10 else V4R1_F1
DOF = "dof9" if VER >= 12 else "dof"                  # v4r9: lighter depth of field, the story's people kept           # v4r7 runs to the end of the chorus
STILLS_DIR = "media/stills-w1" if VER >= 3 else "flash/stills"     # v3: the W1 stills with non-lamp reds pulled to orange

SONG = V4 / "song"
FACES = [("XDIN", "DINishCondensed-Black.otf"), ("XDINB", "DINishCondensed-Bold.otf"), ("XNIM", "NimbusSans-Bold.otf"),
         ("XNIMR", "NimbusSans-Regular.otf"), ("XMONO", "IBMPlexMono-Medium.otf"), ("XMONOR", "IBMPlexMono-Regular.otf"),
         ("XMONOS", "IBMPlexMono-SemiBold.otf")]
CHAPTER = {"s007": "c2", "s008": "c2", "s009": "c2", "s010": "c2", "s011": "c3", "s012": "c3", "s013": "c3", "s014": "c3"}
CJK = re.compile(r"[⺀-鿿豈-﫿＀-￯]")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check_cuts(beats: list[float]) -> list[dict]:
    out = []
    lst = SHOTS_V4R7 if VER >= 10 else SHOTS_V4R6 if VER >= 9 else SHOTS_V4R5 if VER >= 8 else SHOTS_V4R2 if VER >= 5 else SHOTS_V4R1 if VER == 4 else SHOTS_V2
    cuts = SHOTS[1:] if not V2 else [{"id": s["id"], "t0": s["t0"]} for s in lst[1:]] + \
        [{"id": f"{s['id']}:{k}", "t0": at} for s in lst for k, at in s.get("stills", [])[1:]]
    for s in sorted(cuts, key=lambda c: c["t0"]) + [{"id": "end", "t0": 59.2341 if VER >= 10 else 50.933 if VER >= 4 else END}]:
        t = s["t0"]
        nb = min(beats, key=lambda b: abs(b - t))
        f = frame_of(t)
        tf = OFFSET + f / FPS
        row = {"cut": s["id"], "t": t, "beat": nb, "dt": round(t - nb, 4), "frame": f, "frame_t": round(tf, 4),
               "frame_dt_beat": round(tf - nb, 4)}
        if abs(t - nb) > 0.03 or abs(tf - nb) > 0.03:
            raise SystemExit(f"cut {s['id']} at {t} is {t - nb:+.4f} s from the beat {nb} (frame {tf - nb:+.4f})")
        out.append(row)
    return out


def slice_audio(dst: Path, f0: int = 0, nf: int = FRAMES) -> dict:
    if sha(MASTER) != MASTER_SHA:
        raise SystemExit("master wav SHA-256 mismatch")
    with wave.open(str(MASTER)) as r:
        sr, ch, sw = r.getframerate(), r.getnchannels(), r.getsampwidth()
        a = round((OFFSET + f0 / FPS) * sr)
        n = round(nf / FPS * sr)
        r.setpos(a)
        data = r.readframes(n)
    dst.parent.mkdir(exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(sr)
        w.writeframes(data)
    return {"master": str(MASTER.relative_to(REPO)), "master_sha256": MASTER_SHA, "sample_rate": sr, "first_sample": a,
            "samples": n, "start_s": a / sr, "duration_s": n / sr, "slice_sha256": sha(dst)}


def fonts(chars: set[str]) -> list[dict]:
    src = EXC / "fonts/src"
    out = EXC / "fonts"
    for p in out.glob("*.otf"):
        p.unlink()
    unicodes = sorted({ord(c) for c in chars} | set(range(0x20, 0x7F)))
    faces = []
    for fam, fn in FACES:
        opts = ftsubset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        f = ftsubset.load_font(str(src / fn), opts)
        sub = ftsubset.Subsetter(opts)
        sub.populate(unicodes=unicodes)
        sub.subset(f)
        dst = out / fn.replace(".otf", "-subset.otf")
        ftsubset.save_font(f, str(dst), opts)
        cmap = f.getBestCmap()
        faces.append({"family": fam, "file": dst.name, "source": f"fonts/src/{fn}", "glyphs": len(f.getGlyphOrder()),
                      "missing": sorted(c for c in chars if ord(c) not in cmap and not c.isspace())})
    for lic in src.glob("*.txt"):
        shutil.copy2(lic, out / lic.name)
    (out / "fonts.json").write_text(json.dumps({"faces": faces}, indent=1))
    return faces


def ticker_items() -> list[dict]:
    """v4r5: the bottom on-call event stream. Every item is text that already exists in the board (board/shots.json),
    read here from its field so the source is exact; the text is checked to occur in that field (case-insensitive)."""
    board = json.loads((V4 / "board/shots.json").read_text())
    shot = {s["id"]: s for s in board["shots"]}
    dev = lambda sid, kind: next(d for d in shot[sid]["devices"] if d["kind"] == kind)
    items = [
        ("INCIDENT WEEK · EVERY LOOK · PAGED", "shots.json s004 devices[ticket] params.title + type", f"{shot['s004']['type']} {dev('s004', 'ticket')}"),
        ("INC-WEEK · SEV-LOW", "shots.json s004 devices[ticket] params.id / params.sev", json.dumps(dev("s004", "ticket"))),
        ("SHOW SCALE · ONLY P0 IS OPENAI'S OWN ALERT LEVEL", "shots.json s004 devices[ticket] params.scale", json.dumps(dev("s004", "ticket"), ensure_ascii=False)),
        ("SEP 20 · SEE FINALE", "shots.json s005 chrome", shot["s005"]["chrome"]),
        ("INC-0804 · SEV-MED · BILLBOARD BEHIND A TREE · PAGED", "shots.json s007 chrome", shot["s007"]["chrome"]),
        ("$6,000 / MONTH · PARTIALLY OBSCURED BY A TREE", "shots.json s007 devices[label] params.tag / params.sub", json.dumps(dev("s007", "label"))),
        ("INC-0902 · SEV-MED · BUS STOP · PAGED", "shots.json s009 chrome", shot["s009"]["chrome"]),
        ("INC-0902 · FREEWAY · PAGED", "shots.json s010 chrome", shot["s010"]["chrome"]),
        ("ALL HANDS · SEV-HIGH", "shots.json s011 chrome (SEV-MED → SEV-HIGH)", shot["s011"]["chrome"]),
        ("ON CALL · ALL NIGHT", "shots.json s011 devices[gauge] params.label / params.fill", json.dumps(dev("s011", "gauge"))),
        ("INCOMING · SEV-HIGH", "shots.json s013 devices[ui.call] params.label", json.dumps(dev("s013", "ui.call"))),
    ]
    out = []
    for text, src, field in items:
        f = field.upper()
        for part in text.split(" · "):
            if part.upper() not in f:
                raise SystemExit(f"ticker text '{part}' not found in its source {src}")
        out.append({"text": text, "source": src})
    return out


def wave_window(f0: int, f1: int, step: float = 0.045) -> dict:
    """v4r2: the master's level in 45 ms steps over the window (and 3 s before it), for the console's tiny waveform."""
    import numpy as np
    t0 = OFFSET + f0 / FPS - 3.0
    with wave.open(str(MASTER)) as r:
        sr = r.getframerate()
        r.setpos(int(t0 * sr))
        x = np.frombuffer(r.readframes(int(((f1 - f0) / FPS + 3.2) * sr)), np.int16).reshape(-1, 2).astype(np.float32).mean(1) / 32768
    m = int(step * sr)
    db = [round(float(20 * np.log10(np.sqrt((x[i * m:(i + 1) * m] ** 2).mean()) + 1e-9)), 1) for i in range(len(x) // m)]
    return {"wave_t0": t0, "wave_step": step, "wave_db": db}


def levels(shots: list[dict], images: dict) -> dict:
    """v4: per-shot levels from three references read off each source: the black of the garage/night (0.5th percentile
    of linear luminance) set to 0.006, the paper white of the flash edge / light box (99.5th percentile) to 0.80; the
    stretch is limited to 0.85-1.2 so a shot is matched, not re-lit. Stills per image, clips over 12 sampled pictures."""
    import numpy as np
    from PIL import Image
    out = {}

    def lin_lum(paths):
        vals = []
        for p in paths:
            a = np.asarray(Image.open(p).convert("RGB").resize((480, 270)), np.float32) / 255
            a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
            vals.append((a @ np.array([0.2126, 0.7152, 0.0722], np.float32)).ravel())
        v = np.concatenate(vals)
        return float(np.percentile(v, 0.5)), float(np.percentile(v, 99.5))
    for s in shots:
        if s["kind"] == "clip":
            d = EXC / s["seq"]["dir"]
            n = s["seq"]["count"]
            keys = {s["id"]: [d / f"{i:04d}.jpg" for i in range(0, n, max(1, n // 12))]}
        else:
            keys = {k: [EXC / images[k]] for k, _ in s["stills"]}
        for k, paths in keys.items():
            b, w = lin_lum(paths)
            sc = max(0.85, min(1.2, (0.80 - 0.006) / max(w - b, 1e-3)))
            out[k] = [round(b, 5), round(sc, 4), 0.006]
    return out


def main() -> int:
    beats_doc = json.loads((SONG / "beatmap/beats.json").read_text())
    hits = json.loads((SONG / "beatmap/hits.json").read_text())
    words = json.loads((SONG / "timing/words.json").read_text())
    media = json.loads((EXC / "data/media.json").read_text())
    beats = beats_doc["beats"]
    cuts = check_cuts(beats)

    lines = []
    for i, l in enumerate(words["lines"]):
        ws = [w for w in l["words"] if w["end"] > OFFSET and w["start"] < END]
        if ws:
            lines.append({"id": i, "en": l["en"], "mode": l["mode"], "section": l["section"],
                          "words": [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in l["words"]],
                          "in_window": [l["words"].index(w) for w in ws]})
    shots, images = [], {}
    if V2:
        for s in SHOTS_V2:
            shots.append({"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": frame_of(s["t0"]), "f1": frame_of(s["t1"]),
                          "kind": "still", "chapter": CHAPTER[s["id"]], "stills": s["stills"]})
            for key, _ in s["stills"]:
                images[key] = f"{STILLS_DIR}/{key}.png"
        images["X11a-w1-rows" if VER == 3 else "X11a-rows"] = "media/plates/X11a-w1-rows.png" if VER == 3 else "media/plates/X11a-rows.png"
    if VER >= 4:
        shots, images = [], {}
        m4 = json.loads((EXC / "data/media-v4r1.json").read_text())["shots"]
        plate_dir = EXC / "media/stills-v4r1"
        plate_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(V4 / "board/plates/p012-w1.png", plate_dir / "p012-w1.png")
        for s in (SHOTS_V4R7 if VER >= 10 else SHOTS_V4R6 if VER >= 9 else SHOTS_V4R5 if VER >= 8 else SHOTS_V4R2 if VER >= 5 else SHOTS_V4R1):
            f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
            row = {"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": f0, "f1": f1, "chapter": CHAPTER.get(s["id"][:4], "c3")}
            if s.get("seq_from"):
                row.update(kind="clip", seq={"dir": f"media/seq/{s['seq_from']}", "count": f1 - f0, "fixed": s["fixed_pic"]}, punch=s["punch"])
            elif s.get("clip"):
                mid = s.get("media_id", s["id"])
                if m4[mid]["frames"] < f1 - f0 or (VER == 4 and m4[mid]["frames"] != f1 - f0):
                    raise SystemExit(f"{s['id']}: {m4[mid]['frames']} prepared pictures for {f1 - f0} frames (rerun prep_media.py --v4r1)")
                row.update(kind="clip", seq={"dir": f"media/seq/{mid}", "count": f1 - f0})
            else:
                row.update(kind="still", stills=s["stills"])
                for key, _ in s["stills"]:
                    images[key] = (f"{STILLS_DIR}/{key}.png" if key.startswith("X") else "flash/design/D1-b.png" if key == "D1-b"
                                   else f"flash/design/{key.split('-')[0]}/{key}.png" if key.startswith("INS")
                                   else "media/stills-v4r1/p012-w1.png")
                if s.get("placeholder"):
                    row["placeholder"] = True
            if s.get("freeze"):
                row["freeze_f"], row["freeze"], row["punch"] = frame_of(s["freeze"]), s["freeze"], s.get("punch")
            shots.append(row)
    for s in ([] if V2 else SHOTS):
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        row = {"id": s["id"], "t0": s["t0"], "t1": s["t1"], "f0": f0, "f1": f1, "kind": s["kind"], "chapter": CHAPTER[s["id"]]}
        if s["kind"] == "clip":
            m = media["shots"][s["id"]]
            if m["frames"] != f1 - f0:
                raise SystemExit(f"{s['id']}: {m['frames']} prepared pictures for {f1 - f0} frames (rerun prep_media.py)")
            row["seq"] = {"dir": f"media/seq/{s['id']}", "count": m["frames"]}
        else:
            pid = s["plate"]
            images[f"{pid}-bg"] = f"media/plates/{pid}-bg.jpg"
            images[f"{pid}-fg"] = f"media/plates/{pid}-fg.png"
            row["plate"] = pid
        shots.append(row)
    if VER >= 16:
        # v4r11: the clean pictures; depth of field (background only) on the shots prep_dof.py --v11 made it for
        dof11 = json.loads((EXC / "data/dof-v4r11.json").read_text())["seq"]
        for row in shots:
            if row.get("seq") and row["id"] in dof11 and row["seq"]["dir"] == f"media/seq/{row['id']}":
                row["seq"]["dir"] = f"media/dof11/seq/{row['id']}"
    elif VER >= 11:
        # v4r8: the same pictures with depth of field (prep_dof.py)
        for row in shots:
            if row.get("seq"):
                row["seq"]["dir"] = row["seq"]["dir"].replace("media/seq/", f"media/{DOF}/seq/")
        images = {k: f"media/{DOF}/stills/{k}.png" for k in images}
    if not V2:
        images["p011-rows"] = "media/plates/p011-rows.png"
    lo, hi = OFFSET - 4, END + 4
    edl = {"version": VER, "fps": FPS, "W": W, "H": H, "offset": OFFSET, "end": END, "frames": FRAMES, "shots": shots, "images": images,
           "lines": lines, "beats": [b for b in beats if lo <= b <= hi],
           "downbeats": beats_doc["downbeats"], "snare": [x for x in hits["snare"] if lo <= x <= hi],
           "kick": [x for x in hits["kick"] if lo <= x <= hi],
           "tracks": {} if V2 else {k: v["track"] for k, v in media["shots"].items() if v.get("track")}, "cuts": cuts}
    if V2:
        edl["stills_sha256"] = {k: sha(EXC / v) for k, v in images.items()}
    if VER >= 4:
        edl["window_f0"], edl["frames"] = V4R1_F0, WIN_F1 - V4R1_F0
        edl["levels"] = levels(shots, images)
    if VER >= 16:
        # v4r11: s012d's picture from the 4K take (prep_hr11.py), set after the levels so they stay those of s012b's
        # pictures as before; the engine scales the view by the picture's own width
        hr = json.loads((EXC / "data/hr-v4r11.json").read_text())
        for row in shots:
            if row["id"] in hr:
                row["seq"] = {"dir": str(Path(hr[row["id"]]["file"]).parent), "count": row["seq"]["count"], "fixed": 0}
    if VER >= 5:
        edl.update(wave_window(V4R1_F0, WIN_F1))
    if VER >= 8:
        edl["ticker"] = ticker_items()
    if PICTURE:
        # one frame more than v4r10c (song frame 1421, the last of the Agentcut timeline): s014c held
        edl["picture_only"], edl["frames"] = True, WIN_F1 + 1 - V4R1_F0
    text = json.dumps(edl, ensure_ascii=False)
    if CJK.search(text):
        raise SystemExit("Chinese in edl.json")
    (EXC / f"data/edl{TAG}.json").write_text(json.dumps(edl, ensure_ascii=False, indent=1))
    audio_name = "audio/master-v4r7-036-059.wav" if VER >= 10 else "audio/master-v4r1-036-051.wav" if VER >= 4 else "audio/master-026-059.wav"
    audio = slice_audio(EXC / audio_name, V4R1_F0, WIN_F1 - V4R1_F0) if VER >= 4 else slice_audio(EXC / audio_name)

    # glyphs: everything the source and the data can draw
    chars = set()
    for p in (EXC / "src").glob("*.js"):
        js = p.read_text(encoding="utf-8")
        for m in re.finditer(r"'([^'\\]*(?:\\.[^'\\]*)*)'|\"([^\"\\]*(?:\\.[^\"\\]*)*)\"|`([^`]*)`", js):
            chars |= set(next(g for g in m.groups() if g is not None))
    for l in lines:
        chars |= set(l["en"]) | set(l["en"].upper())
    chars = {c for c in chars if c.isprintable()}
    if any(CJK.search(c) for c in chars):
        raise SystemExit("Chinese characters in the drawn strings: " + "".join(sorted(c for c in chars if CJK.search(c))))
    faces = fonts(chars)

    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(EXC / "src/main.js"), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={EXC / 'engine.js'}", "--log-level=warning"], check=True)
    dur = edl["frames"] / FPS if PICTURE else (WIN_F1 - V4R1_F0) / FPS if VER >= 4 else FRAMES / FPS
    win = f' data-ex-offset="{V4R1_F0 / FPS:.9f}"' if VER >= 4 else ""
    audio_el = "" if PICTURE else (f'  <audio id="music" src="{audio_name}" data-start="0" data-duration="{dur:.6f}" data-track-index="1" '
                                   'data-volume="1" data-timeline-role="music"></audio>\n')
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 v4 excerpt 026-059{TAG.replace('-', ' ')}</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-start="0" data-duration="{dur:.6f}"{f' data-ex-edl="data/edl{TAG}.json"' if V2 else ''}{win} data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{dur:.6f}" data-track-index="0"></canvas>
{audio_el}</div>
<script src="engine.js"></script>
</body>
</html>
"""
    (EXC / f"composition{TAG}.html").write_text(html, encoding="utf-8")
    print(json.dumps({"frames": FRAMES, "duration": dur, "cuts": cuts, "audio": audio,
                      "fonts": [{k: f[k] for k in ("family", "file", "glyphs", "missing")} for f in faces],
                      "lines": [l["id"] for l in lines]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
