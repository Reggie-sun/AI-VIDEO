"""Exact media, opt-in execution and public audio MCP integration."""
from __future__ import annotations

import ast
import hashlib
import io
import json
import subprocess
import sys
import wave
from pathlib import Path

import httpx
import pytest

from ai_video_mcp.config import ServerConfig


@pytest.fixture
def audio_source(tmp_path):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * 1600)
    path = tmp_path / "source.wav"
    path.write_bytes(output.getvalue())
    return path, hashlib.sha256(path.read_bytes()).hexdigest(), ServerConfig(audio_media_root=str(tmp_path))


def _call(source, *, execute=False, config=None, expected=None):
    from ai_video_mcp.tools.audio_understand import audio_understand
    path, sha, selected = source
    return audio_understand(str(path), config or selected, expected_sha256=expected or sha, execute=execute)


def test_audio_understand_is_discoverable_and_defaults_to_no_network():
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "src/ai_video_mcp/server.py").read_text())
    tools = {n.name: n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)}
    assert "audio_understand" in tools
    tool = tools["audio_understand"]
    args = [a.arg for a in tool.args.args]
    defaults = dict(zip(args[-len(tool.args.defaults):], tool.args.defaults))
    assert defaults["execute"].value is False
    assert "expected_sha256" in args and "expected_sha256" not in defaults
    assert not {"api_key", "credential", "permit", "runtime_factory"} & set(args)
    assert any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
               and d.func.attr == "tool" for d in tool.decorator_list)


def test_preview_never_imports_runtime_or_exposes_wire_audio(audio_source):
    path, sha, _ = audio_source
    config = ServerConfig(audio_media_root=str(path.parent), audio_runtime_factory="nonexistent_runtime:build")
    result = _call(audio_source, config=config)
    assert result["network_calls"] == 0
    assert result["preview"]["source_sha256"] == sha
    assert result["preview"]["audio_sha256"] == sha
    assert result["preview"]["duration_seconds"] == 0.1
    assert "inline_data" not in json.dumps(result)
    assert result["human_acceptance"] == "NOT_EVALUATED"


def test_wrong_source_hash_and_symlink_fail_closed(audio_source):
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    path, sha, config = audio_source
    with pytest.raises(AudioUnderstandingError, match="differs"):
        _call(audio_source, expected="0" * 64)
    link = path.parent / "link.wav"
    link.symlink_to(path)
    with pytest.raises(AudioUnderstandingError, match="regular file"):
        _call((link, sha, config))


def test_source_outside_operator_root_is_not_read(audio_source, tmp_path):
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    folder = tmp_path / "allowed"
    folder.mkdir()
    config = ServerConfig(audio_media_root=str(folder))
    with pytest.raises(AudioUnderstandingError, match="inside"):
        _call(audio_source, config=config)


def test_execute_without_qualified_runtime_never_posts(audio_source):
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    with pytest.raises(AudioUnderstandingError) as error:
        _call(audio_source, execute=True)
    assert error.value.code == "runtime_required"
    assert error.value.outcome == "KNOWN_NO_EFFECT"


def test_runtime_failure_is_secret_safe(audio_source, monkeypatch):
    from types import ModuleType
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    module = ModuleType("audio_test_operator")
    def build():
        raise ValueError("private-token-that-must-not-escape")
    module.build = build
    monkeypatch.setitem(sys.modules, module.__name__, module)
    config = audio_source[2].model_copy(update={"audio_runtime_factory": "audio_test_operator:build"})
    with pytest.raises(AudioUnderstandingError) as error:
        _call(audio_source, execute=True, config=config)
    assert "private-token" not in str(error.value)
    assert error.value.code == "runtime_unavailable"


def _runtime_with_transport(monkeypatch, config, handler, events=None):
    from types import ModuleType
    from ai_video_mcp.audio_understanding import GeminiAudioAnalyzer
    from ai_video_mcp.tools.audio_understand import AudioUnderstandingRuntime
    client = httpx.Client(transport=httpx.MockTransport(handler))
    class Permit:
        def __init__(self, preview):
            self.preview, self.used = preview, False
        def validate(self, preview):
            if events is not None:
                events.append("permit_validate")
            return self.preview == preview and not self.used
        def consume(self, preview):
            if events is not None:
                events.append("permit_consume")
            if not self.validate(preview):
                return False
            self.used = True
            return True
    module = ModuleType("audio_test_operator")
    def credential():
        if events is not None:
            events.append("credential")
        return "test-only-key"
    def build():
        if events is not None:
            events.append("runtime")
        return AudioUnderstandingRuntime(GeminiAudioAnalyzer(credential, transport=client), Permit)
    module.build = build
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return config.model_copy(update={"audio_runtime_factory": "audio_test_operator:build"}), client


def _response():
    return {"modelVersion": "gemini-3.8-flash-test", "candidates": [{"finishReason": "STOP",
        "content": {"parts": [{"text": json.dumps({"segments": [],
            "voice_description": "not discernible", "delivery_description": "not discernible",
            "background_sounds": [], "uncertainties": ["synthetic silent test audio"]})}]}}]}


def test_execute_uses_exact_audio_and_retains_observations_without_acceptance(audio_source, monkeypatch):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=_response())
    config, client = _runtime_with_transport(monkeypatch, audio_source[2], handler)
    try:
        result = _call(audio_source, execute=True, config=config)
    finally:
        client.close()
    assert len(calls) == 1
    assert result["source_sha256"] == audio_source[1]
    assert result["schema_version"] == "audio-understanding-evidence/1"
    assert result["observations"]["uncertainties"] == ["synthetic silent test audio"]
    assert "PASS" not in json.dumps(result)
    assert "test-only-key" not in json.dumps(result)


def test_media_mutation_after_remote_analysis_invalidates_evidence(audio_source, monkeypatch):
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    def handler(request):
        audio_source[0].write_bytes(b"changed source")
        return httpx.Response(200, json=_response())
    config, client = _runtime_with_transport(monkeypatch, audio_source[2], handler)
    try:
        with pytest.raises(AudioUnderstandingError) as error:
            _call(audio_source, execute=True, config=config)
    finally:
        client.close()
    assert error.value.code == "source_changed"


def test_full_mp4_audio_preview_is_bound_to_original_bytes(tiny_video, tmp_path):
    from ai_video_mcp.tools.audio_understand import audio_understand
    digest = hashlib.sha256(tiny_video.read_bytes()).hexdigest()
    result = audio_understand(str(tiny_video), ServerConfig(audio_media_root=str(tmp_path)),
        expected_sha256=digest)
    assert result["preview"]["source_sha256"] == digest
    assert result["preview"]["audio_sha256"] != digest
    assert result["analysis_audio_derivation"] == "full_source_track_pcm_derivative"
    assert result["network_calls"] == 0


def test_video_analyze_audio_opt_in_requires_full_audio_evidence(tiny_video, mcp_cache, tmp_path):
    from ai_video_mcp.tools.analyze import video_analyze
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    config = ServerConfig(audio_media_root=str(tmp_path))
    normal = video_analyze(str(tiny_video), config, mcp_cache,
        extract_frames=False, transcribe_audio=False, detect_scenes=False)
    assert "audio_understanding" not in normal
    with pytest.raises(AudioUnderstandingError, match="qualified"):
        video_analyze(str(tiny_video), config, mcp_cache, extract_frames=False,
            transcribe_audio=False, detect_scenes=False, understand_audio=True,
            expected_sha256=hashlib.sha256(tiny_video.read_bytes()).hexdigest())


@pytest.mark.parametrize("execute", [False, True])
def test_disguised_hls_cannot_read_external_audio(tiny_video, tmp_path, monkeypatch, execute):
    from ai_video_mcp.audio_understanding import AudioUnderstandingError
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    private_segment = tmp_path / "private.ts"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(tiny_video),
        "-itsoffset", "0.2", "-i", str(tiny_video), "-map", "0:v:0", "-map", "1:a:0",
        "-c", "copy", "-f", "mpegts", str(private_segment)], check=True, capture_output=True)
    manifest = allowed / "source.mp4"
    manifest.write_text("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:3\n"
        "#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:3.0,\n" + str(private_segment) + "\n#EXT-X-ENDLIST\n")
    config = ServerConfig(audio_media_root=str(allowed))
    events = []
    config, client = _runtime_with_transport(monkeypatch, config,
        lambda request: (events.append("POST"), httpx.Response(200, json=_response()))[1], events=events)
    try:
        with pytest.raises(AudioUnderstandingError, match="decoded"):
            _call((manifest, hashlib.sha256(manifest.read_bytes()).hexdigest(), config), execute=execute)
    finally:
        client.close()
    assert events == []


@pytest.mark.parametrize("invalid", [{"max_frames": 0}, {"frame_interval": 0}])
def test_invalid_local_analysis_options_never_consume_audio(tiny_video, tmp_path, mcp_cache, monkeypatch, invalid):
    import importlib
    from ai_video_mcp.tools.analyze import video_analyze
    from ai_video_mcp.errors import McpError
    module = importlib.import_module("ai_video_mcp.tools.audio_understand")
    calls = []
    monkeypatch.setattr(module, "audio_understand", lambda *args, **kwargs: calls.append(kwargs) or {})
    with pytest.raises(McpError):
        video_analyze(str(tiny_video), ServerConfig(audio_media_root=str(tmp_path)), mcp_cache,
            transcribe_audio=False, detect_scenes=False, understand_audio=True,
            expected_sha256=hashlib.sha256(tiny_video.read_bytes()).hexdigest(), **invalid)
    assert calls == []
