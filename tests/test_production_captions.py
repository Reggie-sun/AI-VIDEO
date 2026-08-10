from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import (
    CaptionImportRequest,
    caption_style_fingerprint,
    caption_timing_fingerprint,
    normalize_character_alignment,
    normalize_word_alignment,
    seconds_to_source_sample,
    segment_caption_track,
)
from ai_video.production.models import (
    CaptionSegmentationPolicy,
    CaptionStyleReference,
    SourceReference,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures/voice_captions"
WITH_TIMESTAMPS = FIXTURE_ROOT / "elevenlabs-with-timestamps.json"
FORCED_ALIGNMENT = FIXTURE_ROOT / "elevenlabs-forced-alignment.json"
ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def _load_fixture(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _policy(
    *,
    version: str = "1",
    strategy: str = "word_window",
    max_characters: int = 42,
    max_lines: int = 2,
) -> CaptionSegmentationPolicy:
    return CaptionSegmentationPolicy(
        policy_id=f"{strategy}-fixture",
        policy_version=version,
        max_characters=max_characters,
        max_lines=max_lines,
        break_strategy=strategy,
    )


def _track(*, policy_version: str = "1", style_reference_id: str | None = None):
    payload = _load_fixture(WITH_TIMESTAMPS)
    alignment = normalize_character_alignment(
        payload["normalized_alignment"],
        sample_rate_hz=48_000,
        duration_samples=48_000,
        speaker_id="speaker-1",
    )
    return segment_caption_track(
        alignment,
        artifact_id="caption-artifact-1",
        revision=1,
        creation_receipt_id="caption-create-1",
        source_provenance=(
            SourceReference(kind="derived", reference="alignment-receipt-1"),
        ),
        caption_track_id="caption-track-1",
        language="fr",
        script_text="Cafe\u0301.",
        transcript_text="Caf\u00e9.",
        source_audio_asset_id="voice-asset-1",
        source_audio_sha256=ONE_HASH,
        source_sample_rate_hz=48_000,
        source_duration_samples=48_000,
        segmentation_policy=_policy(version=policy_version),
        alignment_provider="elevenlabs",
        alignment_model="fixture-v1",
        alignment_receipt_id="alignment-receipt-1",
        style_reference_id=style_reference_id,
    )


def test_official_shape_fixtures_are_minimal_and_synthetic():
    timing = _load_fixture(WITH_TIMESTAMPS)
    assert set(timing) == {"audio_base64", "alignment", "normalized_alignment"}
    assert set(timing["normalized_alignment"]) == {
        "characters",
        "character_start_times_seconds",
        "character_end_times_seconds",
    }
    forced = _load_fixture(FORCED_ALIGNMENT)
    assert set(forced) == {"characters", "words", "loss"}
    assert set(forced["words"][0]) == {"text", "start", "end", "loss"}
    assert "api" not in WITH_TIMESTAMPS.read_text(encoding="utf-8").lower()


def test_seconds_to_samples_uses_decimal_and_half_even_rounding():
    assert seconds_to_source_sample("0.000010416666666666666666", 48_000) == 0
    assert seconds_to_source_sample(Decimal("0.00003125"), 48_000) == 2
    assert seconds_to_source_sample(0.1, 48_000) == 4_800


@pytest.mark.parametrize("value", [-1, "NaN", "Infinity", "-Infinity", True])
def test_seconds_to_samples_rejects_invalid_values(value):
    with pytest.raises(AiVideoError) as caught:
        seconds_to_source_sample(value, 48_000)
    assert caught.value.code is ErrorCode.CAPTION_ALIGNMENT_INVALID


@pytest.mark.parametrize("sample_rate", [True, False])
def test_seconds_to_samples_rejects_bool_sample_rate(sample_rate):
    with pytest.raises(AiVideoError):
        seconds_to_source_sample("0.1", sample_rate)


def test_normalizer_rejects_bool_sample_rate_and_duration():
    payload = {
        "characters": ["a"],
        "character_start_times_seconds": [0],
        "character_end_times_seconds": [0.1],
    }
    with pytest.raises(AiVideoError):
        normalize_character_alignment(
            payload, sample_rate_hz=True, duration_samples=48_000
        )
    with pytest.raises(AiVideoError):
        normalize_character_alignment(
            payload, sample_rate_hz=48_000, duration_samples=True
        )


def test_character_alignment_normalizes_unicode_and_seals_sanitized_receipt():
    payload = _load_fixture(WITH_TIMESTAMPS)
    normalized = normalize_character_alignment(
        payload["normalized_alignment"],
        sample_rate_hz=48_000,
        duration_samples=48_000,
        speaker_id="speaker-1",
    )
    assert normalized.unit_kind == "character"
    assert "".join(unit.text for unit in normalized.units) == "Caf\u00e9."
    assert normalized.units[-1].end_sample == 28_800
    assert {unit.speaker_id for unit in normalized.units} == {"speaker-1"}
    assert all(unit.confidence_milli is None for unit in normalized.units)
    assert hashlib.sha256(normalized.receipt_bytes).hexdigest() == (
        normalized.receipt_sha256
    )
    assert b"audio_base64" not in normalized.receipt_bytes
    assert b"xi-api-key" not in normalized.receipt_bytes


def test_character_alignment_merges_cross_element_combining_marks():
    normalized = normalize_character_alignment(
        {
            "characters": ["e", "\u0301"],
            "character_start_times_seconds": [0, 0.1],
            "character_end_times_seconds": [0.1, 0.2],
        },
        sample_rate_hz=48_000,
        duration_samples=48_000,
    )
    assert len(normalized.units) == 1
    assert normalized.units[0].text == "\u00e9"
    assert normalized.units[0].start_sample == 0
    assert normalized.units[0].end_sample == 9_600


def test_character_alignment_rejects_leading_or_ambiguous_combining_marks():
    with pytest.raises(AiVideoError, match="combining"):
        normalize_character_alignment(
            {
                "characters": ["\u0301", "e"],
                "character_start_times_seconds": [0, 0.1],
                "character_end_times_seconds": [0.1, 0.2],
            },
            sample_rate_hz=48_000,
            duration_samples=48_000,
        )
    with pytest.raises(AiVideoError, match="monotonic"):
        normalize_character_alignment(
            {
                "characters": ["e", "\u0301"],
                "character_start_times_seconds": [0, 0.05],
                "character_end_times_seconds": [0.1, 0.2],
            },
            sample_rate_hz=48_000,
            duration_samples=48_000,
        )


def test_character_alignment_rejects_parallel_array_mismatch():
    payload = _load_fixture(WITH_TIMESTAMPS)["normalized_alignment"]
    payload["character_end_times_seconds"].pop()
    with pytest.raises(AiVideoError, match="parallel arrays"):
        normalize_character_alignment(
            payload,
            sample_rate_hz=48_000,
            duration_samples=48_000,
        )


@pytest.mark.parametrize(
    "starts,ends,duration",
    [
        (["NaN"], ["0.1"], 48_000),
        (["0.2"], ["0.1"], 48_000),
        (["-0.1"], ["0.1"], 48_000),
        (["0.9"], ["1.1"], 48_000),
        (["0", "0.1"], ["0.2", "0.3"], 48_000),
    ],
)
def test_character_alignment_fails_closed_on_bad_timing(starts, ends, duration):
    payload = {
        "characters": ["a"] * len(starts),
        "character_start_times_seconds": starts,
        "character_end_times_seconds": ends,
    }
    with pytest.raises(AiVideoError):
        normalize_character_alignment(
            payload,
            sample_rate_hz=48_000,
            duration_samples=duration,
        )


def test_forced_word_alignment_preserves_loss_without_fake_confidence():
    normalized = normalize_word_alignment(
        _load_fixture(FORCED_ALIGNMENT),
        sample_rate_hz=48_000,
        duration_samples=48_000,
        speaker_id="speaker-1",
    )
    assert normalized.unit_kind == "word"
    assert normalized.units[0].text == "Hi"
    assert normalized.units[0].speaker_id == "speaker-1"
    assert normalized.units[0].confidence_milli is None
    receipt = json.loads(normalized.receipt_bytes)
    assert receipt["loss"] == "0.125"
    assert receipt["words"][0]["loss"] == "0.125"


def test_word_alignment_rejects_non_monotonic_and_out_of_duration_bounds():
    payload = _load_fixture(FORCED_ALIGNMENT)
    payload["words"] = [
        {"text": "first", "start": 0, "end": 0.2, "loss": 0.1},
        {"text": "second", "start": 0.1, "end": 0.3, "loss": 0.2},
    ]
    with pytest.raises(AiVideoError, match="monotonic"):
        normalize_word_alignment(
            payload,
            sample_rate_hz=48_000,
            duration_samples=48_000,
        )
    payload["words"] = [{"text": "late", "start": 0.9, "end": 1.1}]
    with pytest.raises(AiVideoError, match="duration"):
        normalize_word_alignment(
            payload,
            sample_rate_hz=48_000,
            duration_samples=48_000,
        )


def test_track_separates_script_transcript_and_optional_word_identity():
    character_track = _track()
    assert character_track.script_hash == hashlib.sha256(
        "Caf\u00e9.".encode("utf-8")
    ).hexdigest()
    assert character_track.transcript_hash == hashlib.sha256(
        "Caf\u00e9.".encode("utf-8")
    ).hexdigest()
    assert character_track.script_hash == character_track.transcript_hash
    assert character_track.segments[0].words is None
    assert character_track.segments[0].speaker_id == "speaker-1"

    alignment = normalize_word_alignment(
        _load_fixture(FORCED_ALIGNMENT),
        sample_rate_hz=48_000,
        duration_samples=48_000,
        speaker_id="speaker-1",
    )
    word_track = segment_caption_track(
        alignment,
        artifact_id="caption-artifact-2",
        revision=1,
        creation_receipt_id="caption-create-2",
        source_provenance=(SourceReference(kind="derived", reference="forced-1"),),
        caption_track_id="caption-track-2",
        language="en",
        script_text="Hi!",
        transcript_text="Hi",
        source_audio_asset_id="voice-asset-1",
        source_audio_sha256=ONE_HASH,
        source_sample_rate_hz=48_000,
        source_duration_samples=48_000,
        segmentation_policy=_policy(),
        alignment_provider="elevenlabs",
        alignment_model=None,
        alignment_receipt_id="forced-1",
    )
    assert word_track.script_hash != word_track.transcript_hash
    assert word_track.segments[0].words[0].end_sample <= (
        word_track.segments[0].end_sample
    )


def test_provider_segments_requires_and_preserves_explicit_boundaries():
    alignment = normalize_character_alignment(
        {
            "characters": ["A", ".", "B", "."],
            "character_start_times_seconds": [0, 0.1, 0.2, 0.3],
            "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4],
        },
        sample_rate_hz=48_000,
        duration_samples=48_000,
    )
    kwargs = dict(
        artifact_id="caption-provider",
        revision=1,
        creation_receipt_id="caption-create-provider",
        source_provenance=(SourceReference(kind="derived", reference="provider"),),
        caption_track_id="caption-provider",
        language="en",
        script_text="A.B.",
        transcript_text="A.B.",
        source_audio_asset_id="voice-asset-1",
        source_audio_sha256=ONE_HASH,
        source_sample_rate_hz=48_000,
        source_duration_samples=48_000,
        segmentation_policy=_policy(strategy="provider_segments"),
        alignment_provider="fixture",
        alignment_model=None,
        alignment_receipt_id="provider",
    )
    with pytest.raises(AiVideoError, match="provider segment boundaries"):
        segment_caption_track(alignment, **kwargs)

    bounded = alignment.model_validate(
        {
            **alignment.model_dump(mode="python"),
            "provider_segment_end_indices": (2, 4),
        }
    )
    track = segment_caption_track(bounded, **kwargs)
    assert [segment.text for segment in track.segments] == ["A.", "B."]
    assert [segment.end_sample for segment in track.segments] == [9_600, 19_200]


def test_sentence_policy_uses_locked_punctuation_and_enforces_limits():
    alignment = normalize_character_alignment(
        {
            "characters": list("Hi. Go!"),
            "character_start_times_seconds": [
                0,
                0.1,
                0.2,
                0.3,
                0.4,
                0.5,
                0.6,
            ],
            "character_end_times_seconds": [
                0.1,
                0.2,
                0.3,
                0.4,
                0.5,
                0.6,
                0.7,
            ],
        },
        sample_rate_hz=48_000,
        duration_samples=48_000,
    )
    common = dict(
        artifact_id="caption-sentence",
        revision=1,
        creation_receipt_id="caption-create-sentence",
        source_provenance=(SourceReference(kind="derived", reference="sentence"),),
        caption_track_id="caption-sentence",
        language="en",
        script_text="Hi. Go!",
        transcript_text="Hi. Go!",
        source_audio_asset_id="voice-asset-1",
        source_audio_sha256=ONE_HASH,
        source_sample_rate_hz=48_000,
        source_duration_samples=48_000,
        alignment_provider="fixture",
        alignment_model=None,
        alignment_receipt_id="sentence",
    )
    track = segment_caption_track(
        alignment,
        segmentation_policy=_policy(
            strategy="sentence", max_characters=4, max_lines=1
        ),
        **common,
    )
    assert [segment.text for segment in track.segments] == ["Hi.", " Go!"]

    with pytest.raises(AiVideoError, match="limits"):
        segment_caption_track(
            alignment,
            segmentation_policy=_policy(
                strategy="sentence", max_characters=3, max_lines=1
            ),
            **common,
        )


def test_word_window_packs_units_and_rejects_unsatisfiable_limits():
    payload = {
        "words": [
            {"text": "one", "start": 0, "end": 0.1},
            {"text": "two", "start": 0.1, "end": 0.2},
            {"text": "x", "start": 0.2, "end": 0.3},
        ],
        "loss": 0.2,
    }
    alignment = normalize_word_alignment(
        payload,
        sample_rate_hz=48_000,
        duration_samples=48_000,
    )
    common = dict(
        artifact_id="caption-window",
        revision=1,
        creation_receipt_id="caption-create-window",
        source_provenance=(SourceReference(kind="derived", reference="window"),),
        caption_track_id="caption-window",
        language="en",
        script_text="one two x",
        transcript_text="one two x",
        source_audio_asset_id="voice-asset-1",
        source_audio_sha256=ONE_HASH,
        source_sample_rate_hz=48_000,
        source_duration_samples=48_000,
        alignment_provider="fixture",
        alignment_model=None,
        alignment_receipt_id="window",
    )
    track = segment_caption_track(
        alignment,
        segmentation_policy=_policy(
            strategy="word_window", max_characters=4, max_lines=2
        ),
        **common,
    )
    assert [segment.text for segment in track.segments] == ["one two", "x"]
    assert [word.text for word in track.segments[0].words] == ["one", "two"]

    with pytest.raises(AiVideoError, match="limits"):
        segment_caption_track(
            alignment,
            segmentation_policy=_policy(
                strategy="word_window", max_characters=2, max_lines=1
            ),
            **common,
        )


def test_policy_version_changes_timing_fingerprint_but_style_does_not():
    plain = _track(policy_version="1", style_reference_id=None)
    styled = _track(policy_version="1", style_reference_id="style-1")
    revised = _track(policy_version="2", style_reference_id=None)
    assert plain.timing_fingerprint == caption_timing_fingerprint(plain)
    assert styled.timing_fingerprint == plain.timing_fingerprint
    assert revised.timing_fingerprint != plain.timing_fingerprint


def test_caption_style_fingerprint_covers_reference_and_consumed_schema():
    style_bytes = b'{"font_family":"Fixture Sans","schema_version":"1"}'
    style_hash = hashlib.sha256(style_bytes).hexdigest()
    reference = CaptionStyleReference(
        artifact_id="style-1",
        revision=1,
        content_hash=style_hash,
        path=Path(f"assets/styles/{style_hash}.json"),
    )
    fingerprint = caption_style_fingerprint(reference, style_bytes)
    assert fingerprint != caption_style_fingerprint(
        reference.model_copy(update={"artifact_id": "style-2"}), style_bytes
    )
    with pytest.raises(AiVideoError, match="hash"):
        caption_style_fingerprint(reference, b"{}")


def test_provider_free_caption_import_seals_bytes_without_active_state_write(tmp_path):
    active = tmp_path / "manifest.json"
    active.write_text("unchanged", encoding="utf-8")
    track = _track(style_reference_id="style-1")
    style_bytes = b'{"font_family":"Fixture Sans","schema_version":"1"}'
    style_hash = hashlib.sha256(style_bytes).hexdigest()
    style = CaptionStyleReference(
        artifact_id="style-1",
        revision=1,
        content_hash=style_hash,
        path=Path(f"assets/styles/{style_hash}.json"),
    )
    request = CaptionImportRequest.create(
        caption_track=track,
        style_reference=style,
        style_bytes=style_bytes,
    )
    prepared = request.prepare()
    assert prepared.caption_track == track
    assert hashlib.sha256(prepared.track_bytes).hexdigest() == prepared.track_sha256
    assert prepared.style_bytes == style_bytes
    assert prepared.style_sha256 == style_hash
    assert active.read_text(encoding="utf-8") == "unchanged"
    assert list(tmp_path.iterdir()) == [active]

    with pytest.raises(ValidationError, match="style"):
        CaptionImportRequest.model_validate(
            {**request.model_dump(mode="python"), "style_bytes": b"{}"}
        )
