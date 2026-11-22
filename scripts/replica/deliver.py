"""Prepare local Agentcut exports, subtitle sidecars, and covers for delivery."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.ffmpeg_tools import run_command

from ._local import agentcut_project, cli, project_root, read_json, tool_path, write_bytes
from .gridshot import grab_frame, video_input_options
from .layers_kit import FPS

_SUBDIR = "另附字幕文件"


def ts(frame: int) -> str:
    ms = round(frame / FPS * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt_items(layers: dict) -> list[tuple[int, int, str]]:
    subs = next((track for track in layers["tracks"] if track["id"] == "subs"), None)
    if subs is None:
        raise ValueError("An Agentcut subtitle track is required.")
    items = []
    for c in sorted(subs["clips"], key=lambda c: c["from"]):
        ls = c["props"]["lines"]
        for i, ln in enumerate(ls):
            a = c["from"] + ln["from"]
            b = c["from"] + (ls[i + 1]["from"] if i + 1 < len(ls) else c["duration"])
            items.append((a, b, ln["text"]))
    return items


def _layers(project: Path) -> dict:
    path = project / "layers.json"
    if path.is_symlink() or not path.is_file():
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Agentcut layers.json must be a regular file.")
    return read_json(path)


def _write_srt(layers: dict, out: Path) -> int:
    if out.suffix.lower() != ".srt" or any(
        item.suffix.lower() == ".mp4" and item.stem.casefold() == out.stem.casefold()
        for item in out.parent.iterdir()
    ):
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Put the subtitle sidecar in its own folder.")
    items = srt_items(layers)
    payload = "".join(f"{index}\n{ts(start)} --> {ts(stop)}\n{line}\n\n"
                      for index, (start, stop, line) in enumerate(items, 1))
    write_bytes(out, payload.encode("utf-8"))
    return len(items)


def write_srt(project_dir: Path, out: Path) -> int:
    return _write_srt(_layers(agentcut_project(project_dir)), out)


def _color_options(source: Path, ffprobe: Path) -> list[str]:
    result = run_command([
        str(ffprobe), "-v", "error", *video_input_options(source), "-select_streams", "v:0",
        "-show_entries", "stream=color_space,color_transfer,color_primaries", "-of", "json", str(source),
    ])
    streams = json.loads(result.stdout).get("streams", [])
    if not streams:
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "No video stream was found in the export.")
    # Some FFmpeg builds drop these fields on encode. Preserve measured values.
    options = []
    for key, option in (("color_space", "-colorspace"), ("color_transfer", "-color_trc"),
                        ("color_primaries", "-color_primaries")):
        value = streams[0].get(key)
        if value and value not in {"unknown", "reserved"}:
            options.extend((option, value))
    return options


def transcode(src: Path, out: Path, *, ffmpeg: Path | None = None, ffprobe: Path | None = None) -> None:
    if src.suffix.lower() != ".mp4" or not src.is_file() or out.suffix.lower() != ".mp4" or out.exists() or out.is_symlink():
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Transcode requires an MP4 source and a new MP4 output path.")
    if any(item.suffix.lower() == ".srt" and item.stem.casefold() == out.stem.casefold()
           for item in out.parent.iterdir()):
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Move the same-named SRT into the subtitle folder first.")
    tool = tool_path("ffmpeg", ffmpeg)
    color_options = _color_options(src.resolve(), tool_path("ffprobe", ffprobe))
    with TemporaryDirectory(prefix=".replica-transcode-", dir=out.parent) as tmp:
        candidate = Path(tmp) / "output.mp4"
        run_command([str(tool), "-nostdin", "-v", "error", *video_input_options(src),
                     "-i", str(src.resolve()), "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
                     "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", *color_options, "-c:a", "copy",
                     "-movflags", "+faststart", str(candidate)])
        if not candidate.is_file() or not candidate.stat().st_size:
            raise AiVideoError(ErrorCode.OUTPUT_INVALID, "FFmpeg did not produce an MP4.")
        out.hardlink_to(candidate)


def _phone(shot, h: int):
    from PIL import Image, ImageDraw

    w = round(shot.width * h / shot.height)
    shot = shot.resize((w, h), Image.LANCZOS)
    B, R = 18, 56
    ph = Image.new("RGBA", (w + 2 * B, h + 2 * B), (0, 0, 0, 0))
    ImageDraw.Draw(ph).rounded_rectangle([0, 0, w + 2 * B - 1, h + 2 * B - 1], R + B, fill=(13, 14, 17, 255), outline=(70, 73, 82, 255), width=3)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], R, fill=255)
    ph.paste(shot, (B, B), m)
    return ph


def cover(out: Path, title: str, sub: str, chip: str, notes: list[str],
          shots: list[tuple[Path, float, float, tuple[int, int]]], *,
          font: Path, font_index: int = 0, ffmpeg: Path | None = None) -> None:
    """Render a cover from one or two caller-reviewed redacted shots."""
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as error:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Cover generation requires the existing Pillow dependency.") from error

    if not (1 <= len(shots) <= 2) or not font.is_file() or font_index < 0:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Provide a local font and one or two shots for the cover.")
    tool = tool_path("ffmpeg", ffmpeg)

    def cover_font(size: int):
        return ImageFont.truetype(str(font), size, index=font_index)

    W, H = 1920, 1080
    im = Image.new("RGB", (W, H), (27, 29, 34))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(44, 47, 54), width=1)
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(44, 47, 54), width=1)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([1050, 80, 1850, 1000], fill=(255, 80, 60, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im.paste(glow, (0, 0), glow)
    phs = [
        (_phone(grab_frame(media, seconds, ffmpeg=tool), 760).rotate(
            angle, expand=True, resample=Image.Resampling.BICUBIC), position)
        for media, seconds, angle, position in shots
    ]
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for p, (x, y) in phs:
        a = p.split()[3].point(lambda v: 150 if v else 0)
        s = Image.new("RGBA", p.size, (0, 0, 0, 255))
        s.putalpha(a)
        sh.paste(s, (x + 10, y + 30), s)
    sh = sh.filter(ImageFilter.GaussianBlur(24))
    im.paste(sh, (0, 0), sh)
    for p, pos in phs:
        im.paste(p, pos, p)
    d = ImageDraw.Draw(im)

    def text(xy, s, size, fill, stroke=6):
        d.text(xy, s, font=cover_font(size), fill=fill, stroke_width=stroke, stroke_fill=(10, 10, 12))

    text((110, 200), title, 128 if len(title) <= 7 else 104, (255, 210, 63), 8)
    text((110, 370), sub, 100 if len(sub) <= 8 else 84, (255, 255, 255), 7)
    tw = d.textlength(chip, font=cover_font(66))
    d.rounded_rectangle([110, 540, 110 + tw + 60, 640], 24, fill=(255, 59, 48))
    d.text((140, 548), chip, font=cover_font(66), fill=(255, 255, 255))
    for i, n in enumerate(notes):
        text((110, 700 + 80 * i), n, 50, (230, 231, 236), 4)
    with BytesIO() as payload:
        im.save(payload, format="PNG")
        write_bytes(out, payload.getvalue())


def _cover_shots(spec: dict, layers: dict, project: Path, root: Path) -> list:
    sources = {clip["src"] for track in layers["tracks"] if track.get("kind") == "video"
               for clip in track["clips"] if "src" in clip}
    shots = []
    for filename, seconds, angle, position in spec["shots"]:
        relative = Path(filename)
        if relative.is_absolute() or ".." in relative.parts or filename not in sources:
            raise AiVideoError(ErrorCode.CONFIG_INVALID, "Cover shots must refer to footage in the same Agentcut cut.")
        source = (project / relative).resolve(strict=True)
        if not source.is_relative_to(root) or not source.is_file():
            raise AiVideoError(ErrorCode.CONFIG_INVALID, "Cover footage must stay within the Agentcut projects root.")
        shots.append((source, seconds, angle, position))
    return shots


def _single_name(value: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value or "\\" in value:
        raise ValueError("Project and delivery names must be single path components.")
    return value


def package(recipe: Path, out: Path, *, projects: Path | None, font: Path,
            font_index: int = 0, ffmpeg: Path | None = None) -> None:
    """Prepare cover and subtitle files from reviewed cuts without touching their exports."""
    projects = project_root(projects)
    jobs = read_json(recipe)["jobs"]
    if not jobs or out.is_symlink() or (out / _SUBDIR).is_symlink():
        raise ValueError("Provide delivery jobs and a local delivery directory.")
    names = [_single_name(job["name"]) for job in jobs]
    if len(set(names)) != len(names):
        raise ValueError("Delivery names must be unique.")
    for name in names:
        for target in (out / f"{name}-封面.png", out / _SUBDIR / f"{name}.srt"):
            if target.exists() or target.is_symlink():
                raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Delivery cover or subtitle already exists.")
    out.mkdir(parents=True, exist_ok=True)
    pending = []
    with TemporaryDirectory(prefix=".replica-delivery-", dir=out) as tmp:
        stage = Path(tmp)
        for name, job in zip(names, jobs):
            project = agentcut_project(projects / _single_name(job["project"]))
            layers = _layers(project)
            job_cover = job["cover"]
            cover_path = stage / f"{name}-封面.png"
            subtitle = stage / f"{name}.srt"
            _write_srt(layers, subtitle)
            cover(
                cover_path, job_cover["title"], job_cover["sub"], job_cover["chip"], job_cover["notes"],
                _cover_shots(job_cover, layers, project, projects),
                font=font, font_index=font_index, ffmpeg=ffmpeg,
            )
            pending.extend(((cover_path, out / cover_path.name), (subtitle, out / _SUBDIR / subtitle.name)))
        (out / _SUBDIR).mkdir(exist_ok=True)
        published = []
        try:
            for source, target in pending:
                target.hardlink_to(source)
                published.append((source, target))
        except OSError:
            for source, target in published:
                if target.exists() and target.samefile(source):
                    target.unlink()
            raise


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    srt = subparsers.add_parser("srt")
    srt.add_argument("project", type=Path)
    srt.add_argument("output", type=Path)
    trans = subparsers.add_parser("transcode")
    trans.add_argument("source", type=Path)
    trans.add_argument("output", type=Path)
    trans.add_argument("--ffmpeg", type=Path)
    trans.add_argument("--ffprobe", type=Path)
    bundle = subparsers.add_parser("package")
    bundle.add_argument("recipe", type=Path)
    bundle.add_argument("output", type=Path)
    bundle.add_argument("--projects-root", type=Path)
    bundle.add_argument("--ffmpeg", type=Path)
    bundle.add_argument("--font", type=Path, required=True)
    bundle.add_argument("--font-index", type=int, default=0)
    args = parser.parse_args(argv)
    if args.command == "srt":
        print("srt lines", write_srt(args.project, args.output))
    elif args.command == "transcode":
        transcode(args.source, args.output, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
        print("ok", args.output)
    else:
        package(args.recipe, args.output, projects=args.projects_root,
                font=args.font, font_index=args.font_index, ffmpeg=args.ffmpeg)
        print("ok", args.output)


if __name__ == "__main__":
    cli(main)
