from __future__ import annotations

import hashlib

import pytest

from ai_video_mcp.errors import McpError
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

    def test_production_static_image_reports_measurement_without_static_failure(
        self, static_video, mcp_config, mcp_cache
    ):
        output_hash = hashlib.sha256(static_video.read_bytes()).hexdigest()
        result = video_review(
            str(static_video),
            mcp_config,
            mcp_cache,
            production_context={
                "render_output_sha256": output_hash,
                "timeline_fingerprint": "1" * 64,
                "measurement_contract_version": "1",
                "windows": [
                    {
                        "shot_id": "shot-1",
                        "visual_strategy": "static_image",
                        "start_frame": 0,
                        "end_frame_exclusive": 24,
                        "expects_audio": False,
                        "visual_span_ids": ["visual-1"],
                        "motion_expectation": None,
                    }
                ],
            },
        )
        assert result["mode"] == "production_evidence"
        assert result["issues"] == []
        assert result["measurements"]["unique_frame_ratio"] <= 0.5

    def test_production_context_rejects_output_hash_mismatch(
        self, tiny_video, mcp_config, mcp_cache
    ):
        with pytest.raises(McpError, match="hash"):
            video_review(
                str(tiny_video),
                mcp_config,
                mcp_cache,
                production_context={
                    "render_output_sha256": "0" * 64,
                    "timeline_fingerprint": "1" * 64,
                    "measurement_contract_version": "1",
                    "windows": [],
                },
            )

    def test_unsupported_p3_motion_strategy_is_not_evaluated(
        self, static_video, mcp_config, mcp_cache
    ):
        output_hash = hashlib.sha256(static_video.read_bytes()).hexdigest()
        result = video_review(
            str(static_video),
            mcp_config,
            mcp_cache,
            production_context={
                "render_output_sha256": output_hash,
                "timeline_fingerprint": "1" * 64,
                "measurement_contract_version": "1",
                "windows": [{
                    "shot_id": "shot-1",
                    "visual_strategy": "image_motion",
                    "start_frame": 0,
                    "end_frame_exclusive": 24,
                    "expects_audio": False,
                    "visual_span_ids": ["visual-1"],
                    "motion_expectation": {
                        "directive_kind": "pan",
                        "directive_parameters_fingerprint": "2" * 64,
                        "measurement_kind": "transform_delta",
                        "minimum_measured_delta_milli": 5,
                        "tolerance_milli": 1,
                    },
                }],
            },
        )
        assert result["windows"][0]["status"] == "not_evaluated"
