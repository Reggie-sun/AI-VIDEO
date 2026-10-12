from datetime import timedelta

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.paid_provider import (
    PaidProviderCallPreview, PaidProviderAuthorizationDecision, SecretReference,
    PaidProviderGateReceipt,
    reserve_paid_provider_budget,
    PaidProviderBudgetSnapshot, PaidProviderSubmitReceipt, PaidProviderSubmitOutcome,
    apply_paid_provider_submit_receipt, settle_paid_provider_budget,
)
from test_grok_subscription import binding, NOW
from paid_provider_support import paid_preview, paid_authorization


def make_paid_preview():
    return paid_preview(attempt_id="legacy-test")


def make_paid_authorization(preview):
    return paid_authorization(preview)


def subscription_call(attempt="grok-subscription-1"):
    old = make_paid_preview()
    data = old.model_dump(mode="python", exclude={"preview_fingerprint"})
    data.update(attempt_id=attempt, provider_kind="grok", model_id="grok-imagine-video-1.5",
        operation="video_generation", destination="https://cli-chat-proxy.grok.com",
        billing_mode="remote_subscription", currency="USD", estimated_cost_upper_bound_microunits=0,
        secret_reference=SecretReference(kind="secret_store", reference_id="GROK_OAUTH"),
        subscription_binding=binding())
    return PaidProviderCallPreview.create(**data)


def subscription_authorization(preview, limit=1):
    old = make_paid_authorization(make_paid_preview())
    data = old.model_dump(mode="python", exclude={"authorization_fingerprint"})
    data.update(attempt_id=preview.attempt_id, preview_fingerprint=preview.preview_fingerprint,
        budget_currency="USD", project_budget_ceiling_microunits=0, per_call_ceiling_microunits=0,
        subscription_submit_limit=limit, issued_at=NOW, expires_at=NOW + timedelta(minutes=5))
    return PaidProviderAuthorizationDecision.create(**data)


def test_subscription_zero_cash_still_consumes_finite_attempts():
    first = subscription_call()
    ledger, reservation = reserve_paid_provider_budget(None, preview=first,
        authorization=subscription_authorization(first), reservation_id="grok-r1")
    assert ledger.project_ceiling_microunits == reservation.upper_bound_microunits == 0
    second = subscription_call("grok-subscription-2")
    with pytest.raises(AiVideoError):
        reserve_paid_provider_budget(ledger, preview=second,
            authorization=subscription_authorization(second), reservation_id="grok-r2")


def test_legacy_paid_bytes_do_not_gain_subscription_fields():
    preview = make_paid_preview()
    authorization = make_paid_authorization(preview)
    assert "subscription_binding" not in preview.model_dump(mode="json")
    assert "subscription_submit_limit" not in authorization.model_dump(mode="json")
    assert PaidProviderCallPreview.model_validate_json(preview.model_dump_json()) == preview


def test_legacy_gate_reconstruction_accepts_serialized_preview_without_changing_bytes():
    preview = make_paid_preview()
    values = dict(preview=preview, authorization=make_paid_authorization(preview),
        reservation_id="legacy-r1", budget_snapshot_revision=1,
        budget_snapshot_content_hash="0" * 64, budget_snapshot_file_sha256="1" * 64)
    typed = PaidProviderGateReceipt.create(**values)
    restored = PaidProviderGateReceipt.create(**{
        **values, "preview": preview.model_dump(mode="python")})
    assert restored == typed
    assert restored.model_dump_json() == typed.model_dump_json()


def test_subscription_binding_cannot_be_reused_as_unbounded_free_metered_call():
    data = subscription_call().model_dump(mode="python", exclude={"preview_fingerprint"})
    data["billing_mode"] = "remote_metered"
    with pytest.raises(ValueError):
        PaidProviderCallPreview.create(**data)


def test_subscription_count_does_not_replace_existing_cash_reservations():
    legacy = make_paid_preview()
    legacy_auth = make_paid_authorization(legacy)
    ledger, cash = reserve_paid_provider_budget(None, preview=legacy,
        authorization=legacy_auth, reservation_id="cash-r1")
    p = subscription_call()
    values = subscription_authorization(p).model_dump(mode="python", exclude={"authorization_fingerprint"})
    values.update(budget_policy_id=ledger.policy_id, budget_currency=ledger.currency,
        project_budget_ceiling_microunits=ledger.project_ceiling_microunits)
    a = PaidProviderAuthorizationDecision.create(**values)
    updated, sub = reserve_paid_provider_budget(ledger, preview=p, authorization=a, reservation_id="sub-r1")
    assert updated.reservations[0] == cash
    assert sub.upper_bound_microunits == 0
    assert updated.committed_microunits == ledger.committed_microunits
    assert updated.subscription_submit_limit == 1


def test_unknown_zero_cash_reservation_still_blocks_new_subscription():
    p = subscription_call()
    ledger, _ = reserve_paid_provider_budget(None, preview=p,
        authorization=subscription_authorization(p, 2), reservation_id="sub-r1")
    receipt = PaidProviderSubmitReceipt.create(attempt_id=p.attempt_id,
        request_fingerprint=p.request_fingerprint, preview_fingerprint=p.preview_fingerprint,
        gate_receipt_fingerprint="9" * 64, reservation_id="sub-r1",
        outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN, external_effect_id=None, recorded_at=NOW)
    unknown = apply_paid_provider_submit_receipt(ledger, receipt)
    with pytest.raises(AiVideoError):
        settle_paid_provider_budget(unknown, reservation_id="sub-r1", actual_cost_microunits=0)
    other = subscription_call("sub-two")
    with pytest.raises(AiVideoError):
        reserve_paid_provider_budget(unknown, preview=other,
            authorization=subscription_authorization(other, 2), reservation_id="sub-r2")
    with pytest.raises(ValueError):
        PaidProviderBudgetSnapshot.create(**unknown.model_dump(mode="python",
            exclude={"content_hash", "subscription_submit_limit"}))
