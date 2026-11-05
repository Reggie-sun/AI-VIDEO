"""Decode one exact local repair result and obtain an unprompted lyric observation."""

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main():
    """Inspect a materialized waveform without providing the reference words to ASR."""
    import numpy as np
    import soundfile as sf
    import torch
    import whisper
    from whisper.normalizers import EnglishTextNormalizer

    folder = Path(sys.argv[1]).resolve()
    if (folder / "asr.json").exists():
        raise SystemExit("ASR observation already exists; retain the original evidence")
    result = json.loads((folder / "result.json").read_text())
    if result.get("success") is not True or len(result.get("outputs", [])) != 1:
        raise SystemExit("No single known successful generation to inspect")
    source = Path(result["outputs"][0]["path"])
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha != result["outputs"][0]["sha256"]:
        raise SystemExit("Source bytes changed")
    audio, rate = sf.read(source, always_2d=True)
    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-xerror", "-i", str(source), "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    if decoded.stderr.strip() or not np.isfinite(audio).all():
        raise SystemExit("Audio decode or finite-sample verification failed")
    validation = {
        "audio_sha256": source_sha, "sample_rate": rate, "channels": audio.shape[1],
        "frames": len(audio), "duration_seconds": len(audio) / rate,
        "peak": float(np.max(np.abs(audio))), "rms": float(np.sqrt(np.mean(audio ** 2))),
        "clipped_sample_count": int(np.count_nonzero(np.abs(audio) >= 1)),
        "finite": True, "full_decode": "PASS", "human_hearing": "NOT_EVALUATED",
    }
    (folder / "audio-validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps({"event": "audio_validated", **validation}), flush=True)
    started = time.monotonic()
    model = whisper.load_model("/home/reggie/.cache/whisper/large-v3.pt", device="cuda")
    answer = model.transcribe(
        str(source), language="en", temperature=0, beam_size=5, fp16=True,
        condition_on_previous_text=False, word_timestamps=True, verbose=None,
    )
    intent = json.loads((folder / "intent.json").read_text())
    original = json.loads(Path(intent["source_intent_path"]).read_text())["fields"]["lyrics"]
    reference = " ".join(line for line in original.splitlines() if not line.startswith("["))
    normalizer = EnglishTextNormalizer()
    expected = normalizer(reference).split()
    observed = normalizer(answer["text"]).split()
    previous = list(range(len(observed) + 1))
    for i, word in enumerate(expected, 1):
        current = [i]
        for j, other in enumerate(observed, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (word != other)))
        previous = current
    report = {
        "source_sha256": source_sha, "model": "OpenAI Whisper large-v3 local",
        "torch_version": torch.__version__, "transcript": answer["text"],
        "normalized_reference": normalizer(reference),
        "normalized_hypothesis": normalizer(answer["text"]),
        "reference_word_count": len(expected), "hypothesis_word_count": len(observed),
        "word_error_rate": previous[-1] / max(1, len(expected)),
        "segments": [{k: s[k] for k in ("start", "end", "text", "words",
                      "avg_logprob", "no_speech_prob") if k in s} for s in answer["segments"]],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "authority": "Unprompted ASR only; not human hearing or canonical caption timing",
        "remote_calls": 0,
    }
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
        raise SystemExit("Source changed during inspection")
    (folder / "asr.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("transcript", "reference_word_count",
                     "hypothesis_word_count", "word_error_rate")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
