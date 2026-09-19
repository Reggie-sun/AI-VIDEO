from __future__ import annotations

import hashlib
import shutil
import wave
from io import BytesIO
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioProbeToolchain,
    VoiceGenerationRequest,
)
from ai_video.production.models import AssetSourceKind, ToolIdentity
from ai_video.production.paths import canonical_audio_asset_path
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.voice_candidate import make_voice_candidate_preparer

import production_project_factory as project_factory


def _toolchain() -> AudioProbeToolchain:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for real WAV probing")
    return AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(strict=True),
        ffprobe_path=Path(ffprobe).resolve(strict=True),
        ffmpeg=ToolIdentity(name="ffmpeg", version="test-pinned"),
        ffprobe=ToolIdentity(name="ffprobe", version="test-pinned"),
    )


def _wav_bytes(*, sample_rate_hz: int, samples: int = 37) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate_hz)
        writer.writeframes(b"\0\0" * samples)
    return output.getvalue()


def _request(root: Path, *, sample_rate_hz: int = 44_100) -> VoiceGenerationRequest:
    base = project_factory.make_voice_request(root)
    return VoiceGenerationRequest.create(
        request_id=base.request_id,
        attempt_id=base.attempt_id,
        provider_kind=base.provider_kind,
        model_id=base.model_id,
        audio_kind=base.audio_kind,
        script_text=base.script_text,
        speaker_id=base.speaker_id,
        voice_id=base.voice_id,
        language=base.language,
        output_container=base.output_container,
        output_codec=base.output_codec,
        output_sample_rate_hz=sample_rate_hz,
        output_channels=base.output_channels,
        provider_parameters=base.provider_parameters,
        base_project=base.base_project,
        base_registry=base.base_registry,
        input_artifact_ids=base.input_artifact_ids,
        input_fingerprint=base.input_fingerprint,
        pricing_snapshot_id=base.pricing_snapshot_id,
        budget_reservation_receipt_id=base.budget_reservation_receipt_id,
        egress_authorization_receipt_id=base.egress_authorization_receipt_id,
    )


def _inputs(root: Path, *, wav: bytes, sample_rate_hz: int = 44_100):
    project_factory.write_production_project(root)
    request = _request(root, sample_rate_hz=sample_rate_hz)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    result = project_factory.make_voice_provider_result(
        request, preview, authorization, audio_bytes=wav
    )
    paths = ProductionStateCommitter(root).voice_attempt_paths(request.attempt_id)
    paths.attempt_root.mkdir(parents=True)
    return request, preview, authorization, result, paths


def test_prepares_exact_generated_wav_from_real_probe(tmp_path: Path) -> None:
    wav = _wav_bytes(sample_rate_hz=44_100)
    request, preview, authorization, result, paths = _inputs(tmp_path, wav=wav)

    prepared = make_voice_candidate_preparer(tmp_path, _toolchain())(
        request, preview, authorization, result, paths
    )

    assert paths.audio_candidate_path.read_bytes() == wav
    assert prepared.caption is None
    assert prepared.audio.payload == wav
    assert prepared.audio.probe.file_sha256 == hashlib.sha256(wav).hexdigest()
    assert prepared.audio.probe.duration_samples == 37
    assert prepared.audio.probe.sample_rate_hz == 44_100
    assert prepared.audio.probe.channels == 1
    record = prepared.audio.asset_record
    assert record.source_kind is AssetSourceKind.GENERATED
    assert record.sha256 == result.audio_sha256
    assert record.artifact_path == canonical_audio_asset_path(result.audio_sha256)
    assert record.audio_metadata is not None
    assert record.audio_metadata.source.kind is AssetSourceKind.GENERATED
    assert record.audio_metadata.duration_samples == 37
    assert record.audio_metadata.provenance_receipt_id.startswith("provenance-")


def test_rejects_wav_that_does_not_match_requested_output(tmp_path: Path) -> None:
    wav = _wav_bytes(sample_rate_hz=48_000)
    request, preview, authorization, result, paths = _inputs(tmp_path, wav=wav)

    with pytest.raises(AiVideoError) as caught:
        make_voice_candidate_preparer(tmp_path, _toolchain())(
            request, preview, authorization, result, paths
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID


def test_rejects_provider_result_with_mismatched_audio_sha(tmp_path: Path) -> None:
    wav = _wav_bytes(sample_rate_hz=44_100)
    request, preview, authorization, result, paths = _inputs(tmp_path, wav=wav)
    contradictory_result = result.model_copy(update={"audio_sha256": "0" * 64})

    with pytest.raises(AiVideoError) as caught:
        make_voice_candidate_preparer(tmp_path, _toolchain())(
            request, preview, authorization, contradictory_result, paths
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
