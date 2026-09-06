from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from ai_video_mcp.errors import McpError, McpErrorCode
from ai_video_mcp.tools.transcribe import video_transcribe
import ai_video_mcp.tools.transcribe as transcribe_module

from conftest import skip_no_ffmpeg

skip_no_whisper = pytest.mark.skipif(
    True,
    reason="Whisper tests are slow, enable manually",
)


@skip_no_ffmpeg
class TestVideoTranscribe:
    def test_transcribe_no_audio(self, no_audio_video, mcp_config, mcp_cache, monkeypatch):
        monkeypatch.setitem(sys.modules, "whisper", None)
        with pytest.raises(McpError) as exc_info:
            video_transcribe(str(no_audio_video), mcp_config, mcp_cache)
        assert exc_info.value.code == McpErrorCode.NO_AUDIO_STREAM

    def test_transcribe_invalid_model(self, tiny_video, mcp_config, mcp_cache, monkeypatch):
        monkeypatch.setitem(
            sys.modules, "whisper", SimpleNamespace(available_models=lambda: ["tiny"])
        )
        with pytest.raises(McpError) as exc_info:
            video_transcribe(str(tiny_video), mcp_config, mcp_cache, model="nonexistent")
        assert exc_info.value.code == McpErrorCode.INVALID_PARAMETER

    def test_transcribe_no_audio_precedes_model_validation(self, no_audio_video, mcp_config, mcp_cache, monkeypatch):
        def available_models():
            pytest.fail("No-audio validation must not consult the model backend")

        monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace(available_models=available_models))
        with pytest.raises(McpError) as exc_info:
            video_transcribe(str(no_audio_video), mcp_config, mcp_cache, model="nonexistent")
        assert exc_info.value.code == McpErrorCode.NO_AUDIO_STREAM

    def test_transcribe_missing_whisper(self, tiny_video, mcp_config, mcp_cache, monkeypatch):
        monkeypatch.setitem(sys.modules, "whisper", None)
        with pytest.raises(McpError) as exc_info:
            video_transcribe(str(tiny_video), mcp_config, mcp_cache)
        assert exc_info.value.code == McpErrorCode.WHISPER_FAILED
        assert isinstance(exc_info.value.__cause__, ImportError)

    def test_transcribe_uses_backend_model_catalog(self, tiny_video, mcp_config, mcp_cache, monkeypatch):
        loaded_models = []

        def load_model(name):
            loaded_models.append(name)
            return SimpleNamespace(transcribe=lambda *args, **kwargs: {
                "language": "en",
                "segments": [{"id": 0, "start": 0, "end": 1, "text": " hello "}],
            })

        monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace(
            available_models=lambda: ["backend-test-model"], load_model=load_model,
        ))
        monkeypatch.setattr(transcribe_module, "_model_cache", {})
        result = video_transcribe(
            str(tiny_video), mcp_config, mcp_cache, model="backend-test-model",
        )
        assert loaded_models == ["backend-test-model"]
        assert result["model"] == "backend-test-model"
        assert result["full_text"] == "hello"

    @skip_no_whisper
    def test_transcribe_with_audio(self, tiny_video, mcp_config, mcp_cache):
        result = video_transcribe(str(tiny_video), mcp_config, mcp_cache, model="tiny")
        assert "segments" in result
        assert "full_text" in result
        assert result["model"] == "tiny"
