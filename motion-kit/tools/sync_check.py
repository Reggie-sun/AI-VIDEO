#!/usr/bin/env python3
"""Sync check for sung takes: how far a take's own soundtrack sits from the vocal window it was given, how
much of it is really in sync, and where it parts. Method and constants from the ESCAPE VELOCITY toolkit
(claudia.gallery/wiki/toolkit, tool 15 "The sync check" and tool 63 "Placing a re-sung take by its lag");
the code is original to this project.

The video model copies the reference vocal into its own soundtrack while it is in sync, and the mouth
follows that soundtrack. So the take's soundtrack is compared with the exact window file that was sent:

- tool 15: global lag by waveform cross-correlation (copy when NCC > 0.2), then per 10 ms frame a waveform
  NCC and a log-mel similarity against a per-take null threshold; the divergence point, the in-sync spans
  and the cut, mapped to song time (song time = song_t0 + clip time - lag);
- tool 63: for a take the model re-sang, the lag of the voice envelope, globally and in sliding windows;
  a steady lag (every window within about 0.05 s) places the take as if it were a copy.

The numbers decide where a take sits and where it is cut. Whether it reads in sync is judged by eye on the
review video (the take with the song laid over at normal speed), never by this script alone.

Usage (one take):
  uv run python motion-kit/tools/sync_check.py --take T.mp4 --window W.wav --song-t0 18.40 --out DIR \
      [--name S8a] [--song SONG.wav --review] [--words words.json]
Usage (a set of takes; see --manifest):
  uv run python motion-kit/tools/sync_check.py --manifest takes.json --out DIR [--review]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 16000
HOP = 160                      # 10 ms frames
N_FFT = 1024                   # 64 ms windows
N_MELS, FMIN, FMAX = 80, 50.0, 7600.0
FLOOR_DB = 70.0                # log-mel floor below each track's peak
LAG_MAX_S = 1.0                # tool 15 global lag search
COPY_NCC = 0.2                 # above: the model copied the window; at or below: it re-sang it
WAVE_WIN = 1600                # 100 ms waveform NCC
MEL_SMOOTH = 11                # frames
ACTIVE_FRAC = 0.10             # of each track's 95th-percentile RMS
NULL_SHIFTS = (37, 61, 89, 131)  # frames, avoiding eighth-note multiples; used as +/-
WAVE_MATCHED, WAVE_MATCH = 0.6, 0.4
DIV_LEN, DIV_ACTIVE, DIV_MATCHED, RECOVER = 30, 0.6, 0.3, 40   # 300 ms stretch, 400 ms recovery run
TAIL_VOICE = 8                 # 80 ms of voice after the last match is a divergence
SYNC_MARGIN = 0.042            # synced_until = last match minus one 24 fps frame
BRIDGE_UNMATCHED, MIN_SPAN = 25, 50                            # 0.25 s, 0.5 s
ENV_LAG_MAX_S, ENV_WIN_S, ENV_HOP_S, ENV_LOCAL_S, ENV_STEADY_S = 2.5, 1.5, 0.25, 0.5, 0.05


# ---------------- audio ----------------
def decode(path: Path, sr: int = SR) -> np.ndarray:
    """Any audio or video file -> mono float32 at sr (ffmpeg's channel average)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    if not len(x):
        raise ValueError(f"{path}: no audio")
    return x


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _hz2mel(f):
    return 2595.0 * np.log10(1.0 + f / 700.0)


def _mel2hz(m):
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


def mel_filterbank(sr: int = SR, n_fft: int = N_FFT, n_mels: int = N_MELS, fmin: float = FMIN,
                   fmax: float = FMAX) -> np.ndarray:
    edges = _mel2hz(np.linspace(_hz2mel(fmin), _hz2mel(fmax), n_mels + 2))
    bins = np.fft.rfftfreq(n_fft, 1.0 / sr)
    fb = np.zeros((n_mels, len(bins)), np.float64)
    for i in range(n_mels):
        lo, c, hi = edges[i], edges[i + 1], edges[i + 2]
        fb[i] = np.maximum(0.0, np.minimum((bins - lo) / (c - lo), (hi - bins) / (hi - c)))
    return fb


def frames_of(x: np.ndarray, n: int | None = None) -> np.ndarray:
    """Centred frames: frame i covers samples around i * HOP."""
    if n is None:
        n = len(x) // HOP + 1
    pad = N_FFT // 2
    xp = np.pad(x.astype(np.float64), (pad, pad + N_FFT + n * HOP))
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n)[:, None]
    return xp[idx]


def features(x: np.ndarray, n: int, fb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(log-mel dB floored at peak - 70, frame RMS) for n frames."""
    fr = frames_of(x, n)
    rms = np.sqrt((fr ** 2).mean(axis=1))
    spec = np.abs(np.fft.rfft(fr * np.hanning(N_FFT)[None, :], axis=1)) ** 2
    db = 10.0 * np.log10(spec @ fb.T + 1e-12)
    return np.maximum(db, db.max() - FLOOR_DB), rms


def place(ref: np.ndarray, lag: int, n: int) -> np.ndarray:
    """The reference on the take's timeline: out[i] = ref[i - lag] (lag > 0: the take is later)."""
    out = np.zeros(n, np.float64)
    lo, hi = max(0, lag), min(n, len(ref) + lag)
    if hi > lo:
        out[lo:hi] = ref[lo - lag:hi - lag]
    return out


def global_lag(take: np.ndarray, ref: np.ndarray, max_lag: int) -> tuple[int, float]:
    """Lag k (samples) maximising sum take[i + k] * ref[i] within +/-max_lag, and its normalised value."""
    a, b = take.astype(np.float64), ref.astype(np.float64)
    nfft = 1 << (len(a) + len(b)).bit_length()
    c = np.fft.irfft(np.fft.rfft(a, nfft) * np.conj(np.fft.rfft(b, nfft)), nfft)
    lags = np.arange(-max_lag, max_lag + 1)
    vals = c[lags % nfft]
    i = int(np.argmax(vals))
    norm = math.sqrt(float((a ** 2).sum() * (b ** 2).sum())) or 1.0
    return int(lags[i]), float(vals[i] / norm)


def wave_ncc(a: np.ndarray, b: np.ndarray, n: int, win: int = WAVE_WIN) -> np.ndarray:
    """Per frame: NCC of the two (aligned) waveforms over win samples centred on the frame."""
    half = win // 2
    pa, pb = (np.pad(x.astype(np.float64), (half, half + n * HOP)) for x in (a, b))
    sab, saa, sbb = (np.concatenate([[0.0], np.cumsum(x)]) for x in (pa * pb, pa * pa, pb * pb))
    s = HOP * np.arange(n)                      # window [c - half, c + half) in padded index [s, s + win)
    ab, aa, bb = (x[s + win] - x[s] for x in (sab, saa, sbb))
    den = np.sqrt(aa * bb)
    return np.where(den > 1e-9, ab / np.maximum(den, 1e-12), 0.0)


def cosine_rows(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Cosine similarity of mean-removed rows."""
    A = A - A.mean(axis=1, keepdims=True)
    B = B - B.mean(axis=1, keepdims=True)
    den = np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1)
    return np.where(den > 1e-9, (A * B).sum(axis=1) / np.maximum(den, 1e-12), 0.0)


def smooth(x: np.ndarray, k: int = MEL_SMOOTH) -> np.ndarray:
    return np.convolve(np.pad(x, (k // 2, k // 2), mode="edge"), np.ones(k) / k, mode="valid")


def shifted(M: np.ndarray, o: int) -> np.ndarray:
    """Rows of M moved by o frames (row i of the result = row i + o of M), floor-filled outside."""
    out = np.full_like(M, M.min())
    n = len(M)
    if o >= 0:
        out[:n - o] = M[o:]
    else:
        out[-o:] = M[:n + o]
    return out


def active_mask(rms_a: np.ndarray, rms_b: np.ndarray) -> np.ndarray:
    ta = ACTIVE_FRAC * np.percentile(rms_a, 95)
    tb = ACTIVE_FRAC * np.percentile(rms_b, 95)
    return (rms_a > ta) | (rms_b > tb)


def has_run(mask: np.ndarray, length: int) -> bool:
    run = 0
    for v in mask:
        run = run + 1 if v else 0
        if run >= length:
            return True
    return False


def divergence(active: np.ndarray, matched: np.ndarray) -> dict:
    """First 300 ms stretch (>= 60% active, < 30% matched, starting unmatched) with no 400 ms matched run
    after it; else voice at least 80 ms after the last match. Frame indices."""
    n = len(active)
    for i in range(0, n - DIV_LEN + 1):
        if matched[i]:
            continue
        seg = slice(i, i + DIV_LEN)
        if active[seg].mean() >= DIV_ACTIVE and matched[seg].mean() < DIV_MATCHED and not has_run(matched[i:], RECOVER):
            before = np.flatnonzero(matched[:i])
            return {"frame": i, "rule": "stretch", "last_match": int(before[-1]) if len(before) else None}
    m = np.flatnonzero(matched)
    if not len(m):
        v = np.flatnonzero(active)
        return {"frame": int(v[0]) if len(v) else None, "rule": "never matched", "last_match": None}
    last = int(m[-1])
    if np.any(active[last + TAIL_VOICE:]):
        return {"frame": last + 1, "rule": "voice after the last match", "last_match": last}
    return {"frame": None, "rule": "none", "last_match": last}


def sync_spans(active: np.ndarray, matched: np.ndarray) -> list[tuple[int, int]]:
    """Matched voice, bridged across silences and up to 0.25 s of unmatched voice; spans under 0.5 s dropped."""
    out, i, n = [], 0, len(active)
    while i < n:
        if not matched[i]:
            i += 1
            continue
        start = last = i
        unmatched = 0
        j = i + 1
        while j < n:
            if matched[j]:
                last, unmatched = j, 0
            elif active[j]:
                unmatched += 1
                if unmatched > BRIDGE_UNMATCHED:
                    break
            j += 1
        if last - start + 1 >= MIN_SPAN:
            out.append((start, last))
        i = last + 1
    return out


def voice_envelope(mel_db: np.ndarray, fb_hz: tuple[float, float] = (150.0, 4000.0)) -> np.ndarray:
    """Voice-band loudness per frame, 0..1 over the top 40 dB (phrasing, not timbre)."""
    edges = np.linspace(2595 * np.log10(1 + FMIN / 700), 2595 * np.log10(1 + FMAX / 700), N_MELS + 2)
    centres = 700 * (10 ** (edges[1:-1] / 2595) - 1)
    band = (centres >= fb_hz[0]) & (centres <= fb_hz[1])
    e = 10 * np.log10((10 ** (mel_db[:, band] / 10)).sum(axis=1) + 1e-12)
    return np.clip((e - (e.max() - 40.0)) / 40.0, 0.0, 1.0)


def env_ncc(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a - a.mean(), b - b.mean()
    den = math.sqrt(float((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / den) if den > 1e-9 else 0.0


def best_lag(env_t: np.ndarray, env_r: np.ndarray, lags: np.ndarray, sel: slice | None = None) -> tuple[float, float]:
    """Lag (frames, parabolic sub-frame) maximising NCC of env_t[i + L] against env_r[i] over sel (take frames)."""
    n = len(env_t)
    lo_t, hi_t = (0, n) if sel is None else (sel.start, sel.stop)
    scores = []
    for L in lags:
        i0, i1 = max(lo_t, L), min(hi_t, len(env_r) + L)
        scores.append(env_ncc(env_t[i0:i1], env_r[i0 - L:i1 - L]) if i1 - i0 > 20 else -1.0)
    scores = np.array(scores)
    k = int(np.argmax(scores))
    frac = 0.0
    if 0 < k < len(scores) - 1:
        y0, y1, y2 = scores[k - 1], scores[k], scores[k + 1]
        d = y0 - 2 * y1 + y2
        frac = 0.5 * (y0 - y2) / d if abs(d) > 1e-12 else 0.0
    return float(lags[k] + frac), float(scores[k])


def envelope_lag(env_t: np.ndarray, env_r: np.ndarray, act_t: np.ndarray, act_r_on_take) -> dict:
    """Tool 63: one global envelope lag over +/-2.5 s, then the lag in sliding 1.5 s windows along the take."""
    fps = SR / HOP
    g, g_ncc = best_lag(env_t, env_r, np.arange(-int(ENV_LAG_MAX_S * fps), int(ENV_LAG_MAX_S * fps) + 1))
    win, hop, local = int(ENV_WIN_S * fps), int(ENV_HOP_S * fps), int(ENV_LOCAL_S * fps)
    rows = []
    gi = int(round(g))
    for s in range(0, max(1, len(env_t) - win + 1), hop):
        sel = slice(s, s + win)
        ref_act = act_r_on_take(gi)[sel]
        if act_t[sel].mean() < 0.3 or ref_act.mean() < 0.3:
            continue
        lag, ncc = best_lag(env_t, env_r, np.arange(gi - local, gi + local + 1), sel)
        rows.append({"clip_t0": round(s / fps, 3), "clip_t1": round((s + win) / fps, 3),
                     "lag_s": round(lag / fps, 3), "ncc": round(ncc, 3)})
    devs = [abs(r["lag_s"] - g / fps) for r in rows]
    return {"lag_s": round(g / fps, 3), "ncc": round(g_ncc, 3), "windows": rows,
            "max_dev_s": round(max(devs), 3) if devs else None,
            "steady": bool(rows) and max(devs) <= ENV_STEADY_S + 1e-9,
            "segments": lag_segments(rows)}


def lag_segments(rows: list[dict]) -> list[dict]:
    """Consecutive windows that agree within about 0.05 s make one segment at their median lag (tool 63:
    phrases at different lags get their own entries). Clip ranges run between window centres."""
    segs: list[list[dict]] = []
    for r in rows:
        if segs and abs(r["lag_s"] - float(np.median([x["lag_s"] for x in segs[-1]]))) <= ENV_STEADY_S + 1e-9:
            segs[-1].append(r)
        else:
            segs.append([r])
    out = []
    for s in segs:
        c0 = (s[0]["clip_t0"] + s[0]["clip_t1"]) / 2 - ENV_HOP_S / 2
        c1 = (s[-1]["clip_t0"] + s[-1]["clip_t1"]) / 2 + ENV_HOP_S / 2
        out.append({"clip_s": [round(c0, 3), round(c1, 3)], "lag_s": round(float(np.median([x["lag_s"] for x in s])), 3),
                    "windows": len(s), "min_ncc": round(min(x["ncc"] for x in s), 3)})
    return out


# ---------------- the check ----------------
def check(take_path: Path, window_path: Path, song_t0: float) -> dict:
    take, ref = decode(take_path), decode(window_path)
    n = len(take) // HOP + 1
    fb = mel_filterbank()
    k, ncc = global_lag(take, ref, int(LAG_MAX_S * SR))
    ref_on = place(ref, k, len(take))
    mel_t, rms_t = features(take, n, fb)
    mel_r, rms_r = features(ref_on, n, fb)
    active = active_mask(rms_t, rms_r)
    wave = wave_ncc(take, ref_on, n)
    mel = smooth(cosine_rows(mel_t, mel_r))
    null = []
    for o in NULL_SHIFTS:
        for s in (o, -o):
            mr = shifted(mel_r, s)
            act = active_mask(rms_t, shifted(rms_r[:, None], s)[:, 0])
            null.append(smooth(cosine_rows(mel_t, mr))[act])
    null = np.concatenate(null) if null else np.zeros(1)
    null90 = float(np.percentile(null, 90))
    strong = active & (wave > WAVE_MATCHED)
    matched_med = float(np.median(mel[strong])) if strong.sum() > 10 else float(np.percentile(mel[active], 75))
    thr = null90 + 0.4 * (matched_med - null90)
    matched = active & ((wave >= WAVE_MATCH) | (mel >= thr))
    div = divergence(active, matched)
    spans = sync_spans(active, matched)
    lag_s = k / SR

    def to_song(f: int) -> float:
        return round(song_t0 + f * HOP / SR - lag_s, 3)
    synced_until = None
    if div["last_match"] is not None:
        synced_until = div["last_match"] * HOP / SR - SYNC_MARGIN
    # tool 63 on the unshifted window: the envelope lag is measured, not assumed from the waveform peak
    mel_r0, rms_r0 = features(ref, len(ref) // HOP + 1, fb)
    env_t, env_r = voice_envelope(mel_t), voice_envelope(mel_r0)
    act_t = rms_t > ACTIVE_FRAC * np.percentile(rms_t, 95)
    act_r0 = rms_r0 > ACTIVE_FRAC * np.percentile(rms_r0, 95)
    def act_r_on_take(L: int) -> np.ndarray:
        out = np.zeros(n, bool)
        lo, hi = max(0, L), min(n, len(act_r0) + L)
        if hi > lo:
            out[lo:hi] = act_r0[lo - L:hi - L]
        return out
    env = envelope_lag(env_t, env_r, act_t, act_r_on_take)
    copy = ncc > COPY_NCC
    if copy:
        placement = {"lag_s": round(lag_s, 4), "method": "tool 15 waveform lag (copy)"}
    elif env["steady"]:
        placement = {"lag_s": env["lag_s"], "method": "tool 63 envelope lag (re-sung, steady)"}
    else:
        placement = {"lag_s": env["lag_s"], "method": "tool 63 envelope lag (re-sung, NOT steady: judge by eye)"}
    return {
        "schema": "motion-kit-sync-check/1",
        "take": str(take_path), "take_sha256": sha256(take_path),
        "window": str(window_path), "window_sha256": sha256(window_path), "song_t0": song_t0,
        "constants": {"sr": SR, "hop": HOP, "n_fft": N_FFT, "mels": [N_MELS, FMIN, FMAX], "copy_ncc": COPY_NCC},
        "lag_s": round(lag_s, 4), "ncc": round(ncc, 4), "copy": copy,
        "threshold": {"null90": round(null90, 4), "matched_med": round(matched_med, 4), "thr": round(thr, 4),
                      "strong_frames": int(strong.sum())},
        "frames": {"total": n, "active": int(active.sum()), "matched": int(matched.sum()),
                   "matched_of_active": round(float(matched.sum() / max(1, active.sum())), 3)},
        "divergence": {**div, "clip_s": None if div["frame"] is None else round(div["frame"] * HOP / SR, 3),
                       "song_s": None if div["frame"] is None else to_song(div["frame"])},
        "synced_until": None if synced_until is None else {"clip_s": round(synced_until, 3),
                                                           "song_s": round(song_t0 + synced_until - lag_s, 3)},
        "spans": [{"clip_s": [round(a * HOP / SR, 3), round(b * HOP / SR, 3)], "song_s": [to_song(a), to_song(b)]}
                  for a, b in spans],
        "envelope": env,
        "placement": {**placement, "song_t_of_clip0": round(song_t0 - placement["lag_s"], 4),
                      "note": "song time = song_t0 + clip time - lag; in-point for a shot starting at song time T is "
                              "T - song_t0 + lag"},
        "_curves": {"wave": wave, "mel": mel, "thr": thr, "active": active, "matched": matched,
                    "mel_t": mel_t, "mel_r": mel_r},
    }


def words_in(words_doc: dict | None, s0: float, s1: float) -> list[dict]:
    if not words_doc:
        return []
    out = []
    for line in words_doc.get("lines", []):
        for w in line.get("words", []):
            if w["end"] > s0 and w["start"] < s1:
                out.append({"text": w["text"], "start": w["start"], "end": w["end"]})
    return out


# ---------------- diagnostic image ----------------
def _font(size: int):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _heat(M: np.ndarray, lo: float | None = None, hi: float | None = None) -> np.ndarray:
    lo = float(M.min()) if lo is None else lo
    hi = float(M.max()) if hi is None else hi
    u = np.clip((M - lo) / max(hi - lo, 1e-9), 0, 1)
    stops = np.array([[0, 0, 4], [60, 15, 110], [180, 50, 100], [250, 140, 40], [252, 253, 191]], np.float64)
    x = u * (len(stops) - 1)
    i = np.minimum(x.astype(int), len(stops) - 2)
    f = (x - i)[..., None]
    return (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)


def diagnostic(res: dict, name: str, words: list[dict], out: Path, prior: dict | None = None) -> None:
    c = res["_curves"]
    n = len(c["wave"])
    W, L = 1600, 90
    pw = W - L - 20
    lag, t0 = res["lag_s"], res["song_t0"]

    def fx(f: float) -> int:                       # frame -> x pixel
        return L + int(f / max(1, n - 1) * pw)

    def clip_of_song(s: float) -> float:
        return s - t0 + lag
    rows = [("window sent (placed at the waveform lag)", 150), ("take soundtrack", 150), ("match", 220),
            ("envelope lag (tool 63)", 170), ("cross-similarity (take rows x window columns)", 460)]
    H = 120 + sum(h + 40 for _, h in rows)
    im = Image.new("RGB", (W, H), (250, 250, 248))
    d = ImageDraw.Draw(im)
    f14, f16, f20 = _font(14), _font(16), _font(20)
    env = res["envelope"]
    head = (f"{name}  ·  take {res['take_sha256'][:12]}  ·  window {Path(res['window']).name}  ·  song_t0 {t0:.3f} s")
    d.text((L, 12), head, fill=(10, 10, 10), font=f20)
    dv, th, pl = res["divergence"], res["threshold"], res["placement"]
    div_txt = "none" if dv["clip_s"] is None else f"clip {dv['clip_s']:.2f} s = song {dv['song_s']:.2f} s"
    line2 = (f"waveform lag {lag:+.3f} s  NCC {res['ncc']:.3f}  {'COPY' if res['copy'] else 're-sung'}  ·  "
             f"thr {th['thr']:.3f} (null90 {th['null90']:.3f}, matched {th['matched_med']:.3f})  ·  "
             f"matched {res['frames']['matched_of_active']:.0%} of active  ·  divergence {div_txt} ({dv['rule']})")
    d.text((L, 42), line2, fill=(30, 30, 30), font=f16)
    dev_txt = "-" if env["max_dev_s"] is None else f"{env['max_dev_s']:.3f}"
    line3 = (f"envelope lag {env['lag_s']:+.3f} s  NCC {env['ncc']:.2f}  max window deviation {dev_txt} s  "
             f"{'steady' if env['steady'] else 'NOT steady'}  ·  placement {pl['lag_s']:+.3f} s ({pl['method']})")
    if prior:
        line3 += f"  ·  prior cut lag {prior['lag_s']:+.3f} s ({prior['why']})"
    d.text((L, 68), line3, fill=(30, 30, 30), font=f16)
    y = 110
    for title, h in rows:
        d.text((L, y), title, fill=(60, 60, 60), font=f14)
        y += 18
        box = (L, y, L + pw, y + h)
        if title.startswith("window") or title.startswith("take"):
            M = c["mel_r"] if title.startswith("window") else c["mel_t"]
            img = Image.fromarray(_heat(M.T[::-1])).resize((pw, h), Image.BILINEAR)
            im.paste(img, (L, y))
            if title.startswith("window"):
                for w in words:
                    a = clip_of_song(w["start"]) * SR / HOP
                    if 0 <= a < n:
                        d.line([(fx(a), y), (fx(a), y + h)], fill=(255, 255, 255), width=1)
                        d.text((fx(a) + 3, y + 3), w["text"], fill=(255, 255, 255), font=f14)
        elif title == "match":
            d.rectangle(box, outline=(180, 180, 180))
            def yv(v: float, y: int = y, h: int = h) -> int:     # similarity -> y pixel
                return y + h - 20 - int(np.clip(v, -0.2, 1.0) / 1.2 * (h - 40) + 0.2 / 1.2 * (h - 40))
            for f in range(n):
                if c["active"][f]:
                    d.line([(fx(f), y + h - 14), (fx(f), y + h - 9)], fill=(170, 170, 170))
                if c["matched"][f]:
                    d.line([(fx(f), y + h - 8), (fx(f), y + h - 2)], fill=(30, 160, 60))
            su_f = res["synced_until"]["clip_s"] * SR / HOP if (res["synced_until"] and dv["frame"] is not None) else None
            for s in res["spans"]:
                a, b = (v * SR / HOP for v in s["clip_s"])
                cut = b if su_f is None else max(a, min(b, su_f))
                if cut > a:
                    d.rectangle([fx(a), y + 2, fx(cut), y + 8], fill=(30, 160, 60))
                if b > cut:                            # bridged past the divergence: not in sync for the edit
                    d.rectangle([fx(cut), y + 2, fx(b), y + 8], fill=(180, 220, 180))
            d.line([(L, yv(c["thr"])), (L + pw, yv(c["thr"]))], fill=(200, 120, 0), width=1)
            d.line([(L, yv(WAVE_MATCH)), (L + pw, yv(WAVE_MATCH))], fill=(60, 90, 200), width=1)
            d.line([(fx(f), yv(c["wave"][f])) for f in range(n)], fill=(60, 90, 200), width=1)
            d.line([(fx(f), yv(c["mel"][f])) for f in range(n)], fill=(220, 120, 0), width=2)
            if dv["frame"] is not None:
                d.line([(fx(dv["frame"]), y), (fx(dv["frame"]), y + h)], fill=(220, 30, 30), width=2)
                d.text((fx(dv["frame"]) + 4, y + 12), "DIVERGED", fill=(220, 30, 30), font=f14)
            if res["synced_until"]:
                su = res["synced_until"]["clip_s"] * SR / HOP
                d.line([(fx(su), y + 10), (fx(su), y + h)], fill=(220, 30, 30), width=1)
            d.text((L + 6, y + 12), "mel (orange) vs thr; wave NCC (blue) vs 0.4; grey = active, green = matched, top bar = spans",
                   fill=(80, 80, 80), font=f14)
        elif title.startswith("envelope"):
            d.rectangle(box, outline=(180, 180, 180))
            g = env["lag_s"]
            span = 0.4
            def yl(v: float, y: int = y, h: int = h, g: float = g, span: float = span) -> int:   # lag -> y pixel
                return y + h // 2 - int((v - g) / span * (h // 2 - 10))
            d.rectangle([L, yl(g + ENV_STEADY_S), L + pw, yl(g - ENV_STEADY_S)], fill=(225, 240, 225))
            d.line([(L, yl(g)), (L + pw, yl(g))], fill=(30, 130, 60), width=1)
            for v in (g - 0.3, g - 0.15, g + 0.15, g + 0.3):
                d.line([(L - 6, yl(v)), (L, yl(v))], fill=(120, 120, 120))
                d.text((L - 62, yl(v) - 8), f"{v:+.2f}", fill=(90, 90, 90), font=f14)
            d.text((L - 62, yl(g) - 8), f"{g:+.2f}", fill=(30, 130, 60), font=f14)
            for r in env["windows"]:
                a, b = (v * SR / HOP for v in (r["clip_t0"], r["clip_t1"]))
                yy = yl(np.clip(r["lag_s"], g - span, g + span))
                d.line([(fx(a), yy), (fx(b), yy)], fill=(40, 40, 160), width=1)
            for s in env["segments"]:
                a, b = (v * SR / HOP for v in s["clip_s"])
                yy = yl(np.clip(s["lag_s"], g - span, g + span))
                d.line([(fx(a), yy), (fx(b), yy)], fill=(200, 40, 140), width=4)
                d.text((fx(a) + 2, yy - 20), f"{s['lag_s']:+.2f}", fill=(200, 40, 140), font=f14)
            d.text((L + 6, y + 6), f"window lags (blue, 1.5 s windows) and lag segments (magenta) around the global "
                   f"{g:+.3f} s; green band = +/-{ENV_STEADY_S} s; lag > 0 = the take sings later", fill=(80, 80, 80), font=f14)
        else:
            A = c["mel_t"] - c["mel_t"].mean(axis=1, keepdims=True)
            B = c["mel_r"] - c["mel_r"].mean(axis=1, keepdims=True)
            A /= np.maximum(np.linalg.norm(A, axis=1, keepdims=True), 1e-9)
            B /= np.maximum(np.linalg.norm(B, axis=1, keepdims=True), 1e-9)
            S = A @ B.T
            side = h
            img = Image.fromarray(_heat(S, 0.0, 1.0)).resize((side, side), Image.BILINEAR)
            im.paste(img, (L, y))
            for k in range(0, side, 12):                  # dashed main diagonal: the window at the waveform lag
                d.line([(L + k, y + k), (L + min(side, k + 6), y + min(side, k + 6))], fill=(0, 220, 255), width=1)
            sec = side / (n * HOP / SR)
            for s in range(1, int(n * HOP / SR) + 1):
                d.line([(L + int(s * sec), y + side), (L + int(s * sec), y + side + 6)], fill=(90, 90, 90))
                d.text((L + int(s * sec) - 4, y + side + 6), f"{s}", fill=(90, 90, 90), font=f14)
            d.text((L + side + 12, y + 6), "bright line on the cyan diagonal = in sync at the waveform lag;", fill=(80, 80, 80), font=f14)
            d.text((L + side + 12, y + 26), "a parallel line above it = the take sings earlier, below = later (clip seconds)",
                   fill=(80, 80, 80), font=f14)
        y += h + 22
    im.save(out, quality=92)


# ---------------- review video ----------------
def _esc(s: str) -> str:
    """Text for a single-quoted drawtext value: a quote cannot be escaped inside one, so it becomes a typographic one."""
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def review_video(res: dict, name: str, song: Path, out: Path, lag_s: float, label: str, words: list[dict],
                 film: tuple[float, float] | None = None, fps: int = 30) -> None:
    """The song laid over the take at lag_s (normal speed), marked IN SYNC / DIVERGED - CUT HERE (tool 15)."""
    t0 = res["song_t0"]
    s_clip0 = t0 - lag_s                              # song time of clip time 0
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    shift = lag_s - res["lag_s"]                      # spans were measured at the waveform lag
    spans = [(a - shift, b - shift) for a, b in ((s["clip_s"][0], s["clip_s"][1]) for s in res["spans"])]
    su = res["synced_until"]["clip_s"] - shift if res["synced_until"] else None
    div = res["divergence"]["clip_s"]
    div = None if div is None else div - shift
    if div is not None and su is not None:            # a span bridged past the divergence is not shown as in sync
        spans = [(a, min(b, su)) for a, b in spans if a < su]
    in_sync = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in spans) or "0"
    vf = [f"fps={fps}", "drawbox=x=0:y=0:w=iw:h=86:color=black@0.62:t=fill",
          f"drawtext=fontfile={font}:text='{_esc(name)}  {_esc(label)}':x=24:y=14:fontsize=30:fontcolor=white",
          f"drawtext=fontfile={font}:text='song %{{eif\\:floor(t+{s_clip0:.4f})\\:d}}.%{{eif\\:mod(floor((t+{s_clip0:.4f})*100)\\,100)\\:d\\:2}} s   "
          f"clip %{{eif\\:floor(t)\\:d}}.%{{eif\\:mod(floor(t*100)\\,100)\\:d\\:2}} s':x=24:y=52:fontsize=24:fontcolor=white@0.9",
          f"drawbox=x=0:y=ih-16:w=iw:h=16:color=0x1fa83c@0.95:t=fill:enable='{in_sync}'"]
    if su is not None:
        vf.append(f"drawtext=fontfile={font}:text='IN SYNC':x=w-tw-28:y=22:fontsize=40:fontcolor=0x3ddc6a:"
                  f"enable='lt(t,{su:.3f})*({in_sync})'")
    if div is not None:
        vf.append(f"drawtext=fontfile={font}:text='DIVERGED - CUT HERE':x=w-tw-28:y=22:fontsize=40:fontcolor=0xff4040:"
                  f"enable='gte(t,{(su if su is not None else div):.3f})'")
    if film:
        a, b = film[0] - s_clip0, film[1] - s_clip0
        vf.append(f"drawbox=x=0:y=86:w=iw:h=8:color=0xffd400@0.95:t=fill:enable='between(t,{a:.3f},{b:.3f})'")
        vf.append(f"drawtext=fontfile={font}:text='FILM WINDOW':x=24:y=100:fontsize=22:fontcolor=0xffd400:"
                  f"enable='between(t,{a:.3f},{b:.3f})'")
    for w in words:
        a, b = w["start"] - s_clip0, w["end"] - s_clip0
        vf.append(f"drawtext=fontfile={font}:text='{_esc(w['text'])}':x=(w-tw)/2:y=h-110:fontsize=54:"
                  f"fontcolor=white:borderw=3:bordercolor=black@0.8:enable='between(t,{a:.3f},{b:.3f})'")
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
                                "-of", "csv=p=0", res["take"]], capture_output=True, text=True, check=True).stdout)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", res["take"], "-ss", f"{max(0.0, s_clip0):.4f}", "-t", f"{dur:.3f}",
                    "-i", str(song), "-map", "0:v:0", "-map", "1:a:0", "-vf", ",".join(vf), "-c:v", "libx264",
                    "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)


# ---------------- CLI ----------------
def public(res: dict) -> dict:
    return {k: v for k, v in res.items() if not k.startswith("_")}


def run_one(spec: dict, out_root: Path, song: Path | None, words_doc: dict | None, review: bool) -> dict:
    take, window = Path(spec["take"]), Path(spec["window"])
    name = spec.get("name") or take.stem
    res = check(take, window, float(spec["song_t0"]))
    out = out_root / name
    out.mkdir(parents=True, exist_ok=True)
    span = (res["song_t0"] - 1.0, res["song_t0"] + len(decode(take)) / SR + 1.0)
    words = words_in(words_doc, *span)
    prior = spec.get("prior")
    diagnostic(res, name, words, out / "sync.png", prior)
    pub = public(res)
    pub["name"] = name
    if spec.get("film"):
        pub["film_window_song_s"] = spec["film"]
    if prior:
        pub["prior"] = prior
    pub["reviews"] = []
    if review and song:
        sha12 = res["take_sha256"][:12]
        cands = [("placement", res["placement"]["lag_s"], f"lag {res['placement']['lag_s']:+.3f} s · {res['placement']['method']}")]
        if prior and abs(prior["lag_s"] - res["placement"]["lag_s"]) >= 1.5 / 30:
            cands.append(("prior", prior["lag_s"], f"lag {prior['lag_s']:+.3f} s · {prior['why']}"))
        for key, lag, label in cands:
            p = out / f"review-{name}-{sha12}-{key}-lag{lag:+.3f}.mp4"
            review_video(res, name, song, p, lag, label, words, tuple(spec["film"]) if spec.get("film") else None)
            pub["reviews"].append({"kind": key, "lag_s": lag, "path": str(p), "sha256": sha256(p)})
    (out / "sync.json").write_text(json.dumps(pub, ensure_ascii=False, indent=1) + "\n")
    return pub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--take", type=Path)
    ap.add_argument("--window", type=Path, help="the exact vocal window file sent with the take")
    ap.add_argument("--song-t0", type=float, help="song time of the window's first sample (clip time 0)")
    ap.add_argument("--name")
    ap.add_argument("--manifest", type=Path, help='JSON {"song": path, "words": path, "takes": [{"name", "take", '
                    '"window", "song_t0", "film": [s0, s1], "prior": {"lag_s", "why"}}]}')
    ap.add_argument("--song", type=Path, help="the song mix laid over the take in the review video")
    ap.add_argument("--words", type=Path, help="timed words (lines[].words[]) in song seconds, for labels")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--review", action="store_true", help="also write the review video(s)")
    args = ap.parse_args()
    if args.manifest:
        man = json.loads(args.manifest.read_text())
        specs = man["takes"]
        song = Path(man["song"]) if man.get("song") else args.song
        words = Path(man["words"]) if man.get("words") else args.words
    else:
        if not (args.take and args.window and args.song_t0 is not None):
            ap.error("--take, --window and --song-t0 (or --manifest) are required")
        specs = [{"name": args.name, "take": str(args.take), "window": str(args.window), "song_t0": args.song_t0}]
        song, words = args.song, args.words
    words_doc = json.loads(words.read_text()) if words else None
    args.out.mkdir(parents=True, exist_ok=True)
    summary = []
    for spec in specs:
        r = run_one(spec, args.out, song, words_doc, args.review)
        summary.append({k: r[k] for k in ("name", "take_sha256", "lag_s", "ncc", "copy", "divergence", "synced_until",
                                          "spans", "placement")} | {"envelope": {k: r["envelope"][k] for k in ("lag_s", "ncc", "max_dev_s", "steady", "segments")}})
        print(json.dumps(summary[-1], ensure_ascii=False))
    (args.out / "sync-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
