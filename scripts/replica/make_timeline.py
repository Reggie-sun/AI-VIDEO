"""Lay voice groups end to end on a 30 fps timeline.

Each group starts after the previous one plus its own "gap" (frames, default 10); the first group starts at
frame LEAD + its gap. Group length is the ceiling of the exact normalized WAV.
The asset prefix names the versioned Agentcut folder receiving each <gid>.wav.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.ffmpeg_tools import run_command

from scripts.replica import align_lines, normalize_vo, tts_run
from scripts.replica._local import cli, read_json, tool_path, write_bytes
from scripts.replica.layers_kit import FPS

LEAD = 6


def probe_seconds(path: Path, ffprobe: Path) -> float:
    result = run_command([str(ffprobe), "-v", "error", "-protocol_whitelist", "file", "-f", "wav",
                          "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    duration = float(result.stdout)
    if not math.isfinite(duration) or duration <= 0:
        raise AiVideoError(ErrorCode.AUDIO_PROBE_FAILED, "Normalized take duration is invalid.")
    return duration


def build(groups, timings, durations: dict[str, float], src_prefix: str) -> list[dict]:
    t = LEAD
    tl = []
    for g in groups:
        gid = g["id"]
        t += int(g.get("gap", 10))
        df = math.ceil(durations[gid] * FPS)
        lines = []
        for i, ln in enumerate(timings[gid]["lines"]):
            if ln["start"] is None or ln["end"] is None:
                raise ValueError(f"{gid} 第{i + 1}句没有对齐到配音（可能漏读）：{ln['text']}")
            lines.append({"text": ln["text"], "from": t + round(ln["start"] * FPS), "to": t + round(ln["end"] * FPS)})
        tl.append({"id": gid, "from": t, "dur": df, "lines": lines, "src": f"{src_prefix}{gid}.wav"})
        t += df
    return tl


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("timings", type=Path)
    parser.add_argument("vo_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("src_prefix")
    parser.add_argument("--ffprobe", type=Path)
    args = parser.parse_args(argv)
    cfg = read_json(args.script)
    groups = tts_run.selected_groups(cfg)
    timings = read_json(args.timings)
    prefix = PurePosixPath(args.src_prefix)
    if prefix.is_absolute() or ".." in prefix.parts or not args.src_prefix.endswith("/") or args.src_prefix.startswith("."):
        parser.error("src_prefix must be a relative Agentcut asset directory ending in /")
    if args.output.resolve() in (args.script.resolve(), args.timings.resolve()):
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Timeline output overlaps an input.")

    ffprobe = tool_path("ffprobe", args.ffprobe)
    durations = {}
    for group in groups:
        gid = group["id"]
        take = normalize_vo.processed_path(group, cfg, args.vo_dir)
        alignment = timings[gid]
        lines = alignment["lines"]
        if (take.is_symlink() or not take.is_file() or take.resolve() == args.output.resolve()
                or alignment.get("audio_sha256") != hashlib.sha256(take.read_bytes()).hexdigest()
                or [line["text"] for line in lines] != group["lines"] or align_lines.weak_lines(lines)):
            raise AiVideoError(ErrorCode.CAPTION_ALIGNMENT_INVALID, f"Group {gid} needs current voice alignment.")
        durations[gid] = probe_seconds(take, ffprobe)
        if any(not 0 <= line["start"] <= line["end"] <= durations[gid] + 0.001 for line in lines
               if line["start"] is not None and line["end"] is not None):
            raise AiVideoError(ErrorCode.CAPTION_ALIGNMENT_INVALID, f"Group {gid} alignment exceeds its WAV.")
    try:
        tl = build(groups, timings, durations, args.src_prefix)
    except ValueError as exc:
        raise AiVideoError(ErrorCode.CAPTION_ALIGNMENT_INVALID, "A subtitle line is unaligned.") from exc
    write_bytes(args.output, json.dumps(tl, ensure_ascii=False, indent=1).encode())
    print("end", tl[-1]["from"] + tl[-1]["dur"])


if __name__ == "__main__":
    cli(main)
