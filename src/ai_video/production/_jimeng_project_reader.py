"""Read-only lineage verification for a reconciled Jimeng paid task."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.jimeng_contracts import (
    JimengCanvasSnapshot, JimengDispatchIntent, canvas_snapshot_path, dispatch_path,
)
from ai_video.production.paid_provider import (
    BudgetReservationStatus, PaidProviderBudgetSnapshot, PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt, reconcile_jimeng_unknown_as_accepted,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow, canonical_paid_provider_submit_path,
    resolve_contained_path,
)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(code=ErrorCode.PRODUCTION_PROJECT_INVALID,
                        user_message=message, retryable=False)


def _dispatch_for_attempt(root: Path, attempt_id: str) -> JimengDispatchIntent:
    directory = root / "artifacts/provider-dispatch/jimeng"
    try:
        matches = []
        for path in sorted(directory.iterdir()):
            if path.suffix != ".json":
                raise _invalid("Jimeng dispatch directory contains an unexpected entry.")
            raw = _read_regular_file_nofollow(path, contained_by=directory)
            item = JimengDispatchIntent.model_validate_json(raw.data)
            expected = resolve_contained_path(root, dispatch_path(item.content_hash),
                allowed_root=directory)
            if path != expected:
                raise _invalid("Jimeng dispatch path differs from its content hash.")
            if item.attempt_id == attempt_id:
                matches.append(item)
    except (AiVideoError, OSError, ValueError) as exc:
        raise _invalid("Jimeng dispatch evidence cannot be reopened.") from exc
    if len(matches) != 1:
        raise _invalid("Jimeng dispatch identity is missing or ambiguous.")
    return matches[0]


def _canvas_for_attempt(root: Path, attempt_id: str) -> JimengCanvasSnapshot:
    directory = root / "artifacts/provider-canvas/jimeng"
    try:
        matches = []
        for path in sorted(directory.iterdir()):
            if path.suffix != ".json":
                raise _invalid("Jimeng canvas snapshot directory has an unexpected entry.")
            raw = _read_regular_file_nofollow(path, contained_by=directory)
            item = JimengCanvasSnapshot.model_validate_json(raw.data)
            expected = resolve_contained_path(root, canvas_snapshot_path(item.content_hash),
                allowed_root=directory)
            if path != expected:
                raise _invalid("Jimeng canvas snapshot path differs from its content hash.")
            if item.attempt_id == attempt_id:
                matches.append(item)
    except (AiVideoError, OSError, ValueError) as exc:
        raise _invalid("Jimeng saved canvas snapshot cannot be reopened.") from exc
    if len(matches) != 1:
        raise _invalid("Jimeng saved canvas snapshot is missing or ambiguous.")
    return matches[0]


def verify_jimeng_task_lineage(
    *, root: Path, attempt_id: str,
    submit: PaidProviderSubmitReceipt, active_budget: PaidProviderBudgetSnapshot,
    load_budget_by_hash: Callable[[str], PaidProviderBudgetSnapshot],
) -> None:
    """Reopen dispatch for every accepted task; recoveries also reopen prior state."""

    proof = submit.jimeng_accepted_effect
    resolved_root = Path(root).resolve(strict=True)
    dispatch = _dispatch_for_attempt(resolved_root, attempt_id)
    canvas = _canvas_for_attempt(resolved_root, attempt_id)
    effect = submit.external_effect_id
    if (submit.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or not isinstance(effect, str)
            or re.fullmatch(r"[0-9a-f-]{36}:[0-9]{1,32}", effect) is None
            or effect.split(":", 1)[0] != dispatch.resource_id
            or submit.request_fingerprint != dispatch.request_fingerprint
            or submit.preview_fingerprint != dispatch.preview_fingerprint
            or canvas.dispatch_hash != dispatch.content_hash
            or canvas.project_id != dispatch.project_id
            or canvas.node_id != dispatch.node_id
            or canvas.resource_id != dispatch.resource_id
            or canvas.recorded_at < dispatch.recorded_at):
        raise _invalid("Jimeng accepted task differs from sealed dispatch.")
    if proof is None:
        return
    try:
        prior_file = resolve_contained_path(resolved_root,
            canonical_paid_provider_submit_path(proof.prior_unknown_receipt_fingerprint),
            allowed_root=resolved_root / "state")
        prior_raw = _read_regular_file_nofollow(prior_file,
            contained_by=resolved_root / "state")
        prior = PaidProviderSubmitReceipt.model_validate_json(prior_raw.data)
        base_budget = load_budget_by_hash(proof.base_budget_hash)
        expected_budget = reconcile_jimeng_unknown_as_accepted(
            base_budget, prior=prior, accepted=submit)
        retained_budget = load_budget_by_hash(expected_budget.content_hash)
    except (AiVideoError, OSError, ValueError) as exc:
        raise _invalid("Jimeng accepted task recovery evidence cannot be reopened.") from exc
    expected_reservation = next((item for item in expected_budget.reservations
        if item.reservation_id == submit.reservation_id), None)
    active_reservation = next((item for item in active_budget.reservations
        if item.reservation_id == submit.reservation_id), None)
    if (expected_reservation is not None and active_reservation is not None
            and active_reservation.status is BudgetReservationStatus.SETTLED
            and active_reservation.actual_cost_microunits is not None):
        expected_reservation = expected_reservation.model_copy(update={
            "status": BudgetReservationStatus.SETTLED,
            "actual_cost_microunits": active_reservation.actual_cost_microunits,
        })
    if (proof.provider_kind != "jimeng"
            or dispatch.content_hash != proof.dispatch_hash
            or dispatch.attempt_id != attempt_id
            or dispatch.request_fingerprint != proof.request_fingerprint
            or dispatch.preview_fingerprint != proof.preview_fingerprint
            or dispatch.account_sha256 != proof.account_sha256
            or dispatch.project_id != proof.project_id
            or dispatch.node_id != proof.node_id
            or dispatch.submit_id != proof.submit_id
            or dispatch.resource_id != proof.resource_id
            or dispatch.params_sha256 != proof.params_sha256
            or effect != f"{proof.resource_id}:{proof.task_id}"
            or prior.submit_receipt_fingerprint != proof.prior_unknown_receipt_fingerprint
            or prior.outcome is not PaidProviderSubmitOutcome.OUTCOME_UNKNOWN
            or prior.external_effect_id is not None
            or prior.jimeng_accepted_effect is not None
            or prior.recorded_at > proof.observed_at
            or dispatch.recorded_at > proof.observed_at
            or submit.recorded_at != proof.observed_at
            or base_budget.content_hash != proof.base_budget_hash
            or retained_budget != expected_budget
            or expected_reservation is None
            or active_reservation != expected_reservation
            or active_budget.policy_id != expected_budget.policy_id
            or active_budget.currency != expected_budget.currency
            or active_budget.revision < expected_budget.revision):
        raise _invalid("Jimeng accepted task recovery lineage is inconsistent.")
