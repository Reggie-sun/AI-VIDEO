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


@pytest.mark.parametrize("path", ["/v1/videos/generations", "/v1/videos/edits",
                                   "/v1/videos/extensions"])
def test_classic_subscription_boundary_must_bind_exact_operation(path):
    proof = binding(model_id="grok-imagine-video", operation_path=path)
    assert require_current_subscription(proof, account_fingerprint="a" * 64,
        model_id=proof.model_id, destination=proof.destination, now=NOW,
        operation_path=path) == proof
    wrong = "/v1/videos/edits" if path != "/v1/videos/edits" else "/v1/videos/extensions"
    with pytest.raises(AiVideoError):
        require_current_subscription(proof, account_fingerprint="a" * 64,
            model_id=proof.model_id, destination=proof.destination, now=NOW,
            operation_path=wrong)


def test_legacy_generation_binding_hash_surface_is_preserved():
    proof = binding()
    assert "operation_path" not in proof.model_dump(mode="json")
    assert require_current_subscription(proof, account_fingerprint="a" * 64,
        model_id=proof.model_id, destination=proof.destination, now=NOW,
        operation_path="/v1/videos/generations") == proof


@pytest.mark.parametrize("model", ["grok-imagine-video", "grok-imagine-video-1.5-lite"])
def test_new_models_need_operation_bound_included_only_evidence(model):
    with pytest.raises(AiVideoError):
        require_current_subscription(binding(model_id=model), account_fingerprint="a" * 64,
            model_id=model, destination="https://cli-chat-proxy.grok.com", now=NOW,
            operation_path="/v1/videos/generations")


@pytest.mark.parametrize("model", ["grok-imagine-video-1.5", "grok-imagine-video-1.5-lite",
                                    "grok-imagine-image-2.0"])
def test_subscription_cannot_bind_edit_to_an_unsupported_model(model):
    with pytest.raises(ValueError):
        binding(model_id=model, operation_path="/v1/videos/edits")
