from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from collections.abc import Mapping
from contextlib import ExitStack
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryFile

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio_retime_contracts import (
    AudioSegmentProcessingProof,
    NativeAudioDerivationProof,
    NativeAudioRetime,
    native_audio_mapping_sha256 as native_audio_mapping_sha256,
)
from ai_video.production.composition import _validated_visual_suffix
from ai_video.production.models import ResolvedTimeline
from ai_video.production.paths import (
    NoFollowFile,
    _open_regular_file_nofollow,
    _read_regular_file_nofollow,
)


_PCM16_STEREO_FRAME_BYTES = 4
_TOOL_TIMEOUT_SECONDS = 180


def _source_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.RENDERER_SOURCE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _tool_unavailable(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.RENDERER_UNAVAILABLE,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _hash_fd(descriptor: int) -> str:
    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while chunk := os.read(descriptor, 1024 * 1024):
        digest.update(chunk)
    os.lseek(descriptor, 0, os.SEEK_SET)
    return digest.hexdigest()


def _validate_tool(path: Path, label: str, descriptor: int) -> str:
    try:
        path = Path(path)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_mode & 0o111 == 0
            or path.resolve(strict=True) != path
        ):
            raise ValueError("not a canonical regular executable")
        digest = _hash_fd(descriptor)
        result = subprocess.run(
            (f"/proc/self/fd/{descriptor}", "-version"),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(descriptor,),
            check=False,
            text=True,
            timeout=15,
            env={"LANG": "C", "LC_ALL": "C", "PATH": os.defpath},
        )
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        raise _tool_unavailable(
            f"Explicit native audio {label} tool is unavailable.",
            type(exc).__name__,
        ) from exc
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    if result.returncode != 0 or not first_line.startswith(f"{label} version "):
        raise _tool_unavailable(f"Explicit native audio {label} identity is invalid.")
    return digest


def _open_tool(stack: ExitStack, path: Path | None, label: str) -> tuple[int, str]:
    if path is None:
        raise _tool_unavailable(
            "Native video audio requires explicit ffmpeg and ffprobe paths."
        )
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise _tool_unavailable(
            f"Explicit native audio {label} path must be absolute and canonical."
        )
    try:
        descriptor, opened = stack.enter_context(
            _open_regular_file_nofollow(path, contained_by=path.parent)
        )
        if not stat.S_ISREG(opened.st_mode) or opened.st_mode & 0o111 == 0:
            raise ValueError("not an executable regular file")
    except (OSError, ValueError) as exc:
        raise _tool_unavailable(
            f"Explicit native audio {label} path is unavailable.",
            type(exc).__name__,
        ) from exc
    return descriptor, _validate_tool(path, label, descriptor)


def _held_source_snapshot(source: NoFollowFile, stack: ExitStack) -> int:
    try:
        if (
            not stat.S_ISREG(source.mode)
            or source.size_bytes != len(source.data)
            or hashlib.sha256(source.data).hexdigest() != source.file_sha256
        ):
            raise ValueError("source snapshot identity mismatch")
        held_file = stack.enter_context(TemporaryFile(prefix="ai-video-native-audio-"))
        descriptor = held_file.fileno()
        view = memoryview(source.data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("could not write held source snapshot")
            view = view[written:]
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor
    except (OSError, ValueError) as exc:
        raise _source_invalid(
            "Native audio source snapshot is invalid.", type(exc).__name__
        ) from exc


def _run(
    descriptor: int,
    arguments: tuple[str, ...],
    *,
    pass_fds: tuple[int, ...],
    input_bytes: bytes | None = None,
    text: bool = False,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            (f"/proc/self/fd/{descriptor}", *arguments),
            stdin=subprocess.DEVNULL if input_bytes is None else None,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(descriptor, *pass_fds),
            check=False,
            text=text,
            timeout=_TOOL_TIMEOUT_SECONDS,
            env={"LANG": "C", "LC_ALL": "C", "PATH": os.defpath},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _source_invalid(
            "Native video audio processing failed.", type(exc).__name__
        ) from exc


def _probe_source(
    ffprobe_descriptor: int,
    source_descriptor: int,
    *,
    sample_rate_hz: int,
) -> int:
    result = _run(
        ffprobe_descriptor,
        (
            "-v",
            "error",
            "-protocol_whitelist",
            "file",
            "-f",
            "mov",
            "-enable_drefs",
            "0",
            "-use_absolute_path",
            "0",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            f"/proc/self/fd/{source_descriptor}",
        ),
        pass_fds=(source_descriptor,),
        text=True,
    )
    if result.returncode != 0:
        raise _source_invalid("Native video source could not be probed.")
    try:
        payload = json.loads(result.stdout)
        streams = payload["streams"]
        if not isinstance(streams, list):
            raise ValueError("stream list")
        audio_streams = tuple(
            item
            for item in streams
            if isinstance(item, dict) and item.get("codec_type") == "audio"
        )
        video_streams = tuple(
            item
            for item in streams
            if isinstance(item, dict) and item.get("codec_type") == "video"
        )
        if len(audio_streams) != 1 or not video_streams:
            raise ValueError("source must contain video and exactly one audio stream")
        video_start = _decimal_timestamp(video_streams[0].get("start_time"))
        if video_start != 0:
            raise ValueError("video presentation origin must be zero")
        audio_start_sample = _stream_start_sample(
            audio_streams[0],
            sample_rate_hz=sample_rate_hz,
        )
        if audio_start_sample < 0:
            raise ValueError("audio presentation origin precedes video origin")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _source_invalid(
            "Native video source stream identity is invalid.", str(exc)
        ) from exc
    return audio_start_sample


def native_audio_video_snapshots(
    timeline: ResolvedTimeline,
    *,
    asset_sources: Mapping[str, Path],
    allowed_asset_root: Path,
) -> dict[str, NoFollowFile]:
    """Read and validate the exact visual sources used by native audio spans."""

    native_spans = tuple(
        item for item in timeline.audio_spans if item.native_audio_retime is not None
    )
    snapshots: dict[str, NoFollowFile] = {}
    for span in native_spans:
        mapping = span.native_audio_retime
        assert mapping is not None
        visual_matches = tuple(
            item
            for item in timeline.visual_spans
            if item.layer_id == mapping.visual_layer_id
        )
        if (
            len(visual_matches) != 1
            or visual_matches[0].asset_id != span.asset_id
            or visual_matches[0].asset_sha256 != span.asset_sha256
            or visual_matches[0].asset_mime_type != "video/mp4"
            or span.audio_kind.value != "native_video"
            or sum(item.output_duration_samples for item in mapping.segments)
            != span.duration_samples
        ):
            raise _source_invalid(
                "Native audio retime does not match its exact visual source and duration."
            )
        if span.asset_id in snapshots:
            continue
        try:
            source_path = Path(asset_sources[span.asset_id])
            snapshot = _read_regular_file_nofollow(
                source_path, contained_by=allowed_asset_root
            )
            suffix = _validated_visual_suffix(
                snapshot,
                suffix=source_path.suffix,
                mime_type="video/mp4",
            )
        except (AiVideoError, KeyError, OSError, ValueError) as exc:
            raise _source_invalid(
                "Native audio video snapshot identity is invalid.", str(exc)
            ) from exc
        if (
            suffix != ".mp4"
            or snapshot.file_sha256 != span.asset_sha256
            or Path("assets") / f"{span.asset_sha256}{suffix}"
            != visual_matches[0].materialized_path
        ):
            raise _source_invalid("Native audio video snapshot identity is invalid.")
        snapshots[span.asset_id] = snapshot
    return snapshots


def validate_native_audio_video_streams(
    snapshots: Mapping[str, NoFollowFile],
    *,
    sample_rate_hz: int,
    ffprobe_path: Path | None,
) -> None:
    """Validate unique audio-stream identity without decoding or rendering media."""

    if not snapshots:
        return
    with ExitStack() as stack:
        ffprobe_descriptor, _ = _open_tool(stack, ffprobe_path, "ffprobe")
        for snapshot in snapshots.values():
            source_descriptor = _held_source_snapshot(snapshot, stack)
            _probe_source(
                ffprobe_descriptor,
                source_descriptor,
                sample_rate_hz=sample_rate_hz,
            )


def _decimal_timestamp(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("video stream timestamp is missing")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("video stream timestamp is invalid") from exc
    if not result.is_finite():
        raise ValueError("video stream timestamp is invalid")
    return result


def _stream_start_sample(stream: dict[str, object], *, sample_rate_hz: int) -> int:
    start_pts = stream.get("start_pts")
    time_base = stream.get("time_base")
    if type(start_pts) is int and isinstance(time_base, str):
        try:
            exact = Fraction(start_pts) * Fraction(time_base) * sample_rate_hz
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError("audio stream time base is invalid") from exc
        return int(
            (Decimal(exact.numerator) / Decimal(exact.denominator)).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )
    timestamp = _decimal_timestamp(stream.get("start_time"))
    return int((timestamp * sample_rate_hz).to_integral_value(rounding=ROUND_HALF_UP))


def _decode_source_pcm(
    ffmpeg_descriptor: int,
    source_descriptor: int,
    *,
    sample_rate_hz: int,
    source_end_sample: int,
    audio_start_sample: int,
) -> bytes:
    if audio_start_sample < 0:
        raise _source_invalid(
            "Native video audio begins before the supported video origin."
        )
    audio_samples_to_end = source_end_sample - audio_start_sample
    if audio_samples_to_end <= 0:
        raise _source_invalid(
            "Native video audio does not overlap the required source window."
        )
    result = _run(
        ffmpeg_descriptor,
        (
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-copyts",
            "-protocol_whitelist",
            "file",
            "-f",
            "mov",
            "-enable_drefs",
            "0",
            "-use_absolute_path",
            "0",
            "-i",
            f"/proc/self/fd/{source_descriptor}",
            "-map",
            "0:a:0",
            "-vn",
            "-sn",
            "-dn",
            "-af",
            f"aresample={sample_rate_hz}:async=1,atrim=end_sample={audio_samples_to_end},asetpts=PTS-STARTPTS",
            "-c:a",
            "pcm_s16le",
            "-ar",
            str(sample_rate_hz),
            "-ac",
            "2",
            "-f",
            "s16le",
            "pipe:1",
        ),
        pass_fds=(source_descriptor,),
    )
    if result.returncode != 0:
        raise _source_invalid("Native video audio decode failed.")
    pcm = result.stdout
    expected_bytes = audio_samples_to_end * _PCM16_STEREO_FRAME_BYTES
    if len(pcm) != expected_bytes:
        raise _source_invalid(
            "Native video audio decode did not cover the exact source window."
        )
    if audio_start_sample > 0:
        aligned = bytes(audio_start_sample * _PCM16_STEREO_FRAME_BYTES) + pcm
    else:
        aligned = pcm
    if len(aligned) != source_end_sample * _PCM16_STEREO_FRAME_BYTES:
        raise _source_invalid(
            "Native video audio timestamp alignment did not cover the exact source window."
        )
    return aligned


def _atempo_factors(source_samples: int, output_samples: int) -> tuple[str, ...]:
    if (
        type(source_samples) is not int
        or source_samples <= 0
        or type(output_samples) is not int
        or output_samples <= 0
    ):
        raise _source_invalid(
            "Native audio segment sample counts must be positive integers."
        )
    # The frame time map owns the exact 0.1..5 ratio. Each window subtracts two
    # floored endpoints, so its sample length differs from the exact length by
    # less than one sample in either direction. These integer bounds admit that
    # finite rounding envelope and reject ratios outside it.
    if (
        10 * source_samples + 10 < output_samples
        or source_samples > 5 * output_samples + 5
    ):
        raise _source_invalid(
            "Native audio segment tempo is outside the supported range."
        )
    factor = Decimal(source_samples) / Decimal(output_samples)
    remaining = factor
    values: list[Decimal] = []
    while remaining > Decimal("2"):
        values.append(Decimal("2"))
        remaining /= Decimal("2")
    while remaining < Decimal("0.5"):
        values.append(Decimal("0.5"))
        remaining /= Decimal("0.5")
    if remaining != 1 or not values:
        values.append(remaining)
    if any(value < Decimal("0.5") or value > Decimal("2") for value in values):
        raise _source_invalid(
            "Native audio tempo factor could not be represented safely."
        )
    return tuple(format(value.normalize(), "f") for value in values)


def _process_segment(
    ffmpeg_descriptor: int,
    source_pcm: bytes,
    *,
    source_samples: int,
    output_samples: int,
    sample_rate_hz: int,
) -> bytes:
    if source_samples == output_samples:
        return source_pcm
    factors = _atempo_factors(source_samples, output_samples)
    result = _run(
        ffmpeg_descriptor,
        (
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "s16le",
            "-ar",
            str(sample_rate_hz),
            "-ac",
            "2",
            "-i",
            "pipe:0",
            "-map",
            "0:a:0",
            "-af",
            ",".join(f"atempo={value}" for value in factors),
            "-c:a",
            "pcm_s16le",
            "-ar",
            str(sample_rate_hz),
            "-ac",
            "2",
            "-f",
            "s16le",
            "pipe:1",
        ),
        pass_fds=(),
        input_bytes=source_pcm,
    )
    if result.returncode != 0 or not result.stdout:
        raise _source_invalid("Native audio pitch-preserving retime failed.")
    return result.stdout


def _fit_segment_sample_count(
    pcm: bytes,
    *,
    target_samples: int,
    maximum_correction_samples: int,
) -> tuple[bytes, int, int, int]:
    if (
        target_samples <= 0
        or maximum_correction_samples < 0
        or len(pcm) % _PCM16_STEREO_FRAME_BYTES
    ):
        raise _source_invalid("Native audio segment sample count is invalid.")
    processed_samples = len(pcm) // _PCM16_STEREO_FRAME_BYTES
    delta = target_samples - processed_samples
    if processed_samples <= 0 or abs(delta) > maximum_correction_samples:
        raise _source_invalid("Native audio segment needs excessive tail correction.")
    if delta > 0:
        return (
            pcm + bytes(delta * _PCM16_STEREO_FRAME_BYTES),
            processed_samples,
            delta,
            0,
        )
    if delta < 0:
        return (
            pcm[: target_samples * _PCM16_STEREO_FRAME_BYTES],
            processed_samples,
            0,
            -delta,
        )
    return pcm, processed_samples, 0, 0


def derive_native_audio_pcm(
    source: NoFollowFile,
    *,
    source_video_asset_id: str,
    source_video_sha256: str,
    track_id: str,
    mapping: NativeAudioRetime,
    sample_rate_hz: int,
    max_correction_samples: int,
    ffmpeg_path: Path | None,
    ffprobe_path: Path | None,
) -> tuple[bytes, NativeAudioDerivationProof]:
    if (
        not source_video_asset_id
        or not track_id
        or sample_rate_hz <= 0
        or max_correction_samples < 0
        or source.file_sha256 != source_video_sha256
        or len(source.data) != source.size_bytes
        or hashlib.sha256(source.data).hexdigest() != source_video_sha256
    ):
        raise _source_invalid(
            "Native audio source identity does not match its binding."
        )
    source_end_sample = max(
        segment.source_start_sample + segment.source_duration_samples
        for segment in mapping.segments
    )
    with ExitStack() as stack:
        source_descriptor = _held_source_snapshot(source, stack)
        ffmpeg_descriptor, ffmpeg_sha256 = _open_tool(stack, ffmpeg_path, "ffmpeg")
        ffprobe_descriptor, ffprobe_sha256 = _open_tool(stack, ffprobe_path, "ffprobe")
        audio_start_sample = _probe_source(
            ffprobe_descriptor,
            source_descriptor,
            sample_rate_hz=sample_rate_hz,
        )
        source_pcm = _decode_source_pcm(
            ffmpeg_descriptor,
            source_descriptor,
            sample_rate_hz=sample_rate_hz,
            source_end_sample=source_end_sample,
            audio_start_sample=audio_start_sample,
        )
        input_pcm_sha256 = hashlib.sha256(source_pcm).hexdigest()
        mapped_parts: list[bytes] = []
        segment_results: list[AudioSegmentProcessingProof] = []
        for segment in mapping.segments:
            start = segment.source_start_sample * _PCM16_STEREO_FRAME_BYTES
            end = (
                segment.source_start_sample + segment.source_duration_samples
            ) * _PCM16_STEREO_FRAME_BYTES
            processed = _process_segment(
                ffmpeg_descriptor,
                source_pcm[start:end],
                source_samples=segment.source_duration_samples,
                output_samples=segment.output_duration_samples,
                sample_rate_hz=sample_rate_hz,
            )
            fitted, processed_samples, padded, trimmed = _fit_segment_sample_count(
                processed,
                target_samples=segment.output_duration_samples,
                maximum_correction_samples=max_correction_samples,
            )
            mapped_parts.append(fitted)
            segment_results.append(
                AudioSegmentProcessingProof(
                    segment=segment,
                    processed_samples=processed_samples,
                    padded_samples=padded,
                    trimmed_samples=trimmed,
                )
            )
        mapped_pcm = b"".join(mapped_parts)
        mapped_samples = sum(
            item.segment.output_duration_samples for item in segment_results
        )
        proof = NativeAudioDerivationProof(
            track_id=track_id,
            source_video_asset_id=source_video_asset_id,
            source_video_sha256=source_video_sha256,
            stream_index=mapping.stream_index,
            sample_rate_hz=sample_rate_hz,
            channels=2,
            audio_start_sample=audio_start_sample,
            input_pcm_sha256=input_pcm_sha256,
            input_samples=len(source_pcm) // _PCM16_STEREO_FRAME_BYTES,
            mapped_pcm_sha256=hashlib.sha256(mapped_pcm).hexdigest(),
            mapped_samples=mapped_samples,
            mapping_sha256=native_audio_mapping_sha256(mapping),
            ffmpeg_sha256=ffmpeg_sha256,
            ffprobe_sha256=ffprobe_sha256,
            segment_results=tuple(segment_results),
        )
        return mapped_pcm, proof
