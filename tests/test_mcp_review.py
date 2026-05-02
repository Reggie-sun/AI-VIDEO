from __future__ import annotations

from ai_video_mcp.tools.review import video_review

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestVideoReview:
    def test_review_returns_metrics_and_actionable_issues(self, tiny_video, mcp_config, mcp_cache):
        result = video_review(str(tiny_video), mcp_config, mcp_cache)

        assert result["video_path"] == str(tiny_video.resolve())
        assert "analysis_summary" in result
        assert "quality_metrics" in result
        assert "issues" in result
        assert result["issues"]

        issue_ids = {issue["id"] for issue in result["issues"]}
        assert "low_resolution" in issue_ids
        assert "low_fps" in issue_ids

        first_issue = result["issues"][0]
        assert "suggested_actions" in first_issue
        assert first_issue["suggested_actions"]
        assert "file_hints" in first_issue["suggested_actions"][0]

    def test_review_flags_static_visuals(self, static_video, mcp_config, mcp_cache):
        result = video_review(str(static_video), mcp_config, mcp_cache)

        issue_ids = {issue["id"] for issue in result["issues"]}
        assert "static_visuals" in issue_ids

        metrics = result["quality_metrics"]
        assert metrics["sampled_frame_count"] >= 2
        assert metrics["unique_frame_ratio"] <= 0.5
