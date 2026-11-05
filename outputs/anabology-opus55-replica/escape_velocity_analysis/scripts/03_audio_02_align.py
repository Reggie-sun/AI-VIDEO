#!/usr/bin/env python
"""Forced alignment of the KNOWN lyrics (source_docs/prompts-suno.md) to the htdemucs vocal stem with
torchaudio MMS_FA (wav2vec2 CTC) + Viterbi. Usage: 03_audio_02_align.py <analysis_root>
Outputs audio/lyrics_aligned.json (words + lines + sections), audio/lyrics_known.json.
Cross-check against audio/whisper_large_v3_words.json is done in 03_audio_03_vocals.py / qa."""
import sys, os, re, json
import numpy as np, torch, torchaudio, soundfile as sf
root = sys.argv[1]
md = open(os.path.join(root, "source_docs", "prompts-suno.md"), encoding="utf-8").read()
blk = md.split("## Lyrics field", 1)[1].split("```", 2)[1]
lines, tag, lid = [], "", 0
for raw in blk.splitlines():
    s = raw.strip()
    if not s: continue
    if s.startswith("["):
        tag = s.strip("[]"); continue
    lid += 1
    lines.append({"line_id": f"LY{lid:03d}", "section_tag": tag, "text": s})
json.dump(lines, open(os.path.join(root, "audio", "lyrics_known.json"), "w"), indent=1, ensure_ascii=False)
toks = []  # display, norm, line_id
for ln in lines:
    for w in re.split(r"[\s\-]+", ln["text"].replace("—", " ")):
        n = re.sub(r"[^a-z']", "", w.lower())
        if n: toks.append((w.strip("()\"."), n, ln["line_id"], ln["section_tag"]))
print("words", len(toks), "lines", len(lines))

wav, sr = sf.read(os.path.join(root, "work", "audio_tmp", "stems", "vocals.wav"), dtype="float32")
wav = torch.from_numpy(wav.mean(1))[None]
bundle = torchaudio.pipelines.MMS_FA
dev = "cuda"
model = bundle.get_model(with_star=False).to(dev).eval()
wav16 = torchaudio.functional.resample(wav, sr, bundle.sample_rate)
with torch.inference_mode():
    # chunk in 60 s windows without overlap trouble: use 3 s overlap, keep centre
    hop = 60 * 16000; ov = 3 * 16000; outs = []
    pos = 0; n = wav16.shape[1]
    while pos < n:
        a = max(0, pos - ov); b = min(n, pos + hop + ov)
        em, _ = model(wav16[:, a:b].to(dev))
        em = torch.log_softmax(em, -1)[0].cpu()
        fr = em.shape[0]; spf = (b - a) / fr          # samples per frame (~320)
        f0 = int(round((pos - a) / spf)); f1 = fr - int(round((b - min(n, pos + hop)) / spf))
        outs.append(em[f0:f1]); pos += hop
    emission = torch.cat(outs)[None]
spf = wav16.shape[1] / emission.shape[1]; fsec = spf / 16000
print("emission frames", emission.shape, "frame s", fsec)
labels = bundle.get_labels(star=None); d = {c: i for i, c in enumerate(labels)}
targets = [d[c] for t in toks for c in t[1] if c in d]
ali, sc = torchaudio.functional.forced_align(emission, torch.tensor([targets], dtype=torch.int32), blank=0)
ali, sc = ali[0], sc[0].exp()
spans = torchaudio.functional.merge_tokens(ali, sc)
ci = 0; words = []
for t in toks:
    k = len([c for c in t[1] if c in d]); sp = spans[ci:ci + k]; ci += k
    words.append({"word": t[0], "norm": t[1], "start_s": round(sp[0].start * fsec, 3), "end_s": round(sp[-1].end * fsec, 3),
                  "line_id": t[2], "section_tag": t[3], "confidence": round(float(np.mean([s.score for s in sp])), 3)})
json.dump({"method": "torchaudio MMS_FA CTC forced alignment of known lyrics on htdemucs vocal stem", "frame_s": fsec, "words": words},
          open(os.path.join(root, "audio", "lyrics_aligned.json"), "w"), indent=1, ensure_ascii=False)
for w in words[::6]: print(f'{w["start_s"]:7.2f} {w["end_s"]:7.2f} {w["confidence"]:.2f} {w["word"]}')
