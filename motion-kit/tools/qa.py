#!/usr/bin/env python3
"""Per-render QA for a motion-kit HyperFrames composition.

Checks a script can run (they beat judgement): spec (ffprobe), beat sync of every board event
(expected frame from the same beat clock the engine uses vs. the frame where the picture
actually changes inside the event's region), WCAG 2.3.1 general-flash count, single-frame pops,
strobe cells, outlier frames, motion per bar. Sheets a person (and a reviewer) looks at:
eighth-note grid, shot first/mid/last, key stills, 390-px phone legibility, safe area, 100% crops.

Usage:
  uv run python motion-kit/tools/qa.py --video R.mp4 --comp COMP_DIR --out QA_DIR
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SAFE = (120, 96, 1800, 980)            # key text box at 1920x1080
MARGIN = (72, 56, 96, 84)              # left, top, right, bottom


# ---------------- clock (mirror of motion-kit/src/clock.js) ----------------
class Clock:
    def __init__(self, beats: dict, music: dict, fps: int):
        self.beats = beats["beats"]
        self.down = beats["downbeats"]
        self.offset = music.get("song_offset", 0.0)
        self.bar0 = music.get("window_bar0", 0)
        self.fps = fps

    def at(self, bar, beat=0, sub=0.0):
        d0 = self.down[self.bar0 + bar]
        bi = bisect.bisect_right(self.beats, d0 + 1e-4) - 1
        idx = bi + beat
        b = self.beats
        if idx + 1 < len(b):
            s = b[idx] + sub * (b[idx + 1] - b[idx])
        else:
            s = b[-1] + (idx - (len(b) - 1) + sub) * (b[-1] - b[-2])
        return s - self.offset

    def when(self, e: dict) -> float:
        """Comp time of an event: absolute seconds ("t") or a [bar, beat, sub] grid position ("at")."""
        return e["t"] if "t" in e else self.at(*e["at"])

    def frame(self, t):
        return math.ceil(t * self.fps - 1e-6)

    def label(self, t):
        s = t + self.offset
        i = bisect.bisect_right(self.down, s) - 1
        bar = i - self.bar0
        j = bisect.bisect_right(self.beats, s) - 1
        d_idx = bisect.bisect_right(self.beats, self.down[i] + 1e-4) - 1
        beat = j - d_idx
        nxt = self.beats[j + 1] if j + 1 < len(self.beats) else self.beats[j] + 0.5
        frac = (s - self.beats[j]) / (nxt - self.beats[j])
        return f"{bar + 1}.{beat + 1}" + ("+" if frac > 0.4 else "")


# ---------------- video io ----------------
def probe(video: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,pix_fmt,color_space,"
                          "color_transfer,color_primaries,color_range,sample_rate,channels,bit_rate:format=duration,bit_rate",
                          "-of", "json", str(video)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def read_small(video: Path, w: int, h: int) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"scale={w}:{h}:flags=area,format=rgb24",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def grab(video: Path, frames: list[int], out_dir: Path, prefix: str) -> dict[int, Path]:
    frames = sorted(set(frames))
    out_dir.mkdir(parents=True, exist_ok=True)
    expr = "+".join(f"eq(n\\,{f})" for f in frames)
    pat = out_dir / f"{prefix}-%04d.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"select='{expr}'", "-vsync", "0",
                    str(pat)], check=True)
    got = sorted(out_dir.glob(f"{prefix}-*.png"))
    res = {}
    for f, p in zip(frames, got):
        q = out_dir / f"{prefix}-f{f:04d}.png"
        p.rename(q)
        res[f] = q
    return res


def srgb_to_lin(x: np.ndarray) -> np.ndarray:
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


# ---------------- checks ----------------
def flash_check(rgb54: np.ndarray, fps: int) -> dict:
    lin = srgb_to_lin(rgb54.astype(np.float32))
    L = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    trans = []                                   # (frame, sign)
    for i in range(1, len(L)):
        a, b = L[i - 1], L[i]
        dark = np.minimum(a, b) < 0.8
        up = ((b - a) >= 0.1) & dark
        down = ((a - b) >= 0.1) & dark
        if up.mean() >= 0.25:
            trans.append((i, 1))
        elif down.mean() >= 0.25:
            trans.append((i, -1))
    flashes = []                                 # a flash = a pair of opposing transitions
    k = 0
    while k + 1 < len(trans):
        if trans[k][1] != trans[k + 1][1]:
            flashes.append(trans[k + 1][0])
            k += 2
        else:
            k += 1
    worst = 0
    for i in range(len(L)):
        worst = max(worst, sum(1 for f in flashes if i <= f < i + fps))
    mean = L.mean(axis=(1, 2))
    pops = [i for i in range(1, len(mean) - 1)
            if (mean[i] - mean[i - 1]) * (mean[i] - mean[i + 1]) > 0
            and min(abs(mean[i] - mean[i - 1]), abs(mean[i] - mean[i + 1])) > 0.03]
    return {"transitions": trans, "flashes": flashes, "max_flashes_per_s": worst,
            "pass": worst <= 3, "single_frame_pops": pops}


def strobe_cells(gray108: np.ndarray) -> list[dict]:
    n = gray108.shape[0]
    cells = gray108.reshape(n, 9, 12, 16, 12).mean(axis=(2, 4))    # n x 9 x 16
    d = np.diff(cells, axis=0)
    hits = []
    for r in range(9):
        for c in range(16):
            seq = d[:, r, c]
            run = 0
            for i in range(1, len(seq)):
                if abs(seq[i]) > 8 and abs(seq[i - 1]) > 8 and np.sign(seq[i]) != np.sign(seq[i - 1]):
                    run += 1
                    if run == 3:                   # 4 alternating changes
                        hits.append({"cell": [r, c], "frame": int(i - 2)})
                else:
                    run = 0
    return hits


def outliers(gray: np.ndarray) -> list[int]:
    g = gray.astype(np.float32)
    res = []
    for i in range(1, len(g) - 1):
        a = np.abs(g[i] - g[i - 1]).mean()
        b = np.abs(g[i] - g[i + 1]).mean()
        c = np.abs(g[i + 1] - g[i - 1]).mean()
        if a > 6 and b > 6 and min(a, b) > 3 * max(c, 0.5):
            res.append(i)
    return res


def event_sync(gray: np.ndarray, clock: Clock, events: dict, scale: float) -> list[dict]:
    g = gray.astype(np.float32)
    diff = np.abs(np.diff(g, axis=0))                     # diff[i] = change into frame i+1
    cut_frames = {clock.frame(clock.when(e)) for k, e in events.items() if k.startswith("cut_")}
    rows = []
    for eid, e in events.items():
        t = clock.when(e)
        f = clock.frame(t)
        roi = e.get("roi")
        if roi:
            x, y, w, h = [int(round(v * scale)) for v in roi]
            series = diff[:, y:y + h, x:x + w].mean(axis=(1, 2))
        else:
            series = diff.mean(axis=(1, 2))
        if not eid.startswith("cut_"):
            # a graphic cue is judged on its own change: drop the picture cuts nearby and the steady
            # change a moving camera makes before the cue (median of the preceding frames)
            series = series.copy()
            for c in cut_frames:
                if 0 <= c - 1 < len(series) and c != f:
                    series[c - 1] = 0.0
            pre = series[max(0, f - 15):max(0, f - 5)]
            if len(pre):
                series = np.maximum(0.0, series - float(np.median(pre)))
        lo, hi = max(0, f - 5), min(len(series), f + 4)
        window = series[lo:hi]
        det = None
        if len(window):
            peak = float(window.max())
            onset = next(i for i, v in enumerate(window) if v >= 0.35 * peak)   # the change begins here
            det = lo + onset + 1
        rows.append({"id": eid, "what": e.get("what", ""), "key": e.get("key", ""), "t": round(t, 4),
                     "expected_frame": f, "detected_frame": det,
                     "offset_frames": None if det is None else det - f,
                     "strength": round(float(window.max()), 2) if len(window) else 0.0,
                     "pass": det is not None and abs(det - f) <= 1})
    return rows


# ---------------- sheets ----------------
def font(size: int):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def tile(items: list[tuple[Path, str]], cols: int, width: int, out: Path, pad: int = 6):
    if not items:
        return
    ims = [Image.open(p).convert("RGB") for p, _ in items]
    h = int(ims[0].height * width / ims[0].width)
    rows = math.ceil(len(ims) / cols)
    lab = 26
    sheet = Image.new("RGB", (cols * (width + pad) + pad, rows * (h + lab + pad) + pad), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    f = font(16)
    for i, (im, (_, text)) in enumerate(zip(ims, items)):
        r, c = divmod(i, cols)
        x, y = pad + c * (width + pad), pad + r * (h + lab + pad)
        sheet.paste(im.resize((width, h), Image.LANCZOS), (x, y + lab))
        d.text((x + 2, y + 3), text, fill=(20, 20, 20), font=f)
    sheet.save(out, quality=92)


def safe_overlay(src: Path, out: Path):
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    W, H = im.size
    d.rectangle([MARGIN[0], MARGIN[1], W - MARGIN[2], H - MARGIN[3]], outline=(0, 255, 120), width=2)
    d.rectangle(list(SAFE), outline=(255, 210, 0), width=2)
    im.save(out, quality=90)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path, required=True)
    ap.add_argument("--comp", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--dur", type=float, default=10.0, help="composition duration (s)")
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    data = args.comp / "data"
    beats = json.loads((data / "beats.json").read_text())
    music = json.loads((data / "music.json").read_text())
    events = json.loads((data / "events.json").read_text())["events"]
    clock = Clock(beats, music, args.fps)

    meta = probe(args.video)
    v = next(s for s in meta["streams"] if s["codec_type"] == "video")
    vdur = int(v.get("nb_frames", 0)) / args.fps
    a = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
    n_frames = int(v.get("nb_frames", 0))
    spec = {"size": [v["width"], v["height"]], "fps": v["r_frame_rate"], "frames": n_frames, "pix_fmt": v.get("pix_fmt"),
            "color": [v.get("color_space"), v.get("color_transfer"), v.get("color_primaries"), v.get("color_range")],
            "video_kbps": round(int(meta["format"].get("bit_rate", 0)) / 1000),
            "audio": None if a is None else {"codec": a["codec_name"], "rate": a.get("sample_rate"), "ch": a.get("channels")},
            "duration": float(meta["format"]["duration"])}

    rgb = read_small(args.video, 192, 108)
    gray = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(np.float32)
    rgb54 = rgb.reshape(rgb.shape[0], 54, 2, 96, 2, 3).mean(axis=(2, 4))
    flash = flash_check(rgb54, args.fps)
    strobes = strobe_cells(gray)
    outl = outliers(gray)
    sync = event_sync(gray, clock, events, 192 / 1920)

    # motion per bar
    motion = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    per_bar = []
    for bar in range(0, len(clock.down)):
        try:
            t0, t1 = clock.at(bar), clock.at(bar + 1)
        except IndexError:
            break
        f0, f1 = max(0, clock.frame(t0)), min(len(motion), clock.frame(t1))
        if f0 >= len(motion):
            break
        per_bar.append({"bar": bar + 1, "t0": round(t0, 3), "motion": round(float(motion[f0:f1].mean()), 3)})

    # sheets: eighth-note grid
    dur = spec["duration"]
    eighths = []
    for b in range(0, len(clock.down)):
        for be in range(4):
            for sub in (0.0, 0.5):
                try:
                    t = clock.at(b, be, sub)
                except IndexError:
                    continue
                if 0 <= t < dur - 1e-3:
                    eighths.append(t)
    eighth_frames = sorted({min(n_frames - 1, clock.frame(t)) for t in eighths})
    cut_frames = sorted({clock.frame(clock.when(e)) for k, e in events.items() if k.startswith("cut_")})
    bounds = [0, *cut_frames, n_frames]
    shot_frames = []
    for s0, s1 in zip(bounds[:-1], bounds[1:]):
        shot_frames += [s0, (s0 + s1) // 2, s1 - 1]
    key_frames = sorted({min(n_frames - 1, clock.frame(clock.when(e) + 0.3)) for e in events.values()})
    frames_dir = out / "frames"
    for old in frames_dir.glob("*.png") if frames_dir.exists() else []:
        old.unlink()
    got = grab(args.video, eighth_frames + shot_frames + key_frames, frames_dir, "f")
    lab = lambda f: f"{clock.label(f / args.fps)}  t={f / args.fps:.3f}  f={f}"
    tile([(got[f], lab(f)) for f in eighth_frames], 8, 300, out / "sheet-eighths.jpg")
    tile([(got[f], lab(f)) for f in shot_frames], 3, 520, out / "sheet-shots.jpg")
    tile([(got[f], lab(f)) for f in key_frames], 2, 390, out / "sheet-legibility-390.jpg")
    for f in key_frames:
        safe_overlay(got[f], out / f"safe-f{f:04d}.jpg")
    tile([(out / f"safe-f{f:04d}.jpg", lab(f)) for f in key_frames], 3, 600, out / "sheet-safe-area.jpg")
    crops = []
    for eid, e in events.items():
        if e.get("roi"):
            f = min(n_frames - 1, clock.frame(clock.when(e) + 0.3))
            x, y, w, h = e["roi"]
            c = Image.open(got[f]).crop((x, y, x + w, y + h))
            cp = out / f"crop-{eid}.png"
            c.save(cp)
            crops.append((cp, f"{eid} @ {lab(f)}"))
    tile(crops, 2, 760, out / "sheet-crops-100.jpg")
    for f in got.values():
        f.unlink()
    for f in out.glob("safe-f*.jpg"):
        f.unlink()

    spec["video_duration"] = vdur
    report = {"video": str(args.video), "spec": spec, "sync": sync, "flash": flash, "strobe_cells": strobes,
              "outlier_frames": outl, "motion_per_bar": per_bar,
              "verdicts": {"spec": spec["size"] == [1920, 1080] and spec["fps"] == f"{args.fps}/1" and n_frames == round(args.dur * args.fps),
                           "sync": all(r["pass"] for r in sync), "flash": flash["pass"],
                           "frames_match_comp": n_frames == round(args.dur * args.fps),
                           "pops": len(flash["single_frame_pops"]) == 0, "strobe": len(strobes) == 0, "outliers": len(outl) == 0}}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    lines = [f"# QA · {args.video.name}", "", f"- spec: {spec}", f"- verdicts: {report['verdicts']}", "",
             "| event | what | key | t | expected | detected | Δframes | pass |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in sync:
        lines.append(f"| {r['id']} | {r['what']} | {r['key']} | {r['t']} | {r['expected_frame']} | {r['detected_frame']} | {r['offset_frames']} | {'PASS' if r['pass'] else 'FAIL'} |")
    lines += ["", f"- flash: max {flash['max_flashes_per_s']}/s (limit 3), transitions {len(flash['transitions'])}, pops {flash['single_frame_pops']}",
              f"- strobe cells: {strobes[:10]}{' ...' if len(strobes) > 10 else ''}", f"- outlier frames: {outl}",
              f"- motion per bar: {per_bar}"]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all(report["verdicts"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
