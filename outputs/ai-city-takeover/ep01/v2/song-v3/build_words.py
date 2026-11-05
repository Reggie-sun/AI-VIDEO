#!/usr/bin/env python3
"""Lyric line and word timing for the selected IRIS EP01 song (Suno v6 take T4) -> timing/words.json.

  ~/miniconda3/bin/python -I outputs/ai-city-takeover/ep01/v2/song-v3/build_words.py

Source of truth for timing: Suno's own aligned words for the clip (suno-timed-lyrics.json, from `suno timed-lyrics`).
Each lyric line of the sung lyric (ep01/lyrics-v2.2-suno.md, the exact `fields.json` text) is matched to Suno's word
stream in order. Cross-check: Whisper forced alignment (motion-kit/tools/whisper_align.py, large-v3) of each line on
the Demucs vocal stem; a word whose two start times differ by more than 0.25 s is listed in timing/check.json for a
look, never silently replaced. Output schema iris-lyric-lines/1 (same as song-full/timing/words.json):
{schema, song{path, sha256}, lines[{en, mode, section, start, end, words[{text, start, end}]}]}.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FIELDS = HERE.parent / "song-suno/fields.json"
MASTER = HERE / "IRIS-01-T4.wav"
VOCALS = HERE / "stems/htdemucs_ft/IRIS-01-T4/vocals.wav"
MODE = {"Intro": "spoken", "Verse 1": "spoken", "Verse 2": "spoken", "Outro": "spoken", "Pre-Chorus": "whisper",
        "Bridge": "whisper", "Chorus": "sung", "Final Chorus": "sung", "Coda": "sung", "Drop": "chant"}
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())


def lyric_lines(text: str) -> list[tuple[str, str]]:
    out, sec = [], None
    for raw in text.split("\n"):
        line = raw.strip()
        m = re.match(r"\[([^\]]+)\]", line)
        if m:
            sec = m.group(1).split(" - ")[0].strip()
            continue
        if line:
            out.append((sec, line))
    return out


def suno_tokens(words: list[dict]) -> list[dict]:
    """Suno words with the section tags removed; each keeps its own start/end."""
    toks = []
    for w in words:
        text = re.sub(r"\[[^\]]*\]", " ", w["word"])
        for piece in text.split():
            if norm(piece):
                toks.append({"text": piece, "n": norm(piece), "start": w["start_s"], "end": w["end_s"]})
    return toks


def forced(line: str, a: float, b: float) -> list[dict]:
    tmp = Path("/tmp") / f"bw-{int(a * 100)}.txt"
    tmp.write_text(line)
    out = Path("/tmp") / f"bw-{int(a * 100)}.json"
    subprocess.run([sys.executable, "-I", str(ROOT / "motion-kit/tools/whisper_align.py"), "align", "--audio", str(VOCALS),
                    "--text", str(tmp), "--start", f"{a:.2f}", "--end", f"{b:.2f}", "--out", str(out)], check=True, capture_output=True)
    return [w for w in json.loads(out.read_text())["words"] if norm(w["text"])]


def main() -> None:
    lyrics = json.loads(FIELDS.read_text())["lyrics"]
    toks = suno_tokens(json.loads((HERE / "suno-timed-lyrics.json").read_text())["data"])
    k, lines, checks = 0, [], []
    for sec, line in lyric_lines(lyrics):
        lw = [p for p in line.replace("—", " ").split() if norm(p)]
        ws = []
        for p in lw:
            target, acc, parts = norm(p), "", []
            while k < len(toks) and len(acc) < len(target):
                acc += toks[k]["n"]; parts.append(toks[k]); k += 1
            if acc != target:
                raise SystemExit(f"Suno words do not follow the lyric at {p!r} (got {acc!r}) in {line!r}")
            ws.append({"text": p, "start": round(parts[0]["start"], 3), "end": round(parts[-1]["end"], 3)})
        start, end = ws[0]["start"], ws[-1]["end"]
        fa = forced(line, max(0.0, start - 0.6), min(end + 0.8, start + 29.5))
        for w, f in zip(ws, fa):
            if abs(w["start"] - f["start"]) > 0.25:
                checks.append({"line": line, "word": w["text"], "suno_start": w["start"], "whisper_start": round(f["start"], 3)})
        lines.append({"en": line, "mode": MODE.get(sec, "sung"), "section": sec, "start": start, "end": end, "words": ws})
    sha = hashlib.sha256(MASTER.read_bytes()).hexdigest()
    (HERE / "timing").mkdir(exist_ok=True)
    (HERE / "timing/words.json").write_text(json.dumps({"schema": "iris-lyric-lines/1", "song": {"path": "../IRIS-01-T4.wav", "sha256": sha},
                                                        "timing_source": "suno timed-lyrics (aligned words) for clip of T4", "lines": lines},
                                                       ensure_ascii=False, indent=1) + "\n")
    (HERE / "timing/check.json").write_text(json.dumps({"threshold_s": 0.25, "disagreements": checks}, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"lines": len(lines), "words": sum(len(l["words"]) for l in lines), "disagreements": len(checks),
                      "first": lines[0]["start"], "last": lines[-1]["end"]}))


if __name__ == "__main__":
    main()
