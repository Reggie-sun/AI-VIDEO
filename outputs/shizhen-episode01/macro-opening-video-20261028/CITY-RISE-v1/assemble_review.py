"""Review assembly: approved municipal -> CITY-RISE (+dispatch radio, captions) -> approved B6.

Review-only 1080p encode for the user to watch at normal speed; not a Production
HyperFrames render, not delivery. Municipal and B6 pictures/audio are untouched
apart from format conversion; CITY-RISE is upscaled from 480p.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FF = "/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg"
MUN = ROOT / "outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4"
B6 = ROOT / "outputs/shizhen-episode01/fusion-B-motion-20261027/variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4"
MUN_FRAMES = 164  # 6.833s @24
RADIO_GAIN_DB = -12.5
AMBIENCE_GAIN_DB = -4.0


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ass_time(t: float) -> str:
    cs = int(round(t * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def main(rise: Path, rise_frames: int) -> None:
    out_dir = HERE / "assembly"
    out_dir.mkdir(exist_ok=True)
    cues = json.loads((HERE / "dispatch/dispatch-cues.json").read_text())
    offset = MUN_FRAMES / 24 - 1 / 24  # CITY-RISE frame 0 is dropped
    ass = out_dir / "dispatch-captions.ass"
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: B6,Noto Sans CJK SC Medium,54,&H00FFFFFF,&H00FFFFFF,&H64000000,&H78000000,0,0,0,0,100,100,2,0,1,1.4,1.5,2,60,60,52,1",
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for c in cues["cues"]:
        lines.append(f"Dialogue: 0,{ass_time(offset + c['start'])},{ass_time(offset + c['caption_end'])},B6,,0,0,0,,{c['text']}")
    ass.write_text("\n".join(lines) + "\n")
    # CITY-RISE: drop the last frame (duplicate of B6 f0); start frame kept (municipal last frame repeats once? see cut note)
    keep = rise_frames - 1
    out = out_dir / "失帧-独立开场-城市调度版-审看-1080p.mp4"
    fc = (
        f"[0:v]setpts=N/24/TB,scale=1920:1080,setsar=1[v0];"
        f"[1:v]select='between(n\\,1\\,{keep - 1})',setpts=N/24/TB,scale=1920:1080:flags=lanczos,setsar=1[v1];"
        f"[2:v]setpts=N/24/TB,scale=1920:1080,setsar=1[v2];"
        f"[v0][v1][v2]concat=n=3:v=1:a=0,subtitles=filename='{ass.as_posix()}'[v];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a0];"
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=start={1/24}:end={keep/24},asetpts=PTS-STARTPTS,volume={AMBIENCE_GAIN_DB}dB[amb];"
        f"[3:a]aresample=48000,aformat=channel_layouts=stereo,atrim=start={1/24}:end={keep/24},asetpts=PTS-STARTPTS,volume={RADIO_GAIN_DB}dB[rad];"
        f"[amb][rad]amix=inputs=2:normalize=0:duration=first[a1];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a2];"
        f"[a0][a1][a2]concat=n=3:v=0:a=1[a]")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(MUN), "-i", str(rise), "-i", str(B6),
                    "-i", str(HERE / "dispatch" / cues["audio"]), "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-r", "24", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    record = {"kind": "review_assembly/1", "not_delivery": True, "path": str(out.relative_to(ROOT)), "sha256": sha(out),
              "segments": [{"name": "municipal", "path": str(MUN.relative_to(ROOT)), "sha256": sha(MUN), "frames": MUN_FRAMES},
                           {"name": "CITY-RISE", "path": str(rise.relative_to(ROOT)), "sha256": sha(rise),
                            "frames_used": f"1..{keep - 1}", "note": "frame0 dropped (municipal last frame duplicate), last frame dropped (B6 f0 duplicate)"},
                           {"name": "B6", "path": str(B6.relative_to(ROOT)), "sha256": sha(B6)}],
              "captions": str(ass.relative_to(ROOT)), "caption_offset_seconds": offset - 1 / 24,
              "radio_gain_db": RADIO_GAIN_DB, "ambience_gain_db": AMBIENCE_GAIN_DB,
              "scope": "review only; CITY-RISE upscaled from 480p; captions burned via libass, not HyperFrames"}
    (out_dir / "assembly-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"out": record["path"], "sha256": record["sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), int(sys.argv[2]))
