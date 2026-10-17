from __future__ import annotations

import struct
import wave
from collections.abc import Mapping
from decimal import (
    Decimal,
    DecimalException,
    ROUND_HALF_EVEN,
    localcontext,
)
from io import BytesIO
from typing import Callable

from ai_video.errors import AiVideoError
from ai_video.production.models import ResolvedTimeline
from ai_video.production.paths import NoFollowFile

_MIX_SCALE = 1_000_000
_PCM16_STEREO_FRAME_BYTES = 4
_MIN_GAIN_MILLIDB = -96_000
_MAX_GAIN_MILLIDB = 24_000

SourceInvalid = Callable[[str, str | None], AiVideoError]


def fixed_gain(gain_millidb: int, *, source_invalid: SourceInvalid) -> int:
    """Convert the adapter-supported -96..+24 dB range to fixed-point gain."""

    if not _MIN_GAIN_MILLIDB <= gain_millidb <= _MAX_GAIN_MILLIDB:
        raise source_invalid(
            "Audio gain is outside the P4 renderer adapter range.",
            f"supported gain_millidb range is {_MIN_GAIN_MILLIDB}..{_MAX_GAIN_MILLIDB}",
        )
    try:
        with localcontext() as context:
            context.prec = 50
            context.rounding = ROUND_HALF_EVEN
            exponent = Decimal(gain_millidb) / Decimal(20_000)
            scaled = (Decimal(10) ** exponent) * Decimal(_MIX_SCALE)
            return int(scaled.to_integral_value(rounding=ROUND_HALF_EVEN))
    except (DecimalException, OverflowError, ValueError) as exc:
        raise source_invalid(
            "Audio gain could not be converted deterministically.",
            f"supported gain_millidb range is {_MIN_GAIN_MILLIDB}..{_MAX_GAIN_MILLIDB}",
        ) from exc


def multiply_fixed(left: int, right: int) -> int:
    product = left * right
    return (product + _MIX_SCALE // 2) // _MIX_SCALE


def scale_pcm(sample: int, scale: int) -> int:
    product = sample * scale
    if product >= 0:
        return (product + _MIX_SCALE // 2) // _MIX_SCALE
    return -((-product + _MIX_SCALE // 2) // _MIX_SCALE)


def linear_scale(start: int, end: int, ordinal: int, length: int) -> int:
    if length <= 0:
        return end
    return start + ((end - start) * ordinal + length // 2) // length


def ducking_scale(
    sample: int,
    *,
    intervals: tuple[tuple[int, int], ...],
    attenuation: int,
    attack: int,
    release: int,
) -> int:
    result = _MIX_SCALE
    for start, end in intervals:
        if start <= sample < end:
            if attack and sample - start < attack:
                candidate = linear_scale(
                    _MIX_SCALE, attenuation, sample - start + 1, attack
                )
            else:
                candidate = attenuation
            result = min(result, candidate)
        elif release and end <= sample < end + release:
            candidate = linear_scale(attenuation, _MIX_SCALE, sample - end + 1, release)
            result = min(result, candidate)
    return result


def decoded_pcm16(
    snapshot: NoFollowFile, *, source_invalid: SourceInvalid
) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    sample_rate, channels, frames = validated_wav(
        snapshot, source_invalid=source_invalid
    )
    with wave.open(BytesIO(snapshot.data), "rb") as source:
        payload = source.readframes(frames)
    values = struct.unpack(f"<{frames * channels}h", payload)
    if channels == 1:
        stereo = tuple((value, value) for value in values)
    else:
        stereo = tuple(zip(values[0::2], values[1::2], strict=True))
    return sample_rate, frames, stereo


def mix_resolved_audio(
    timeline: ResolvedTimeline,
    *,
    audio_snapshots: Mapping[str, NoFollowFile],
    native_audio_pcm_by_track: Mapping[str, bytes] | None = None,
    source_invalid: SourceInvalid,
) -> bytes:
    decoded: dict[str, tuple[tuple[int, int], ...]] = {}
    for asset_id, snapshot in audio_snapshots.items():
        sample_rate, _, samples = decoded_pcm16(snapshot, source_invalid=source_invalid)
        if sample_rate != timeline.sample_rate:
            raise source_invalid("Audio source sample rate does not match timeline.")
        decoded[asset_id] = samples
    by_track = {item.track_id: item for item in timeline.audio_spans}
    native_audio_pcm = native_audio_pcm_by_track or {}
    native_track_ids = {
        item.track_id
        for item in timeline.audio_spans
        if item.native_audio_retime is not None
    }
    if set(native_audio_pcm) != native_track_ids:
        raise source_invalid(
            "Native audio PCM tracks do not match the resolved timeline."
        )
    native_decoded: dict[str, tuple[tuple[int, int], ...]] = {}
    for track_id, payload in native_audio_pcm.items():
        if len(payload) % _PCM16_STEREO_FRAME_BYTES:
            raise source_invalid("Native audio PCM has an invalid sample count.")
        frame_count = len(payload) // _PCM16_STEREO_FRAME_BYTES
        values = struct.unpack(f"<{frame_count * 2}h", payload)
        native_decoded[track_id] = tuple(zip(values[0::2], values[1::2], strict=True))
    output = [[0, 0] for _ in range(timeline.total_samples)]
    for span in timeline.audio_spans:
        if span.native_audio_retime is None:
            source = decoded[span.asset_id]
            source_start = span.source_start_sample
            source_end = source_start + span.source_duration_samples
            if (
                source_end > len(source)
                or span.duration_samples != span.source_duration_samples
            ):
                raise source_invalid(
                    "P4 pre-mix requires exact source-duration placement."
                )
        else:
            source = native_decoded[span.track_id]
            source_start = 0
            if span.duration_samples != len(source):
                raise source_invalid(
                    "Native audio PCM does not match its resolved duration."
                )
        gain = fixed_gain(span.gain_millidb, source_invalid=source_invalid)
        duck_intervals: tuple[tuple[int, int], ...] = ()
        attenuation = _MIX_SCALE
        attack = release = 0
        if span.ducking is not None:
            duck_intervals = tuple(
                (
                    by_track[track_id].start_sample,
                    by_track[track_id].start_sample
                    + by_track[track_id].duration_samples,
                )
                for track_id in span.ducking.sidechain_track_ids
            )
            attenuation = fixed_gain(
                span.ducking.attenuation_millidb,
                source_invalid=source_invalid,
            )
            attack = span.ducking.attack_samples
            release = span.ducking.release_samples
        for offset in range(span.duration_samples):
            envelope = _MIX_SCALE
            if span.fade_in_samples and offset < span.fade_in_samples:
                envelope = min(
                    envelope,
                    linear_scale(0, _MIX_SCALE, offset + 1, span.fade_in_samples),
                )
            remaining = span.duration_samples - offset
            if span.fade_out_samples and remaining <= span.fade_out_samples:
                envelope = min(
                    envelope,
                    linear_scale(0, _MIX_SCALE, remaining, span.fade_out_samples),
                )
            if span.ducking is not None:
                envelope = multiply_fixed(
                    envelope,
                    ducking_scale(
                        span.start_sample + offset,
                        intervals=duck_intervals,
                        attenuation=attenuation,
                        attack=attack,
                        release=release,
                    ),
                )
            scale = multiply_fixed(gain, envelope)
            left, right = source[source_start + offset]
            target = output[span.start_sample + offset]
            target[0] += scale_pcm(left, scale)
            target[1] += scale_pcm(right, scale)
    pcm = bytearray()
    for left, right in output:
        pcm.extend(
            struct.pack(
                "<hh",
                max(-32768, min(32767, left)),
                max(-32768, min(32767, right)),
            )
        )
    buffer = BytesIO()
    with wave.open(buffer, "wb") as mixed:
        mixed.setnchannels(2)
        mixed.setsampwidth(2)
        mixed.setframerate(timeline.sample_rate)
        mixed.writeframes(bytes(pcm))
    return buffer.getvalue()


def validated_wav(
    snapshot: NoFollowFile, *, source_invalid: SourceInvalid
) -> tuple[int, int, int]:
    try:
        with wave.open(BytesIO(snapshot.data), "rb") as source:
            if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
                raise ValueError("only PCM16 WAV is accepted by the P4 renderer")
            channels = source.getnchannels()
            if channels not in {1, 2}:
                raise ValueError("P4 audio must be mono or stereo")
            return source.getframerate(), channels, source.getnframes()
    except (EOFError, wave.Error, ValueError) as exc:
        raise source_invalid(
            "Renderer audio source is not canonical PCM16 WAV.", str(exc)
        ) from exc
