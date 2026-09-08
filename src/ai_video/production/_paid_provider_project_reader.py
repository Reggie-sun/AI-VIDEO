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
    root: str | Path, pointer: PaidProviderBudgetSnapshotPointer, *, _seen=frozenset()
) -> PaidProviderBudgetSnapshot:
    if pointer.content_hash in _seen:
        raise _invalid("Paid Provider budget extension base is cyclic.")
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
    seen = _seen | {pointer.content_hash}
    _verify_budget_extensions(resolved_root, budget, seen)
    _verify_submit_quota_extensions(resolved_root, budget, seen)
    return budget


def _verify_budget_extensions(root: Path, budget: PaidProviderBudgetSnapshot, seen) -> None:
    extensions = budget.ceiling_extensions
    if len({item.extension_id for item in extensions}) != len(extensions):
        raise _invalid("Paid Provider budget extension IDs are duplicated.")
    previous = None
    for index, entry in enumerate(extensions):
        if (
            entry.policy_id != budget.policy_id
            or entry.currency != budget.currency
            or entry.new_ceiling_microunits <= entry.old_ceiling_microunits
        ):
            raise _invalid("Paid Provider budget extension metadata is invalid.")
        if previous is not None and entry.old_ceiling_microunits != previous.new_ceiling_microunits:
            raise _invalid("Paid Provider budget extension chain is discontinuous.")
        try:
            base = load_paid_provider_budget(root, entry.base_budget, _seen=seen)
        except AiVideoError as exc:
            raise _invalid("Paid Provider budget extension base is invalid.", str(exc)) from exc
        if (
            base.policy_id != entry.policy_id
            or base.currency != entry.currency
            or base.project_ceiling_microunits != entry.old_ceiling_microunits
            or base.ceiling_extensions != extensions[:index]
            or base.blocked
            or any(item.status is BudgetReservationStatus.UNSETTLED for item in base.reservations)
            or budget.revision <= base.revision
        ):
            raise _invalid("Paid Provider budget extension base chain is invalid.")
        # The first snapshot produced by this extension is deterministic: it
        # changes only the ceiling and appends the sealed entry.  Reopening it
        # proves the extension did not rewrite reservations at publication.
        expected = PaidProviderBudgetSnapshot.create(
            revision=base.revision + 1,
            policy_id=base.policy_id,
            currency=base.currency,
            project_ceiling_microunits=entry.new_ceiling_microunits,
            reservations=base.reservations,
            ceiling_extensions=(*base.ceiling_extensions, entry),
            submit_quota_extensions=base.submit_quota_extensions,
            blocked=False,
        )
        if budget.content_hash != expected.content_hash:
            try:
                derived = load_paid_provider_budget_by_content_hash(root, expected.content_hash)
            except AiVideoError as exc:
                raise _invalid("Paid Provider first extension snapshot is missing.", str(exc)) from exc
            if derived != expected:
                raise _invalid("Paid Provider first extension snapshot is invalid.")
        previous = entry
    if extensions and budget.project_ceiling_microunits != extensions[-1].new_ceiling_microunits:
        raise _invalid("Paid Provider budget extension ceiling regressed.")


def _verify_submit_quota_extensions(root: Path, budget: PaidProviderBudgetSnapshot, seen) -> None:
    """Verify the immutable publication chain without treating it as lifecycle."""
    extensions = budget.submit_quota_extensions
    if len({item.extension_id for item in extensions}) != len(extensions):
        raise _invalid("Paid Provider submit quota extension IDs are duplicated.")
    for index, entry in enumerate(extensions):
        try:
            base = load_paid_provider_budget(root, entry.base_budget, _seen=seen)
            from ai_video.production._generation_feedback_reader import (
                load_generation_execution_binding,
            )

            target_binding = load_generation_execution_binding(root, entry.target_binding)
            prior_binding = load_generation_execution_binding(root, entry.prior_binding)
        except AiVideoError as exc:
            raise _invalid("Paid Provider submit quota extension base is invalid.", str(exc)) from exc
        except (OSError, ValueError) as exc:
            raise _invalid("Paid Provider submit quota extension bindings are invalid.", str(exc)) from exc
        target_limits = target_binding.inputs.limits
        prior_limits = prior_binding.inputs.limits
        if (
            not entry.authorization_receipt_id
            or entry.explicit_opt_in is not True
            or target_limits.task_id != entry.task_id
            or prior_limits.task_id != entry.task_id
            or target_limits.paid_submit_ceiling != entry.new_paid_submit_ceiling
            or prior_limits.paid_submit_ceiling != entry.old_paid_submit_ceiling
            or base.submit_quota_extensions != extensions[:index]
            or base.blocked
            or any(item.status is BudgetReservationStatus.UNSETTLED for item in base.reservations)
            or any(item.attempt_id == entry.target_attempt_id for item in base.reservations)
            or budget.revision <= base.revision
        ):
            raise _invalid("Paid Provider submit quota extension chain is invalid.")
        expected = PaidProviderBudgetSnapshot.create(
            revision=base.revision + 1,
            policy_id=base.policy_id,
            currency=base.currency,
            project_ceiling_microunits=base.project_ceiling_microunits,
            reservations=base.reservations,
            ceiling_extensions=base.ceiling_extensions,
            submit_quota_extensions=(*base.submit_quota_extensions, entry),
            blocked=False,
        )
        if budget.content_hash != expected.content_hash:
            try:
                derived = load_paid_provider_budget_by_content_hash(root, expected.content_hash)
            except AiVideoError as exc:
                raise _invalid("Paid Provider first submit quota snapshot is missing.", str(exc)) from exc
            if derived != expected:
                raise _invalid("Paid Provider first submit quota snapshot is invalid.")


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
    _verify_budget_extensions(resolved_root, budget, {content_hash})
    _verify_submit_quota_extensions(resolved_root, budget, {content_hash})
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
    if any(entry.project_id != manifest.project_id for entry in budget.ceiling_extensions):
        raise _invalid("Paid Provider budget extension project is invalid.")
    if any(entry.project_id != manifest.project_id for entry in budget.submit_quota_extensions):
        raise _invalid("Paid Provider submit quota extension project is invalid.")
    for entry in budget.submit_quota_extensions:
        target = next((item for item in manifest.attempts if item.attempt_id == entry.target_attempt_id), None)
        prior = next((item for item in manifest.attempts if item.attempt_id == entry.prior_attempt_id), None)
        if (
            target is None
            or prior is None
            or target.operation != "video_generation"
            or prior.operation != "video_generation"
            or target.video_generation_state is None
            or prior.video_generation_state is None
            or target.video_generation_state.execution_binding != entry.target_binding
            or prior.video_generation_state.execution_binding != entry.prior_binding
        ):
            raise _invalid("Paid Provider submit quota extension attempt binding is invalid.")
    initial_ceiling = (
        budget.ceiling_extensions[0].old_ceiling_microunits
        if budget.ceiling_extensions else budget.project_ceiling_microunits
    )
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
        gate_initial_ceiling = (
            gate_budget.ceiling_extensions[0].old_ceiling_microunits
            if gate_budget.ceiling_extensions else gate_budget.project_ceiling_microunits
        )
        # Historical Gate authorization anchors the legacy ledger ceiling even
        # if a rehashed active snapshot has stripped its optional extension field.
        if (
            gate_budget.policy_id != gate.authorization.budget_policy_id
            or gate_budget.currency != gate.authorization.budget_currency
            or gate_budget.project_ceiling_microunits
            != gate.authorization.project_budget_ceiling_microunits
            or budget.policy_id != gate_budget.policy_id
            or budget.currency != gate_budget.currency
            or initial_ceiling != gate_initial_ceiling
            or budget.revision < gate_budget.revision
            or budget.ceiling_extensions[:len(gate_budget.ceiling_extensions)]
            != gate_budget.ceiling_extensions
            or budget.submit_quota_extensions[:len(gate_budget.submit_quota_extensions)]
            != gate_budget.submit_quota_extensions
        ):
            raise _invalid("Paid Provider budget lineage differs from retained Gate authorization.")
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
