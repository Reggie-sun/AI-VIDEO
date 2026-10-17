from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import subprocess
import wave
from types import SimpleNamespace
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._hyperframes_native_audio import (
    _fit_segment_sample_count,
    derive_native_audio_pcm,
)
import ai_video.production._hyperframes_native_audio as native_audio
from ai_video.production.audio_retime_contracts import (
    AudioTimeSegment,
    NativeAudioRetime,
)
from ai_video.production.composition import timeline_fingerprint
from ai_video.production.composition_contracts import AudioKind, ResolvedAudioSpan
from ai_video.production.hyperframes import (
    materialize_hyperframes_source,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import RendererAudioBinding
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.project import _validate_source_timeline_bindings
from test_production_hyperframes import (
    _reseal_timeline,
    make_asset_sources,
    make_resolved_timeline,
)


def _tool_paths() -> tuple[Path, Path]:
    ffmpeg_value = os.environ.get("AI_VIDEO_TEST_FFMPEG")
    ffprobe_value = os.environ.get("AI_VIDEO_TEST_FFPROBE")
    if not ffmpeg_value or not ffprobe_value:
        pytest.skip("set explicit AI_VIDEO_TEST_FFMPEG and AI_VIDEO_TEST_FFPROBE paths")
    return Path(ffmpeg_value), Path(ffprobe_value)


def _write_piecewise_tone(path: Path, *, rate: int = 48_000) -> None:
    frequencies = (
        (0, 2 * rate, 440),
        (2 * rate, 3 * rate, 660),
        (3 * rate, 5 * rate, 880),
    )
    samples: list[int] = []
    for start, end, frequency in frequencies:
        samples.extend(
            int(12_000 * math.sin(2 * math.pi * frequency * sample / rate))
            for sample in range(start, end)
        )
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def _make_mp4(
    tmp_path: Path,
    *,
    with_audio: bool = True,
    nonzero_origin: bool = False,
    audio_offset_seconds: int = 0,
) -> Path:
    ffmpeg, _ = _tool_paths()
    tone = tmp_path / "tone.wav"
    output = tmp_path / ("source-offset.mp4" if nonzero_origin else "source.mp4")
    _write_piecewise_tone(tone)
    args = [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=32x32:r=24:d=5",
    ]
    if with_audio:
        if audio_offset_seconds:
            args.extend(("-itsoffset", str(audio_offset_seconds)))
        args.extend(("-i", str(tone), "-map", "0:v:0", "-map", "1:a:0"))
    else:
        args.extend(("-map", "0:v:0", "-an"))
    if nonzero_origin:
        args.extend(("-output_ts_offset", "1"))
    args.extend(
        (
            "-t",
            "5",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
        )
    )
    if with_audio:
        args.extend(("-c:a", "aac", "-b:a", "128k"))
    args.extend(("-movflags", "+faststart", "-y", str(output)))
    subprocess.run(args, check=True, capture_output=True, timeout=60)
    return output


def _mapping(*segments: AudioTimeSegment) -> NativeAudioRetime:
    return NativeAudioRetime(
        visual_layer_id="video-layer",
        stream_index=0,
        time_map_sha256="a" * 64,
        segments=segments,
    )


def _derive(tmp_path: Path, *, mapping: NativeAudioRetime):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    return derive_native_audio_pcm(
        snapshot,
        source_video_asset_id="source-video",
        source_video_sha256=snapshot.file_sha256,
        track_id="native-track",
        mapping=mapping,
        sample_rate_hz=48_000,
        max_correction_samples=2_000,
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
    )


def _frequency(pcm: bytes, *, start_sample: int, samples: int, rate: int) -> float:
    values = struct.unpack(
        f"<{samples * 2}h", pcm[start_sample * 4 : (start_sample + samples) * 4]
    )
    mono = values[0::2]
    crossings = sum((left < 0) != (right < 0) for left, right in zip(mono, mono[1:]))
    return crossings * rate / (2 * samples)


def test_native_video_audio_retime_preserves_pitch_and_piecewise_sample_timing(
    tmp_path,
):
    mapping = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=96_000,
            output_offset_sample=0,
            output_duration_samples=48_000,
        ),
        AudioTimeSegment(
            source_start_sample=96_000,
            source_duration_samples=48_000,
            output_offset_sample=48_000,
            output_duration_samples=96_000,
        ),
        AudioTimeSegment(
            source_start_sample=144_000,
            source_duration_samples=96_000,
            output_offset_sample=144_000,
            output_duration_samples=96_000,
        ),
    )

    pcm, proof = _derive(tmp_path, mapping=mapping)

    assert len(pcm) == 240_000 * 4
    assert proof.mapped_samples == 240_000
    assert proof.input_samples == 240_000
    assert proof.source_video_asset_id == "source-video"
    assert proof.track_id == "native-track"
    assert [item.segment for item in proof.segment_results] == list(mapping.segments)
    assert (
        abs(_frequency(pcm, start_sample=18_000, samples=9_600, rate=48_000) - 440) < 15
    )
    assert (
        abs(_frequency(pcm, start_sample=84_000, samples=9_600, rate=48_000) - 660) < 15
    )
    assert (
        abs(_frequency(pcm, start_sample=168_000, samples=9_600, rate=48_000) - 880)
        < 15
    )


def test_native_video_audio_keeps_initial_gap_when_audio_stream_starts_late(tmp_path):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path, audio_offset_seconds=1)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    mapping = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=96_000,
            output_offset_sample=0,
            output_duration_samples=96_000,
        )
    )

    pcm, proof = derive_native_audio_pcm(
        snapshot,
        source_video_asset_id="source-video",
        source_video_sha256=snapshot.file_sha256,
        track_id="native-track",
        mapping=mapping,
        sample_rate_hz=48_000,
        max_correction_samples=2_000,
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
    )

    assert proof.input_samples == 96_000
    assert proof.audio_start_sample == 46_944
    initial_gap = struct.unpack("<93888h", pcm[: 46_944 * 4])
    assert max(abs(value) for value in initial_gap) == 0
    assert (
        abs(_frequency(pcm, start_sample=60_000, samples=9_600, rate=48_000) - 440) < 15
    )


def test_native_video_audio_rejects_audio_timestamp_before_video_origin(monkeypatch):
    payload = {
        "streams": [
            {"codec_type": "video", "start_time": "0.000000"},
            {
                "codec_type": "audio",
                "index": 1,
                "start_pts": -4800,
                "time_base": "1/48000",
                "start_time": "-0.100000",
            },
        ]
    }
    monkeypatch.setattr(
        native_audio,
        "_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=(), returncode=0, stdout=json.dumps(payload), stderr=""
        ),
    )

    with pytest.raises(AiVideoError) as caught:
        native_audio._probe_source(11, 12, sample_rate_hz=48_000)

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID


def test_native_video_audio_uses_first_video_stream_as_clock_origin(monkeypatch):
    payload = {
        "streams": [
            {"codec_type": "video", "start_time": "0.000000"},
            {"codec_type": "audio", "index": 1, "start_time": "0.000000"},
            {"codec_type": "video", "start_time": "1.000000"},
        ]
    }
    monkeypatch.setattr(
        native_audio,
        "_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=(), returncode=0, stdout=json.dumps(payload), stderr=""
        ),
    )

    assert native_audio._probe_source(11, 12, sample_rate_hz=48_000) == 0


def test_native_audio_same_video_supports_independent_retime_maps(tmp_path):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    first_map = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=96_000,
            output_offset_sample=0,
            output_duration_samples=48_000,
        )
    )
    second_map = _mapping(
        AudioTimeSegment(
            source_start_sample=96_000,
            source_duration_samples=48_000,
            output_offset_sample=0,
            output_duration_samples=96_000,
        )
    )

    first_pcm, first_proof = derive_native_audio_pcm(
        snapshot,
        source_video_asset_id="source-video",
        source_video_sha256=snapshot.file_sha256,
        track_id="first-track",
        mapping=first_map,
        sample_rate_hz=48_000,
        max_correction_samples=2_000,
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
    )
    second_pcm, second_proof = derive_native_audio_pcm(
        snapshot,
        source_video_asset_id="source-video",
        source_video_sha256=snapshot.file_sha256,
        track_id="second-track",
        mapping=second_map,
        sample_rate_hz=48_000,
        max_correction_samples=2_000,
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
    )

    assert len(first_pcm) == 48_000 * 4
    assert len(second_pcm) == 96_000 * 4
    assert first_proof.track_id == "first-track"
    assert second_proof.track_id == "second-track"
    assert first_proof.mapping_sha256 != second_proof.mapping_sha256


def test_hyperframes_materializes_and_reader_validates_reused_video_audio_tracks(
    tmp_path,
):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path)
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    base = make_resolved_timeline()
    video_spans = (
        base.visual_spans[0].model_copy(
            update={
                "asset_id": "source-video",
                "asset_sha256": source_hash,
                "asset_mime_type": "video/mp4",
                "materialized_path": Path(f"assets/{source_hash}.mp4"),
                "duration_frames": 5,
                "duration_samples": 10_000,
                "trim_start_frame": 0,
                "trim_duration_frames": 5,
            }
        ),
        base.visual_spans[1].model_copy(
            update={
                "asset_id": "source-video",
                "asset_sha256": source_hash,
                "asset_mime_type": "video/mp4",
                "materialized_path": Path(f"assets/{source_hash}.mp4"),
                "trim_start_frame": 48,
                "trim_duration_frames": 5,
            }
        ),
    )
    first_map = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=10_000,
            output_offset_sample=0,
            output_duration_samples=10_000,
        )
    ).model_copy(update={"visual_layer_id": "layer-red"})
    second_map = _mapping(
        AudioTimeSegment(
            source_start_sample=96_000,
            source_duration_samples=10_000,
            output_offset_sample=0,
            output_duration_samples=10_000,
        )
    ).model_copy(update={"visual_layer_id": "layer-blue"})
    audio_spans = (
        ResolvedAudioSpan(
            track_id="native-track-1",
            audio_kind=AudioKind.NATIVE_VIDEO,
            asset_id="source-video",
            asset_sha256=source_hash,
            start_sample=0,
            duration_samples=10_000,
            source_start_sample=0,
            source_duration_samples=10_000,
            gain_millidb=0,
            fade_in_samples=0,
            fade_out_samples=0,
            native_audio_retime=first_map,
        ),
        ResolvedAudioSpan(
            track_id="native-track-2",
            audio_kind=AudioKind.NATIVE_VIDEO,
            asset_id="source-video",
            asset_sha256=source_hash,
            start_sample=10_000,
            duration_samples=10_000,
            source_start_sample=96_000,
            source_duration_samples=10_000,
            gain_millidb=0,
            fade_in_samples=0,
            fade_out_samples=0,
            native_audio_retime=second_map,
        ),
    )
    provisional = base.model_copy(
        update={
            "schema_version": "2.4",
            "visual_spans": video_spans,
            "audio_spans": audio_spans,
            "content_hash": "0" * 64,
            "composition_fingerprint": "0" * 64,
        }
    )
    timeline = seal_artifact(
        provisional.model_copy(
            update={"composition_fingerprint": timeline_fingerprint(provisional)}
        )
    )
    asset_sources = make_asset_sources(tmp_path, timeline)
    asset_sources["source-video"] = source_path
    missing_tool_staging = tmp_path / "missing-tool-staging"
    with pytest.raises(AiVideoError) as caught:
        materialize_hyperframes_source(
            timeline,
            asset_sources=asset_sources,
            allowed_asset_root=tmp_path,
            staging_root=missing_tool_staging,
            allowed_staging_parent=tmp_path,
        )
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert not missing_tool_staging.exists()

    materialized = materialize_hyperframes_source(
        timeline,
        asset_sources=asset_sources,
        allowed_asset_root=tmp_path,
        staging_root=tmp_path / "staging",
        allowed_staging_parent=tmp_path,
        native_audio_ffmpeg_path=ffmpeg,
        native_audio_ffprobe_path=ffprobe,
    )

    assert len(materialized.audio_bindings) == 1
    binding = materialized.audio_bindings[0]
    proofs = binding.native_audio_derivations
    assert tuple(item.track_id for item in proofs) == (
        "native-track-1",
        "native-track-2",
    )
    assert tuple(item.mapped_samples for item in proofs) == (10_000, 10_000)
    assert proofs[0].mapped_pcm_sha256 != proofs[1].mapped_pcm_sha256
    with wave.open(str(materialized.root / binding.materialized_path), "rb") as mixed:
        assert mixed.getframerate() == 48_000
        assert mixed.getnchannels() == 2
        assert mixed.getnframes() == timeline.total_samples

    source_receipt = SimpleNamespace(
        schema_version="2.1",
        audio_bindings=materialized.audio_bindings,
        caption_bindings=materialized.caption_bindings,
        asset_bindings=materialized.asset_bindings,
    )
    _validate_source_timeline_bindings(source_receipt, timeline)
    missing_proof = binding.model_copy(update={"native_audio_derivations": ()})
    with pytest.raises(ValueError, match="native audio derivation proofs"):
        _validate_source_timeline_bindings(
            SimpleNamespace(
                schema_version="2.1",
                audio_bindings=(missing_proof,),
                caption_bindings=materialized.caption_bindings,
                asset_bindings=materialized.asset_bindings,
            ),
            timeline,
        )
    extra_proof_binding = binding.model_copy(
        update={
            "native_audio_derivations": (
                *proofs,
                proofs[0].model_copy(update={"track_id": "extra-track"}),
            )
        }
    )
    with pytest.raises(ValueError, match="native audio derivation proofs"):
        _validate_source_timeline_bindings(
            SimpleNamespace(
                schema_version="2.1",
                audio_bindings=(extra_proof_binding,),
                caption_bindings=materialized.caption_bindings,
                asset_bindings=materialized.asset_bindings,
            ),
            timeline,
        )
    tampered_timeline = _reseal_timeline(
        timeline,
        audio_spans=(
            audio_spans[0].model_copy(
                update={
                    "native_audio_retime": first_map.model_copy(
                        update={"time_map_sha256": "b" * 64}
                    )
                }
            ),
            audio_spans[1],
        ),
    )
    with pytest.raises(ValueError, match="native audio proof"):
        _validate_source_timeline_bindings(source_receipt, tampered_timeline)


def test_legacy_renderer_audio_binding_keeps_its_serialized_shape():
    digest = "a" * 64
    binding = RendererAudioBinding(
        asset_id="p4-mix-legacy",
        asset_sha256=digest,
        asset_mime_type="audio/wav",
        materialized_path=Path(f"assets/{digest}.wav"),
        sample_rate_hz=48_000,
        channels=2,
        duration_samples=96_000,
        resolved_track_ids=("dialogue",),
    )

    assert binding.model_dump(mode="json") == {
        "asset_id": "p4-mix-legacy",
        "asset_sha256": digest,
        "asset_mime_type": "audio/wav",
        "materialized_path": f"assets/{digest}.wav",
        "sample_rate_hz": 48_000,
        "channels": 2,
        "duration_samples": 96_000,
        "resolved_track_ids": ["dialogue"],
    }


def test_native_audio_rejects_tampered_source_hash_before_decode(tmp_path):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    mapping = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=48_000,
            output_offset_sample=0,
            output_duration_samples=48_000,
        )
    )

    with pytest.raises(AiVideoError) as caught:
        derive_native_audio_pcm(
            snapshot,
            source_video_asset_id="source-video",
            source_video_sha256="f" * 64,
            track_id="native-track",
            mapping=mapping,
            sample_rate_hz=48_000,
            max_correction_samples=2_000,
            ffmpeg_path=ffmpeg,
            ffprobe_path=ffprobe,
        )

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID
    assert caught.value.retryable is False


def test_native_audio_rejects_source_without_unique_audio_stream(tmp_path):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path, with_audio=False)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    mapping = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=48_000,
            output_offset_sample=0,
            output_duration_samples=48_000,
        )
    )

    with pytest.raises(AiVideoError) as caught:
        derive_native_audio_pcm(
            snapshot,
            source_video_asset_id="source-video",
            source_video_sha256=snapshot.file_sha256,
            track_id="native-track",
            mapping=mapping,
            sample_rate_hz=48_000,
            max_correction_samples=2_000,
            ffmpeg_path=ffmpeg,
            ffprobe_path=ffprobe,
        )

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID


def test_native_audio_rejects_nonzero_video_timestamp_origin(tmp_path):
    ffmpeg, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path, nonzero_origin=True)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    mapping = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=48_000,
            output_offset_sample=0,
            output_duration_samples=48_000,
        )
    )

    with pytest.raises(AiVideoError) as caught:
        derive_native_audio_pcm(
            snapshot,
            source_video_asset_id="source-video",
            source_video_sha256=snapshot.file_sha256,
            track_id="native-track",
            mapping=mapping,
            sample_rate_hz=48_000,
            max_correction_samples=2_000,
            ffmpeg_path=ffmpeg,
            ffprobe_path=ffprobe,
        )

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID


def test_native_audio_rejects_missing_explicit_ffmpeg(tmp_path):
    _, ffprobe = _tool_paths()
    source_path = _make_mp4(tmp_path)
    snapshot = _read_regular_file_nofollow(source_path, contained_by=tmp_path)
    mapping = _mapping(
        AudioTimeSegment(
            source_start_sample=0,
            source_duration_samples=48_000,
            output_offset_sample=0,
            output_duration_samples=48_000,
        )
    )

    with pytest.raises(AiVideoError) as caught:
        derive_native_audio_pcm(
            snapshot,
            source_video_asset_id="source-video",
            source_video_sha256=snapshot.file_sha256,
            track_id="native-track",
            mapping=mapping,
            sample_rate_hz=48_000,
            max_correction_samples=2_000,
            ffmpeg_path=tmp_path / "missing-ffmpeg",
            ffprobe_path=ffprobe,
        )

    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE


@pytest.mark.parametrize("delta", [-2_001, 2_001])
def test_native_audio_rejects_tail_correction_over_one_frame(delta):
    with pytest.raises(AiVideoError) as caught:
        _fit_segment_sample_count(
            bytes(max(0, (48_000 + delta) * 4)),
            target_samples=48_000,
            maximum_correction_samples=2_000,
        )

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID


@pytest.mark.parametrize(
    ("source_samples", "output_samples"),
    [
        (90_037, 900_375),
        (450_187, 90_037),
    ],
    ids=["lower-frame-ratio-after-floor", "upper-frame-ratio-after-floor"],
)
def test_native_audio_atempo_accepts_sample_floor_envelope(
    source_samples, output_samples
):
    factors = native_audio._atempo_factors(source_samples, output_samples)

    assert factors
    assert all(0.5 <= float(value) <= 2 for value in factors)


@pytest.mark.parametrize(
    ("source_samples", "output_samples"),
    [
        (90_036, 900_375),
        (450_191, 90_037),
    ],
    ids=["below-floor-envelope", "above-floor-envelope"],
)
def test_native_audio_atempo_rejects_true_sample_ratio_outside_frame_envelope(
    source_samples, output_samples
):
    with pytest.raises(AiVideoError) as caught:
        native_audio._atempo_factors(source_samples, output_samples)

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID


@pytest.mark.parametrize(
    ("source_samples", "output_samples"),
    [(0, 1), (1, 0), (-1, -1), (True, 1), (1, 1.0)],
)
def test_native_audio_atempo_requires_positive_integer_sample_counts(
    source_samples, output_samples
):
    with pytest.raises(AiVideoError) as caught:
        native_audio._atempo_factors(source_samples, output_samples)

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID
