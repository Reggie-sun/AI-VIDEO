from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from ai_video.production.video_cleanup_media import (
    VideoCleanupTools, prepare_video_cleanup, VideoCleanupReceipt,
)


@pytest.fixture
def tools():
    values = [os.environ.get(key) for key in ("AI_VIDEO_TEST_FFMPEG", "AI_VIDEO_TEST_FFPROBE")]
    if not all(values):
        pytest.skip("explicit local FFmpeg/ffprobe paths required")
    return VideoCleanupTools(ffmpeg=Path(values[0]), ffprobe=Path(values[1]))


def _source(tmp_path, tools, *, audio=True, size="80x64", rate="12"):
    target = tmp_path / "source.mp4"
    argv = [str(tools.ffmpeg), "-nostdin", "-v", "error", "-f", "lavfi", "-i",
            f"testsrc2=size={size}:rate={rate}:duration=1"]
    if audio:
        argv += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=32000:duration=1"]
    argv += ["-c:v", "libx264rgb", "-crf", "0", "-preset", "ultrafast", "-threads", "1"]
    if audio:
        argv += ["-c:a", "aac"]
    subprocess.run([*argv, str(target)], check=True, capture_output=True)
    return target.read_bytes()


def _plan(raw):
    return {"contract_version": "video-clean-plate/1", "source_sha256": hashlib.sha256(raw).hexdigest(), "frames": [
        {"frame_index": i, "patches": [{"plate_frame": 0,
            "polygons": [[[12, 12], [40, 12], [40, 40], [12, 40]]], "feather_px": 2}],
         "protected_polygons": [[[18, 18], [25, 18], [25, 25], [18, 25]]]}
        for i in (4, 5, 6)
    ]}


@pytest.mark.parametrize("audio,rate", [(True, "12"), (False, "24000/1001")])
def test_local_cleanup_preserves_all_decoded_frames_protection_and_native_audio(tmp_path, tools, audio, rate):
    raw = _source(tmp_path, tools, audio=audio, rate=rate)
    result = prepare_video_cleanup(source_bytes=raw, plan=_plan(raw), tools=tools)
    proof = result.receipt
    assert hashlib.sha256(result.media_bytes).hexdigest() == proof.output.artifact_sha256
    assert proof.source.artifact_sha256 == hashlib.sha256(raw).hexdigest()
    assert proof.source.frame_count == proof.output.frame_count == len(proof.frame_proofs)
    assert proof.source.width == proof.output.width == 80
    assert proof.source.audio_stream_count == proof.output.audio_stream_count == int(audio)
    assert proof.source_frame_times == proof.output_frame_times
    assert proof.input_audio_sha256 == proof.output_audio_sha256
    assert proof.input_audio_sha256 is not None if audio else proof.input_audio_sha256 is None
    assert all(frame.protected_pixel_changes == 0 for frame in proof.frame_proofs)
    assert any(frame.changed_pixel_count > 0 for frame in proof.frame_proofs)
    assert all(frame.input_rgb_sha256 == frame.output_rgb_sha256
               for i, frame in enumerate(proof.frame_proofs) if i not in (4, 5, 6))
    assert VideoCleanupReceipt.model_validate_json(proof.model_dump_json()) == proof


def test_bad_source_identity_and_out_of_range_plan_are_rejected(tmp_path, tools):
    raw = _source(tmp_path, tools)
    plan = _plan(raw)
    with pytest.raises(ValueError, match="identity"):
        prepare_video_cleanup(source_bytes=raw + b"changed", plan=plan, tools=tools)
    plan["frames"][0]["patches"][0]["plate_frame"] = 999
    with pytest.raises(ValueError, match="frame"):
        prepare_video_cleanup(source_bytes=raw, plan=plan, tools=tools)


def test_declared_media_resource_limits_fail_before_pixel_preparation(tmp_path, tools):
    from dataclasses import replace

    raw = _source(tmp_path, tools)
    for bounds in ({"max_frames": 1}, {"max_decoded_bytes": 1}, {"max_duration_milliseconds": 1},
                   {"max_audio_decoded_bytes": 1}):
        with pytest.raises(ValueError, match="bound"):
            prepare_video_cleanup(source_bytes=raw, plan=_plan(raw), tools=replace(tools, **bounds))


@pytest.mark.parametrize("changed", ["frames", "audio", "protection"])
def test_cleanup_proof_cannot_be_resealed_to_hide_frame_or_audio_changes(tmp_path, tools, changed):
    from ai_video.production.hashing import canonical_sha256

    raw = _source(tmp_path, tools)
    result = prepare_video_cleanup(source_bytes=raw, plan=_plan(raw), tools=tools)
    data = result.receipt.model_dump(mode="json")
    if changed == "frames":
        data["output"]["frame_count"] += 1
    elif changed == "audio":
        data["output_audio_sha256"] = "0" * 64
    else:
        data["frame_proofs"][4]["protected_pixel_changes"] = 1
    data["content_hash"] = canonical_sha256(data)
    with pytest.raises(ValueError):
        VideoCleanupReceipt.model_validate(data)
