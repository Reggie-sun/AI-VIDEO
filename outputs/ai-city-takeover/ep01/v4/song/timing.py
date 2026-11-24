#!/usr/bin/env python3
"""Word timing for the chosen IRIS EP01 v4 take ("All Hands r4") -> timing/words-ctc.json + timing/check.json (resolve.py then writes timing/words.json).

  ~/miniconda3/bin/python -I outputs/ai-city-takeover/ep01/v4/song/timing.py

Author's method (wiki_listen): Suno's aligned words locate each line; CTC forced alignment (torchaudio MMS_FA)
of the exact lyric words on the Demucs vocal stem gives the word times; every word is then checked against the
vocal-stem energy. A word is flagged for a human listen when
  - CTC and Suno starts differ by more than 0.25 s, or
  - the CTC word span is mostly vocal silence (the v3 song put "looked/outside" into 9 s of silence this way), or
  - Suno itself reports success=false / p_align < 0.5.
Flags are never auto-fixed. Lines come from fields-r4-industrial.json (the exact submitted lyric = lyrics-v5.txt).
Output schema iris-lyric-lines/1: {schema, song{path, sha256}, timing_source, lines[{en, mode, section, start, end, words}]}.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MASTER = HERE / "master/all-hands-r4-edc6c6bf.wav"
VOCALS = HERE / "stems/htdemucs_ft/all-hands-r4-edc6c6bf/vocals.wav"
FIELDS = HERE / "fields-r4-industrial.json"
SUNO = HERE / "master/suno-timed-lyrics.json"
OUT = HERE / "timing"
MODE = {"Spoken": "spoken", "Verse 1": "spoken", "Verse 2": "spoken", "Verse 3": "spoken", "Verse 4": "spoken",
        "Outro": "spoken", "Chorus": "sung", "Final Chorus": "sung", "Bridge": "sung", "Post-Chorus": "chant"}
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
# CTC tokenizer (MMS_FA) knows letters and apostrophe only: spell digits as sung
DIGITS = {"467": "four sixty seven"}


def lyric_lines(text: str) -> list[tuple[str, str]]:
    out, sec = [], None
    for raw in text.split("\n"):
        line = raw.strip()
        m = re.match(r"\[([^\]]+)\]", line)
        if m:
            sec = m.group(1).split(" - ")[0].strip()
        elif line:
            out.append((sec, line))
    return out


def suno_tokens(words: list[dict]) -> list[dict]:
    """Suno's word stream with [section tags] removed (tags can span several Suno tokens)."""
    toks, depth = [], 0
    for w in words:
        kept = ""
        for ch in w["word"]:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth = max(0, depth - 1)
                kept += " "
            elif depth == 0:
                kept += ch
        for piece in kept.split():
            if norm(piece):
                toks.append({"text": piece, "n": norm(piece), "start": w["start_s"], "end": w["end_s"],
                             "ok": bool(w.get("success", True)), "p": float(w.get("p_align", 1.0))})
    return toks


def main() -> None:
    import librosa
    import torch
    import torchaudio

    lyrics = json.loads(FIELDS.read_text())["lyrics"]
    toks = suno_tokens(json.loads(SUNO.read_text())["data"])
    k, lines = 0, []
    for sec, line in lyric_lines(lyrics):
        ws = []
        for p in [p for p in line.split() if norm(p)]:
            target, acc, parts = norm(p), "", []
            while k < len(toks) and len(acc) < len(target):
                acc += toks[k]["n"]; parts.append(toks[k]); k += 1
            if acc != target:
                raise SystemExit(f"Suno words do not follow the lyric at {p!r} (got {acc!r}) in {line!r}")
            ws.append({"text": p, "suno_start": round(parts[0]["start"], 3), "suno_end": round(parts[-1]["end"], 3),
                       "suno_ok": all(t["ok"] for t in parts), "suno_p": round(min(t["p"] for t in parts), 2)})
        lines.append({"en": line, "section": sec, "mode": MODE.get(sec, "sung"), "words": ws})

    bundle = torchaudio.pipelines.MMS_FA
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = bundle.get_model(with_star=False).to(dev)
    tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
    sr = bundle.sample_rate
    x = librosa.load(str(VOCALS), sr=sr, mono=True)[0]
    wav = torch.from_numpy(x).unsqueeze(0)
    hop = int(0.01 * sr)
    n = len(x) // hop
    env = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    voiced_thr = float(np.percentile(env, 30) + 0.35 * (np.percentile(env, 95) - np.percentile(env, 30)))
    dur = len(x) / sr

    flags, out_lines = [], []
    for i, ln in enumerate(lines):
        a = max(0.0, ln["words"][0]["suno_start"] - 0.6)
        b = lines[i + 1]["words"][0]["suno_start"] if i + 1 < len(lines) else min(dur, ln["words"][-1]["suno_end"] + 3.0)
        b = max(b, a + 1.0)
        seg = wav[:, int(a * sr):int(b * sr)].to(dev)
        toks_ctc = []
        for w in ln["words"]:
            t = norm(w["text"]).replace("'", "")
            toks_ctc.append(DIGITS.get(t, t).replace(" ", ""))
        with torch.inference_mode():
            emission, _ = model(seg)
            spans = aligner(emission[0], tokenizer(toks_ctc))
        ratio = seg.size(1) / emission.size(1) / sr
        new = []
        for w, sp in zip(ln["words"], spans):
            s, e = a + sp[0].start * ratio, a + sp[-1].end * ratio
            lo, hi = int(s / 0.01), max(int(s / 0.01) + 1, int(e / 0.01))
            voiced = float(np.mean(env[lo:hi] > voiced_thr))
            why = []
            if abs(s - w["suno_start"]) > 0.25:
                why.append(f"ctc-suno {s - w['suno_start']:+.2f}s")
            if voiced < 0.3:
                why.append(f"voiced {voiced:.0%}")
            if not w["suno_ok"] or w["suno_p"] < 0.5:
                why.append(f"suno p={w['suno_p']}")
            word = {"text": w["text"], "start": round(s, 3), "end": round(e, 3), "suno_start": w["suno_start"],
                    "voiced": round(voiced, 2)}
            if why:
                flags.append({"line": ln["en"], "word": w["text"], "ctc_start": round(s, 3), "suno_start": w["suno_start"],
                              "why": why})
            new.append(word)
        out_lines.append({"en": ln["en"], "mode": ln["mode"], "section": ln["section"],
                          "start": new[0]["start"], "end": new[-1]["end"], "words": new})

    OUT.mkdir(exist_ok=True)
    sha = hashlib.sha256(MASTER.read_bytes()).hexdigest()
    (OUT / "words-ctc.json").write_text(json.dumps({
        "schema": "iris-lyric-lines/1", "song": {"path": "../master/all-hands-r4-edc6c6bf.wav", "sha256": sha},
        "timing_source": "torchaudio MMS_FA CTC on Demucs htdemucs_ft vocal stem; line windows located by Suno timed-lyrics",
        "lines": out_lines}, ensure_ascii=False, indent=1) + "\n")
    (OUT / "check.json").write_text(json.dumps({"voiced_threshold_db": round(voiced_thr, 1), "flags": flags},
                                               ensure_ascii=False, indent=1) + "\n")
    nw = sum(len(l["words"]) for l in out_lines)
    print(json.dumps({"lines": len(out_lines), "words": nw, "flags": len(flags), "suno_tokens_left": len(toks) - k,
                      "first": out_lines[0]["start"], "last": out_lines[-1]["end"]}))


if __name__ == "__main__":
    main()
