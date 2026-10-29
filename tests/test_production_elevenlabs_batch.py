"""Production entry regressions; injected wire does not prove live quality."""
import base64
import json
import wave

import pytest

from ai_video.production.elevenlabs import ElevenLabsTransportResponse
from ai_video.production.elevenlabs_batch import ElevenLabsSpeechTestBatch, run_elevenlabs_speech_batch
from ai_video.production.project import load_production_project
from tests.test_production_voice_candidate import _toolchain
from tests.paid_provider_support import NOW


def batch(**updates):
    values = dict(batch_id="eleven-test", scripts=("你好",), source_reference="fixture",
        voice_id="test-voice", unit_price_microunits=100,
        per_call_ceiling_microunits=10000, project_ceiling_microunits=20000)
    return ElevenLabsSpeechTestBatch(**{**values, **updates})


class Transport:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def request(self, request):
        self.calls.append(request)
        if self.failure == "timeout":
            raise TimeoutError("SECRET")
        if self.failure == "credential":
            request.headers["xi-api-key"].api_key()
        text = json.loads(request.body)["text"]
        timing = dict(characters=list(text), character_start_times_seconds=[i * .1 for i in range(len(text))],
                      character_end_times_seconds=[(i + 1) * .1 for i in range(len(text))])
        payload = dict(audio_base64=base64.b64encode(b"\0\0" * 48000).decode(),
                       alignment=timing, normalized_alignment=timing)
        return ElevenLabsTransportResponse(200, {"character-cost": str(len(text)), "request-id": f"test-request-{len(self.calls)}"},
            b"{}" if self.failure == "malformed" else json.dumps(payload).encode())


def run(root, exact, transport, credential=object()):
    return run_elevenlabs_speech_batch(root, exact, transport=transport, credential=credential,
                                      toolchain=_toolchain(), clock=lambda: NOW)


def test_chinese_batch_canonical_wav_reopen_and_drift(tmp_path):
    transport = Transport()
    exact = batch(scripts=("你好", "再见"))
    outputs = run(tmp_path, exact, transport)
    assert len(outputs) == 2
    with wave.open(str(outputs[0])) as wav:
        assert (wav.getframerate(), wav.getnchannels()) == (48000, 1)
    call = transport.calls[0]
    assert call.url == "https://api.elevenlabs.io/v1/text-to-speech/test-voice/with-timestamps"
    assert ("output_format", "pcm_48000") in call.query
    assert json.loads(call.body)["model_id"] == "eleven_multilingual_v2"
    loaded = load_production_project(tmp_path / "project.yaml")
    assert all(a.status.value == "succeeded" for a in loaded.manifest.attempts)
    before = (tmp_path / "state/manifest.json").read_bytes()
    assert run(tmp_path, exact, transport) == outputs
    assert len(transport.calls) == 2
    assert (tmp_path / "state/manifest.json").read_bytes() == before
    with pytest.raises(Exception, match="exact batch"):
        run(tmp_path, batch(voice_id="different"), transport)
    assert len(transport.calls) == 2


@pytest.mark.parametrize("failure", ["timeout", "credential", "malformed"])
def test_unknown_stops_batch_and_reopen(tmp_path, failure):
    class Secret:
        def api_key(self):
            raise RuntimeError("PRIVATE-SECRET")
    transport = Transport(failure)
    exact = batch(scripts=("你好", "再见"))
    with pytest.raises(Exception):
        run(tmp_path, exact, transport, Secret())
    loaded = load_production_project(tmp_path / "project.yaml")
    attempts = [a for a in loaded.manifest.attempts if a.operation == "voice_generation"]
    assert len(attempts) == 1 and attempts[0].status.value == "outcome_unknown"
    assert "PRIVATE-SECRET" not in loaded.manifest.model_dump_json()
    with pytest.raises(Exception, match="explicit recovery"):
        run(tmp_path, exact, transport, Secret())
    assert len(transport.calls) == 1


def test_budget_rejection_precedes_transport(tmp_path):
    transport = Transport()
    with pytest.raises(Exception):
        run(tmp_path, batch(per_call_ceiling_microunits=1), transport)
    assert not transport.calls


def test_cli_reuses_canonical_batch(tmp_path, monkeypatch, capsys):
    import sys
    from scripts import elevenlabs_speech_batch as cli
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, prepare_minimax_speech_test_project
    source = tmp_path / "source"
    prepare_minimax_speech_test_project(source, MiniMaxSpeechTestBatch(
        batch_id="source", scripts=("test",), source_reference="fixture"))
    transport = Transport()
    monkeypatch.setattr(cli, "_HttpTransport", lambda: transport)
    monkeypatch.setattr(sys, "argv", ["speech", "--root", str(tmp_path / "target"),
        "--source-project", str(source / "project.yaml"), "--text", "你好", "--voice-id", "voice",
        "--unit-price-microunits", "100", "--per-call-ceiling-microunits", "10000",
        "--project-ceiling-microunits", "20000"])
    cli.main()
    assert len(json.loads(capsys.readouterr().out)["wav_files"]) == 1
    cli.main()
    assert len(transport.calls) == 1


def test_http_transport_query_secret_and_no_redirect(monkeypatch):
    from scripts import elevenlabs_speech_batch as cli
    from ai_video.production.elevenlabs import ElevenLabsTransportRequest
    lookups = []
    def lookup(argv, **kwargs):
        import subprocess
        lookups.append(argv)
        return subprocess.CompletedProcess(argv, 0, b"PRIVATE-SECRET", b"")
    monkeypatch.setattr(cli.subprocess, "run", lookup)
    wires = []
    class Response:
        code = 200
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit):
            assert limit == 2 * 1024 * 1024 + 1
            return b"{}"
    class Opener:
        def open(self, wire, timeout):
            wires.append(wire)
            assert timeout == 90
            return Response()
    def opener(handler):
        assert handler.redirect_request(None, None, 302, "", {}, "https://elsewhere") is None
        return Opener()
    monkeypatch.setattr(cli, "build_opener", opener)
    request = ElevenLabsTransportRequest("POST", "https://api.elevenlabs.io/v1/text-to-speech/v/with-timestamps",
        (("output_format", "pcm_48000"), ("enable_logging", "true")),
        {"xi-api-key": cli._SecretServiceCredential()}, b"{}")
    cli._HttpTransport().request(request)
    assert wires[0].full_url.endswith("?output_format=pcm_48000&enable_logging=true")
    assert lookups == [["secret-tool", "lookup", "application", "ai-video", "provider", "elevenlabs",
                        "credential", "ELEVENLABS_API_KEY"]]
    assert "PRIVATE-SECRET" not in repr(request)


def test_cli_errors_hide_secret(monkeypatch, capsys):
    from scripts import elevenlabs_speech_batch as cli
    def fail(): raise RuntimeError("PRIVATE-SECRET")
    monkeypatch.setattr(cli, "main", fail)
    with pytest.raises(SystemExit): cli.entrypoint()
    assert json.loads(capsys.readouterr().out) == {"status": "stopped", "error_type": "RuntimeError"}


@pytest.mark.parametrize("code", ["VOICE_BUDGET_REJECTED", "VOICE_PROVIDER_OUTCOME_UNKNOWN"])
def test_cli_typed_errors_preserve_recovery_signal_without_secret(monkeypatch, capsys, code):
    from ai_video.errors import AiVideoError, ErrorCode
    from scripts import elevenlabs_speech_batch as cli
    exact_code = ErrorCode[code]
    def fail():
        raise AiVideoError(code=exact_code, user_message="PRIVATE-SECRET message",
                           technical_detail="PRIVATE-SECRET detail", retryable=False)
    monkeypatch.setattr(cli, "main", fail)
    with pytest.raises(SystemExit) as stopped:
        cli.entrypoint()
    assert stopped.value.code == 1
    output = capsys.readouterr()
    assert json.loads(output.out) == {"status": "stopped", "error_type": "AiVideoError",
                                     "code": exact_code.value, "retryable": False}
    assert "PRIVATE-SECRET" not in output.out + output.err
