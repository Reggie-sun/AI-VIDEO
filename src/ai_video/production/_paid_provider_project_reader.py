from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    PaidProviderAttemptPhase,
    PaidProviderBudgetSnapshotPointer,
    PaidProviderGateReceiptPointer,
    PaidProviderSubmitReceiptPointer,
    ProductionManifest,
    StateCommitStatus,
)
from ai_video.production.paid_provider import (
    BudgetReservationStatus,
    PaidProviderBudgetSnapshot,
    PaidProviderGateReceipt,
    PaidProviderSubmitReceipt,
    PaidProviderSubmitOutcome,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_paid_provider_budget_path,
    resolve_contained_path,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _root_and_path(root: str | Path, stored: Path) -> tuple[Path, Path]:
    try:
        resolved_root = Path(root).resolve(strict=True)
        resolved = resolve_contained_path(
            resolved_root, stored, allowed_root=resolved_root / "state"
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid("Paid Provider evidence path is unsafe.", str(exc)) from exc
    return resolved_root, resolved


def load_paid_provider_budget(
    root: str | Path, pointer: PaidProviderBudgetSnapshotPointer
) -> PaidProviderBudgetSnapshot:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        budget = PaidProviderBudgetSnapshot.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen paid Provider budget.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or budget.revision != pointer.revision
        or budget.content_hash != pointer.content_hash
    ):
        raise _invalid("Paid Provider budget pointer identity is invalid.")
    return budget


def load_paid_provider_budget_by_content_hash(
    root: str | Path, content_hash: str
) -> PaidProviderBudgetSnapshot:
    """Reopen one immutable historical budget by its sealed content identity."""

    resolved_root, resolved = _root_and_path(
        root, canonical_paid_provider_budget_path(content_hash)
    )
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        budget = PaidProviderBudgetSnapshot.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen historical paid Provider budget.", str(exc)) from exc
    if budget.content_hash != content_hash:
        raise _invalid("Historical paid Provider budget identity is invalid.")
    return budget


def load_paid_provider_gate_receipt(
    root: str | Path, pointer: PaidProviderGateReceiptPointer
) -> PaidProviderGateReceipt:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        receipt = PaidProviderGateReceipt.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen paid Provider Gate receipt.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or receipt.gate_receipt_fingerprint != pointer.gate_receipt_fingerprint
    ):
        raise _invalid("Paid Provider Gate receipt pointer identity is invalid.")
    return receipt


def load_paid_provider_submit_receipt(
    root: str | Path, pointer: PaidProviderSubmitReceiptPointer
) -> PaidProviderSubmitReceipt:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        receipt = PaidProviderSubmitReceipt.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen paid Provider submit receipt.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or receipt.submit_receipt_fingerprint != pointer.submit_receipt_fingerprint
    ):
        raise _invalid("Paid Provider submit receipt pointer identity is invalid.")
    return receipt


def verify_paid_provider_evidence(root: Path, manifest: ProductionManifest) -> None:
    pointer = manifest.active_paid_provider_budget
    paid_attempts = [
        item for item in manifest.attempts if item.paid_provider_state is not None
    ]
    if pointer is None:
        return
    budget = load_paid_provider_budget(root, pointer)
    reservations = {item.reservation_id: item for item in budget.reservations}
    external_effect_ids: list[str] = []
    for attempt in paid_attempts:
        state = attempt.paid_provider_state
        assert state is not None
        required_status = {
            PaidProviderAttemptPhase.SUBMIT_INTENT: StateCommitStatus.RUNNING,
            PaidProviderAttemptPhase.ACCEPTED: StateCommitStatus.RUNNING,
            PaidProviderAttemptPhase.KNOWN_NO_EFFECT: StateCommitStatus.FAILED,
            PaidProviderAttemptPhase.OUTCOME_UNKNOWN: StateCommitStatus.OUTCOME_UNKNOWN,
        }.get(state.phase)
        accepted_video_terminal = (
            attempt.operation == "video_generation"
            and state.phase is PaidProviderAttemptPhase.ACCEPTED
            and attempt.status
            in {StateCommitStatus.FAILED, StateCommitStatus.INTERRUPTED}
        )
        if (
            required_status is not None
            and attempt.status is not required_status
            and not accepted_video_terminal
        ):
            raise _invalid("Paid Provider attempt status is inconsistent with its phase.")
        gate = load_paid_provider_gate_receipt(root, state.gate_receipt)
        gate_budget = load_paid_provider_budget(
            root,
            PaidProviderBudgetSnapshotPointer(
                path=Path(
                    "state/paid-provider/budgets/"
                    f"{gate.budget_snapshot_content_hash}.json"
                ),
                revision=gate.budget_snapshot_revision,
                content_hash=gate.budget_snapshot_content_hash,
                file_sha256=gate.budget_snapshot_file_sha256,
            ),
        )
        gate_reservation = next(
            (
                item
                for item in gate_budget.reservations
                if item.reservation_id == state.reservation_id
            ),
            None,
        )
        reservation = reservations.get(state.reservation_id)
        if (
            reservation is None
            or gate_reservation is None
            or reservation.attempt_id != attempt.attempt_id
            or gate_reservation.attempt_id != attempt.attempt_id
            or reservation.request_fingerprint
            != gate.preview.request_fingerprint
            or gate_reservation.request_fingerprint
            != gate.preview.request_fingerprint
            or reservation.preview_fingerprint
            != gate.preview.preview_fingerprint
            or gate_reservation.preview_fingerprint
            != gate.preview.preview_fingerprint
            or reservation.upper_bound_microunits
            != gate.preview.estimated_cost_upper_bound_microunits
            or gate_reservation.upper_bound_microunits
            != gate.preview.estimated_cost_upper_bound_microunits
            or gate_reservation.status is not BudgetReservationStatus.RESERVED
            or gate_reservation.actual_cost_microunits is not None
            or gate_reservation.submit_receipt_fingerprint is not None
            or gate.preview.attempt_id != attempt.attempt_id
            or gate.reservation_id != state.reservation_id
        ):
            raise _invalid("Paid Provider attempt evidence is inconsistent.")
        if state.phase is PaidProviderAttemptPhase.SUBMIT_INTENT:
            if (
                state.submit_receipt is not None
                or reservation.status is not BudgetReservationStatus.RESERVED
                or reservation.actual_cost_microunits is not None
                or reservation.submit_receipt_fingerprint is not None
            ):
                raise _invalid("Paid Provider attempt evidence is inconsistent.")
            continue
        if state.submit_receipt is not None:
            submit = load_paid_provider_submit_receipt(root, state.submit_receipt)
            if (
                submit.attempt_id != attempt.attempt_id
                or submit.reservation_id != state.reservation_id
                or submit.request_fingerprint
                != gate.preview.request_fingerprint
                or submit.preview_fingerprint
                != gate.preview.preview_fingerprint
                or submit.gate_receipt_fingerprint
                != gate.gate_receipt_fingerprint
                or reservation.submit_receipt_fingerprint
                != submit.submit_receipt_fingerprint
            ):
                raise _invalid("Paid Provider submit evidence is inconsistent.")
            expected = {
                PaidProviderAttemptPhase.ACCEPTED: (
                    PaidProviderSubmitOutcome.ACCEPTED,
                    BudgetReservationStatus.RESERVED,
                ),
                PaidProviderAttemptPhase.KNOWN_NO_EFFECT: (
                    PaidProviderSubmitOutcome.KNOWN_NO_EFFECT,
                    BudgetReservationStatus.RELEASED,
                ),
                PaidProviderAttemptPhase.OUTCOME_UNKNOWN: (
                    PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
                    BudgetReservationStatus.UNSETTLED,
                ),
                PaidProviderAttemptPhase.SETTLED: (
                    PaidProviderSubmitOutcome.ACCEPTED,
                    BudgetReservationStatus.SETTLED,
                ),
            }.get(state.phase)
            if expected is None or (submit.outcome, reservation.status) != expected:
                raise _invalid("Paid Provider submit evidence is inconsistent.")
            if (
                state.phase is PaidProviderAttemptPhase.KNOWN_NO_EFFECT
                and reservation.actual_cost_microunits != 0
            ) or (
                state.phase is PaidProviderAttemptPhase.SETTLED
                and reservation.actual_cost_microunits is None
            ) or (
                state.phase
                in {
                    PaidProviderAttemptPhase.ACCEPTED,
                    PaidProviderAttemptPhase.OUTCOME_UNKNOWN,
                }
                and reservation.actual_cost_microunits is not None
            ):
                raise _invalid("Paid Provider settlement evidence is inconsistent.")
            if submit.external_effect_id is not None:
                external_effect_ids.append(submit.external_effect_id)
    if len(external_effect_ids) != len(set(external_effect_ids)):
        raise _invalid("Paid Provider external effect ownership is ambiguous.")
