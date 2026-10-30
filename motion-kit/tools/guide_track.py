#!/usr/bin/env python3
"""Synthesize a TEMPORARY guide track from beats.json/hits.json so picture sync can be
judged by ear before the real music exists. Never delivered as music.

Kick on every beat (harder on downbeats), closed hat on eighths, snare on beats 2 and 4,
a filtered-noise riser over each riser span, a low impact on each hit, and a quiet dark pad.
48 kHz stereo 16-bit, soft-limited, ~ -16 dBFS RMS.

Usage: uv run python motion-kit/tools/guide_track.py --beats B.json --hits H.json --start 0 --dur 10 --out guide.wav
"""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

import numpy as np

SR = 48000


def env_exp(n: int, tau: float) -> np.ndarray:
    return np.exp(-np.arange(n) / (tau * SR))


def kick(strength: float) -> np.ndarray:
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env_exp(n, 0.16)
    click = np.random.default_rng(1).standard_normal(n) * env_exp(n, 0.0025) * 0.25
    return (body + click) * strength


def hat(seed: int, level: float) -> np.ndarray:
    n = int(0.05 * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    x = np.diff(np.concatenate([[0.0], x]))            # crude high-pass
    return x * env_exp(n, 0.012) * level


def snare(seed: int) -> np.ndarray:
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(seed).standard_normal(n) * env_exp(n, 0.06)
    tone = np.sin(2 * np.pi * 185 * t) * env_exp(n, 0.04)
    return (0.5 * noise + 0.6 * tone) * 0.45


def riser(dur: float, seed: int) -> np.ndarray:
    n = int(dur * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    out = np.zeros(n)
    a = 0.0
    for i in range(n):                                   # one-pole low-pass opening up
        c = 0.02 + 0.5 * (i / n) ** 2
        a += c * (x[i] - a)
        out[i] = a
    return out * np.linspace(0.05, 0.9, n) ** 2 * 0.8


def impact() -> np.ndarray:
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 32 + 80 * np.exp(-t / 0.06)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.55)
    crash = np.random.default_rng(9).standard_normal(n) * env_exp(n, 0.35) * 0.18
    return (boom * 1.1 + crash)


def pad(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    tones = [55.0, 65.41, 82.41, 110.0]                  # A minor-ish drone
    x = sum(np.sin(2 * np.pi * f * t + i) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t) for i, f in enumerate(tones))
    return x / 12 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t))


def place(buf: np.ndarray, sig: np.ndarray, at: float) -> None:
    i = int(round(at * SR))
    if i >= len(buf) or i + len(sig) <= 0:
        return
    s0 = max(0, -i)
    i = max(0, i)
    m = min(len(buf) - i, len(sig) - s0)
    buf[i:i + m] += sig[s0:s0 + m]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", type=Path, required=True)
    ap.add_argument("--hits", type=Path, required=True)
    ap.add_argument("--start", type=float, default=0.0, help="song time of comp t=0")
    ap.add_argument("--dur", type=float, default=10.0)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    beats = json.loads(args.beats.read_text())
    hits = json.loads(args.hits.read_text())
    n = int(args.dur * SR)
    buf = np.zeros(n)
    downs = set(round(d, 4) for d in beats["downbeats"])
    b = beats["beats"]
    for i, s in enumerate(b):
        t = s - args.start
        if -0.5 < t < args.dur:
            place(buf, kick(1.0 if round(s, 4) in downs else 0.75), t)
            nxt = b[i + 1] if i + 1 < len(b) else s + (s - b[i - 1])
            place(buf, hat(i * 2, 0.10), t + (nxt - s) / 2)
            place(buf, hat(i * 2 + 1, 0.05), t)
    for s in hits.get("snare", []):
        if -0.5 < s - args.start < args.dur:
            place(buf, snare(int(s * 100)), s - args.start)
    for r in hits.get("risers", []):
        if r["land"] - args.start > 0 and r["t0"] - args.start < args.dur:
            place(buf, riser(r["land"] - r["t0"], 3), r["t0"] - args.start)
    for h in hits.get("hits", []):
        if 0 <= h["t"] - args.start < args.dur:
            place(buf, impact(), h["t"] - args.start)
    buf += pad(n) * 0.35
    fade = int(0.25 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    rms = np.sqrt(np.mean(buf ** 2)) + 1e-9
    buf *= (10 ** (-16 / 20)) / rms
    buf = np.tanh(buf * 1.2) / np.tanh(1.2)              # soft limit
    st = np.stack([buf, buf], 1)
    pcm = (np.clip(st, -1, 1) * 32767 * 0.95).astype("<i2")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(args.out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {args.out} {args.dur}s peak={np.abs(st).max():.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
