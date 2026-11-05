#!/usr/bin/env python
"""Whisper large-v3 word-timestamp transcription of the vocals stem (GPU). Usage: 03_audio_01_whisper.py <analysis_root>
Output: audio/whisper_large_v3_words.json  (independent cross-check for forced alignment)."""
import sys, os, json
root = sys.argv[1]
import whisper, torch
stem = os.path.join(root, "work", "audio_tmp", "stems", "vocals.wav")
model = whisper.load_model("large-v3", device="cuda")
res = model.transcribe(stem, word_timestamps=True, language="en", condition_on_previous_text=False,
                       temperature=0.0, no_speech_threshold=0.5, compression_ratio_threshold=2.6, verbose=False)
out = {"model": "openai-whisper large-v3", "input": "vocals stem (htdemucs)", "segments": []}
for s in res["segments"]:
    out["segments"].append({"start": s["start"], "end": s["end"], "text": s["text"], "avg_logprob": s["avg_logprob"],
        "no_speech_prob": s["no_speech_prob"],
        "words": [{"word": w["word"].strip(), "start": w["start"], "end": w["end"], "p": w["probability"]} for w in s.get("words", [])]})
json.dump(out, open(os.path.join(root, "audio", "whisper_large_v3_words.json"), "w"), indent=1, ensure_ascii=False)
for s in out["segments"]: print(f'{s["start"]:7.2f} {s["end"]:7.2f} {s["text"]}')
