#!/usr/bin/env python3
"""QA of the IRIS EP01 Agentcut review film, song 0-59.2341 s (1422 frames, frame n = song n/24). Run from the
repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/qa_opening.py --film <mp4> [--out <dir>] [--edl <chorus edl>]

--edl (opening v2c): the chorus picture EDL whose cuts are checked (default data/edl-v4r11-picture.json; v2c:
data/edl-v4r11-picture-v2c.json, s014 one shot, no 57.3765 cut).

Writes <out>/qa.json (default excerpt/qa/opening/) with:
- spec: size, rate, frame count, audio stream.
- sound: the film's audio against the master's samples 0-59.25 s: sample offset (cross-correlation, 48 kHz) and RMS
  difference (dB), as qa.py's check_sound.
- cuts: every picture cut (opening.py's s002-s010, the v4r11 picture's s011-s014c) as song time, frame, the nearest beat
  (beats.json) and the frame's distance to it; and the frame where the film's mean luminance change peaks (+-3 frames).
- lips: for the two lip-synced shots (s004 SG01-o-2, s008 SG02-o-1), (a) which take picture each film frame shows,
  found by matching the frame against the take's pictures (grey 160x90, normalised correlation, the expected picture
  +-4), so the placement is read off the film itself; (b) motion-kit/tools/sync_check.py on the take's own soundtrack
  laid at that placement (the soundtrack the mouth follows) against the film's own audio over the shot: lag and the
  in-sync spans in song time; the visible lip-synced interval is the shot's frames inside those spans. The window is the
  vocal window of the take's gate (sync.json "window", song_t0) cut at the film's time: the film's own audio is the
  master (checked at 0 samples under sound), whose music bed makes a waveform lag unreliable.
- flash: qa.py's WCAG 2.3.1 general-flash count (relative luminance, 4x4 cells, opposing changes of 10% with the
  darker state below 0.8, flashes in any one second), and single-frame luminance jumps off the cuts.
- red: qa.py's saturated-red object mask on every 2nd frame at 960x540; red outside her u2netp matte (grown 29 px, as
  qa.py v1) counted per frame, and inside the matte any red component larger than an ear lamp (60x60 px at 960) listed.
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
from edl import EXC, FPS, MASTER, REPO, V4  # noqa: E402
from opening import SHOTS as OPEN, frame_of, sha  # noqa: E402
from prep_media import grow, matte  # noqa: E402
from qa import lin, red_mask, transitions  # noqa: E402

FILM = Path(sys.argv[sys.argv.index("--film") + 1]).resolve()
OUT = Path(sys.argv[sys.argv.index("--out") + 1]).resolve() if "--out" in sys.argv else EXC / "qa/opening"
CHORUS_EDL = Path(sys.argv[sys.argv.index("--edl") + 1]).resolve() if "--edl" in sys.argv else EXC / "data/edl-v4r11-picture.json"
N = 1422
SW, SH = 480, 270


def frames(w: int, h: int, every: int = 1):
    vf = f"scale={w}:{h}:flags=area" if every == 1 else f"select='not(mod(n\\,{every}))',scale={w}:{h}:flags=area"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(FILM), "-map", "0:v", "-vf", vf, "-vsync", "0", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.wait()


def spec() -> dict:
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(FILM)],
                                  capture_output=True, text=True, check=True).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = [s for s in d["streams"] if s["codec_type"] == "audio"]
    out = {"width": v["width"], "height": v["height"], "fps": v["r_frame_rate"], "frames": int(v["nb_read_frames"]),
           "video_codec": v["codec_name"], "pix_fmt": v.get("pix_fmt"), "duration_s": float(d["format"]["duration"]),
           "audio": [{"codec": s["codec_name"], "sample_rate": int(s["sample_rate"]), "channels": s["channels"]} for s in a]}
    out["pass"] = (v["width"], v["height"], v["r_frame_rate"], int(v["nb_read_frames"])) == (1920, 1080, "24/1", N) and bool(a)
    return out


def read_wav(p: Path, t0: float = 0.0, dur: float | None = None) -> tuple[np.ndarray, int]:
    with wave.open(str(p)) as r:
        sr = r.getframerate()
        r.setpos(int(round(t0 * sr)))
        x = np.frombuffer(r.readframes(r.getnframes() if dur is None else int(round(dur * sr))), np.int16)
        return x.reshape(-1, r.getnchannels()).astype(np.float32).mean(1), sr


def sound(tmp: Path) -> dict:
    wav = tmp / "film.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(FILM), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)], check=True)
    a, sr = read_wav(wav)
    b, _ = read_wav(MASTER, 0.0, N / FPS)
    n = min(len(a), len(b))
    x, y = a[sr:n - sr], b[sr:n - sr]
    corr = lambda L: float(np.dot(x[max(0, L):len(x) + min(0, L)], y[max(0, -L):len(y) - max(0, L)]))
    best = max(range(-4800, 4801, 8), key=corr)
    fine = max(range(best - 8, best + 9), key=corr)
    rms = lambda v: float(np.sqrt(np.mean(v ** 2)))
    xs, ys = (a[fine:n], b[:n - fine]) if fine >= 0 else (a[:n + fine], b[-fine:n])
    return {"film_samples": len(a), "master_samples": len(b), "offset_samples": fine, "offset_ms": round(fine / sr * 1000, 3),
            "rms_diff_db": round(20 * np.log10(rms(a[:n]) / rms(b[:n])), 3),
            "residual_db_after_alignment": round(20 * np.log10(rms(xs - ys) / rms(ys)), 1),
            "pass": abs(fine) <= sr / FPS and abs(20 * np.log10(rms(a[:n]) / rms(b[:n]))) <= 0.5}


def cut_list() -> list[dict]:
    e = json.loads(CHORUS_EDL.read_text())
    cuts = [{"cut": s["id"], "take": s["take"][0], "t": s["t0"], "frame": frame_of(s["t0"])} for s in OPEN[1:]]
    for s in e["shots"]:
        if s["t0"] >= 40.7859 - 1e-6:                      # v4r11 frames are its excerpt frames; song frame = f0 - 244 + 869
            cuts.append({"cut": s["id"], "take": "v4r11", "t": s["t0"], "frame": s["f0"] - e["window_f0"] + 869})
    return cuts


def check_cuts(L: np.ndarray) -> dict:
    beats = json.loads((V4 / "song/beatmap/beats.json").read_text())["beats"]
    d = np.abs(np.diff(L, axis=0)).mean((1, 2))
    rows = []
    for c in cut_list():
        nb = min(beats, key=lambda b: abs(b - c["t"]))
        f = c["frame"]
        peak = max(0, f - 4) + int(np.argmax(d[max(0, f - 4):f + 3])) + 1
        rows.append({**c, "frame_t": round(f / FPS, 4), "nearest_beat": nb, "cut_dt_beat": round(c["t"] - nb, 4),
                     "frame_dt_beat": round(f / FPS - nb, 4), "film_change_peak_frame": peak,
                     "pass": abs(f / FPS - nb) <= 0.03 and abs(c["t"] - nb) <= 0.03})
    return {"cuts": rows, "pass": all(r["pass"] for r in rows),
            "change_peak_on_cut": sum(1 for r in rows if r["film_change_peak_frame"] == r["frame"])}


def check_flash(L: np.ndarray) -> dict:
    g = 4
    Lc = L[:, :SH // g * g, :SW // g * g]
    cells = Lc.reshape(L.shape[0], g, SH // g, g, SW // g).mean((2, 4)).reshape(L.shape[0], -1)
    per = []
    for c in range(cells.shape[1]):
        fl = [i for i, _ in transitions(cells[:, c])]
        for i in range(len(fl)):
            per.append((sum(1 for t in fl[i:] if t - fl[i] < FPS) / 2, c, fl[i]))
    per.sort(reverse=True)
    worst = per[0] if per else (0, None, None)
    over = sorted({f for n, _, f in per if n > 3})
    cuts = {c["frame"] for c in cut_list()}
    D = np.abs(np.diff(L, axis=0)).mean((1, 2))
    singles = []
    for f in range(1, len(L) - 1):
        if f in cuts or f + 1 in cuts:
            continue
        a, b = D[f - 1], D[f]
        if a > 0.02 and b > 0.02 and float(np.abs(L[f + 1] - L[f - 1]).mean()) < 0.4 * min(a, b):
            singles.append({"frame": f, "t": round(f / FPS, 3), "d_prev": round(float(a), 4), "d_next": round(float(b), 4)})
    return {"max_flashes_per_second_any_cell": worst[0], "at": {"cell": worst[1], "frame": worst[2]},
            "windows_over_3_per_second_start_frames": over, "single_frame_jumps": singles,
            "pass": worst[0] <= 3 and not singles}


def check_red(every: int = 2) -> dict:
    rows, red_map = [], np.zeros((540, 960), np.float32)
    for i, fr in enumerate(frames(960, 540, every)):
        f = i * every
        a = fr.astype(np.float32) / 255
        red = red_mask(a)
        row = {"frame": f, "red_px": int(red.sum()), "outside_her_px": 0, "large_inside": []}
        if red.any():
            her = grow((matte(fr) > 0.3).astype(np.float32), 29) > 0.5
            bad = red & ~her
            row["outside_her_px"] = int(bad.sum())
            red_map += bad
            inside = red & her
            if inside.sum() > 60:
                ys, xs = np.nonzero(inside)
                if xs.max() - xs.min() > 60 or ys.max() - ys.min() > 60:
                    row["large_inside"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(inside.sum())]
        rows.append(row)
    if red_map.max() > 0:
        Image.fromarray((np.clip(red_map / red_map.max(), 0, 1) * 255).astype(np.uint8)).save(OUT / "red-outside-map.png")
    worst = sorted(rows, key=lambda r: -r["outside_her_px"])[:10]
    starts = [(0, "s001")] + [(c["frame"], c["cut"]) for c in cut_list()]
    per = {}
    for r in rows:
        sid = [n for f0, n in starts if f0 <= r["frame"]][-1]
        p = per.setdefault(sid, {"frames": 0, "over_12": 0, "max_outside_px": 0, "at": None})
        p["frames"] += 1
        p["over_12"] += r["outside_her_px"] > 12
        if r["outside_her_px"] > p["max_outside_px"]:
            p["max_outside_px"], p["at"] = r["outside_her_px"], r["frame"]
    bad = [r["frame"] for r in rows if r["outside_her_px"] > 12]
    return {"frames_checked": len(rows), "every": every, "frames_with_red": sum(1 for r in rows if r["red_px"]),
            "frames_with_red_outside_her_over_12px": len(bad), "bad_frames": bad, "worst": worst,
            "frames_with_large_red_inside_matte": [r for r in rows if r["large_inside"]][:20], "per_shot": per,
            "pass": not bad}


def take_pictures(clip: Path, n: int) -> np.ndarray:
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-map", "0:v", "-vf", "scale=160:90:flags=area,format=gray",
                        "-vsync", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, 90, 160).astype(np.float32)[:n]


def lips(grey: np.ndarray, tmp: Path) -> dict:
    out = {}
    for sid, unit in (("s004", "SG01"), ("s008", "SG02")):
        s = next(x for x in OPEN if x["id"] == sid)
        start = s["clip_song_start"] + s["lag"]                  # song time of clip 0 (opening.py / prep_clip)
        clip = V4 / "pilot/sd-{}/{}/project/state/video-generation/fetch/files/{}.mp4".format(*s["take"])
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        pics = take_pictures(clip, 200)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        offs = []
        for f in range(f0, f1):
            exp = int(round((f / FPS - start) * 24))
            cand = range(max(0, exp - 4), min(len(pics), exp + 5))
            sc = {k: float((z(grey[f]) * z(pics[k])).mean()) for k in cand}
            k = max(sc, key=sc.get)
            offs.append(k - exp)
        # the take's soundtrack laid at the placement, over the shot, against the vocal window it was made from (its
        # gate sync.json), cut at the film's song time of the same frames (the film's audio is the master at 0 samples)
        t0, dur = f0 / FPS, (f1 - f0) / FPS
        gate = json.loads((clip.parents[5] / f"gate/{unit}-sd/sync.json").read_text())
        take_wav, win_wav = tmp / f"{sid}-take.wav", tmp / f"{sid}-film.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0 - start:.4f}", "-t", f"{dur:.4f}", "-i", str(clip), "-vn",
                        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(take_wav)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0 - gate['song_t0']:.4f}", "-t", f"{dur:.4f}", "-i", str(REPO / gate["window"]),
                        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(win_wav)], check=True)
        d = tmp / sid
        r = subprocess.run(["uv", "run", "python", str(REPO / "motion-kit/tools/sync_check.py"), "--take", str(take_wav), "--window", str(win_wav),
                            "--song-t0", f"{t0:.4f}", "--out", str(d), "--name", f"{sid}-film",
                            "--words", str(V4 / "song/timing/words.json")], capture_output=True, text=True, cwd=REPO)
        js = sorted(d.glob("**/sync.json"))
        sc = json.loads(js[0].read_text()) if js else {"error": r.stderr[-600:]}
        spans = sc.get("spans", [])
        vis = [[max(a, t0), min(b, f1 / FPS)] for a, b in (x["song_s"] for x in spans) if min(b, f1 / FPS) > max(a, t0)]
        out[sid] = {"take": s["take"][0], "take_sha256": sha(clip), "frames": [f0, f1], "song": [round(t0, 4), round(f1 / FPS, 4)],
                    "picture_offset_vs_placement": {"0": offs.count(0), "nonzero": [o for o in offs if o], "frames": len(offs)},
                    "sync_check": {k: sc.get(k) for k in ("lag_s", "ncc", "copy", "synced_until", "spans", "divergence", "frames", "error")},
                    "visible_lip_synced_song_s": [[round(a, 3), round(b, 3)] for a, b in vis],
                    "visible_lip_synced_frames": [[frame_of(a), frame_of(b)] for a, b in vis]}
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"film": str(FILM), "film_sha256": sha(FILM), "spec": spec()}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        res["sound"] = sound(tmp)
        small = np.stack(list(frames(SW, SH)))
        L = lin(small) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        res["cuts"] = check_cuts(L)
        res["flash"] = check_flash(L)
        grey = np.stack([np.asarray(Image.fromarray(f).convert("L").resize((160, 90), Image.BOX), np.float32) for f in small])
        del small
        res["lips"] = lips(grey, tmp)
    res["red"] = check_red()
    (OUT / "qa.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print(json.dumps({k: (bool(v.get("pass")) if isinstance(v, dict) and "pass" in v else "-") for k, v in res.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
