#!/usr/bin/env python3
"""QA of the rendered IRIS EP01 v4 excerpt. Run from the repository root after the render and after
`node .../snap.mjs --marks .../qa/marks.json` (the words each frame drew, from the engine itself):

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa.py

Checks (results in qa/qa.json and qa/QA.md, sheets in qa/):
1. spec: 1920x1080, 24 fps, 796 frames, H.264 + AAC, BT.709 tags.
2. sound: the render's AAC against the master's own samples for the window: offset by cross-correlation (must be
   within one audio frame of 0) and level (RMS difference, must be within 0.5 dB: no loudness change).
3. cuts: every planned cut within 0.03 s of a beat (beats.json), and the render's picture actually changes on exactly
   that frame (the frame difference peaks there and nowhere else above the cut threshold).
4. lyrics N/N: every word of words.json sung or spoken inside the window is drawn on its onset frame (or, for a word
   begun before the window, on frame 0) and stays on for 8 frames or to its end, whichever is shorter (or to the end of
   the excerpt); none is drawn more than one frame before its onset.
5. flashes: WCAG 2.3.1 general flash (relative luminance, opposing changes of 10% where the darker state is below
   0.8, counted on each cell of a 4x4 grid, any cell over 3 flashes in any one second fails) and single-frame jumps
   (a frame that differs from both neighbours while the neighbours agree), cuts excluded.
6. no Chinese on screen: no CJK character in any drawn string (source and data) and no CJK glyph in any font shipped.
7. red (v1: on her = inside her u2netp matte; v2: each red render pixel mapped back through the frame's camera, from the
   engine's own log, into its still, allowed where the still is red there): saturated red pixels per frame (grouped: a pixel counts when 4+ of its 3x3 neighbours are red, so single grain
   specks on the amber street light are not read as red objects; the raw count is kept per frame), each classed as on her (inside her matte, u2netp, grown) or on the one graphic
   accent allowed red (the P0 ALERT RAISED label of the pager readout from 58.726); anything else is reported.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, FPS, FRAMES, H, OFFSET, END, W, frame_of  # noqa: E402
from prep_media import grow, matte  # noqa: E402

TAG = "-v4r11" if "--v4r11" in sys.argv else "-v4r10c" if "--v4r10c" in sys.argv else "-v4r10b" if "--v4r10b" in sys.argv else "-v4r10" if "--v4r10" in sys.argv else "-v4r9" if "--v4r9" in sys.argv else "-v4r8" if "--v4r8" in sys.argv else "-v4r7" if "--v4r7" in sys.argv else "-v4r6" if "--v4r6" in sys.argv else "-v4r5" if "--v4r5" in sys.argv else "-v4r4" if "--v4r4" in sys.argv else "-v4r3" if "--v4r3" in sys.argv else "-v4r2" if "--v4r2" in sys.argv else "-v4r1" if "--v4r1" in sys.argv else "-v3" if "--v3" in sys.argv else "-v2" if "--v2" in sys.argv else ""
V2 = bool(TAG)                                          # the stills-first edits (v2, v3) and the v4 rounds
RENDER = EXC / (f"renders/IRIS-EP01-v4-excerpt{TAG}-036-059.mp4" if TAG in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else f"renders/IRIS-EP01-v4-excerpt{TAG}-036-051.mp4" if TAG.startswith("-v4r") else f"renders/IRIS-EP01-v4-excerpt-026-059{TAG}.mp4")
AUDIO = EXC / ("audio/master-v4r7-036-059.wav" if TAG in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else "audio/master-v4r1-036-051.wav" if TAG.startswith("-v4r") else "audio/master-026-059.wav")
if TAG.startswith("-v4r"):
    # a window of the excerpt (frames 244..596): every frame number below is a frame of the render
    from edl import V4R1_F0, V4R1_F1, V4R7_F1
    if TAG in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11"):
        V4R1_F1 = V4R7_F1
    _frame_of = frame_of
    frame_of = lambda t: _frame_of(t) - V4R1_F0  # noqa: E731
    FRAMES = V4R1_F1 - V4R1_F0
QA = EXC / ("qa/" + TAG[1:] if TAG else "qa")
EDL_JSON = EXC / f"data/edl{TAG}.json"
CJK = re.compile(r"[⺀-鿿豈-﫿＀-￯㐀-䶿]")
SW, SH = 480, 270


def probe() -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(RENDER)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def frames_small():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(RENDER), "-vf", f"scale={SW}:{SH}:flags=area", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = SW * SH * 3
    out = []
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        out.append(np.frombuffer(b, np.uint8).reshape(SH, SW, 3))
    p.wait()
    return np.stack(out)


def lin(a: np.ndarray) -> np.ndarray:
    c = a.astype(np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def check_sound() -> dict:
    wav = QA / "render-audio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(RENDER), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)], check=True)
    def read(p):
        with wave.open(str(p)) as r:
            return np.frombuffer(r.readframes(r.getnframes()), np.int16).reshape(-1, r.getnchannels()).astype(np.float32).mean(1), r.getframerate()
    a, sr = read(wav)
    b, _ = read(AUDIO)
    n = min(len(a), len(b))
    seg = slice(sr * 2, min(n, sr * 30, n - sr))
    x, y = a[seg], b[seg]
    lag_range = 4800
    best = max(range(-lag_range, lag_range + 1, 8), key=lambda L: float(np.dot(x[max(0, L):len(x) + min(0, L)], y[max(0, -L):len(y) - max(0, L)])))
    fine = max(range(best - 8, best + 9), key=lambda L: float(np.dot(x[max(0, L):len(x) + min(0, L)], y[max(0, -L):len(y) - max(0, L)])))
    rms = lambda v: float(np.sqrt(np.mean(v ** 2)))
    db = 20 * np.log10(rms(a[:n]) / rms(b[:n]))
    wav.unlink()
    return {"render_samples": len(a), "master_slice_samples": len(b), "offset_samples": fine, "offset_ms": round(fine / sr * 1000, 3),
            "rms_diff_db": round(float(db), 3), "pass": abs(fine) <= sr / FPS and abs(db) <= 0.5}


def check_cuts(fr: np.ndarray, edl: dict) -> tuple[dict, np.ndarray]:
    L = lin(fr) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    d = np.abs(np.diff(L, axis=0)).mean((1, 2))                 # d[i] = change from frame i to i+1
    shots = [{"id": s["id"], "t0": s["t0"]} for s in edl["shots"][1:]]
    if V2:
        shots += [{"id": f"{s['id']}:{key}", "t0": at} for s in edl["shots"] for key, at in s.get("stills", [])[1:]]
    shots.sort(key=lambda s: s["t0"])
    planned = [frame_of(s["t0"]) for s in shots]
    rows = []
    beats = edl["beats"]
    for c, s in zip(planned, shots):
        local = d[max(0, c - 4):c + 3]
        peak = max(0, c - 4) + int(np.argmax(local)) + 1
        t = OFFSET + (c + (V4R1_F0 if TAG.startswith("-v4r") else 0)) / FPS
        nb = min(beats, key=lambda b: abs(b - s["t0"]))
        rows.append({"shot": s["id"], "planned_t": s["t0"], "nearest_beat": nb, "cut_dt_beat": round(s["t0"] - nb, 4),
                     "frame": c, "frame_t": round(t, 4), "frame_dt_beat": round(t - nb, 4),
                     "render_change_frame": peak, "change": round(float(d[c - 1]), 4),
                     "pass": peak == c and abs(t - nb) <= 0.03 and abs(s["t0"] - nb) <= 0.03})
    thr = min(r["change"] for r in rows) * 0.8
    others = [int(i + 1) for i in np.nonzero(d > thr)[0] if int(i + 1) not in planned]
    return {"cuts": rows, "cut_threshold": round(float(thr), 4), "unplanned_changes_above_threshold": others,
            "pass": all(r["pass"] for r in rows)}, d


def transitions(v: np.ndarray, th: float = 0.1) -> list[tuple[int, int]]:
    """Reversals of at least `th` relative luminance (hysteresis), kept when the darker state is below 0.8."""
    out, hi, lo, trend, ext = [], v[0], v[0], 0, v[0]
    for i, x in enumerate(v):
        if trend == 0:
            hi, lo = max(hi, x), min(lo, x)
            if hi - lo >= th:
                trend = 1 if x == hi else -1
                if lo < 0.8:
                    out.append((i, trend))
                ext = x
        elif trend == 1:
            if x > ext:
                ext = x
            elif ext - x >= th:
                trend = -1
                if x < 0.8:
                    out.append((i, -1))
                ext = x
        else:
            if x < ext:
                ext = x
            elif x - ext >= th:
                trend = 1
                if ext < 0.8:
                    out.append((i, 1))
                ext = x
    return out


def check_flash(fr: np.ndarray, planned: list[int]) -> dict:
    L = lin(fr) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    g = 4
    Lc = L[:, :SH // g * g, :SW // g * g]
    cells = Lc.reshape(L.shape[0], g, SH // g, g, SW // g).mean((2, 4)).reshape(L.shape[0], -1)
    worst = 0
    where = None
    for c in range(cells.shape[1]):
        fl = [i for i, _ in transitions(cells[:, c])]
        for i in range(len(fl)):
            n = sum(1 for t in fl[i:] if t - fl[i] < FPS) / 2
            if n > worst:
                worst, where = n, (c, fl[i])
    D = np.abs(np.diff(L, axis=0)).mean((1, 2))
    singles = []
    for f in range(1, len(L) - 1):
        if f in planned or f + 1 in planned:
            continue
        a, b = D[f - 1], D[f]
        skip = float(np.abs(L[f + 1] - L[f - 1]).mean())
        if a > 0.02 and b > 0.02 and skip < 0.4 * min(a, b):
            singles.append({"frame": f, "t": round(OFFSET + f / FPS, 3), "d_prev": round(float(a), 4), "d_next": round(float(b), 4)})
    return {"max_flashes_per_second_any_cell": worst, "at": {"cell": where[0], "frame": where[1]} if where else None,
            "single_frame_jumps": singles, "pass": worst <= 3 and not singles}


def check_lyrics(edl: dict, marks: dict) -> dict:
    on = [set(r["words"]) for r in marks["frames"]]
    rows, ok = [], 0
    for l in edl["lines"]:
        for wi in l["in_window"]:
            w = l["words"][wi]
            if frame_of(w["end"]) <= 0 or frame_of(w["start"]) >= FRAMES:
                continue                                 # outside the rendered window
            key = f"{l['id']}:{wi}"
            f_on = max(0, frame_of(w["start"]))
            f_end = min(FRAMES, max(f_on + 1, frame_of(w["end"])))
            need = list(range(f_on, min(FRAMES, f_on + min(8, max(1, f_end - f_on)))))
            if f_end >= FRAMES:
                need = list(range(f_on, FRAMES))
            first = next((f for f in range(FRAMES) if key in on[f]), None)
            held = all(key in on[f] for f in need)
            early = first is not None and first < f_on - 1
            good = first is not None and held and not early
            ok += good
            rows.append({"line": l["id"], "word": w["text"], "start": w["start"], "onset_frame": f_on, "first_frame": first,
                         "held_frames": sum(1 for f in range(f_on, FRAMES) if key in on[f]), "pass": good})
    return {"words": len(rows), "on_time": ok, "pass": ok == len(rows), "rows": rows}


def check_chinese(edl: dict) -> dict:
    hits = []
    for p in list((EXC / "src").glob("*.js")) + [EDL_JSON, EXC / f"composition{TAG}.html"]:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if CJK.search(line):
                hits.append(f"{p.name}:{i}")
    glyphs = {}
    for f in (EXC / "fonts").glob("*.otf"):
        cmap = TTFont(f).getBestCmap()
        glyphs[f.name] = sum(1 for cp in cmap if CJK.match(chr(cp)))
    return {"cjk_in_drawn_sources": hits, "cjk_glyphs_in_fonts": glyphs,
            "pass": not hits and not any(glyphs.values())}


def red_mask(a: np.ndarray) -> np.ndarray:
    mx, mn = a.max(-1), a.min(-1)
    s = (mx - mn) / np.maximum(mx, 1e-3)
    r, g, bb = a[..., 0], a[..., 1], a[..., 2]
    speck = (r == mx) & ((g - bb) < 0.3 * (r - bb)) & (s > 0.5) & (mx > 0.3)
    h, w = speck.shape
    pad = np.pad(speck.astype(np.int16), 1)
    nb = sum(pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    return speck & (nb >= 4)


def still_reds() -> dict:
    """v2/v3: the red in each source still (prompted to be only her ear lamp and, in v2, her collar line; W1 in v3 has no
    collar line), as a grown mask in plate px, with its bounding box listed and drawn on qa/<v>/still-reds.jpg for the eye."""
    from edl import STILLS, STILLS_W1
    out, sheet = {}, []
    for p in sorted(((EXC / "media/stills-w1") if TAG in ("-v3", "-v4r1", "-v4r2", "-v4r3", "-v4r4", "-v4r5", "-v4r6", "-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else STILLS).glob("X*.png")) + \
            ([EXC / "media/stills-v4r1/p012-w1.png"] if TAG.startswith("-v4r") else []) + \
            ([EXC / "flash/design/D1-b.png"] if TAG in ("-v4r2", "-v4r3", "-v4r4") else []) + \
            ([EXC / "flash/design/INS13/INS13-a.png", EXC / "flash/design/INS14/INS14-b.png"] if TAG in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else []):
        a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
        if TAG in ("-v3", "-v4r1", "-v4r2", "-v4r3", "-v4r4", "-v4r5", "-v4r6", "-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11"):                      # full size: the lamp is a few pixels on the wide stills
            big = red_mask(a)
        else:
            lo = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((a.shape[1] // 2, a.shape[0] // 2), Image.BILINEAR), np.float32) / 255
            m = red_mask(lo)
            big = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((a.shape[1], a.shape[0]), Image.NEAREST)) > 0
        out[p.stem] = grow(big.astype(np.float32), 18) > 0.5      # her lamp and collar line with their glow
        out[str(p.relative_to(EXC))] = out[p.stem]
        ys, xs = np.nonzero(big)
        view = (a * 0.35)
        view[big] = [1, 1, 0]
        sheet.append(Image.fromarray((view * 255).astype(np.uint8)).resize((418, 235)))
        out[p.stem + ":box"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None
    s = Image.new("RGB", (418 * 4, 235 * 3))
    for i, im in enumerate(sheet):
        s.paste(im, ((i % 4) * 418, (i // 4) * 235))
    s.save(QA / "still-reds.jpg", quality=88)
    return out


def check_red(fr_full_every: int = 4) -> dict:
    """Saturated red at full size on every 4th frame: on her (matte grown 3% of the width) or on the P0 label."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(RENDER), "-vf", f"select='not(mod(n\\,{fr_full_every}))',scale=960:540",
                          "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = 960 * 540 * 3
    rows, bad_total, i = [], 0, 0
    src = still_reds() if V2 else None
    marks = json.loads((QA / "marks.json").read_text())["frames"] if V2 else None
    x0, y0 = (1300, 600) if V2 else (1380, 560)                 # lcdCard origin; the P0 ALERT RAISED label row
    p0 = (x0 // 2, (y0 + 90) // 2, (x0 + 300) // 2, (y0 + 140) // 2)
    red_map = np.zeros((540, 960), np.float32)
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        f = i * fr_full_every
        a = np.frombuffer(b, np.uint8).reshape(540, 960, 3).astype(np.float32) / 255
        mx, mn = a.max(-1), a.min(-1)
        s = (mx - mn) / np.maximum(mx, 1e-3)
        r, g, bb = a[..., 0], a[..., 1], a[..., 2]
        hue_ok = (r == mx) & ((g - bb) < 0.3 * (r - bb))           # hue within ~18 deg of red
        speck = hue_ok & (s > 0.5) & (mx > 0.3)
        # a red object, not a grain speck on warm sodium light: at least 4 red pixels in its 3x3 neighbourhood
        pad = np.pad(speck.astype(np.int16), 1)
        nb = sum(pad[1 + dy:541 + dy, 1 + dx:961 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        red = speck & (nb >= 4)
        raw_bad = int(speck.sum())
        cnt = int(red.sum())
        bad = 0
        if cnt and V2:
            # map every red render pixel back into its still through the frame's own camera (engine log): allowed
            # where the still itself is red there (her lamp and collar), or on the P0 label
            mk = marks[f]
            cx, cy, z, rot = mk["view"]
            sw, sh_ = mk.get("size") or [1672, 941]
            k_ = max(W / sw, H / sh_) * z
            ys, xs = np.nonzero(red)
            dx, dy = xs * 2 - W / 2 - mk["shake"][0], ys * 2 - H / 2 - mk["shake"][1]
            c, s_ = np.cos(-rot), np.sin(-rot)
            px, py = cx + (c * dx - s_ * dy) / k_, cy + (s_ * dx + c * dy) / k_
            sm = src.get(mk.get("src")) if mk.get("src") in src else src.get(mk["still"])
            if sm is None:                                  # a clip picture: its own red, grown, is the allowed red
                pa = np.asarray(Image.open(EXC / mk["src"]).convert("RGB"), np.float32) / 255
                sm = grow(red_mask(pa).astype(np.float32), 18) > 0.5
                src[mk["src"]] = sm
            inb = (px >= 0) & (px < sm.shape[1]) & (py >= 0) & (py < sm.shape[0])
            ok = np.zeros(len(xs), bool)
            ok[inb] = sm[py[inb].astype(int), px[inb].astype(int)]
            allow = np.zeros_like(red)
            allow[ys[ok], xs[ok]] = True
            if f >= frame_of(58.726):
                allow[p0[1]:p0[3], p0[0]:p0[2]] = True
            badm = red & ~allow
            bad = int(badm.sum())
            red_map += badm
        elif cnt:
            her = grow((matte((a * 255).astype(np.uint8)) > 0.3).astype(np.float32), 29) > 0.5
            allow = her.copy()
            if f >= frame_of(58.726):
                allow[p0[1]:p0[3], p0[0]:p0[2]] = True
            badm = red & ~allow
            bad = int(badm.sum())
            red_map += badm
        bad_total += bad
        rows.append({"frame": f, "red_px": cnt, "outside_px": bad, "red_px_incl_isolated_specks": raw_bad})
        i += 1
    p.wait()
    worst = sorted(rows, key=lambda r: -r["outside_px"])[:8]
    if red_map.max() > 0:
        Image.fromarray((np.clip(red_map / red_map.max(), 0, 1) * 255).astype(np.uint8)).save(QA / "red-outside-map.png")
    frames_bad = sum(1 for r in rows if r["outside_px"] > 12)
    boxes = {k[:-4]: v for k, v in src.items() if k.endswith(":box")} if V2 else {}
    # v3: W1 has no collar line, so each still's red must be one small spot (the ear lamp, under 90 plate px a side)
    lamp_only = {k: (b is None or (b[2] - b[0] < 90 and b[3] - b[1] < 90)) for k, b in boxes.items()} if TAG in ("-v3", "-v4r1", "-v4r2", "-v4r3", "-v4r4", "-v4r5", "-v4r6", "-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") else {}
    res_extra = {"still_red_boxes": boxes, "still_red_is_lamp_only": lamp_only,
                 "method": f"{TAG[1:]}: render red mapped back through the frame's camera into its still; allowed where the still is red "
                           f"(checked on qa/{TAG[1:]}/still-reds.jpg: her ear lamp" + (" and collar line" if TAG == "-v2" else " only") +
                           ") or on the P0 label"} if V2 else {}
    return {**res_extra, "frames_checked": len(rows), "frames_with_red": sum(1 for r in rows if r["red_px"]),
            "frames_with_red_outside_her_or_p0_over_12px": frames_bad, "worst": worst,
            "pass": frames_bad == 0 and all(lamp_only.values()) if V2 else frames_bad == 0}


def check_logos(fr: np.ndarray, edl: dict) -> dict:
    """The laptop logos of the takes (prep_media.py remove_logos log): every picture where a logo's lid was in view was
    blotted; a sheet of the render cropped round each logo every 6 frames (qa/<v>/logos.jpg) for the eye. v4r7: every
    clip shot whose prepared pictures carry a logo log (MO06-s-1, MO07-s-2); before it, the walk take of s011."""
    media = json.loads((EXC / "data/media-v4r1.json").read_text())["shots"]
    rows, crops = {}, []
    for shot in edl["shots"]:
        if shot.get("kind") != "clip" or "seq" not in shot:
            continue
        mid = shot["seq"]["dir"].split("/")[-1]
        m = media.get(mid)
        if not m or not m.get("logos") or (TAG not in ("-v4r7", "-v4r8", "-v4r9", "-v4r10", "-v4r10b", "-v4r10c", "-v4r11") and mid != "s011"):
            continue
        pics = sorted(set(m["map"]))
        for x in m["logos"]:
            r = rows.setdefault(f"{shot['id']}:{x['logo']}", {"pictures": 0, "blotted": 0, "skipped_not_lid": 0})
            r["pictures"] += 1
            r["blotted" if x["blotted"] else "skipped_not_lid"] += 1
        for k in range(0, shot["f1"] - shot["f0"], 6):
            f = shot["f0"] - edl.get("window_f0", 0) + k
            pic = pics.index(m["map"][k])
            for x in m["logos"]:
                if x["pic"] == pic and x.get("x") is not None:
                    sx, sy = int(x["x"] * SW / 1920), int(x["y"] * SH / 1080)
                    crops.append(Image.fromarray(fr[f]).crop((sx - 24, sy - 24, sx + 24, sy + 24)).resize((96, 96), Image.NEAREST))
    cols = 16
    sheet = Image.new("RGB", (96 * cols, 96 * max(1, (len(crops) + cols - 1) // cols)))
    for i, c in enumerate(crops):
        sheet.paste(c, ((i % cols) * 96, (i // cols) * 96))
    sheet.save(QA / "logos.jpg", quality=90)
    return {"per_logo": rows, "sheet": f"qa/{TAG[1:]}/logos.jpg (480x270 render crops, 2x)",
            "note": "skipped = her leg in front of the lid (skin); checked on the sheet",
            "pass": bool(rows) and all(r["blotted"] > 0 for r in rows.values())}


def contact(fr: np.ndarray, edl: dict) -> None:
    # one frame every half beat-ish (every 6 frames), 10 across
    idx = list(range(0, len(fr), 6))
    cols = 10
    rows = (len(idx) + cols - 1) // cols
    tw, th = 192, 108
    sheet = Image.new("RGB", (cols * tw, rows * th))
    for k, f in enumerate(idx):
        sheet.paste(Image.fromarray(fr[f]).resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
    sheet.save(QA / "contact-every-6-frames.jpg", quality=85)


def main() -> int:
    QA.mkdir(exist_ok=True)
    edl = json.loads(EDL_JSON.read_text())
    marks = json.loads((QA / "marks.json").read_text())
    pr = probe()
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    spec = {"width": v["width"], "height": v["height"], "fps": v["r_frame_rate"], "frames": int(v.get("nb_frames", 0)),
            "codec": v["codec_name"], "pix_fmt": v["pix_fmt"], "color": [v.get("color_space"), v.get("color_transfer"), v.get("color_primaries")],
            "audio": a and {"codec": a["codec_name"], "rate": a["sample_rate"], "channels": a["channels"], "bit_rate": a.get("bit_rate")},
            "duration": pr["format"]["duration"]}
    spec["pass"] = (v["width"], v["height"]) == (W, H) and v["r_frame_rate"] == f"{FPS}/1" and spec["frames"] == FRAMES and \
        bool(a) and a["codec_name"] == "aac"
    fr = frames_small()
    cuts, _ = check_cuts(fr, edl)
    planned = [c["frame"] for c in cuts["cuts"]]
    res = {"render": str(RENDER.relative_to(EXC.parents[4])), "spec": spec, "sound": check_sound(), "cuts": cuts,
           "lyrics": check_lyrics(edl, marks), "flash": check_flash(fr, planned), "chinese": check_chinese(edl),
           "red": check_red()}
    contact(fr, edl)
    if TAG.startswith("-v4r"):
        res["logos"] = check_logos(fr, edl)
    res["pass"] = all(res[k]["pass"] for k in ("spec", "sound", "cuts", "lyrics", "flash", "chinese", "red") + (("logos",) if TAG.startswith("-v4r") else ()))
    (QA / "qa.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print(json.dumps({k: (bool(v["pass"]) if isinstance(v, dict) and "pass" in v else v) for k, v in res.items()}, indent=1, default=str))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
