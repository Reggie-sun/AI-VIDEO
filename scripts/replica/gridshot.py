"""Make a contact sheet with source-coordinate grids from local video frames."""

from __future__ import annotations

import argparse
from io import BytesIO
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.ffmpeg_tools import run_command

from ._local import cli, tool_path, write_bytes


def video_input_options(source: Path) -> list[str]:
    options = ["-protocol_whitelist", "file"]
    if source.suffix.lower() in {".mp4", ".mov", ".m4v"}:
        options.extend(["-f", "mov", "-enable_drefs", "0", "-use_absolute_path", "0"])
    return options


def grab_frame(source: Path, seconds: float, *, ffmpeg: Path):
    from PIL import Image

    if not isfinite(seconds) or seconds < 0 or not source.is_file():
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Frame extraction requires a local file and a nonnegative time.")
    with TemporaryDirectory(prefix="replica-frame-") as tmp:
        frame = Path(tmp) / "frame.png"
        run_command([str(ffmpeg), "-nostdin", "-v", "error", "-ss", str(seconds),
                     *video_input_options(source), "-i", str(source.resolve()),
                     "-frames:v", "1", "-threads", "1", str(frame)])
        if not frame.is_file():
            raise AiVideoError(ErrorCode.OUTPUT_INVALID, "The requested time has no video frame.")
        with Image.open(frame) as image:
            return image.convert("RGB")


def _grid_tile(source: Path, time: str, ffmpeg: Path):
    from PIL import Image, ImageDraw

    image = grab_frame(source, float(time), ffmpeg=ffmpeg)
    width, height = image.size
    scale = 1 if width < 500 else 0.76
    if scale != 1:
        image = image.resize((round(width * scale), round(height * scale)), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(image)
    for y in range(0, height, 40):
        yy = int(y * scale)
        draw.line((0, yy, image.width, yy), fill="#ff0000" if y % 200 == 0 else "#ffb400")
        draw.text((2, yy + 1), str(y), fill="#ff0000", stroke_width=1, stroke_fill="#202020")
    for x in range(0, width, 40):
        xx = int(x * scale)
        draw.line((xx, 0, xx, image.height), fill="#0060ff" if x % 200 == 0 else "#00a0ff")
        draw.text((xx + 1, 0), str(x), fill="#0060ff", stroke_width=1, stroke_fill="#202020")
    draw.text((4, image.height - 17), f"{source.name}@{time}", fill="#ff0000", stroke_width=1, stroke_fill="#202020")
    return image


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("frames", nargs="+", metavar="MEDIA@SECONDS")
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_args(argv)
    try:
        from PIL import Image
    except ImportError as error:
        raise AiVideoError(ErrorCode.CONFIG_INVALID, "Grid sheets require the existing Pillow dependency.") from error
    ffmpeg = tool_path("ffmpeg", args.ffmpeg)
    if args.output.suffix.lower() != ".png":
        parser.error("output must be a PNG")
    tiles = []
    for item in args.frames:
        media, time = item.rsplit("@", 1)
        if Path(media).resolve() == args.output.resolve():
            parser.error("output must differ from the source media")
        tiles.append(_grid_tile(Path(media), time, ffmpeg))
    sheet = Image.new("RGB", (sum(tile.width for tile in tiles), max(tile.height for tile in tiles)), "#282828")
    x = 0
    for tile in tiles:
        sheet.paste(tile, (x, 0))
        x += tile.width
    with BytesIO() as payload:
        sheet.save(payload, format="PNG")
        write_bytes(args.output, payload.getvalue())


if __name__ == "__main__":
    cli(main)
