#!/usr/bin/env python3
"""Media prep for the IRIS EP01 v4 finished excerpt (song 26.0528-59.2341 s). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/prep_media.py

Reads the edit decision list in edl.py and writes, under media/ and data/:
- media/seq/<shot>/NNNN.jpg: one picture per output frame (24 fps) for every clip shot. The clips are 3840x2160 10-bit
  H.264 whose real cadence is about 24 pictures a second under a 60 fps header, so they are cut by timestamps, never by
  frame count: each output frame shows the clip picture on screen at its clip time (the last picture whose presentation
  time is at or before it), clip_time = song_time - clip_song_start - lag. Pictures are decoded once (BT.709, limited
  range), downscaled with Lanczos to 2304x1296 (1.2x the 1080p output, room for the push-ins) and stored as 4:4:4 JPEG.
- s010 (MO05): the red tail lights of the traffic pulled to orange (selective hue); s007 (MO04): the same move on the
  red signal reflected in the wet pavement. Her ear lamp and collar line stay red: the shift is held off inside her
  matte (u2netp, grown and feathered).
- media/plates/<pid>-bg.jpg / -fg.png: the 2.5D layers of the four plates (s009, s011, s013, s014): her matte (u2netp,
  the salient figure) cut out as the foreground (RGBA), and the background with the figure filled from its surround
  (push-pull fill), so the two layers can move apart without a hole.
- media/plates/p011-rows.png: the fluorescent tubes of s011 in four depth bands (R far .. A near), feathered, for the
  row-by-row snap-on done in the engine.
- data/media.json: per shot its frame map (output frame -> clip picture index and pts), the input SHA-256s, the
  sticker track of s008 (the blank name sticker, found per frame as the bright neutral patch at lower right).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, FPS, OFFSET, SHOTS, V4, frame_of  # noqa: E402

SEQ_W, SEQ_H = 2304, 1296
U2NETP = Path.home() / ".local/state/jianji-hybrid-repair-20261006/matting-reference/u2netp.onnx"
U2NETP_SHA = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8"
_sess = None


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def matte(rgb: np.ndarray) -> np.ndarray:
    """u2netp salient-object matte (0..1) at the image's own size."""
    global _sess
    if _sess is None:
        if sha(U2NETP) != U2NETP_SHA:
            raise SystemExit("u2netp.onnx sha mismatch")
        _sess = ort.InferenceSession(str(U2NETP), providers=["CPUExecutionProvider"])
    h, w = rgb.shape[:2]
    x = np.asarray(Image.fromarray(rgb).resize((320, 320), Image.BICUBIC), np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    o = _sess.run(None, {_sess.get_inputs()[0].name: x})[0][0, 0]
    o = (o - o.min()) / (o.max() - o.min() + 1e-6)
    m = np.asarray(Image.fromarray((o * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    return np.clip((m - 0.2) / 0.6, 0, 1)


def grow(m: np.ndarray, px: int) -> np.ndarray:
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * px + 1)), np.float32) / 255


def feather(m: np.ndarray, r: float) -> np.ndarray:
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


# ---------------------------------------------------------------- clips
def probe_pts(clip: Path) -> list[float]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "frame=best_effort_timestamp_time", "-of", "csv=p=0", str(clip)],
                         capture_output=True, text=True, check=True).stdout
    return [float(x.strip().strip(",")) for x in out.split() if x.strip().strip(",")]


def decode(clip: Path, wanted: set[int]):
    """Yield (index, rgb uint8 SEQ_HxSEQ_Wx3) in presentation order for the wanted picture indices."""
    vf = (f"scale={SEQ_W}:{SEQ_H}:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix=bt709:in_range=tv:"
          f"out_range=pc,format=rgb24")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(clip), "-vf", vf, "-vsync", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = SEQ_W * SEQ_H * 3
    i = 0
    last = max(wanted)
    while i <= last:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        if i in wanted:
            yield i, np.frombuffer(buf, np.uint8).reshape(SEQ_H, SEQ_W, 3)
        i += 1
    p.stdout.close()
    p.kill()
    p.wait()


def rgb_to_hsv(a: np.ndarray):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def hsv_to_rgb(h, s, v):
    h = (h % 360) / 60.0
    c = v * s
    x = c * (1 - np.abs(h % 2 - 1))
    z = np.zeros_like(h)
    i = np.floor(h).astype(int) % 6
    r = np.choose(i, [c, x, z, z, x, c])
    g = np.choose(i, [x, c, c, x, z, z])
    b = np.choose(i, [z, z, x, c, c, x])
    m = v - c
    return np.stack([r + m, g + m, b + m], -1)


def tail_lights_to_orange(rgb: np.ndarray, sat_lo: float = 0.30, v_lo: float = 0.12) -> tuple[np.ndarray, dict]:
    """Rotate saturated reds (hue within ~24 deg of 0) to orange (+30 deg), except inside her matte (grown 2.5% of the
    frame width, feathered), where her ear lamp and collar line stay red."""
    a = rgb.astype(np.float32) / 255
    h, s, v = rgb_to_hsv(a)
    dh = np.minimum(np.abs(h), np.abs(360 - h))
    w = np.clip((26 - dh) / 10, 0, 1) * np.clip((s - sat_lo) / 0.2, 0, 1) * np.clip((v - v_lo) / 0.1, 0, 1)
    small = np.asarray(Image.fromarray(rgb).resize((SEQ_W // 2, SEQ_H // 2), Image.BILINEAR))
    her = matte(small)
    her = grow((her > 0.35).astype(np.float32), int(0.025 * SEQ_W / 2))
    her = feather(her, 6)
    her = np.asarray(Image.fromarray((her * 255).astype(np.uint8)).resize((SEQ_W, SEQ_H), Image.BILINEAR), np.float32) / 255
    w = w * (1 - her)
    hn = np.where(h > 180, h - 360, h) + 30.0 * w
    out = hsv_to_rgb(hn % 360, s, v)
    out = a * (1 - w[..., None]) + out * w[..., None]
    stats = {"shifted_px": int((w > 0.5).sum()), "kept_red_px_in_matte": int(((dh < 20) & (s > 0.45) & (v > 0.25) & (her > 0.5)).sum())}
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), stats


# the blank name sticker of s008 on one picture (normalised x0, y0, x1, y1, read off picture 14 of SG02 at 2304x1296)
STICKER = (0.7865, 0.8526, 0.9036, 0.9406)


def track_sticker(frames: list[np.ndarray]) -> list[list[float]]:
    """The sticker followed through the shot: its patch on the middle picture matched (sum of squared differences on a
    half-size grey image, +-40 px, then +-2 px at full step) on every picture; the box moves by the match."""
    g = [np.asarray(Image.fromarray(f).convert("L").resize((SEQ_W // 2, SEQ_H // 2), Image.BILINEAR), np.float32) for f in frames]
    ref = g[len(g) // 2]
    x0, y0, x1, y1 = (int(STICKER[0] * SEQ_W / 2), int(STICKER[1] * SEQ_H / 2), int(STICKER[2] * SEQ_W / 2),
                      int(STICKER[3] * SEQ_H / 2))
    tpl = ref[y0:y1, x0:x1] - ref[y0:y1, x0:x1].mean()
    out = []
    for im in g:
        best = (1e30, 0, 0)
        for dy in range(-20, 21, 2):
            for dx in range(-20, 21, 2):
                p = im[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
                if p.shape != tpl.shape:
                    continue
                e = float(((p - p.mean() - tpl) ** 2).mean())
                if e < best[0]:
                    best = (e, dx, dy)
        _, bx, by = best
        for dy in range(by - 2, by + 3):
            for dx in range(bx - 2, bx + 3):
                p = im[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
                if p.shape != tpl.shape:
                    continue
                e = float(((p - p.mean() - tpl) ** 2).mean())
                if e < best[0]:
                    best = (e, dx, dy)
        _, dx, dy = best
        out.append([round(STICKER[0] + 2 * dx / SEQ_W, 4), round(STICKER[1] + 2 * dy / SEQ_H, 4),
                    round(STICKER[2] + 2 * dx / SEQ_W, 4), round(STICKER[3] + 2 * dy / SEQ_H, 4)])
    return out


def remove_logos(frames: list[np.ndarray], times: list[float], seeds: list[dict]) -> list[dict]:
    """Blot the laptop logos of a clip. Each logo has keyframes (clip time, x, y in 1920 px) read off the footage, the
    sign of its contrast with the lid (a dark apple on a silver lid: -1; a light one on a dark lid: +1) and the lid's
    luminance range. Per picture the position is interpolated between keyframes, refined to the logo's own blob (the
    extremum of a difference of Gaussians of that sign within +-9 px), and the disc (radius r) is refilled from its
    surround (push-pull), feathered. A picture is skipped where the surround is her skin (her leg passing in front). Returns per logo and picture what was done."""
    S = SEQ_W / 1920
    log = []
    for sd in seeds:
        r = sd.get("r", 12) * S
        rb = sd.get("blot", 1.7 * sd.get("r", 12)) * S          # the blot is wider than the logo: the keyframes are hand-read
        ks = sorted(sd["keys"])
        for i, f in enumerate(frames):
            t = times[i]
            if t <= ks[0][0]:
                x, y = ks[0][1], ks[0][2]
            elif t >= ks[-1][0]:
                x, y = ks[-1][1], ks[-1][2]
            else:
                j = max(n for n in range(len(ks)) if ks[n][0] <= t)
                a_, b_ = ks[j], ks[j + 1]
                u = (t - a_[0]) / (b_[0] - a_[0])
                x, y = a_[1] + (b_[1] - a_[1]) * u, a_[2] + (b_[2] - a_[2]) * u
            x, y = x * S, y * S
            R = int(max(4 * r, 2.2 * rb))
            x0, y0 = int(x) - R, int(y) - R
            sub = f[max(0, y0):y0 + 2 * R, max(0, x0):x0 + 2 * R].astype(np.float32)
            if sub.shape[0] < 2 * R or sub.shape[1] < 2 * R:
                log.append({"logo": sd["name"], "pic": i, "t": round(t, 3), "blotted": False, "why": "edge"})
                continue
            L = sub @ np.array([0.2126, 0.7152, 0.0722], np.float32) / 255
            g1 = np.asarray(Image.fromarray((L * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r * 0.35)), np.float32) / 255
            g2 = np.asarray(Image.fromarray((L * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r * 1.2)), np.float32) / 255
            dog = (g1 - g2) * sd["sign"]
            win = int(sd.get("win", 14) * S)             # v2c: a small window keeps the refinement off a lid's rim
            c0 = R
            w_ = dog[c0 - win:c0 + win + 1, c0 - win:c0 + win + 1]
            dy, dx = np.unravel_index(int(np.argmax(w_)), w_.shape)
            cx, cy = dx - win + c0, dy - win + c0
            yy, xx = np.mgrid[0:2 * R, 0:2 * R]
            d = np.hypot(xx - cx, yy - cy)
            ring = (d > r * 1.6) & (d < r * 2.6)
            rl = L[ring]
            sat = (sub.max(-1) - sub.min(-1))[ring] / 255
            lo, hi = sd["lid"]
            # skipped only where her leg passes in front: the disc and its ring turn warm and saturated (skin); a hand
            # or a sleeve at the lid's edge does not stop the blot
            disc = d < r * 2.0
            dsat = (sub.max(-1) - sub.min(-1))[disc] / 255
            warm = float(np.median(sub[disc][:, 0] - sub[disc][:, 2])) / 255
            lid = not (float(np.median(dsat)) > 0.14 and warm > 0.06)
            if lid:
                hole = (d < rb).astype(np.float32)
                fill = push_pull(sub, hole)
                wgt = np.clip((rb + 4 - d) / 4, 0, 1)[..., None]
                f[y0:y0 + 2 * R, x0:x0 + 2 * R] = np.clip(sub * (1 - wgt) + fill * wgt, 0, 255).astype(np.uint8)
            log.append({"logo": sd["name"], "pic": i, "t": round(t, 3), "x": round((x0 + cx) / S, 1), "y": round((y0 + cy) / S, 1),
                        "contrast": round(float(w_.max()), 3), "ring_lum": round(float(np.median(rl)), 3), "blotted": bool(lid)})
    return log


def prep_clip(shot: dict, out: Path) -> dict:
    clip = V4 / shot["clip"]
    pts = probe_pts(clip)
    if sorted(pts) != pts:
        raise SystemExit(f"{shot['id']}: frame times not monotonic in presentation order")
    f0, f1 = frame_of(shot["t0"]), frame_of(shot["t1"])
    start = shot["clip_song_start"] + shot.get("lag", 0.0)
    # the pictures are a steady 24 a second whose times were rounded onto the 1/60 s grid of the header: picture k is
    # the instant k/24 (checked below), so an output frame at clip time c shows picture round(24 c) (clamped)
    rate = 24.0
    worst = max(abs(p - k / rate) for k, p in enumerate(pts))
    if worst > 1 / 120 + 1e-3:
        raise SystemExit(f"{shot['id']}: pictures are not a steady 24/s (worst offset {worst:.4f} s)")
    fmap = []
    for f in range(f0, f1):
        c = OFFSET + f / FPS - start
        idx = min(len(pts) - 1, max(0, int(round(c * rate))))
        fmap.append({"f": f, "clip_t": round(c, 4), "idx": idx, "pts": pts[idx], "t_pic": round(idx / rate, 4)})
    wanted = {m["idx"] for m in fmap}
    d = out / "seq" / shot.get("media_id", shot["id"])
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cache, extra = {}, {}
    for i, rgb in decode(clip, wanted):
        if shot.get("tail_lights_to_orange"):
            rgb, st = tail_lights_to_orange(rgb, *shot.get("orange_thresholds", (0.30, 0.12)))
            extra.setdefault("hue", {})[i] = st
        cache[i] = rgb.copy()
    missing = wanted - set(cache)
    if missing:
        raise SystemExit(f"{shot['id']}: pictures not decoded: {sorted(missing)[:5]}")
    logo_log = None
    if shot.get("logos"):
        idxs = sorted(cache)
        frames = [cache[i] for i in idxs]
        logo_log = remove_logos(frames, [i / 24.0 for i in idxs], shot["logos"])
        for i, fimg in zip(idxs, frames):
            cache[i] = fimg
    for k, m in enumerate(fmap):
        Image.fromarray(cache[m["idx"]]).save(d / f"{k:04d}.jpg", quality=93, subsampling=0)
    track = track_sticker([cache[m["idx"]] for m in fmap]) if shot.get("track") == "sticker" else None
    gaps = [round(b - a, 4) for a, b in zip(pts, pts[1:])]
    return {"clip": shot["clip"], "clip_sha256": sha(clip), "pictures": len(pts),
            "cadence_fps": round((len(pts) - 1) / (pts[-1] - pts[0]), 3), "max_gap": max(gaps),
            "clip_song_start": shot["clip_song_start"], "lag": shot.get("lag", 0.0), "frames": len(fmap),
            "first": fmap[0], "last": fmap[-1], "repeats": sum(1 for a, b in zip(fmap, fmap[1:]) if a["idx"] == b["idx"]),
            "skips": sum(1 for a, b in zip(fmap, fmap[1:]) if b["idx"] - a["idx"] > 1),
            "map": [m["idx"] for m in fmap], "worst_pts_offset": round(worst, 4), "track": track, "logos": logo_log,
            "hue": {str(k): v for k, v in extra.get("hue", {}).items()} or None}


# ---------------------------------------------------------------- plates
def push_pull(rgb: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """Fill hole (1 = unknown) from its surround: a pyramid of weighted averages, pulled back up."""
    w = (1 - hole).astype(np.float32)
    levels = [(rgb.astype(np.float32) * w[..., None], w)]
    while min(levels[-1][1].shape) > 2:
        c, ww = levels[-1]
        h2, w2 = (c.shape[0] // 2) * 2, (c.shape[1] // 2) * 2
        c, ww = c[:h2, :w2], ww[:h2, :w2]
        c = c.reshape(h2 // 2, 2, w2 // 2, 2, 3).sum((1, 3))
        ww = ww.reshape(h2 // 2, 2, w2 // 2, 2).sum((1, 3))
        levels.append((c, ww))
    fill = levels[-1][0] / np.maximum(levels[-1][1], 1e-6)[..., None]
    for c, ww in reversed(levels[:-1]):
        up = np.asarray(Image.fromarray(np.clip(fill, 0, 255).astype(np.uint8)).resize((c.shape[1], c.shape[0]), Image.BILINEAR), np.float32)
        own = c / np.maximum(ww, 1e-6)[..., None]
        k = np.clip(ww, 0, 1)[..., None]
        fill = own * k + up * (1 - k)
    out = rgb.astype(np.float32).copy()
    hh, wh = fill.shape[:2]
    out[:hh, :wh] = rgb[:hh, :wh] * (1 - hole[:hh, :wh, None]) + fill * hole[:hh, :wh, None]
    return out


def prep_plate(pid: str, out: Path) -> dict:
    src = V4 / "board/plates" / f"{pid}.png"
    rgb = np.asarray(Image.open(src).convert("RGB"))
    m = matte(rgb)
    alpha = feather(np.clip((m - 0.1) / 0.8, 0, 1), 1.2)
    hole = (grow((m > 0.08).astype(np.float32), 14) > 0.5).astype(np.float32)
    bg = push_pull(rgb, hole)
    bg = np.asarray(Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    bg = np.where(hole[..., None] > 0, bg, rgb)
    d = out / "plates"
    d.mkdir(parents=True, exist_ok=True)
    Image.fromarray(bg.astype(np.uint8)).save(d / f"{pid}-bg.jpg", quality=94, subsampling=0)
    fg = np.dstack([rgb, (alpha * 255 + 0.5).astype(np.uint8)])
    Image.fromarray(fg, "RGBA").save(d / f"{pid}-fg.png")
    ys, xs = np.nonzero(alpha > 0.5)
    return {"plate": f"board/plates/{pid}.png", "sha256": sha(src), "size": [rgb.shape[1], rgb.shape[0]],
            "fg_box": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
            "fg_cover": round(float(alpha.mean()), 4)}


def prep_rows(out: Path, src: Path | None = None, name: str = "p011", top: float = 0.42, sat_max: float = 0.18,
              lum_min: float = 0.72, exclude_x: tuple[int, int] | None = None) -> dict:
    """The tube rows as four bands far->near (R,G,B,A). A tube is a bright, low-saturation run in the ceiling
    (upper `top` of the plate, outside `exclude_x`: her white jacket); rows are the y runs of the horizontal
    projection, ordered bottom (far) to top (near)."""
    rgb = np.asarray(Image.open(src or V4 / "board/plates/p011.png").convert("RGB")).astype(np.float32) / 255
    H, W = rgb.shape[:2]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    sat = rgb.max(-1) - rgb.min(-1)
    tube = (lum > lum_min) & (sat < sat_max)
    tube[int(top * H):] = False
    if exclude_x:
        tube[:, exclude_x[0]:exclude_x[1]] = False
    proj = tube.sum(1)
    on = proj > 6
    runs, y = [], 0
    while y < H:
        if on[y]:
            y1 = y
            while y1 + 1 < H and on[y1 + 1]:
                y1 += 1
            runs.append((y, y1))
            y = y1 + 1
        else:
            y += 1
    runs = [r for r in runs if r[1] - r[0] >= 1]
    runs.sort(key=lambda r: -r[0])                                   # far (lower on screen) first
    bands = np.array_split(np.arange(len(runs)), 4)
    mask = np.zeros((H, W, 4), np.float32)
    for b, idx in enumerate(bands):
        m = np.zeros((H, W), np.float32)
        for i in idx:
            y0, y1 = runs[i]
            m[max(0, y0 - 2):y1 + 3] = tube[max(0, y0 - 2):y1 + 3]
        m = feather(grow(m, 3), 5.0)
        mask[..., b] = np.clip(m * 1.6, 0, 1)
    d = out / "plates"
    d.mkdir(parents=True, exist_ok=True)
    Image.fromarray((mask * 255 + 0.5).astype(np.uint8), "RGBA").save(d / f"{name}-rows.png")
    return {"runs": [[int(a), int(b)] for a, b in runs], "bands": [[int(i) for i in idx] for idx in bands]}


def main() -> int:
    out = EXC / "media"
    out.mkdir(exist_ok=True)
    if "--v2c" in sys.argv:
        # opening v2c: s014 = MO07 r6-2 in one span (edl.S014_V2C) -> media/seq/s014r6, data/media-v2c.json
        from edl import S014_V2C
        meta_p = EXC / "data/media-v2c.json"
        if meta_p.exists() or (out / "seq" / S014_V2C["media_id"]).exists():
            raise SystemExit("v2c media exist (not overwritten)")
        meta = {"shots": {S014_V2C["media_id"]: prep_clip(S014_V2C, out)}}
        meta_p.write_text(json.dumps(meta, indent=1))
        m = meta["shots"][S014_V2C["media_id"]]
        print({k: m[k] for k in ("frames", "first", "last", "repeats", "skips")}, flush=True)
        return 0
    if "--v4r7" in sys.argv:
        from edl import SHOTS_V4R7
        meta_p = EXC / "data/media-v4r1.json"
        meta = json.loads(meta_p.read_text())
        want = [a for a in sys.argv[2:] if not a.startswith("--")]
        for s_ in SHOTS_V4R7:
            mid = s_.get("media_id", s_["id"])
            if s_.get("clip") and s_["id"] not in ("s012b", "s012c") and (not want or mid in want):
                meta["shots"][mid] = prep_clip(s_, out)
                meta_p.write_text(json.dumps(meta, indent=1))
                print(mid, "done", {k: meta["shots"][mid][k] for k in ("frames", "first", "last")}, flush=True)
        return 0
    if "--v4r6" in sys.argv:
        # the d1 close-up, prepared into the same media file the v4 rounds read
        from edl import SHOTS_V4R6
        meta_p = EXC / "data/media-v4r1.json"
        meta = json.loads(meta_p.read_text())
        s_ = next(x for x in SHOTS_V4R6 if x["id"] == "s012c")
        meta["shots"]["s012c"] = prep_clip(s_, out)
        meta_p.write_text(json.dumps(meta, indent=1))
        print("s012c done", {k: meta["shots"]["s012c"][k] for k in ("frames", "first", "last", "repeats", "skips")})
        return 0
    if "--v4r1" in sys.argv:
        from edl import SHOTS_V4R1
        meta_p = EXC / "data/media-v4r1.json"
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else {"shots": {}}
        for s_ in SHOTS_V4R1:
            if s_.get("clip") and (len(sys.argv) <= 2 or s_["id"] in sys.argv):
                meta["shots"][s_["id"]] = prep_clip(s_, out)
                print(s_["id"], "done", flush=True)
        meta_p.write_text(json.dumps(meta, indent=1))
        return 0
    if "--v3" in sys.argv:
        from edl import STILLS_W1, W1_LAMP
        # W1 has no collar line: red is only her ear lamp. Other reds in the stills (a tail light, a city light, a
        # reflection) are pulled to orange like v1's tail lights; a disc round her lamp (edl.W1_LAMP) is held off.
        dst = out / "stills-w1"
        dst.mkdir(parents=True, exist_ok=True)
        stats = {}
        for p in sorted(STILLS_W1.glob("X*.png")):
            rgb = np.asarray(Image.open(p).convert("RGB"))
            H_, W_ = rgb.shape[:2]
            a = rgb.astype(np.float32) / 255
            h, s, v = rgb_to_hsv(a)
            dh = np.minimum(np.abs(h), np.abs(360 - h))
            w = np.clip((26 - dh) / 10, 0, 1) * np.clip((s - 0.3) / 0.2, 0, 1) * np.clip((v - 0.12) / 0.1, 0, 1)
            keep = np.zeros((H_, W_), np.float32)
            if p.stem in W1_LAMP:
                cx, cy, r = W1_LAMP[p.stem]
                yy, xx = np.mgrid[0:H_, 0:W_]
                keep = np.clip((r + 12 - np.hypot(xx - cx, yy - cy)) / 12, 0, 1)
            w = w * (1 - keep)
            hn = np.where(h > 180, h - 360, h) + 30.0 * w
            o = hsv_to_rgb(hn % 360, s, v)
            o = a * (1 - w[..., None]) + o * w[..., None]
            Image.fromarray((np.clip(o, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst / p.name)
            stats[p.stem] = {"source_sha256": sha(p), "shifted_px": int((w > 0.5).sum()), "out_sha256": sha(dst / p.name)}
        meta = prep_rows(out, STILLS_W1 / "X11a.png", "X11a-w1", top=0.62, sat_max=0.4, lum_min=0.62, exclude_x=(620, 1010))
        (EXC / "data/media-v3.json").write_text(json.dumps({"rows": meta, "reds_to_orange": stats}, indent=1))
        print(meta)
        return 0
    if "--v2" in sys.argv:
        # v2 needs only the X11a rows mask (stills are used as they are)
        from edl import STILLS
        meta = prep_rows(out, STILLS / "X11a.png", "X11a", top=0.62, sat_max=0.4, lum_min=0.62, exclude_x=(630, 1010))
        (EXC / "data/media-v2.json").write_text(json.dumps({"rows": meta}, indent=1))
        print(meta)
        return 0
    only = set(sys.argv[1:])
    meta_p = EXC / "data/media.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {"shots": {}, "plates": {}}
    meta["u2netp"] = {"path": str(U2NETP), "sha256": U2NETP_SHA}
    for s in SHOTS:
        if only and s["id"] not in only:
            continue
        if s["kind"] == "clip":
            meta["shots"][s["id"]] = prep_clip(s, out)
        else:
            meta["plates"][s["plate"]] = prep_plate(s["plate"], out)
            if s["plate"] == "p011":
                meta["rows"] = prep_rows(out)
        print(s["id"], "done", flush=True)
    meta_p.parent.mkdir(exist_ok=True)
    meta_p.write_text(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
