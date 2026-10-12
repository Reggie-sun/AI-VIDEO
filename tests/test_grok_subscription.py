from datetime import UTC, datetime, timedelta

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.grok_subscription import (
    GrokSubscriptionBinding, parse_subscription_usage, require_current_subscription,
)

NOW = datetime(2026, 10, 12, tzinfo=UTC)


def binding(**changes):
    values = dict(account_fingerprint="a" * 64, model_id="grok-imagine-video-1.5",
        destination="https://cli-chat-proxy.grok.com", credential_reference_id="GROK_OAUTH",
        quota_observed_at=NOW, quota_expires_at=NOW + timedelta(minutes=5),
        period_end=NOW + timedelta(days=1), used_percent=20,
        included_only_evidence_id="fake-server-hard-cap")
    return GrokSubscriptionBinding(**{**values, **changes})


def test_quota_omission_is_unknown_and_never_zero():
    usage = parse_subscription_usage({"config": {"currentPeriod": {
        "type": "WEEKLY", "end": "2026-10-13T00:00:00Z"}}})
    assert usage.used_percent is None
    assert usage.included_only_verified is False


def test_usage_does_not_treat_prepaid_or_ondemand_as_included_quota():
    usage = parse_subscription_usage({"config": {
        "prepaidBalance": {"val": 5000}, "onDemandUsagePercent": 0}})
    assert usage.used_percent is None
    assert usage.included_only_verified is False


@pytest.mark.parametrize("changes", [
    {"used_percent": 100}, {"quota_expires_at": NOW},
    {"period_end": NOW}, {"account_fingerprint": "b" * 64},
])
def test_admission_rejects_exhausted_stale_and_wrong_account(changes):
    with pytest.raises((AiVideoError, ValueError)):
        require_current_subscription(binding(**changes), account_fingerprint="a" * 64,
            model_id="grok-imagine-video-1.5", destination="https://cli-chat-proxy.grok.com", now=NOW)


def test_exact_fake_boundary_can_be_bound_without_asserting_real_account_eligibility():
    proof = binding()
    assert require_current_subscription(proof, account_fingerprint="a" * 64,
        model_id=proof.model_id, destination=proof.destination, now=NOW) == proof
