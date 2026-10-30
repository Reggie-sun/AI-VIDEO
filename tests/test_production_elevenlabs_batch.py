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


def test_v4_batch_omits_unsupported_settings_and_seals_language(tmp_path):
    transport = Transport()
    exact = batch(model_id="eleven_v4")
    assert exact.parameters.style_milli is None and exact.parameters.use_speaker_boost is None
    run(tmp_path, exact, transport)
    body = json.loads(transport.calls[0].body)
    assert body["model_id"] == "eleven_v4"
    assert body["language_code"] == "zh"
    assert body["voice_settings"] == {"stability": 0.5, "similarity_boost": 0.75, "speed": 1.0}
    assert batch().policy_id != exact.policy_id


def test_v4_rejects_unsupported_settings_before_transport(tmp_path):
    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production.audio import VoiceProviderParameters
    transport = Transport()
    exact = batch(model_id="eleven_v4", parameters=VoiceProviderParameters(
        stability_milli=500, style_milli=0))
    with pytest.raises(AiVideoError) as caught:
        run(tmp_path, exact, transport)
    assert caught.value.code is ErrorCode.VOICE_REQUEST_INVALID
    assert transport.calls == []


class DirectedTransport:
    """Provider mock returns explicit spoken alignment, never inferred tag removal."""
    def __init__(self, alignment_text="你好", normalized_text="ni hao"):
        self.calls = []
        self.alignment_text = alignment_text
        self.normalized_text = normalized_text

    def request(self, request):
        self.calls.append(request)
        submitted = json.loads(request.body)["text"]
        def timing(text):
            return dict(characters=list(text),
                        character_start_times_seconds=[i * .01 for i in range(len(text))],
                        character_end_times_seconds=[(i + 1) * .01 for i in range(len(text))])
        payload = dict(audio_base64=base64.b64encode(b"\0\0" * 48000).decode(),
                       alignment=timing(self.alignment_text),
                       normalized_alignment=timing(self.normalized_text))
        return ElevenLabsTransportResponse(200,
            {"character-cost": str(len(submitted)), "request-id": "directed-test"},
            json.dumps(payload).encode())


def directed_batch(**updates):
    from ai_video.production.audio import VoiceProviderParameters
    return batch(model_id="eleven_v4", parameters=VoiceProviderParameters(
        stability_milli=500, similarity_boost_milli=750, speed_milli=1000,
        audio_tags=("quiet",)), **updates)


def test_empty_audio_tags_preserve_historical_batch_hash():
    assert batch().policy_id == "elevenlabs-batch-1adaf10f42dd030e38f835734c178eac431b36cd672d40a19de18bf58ad612ec"


def test_directed_batch_seals_wire_egress_and_replays_without_post(tmp_path):
    import hashlib
    transport = DirectedTransport()
    exact = directed_batch()
    paths = run(tmp_path, exact, transport)
    assert len(paths) == 1
    submitted = json.loads(transport.calls[0].body)["text"]
    assert submitted == "[quiet] 你好"
    attempt = tmp_path / "state/voice/attempts/eleven-test-1"
    request = json.loads((attempt / "request.json").read_text())
    preview = json.loads((attempt / "preview.json").read_text())
    assert request["script_text"] == "你好"
    assert request["script_hash"] == hashlib.sha256("你好".encode()).hexdigest()
    assert preview["billable_units_upper_bound"] == len(submitted)
    assert preview["estimated_cost_upper_bound_microunits"] == len(submitted) * 100
    assert preview["script_utf8_bytes"] == len(submitted.encode())
    gates = [json.loads(p.read_text()) for p in (tmp_path / "state/paid-provider/gates").glob("*.json")]
    assert gates
    for gate in gates:
        item = gate["preview"]["egress_items"][0]
        assert item["sha256"] == hashlib.sha256(submitted.encode()).hexdigest()
        assert item["size_bytes"] == len(submitted.encode())
    alignment = json.loads((attempt / "alignment.json").read_text())
    assert "".join(alignment["alignment"]["characters"]) == "你好"
    assert run(tmp_path, exact, transport) == paths
    assert len(transport.calls) == 1
    from ai_video.production.audio import VoiceProviderParameters
    altered = exact.model_copy(update={"parameters": VoiceProviderParameters(audio_tags=("tired",))})
    with pytest.raises(Exception, match="exact batch"):
        run(tmp_path, altered, transport)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("returned", ["[quiet] 你好", "你", "你好呀"])
def test_directed_alignment_gap_stops_without_retry_or_second_line(tmp_path, returned):
    transport = DirectedTransport(alignment_text=returned, normalized_text=returned)
    exact = directed_batch(scripts=("你好", "再见"))
    with pytest.raises(Exception):
        run(tmp_path, exact, transport)
    loaded = load_production_project(tmp_path / "project.yaml")
    attempts = [a for a in loaded.manifest.attempts if a.operation == "voice_generation"]
    assert len(attempts) == 1
    assert attempts[0].status.value == "outcome_unknown"
    with pytest.raises(Exception, match="explicit recovery"):
        run(tmp_path, exact, transport)
    assert len(transport.calls) == 1


def test_directed_batch_budgets_compiled_tags_before_transport(tmp_path):
    transport = DirectedTransport()
    with pytest.raises(Exception):
        run(tmp_path, directed_batch(per_call_ceiling_microunits=300), transport)
    assert transport.calls == []


def test_directed_batch_accepts_exact_normalized_spoken_alignment(tmp_path):
    transport = DirectedTransport(alignment_text="ni hao", normalized_text="你好")
    paths = run(tmp_path, directed_batch(), transport)
    assert len(paths) == 1
    assert len(transport.calls) == 1


def test_directed_batch_does_not_strip_literal_dialogue_brackets(tmp_path):
    transport = DirectedTransport(alignment_text="[A]你好", normalized_text="[A]你好")
    paths = run(tmp_path, directed_batch(scripts=("[A]你好",)), transport)
    assert len(paths) == 1
    assert json.loads(transport.calls[0].body)["text"] == "[quiet] [A]你好"
    attempt = tmp_path / "state/voice/attempts/eleven-test-1"
    alignment = json.loads((attempt / "alignment.json").read_text())
    assert "".join(alignment["alignment"]["characters"]) == "[A]你好"


def test_cli_audio_tag_uses_canonical_directed_batch(tmp_path, monkeypatch, capsys):
    import sys
    from scripts import elevenlabs_speech_batch as cli
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, prepare_minimax_speech_test_project
    source = tmp_path / "source"
    prepare_minimax_speech_test_project(source, MiniMaxSpeechTestBatch(
        batch_id="source", scripts=("test",), source_reference="fixture"))
    transport = DirectedTransport()
    monkeypatch.setattr(cli, "_HttpTransport", lambda: transport)
    monkeypatch.setattr(sys, "argv", ["speech", "--root", str(tmp_path / "target"),
        "--source-project", str(source / "project.yaml"), "--text", "你好", "--voice-id", "voice",
        "--model-id", "eleven_v4", "--audio-tag", "quiet",
        "--unit-price-microunits", "100", "--per-call-ceiling-microunits", "10000",
        "--project-ceiling-microunits", "20000"])
    cli.main()
    assert len(json.loads(capsys.readouterr().out)["wav_files"]) == 1
    body = json.loads(transport.calls[0].body)
    assert body["text"] == "[quiet] 你好"
    assert body["voice_settings"] == {"stability": 0.5, "similarity_boost": 0.75, "speed": 1.0}
    cli.main()
    assert len(transport.calls) == 1


@pytest.fixture
def performance_context_package(tmp_path, monkeypatch):
    import hashlib
    from scripts import elevenlabs_performance_context as context
    monkeypatch.setattr(context, "REPO_ROOT", tmp_path)
    line = dict(id="L1", text="你好", role="relay", unit="D1", shot_s=4.0)
    source = tmp_path / "source-plan.json"
    source.write_text(json.dumps({"lines": [line]}, ensure_ascii=False))
    row = {**line, "audio_tags": ["quiet"], "model_candidate": "eleven_v4",
           "performance_context": {key: "explicit scene fact" for key in
            ("trigger", "listener", "objective", "subtext", "delivery", "after", "knowledge")}}
    package = dict(source_plan="source-plan.json",
        source_plan_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        shared_scene="Night dispatcher speaking to record keeper.", rows=[row],
        submit_status="BLOCKED_BY_PREVIOUS_UNKNOWN")
    path = tmp_path / "context.json"
    path.write_text(json.dumps(package, ensure_ascii=False))
    return path, package, source


def _forbid_context_execution(monkeypatch):
    from scripts import elevenlabs_speech_batch as cli
    def forbidden(*args, **kwargs):
        pytest.fail("Offline/blocked context crossed the execution boundary")
    for name in ("load_production_project", "_HttpTransport", "_SecretServiceCredential",
                 "run_elevenlabs_speech_batch", "_toolchain"):
        monkeypatch.setattr(cli, name, forbidden)


def test_context_cli_preview_is_offline_and_keeps_full_scene(performance_context_package, monkeypatch, capsys):
    import sys
    from scripts import elevenlabs_speech_batch as cli
    path, package, _ = performance_context_package
    _forbid_context_execution(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["speech", "--performance-context", str(path),
                                    "--line-id", "L1", "--preview-context"])
    cli.main()
    preview = json.loads(capsys.readouterr().out)
    assert preview["script_text"] == package["rows"][0]["text"]
    assert preview["shared_scene"] and preview["line"]["performance_context"]["listener"]
    assert preview["synthesis_text"].endswith(preview["script_text"])
    assert preview["authoring_blocked"] is True
    assert preview["network_calls"] == 0
    assert preview["canonical_paid_preview"] is False
    assert preview["authorization_granted"] is False


def test_blocked_context_execution_precedes_root_source_or_secret(performance_context_package, tmp_path, monkeypatch):
    import sys
    from ai_video.errors import AiVideoError, ErrorCode
    from scripts import elevenlabs_speech_batch as cli
    path, _, _ = performance_context_package
    _forbid_context_execution(monkeypatch)
    target = tmp_path / "not-created"
    monkeypatch.setattr(sys, "argv", ["speech", "--performance-context", str(path),
                                    "--line-id", "L1", "--root", str(target)])
    with pytest.raises(AiVideoError) as caught:
        cli.main()
    assert caught.value.code is ErrorCode.VOICE_REQUEST_INVALID
    assert not target.exists()


@pytest.mark.parametrize("extra", [
    ["--text", "wrong"], ["--audio-tag", "whisper"],
    ["--model-id", "eleven_multilingual_v2"],
])
def test_context_cli_rejects_conflicting_explicit_inputs(performance_context_package, monkeypatch, extra):
    import sys
    from scripts import elevenlabs_speech_batch as cli
    path, _, _ = performance_context_package
    _forbid_context_execution(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["speech", "--performance-context", str(path),
                                    "--line-id", "L1", "--preview-context", *extra])
    with pytest.raises(SystemExit):
        cli.main()


def test_context_line_id_without_package_is_invalid(monkeypatch):
    import sys
    from scripts import elevenlabs_speech_batch as cli
    _forbid_context_execution(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["speech", "--line-id", "L1"])
    with pytest.raises(SystemExit):
        cli.main()


@pytest.mark.parametrize("mutation", ["stale", "text", "role", "unit", "duration", "duplicate_id", "escape", "absolute"])
def test_context_rejects_source_identity_drift(performance_context_package, mutation):
    from scripts.elevenlabs_performance_context import load_performance_context
    from ai_video.errors import AiVideoError
    path, data, source = performance_context_package
    if mutation == "stale":
        source.write_text(source.read_text() + " ")
    elif mutation == "duplicate_id":
        data["rows"].append(dict(data["rows"][0]))
    elif mutation == "escape":
        data["source_plan"] = "../source-plan.json"
    elif mutation == "absolute":
        data["source_plan"] = str(source)
    else:
        key = {"text": "text", "role": "role", "unit": "unit", "duration": "shot_s"}[mutation]
        data["rows"][0][key] = 5.0 if key == "shot_s" else "wrong"
    path.write_text(json.dumps(data))
    with pytest.raises(AiVideoError):
        load_performance_context(path, "L1")


def test_context_rejects_duplicate_json_keys_and_oversize(performance_context_package):
    from scripts.elevenlabs_performance_context import load_performance_context, MAX_CONTEXT_BYTES
    from ai_video.errors import AiVideoError
    path, _, _ = performance_context_package
    path.write_text('{"source_plan":"a","source_plan":"b"}')
    with pytest.raises(AiVideoError):
        load_performance_context(path, "L1")
    path.write_bytes(b" " * (MAX_CONTEXT_BYTES + 1))
    with pytest.raises(AiVideoError):
        load_performance_context(path, "L1")


def test_context_rejects_symlink_files_and_parent_directories(performance_context_package, tmp_path):
    from scripts.elevenlabs_performance_context import load_performance_context
    from ai_video.errors import AiVideoError
    path, data, source = performance_context_package
    link = tmp_path / "context-link.json"
    link.symlink_to(path)
    with pytest.raises(AiVideoError):
        load_performance_context(link, "L1")
    folder = tmp_path / "real"
    folder.mkdir()
    (folder / "source.json").write_bytes(source.read_bytes())
    (tmp_path / "linked-folder").symlink_to(folder, target_is_directory=True)
    data["source_plan"] = "linked-folder/source.json"
    path.write_text(json.dumps(data))
    with pytest.raises(AiVideoError):
        load_performance_context(path, "L1")


def test_ready_context_cli_runs_canonical_batch_and_seals_context_reference(performance_context_package, tmp_path, monkeypatch, capsys):
    import sys, hashlib
    from scripts import elevenlabs_speech_batch as cli
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, prepare_minimax_speech_test_project
    path, package, _ = performance_context_package
    package["submit_status"] = "READY_FOR_CANONICAL_PREFLIGHT"
    path.write_text(json.dumps(package))
    context_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    source = tmp_path / "source-project"
    prepare_minimax_speech_test_project(source, MiniMaxSpeechTestBatch(
        batch_id="source", scripts=("test",), source_reference="fixture"))
    transport = DirectedTransport()
    monkeypatch.setattr(cli, "_HttpTransport", lambda: transport)
    target = tmp_path / "target"
    monkeypatch.setattr(sys, "argv", ["speech", "--performance-context", str(path),
        "--line-id", "L1", "--root", str(target), "--source-project", str(source / "project.yaml"),
        "--voice-id", "voice", "--unit-price-microunits", "100",
        "--per-call-ceiling-microunits", "10000", "--project-ceiling-microunits", "20000"])
    cli.main()
    assert len(json.loads(capsys.readouterr().out)["wav_files"]) == 1
    assert json.loads(transport.calls[0].body)["text"] == "[quiet] 你好"
    loaded = load_production_project(target / "project.yaml")
    sealed = json.loads(loaded.brief.objective)
    assert f"performance-context:{context_sha}:line:L1" in sealed["source_reference"]
    cli.main()
    assert len(transport.calls) == 1


@pytest.mark.parametrize("restriction", ["missing_status", "package_pointer", "line_pointer"])
def test_ready_context_cannot_override_unresolved_authoring_restrictions(performance_context_package, restriction):
    from scripts.elevenlabs_performance_context import load_performance_context
    path, data, _ = performance_context_package
    data["submit_status"] = "READY_FOR_CANONICAL_PREFLIGHT"
    if restriction == "missing_status":
        del data["submit_status"]
    elif restriction == "package_pointer":
        data["blocked_by_attempt"] = "preserve-unknown-attempt"
    else:
        data["rows"][0]["blocked_by_attempt"] = "preserve-unknown-attempt"
    path.write_text(json.dumps(data))
    assert load_performance_context(path, "L1")["authoring_blocked"] is True


def test_ready_context_execution_requires_explicit_voice(performance_context_package, monkeypatch):
    import sys
    from scripts import elevenlabs_speech_batch as cli
    path, data, _ = performance_context_package
    data["submit_status"] = "READY_FOR_CANONICAL_PREFLIGHT"
    path.write_text(json.dumps(data))
    _forbid_context_execution(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["speech", "--performance-context", str(path), "--line-id", "L1",
        "--root", "not-created", "--source-project", "not-read.yaml", "--unit-price-microunits", "100",
        "--per-call-ceiling-microunits", "10000", "--project-ceiling-microunits", "20000"])
    with pytest.raises(SystemExit):
        cli.main()


@pytest.mark.parametrize("existing_bus", [None, "unix:path=/explicit/user-bus"])
def test_secret_supplier_preserves_exact_reference_and_user_bus(monkeypatch, existing_bus):
    import os
    import subprocess
    from scripts import elevenlabs_speech_batch as cli
    if existing_bus is None:
        monkeypatch.delenv("DBUS_SESSION_BUS_ADDRESS", raising=False)
    else:
        monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", existing_bus)
    calls = []
    def lookup(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, b"PRIVATE-SECRET", b"")
    monkeypatch.setattr(cli.subprocess, "run", lookup)
    assert cli._SecretServiceCredential().api_key() == "PRIVATE-SECRET"
    argv, kwargs = calls[0]
    assert argv == ["secret-tool", "lookup", "application", "ai-video", "provider", "elevenlabs",
                    "credential", "ELEVENLABS_API_KEY"]
    assert kwargs["env"]["DBUS_SESSION_BUS_ADDRESS"] == (
        existing_bus or f"unix:path=/run/user/{os.getuid()}/bus")
    assert os.environ.get("DBUS_SESSION_BUS_ADDRESS") == existing_bus
    assert len(calls) == 1
