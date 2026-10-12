import json

import httpx
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.grok_billing import read_grok_subscription_usage
from ai_video.production.grok_subscription import GROK_BILLING_URL


def test_usage_get_binds_fixed_origin_and_never_claims_cash_boundary():
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"config": {"creditUsagePercent": 25,
            "currentPeriod": {"type": "WEEKLY", "end": "2026-10-19T00:00:00Z"}}})
    with httpx.Client(transport=httpx.MockTransport(respond), auth=("other-account", "private"),
            cookies={"session": "private"}) as client:
        result = read_grok_subscription_usage(account_fingerprint="a" * 64,
            credential=lambda: "test-secret", client=client)
    assert len(calls) == 1 and str(calls[0].url) == GROK_BILLING_URL
    assert calls[0].method == "GET"
    assert calls[0].headers["authorization"] == "Bearer test-secret"
    assert "cookie" not in calls[0].headers
    assert result["used_percent"] == 25
    assert result["generation_state"] == "blocked"
    assert result["included_only_verified"] is False
    assert "test-secret" not in json.dumps(result)


@pytest.mark.parametrize("status,body", [(302, b"test-secret"), (401, b"test-secret"),
    (200, b"invalid-test-secret"), (200, b"x" * (256 * 1024 + 1))])
def test_usage_rejects_redirect_error_invalid_and_oversize_without_secret(status, body):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(status, content=body, headers={"location": "https://elsewhere.invalid"})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(AiVideoError) as error:
            read_grok_subscription_usage(account_fingerprint="a" * 64,
                credential=lambda: "test-secret", client=client)
    assert len(calls) == 1
    assert "test-secret" not in str(error.value)
