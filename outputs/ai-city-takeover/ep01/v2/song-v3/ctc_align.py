#!/usr/bin/env python3
"""CTC forced alignment of the lyric on the Demucs vocal stem (torchaudio MMS_FA, wav2vec2-family), the author's method.

  ~/miniconda3/bin/python -I outputs/ai-city-takeover/ep01/v2/song-v3/ctc_align.py

For each lyric line of timing/words.json, align its exact words inside a window that starts 0.6 s before the
earliest of the Suno/Whisper line starts and ends at the next line's start (Suno word times are only a rough
locator). Writes timing/words-ctc.json (same schema, CTC word times) and timing/ctc-check.json, which compares
every CTC word start with the vocal-stem energy onset near it. Nothing is overwritten; the caller decides which
timing becomes timing/words.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import torch
import torchaudio

HERE = Path(__file__).resolve().parent
VOCALS = HERE / "stems/htdemucs_ft/IRIS-01-T4/vocals.wav"
norm = lambda s: re.sub(r"[^a-z']", "", s.lower().replace("—", " "))


def main() -> None:
    words = json.loads((HERE / "timing/words.json").read_text())
    check = {(d["line"], d["word"]): d for d in json.loads((HERE / "timing/check.json").read_text())["disagreements"]}
    bundle = torchaudio.pipelines.MMS_FA
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = bundle.get_model(with_star=False).to(dev)
    tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
    import librosa                                   # torchaudio 2.9 needs torchcodec to load files; librosa is already here
    sr = bundle.sample_rate
    wav = torch.from_numpy(librosa.load(str(VOCALS), sr=sr, mono=True)[0]).unsqueeze(0)
    env_hop = int(0.005 * sr)
    x = wav[0].numpy()
    n = len(x) // env_hop
    env = 20 * np.log10(np.sqrt((x[:n * env_hop].reshape(n, env_hop) ** 2).mean(1)) + 1e-9)
    lines = words["lines"]
    out_lines, cmp = [], []
    for i, ln in enumerate(lines):
        first = ln["words"][0]["start"]
        wh = check.get((ln["en"], ln["words"][0]["text"]), {}).get("whisper_start", first)
        a = max(0.0, min(first, wh) - 0.6)
        b = lines[i + 1]["words"][0]["start"] if i + 1 < len(lines) else min(len(x) / sr, ln["end"] + 3.0)
        b = max(b, a + 1.0)
        seg = wav[:, int(a * sr):int(b * sr)].to(dev)
        toks = [norm(w["text"]) for w in ln["words"]]
        with torch.inference_mode():
            emission, _ = model(seg)
            spans = aligner(emission[0], tokenizer(toks))
        ratio = seg.size(1) / emission.size(1) / sr
        new_words = []
        for w, sp in zip(ln["words"], spans):
            s, e = a + sp[0].start * ratio, a + sp[-1].end * ratio
            # energy onset near the CTC start: first frame within -0.15..+0.30 s above the local mid level
            lo, hi = int((s - 0.15) * sr / env_hop), int((s + 0.30) * sr / env_hop)
            loc = env[max(0, lo):hi]
            thr = np.percentile(loc, 10) + 0.5 * (loc.max() - np.percentile(loc, 10)) if len(loc) else 0
            idx = np.nonzero(loc > thr)[0]
            onset = (max(0, lo) + idx[0]) * env_hop / sr if len(idx) else None
            cmp.append({"line": ln["en"], "word": w["text"], "ctc_start": round(s, 3), "suno_start": w["start"],
                        "energy_onset": round(onset, 3) if onset is not None else None})
            new_words.append({"text": w["text"], "start": round(s, 3), "end": round(e, 3)})
        out_lines.append({**ln, "start": new_words[0]["start"], "end": new_words[-1]["end"], "words": new_words})
    (HERE / "timing/words-ctc.json").write_text(json.dumps({**words, "timing_source": "torchaudio MMS_FA CTC forced alignment on the Demucs vocal stem; windows located by Suno word times",
                                                         "lines": out_lines}, ensure_ascii=False, indent=1) + "\n")
    d = [abs(c["ctc_start"] - c["energy_onset"]) for c in cmp if c["energy_onset"] is not None]
    ds = [abs(c["suno_start"] - c["energy_onset"]) for c in cmp if c["energy_onset"] is not None]
    summary = {"words": len(cmp), "ctc_vs_onset_median_s": round(float(np.median(d)), 3), "ctc_within_0_1": int(sum(v <= 0.1 for v in d)),
               "suno_vs_onset_median_s": round(float(np.median(ds)), 3), "suno_within_0_1": int(sum(v <= 0.1 for v in ds))}
    (HERE / "timing/ctc-check.json").write_text(json.dumps({"summary": summary, "words": cmp}, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
