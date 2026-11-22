"""Prepare the exact committed WAV for each selected Agentcut voice group."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.ffmpeg_tools import run_command

from ._local import cli, read_json, tool_path, write_bytes
from .tts_run import current_artifact, load_voice_project, selected_groups, take_name, voice_root


CHAIN = "acompressor=threshold=-32dB:ratio=3.5:attack=3:release=60:makeup=6dB,loudnorm=I=-16:TP=-1.5:LRA=7"


def current_takes(cfg: dict, vo_dir: Path, only: Iterable[str] = ()) -> dict[str, Path]:
    groups = selected_groups(cfg, only)
    loaded = load_voice_project(vo_dir, cfg)
    takes = {}
    for group in groups:
        artifact = current_artifact(loaded, group, cfg)
        if artifact is None:
            raise AiVideoError(ErrorCode.AUDIO_ASSET_INVALID, f"No exact committed take for {group['id']}.")
        takes[group["id"]] = artifact
    return takes


def processed_path(group: dict, cfg: dict, vo_dir: Path) -> Path:
    parent = voice_root(vo_dir).parent / "processed"
    if parent.is_symlink():
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "The processed voice directory must not be a symlink.")
    return parent / f"{take_name(group, cfg)}.wav"


def normalize(cfg: dict, vo_dir: Path, *, only: Iterable[str] = (), ffmpeg: Path) -> dict[str, Path]:
    groups = selected_groups(cfg, only)
    inputs = current_takes(cfg, vo_dir, [group["id"] for group in groups])
    outputs = {}
    for group in groups:
        group_id = group["id"]
        target = processed_path(group, cfg, vo_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".normalize-", dir=target.parent) as temporary:
            wav = Path(temporary) / "voice.wav"
            run_command([
                str(ffmpeg), "-nostdin", "-v", "error", "-protocol_whitelist", "file",
                "-f", "wav", "-i", str(inputs[group_id]), "-af", CHAIN, "-ar", "48000",
                "-ac", "2", "-c:a", "pcm_s16le", str(wav),
            ])
            write_bytes(target, wav.read_bytes())
        outputs[group_id] = target
    return outputs


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("vo_dir", type=Path)
    parser.add_argument("groups", nargs="*")
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_intermixed_args(argv)
    cfg = read_json(args.plan)
    for group_id, path in normalize(cfg, args.vo_dir, only=args.groups, ffmpeg=tool_path("ffmpeg", args.ffmpeg)).items():
        print(group_id, path)


if __name__ == "__main__":
    cli(main)
