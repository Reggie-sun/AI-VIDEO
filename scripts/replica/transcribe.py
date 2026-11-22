"""Transcribe local reference footage with an existing Whisper checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

from ai_video.errors import AiVideoError, ErrorCode

from scripts.replica._local import cli, tool_path, write_bytes


def load_model(checkpoint: Path):
    path = checkpoint.resolve(strict=True)
    if path.suffix != ".pt" or not path.is_file():
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Whisper requires an existing local .pt checkpoint.")
    try:
        import whisper

        return whisper.load_model(str(path))
    except Exception:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Cannot load the local Whisper checkpoint.") from None


def transcribe(model, media: Path, ffmpeg: Path, *, language: str = "zh") -> dict:
    """Prepare the same 16 kHz mono samples for reference and voice alignment."""
    path = media.resolve(strict=True)
    if not path.is_file():
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Transcription media must be a local file.")
    options: list[str] = []
    if path.suffix.lower() in {".mp4", ".mov", ".m4a"}:
        options = ["-f", "mov", "-enable_drefs", "0", "-use_absolute_path", "0"]
    result = subprocess.run(
        [str(ffmpeg), "-nostdin", "-v", "error", "-protocol_whitelist", "file", *options,
         "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "s16le", "pipe:1"],
        capture_output=True, check=False,
    )
    if result.returncode != 0 or not result.stdout:
        raise AiVideoError(ErrorCode.AUDIO_PROBE_FAILED, "Cannot decode an audio stream for transcription.")

    import numpy as np

    samples = np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768.0
    try:
        return model.transcribe(samples, language=language, word_timestamps=True,
                                condition_on_previous_text=False, temperature=0)
    except Exception:
        raise AiVideoError(ErrorCode.CAPTION_ALIGNMENT_INVALID, "Local Whisper transcription failed.") from None


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("media", nargs="+", metavar="NAME=MEDIA")
    parser.add_argument("--whisper-checkpoint", type=Path, required=True)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_args(argv)
    sources = {}
    for item in args.media:
        name, sep, source = item.partition("=")
        if not sep or not source or not re.fullmatch(r"[A-Za-z0-9_-]+", name) or name in sources:
            parser.error("each input must have a unique NAME=MEDIA")
        sources[name] = Path(source)

    ffmpeg = tool_path("ffmpeg", args.ffmpeg)
    model = load_model(args.whisper_checkpoint)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, media in sources.items():
        result = transcribe(model, media, ffmpeg, language=args.language)
        transcript = "".join(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text']}\n" for s in result["segments"])
        write_bytes(args.output_dir / f"{name}.whisper.json", json.dumps(result, ensure_ascii=False).encode())
        write_bytes(args.output_dir / f"{name}.txt", transcript.encode())
        print("done", name, flush=True)


if __name__ == "__main__":
    cli(main)
