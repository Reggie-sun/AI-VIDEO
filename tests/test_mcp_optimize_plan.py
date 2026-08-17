from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ai_video_mcp.tools.optimize_plan import video_optimize_plan

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestVideoOptimizePlan:
    def test_production_plan_consumes_receipt_without_reanalysis(
        self, tiny_video, mcp_config, mcp_cache, monkeypatch
    ):
        def fail_review(*args, **kwargs):
            raise AssertionError("Production planning must not analyze video")

        monkeypatch.setattr(
            "ai_video_mcp.tools.optimize_plan.video_review", fail_review
        )
        pointer_data = {
            "review_id": "review-1",
            "layer": "layout",
            "path": "state/reviews/review." + "0" * 64 + ".json",
            "content_hash": "0" * 64,
            "file_sha256": "1" * 64,
        }
        from ai_video.production.models import ReviewReceiptPointer
        pointer = ReviewReceiptPointer.model_validate(pointer_data)
        monkeypatch.setattr(
            "ai_video_mcp.tools.optimize_plan.load_production_project",
            lambda path: SimpleNamespace(
                root=Path("/verified/project"),
                manifest=SimpleNamespace(active_review_receipts=(pointer,)),
            ),
        )
        monkeypatch.setattr(
            "ai_video_mcp.tools.optimize_plan.load_review_receipt",
            lambda root, selected: SimpleNamespace(issue_ids=("caption-overflow",)),
        )
        result = video_optimize_plan(
            str(tiny_video),
            mcp_config,
            mcp_cache,
            production_review_receipt=pointer_data,
            production_project_path="/verified/project/project.yaml",
        )
        assert result["mode"] == "production_repair_proposal"
        assert result["targets"] == []
        assert result["review_receipt_id"] == "review-1"
    def test_optimize_plan_maps_review_issues_to_repo_files(
        self,
        tiny_video,
        mcp_config,
        mcp_cache,
        example_project_files,
    ):
        project_path, shots_path = example_project_files

        result = video_optimize_plan(
            str(tiny_video),
            mcp_config,
            mcp_cache,
            project_path=str(project_path),
            shots_path=str(shots_path),
        )

        assert result["video_path"] == str(tiny_video.resolve())
        assert result["issue_ids"]
        assert "low_resolution" in result["issue_ids"]
        assert "low_fps" in result["issue_ids"]
        assert result["targets"]

        target_paths = {target["file_path"] for target in result["targets"]}
        assert str(project_path.resolve()) in target_paths
        assert any(path.endswith("template.json") for path in target_paths)
        assert any(path.endswith("ffmpeg_tools.py") for path in target_paths)

        project_targets = [target for target in result["targets"] if target["file_path"] == str(project_path.resolve())]
        assert any("defaults.width" in change for target in project_targets for change in target["proposed_changes"])
        assert any("defaults.fps" in change for target in project_targets for change in target["proposed_changes"])

    def test_optimize_plan_routes_static_visuals_to_shot_and_binding_files(
        self,
        static_video,
        mcp_config,
        mcp_cache,
        example_project_files,
    ):
        project_path, shots_path = example_project_files

        result = video_optimize_plan(
            str(static_video),
            mcp_config,
            mcp_cache,
            project_path=str(project_path),
            shots_path=str(shots_path),
        )

        assert "static_visuals" in result["issue_ids"]

        target_paths = {target["file_path"] for target in result["targets"]}
        assert str(shots_path.resolve()) in target_paths
        assert any(path.endswith("binding.yaml") for path in target_paths)

        shot_target = next(target for target in result["targets"] if target["file_path"] == str(shots_path.resolve()))
        assert any("prompt" in change for change in shot_target["proposed_changes"])
