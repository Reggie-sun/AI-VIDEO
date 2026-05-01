import subprocess

import pytest

from ai_video.ffmpeg_tools import (
    concat_list_text,
    extract_last_frame,
    ffmpeg_available,
    normalize_clip,
)


def test_concat_list_escapes_single_quotes():
    text = concat_list_text(["/tmp/a clip.mp4", "/tmp/b'clip.mp4"])
    assert "file '/tmp/a clip.mp4'" in text
    assert "file '/tmp/b'\\''clip.mp4'" in text


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not available")
def test_extract_last_frame_from_tiny_video(tmp_path):
    source = tmp_path / "source.mp4"
    frame = tmp_path / "last frame.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=64x64:rate=4",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    extract_last_frame(source, frame)
    assert frame.exists()
    assert frame.stat().st_size > 0


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not available")
def test_normalize_clip_writes_output(tmp_path):
    source = tmp_path / "source.mp4"
    target = tmp_path / "normalized.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=64x64:rate=4",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    normalize_clip(source, target, width=64, height=64, fps=4, encoder="libx264")
    assert target.exists()
    assert target.stat().st_size > 0
