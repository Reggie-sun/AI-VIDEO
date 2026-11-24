#!/usr/bin/env python3
"""Cut a v4 sung clip's exact generation window from the Demucs vocal stem: the vocal both lip-sync lanes send.

  uv run python outputs/ai-city-takeover/ep01/v4/gen/cut_audio.py SG03 [SG05 ...] [--out DIR]
  uv run python outputs/ai-city-takeover/ep01/v4/gen/cut_audio.py SG05 --name SG05m

For each clip id (tier "sung" in board/shots.json clips[]) the cut is samples [round(t0*sr), round(t1*sr)) of the stem,
downmixed to mono as floor((L+R+1)/2), written as 16-bit PCM WAV at the stem's rate (44.1 kHz) with no fade. That is the
v3 pilot method: v3 pilot/audio/U021.wav holds exactly those samples of the song-v3 stem (only its ffmpeg header differs).
The window is the clip's generation `window` {t0, t1} (handles included), not its `plays` span.

Refuses: a clip that is not sung; a window that starts inside a word of song/timing/words.json by more than 0.05 s (the
board_audit tolerance); an existing <clip>.wav with other bytes (an approval may already name it; never overwritten).
Each cut is sealed in <out>/windows.json (path, song_window, plays, samples, seconds, sha256), which unit.py checks.
--name (one clip only) writes <name>.wav sealed as windows[<name>] instead: a retake whose board window moved keeps the
earlier cut its approvals name (SG05m, 2026-11-22: SG05.wav stays the 59.157 cut of sd-SG05-n-1|2).
Prints one JSON line per clip with seconds (rounded 0.01) and sha256. Local only: reads the stem, writes WAVs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import wave

import numpy as np

P = Path(__file__).resolve().parent
REPO = P.parents[4]
BOARD = REPO / "outputs/ai-city-takeover/ep01/v4/board/shots.json"
WORDS = REPO / "outputs/ai-city-takeover/ep01/v4/song/timing/words.json"
STEM = REPO / "outputs/ai-city-takeover/ep01/v4/song/stems/htdemucs_ft/all-hands-r4-edc6c6bf/vocals.wav"
OUT = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/audio"
TOLERANCE = 0.05
FORMAT = "pcm_s16le mono at the stem rate; floor((L+R+1)/2) downmix; no fade (v3 pilot method)"


class Refused(ValueError):
    pass


def rel(path: Path) -> str:
    path = path.resolve()
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def cut_window(stem: Path, t0: float, t1: float) -> tuple[bytes, int, int]:
    """Mono 16-bit PCM frames of [round(t0*sr), round(t1*sr)) of a 16-bit WAV, its rate and its sample count."""
    with wave.open(str(stem)) as wav:
        sr, ch, width, total = wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes()
        if width != 2 or ch not in (1, 2):
            raise Refused(f"stem must be 16-bit mono or stereo PCM: {stem}")
        i0, i1 = round(t0 * sr), round(t1 * sr)
        if not 0 <= i0 < i1 <= total:
            raise Refused(f"window {t0}-{t1} s is outside the stem ({total / sr:.3f} s)")
        wav.setpos(i0)
        x = np.frombuffer(wav.readframes(i1 - i0), dtype="<i2").reshape(-1, ch).astype(np.int32)
    mono = x[:, 0] if ch == 1 else (x[:, 0] + x[:, 1] + 1) >> 1
    return mono.astype("<i2").tobytes(), sr, i1 - i0


def wav_bytes(frames: bytes, sr: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(frames)
    return buffer.getvalue()


def inside_word(t0: float, words: dict) -> list[str]:
    return [w["text"] for line in words["lines"] for w in line["words"]
            if w["start"] + TOLERANCE < t0 < w["end"] - TOLERANCE]


def cut(clip_id: str, out: Path = OUT, stem: Path = STEM, name: str | None = None) -> dict:
    name = name or clip_id
    clips = [c for c in json.loads(BOARD.read_text(encoding="utf-8"))["clips"] if c["clip"] == clip_id]
    if len(clips) != 1:
        raise Refused(f"{clip_id} is not one clip of the v4 board")
    clip = clips[0]
    if clip["tier"] != "sung":
        raise Refused(f"{clip_id} is a {clip['tier']} clip; only sung clips get a vocal window")
    t0, t1 = clip["window"]["t0"], clip["window"]["t1"]
    words = inside_word(t0, json.loads(WORDS.read_text(encoding="utf-8")))
    if words:
        raise Refused(f"{clip_id} window starts at {t0} s inside the word(s) {words}; move the window, do not cut it")
    frames, sr, n = cut_window(stem, t0, t1)
    payload = wav_bytes(frames, sr)
    target = out / f"{name}.wav"
    if target.exists() and target.read_bytes() != payload:
        raise Refused(f"{rel(target)} already exists with other bytes; it is never overwritten")
    book_path = out / "windows.json"
    source = {"source": rel(stem), "source_sha256": hashlib.sha256(stem.read_bytes()).hexdigest(), "format": FORMAT}
    book = json.loads(book_path.read_text(encoding="utf-8")) if book_path.exists() else {**source, "windows": {}}
    if {k: book.get(k) for k in source} != source:
        raise Refused(f"{rel(book_path)} was cut from another stem or format: {book.get('source')}")
    sha = hashlib.sha256(payload).hexdigest()
    entry = {"path": rel(target), "song_window": [t0, t1], "plays": [clip["plays"]["t0"], clip["plays"]["t1"]],
             "samples": n, "sample_rate_hz": sr, "seconds": round(n / sr, 2), "sha256": sha}
    sealed = {k: v for k, v in book["windows"].get(name, entry).items() if k != "plays"}
    if sealed != {k: v for k, v in entry.items() if k != "plays"}:      # `plays` (the edit's span) may move; the cut not
        raise Refused(f"{rel(book_path)} already seals another {name} window")
    out.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(payload)
    book["windows"][name] = entry
    book_path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"clip": clip_id, "path": entry["path"], "window": entry["song_window"], "samples": n,
            "seconds": entry["seconds"], "sha256": sha}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--out", type=Path, default=OUT, help="output folder (default ep01/v4/pilot/audio)")
    ap.add_argument("--name", help="file stem and windows.json key for a single clip (default: the clip id)")
    args = ap.parse_args()
    if args.name and len(args.clips) != 1:
        ap.error("--name takes exactly one clip")
    code = 0
    for clip_id in args.clips:
        try:
            print(json.dumps(cut(clip_id, out=args.out.resolve(), name=args.name), ensure_ascii=False))
        except Refused as error:
            print(json.dumps({"clip": clip_id, "refused": str(error)}, ensure_ascii=False), file=sys.stderr)
            code = 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
