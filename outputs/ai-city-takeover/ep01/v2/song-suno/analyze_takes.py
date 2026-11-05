#!/usr/bin/env python3
"""Objective measurements of the Suno takes of "Looked Outside" (local, read-only, no network).

  ~/miniconda3/bin/python -I outputs/ai-city-takeover/ep01/v2/song-suno/analyze_takes.py

Needs librosa and openai-whisper (the miniconda base env). Uses Suno's own word timings (takes/<id>.timed.json,
via structure.json) for section boundaries. Measures, per take: time to the first vocal and the first chorus,
loudness of each section (RMS dBFS) and the lifts verse->chorus, chorus 1->final chorus and into the drop, the key
of chorus 1 vs the final chorus (Krumhansl profiles on CQT chroma, so a key change shows as a semitone shift),
tempo and beat steadiness, and Whisper word error rate of spoken verse 1 and sung chorus 1 against the lyric.
These are proxies, not listening: the user, or a listening model, judges taste.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).resolve().parent
T = HERE / "takes"
ROOT = HERE.parents[4]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def key_of(chroma: np.ndarray) -> tuple[int, str]:
    v = chroma.mean(axis=1)
    best = max(((np.corrcoef(np.roll(prof, k), v)[0, 1], k, m) for m, prof in (("maj", MAJOR), ("min", MINOR)) for k in range(12)))
    return best[1], best[2]


def words(s: str) -> list[str]:
    return re.findall(r"[a-z']+", s.lower().replace("—", " "))


def wer(ref: list[str], hyp: list[str]) -> float:
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
            prev, d[j] = d[j], cur
    return d[len(hyp)] / max(1, len(ref))


def whisper(path: Path, a: float, b: float) -> str:
    out = Path("/tmp") / f"an-{path.stem[:8]}-{int(a)}.json"
    subprocess.run([sys.executable, "-I", str(ROOT / "motion-kit/tools/whisper_align.py"), "transcribe", "--audio", str(path),
                    "--start", f"{a:.2f}", "--end", f"{b:.2f}", "--out", str(out)], check=True, capture_output=True)
    return "".join(w["text"] for w in json.loads(out.read_text())["words"])


def main() -> None:
    fields = json.loads((HERE / "fields.json").read_text())
    lyr = fields["lyrics"]
    blocks = {m.group(1).split(" - ")[0]: m.group(2) for m in re.finditer(r"\[([^\]]+)\]\n(.*?)(?=\n\[|\Z)", lyr, re.S)}
    takes = json.loads((T / "takes.json").read_text())["takes"]
    st = json.loads((T / "structure.json").read_text())
    report = {}
    for r in takes:
        k = f"T{r['n']}"
        wav = T / r["wav"]
        y, sr = librosa.load(str(wav), sr=22050, mono=True)
        secs = st[k]["sections"]
        bounds = [(name, t0, (secs[i + 1][1] if i + 1 < len(secs) else st[k]["last_word_end"])) for i, (name, t0) in enumerate(secs)]
        def span(name, nth=1):
            hits = [b for b in bounds if b[0] == name]
            return hits[nth - 1] if len(hits) >= nth else None
        def db(b):
            seg = y[int(b[1] * sr):int(b[2] * sr)]
            return float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9))
        v1, c1, c2, dr, fc = span("Verse 1"), span("Chorus"), span("Chorus", 2), span("Drop"), span("Final Chorus")
        lifts = {"verse1_db": round(db(v1), 1), "chorus1_db": round(db(c1), 1), "chorus2_db": round(db(c2), 1),
                 "drop_db": round(db(dr), 1), "final_db": round(db(fc), 1)}
        lifts["chorus_lift_db"] = round(lifts["chorus1_db"] - lifts["verse1_db"], 1)
        lifts["final_vs_chorus1_db"] = round(lifts["final_db"] - lifts["chorus1_db"], 1)
        chroma = lambda b: librosa.feature.chroma_cqt(y=y[int(b[1] * sr):int(b[2] * sr)], sr=sr)
        k1, m1 = key_of(chroma(c1))
        kf, mf = key_of(chroma(fc))
        shift = (kf - k1) % 12
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        ibi = np.diff(librosa.frames_to_time(beats, sr=sr))
        v1_hyp = whisper(wav, v1[1], v1[2])
        c1_hyp = whisper(wav, c1[1], c1[2])
        report[k] = {
            "id": r["id"], "duration_s": r["duration"], "first_vocal_s": secs[0][1], "first_chorus_s": c1[1],
            **lifts, "key_chorus1": f"{NAMES[k1]} {m1}", "key_final": f"{NAMES[kf]} {mf}",
            "key_change_up_semitones": shift if shift <= 6 else shift - 12,
            "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 1), "beat_interval_cv": round(float(np.std(ibi) / np.mean(ibi)), 3),
            "verse1_wer": round(wer(words(blocks["Verse 1"]), words(v1_hyp)), 2), "chorus1_wer": round(wer(words(blocks["Chorus"]), words(c1_hyp)), 2),
            "verse1_heard": v1_hyp.strip()[:200], "chorus1_heard": c1_hyp.strip()[:160],
        }
        print(json.dumps({k: {x: report[k][x] for x in report[k] if not x.endswith("heard") and x != "id"}}, ensure_ascii=False), flush=True)
    (T / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
