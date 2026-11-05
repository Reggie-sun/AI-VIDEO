"""Synthesize one complete local spoken reference without trimming or speeding a waveform."""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    """Return the exact bytes identity of a local artifact."""
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    """Produce all speech chunks, retaining an overlong reference as an unsuccessful candidate."""
    path = Path(sys.argv[1]).resolve()
    intent = json.loads(path.read_text())
    out = path.parent
    if (out / "consume.json").exists():
        raise SystemExit("Guide unit already consumed; no replay")
    if sha(__file__) != intent["runner_sha256"]:
        raise SystemExit("Guide runner changed")
    series_path = Path(intent["series_intent_path"])
    if sha(series_path) != intent["series_intent_sha256"]:
        raise SystemExit("Guide series changed")
    series = json.loads(series_path.read_text())
    speed = intent["synthesis_speed"]
    if not series["guide_tts_speed_range"][0] <= speed <= series["guide_tts_speed_range"][1]:
        raise SystemExit("Synthesis pace exceeds sealed bound")
    if not 1 <= intent["guide_ordinal"] <= series["guide_tts_generation_limit"]:
        raise SystemExit("Guide count exceeds sealed bound")
    source = Path(series["source_intent_path"])
    if sha(source) != series["source_intent_sha256"]:
        raise SystemExit("Original brief changed")
    original = json.loads(source.read_text())["fields"]["lyrics"]
    plain = " ".join(line for line in original.splitlines() if not line.startswith("["))
    plain = re.sub(r"\s+", " ", plain).strip()
    if hashlib.sha256(plain.encode()).hexdigest() != intent["plain_text_sha256"]:
        raise SystemExit("Reference words changed")
    weights = Path(intent["weights_root"])
    manifest_path = Path(intent["weights_manifest_path"])
    if sha(manifest_path) != intent["weights_manifest_sha256"]:
        raise SystemExit("Reference model manifest changed")
    manifest = json.loads(manifest_path.read_text())
    if not manifest.get("all_files_verified"):
        raise SystemExit("Reference model not verified")
    for record in manifest["files"]:
        if sha(weights / record["path"]) != record["actual_sha256"]:
            raise SystemExit("Reference model file changed")

    import importlib.metadata
    import soundfile as sf
    import spacy
    import torch
    from kokoro import KModel, KPipeline
    from misaki import espeak

    if not torch.cuda.is_available() or not spacy.util.is_package("en_core_web_sm"):
        raise SystemExit("Local CUDA or English G2P resource unavailable")
    espeak.EspeakFallback(british=False)
    model = KModel(repo_id="hexgrad/Kokoro-82M", config=str(weights / "config.json"),
                   model=str(weights / "kokoro-v1_0.pth")).to("cuda").eval()
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", model=model)
    if getattr(pipeline.g2p, "fallback", None) is None:
        raise SystemExit("Local G2P fallback missing; refusing possible word omission")
    phonemes, tokens = pipeline.g2p(plain)
    missing = [t.text for t in tokens if re.search(r"[A-Za-z]", t.text) and not t.phonemes]
    if missing:
        raise SystemExit("Some reference words have no phonemes")
    consume = {"intent_sha256": sha(path), "guide_ordinal": intent["guide_ordinal"],
               "synthesis_speed": speed, "post_output_speedup": False,
               "phoneme_count": len(phonemes), "automatic_retries": 0,
               "consumed_at_utc": datetime.now(timezone.utc).isoformat()}
    with (out / "consume.json").open("x") as stream:
        json.dump(consume, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    started = time.monotonic()
    print(json.dumps({"event": "guide_synthesis_started", "speed": speed,
                      "phoneme_count": len(phonemes)}), flush=True)
    chunks = list(pipeline(plain, voice=str(weights / "voices/af_heart.pt"),
                           speed=speed, split_pattern=r"\n+"))
    if not chunks or any(chunk.audio is None for chunk in chunks):
        raise RuntimeError("Reference synthesis returned incomplete chunks")
    audio = torch.cat([chunk.audio for chunk in chunks]).detach().cpu().numpy()
    raw = out / "reference-native.wav"
    sf.write(raw, audio, 24000, subtype="PCM_16")
    duration = len(audio) / 24000
    outputs = [{"path": str(raw), "sha256": sha(raw), "bytes": raw.stat().st_size}]
    padded = None
    if duration <= 30.0:
        padded = out / "reference-30s.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(raw),
                        "-af", "aresample=48000,apad=whole_len=1440000", "-t", "30",
                        "-ac", "2", "-c:a", "pcm_s16le", str(padded)], check=True)
        outputs.append({"path": str(padded), "sha256": sha(padded),
                        "bytes": padded.stat().st_size})
    report = {"success": True, "intent_sha256": sha(path), "outputs": outputs,
              "native_duration_seconds": duration, "reference_duration_ready": duration <= 30,
              "reference_path": str(padded) if padded else None,
              "all_generator_chunks_collected": True, "chunks": len(chunks),
              "generated_graphemes": [chunk.graphemes for chunk in chunks],
              "synthesis_speed": speed, "post_output_speedup": False,
              "elapsed_seconds": round(time.monotonic() - started, 3),
              "role": "Spoken rhythm guide only; not an accepted song or voice",
              "packages": {p: importlib.metadata.version(p) for p in
                           ("kokoro", "misaki", "en-core-web-sm", "torch")},
              "human_hearing": "NOT_EVALUATED", "production_state_writes": 0,
              "completed_at_utc": datetime.now(timezone.utc).isoformat()}
    (out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"event": "guide_synthesis_finished", "native_seconds": duration,
                      "fits30s": duration <= 30, "chunks": len(chunks),
                      "outputs": outputs}), flush=True)


if __name__ == "__main__":
    main()
