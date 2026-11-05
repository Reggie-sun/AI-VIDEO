#!/usr/bin/env python3
"""IRIS EP01 full song v3 (2:40): splice the bed, place the voiceover on the bar grid, mix and master.

  uv run python outputs/ai-city-takeover/ep01/v2/song-full/assemble_full.py [--bed-only] [--dry-run]

Adapted from ../song/assemble_vo.py (v2, approved 30.5 s song). Inputs are named in placement.json:
bed sources (bed-01, the approved v2 bed for the three choruses, patch-01, patch-02) with one time
shift per segment (master = source + shift) and a short crossfade per splice; VO sections, each a TTS
file with Whisper align.json whose phrases are packed into bar-map windows on the 8th-note grid.
Outputs (mix/): bed-spliced.wav, vo-stem.wav, IRIS-01-full-v3.{wav,mp3} (48 kHz stereo), placement-result.json.
"""
import argparse
import hashlib
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- bed: segments + crossfaded splices

def build_bed(spec: dict, total: int) -> tuple[np.ndarray, list[dict]]:
    """Each segment plays its source at master = source + shift; consecutive segments overlap only inside
    their splice window, where an equal-gain raised-cosine crossfade joins them. A splice with search_ms
    is a re-timing splice inside one source: the next segment's shift is moved within +-search_ms to the
    lag with the highest waveform correlation over the window (WSOLA-style), so the repeated or dropped
    audio joins in phase."""
    srcs = {k: decode(HERE / v, 2) for k, v in spec["sources"].items()}
    segs, splices = [dict(s) for s in spec["segments"]], spec["splices"]
    if len(splices) != len(segs) - 1:
        raise SystemExit("bed: need exactly one splice between consecutive segments")
    idx = lambda t: int(round(t * SR))

    def take(seg, a, b):                       # master samples [a, b) of a segment, zero outside its source
        x, off = srcs[seg["src"]], idx(seg["shift_s"])
        out = np.zeros((b - a, 2), np.float32)
        lo, hi = max(a - off, 0), min(b - off, len(x))
        if hi > lo:
            out[lo - (a - off):hi - (a - off)] = x[lo:hi]
        return out

    report = []
    for k, sp in enumerate(splices):
        a, b = idx(sp["xfade_s"][0]), idx(sp["xfade_s"][1])
        prev, nxt = segs[k], segs[k + 1]
        corr = None
        if sp.get("search_ms"):
            if prev["src"] != nxt["src"]:
                raise SystemExit(f"splice {k}: search only within one source")
            ref = take(prev, a, b).mean(1)
            best = (-2.0, nxt["shift_s"])
            r = int(sp["search_ms"] / 1000 * SR)
            for d in range(-r, r + 1):
                trial = dict(nxt, shift_s=nxt["shift_s"] + d / SR)
                y = take(trial, a, b).mean(1)
                c = float((ref * y).sum() / (np.sqrt((ref ** 2).sum() * (y ** 2).sum()) + 1e-12))
                if c > best[0]:
                    best = (c, trial["shift_s"])
            corr, nxt["shift_s"] = best[0], round(best[1], 6)
        report.append({"splice": k, "xfade_s": sp["xfade_s"], "from": prev["src"], "to": nxt["src"],
                       "shift_from_s": prev["shift_s"], "shift_to_s": nxt["shift_s"],
                       "jump_ms": round(1000 * (nxt["shift_s"] - prev["shift_s"]), 2) if prev["src"] == nxt["src"] else None,
                       "window_corr": None if corr is None else round(corr, 4), "at": sp.get("at", "")})
    out = np.zeros((total, 2), np.float32)
    for k, seg in enumerate(segs):
        a = 0 if k == 0 else idx(splices[k - 1]["xfade_s"][0])
        b = total if k == len(segs) - 1 else idx(splices[k]["xfade_s"][1])
        g = np.ones(b - a, np.float32)
        if k > 0:                                                  # fade in over the previous splice
            n = idx(splices[k - 1]["xfade_s"][1]) - a
            g[:n] = np.sin(np.linspace(0, np.pi / 2, n, endpoint=False) + np.pi / (4 * n)) ** 2
        if k < len(segs) - 1:                                      # fade out over the next splice
            n = b - idx(splices[k]["xfade_s"][0])
            g[-n:] = np.cos(np.linspace(0, np.pi / 2, n, endpoint=False) + np.pi / (4 * n)) ** 2
        out[a:b] += take(seg, a, b) * g[:, None]
        seg["master_s"] = [round(a / SR, 6), round(b / SR, 6)]
        seg["source_s"] = [round(a / SR - seg["shift_s"], 6), round(b / SR - seg["shift_s"], 6)]
    return out, [{"src": s["src"], "file": spec["sources"][s["src"]], "shift_s": s["shift_s"],
                  "master_s": s["master_s"], "source_s": s["source_s"], "covers": s.get("covers", "")}
                 for s in segs], report


# ---------------------------------------------------------------- voiceover (from v2 assemble_vo.py)

def words_of(phrase: str) -> list[str]:
    return [w for w in phrase.split() if any(c.isalnum() for c in w)]


def phrase_spans(align: dict, phrases: list[str]) -> list[tuple[float, float, list[dict]]]:
    """Whisper span and words of each phrase, matched in order on alphanumeric word content."""
    norm = lambda s: "".join(c for c in s.lower() if c.isalnum())
    aw = [w for w in align["words"] if norm(w["text"])]
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
    """Contiguous word spans inside a phrase [a, b]; a Whisper start that falls in silence moves to the
    next voiced frame and the previous word ends at the last voiced frame before that silence."""
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


def pack(line: dict, durs: list[float], beat: float, kick: float) -> list[float]:
    """Grid beats of a lyric line's phrases at natural speed: the first starts at the window start, each
    next one on the first 8th-note step after the previous ends plus a short gap; all inside the window."""
    b0, b1 = line["window"]
    grid, gap = line.get("grid", 0.5), line.get("min_gap", 0.08)
    t_of = lambda b: b * beat + kick
    cursor, onsets = t_of(b0), []
    for d in durs:
        g = np.ceil(((cursor - kick) / beat) / grid - 1e-6) * grid
        onsets.append(float(g))
        cursor = t_of(g) + d + gap
    if cursor - gap > t_of(b1) + 1e-6:
        raise SystemExit(f"line {line['phrases']} does not fit window {line['window']}")
    return onsets


def place_vo(plan: dict, total: int) -> tuple[np.ndarray, list[dict]]:
    beat, kick = 60 / plan["grid"]["bpm"], plan["grid"]["kick_onset_s"]
    vo = np.zeros(total, np.float32)
    report = []
    for sec in plan["sections"]:
        d = (HERE / sec["vo"]).resolve()
        mp3 = next(d.glob("*.mp3"))
        x = decode(mp3, 1)[:, 0]
        phrases = [p for line in sec["lines"] for p in line["phrases"]]
        spans = phrase_spans(json.loads((d / "align.json").read_text()), phrases)
        bounds = phrase_bounds(x, spans)
        env, thr = envelope(x)
        k = 0
        for li, line in enumerate(sec["lines"]):
            n = len(line["phrases"])
            onsets = pack(line, [b - a for a, b in bounds[k:k + n]], beat, kick)
            for text, (a, b), (_, _, ws), gb in zip(line["phrases"], bounds[k:k + n], spans[k:k + n], onsets):
                seg = x[max(0, int((a - PRE) * SR)):int((b + POST) * SR)] * 10 ** (sec.get("gain_db", 0.0) / 20)
                t = gb * beat + kick
                s0 = int(round((t - PRE) * SR))
                fade = np.ones(len(seg), np.float32)
                m = int(0.004 * SR)
                fade[:m] = np.linspace(0, 1, m)
                fade[-m * 4:] = np.linspace(1, 0, m * 4)
                if s0 < 0 or s0 + len(seg) > total:
                    raise SystemExit(f"phrase {text!r} falls outside the bed")
                vo[s0:s0 + len(seg)] += seg * fade
                report.append({"section": sec["name"], "mode": sec["mode"], "line": li, "text": text,
                               "vo_file": str(mp3.relative_to(HERE.parent)), "beat": gb,
                               "bar": round(1 + gb / 4, 3), "onset": round(t, 4), "end": round(t + b - a, 4),
                               "source_span": [round(a, 4), round(b, 4)], "gain_db": sec.get("gain_db", 0.0),
                               "words": [{"text": w["text"], "start": round(t + s - a, 4), "end": round(t + e - a, 4)}
                                         for w, (s, e) in zip(ws, word_times(ws, a, b, env, thr))]})
            k += n
    return vo, report


# ---------------------------------------------------------------- mix and master (as v2)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bed-only", action="store_true", help="write mix/bed-spliced.wav and the splice report only")
    ap.add_argument("--dry-run", action="store_true", help="print the VO placement, write nothing")
    args = ap.parse_args()
    plan = json.loads((HERE / "placement.json").read_text(encoding="utf-8"))
    total = int(round(plan["duration_s"] * SR))
    out = HERE / "mix"
    out.mkdir(exist_ok=True)
    bed, segments, splices = build_bed(plan["bed"], total)
    for s in splices:
        print(f"splice {s['splice']:2d} {s['xfade_s'][0]:9.4f}-{s['xfade_s'][1]:9.4f} {s['from']}->{s['to']} "
              f"jump {s['jump_ms']} ms corr {s['window_corr']}  {s['at']}")
    bed_wav = out / "bed-spliced.wav"
    if not args.dry_run:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_f32le", str(bed_wav)], input=bed.tobytes(), check=True)
    if args.bed_only:
        return
    vo, report = place_vo(plan, total)
    placed = sorted((p["onset"], p["end"], p["text"]) for p in report)
    clashes = [(p, q) for p, q in zip(placed, placed[1:]) if p[1] > q[0] - 0.05]
    for p in report:
        print(f"{p['onset']:8.3f}-{p['end']:8.3f}  bar {p['bar']:6.2f}  [{p['section']}] {p['text']}")
    for p, q in clashes:
        print(f"CLASH: {p[2]!r} ends {p[1]:.3f} > {q[2]!r} starts {q[0]:.3f}")
    if clashes:
        raise SystemExit("resolve clashes before mixing")
    if args.dry_run:
        return
    stem = out / "vo-stem.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s24le", str(stem)], input=vo.tobytes(), check=True)
    vo_proc, bed_duck, pre_master = (out / n for n in ("vo-processed.wav", "bed-ducked.wav", "pre-master.wav"))
    mix, mp3 = HERE / (plan["master"] + ".wav"), HERE / (plan["master"] + ".mp3")
    ff = lambda *a: subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True,
                                   capture_output=True, text=True)
    ff("-i", stem, "-af", f"{plan['vocal_chain']},pan=stereo|c0=c0|c1=c0,{FMT}", "-c:a", "pcm_f32le", vo_proc)
    ff("-i", bed_wav, "-i", vo_proc, "-filter_complex",
       f"[0:a]{FMT}[b];[1:a]{FMT}[s];[b][s]sidechaincompress={plan['duck']}[o]",
       "-map", "[o]", "-c:a", "pcm_f32le", bed_duck)
    v, b = decode(vo_proc, 2), decode(bed_duck, 2)
    n = min(len(v), len(b), total)
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
    # gain to the loudness target first, then a peak limiter at the ceiling (sample peak, 1 dB under TP:
    # v2's 0.5 dB margin let inter-sample peaks reach -0.8 dBTP on this longer master)
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre_master), "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"],
                           check=True, capture_output=True, text=True).stderr
    meas = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    lufs, ceiling = plan["lufs"], plan["true_peak_db"] - 1.0
    make_up = lufs - float(meas["input_i"])
    ff("-i", pre_master, "-af", f"volume={make_up:.2f}dB,alimiter=limit={10 ** (ceiling / 20):.4f}:attack=2:"
       f"release=50:level=0", "-ar", str(SR), "-c:a", "pcm_s24le", mix)
    ff("-i", mix, "-c:a", "libmp3lame", "-b:a", "256k", mp3)
    print(f"voice over bed before gain {over:+.1f} dB -> applied {gain_db:+.1f} dB; "
          f"pre-master {meas['input_i']} LUFS / {meas['input_tp']} dBTP -> make-up {make_up:+.2f} dB, limiter {ceiling} dBFS")
    sources = {k: {"file": v, "sha256": sha256(HERE / v)} for k, v in plan["bed"]["sources"].items()}
    vo_files = sorted({p["vo_file"] for p in report})
    (out / "placement-result.json").write_text(json.dumps({
        "master": {"wav": str(mix.relative_to(HERE)), "sha256": sha256(mix), "mp3": str(mp3.relative_to(HERE)),
                   "mp3_sha256": sha256(mp3)},
        "sample_rate": SR, "duration_s": n / SR, "grid": plan["grid"], "bed_sources": sources,
        "segments": segments, "splices": splices,
        "vo_files": {f: sha256(HERE.parent / f) for f in vo_files},
        "voice_gain_db": round(float(gain_db), 2), "make_up_db": round(make_up, 2),
        "phrases": report}, ensure_ascii=False, indent=1) + "\n")
    print("wrote", mix, mp3)


if __name__ == "__main__":
    main()
