from __future__ import annotations

import base64
import binascii
import io
import json
import math
import re
import wave
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Callable, Literal, Mapping, Protocol
from urllib.parse import quote

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


_ORIGIN = "https://api.elevenlabs.io"
MAX_AUDIO_BYTES = 1024 * 1024
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_MAX_ALIGNMENT_CHARACTERS = 100_000
_SANITIZED_RESPONSE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SANITIZED_POLICY_DECISION = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


@dataclass(frozen=True)
class ElevenLabsCompatibility:
    checked_on: date
    sdk_release: str
    sdk_license: str
    tts_with_timestamps_path: str
    forced_alignment_path: str
    auth_header: str


ELEVENLABS_COMPATIBILITY = ElevenLabsCompatibility(
    checked_on=date(2026, 8, 10),
    sdk_release="v2.62.0",
    sdk_license="MIT",
    tts_with_timestamps_path="/v1/text-to-speech/:voice_id/with-timestamps",
    forced_alignment_path="/v1/forced-alignment",
    auth_header="xi-api-key",
)


@dataclass(frozen=True)
class ElevenLabsProviderPolicy:
    provider_enabled: bool
    enable_logging: bool
    zero_retention_entitled: bool
    credential_reference_kind: Literal["environment", "secret_store"]
    license_policy_decision: str

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (
                self.provider_enabled,
                self.enable_logging,
                self.zero_retention_entitled,
            )
        ):
            raise ValueError("ElevenLabs policy flags must be exact booleans")
        if (
            type(self.credential_reference_kind) is not str
            or self.credential_reference_kind not in {"environment", "secret_store"}
        ):
            raise ValueError("ElevenLabs credential reference kind is invalid")
        if (
            type(self.license_policy_decision) is not str
            or _SANITIZED_POLICY_DECISION.fullmatch(
                self.license_policy_decision
            )
            is None
        ):
            raise ValueError("ElevenLabs license policy decision is invalid")


@dataclass(frozen=True)
class ElevenLabsTransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes = field(repr=False)


@dataclass(frozen=True)
class ElevenLabsTransportRequest:
    method: Literal["POST"]
    url: str
    query: tuple[tuple[str, str], ...]
    headers: Mapping[str, object] = field(repr=False)
    body: bytes = field(repr=False)
    _consume: Callable[[], bool] = field(repr=False, compare=False)

    def consume_permit(self) -> bool:
        """Called exactly at the injected transport's external-effect boundary."""

        return self._consume()


class ElevenLabsTransport(Protocol):
    """Injected transport; implementations must consume before external I/O."""

    def request(
        self, request: ElevenLabsTransportRequest
    ) -> ElevenLabsTransportResponse: ...


def _error(
    code: ErrorCode,
    message: str,
    *,
    retryable: bool = False,
) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=None,
        retryable=retryable,
    )


def _permit_binding(
    request: VoiceGenerationRequest,
    authorization: VoiceCallAuthorization,
) -> dict[str, str]:
    return {
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.voice_request_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "destination": authorization.destination,
        "budget_reservation_receipt_id": (
            authorization.budget_reservation_receipt_id
        ),
        "egress_authorization_receipt_id": (
            authorization.egress_authorization_receipt_id
        ),
    }


def _permit_is_valid(permit: object, binding: dict[str, str]) -> bool:
    # Task 5 deliberately recognizes only a private structural seam. Task 8 must
    # replace this with the nominal committer-issued R+2 permit identity.
    validator = getattr(permit, "_validate_voice_submit_permit", None)
    if not callable(validator):
        return False
    try:
        return validator(**binding) is True
    except Exception:
        return False


def _permit_consumer(
    permit: object, binding: dict[str, str]
) -> Callable[[], bool]:
    def consume() -> bool:
        consumer = getattr(permit, "_consume_voice_submit_permit", None)
        if not callable(consumer):
            return False
        try:
            return consumer(**binding) is True
        except Exception:
            return False

    return consume


def _voice_settings(request: VoiceGenerationRequest) -> dict[str, object]:
    parameters = request.provider_parameters
    settings: dict[str, object] = {}
    for source, target in (
        ("stability_milli", "stability"),
        ("similarity_boost_milli", "similarity_boost"),
        ("style_milli", "style"),
        ("speed_milli", "speed"),
    ):
        value = getattr(parameters, source)
        if value is not None:
            settings[target] = value / 1000
    if parameters.use_speaker_boost is not None:
        settings["use_speaker_boost"] = parameters.use_speaker_boost
    return settings


def _decode_audio(value: object) -> bytes:
    if not isinstance(value, str) or not value:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response is incomplete.",
        )
    if len(value) > ((MAX_AUDIO_BYTES + 2) // 3) * 4:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response exceeds the audio limit.",
        )
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response contains malformed base64 audio.",
        ) from exc
    if not decoded or len(decoded) > MAX_AUDIO_BYTES:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response exceeds the audio limit.",
        )
    return decoded


def _decimal_string(value: object, *, field_name: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {field_name} is malformed.",
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {field_name} is malformed.",
        )
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {field_name} is malformed.",
        ) from exc
    if number < 0:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {field_name} is malformed.",
        )
    return format(number, "f")


def _parse_character_alignment(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "characters",
        "character_start_times_seconds",
        "character_end_times_seconds",
    }:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {name} is incomplete.",
        )
    characters = value["characters"]
    starts = value["character_start_times_seconds"]
    ends = value["character_end_times_seconds"]
    if not all(isinstance(items, list) for items in (characters, starts, ends)):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {name} arrays are malformed.",
        )
    if not characters or len(characters) > _MAX_ALIGNMENT_CHARACTERS:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {name} exceeds the alignment limit.",
        )
    if len(characters) != len(starts) or len(characters) != len(ends):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {name} parallel arrays do not match.",
        )
    if any(not isinstance(character, str) for character in characters):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            f"ElevenLabs {name} characters are malformed.",
        )
    normalized_starts = []
    normalized_ends = []
    previous_start = Decimal(0)
    for index, (start, end) in enumerate(zip(starts, ends)):
        start_text = _decimal_string(start, field_name=f"{name} start")
        end_text = _decimal_string(end, field_name=f"{name} end")
        start_decimal = Decimal(start_text)
        end_decimal = Decimal(end_text)
        if end_decimal < start_decimal or (index and start_decimal < previous_start):
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                f"ElevenLabs {name} timing is malformed.",
            )
        normalized_starts.append(start_text)
        normalized_ends.append(end_text)
        previous_start = start_decimal
    return {
        "characters": characters,
        "character_start_times_seconds": normalized_starts,
        "character_end_times_seconds": normalized_ends,
    }


def _parse_timing_response(body: bytes, script_text: str) -> tuple[bytes, bytes]:
    if not body or len(body) > _MAX_RESPONSE_BYTES:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response exceeds the response limit.",
        )
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response JSON is malformed.",
        ) from exc
    if not isinstance(payload, dict) or set(payload) != {
        "audio_base64",
        "alignment",
        "normalized_alignment",
    }:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response is incomplete.",
        )
    audio = _decode_audio(payload["audio_base64"])
    alignment = _parse_character_alignment(payload["alignment"], name="alignment")
    normalized = _parse_character_alignment(
        payload["normalized_alignment"], name="normalized alignment"
    )
    if "".join(normalized["characters"]) != script_text:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs normalized alignment does not match the script.",
        )
    receipt = json.dumps(
        {"alignment": alignment, "normalized_alignment": normalized},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return audio, receipt


def _parse_headers(headers: Mapping[str, str]) -> tuple[int, str, str | None]:
    normalized: dict[str, str] = {}
    for name, value in headers.items():
        key = name.lower()
        if key in normalized or not isinstance(value, str):
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                "ElevenLabs response metadata is malformed.",
            )
        normalized[key] = value
    try:
        character_cost = int(normalized["character-cost"])
        request_id = normalized["request-id"]
    except (KeyError, ValueError) as exc:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response metadata is incomplete.",
        ) from exc
    trace_id = normalized.get("x-trace-id")
    if (
        character_cost <= 0
        or _SANITIZED_RESPONSE_ID.fullmatch(request_id) is None
        or (
            trace_id is not None
            and _SANITIZED_RESPONSE_ID.fullmatch(trace_id) is None
        )
    ):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs response metadata is malformed.",
        )
    return character_cost, request_id, trace_id


def _pcm_to_wav(raw_audio: bytes, *, sample_rate: int, channels: int) -> bytes:
    if len(raw_audio) % (2 * channels) != 0:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs PCM audio is malformed.",
        )
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(raw_audio)
    return output.getvalue()


def parse_forced_alignment_response(body: bytes) -> bytes:
    """Validate official forced-alignment evidence without inventing confidence."""

    if not body or len(body) > _MAX_RESPONSE_BYTES:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs forced-alignment response exceeds the response limit.",
        )
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs forced-alignment JSON is malformed.",
        ) from exc
    if not isinstance(payload, dict) or set(payload) != {"characters", "words", "loss"}:
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs forced-alignment response is incomplete.",
        )
    characters = payload["characters"]
    words = payload["words"]
    if not isinstance(characters, list) or not isinstance(words, list):
        raise _error(
            ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs forced-alignment arrays are malformed.",
        )

    def timed_item(item: object, *, with_loss: bool) -> dict[str, str]:
        expected = {"text", "start", "end"}
        if with_loss:
            expected.add("loss")
        if not isinstance(item, dict) or set(item) != expected:
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                "ElevenLabs forced-alignment item is malformed.",
            )
        if not isinstance(item["text"], str):
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                "ElevenLabs forced-alignment text is malformed.",
            )
        result = {
            "text": item["text"],
            "start": _decimal_string(item["start"], field_name="alignment start"),
            "end": _decimal_string(item["end"], field_name="alignment end"),
        }
        if Decimal(result["end"]) < Decimal(result["start"]):
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                "ElevenLabs forced-alignment timing is malformed.",
            )
        if with_loss:
            result["loss"] = _decimal_string(
                item["loss"], field_name="alignment loss"
            )
        return result

    normalized = {
        "characters": [timed_item(item, with_loss=False) for item in characters],
        "words": [timed_item(item, with_loss=True) for item in words],
        "loss": _decimal_string(payload["loss"], field_name="alignment loss"),
    }
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


class ElevenLabsVoiceProvider:
    """Explicit opt-in REST adapter with no implicit client or network transport."""

    def __init__(
        self,
        *,
        transport: ElevenLabsTransport,
        pricing: VoicePricingSnapshot,
        api_key: object,
        policy: ElevenLabsProviderPolicy,
    ) -> None:
        self._transport = transport
        self._pricing = pricing
        self._api_key = api_key
        self._policy = policy

    def preview(self, request: VoiceGenerationRequest) -> VoiceGenerationPreview:
        return build_voice_generation_preview(
            request,
            pricing=self._pricing,
            destination=_ORIGIN,
            credential_reference_kind=self._policy.credential_reference_kind,
            timing_supported=True,
            output_supported=(
                request.provider_kind == "elevenlabs"
                and request.output_container == "wav"
                and request.output_codec == "pcm_s16le"
                and request.output_sample_rate_hz == 48_000
                and request.output_channels == 1
            ),
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
                "ElevenLabs provider is not explicitly enabled.",
            )
        if not self._policy.enable_logging and not self._policy.zero_retention_entitled:
            raise _error(
                ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
                "ElevenLabs zero-retention entitlement is required.",
            )
        binding = _permit_binding(request, authorization)
        if not _permit_is_valid(permit, binding):
            raise _error(
                ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED,
                "A current one-use durable voice submit permit is required.",
            )
        body = json.dumps(
            {
                "text": request.script_text,
                "model_id": request.model_id,
                "language_code": request.language,
                "voice_settings": _voice_settings(request),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        transport_request = ElevenLabsTransportRequest(
            method="POST",
            url=(
                f"{_ORIGIN}/v1/text-to-speech/"
                f"{quote(request.voice_id, safe='')}/with-timestamps"
            ),
            query=(
                ("enable_logging", "true" if self._policy.enable_logging else "false"),
                ("output_format", "pcm_48000"),
            ),
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "xi-api-key": self._api_key,
            },
            body=body,
            _consume=_permit_consumer(permit, binding),
        )
        transport_failed = False
        try:
            response = self._transport.request(transport_request)
        except Exception:
            transport_failed = True
        if transport_failed:
            raise AiVideoError(
                code=ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN,
                user_message="ElevenLabs submit outcome is unknown.",
                technical_detail=(
                    "Injected ElevenLabs transport failed after permit consumption."
                ),
                retryable=False,
            )
        if response.status_code < 200 or response.status_code >= 300:
            raise _error(
                ErrorCode.VOICE_PROVIDER_FAILED,
                f"ElevenLabs request failed with HTTP {response.status_code}.",
            )
        raw_audio, alignment_receipt = _parse_timing_response(
            response.body, request.script_text
        )
        measured_units, provider_request_id, provider_trace_id = _parse_headers(
            response.headers
        )
        audio_bytes = _pcm_to_wav(
            raw_audio,
            sample_rate=request.output_sample_rate_hz,
            channels=request.output_channels,
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
            provider_request_id=provider_request_id,
        )
        provenance_receipt = VoiceProvenanceReceipt(
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
            alignment_mode="character",
            adapter=ToolIdentity(
                name="elevenlabs-rest-adapter",
                version="2026-08-10",
            ),
            egress_authorization_receipt_id=(
                authorization.egress_authorization_receipt_id
            ),
            license_policy_decision=self._policy.license_policy_decision,
            provider_request_id=provider_request_id,
            provider_trace_id=provider_trace_id,
        )
        return VoiceProviderResult.create(
            request=request,
            preview=preview,
            authorization=authorization,
            pricing=self._pricing,
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            provider_request_id=provider_request_id,
            provider_trace_id=provider_trace_id,
            alignment_receipt_bytes=alignment_receipt,
            cost_receipt=cost_receipt,
            provenance_receipt=provenance_receipt,
            terminal_status="succeeded",
        )
