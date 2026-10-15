"""Development-only durable operator binding for the audio MCP runtime."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import stat
from threading import Event
import wave

import httpx
import pytest

from ai_video_mcp.audio_understanding import (
    AudioUnderstandingError,
    GeminiAudioAnalyzer,
    prepare_audio_request,
)


MODEL = "gemini-3.8-flash"
ORIGIN = "https://generativelanguage.googleapis.com"
AUTHORIZATION_REFERENCE = (
    "user-gemini-audio-key-provision-20261015"
)


def _wav() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 1600)
    return output.getvalue()


def _response() -> httpx.Response:
    observations = {
        "segments": [],
        "voice_description": "not discernible",
        "delivery_description": "not discernible",
        "background_sounds": [],
        "uncertainties": ["synthetic test audio"],
    }
    return httpx.Response(200, json={
        "modelVersion": "gemini-3.8-flash-test",
        "candidates": [{"finishReason": "STOP", "content": {
            "parts": [{"text": json.dumps(observations)}],
        }}],
    })


class FakeTransport:
    def __init__(self, handler=None):
        self.handler = handler or (lambda _url, _headers, _content: _response())
        self.calls = []

    def post(self, url, *, headers, content):
        self.calls.append((url, dict(headers), content))
        return self.handler(url, headers, content)


@pytest.fixture
def operator_case(tmp_path):
    source = tmp_path / "source.wav"
    source_bytes = _wav()
    source.write_bytes(source_bytes)
    prepared = prepare_audio_request(
        audio_bytes=source_bytes,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_size_bytes=len(source_bytes),
        model_id=MODEL,
    )
    now = datetime.now(timezone.utc)
    unit = tmp_path / "operator-unit"
    from ai_video_mcp.audio_operator import prepare_operator_unit
    receipt = prepare_operator_unit(
        unit,
        media_path=source,
        prepared=prepared,
        authorization_reference=AUTHORIZATION_REFERENCE,
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    return unit, source, prepared, receipt, now


def _runtime(case, *, transport=None, now=None, credential=None):
    from ai_video_mcp.audio_operator import runtime_for_unit
    unit, _source, _prepared, receipt, issued = case
    return runtime_for_unit(
        unit,
        receipt["intent_sha256"],
        credential_supplier=credential or (lambda: "test-only-key"),
        transport=transport,
        clock=now or (lambda: issued + timedelta(seconds=1)),
    )


def _execute(runtime, prepared):
    permit = runtime.permit_supplier(prepared.preview())
    return runtime.analyzer.analyze(prepared, permit=permit)


def test_prepare_seals_exact_preview_source_wire_and_internal_reservation(operator_case):
    unit, source, prepared, returned, _now = operator_case
    intent_bytes = (unit / "intent.json").read_bytes()
    reservation_bytes = (unit / "reservation.json").read_bytes()
    intent = json.loads(intent_bytes)
    reservation = json.loads(reservation_bytes)

    assert returned["intent_path"] == str(unit / "intent.json")
    assert returned["intent_sha256"] == hashlib.sha256(intent_bytes).hexdigest()
    assert intent["scope"] == "DEVELOPMENT_ONLY"
    assert intent["model_id"] == MODEL
    assert intent["origin"] == ORIGIN
    assert intent["authorization"] == {
        "source": "user", "reference": AUTHORIZATION_REFERENCE,
    }
    assert intent["budget"]["source"] == "operator_internal_upper_bound"
    assert intent["source"] == {
        "path": str(source),
        "sha256": prepared.source_sha256,
        "size_bytes": source.stat().st_size,
    }
    assert intent["request"]["preview"] == prepared.preview()
    assert intent["request"]["wire_sha256"] == hashlib.sha256(prepared._payload).hexdigest()
    assert intent["egress"]["audio_sha256"] == prepared.audio_sha256
    assert intent["egress"]["audio_size_bytes"] == prepared.audio_size_bytes
    assert len(intent["egress"]["prompt_sha256"]) == 64
    assert len(intent["egress"]["schema_sha256"]) == 64
    assert reservation["intent_sha256"] == returned["intent_sha256"]
    assert reservation["currency"] == "USD"
    assert reservation["reserved_microunits"] == 50_000
    assert reservation["submit_count"] == 1
    assert b"inline_data" not in intent_bytes and b"test-only-key" not in intent_bytes


@pytest.mark.parametrize("field,value", [
    ("model_id", "gemini-3.8-pro"),
    ("endpoint", "https://attacker.invalid/upload"),
    ("source_sha256", "f" * 64),
])
def test_prepare_rejects_prepared_request_drift(operator_case, tmp_path, field, value):
    unit, source, prepared, _returned, now = operator_case
    from ai_video_mcp.audio_operator import prepare_operator_unit
    with pytest.raises(AudioUnderstandingError):
        prepare_operator_unit(
            tmp_path / f"invalid-{field}",
            media_path=source,
            prepared=replace(prepared, **{field: value}),
            authorization_reference=AUTHORIZATION_REFERENCE,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )


def test_prepare_rejects_tampered_wire_and_source_drift(operator_case, tmp_path):
    _unit, source, prepared, _returned, now = operator_case
    from ai_video_mcp.audio_operator import prepare_operator_unit
    altered = replace(prepared, _payload=prepared._payload + b" ")
    with pytest.raises(AudioUnderstandingError):
        prepare_operator_unit(
            tmp_path / "tampered-wire",
            media_path=source,
            prepared=altered,
            authorization_reference=AUTHORIZATION_REFERENCE,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    source.write_bytes(b"different source bytes")
    with pytest.raises(AudioUnderstandingError):
        prepare_operator_unit(
            tmp_path / "changed-source",
            media_path=source,
            prepared=prepared,
            authorization_reference=AUTHORIZATION_REFERENCE,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )


def test_prepare_never_overwrites_existing_unit(operator_case):
    unit, source, prepared, _returned, now = operator_case
    from ai_video_mcp.audio_operator import prepare_operator_unit
    before = (unit / "intent.json").read_bytes()
    with pytest.raises(AudioUnderstandingError):
        prepare_operator_unit(
            unit,
            media_path=source,
            prepared=prepared,
            authorization_reference=AUTHORIZATION_REFERENCE,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    assert (unit / "intent.json").read_bytes() == before


@pytest.mark.parametrize("tamper", ["intent", "reservation"])
def test_runtime_rejects_tampered_intent_or_reservation(operator_case, tamper):
    unit, _source, _prepared, returned, now = operator_case
    path = unit / ("intent.json" if tamper == "intent" else "reservation.json")
    value = json.loads(path.read_bytes())
    value["tampered"] = True
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(AudioUnderstandingError):
        _runtime((unit, None, None, returned, now))


@pytest.mark.parametrize("offset", [-1, 601])
def test_runtime_rejects_future_or_expired_clock(operator_case, offset):
    unit, _source, _prepared, returned, issued = operator_case
    from ai_video_mcp.audio_operator import runtime_for_unit
    with pytest.raises(AudioUnderstandingError):
        runtime_for_unit(
            unit,
            returned["intent_sha256"],
            credential_supplier=lambda: "test-only-key",
            transport=FakeTransport(),
            clock=lambda: issued + timedelta(seconds=offset),
        )


def test_runtime_rejects_wrong_expected_intent_hash(operator_case):
    unit, _source, _prepared, _returned, now = operator_case
    from ai_video_mcp.audio_operator import runtime_for_unit
    with pytest.raises(AudioUnderstandingError):
        runtime_for_unit(unit, "f" * 64, credential_supplier=lambda: "test-only-key",
                         clock=lambda: now + timedelta(seconds=1))


def test_runtime_is_an_existing_tool_runtime_and_posts_exactly_once(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    transport = FakeTransport()
    runtime = _runtime(operator_case, transport=transport)
    from ai_video_mcp.tools.audio_understand import AudioUnderstandingRuntime
    assert isinstance(runtime, AudioUnderstandingRuntime)
    assert isinstance(runtime.analyzer, GeminiAudioAnalyzer)
    result = _execute(runtime, prepared)
    assert result["response_model_id"] == "gemini-3.8-flash-test"
    assert "PASS" not in json.dumps(result)
    assert len(transport.calls) == 1
    url, headers, wire = transport.calls[0]
    assert url == prepared.endpoint == f"{ORIGIN}/v1beta/models/{MODEL}:generateContent"
    assert headers["x-goog-api-key"] == "test-only-key"
    assert wire == prepared._payload
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "SUCCEEDED"
    assert outcome["consumed"] is True
    assert outcome["evidence"]["response_sha256"] == result["response_sha256"]
    assert outcome["qa_acceptance"] == "NOT_EVALUATED"
    assert outcome["human_acceptance"] == "NOT_EVALUATED"
    assert "test-only-key" not in json.dumps(outcome)


def test_consumed_unit_cannot_be_reopened_or_replayed_after_restart(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    runtime = _runtime(operator_case, transport=FakeTransport())
    _execute(runtime, prepared)
    with pytest.raises(AudioUnderstandingError):
        _runtime(operator_case, transport=FakeTransport())
    assert (unit / "consume.json").is_file()


def test_expiry_between_source_validation_and_consume_prevents_post(operator_case):
    unit, _source, prepared, returned, issued = operator_case
    from ai_video_mcp.audio_operator import runtime_for_unit

    boundary = issued + timedelta(minutes=10)
    instants = iter((
        issued + timedelta(seconds=1),
        issued + timedelta(seconds=2),
        issued + timedelta(seconds=3),
        boundary - timedelta(microseconds=1),
        boundary,
        boundary + timedelta(seconds=1),
    ))
    transport = FakeTransport()
    runtime = runtime_for_unit(
        unit,
        returned["intent_sha256"],
        credential_supplier=lambda: "test-only-key",
        transport=transport,
        clock=lambda: next(instants),
    )
    permit = runtime.permit_supplier(prepared.preview())

    with pytest.raises(AudioUnderstandingError):
        runtime.analyzer.analyze(prepared, permit=permit)

    assert transport.calls == []
    assert not (unit / "consume.json").exists()
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "REJECTED"
    assert outcome["consumed"] is False


def test_consumed_http_200_evidence_gap_is_preserved_across_restart(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    invalid_observations = {"segments": "not-an-array"}
    invalid_response = httpx.Response(200, json={
        "modelVersion": "gemini-3.8-flash-test",
        "candidates": [{"finishReason": "STOP", "content": {
            "parts": [{"text": json.dumps(invalid_observations)}],
        }}],
    })
    transport = FakeTransport(lambda *_: invalid_response)
    runtime = _runtime(operator_case, transport=transport)

    with pytest.raises(AudioUnderstandingError) as error:
        _execute(runtime, prepared)

    assert error.value.code == "invalid_observations"
    assert error.value.outcome == "EVIDENCE_GAP"
    assert len(transport.calls) == 1
    assert (unit / "consume.json").is_file()
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "EVIDENCE_GAP"
    assert outcome["outcome"] == "EVIDENCE_GAP"
    assert outcome["consumed"] is True

    retry_transport = FakeTransport()
    with pytest.raises(AudioUnderstandingError):
        _runtime(operator_case, transport=retry_transport)
    assert retry_transport.calls == []


def test_credential_failure_records_unconsumed_outcome_without_post(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    secret = "never-in-outcome-credential-detail"
    transport = FakeTransport()
    runtime = _runtime(
        operator_case,
        transport=transport,
        credential=lambda: (_ for _ in ()).throw(RuntimeError(secret)),
    )
    with pytest.raises(AudioUnderstandingError) as error:
        _execute(runtime, prepared)
    assert error.value.code == "credential_unavailable"
    assert secret not in str(error.value)
    assert transport.calls == []
    assert not (unit / "consume.json").exists()
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "REJECTED"
    assert outcome["consumed"] is False
    assert secret not in json.dumps(outcome)


def test_wrong_preview_is_recorded_without_credential_lookup_or_post(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    credential_calls = []
    transport = FakeTransport()
    runtime = _runtime(operator_case, transport=transport, credential=lambda: credential_calls.append(True))
    with pytest.raises(AudioUnderstandingError) as error:
        runtime.permit_supplier({**prepared.preview(), "source_sha256": "f" * 64})
    assert error.value.code == "operator_preview_mismatch"
    assert credential_calls == []
    assert transport.calls == []
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "REJECTED"
    assert outcome["consumed"] is False


def test_source_drift_after_runtime_binding_closes_unit_without_post(operator_case):
    unit, source, prepared, _returned, _now = operator_case
    transport = FakeTransport()
    runtime = _runtime(operator_case, transport=transport)
    source.write_bytes(b"changed exact source")
    with pytest.raises(AudioUnderstandingError):
        _execute(runtime, prepared)
    assert transport.calls == []
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "REJECTED"
    assert outcome["consumed"] is False


def test_unknown_transport_consumes_once_records_unknown_and_never_retries(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    transport = FakeTransport(lambda *_: (_ for _ in ()).throw(httpx.ReadTimeout("private transport detail")))
    runtime = _runtime(operator_case, transport=transport)
    with pytest.raises(AudioUnderstandingError) as error:
        _execute(runtime, prepared)
    assert error.value.code == "transport_unknown"
    assert error.value.outcome == "UNKNOWN"
    assert "private transport detail" not in str(error.value)
    assert len(transport.calls) == 1
    assert (unit / "consume.json").exists()
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "UNKNOWN"
    assert outcome["consumed"] is True


def test_consume_write_uncertainty_is_unknown_and_never_posts(operator_case, monkeypatch):
    unit, _source, prepared, _returned, _now = operator_case
    from ai_video_mcp import audio_operator
    transport = FakeTransport()
    runtime = _runtime(operator_case, transport=transport)
    real_write = audio_operator._write

    def uncertain(fd, name, data):
        real_write(fd, name, data)
        if name == "consume.json":
            raise OSError("private fsync detail")

    monkeypatch.setattr(audio_operator, "_write", uncertain)
    with pytest.raises(AudioUnderstandingError) as error:
        _execute(runtime, prepared)
    assert error.value.outcome == "UNKNOWN"
    assert transport.calls == []
    assert (unit / "consume.json").exists()
    outcome = json.loads((unit / "outcome.json").read_bytes())
    assert outcome["status"] == "UNKNOWN"
    assert outcome["consumed"] is True


def test_outcome_write_failure_after_consumption_fails_closed(operator_case, monkeypatch):
    unit, _source, prepared, _returned, _now = operator_case
    from ai_video_mcp import audio_operator
    transport = FakeTransport()
    runtime = _runtime(operator_case, transport=transport)
    real_write = audio_operator._write

    def fail_outcome(fd, name, data):
        if name == "outcome.json":
            raise OSError("private receipt detail")
        real_write(fd, name, data)

    monkeypatch.setattr(audio_operator, "_write", fail_outcome)
    with pytest.raises(AudioUnderstandingError) as error:
        _execute(runtime, prepared)
    assert error.value.outcome == "UNKNOWN"
    assert len(transport.calls) == 1
    assert (unit / "consume.json").exists()
    assert not (unit / "outcome.json").exists()
    with pytest.raises(AudioUnderstandingError):
        _runtime(operator_case, transport=FakeTransport())


def test_concurrent_contenders_can_consume_and_post_only_once(operator_case):
    unit, _source, prepared, _returned, _now = operator_case
    post_started, finish_post = Event(), Event()

    def blocked_post(_url, _headers, _content):
        post_started.set()
        if not finish_post.wait(5):
            raise TimeoutError
        return _response()

    transport = FakeTransport(blocked_post)
    runtimes = [_runtime(operator_case, transport=transport) for _ in range(2)]

    def run(runtime):
        try:
            return _execute(runtime, prepared)
        except AudioUnderstandingError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        winner = pool.submit(run, runtimes[0])
        assert post_started.wait(2)
        loser = pool.submit(run, runtimes[1])
        try:
            loser_result = loser.result(timeout=2)
            assert loser_result == "operator_preview_mismatch"
            assert not (unit / "outcome.json").exists()
        finally:
            finish_post.set()
        winner_result = winner.result(timeout=2)
    assert len(transport.calls) == 1
    assert isinstance(winner_result, dict)
    assert loser_result == "operator_preview_mismatch"
    receipt = json.loads((unit / "outcome.json").read_bytes())
    assert receipt["consumed"] is True


def test_build_runtime_reads_only_two_nonsecret_env_values_and_exact_secret(monkeypatch, operator_case):
    unit, _source, _prepared, returned, _now = operator_case
    from ai_video_mcp import audio_operator
    monkeypatch.setenv("VIDEO_MCP_AUDIO_OPERATOR_UNIT", str(unit))
    monkeypatch.setenv("VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256", returned["intent_sha256"])
    monkeypatch.setenv("GEMINI_API_KEY", "ambient-key-must-not-be-read")
    calls = []
    bus = Path(f"/run/user/{__import__('os').getuid()}/bus")
    real_lstat = audio_operator.os.lstat

    def lstat(path):
        if Path(path) == bus:
            return type("BusStat", (), {"st_mode": stat.S_IFSOCK, "st_uid": __import__('os').getuid()})()
        return real_lstat(path)

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return __import__("subprocess").CompletedProcess(argv, 0, b"secret-service-test-key\n", b"")

    monkeypatch.setattr(audio_operator.os, "lstat", lstat)
    monkeypatch.setattr(audio_operator.subprocess, "run", run)
    runtime = audio_operator.build_runtime()
    assert isinstance(runtime, audio_operator.AudioUnderstandingRuntime)
    assert runtime.analyzer._credential_supplier() == "secret-service-test-key"
    assert calls[0][0] == [
        "secret-tool", "lookup", "application", "ai-video", "provider", "gemini-audio",
        "credential", "GEMINI_API_KEY",
    ]
    assert calls[0][1]["env"]["DBUS_SESSION_BUS_ADDRESS"] == f"unix:path={bus}"
    assert "GEMINI_API_KEY" not in calls[0][1]["env"]


def test_build_runtime_rejects_non_owner_bus_without_secret_lookup(monkeypatch, operator_case):
    unit, _source, _prepared, returned, _now = operator_case
    from ai_video_mcp import audio_operator
    monkeypatch.setenv("VIDEO_MCP_AUDIO_OPERATOR_UNIT", str(unit))
    monkeypatch.setenv("VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256", returned["intent_sha256"])
    bus = Path(f"/run/user/{__import__('os').getuid()}/bus")
    real_lstat = audio_operator.os.lstat
    monkeypatch.setattr(audio_operator.os, "lstat", lambda path: (
        type("BusStat", (), {"st_mode": stat.S_IFSOCK, "st_uid": -1})()
        if Path(path) == bus else real_lstat(path)
    ))
    calls = []
    monkeypatch.setattr(audio_operator.subprocess, "run", lambda *a, **k: calls.append(a))
    runtime = audio_operator.build_runtime()
    with pytest.raises(AudioUnderstandingError):
        runtime.analyzer._credential_supplier()
    assert calls == []
