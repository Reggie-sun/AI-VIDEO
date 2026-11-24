#!/usr/bin/env python3
"""IRIS EP01 opening v3 (2026-11-21, v2d review: "还是都是一个模糊程度，太单调"): per-shot blur classes measured on EV
(outputs/anabology-opus55-replica/escape_velocity_analysis/blur_study/REPORT.md: over 0-120 s A fully sharp 62.5 %,
B shallow focus 14.5 %, C / C* motion smear 5.7 %, D whole frame soft / dark / low contrast 9 %, E whole-frame defocus
3.1 %). This script makes the pictures that carry a class in the picture itself; the classes that are a grade (A: the
v4r11 print's uniform softening taken down; D: soft, darker, flatter) are shot.blur.grade in the v3 EDLs
(opening_v2.py --build-3). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/prep_blur_v3.py [--only s002,s006,...]

Inputs are the prepared pictures every earlier round shows (media/seq/<media>/NNNN.jpg, 2304x1296; the board stills
1672x941), outputs never overwrite them:

- B (shallow focus): prep_dof.dof() as v4r11 used it (fg 0: the subject untouched; the background blurred with a
  Gaussian normalised by the held-out matte so the subject does not bleed into it, composited through the feathered
  matte). The matte is u2netp on the part of the picture the shot shows (a still's crop, or a region holding the
  subject), so the salient object is the shot's subject. Clips: the matte averaged over +-1 picture.
- E (whole-frame defocus, environment): one Gaussian over the whole still.
- D (whole frame soft, darker, flatter): one Gaussian over every picture (the darker, flatter part is the grade).
- C / C* (motion smear): a shutter blur along a block motion field (phase correlation in 32x32 blocks at quarter
  size, 3x3 median, smoothed): each pixel averaged over 15 taps along gain x its motion to the next picture. Envelopes
  follow the author ("the impact frame stays sharp: the smear peaks on the second frame and is gone by the fourth"):
  on a flash pop or a jolt at picture p, p stays sharp, p+1 gain 1, p+2 gain 0.45, p+3 none. s014's wide: the motion
  field held to her matte (the camera is locked off, the room stays sharp), the turn and the sleeve swing smeared, the
  walk away a lighter shutter blur.
- s014p (the punch-in): edl.S014P_V3 through prep_media.prep_clip at the take's own 3840x2160 (the same placement,
  red repair and lid blot), media/hr3/seq/s014p.

Writes media/blur3/<shot>/NNNN.jpg (clips: every picture of the shot; stills: 0000.jpg), media/blur3/stills/<key>.png,
media/hr3/seq/s014p/NNNN.jpg and data/blur-v3.json (parameters, inputs and outputs with SHA-256).
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep_dof as PD  # noqa: E402
import prep_media as PM  # noqa: E402
from edl import EXC, S014P_V3  # noqa: E402

PD.FG = 0.0                                    # the subject untouched (v4r11's --v11 setting)
OUT = EXC / "media/blur3"
SEQ = EXC / "media/seq"

# B: source, frames, subject region (fractions of the picture the matte is computed on), background sigma (picture px)
B = {
    # her walk down the runway; the front row and the pillars behind and beside her out of focus
    "s002": {"seq": "o002", "region": (0.30, 0.0, 0.78, 1.0), "bg": 22.0},
    # the front-row engineer on his phone sharp, she walks past soft behind him (board s003: FRONT ROW LOOKING AT
    # HER 0 / THEIR PAGER 1; the classifier boxes him): the region holds him, so the matte is his
    "s003": {"seq": "o003", "still": True, "region": (0.0, 0.08, 0.50, 1.0), "bg": 22.0,
             "protect": [(0.0, 0.12, 0.47, 1.0)]},           # his whole figure (u2netp takes his head only), phone, laptop
    # her face at the payphone; the pillar, the phone box and the street lights behind out of focus
    "s005": {"seq": "o005", "region": (0.38, 0.0, 1.0, 1.0), "bg": 22.0},
    # she reaches to the board; the street and the glass behind her out of focus (the board too: the scratch is a
    # graphic in Agentcut)
    "s009": {"seq": "o009", "still": True, "region": (0.0, 0.0, 1.0, 1.0), "bg": 22.0,
             "protect": [(0.55, 0.25, 0.84, 0.55)],          # her reaching arm (u2netp drops it) ...
             "falloff": (0.60, 0.86, 0.15)},                 # ... going out of focus toward the board (x 0.60 -> 0.86)
}
# B on the chorus stills (1672x941 board plates): the matte on the shot's own view (shots6.js s012a engineer view
# [380, 420, 2.2]; shots8.js s013a view [900..920, 560..540, 1.55..1.9]); sigma in plate px (x 2.53 / x 1.95 on screen)
B_STILLS = {
    "p012w1-engineer": {"src": "media/stills-v4r1/p012-w1.png", "region_px": (0, 80, 560, 941), "bg": 8.0,
                        "protect": [(0.0, 0.13, 0.265, 1.0)]},   # him (head to laptop), not her: the view is his face
    "INS13-a": {"src": "flash/design/INS13/INS13-a.png", "region_px": (360, 256, 1440, 863), "bg": 9.0},
}
# E: one still, whole-frame Gaussian (picture px)
E = {"s007": {"seq": "o007", "sigma": 13.0}, "s010": {"seq": "o010", "sigma": 13.0}}
# D: the whole picture softened (Gaussian, picture px) under D's darker, flatter grade (opening_v2.py D_GRADE): the
# chorus's closed-eye sung close-up (every picture of s012c, 2304 wide) and the pager insert (INS14-b, 1672 wide, shown
# at ~1.5x)
D = {"s012c": {"seq": "s012c", "sigma": 14.0}, "INS14-b": {"src": "flash/design/INS14/INS14-b.png", "sigma": 6.0}}
# C: motion smear
POP = (0.0, 1.0, 0.45)                         # p (sharp), p+1, p+2; gone from p+3
C = {
    # handheld paparazzi: the take's flash pops (whole-frame luminance up >= 8 on one picture and back) and her
    # fastest swing (pictures 77-79, the camera at 60-80 px per picture): the smear along the camera's own motion at
    # 4x it on her (a one-picture whip; EV's C / C* shots measure subject sigma_e 16-24), 0.3 of that on the street
    # behind her ("bg"), and where the smear is long a Gaussian ("iso" px) mixed in over her: a turning, twisting
    # figure smears in more than one direction (a straight line blur alone leaves the edges along it sharp)
    "s006": {"seq": "o006", "gain": 4.0, "matte": "weight", "bg": 0.3, "iso": 7.0, "pop_rise": 8.0, "extra_impacts": [77]},
    # s014's wide (r6-2 pictures 44-87 = song frames 1366-1409): her turn and the single sleeve swing (pictures 44-56,
    # 56.92-57.42 s) smeared at 5x her motion to the next picture (the smear burned into the turn, EV's S0058), then
    # the walk away at 2x; the motion field (16 px blocks at half size in her box) held to her matte
    "s014a": {"seq": "s014r6", "first": 44, "matte": "box", "iso": 7.0, "flow": {"q": 2, "bs": 32, "step": 8},
              "ramp": [(44, 5.0), (56, 5.0), (60, 2.0), (87, 2.0)]},
}


def sha(p: Path) -> str:
    return PM.sha(p)


def load(p: Path) -> np.ndarray:
    return np.asarray(Image.open(p).convert("RGB"))


def save(a: np.ndarray, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix == ".png":
        Image.fromarray(a).save(p)
    else:
        Image.fromarray(a).save(p, quality=93, subsampling=0)


def region_matte(rgb: np.ndarray, region=None, region_px=None) -> np.ndarray:
    """u2netp matte of the region (fractions or px), placed back into a full-size matte (0 outside)."""
    h, w = rgb.shape[:2]
    if region_px is None:
        x0, y0, x1, y1 = region or (0, 0, 1, 1)
        region_px = (int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))
    x0, y0, x1, y1 = region_px
    m = np.zeros((h, w), np.float32)
    m[y0:y1, x0:x1] = PM.matte(np.ascontiguousarray(rgb[y0:y1, x0:x1]))
    return m


# ---------------------------------------------------------------- B
def do_b(sid: str) -> dict:
    c = B[sid]
    src = SEQ / c["seq"]
    files = sorted(src.glob("*.jpg"))[:1] if c.get("still") else sorted(src.glob("*.jpg"))
    imgs = [load(f) for f in files]
    mats = [region_matte(i, c["region"]) for i in imgs]
    if c.get("falloff"):
        # the focus falls off along x: the subject matte (and the protect boxes) weighted 1 -> w1 from x0 to x1; the
        # protect boxes are joined here, so dof() gets none
        x0, x1, w1 = c["falloff"]
        h, w = imgs[0].shape[:2]
        ramp = np.clip(1 - (np.arange(w) / w - x0) / (x1 - x0) * (1 - w1), w1, 1).astype(np.float32)[None, :]
        box = np.zeros((h, w), np.float32)
        for bx0, by0, bx1, by1 in c.get("protect") or []:
            box[int(by0 * h):int(by1 * h), int(bx0 * w):int(bx1 * w)] = 1
        box = np.clip(PD.blur(box, 0.03 * w, 255), 0, 1)
        # dof() maps the matte through (m - 0.25) / 0.5: the weights are given in that mapped scale
        mats = [0.25 + 0.5 * (np.maximum(np.clip((m - 0.25) / 0.5, 0, 1), box) * ramp) for m in mats]
    dst = OUT / sid
    for k, (f, im) in enumerate(zip(files, imgs)):
        m = np.mean(mats[max(0, k - 1):k + 2], 0)
        save(PD.dof(im, m, None if c.get("falloff") else c.get("protect"), c["bg"]), dst / f.name)
    return {"class": "B", "src": str(src.relative_to(EXC)), "pictures": len(files), "bg_sigma_px": c["bg"],
            "matte_region": c["region"], "protect": c.get("protect"), "falloff": c.get("falloff"), "out": str(dst.relative_to(EXC)), "sha256_0000": sha(dst / files[0].name)}


def do_b_still(key: str) -> dict:
    c = B_STILLS[key]
    im = load(EXC / c["src"])
    m = region_matte(im, region_px=c["region_px"])
    dst = OUT / "stills" / f"{key}.png"
    save(PD.dof(im, m, c.get("protect"), c["bg"]), dst)
    return {"class": "B", "src": c["src"], "src_sha256": sha(EXC / c["src"]), "bg_sigma_px": c["bg"], "matte_region_px": c["region_px"], "protect": c.get("protect"),
            "out": str(dst.relative_to(EXC)), "sha256": sha(dst)}


# ---------------------------------------------------------------- E
def do_e(sid: str) -> dict:
    c = E[sid]
    f = SEQ / c["seq"] / "0000.jpg"
    dst = OUT / f"{sid}-E" / "0000.jpg"
    save(np.asarray(Image.open(f).convert("RGB").filter(ImageFilter.GaussianBlur(c["sigma"]))), dst)
    return {"class": "E", "src": str(f.relative_to(EXC)), "sigma_px": c["sigma"], "out": str(dst.parent.relative_to(EXC)), "sha256_0000": sha(dst)}


# ---------------------------------------------------------------- D
def do_d(key: str) -> dict:
    c = D[key]
    g = ImageFilter.GaussianBlur(c["sigma"])
    if "seq" in c:
        files = sorted((SEQ / c["seq"]).glob("*.jpg"))
        dst = OUT / f"{key}-D"
        for f in files:
            save(np.asarray(Image.open(f).convert("RGB").filter(g)), dst / f.name)
        return {"class": "D", "src": f"media/seq/{c['seq']}", "pictures": len(files), "sigma_px": c["sigma"], "out": str(dst.relative_to(EXC)),
                "sha256_0000": sha(dst / "0000.jpg")}
    dst = OUT / "stills" / f"{key}-D.png"
    save(np.asarray(Image.open(EXC / c["src"]).convert("RGB").filter(g)), dst)
    return {"class": "D", "src": c["src"], "src_sha256": sha(EXC / c["src"]), "sigma_px": c["sigma"], "out": str(dst.relative_to(EXC)), "sha256": sha(dst)}


# ---------------------------------------------------------------- C
def shift(a, b):
    """Phase-correlation shift (dx, dy) of b against a and the peak height."""
    h, w = a.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    A, Bf = np.fft.fft2((a - a.mean()) * win), np.fft.fft2((b - b.mean()) * win)
    R = A.conj() * Bf
    R /= np.abs(R) + 1e-9
    c = np.real(np.fft.ifft2(R))
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    return (ix if ix <= w // 2 else ix - w), (iy if iy <= h // 2 else iy - h), float(c.max())


def flow(a: np.ndarray, b: np.ndarray, bs: int = 32, step: int = 16, q: int = 4, box=None) -> np.ndarray:
    """Block motion field (px of the full picture per picture) from picture a to b, both full-size RGB; with box
    (x0, y0, x1, y1 px) only inside it (zero outside)."""
    H0, W0 = a.shape[:2]
    x0, y0, x1, y1 = box or (0, 0, W0, H0)
    a, b = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
    h, w = a.shape[:2]
    ga = np.asarray(Image.fromarray(a).convert("L").resize((w // q, h // q), Image.BOX), np.float64)
    gb = np.asarray(Image.fromarray(b).convert("L").resize((w // q, h // q), Image.BOX), np.float64)
    gh, gw = (ga.shape[0] - bs) // step + 1, (ga.shape[1] - bs) // step + 1
    V = np.zeros((gh, gw, 2))
    for j in range(gh):
        for i in range(gw):
            pa = ga[j * step:j * step + bs, i * step:i * step + bs]
            pb = gb[j * step:j * step + bs, i * step:i * step + bs]
            if pa.std() < 2:
                continue
            dx, dy, pk = shift(pa, pb)
            if pk > 0.12:
                V[j, i] = (dx, dy)
    M = V.copy()                                       # 3x3 median per component
    P = np.pad(V, ((1, 1), (1, 1), (0, 0)), mode="edge")
    for c in range(2):
        st = np.stack([P[1 + dj:1 + dj + gh, 1 + di:1 + di + gw, c] for dj in (-1, 0, 1) for di in (-1, 0, 1)])
        M[..., c] = np.median(st, 0)
    P = np.pad(M, ((1, 1), (1, 1), (0, 0)), mode="edge")             # then a 3x3 mean, and bilinear up to full size
    M = sum(P[1 + dj:1 + dj + gh, 1 + di:1 + di + gw] for dj in (-1, 0, 1) for di in (-1, 0, 1)) / 9
    out = np.zeros((H0, W0, 2), np.float32)
    for c in range(2):
        im = Image.fromarray(M[..., c].astype(np.float32), mode="F").resize((w, h), Image.BILINEAR)
        out[y0:y1, x0:x1, c] = np.asarray(im, np.float32) * q
    return out


def bilinear(img: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def shutter(img: np.ndarray, v: np.ndarray, gain: float, taps: int = 15) -> np.ndarray:
    if gain <= 0:
        return img
    f = img.astype(np.float32)
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    acc = np.zeros_like(f)
    for t in np.linspace(-0.5, 0.5, taps):
        acc += bilinear(f, xx + t * gain * v[..., 0], yy + t * gain * v[..., 1])
    return np.clip(acc / taps + 0.5, 0, 255).astype(np.uint8)


def pops(files: list[Path], rise: float) -> list[int]:
    L = np.array([np.asarray(Image.open(f).convert("L").resize((288, 162), Image.BOX), np.float64).mean() for f in files])
    return [i for i in range(1, len(L) - 1) if L[i] - L[i - 1] >= rise and L[i] - L[i + 1] >= rise * 0.6]


def do_c(sid: str) -> dict:
    c = C[sid]
    files = sorted((SEQ / c["seq"]).glob("*.jpg"))[c.get("first", 0):]
    n = len(files)
    gains = np.zeros(n)
    impacts = []
    if "pop_rise" in c:
        impacts = sorted(set(pops(files, c["pop_rise"]) + c.get("extra_impacts", [])))
        for p in impacts:
            for k, g in enumerate(POP):
                if p + k < n:
                    gains[p + k] = max(gains[p + k], g * c["gain"])
    if "ramp" in c:
        f0 = c.get("first", 0)
        xs, ys = zip(*c["ramp"])
        gains = np.interp(np.arange(n) + f0, xs, ys)
    dst = OUT / sid
    dst.mkdir(parents=True, exist_ok=True)
    imgs = [load(f) for f in files]
    log = []
    for k in range(n):
        im = imgs[k]
        g = float(gains[k])
        if g > 0:
            nb = imgs[k + 1] if k + 1 < n else None
            m = None
            box = None
            if c.get("matte"):
                m = np.clip((PM.matte(im) - 0.2) / 0.5, 0, 1)
            if c.get("matte") == "box":
                ys, xs = np.nonzero(m > 0.3)
                pad = 96                                 # her box, grown so the sleeve's swing stays inside it
                box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.shape[1], xs.max() + pad), min(im.shape[0], ys.max() + pad))
            fa, fb = (im, nb) if nb is not None else (imgs[k - 1], im)
            v = flow(fa, fb, **c.get("flow", {}), box=box)
            if m is not None:
                m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
                bg = c.get("bg", 0.0)
                v = v * (bg + (1 - bg) * m)[..., None]
            out = shutter(im, v, g)
            mag = np.hypot(v[..., 0], v[..., 1])
            if c.get("iso"):
                w = np.clip(mag * g / 40.0, 0, 1) * (m if m is not None else 1.0)
                iso = np.asarray(Image.fromarray(out).filter(ImageFilter.GaussianBlur(c["iso"])), np.float32)
                out = np.clip(out * (1 - w[..., None]) + iso * w[..., None] + 0.5, 0, 255).astype(np.uint8)
            log.append({"pic": k, "gain": round(g, 3), "motion_p90_px": round(float(np.percentile(mag[mag > 0.5], 90)), 1) if (mag > 0.5).any() else 0.0})
        else:
            out = im
        save(out, dst / f"{k:04d}.jpg")
    return {"class": "C", "src": f"media/seq/{c['seq']}", "first_picture": c.get("first", 0), "pictures": n, "impacts": impacts,
            "envelope": list(POP) if impacts else None, "ramp": c.get("ramp"), "gain": c.get("gain"), "matte": c.get("matte", False),
            "bg_share": c.get("bg"), "iso_px": c.get("iso"),
            "smeared": log, "out": str(dst.relative_to(EXC))}


# ---------------------------------------------------------------- s014p
def do_s014p() -> dict:
    out = EXC / "media/hr3"
    if (out / "seq" / S014P_V3["media_id"]).exists():
        raise SystemExit("media/hr3/seq/s014p exists (not overwritten)")
    PM.SEQ_W, PM.SEQ_H = 3840, 2160              # decode, the hue step and the blot read these at call time
    m = PM.prep_clip(S014P_V3, out)
    return {"class": "A (punch-in source)", "size": [3840, 2160], **{k: m[k] for k in ("clip", "clip_sha256", "frames", "first", "last", "map", "logos")},
            "out": "media/hr3/seq/s014p"}


JOBS = {**{k: ("b", k) for k in B}, **{k: ("bs", k) for k in B_STILLS}, **{k: ("e", k) for k in E}, **{k: ("c", k) for k in C}, **{f"{k}-D": ("d", k) for k in D},
        "s014p": ("p", "s014p")}


def run(job):
    kind, k = job
    return (f"{k}-D" if kind == "d" else k), {"b": do_b, "bs": do_b_still, "e": do_e, "c": do_c, "d": do_d, "p": lambda _: do_s014p()}[kind](k)


def main() -> int:
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(JOBS)
    meta_p = EXC / "data/blur-v3.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        for k, r in ex.map(run, [JOBS[k] for k in only]):
            meta[k] = r
            print(k, json.dumps({x: y for x, y in r.items() if x not in ("smeared", "map", "logos")}), flush=True)
    meta_p.write_text(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
