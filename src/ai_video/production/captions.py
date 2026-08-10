from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN
from typing import Literal

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    CaptionSegment,
    CaptionSegmentationPolicy,
    CaptionStyleReference,
    CaptionTrack,
    CaptionWord,
    SourceReference,
    StrictModel,
)


_MAX_SOURCE_SAMPLE = (1 << 63) - 1
_MAX_DECIMAL_INPUT_LENGTH = 128
_MAX_DECIMAL_ADJUSTED_MAGNITUDE = 96
_MAX_RECEIPT_DECIMAL_MAGNITUDE = Decimal("1e12")


def _alignment_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.CAPTION_ALIGNMENT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _track_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.CAPTION_TRACK_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class NormalizedAlignmentUnit(StrictModel):
    text: str = Field(min_length=1)
    start_sample: int = Field(strict=True, ge=0)
    end_sample: int = Field(strict=True, gt=0)
    speaker_id: str | None = None
    confidence_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "NormalizedAlignmentUnit":
        if self.end_sample <= self.start_sample:
            raise ValueError("normalized alignment end must follow start")
        return self


class NormalizedAlignment(StrictModel):
    unit_kind: Literal["character", "word"]
    units: tuple[NormalizedAlignmentUnit, ...] = Field(min_length=1)
    sample_rate_hz: int = Field(strict=True, gt=0)
    duration_samples: int = Field(strict=True, gt=0)
    provider_segment_end_indices: tuple[int, ...] | None = None
    receipt_bytes: bytes = Field(min_length=1)
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_receipt_and_bounds(self) -> "NormalizedAlignment":
        if hashlib.sha256(self.receipt_bytes).hexdigest() != self.receipt_sha256:
            raise ValueError("normalized alignment receipt hash does not match bytes")
        previous_end = 0
        for unit in self.units:
            if unit.start_sample < previous_end:
                raise ValueError("normalized alignment units must be monotonic")
            if unit.end_sample > self.duration_samples:
                raise ValueError("normalized alignment exceeds source duration")
            previous_end = unit.end_sample
        if self.provider_segment_end_indices is not None:
            previous_index = 0
            for end_index in self.provider_segment_end_indices:
                if (
                    isinstance(end_index, bool)
                    or end_index <= previous_index
                    or end_index > len(self.units)
                ):
                    raise ValueError(
                        "provider segment boundaries must be strict end indices"
                    )
                previous_index = end_index
            if previous_index != len(self.units):
                raise ValueError("provider segment boundaries must cover every unit")
        return self


def _bounded_decimal(
    value: object,
    label: str,
    *,
    maximum_magnitude: Decimal,
) -> Decimal:
    if isinstance(value, bool):
        raise _alignment_invalid(f"{label} must be a finite bounded decimal number.")
    try:
        token = str(value)
        if len(token) > _MAX_DECIMAL_INPUT_LENGTH:
            raise ValueError("decimal token is too long")
        decimal = Decimal(token)
        if (
            not decimal.is_finite()
            or abs(decimal.adjusted()) > _MAX_DECIMAL_ADJUSTED_MAGNITUDE
            or abs(decimal) > maximum_magnitude
        ):
            raise ValueError("decimal magnitude is out of bounds")
        return decimal
    except (DecimalException, OverflowError, ValueError) as exc:
        raise _alignment_invalid(
            f"{label} must be a finite bounded decimal number."
        ) from exc


def _maximum_timing_seconds(sample_rate_hz: int, duration_samples: int) -> Decimal:
    if (
        isinstance(sample_rate_hz, bool)
        or not isinstance(sample_rate_hz, int)
        or sample_rate_hz <= 0
        or isinstance(duration_samples, bool)
        or not isinstance(duration_samples, int)
        or duration_samples <= 0
        or duration_samples > _MAX_SOURCE_SAMPLE
    ):
        raise _alignment_invalid("Caption source sample bounds are invalid.")
    return Decimal(_MAX_SOURCE_SAMPLE) / Decimal(sample_rate_hz)


def seconds_to_source_sample(value: object, sample_rate_hz: int) -> int:
    if (
        isinstance(sample_rate_hz, bool)
        or not isinstance(sample_rate_hz, int)
        or sample_rate_hz <= 0
    ):
        raise _alignment_invalid("Caption source sample rate must be positive.")
    maximum_seconds = Decimal(_MAX_SOURCE_SAMPLE) / Decimal(sample_rate_hz)
    try:
        seconds = _bounded_decimal(
            value,
            "Caption timing value",
            maximum_magnitude=maximum_seconds,
        )
        if seconds < 0:
            raise ValueError("negative timing")
        samples = (seconds * Decimal(sample_rate_hz)).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
        if samples > _MAX_SOURCE_SAMPLE:
            raise ValueError("sample bound exceeded")
        return int(samples)
    except AiVideoError:
        raise
    except (DecimalException, OverflowError, ValueError) as exc:
        raise _alignment_invalid(
            "Caption timing value must be finite, non-negative, and bounded."
        ) from exc


def _canonical_receipt_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _alignment_invalid(f"{label} must be an object.")
    return value


def _require_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise _alignment_invalid(f"{label} must be an array.")
    return value


def _normalized_decimal(
    value: object,
    label: str,
    *,
    maximum_magnitude: Decimal = _MAX_RECEIPT_DECIMAL_MAGNITUDE,
) -> str:
    try:
        decimal = _bounded_decimal(
            value,
            label,
            maximum_magnitude=maximum_magnitude,
        )
        return format(decimal, "f")
    except AiVideoError:
        raise
    except (DecimalException, OverflowError, ValueError) as exc:
        raise _alignment_invalid(f"{label} cannot be normalized safely.") from exc


def _contains_unsupported_grapheme_extension(value: str) -> bool:
    return any(
        character == "\u200d"
        or "\ufe00" <= character <= "\ufe0f"
        or "\U000e0100" <= character <= "\U000e01ef"
        or "\U0001f3fb" <= character <= "\U0001f3ff"
        for character in value
    )


def _make_alignment(
    *,
    unit_kind: Literal["character", "word"],
    texts: Sequence[object],
    starts: Sequence[object],
    ends: Sequence[object],
    sample_rate_hz: int,
    duration_samples: int,
    speaker_id: str | None,
    receipt_payload: object,
) -> NormalizedAlignment:
    if (
        isinstance(duration_samples, bool)
        or not isinstance(duration_samples, int)
        or duration_samples <= 0
    ):
        raise _alignment_invalid("Caption source duration must be positive samples.")
    if len(texts) != len(starts) or len(texts) != len(ends):
        raise _alignment_invalid("Caption alignment parallel arrays must have equal length.")
    if not texts:
        raise _alignment_invalid("Caption alignment must contain at least one timing unit.")
    units: list[NormalizedAlignmentUnit] = []
    previous_end = 0
    for index, (raw_text, raw_start, raw_end) in enumerate(
        zip(texts, starts, ends, strict=True)
    ):
        if not isinstance(raw_text, str) or not raw_text:
            raise _alignment_invalid("Caption alignment text units must be non-empty.")
        text = unicodedata.normalize("NFC", raw_text)
        start = seconds_to_source_sample(raw_start, sample_rate_hz)
        end = seconds_to_source_sample(raw_end, sample_rate_hz)
        if end <= start:
            raise _alignment_invalid(
                "Caption alignment end must follow start.", f"unit_index={index}"
            )
        if start < previous_end:
            raise _alignment_invalid(
                "Caption alignment must be monotonic.", f"unit_index={index}"
            )
        if end > duration_samples:
            raise _alignment_invalid(
                "Caption alignment exceeds source duration.", f"unit_index={index}"
            )
        if unit_kind == "character" and unicodedata.combining(raw_text[0]):
            if any(not unicodedata.combining(character) for character in raw_text):
                raise _alignment_invalid(
                    "Caption combining-mark timing is ambiguous.",
                    f"unit_index={index}",
                )
            if not units:
                raise _alignment_invalid(
                    "Caption alignment cannot start with an orphan combining mark."
                )
            previous = units[-1]
            units[-1] = previous.model_copy(
                update={
                    "text": unicodedata.normalize("NFC", previous.text + raw_text),
                    "end_sample": max(previous.end_sample, end),
                }
            )
            previous_end = max(previous.end_sample, end)
            continue
        units.append(
            NormalizedAlignmentUnit(
                text=text,
                start_sample=start,
                end_sample=end,
                speaker_id=speaker_id,
                confidence_milli=None,
            )
        )
        previous_end = end
    receipt_bytes = _canonical_receipt_bytes(receipt_payload)
    return NormalizedAlignment(
        unit_kind=unit_kind,
        units=tuple(units),
        sample_rate_hz=sample_rate_hz,
        duration_samples=duration_samples,
        receipt_bytes=receipt_bytes,
        receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
    )


def normalize_character_alignment(
    alignment: Mapping[str, object],
    *,
    sample_rate_hz: int,
    duration_samples: int,
    speaker_id: str | None = None,
) -> NormalizedAlignment:
    payload = _require_mapping(alignment, "Character alignment")
    required = {
        "characters",
        "character_start_times_seconds",
        "character_end_times_seconds",
    }
    if set(payload) != required:
        raise _alignment_invalid(
            "Character alignment must contain only the official timing fields."
        )
    characters = _require_sequence(payload["characters"], "characters")
    starts = _require_sequence(
        payload["character_start_times_seconds"], "character starts"
    )
    ends = _require_sequence(
        payload["character_end_times_seconds"], "character ends"
    )
    maximum_seconds = _maximum_timing_seconds(sample_rate_hz, duration_samples)
    for character in characters:
        if isinstance(character, str) and _contains_unsupported_grapheme_extension(
            character
        ):
            raise _alignment_invalid(
                "Character alignment contains an unsupported grapheme extension."
            )
    receipt = {
        "characters": [
            unicodedata.normalize("NFC", item) if isinstance(item, str) else item
            for item in characters
        ],
        "character_start_times_seconds": [
            _normalized_decimal(
                item,
                "character start",
                maximum_magnitude=maximum_seconds,
            )
            for item in starts
        ],
        "character_end_times_seconds": [
            _normalized_decimal(
                item,
                "character end",
                maximum_magnitude=maximum_seconds,
            )
            for item in ends
        ],
    }
    return _make_alignment(
        unit_kind="character",
        texts=characters,
        starts=starts,
        ends=ends,
        sample_rate_hz=sample_rate_hz,
        duration_samples=duration_samples,
        speaker_id=speaker_id,
        receipt_payload=receipt,
    )


def normalize_word_alignment(
    alignment: Mapping[str, object],
    *,
    sample_rate_hz: int,
    duration_samples: int,
    speaker_id: str | None = None,
) -> NormalizedAlignment:
    payload = _require_mapping(alignment, "Word alignment")
    allowed = {"characters", "words", "loss"}
    if "words" not in payload or not set(payload).issubset(allowed):
        raise _alignment_invalid(
            "Word alignment must contain only the official forced-alignment fields."
        )
    raw_words = _require_sequence(payload["words"], "words")
    maximum_seconds = _maximum_timing_seconds(sample_rate_hz, duration_samples)
    texts: list[object] = []
    starts: list[object] = []
    ends: list[object] = []
    receipt_words: list[dict[str, str]] = []
    for raw_word in raw_words:
        word = _require_mapping(raw_word, "forced-alignment word")
        if not {"text", "start", "end"}.issubset(word) or not set(word).issubset(
            {"text", "start", "end", "loss"}
        ):
            raise _alignment_invalid("Forced-alignment word fields are invalid.")
        texts.append(word["text"])
        starts.append(word["start"])
        ends.append(word["end"])
        receipt_word = {
            "text": (
                unicodedata.normalize("NFC", word["text"])
                if isinstance(word["text"], str)
                else word["text"]
            ),
            "start": _normalized_decimal(
                word["start"], "word start", maximum_magnitude=maximum_seconds
            ),
            "end": _normalized_decimal(
                word["end"], "word end", maximum_magnitude=maximum_seconds
            ),
        }
        if "loss" in word:
            receipt_word["loss"] = _normalized_decimal(word["loss"], "word loss")
        receipt_words.append(receipt_word)
    receipt: dict[str, object] = {"words": receipt_words}
    if "characters" in payload:
        characters = _require_sequence(payload["characters"], "characters")
        receipt["characters"] = []
        for raw_character in characters:
            character = _require_mapping(raw_character, "forced-alignment character")
            if set(character) != {"text", "start", "end"}:
                raise _alignment_invalid("Forced-alignment character fields are invalid.")
            receipt["characters"].append(
                {
                    "text": (
                        unicodedata.normalize("NFC", character["text"])
                        if isinstance(character["text"], str)
                        else character["text"]
                    ),
                    "start": _normalized_decimal(
                        character["start"],
                        "character start",
                        maximum_magnitude=maximum_seconds,
                    ),
                    "end": _normalized_decimal(
                        character["end"],
                        "character end",
                        maximum_magnitude=maximum_seconds,
                    ),
                }
            )
    if "loss" in payload:
        receipt["loss"] = _normalized_decimal(payload["loss"], "alignment loss")
    return _make_alignment(
        unit_kind="word",
        texts=texts,
        starts=starts,
        ends=ends,
        sample_rate_hz=sample_rate_hz,
        duration_samples=duration_samples,
        speaker_id=speaker_id,
        receipt_payload=receipt,
    )


def _alignment_text(alignment: NormalizedAlignment) -> str:
    if alignment.unit_kind == "character":
        return "".join(unit.text for unit in alignment.units)
    return " ".join(unit.text for unit in alignment.units)


def _group_text(
    alignment: NormalizedAlignment,
    units: Sequence[NormalizedAlignmentUnit],
) -> str:
    if alignment.unit_kind == "character":
        return "".join(unit.text for unit in units)
    return " ".join(unit.text for unit in units)


def _segment_unit_groups(
    alignment: NormalizedAlignment,
    policy: CaptionSegmentationPolicy,
) -> tuple[tuple[NormalizedAlignmentUnit, ...], ...]:
    capacity = policy.max_characters * policy.max_lines

    def checked_group(
        units: Sequence[NormalizedAlignmentUnit],
    ) -> tuple[NormalizedAlignmentUnit, ...]:
        group = tuple(units)
        if not group or len(_group_text(alignment, group)) > capacity:
            raise _track_invalid(
                "Caption segment cannot satisfy segmentation policy limits."
            )
        return group

    if policy.break_strategy == "provider_segments":
        boundaries = alignment.provider_segment_end_indices
        if boundaries is None:
            raise _track_invalid(
                "Caption provider segment boundaries are required by policy."
            )
        groups: list[tuple[NormalizedAlignmentUnit, ...]] = []
        start = 0
        for end in boundaries:
            groups.append(checked_group(alignment.units[start:end]))
            start = end
        return tuple(groups)

    if policy.break_strategy == "sentence":
        punctuation = frozenset(".!?。！？")
        groups = []
        start = 0
        for index, unit in enumerate(alignment.units, start=1):
            if unit.text[-1] in punctuation:
                groups.append(checked_group(alignment.units[start:index]))
                start = index
        if start < len(alignment.units):
            groups.append(checked_group(alignment.units[start:]))
        return tuple(groups)

    groups = []
    current: list[NormalizedAlignmentUnit] = []
    for unit in alignment.units:
        candidate = (*current, unit)
        if len(_group_text(alignment, candidate)) <= capacity:
            current.append(unit)
            continue
        if not current:
            raise _track_invalid(
                "Caption segment cannot satisfy segmentation policy limits."
            )
        groups.append(tuple(current))
        current = [unit]
        if len(_group_text(alignment, current)) > capacity:
            raise _track_invalid(
                "Caption segment cannot satisfy segmentation policy limits."
            )
    if current:
        groups.append(tuple(current))
    return tuple(groups)


def caption_timing_fingerprint(track: CaptionTrack) -> str:
    return canonical_sha256(
        {
            "caption_track_id": track.caption_track_id,
            "language": track.language,
            "script_hash": track.script_hash,
            "transcript_hash": track.transcript_hash,
            "source_audio_asset_id": track.source_audio_asset_id,
            "source_audio_sha256": track.source_audio_sha256,
            "source_sample_rate_hz": track.source_sample_rate_hz,
            "segments": [item.model_dump(mode="json") for item in track.segments],
            "segmentation_policy": track.segmentation_policy.model_dump(mode="json"),
            "alignment_provider": track.alignment_provider,
            "alignment_model": track.alignment_model,
            "alignment_receipt_id": track.alignment_receipt_id,
        }
    )


def segment_caption_track(
    alignment: NormalizedAlignment,
    *,
    artifact_id: str,
    revision: int,
    creation_receipt_id: str,
    source_provenance: tuple[SourceReference, ...],
    caption_track_id: str,
    language: str,
    script_text: str,
    transcript_text: str,
    source_audio_asset_id: str,
    source_audio_sha256: str,
    source_sample_rate_hz: int,
    source_duration_samples: int,
    segmentation_policy: CaptionSegmentationPolicy,
    alignment_provider: str,
    alignment_model: str | None,
    alignment_receipt_id: str,
    style_reference_id: str | None = None,
) -> CaptionTrack:
    if (
        source_sample_rate_hz != alignment.sample_rate_hz
        or source_duration_samples != alignment.duration_samples
    ):
        raise _track_invalid("Caption alignment source audio identity is inconsistent.")
    normalized_script = unicodedata.normalize("NFC", script_text)
    normalized_transcript = unicodedata.normalize("NFC", transcript_text)
    if not normalized_script or not normalized_transcript:
        raise _track_invalid("Caption script and transcript must be non-empty.")
    if _alignment_text(alignment) != normalized_transcript:
        raise _track_invalid("Caption transcript does not match normalized alignment text.")

    unit_groups = _segment_unit_groups(alignment, segmentation_policy)
    segments: list[CaptionSegment] = []
    for index, group in enumerate(unit_groups, start=1):
        speakers = {item.speaker_id for item in group}
        segment_speaker = next(iter(speakers)) if len(speakers) == 1 else None
        words: tuple[CaptionWord, ...] | None = None
        if alignment.unit_kind == "word":
            words = tuple(
                CaptionWord(
                    text=item.text,
                    start_sample=item.start_sample,
                    end_sample=item.end_sample,
                    speaker_id=item.speaker_id,
                    confidence_milli=item.confidence_milli,
                )
                for item in group
            )
        segments.append(
            CaptionSegment(
                segment_id=f"segment-{index:04d}",
                text=_group_text(alignment, group),
                start_sample=group[0].start_sample,
                end_sample=group[-1].end_sample,
                speaker_id=segment_speaker,
                words=words,
                confidence_milli=None,
            )
        )
    track = CaptionTrack(
        artifact_id=artifact_id,
        schema_version="2.1",
        revision=revision,
        content_hash="0" * 64,
        creation_receipt_id=creation_receipt_id,
        source_provenance=source_provenance,
        caption_track_id=caption_track_id,
        language=language,
        script_hash=hashlib.sha256(normalized_script.encode("utf-8")).hexdigest(),
        transcript_hash=hashlib.sha256(
            normalized_transcript.encode("utf-8")
        ).hexdigest(),
        source_audio_asset_id=source_audio_asset_id,
        source_audio_sha256=source_audio_sha256,
        source_sample_rate_hz=source_sample_rate_hz,
        segments=tuple(segments),
        segmentation_policy=segmentation_policy,
        alignment_provider=alignment_provider,
        alignment_model=alignment_model,
        alignment_receipt_id=alignment_receipt_id,
        style_reference_id=style_reference_id,
        timing_fingerprint="0" * 64,
    )
    track = track.model_copy(
        update={"timing_fingerprint": caption_timing_fingerprint(track)}
    )
    return CaptionTrack.model_validate(seal_artifact(track).model_dump(mode="python"))


def caption_style_fingerprint(
    style_reference: CaptionStyleReference, style_bytes: bytes
) -> str:
    if hashlib.sha256(style_bytes).hexdigest() != style_reference.content_hash:
        raise _track_invalid("Caption style bytes hash does not match reference.")
    try:
        schema = json.loads(style_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _track_invalid("Caption style bytes must contain UTF-8 JSON.") from exc
    if not isinstance(schema, dict):
        raise _track_invalid("Caption style schema must be a JSON object.")
    return canonical_sha256(
        {
            "artifact_id": style_reference.artifact_id,
            "revision": style_reference.revision,
            "content_hash": style_reference.content_hash,
            "renderer_consumed_style_schema": schema,
        }
    )


def _canonical_track_bytes(track: CaptionTrack) -> bytes:
    return _canonical_receipt_bytes(track.model_dump(mode="json"))


class CaptionImportRequest(StrictModel):
    caption_track: CaptionTrack
    track_bytes: bytes = Field(min_length=1)
    track_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    style_reference: CaptionStyleReference | None = None
    style_bytes: bytes | None = None
    style_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_sealed_bytes(self) -> "CaptionImportRequest":
        if self.track_bytes != _canonical_track_bytes(self.caption_track):
            raise ValueError("caption track bytes must be canonical and exact")
        if hashlib.sha256(self.track_bytes).hexdigest() != self.track_sha256:
            raise ValueError("caption track bytes hash does not match")
        if self.caption_track.content_hash != canonical_sha256(self.caption_track):
            raise ValueError("caption track semantic content hash does not match")
        if self.caption_track.timing_fingerprint != caption_timing_fingerprint(
            self.caption_track
        ):
            raise ValueError("caption timing fingerprint does not match track")
        style_values = (self.style_reference, self.style_bytes, self.style_sha256)
        if any(value is None for value in style_values) and any(
            value is not None for value in style_values
        ):
            raise ValueError("caption style bytes and identity must be all-or-none")
        if self.style_reference is None:
            if self.caption_track.style_reference_id is not None:
                raise ValueError("caption track style identity requires sealed style bytes")
            return self
        assert self.style_bytes is not None and self.style_sha256 is not None
        if self.caption_track.style_reference_id != self.style_reference.artifact_id:
            raise ValueError("caption style identity does not match track")
        if hashlib.sha256(self.style_bytes).hexdigest() != self.style_sha256:
            raise ValueError("caption style bytes hash does not match")
        if self.style_sha256 != self.style_reference.content_hash:
            raise ValueError("caption style reference hash does not match bytes")
        caption_style_fingerprint(self.style_reference, self.style_bytes)
        return self

    @classmethod
    def create(
        cls,
        *,
        caption_track: CaptionTrack,
        style_reference: CaptionStyleReference | None = None,
        style_bytes: bytes | None = None,
    ) -> "CaptionImportRequest":
        track_bytes = _canonical_track_bytes(caption_track)
        return cls(
            caption_track=caption_track,
            track_bytes=track_bytes,
            track_sha256=hashlib.sha256(track_bytes).hexdigest(),
            style_reference=style_reference,
            style_bytes=style_bytes,
            style_sha256=(
                hashlib.sha256(style_bytes).hexdigest()
                if style_bytes is not None
                else None
            ),
        )

    def prepare(self) -> "PreparedCaptionImport":
        return PreparedCaptionImport(
            caption_track=self.caption_track,
            track_bytes=self.track_bytes,
            track_sha256=self.track_sha256,
            style_reference=self.style_reference,
            style_bytes=self.style_bytes,
            style_sha256=self.style_sha256,
        )


@dataclass(frozen=True)
class PreparedCaptionImport:
    caption_track: CaptionTrack
    track_bytes: bytes
    track_sha256: str
    style_reference: CaptionStyleReference | None
    style_bytes: bytes | None
    style_sha256: str | None
