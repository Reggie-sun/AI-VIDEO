from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    ActorIdentity,
    PaidProviderAttemptPhase,
    PaidProviderAttemptState,
    PaidProviderBudgetSnapshotPointer,
    PaidProviderGateReceiptPointer,
    PaidProviderSubmitReceiptPointer,
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StateCommitAttempt,
    StateCommitStatus,
    VoiceRequestReceipt,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    SecretReference,
)
from ai_video.production.state_commit import CommitPhase, ProductionStateCommitter


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def _project() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"), revision=1, content_hash=ZERO, file_sha256=ONE
    )


def _registry() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{ZERO}.json"),
        revision_id=ZERO,
        content_hash=ZERO,
        file_sha256=ONE,
    )


def _budget() -> PaidProviderBudgetSnapshotPointer:
    return PaidProviderBudgetSnapshotPointer(
        path=Path(f"state/paid-provider/budgets/{ZERO}.json"),
        revision=2,
        content_hash=ZERO,
        file_sha256=ONE,
    )


def _gate() -> PaidProviderGateReceiptPointer:
    return PaidProviderGateReceiptPointer(
        path=Path(f"state/paid-provider/gates/{ONE}.json"),
        gate_receipt_fingerprint=ONE,
        file_sha256=TWO,
    )


def _submit() -> PaidProviderSubmitReceiptPointer:
    return PaidProviderSubmitReceiptPointer(
        path=Path(f"state/paid-provider/submits/{TWO}.json"),
        submit_receipt_fingerprint=TWO,
        file_sha256=THREE,
    )


def _attempt(*, state: PaidProviderAttemptState) -> StateCommitAttempt:
    return StateCommitAttempt(
        attempt_id="paid-attempt-1",
        operation="paid_fixture",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=_project(),
        base_registry=_registry(),
        candidate_artifacts_hash=ZERO,
        paid_provider_state=state,
        started_at="2026-08-18T12:00:00+00:00",
    )


def _manifest(*, attempt: StateCommitAttempt | None = None) -> ProductionManifest:
    return ProductionManifest(
        schema_version="2.6",
        project_id="paid-demo",
        manifest_revision=2,
        active_project=_project(),
        active_registry=_registry(),
        active_paid_provider_budget=_budget(),
        attempts=() if attempt is None else (attempt,),
    )


def test_manifest_26_round_trips_exact_paid_intent_and_submit_pointers():
    intent = PaidProviderAttemptState(
        gate_receipt=_gate(),
        reservation_id="reservation-1",
        phase=PaidProviderAttemptPhase.SUBMIT_INTENT,
    )
    manifest = _manifest(attempt=_attempt(state=intent))
    reopened = ProductionManifest.model_validate_json(manifest.model_dump_json())

    assert reopened.active_paid_provider_budget == _budget()
    assert reopened.attempts[0].paid_provider_state == intent

    accepted = intent.model_copy(
        update={"phase": PaidProviderAttemptPhase.ACCEPTED, "submit_receipt": _submit()}
    )
    accepted_manifest = _manifest(attempt=_attempt(state=accepted))
    assert accepted_manifest.attempts[0].paid_provider_state.submit_receipt == _submit()


def test_paid_fields_are_rejected_before_manifest_26():
    payload = _manifest().model_dump(mode="json")
    payload["schema_version"] = "2.5"

    with pytest.raises(ValidationError, match="cannot contain explicit paid Provider"):
        ProductionManifest.model_validate(payload)


def test_paid_attempt_requires_active_budget_and_submit_pointer_for_terminal_phase():
    state = PaidProviderAttemptState(
        gate_receipt=_gate(),
        reservation_id="reservation-1",
        phase=PaidProviderAttemptPhase.ACCEPTED,
        submit_receipt=_submit(),
    )
    payload = _manifest(attempt=_attempt(state=state)).model_dump(mode="json")
    payload.pop("active_paid_provider_budget")
    with pytest.raises(ValidationError, match="active paid Provider budget"):
        ProductionManifest.model_validate(payload)

    with pytest.raises(ValidationError, match="submit receipt"):
        PaidProviderAttemptState(
            gate_receipt=_gate(),
            reservation_id="reservation-1",
            phase=PaidProviderAttemptPhase.OUTCOME_UNKNOWN,
        )


@pytest.mark.parametrize(
    ("pointer", "path"),
    [
        (_budget, Path(f"state/paid-provider/budgets/{ONE}.json")),
        (_gate, Path(f"state/paid-provider/gates/{TWO}.json")),
        (_submit, Path(f"state/paid-provider/submits/{THREE}.json")),
    ],
)
def test_paid_pointers_require_exact_content_addressed_paths(pointer, path):
    current = pointer()
    with pytest.raises(ValidationError, match="canonical"):
        type(current).model_validate({**current.model_dump(mode="json"), "path": path})


def test_manifest_rejects_duplicate_paid_receipt_ownership():
    state = PaidProviderAttemptState(
        gate_receipt=_gate(),
        reservation_id="reservation-1",
        phase=PaidProviderAttemptPhase.SUBMIT_INTENT,
    )
    first = _attempt(state=state)
    second = first.model_copy(update={"attempt_id": "paid-attempt-2"})
    with pytest.raises(ValidationError, match="receipt ownership"):
        ProductionManifest.model_validate(
            {**_manifest().model_dump(mode="json"), "attempts": (first, second)}
        )


def _preview() -> PaidProviderCallPreview:
    return PaidProviderCallPreview.create(
        attempt_id="paid-attempt-1",
        operation="voice_generation",
        provider_kind="fixture-provider",
        model_id="fixture-model",
        request_fingerprint=ZERO,
        billing_mode="remote_metered",
        currency="USD",
        estimated_cost_upper_bound_microunits=2_000_000,
        destination="https://api.fixture.invalid",
        method="POST",
        egress_items=(
            PaidProviderEgressItem(
                item_id="script",
                sha256=ONE,
                size_bytes=12,
                mime_type="text/plain",
                purpose="script",
            ),
        ),
        retention_mode="provider_standard",
        provider_policy_snapshot_id="policy-1",
        secret_reference=SecretReference(
            kind="environment", reference_id="FIXTURE_API_KEY"
        ),
    )


def _authorization(
    preview: PaidProviderCallPreview,
    *,
    egress_policy_receipt_id: str = "egress-1",
) -> PaidProviderAuthorizationDecision:
    return PaidProviderAuthorizationDecision.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="human-owner", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in-1",
        budget_policy_id="budget-1",
        budget_currency="USD",
        project_budget_ceiling_microunits=10_000_000,
        per_call_ceiling_microunits=3_000_000,
        egress_authorized=True,
        egress_policy_receipt_id=egress_policy_receipt_id,
        live_test_authorized=True,
        live_authorization_receipt_id="live-1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        max_submit_count=1,
    )


def _committer(tmp_path: Path):
    preview = _preview()
    authorization = _authorization(preview)
    attempt = StateCommitAttempt(
        attempt_id=preview.attempt_id,
        operation="voice_generation",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=_project(),
        base_registry=_registry(),
        candidate_artifacts_hash=ZERO,
        voice_request=VoiceRequestReceipt(
            request_id=preview.request_fingerprint,
            attempt_id=preview.attempt_id,
            request_fingerprint=preview.request_fingerprint,
            script_hash=ONE,
            provider_kind=preview.provider_kind,
            model_id=preview.model_id,
            voice_id="fixture-voice",
            language="en",
            pricing_snapshot_id="pricing-1",
            budget_reservation_receipt_id="budget-1",
            egress_authorization_receipt_id="egress-1",
            destination=preview.destination,
        ),
        voice_phase="submit_intent",
        started_at=NOW.isoformat(),
    )
    manifest = ProductionManifest(
        schema_version="2.6",
        project_id="paid-demo",
        manifest_revision=1,
        active_project=_project(),
        active_registry=_registry(),
        attempts=(attempt,),
    )
    committer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: NOW,
    )
    committer._write_manifest_atomic(manifest)
    return committer, preview


def test_submit_intent_rejects_preview_not_matching_durable_operation_request(
    tmp_path: Path,
):
    committer, preview = _committer(tmp_path)
    manifest = committer._read_manifest()
    attempt = manifest.attempts[0]
    assert attempt.voice_request is not None
    mismatched_attempt = attempt.model_copy(
        update={
            "voice_request": attempt.voice_request.model_copy(
                update={"request_fingerprint": ONE, "request_id": ONE}
            )
        }
    )
    committer._write_manifest_atomic(
        manifest.model_copy(update={"attempts": (mismatched_attempt,)})
    )

    with pytest.raises(AiVideoError, match="operation request"):
        committer.record_paid_provider_submit_intent(
            preview, reservation_id="reservation-1"
        )


def _consume(
    permit,
    preview: PaidProviderCallPreview,
    gate_fingerprint: str,
    authorization: PaidProviderAuthorizationDecision | None = None,
) -> bool:
    selected_authorization = authorization or _authorization(preview)
    return permit._consume_paid_provider_submit_permit(
        attempt_id=preview.attempt_id,
        operation=preview.operation,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=gate_fingerprint,
        reservation_id="reservation-1",
        destination=preview.destination,
        provider_kind=preview.provider_kind,
        model_id=preview.model_id,
        currency=preview.currency,
        estimated_cost_upper_bound_microunits=str(
            preview.estimated_cost_upper_bound_microunits
        ),
        authorization_fingerprint=selected_authorization.authorization_fingerprint,
        provider_policy_snapshot_id=preview.provider_policy_snapshot_id,
        retention_mode=preview.retention_mode,
        secret_reference_kind=preview.secret_reference.kind,
        secret_reference_id=preview.secret_reference.reference_id,
    )


def test_committer_atomically_reserves_reopens_and_mints_one_use_permit(tmp_path: Path):
    committer, preview = _committer(tmp_path)

    permit = committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    manifest = committer._read_manifest()
    state = manifest.attempts[0].paid_provider_state

    assert manifest.manifest_revision == 2
    assert manifest.active_paid_provider_budget is not None
    assert state is not None
    assert state.phase is PaidProviderAttemptPhase.SUBMIT_INTENT
    assert _consume(permit, preview, state.gate_receipt.gate_receipt_fingerprint)
    assert not _consume(permit, preview, state.gate_receipt.gate_receipt_fingerprint)


def test_durable_permit_rejects_authorization_not_selected_by_reopened_gate(
    tmp_path: Path,
):
    committer, preview = _committer(tmp_path)
    permit = committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    state = committer._read_manifest().attempts[0].paid_provider_state
    assert state is not None
    submit_authorization = _authorization(
        preview, egress_policy_receipt_id="egress-2"
    )

    assert not _consume(
        permit,
        preview,
        state.gate_receipt.gate_receipt_fingerprint,
        submit_authorization,
    )
    assert _consume(permit, preview, state.gate_receipt.gate_receipt_fingerprint)


def test_submit_receipt_and_settlement_survive_restart(tmp_path: Path):
    committer, preview = _committer(tmp_path)
    permit = committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    state = committer._read_manifest().attempts[0].paid_provider_state
    assert state is not None
    assert _consume(permit, preview, state.gate_receipt.gate_receipt_fingerprint)
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=state.gate_receipt.gate_receipt_fingerprint,
        reservation_id=state.reservation_id,
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id="fixture-task-1",
        recorded_at=NOW,
    )

    submitted = committer.record_paid_provider_submit_receipt(receipt)
    settled = committer.settle_paid_provider_reservation(
        attempt_id=preview.attempt_id, actual_cost_microunits=1_500_000
    )
    restarted = ProductionStateCommitter(tmp_path)
    reopened = restarted._read_manifest()

    assert submitted.attempts[0].paid_provider_state.phase is PaidProviderAttemptPhase.ACCEPTED
    assert settled.attempts[0].paid_provider_state.phase is PaidProviderAttemptPhase.SETTLED
    assert reopened == settled
    budget = restarted._reopen_paid_budget(reopened.active_paid_provider_budget)
    assert budget.committed_microunits == 1_500_000


def test_unknown_submit_is_unsettled_and_never_remints_on_restart(tmp_path: Path):
    committer, preview = _committer(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    state = committer._read_manifest().attempts[0].paid_provider_state
    assert state is not None
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=state.gate_receipt.gate_receipt_fingerprint,
        reservation_id=state.reservation_id,
        outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
        external_effect_id=None,
        recorded_at=NOW,
    )

    recorded = committer.record_paid_provider_submit_receipt(receipt)
    restarted = ProductionStateCommitter(tmp_path)
    budget = restarted._reopen_paid_budget(recorded.active_paid_provider_budget)

    assert recorded.attempts[0].status is StateCommitStatus.OUTCOME_UNKNOWN
    assert budget.blocked is False
    assert budget.reservations[0].status.value == "unsettled"
    with pytest.raises(Exception):
        restarted.settle_paid_provider_reservation(
            attempt_id=preview.attempt_id, actual_cost_microunits=0
        )


def test_committer_uses_its_clock_and_rejects_expired_caller_evidence(tmp_path: Path):
    committer, preview = _committer(tmp_path)
    committer._paid_provider_clock = lambda: NOW + timedelta(minutes=11)

    with pytest.raises(AiVideoError) as exc:
        committer.record_paid_provider_submit_intent(
            preview, reservation_id="reservation-1"
        )

    assert exc.value.code is ErrorCode.PAID_PROVIDER_LIVE_AUTHORIZATION_REQUIRED


def test_known_no_effect_is_terminal_and_releases_exact_zero(tmp_path: Path):
    committer, preview = _committer(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    state = committer._read_manifest().attempts[0].paid_provider_state
    assert state is not None
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=state.gate_receipt.gate_receipt_fingerprint,
        reservation_id=state.reservation_id,
        outcome=PaidProviderSubmitOutcome.KNOWN_NO_EFFECT,
        external_effect_id=None,
        recorded_at=NOW,
    )

    manifest = committer.record_paid_provider_submit_receipt(receipt)
    budget = committer._reopen_paid_budget(manifest.active_paid_provider_budget)

    assert manifest.attempts[0].status is StateCommitStatus.FAILED
    assert manifest.attempts[0].error_code == ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT
    assert budget.available_microunits == budget.project_ceiling_microunits


class _CrashOnce:
    def __init__(self, target: CommitPhase) -> None:
        self.target = target
        self.triggered = False

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.target and not self.triggered:
            self.triggered = True
            raise RuntimeError(f"fixture crash at {phase.value}")


_PAID_WRITER_CRASH_PHASES = (
    CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
    CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
    CommitPhase.AFTER_ARTIFACT_PROMOTION,
    CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
    CommitPhase.AFTER_ARTIFACT_VERIFICATION,
    CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
    CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
    CommitPhase.AFTER_MANIFEST_REPLACE,
    CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
)


def _accepted_submit(committer, preview):
    state = committer._read_manifest().attempts[0].paid_provider_state
    assert state is not None
    return PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=state.gate_receipt.gate_receipt_fingerprint,
        reservation_id=state.reservation_id,
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id="fixture-effect-1",
        recorded_at=NOW,
    )


@pytest.mark.parametrize("phase", _PAID_WRITER_CRASH_PHASES)
def test_paid_intent_crash_never_selects_partial_evidence_or_mints_a_permit(
    tmp_path: Path, phase: CommitPhase
):
    committer, preview = _committer(tmp_path)
    committer._crash_injector = _CrashOnce(phase)

    with pytest.raises(AiVideoError):
        committer.record_paid_provider_submit_intent(
            preview, reservation_id="reservation-1"
        )

    manifest = ProductionStateCommitter(tmp_path)._read_manifest()
    state = manifest.attempts[0].paid_provider_state
    if phase in {
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    }:
        assert state is not None
        recovery = ProductionStateCommitter(tmp_path)
        recovered, _ = recovery._recover_paid_provider_intents(manifest)
        assert recovered.manifest_revision == manifest.manifest_revision + 1
        recovered_state = (
            ProductionStateCommitter(tmp_path)
            ._read_manifest()
            .attempts[0]
            .paid_provider_state
        )
        assert recovered_state is not None
        assert recovered_state.phase is PaidProviderAttemptPhase.OUTCOME_UNKNOWN
    else:
        assert state is None
        assert manifest.active_paid_provider_budget is None


@pytest.mark.parametrize("phase", _PAID_WRITER_CRASH_PHASES)
def test_paid_submit_receipt_crash_recovers_without_blind_resubmit(
    tmp_path: Path, phase: CommitPhase
):
    committer, preview = _committer(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    receipt = _accepted_submit(committer, preview)
    committer._crash_injector = _CrashOnce(phase)

    with pytest.raises(AiVideoError):
        committer.record_paid_provider_submit_receipt(receipt)

    manifest = ProductionStateCommitter(tmp_path)._read_manifest()
    state = manifest.attempts[0].paid_provider_state
    assert state is not None
    if phase in {
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    }:
        assert state.phase is PaidProviderAttemptPhase.ACCEPTED
    else:
        assert state.phase is PaidProviderAttemptPhase.SUBMIT_INTENT
        recovery = ProductionStateCommitter(tmp_path)
        recovery._recover_paid_provider_intents(manifest)
        recovered_state = (
            ProductionStateCommitter(tmp_path)
            ._read_manifest()
            .attempts[0]
            .paid_provider_state
        )
        assert recovered_state is not None
        assert recovered_state.phase is PaidProviderAttemptPhase.OUTCOME_UNKNOWN


@pytest.mark.parametrize("phase", _PAID_WRITER_CRASH_PHASES)
def test_paid_settlement_crash_preserves_accepted_or_exact_settled_state(
    tmp_path: Path, phase: CommitPhase
):
    committer, preview = _committer(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    committer.record_paid_provider_submit_receipt(_accepted_submit(committer, preview))
    committer._crash_injector = _CrashOnce(phase)

    with pytest.raises(AiVideoError):
        committer.settle_paid_provider_reservation(
            attempt_id=preview.attempt_id,
            actual_cost_microunits=1_500_000,
        )

    manifest = ProductionStateCommitter(tmp_path)._read_manifest()
    state = manifest.attempts[0].paid_provider_state
    assert state is not None
    if phase in {
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    }:
        assert state.phase is PaidProviderAttemptPhase.SETTLED
    else:
        assert state.phase is PaidProviderAttemptPhase.ACCEPTED
