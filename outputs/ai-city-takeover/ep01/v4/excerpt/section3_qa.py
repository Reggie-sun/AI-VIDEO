#!/usr/bin/env python3
"""QA of the IRIS EP01 s031-s048 v1 export (section2_qa.py's checks on section3.SHOTS). Run from the repo root, in parts
(each part writes <out>/part-<name>.json; --merge writes <out>/qa.json):

  Q="uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3_qa.py --film <export.mp4> --picture <picture.mp4> --out <dir>"
  $Q --only base            # spec, sound (offset / RMS vs the master's samples 134.4583-209.3333 s), cuts, flash
  $Q --only lips            # the lip spans used: picture = expected take picture; sync_check on the take's own sound
  $Q --only red --range a b # saturated red outside her grown matte, every 2nd frame of film frames a..b-1
  $Q --merge

Red: qa.red_mask on the film at 960x540; red outside her u2netp matte (grown 29 px) counted per frame. The door-crack
line of s039 is the user's exception (「留红光，和 s002 一样算例外」): red inside section3.KEEP_RED during s039a/s039b is
counted separately as `exception_px` and not as a failure. Pass: no frame with more than 12 px outside her and the mask.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import FPS, MASTER, REPO, V4  # noqa: E402
from prep_media import grow, matte  # noqa: E402
from qa import red_mask, transitions  # noqa: E402
from section3 import KEEP_RED, N, SF0, SF1, SHOTS, clip_time, frame_of, sha, take_path  # noqa: E402

ARG = lambda k: Path(sys.argv[sys.argv.index(k) + 1]).resolve()
FILM, PICTURE, OUT = ARG("--film"), ARG("--picture"), ARG("--out")
SW, SH = 480, 270
LIPS = ["s031a", "s031c", "s037b", "s037d", "s039a", "s039b", "s041a", "s041c", "s042", "s048"]
EXC_SHOTS = {"s039a", "s039b"}


def frames(src: Path, w: int, h: int, every: int = 1, start: int = 0, count: int | None = None):
    sel = f"select='gte(n\\,{start})*not(mod(n-{start}\\,{every}))'," if (every > 1 or start) else ""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:v", "-vf", f"{sel}scale={w}:{h}:flags=area", "-vsync", "0",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n, i = w * h * 3, 0
    while count is None or i < count:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        i += 1
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.stdout.close()
    p.kill()
    p.wait()


def spec() -> dict:
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries",
                                   "stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels",
                                   "-of", "json", str(FILM)], capture_output=True, text=True, check=True).stdout)["streams"]
    v = next(s for s in j if s["codec_type"] == "video")
    a = [s for s in j if s["codec_type"] == "audio"]
    return {"video": v, "audio": a, "pass": v["width"] == 1920 and v["height"] == 1080 and v["r_frame_rate"] == "24/1"
            and int(v["nb_read_frames"]) == N and bool(a)}


def read_wav(p: Path, t0: float = 0.0, dur: float | None = None):
    with wave.open(str(p)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        w.setpos(int(round(t0 * sr)))
        x = np.frombuffer(w.readframes(w.getnframes() if dur is None else int(round(dur * sr))), np.int16)
    return x.reshape(-1, ch).mean(1).astype(np.float64) / 32768, sr


def sound_against(film: Path, t0: float, dur: float, tmp: Path, film_t0: float = 0.0) -> dict:
    """the film's sound from film_t0 for dur against the master from t0 (48 kHz cross-correlation +-0.1 s)"""
    wav = tmp / f"film-{film.stem}.wav"
    if not wav.exists():                  # the whole sound decoded once from 0 (an input -ss skips the AAC edit list)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(film), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)], check=True)
    a, sr = read_wav(wav, film_t0, dur)
    b, sr2 = read_wav(MASTER, t0, dur)
    if sr2 != sr:
        raise SystemExit(f"master rate {sr2} != {sr}")
    n = min(len(a), len(b))
    m = int(0.2 * sr) if dur > 1 else 0
    x, y = a[m:n - m], b[m:n - m]
    corr = lambda L: float(np.dot(x[max(0, L):len(x) + min(0, L)], y[max(0, -L):len(y) - max(0, L)]))
    best = max(range(-4800, 4801, 8), key=corr)
    fine = max(range(best - 8, best + 9), key=corr)
    rms = lambda v: float(np.sqrt(np.mean(v ** 2)))
    db = 20 * np.log10(rms(a[:n]) / rms(b[:n]))
    return {"film_samples": len(a), "master_samples": len(b), "master_window_s": [t0, t0 + dur], "offset_samples": fine,
            "offset_ms": round(fine / sr * 1000, 3), "rms_diff_db": round(db, 3), "pass": abs(fine) <= sr / FPS and abs(db) <= 0.5}


def check_cuts(L: np.ndarray) -> dict:
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())["beats"]
    d = np.abs(np.diff(L, axis=0)).mean((1, 2))
    rows = []
    for s in SHOTS[1:]:
        t, fr = s["t0"], frame_of(s["t0"])
        nb = min(beats, key=lambda b: abs(b - t))
        peak = max(0, fr - 4) + int(np.argmax(d[max(0, fr - 4):fr + 3])) + 1
        ft = (SF0 + fr) / FPS
        rows.append({"cut": s["id"], "t": t, "frame": fr, "song_frame": SF0 + fr, "nearest_beat": nb, "cut_dt_beat": round(t - nb, 4),
                     "frame_dt_beat": round(ft - nb, 4), "picture_change_peak_frame": peak,
                     "pass": abs(ft - nb) <= 0.03 and abs(t - nb) <= 0.03})
    return {"cuts": rows, "pass": all(r["pass"] for r in rows), "change_peak_on_cut": sum(1 for r in rows if r["picture_change_peak_frame"] == r["frame"]),
            "n": len(rows)}


def check_flash(L: np.ndarray) -> dict:
    g = 4
    cells = L[:, :SH // g * g, :SW // g * g].reshape(L.shape[0], g, SH // g, g, SW // g).mean((2, 4)).reshape(L.shape[0], -1)
    per = []
    for c in range(cells.shape[1]):
        fl = [i for i, _ in transitions(cells[:, c])]
        for i in range(len(fl)):
            per.append((sum(1 for t in fl[i:] if t - fl[i] < FPS) / 2, c, fl[i]))
    per.sort(reverse=True)
    worst = per[0] if per else (0, None, None)
    cuts = {frame_of(s["t0"]) for s in SHOTS}
    D = np.abs(np.diff(L, axis=0)).mean((1, 2))
    singles = []
    for fr in range(1, len(L) - 1):
        if fr in cuts or fr + 1 in cuts:
            continue
        a, b = D[fr - 1], D[fr]
        if a > 0.02 and b > 0.02 and float(np.abs(L[fr + 1] - L[fr - 1]).mean()) < 0.4 * min(a, b):
            singles.append({"frame": fr, "song_t": round((SF0 + fr) / FPS, 3), "d_prev": round(float(a), 4), "d_next": round(float(b), 4)})
    return {"max_flashes_per_second_any_cell": worst[0], "at": {"cell": worst[1], "frame": worst[2]},
            "windows_over_3_per_second_start_frames": sorted({fr for n, _, fr in per if n > 3}), "single_frame_jumps": singles,
            "pass": worst[0] <= 3}


def shot_at(fr: int) -> str:
    return [s["id"] for s in SHOTS if frame_of(s["t0"]) <= fr][-1]


def check_red(a0: int, a1: int, every: int = 2) -> dict:
    rows = []
    red_map = np.zeros((540, 960), np.float32)
    x0, y0, x1, y1 = KEEP_RED
    exc = np.zeros((540, 960), bool)
    exc[int(y0 * 540):int(y1 * 540), int(x0 * 960):int(x1 * 960)] = True
    for i, fr in enumerate(frames(FILM, 960, 540, every, a0, (a1 - a0 + every - 1) // every)):
        k = a0 + i * every
        a = fr.astype(np.float32) / 255
        red = red_mask(a)
        row = {"frame": k, "red_px": int(red.sum()), "outside_her_px": 0, "exception_px": 0}
        if red.any():
            her = grow((matte(fr) > 0.3).astype(np.float32), 29) > 0.5
            bad = red & ~her
            if shot_at(k) in EXC_SHOTS:
                row["exception_px"] = int((bad & exc).sum())
                bad = bad & ~exc
            row["outside_her_px"] = int(bad.sum())
            red_map += bad
        rows.append(row)
    np.save(OUT / f"red-map-{a0}-{a1}.npy", red_map)
    return {"range": [a0, a1], "every": every, "rows": rows}


def take_pictures(clip: Path) -> np.ndarray:
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-map", "0:v", "-vf", "scale=160:90:flags=area,format=gray",
                        "-vsync", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, 90, 160).astype(np.float32)


def lips(tmp: Path) -> dict:
    grey = np.stack([fr.astype(np.float32).mean(-1) for fr in frames(PICTURE, 160, 90)])
    out = {}
    z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
    for sid in LIPS:
        s = next(x for x in SHOTS if x["id"] == sid)
        clip = take_path(s["src"])
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        pics = take_pictures(clip)
        offs = []
        for fr in range(f0, f1):
            exp = int(round(clip_time(s, (SF0 + fr) / FPS) * 24))
            cand = range(max(0, exp - 4), min(len(pics), exp + 5))
            sc = {k: float((z(grey[fr]) * z(pics[k])).mean()) for k in cand}
            offs.append(max(sc, key=sc.get) - exp)
        t0, dur = (SF0 + f0) / FPS, (f1 - f0) / FPS
        c0 = clip_time(s, t0)
        unit = clip.parents[5].name
        gate = json.loads((clip.parents[5] / f"gate/{unit}-sd/sync.json").read_text())
        take_wav, win_wav = tmp / f"{sid}-take.wav", tmp / f"{sid}-win.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, c0):.4f}", "-t", f"{dur:.4f}", "-i", str(clip), "-vn",
                        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(take_wav)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, t0 - gate['song_t0']):.4f}", "-t", f"{dur:.4f}", "-i", str(REPO / gate["window"]),
                        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(win_wav)], check=True)
        d = tmp / sid
        r = subprocess.run(["uv", "run", "python", str(REPO / "motion-kit/tools/sync_check.py"), "--take", str(take_wav), "--window", str(win_wav),
                            "--song-t0", f"{t0:.4f}", "--out", str(d), "--name", f"{sid}-film", "--words", str(V4 / "song/timing/words.json")],
                           capture_output=True, text=True, cwd=REPO)
        js = sorted(d.glob("**/sync.json"))
        sc = json.loads(js[0].read_text()) if js else {"error": r.stderr[-600:]}
        spans = sc.get("spans") or []
        t1 = (SF0 + f1) / FPS
        vis = [[max(a, t0), min(b, t1)] for a, b in (x["song_s"] for x in spans) if min(b, t1) > max(a, t0)]
        gspans = [[max(a, t0), min(b, t1)] for a, b in (x["song_s"] for x in gate.get("spans") or []) if min(b, t1) > max(a, t0)]
        out[sid] = {"take": s["src"], "take_sha256": sha(clip), "song": [round(t0, 4), round(t1, 4)], "clip_in": round(c0, 4),
                    "knots": s.get("knots"), "window": gate["window"], "gate_copy": gate.get("copy"), "gate_lag_s": gate.get("lag_s"),
                    "gate_spans_in_shot_song_s": [[round(a, 3), round(b, 3)] for a, b in gspans],
                    "picture_offset_vs_placement": {"0": offs.count(0), "nonzero": [o for o in offs if o], "frames": len(offs)},
                    "sync_check": {k: sc.get(k) for k in ("lag_s", "ncc", "copy", "synced_until", "spans", "divergence", "error")},
                    "visible_lip_synced_song_s": [[round(a, 3), round(b, 3)] for a, b in vis],
                    "covered_share": round(sum(b - a for a, b in vis) / dur, 3)}
    return out


def merge() -> dict:
    res = json.loads((OUT / "part-base.json").read_text())
    res["lips"] = json.loads((OUT / "part-lips.json").read_text())
    parts = sorted(OUT.glob("part-red-*.json"), key=lambda p: int(p.stem.split("-")[2]))
    rows = [r for p in parts for r in json.loads(p.read_text())["rows"]]
    have = sorted(r["frame"] for r in rows)
    want = list(range(0, N, 2))
    red_map = sum(np.load(OUT / f"red-map-{p.stem.split('-')[2]}-{p.stem.split('-')[3]}.npy") for p in parts)
    if red_map.max() > 0:
        Image.fromarray((np.clip(red_map / red_map.max(), 0, 1) * 255).astype(np.uint8)).save(OUT / "red-outside-map.png")
    per = {}
    for r in rows:
        sid = shot_at(r["frame"])
        p = per.setdefault(sid, {"frames": 0, "over_12": 0, "max_outside_px": 0, "at": None, "max_red_px": 0, "max_exception_px": 0})
        p["frames"] += 1
        p["over_12"] += r["outside_her_px"] > 12
        p["max_red_px"] = max(p["max_red_px"], r["red_px"])
        p["max_exception_px"] = max(p["max_exception_px"], r["exception_px"])
        if r["outside_her_px"] > p["max_outside_px"]:
            p["max_outside_px"], p["at"] = r["outside_her_px"], r["frame"]
    bad = [r["frame"] for r in rows if r["outside_her_px"] > 12]
    res["red"] = {"frames_checked": len(rows), "every": 2, "complete": have == want, "frames_with_red": sum(1 for r in rows if r["red_px"]),
                  "exception": {"shots": sorted(EXC_SHOTS), "box": KEEP_RED, "frames_with_exception_red": sum(1 for r in rows if r["exception_px"])},
                  "bad_frames": bad, "per_shot": per, "pass": not bad and have == want}
    np_ = lambda o: o.item() if hasattr(o, "item") else str(o)
    (OUT / "qa.json").write_text(json.dumps(res, indent=1, default=np_))
    return res


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    np_ = lambda o: o.item() if hasattr(o, "item") else str(o)
    if "--merge" in sys.argv:
        res = merge()
        print(json.dumps({k: res[k].get("pass") for k in ("spec", "sound", "cuts", "flash", "red")}, indent=1, default=np_))
        return 0
    only = sys.argv[sys.argv.index("--only") + 1]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if only == "base":
            res = {"film": str(FILM.relative_to(REPO)), "film_sha256": sha(FILM), "picture": str(PICTURE.relative_to(REPO)),
                   "picture_sha256": sha(PICTURE), "spec": spec(), "sound": sound_against(FILM, SF0 / FPS, N / FPS, tmp)}
            lin = lambda a: np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
            L = np.stack([lin(fr.astype(np.float32) / 255) @ np.array([0.2126, 0.7152, 0.0722], np.float32) for fr in frames(FILM, SW, SH)])
            res["flash"] = check_flash(L)
            P = np.stack([fr.astype(np.float32).mean(-1) / 255 for fr in frames(PICTURE, SW, SH)])
            res["cuts"] = check_cuts(P)
            (OUT / "part-base.json").write_text(json.dumps(res, indent=1, default=np_))
            print(json.dumps({k: res[k].get("pass") for k in ("spec", "sound", "cuts", "flash")}, default=np_), res["sound"]["offset_samples"],
                  res["flash"]["max_flashes_per_second_any_cell"])
        elif only == "lips":
            res = lips(tmp)
            (OUT / "part-lips.json").write_text(json.dumps(res, indent=1, default=np_))
            print(json.dumps({k: {"lag": v["sync_check"].get("lag_s"), "copy": v["sync_check"].get("copy"), "vis": v["visible_lip_synced_song_s"],
                                  "pic0": f"{v['picture_offset_vs_placement']['0']}/{v['picture_offset_vs_placement']['frames']}"}
                              for k, v in res.items()}, default=np_))
        elif only == "red":
            i = sys.argv.index("--range")
            a0, a1 = int(sys.argv[i + 1]), int(sys.argv[i + 2])
            res = check_red(a0, a1)
            (OUT / f"part-red-{a0}-{a1}.json").write_text(json.dumps(res, indent=1, default=np_))
            print(a0, a1, len(res["rows"]), "bad", [r["frame"] for r in res["rows"] if r["outside_her_px"] > 12])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
