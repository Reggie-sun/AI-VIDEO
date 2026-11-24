#!/usr/bin/env python3
"""List the exact inputs a v4 preview pack needs for the given board clips; reads files only, writes nothing.

  uv run python outputs/ai-city-takeover/ep01/v4/gen/units.py SG03 MO06

Per clip: tier and the lanes it can take (sung: 数字人 OmniHuman 1.5 or Seedance 2.0 multimodal lip-sync; motion:
Seedance 2.0 first frame), the generation window {t0, t1}, plays, seconds and the whole-second Seedance length (ceil),
the plate path + sha256 + size, for a sung clip the cut vocal path + sha256 + seconds and whether it is the window sealed
in pilot/audio/windows.json (cut_audio.py), the board's words and the timed words (song/timing/words.json) inside the
window, and each shot's set / framing / action / camera / look text.
Exit 2 when any input is missing or unsealed (plate not drawn, vocal not cut): a preview pack is never built from
partial inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import wave

from PIL import Image

P = Path(__file__).resolve().parent
REPO = P.parents[4]
BOARD = REPO / "outputs/ai-city-takeover/ep01/v4/board/shots.json"
WORDS = REPO / "outputs/ai-city-takeover/ep01/v4/song/timing/words.json"
PLATES = REPO / "outputs/ai-city-takeover/ep01/v4/board/plates"
AUDIO = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/audio"
LANES = {"sung": ["omnihuman-1.5 (数字人 大师模式)", "seedance_2.0_vip multimodal (全能参考对嘴)"],
         "motion": ["seedance_2.0_vip first_frame"]}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plate_entry(plate: str) -> dict:
    path = PLATES / f"{plate}.png"
    if not path.is_file():
        return {"path": rel(path), "missing": True}
    with Image.open(path) as im:
        size = list(im.size)
    return {"path": rel(path), "sha256": sha(path), "size": size}


def audio_entry(clip: dict, audio: Path) -> dict:
    path = audio / f"{clip['clip']}.wav"
    if not path.is_file():
        return {"path": rel(path), "missing": True, "cut": f"cut_audio.py {clip['clip']}"}
    with wave.open(str(path)) as wav:
        n, sr, ch = wav.getnframes(), wav.getframerate(), wav.getnchannels()
    digest = sha(path)
    book = audio / "windows.json"
    sealed = (json.loads(book.read_text(encoding="utf-8"))["windows"].get(clip["clip"]) or {}) if book.is_file() else {}
    window = [clip["window"]["t0"], clip["window"]["t1"]]
    return {"path": rel(path), "sha256": digest, "seconds": round(n / sr, 2), "channels": ch, "sample_rate_hz": sr,
            "sealed_window": sealed.get("path") == rel(path) and sealed.get("sha256") == digest
            and sealed.get("song_window") == window}


def pack(clip_ids: list[str], audio: Path = AUDIO) -> dict:
    raw = BOARD.read_bytes()
    board = json.loads(raw)
    clips = {c["clip"]: c for c in board["clips"]}
    shots = {s["id"]: s for s in board["shots"]}
    words = [w for line in json.loads(WORDS.read_text(encoding="utf-8"))["lines"] for w in line["words"]]
    out, missing = [], []
    for clip_id in clip_ids:
        clip = clips.get(clip_id)
        if clip is None:
            missing.append(f"{clip_id}: not a clip of the board")
            continue
        t0, t1 = clip["window"]["t0"], clip["window"]["t1"]
        entry = {"clip": clip_id, "tier": clip["tier"], "kind": clip["kind"], "lanes": LANES.get(clip["tier"], []),
                 "window": {"t0": t0, "t1": t1}, "plays": clip["plays"], "seconds": clip["seconds"],
                 "seedance_seconds": math.ceil(clip["seconds"]), "plate": plate_entry(clip["start_frame"]),
                 "board_words": clip["words"],
                 "timed_words": [{"text": w["text"], "start": w["start"], "end": w["end"],
                                  "at": round(w["start"] - t0, 3)} for w in words if w["end"] > t0 and w["start"] < t1],
                 "shots": [{k: shots[s].get(k) for k in ("id", "t0", "t1", "section", "set", "framing", "action", "camera",
                                                       "look", "clip_words")} for s in clip["used_by"]]}
        if entry["plate"].get("missing"):
            missing.append(f"{clip_id}: plate {entry['plate']['path']} not drawn")
        if clip["tier"] == "sung":
            entry["audio"] = audio_entry(clip, audio)
            if entry["audio"].get("missing") or not entry["audio"]["sealed_window"]:
                missing.append(f"{clip_id}: vocal {entry['audio']['path']} not cut or not the sealed window")
        out.append(entry)
    return {"board": {"path": rel(BOARD), "sha256": hashlib.sha256(raw).hexdigest()}, "clips": out, "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--audio", type=Path, default=AUDIO, help="vocal folder (default ep01/v4/pilot/audio)")
    args = ap.parse_args()
    result = pack(args.clips, audio=args.audio.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 2 if result["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
