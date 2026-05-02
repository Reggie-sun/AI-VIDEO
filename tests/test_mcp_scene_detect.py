from __future__ import annotations

import pytest

from ai_video_mcp.errors import McpErrorCode
from ai_video_mcp.tools.scene_detect import video_scene_detect

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestVideoSceneDetect:
    def test_detect_single_scene(self, tiny_video, mcp_config, mcp_cache):
        result = video_scene_detect(str(tiny_video), mcp_config, mcp_cache)
        assert result["total_scenes"] >= 1
        assert result["scenes"][0]["start_time"] == 0.0

    def test_detect_invalid_threshold(self, tiny_video, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_scene_detect(str(tiny_video), mcp_config, mcp_cache, threshold=0)
        assert exc_info.value.code == McpErrorCode.INVALID_PARAMETER

    def test_detect_threshold_too_high(self, tiny_video, mcp_config, mcp_cache):
        with pytest.raises(Exception) as exc_info:
            video_scene_detect(str(tiny_video), mcp_config, mcp_cache, threshold=1.5)
        assert exc_info.value.code == McpErrorCode.INVALID_PARAMETER

    def test_detect_caches_result(self, tiny_video, mcp_config, mcp_cache):
        r1 = video_scene_detect(str(tiny_video), mcp_config, mcp_cache)
        r2 = video_scene_detect(str(tiny_video), mcp_config, mcp_cache)
        assert r1 is r2
