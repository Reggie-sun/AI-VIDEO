from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AUDIO_KIND_TO_ASSET_TYPE,
    AssetRecord,
    AssetSourceKind,
    AudioAssetMetadata,
    AudioChannelLayout,
    AudioKind,
    AudioLoudnessMetadata,
    AudioSource,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
    ToolIdentity,
)
from ai_video.production.paths import (
    NoFollowFile,
    _materialize_immutable_regular_file_nofollow,
    canonical_audio_asset_path,
    canonical_voice_audio_candidate_path,
)


_ALLOWED_MIME_TYPES = {"audio/wav", "audio/x-wav"}
_Runner = Callable[..., subprocess.CompletedProcess]


def _audio_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.AUDIO_ASSET_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _probe_failed(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.AUDIO_PROBE_FAILED,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class VoiceProviderParameters(StrictModel):
    stability_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)
    similarity_boost_milli: int | None = Field(
        default=None, strict=True, ge=0, le=1000
    )
    style_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)
    use_speaker_boost: bool | None = Field(default=None, strict=True)
    speed_milli: int | None = Field(default=None, strict=True, ge=700, le=1200)


class VoiceGenerationRequest(StrictModel):
    request_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    audio_kind: AudioKind
    script_text: str = Field(min_length=1)
    script_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    speaker_id: str = Field(min_length=1)
    voice_id: str = Field(min_length=1)
    language: str = Field(min_length=1)
    output_container: Literal["wav"]
    output_codec: Literal["pcm_s16le"]
    output_sample_rate_hz: int = Field(strict=True, gt=0)
    output_channels: Literal[1, 2]
    provider_parameters: VoiceProviderParameters
    provider_parameters_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    input_artifact_ids: tuple[str, ...] = Field(min_length=1)
    input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    pricing_snapshot_id: str = Field(min_length=1)
    budget_reservation_receipt_id: str = Field(min_length=1)
    egress_authorization_receipt_id: str = Field(min_length=1)
    voice_request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @staticmethod
    def _fingerprint_payload(data: dict[str, object]) -> dict[str, object]:
        return {
            key: data[key]
            for key in (
                "provider_kind",
                "model_id",
                "audio_kind",
                "script_hash",
                "speaker_id",
                "voice_id",
                "language",
                "output_container",
                "output_codec",
                "output_sample_rate_hz",
                "output_channels",
                "provider_parameters_hash",
                "base_project",
                "base_registry",
                "input_artifact_ids",
                "input_fingerprint",
                "pricing_snapshot_id",
                "budget_reservation_receipt_id",
                "egress_authorization_receipt_id",
            )
        }

    @model_validator(mode="after")
    def _validate_sealed_request(self) -> "VoiceGenerationRequest":
        if self.audio_kind not in {AudioKind.DIALOGUE, AudioKind.NARRATION}:
            raise ValueError("voice request audio_kind must be dialogue or narration")
        if unicodedata.normalize("NFC", self.script_text) != self.script_text:
            raise ValueError("script_text must use Unicode NFC normalization")
        expected_script = hashlib.sha256(self.script_text.encode("utf-8")).hexdigest()
        if self.script_hash != expected_script:
            raise ValueError("script_hash does not match exact UTF-8 script_text")
        expected_parameters = canonical_sha256(
            self.provider_parameters.model_dump(mode="json")
        )
        if self.provider_parameters_hash != expected_parameters:
            raise ValueError("provider_parameters_hash does not match parameters")
        data = self.model_dump(mode="json")
        expected_request = canonical_sha256(self._fingerprint_payload(data))
        if self.voice_request_fingerprint != expected_request:
            raise ValueError("voice_request_fingerprint does not match request")
        return self

    @classmethod
    def create(cls, **values: object) -> "VoiceGenerationRequest":
        script_text = values.get("script_text")
        parameters = values.get("provider_parameters")
        if not isinstance(script_text, str):
            raise _audio_invalid("Voice request script_text must be text.")
        if not isinstance(parameters, VoiceProviderParameters):
            raise _audio_invalid("Voice request provider_parameters are invalid.")
        data = dict(values)
        data["script_hash"] = hashlib.sha256(script_text.encode("utf-8")).hexdigest()
        data["provider_parameters_hash"] = canonical_sha256(
            parameters.model_dump(mode="json")
        )
        serializable = {
            key: (
                value.model_dump(mode="json")
                if isinstance(value, StrictModel)
                else [str(item) for item in value]
                if key == "input_artifact_ids" and isinstance(value, tuple)
                else value.value
                if isinstance(value, AudioKind)
                else value
            )
            for key, value in data.items()
        }
        data["voice_request_fingerprint"] = canonical_sha256(
            cls._fingerprint_payload(serializable)
        )
        return cls.model_validate(data)


class AudioProbeToolchain(StrictModel):
    ffmpeg_path: Path
    ffprobe_path: Path
    ffmpeg: ToolIdentity
    ffprobe: ToolIdentity

    @field_validator("ffmpeg_path", "ffprobe_path")
    @classmethod
    def _require_canonical_executable(cls, value: Path) -> Path:
        try:
            resolved = value.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError("audio tool path must resolve to an existing file") from exc
        if not value.is_absolute() or value != resolved or not value.is_file():
            raise ValueError("audio tool path must be canonical and absolute")
        if not os.access(value, os.X_OK):
            raise ValueError("audio tool path must be executable")
        return value


class ClaimedAudioMetadata(StrictModel):
    codec_name: str = Field(min_length=1)
    duration_samples: int = Field(strict=True, gt=0)
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: Literal[1, 2]


class AudioProbeResult(StrictModel):
    mime_type: Literal["audio/wav", "audio/x-wav"]
    container_name: Literal["wav"]
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    file_device: int = Field(strict=True, ge=0)
    file_inode: int = Field(strict=True, ge=0)
    codec_name: Literal["pcm_s16le"]
    duration_samples: int = Field(strict=True, gt=0)
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: Literal[1, 2]
    channel_layout: AudioChannelLayout
    decoded_pcm_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    loudness: AudioLoudnessMetadata
    loudness_receipt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    ffmpeg: ToolIdentity
    ffprobe: ToolIdentity
    content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class AudioImportRequest(StrictModel):
    asset_id: str = Field(min_length=1)
    audio_kind: AudioKind
    mime_type: Literal["audio/wav", "audio/x-wav"]
    source: AudioSource
    speaker_id: str | None = None
    voice_id: str | None = None
    language: str | None = None
    script_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    provenance_receipt_id: str = Field(min_length=1)
    alignment_receipt_id: str | None = None
    creation_receipt_id: str = Field(min_length=1)
    usage_license: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_import_identity(self) -> "AudioImportRequest":
        if self.source.kind is AssetSourceKind.GENERATED:
            raise ValueError("AudioImportRequest cannot represent generated provider audio")
        speech = self.audio_kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
        if speech and (not self.language or self.script_hash is None):
            raise ValueError("speech import requires language and script_hash")
        if not speech and any(
            item is not None
            for item in (
                self.speaker_id,
                self.voice_id,
                self.language,
                self.script_hash,
                self.alignment_receipt_id,
            )
        ):
            raise ValueError("non-speech import cannot contain voice identity")
        return self

    def prepare(
        self,
        held_source_fd: int,
        *,
        toolchain: AudioProbeToolchain,
        measure_loudness: bool = True,
        runner: _Runner = subprocess.run,
    ) -> "PreparedAudioImport":
        probe = probe_audio_candidate(
            held_source_fd,
            mime_type=self.mime_type,
            toolchain=toolchain,
            measure_loudness=measure_loudness,
            runner=runner,
        )
        payload, final_stat = _read_held_fd(held_source_fd)
        if (
            hashlib.sha256(payload).hexdigest() != probe.file_sha256
            or (final_stat.st_dev, final_stat.st_ino, final_stat.st_size)
            != (probe.file_device, probe.file_inode, probe.size_bytes)
        ):
            raise _audio_invalid("Audio import source changed after probe.")
        record = build_audio_asset_record(self, probe)
        return PreparedAudioImport(payload=payload, probe=probe, asset_record=record)


@dataclass(frozen=True)
class PreparedAudioImport:
    payload: bytes
    probe: AudioProbeResult
    asset_record: AssetRecord


def _read_held_fd(held_fd: int) -> tuple[bytes, os.stat_result]:
    try:
        before = os.fstat(held_fd)
        if not stat.S_ISREG(before.st_mode):
            raise _audio_invalid("Audio source FD must reference a regular file.")
        offset = os.lseek(held_fd, 0, os.SEEK_CUR)
        os.lseek(held_fd, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while chunk := os.read(held_fd, 1024 * 1024):
            chunks.append(chunk)
        os.lseek(held_fd, offset, os.SEEK_SET)
        after = os.fstat(held_fd)
    except AiVideoError:
        raise
    except OSError as exc:
        raise _audio_invalid("Audio source FD could not be read.", str(exc)) from exc
    if (before.st_dev, before.st_ino, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ):
        raise _audio_invalid("Audio source FD changed during read.")
    payload = b"".join(chunks)
    if len(payload) != after.st_size:
        raise _audio_invalid("Audio source FD size changed during read.")
    return payload, after


def _run_fd_tool(
    runner: _Runner,
    argv: list[str],
    held_fd: int,
    *,
    text: bool,
) -> subprocess.CompletedProcess:
    duplicate = os.dup(held_fd)
    try:
        os.lseek(duplicate, 0, os.SEEK_SET)
        actual_argv = [item.replace("{fd}", str(duplicate)) for item in argv]
        return runner(
            actual_argv,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(duplicate,),
            check=False,
            text=text,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _probe_failed("Audio probe tool could not run.", type(exc).__name__) from exc
    finally:
        os.close(duplicate)


def _require_unchanged_fd(held_fd: int, expected: os.stat_result) -> None:
    current = os.fstat(held_fd)
    if (current.st_dev, current.st_ino, current.st_size) != (
        expected.st_dev,
        expected.st_ino,
        expected.st_size,
    ):
        raise _audio_invalid("Audio source FD changed during probe.")


def _measure_loudness(
    held_fd: int,
    *,
    toolchain: AudioProbeToolchain,
    runner: _Runner,
) -> AudioLoudnessMetadata:
    result = _run_fd_tool(
        runner,
        [
            str(toolchain.ffmpeg_path),
            "-nostdin",
            "-hide_banner",
            "-v",
            "info",
            "-i",
            "/proc/self/fd/{fd}",
            "-filter_complex",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        held_fd,
        text=True,
    )
    if result.returncode != 0:
        raise _probe_failed("Audio loudness measurement failed.")
    integrated = re.findall(r"\bI:\s*(-?\d+(?:\.\d+)?)\s+LUFS", result.stderr)
    peaks = re.findall(r"\bPeak:\s*(-?\d+(?:\.\d+)?)\s+dBFS", result.stderr)
    if not integrated or not peaks:
        raise _probe_failed("Audio loudness evidence was incomplete.")

    def milli(value: str) -> int:
        return int((Decimal(value) * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    return AudioLoudnessMetadata(
        integrated_lufs_milli=milli(integrated[-1]),
        true_peak_dbfs_milli=milli(peaks[-1]),
        measurement_standard="ebu_r128",
    )


def probe_audio_candidate(
    held_fd: int,
    *,
    mime_type: str,
    toolchain: AudioProbeToolchain,
    claimed_metadata: ClaimedAudioMetadata | None = None,
    measure_loudness: bool = True,
    runner: _Runner = subprocess.run,
) -> AudioProbeResult:
    if mime_type not in _ALLOWED_MIME_TYPES:
        raise _audio_invalid("Audio MIME type is not an accepted WAV type.")
    payload, held_stat = _read_held_fd(held_fd)
    if not payload:
        raise _audio_invalid("Audio source is empty.")
    file_sha256 = hashlib.sha256(payload).hexdigest()

    probed = _run_fd_tool(
        runner,
        [
            str(toolchain.ffprobe_path),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            "/proc/self/fd/{fd}",
        ],
        held_fd,
        text=True,
    )
    _require_unchanged_fd(held_fd, held_stat)
    if probed.returncode != 0:
        raise _probe_failed("ffprobe rejected the audio candidate.")
    try:
        evidence = json.loads(probed.stdout)
        streams = evidence["streams"]
        format_name = evidence["format"]["format_name"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _probe_failed("ffprobe returned invalid audio evidence.") from exc
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    if len(audio_streams) != 1 or len(streams) != 1:
        raise _probe_failed("Audio candidate must contain exactly one audio stream.")
    if "wav" not in str(format_name).split(","):
        raise _audio_invalid("Audio candidate container is not WAV.")
    stream = audio_streams[0]
    try:
        codec_name = str(stream["codec_name"])
        sample_rate_hz = int(stream["sample_rate"])
        channels = int(stream["channels"])
    except (KeyError, TypeError, ValueError) as exc:
        raise _probe_failed("ffprobe audio stream metadata is incomplete.") from exc
    if codec_name != "pcm_s16le" or channels not in {1, 2} or sample_rate_hz <= 0:
        raise _audio_invalid("Audio candidate format is unsupported.")

    decoded = _run_fd_tool(
        runner,
        [
            str(toolchain.ffmpeg_path),
            "-nostdin",
            "-v",
            "error",
            "-i",
            "/proc/self/fd/{fd}",
            "-map",
            "0:a:0",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(sample_rate_hz),
            "-ac",
            str(channels),
            "-f",
            "s16le",
            "-",
        ],
        held_fd,
        text=False,
    )
    _require_unchanged_fd(held_fd, held_stat)
    if decoded.returncode != 0:
        raise _probe_failed("Audio PCM decode failed.")
    bytes_per_frame = channels * 2
    if not decoded.stdout or len(decoded.stdout) % bytes_per_frame:
        raise _probe_failed("Decoded PCM length is invalid.")
    duration_samples = len(decoded.stdout) // bytes_per_frame
    layout = AudioChannelLayout.MONO if channels == 1 else AudioChannelLayout.STEREO

    if measure_loudness:
        loudness = _measure_loudness(held_fd, toolchain=toolchain, runner=runner)
        _require_unchanged_fd(held_fd, held_stat)
    else:
        loudness = AudioLoudnessMetadata(
            integrated_lufs_milli=None,
            true_peak_dbfs_milli=None,
            measurement_standard=None,
        )
    final_payload, final_stat = _read_held_fd(held_fd)
    if (
        hashlib.sha256(final_payload).hexdigest() != file_sha256
        or (final_stat.st_dev, final_stat.st_ino, final_stat.st_size)
        != (held_stat.st_dev, held_stat.st_ino, held_stat.st_size)
    ):
        raise _audio_invalid("Audio source bytes changed during probe.")
    loudness_receipt_id = canonical_sha256(
        {
            "loudness": loudness.model_dump(mode="json"),
            "ffmpeg": toolchain.ffmpeg.model_dump(mode="json"),
            "source_file_sha256": file_sha256,
        }
    )
    durable_evidence = {
        "mime_type": mime_type,
        "container_name": "wav",
        "file_sha256": file_sha256,
        "size_bytes": held_stat.st_size,
        "codec_name": codec_name,
        "duration_samples": duration_samples,
        "sample_rate_hz": sample_rate_hz,
        "channels": channels,
        "channel_layout": layout.value,
        "decoded_pcm_sha256": hashlib.sha256(decoded.stdout).hexdigest(),
        "loudness": loudness.model_dump(mode="json"),
        "loudness_receipt_id": loudness_receipt_id,
        "ffmpeg": toolchain.ffmpeg.model_dump(mode="json"),
        "ffprobe": toolchain.ffprobe.model_dump(mode="json"),
    }
    content_fingerprint = canonical_sha256(durable_evidence)
    result = AudioProbeResult.model_validate(
        {
            **durable_evidence,
            "file_device": held_stat.st_dev,
            "file_inode": held_stat.st_ino,
            "content_fingerprint": content_fingerprint,
        }
    )
    if claimed_metadata is not None:
        measured_claim = (
            result.codec_name,
            result.duration_samples,
            result.sample_rate_hz,
            result.channels,
        )
        provider_claim = (
            claimed_metadata.codec_name,
            claimed_metadata.duration_samples,
            claimed_metadata.sample_rate_hz,
            claimed_metadata.channels,
        )
        if measured_claim != provider_claim:
            raise _audio_invalid("Audio provider metadata does not match measured truth.")
    return result


def audio_content_fingerprint(probe: AudioProbeResult) -> str:
    data = probe.model_dump(
        mode="json",
        exclude={"content_fingerprint", "file_device", "file_inode"},
    )
    return canonical_sha256(data)


def materialize_audio_candidate(
    payload: bytes,
    *,
    candidate_path: Path,
    project_root: Path,
    attempt_id: str,
) -> NoFollowFile:
    if not isinstance(payload, bytes) or not payload:
        raise _audio_invalid("Audio candidate payload must be non-empty bytes.")
    try:
        expected = canonical_voice_audio_candidate_path(project_root, attempt_id)
        if candidate_path != expected:
            raise ValueError("Audio candidate is not the exact attempt-owned path.")
        return _materialize_immutable_regular_file_nofollow(
            candidate_path,
            data=payload,
            contained_by=project_root,
        )
    except (OSError, ValueError) as exc:
        raise _audio_invalid("Could not materialize exact attempt-owned audio candidate.", str(exc)) from exc


def build_audio_asset_record(
    request: AudioImportRequest,
    probe: AudioProbeResult,
) -> AssetRecord:
    metadata = AudioAssetMetadata(
        audio_kind=request.audio_kind,
        source=request.source,
        speaker_id=request.speaker_id,
        voice_id=request.voice_id,
        language=request.language,
        script_hash=request.script_hash,
        duration_samples=probe.duration_samples,
        sample_rate_hz=probe.sample_rate_hz,
        channels=probe.channels,
        channel_layout=probe.channel_layout,
        codec_name=probe.codec_name,
        loudness=probe.loudness,
        provenance_receipt_id=request.provenance_receipt_id,
        alignment_receipt_id=request.alignment_receipt_id,
    )
    return AssetRecord(
        asset_id=request.asset_id,
        asset_type=AUDIO_KIND_TO_ASSET_TYPE[request.audio_kind],
        artifact_path=canonical_audio_asset_path(probe.file_sha256),
        sha256=probe.file_sha256,
        size_bytes=probe.size_bytes,
        mime_type=request.mime_type,
        source_kind=request.source.kind,
        tool=request.source.provider_or_tool,
        input_artifact_ids=request.source.input_artifact_ids,
        input_fingerprint=request.source.input_fingerprint,
        creation_receipt_id=request.creation_receipt_id,
        usage_license=request.usage_license,
        audio_metadata=metadata,
    )
