#!/usr/bin/env python3
"""QA of the IRIS EP01 s015-s030 v1 export (as qa_opening.py did for 0-59.23 s). Run from the repo root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section2_qa.py --film <export.mp4> --picture <picture.mp4> --out <dir>

Writes <out>/qa.json:
- spec: size, rate, frame count (1805), audio stream.
- sound: the film's audio against the master's samples 59.25-134.4583 s (cross-correlation at 48 kHz; offset, RMS
  difference): pass within one frame and 0.5 dB.
- cuts: every cut of section2.SHOTS (song time, section/song frame, nearest beat; pass <= 0.03 s) and the frame where
  the picture render's mean luminance change peaks (+-3 frames).
- flash: qa.py's WCAG 2.3.1 general-flash count on the film (4x4 cells, 480x270) and single-frame jumps off the cuts.
- red: qa.py's saturated-red mask on every 2nd frame of the film at 960x540; red outside her u2netp matte (grown 29 px)
  per frame and per shot (pass: no frame over 12 px; graphics are white / amber / ink, so red there is picture red).
- lips: for each lip-synced span used (s015a, s015b, s016a, s016b, s017a, s017s, s024, s026c): (a) which take picture
  each picture-render frame shows (grey 160x90 normalised correlation, expected picture +-4); (b) sync_check.py on the
  take's own soundtrack cut at the shot's clip in-point against the take's vocal window (its gate sync.json) cut at the
  shot's song time: lag (0 = the mouth on the song) and in-sync spans.
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
from section2 import N, SF0, SF1, SHOTS, clip_time, frame_of, sha, take_path  # noqa: E402

FILM = Path(sys.argv[sys.argv.index("--film") + 1]).resolve()
PICTURE = Path(sys.argv[sys.argv.index("--picture") + 1]).resolve()
OUT = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
SW, SH = 480, 270
GATES = {"SG05m2": "SG05m-sd", "SG06p1": "SG06-sd", "SG07m1": "SG07-sd", "SG07m2": "SG07-sd", "SG09m2": "SG09-sd", "SG10m2": "SG10-sd"}
LIPS = ["s015a", "s015b", "s016a", "s016b", "s017a", "s017s", "s024", "s026c"]


def frames(src: Path, w: int, h: int, every: int = 1):
    vf = f"scale={w}:{h}:flags=area" if every == 1 else f"select='not(mod(n\\,{every}))',scale={w}:{h}:flags=area"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:v", "-vf", vf, "-vsync", "0", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
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


def sound(tmp: Path) -> dict:
    wav = tmp / "film.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(FILM), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)], check=True)
    a, sr = read_wav(wav)
    b, _ = read_wav(MASTER, SF0 / FPS, N / FPS)
    n = min(len(a), len(b))
    x, y = a[sr:n - sr], b[sr:n - sr]
    corr = lambda L: float(np.dot(x[max(0, L):len(x) + min(0, L)], y[max(0, -L):len(y) - max(0, L)]))
    best = max(range(-4800, 4801, 8), key=corr)
    fine = max(range(best - 8, best + 9), key=corr)
    rms = lambda v: float(np.sqrt(np.mean(v ** 2)))
    db = 20 * np.log10(rms(a[:n]) / rms(b[:n]))
    return {"film_samples": len(a), "master_samples": len(b), "master_window_s": [SF0 / FPS, SF1 / FPS], "offset_samples": fine,
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


def check_red(every: int = 2) -> dict:
    rows, red_map = [], np.zeros((540, 960), np.float32)
    for i, fr in enumerate(frames(FILM, 960, 540, every)):
        k = i * every
        a = fr.astype(np.float32) / 255
        red = red_mask(a)
        row = {"frame": k, "red_px": int(red.sum()), "outside_her_px": 0}
        if red.any():
            her = grow((matte(fr) > 0.3).astype(np.float32), 29) > 0.5
            bad = red & ~her
            row["outside_her_px"] = int(bad.sum())
            red_map += bad
        rows.append(row)
    if red_map.max() > 0:
        Image.fromarray((np.clip(red_map / red_map.max(), 0, 1) * 255).astype(np.uint8)).save(OUT / "red-outside-map.png")
    per = {}
    for r in rows:
        sid = [s["id"] for s in SHOTS if frame_of(s["t0"]) <= r["frame"]][-1]
        p = per.setdefault(sid, {"frames": 0, "over_12": 0, "max_outside_px": 0, "at": None, "max_red_px": 0})
        p["frames"] += 1
        p["over_12"] += r["outside_her_px"] > 12
        p["max_red_px"] = max(p["max_red_px"], r["red_px"])
        if r["outside_her_px"] > p["max_outside_px"]:
            p["max_outside_px"], p["at"] = r["outside_her_px"], r["frame"]
    bad = [r["frame"] for r in rows if r["outside_her_px"] > 12]
    return {"frames_checked": len(rows), "every": every, "frames_with_red": sum(1 for r in rows if r["red_px"]),
            "bad_frames": bad, "per_shot": per, "pass": not bad}


def take_pictures(clip: Path, crop=None) -> np.ndarray:
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-map", "0:v", "-vf", "scale=160:90:flags=area,format=gray",
                        "-vsync", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, 90, 160).astype(np.float32)


def lips(grey: np.ndarray, tmp: Path) -> dict:
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
        gate = json.loads((clip.parents[5] / f"gate/{GATES[s['src']]}/sync.json").read_text())
        take_wav, win_wav = tmp / f"{sid}-take.wav", tmp / f"{sid}-win.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c0:.4f}", "-t", f"{dur:.4f}", "-i", str(clip), "-vn",
                        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(take_wav)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0 - gate['song_t0']:.4f}", "-t", f"{dur:.4f}", "-i", str(REPO / gate["window"]),
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
        out[sid] = {"take": s["src"], "take_sha256": sha(clip), "song": [round(t0, 4), round(t1, 4)], "clip_in": round(c0, 4),
                    "window": gate["window"], "picture_offset_vs_placement": {"0": offs.count(0), "nonzero": [o for o in offs if o], "frames": len(offs)},
                    "sync_check": {k: sc.get(k) for k in ("lag_s", "ncc", "copy", "synced_until", "spans", "divergence", "error")},
                    "visible_lip_synced_song_s": [[round(a, 3), round(b, 3)] for a, b in vis],
                    "covered_share": round(sum(b - a for a, b in vis) / dur, 3)}
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"film": str(FILM.relative_to(REPO)), "film_sha256": sha(FILM), "picture": str(PICTURE.relative_to(REPO)), "picture_sha256": sha(PICTURE)}
    res["spec"] = spec()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        res["sound"] = sound(tmp)
        lin = lambda a: np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
        L = np.stack([lin(fr.astype(np.float32) / 255) @ np.array([0.2126, 0.7152, 0.0722], np.float32) for fr in frames(FILM, SW, SH)])
        res["flash"] = check_flash(L)
        P = np.stack([fr.astype(np.float32).mean(-1) / 255 for fr in frames(PICTURE, SW, SH)])
        res["cuts"] = check_cuts(P)
        grey = np.stack([fr.astype(np.float32).mean(-1) for fr in frames(PICTURE, 160, 90)])
        res["lips"] = lips(grey, tmp)
    res["red"] = check_red()
    np_ = lambda o: o.item() if hasattr(o, "item") else str(o)          # numpy scalars (bool_, int64, float64)
    (OUT / "qa.json").write_text(json.dumps(res, indent=1, default=np_))
    print(json.dumps({k: res[k].get("pass") for k in ("spec", "sound", "cuts", "flash", "red")}, indent=1, default=np_))
    print(json.dumps({k: {"lag": v["sync_check"].get("lag_s"), "vis": v["visible_lip_synced_song_s"], "pic0": v["picture_offset_vs_placement"]["0"],
                          "n": v["picture_offset_vs_placement"]["frames"]} for k, v in res["lips"].items()}, default=np_))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
