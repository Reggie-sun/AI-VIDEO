from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    SecretReference,
)


NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
ZERO = "0" * 64
ONE = "1" * 64


def paid_preview(*, attempt_id: str) -> PaidProviderCallPreview:
    return PaidProviderCallPreview.create(
        attempt_id=attempt_id,
        operation="voice_generation",
        provider_kind="scripted-fake",
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


def paid_authorization(
    preview: PaidProviderCallPreview,
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
        egress_policy_receipt_id="egress-1",
        live_test_authorized=True,
        live_authorization_receipt_id="live-1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        max_submit_count=1,
    )


class ScriptedFakePaidProviderTransport:
    def __init__(self) -> None:
        self.calls = 0

    def submit(
        self,
        permit: object,
        preview: PaidProviderCallPreview,
        gate_receipt_fingerprint: str,
        reservation_id: str,
    ) -> str:
        consume = getattr(permit, "_consume_paid_provider_submit_permit", None)
        if not callable(consume) or not consume(
            attempt_id=preview.attempt_id,
            operation=preview.operation,
            request_fingerprint=preview.request_fingerprint,
            preview_fingerprint=preview.preview_fingerprint,
            gate_receipt_fingerprint=gate_receipt_fingerprint,
            reservation_id=reservation_id,
            destination=preview.destination,
            provider_kind=preview.provider_kind,
            model_id=preview.model_id,
            currency=preview.currency,
            estimated_cost_upper_bound_microunits=str(
                preview.estimated_cost_upper_bound_microunits
            ),
            authorization_fingerprint=(
                paid_authorization(preview).authorization_fingerprint
            ),
            provider_policy_snapshot_id=preview.provider_policy_snapshot_id,
            retention_mode=preview.retention_mode,
            secret_reference_kind=preview.secret_reference.kind,
            secret_reference_id=preview.secret_reference.reference_id,
        ):
            raise PermissionError("exact paid Provider permit required")
        self.calls += 1
        return "fixture-task-1"
