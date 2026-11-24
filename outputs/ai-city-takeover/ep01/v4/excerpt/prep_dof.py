#!/usr/bin/env python3
"""v4r8 (2026-11-19): depth of field for every picture v4r7 shows. The user: "很多还是都太清晰了"; the coordinator's
viewing-scale measure (qa/grad.py: mean |grad| / std at 240 and 160 px wide) put ours ~60% above EV, because ours is
sharp from front to back where EV's backgrounds are soft. Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/prep_dof.py [--bg 10] [--fg 1.4]

For each picture (the prepared clip pictures of v4r7 and its stills): the figure matte (u2netp, the salient subject:
her, or the hand / phone / pager of an insert; for clips averaged with the neighbouring pictures so it does not
flicker), grown and feathered; the background blurred with a large Gaussian (sigma --bg px of the picture) normalised
by the matte, so the figure does not bleed into it; the figure itself only lightly softened (--fg); composited through
the feathered matte. Writes media/dof/seq/<id>/NNNN.jpg and media/dof/stills/<key>.png, and data/dof-v4r8.json.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, SHOTS_V4R7  # noqa: E402

OUT = EXC / "media/dof"
# v4r9 (--v9): the coordinator's note on v4r8 ("像手机人像模式"): the story's other people and the inserts' hands and
# props are subjects too, softened like her and not as background. Boxes in fractions of the frame (x0, y0, x1, y1),
# feathered, joined to her matte; "all" = the whole picture is subject (a close insert).
PROTECT = {
    "s011s": [(0.0, 0.36, 0.30, 1.0), (0.70, 0.40, 1.0, 1.0)],      # the nearest engineers, both front rows
    "s012b": [(0.0, 0.12, 0.30, 1.0)],                              # the engineer she sings to: face, hands, laptop
    "s012c": [(0.0, 0.25, 0.22, 1.0)],                              # him, left foreground of the close-up
    "s013b": [(0.0, 0.62, 0.30, 1.0)],                              # his hand reaching for the phone
    "s014a": [(0.0, 0.40, 0.26, 1.0), (0.78, 0.40, 1.0, 1.0)],      # the nearest engineers either side
    "s014b": [(0.0, 0.40, 0.26, 1.0), (0.78, 0.40, 1.0, 1.0)],
    "INS13-a": "all", "INS14-b": "all",                              # hand + phone / hand + pager: close inserts
}


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


BG, FG = arg("--bg", 10.0), arg("--fg", 1.4)
V9 = "--v9" in sys.argv
BG_FLAT, BG_DIM = arg("--flat", 0.4), arg("--dim", 0.78)
if V9:
    OUT = EXC / "media/dof9"
# v4r11 (--v11, 2026-11-20; blur_study/REPORT.md section 6): EV keeps 62% of its shots sharp front to back and gives a
# shallow focus to a few face / medium shots only (face 6.4-9.3, background 17-27, ratio 1.8-4). So: no depth of field
# on any other picture (v4r11 shows the clean media/seq), and on the shots picked here the figure untouched (fg 0), the
# background at its own sigma (picture px, 2304 wide), no flatten or dim (an optical blur only). The PROTECT boxes of
# these shots (the engineer at her chair, his reaching hand) are nearer the lens than her: out of focus too, at the
# background's sigma x V11_NEAR (a defocus grows with |1/d - 1/d_focus|: the near figure close to the lens, the garage far
# behind; 0.7 so the near figure's edges read soft at the measured background's floor, blur_study 16-27 px).
V11 = "--v11" in sys.argv
V11_BG = {"s012b": 28.0, "s013b": 28.0}
V11_NEAR = 0.7
# the near figures of these shots: PROTECT's boxes, s012b's widened to take the engineer's nose and brow (0.30 left them
# at the box's edge, sharp)
V11_BOX = {"s012b": [(0.0, 0.12, 0.35, 1.0)], "s013b": PROTECT["s013b"]}
if V11:
    OUT, FG = EXC / "media/dof11", arg("--fg", 0.0)
_sess = None


def raw_matte(rgb: np.ndarray) -> np.ndarray:
    global _sess
    import prep_media
    return prep_media.matte(rgb)


def blur(a: np.ndarray, s: float, scale: float = 1.0) -> np.ndarray:
    """Gaussian blur through PIL (8-bit L / RGB); `scale` maps the array to 0..255 and back (1 for pixels, 255 for 0..1)."""
    if s <= 0.05:
        return a.astype(np.float32)
    im = Image.fromarray(np.clip(a * scale + 0.5, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(s)), np.float32) / scale


def dof(rgb: np.ndarray, m: np.ndarray, protect=None, bg_sigma=None, near_sigma=None) -> np.ndarray:
    h, w = m.shape
    bg_sigma = BG if bg_sigma is None else bg_sigma
    m = np.clip((m - 0.25) / 0.5, 0, 1)
    near = None
    if protect == "all":
        m = np.ones_like(m)
    elif protect and near_sigma is not None:
        # v4r11: the boxes are a near figure, defocused at near_sigma, not joined to her matte
        box = np.zeros_like(m)
        for x0, y0, x1, y1 in protect:
            box[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 1
        near = np.clip(blur(box, 0.03 * w, 255), 0, 1)
        m = m * (1 - near)                     # the salient matte takes him in too (s012b): he is the near figure
    elif protect:
        box = np.zeros_like(m)
        for x0, y0, x1, y1 in protect:
            box[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 1
        m = np.maximum(m, blur(box, 0.03 * w, 255))
    grown = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * int(0.006 * w) + 1)), np.float32) / 255
    a = np.clip(blur(grown, 0.012 * w, 255), 0, 1)                    # the feathered figure
    img = rgb.astype(np.float32)
    keep = 1 - np.clip(blur(grown, 0.004 * w, 255) * 1.4, 0, 1)       # background weights, the figure held out
    num = blur(img * keep[..., None], bg_sigma)
    den = blur(keep, bg_sigma, 255)[..., None]
    bg = np.where(den > 0.02, num / np.maximum(den, 1e-3), blur(img, bg_sigma))
    if V9:
        # EV's backgrounds are "dark, shallow, misty" (the coordinator): flatten the background's local contrast toward a
        # wide blur of itself and darken it a little; its people and things keep their shapes
        bg = (bg * (1 - BG_FLAT) + blur(bg, 0.02 * w) * BG_FLAT) * BG_DIM
    if near is not None:
        nb = near * (1 - np.clip(blur(grown, 0.004 * w, 255) * 1.4, 0, 1))      # her figure stays hers
        bg = blur(img, near_sigma) * nb[..., None] + bg * (1 - nb[..., None])
    fg = blur(img, FG)
    return np.clip(fg * a[..., None] + bg * (1 - a[..., None]), 0, 255).astype(np.uint8)


def do_seq(job):
    src_dir, dst_dir = Path(job[0]), Path(job[1])
    prot = V11_BOX[src_dir.name] if V11 else PROTECT.get(src_dir.name) if V9 else None
    bg_sigma = V11_BG[src_dir.name] if V11 else None
    near_sigma = bg_sigma * V11_NEAR if V11 else None
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob("*.jpg"))
    imgs = [np.asarray(Image.open(f).convert("RGB")) for f in files]
    mats = [raw_matte(i) for i in imgs]
    for k, (f, im) in enumerate(zip(files, imgs)):
        lo, hi = max(0, k - 1), min(len(mats), k + 2)
        m = np.mean(mats[lo:hi], 0)                                     # steadier than one picture's matte
        Image.fromarray(dof(im, m, prot, bg_sigma, near_sigma)).save(dst_dir / f.name, quality=93, subsampling=0)
    return str(dst_dir), len(files)


def do_still(job):
    src, dst = Path(job[0]), Path(job[1])
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = np.asarray(Image.open(src).convert("RGB"))
    if dst.stem.startswith("p012w1"):
        # the two s012a inserts are 2.2-3.2x crops of this still (her hand on the chair, his face): the subject IS the
        # crop, and the still's matte is her whole figure; at that zoom the plate is already soft. Left as it is.
        Image.fromarray(im).save(dst)
        return str(dst), 1
    Image.fromarray(dof(im, raw_matte(im), PROTECT.get(dst.stem) if V9 else None)).save(dst)
    return str(dst), 1


def main() -> int:
    seq_ids, stills = set(), {}
    for s in SHOTS_V4R7:
        if s.get("clip") or s.get("seq_from"):
            seq_ids.add(s.get("seq_from") or s.get("media_id", s["id"]))
        for key, _ in s.get("stills", []):
            stills[key] = (EXC / f"media/stills-w1/{key}.png" if key.startswith("X") else
                           EXC / f"flash/design/{key.split('-')[0]}/{key}.png" if key.startswith("INS") else
                           EXC / "media/stills-v4r1/p012-w1.png")
    if V11:
        seq_ids, stills = set(V11_BG), {}
    jobs_seq = [(str(EXC / f"media/seq/{i}"), str(OUT / f"seq/{i}")) for i in sorted(seq_ids)]
    jobs_still = [(str(p), str(OUT / f"stills/{k}.png")) for k, p in stills.items()]
    with ProcessPoolExecutor(max_workers=8) as ex:
        done = list(ex.map(do_seq, jobs_seq)) + list(ex.map(do_still, jobs_still))
    meta = {"bg_sigma": BG, "fg_sigma": FG, "bg_flat": BG_FLAT if V9 else None, "bg_dim": BG_DIM if V9 else None, "matte": "u2netp (prep_media.matte), clips averaged over +-1 picture",
            "seq": {Path(d).name: n for d, n in done if "/seq/" in d}, "stills": sorted(stills)}
    meta["protect"] = PROTECT if V9 else V11_BOX if V11 else None
    if V11:
        meta.update(bg_sigma=V11_BG, near_sigma={k: v * V11_NEAR for k, v in V11_BG.items()}, bg_flat=None, bg_dim=None)
    (EXC / ("data/dof-v4r11.json" if V11 else "data/dof-v4r9.json" if V9 else "data/dof-v4r8.json")).write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
