from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from hashlib import sha256

from PIL import Image, ImageDraw
import pytest

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_cleanup_media import (
    VideoCleanupTools,
    _LocalRunner,
    _probe,
    _pcm_hash,
)
from ai_video.production.video_cleanup_viewing import (
    CleanupViewingProxyReceipt,
    prepare_cleanup_viewing_proxy,
)


@pytest.fixture
def tools():
    values = [
        os.environ.get(key) for key in ("AI_VIDEO_TEST_FFMPEG", "AI_VIDEO_TEST_FFPROBE")
    ]
    if not all(values):
        pytest.skip("explicit local FFmpeg/ffprobe paths required")
    return VideoCleanupTools(ffmpeg=Path(values[0]), ffprobe=Path(values[1]))


def _rgb_master(tmp_path, tools, *, audio=True, width=80, height=64, rate=12):
    frames = tmp_path / "rgb-frames"
    frames.mkdir()
    palette = (
        (198, 145, 118),  # skin-like
        (128, 128, 128),  # neutral gray
        (220, 30, 30),
        (30, 200, 40),
        (30, 50, 220),
    )
    for index in range(rate):
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        column = width // len(palette)
        for position, color in enumerate(palette):
            left = position * column
            right = (position + 1) * column if position < len(palette) - 1 else width
            draw.rectangle((left, 0, right - 1, height - 1), fill=color)
        image.save(frames / f"frame-{index:04d}.png")

    target = tmp_path / "rgb-master.mp4"
    argv = [
        str(tools.ffmpeg),
        "-nostdin",
        "-v",
        "error",
        "-framerate",
        str(rate),
        "-i",
        str(frames / "frame-%04d.png"),
    ]
    if audio:
        argv += [
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=32000:duration=1",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
        ]
    argv += [
        "-c:v",
        "libx264rgb",
        "-crf",
        "0",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "rgb24",
        "-threads",
        "1",
    ]
    if audio:
        argv += ["-c:a", "aac"]
    argv.append(str(target))
    subprocess.run(argv, check=True, capture_output=True)
    return target.read_bytes(), palette


def _yuv_master(tmp_path, tools):
    target = tmp_path / "yuv-master.mp4"
    subprocess.run(
        [
            str(tools.ffmpeg),
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=80x64:rate=12:duration=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-threads",
            "1",
            str(target),
        ],
        check=True,
        capture_output=True,
    )
    return target.read_bytes()


def _decode_first_frame(proxy_bytes, tools, tmp_path):
    path = tmp_path / "proxy-to-decode.mp4"
    path.write_bytes(proxy_bytes)
    runner = _LocalRunner(tools)
    return runner.run(
        "ffmpeg",
        [
            "-nostdin",
            "-v",
            "error",
            "-protocol_whitelist",
            "file",
            "-f",
            "mov",
            "-i",
            path,
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
    )


def _probe_pixel_tags(proxy_bytes, tools, tmp_path):
    path = tmp_path / "proxy-to-probe.mp4"
    path.write_bytes(proxy_bytes)
    runner = _LocalRunner(tools)
    raw = runner.run(
        "ffprobe",
        [
            "-v",
            "error",
            "-protocol_whitelist",
            "file",
            "-f",
            "mov",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,pix_fmt,color_range,color_space,color_primaries,color_transfer",
            "-of",
            "json",
            path,
        ],
    )
    return json.loads(raw)["streams"][0]


def test_viewing_proxy_is_separate_bt709_yuv420p_copy_preserving_frames_audio_and_colors(
    tmp_path, tools
):
    source, palette = _rgb_master(tmp_path, tools)
    result = prepare_cleanup_viewing_proxy(source_bytes=source, tools=tools)

    receipt = result.receipt
    assert result.media_bytes != source
    assert receipt.qualification == "NOT_EVALUATED"
    assert receipt.source.artifact_sha256 == sha256(source).hexdigest()
    assert receipt.output.artifact_sha256 == sha256(result.media_bytes).hexdigest()
    assert receipt.source.artifact_sha256 != receipt.output.artifact_sha256
    assert receipt.source_pixel_format in {"gbrp", "rgb24"}
    assert receipt.output_pixel_format == "yuv420p"
    assert receipt.output_color_range == "tv"
    assert receipt.output_color_space == "bt709"
    assert receipt.output_color_primaries == "bt709"
    assert receipt.output_color_transfer == "bt709"
    assert receipt.video_encoding == "libx264-crf17-veryfast-bt709-limited-yuv420p/1"
    assert receipt.source.width == receipt.output.width == 80
    assert receipt.source.height == receipt.output.height == 64
    assert (
        receipt.source.frame_count
        == receipt.output.frame_count
        == len(receipt.source_frame_times)
    )
    assert receipt.source_frame_times == receipt.output_frame_times
    assert receipt.source.duration_milliseconds == receipt.output.duration_milliseconds
    assert receipt.source.audio_stream_count == receipt.output.audio_stream_count == 1
    assert receipt.input_audio_sha256 == receipt.output_audio_sha256
    assert receipt.input_audio_sha256 is not None
    assert receipt.input_audio_signature == receipt.output_audio_signature
    assert receipt.ffmpeg_sha256 and receipt.ffprobe_sha256
    assert (
        CleanupViewingProxyReceipt.model_validate_json(receipt.model_dump_json())
        == receipt
    )

    frame = _decode_first_frame(result.media_bytes, tools, tmp_path)
    assert len(frame) == receipt.output.width * receipt.output.height * 3
    image = Image.frombytes("RGB", (receipt.output.width, receipt.output.height), frame)
    column = receipt.output.width // len(palette)
    tolerance = 20
    for index, expected in enumerate(palette):
        observed = image.getpixel(
            (index * column + column // 2, receipt.output.height // 2)
        )
        assert all(
            abs(actual - wanted) <= tolerance
            for actual, wanted in zip(observed, expected)
        ), (index, expected, observed)
    skin = image.getpixel((column // 2, receipt.output.height // 2))
    neutral = image.getpixel((column + column // 2, receipt.output.height // 2))
    assert skin[0] > skin[1] > skin[2]
    assert max(neutral) - min(neutral) <= tolerance

    probed = _probe_pixel_tags(result.media_bytes, tools, tmp_path)
    assert probed["codec_name"] == "h264"
    assert probed["pix_fmt"] == "yuv420p"
    assert probed["color_range"] == "tv"
    assert probed["color_space"] == "bt709"
    assert probed["color_primaries"] == "bt709"
    assert probed["color_transfer"] == "bt709"

    runner = _LocalRunner(tools)
    source_path, proxy_path = (
        tmp_path / "source-check.mp4",
        tmp_path / "proxy-check.mp4",
    )
    source_path.write_bytes(source)
    proxy_path.write_bytes(result.media_bytes)
    source_measured, source_times, source_signature = _probe(
        runner, source_path, source
    )
    output_measured, output_times, output_signature = _probe(
        runner, proxy_path, result.media_bytes
    )
    assert source_measured == receipt.source
    assert output_measured == receipt.output
    assert source_times == output_times == receipt.source_frame_times
    assert source_signature == output_signature == receipt.input_audio_signature
    assert _pcm_hash(runner, source_path, True) == _pcm_hash(runner, proxy_path, True)


def test_viewing_proxy_supports_silent_rgb_master(tmp_path, tools):
    source, _ = _rgb_master(tmp_path, tools, audio=False)
    result = prepare_cleanup_viewing_proxy(source_bytes=source, tools=tools)
    assert (
        result.receipt.source.audio_stream_count
        == result.receipt.output.audio_stream_count
        == 0
    )
    assert result.receipt.input_audio_sha256 is None
    assert result.receipt.input_audio_signature is None
    assert result.receipt.source_frame_times == result.receipt.output_frame_times


def test_viewing_proxy_rejects_non_rgb_input_and_resource_overflow(tmp_path, tools):
    from dataclasses import replace

    yuv_source = _yuv_master(tmp_path, tools)
    with pytest.raises(ValueError, match="RGB cleanup master"):
        prepare_cleanup_viewing_proxy(source_bytes=yuv_source, tools=tools)

    rgb_source, _ = _rgb_master(tmp_path, tools)
    with pytest.raises(ValueError, match="byte bound"):
        prepare_cleanup_viewing_proxy(
            source_bytes=rgb_source,
            tools=replace(tools, max_source_bytes=len(rgb_source) - 1),
        )


def test_viewing_receipt_seal_and_frame_identity_cannot_be_tampered(tmp_path, tools):
    source, _ = _rgb_master(tmp_path, tools)
    receipt = prepare_cleanup_viewing_proxy(source_bytes=source, tools=tools).receipt

    changed = receipt.model_dump(mode="json")
    changed["output_frame_times"][1] += 1
    with pytest.raises(ValueError, match="seal"):
        CleanupViewingProxyReceipt.model_validate(changed)

    resealed = receipt.model_dump(mode="json")
    resealed["output_frame_times"][1] += 1
    resealed["content_hash"] = canonical_sha256(resealed)
    with pytest.raises(ValueError, match="frame|timestamp"):
        CleanupViewingProxyReceipt.model_validate(resealed)

    extra = receipt.model_dump(mode="json")
    extra["unexpected"] = True
    with pytest.raises(ValueError):
        CleanupViewingProxyReceipt.model_validate(extra)
