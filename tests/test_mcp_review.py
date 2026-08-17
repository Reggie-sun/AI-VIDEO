from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video_mcp.errors import McpError
from ai_video_mcp.tools.review import video_review
from ai_video.production.models import (
    ReviewRequestPointer,
    StateCommitStatus,
    TechnicalReviewContext,
)

from conftest import skip_no_ffmpeg


def production_request(monkeypatch, context):
    pointer = ReviewRequestPointer(
        path=Path("state/reviews/request." + "2" * 64 + ".json"),
        request_id="request-1",
        content_hash="2" * 64,
        file_sha256="3" * 64,
    )
    attempt = SimpleNamespace(
        operation="review",
        status=StateCommitStatus.RUNNING,
        review_request=pointer,
    )
    monkeypatch.setattr(
        "ai_video_mcp.tools.review.load_production_project",
        lambda path: SimpleNamespace(
            root=Path("/verified/project"),
            manifest=SimpleNamespace(attempts=(attempt,)),
        ),
    )
    monkeypatch.setattr(
        "ai_video_mcp.tools.review.load_review_request",
        lambda root, selected: SimpleNamespace(
            technical_context=TechnicalReviewContext.model_validate(context)
        ),
    )
    return {
        "production_project_path": "/verified/project/project.yaml",
        "production_review_request": pointer.model_dump(mode="json"),
    }


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
        self, static_video, mcp_config, mcp_cache, monkeypatch
    ):
        output_hash = hashlib.sha256(static_video.read_bytes()).hexdigest()
        context = {
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
        }
        result = video_review(
            str(static_video),
            mcp_config,
            mcp_cache,
            production_context=context,
            **production_request(monkeypatch, context),
        )
        assert result["mode"] == "production_evidence"
        assert result["issues"] == []
        assert result["measurements"]["unique_frame_ratio"] <= 0.5

    def test_production_context_rejects_output_hash_mismatch(
        self, tiny_video, mcp_config, mcp_cache, monkeypatch
    ):
        with pytest.raises(McpError, match="hash"):
            context = {
                "render_output_sha256": "0" * 64,
                "timeline_fingerprint": "1" * 64,
                "measurement_contract_version": "1",
                "windows": [],
            }
            video_review(
                str(tiny_video),
                mcp_config,
                mcp_cache,
                production_context=context,
                **production_request(monkeypatch, context),
            )

    def test_unsupported_p3_motion_strategy_is_not_evaluated(
        self, static_video, mcp_config, mcp_cache, monkeypatch
    ):
        output_hash = hashlib.sha256(static_video.read_bytes()).hexdigest()
        context = {
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
        }
        result = video_review(
            str(static_video),
            mcp_config,
            mcp_cache,
            production_context=context,
            **production_request(monkeypatch, context),
        )
        assert result["windows"][0]["status"] == "not_evaluated"
