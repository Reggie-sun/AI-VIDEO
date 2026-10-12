import json

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.seedance_rejection import submit_rejection_message
from ai_video.production.seedance import SeedanceTransportResponse, SeedanceVideoProvider
from test_production_seedance import (
    FIXED_NOW, _FakeTransport, _authorization, _paid_preview,
    _permit, _profile, _provider_asset_reference, _request,
)


@pytest.mark.parametrize("code", [
    "InputImageSensitiveContentDetected.PrivacyInformation",
    "InvalidParameter", "AccountOverdueError", "AuthenticationError",
])
def test_rejection_exposes_only_known_code_and_named_parameter(code):
    body = json.dumps({"error": {"code": code, "message":
        "The parameter `content` is invalid: secret-token https://private/?key=secret "
        "data:image/png;base64,secret Request ID: private-account"}}).encode()
    message = submit_rejection_message(400, body)
    assert code in message
    assert "content" in message
    for secret in ("secret", "https://", "data:", "private-account", "Request ID"):
        assert secret not in message


@pytest.mark.parametrize("body", [
    b"invalid secret", b"\xff", b"[]", b"null",
    b'{"error": {"code": "unknown-secret", "message": "secret"}}',
    b'{"error": {"code": ["secret"]}}',
    b'{"error": {"code": "InvalidParameter", "message": "secret"}}' + b" " * 65536,
])
def test_untrusted_rejection_falls_back_to_http_without_body(body):
    assert submit_rejection_message(400, body) == "Seedance submit was rejected with HTTP 400."


@pytest.mark.parametrize("status,expected", [
    (400, ErrorCode.VIDEO_PROVIDER_FAILED),
    (403, ErrorCode.VIDEO_PROVIDER_FAILED),
    (429, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN),
    (500, ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN),
])
def test_submit_keeps_outcome_and_consumed_permit_without_retry(status, expected):
    profile, transport = _profile(), _FakeTransport()
    body = json.dumps({"error": {"code": "InvalidParameter",
        "message": "The parameter `duration` is invalid secret-token"}}).encode()
    transport.responses.append(SeedanceTransportResponse(status, {}, body))
    provider = SeedanceVideoProvider(profile=profile, transport=transport,
        credential=lambda: "secret-token", input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW)
    request = provider.resolve(_request(profile))
    video = provider.preview(request)
    paid = _paid_preview(request, video)
    auth = _authorization(paid)
    permit = _permit(request, video, paid, auth)
    with pytest.raises(AiVideoError) as failure:
        provider.submit(request, video, paid, auth, permit)
    assert failure.value.code is expected
    assert "secret-token" not in str(failure.value)
    if status in (400, 403):
        assert "InvalidParameter" in str(failure.value)
        assert "duration" in str(failure.value)
    with pytest.raises(AiVideoError):
        provider.submit(request, video, paid, auth, permit)
    assert len(transport.requests) == 1
