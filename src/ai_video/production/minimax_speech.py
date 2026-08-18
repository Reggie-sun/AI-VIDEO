"""Explicit MiniMax Speech adapter for the provider-neutral P4 voice contract."""

from __future__ import annotations

import binascii
import io
import json
import re
import wave
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    VoiceCallAuthorization,
    VoiceCostReceipt,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoicePricingSnapshot,
    VoiceProviderResult,
    VoiceProvenanceReceipt,
    build_voice_generation_preview,
    validate_voice_call_authorization,
)
from ai_video.production.models import ToolIdentity
from ai_video.production.state_commit import _DurablePaidProviderSubmitPermit


_ORIGIN = "https://api.minimax.io"
_T2A_PATH = "/v1/t2a_v2"
_SUPPORTED_MODELS = frozenset({"speech-2.8-hd", "speech-2.8-turbo"})
_SUPPORTED_SAMPLE_RATES = frozenset({8_000, 16_000, 22_050, 24_000, 32_000, 44_100})
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SAFE_PROVIDER_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]{1,128}$")
_MAX_AUDIO_BYTES = 4 * 1024 * 1024
_MAX_RESPONSE_BYTES = 6 * 1024 * 1024
_MAX_RESPONSE_HEADERS = 64
_MAX_HEADER_VALUE_LENGTH = 1024


@dataclass(frozen=True)
class MiniMaxSpeechCompatibility:
    checked_on: date
    endpoint_path: str
    auth_scheme: str
    output_format: str
    supported_sample_rates_hz: tuple[int, ...]


MINIMAX_SPEECH_COMPATIBILITY = MiniMaxSpeechCompatibility(
    checked_on=date(2026, 8, 19),
    endpoint_path=_T2A_PATH,
    auth_scheme="Bearer",
    output_format="hex-wav",
    supported_sample_rates_hz=tuple(sorted(_SUPPORTED_SAMPLE_RATES)),
)


@dataclass(frozen=True)
class MiniMaxSpeechProviderPolicy:
    provider_enabled: bool
    credential_reference_kind: Literal["environment", "secret_store"]
    credential_reference_id: str
    retention_mode: Literal["provider_standard", "zero_retention"]
    license_policy_decision: str
    license_allowed: bool
    use_policy_allowed: bool
    voice_authorization_verified: bool
    policy_receipt_id: str

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (
                self.provider_enabled,
                self.license_allowed,
                self.use_policy_allowed,
                self.voice_authorization_verified,
            )
        ):
            raise ValueError("MiniMax Speech policy flags must be exact booleans")
        if (
            type(self.credential_reference_kind) is not str
            or self.credential_reference_kind not in {"environment", "secret_store"}
        ):
            raise ValueError("MiniMax Speech credential reference kind is invalid")
        for value, label in (
            (self.credential_reference_id, "credential reference identity"),
            (self.license_policy_decision, "license policy decision"),
            (self.policy_receipt_id, "policy receipt identity"),
        ):
            if type(value) is not str or _SAFE_ID.fullmatch(value) is None:
                raise ValueError(f"MiniMax Speech {label} is invalid")
        if (
            type(self.retention_mode) is not str
            or self.retention_mode not in {"provider_standard", "zero_retention"}
        ):
            raise ValueError("MiniMax Speech retention mode is invalid")


@dataclass(frozen=True)
class MiniMaxSpeechTransportRequest:
    method: Literal["POST"]
    url: str
    headers: Mapping[str, object] = field(repr=False)
    body: bytes = field(repr=False)


@dataclass(frozen=True)
class MiniMaxSpeechTransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes = field(repr=False)


class MiniMaxSpeechTransport(Protocol):
    """Injected raw transport; permit security remains adapter-owned."""

    def request(
        self, request: MiniMaxSpeechTransportRequest
    ) -> MiniMaxSpeechTransportResponse: ...


class MiniMaxSpeechCredential(Protocol):
    """Opaque secret capability; the returned header is never modeled or persisted."""

    def bearer_header(self) -> str: ...


def _error(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=None,
        retryable=False,
    )


def _outcome_unknown() -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN,
        user_message="MiniMax Speech submit outcome is unknown.",
        technical_detail=None,
        retryable=False,
    )


def _permit_binding(
    request: VoiceGenerationRequest,
    authorization: VoiceCallAuthorization,
    preview: VoiceGenerationPreview,
    policy: MiniMaxSpeechProviderPolicy,
) -> dict[str, str]:
    return {
        "attempt_id": request.attempt_id,
        "operation": "voice_generation",
        "request_fingerprint": request.voice_request_fingerprint,
        "destination": authorization.destination,
        "provider_kind": request.provider_kind,
        "model_id": request.model_id,
        "currency": preview.currency,
        "estimated_cost_upper_bound_microunits": str(
            preview.estimated_cost_upper_bound_microunits
        ),
        "provider_policy_snapshot_id": policy.policy_receipt_id,
        "retention_mode": policy.retention_mode,
        "secret_reference_kind": policy.credential_reference_kind,
        "secret_reference_id": policy.credential_reference_id,
    }


def _permit_is_valid(permit: object, binding: dict[str, str]) -> bool:
    if type(permit) is not _DurablePaidProviderSubmitPermit:
        return False
    try:
        return permit._validate_paid_provider_operation_permit(**binding) is True
    except Exception:
        return False


def _consume_permit(permit: object, binding: dict[str, str]) -> bool:
    if type(permit) is not _DurablePaidProviderSubmitPermit:
        return False
    try:
        return permit._consume_paid_provider_operation_permit(**binding) is True
    except Exception:
        return False


def _request_is_supported(request: VoiceGenerationRequest) -> bool:
    parameters = request.provider_parameters
    return (
        request.provider_kind == "minimax-speech"
        and request.model_id in _SUPPORTED_MODELS
        and request.output_container == "wav"
        and request.output_codec == "pcm_s16le"
        and request.output_sample_rate_hz in _SUPPORTED_SAMPLE_RATES
        and request.output_channels in {1, 2}
        and request.language == "English"
        and len(request.script_text) < 10_000
        and parameters.stability_milli is None
        and parameters.similarity_boost_milli is None
        and parameters.style_milli is None
        and parameters.use_speaker_boost is None
    )


def _request_body(request: VoiceGenerationRequest) -> bytes:
    speed = request.provider_parameters.speed_milli
    return json.dumps(
        {
            "audio_setting": {
                "channel": request.output_channels,
                "format": "wav",
                "sample_rate": request.output_sample_rate_hz,
            },
            "language_boost": request.language,
            "model": request.model_id,
            "output_format": "hex",
            "stream": False,
            "subtitle_enable": False,
            "text": request.script_text,
            "voice_setting": {
                "pitch": 0,
                "speed": (speed if speed is not None else 1000) / 1000,
                "voice_id": request.voice_id,
                "vol": 1,
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _authorization_header(secret: object) -> str:
    method = getattr(secret, "bearer_header", None)
    if not callable(method):
        raise _error(
            ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
            "MiniMax Speech credential capability is unavailable.",
        )
    try:
        value = method()
    except Exception:
        raise _error(
            ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
            "MiniMax Speech credential capability is unavailable.",
        ) from None
    if (
        type(value) is not str
        or not value.startswith("Bearer ")
        or len(value) <= len("Bearer ")
        or len(value) > 2048
        or not value.isascii()
        or any(character in value for character in "\r\n\0")
    ):
        raise _error(
            ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
            "MiniMax Speech credential capability is invalid.",
        )
    return value


def _validate_transport_response(response: object) -> MiniMaxSpeechTransportResponse:
    if type(response) is not MiniMaxSpeechTransportResponse:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech transport response type is invalid.",
        )
    if (
        type(response.status_code) is not int
        or response.status_code < 100
        or response.status_code > 599
    ):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response status is invalid.",
        )
    if type(response.headers) is not dict or len(response.headers) > (
        _MAX_RESPONSE_HEADERS
    ):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response headers are invalid.",
        )
    for name, value in response.headers.items():
        if (
            type(name) is not str
            or _HEADER_NAME.fullmatch(name) is None
            or type(value) is not str
            or not value.isascii()
            or len(value) > _MAX_HEADER_VALUE_LENGTH
        ):
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                "MiniMax Speech response headers are invalid.",
            )
    if (
        type(response.body) is not bytes
        or not response.body
        or len(response.body) > _MAX_RESPONSE_BYTES
    ):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response body is invalid.",
        )
    return response


def _bounded_int(token: str) -> int:
    if len(token) > 20:
        raise ValueError("integer token is too large")
    return int(token)


def _bounded_decimal(token: str) -> Decimal:
    if len(token) > 64:
        raise ValueError("decimal token is too large")
    try:
        value = Decimal(token)
    except InvalidOperation:
        raise ValueError("decimal token is invalid") from None
    if not value.is_finite() or abs(value) > Decimal("1000000000"):
        raise ValueError("decimal token is out of range")
    return value


def _parse_json(body: bytes) -> dict[str, object]:
    try:
        payload = json.loads(
            body,
            parse_int=_bounded_int,
            parse_float=_bounded_decimal,
            parse_constant=lambda _token: (_ for _ in ()).throw(
                ValueError("non-finite values are not accepted")
            ),
        )
    except Exception:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response JSON is malformed.",
        ) from None
    if not isinstance(payload, dict):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response is incomplete.",
        )
    return payload


def _decode_wav(value: object, request: VoiceGenerationRequest) -> bytes:
    if not isinstance(value, str) or not value or len(value) > _MAX_AUDIO_BYTES * 2:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response audio is invalid.",
        )
    try:
        audio = bytes.fromhex(value)
    except (ValueError, binascii.Error):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response contains malformed hex audio.",
        ) from None
    if not audio or len(audio) > _MAX_AUDIO_BYTES:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response exceeds the audio limit.",
        )
    try:
        with wave.open(io.BytesIO(audio), "rb") as source:
            valid = (
                source.getcomptype() == "NONE"
                and source.getsampwidth() == 2
                and source.getframerate() == request.output_sample_rate_hz
                and source.getnchannels() == request.output_channels
                and source.getnframes() > 0
            )
    except (EOFError, wave.Error):
        valid = False
    if not valid:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response WAV does not match the requested PCM contract.",
        )
    return audio


def _parse_result(
    body: bytes,
    request: VoiceGenerationRequest,
    preview: VoiceGenerationPreview,
) -> tuple[bytes, int, str]:
    payload = _parse_json(body)
    if set(payload) != {"data", "extra_info", "trace_id", "base_resp"}:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response is incomplete.",
        )
    data = payload["data"]
    extra = payload["extra_info"]
    base = payload["base_resp"]
    trace_id = payload["trace_id"]
    if (
        not isinstance(data, dict)
        or set(data) != {"audio", "status"}
        or type(data.get("status")) is not int
        or data["status"] != 2
        or not isinstance(extra, dict)
        or not isinstance(base, dict)
        or type(base.get("status_code")) is not int
        or base["status_code"] != 0
        or not isinstance(trace_id, str)
        or _SAFE_PROVIDER_ID.fullmatch(trace_id) is None
    ):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response status or identity is invalid.",
        )
    required_extra = {
        "audio_length",
        "audio_sample_rate",
        "audio_size",
        "bitrate",
        "word_count",
        "invisible_character_ratio",
        "usage_characters",
        "audio_format",
        "audio_channel",
    }
    if set(extra) != required_extra:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response metadata is incomplete.",
        )
    audio = _decode_wav(data["audio"], request)
    usage = extra["usage_characters"]
    invisible_character_ratio = extra["invisible_character_ratio"]
    if (
        type(extra["audio_length"]) is not int
        or extra["audio_length"] <= 0
        or type(extra["audio_size"]) is not int
        or extra["audio_size"] != len(audio)
        or type(extra["audio_sample_rate"]) is not int
        or extra["audio_sample_rate"] != request.output_sample_rate_hz
        or type(extra["audio_channel"]) is not int
        or extra["audio_channel"] != request.output_channels
        or extra["audio_format"] != "wav"
        or type(extra["bitrate"]) is not int
        or extra["bitrate"] <= 0
        or type(extra["word_count"]) is not int
        or extra["word_count"] < 0
        or type(invisible_character_ratio) not in {int, Decimal}
        or not Decimal(0) <= invisible_character_ratio <= Decimal(1)
        or type(usage) is not int
        or usage <= 0
        or usage > preview.billable_units_upper_bound
    ):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "MiniMax Speech response metadata contradicts the request.",
        )
    return audio, usage, trace_id


class MiniMaxSpeechVoiceProvider:
    """Explicit opt-in REST adapter with no implicit client or network transport."""

    def __init__(
        self,
        *,
        transport: MiniMaxSpeechTransport,
        pricing: VoicePricingSnapshot,
        api_key: object,
        policy: MiniMaxSpeechProviderPolicy,
    ) -> None:
        self._transport = transport
        self._pricing = pricing
        self._api_key = api_key
        self._policy = policy

    def preview(self, request: VoiceGenerationRequest) -> VoiceGenerationPreview:
        supported = _request_is_supported(request)
        return build_voice_generation_preview(
            request,
            pricing=self._pricing,
            destination=_ORIGIN,
            credential_reference_kind=self._policy.credential_reference_kind,
            timing_supported=supported,
            output_supported=supported,
        )

    def generate(
        self,
        request: VoiceGenerationRequest,
        authorization: VoiceCallAuthorization,
        permit: object,
    ) -> VoiceProviderResult:
        preview = self.preview(request)
        validate_voice_call_authorization(
            request,
            preview,
            authorization,
            pricing=self._pricing,
        )
        if not self._policy.provider_enabled:
            raise _error(
                ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
                "MiniMax Speech provider is not explicitly enabled.",
            )
        if not (
            self._policy.license_allowed
            and self._policy.use_policy_allowed
            and self._policy.voice_authorization_verified
        ):
            raise _error(
                ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
                "MiniMax Speech machine policy authorization is incomplete.",
            )
        binding = _permit_binding(request, authorization, preview, self._policy)
        if not _permit_is_valid(permit, binding):
            raise _error(
                ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
                "A current one-use durable voice submit permit is required.",
            )
        transport_request = MiniMaxSpeechTransportRequest(
            method="POST",
            url=f"{_ORIGIN}{_T2A_PATH}",
            headers={
                "authorization": _authorization_header(self._api_key),
                "content-type": "application/json",
            },
            body=_request_body(request),
        )
        if not _consume_permit(permit, binding):
            raise _error(
                ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
                "A current one-use durable voice submit permit is required.",
            )
        transport_failed = False
        try:
            response = self._transport.request(transport_request)
        except Exception:
            transport_failed = True
            response = None
        if transport_failed:
            raise _outcome_unknown()
        response_invalid = False
        try:
            response = _validate_transport_response(response)
        except Exception:
            response_invalid = True
        if response_invalid:
            raise _outcome_unknown()
        assert isinstance(response, MiniMaxSpeechTransportResponse)
        if response.status_code < 200 or response.status_code >= 300:
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                f"MiniMax Speech request failed with HTTP {response.status_code}.",
            )
        response_parse_failed = False
        result: VoiceProviderResult | None = None
        try:
            audio, measured_units, trace_id = _parse_result(
                response.body, request, preview
            )
            cost_receipt = VoiceCostReceipt(
                currency=preview.currency,
                pricing_unit=preview.pricing_unit,
                measured_billable_units=measured_units,
                estimated_cost_upper_bound_microunits=(
                    preview.estimated_cost_upper_bound_microunits
                ),
                provider_reported_cost_microunits=None,
                pricing_snapshot_id=preview.pricing_snapshot_id,
                request_id=request.request_id,
                provider_request_id=trace_id,
            )
            provenance = VoiceProvenanceReceipt(
                request_id=request.request_id,
                provider_kind=request.provider_kind,
                model_id=request.model_id,
                voice_id=request.voice_id,
                language=request.language,
                request_fingerprint=request.voice_request_fingerprint,
                script_hash=request.script_hash,
                output_container=request.output_container,
                output_codec=request.output_codec,
                output_sample_rate_hz=request.output_sample_rate_hz,
                output_channels=request.output_channels,
                alignment_mode="none",
                adapter=ToolIdentity(
                    name="minimax-speech-rest-adapter",
                    version="2026-08-19",
                ),
                egress_authorization_receipt_id=(
                    authorization.egress_authorization_receipt_id
                ),
                license_policy_decision=self._policy.license_policy_decision,
                policy_receipt_id=self._policy.policy_receipt_id,
                retention_mode=self._policy.retention_mode,
                provider_request_id=trace_id,
                provider_trace_id=trace_id,
            )
            alignment_receipt = json.dumps(
                {
                    "alignment_mode": "none",
                    "request_fingerprint": request.voice_request_fingerprint,
                    "script_hash": request.script_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            result = VoiceProviderResult.create(
                request=request,
                preview=preview,
                authorization=authorization,
                pricing=self._pricing,
                audio_bytes=audio,
                content_type="audio/wav",
                provider_request_id=trace_id,
                provider_trace_id=trace_id,
                alignment_receipt_bytes=alignment_receipt,
                cost_receipt=cost_receipt,
                provenance_receipt=provenance,
                terminal_status="succeeded",
            )
        except Exception:
            response_parse_failed = True
        if response_parse_failed or result is None:
            raise _outcome_unknown()
        return result
