from __future__ import annotations

from pathlib import Path
import shutil

import yaml

from ai_video_mcp.tools.apply_optimization import apply_video_optimization

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestApplyVideoOptimization:
    def test_production_output_path_is_refused_without_caller_mode_flag(
        self, tiny_video, tmp_path, mcp_config, mcp_cache, monkeypatch
    ):
        root = tmp_path / "production"
        output = root / "state/render/outputs" / tiny_video.name
        output.parent.mkdir(parents=True)
        (root / "state/manifest.json").write_text("{}", encoding="utf-8")
        shutil.copyfile(tiny_video, output)
        monkeypatch.setattr(
            "ai_video_mcp.tools.apply_optimization.video_optimize_plan",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("Legacy planner must not run")
            ),
        )
        result = apply_video_optimization(str(output), mcp_config, mcp_cache)
        assert result["mode"] == "production_repair_refused"
        assert result["submit_count"] == 0
    def test_production_apply_fails_closed_before_planning_or_writes(
        self, tiny_video, mcp_config, mcp_cache, monkeypatch
    ):
        def fail(*args, **kwargs):
            raise AssertionError("Production apply must not call Legacy helpers")

        monkeypatch.setattr(
            "ai_video_mcp.tools.apply_optimization.video_optimize_plan", fail
        )
        monkeypatch.setattr(
            "ai_video_mcp.tools.apply_optimization.load_production_project",
            lambda path: object(),
        )
        result = apply_video_optimization(
            str(tiny_video),
            mcp_config,
            mcp_cache,
            production_project_path="/verified/project/project.yaml",
        )
        assert result == {
            "mode": "production_repair_refused",
            "applied": False,
            "reason": "durable_approved_repair_receipt_required",
            "submit_count": 0,
        }
    def test_apply_updates_project_and_shots_for_detected_issues(
        self,
        static_video,
        mcp_config,
        mcp_cache,
        example_project_files,
    ):
        project_path, shots_path = example_project_files

        result = apply_video_optimization(
            str(static_video),
            mcp_config,
            mcp_cache,
            project_path=str(project_path),
            shots_path=str(shots_path),
        )

        assert result["updated_files"]
        updated_paths = set(result["updated_files"])
        assert str(project_path.resolve()) in updated_paths
        assert str(shots_path.resolve()) in updated_paths
        assert result["validation"]["ok"] is True

        project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
        assert project_data["defaults"]["width"] >= 1024
        assert project_data["defaults"]["height"] >= 576
        assert project_data["defaults"]["fps"] >= 20

        shots_data = yaml.safe_load(shots_path.read_text(encoding="utf-8"))
        prompt_text = shots_data["shots"][0]["prompt"]
        assert "camera" in prompt_text.lower()
        assert "motion" in prompt_text.lower() or "move" in prompt_text.lower()

    def test_apply_reports_pending_code_followups(
        self,
        tiny_video,
        mcp_config,
        mcp_cache,
        example_project_files,
    ):
        project_path, shots_path = example_project_files

        result = apply_video_optimization(
            str(tiny_video),
            mcp_config,
            mcp_cache,
            project_path=str(project_path),
            shots_path=str(shots_path),
        )

        followup_files = {item["file_path"] for item in result["pending_followups"]}
        assert any(path.endswith("ffmpeg_tools.py") for path in followup_files)
