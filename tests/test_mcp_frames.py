from __future__ import annotations

import base64

import pytest

from ai_video_mcp.errors import McpErrorCode
from ai_video_mcp.tools.frames import video_extract_frames
from ai_video_mcp.tools.probe import video_probe

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestVideoExtractFrames:
    def test_extract_frames_default(self, tiny_video, mcp_config, mcp_cache):
        result = video_extract_frames(str(tiny_video), mcp_config, mcp_cache)
        assert result["total_frames_extracted"] > 0
        assert len(result["frames"]) > 0
        frame = result["frames"][0]
        assert "base64" in frame
        assert "timestamp_seconds" in frame
        decoded = base64.b64decode(frame["base64"])
        assert len(decoded) > 0

    def test_extract_frames_custom_interval(self, tiny_video, mcp_config, mcp_cache):
        result = video_extract_frames(str(tiny_video), mcp_config, mcp_cache, interval_seconds=1.0)
        probe = video_probe(str(tiny_video), mcp_config, mcp_cache)
        fps = float(probe["video_stream"]["fps"] or 0.0)
        margin = 1.0 / fps if fps > 0 else 0.1
        assert all(
            frame["timestamp_seconds"] < probe["file"]["duration_seconds"] - margin
            for frame in result["frames"]
        )
        assert result["total_frames_extracted"] >= 3

    def test_extract_frames_max_frames_cap(self, tiny_video, mcp_config, mcp_cache):
        result = video_extract_frames(str(tiny_video), mcp_config, mcp_cache, max_frames=2, interval_seconds=0.5)
        assert result["total_frames_extracted"] <= 2

    def test_extract_frames_invalid_interval(self, tiny_video, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_extract_frames(str(tiny_video), mcp_config, mcp_cache, interval_seconds=-1)
        assert exc_info.value.code == McpErrorCode.INVALID_PARAMETER

    def test_extract_frames_missing_file(self, tmp_path, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_extract_frames(str(tmp_path / "no.mp4"), mcp_config, mcp_cache)
        assert exc_info.value.code == McpErrorCode.FILE_NOT_FOUND
