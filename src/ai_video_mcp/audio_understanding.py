"""Bounded Gemini audio observations for an explicitly authorized MCP caller."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import re
import wave
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx


_ORIGIN = "https://generativelanguage.googleapis.com"
_MAX_DURATION_SECONDS = 120.0
_MAX_REQUEST_BYTES = 20_000_000
_MAX_RESPONSE_BYTES = 1_000_000
_MODEL_PATTERN = re.compile(r"gemini-[a-z0-9.-]+\Z")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_OBSERVATION_PROMPT = (
    "Listen only to the supplied audio and return audible observations in the required JSON schema. "
    "Transcribe speech in chronological segments, preserving language and wording; estimate times "
    "relative to audio start, not as precision measurements. Describe audible voice, delivery, and "
    "background sounds; put uncertainty in uncertainties. Do not infer context, identify people, "
    "answer intended-dialogue questions, or provide quality verdicts. Use empty arrays when none "
    "are discernible and 'not discernible' when voice or delivery cannot be characterized."
)
_STRING = {"type": "STRING"}
_STRING_ARRAY = {"type": "ARRAY", "items": _STRING}
_OBSERVATION_SCHEMA: dict[str, Any] = {
    "type": "OBJECT", "properties": {
        "segments": {"type": "ARRAY", "items": {
            "type": "OBJECT", "properties": {
                "start_seconds": {"type": "NUMBER"}, "end_seconds": {"type": "NUMBER"},
                "text": _STRING, "speaker": _STRING,
            }, "required": ["start_seconds", "end_seconds", "text", "speaker"],
        }},
        "voice_description": _STRING, "delivery_description": _STRING,
        "background_sounds": _STRING_ARRAY, "uncertainties": _STRING_ARRAY,
    }, "required": ["segments", "voice_description", "delivery_description",
                    "background_sounds", "uncertainties"],
}


class AudioUnderstandingError(Exception):
    """A secret-safe adapter failure with an explicit retry/evidence outcome."""

    def __init__(self, code: str, outcome: str, message: str):
        super().__init__(message)
        self.code = code
        self.outcome = outcome


@dataclass(frozen=True)
class PreparedAudioRequest:
    source_sha256: str
    source_size_bytes: int
    audio_sha256: str
    audio_size_bytes: int
    duration_seconds: float
    audio_start_seconds: float
    model_id: str
    request_fingerprint: str
    endpoint: str
    _payload: bytes = field(repr=False)

    def preview(self) -> dict[str, Any]:
        """Return only the exact safe identity and scope needed for authorization."""
        return {"operation": "audio_understand", "provider": "gemini", "endpoint": self.endpoint,
                "model_id": self.model_id, "source_sha256": self.source_sha256,
                "source_size_bytes": self.source_size_bytes, "audio_sha256": self.audio_sha256,
                "audio_size_bytes": self.audio_size_bytes, "duration_seconds": self.duration_seconds,
                "audio_start_seconds": self.audio_start_seconds,
                "request_fingerprint": self.request_fingerprint}


def prepare_audio_request(
    *,
    audio_bytes: bytes,
    source_sha256: str,
    source_size_bytes: int,
    model_id: str = "gemini-3.8-flash",
    audio_start_seconds: float = 0.0,
) -> PreparedAudioRequest:
    """Seal one inline PCM WAV request without retrieving credentials or sending it."""
    if not isinstance(audio_bytes, bytes) or not audio_bytes:
        raise _error("invalid_audio", "EVIDENCE_GAP", "A non-empty PCM WAV is required.")
    if not isinstance(source_sha256, str) or not _SHA256_PATTERN.fullmatch(source_sha256):
        raise _error("invalid_source_identity", "EVIDENCE_GAP", "The source SHA-256 is invalid.")
    if isinstance(source_size_bytes, bool) or not isinstance(source_size_bytes, int) or source_size_bytes <= 0:
        raise _error("invalid_source_identity", "EVIDENCE_GAP", "The source byte size is invalid.")
    if not isinstance(model_id, str) or not _MODEL_PATTERN.fullmatch(model_id):
        raise _error("invalid_model", "REJECTED", "The Gemini model identifier is invalid.")
    if (isinstance(audio_start_seconds, bool) or not isinstance(audio_start_seconds, (int, float))
            or not math.isfinite(audio_start_seconds) or audio_start_seconds < 0):
        raise _error("invalid_audio_clock", "EVIDENCE_GAP", "The audio clock offset is invalid.")
    if 4 * ((len(audio_bytes) + 2) // 3) > _MAX_REQUEST_BYTES:
        raise _error("request_too_large", "EVIDENCE_GAP", "The inline audio request exceeds the size limit.")

    duration = _pcm_wav_duration(audio_bytes)
    if duration > _MAX_DURATION_SECONDS:
        raise _error("audio_too_long", "EVIDENCE_GAP", "The PCM WAV exceeds the 120 second limit.")
    audio_hash = hashlib.sha256(audio_bytes).hexdigest()
    endpoint = f"{_ORIGIN}/v1beta/models/{model_id}:generateContent"
    payload = json.dumps({"contents": [{"parts": [
        {"text": _OBSERVATION_PROMPT},
        {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(audio_bytes).decode("ascii")}},
    ]}], "generationConfig": {"responseMimeType": "application/json", "responseSchema": _OBSERVATION_SCHEMA,
                              "maxOutputTokens": 4096}}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > _MAX_REQUEST_BYTES:
        raise _error("request_too_large", "EVIDENCE_GAP", "The inline audio request exceeds the size limit.")
    fingerprint = _request_fingerprint(
        endpoint=endpoint,
        model_id=model_id,
        source_sha256=source_sha256,
        source_size_bytes=source_size_bytes,
        audio_sha256=audio_hash,
        audio_size_bytes=len(audio_bytes),
        duration_seconds=duration,
        audio_start_seconds=float(audio_start_seconds),
        payload=payload,
    )
    return PreparedAudioRequest(source_sha256, source_size_bytes, audio_hash, len(audio_bytes), duration,
                                float(audio_start_seconds), model_id, fingerprint, endpoint, payload)


def _request_fingerprint(
    *,
    endpoint: str,
    model_id: str,
    source_sha256: str,
    source_size_bytes: int,
    audio_sha256: str,
    audio_size_bytes: int,
    duration_seconds: float,
    audio_start_seconds: float,
    payload: bytes,
) -> str:
    preimage = {
        "endpoint": endpoint,
        "model_id": model_id,
        "source_sha256": source_sha256,
        "source_size_bytes": source_size_bytes,
        "audio_sha256": audio_sha256,
        "audio_size_bytes": audio_size_bytes,
        "duration_seconds": duration_seconds,
        "audio_start_seconds": audio_start_seconds,
        "wire_sha256": hashlib.sha256(payload).hexdigest(),
    }
    encoded = json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(b"audio-understanding-request/1\n" + encoded).hexdigest()


def _pcm_wav_duration(audio_bytes: bytes) -> float:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            if wav.getcomptype() != "NONE":
                raise ValueError
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            frames = wav.getnframes()
            if channels <= 0 or width not in {1, 2, 3, 4} or rate <= 0 or frames <= 0:
                raise ValueError
            duration = frames / rate
            # Read bounded chunks so validating a large caller buffer does not
            # allocate a second copy of the complete audio payload.
            frame_bytes = channels * width
            remaining = frames * frame_bytes
            frames_per_chunk = max(1, 64 * 1024 // frame_bytes)
            while remaining:
                chunk_frames = min(frames, frames_per_chunk, (remaining + frame_bytes - 1) // frame_bytes)
                chunk = wav.readframes(chunk_frames)
                expected = chunk_frames * frame_bytes
                if len(chunk) != expected:
                    raise ValueError
                remaining -= len(chunk)
                frames -= chunk_frames
            return duration
    except (wave.Error, EOFError, OSError, ValueError, OverflowError):
        raise _error("invalid_audio", "EVIDENCE_GAP", "The audio is not a complete PCM WAV.") from None


class _HttpxTransport:
    """Single-request transport that bounds response bytes before buffering."""

    def post(self, url: str, *, headers: dict[str, str], content: bytes) -> httpx.Response:
        collected: list[bytes] = []
        total = 0
        with httpx.Client(
            timeout=httpx.Timeout(45.0),
            follow_redirects=False,
            trust_env=False,
            headers={"accept-encoding": "identity"},
        ) as client:
            with client.stream("POST", url, headers=headers, content=content) as response:
                if response.status_code != 200:
                    return httpx.Response(
                        response.status_code,
                        headers=response.headers,
                        content=b"",
                        request=response.request,
                    )
                for chunk in response.iter_bytes(chunk_size=64 * 1024):
                    total += len(chunk)
                    if total > _MAX_RESPONSE_BYTES:
                        raise _ResponseTooLarge
                    collected.append(chunk)
                return httpx.Response(
                    response.status_code,
                    headers=response.headers,
                    content=b"".join(collected),
                    request=response.request,
                )


class _ResponseTooLarge(Exception):
    pass


class GeminiAudioAnalyzer:
    def __init__(self, credential_supplier: Callable[[], str], transport: Any = None):
        self._credential_supplier = credential_supplier
        self._transport = transport if transport is not None else _HttpxTransport()

    def analyze(self, prepared: PreparedAudioRequest, *, permit: Any) -> dict[str, Any]:
        try:
            _verify_prepared_request(prepared)
            preview = prepared.preview()
        except Exception:
            raise _error("prepared_request_invalid", "REJECTED", "The prepared audio request is invalid.") from None
        if permit is None:
            raise _error("permit_required", "REJECTED", "An authorized audio execution permit is required.")
        validate = getattr(permit, "validate", None)
        consume = getattr(permit, "consume", None)
        if not callable(validate) or not callable(consume):
            raise _error("permit_invalid", "REJECTED", "The audio execution permit is invalid.")
        try:
            valid = validate(preview)
        except Exception:
            raise _error("permit_rejected", "REJECTED", "The audio execution permit rejected this request.") from None
        if valid is not True:
            raise _error("permit_rejected", "REJECTED", "The audio execution permit rejected this request.")

        try:
            credential = self._credential_supplier()
        except Exception:
            raise _error("credential_unavailable", "REJECTED",
                         "The configured audio credential is unavailable.") from None
        if (not isinstance(credential, str) or not credential
                or not credential.isascii()
                or any(not 0x21 <= ord(char) <= 0x7E for char in credential)):
            raise _error("credential_invalid", "REJECTED", "The configured audio credential is invalid.")

        try:
            consumed = consume(preview)
        except Exception:
            raise _error("permit_consume_unknown", "UNKNOWN",
                         "The audio execution permit outcome is unknown.") from None
        if consumed is not True:
            raise _error("permit_rejected", "REJECTED", "The audio execution permit rejected this request.")

        try:
            response = self._transport.post(
                prepared.endpoint,
                headers={"content-type": "application/json", "x-goog-api-key": credential},
                content=prepared._payload,
            )
        except _ResponseTooLarge:
            raise _error("response_too_large", "EVIDENCE_GAP",
                         "The audio analyzer response exceeds the size limit.") from None
        except Exception:
            raise _error("transport_unknown", "UNKNOWN", "The audio analyzer request outcome is unknown.") from None

        try:
            status = response.status_code
            response_bytes = response.content
        except Exception:
            raise _error("invalid_transport_response", "UNKNOWN",
                         "The audio analyzer response is unavailable.") from None
        if not isinstance(response_bytes, bytes) or len(response_bytes) > _MAX_RESPONSE_BYTES:
            raise _error("response_too_large", "EVIDENCE_GAP", "The audio analyzer response exceeds the size limit.")
        if status in {400, 401, 403, 429} or 400 <= status < 500:
            raise _error("provider_rejected", "REJECTED", "The audio analyzer rejected the request.")
        if status >= 500 or 300 <= status < 400:
            raise _error("provider_outcome_unknown", "UNKNOWN", "The audio analyzer request outcome is unknown.")
        if status != 200:
            raise _error("invalid_provider_status", "EVIDENCE_GAP",
                         "The audio analyzer returned an unusable response.")
        if credential.encode("utf-8") in response_bytes:
            raise _error("response_secret_reflection", "EVIDENCE_GAP",
                         "The audio analyzer response is unsafe to retain.")
        return _parse_response(prepared, response_bytes, credential)


def _verify_prepared_request(prepared: PreparedAudioRequest) -> None:
    if type(prepared) is not PreparedAudioRequest or not isinstance(prepared._payload, bytes):
        raise ValueError
    if len(prepared._payload) > _MAX_REQUEST_BYTES:
        raise ValueError
    decoded = json.loads(prepared._payload)
    if not isinstance(decoded, dict):
        raise ValueError
    contents = decoded.get("contents")
    parts = contents[0].get("parts") if isinstance(contents, list) and len(contents) == 1 else None
    if not isinstance(parts, list) or len(parts) != 2:
        raise ValueError
    text_part, audio_part = parts
    if not isinstance(text_part, dict) or text_part != {"text": _OBSERVATION_PROMPT}:
        raise ValueError
    inline = audio_part.get("inline_data") if isinstance(audio_part, dict) else None
    if (not isinstance(inline, dict) or set(inline) != {"mime_type", "data"}
            or inline.get("mime_type") != "audio/wav" or not isinstance(inline.get("data"), str)):
        raise ValueError
    audio_bytes = base64.b64decode(inline["data"], validate=True)
    if base64.b64encode(audio_bytes).decode("ascii") != inline["data"]:
        raise ValueError
    canonical = prepare_audio_request(
        audio_bytes=audio_bytes,
        source_sha256=prepared.source_sha256,
        source_size_bytes=prepared.source_size_bytes,
        model_id=prepared.model_id,
        audio_start_seconds=prepared.audio_start_seconds,
    )
    if (canonical._payload != prepared._payload
            or canonical.preview() != prepared.preview()
            or canonical.endpoint != prepared.endpoint
            or canonical.request_fingerprint != prepared.request_fingerprint):
        raise ValueError


def _parse_response(
    prepared: PreparedAudioRequest,
    response_bytes: bytes,
    credential: str,
) -> dict[str, Any]:
    try:
        decoded = json.loads(response_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _error("invalid_response_json", "EVIDENCE_GAP",
                     "The audio analyzer response is not valid JSON.") from None
    if not isinstance(decoded, dict):
        raise _error("invalid_response", "EVIDENCE_GAP", "The audio analyzer response has an invalid shape.")
    model_version = decoded.get("modelVersion")
    candidates = decoded.get("candidates")
    if (not isinstance(model_version, str) or not model_version.strip()
            or not isinstance(candidates, list) or len(candidates) != 1):
        raise _error("invalid_response", "EVIDENCE_GAP", "The audio analyzer response has an invalid shape.")
    candidate = candidates[0]
    if not isinstance(candidate, dict) or candidate.get("finishReason") != "STOP":
        raise _error("incomplete_response", "EVIDENCE_GAP", "The audio analyzer did not complete its response.")
    content = candidate.get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        raise _error("invalid_response", "EVIDENCE_GAP", "The audio analyzer response has an invalid shape.")
    texts = [part.get("text") for part in parts if isinstance(part, dict) and isinstance(part.get("text"), str)]
    if len(texts) != 1:
        raise _error("invalid_observations", "EVIDENCE_GAP", "The audio analyzer observations are incomplete.")
    try:
        observations = json.loads(texts[0])
        _validate_observations(observations, prepared.duration_seconds)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise _error("invalid_observations", "EVIDENCE_GAP", "The audio analyzer observations are invalid.") from None
    if _contains_secret(decoded, credential) or _contains_secret(observations, credential):
        raise _error("response_secret_reflection", "EVIDENCE_GAP", "The audio analyzer response is unsafe to retain.")
    return {
        "schema_version": "audio-understanding-evidence/1",
        "source_sha256": prepared.source_sha256,
        "source_size_bytes": prepared.source_size_bytes,
        "audio_sha256": prepared.audio_sha256,
        "audio_size_bytes": prepared.audio_size_bytes,
        "duration_seconds": prepared.duration_seconds,
        "audio_start_seconds": prepared.audio_start_seconds,
        "request_fingerprint": prepared.request_fingerprint,
        "requested_model_id": prepared.model_id,
        "response_model_id": model_version,
        "response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "observations": observations,
        "proof_boundary": "analyzer observations; not QA/human/timing acceptance",
    }


def _contains_secret(value: Any, secret: str) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, dict):
        return any(_contains_secret(key, secret) or _contains_secret(item, secret)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_secret(item, secret) for item in value)
    return False


def _validate_observations(observations: Any, duration: float) -> None:
    required = {
        "segments", "voice_description", "delivery_description",
        "background_sounds", "uncertainties",
    }
    if not isinstance(observations, dict) or set(observations) != required:
        raise ValueError
    for name in ("voice_description", "delivery_description"):
        value = observations[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError
    for name in ("background_sounds", "uncertainties"):
        values = observations[name]
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError
    segments = observations["segments"]
    if not isinstance(segments, list):
        raise ValueError
    last_start = -1.0
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) != {
            "start_seconds", "end_seconds", "text", "speaker",
        }:
            raise ValueError
        start, end = segment["start_seconds"], segment["end_seconds"]
        if (isinstance(start, bool) or isinstance(end, bool)
                or not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                or not math.isfinite(start) or not math.isfinite(end)
                or start < 0 or start < last_start or end <= start or end > duration):
            raise ValueError
        if not isinstance(segment["text"], str) or not segment["text"].strip():
            raise ValueError
        if not isinstance(segment["speaker"], str) or not segment["speaker"].strip():
            raise ValueError
        last_start = float(start)


def _error(code: str, outcome: str, message: str) -> AudioUnderstandingError:
    return AudioUnderstandingError(code, outcome, message)
