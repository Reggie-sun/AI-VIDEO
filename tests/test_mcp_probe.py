from __future__ import annotations

import pytest

from ai_video_mcp.errors import McpErrorCode
from ai_video_mcp.tools.probe import video_probe

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestVideoProbe:
    def test_probe_valid_video(self, tiny_video, mcp_config, mcp_cache):
        result = video_probe(str(tiny_video), mcp_config, mcp_cache)
        assert "file" in result
        assert "video_stream" in result
        assert result["file"]["duration_seconds"] > 0
        assert result["video_stream"]["width"] == 320
        assert result["video_stream"]["height"] == 240
        assert result["video_stream"]["codec"] == "h264"
        assert result["audio_stream"] is not None
        assert result["audio_stream"]["codec"] == "aac"

    def test_probe_caches_result(self, tiny_video, mcp_config, mcp_cache):
        r1 = video_probe(str(tiny_video), mcp_config, mcp_cache)
        r2 = video_probe(str(tiny_video), mcp_config, mcp_cache)
        assert r1 is r2

    def test_probe_missing_file(self, tmp_path, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_probe(str(tmp_path / "nonexistent.mp4"), mcp_config, mcp_cache)
        assert exc_info.value.code == McpErrorCode.FILE_NOT_FOUND

    def test_probe_no_audio(self, no_audio_video, mcp_config, mcp_cache):
        result = video_probe(str(no_audio_video), mcp_config, mcp_cache)
        assert result["audio_stream"] is None

    def test_probe_duration_format(self, tiny_video, mcp_config, mcp_cache):
        result = video_probe(str(tiny_video), mcp_config, mcp_cache)
        hms = result["file"]["duration_hms"]
        assert ":" in hms
