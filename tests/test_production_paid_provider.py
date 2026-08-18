from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import (
    BudgetReservationStatus,
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderGateReceipt,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    SecretReference,
    apply_paid_provider_submit_receipt,
    reserve_paid_provider_budget,
    settle_paid_provider_budget,
    validate_paid_provider_authorization,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def _preview(**overrides: object) -> PaidProviderCallPreview:
    values: dict[str, object] = {
        "attempt_id": "paid-attempt-1",
        "operation": "voice_generation",
        "provider_kind": "fixture-provider",
        "model_id": "fixture-model-1",
        "request_fingerprint": ZERO_HASH,
        "billing_mode": "remote_metered",
        "currency": "USD",
        "estimated_cost_upper_bound_microunits": 2_000_000,
        "destination": "https://api.fixture.invalid",
        "method": "POST",
        "egress_items": (
            PaidProviderEgressItem(
                item_id="script",
                sha256=ONE_HASH,
                size_bytes=12,
                mime_type="text/plain",
                purpose="script",
            ),
        ),
        "retention_mode": "provider_standard",
        "provider_policy_snapshot_id": "provider-policy-1",
        "secret_reference": SecretReference(
            kind="environment", reference_id="FIXTURE_API_KEY"
        ),
    }
    values.update(overrides)
    return PaidProviderCallPreview.create(**values)


def _authorization(
    preview: PaidProviderCallPreview, **overrides: object
) -> PaidProviderAuthorizationDecision:
    values: dict[str, object] = {
        "attempt_id": preview.attempt_id,
        "preview_fingerprint": preview.preview_fingerprint,
        "explicit_opt_in": True,
        "actor": ActorIdentity(actor_id="human-owner", actor_kind="human"),
        "opt_in_policy_receipt_id": "opt-in-policy-1",
        "budget_policy_id": "budget-policy-1",
        "budget_currency": preview.currency,
        "project_budget_ceiling_microunits": 10_000_000,
        "per_call_ceiling_microunits": 3_000_000,
        "egress_authorized": True,
        "egress_policy_receipt_id": "egress-policy-1",
        "live_test_authorized": True,
        "live_authorization_receipt_id": "live-policy-1",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=10),
        "max_submit_count": 1,
    }
    values.update(overrides)
    return PaidProviderAuthorizationDecision.create(**values)


def _reserved_gate():
    preview = _preview()
    authorization = _authorization(preview)
    snapshot, reservation = reserve_paid_provider_budget(
        None,
        preview=preview,
        authorization=authorization,
        reservation_id="reservation-1",
    )
    gate = PaidProviderGateReceipt.create(
        preview=preview,
        authorization=authorization,
        reservation_id=reservation.reservation_id,
        budget_snapshot_revision=snapshot.revision,
        budget_snapshot_content_hash=snapshot.content_hash,
        budget_snapshot_file_sha256=ONE_HASH,
    )
    return preview, authorization, snapshot, reservation, gate


def test_preview_is_strict_frozen_self_sealed_and_secret_free():
    preview = _preview()

    assert preview.preview_fingerprint
    assert preview.secret_reference.reference_id == "FIXTURE_API_KEY"
    assert "secret_value" not in preview.model_dump(mode="json")
    with pytest.raises(ValidationError):
        preview.model_validate(
            {**preview.model_dump(mode="json"), "authorization": "Bearer secret"}
        )
    with pytest.raises(ValidationError):
        preview.model_validate(
            {**preview.model_dump(mode="json"), "preview_fingerprint": ONE_HASH}
        )
    with pytest.raises(ValidationError):
        preview.currency = "EUR"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("estimated_cost_upper_bound_microunits", -1),
        ("estimated_cost_upper_bound_microunits", 1.5),
        ("currency", "usd"),
        ("destination", "http://api.fixture.invalid"),
        ("destination", "https://api.fixture.invalid/v1"),
        ("destination", "https://user:secret@api.fixture.invalid"),
        ("billing_mode", "local_unmetered"),
    ],
)
def test_preview_rejects_unsafe_money_destination_and_billing(field, value):
    with pytest.raises((ValidationError, ValueError)):
        _preview(**{field: value})


def test_preview_identity_changes_for_every_paid_side_effect_input():
    base = _preview()
    variants = (
        _preview(provider_kind="other-provider"),
        _preview(model_id="other-model"),
        _preview(request_fingerprint=ONE_HASH),
        _preview(estimated_cost_upper_bound_microunits=2_000_001),
        _preview(destination="https://other.fixture.invalid"),
        _preview(retention_mode="zero_retention"),
        _preview(provider_policy_snapshot_id="provider-policy-2"),
        _preview(
            secret_reference=SecretReference(
                kind="secret_store", reference_id="paid-provider/fixture"
            )
        ),
    )

    assert all(item.preview_fingerprint != base.preview_fingerprint for item in variants)


def test_authorization_binds_exact_preview_actor_expiry_and_one_submit():
    preview = _preview()
    authorization = _authorization(preview)

    assert validate_paid_provider_authorization(
        preview, authorization, now=NOW
    ) is authorization
    for overrides in (
        {"attempt_id": "other-attempt"},
        {"preview_fingerprint": ONE_HASH},
        {"budget_currency": "EUR"},
        {"per_call_ceiling_microunits": 1_999_999},
    ):
        mismatched = _authorization(preview, **overrides)
        with pytest.raises(AiVideoError):
            validate_paid_provider_authorization(preview, mismatched, now=NOW)

    with pytest.raises(ValidationError):
        _authorization(preview, expires_at=NOW)

    with pytest.raises(ValidationError):
        PaidProviderAuthorizationDecision.model_validate(
            {**authorization.model_dump(mode="json"), "max_submit_count": 2}
        )


def test_budget_reservation_accounts_for_reserved_unsettled_and_settled_cost():
    preview, authorization, snapshot, reservation, gate = _reserved_gate()

    assert reservation.status is BudgetReservationStatus.RESERVED
    assert snapshot.available_microunits == 8_000_000

    accepted = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
        reservation_id=reservation.reservation_id,
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id="task-exact:ABC_123",
        recorded_at=NOW,
    )
    held = apply_paid_provider_submit_receipt(snapshot, accepted)
    assert held.available_microunits == 8_000_000
    assert held.reservations[0].status is BudgetReservationStatus.RESERVED

    settled = settle_paid_provider_budget(
        held, reservation_id=reservation.reservation_id, actual_cost_microunits=1_500_000
    )
    assert settled.reservations[0].status is BudgetReservationStatus.SETTLED
    assert settled.available_microunits == 8_500_000
    assert not settled.blocked

    preview_2 = _preview(attempt_id="paid-attempt-2", request_fingerprint=ONE_HASH)
    auth_2 = _authorization(preview_2)
    snapshot_2, _ = reserve_paid_provider_budget(
        settled,
        preview=preview_2,
        authorization=auth_2,
        reservation_id="reservation-2",
    )
    assert snapshot_2.available_microunits == 6_500_000


def test_unknown_outcome_keeps_reservation_unsettled_and_never_releases_zero():
    preview, _, snapshot, reservation, gate = _reserved_gate()
    unknown = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
        reservation_id=reservation.reservation_id,
        outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
        external_effect_id=None,
        recorded_at=NOW,
    )

    updated = apply_paid_provider_submit_receipt(snapshot, unknown)

    assert updated.reservations[0].status is BudgetReservationStatus.UNSETTLED
    assert updated.reservations[0].actual_cost_microunits is None
    assert updated.available_microunits == 8_000_000
    with pytest.raises(AiVideoError) as exc:
        settle_paid_provider_budget(
            updated,
            reservation_id=reservation.reservation_id,
            actual_cost_microunits=0,
        )
    assert exc.value.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN


def test_known_no_effect_releases_reservation_with_exact_zero():
    preview, _, snapshot, reservation, gate = _reserved_gate()
    no_effect = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
        reservation_id=reservation.reservation_id,
        outcome=PaidProviderSubmitOutcome.KNOWN_NO_EFFECT,
        external_effect_id=None,
        recorded_at=NOW,
    )

    updated = apply_paid_provider_submit_receipt(snapshot, no_effect)

    assert updated.reservations[0].status is BudgetReservationStatus.RELEASED
    assert updated.reservations[0].actual_cost_microunits == 0
    assert updated.available_microunits == 10_000_000


def test_reservation_cannot_settle_before_an_accepted_submit_receipt():
    _, _, snapshot, reservation, _ = _reserved_gate()

    with pytest.raises(AiVideoError) as exc:
        settle_paid_provider_budget(
            snapshot,
            reservation_id=reservation.reservation_id,
            actual_cost_microunits=1,
        )

    assert exc.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED


def test_actual_overrun_is_preserved_and_blocks_future_reservations():
    preview, _, snapshot, reservation, gate = _reserved_gate()
    accepted = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
        reservation_id=reservation.reservation_id,
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id="task-1",
        recorded_at=NOW,
    )
    held = apply_paid_provider_submit_receipt(snapshot, accepted)
    overrun = settle_paid_provider_budget(
        held,
        reservation_id=reservation.reservation_id,
        actual_cost_microunits=11_000_000,
    )

    assert overrun.reservations[0].actual_cost_microunits == 11_000_000
    assert overrun.blocked
    with pytest.raises(AiVideoError) as exc:
        reserve_paid_provider_budget(
            overrun,
            preview=_preview(attempt_id="paid-attempt-2"),
            authorization=_authorization(_preview(attempt_id="paid-attempt-2")),
            reservation_id="reservation-2",
        )
    assert exc.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED


@pytest.mark.parametrize(
    ("outcome", "external_effect_id"),
    [
        (PaidProviderSubmitOutcome.ACCEPTED, None),
        (PaidProviderSubmitOutcome.KNOWN_NO_EFFECT, "unexpected-task"),
        (PaidProviderSubmitOutcome.OUTCOME_UNKNOWN, "guessed-task"),
        (PaidProviderSubmitOutcome.ACCEPTED, "contains whitespace"),
        (PaidProviderSubmitOutcome.ACCEPTED, "x" * 513),
    ],
)
def test_submit_receipt_requires_exact_bounded_effect_identity(
    outcome, external_effect_id
):
    preview, _, _, reservation, gate = _reserved_gate()
    with pytest.raises((ValidationError, ValueError)):
        PaidProviderSubmitReceipt.create(
            attempt_id=preview.attempt_id,
            request_fingerprint=preview.request_fingerprint,
            preview_fingerprint=preview.preview_fingerprint,
            gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
            reservation_id=reservation.reservation_id,
            outcome=outcome,
            external_effect_id=external_effect_id,
            recorded_at=NOW,
        )


def test_budget_rejects_duplicate_attempt_or_reservation_and_insufficient_funds():
    preview, _, snapshot, _, _ = _reserved_gate()
    with pytest.raises(AiVideoError) as exc:
        reserve_paid_provider_budget(
            snapshot,
            preview=preview,
            authorization=_authorization(preview),
            reservation_id="reservation-other",
        )
    assert exc.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED

    expensive = _preview(
        attempt_id="paid-attempt-2",
        estimated_cost_upper_bound_microunits=9_000_000,
    )
    with pytest.raises(AiVideoError) as exc:
        reserve_paid_provider_budget(
            snapshot,
            preview=expensive,
            authorization=_authorization(
                expensive,
                per_call_ceiling_microunits=9_000_000,
            ),
            reservation_id="reservation-2",
        )
    assert exc.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED
