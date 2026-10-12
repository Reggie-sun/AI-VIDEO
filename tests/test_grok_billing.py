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


def test_included_only_authority_reopens_real_boundaries_and_rejects_changed_rules():
    from datetime import UTC, datetime
    from ai_video.production.grok_billing import GrokIncludedOnlyAuthority
    calls = []
    topup = [{}]
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=(topup[0] if request.url.path.endswith('auto-topup-rule')
            else {"config": {"creditUsagePercent": 8, "isUnifiedBillingUser": True,
                "onDemandCap": {"val": 0}, "onDemandUsed": {"val": 0},
                "prepaidBalance": {"val": 0},
                "currentPeriod": {"type": "WEEKLY", "end": "2026-10-19T00:00:00Z"}}}))
    with httpx.Client(transport=httpx.MockTransport(respond), auth=('wrong', 'private'),
            cookies={'session': 'private'}) as client:
        authority = GrokIncludedOnlyAuthority(account_fingerprint='a' * 64,
            credential=lambda: 'test-secret', client=client,
            now=lambda: datetime(2026, 10, 12, tzinfo=UTC))
        binding = authority.observe(model_id='grok-imagine-video',
            operation_path='/v1/videos/generations')
        authority(binding)
        assert len(calls) == 4
        topup[0] = {"rule": {"enabled": True}}
        with pytest.raises(AiVideoError):
            authority(binding)
    assert binding.used_percent == 8
    assert binding.included_only_evidence_id.startswith('grok-included-only:')
    assert all(req.method == 'GET' and req.url.host == 'cli-chat-proxy.grok.com'
        and req.headers['authorization'] == 'Bearer test-secret'
        and 'cookie' not in req.headers for req in calls)


@pytest.mark.parametrize('field,value', [
    ('onDemandCap', {'val': 1}), ('onDemandUsed', {'val': 1}),
    ('prepaidBalance', {'val': -1}), ('onDemandCap', {}),
    ('onDemandCap', {'val': False}), ('onDemandCap', {'val': '0'}),
    ('isUnifiedBillingUser', False), ('isUnifiedBillingUser', None),
    ('creditUsagePercent', 100), ('creditUsagePercent', float('nan')),
    ('currentPeriod', {'type':'WEEKLY', 'end':'2026-10-11T00:00:00Z'}),
])
def test_included_only_authority_rejects_unverified_or_nonzero_fields(field, value):
    from datetime import UTC, datetime
    from ai_video.production.grok_billing import GrokIncludedOnlyAuthority
    config = {"creditUsagePercent": 8, "isUnifiedBillingUser": True,
        "onDemandCap": {"val": 0}, "onDemandUsed": {"val": 0},
        "prepaidBalance": {"val": 0},
        "currentPeriod": {"type": "WEEKLY", "end": "2026-10-19T00:00:00Z"}}
    config[field] = value
    def respond(request):
        return httpx.Response(200, json={} if request.url.path.endswith('auto-topup-rule')
            else {"config":config})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        authority = GrokIncludedOnlyAuthority(account_fingerprint='a' * 64,
            credential=lambda:'test-secret', client=client,
            now=lambda:datetime(2026, 10, 12, tzinfo=UTC))
        with pytest.raises(AiVideoError) as error:
            authority.observe(model_id='grok-imagine-video', operation_path='/v1/videos/generations')
    assert 'test-secret' not in str(error.value)


@pytest.mark.parametrize('topup,accepted', [
    ({}, True), ({'rule':None}, True), ({'rule':{}}, True),
    ({'rule':{'enabled':False}}, True), ({'rule':{'enabled':True}}, False),
    ({'rule':{'enabled':0}}, False), ({'rule':{'unexpected':False}}, False),
    ({'unexpected':False}, False), ([], False),
])
def test_included_only_authority_distinguishes_known_disabled_from_unknown_schema(topup, accepted):
    from datetime import UTC, datetime
    from ai_video.production.grok_billing import GrokIncludedOnlyAuthority
    def respond(request):
        return httpx.Response(200, json=topup if request.url.path.endswith('auto-topup-rule') else
            {'config':{'creditUsagePercent':8,'isUnifiedBillingUser':True,
                'onDemandCap':{'val':0},'onDemandUsed':{'val':0},'prepaidBalance':{'val':0},
                'currentPeriod':{'type':'WEEKLY','end':'2026-10-19T00:00:00Z'}}})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        authority = GrokIncludedOnlyAuthority(account_fingerprint='a' * 64,
            credential=lambda:'test-secret',client=client,
            now=lambda:datetime(2026,10,12,tzinfo=UTC))
        if accepted:
            authority.observe(model_id='grok-imagine-video',operation_path='/v1/videos/generations')
        else:
            with pytest.raises(AiVideoError):
                authority.observe(model_id='grok-imagine-video',operation_path='/v1/videos/generations')


def test_included_only_authority_rejects_invalid_model_before_credentials():
    from ai_video.production.grok_billing import GrokIncludedOnlyAuthority
    def forbidden():
        raise AssertionError('must not read credentials')
    authority = GrokIncludedOnlyAuthority(account_fingerprint='a' * 64,credential=forbidden)
    with pytest.raises(AiVideoError):
        authority.observe(model_id='unknown',operation_path='/v1/videos/generations')
