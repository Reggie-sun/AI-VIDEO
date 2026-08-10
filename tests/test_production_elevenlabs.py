from __future__ import annotations

import base64
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pytest

import ai_video.production as production_root
import ai_video.production.elevenlabs as elevenlabs_module
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    VoiceCallAuthorization,
    VoiceGenerationRequest,
    VoicePricingSnapshot,
    VoiceProviderParameters,
)
from ai_video.production.elevenlabs import (
    ELEVENLABS_COMPATIBILITY,
    MAX_AUDIO_BYTES,
    ElevenLabsProviderPolicy,
    ElevenLabsTransportResponse,
    ElevenLabsVoiceProvider,
    parse_forced_alignment_response,
)
from ai_video.production.models import (
    AudioKind,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from tests.production_project_factory import make_test_voice_submit_permit


FIXTURE_ROOT = Path(__file__).parent / "fixtures/voice_captions"
ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


class _DummySecret:
    def __repr__(self) -> str:
        return "<TOP-SECRET-DUMMY>"


class _FakeTransport:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.invocations = 0
        self.calls = []

    def request(self, request):
        self.invocations += 1
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.response


class _IgnoringPermitTransport:
    """Malicious raw transport that never participates in permit security."""

    def __init__(self, response) -> None:
        self.response = response
        self.invocations = 0
        self.calls = []

    def request(self, request):
        self.invocations += 1
        self.calls.append(request)
        return self.response


def _request(**overrides) -> VoiceGenerationRequest:
    values = {
        "request_id": "request-1",
        "attempt_id": "attempt-1",
        "provider_kind": "elevenlabs",
        "model_id": "eleven_multilingual_v2",
        "audio_kind": AudioKind.DIALOGUE,
        "script_text": "Café.",
        "speaker_id": "speaker-1",
        "voice_id": "voice/one",
        "language": "fr",
        "output_container": "wav",
        "output_codec": "pcm_s16le",
        "output_sample_rate_hz": 48_000,
        "output_channels": 1,
        "provider_parameters": VoiceProviderParameters(
            stability_milli=500,
            similarity_boost_milli=750,
            use_speaker_boost=True,
        ),
        "base_project": ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{ZERO_HASH}.yaml"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        "base_registry": RegistrySnapshotPointer(
            path=Path(f"assets/registry.{ONE_HASH}.json"),
            revision_id=ONE_HASH,
            content_hash=ONE_HASH,
            file_sha256=ZERO_HASH,
        ),
        "input_artifact_ids": ("shot-1",),
        "input_fingerprint": ONE_HASH,
        "pricing_snapshot_id": "pricing-2026-08-10",
        "budget_reservation_receipt_id": "budget-1",
        "egress_authorization_receipt_id": "egress-1",
    }
    values.update(overrides)
    return VoiceGenerationRequest.create(**values)


def _pricing() -> VoicePricingSnapshot:
    return VoicePricingSnapshot(
        snapshot_id="pricing-2026-08-10",
        effective_date=date(2026, 8, 10),
        currency="USD",
        pricing_unit="character",
        unit_price_microunits=100,
        minimum_billable_units=0,
    )


def _policy(**overrides) -> ElevenLabsProviderPolicy:
    values = {
        "provider_enabled": True,
        "enable_logging": True,
        "zero_retention_entitled": False,
        "credential_reference_kind": "secret_store",
        "license_policy_decision": "test-noncommercial-attributed",
        "license_allowed": True,
        "use_policy_allowed": True,
        "voice_authorization_verified": True,
        "policy_receipt_id": "fixture-policy-receipt-1",
    }
    values.update(overrides)
    return ElevenLabsProviderPolicy(**values)


def _response(*, payload: dict | None = None, headers: dict | None = None, status=200):
    if payload is None:
        payload = json.loads(
            (FIXTURE_ROOT / "elevenlabs-with-timestamps.json").read_text(
                encoding="utf-8"
            )
        )
    return ElevenLabsTransportResponse(
        status_code=status,
        headers=headers
        or {
            "character-cost": "5",
            "request-id": "provider-request-1",
            "x-trace-id": "provider-trace-1",
        },
        body=json.dumps(payload).encode(),
    )


def _provider(transport, *, policy=None, secret=None):
    return ElevenLabsVoiceProvider(
        transport=transport,
        pricing=_pricing(),
        api_key=secret or _DummySecret(),
        policy=policy or _policy(),
    )


def _authorization(provider, request):
    preview = provider.preview(request)
    return VoiceCallAuthorization.create(
        request_fingerprint=request.voice_request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        pricing_snapshot_id=request.pricing_snapshot_id,
        budget_reservation_receipt_id=request.budget_reservation_receipt_id,
        egress_authorization_receipt_id=request.egress_authorization_receipt_id,
        destination=preview.destination,
        payload_categories=preview.payload_categories,
        cost_ceiling_microunits=preview.estimated_cost_upper_bound_microunits,
        provider_enabled=True,
    )


def _generate(provider, request, authorization, *, permit=None):
    if permit is None:
        permit = make_test_voice_submit_permit(request, authorization)
    return provider.generate(request, authorization, permit)


def test_compatibility_metadata_is_dated_and_sdk_is_reference_only():
    assert ELEVENLABS_COMPATIBILITY.checked_on == date(2026, 8, 10)
    assert ELEVENLABS_COMPATIBILITY.sdk_release == "v2.62.0"
    assert ELEVENLABS_COMPATIBILITY.sdk_license == "MIT"
    assert ELEVENLABS_COMPATIBILITY.tts_with_timestamps_path == (
        "/v1/text-to-speech/:voice_id/with-timestamps"
    )
    assert ELEVENLABS_COMPATIBILITY.forced_alignment_path == "/v1/forced-alignment"
    assert ELEVENLABS_COMPATIBILITY.auth_header == "xi-api-key"


def test_valid_submit_maps_exact_request_and_receipts_without_real_network(monkeypatch):
    network_calls = []
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: network_calls.append(a))
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: network_calls.append(a))
    secret = _DummySecret()
    transport = _FakeTransport(_response())
    provider = _provider(transport, secret=secret)
    request = _request()
    authorization = _authorization(provider, request)

    result = _generate(provider, request, authorization)

    assert network_calls == []
    assert transport.invocations == 1
    assert len(transport.calls) == 1
    sent = transport.calls[0]
    assert not hasattr(sent, "consume_permit")
    assert sent.method == "POST"
    assert sent.url == (
        "https://api.elevenlabs.io/v1/text-to-speech/voice%2Fone/with-timestamps"
    )
    assert dict(sent.query) == {"enable_logging": "true", "output_format": "pcm_48000"}
    assert sent.headers == {
        "accept": "application/json",
        "content-type": "application/json",
        "xi-api-key": secret,
    }
    assert json.loads(sent.body) == {
        "language_code": "fr",
        "model_id": "eleven_multilingual_v2",
        "text": "Café.",
        "voice_settings": {
            "similarity_boost": 0.75,
            "stability": 0.5,
            "use_speaker_boost": True,
        },
    }
    assert result.audio_bytes.startswith(b"RIFF")
    assert result.content_type == "audio/wav"
    assert result.provider_request_id == "provider-request-1"
    assert result.provider_trace_id == "provider-trace-1"
    assert result.cost_receipt.measured_billable_units == 5
    assert result.cost_receipt.provider_reported_cost_microunits is None
    alignment = json.loads(result.alignment_receipt_bytes)
    assert "alignment" in alignment and "normalized_alignment" in alignment
    assert "xi-api-key" not in repr(result)
    assert "TOP-SECRET-DUMMY" not in repr(result)


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (b"not-json", "malformed"),
        (json.dumps({"alignment": {}}).encode(), "incomplete"),
        (
            json.dumps(
                {
                    "audio_base64": "%%%",
                    "alignment": {
                        "characters": ["C"],
                        "character_start_times_seconds": [0],
                        "character_end_times_seconds": [1],
                    },
                    "normalized_alignment": {
                        "characters": ["C"],
                        "character_start_times_seconds": [0],
                        "character_end_times_seconds": [1],
                    },
                }
            ).encode(),
            "base64",
        ),
        (
            json.dumps(
                {
                    "audio_base64": "AAAA",
                    "alignment": {
                        "characters": ["C", "a"],
                        "character_start_times_seconds": [0],
                        "character_end_times_seconds": [1, 2],
                    },
                    "normalized_alignment": {
                        "characters": ["C"],
                        "character_start_times_seconds": [0],
                        "character_end_times_seconds": [1],
                    },
                }
            ).encode(),
            "parallel",
        ),
    ],
)
def test_malformed_or_partial_response_is_typed_and_secret_redacted(payload, match):
    transport = _FakeTransport(
        ElevenLabsTransportResponse(
            status_code=200,
            headers={"character-cost": "5", "request-id": "provider-request-1"},
            body=payload,
        )
    )
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError, match=match) as caught:
        _generate(provider, request, authorization)

    assert caught.value.code is ErrorCode.VOICE_PROVIDER_FAILED
    assert transport.invocations == 1
    assert len(transport.calls) == 1
    assert "TOP-SECRET-DUMMY" not in str(caught.value)
    assert "TOP-SECRET-DUMMY" not in repr(caught.value)


def test_audio_base64_decode_is_bounded_before_decode():
    oversized = base64.b64encode(b"\0" * (MAX_AUDIO_BYTES + 1)).decode()
    payload = json.loads(
        (FIXTURE_ROOT / "elevenlabs-with-timestamps.json").read_text(encoding="utf-8")
    )
    payload["audio_base64"] = oversized
    transport = _FakeTransport(_response(payload=payload))
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError, match="audio limit"):
        _generate(provider, request, authorization)

    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    ("response", "transport_error", "code"),
    [
        (_response(status=429), None, ErrorCode.VOICE_PROVIDER_FAILED),
        (None, TimeoutError("TOP-SECRET-DUMMY timeout"), ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN),
    ],
)
def test_http_and_timeout_fail_once_without_retry_or_secret(response, transport_error, code):
    transport = _FakeTransport(response, transport_error)
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)

    assert caught.value.code is code
    assert transport.invocations == 1
    assert len(transport.calls) == 1
    assert "TOP-SECRET-DUMMY" not in str(caught.value)
    assert "TOP-SECRET-DUMMY" not in repr(caught.value)


def test_transport_typed_error_is_rewrapped_without_untrusted_metadata_or_retry():
    untrusted = AiVideoError(
        code=ErrorCode.VOICE_PROVIDER_FAILED,
        user_message="TOP-SECRET-DUMMY user",
        technical_detail="TOP-SECRET-DUMMY technical",
        retryable=True,
        cause=RuntimeError("TOP-SECRET-DUMMY cause"),
    )
    transport = _FakeTransport(error=untrusted)
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)

    assert caught.value is not untrusted
    assert caught.value.code is ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN
    assert caught.value.technical_detail == (
        "Injected ElevenLabs transport failed after permit consumption."
    )
    assert caught.value.cause is None
    assert caught.value.retryable is False
    assert caught.value.__context__ is None
    assert transport.invocations == 1
    assert len(transport.calls) == 1
    assert "TOP-SECRET-DUMMY" not in str(caught.value)
    assert "TOP-SECRET-DUMMY" not in repr(caught.value)


def test_http_error_ignores_untrusted_body_and_headers():
    response = ElevenLabsTransportResponse(
        status_code=500,
        headers={"x-secret": "TOP-SECRET-DUMMY header"},
        body=b"TOP-SECRET-DUMMY body",
    )
    transport = _FakeTransport(response)
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)

    assert caught.value.code is ErrorCode.VOICE_PROVIDER_FAILED
    assert caught.value.technical_detail is None
    assert caught.value.cause is None
    assert "TOP-SECRET-DUMMY" not in str(caught.value)
    assert "TOP-SECRET-DUMMY" not in repr(caught.value)


@pytest.mark.parametrize(
    "headers",
    [
        {"request-id": "provider-request-1"},
        {
            "character-cost": "5",
            "request-id": "provider-request-1 TOP-SECRET-DUMMY",
        },
        {
            "character-cost": "5",
            "request-id": "provider-request-1",
            "x-trace-id": "TOP-SECRET-DUMMY\nraw-header",
        },
    ],
)
def test_missing_or_unsanitized_response_metadata_is_typed_and_redacted(headers):
    transport = _FakeTransport(_response(headers=headers))
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)

    assert caught.value.code is ErrorCode.VOICE_PROVIDER_FAILED
    assert "TOP-SECRET-DUMMY" not in str(caught.value)
    assert "TOP-SECRET-DUMMY" not in repr(caught.value)


@pytest.mark.parametrize(
    "permit",
    [
        None,
        "r+1",
        "stale-request",
        "mismatched-authorization",
        "mismatched-destination",
        "consumed",
    ],
)
def test_invalid_permits_are_rejected_before_transport(permit):
    transport = _FakeTransport(_response())
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    if permit is None:
        candidate = None
    elif permit == "r+1":
        candidate = make_test_voice_submit_permit(request, authorization, phase="r+1")
    elif permit == "stale-request":
        candidate = make_test_voice_submit_permit(
            request, authorization, request_fingerprint=ZERO_HASH
        )
    elif permit == "mismatched-authorization":
        candidate = make_test_voice_submit_permit(
            request, authorization, authorization_fingerprint=ZERO_HASH
        )
    elif permit == "mismatched-destination":
        candidate = make_test_voice_submit_permit(
            request, authorization, destination="https://other.invalid"
        )
    else:
        candidate = make_test_voice_submit_permit(
            request, authorization, consumed=True
        )

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, candidate)

    assert caught.value.code is ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED
    assert transport.invocations == 0
    assert transport.calls == []


def test_permit_is_one_use_and_second_submit_is_zero_transport_calls():
    first_transport = _FakeTransport(_response())
    provider = _provider(first_transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = make_test_voice_submit_permit(request, authorization)
    provider.generate(request, authorization, permit)

    second_transport = _FakeTransport(_response())
    second_provider = _provider(second_transport)
    with pytest.raises(AiVideoError):
        second_provider.generate(request, authorization, permit)
    assert second_transport.invocations == 0


def test_zero_retention_requires_entitlement_before_transport():
    transport = _FakeTransport(_response())
    provider = _provider(
        transport,
        policy=_policy(enable_logging=False, zero_retention_entitled=False),
    )
    request = _request()
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError, match="retention entitlement"):
        _generate(provider, request, authorization)
    assert transport.invocations == 0


def test_zero_retention_entitlement_emits_explicit_false_query():
    transport = _FakeTransport(_response())
    provider = _provider(
        transport,
        policy=_policy(enable_logging=False, zero_retention_entitled=True),
    )
    request = _request()
    authorization = _authorization(provider, request)
    _generate(provider, request, authorization)
    assert dict(transport.calls[0].query)["enable_logging"] == "false"


def test_provider_disabled_is_zero_transport_and_root_exports_no_adapter():
    transport = _FakeTransport(_response())
    provider = _provider(transport, policy=_policy(provider_enabled=False))
    request = _request()
    authorization = _authorization(provider, request)
    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)
    assert caught.value.code is ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED
    assert transport.invocations == 0
    assert not hasattr(production_root, "ElevenLabsVoiceProvider")
    assert not hasattr(production_root, "ElevenLabsTransport")
    assert production_root.VoiceGenerationRequest is VoiceGenerationRequest
    assert production_root.VoiceProviderResult.__name__ == "VoiceProviderResult"


@pytest.mark.parametrize(
    "override",
    [
        {"provider_enabled": "true"},
        {"enable_logging": 1},
        {"zero_retention_entitled": "false"},
        {"credential_reference_kind": "vault"},
        {"license_policy_decision": ""},
        {"license_policy_decision": "  "},
        {"license_policy_decision": "unsafe policy\nvalue"},
        {"license_policy_decision": "x" * 129},
    ],
)
def test_policy_rejects_coercion_and_malformed_values_before_transport(override):
    transport = _FakeTransport(_response())
    with pytest.raises(ValueError):
        _policy(**override)
    assert transport.invocations == 0
    assert transport.calls == []


def test_structural_permit_is_explicitly_test_only_until_task8_nominal_identity():
    assert make_test_voice_submit_permit.__module__ == "tests.production_project_factory"
    assert not hasattr(elevenlabs_module, "make_voice_submit_permit")
    assert not hasattr(elevenlabs_module, "DurableVoiceSubmitPermit")


def test_adapter_consumes_permit_without_trusting_transport_and_blocks_replay():
    transport = _IgnoringPermitTransport(_response())
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = make_test_voice_submit_permit(request, authorization)

    provider.generate(request, authorization, permit)
    with pytest.raises(AiVideoError):
        provider.generate(request, authorization, permit)

    assert transport.invocations == 1
    assert len(transport.calls) == 1


def test_adapter_atomic_consume_allows_exactly_one_transport_call_in_race():
    transport = _IgnoringPermitTransport(_response())
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = make_test_voice_submit_permit(request, authorization)

    def submit():
        try:
            provider.generate(request, authorization, permit)
            return "succeeded"
        except AiVideoError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: submit(), range(2)))

    assert outcomes.count("succeeded") == 1
    assert outcomes.count(ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED) == 1
    assert transport.invocations == 1


@pytest.mark.parametrize(
    "response",
    [
        ElevenLabsTransportResponse(status_code="200", headers={}, body=b"{}"),
        ElevenLabsTransportResponse(status_code=True, headers={}, body=b"{}"),
        ElevenLabsTransportResponse(status_code=99, headers={}, body=b"{}"),
        ElevenLabsTransportResponse(status_code=600, headers={}, body=b"{}"),
        ElevenLabsTransportResponse(status_code=200, headers={1: "x"}, body=b"{}"),
        ElevenLabsTransportResponse(
            status_code=200,
            headers={f"x-{index}": "x" for index in range(65)},
            body=b"{}",
        ),
        ElevenLabsTransportResponse(
            status_code=200,
            headers={"x-long": "x" * 1025},
            body=b"{}",
        ),
        ElevenLabsTransportResponse(status_code=200, headers={}, body="{}"),
        ElevenLabsTransportResponse(
            status_code=200,
            headers={},
            body=b"x" * (2 * 1024 * 1024 + 1),
        ),
        ElevenLabsTransportResponse(
            status_code=200,
            headers={"character-cost": "5", "request-id": "request-1"},
            body=b'{"audio_base64":"AAAA","alignment":{"characters":[1e999999]},'
            b'"normalized_alignment":{},"padding":'
            + (b"9" * 5000)
            + b"}",
        ),
    ],
)
def test_transport_response_types_and_json_numeric_tokens_are_bounded(response):
    transport = _FakeTransport(response)
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)
    assert caught.value.code is ErrorCode.VOICE_PROVIDER_FAILED
    assert caught.value.cause is None
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "character_cost",
    [" 5", "+5", "05", "9" * 1000],
)
def test_character_cost_requires_bounded_canonical_decimal(character_cost):
    transport = _FakeTransport(
        _response(
            headers={
                "character-cost": character_cost,
                "request-id": "provider-request-1",
            }
        )
    )
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)
    assert caught.value.code is ErrorCode.VOICE_PROVIDER_FAILED


def test_malformed_json_error_graph_does_not_retain_provider_body():
    secret = "TOP-SECRET-DUMMY-JSON-BODY"
    transport = _FakeTransport(
        ElevenLabsTransportResponse(
            status_code=200,
            headers={"character-cost": "5", "request-id": "request-1"},
            body=f'{{"audio_base64":"{secret}"'.encode(),
        )
    )
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    with pytest.raises(AiVideoError) as caught:
        _generate(provider, request, authorization)

    graph = []
    pending = [caught.value]
    seen = set()
    while pending:
        error = pending.pop()
        if id(error) in seen:
            continue
        seen.add(id(error))
        graph.extend(
            str(value)
            for value in (
                error,
                repr(error),
                getattr(error, "user_message", None),
                getattr(error, "technical_detail", None),
                getattr(error, "doc", None),
            )
            if value is not None
        )
        pending.extend(
            value
            for value in (error.__cause__, error.__context__)
            if isinstance(value, BaseException)
        )
    assert secret not in "\n".join(graph)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_machine_policy_denial_is_zero_call_and_does_not_consume_permit():
    denied = ElevenLabsProviderPolicy(
        provider_enabled=True,
        enable_logging=True,
        zero_retention_entitled=False,
        credential_reference_kind="secret_store",
        license_policy_decision="fixture-policy-allowed",
        license_allowed=False,
        use_policy_allowed=True,
        voice_authorization_verified=True,
        policy_receipt_id="policy-receipt-1",
    )
    transport = _IgnoringPermitTransport(_response())
    denied_provider = _provider(transport, policy=denied)
    request = _request()
    authorization = _authorization(denied_provider, request)
    permit = make_test_voice_submit_permit(request, authorization)
    with pytest.raises(AiVideoError):
        denied_provider.generate(request, authorization, permit)
    assert transport.invocations == 0

    allowed = ElevenLabsProviderPolicy(
        provider_enabled=True,
        enable_logging=True,
        zero_retention_entitled=False,
        credential_reference_kind="secret_store",
        license_policy_decision="fixture-policy-allowed",
        license_allowed=True,
        use_policy_allowed=True,
        voice_authorization_verified=True,
        policy_receipt_id="policy-receipt-1",
    )
    _provider(transport, policy=allowed).generate(request, authorization, permit)
    assert transport.invocations == 1


@pytest.mark.parametrize(
    "override",
    [
        {"license_allowed": "true"},
        {"use_policy_allowed": 1},
        {"voice_authorization_verified": "yes"},
        {"policy_receipt_id": ""},
        {"policy_receipt_id": "unsafe receipt\nvalue"},
        {"policy_receipt_id": "x" * 129},
    ],
)
def test_machine_policy_fields_reject_coercion_and_malformed_receipts(override):
    values = {
        "provider_enabled": True,
        "enable_logging": True,
        "zero_retention_entitled": False,
        "credential_reference_kind": "secret_store",
        "license_policy_decision": "fixture-policy-allowed",
        "license_allowed": True,
        "use_policy_allowed": True,
        "voice_authorization_verified": True,
        "policy_receipt_id": "policy-receipt-1",
    }
    values.update(override)
    with pytest.raises(ValueError):
        ElevenLabsProviderPolicy(**values)


def test_forced_alignment_fixture_is_strict_and_preserves_loss_without_confidence():
    payload = (FIXTURE_ROOT / "elevenlabs-forced-alignment.json").read_bytes()
    parsed = json.loads(parse_forced_alignment_response(payload))
    assert parsed["loss"] == "0.125"
    assert parsed["words"][0]["loss"] == "0.125"
    assert "confidence" not in parsed
