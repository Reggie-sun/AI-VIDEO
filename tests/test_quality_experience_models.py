"""T1 strict TDD tests for QualityExperienceRecord v1 Q0 models.

Covers the minimum Q0 contract:
- strict / frozen / no-extra Pydantic v2 configuration
- schema_version 1.0 + record_kind prospective_q0_attempt
- prospective success / known failure / outcome-unknown / repair-new-attempt fixtures
- deterministic AttemptIdentityKey (domain-separated SHA-256)
- ManifestObservation / attempt_sequence derivation references
- tagged EvidenceValue (known | unknown | incomplete | not_applicable)
- bounded NFC free text + defense-in-depth denylist
- canonical sorted unique named parameters and rubric items
- distinct outcome variants with no fabrication
- backward-only predecessor pointer
- required prospective identity that cannot be unknown
- sanitized representation / error text (no rejected value leakage)

These tests assert behavior; they do not exercise IO, the store, cohort/roster
construction, dataset aggregation, or RAG projection (covered by later
T-segments).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.quality_intelligence.models import (
    AttemptIdentityKey,
    AttemptKind,
    CanonicalRuntimeBoundary,
    QualityExperienceRecordV1,
    QualityRecordPointer,
    RecordKind,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "quality_experience" / "v1"
HEX64_BODY = r"[0-9a-f]{64}"


def _load(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Strict / frozen / no-extra Pydantic config (and implicit schema / kind
# constraints — each model_validate path validates Literal["1.0"] /
# Literal["prospective_q0_attempt"] / CanonicalRuntimeBoundary / AttemptKind
# because the fixtures use those values and rejection tests mutate them).
# ---------------------------------------------------------------------------


def test_record_is_frozen_blocks_mutation() -> None:
    record = QualityExperienceRecordV1.model_validate(_load("prospective_success.json"))
    with pytest.raises((TypeError, AttributeError, ValueError)):
        record.experiment_id = "tampered"  # type: ignore[misc]


def test_record_rejects_extra_fields() -> None:
    bad = dict(_load("prospective_success.json"))
    bad["rogue_field"] = "must-be-rejected"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_record_enforces_schema_version_one_dot_zero() -> None:
    bad = dict(_load("prospective_success.json"))
    bad["schema_version"] = "0.9"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_record_enforces_record_kind_literal() -> None:
    bad = dict(_load("prospective_success.json"))
    bad["record_kind"] = "retrospective"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


@pytest.mark.parametrize(
    "section",
    (
        "planning",
        "routing",
        "prompt",
        "parameters",
        "inputs",
        "continuity",
        "artifact_evidence",
        "durability",
        "analyzer",
        "human_review",
        "intervention",
        "outcome_boundary",
    ),
)
def test_prospective_record_requires_every_exact_binding_section(section: str) -> None:
    payload = _load("prospective_success.json")
    payload.pop(section, None)
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


@pytest.mark.parametrize(
    ("section", "field"),
    (
        ("parameters", "sources"),
        ("artifact_evidence", "ffprobe_hash"),
        ("artifact_evidence", "video_probe_receipt_id"),
        ("artifact_evidence", "provenance_receipt_id"),
    ),
)
def test_prospective_record_requires_exact_parameter_and_probe_identity(
    section: str, field: str
) -> None:
    payload = _load("prospective_success.json")
    payload[section].pop(field)
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


def test_prospective_record_requires_typed_analyzer_measurements() -> None:
    payload = _load("prospective_success.json")
    payload["analyzer"]["evidence"][0].pop("measurements")
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


@pytest.mark.parametrize("invalid_ratio", ("not_a_ratio", 1.5, -0.1))
def test_analyzer_ratios_are_strict_and_bounded(invalid_ratio: object) -> None:
    payload = _load("prospective_success.json")
    black_ratio = next(
        item
        for item in payload["analyzer"]["evidence"][0]["measurements"]["parameters"]
        if item["key"] == "black_ratio"
    )
    black_ratio["value"]["value"] = invalid_ratio
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


def test_exact_terminal_continuity_requires_exact_frame_evidence() -> None:
    payload = _load("prospective_success.json")
    payload["continuity"]["mode"] = "exact_terminal"
    payload["continuity"]["source_shot_id"] = {
        "state": "known",
        "value": "shot_000",
        "source_document": "state/project.yaml",
        "source_span": "shots.0.id",
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


def test_failed_attempt_without_artifact_cannot_claim_human_go() -> None:
    failure = _load("prospective_failure.json")
    failure["human_review"] = _load("prospective_success.json")["human_review"]
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(failure)


def test_outcome_and_durability_boundaries_cannot_contradict() -> None:
    payload = _load("prospective_success.json")
    payload["durability"]["activation_state"] = "candidate"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


def test_workflow_identity_cannot_mix_known_and_not_applicable() -> None:
    payload = _load("prospective_success.json")
    payload["provider"]["workflow_path"] = {
        "state": "not_applicable",
        "reason": "contradictory",
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


def test_none_continuity_cannot_carry_source_identity() -> None:
    payload = _load("prospective_success.json")
    payload["continuity"]["source_shot_id"] = {
        "state": "known",
        "value": "shot_000",
        "source_document": "state/project.yaml",
        "source_span": "shots.0.id",
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


# ---------------------------------------------------------------------------
# Prospective success / known failure / outcome_unknown round-trip
# ---------------------------------------------------------------------------


def test_prospective_success_round_trip() -> None:
    record = QualityExperienceRecordV1.model_validate(_load("prospective_success.json"))
    assert record.schema_version == "1.0"
    assert record.canonical_runtime_boundary == CanonicalRuntimeBoundary.PRODUCTION_MANIFEST
    assert record.identity.attempt_id == "attempt_001"
    assert record.identity.generation_id == "gen_001"
    assert record.lineage.attempt_kind == AttemptKind.INITIAL
    assert record.lineage.attempt_sequence == 1
    assert record.lineage.predecessor is None
    assert record.outcome.variant == "succeeded"
    assert record.artifact_evidence.asset_id == "asset_render_001"


def test_known_failure_round_trip() -> None:
    record = QualityExperienceRecordV1.model_validate(_load("prospective_failure.json"))
    assert record.outcome.variant == "known_failure"
    # Failure must not fabricate an artifact pointer.
    assert not hasattr(record.outcome, "artifact_pointer") or record.outcome.artifact_pointer is None
    assert record.outcome.error_code
    assert record.human_review.status.value == "NOT_REVIEWED"


def test_outcome_unknown_round_trip() -> None:
    record = QualityExperienceRecordV1.model_validate(_load("outcome_unknown.json"))
    assert record.outcome.variant == "outcome_unknown"
    # Must be distinct from failure or success.
    assert record.outcome.variant not in ("known_failure", "succeeded")


def test_outcome_unknown_not_constructible_as_failure() -> None:
    record = QualityExperienceRecordV1.model_validate(_load("outcome_unknown.json"))
    with pytest.raises((TypeError, AttributeError, ValueError)):
        record.outcome.variant = "known_failure"  # type: ignore[misc]


def test_outcome_failure_distinct_from_unknown() -> None:
    fail = QualityExperienceRecordV1.model_validate(_load("prospective_failure.json"))
    unknown = QualityExperienceRecordV1.model_validate(_load("outcome_unknown.json"))
    assert fail.outcome.variant == "known_failure"
    assert unknown.outcome.variant == "outcome_unknown"


def test_outcome_succeeded_must_have_terminal_boundary() -> None:
    from ai_video.quality_intelligence.models import OutcomeSucceeded
    with pytest.raises(ValidationError):
        OutcomeSucceeded.model_validate({"variant": "succeeded"})


# ---------------------------------------------------------------------------
# Repair / new-attempt lineage
# ---------------------------------------------------------------------------


def test_repair_attempt_distinct_id_higher_sequence_with_backward_predecessor() -> None:
    failure = QualityExperienceRecordV1.model_validate(_load("prospective_failure.json"))
    payload = json.loads(json.dumps(_load("prospective_success.json")))
    payload["identity"] = dict(payload["identity"])
    payload["identity"]["attempt_id"] = "attempt_002"
    payload["lineage"] = {
        "attempt_sequence": failure.lineage.attempt_sequence + 1,
        "attempt_kind": "repair",
        "predecessor": {
            "record_kind": "prospective_q0_attempt",
            "schema_version": "1.0",
            "relative_path": "records/sha256/ab/" + "0" * 64 + ".json",
            "content_hash": "0" * 64,
            "file_sha256": "1" * 64,
            "recorded_sequence": failure.lineage.attempt_sequence,
            "recorded_attempt_id": failure.identity.attempt_id,
        },
    }
    payload["outcome"] = {
        "variant": "succeeded",
        "terminal_boundary": "activated",
        "observed_at": "2026-08-21T12:01:00Z",
    }
    payload["artifact_evidence"]["asset_id"] = "asset_repair_001"
    payload["artifact_evidence"]["relative_path"] = "shots/shot_001/render_retry.mp4"
    payload["artifact_evidence"]["file_sha256"] = "3" * 64
    payload["analyzer"]["evidence"][0]["subject_id"] = "asset_repair_001"
    repair = QualityExperienceRecordV1.model_validate(payload)
    assert repair.lineage.attempt_kind == AttemptKind.REPAIR
    assert repair.lineage.attempt_sequence == failure.lineage.attempt_sequence + 1
    assert repair.identity.attempt_id != failure.identity.attempt_id
    assert repair.lineage.predecessor is not None
    assert repair.lineage.predecessor.recorded_sequence < repair.lineage.attempt_sequence


def test_predecessor_forward_sequence_rejected() -> None:
    payload = dict(_load("prospective_success.json"))
    payload["lineage"] = {
        "attempt_sequence": 1,
        "attempt_kind": "retry",
        "predecessor": {
            "record_kind": "prospective_q0_attempt",
            "schema_version": "1.0",
            "relative_path": "records/sha256/ab/" + "0" * 64 + ".json",
            "content_hash": "0" * 64,
            "file_sha256": "1" * 64,
            "recorded_sequence": 5,  # forward!
            "recorded_attempt_id": "future_attempt",
        },
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


def test_predecessor_equal_sequence_rejected() -> None:
    payload = dict(_load("prospective_success.json"))
    payload["lineage"] = {
        "attempt_sequence": 3,
        "attempt_kind": "retry",
        "predecessor": {
            "record_kind": "prospective_q0_attempt",
            "schema_version": "1.0",
            "relative_path": "records/sha256/ab/" + "0" * 64 + ".json",
            "content_hash": "0" * 64,
            "file_sha256": "1" * 64,
            "recorded_sequence": 3,
            "recorded_attempt_id": "self",
        },
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(payload)


# ---------------------------------------------------------------------------
# AttemptIdentityKey determinism
# ---------------------------------------------------------------------------


def test_attempt_identity_key_is_deterministic() -> None:
    key_a = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    key_b = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    assert key_a == key_b
    assert key_a.identity_hash == key_b.identity_hash


def test_attempt_identity_key_hash_is_hex64() -> None:
    key = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    assert re.fullmatch(HEX64_BODY, key.identity_hash)


def test_attempt_identity_key_distinguishes_runtime_boundary() -> None:
    base = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    lab = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="lab_only",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    assert base.identity_hash != lab.identity_hash


def test_attempt_identity_key_rejects_forged_component_hash() -> None:
    with pytest.raises(ValidationError):
        AttemptIdentityKey(
            canonical_runtime_boundary="production_manifest",
            project_id="project_001",
            attempt_id="attempt_001",
            generation_id="generation_001",
            identity_hash="0" * 64,
        )


def test_attempt_identity_key_distinguishes_attempt_id() -> None:
    a = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    b = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_002",
        generation_id="gen_001",
    )
    assert a.identity_hash != b.identity_hash


def test_attempt_identity_key_distinguishes_project_id() -> None:
    a = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    b = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_002",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    assert a.identity_hash != b.identity_hash


def test_attempt_identity_key_distinguishes_generation_id() -> None:
    a = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_001",
    )
    b = AttemptIdentityKey.from_components(
        canonical_runtime_boundary="production_manifest",
        project_id="proj_001",
        attempt_id="attempt_001",
        generation_id="gen_002",
    )
    assert a.identity_hash != b.identity_hash


# ---------------------------------------------------------------------------
# Required prospective identity cannot be unknown
# ---------------------------------------------------------------------------


def test_required_identity_hash_pattern_enforced() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["identity"]["project_artifact_content_hash"] = "not-a-hash"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_required_identity_attempt_id_must_be_present() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["identity"].pop("attempt_id")
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_required_identity_revision_must_be_positive() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["identity"]["project_artifact_revision"] = 0
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_identity_cannot_be_silently_dropped_to_none() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["identity"]["shot_content_hash"] = None
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


# ---------------------------------------------------------------------------
# Tagged EvidenceValue behavior
# ---------------------------------------------------------------------------


def test_provider_workflow_fingerprint_not_applicable_accepted() -> None:
    payload = _load("prospective_success.json")
    modified = json.loads(json.dumps(payload))
    modified["provider"]["workflow_id"] = {
        "state": "not_applicable",
        "reason": "provider_does_not_use_workflow_files",
    }
    modified["provider"]["workflow_version"] = {
        "state": "not_applicable",
        "reason": "provider_does_not_use_workflow_files",
    }
    modified["provider"]["workflow_path"] = {
        "state": "not_applicable",
        "reason": "provider_does_not_use_workflow_files",
    }
    modified["provider"]["workflow_fingerprint"] = {
        "state": "not_applicable",
        "reason": "provider_does_not_use_workflow_files",
    }
    record = QualityExperienceRecordV1.model_validate(modified)
    assert record.provider.workflow_fingerprint.state == "not_applicable"


def test_provider_workflow_fingerprint_known_requires_hex64_value() -> None:
    payload = _load("prospective_success.json")
    modified = json.loads(json.dumps(payload))
    modified["provider"]["workflow_fingerprint"] = {
        "state": "known",
        "value": "not-hex",
        "source_document": "wf.json",
        "source_span": "id",
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(modified)


def test_prospective_provider_workflow_fingerprint_cannot_be_incomplete() -> None:
    payload = _load("prospective_success.json")
    modified = json.loads(json.dumps(payload))
    modified["provider"]["workflow_fingerprint"] = {
        "state": "incomplete",
        "missing_fields": ["workflow_sha256"],
        "source_span": "wf.json",
    }
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(modified)


def test_provider_workflow_fingerprint_unknown_requires_reason() -> None:
    from ai_video.quality_intelligence.models import EvidenceHex64
    with pytest.raises(ValidationError):
        EvidenceHex64.model_validate({"state": "unknown"})


def test_tagged_evidence_rejects_contradictory_unknown_value() -> None:
    from ai_video.quality_intelligence.models import EvidenceHex64

    with pytest.raises(ValidationError):
        EvidenceHex64.model_validate(
            {"state": "unknown", "reason": "not_observed", "value": "a" * 64}
        )


def test_tagged_evidence_rejects_sensitive_source_span() -> None:
    from ai_video.quality_intelligence.models import EvidenceString

    with pytest.raises(ValidationError) as exc_info:
        EvidenceString.model_validate(
            {
                "state": "known",
                "value": "model_x",
                "source_document": "registry.json",
                "source_span": "https://signed.example/?token=raw-secret",
            }
        )
    assert "raw-secret" not in str(exc_info.value)


@pytest.mark.parametrize(
    "payload",
    (
        {"state": "unknown", "reason": "not_observed", "value": "leaked"},
        {
            "state": "not_applicable",
            "reason": "not_relevant",
            "source_document": "records/source.md",
        },
        {
            "state": "known",
            "value": "exact",
            "reason": "contradictory",
            "source_document": "records/source.md",
            "source_span": "fields.value",
        },
    ),
)
def test_historical_evidence_variants_are_mutually_exclusive(payload: dict) -> None:
    from ai_video.quality_intelligence.models import HistoricalEvidence

    with pytest.raises(ValidationError):
        HistoricalEvidence.model_validate(payload)


# ---------------------------------------------------------------------------
# BoundedFreeText denylist
# ---------------------------------------------------------------------------


def test_free_text_nfc_normalized() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    decomposed = "e\u0301"  # NFD "e + combining acute"
    text = BoundedFreeText.model_validate({"value": decomposed})
    assert text.value == "\u00e9"


def test_free_text_rejects_control_char() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "hello\x00world"})


def test_free_text_rejects_url() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "see https://internal.example.com/foo"})


def test_free_text_rejects_http_header_marker() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "Authorization: Bearer xyz"})


def test_free_text_rejects_cookie_marker() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "Cookie: session=abcdef"})


def test_free_text_rejects_secret_assignment() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "api_key=abcdef1234567890"})


def test_free_text_rejects_aws_access_key_marker() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "key AKIAIOSFODNN7EXAMPLE leaked"})


def test_free_text_rejects_prompt_envelope() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "[prompt begin] cat in a hat [prompt end]"})


def test_free_text_rejects_response_envelope() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "[response begin] some text [response end]"})


def test_free_text_rejects_private_key_block() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "-----BEGIN RSA PRIVATE KEY-----"})


@pytest.mark.parametrize("private_path", ("/home/person/private.json", "C:\\Users\\person\\secret.txt"))
def test_free_text_rejects_absolute_private_path(private_path: str) -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText

    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": private_path})


def test_free_text_rejects_signed_url_signature() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate(
            {"value": "https://x.example/?Signature=abcdef1234567890abcdef"}
        )


def test_free_text_rejects_email() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "contact me at alice@example.com"})


def test_free_text_enforces_length_cap() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": "x" * 4096})


def test_free_text_rejects_empty_value() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    with pytest.raises(ValidationError):
        BoundedFreeText.model_validate({"value": ""})


def test_free_text_accepts_clean_chinese_text() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    text = BoundedFreeText.model_validate({"value": "实验目的：记录 Q0 行为"})
    assert text.value == "实验目的：记录 Q0 行为"


def test_free_text_accepts_plain_ascii_text() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    text = BoundedFreeText.model_validate({"value": "no intervention applied"})
    assert text.value == "no intervention applied"


def test_free_text_error_does_not_leak_rejected_secret_value() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    secret = "AKIAIOSFODNN7EXAMPLE"
    with pytest.raises(ValidationError) as excinfo:
        BoundedFreeText.model_validate({"value": secret})
    rendered = str(excinfo.value)
    assert secret not in rendered


def test_free_text_error_does_not_leak_rejected_url() -> None:
    from ai_video.quality_intelligence.models import BoundedFreeText
    url = "https://internal.example.com/secret/path"
    with pytest.raises(ValidationError) as excinfo:
        BoundedFreeText.model_validate({"value": url})
    rendered = str(excinfo.value)
    assert url not in rendered


# ---------------------------------------------------------------------------
# Canonical sorted unique named parameters / rubric items
# ---------------------------------------------------------------------------


def test_named_parameters_reject_duplicate_keys() -> None:
    from ai_video.quality_intelligence.models import NamedParameters
    with pytest.raises(ValidationError):
        NamedParameters.model_validate(
            {
                "parameters": [
                    {
                        "key": "seed",
                        "value": {
                            "state": "known",
                            "value": 1,
                            "source_document": "m",
                            "source_span": "s",
                        },
                    },
                    {
                        "key": "seed",
                        "value": {
                            "state": "known",
                            "value": 2,
                            "source_document": "m",
                            "source_span": "s",
                        },
                    },
                ]
            }
        )


def test_named_parameters_reject_unsorted_order() -> None:
    from ai_video.quality_intelligence.models import NamedParameters
    with pytest.raises(ValidationError):
        NamedParameters.model_validate(
            {
                "parameters": [
                    {
                        "key": "zeta",
                        "value": {
                            "state": "known",
                            "value": 1,
                            "source_document": "m",
                            "source_span": "s",
                        },
                    },
                    {
                        "key": "alpha",
                        "value": {
                            "state": "known",
                            "value": 2,
                            "source_document": "m",
                            "source_span": "s",
                        },
                    },
                ]
            }
        )


def test_named_parameters_accept_sorted_unique_keys() -> None:
    from ai_video.quality_intelligence.models import NamedParameters
    params = NamedParameters.model_validate(
        {
            "parameters": [
                {
                    "key": "alpha",
                    "value": {
                        "state": "known",
                        "value": 1,
                        "source_document": "m",
                        "source_span": "s",
                    },
                },
                {
                    "key": "zeta",
                    "value": {
                        "state": "known",
                        "value": 2,
                        "source_document": "m",
                        "source_span": "s",
                    },
                },
            ]
        }
    )
    assert [p.key for p in params.parameters] == ["alpha", "zeta"]


def test_rubric_items_reject_duplicate_item_ids() -> None:
    from ai_video.quality_intelligence.models import RubricItems
    with pytest.raises(ValidationError):
        RubricItems.model_validate(
            {
                "items": [
                    {"item_id": "composition", "verdict": "pass", "concerns": []},
                    {"item_id": "composition", "verdict": "fail", "concerns": []},
                ]
            }
        )


def test_rubric_items_reject_unsorted_order() -> None:
    from ai_video.quality_intelligence.models import RubricItems
    with pytest.raises(ValidationError):
        RubricItems.model_validate(
            {
                "items": [
                    {"item_id": "zeta", "verdict": "pass", "concerns": []},
                    {"item_id": "alpha", "verdict": "pass", "concerns": []},
                ]
            }
        )


def test_rubric_items_accept_sorted_unique() -> None:
    from ai_video.quality_intelligence.models import RubricItems
    items = RubricItems.model_validate(
        {
            "items": [
                {"item_id": "alpha", "verdict": "pass", "concerns": []},
                {"item_id": "zeta", "verdict": "fail", "concerns": []},
            ]
        }
    )
    assert [i.item_id for i in items.items] == ["alpha", "zeta"]


# ---------------------------------------------------------------------------
# QualityRecordPointer path / hash constraints
# ---------------------------------------------------------------------------


def test_quality_record_pointer_requires_hex64_content_hash() -> None:
    with pytest.raises(ValidationError):
        QualityRecordPointer.model_validate(
            {
                "record_kind": "prospective_q0_attempt",
                "schema_version": "1.0",
                "relative_path": "records/sha256/ab/" + "0" * 64 + ".json",
                "content_hash": "not-hex",
                "file_sha256": "1" * 64,
                "recorded_sequence": 1,
                "recorded_attempt_id": "a1",
            }
        )


def test_quality_record_pointer_rejects_absolute_path() -> None:
    with pytest.raises(ValidationError):
        QualityRecordPointer.model_validate(
            {
                "record_kind": "prospective_q0_attempt",
                "schema_version": "1.0",
                "relative_path": "/absolute/path/file.json",
                "content_hash": "0" * 64,
                "file_sha256": "1" * 64,
                "recorded_sequence": 1,
                "recorded_attempt_id": "a1",
            }
        )


def test_quality_record_pointer_rejects_path_traversal() -> None:
    with pytest.raises(ValidationError):
        QualityRecordPointer.model_validate(
            {
                "record_kind": "prospective_q0_attempt",
                "schema_version": "1.0",
                "relative_path": "../outside/file.json",
                "content_hash": "0" * 64,
                "file_sha256": "1" * 64,
                "recorded_sequence": 1,
                "recorded_attempt_id": "a1",
            }
        )


def test_quality_record_pointer_rejects_sequence_zero() -> None:
    with pytest.raises(ValidationError):
        QualityRecordPointer.model_validate(
            {
                "record_kind": "prospective_q0_attempt",
                "schema_version": "1.0",
                "relative_path": "records/sha256/ab/" + "0" * 64 + ".json",
                "content_hash": "0" * 64,
                "file_sha256": "1" * 64,
                "recorded_sequence": 0,
                "recorded_attempt_id": "a1",
            }
        )


def test_quality_record_pointer_accepts_clean_relative_path() -> None:
    ptr = QualityRecordPointer.model_validate(
        {
            "record_kind": "prospective_q0_attempt",
            "schema_version": "1.0",
            "relative_path": "records/sha256/ab/" + "0" * 64 + ".json",
            "content_hash": "0" * 64,
            "file_sha256": "1" * 64,
            "recorded_sequence": 1,
            "recorded_attempt_id": "a1",
        }
    )
    assert ptr.record_kind == "prospective_q0_attempt"
    assert ptr.schema_version == "1.0"


# ---------------------------------------------------------------------------
# Identity path / hash integrity (full record)
# ---------------------------------------------------------------------------


def test_record_rejects_manifest_observation_non_hex() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["identity"]["manifest_observation_file_hash"] = "ZZZZZ"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_record_rejects_registry_observation_non_hex() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["identity"]["registry_observation_file_hash"] = "not-hex"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_record_rejects_bad_captured_at_timestamp() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad["captured_at"] = "2026-08-21 12:00:00"
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)


def test_record_rejects_missing_capture_actor() -> None:
    payload = _load("prospective_success.json")
    bad = json.loads(json.dumps(payload))
    bad.pop("capture_actor")
    with pytest.raises(ValidationError):
        QualityExperienceRecordV1.model_validate(bad)
