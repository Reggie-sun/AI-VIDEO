from __future__ import annotations

import pytest

from ai_video_mcp.tools.analyze import video_analyze

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestVideoAnalyze:
    def test_analyze_full(self, tiny_video, mcp_config, mcp_cache):
        result = video_analyze(
            str(tiny_video), mcp_config, mcp_cache,
            extract_frames=True,
            transcribe_audio=False,
            detect_scenes=True,
        )
        assert "probe" in result
        assert "frames" in result
        assert "scenes" in result
        assert result["transcription"] is None
        assert "analysis_summary" in result
        assert result["analysis_summary"]["resolution"] == "320x240"

    def test_analyze_no_frames(self, tiny_video, mcp_config, mcp_cache):
        result = video_analyze(
            str(tiny_video), mcp_config, mcp_cache,
            extract_frames=False,
            transcribe_audio=False,
            detect_scenes=False,
        )
        assert result["frames"] is None
        assert result["scenes"] is None

    def test_analyze_summary_fields(self, tiny_video, mcp_config, mcp_cache):
        result = video_analyze(
            str(tiny_video), mcp_config, mcp_cache,
            extract_frames=True,
            transcribe_audio=False,
            detect_scenes=True,
        )
        s = result["analysis_summary"]
        assert "duration_hms" in s
        assert "resolution" in s
        assert "has_audio" in s
        assert "scene_count" in s
        assert "frames_extracted" in s
