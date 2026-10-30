from __future__ import annotations

import base64
from dataclasses import replace
import gzip
import hashlib
import io
import json
import math
import wave

import httpx
import pytest

import ai_video_mcp.audio_understanding as audio_understanding
from ai_video_mcp.audio_understanding import (
    AudioUnderstandingError,
    GeminiAudioAnalyzer,
    prepare_audio_request,
)

_REAL_HTTPX_CLIENT = httpx.Client


def pcm_wav(seconds: float = 0.5, *, sample_rate: int = 8_000) -> bytes:
    frames = int(sample_rate * seconds)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()


def prepared(audio: bytes | None = None):
    audio = audio if audio is not None else pcm_wav()
    return prepare_audio_request(
        audio_bytes=audio,
        source_sha256="a" * 64,
        source_size_bytes=1234,
        audio_start_seconds=1.25,
    )


def gemini_response(observations: dict | None = None, *, model: str = "gemini-3.8-flash-001"):
    observations = observations or {
        "segments": [{
            "start_seconds": 0.05,
            "end_seconds": 0.4,
            "text": "Test words.",
            "speaker": "speaker_1",
        }],
        "voice_description": "One adult voice.",
        "delivery_description": "Quiet and measured.",
        "background_sounds": ["Low train rumble."],
        "uncertainties": [],
    }
    return httpx.Response(200, json={
        "modelVersion": model,
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": json.dumps(observations)}]},
        }],
    })


class OneShotPermit:
    def __init__(self, *, accepted: bool = True, consume_accepted: bool | None = None):
        self.accepted = accepted
        self.consume_accepted = accepted if consume_accepted is None else consume_accepted
        self.validated = []
        self.consumed = []

    def validate(self, preview):
        self.validated.append(dict(preview))
        return self.accepted

    def consume(self, preview):
        self.consumed.append(dict(preview))
        return self.consume_accepted


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def post(self, url, *, headers, content):
        self.calls.append((url, dict(headers), content))
        if self.error:
            raise self.error
        return self.response


def test_prepare_binds_source_audio_model_and_exact_inline_wav_bytes():
    audio = pcm_wav()
    request = prepare_audio_request(
        audio_bytes=audio,
        source_sha256="b" * 64,
        source_size_bytes=987,
        audio_start_seconds=3.0,
    )
    preview = request.preview()

    assert request.model_id == "gemini-3.8-flash"
    assert request.audio_sha256 == hashlib.sha256(audio).hexdigest()
    assert request.duration_seconds == pytest.approx(0.5)
    assert preview["source_sha256"] == "b" * 64
    assert preview["source_size_bytes"] == 987
    assert preview["audio_sha256"] == request.audio_sha256
    assert preview["audio_start_seconds"] == 3.0
    assert preview["request_fingerprint"] == request.request_fingerprint
    assert "api_key" not in preview and "payload" not in preview

    response = gemini_response()
    response_bytes = response.content
    transport = FakeTransport(response)
    permit = OneShotPermit()
    result = GeminiAudioAnalyzer(lambda: "test-key", transport).analyze(
        request, permit=permit,
    )
    url, headers, body = transport.calls[0]
    wire = json.loads(body)
    schema = wire["generationConfig"]["responseSchema"]

    def assert_schema_subset(node):
        assert set(node) <= {"type", "properties", "items", "required"}
        for child in node.get("properties", {}).values():
            assert_schema_subset(child)
        if "items" in node:
            assert_schema_subset(node["items"])

    assert_schema_subset(schema)
    inline_audio = wire["contents"][0]["parts"][1]["inline_data"]
    assert base64.b64decode(inline_audio["data"]) == audio
    assert inline_audio["mime_type"] == "audio/wav"
    assert url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    assert headers["x-goog-api-key"] == "test-key"
    assert permit.validated == permit.consumed == [preview]
    assert result["source_sha256"] == "b" * 64
    assert result["audio_sha256"] == request.audio_sha256
    assert result["response_model_id"] == "gemini-3.8-flash-001"
    assert result["response_sha256"] == hashlib.sha256(response_bytes).hexdigest()
    assert result["observations"]["segments"][0]["text"] == "Test words."
    assert result["proof_boundary"].startswith("analyzer observations")
    assert "PASS" not in result


def test_request_fingerprint_binds_source_identity_and_audio_clock():
    audio = pcm_wav()
    baseline = prepare_audio_request(
        audio_bytes=audio,
        source_sha256="a" * 64,
        source_size_bytes=1234,
        audio_start_seconds=1.25,
    )
    variants = (
        prepare_audio_request(audio_bytes=audio, source_sha256="b" * 64,
                              source_size_bytes=1234, audio_start_seconds=1.25),
        prepare_audio_request(audio_bytes=audio, source_sha256="a" * 64,
                              source_size_bytes=4321, audio_start_seconds=1.25),
        prepare_audio_request(audio_bytes=audio, source_sha256="a" * 64,
                              source_size_bytes=1234, audio_start_seconds=2.5),
    )
    assert all(item.audio_sha256 == baseline.audio_sha256 for item in variants)
    assert all(item.request_fingerprint != baseline.request_fingerprint for item in variants)


@pytest.mark.parametrize("audio", [
    b"not wav",
    b"RIFF\x00\x00\x00\x00WAVE",
    pcm_wav()[:-8],
])
def test_prepare_rejects_invalid_wav(audio):
    with pytest.raises(AudioUnderstandingError) as error:
        prepared(audio)
    assert error.value.outcome == "EVIDENCE_GAP"


def test_prepare_rejects_long_wav_invalid_identity_model_and_clock():
    for kwargs in (
        {"audio_bytes": pcm_wav(120.01)},
        {"source_sha256": "not-a-hash"},
        {"source_size_bytes": 0},
        {"model_id": "gemini-3.8-flash/extra"},
        {"audio_start_seconds": math.nan},
    ):
        params = {
            "audio_bytes": pcm_wav(),
            "source_sha256": "a" * 64,
            "source_size_bytes": 100,
            **kwargs,
        }
        with pytest.raises(AudioUnderstandingError):
            prepare_audio_request(**params)


def test_prepare_enforces_wire_body_limit():
    # 15.2 MB PCM remains within 120 seconds but expands beyond the 20 MB JSON ceiling.
    too_large = pcm_wav(1.0, sample_rate=7_600_000)
    with pytest.raises(AudioUnderstandingError) as error:
        prepared(too_large)
    assert error.value.outcome == "EVIDENCE_GAP"
    assert error.value.code == "request_too_large"


def test_missing_or_refused_permit_never_reads_credential_or_posts():
    transport = FakeTransport(gemini_response())
    supplier_calls = []
    analyzer = GeminiAudioAnalyzer(lambda: supplier_calls.append(True), transport)
    request = prepared()

    with pytest.raises(AudioUnderstandingError) as missing:
        analyzer.analyze(request, permit=None)
    with pytest.raises(AudioUnderstandingError) as refused:
        analyzer.analyze(request, permit=OneShotPermit(accepted=False))

    assert missing.value.outcome == refused.value.outcome == "REJECTED"
    assert supplier_calls == []
    assert transport.calls == []


def test_permit_identity_mismatch_and_consume_refusal_never_post():
    request = prepared()

    class WrongSourcePermit(OneShotPermit):
        def validate(self, preview):
            self.validated.append(dict(preview))
            return preview["source_sha256"] == "c" * 64

    transport = FakeTransport(gemini_response())
    with pytest.raises(AudioUnderstandingError) as mismatch:
        GeminiAudioAnalyzer(lambda: "test-key", transport).analyze(
            request, permit=WrongSourcePermit(),
        )
    assert mismatch.value.outcome == "REJECTED"
    assert transport.calls == []

    permit = OneShotPermit(consume_accepted=False)
    with pytest.raises(AudioUnderstandingError) as consumed:
        GeminiAudioAnalyzer(lambda: "test-key", transport).analyze(request, permit=permit)
    assert consumed.value.outcome == "REJECTED"
    assert permit.validated and permit.consumed
    assert transport.calls == []


def test_permit_consume_exception_is_unknown_and_does_not_post_or_leak():
    secret = "permit-private-detail"

    class UncertainConsumePermit(OneShotPermit):
        def consume(self, preview):
            self.consumed.append(dict(preview))
            raise RuntimeError(secret)

    transport = FakeTransport(gemini_response())
    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: "test-key", transport).analyze(
            prepared(), permit=UncertainConsumePermit(),
        )
    assert error.value.outcome == "UNKNOWN"
    assert secret not in str(error.value)
    assert transport.calls == []


def test_dataclass_replacements_are_rejected_before_credentials_or_permit_consumption():
    request = prepared()
    tampered = (
        replace(request, _payload=request._payload + b" "),
        replace(request, endpoint="https://attacker.invalid/collect"),
        replace(request, request_fingerprint="b" * 64),
        replace(request, source_sha256="b" * 64),
        replace(request, source_size_bytes=4321),
        replace(request, audio_sha256="c" * 64),
        replace(request, audio_size_bytes=request.audio_size_bytes + 1),
        replace(request, duration_seconds=2.0),
        replace(request, audio_start_seconds=9.0),
    )
    for candidate in tampered:
        supplier_calls = []
        permit = OneShotPermit()
        transport = FakeTransport(gemini_response())
        analyzer = GeminiAudioAnalyzer(lambda: supplier_calls.append(True), transport)
        with pytest.raises(AudioUnderstandingError) as error:
            analyzer.analyze(candidate, permit=permit)
        assert error.value.outcome == "REJECTED"
        assert supplier_calls == []
        assert not permit.consumed
        assert transport.calls == []


def test_credential_failure_is_safe_and_does_not_consume_or_post():
    secret = "sensitive-key-value"
    transport = FakeTransport(gemini_response())
    permit = OneShotPermit()
    analyzer = GeminiAudioAnalyzer(
        lambda: (_ for _ in ()).throw(RuntimeError(secret)), transport,
    )

    with pytest.raises(AudioUnderstandingError) as error:
        analyzer.analyze(prepared(), permit=permit)

    assert error.value.outcome == "REJECTED"
    assert secret not in str(error.value)
    assert permit.validated and not permit.consumed
    assert transport.calls == []


@pytest.mark.parametrize("credential", ["", "unsafe\nheader", "has space", "密钥", "bad\x00key"])
def test_invalid_credential_is_rejected_without_consuming_or_posting(credential):
    transport = FakeTransport(gemini_response())
    permit = OneShotPermit()
    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: credential, transport).analyze(prepared(), permit=permit)
    assert error.value.outcome == "REJECTED"
    assert not permit.consumed
    assert transport.calls == []


def test_api_error_is_redacted_and_attempted_once():
    secret = "sensitive-key-value"
    transport = FakeTransport(httpx.Response(401, text=f"bad key {secret}"))
    permit = OneShotPermit()
    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: secret, transport).analyze(prepared(), permit=permit)
    assert error.value.outcome == "REJECTED"
    assert secret not in str(error.value)
    assert len(transport.calls) == 1
    assert len(permit.consumed) == 1


def test_timeout_is_unknown_and_never_retried():
    transport = FakeTransport(error=httpx.TimeoutException("private timeout details"))
    permit = OneShotPermit()
    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: "test-key", transport).analyze(prepared(), permit=permit)
    assert error.value.outcome == "UNKNOWN"
    assert "private timeout details" not in str(error.value)
    assert len(transport.calls) == 1
    assert len(permit.consumed) == 1


@pytest.mark.parametrize("observations", [
    {"segments": [], "voice_description": "", "delivery_description": "ok",
     "background_sounds": [], "uncertainties": []},
    {"segments": [{"start_seconds": math.nan, "end_seconds": 0.2, "text": "x", "speaker": "s"}],
     "voice_description": "ok", "delivery_description": "ok",
     "background_sounds": [], "uncertainties": []},
    {"segments": [{"start_seconds": 0.1, "end_seconds": 1.0, "text": "x", "speaker": "s"}],
     "voice_description": "ok", "delivery_description": "ok",
     "background_sounds": [], "uncertainties": []},
])
def test_invalid_or_empty_model_observations_are_evidence_gap(observations):
    permit = OneShotPermit()
    analyzer = GeminiAudioAnalyzer(lambda: "test-key", FakeTransport(gemini_response(observations)))
    with pytest.raises(AudioUnderstandingError) as error:
        analyzer.analyze(prepared(), permit=permit)
    assert error.value.outcome == "EVIDENCE_GAP"


def test_estimated_end_rounding_past_duration_is_clamped_not_discarded():
    # Models pin the last segment to the file end; a rounding overshoot must not discard the observation.
    observations = {
        "segments": [{"start_seconds": 0.05, "end_seconds": 0.6, "text": "Test words.", "speaker": "s"}],
        "voice_description": "ok", "delivery_description": "ok",
        "background_sounds": [], "uncertainties": [],
    }
    request = prepared()
    analyzer = GeminiAudioAnalyzer(lambda: "test-key", FakeTransport(gemini_response(observations)))
    result = analyzer.analyze(request, permit=OneShotPermit())
    assert result["observations"]["segments"][0]["end_seconds"] == pytest.approx(request.duration_seconds)


def test_invalid_response_shape_and_secret_reflection_are_safe():
    for response in (
        httpx.Response(200, json={"modelVersion": "", "candidates": []}),
        httpx.Response(200, text="not json"),
    ):
        with pytest.raises(AudioUnderstandingError) as error:
            GeminiAudioAnalyzer(lambda: "test-key", FakeTransport(response)).analyze(
                prepared(), permit=OneShotPermit(),
            )
        assert error.value.outcome == "EVIDENCE_GAP"
        assert "test-key" not in str(error.value)

    secret = "sensitive-key-value"
    response = httpx.Response(200, text=secret)
    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: secret, FakeTransport(response)).analyze(
            prepared(), permit=OneShotPermit(),
        )
    assert error.value.outcome == "EVIDENCE_GAP"
    assert secret not in str(error.value)


def test_json_escaped_credential_reflection_is_rejected_after_decoding():
    secret = "AIzaSyEscapedKey_123"
    escaped = '"' + "".join(f"\\u{ord(char):04x}" for char in secret) + '"'
    observations = (
        '{"segments":[],"voice_description":' + escaped
        + ',"delivery_description":"quiet","background_sounds":[],"uncertainties":[]}'
    )
    outer = {
        "modelVersion": "gemini-3.8-flash-001",
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": observations}]},
        }],
    }
    response = httpx.Response(200, content=json.dumps(outer).encode("utf-8"))
    assert secret.encode("ascii") not in response.content

    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: secret, FakeTransport(response)).analyze(
            prepared(), permit=OneShotPermit(),
        )
    assert error.value.outcome == "EVIDENCE_GAP"
    assert secret not in str(error.value)


def test_server_failures_are_unknown_and_no_redirects_are_followed():
    for response, outcome in (
        (httpx.Response(503), "UNKNOWN"),
        (httpx.Response(302, headers={"location": "https://example.invalid"}), "UNKNOWN"),
    ):
        transport = FakeTransport(response)
        with pytest.raises(AudioUnderstandingError) as error:
            GeminiAudioAnalyzer(lambda: "test-key", transport).analyze(
                prepared(), permit=OneShotPermit(),
            )
        assert error.value.outcome == outcome
        assert len(transport.calls) == 1


def _mock_default_httpx_client(monkeypatch, *, status_code: int, body: bytes,
                               response_headers: dict[str, str]):
    requests = []
    client_options = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status_code, headers=response_headers, content=body, request=request)

    def make_client(**kwargs):
        client_options.append(kwargs)
        return _REAL_HTTPX_CLIENT(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(audio_understanding.httpx, "Client", make_client)
    return requests, client_options


def test_default_httpx_transport_decodes_gzip_once_and_discards_stale_body_headers(monkeypatch):
    expected = gemini_response().content
    wire_body = gzip.compress(expected)
    requests, options = _mock_default_httpx_client(monkeypatch, status_code=200, body=wire_body,
        response_headers={"content-type": "application/json", "content-encoding": "gzip",
                          "content-length": str(len(wire_body))})

    class CapturingHttpxTransport(audio_understanding._HttpxTransport):
        response = None

        def post(self, url, *, headers, content):
            self.response = super().post(url, headers=headers, content=content)
            return self.response

    transport = CapturingHttpxTransport()
    analyzer = GeminiAudioAnalyzer(lambda: "test-key", transport)
    permit = OneShotPermit()

    result = analyzer.analyze(prepared(), permit=permit)

    assert result["observations"]["segments"][0]["text"] == "Test words."
    assert transport.response.content == expected
    assert "content-encoding" not in transport.response.headers
    assert transport.response.headers["content-length"] == str(len(expected))
    assert len(requests) == len(permit.consumed) == 1
    assert requests[0].headers["x-goog-api-key"] == "test-key"
    assert requests[0].headers["accept-encoding"] == "identity"
    assert options[0]["follow_redirects"] is False
    assert options[0]["trust_env"] is False
    assert options[0]["timeout"].read == 45.0


def test_default_httpx_transport_preserves_uncompressed_response(monkeypatch):
    expected = gemini_response().content
    requests, _ = _mock_default_httpx_client(monkeypatch, status_code=200, body=expected,
        response_headers={"content-type": "application/json", "content-length": str(len(expected))})

    response = audio_understanding._HttpxTransport().post(
        "https://generativelanguage.googleapis.com/test", headers={}, content=b"request",
    )

    assert response.content == expected
    assert len(requests) == 1


def test_default_httpx_transport_preserves_non_200_rejection_without_decoding_empty_body(monkeypatch):
    body = gzip.compress(b"private provider error")
    requests, _ = _mock_default_httpx_client(monkeypatch, status_code=401, body=body,
        response_headers={"content-type": "text/plain", "content-encoding": "gzip",
                          "content-length": str(len(body))})
    permit = OneShotPermit()

    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: "test-key").analyze(prepared(), permit=permit)

    assert error.value.code == "provider_rejected"
    assert error.value.outcome == "REJECTED"
    assert len(requests) == len(permit.consumed) == 1
    assert "private provider error" not in str(error.value)


def test_default_httpx_transport_enforces_decoded_response_size_boundary(monkeypatch):
    from ai_video_mcp.audio_understanding import _MAX_RESPONSE_BYTES

    boundary_body = gzip.compress(b"x" * _MAX_RESPONSE_BYTES)
    requests, _ = _mock_default_httpx_client(monkeypatch, status_code=200, body=boundary_body,
        response_headers={"content-encoding": "gzip", "content-length": str(len(boundary_body))})
    response = audio_understanding._HttpxTransport().post(
        "https://generativelanguage.googleapis.com/test", headers={}, content=b"request",
    )
    assert len(response.content) == _MAX_RESPONSE_BYTES
    assert len(requests) == 1

    oversized_body = gzip.compress(b"x" * (_MAX_RESPONSE_BYTES + 1))
    oversized_requests, _ = _mock_default_httpx_client(monkeypatch, status_code=200, body=oversized_body,
        response_headers={"content-encoding": "gzip", "content-length": str(len(oversized_body))})
    permit = OneShotPermit()
    with pytest.raises(AudioUnderstandingError) as error:
        GeminiAudioAnalyzer(lambda: "test-key").analyze(prepared(), permit=permit)

    assert error.value.code == "response_too_large"
    assert error.value.outcome == "EVIDENCE_GAP"
    assert len(oversized_requests) == len(permit.consumed) == 1
