from __future__ import annotations

import importlib
import io
import json
import wave
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    VoiceCallAuthorization,
    VoiceGenerationRequest,
    VoicePricingSnapshot,
    VoiceProviderParameters,
)
from ai_video.production.models import (
    ActorIdentity,
    AudioKind,
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    SecretReference,
)
from ai_video.production.state_commit import ProductionStateCommitter
from tests import production_project_factory as project_factory


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def _module():
    try:
        return importlib.import_module("ai_video.production.minimax_speech")
    except ModuleNotFoundError:
        pytest.fail("MiniMax Speech adapter is not implemented", pytrace=False)


class _DummySecret:
    RAW = "TOP-SECRET-DUMMY-MINIMAX-SPEECH"

    def bearer_header(self) -> str:
        return f"Bearer {self.RAW}"

    def __repr__(self) -> str:
        return "<MINIMAX-SPEECH-SECRET>"


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


def _wav_bytes(*, sample_rate: int = 44_100, channels: int = 1) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(channels)
        target.setsampwidth(2)
        target.setframerate(sample_rate)
        target.writeframes(b"\0\0" * channels * 100)
    return output.getvalue()


def _request(**overrides) -> VoiceGenerationRequest:
    values = {
        "request_id": "speech-request-1",
        "attempt_id": "speech-attempt-1",
        "provider_kind": "minimax-speech",
        "model_id": "speech-2.8-hd",
        "audio_kind": AudioKind.NARRATION,
        "script_text": "Inside the old library, every shelf guarded a forgotten secret.",
        "speaker_id": "narrator-1",
        "voice_id": "English_expressive_narrator",
        "language": "English",
        "output_container": "wav",
        "output_codec": "pcm_s16le",
        "output_sample_rate_hz": 44_100,
        "output_channels": 1,
        "provider_parameters": VoiceProviderParameters(speed_milli=1000),
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
        "pricing_snapshot_id": "minimax-token-plan-2026-08-19",
        "budget_reservation_receipt_id": "speech-budget-1",
        "egress_authorization_receipt_id": "speech-egress-1",
    }
    values.update(overrides)
    return VoiceGenerationRequest.create(**values)


def _pricing() -> VoicePricingSnapshot:
    return VoicePricingSnapshot(
        snapshot_id="minimax-token-plan-2026-08-19",
        effective_date=date(2026, 8, 19),
        currency="USD",
        pricing_unit="character",
        unit_price_microunits=0,
        minimum_billable_units=0,
    )


def _policy(**overrides):
    module = _module()
    values = {
        "provider_enabled": True,
        "credential_reference_kind": "environment",
        "credential_reference_id": "MINIMAX_SPEECH_API_KEY",
        "retention_mode": "provider_standard",
        "license_policy_decision": "authorized-token-plan-speech",
        "license_allowed": True,
        "use_policy_allowed": True,
        "voice_authorization_verified": True,
        "policy_receipt_id": "minimax-speech-policy-2026-08-19",
    }
    values.update(overrides)
    return module.MiniMaxSpeechProviderPolicy(**values)


def _response(*, audio: bytes | None = None, status: int = 200, mutate=None):
    module = _module()
    audio = audio or _wav_bytes()
    payload = {
        "data": {"audio": audio.hex(), "status": 2},
        "extra_info": {
            "audio_length": 3,
            "audio_sample_rate": 44_100,
            "audio_size": len(audio),
            "bitrate": 705_600,
            "word_count": 10,
            "invisible_character_ratio": 0,
            "usage_characters": 63,
            "audio_format": "wav",
            "audio_channel": 1,
        },
        "trace_id": "minimax-trace-1",
        "base_resp": {"status_code": 0, "status_msg": "success"},
    }
    if mutate is not None:
        mutate(payload)
    return module.MiniMaxSpeechTransportResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=json.dumps(payload).encode(),
    )


def _provider(transport, *, policy=None, secret=None):
    module = _module()
    return module.MiniMaxSpeechVoiceProvider(
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


def _issue_real_permit(root: Path, provider, request, authorization):
    project_factory.write_production_project(root)
    manifest_path = root / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
    manifest = manifest.model_copy(
        update={
            "active_project": request.base_project,
            "active_registry": request.base_registry,
        }
    )
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    preview = provider.preview(request)
    paid_preview = PaidProviderCallPreview.create(
        attempt_id=request.attempt_id,
        operation="voice_generation",
        provider_kind=request.provider_kind,
        model_id=request.model_id,
        request_fingerprint=request.voice_request_fingerprint,
        billing_mode="remote_metered",
        currency=preview.currency,
        estimated_cost_upper_bound_microunits=(
            preview.estimated_cost_upper_bound_microunits
        ),
        destination=preview.destination,
        method="POST",
        egress_items=(
            PaidProviderEgressItem(
                item_id="script",
                sha256=request.script_hash,
                size_bytes=len(request.script_text.encode("utf-8")),
                mime_type="text/plain",
                purpose="script",
            ),
        ),
        retention_mode=provider._policy.retention_mode,
        provider_policy_snapshot_id=provider._policy.policy_receipt_id,
        secret_reference=SecretReference(
            kind=provider._policy.credential_reference_kind,
            reference_id=provider._policy.credential_reference_id,
        ),
    )
    now = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
    paid_authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=paid_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="test-speech-opt-in",
        budget_policy_id="test-speech-budget",
        budget_currency=preview.currency,
        project_budget_ceiling_microunits=1,
        per_call_ceiling_microunits=0,
        egress_authorized=True,
        egress_policy_receipt_id="test-speech-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="test-speech-live",
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
        max_submit_count=1,
    )
    committer = ProductionStateCommitter(
        root,
        paid_provider_authorizer=lambda exact: (
            paid_authorization if exact == paid_preview else None
        ),
        paid_provider_clock=lambda: now,
    )
    committer.begin_voice_generation(request, preview, authorization)
    committer.record_voice_submit_intent(request, preview, authorization)
    return committer.record_paid_provider_submit_intent(
        paid_preview,
        reservation_id=f"paid-{request.attempt_id}",
    )


def test_exact_request_and_successful_wav_result_use_real_paid_permit(tmp_path):
    transport = _FakeTransport(_response())
    secret = _DummySecret()
    provider = _provider(transport, secret=secret)
    request = _request()
    authorization = _authorization(provider, request)
    permit = _issue_real_permit(tmp_path, provider, request, authorization)

    result = provider.generate(request, authorization, permit)

    assert transport.invocations == 1
    sent = transport.calls[0]
    assert sent.method == "POST"
    assert sent.url == "https://api.minimax.io/v1/t2a_v2"
    assert sent.headers == {
        "authorization": f"Bearer {secret.RAW}",
        "content-type": "application/json",
    }
    assert secret.RAW not in repr(sent)
    assert secret.RAW.encode() not in sent.body
    assert json.loads(sent.body) == {
        "audio_setting": {
            "channel": 1,
            "format": "wav",
            "sample_rate": 44_100,
        },
        "language_boost": "English",
        "model": "speech-2.8-hd",
        "output_format": "hex",
        "stream": False,
        "subtitle_enable": False,
        "text": request.script_text,
        "voice_setting": {
            "pitch": 0,
            "speed": 1.0,
            "voice_id": "English_expressive_narrator",
            "vol": 1,
        },
    }
    assert result.audio_bytes.startswith(b"RIFF")
    assert result.provider_request_id == "minimax-trace-1"
    assert result.cost_receipt.measured_billable_units == 63
    assert result.provenance_receipt.alignment_mode == "none"


def test_bounded_decimal_metadata_from_official_response_is_accepted(tmp_path):
    transport = _FakeTransport(
        _response(
            mutate=lambda payload: payload["extra_info"].update(
                invisible_character_ratio=0.0
            )
        )
    )
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = _issue_real_permit(tmp_path, provider, request, authorization)

    result = provider.generate(request, authorization, permit)

    assert result.audio_bytes.startswith(b"RIFF")
    assert transport.invocations == 1


def test_adapter_consumes_paid_permit_once_and_blocks_replay(tmp_path):
    transport = _FakeTransport(_response())
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = _issue_real_permit(tmp_path, provider, request, authorization)

    provider.generate(request, authorization, permit)
    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, permit)

    assert caught.value.code is ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED
    assert transport.invocations == 1


def test_unsupported_48khz_request_fails_before_transport(tmp_path):
    transport = _FakeTransport(_response())
    provider = _provider(transport)
    request = _request(output_sample_rate_hz=48_000)
    authorization = _authorization(provider, request)

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, object())

    assert caught.value.code is ErrorCode.VOICE_REQUEST_INVALID
    assert transport.invocations == 0


def test_script_character_limit_fails_before_transport(tmp_path):
    transport = _FakeTransport(_response())
    provider = _provider(transport)
    accepted = _request(script_text="x" * 9_999)
    rejected = _request(script_text="x" * 10_000)

    assert provider.preview(accepted).output_supported is True
    assert provider.preview(rejected).output_supported is False
    with pytest.raises(AiVideoError) as caught:
        provider.generate(rejected, _authorization(provider, rejected), object())

    assert caught.value.code is ErrorCode.VOICE_REQUEST_INVALID
    assert transport.invocations == 0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload["data"].update(status=1),
        lambda payload: payload["data"].update(status=2.0),
        lambda payload: payload["extra_info"].update(audio_sample_rate=32_000),
        lambda payload: payload["extra_info"].update(audio_channel=2),
        lambda payload: payload["extra_info"].update(audio_channel=True),
        lambda payload: payload["extra_info"].update(audio_format="mp3"),
        lambda payload: payload["extra_info"].update(usage_characters=10_000),
        lambda payload: payload["base_resp"].update(status_code=1008),
        lambda payload: payload["base_resp"].update(status_code=False),
        lambda payload: payload["extra_info"].update(bitrate="705600"),
        lambda payload: payload["extra_info"].update(word_count="10"),
        lambda payload: payload["extra_info"].update(
            invisible_character_ratio="0"
        ),
        lambda payload: payload["data"].update(audio="not-hex"),
    ],
)
def test_tampered_or_contradictory_response_is_outcome_unknown(tmp_path, mutate):
    transport = _FakeTransport(_response(mutate=mutate))
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = _issue_real_permit(tmp_path, provider, request, authorization)

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, permit)

    assert caught.value.code is ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN
    assert transport.invocations == 1
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_machine_policy_denial_is_zero_call_and_does_not_consume_permit(tmp_path):
    transport = _FakeTransport(_response())
    denied = _provider(transport, policy=_policy(use_policy_allowed=False))
    request = _request()
    authorization = _authorization(denied, request)
    permit = _issue_real_permit(tmp_path, denied, request, authorization)

    with pytest.raises(AiVideoError) as caught:
        denied.generate(request, authorization, permit)

    assert caught.value.code is ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED
    assert transport.invocations == 0
    allowed = _provider(transport)
    allowed.generate(request, authorization, permit)
    assert transport.invocations == 1


def test_transport_failure_after_permit_consumption_is_outcome_unknown(tmp_path):
    transport = _FakeTransport(error=RuntimeError("secret response body"))
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = _issue_real_permit(tmp_path, provider, request, authorization)

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, permit)

    assert caught.value.code is ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_2049_error_envelope_is_fail_closed_and_exact_permit_cannot_replay(tmp_path):
    module = _module()
    transport = _FakeTransport(
        module.MiniMaxSpeechTransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps(
                {"base_resp": {"status_code": 2049, "status_msg": "invalid api key"}}
            ).encode(),
        )
    )
    provider = _provider(transport)
    request = _request()
    authorization = _authorization(provider, request)
    permit = _issue_real_permit(tmp_path, provider, request, authorization)

    with pytest.raises(AiVideoError) as first:
        provider.generate(request, authorization, permit)
    with pytest.raises(AiVideoError) as replay:
        provider.generate(request, authorization, permit)

    assert first.value.code is ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN
    assert replay.value.code is ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED
    assert transport.invocations == 1


def test_official_compatibility_snapshot_is_exact():
    compatibility = _module().MINIMAX_SPEECH_COMPATIBILITY
    assert compatibility.auth_scheme == "Bearer"
    assert compatibility.endpoint_path == "/v1/t2a_v2"
    assert compatibility.output_format == "hex-wav"
    assert compatibility.supported_sample_rates_hz == (
        8_000,
        16_000,
        22_050,
        24_000,
        32_000,
        44_100,
    )


@pytest.mark.parametrize(
    "override",
    [
        {"provider_enabled": "true"},
        {"credential_reference_id": ""},
        {"credential_reference_id": "unsafe\nreference"},
        {"retention_mode": "unknown"},
        {"policy_receipt_id": ""},
    ],
)
def test_policy_rejects_coercion_and_malformed_values(override):
    with pytest.raises(ValueError):
        _policy(**override)
