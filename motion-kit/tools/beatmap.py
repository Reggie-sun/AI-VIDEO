#!/usr/bin/env python3
"""Beat map, hits and sections for a song (numpy only; no librosa/torch in this repo).

Follows the claudia.gallery toolkit spec (beat map §6, sections and hits §7) adapted to what is
available here: band-split spectral flux instead of separated stems (pass --drums STEM when a
drum/instrumental stem exists), Ellis-style dynamic-programming beat tracking (tempo may drift),
beats snapped to kick onsets within ±30 ms, downbeat phase voted by kick energy and harmony change.

Outputs (formats of the wiki's Data formats page):
  beats.json  {duration, beats, downbeats, tempo[{t,bpm}], downbeat_phase, downbeat_method, bars_energy}
  hits.json   {kick, snare, hat, hits[{t,score}], risers[{t0,t1,land}], fills, vocal_entries, env24{low,mid,high}}
  beatmap.png  onset envelope with beats/downbeats/hits for a visual check

Usage:
  uv run python motion-kit/tools/beatmap.py --audio song.wav --out analysis/ [--bpm-range 110 140] [--downbeat-phase N]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

SR = 22050
NFFT = 2048          # harmony / timbre analysis
NFFT_ON = 1024       # onset analysis: shorter window, less smearing of attacks
HOP = 256
ON_OFF = NFFT_ON / 2 / SR   # onset frame i is centred at i*HOP/SR + ON_OFF


def t_of(i: float) -> float:
    return i * HOP / SR + ON_OFF


def i_of(t: float) -> int:
    return int(round((t - ON_OFF) * SR / HOP))


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def stft_mag(x: np.ndarray, nfft: int = NFFT) -> np.ndarray:
    if x.ndim != 1 or len(x) < nfft:
        raise ValueError(f"audio must be mono and contain at least {nfft} samples")
    win = np.hanning(nfft).astype(np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(x, nfft)[::HOP]
    return np.abs(np.fft.rfft(frames * win, axis=1)).astype(np.float32)          # n x (nfft/2+1)


def band_flux(S: np.ndarray, lo: float, hi: float) -> np.ndarray:
    f = np.fft.rfftfreq(NFFT_ON, 1 / SR)
    sel = (f >= lo) & (f < hi)
    L = np.log1p(100 * S[:, sel])
    d = np.diff(L, axis=0, prepend=L[:1])
    o = np.maximum(d, 0).sum(axis=1)
    o -= np.convolve(o, np.ones(16) / 16, mode="same")                          # local mean removal
    o = np.maximum(o, 0)
    return o / (o.max() + 1e-9)


def peaks(o: np.ndarray, thresh: float, min_gap_s: float) -> list[float]:
    t = []
    gap = int(min_gap_s * SR / HOP)
    last = -gap
    adapt = np.convolve(o, np.ones(32) / 32, mode="same")
    for i in range(1, len(o) - 1):
        if o[i] >= o[i - 1] and o[i] > o[i + 1] and o[i] > thresh + adapt[i] and i - last >= gap:
            t.append(t_of(i))
            last = i
    return t


def tempo_estimate(o: np.ndarray, lo: float, hi: float) -> float:
    ac = np.correlate(o, o, mode="full")[len(o) - 1:]
    fps = SR / HOP
    best, bscore = lo, -1.0
    for bpm in np.arange(lo, hi + 1e-9, 0.05):
        lag = 60 * fps / bpm
        i = int(lag)
        f = lag - i
        if i + 1 >= len(ac):
            continue
        v = ac[i] * (1 - f) + ac[i + 1] * f
        # reward the half-bar and bar periodicities too (avoids half/double time)
        for m, w in ((2, 0.5), (4, 0.5)):
            j = lag * m
            k = int(j)
            if k + 1 < len(ac):
                v += w * (ac[k] * (1 - (j - k)) + ac[k + 1] * (j - k))
        if v > bscore:
            best, bscore = bpm, v
    return float(best)


def dp_beats(o: np.ndarray, bpm: float, tightness: float = 100.0) -> list[float]:
    fps = SR / HOP
    period = 60 * fps / bpm
    n = len(o)
    score = o.copy().astype(np.float64)
    back = -np.ones(n, dtype=int)
    lo, hi = int(round(period / 2)), int(round(period * 2))
    for i in range(n):
        a, b = i - hi, i - lo
        if b <= 0:
            continue
        js = np.arange(max(0, a), b)
        if not len(js):
            continue
        pen = -tightness * (np.log((i - js) / period)) ** 2
        cand = score[js] + pen
        k = int(np.argmax(cand))
        score[i] = o[i] + cand[k]
        back[i] = js[k]
    end = int(np.argmax(score[-int(period * 2):])) + n - int(period * 2)
    beats = []
    while end >= 0:
        beats.append(end)
        end = back[end]
    return [t_of(b) for b in reversed(beats)]


def snap(beats: list[float], onsets: list[float], tol: float = 0.03) -> list[float]:
    if not onsets:
        return beats
    on = np.array(onsets)
    out = []
    for b in beats:
        j = int(np.argmin(np.abs(on - b)))
        out.append(float(on[j]) if abs(on[j] - b) <= tol else b)
    return out


def chroma_at(S: np.ndarray, times: list[float]) -> np.ndarray:
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    sel = (f > 55) & (f < 2000)
    pc = (np.round(12 * np.log2(f[sel] / 440.0)) % 12).astype(int)
    out = []
    for t in times:
        i = min(len(S) - 1, int(t * SR / HOP))
        frame = S[max(0, i - 4): i + 8, sel].mean(axis=0)
        c = np.bincount(pc, weights=frame, minlength=12)
        out.append(c / (np.linalg.norm(c) + 1e-9))
    return np.array(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--drums", type=Path, help="optional drum/instrumental stem for onsets")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--bpm-range", type=float, nargs=2, default=(100.0, 150.0))
    ap.add_argument("--downbeat-phase", type=int, default=None, help="manual override 0..3")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    x = load(args.audio)
    dur = len(x) / SR
    try:
        S = stft_mag(x)
        So = stft_mag(load(args.drums) if args.drums else x, NFFT_ON)
    except ValueError as exc:
        ap.error(str(exc))
    o_full = band_flux(So, 30, 11000)
    o_kick = band_flux(So, 30, 150)
    o_snare = band_flux(So, 150, 5000)
    o_hat = band_flux(So, 6000, 11000)

    bpm = tempo_estimate(o_full, *args.bpm_range)
    beats = dp_beats(o_full + 0.8 * o_kick, bpm)
    kick_t = peaks(o_kick, 0.18, 0.12)
    beats = snap(beats, kick_t, 0.03)

    # impacts first (they vote for the downbeat phase in four-on-the-floor music)
    rms = np.sqrt(np.convolve(x ** 2, np.ones(HOP) / HOP, mode="same")[::HOP] + 1e-12)
    fps = SR / HOP
    imp = []
    for i in range(len(rms)):
        a = rms[max(0, i - int(1.5 * fps)): i]
        b = rms[i: i + int(0.6 * fps)]
        if len(a) < 5 or len(b) < 5:
            continue
        sc = (b.mean() - a.mean()) / (a.mean() + 1e-6)
        if sc > 0.22:
            imp.append((i * HOP / SR, float(sc)))
    raw_hits = []
    for t, sc in sorted(imp, key=lambda z: -z[1]):
        if all(abs(t - h[0]) > 2.0 for h in raw_hits):
            raw_hits.append((t, min(1.0, sc)))

    # downbeat: harmony change (if real) -> strongest impact -> kick energy; manual override wins
    kick_at = [o_kick[min(len(o_kick) - 1, max(0, i_of(b)))] for b in beats]
    kick_vote = [float(np.mean(kick_at[p::4])) if len(kick_at[p::4]) else 0 for p in range(4)]
    ch = chroma_at(S, beats)
    change = np.r_[0, 1 - (ch[1:] * ch[:-1]).sum(axis=1)]
    chord_vote = [float(np.mean(change[p::4])) if len(change[p::4]) else 0 for p in range(4)]
    kp, cp = int(np.argmax(kick_vote)), int(np.argmax(chord_vote))
    others = sorted(chord_vote, reverse=True)
    chord_strong = others[0] >= 0.08 and others[0] >= 1.5 * max(others[1], 1e-9)   # a static pad votes noise
    strong = [h for h in raw_hits if h[1] >= 0.6]
    if args.downbeat_phase is not None:
        phase, method = args.downbeat_phase, "manual"
    elif chord_strong:
        phase, method = cp, "harmony"
    elif strong:
        t_imp = max(strong, key=lambda h: h[1])[0]
        # the impact's energy jump starts slightly before its beat (a riser leads in): take the next beat within 0.35 s
        j = min(range(len(beats)), key=lambda k: (beats[k] < t_imp - 0.05, abs(beats[k] - t_imp)))
        phase, method = j % 4, "impact"
    else:
        phase, method = kp, "kick"
    downbeats = beats[phase::4]

    # local tempo from beat intervals
    tempo = [{"t": round(beats[i], 3), "bpm": round(60 / (beats[i + 1] - beats[i]), 2)}
             for i in range(0, len(beats) - 1, 8)]

    # hits
    snare_t = [t for t in peaks(o_snare, 0.2, 0.1) if min((abs(t - k) for k in kick_t), default=1) > 0.045]
    hat_t = [t for t in peaks(o_hat, 0.15, 0.06) if min((abs(t - k) for k in kick_t), default=1) > 0.045]
    hits = []
    for t, sc in raw_hits:
        d = min(downbeats, key=lambda d: abs(d - t)) if downbeats else t
        hits.append({"t": round(d if abs(d - t) <= 0.65 else t, 4), "score": round(sc, 3)})
    hits.sort(key=lambda h: h["t"])
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    hb = S[:, (f >= 4000) & (f < 11000)].sum(axis=1)
    k = max(1, int(0.25 * fps))
    hbs = np.convolve(hb, np.ones(k) / k, mode="same")
    risers, i = [], 0
    while i < len(hbs) - int(fps):
        j = i
        while j + 1 < len(hbs) and hbs[j + 1] >= hbs[j] * 0.995:
            j += 1
        if (j - i) / fps >= 1.0 and hbs[j] > 2.0 * max(hbs[i], 1e-9):
            t0, t1 = i * HOP / SR, j * HOP / SR
            land = next((h["t"] for h in hits if t1 - 0.3 <= h["t"] <= t1 + 0.7), round(t1, 3))
            risers.append({"t0": round(t0, 3), "t1": round(t1, 3), "land": land})
            i = j
        i += 1

    def env(lo, hi):
        sel = (f >= lo) & (f < hi)
        e = S[:, sel].sum(axis=1)
        tt = np.arange(0, dur, 1 / 24)
        v = np.interp(tt * fps, np.arange(len(e)), e)
        return [round(float(z), 4) for z in v / (v.max() + 1e-9)]

    bars_energy = []
    for k in range(len(downbeats) - 1):
        a, b = int(downbeats[k] * fps), int(downbeats[k + 1] * fps)
        bars_energy.append(float(rms[a:b].mean()) if b > a else 0.0)
    if bars_energy:
        m = max(bars_energy)
        bars_energy = [int(round(9 * e / m)) for e in bars_energy]

    beats_doc = {"duration": round(dur, 3), "beats": [round(b, 4) for b in beats],
                 "downbeats": [round(b, 4) for b in downbeats], "tempo": tempo, "bpm_global": round(bpm, 2),
                 "downbeat_phase": phase, "downbeat_method": method,
                 "votes": {"kick": [round(v, 3) for v in kick_vote], "harmony": [round(v, 3) for v in chord_vote]},
                 "bars_energy_0_9": bars_energy}
    hits_doc = {"kick": [round(t, 4) for t in kick_t], "snare": [round(t, 4) for t in snare_t],
                "hat": [round(t, 4) for t in hat_t], "hits": hits, "risers": risers, "fills": [],
                "vocal_entries": [], "env24": {"low": env(30, 150), "mid": env(150, 4000), "high": env(4000, 11000)}}
    (args.out / "beats.json").write_text(json.dumps(beats_doc, indent=1))
    (args.out / "hits.json").write_text(json.dumps(hits_doc))

    try:
        from PIL import Image, ImageDraw
        W, H = 2400, 360
        im = Image.new("RGB", (W, H), (250, 250, 250))
        d = ImageDraw.Draw(im)
        sx = W / dur
        pts = [(i / fps * sx, H - 40 - o_full[i] * 260) for i in range(0, len(o_full), 2)]
        d.line(pts, fill=(80, 80, 80), width=1)
        for b in beats:
            d.line([(b * sx, H - 40), (b * sx, H - 300)], fill=(60, 140, 255), width=1)
        for b in downbeats:
            d.line([(b * sx, H - 40), (b * sx, 20)], fill=(230, 50, 50), width=2)
        for h in hits:
            d.ellipse([(h["t"] * sx - 6, 12), (h["t"] * sx + 6, 24)], fill=(0, 170, 90))
        for s in range(int(dur) + 1):
            d.text((s * sx + 2, H - 30), f"{s}s", fill=(0, 0, 0))
        im.save(args.out / "beatmap.png")
    except Exception as exc:                                                       # plot is optional evidence
        print("plot skipped:", exc)
    print(json.dumps({"bpm": round(bpm, 2), "beats": len(beats), "downbeat_phase": phase, "method": method,
                      "first_downbeats": [round(b, 3) for b in downbeats[:4]], "hits": hits[:6],
                      "risers": risers[:4]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
