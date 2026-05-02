from __future__ import annotations

import pytest

from ai_video_mcp.errors import McpErrorCode
from ai_video_mcp.tools.transcribe import video_transcribe

from conftest import skip_no_ffmpeg

skip_no_whisper = pytest.mark.skipif(
    True,
    reason="Whisper tests are slow, enable manually",
)


@skip_no_ffmpeg
class TestVideoTranscribe:
    def test_transcribe_no_audio(self, no_audio_video, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_transcribe(str(no_audio_video), mcp_config, mcp_cache)
        assert exc_info.value.code == McpErrorCode.NO_AUDIO_STREAM

    def test_transcribe_invalid_model(self, tiny_video, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_transcribe(str(tiny_video), mcp_config, mcp_cache, model="nonexistent")
        assert exc_info.value.code == McpErrorCode.INVALID_PARAMETER

    @skip_no_whisper
    def test_transcribe_with_audio(self, tiny_video, mcp_config, mcp_cache):
        result = video_transcribe(str(tiny_video), mcp_config, mcp_cache, model="tiny")
        assert "segments" in result
        assert "full_text" in result
        assert result["model"] == "tiny"
