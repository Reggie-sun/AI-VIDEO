#!/usr/bin/env python3
"""IRIS EP01 song v2: place the voiceover phrases on the bed's beat grid and mix.

  uv run python outputs/ai-city-takeover/ep01/v2/song/assemble_vo.py [--dry-run]

Inputs (this folder): bed-01/<mp3> + bed-01/beatmap/beats.json, vo/<section>/{<mp3>, align.json},
placement.json. Each phrase is cut from the clean TTS at its measured speech onset/offset (silence
near the Whisper word boundaries), so a phrase's first syllable lands on its target beat.
Outputs: mix/IRIS-01-v2.wav (48 kHz stereo), mix/vo-stem.wav, mix/placement-result.json.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SR = 48000
HOP = 240                       # 5 ms envelope hop
PRE, POST = 0.015, 0.060        # seconds kept before the onset / after the offset of a phrase
FMT = f"aformat=sample_fmts=fltp:sample_rates={SR}:channel_layouts=stereo"


def decode(path: Path, channels: int) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(channels), "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, channels).copy()


def words_of(phrase: str) -> list[str]:
    return [w for w in phrase.split() if any(c.isalnum() for c in w)]


def phrase_spans(align: dict, phrases: list[str]) -> list[tuple[float, float, list[dict]]]:
    """Whisper span and words of each phrase, matched in order on alphanumeric word content."""
    norm = lambda s: "".join(c for c in s.lower() if c.isalnum())
    aw = [w for w in align["words"] if norm(w["text"])]
    # Whisper splits hyphenated words ("forty", "-seven"); merge tokens until they match lyric words
    out, k = [], 0
    for p in phrases:
        ws = []
        for lw in words_of(p):
            target, acc, parts = norm(lw), "", []
            while k < len(aw) and len(acc) < len(target):
                acc += norm(aw[k]["text"])
                parts.append(aw[k])
                k += 1
            if acc != target:
                raise SystemExit(f"alignment does not match lyric word {lw!r} (got {acc!r})")
            ws.append({"text": lw, "start": parts[0]["start"], "end": parts[-1]["end"]})
        out.append((ws[0]["start"], ws[-1]["end"], ws))
    if k != len(aw):
        raise SystemExit("alignment has words beyond the placement phrases")
    return out


def envelope(x: np.ndarray) -> tuple[np.ndarray, float]:
    n = len(x) // HOP
    env = 20 * np.log10(np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1e-9)
    return env, env.max() - 42


def phrase_bounds(x: np.ndarray, spans) -> list[tuple[float, float]]:
    """Speech onset/offset of each phrase. Between two phrases cut in the longest silence near the
    Whisper boundary (Whisper word starts absorb the preceding pause), else at the quietest frame."""
    env, thr = envelope(x)
    f = lambda t: int(round(t * SR / HOP))
    cuts = []
    for (_, e, _), (s, _, _) in zip(spans, spans[1:]):
        a, b = max(0, f(e - 0.25)), min(len(env), f(s + 0.45))
        quiet, best, j = env[a:b] < thr, None, 0
        while j < b - a:
            if quiet[j]:
                k = j
                while k < b - a and quiet[k]:
                    k += 1
                if best is None or k - j > best[1] - best[0]:
                    best = (j, k)
                j = k
            else:
                j += 1
        if best and best[1] - best[0] >= 6:       # >= 30 ms of silence
            cuts.append(((a + best[0]) * HOP / SR, (a + best[1]) * HOP / SR))
        else:
            k = a + int(np.argmin(np.convolve(env[a:b], np.ones(5) / 5, mode="same")))
            cuts.append((k * HOP / SR, k * HOP / SR))
    edges = [0.0] + [c for pair in cuts for c in pair] + [len(x) / SR]
    out = []
    for i in range(len(spans)):
        lo, hi = f(edges[2 * i]), f(edges[2 * i + 1])
        voiced = np.nonzero(env[lo:hi] > thr)[0]
        if not len(voiced):
            raise SystemExit(f"no speech found for phrase {i}")
        out.append(((lo + voiced[0]) * HOP / SR, (lo + voiced[-1] + 1) * HOP / SR))
    return out


def word_times(ws, a, b, env, thr) -> list[tuple[float, float]]:
    """Contiguous word spans inside a phrase [a, b]. Whisper word starts absorb a preceding pause,
    so a start that falls in silence moves to the next voiced frame and the previous word ends at the
    last voiced frame before that silence."""
    voiced = lambda t: env[min(len(env) - 1, int(t * SR / HOP))] > thr
    starts = [a] + [min(max(w["start"], a), b) for w in ws[1:]]
    ends = starts[1:] + [b]
    for k in range(1, len(ws)):
        t = starts[k]
        if not voiced(t):
            on = t
            while on < b and not voiced(on):
                on += HOP / SR
            off = t
            while off > starts[k - 1] and not voiced(off):
                off -= HOP / SR
            starts[k], ends[k - 1] = on, off + HOP / SR
    out = []
    for s, e in zip(starts, ends):
        s = max(s, out[-1][1]) if out else s
        out.append((s, max(e, s + 0.04)))
    return out


def beat_time(beats: list[float], b: float) -> float:
    i = min(int(np.floor(b)), len(beats) - 2)
    return beats[i] + (b - i) * (beats[i + 1] - beats[i])


def beat_of(beats: list[float], t: float) -> float:
    i = max(0, min(int(np.searchsorted(beats, t, side="right")) - 1, len(beats) - 2))
    return i + (t - beats[i]) / (beats[i + 1] - beats[i])


def fit(beats, sec, durs):
    """Smallest tempo (speech speed-up) at which the phrases, each starting on the next free grid
    step after the previous one ends, all finish inside the section window."""
    b0, b1 = sec["window"]
    grid, gap = sec.get("grid", 0.5), sec.get("min_gap", 0.08)
    for tempo in np.arange(1.0, sec.get("max_tempo", 1.2) + 1e-9, 0.01):
        cursor, onsets = beat_time(beats, b0), []
        for d in durs:
            g = np.ceil(beat_of(beats, cursor) / grid - 1e-6) * grid
            onsets.append(g)
            cursor = beat_time(beats, g) + d / tempo + gap
        if cursor - gap <= beat_time(beats, b1):
            return round(float(tempo), 2), onsets
    raise SystemExit(f"section {sec['name']} does not fit its window even at max tempo")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    plan = json.loads((HERE / "placement.json").read_text(encoding="utf-8"))
    beats = json.loads((HERE / "bed-01/beatmap/beats.json").read_text())["beats"]
    bed = decode(HERE / plan["bed"], 2)
    total = len(bed)
    vo = np.zeros(total, np.float32)
    report, placed = [], []
    for sec in plan["sections"]:
        d = HERE / "vo" / sec["name"]
        mp3 = next(d.glob("*.mp3"))
        x = decode(mp3, 1)[:, 0]
        spans = phrase_spans(json.loads((d / "align.json").read_text()), sec["phrases"])
        bounds = phrase_bounds(x, spans)
        env, thr = envelope(x)
        tempo, grid_beats = fit(beats, sec, [b - a for a, b in bounds])
        print(f"[{sec['name']}] tempo {tempo}")
        for text, (a, b), (_, _, ws), gb in zip(sec["phrases"], bounds, spans, grid_beats):
            seg = x[max(0, int((a - PRE) * SR)):int((b + POST) * SR)]
            if tempo != 1.0:
                seg = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                                      "-af", f"atempo={tempo}", "-f", "f32le", "-"], input=seg.tobytes(),
                                     capture_output=True, check=True).stdout
                seg = np.frombuffer(seg, np.float32)
            seg = seg * 10 ** (sec.get("gain_db", 0.0) / 20)
            t = beat_time(beats, gb)
            s0 = int(round((t - PRE / tempo) * SR))
            fade = np.ones(len(seg), np.float32)
            n = int(0.004 * SR)
            fade[:n] = np.linspace(0, 1, n)
            fade[-n * 4:] = np.linspace(1, 0, n * 4)
            if s0 < 0 or s0 + len(seg) > total:
                raise SystemExit(f"phrase {text!r} falls outside the bed")
            vo[s0:s0 + len(seg)] += seg * fade
            onset, end = t, t + (b - a) / tempo
            report.append({"section": sec["name"], "text": text, "beat": float(gb), "onset": round(onset, 4),
                           "end": round(end, 4), "tempo": tempo, "source_span": [round(a, 4), round(b, 4)],
                           "words": [{"text": w["text"], "start": round(onset + (s - a) / tempo, 4),
                                      "end": round(onset + (e - a) / tempo, 4)}
                                     for w, (s, e) in zip(ws, word_times(ws, a, b, env, thr))]})
            placed.append((onset, end, text))
    placed.sort()
    clashes = [(p, q) for p, q in zip(placed, placed[1:]) if p[1] > q[0] - 0.05]
    for o, e, txt in placed:
        print(f"{o:7.3f}-{e:7.3f}  {txt}")
    for p, q in clashes:
        print(f"CLASH: {p[2]!r} ends {p[1]:.3f} > {q[2]!r} starts {q[0]:.3f}")
    if args.dry_run:
        return
    if clashes:
        raise SystemExit("resolve clashes before mixing")
    out = HERE / "mix"
    out.mkdir(exist_ok=True)
    stem = out / "vo-stem.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s24le", str(stem)], input=vo.tobytes(), check=True)
    vo_proc, bed_duck, pre_master, mix = (out / n for n in
                                          ("vo-processed.wav", "bed-ducked.wav", "pre-master.wav", "IRIS-01-v2.wav"))
    ff = lambda *a: subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True,
                                   capture_output=True, text=True)
    ff("-i", stem, "-af", f"{plan['vocal_chain']},pan=stereo|c0=c0|c1=c0,{FMT}", "-c:a", "pcm_f32le", vo_proc)
    ff("-i", HERE / plan["bed"], "-i", vo_proc, "-filter_complex",
       f"[0:a]aresample={SR},{FMT}[b];[1:a]{FMT}[s];[b][s]sidechaincompress={plan['duck']}[o]",
       "-map", "[o]", "-c:a", "pcm_f32le", bed_duck)
    v, b = decode(vo_proc, 2), decode(bed_duck, 2)
    n = min(len(v), len(b))
    v, b = v[:n], b[:n]
    win = SR // 20                                  # 50 ms windows where the voice is speaking
    k = n // win
    pw = lambda y: (y[:k * win] ** 2).mean(1).reshape(k, win).mean(1)
    pv, pb = pw(v), pw(b)
    active = pv > pv.max() * 10 ** (-30 / 10)
    over = 10 * np.log10(pv[active].mean() / pb[active].mean())
    gain_db = plan["vo_over_bed_db"] - over
    m = b + v * 10 ** (gain_db / 20)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", str(pre_master)], input=m.astype(np.float32).tobytes(), check=True)
    # gain to the loudness target first, then a peak limiter at the ceiling (sample peak, 0.5 dB under TP)
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre_master), "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"],
                           check=True, capture_output=True, text=True).stderr
    meas = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    lufs, ceiling = plan["lufs"], plan["true_peak_db"] - 0.5
    make_up = lufs - float(meas["input_i"])
    ff("-i", pre_master, "-af", f"volume={make_up:.2f}dB,alimiter=limit={10 ** (ceiling / 20):.4f}:attack=2:"
       f"release=50:level=0", "-ar", str(SR), "-c:a", "pcm_s24le", mix)
    print(f"voice over bed before gain {over:+.1f} dB -> applied {gain_db:+.1f} dB; "
          f"pre-master {meas['input_i']} LUFS / {meas['input_tp']} dBTP -> make-up {make_up:+.2f} dB, limiter {ceiling} dBFS")
    (out / "placement-result.json").write_text(json.dumps({
        "bed": plan["bed"], "phrases": report, "sample_rate": SR, "voice_gain_db": round(float(gain_db), 2)}, ensure_ascii=False, indent=1) + "\n")
    print("wrote", mix)


if __name__ == "__main__":
    main()
