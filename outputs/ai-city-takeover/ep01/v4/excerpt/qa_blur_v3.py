#!/usr/bin/env python3
"""IRIS EP01 opening v3: every shot's blur class measured with EV's own measurement (blur_study/work: metrics.py's
sigma_e at 480 wide on the strongest 10 % of edges, analyze_ev_common's chrome mask, classify.py's rule), on the picture
render (song frame n = picture frame n). Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa_blur_v3.py --picture <mp4 | dir of fNNNN.png> --out <dir> [--figures]

Per shot: three samples (mid - 6, mid, mid + 6, inside the shot; s012a split into its two stills as blur_study did),
face / subject / background sigma_e (1920 px), tone p2 / p98, subject motion to the next frame (phase correlation in
the subject box, x4; not measured where the correlation peak is under 0.2: the grain's own motion on a defocused still), the median over the samples, the class by classify.py, against the target class (opening_v2.py
BLUR_OPEN / BLUR_CHORUS) and EV's class range (shots_ev.csv, 68 shots). The smear shots also get their peak frames
measured (C rows "@peak": the frames prep_blur_v3.py smeared at full gain). Boxes: the v4r11 shots keep blur_study's
ours_annot.py; the opening shots and s014's two pieces are read off the v3 frames (fractions x0, y0, x1, y1).

Writes <out>/blur_v3.json, <out>/blur_v3.md (table) and with --figures <out>/pair_<class>_*.jpg (EV | IRIS rows as
blur_study's figures: frame, 2x face/subject crop, 2x background crop, NEAREST from the full-resolution frame).
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BS = Path("outputs/anabology-opus55-replica/escape_velocity_analysis/blur_study").resolve()
sys.path.insert(0, str(BS / "work"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402
from analyze_ev_common import CHROME, SH, med, xyxy  # noqa: E402
from classify import classify  # noqa: E402
import ours_annot  # noqa: E402

arg = lambda k: sys.argv[sys.argv.index(k) + 1]
PIC, OUT = Path(arg("--picture")), Path(arg("--out"))
W, H = 1920, 1080
OA = ours_annot.A
# (id, f0, f1, cat, subject box, face box, target class); song frames
SHOTS = [
    ("s001", 0, 99, "face", (0.15, 0.0, 1.0, 1.0), (0.53, 0.0, 0.92, 0.62), "A"),
    ("s002", 99, 231, "full", (0.42, 0.0, 0.62, 0.97), (0.48, 0.0, 0.56, 0.13), "B"),
    ("s003", 231, 307, "medium", (0.0, 0.12, 0.47, 1.0), (0.08, 0.15, 0.27, 0.45), "B"),
    ("s004", 307, 406, "medium", (0.45, 0.0, 0.90, 1.0), (0.61, 0.03, 0.75, 0.34), "A"),
    ("s005", 406, 493, "face", (0.40, 0.0, 1.0, 1.0), (0.55, 0.0, 0.92, 0.68), "B"),
    ("s006", 493, 625, "medium", (0.40, 0.05, 0.95, 1.0), (0.47, 0.07, 0.70, 0.45), "C"),
    ("s007", 625, 714, "full", (0.44, 0.0, 0.80, 1.0), (0.55, 0.0, 0.66, 0.16), "E"),
    ("s008", 714, 791, "face", (0.20, 0.0, 0.85, 1.0), (0.34, 0.0, 0.62, 0.52), "A"),
    ("s009", 791, 869, "medium", (0.08, 0.0, 0.62, 1.0), (0.33, 0.12, 0.55, 0.42), "B"),     # her body; the reaching arm goes toward the board
    ("s010", 869, 956, "medium", (0.37, 0.10, 1.0, 1.0), (0.43, 0.12, 0.58, 0.38), "A"),
    ("s011", 979, 1078, *OA["s011"], "A"),
    ("s012a_hand", 1078, 1100, *OA["s012a_hand"], "B"),
    ("s012a", 1100, 1123, *OA["s012a"], "B"),
    ("s012b", 1123, 1178, *OA["s012b"], "A"),
    ("s012c", 1178, 1211, *OA["s012c"], "D"),
    ("s012d", 1211, 1222, *OA["s012d"], "A"),
    ("s013a", 1222, 1255, *OA["s013a"], "B"),
    ("s013b", 1255, 1322, *OA["s013b"], "A"),
    ("s014p", 1322, 1366, "medium", (0.27, 0.0, 0.73, 1.0), (0.40, 0.12, 0.60, 0.40), "A"),
    ("s014a", 1366, 1410, "full", (0.50, 0.06, 0.72, 1.0), None, "C"),
    ("s014c", 1410, 1422, *OA["s014c"], "D"),
]
# the smear peaks: s006 the picture after a flash pop or a jolt (prep_blur_v3.py envelope gain 1), the six with the
# largest camera motion; s014a the turn and the sleeve (r6-2 pictures 46-52, gain 2.5), her box there (0.42-0.64)
PEAKS = {"s006": [], "s014a": [1368, 1371, 1374]}
PEAK_BOX = {"s014a": (0.42, 0.03, 0.64, 1.0)}
# at the peaks her place changes frame to frame (s006 is handheld): the subject box per frame from her u2netp matte on
# the clean prepared picture the frame shows (same geometry: the shot shows the whole picture), the face box its top 30 %
PEAK_SRC = {"s006": ("outputs/ai-city-takeover/ep01/v4/excerpt/media/seq/o006", 493),
            "s014a": ("outputs/ai-city-takeover/ep01/v4/excerpt/media/seq/s014r6", 1322)}


def matte_boxes(sid, k):
    import prep_media
    d, f0 = PEAK_SRC[sid]
    m = prep_media.matte(np.asarray(Image.open(f"{d}/{k - f0:04d}.jpg").convert("RGB"))) > 0.5
    ys, xs = np.nonzero(m)
    h, w = m.shape
    x0, x1, y0, y1 = xs.min() / w, xs.max() / w, ys.min() / h, ys.max() / h
    return (x0, y0, x1, y1), (x0, y0, x1, y0 + 0.3 * (y1 - y0))


def peaks_s006() -> list[int]:
    p = Path("outputs/ai-city-takeover/ep01/v4/excerpt/data/blur-v3.json")
    if not p.exists():
        return []
    m = json.loads(p.read_text()).get("s006", {})
    mot = {x["pic"]: x["motion_p90_px"] for x in m.get("smeared", [])}
    pk = [i + 1 for i in m.get("impacts", []) if i + 2 < 132 and i + 1 in mot]
    return sorted(493 + i for i in sorted(pk, key=lambda i: -mot[i])[:6])


def samples(a, z):
    b = z - 1
    mid = (a + b) // 2
    lo, hi = (a + 1, b - 1) if b - a >= 4 else (a, b)
    return sorted({min(max(x, lo), hi) for x in (mid - 6, mid, mid + 6)})


def load_frames(need: set[int]) -> dict[int, np.ndarray]:
    out = {}
    if PIC.is_dir():
        for f in need:
            p = PIC / f"f{f:04d}.png"
            if p.exists():
                out[f] = np.asarray(Image.open(p).convert("RGB"))
        return out
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(PIC), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        if n in need:
            out[n] = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        n += 1
    p.wait()
    return out


def luma(rgb):
    a = rgb.astype(np.float32)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def measure(fr: dict, ks: list[int], cat, subj, face, valid, per_frame=None) -> dict:
    rows = []
    for k in ks:
        if k not in fr:
            continue
        if per_frame:
            subj, face = per_frame(k)
        a = M.down(luma(fr[k]))
        P = M.Pyr(a)
        r = {"k": k, "full": P.esr(valid), "tone": M.tone(a, valid)}
        sm = M.box_mask(SH, [xyxy(subj)]) & valid
        bm = valid & ~M.box_mask(SH, [xyxy(subj, 0.03)])
        r["subj"], r["bg"] = P.esr(sm), P.esr(bm)
        if face:
            r["face"] = P.esr(M.box_mask(SH, [xyxy(face)]) & valid, minpx=25)
        if k + 1 in fr:
            s = M.shift(a, M.down(luma(fr[k + 1])), M.box_mask(SH, [xyxy(subj)]))
            # a correlation peak under 0.2 is no match: on a defocused still the engine's grain (main.js FINAL: its noise
            # field moves by (46.4, 21.6) px a frame) is the only structure left and the correlation locks onto it
            r["move"] = None if s is None or s[2] < 0.2 else float(4 * np.hypot(s[0], s[1]))
            r["move_peak"] = None if s is None else s[2]
        r["g240m"] = M.grad_view_masked(a, valid)
        rows.append(r)
    g = lambda key: med([(r.get(key) or {}).get("se") for r in rows])
    v = {"cat": cat, "se_face": g("face"), "se_subj": g("subj"), "se_bg": g("bg"), "se_full": g("full"),
         "p2": med([(r["tone"] or {}).get("p2") for r in rows]), "p98": med([(r["tone"] or {}).get("p98") for r in rows]),
         "move_subj": med([r.get("move") for r in rows]), "g240m": med([r.get("g240m") for r in rows]), "samples": ks}
    return v


def ev_ranges() -> dict:
    R = list(csv.DictReader(open(BS / "shots_ev.csv")))
    out = {}
    num = lambda x: float(x) if x not in ("", None) else None
    for c in ("A", "B", "C", "C*", "D", "E"):
        rs = [r for r in R if r["class"] == c]
        def rng(key, cap=True):
            v = [num(r[key]) for r in rs if num(r[key]) is not None and (not cap or num(r[key]) < 90)]
            return [round(min(v), 1), round(float(np.median(v)), 1), round(max(v), 1)] if v else None
        out[c] = {"n": len(rs), "shots": [r["shot"] for r in rs], "main": rng("main_se"), "bg": rng("bg_se"),
                  "bg_over_main": rng("bg_over_main"), "p2": rng("p2", False), "p98": rng("p98", False), "move": rng("move_px_f")}
    return out


def in_range(cls, v, rng):
    """The measured class equals the target and the numbers sit in EV's class range (the rule's own thresholds)."""
    return v["class"] == cls or (cls == "C" and v["class"] in ("C", "C*"))


def f0(x):
    return "-" if x is None else f"{x:.0f}"


def f2(x):
    return "-" if x is None else f"{x:.2f}"


def f3(x):
    return "-" if x is None else f"{x:.3f}"


def f1(x):
    return "-" if x is None else ("flat" if x >= 90 else f"{x:.1f}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PEAKS["s006"] = peaks_s006()
    plan = {s[0]: samples(s[1], s[2]) for s in SHOTS}
    need = set()
    for ks in list(plan.values()) + list(PEAKS.values()):
        need |= set(ks) | {k + 1 for k in ks}
    fr = load_frames(need)
    valid = ~M.box_mask(SH, CHROME)
    res, rng = {}, ev_ranges()
    for sid, a, z, cat, subj, face, tgt in SHOTS:
        rows = [(sid, plan[sid])] + ([(f"{sid}@peak", PEAKS[sid])] if PEAKS.get(sid) else [])
        for name, ks in rows:
            sb = PEAK_BOX.get(sid, subj) if "@" in name else subj
            v = measure(fr, ks, cat, sb, face, valid, (lambda k, s_=sid: matte_boxes(s_, k)) if "@" in name else None)
            c, why = classify(v)
            main = v["se_face"] if cat in ("face", "medium") and v["se_face"] is not None and v["se_face"] < 90 else v["se_subj"]
            v.update({"frames": [a, z - 1], "target": tgt, "class": c, "rule": why, "main": main,
                      "bg_over_main": (v["se_bg"] / main) if (main and v["se_bg"] and v["se_bg"] < 90) else None,
                      "boxes": {"subj": sb, "face": face}})
            v["pass"] = in_range(tgt, v, rng)
            res[name] = v
    out = {"picture": str(PIC), "ev_class_ranges": rng, "shots": res,
           "counts": {c: sum(1 for k, v in res.items() if "@" not in k and v["class"] == c) for c in ("A", "B", "C", "C*", "D", "E", "B*", "?")}}
    (OUT / "blur_v3.json").write_text(json.dumps(out, indent=1))
    L = ["| 镜 | 帧 | 类型 | 目标 | 实测类 | main σ_e | 背景 σ_e | 背景/main | p2 | p98 | 运动 px/帧 | g240m | EV 该类范围 main / 背景 / 比值 | 结果 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in res.items():
        r = rng.get(v["target"]) or {}
        er = lambda x: "-" if not x else f"{x[0]}–{x[2]}"
        L.append(f"| {k} | {v['frames'][0]}–{v['frames'][1]} | {v['cat']} | {v['target']} | {v['class']} | {f1(v['main'])} | {f1(v['se_bg'])} | "
                 f"{f2(v['bg_over_main'])} | {f0(v['p2'])} | {f0(v['p98'])} | {f1(v['move_subj'])} | "
                 f"{f3(v['g240m'])} | {er(r.get('main'))} / {er(r.get('bg'))} / {er(r.get('bg_over_main'))} | {'PASS' if v['pass'] else 'FAIL'} |")
    (OUT / "blur_v3.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(json.dumps(out["counts"]))
    if "--figures" in sys.argv:
        figures(res, fr)
    return 0


GROUPS = [("A", "S0022", "s008"), ("A", "S0016", "s014p"), ("B", "S0014", "s005"), ("B", "S0061", "s003"), ("C", "S0064", "s014a@peak"),
          ("C-star", "S0058", "s006@peak"), ("D", "S0056", "s012c"), ("D", "S0049", "s014c"), ("E", "S0059", "s007")]


def figures(res: dict, fr: dict) -> None:
    from PIL import ImageDraw
    from make_panels import C, bg_point, crop2x, panel
    import ev_annot
    ev = json.load(open(BS / "work/ev_metrics.json")); evp = json.load(open(BS / "work/ev_plan.json"))
    bad = np.load(BS / "work/ev_badmask_mid.npz")
    for cls, e, o in GROUPS:
        v = res[o]
        sid = o.split("@")[0]
        ks = v["samples"]
        k = ks[len(ks) // 2]
        im = Image.fromarray(fr[k])
        subj, face = v["boxes"]["subj"], v["boxes"]["face"]
        box = face or subj
        c1, o1 = crop2x(im, (box[0] + box[2]) / 2 * W, (box[1] + box[3]) / 2 * H)
        bp = bg_point(im, subj)
        c2, o2 = crop2x(im, *bp) if bp else (Image.new("RGB", (2 * C, 2 * C), (30, 30, 30)), None)
        small = im.resize((960, 540), Image.LANCZOS); d = ImageDraw.Draw(small); s = 960 / W
        d.rectangle([subj[0] * 960, subj[1] * 540, subj[2] * 960, subj[3] * 540], outline=(0, 255, 0), width=2)
        if face:
            d.rectangle([face[0] * 960, face[1] * 540, face[2] * 960, face[3] * 540], outline=(255, 230, 0), width=2)
        d.rectangle([o1[0] * s, o1[1] * s, (o1[0] + C) * s, (o1[1] + C) * s], outline=(255, 0, 255), width=2)
        if o2:
            d.rectangle([o2[0] * s, o2[1] * s, (o2[0] + C) * s, (o2[1] + C) * s], outline=(0, 230, 255), width=2)
        P = Image.new("RGB", (960 + 4 * C + 12, 540 + 64), (20, 20, 20))
        P.paste(small, (0, 64)); P.paste(c1, (966, 64)); P.paste(c2, (966 + 2 * C + 6, 64))
        d = ImageDraw.Draw(P)
        d.text((6, 4), f"IRIS v3 {o}  song frame {k}  {v['cat']}  target {v['target']}  measured class {v['class']}", fill=(255, 255, 255))
        d.text((6, 20), f"sigma_e (1920 px): face {f1(v['se_face'])}  subject {f1(v['se_subj'])}  background {f1(v['se_bg'])}", fill=(210, 210, 210))
        d.text((6, 34), f"p2 {f0(v['p2'])}  p98 {f0(v['p98'])}  motion {f1(v['move_subj'])} px/f   rule: {v['rule']}", fill=(210, 210, 210))
        d.text((970, 48), "2x: face/subject (magenta box)", fill=(255, 0, 255)); d.text((970 + 2 * C + 6, 48), "2x: background (cyan box)", fill=(0, 230, 255))
        x = ev[e]; c, why = classify(x, e)
        tmp = OUT / f"_ev_{e}.jpg"
        panel(BS / "work/ev_mid" / f"f{evp[e]['mid']:05d}.jpg", ev_annot.A[e][1], ev_annot.A[e][2], f"EV {e}  {x['section']}  {x['cat']}  class {c}",
              [f"sigma_e (1920 px): face {f1(x['se_face'])}  subject {f1(x['se_subj'])}  background {f1(x['se_bg'])}",
               f"p2 {f1(x['p2'])}  p98 {f1(x['p98'])}  motion {f1(x.get('move_subj'))} px/f", f"rule: {why}"], tmp, bad[e])
        Q = Image.open(tmp)
        S = Image.new("RGB", (max(P.width, Q.width), P.height + Q.height + 8), (60, 60, 60))
        S.paste(Q, (0, 0)); S.paste(P, (0, Q.height + 8))
        S.save(OUT / f"pair_{cls}_{e}_vs_{sid}.jpg", quality=88)
        tmp.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
