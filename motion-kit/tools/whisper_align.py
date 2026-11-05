#!/usr/bin/env python3
"""Whisper word timing for a vocal stem or mix (forced alignment: one <=30 s span per call).

Runs in a Python that has openai-whisper and torch (not the project env); lyric_align.py calls it.

  transcribe  unprompted ASR with word timestamps; never sees the lyrics, so it can check completeness
  align       forced alignment of the given lyric text (Whisper cross-attention DTW on those exact tokens)

Output JSON: mode, model, audio_sha256, start, end, text, words[{text, start, end, probability}].
Times are seconds in the source file's timeline. In align mode word texts keep Whisper's leading
spaces so that "".join(texts) == " " + text, which lets the caller map them back by character offset.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["transcribe", "align"])
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--text", type=Path, help="align: UTF-8 file with the exact lyric text of the span")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.mode == "align" and a.text is None:
        sys.exit("align mode needs --text")

    import torch
    import whisper
    from whisper.audio import HOP_LENGTH, N_SAMPLES, SAMPLE_RATE, load_audio, log_mel_spectrogram, pad_or_trim
    from whisper.timing import find_alignment
    from whisper.tokenizer import get_tokenizer

    audio = load_audio(str(a.audio))
    s0 = int(round(a.start * SAMPLE_RATE))
    s1 = len(audio) if a.end is None else int(round(a.end * SAMPLE_RATE))
    seg = audio[s0:s1]
    if a.mode == "align" and len(seg) > N_SAMPLES:
        sys.exit("align span is longer than 30 s; align one window at a time")
    model = whisper.load_model(a.model, device="cuda" if torch.cuda.is_available() else "cpu")

    if a.mode == "transcribe":
        r = model.transcribe(seg, language="en", word_timestamps=True,
                             condition_on_previous_text=False, temperature=0.0)
        text = r["text"].strip()
        words = [{"text": w["word"], "start": w["start"] + a.start, "end": w["end"] + a.start,
                  "probability": w["probability"]} for s in r["segments"] for w in s["words"]]
    else:
        text = " ".join(a.text.read_text(encoding="utf-8").split())
        tok = get_tokenizer(model.is_multilingual, num_languages=model.num_languages,
                            language="en", task="transcribe")
        mel = log_mel_spectrogram(pad_or_trim(seg), model.dims.n_mels).to(model.device)
        timings = find_alignment(model, tok, tok.encode(" " + text), mel, len(seg) // HOP_LENGTH)
        words = [{"text": t.word, "start": float(t.start) + a.start, "end": float(t.end) + a.start,
                  "probability": float(t.probability)} for t in timings]
        if "".join(w["text"] for w in words) != " " + text:
            sys.exit("aligned words do not reproduce the lyric text")

    a.out.write_text(json.dumps({
        "mode": a.mode, "model": f"openai-whisper {a.model}", "audio": str(a.audio),
        "audio_sha256": sha256(a.audio), "start": a.start, "end": s0 / SAMPLE_RATE + len(seg) / SAMPLE_RATE,
        "text": text, "words": words}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"mode": a.mode, "words": len(words)}))


if __name__ == "__main__":
    main()
