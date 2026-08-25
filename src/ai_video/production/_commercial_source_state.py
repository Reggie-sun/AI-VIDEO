from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel


class CommercialSourceLifecycle(str, Enum):
    REQUESTED = "requested"
    MATERIALIZED_CANDIDATE = "materialized_candidate"
    EVIDENCED = "evidenced"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_EVALUATED = "not_evaluated"
    STALE = "stale"
    OUTCOME_UNKNOWN = "outcome_unknown"


class CommercialSourceApprovalPointer(StrictModel):
    path: Path
    approval_id: str = Field(min_length=1)
    target_shot_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _canonical_pointer(self) -> "CommercialSourceApprovalPointer":
        expected = Path(f"state/commercial-source/approval.{self.content_hash}.json")
        if self.path != expected:
            raise ValueError("commercial source approval pointer path must be canonical")
        return self


class _CommercialSourceAttempt(Protocol):
    lifecycle: CommercialSourceLifecycle
    candidate_asset_id: str | None
    candidate_sha256: str | None
    candidate_record_hash: str | None
    review_intent_hash: str | None
    review_phase: str | None
    review_evidence_hash: str | None
    review_receipt_hash: str | None
    active_approval: object | None


def validate_commercial_source_attempt_state(
    attempt: _CommercialSourceAttempt,
) -> None:
    candidate_identity = (
        attempt.candidate_asset_id,
        attempt.candidate_sha256,
        attempt.candidate_record_hash,
    )
    has_candidate = all(item is not None for item in candidate_identity)
    if any(item is not None for item in candidate_identity) != has_candidate:
        raise ValueError("Commercial source candidate identity must be all-or-none")
    if attempt.lifecycle not in {
        CommercialSourceLifecycle.REQUESTED,
        CommercialSourceLifecycle.STALE,
    } and not has_candidate:
        raise ValueError("Commercial source lifecycle requires candidate identity")
    if (attempt.review_intent_hash is None) != (attempt.review_phase is None):
        raise ValueError(
            "Commercial source review intent identity and phase must be all-or-none"
        )
    has_review_result = (
        attempt.review_evidence_hash is not None
        and attempt.review_receipt_hash is not None
    )
    if (attempt.review_evidence_hash is None) != (
        attempt.review_receipt_hash is None
    ):
        raise ValueError(
            "Commercial source review evidence and receipt must be all-or-none"
        )
    reviewed_lifecycles = {
        CommercialSourceLifecycle.EVIDENCED,
        CommercialSourceLifecycle.REJECTED,
        CommercialSourceLifecycle.NOT_EVALUATED,
        CommercialSourceLifecycle.APPROVED,
    }
    if attempt.lifecycle in reviewed_lifecycles and (
        attempt.review_phase != "activate" or not has_review_result
    ):
        raise ValueError(
            "Commercial source reviewed lifecycle requires activated evidence"
        )
    if (
        attempt.review_phase == "activate"
        and attempt.lifecycle is not CommercialSourceLifecycle.STALE
        and attempt.lifecycle not in reviewed_lifecycles
    ):
        raise ValueError("Activated commercial review requires a reviewed lifecycle")
    if attempt.lifecycle is CommercialSourceLifecycle.APPROVED:
        if attempt.active_approval is None or attempt.review_receipt_hash is None:
            raise ValueError("Approved commercial source requires receipt and pointer")
    elif attempt.active_approval is not None:
        raise ValueError("Only approved commercial source lifecycle selects an approval")


class CommercialSourceAttemptState(StrictModel):
    attempt_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_path: Path
    target_shot_id: str = Field(min_length=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_reference_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    lifecycle: CommercialSourceLifecycle
    candidate_asset_id: str | None = Field(default=None, min_length=1)
    candidate_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    candidate_record_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_intent_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_phase: Literal["requested", "evidence", "activate"] | None = None
    review_evidence_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_receipt_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    active_approval: CommercialSourceApprovalPointer | None = None

    @model_validator(mode="after")
    def _validate_lifecycle_fields(self) -> "CommercialSourceAttemptState":
        validate_commercial_source_attempt_state(self)
        return self


class CommercialSourceDependencyEvidence(StrictModel):
    owner: Literal["commercial_source_approval"]
    pointer: CommercialSourceApprovalPointer
    artifact_id: str = Field(min_length=1)
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


def reject_explicit_commercial_source_fields(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    fields = {
        "active_commercial_source_approvals",
        "commercial_source_attempts",
    }
    manifest_version = value.get("schema_version", "2.0")
    if manifest_version not in {"2.12", "2.13"} and fields.intersection(value):
        raise ValueError(
            f"Production Manifest {manifest_version} cannot contain commercial source state"
        )
    return value


def validate_commercial_source_manifest(manifest: Any) -> None:
    attempt_ids = [item.attempt_id for item in manifest.commercial_source_attempts]
    if len(attempt_ids) != len(set(attempt_ids)):
        raise ValueError("Commercial source attempt IDs must be unique")
    approvals = manifest.active_commercial_source_approvals
    shot_ids = [item.target_shot_id for item in approvals]
    if len(shot_ids) != len(set(shot_ids)):
        raise ValueError("Active commercial source approvals must be unique per Shot")
    if approvals != tuple(sorted(approvals, key=lambda item: item.target_shot_id)):
        raise ValueError("Active commercial source approvals must be ordered by Shot")


def serialize_commercial_source_manifest(
    data: dict[str, object], schema_version: str
) -> None:
    if schema_version not in {"2.12", "2.13"}:
        data.pop("active_commercial_source_approvals", None)
        data.pop("commercial_source_attempts", None)
