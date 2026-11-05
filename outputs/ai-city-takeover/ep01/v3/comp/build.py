#!/usr/bin/env python3
"""Build the IRIS EP01 v3 full-length animatic (a2) as a HyperFrames project in this folder (run from the repository root):

  uv run python outputs/ai-city-takeover/ep01/v3/comp/build.py [--samples 0:12,44:60,205:226]

Spec: ../animatic-spec.md (a2 修订). Everything is driven by ../shots-map.json (board v2-a2, 84 units: times, stills,
camera moves, graphic components, viewpoint, on-screen text, optional target(s) and cue time, and the top-level
editorial `chrome`); src/main.js draws every unit with generic per-family code, never one function per unit. Generated
video replaces the stills later at the same times.
- data: the T4 beat map and hits, the CTC word timing and the music map (copied unchanged); units.json (the shots map
  resolved to frames, plate keys, the parsed camera move, the unit cue, the CTC onset of every on-screen token, the
  CTC words each lyric unit shows (unit_lyric), the wall's stills and the chrome with its switches on frames; it
  carries no Chinese field: graphic_note, lyric and objective stay out of the engine); events.json (every cut, plate
  switch and big-change cue, read by qa.py); plates.json (plate, derived plate or placeholder, SHA-256, whether its
  edges are light); assets.json (bitmaps for the 2D layers)
- audio: the master song-v3/IRIS-01-T4.wav, copied byte for byte (no loudness change)
- plates: the stills named in the shots map; a still missing at build time becomes a dark placeholder that names its
  units (listed in plates.json and printed), so the film always plays end to end. A unit with light_flicker_on also
  gets its first still with her lights off (<key>--off.png, lights_off(): round the collar line and the ear light in
  anchors.js the red is pressed to the cloth's own neutral grey, the light itself an unlit darker strip), shown until
  the light comes on and on the flicker's dark frames
- fonts: motion-kit/tools/fonts.py (the v2 faces), subset to the glyphs in src, motion-kit, the lyrics and units.json,
  plus a local Nimbus Sans Narrow Bold subset (MK Narrow Bold: the tall narrow face of the chant and the long-note
  key words; URW base35, same licence as MK Grotesk Bold)
- --samples a:b,...: one extra composition per window (sample-AAAA-BBBB.html, same engine, time offset on the root) for
  quick checks before the full render
Cue rule (spec 映射字段): a unit's cue is its cue_s; else the first hit (hits.json) inside the unit; else the first CTC
word onset inside it; else the first beat after the cut; else the cut itself. A token of graphic_text that is voiced
inside the unit (CTC, same word, a month/number word or a spelled-out acronym) appears on its onset; an unvoiced token
appears with the token before it, the first one on the unit cue.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from fontTools import subset as ftsubset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

COMP = Path(__file__).resolve().parent
V3 = COMP.parent
EP01 = V3.parent
SERIES = EP01.parent                                   # outputs/ai-city-takeover: shots-map paths are relative to it
REPO = COMP.parents[4]
KIT = REPO / "motion-kit"
SONG = EP01 / "v2/song-v3"
W, H, FPS = 1920, 1080, 30
BOARD = "v2-a2"
GROUND = "GROUND"                                      # flat blue-black plate under the full-screen graphic units
NO_RED = (36, 40)                                      # spec: 红队测试室（U036–U040）不用红色
# components whose cue changes most of the frame at once (the feed opening, a punch, a flap clock turning, an inverted
# frame, the white panel's word, the spotlight dropping out): their cue goes into events.json for qa.py
BIG_CUE = ("osd_power_on", "pulse_on_beat", "flipclock_", "invert_flash_", "invert_white_panel_words", "spotlight_flicker")
# components that turn the whole ground white (the chrome and the type go dark on them)
LIGHT_GROUND = ("invert_white_panel_words",)
# the monitor wall (U073, a2): nine stills of her with her mouth closed, looking into the lens (the unit is the
# unsung stare after the final chorus, board-table 073), in window order (rows of three)
WALL = ["P-gaze-b", "P-door-latch-a", "P-headturn-b", "P-speak-aisle-b", "P-spotlight-low-a", "P-catwalk-b",
        "P-behind-glass-a", "P-hairflip-a", "P-door-face-a"]
LIGHT_EDGE = 0.6                                       # mean luminance of a plate's edge bands above which it is light
NARROW = ("MK Narrow Bold", "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf")
NARROW_LICENSE = "AGPL-3.0 with font exception (URW base35, (URW)++ 2013-2015; Debian fonts-urw-base35)"
CJK = re.compile(r"[⺀-鿿豈-﫿＀-￯]")


def q(t: float) -> int:
    """motion-kit cut contract: a time shows on the first frame at or after it."""
    return math.ceil(t * FPS - 1e-6)


def qt(t: float) -> float:
    return q(t) / FPS


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def placeholder(key: str, units: list[str], out: Path) -> None:
    """A dark plate that says what is missing (English only: no Chinese on screen)."""
    im = Image.new("RGB", (1672, 941), (11, 15, 20))
    d = ImageDraw.Draw(im)
    for y in range(0, 941, 4):                                        # faint scan texture so the camera move reads
        d.line([(0, y), (1672, y)], fill=(14, 19, 25))
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 54)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 30)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.rectangle([60, 60, 1612, 881], outline=(70, 80, 92), width=2)
    d.text((110, 360), "PLACEHOLDER " + " ".join(units), fill=(150, 160, 172), font=f1)
    d.text((110, 450), key, fill=(110, 120, 132), font=f2)
    im.save(out)


def edge_luma(path: Path) -> dict:
    """Mean luminance (0..1) of a still's top and bottom bands (the chrome rows) and lower-left quarter (the lyric):
    the chrome and the type turn dark on a light ground (spec a2: 暗底浅字、亮底深字)."""
    with Image.open(path) as im:
        a = np.asarray(im.convert("L").resize((192, 108), Image.BILINEAR), np.float32) / 255
    lum = {"top": float(a[:12].mean()), "bottom": float(a[-12:].mean()), "lower_left": float(a[60:100, :80].mean())}
    return {k: round(v, 3) for k, v in lum.items()}


def blur2(a: np.ndarray, sigma: float) -> np.ndarray:
    """Separable Gaussian blur of a 2D or 3D (H, W, C) float array (edges padded by reflection)."""
    r = max(1, int(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    pad = [(r, r), (r, r)] + [(0, 0)] * (a.ndim - 2)
    p = np.pad(a, pad, mode="reflect")
    p = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 0, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 1, p)


def grow(m: np.ndarray, px: int) -> np.ndarray:
    """A boolean mask grown by px pixels (square max filter)."""
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * px + 1))) > 0


def lights_off(src: Path, dst: Path, a: dict, band: int = 40, disc: int = 30, tol: float = 1.5) -> dict:
    """Her lights switched off on a still (a2 修正 U002: before the cue the red is a fully neutral grey, not a dim
    orange line). Red light adds mostly to the red channel, so inside a band round the collar line (anchors `collar`)
    and a disc round the ear light (`led`), feathered over 12 px, every pixel gets at most the red that its own green and
    blue predict (a linear fit on the unlit pixels round the zones): the cloth keeps its shading and the spill turns the
    grey of the cloth. Where the light itself was (its hot core) the pixel takes the cool grey of the cloth, a shade
    darker (an unlit strip, not a pale line), and a white-hot core at the ear light is filled from the dark device round
    it. Everything outside the zones is left as it is (2026-11-04: the a2 first pass refilled only the red pixels and
    drew a strip and a lens back, which left the shoulder spill on P-dark-hall-b and drew a lens on its collar).
    Returns the lit pixel count per light (none -> nothing to switch off) and the fit."""
    im = np.asarray(Image.open(src).convert("RGB"), np.float32)
    h, w = im.shape[:2]
    red = im[..., 0] - np.maximum(im[..., 1], im[..., 2])
    yy, xx = np.mgrid[0:h, 0:w]
    dist, radius = {}, {"collar": band, "led": disc}
    if a.get("collar"):
        (x0, y0), (x1, y1) = a["collar"]
        dx, dy = x1 - x0, y1 - y0
        s = np.clip(((xx - x0) * dx + (yy - y0) * dy) / (dx * dx + dy * dy), 0, 1)
        dist["collar"] = np.hypot(xx - (x0 + s * dx), yy - (y0 + s * dy))
    if a.get("led"):
        dist["led"] = np.hypot(xx - a["led"][0], yy - a["led"][1])
    if not dist:
        return {}
    wgt = np.max([np.clip((radius[k] + 12 - d) / 12, 0, 1) for k, d in dist.items()], axis=0)
    reach = wgt > 0
    lit = reach & (red > 2)
    count = {k: int(((d <= radius[k]) & lit).sum()) for k, d in dist.items()}
    if not lit.any():
        return count
    ring = grow(reach, 30) & ~grow(reach, 3) & (red <= 0)
    X = lambda m: np.c_[im[m][:, 1], im[m][:, 2], np.ones(int(m.sum()))]
    coef, *_ = np.linalg.lstsq(X(ring), im[ring][:, 0], rcond=None)
    out = im.copy()
    r = im[reach, 0]
    out[reach, 0] = r - wgt[reach] * np.maximum(0, r - np.clip(X(reach) @ coef, 0, 255) - tol)
    lum = lambda c: c @ np.array([0.299, 0.587, 0.114], np.float32)
    hot = reach & (red > 30)
    if hot.any():
        rg = im[ring]
        tone = np.median(rg[lum(rg) > 20] / lum(rg[lum(rg) > 20])[:, None], axis=0)
        out[hot] = tone * np.minimum(lum(out[hot]), np.median(lum(rg)))[:, None] * 0.8
    if "led" in dist:
        core = (dist["led"] <= disc) & (im[..., 1] > 150) & (im[..., 2] > 150) & grow(red > 30, 3)
        if core.any():
            core = grow(core, 1)
            keep = (~core).astype(np.float32)
            num, den = blur2(out * keep[..., None], 4.0), blur2(keep, 4.0)
            out[core] = num[core] / np.maximum(den[core], 1e-3)[:, None]
            count["core"] = int(core.sum())
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
    return {**count, "fit": [round(float(x), 3) for x in coef]}


def load_anchors() -> dict:
    """src/anchors.js (the plate anchors the engine uses), read through esbuild + node like check_graphics."""
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "anchors.mjs"
        subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(COMP / "src/anchors.js"), "--bundle", "--format=esm",
                        "--platform=node", f"--outfile={out}", "--log-level=warning"], check=True)
        js = f"const m = await import({json.dumps(out.as_uri())}); console.log(JSON.stringify(m.ANCHORS));"
        res = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def narrow_face(fonts: Path) -> dict:
    """MK Narrow Bold: Nimbus Sans Narrow Bold subset to printable ASCII and the typographic marks the chant and the key
    words use (motion-kit/tools/fonts.py has no narrow face; spec a2 asks for a tall narrow bold). Appended to
    fonts.json, so the runtime loads it with the other faces."""
    family, src = NARROW
    font = TTFont(src)
    opts = ftsubset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.hinting = False
    sub = ftsubset.Subsetter(opts)
    sub.populate(text="".join(chr(c) for c in range(0x20, 0x7F)) + "’‘“”—–·")
    sub.subset(font)
    path = fonts / (family.replace(" ", "-") + ".otf")
    font.save(path)
    data = path.read_bytes()
    return {"family": family, "source_family": Path(src).stem, "weight": "Bold", "file": path.name, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "license": NARROW_LICENSE, "missing": ""}


# ---- camera move: shots-map camera_move text -> kind + amounts (fractions) ----
def parse_move(text: str) -> dict:
    s = text.lower()
    pct = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", s)]
    rng = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*%", s)
    amount = ((float(rng.group(1)) + float(rng.group(2))) / 2 if rng else (pct[0] if pct else 0.0)) / 100
    if s.startswith("hold"):
        return {"kind": "hold", "z": amount or 0.015}
    if "push" in s:
        return {"kind": "push", "z": amount or 0.06, "drift": 0.015 if "drift" in s else 0.0}
    if "pull" in s:
        return {"kind": "pull", "z": amount or 0.08}
    if "truck" in s:
        return {"kind": "truck", "dx": amount or 0.08}
    if "eye" in s:
        return {"kind": "eye", "dx": amount or 0.08}
    if "pan" in s:
        return {"kind": "pan", "dx": amount or 0.08}
    if "up" in s or "crane" in s or "rise" in s:
        return {"kind": "up", "dy": amount or 0.06}
    if "rotat" in s or "arc" in s:
        return {"kind": "rotate", "r": 2.5}
    return {"kind": "hold", "z": 0.015}


# ---- CTC words and on-screen tokens ----
UNITS_W = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
           "seventeen eighteen nineteen").split()
TENS_W = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}
ORD_W = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}


def wnorm(s: str) -> str:
    return re.sub(r"[^a-z0-9'-]", "", s.lower().replace("’", "'")).strip("'-")


def number(w: str) -> int | None:
    if w in ORD_W:
        return ORD_W[w]
    if w in UNITS_W:
        return UNITS_W.index(w)
    parts = w.split("-")
    if parts[0] in TENS_W and (len(parts) == 1 or (len(parts) == 2 and parts[1] in UNITS_W[1:10])):
        return TENS_W[parts[0]] + (UNITS_W.index(parts[1]) if len(parts) == 2 else 0)
    return None


def spoken_words(lines: list[dict]) -> list[tuple[float, str]]:
    """(onset, normalised word) for every CTC word, its hyphen parts, and spelled-out letters joined (D N S -> dns)."""
    out = []
    for L in lines:
        ws = L["words"]
        i = 0
        while i < len(ws):
            w = wnorm(ws[i]["text"])
            out.append((ws[i]["start"], w))
            if "-" in w:
                out += [(ws[i]["start"], p) for p in w.split("-") if p]
            j = i
            while j < len(ws) and len(wnorm(ws[j]["text"])) == 1 and wnorm(ws[j]["text"]).isalpha():
                j += 1
            if j - i >= 2:
                out.append((ws[i]["start"], "".join(wnorm(x["text"]) for x in ws[i:j])))
            i += 1
    return sorted(out)


def token_matches(tok: str, w: str) -> bool:
    k = wnorm(tok)
    if not k or not w:
        return False
    if k == w:
        return True
    if k.isalpha() and len(k) >= 3 and w.startswith(k):                # SEP september, OCT october, EVAL evaluation
        return True
    if k.isdigit():
        return number(w) == int(k)                                     # 20 twenty, 11 eleven, 01 first
    return False


def tokens(text: str) -> list[str]:
    return [x for x in re.split(r"[\s·→,—:]+|(?<=\D)\.|\n", text) if re.search(r"[A-Za-z0-9]", x)]


def unit_lyric(lines: list[dict], t0: float, t1: float, min_s: float = 0.1) -> list[dict]:
    """The CTC words a unit shows (spec 歌词层: 单元内按 [t0, t1) 取): every word that sounds inside [t0, t1), i.e. its
    midpoint falls there (the board's rule, build_board.py lyric()) or at least min_s of it does. So a word sung across
    a cut shows in both units from its onset (no lyric arrives late), and a word that only grazes a cut (a few frames)
    does not pop up at a unit's edge. Grouped per CTC line ("line": its index in words.json, for the key word), times
    unchanged."""
    own = [(i, w) for i, L in enumerate(lines) for w in L["words"]
           if t0 <= (w["start"] + w["end"]) / 2 < t1 or min(w["end"], t1) - max(w["start"], t0) >= min_s]
    segs: list[dict] = []
    for i, w in own:
        if not segs or segs[-1]["line"] != i:
            segs.append({"line": i, "mode": lines[i].get("mode", "spoken"), "words": []})
        segs[-1]["words"].append({"text": w["text"], "start": w["start"], "end": w["end"]})
    for s in segs:
        s["start"], s["end"] = s["words"][0]["start"], s["words"][-1]["end"]
    return segs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", type=Path, default=V3 / "shots-map.json")
    ap.add_argument("--main", type=Path, default=COMP / "src/main.js", help="scene code")
    ap.add_argument("--samples", default="", help="extra compositions for windows a:b,c:d (seconds)")
    args = ap.parse_args()
    shots_doc = json.loads(args.shots.read_text(encoding="utf-8"))
    if shots_doc.get("board") != BOARD:
        raise SystemExit(f"shots map board {shots_doc.get('board')!r}, this build reads board {BOARD}")
    DUR = float(shots_doc["duration"])
    units_src = sorted(shots_doc["shots"], key=lambda s: s["t0"])
    data = COMP / "data"
    data.mkdir(exist_ok=True)

    # ---- song: master, beat map, hits, CTC words, music map (copied unchanged) ----
    wav = SONG / "IRIS-01-T4.wav"
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(wav)],
                                      capture_output=True, text=True, check=True).stdout)
    if abs(float(probe["format"]["duration"]) - DUR) > 1e-3:
        raise SystemExit(f"song {probe['format']['duration']} s != shots map {DUR} s")
    for name in ("beats", "hits"):
        shutil.copyfile(SONG / f"beatmap/{name}.json", data / f"{name}.json")
    shutil.copyfile(SONG / "timing/words.json", data / "words.json")
    shutil.copyfile(SONG / "music-map.json", data / "music-map.json")
    (data / "music.json").write_text(json.dumps({"song_offset": 0.0, "window_bar0": 0, "source": "IRIS-01-T4"}))
    audio = COMP / "audio"
    audio.mkdir(exist_ok=True)
    if not (audio / "IRIS-01-T4.wav").exists() or sha(audio / "IRIS-01-T4.wav") != sha(wav):
        shutil.copyfile(wav, audio / "IRIS-01-T4.wav")
    beats = json.loads((data / "beats.json").read_text())
    hits = json.loads((data / "hits.json").read_text())
    lines = json.loads((data / "words.json").read_text())["lines"]
    bt = beats["beats"]
    spoken = spoken_words(lines)
    onsets = sorted(w["start"] for L in lines for w in L["words"])

    # ---- units: contiguous, frame-quantised ----
    total = q(DUR)
    if abs(units_src[0]["t0"]) > 1e-9 or abs(units_src[-1]["t1"] - DUR) > 1e-6:
        raise SystemExit("shots map does not cover 0..duration")
    for a, b in zip(units_src, units_src[1:]):
        if abs(a["t1"] - b["t0"]) > 1e-6:
            raise SystemExit(f"gap between {a['unit']} and {b['unit']}")
    plate_units: dict[str, list[str]] = {}
    for s in units_src:
        for p in s["plates"]:
            plate_units.setdefault(Path(p["plate"]).stem, []).append(s["unit"])

    notes: list[str] = []
    plates_dir = COMP / "plates"
    plates_dir.mkdir(exist_ok=True)
    for old in plates_dir.glob("*.png"):                               # stale plates of an earlier map
        if old.stem not in plate_units and old.stem != GROUND:
            old.unlink()
    plates: dict[str, dict] = {}
    for key, us in plate_units.items():
        rel = next(p["plate"] for s in units_src for p in s["plates"] if Path(p["plate"]).stem == key)
        src, dst = SERIES / rel, plates_dir / f"{key}.png"
        if src.exists():
            if not dst.exists() or sha(dst) != sha(src):
                shutil.copyfile(src, dst)
            with Image.open(dst) as im:
                size = list(im.size)
            plates[key] = {"src": rel, "status": "plate", "sha256": sha(dst), "size": size, "units": us}
        else:
            placeholder(key, us, dst)
            plates[key] = {"src": rel, "status": "placeholder", "sha256": sha(dst), "size": [1672, 941], "units": us}
        lum = edge_luma(dst)
        plates[key]["lum"] = lum
        plates[key]["light"] = (lum["top"] + lum["bottom"]) / 2 > LIGHT_EDGE
    Image.new("RGB", (W, H), (11, 15, 20)).save(plates_dir / f"{GROUND}.png")
    plates[GROUND] = {"src": None, "status": "generated", "sha256": sha(plates_dir / f"{GROUND}.png"), "size": [W, H], "units": [],
                      "light": False}
    # her lights switched off, for the units whose light flickers on (U002, U084): the unit's first still, derived
    anchors = load_anchors()
    off_of: dict[str, str] = {}
    for s in units_src:
        if "light_flicker_on" in (s["graphic"] or "").split("+") and s["plates"]:
            key = Path(s["plates"][0]["plate"]).stem
            if key in off_of or plates[key]["status"] != "plate":
                continue
            off = f"{key}--off"
            count = lights_off(plates_dir / f"{key}.png", plates_dir / f"{off}.png", anchors.get(key, {}))
            fit = count.pop("fit", None)
            if not count or not any(count.values()):
                (plates_dir / f"{off}.png").unlink(missing_ok=True)
                notes.append(f"{s['unit']}: no light to switch off on {key} ({count})")
                continue
            off_of[key] = off
            plates[off] = {"src": None, "status": "derived", "of": key, "masked_px": count, "red_fit": fit,
                           "sha256": sha(plates_dir / f"{off}.png"),
                           "size": plates[key]["size"], "units": [s["unit"]], "lum": plates[key]["lum"], "light": plates[key]["light"]}

    def first(seq, lo, hi):
        i = bisect.bisect_left(seq, lo)
        return seq[i] if i < len(seq) and seq[i] < hi else None

    hit_t = sorted(h["t"] for h in hits["hits"])
    chrome = shots_doc.get("chrome") or {}
    units = []
    for i, s in enumerate(units_src):
        t0, t1 = s["t0"], s["t1"]
        f0 = q(t0)
        f1 = q(units_src[i + 1]["t0"]) if i + 1 < len(units_src) else total
        if "cue_s" in s:
            cue, src = s["cue_s"], "cue_s"
        elif (h := first(hit_t, t0, t1)) is not None:
            cue, src = h, "hit"
        elif (w := first(onsets, t0, t1)) is not None:
            cue, src = w, "word"
        elif (b := first(bt, t0 + 2 / FPS, t1)) is not None:
            cue, src = b, "beat"
        else:
            cue, src = t0, "cut"                                       # nothing inside: the cut itself (U053's flash)
        last = (f1 - 1) / FPS                                          # a cue in the unit's last frame stays in the unit
        cue = min(max(qt(cue), f0 / FPS), last)
        text = s["graphic_text"] or ""
        toks, prev = [], cue
        for tok in tokens(text):
            on = next((ts for ts, w in spoken if t0 - 0.25 <= ts < t1 and token_matches(tok, w)), None)
            at = min(max(qt(on), f0 / FPS + 2 / FPS), last) if on is not None else prev
            toks.append({"text": tok, "at": at, "voiced": on is not None})
            prev = at
        ups = [{"key": Path(p["plate"]).stem, "from": p["from"],
                "f": q(t0 + p["from"] * (t1 - t0)) if p["from"] > 0 else f0} for p in s["plates"]]
        num = int(s["unit"][1:])
        graphics = [g for g in (s["graphic"] or "").split("+") if g]
        units.append({
            "id": s["unit"], "i": i, "t0": t0, "t1": t1, "f0": f0, "f1": f1, "view": s["viewpoint"], "scale": s["scale"],
            "move": parse_move(s["camera_move"]), "plates": ups, "graphics": graphics, "text": text,
            "lines": text.split("\n") if text else [], "toks": toks, "target": s.get("target"), "targets": s.get("targets"),
            "lineTok": [sum(len(tokens(x)) for x in text.split("\n")[:n]) for n in range(len(text.split("\n")))] if text else [],
            "cue": cue, "cueSrc": src, "voice": s.get("voice", ""), "sing": bool(s.get("sing")),
            "nored": NO_RED[0] <= num <= NO_RED[1], "lyric": next((g for g in graphics if g.startswith("lyric_")), None),
            "lyr": unit_lyric(lines, t0, t1) if any(g.startswith("lyric_") for g in graphics) else [],
            "off": off_of.get(ups[0]["key"]) if ups and "light_flicker_on" in graphics else None,
            "light": any(g.startswith(LIGHT_GROUND) for g in graphics),
            "chromeDim": s["unit"] in chrome.get("dim_units", []), "ticker": s["unit"] not in chrome.get("no_ticker_units", []),
        })
        if not graphics and s["viewpoint"] == "graphic":
            notes.append(f"{s['unit']}: graphic unit with no component")
    # the monitor wall (a2): nine stills of her not singing, staring into the lens (WALL)
    wall = [k for k in WALL if k in plates]
    if len(wall) != len(WALL):
        raise SystemExit(f"wall stills not in the map: {sorted(set(WALL) - set(wall))}")
    bitmaps = set(wall)
    for u in units:
        if {"photo_flip_cached", "reflection_layer"} & set(u["graphics"]):
            bitmaps |= {p["key"] for p in u["plates"]}
    # the editorial chrome (spec a2 剪辑界面层): its switches resolved to frames
    switches = lambda xs: [{"f": q(x["from"]), "text": x["text"]} for x in sorted(xs, key=lambda x: x["from"])]
    chrome_doc = {"corners": bool(chrome.get("corner_marks")), "topLeft": chrome.get("top_left", ""),
                  "counter": switches(chrome.get("counter", [])), "topRight": switches(chrome.get("top_right", [])),
                  "ticker": chrome.get("ticker", [])}
    doc = {"shots_map_sha256": sha(args.shots), "fps": FPS, "duration": DUR, "frames": total, "units": units, "wall": wall,
           "chrome": chrome_doc}
    blob = json.dumps(doc, ensure_ascii=False)
    if CJK.search(blob):
        raise SystemExit(f"units.json would carry Chinese: {CJK.search(blob).group(0)!r}")
    (data / "units.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    (data / "plates.json").write_text(json.dumps(plates, ensure_ascii=False, indent=1))
    (data / "assets.json").write_text(json.dumps({"images": sorted(plates), "bitmaps": sorted(bitmaps)}, indent=1))
    for old in ("card.json",):                                         # v1 leftovers the engine no longer reads
        (data / old).unlink(missing_ok=True)

    # ---- events qa.py checks (the picture changes within a frame of the time, measured on the whole frame): every cut,
    # every plate switch, and the cue of a component that changes most of the picture on it (BIG_CUE). Small changes
    # (boxes, tags, OSD words, lyric words, a collar light) do not move the whole-frame difference above the grain and
    # are checked on the frame review instead ----
    ev = {}
    for u in units[1:]:
        ev[f"cut_{u['id']}"] = {"t": u["f0"] / FPS, "what": f"cut to {u['id']} ({u['plates'][0]['key'] if u['plates'] else GROUND})"}
    for u in units:
        for n, p in enumerate(u["plates"][1:], 1):
            ev[f"{u['id']}_plate{n}"] = {"t": p["f"] / FPS, "what": f"{u['id']} switches to {p['key']}"}
        big = [g for g in u["graphics"] if g.startswith(BIG_CUE)]
        if big and u["cue"] > u["f0"] / FPS + 1e-9:
            ev[f"{u['id']}_cue"] = {"t": u["cue"], "what": f"{u['id']} cue ({u['cueSrc']}): {'+'.join(big)}"}
    (data / "events.json").write_text(json.dumps({"events": ev}, ensure_ascii=False, indent=1))

    # ---- fonts, bundle, pages ----
    subprocess.run([sys.executable, str(KIT / "tools/fonts.py"), "--out", str(COMP / "fonts"), "--latin", "--grotesk",
                    "--scan", str(COMP / "src"), str(KIT / "src"), str(data / "words.json"), str(data / "units.json")],
                   check=True, stdout=subprocess.DEVNULL)
    manifest = json.loads((COMP / "fonts/fonts.json").read_text(encoding="utf-8"))
    manifest["faces"] = [f for f in manifest["faces"] if f["family"] != NARROW[0]] + [narrow_face(COMP / "fonts")]
    (COMP / "fonts/fonts.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(args.main), "--bundle", "--format=iife",
                    "--target=chrome120", f"--outfile={COMP / 'engine.js'}", "--log-level=warning"], check=True)
    unhandled = check_graphics(units)

    def page(dur: float, offset: float = 0.0) -> str:
        extra = f' data-mk-offset="{offset:g}"' if offset else ""
        media = f' data-media-start="{offset:g}"' if offset else ""
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRIS EP01 v3 animatic a2</title>
<style>html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-start="0" data-duration="{dur:g}"{extra} data-no-timeline>
  <canvas id="stage" class="clip" width="{W}" height="{H}" data-start="0" data-duration="{dur:g}" data-track-index="0"></canvas>
  <audio id="music" src="audio/IRIS-01-T4.wav" data-start="0" data-duration="{dur:g}"{media} data-track-index="1" data-volume="1" data-timeline-role="music"></audio>
</div>
<script src="engine.js"></script>
</body>
</html>
"""
    (COMP / "index.html").write_text(page(DUR), encoding="utf-8")
    for old in COMP.glob("sample-*.html"):
        old.unlink()
    for win in filter(None, args.samples.split(",")):
        a, b = (float(x) for x in win.split(":"))
        if q(a) != a * FPS:
            raise SystemExit(f"sample start {a} is not on a frame")
        (COMP / f"sample-{a:04.0f}-{b:04.0f}.html").write_text(page(b - a, a), encoding="utf-8")
    missing = sorted(f"{k} ({','.join(v['units'])})" for k, v in plates.items() if v["status"] == "placeholder")
    for n in notes:
        print("note:", n)
    print(json.dumps({"units": len(units), "frames": total, "duration": DUR, "plates": len(plates) - 1,
                      "placeholders": missing, "unhandled_graphics": unhandled, "shots_map_sha256": doc["shots_map_sha256"],
                      "events": len(ev), "wall": wall, "lights_off": off_of,
                      "cues": {u["id"]: [round(u["cue"], 4), u["cueSrc"]] for u in units}}, ensure_ascii=False))
    return 0


def check_graphics(units: list[dict]) -> list[str]:
    """Graphic names in the shots map that src/graphics.js has no handler for (they would draw nothing)."""
    names = sorted({g for u in units for g in u["graphics"]})
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "graphics.mjs"
        subprocess.run([str(REPO / "node_modules/.bin/esbuild"), str(COMP / "src/graphics.js"), "--bundle", "--format=esm",
                        "--platform=node", f"--outfile={out}", "--log-level=warning"], check=True)
        js = f"const m = await import({json.dumps(out.as_uri())}); console.log(JSON.stringify({json.dumps(names)}.filter(n => !m.handlerOf(n))));"
        res = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
