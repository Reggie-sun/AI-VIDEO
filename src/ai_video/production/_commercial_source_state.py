from __future__ import annotations

from enum import Enum
from typing import Protocol


class _CommercialSourceAttempt(Protocol):
    lifecycle: Enum
    candidate_asset_id: str | None
    candidate_sha256: str | None
    candidate_record_hash: str | None
    review_intent_hash: str | None
    review_phase: Enum | None
    review_evidence_hash: str | None
    review_receipt_hash: str | None
    active_approval: object | None


def validate_commercial_source_attempt_state(
    attempt: _CommercialSourceAttempt,
) -> None:
    lifecycle = attempt.lifecycle.value
    candidate_identity = (
        attempt.candidate_asset_id,
        attempt.candidate_sha256,
        attempt.candidate_record_hash,
    )
    has_candidate = all(item is not None for item in candidate_identity)
    if any(item is not None for item in candidate_identity) != has_candidate:
        raise ValueError("Commercial source candidate identity must be all-or-none")
    if lifecycle not in {"requested", "stale"} and not has_candidate:
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
    reviewed_lifecycles = {"evidenced", "rejected", "not_evaluated", "approved"}
    review_phase = (
        attempt.review_phase.value if attempt.review_phase is not None else None
    )
    if lifecycle in reviewed_lifecycles and (
        review_phase != "activate" or not has_review_result
    ):
        raise ValueError(
            "Commercial source reviewed lifecycle requires activated evidence"
        )
    if (
        review_phase == "activate"
        and lifecycle != "stale"
        and lifecycle not in reviewed_lifecycles
    ):
        raise ValueError("Activated commercial review requires a reviewed lifecycle")
    if lifecycle == "approved":
        if attempt.active_approval is None or attempt.review_receipt_hash is None:
            raise ValueError("Approved commercial source requires receipt and pointer")
    elif attempt.active_approval is not None:
        raise ValueError("Only approved commercial source lifecycle selects an approval")
