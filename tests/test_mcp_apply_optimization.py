from __future__ import annotations

from pathlib import Path

import yaml

from ai_video_mcp.tools.apply_optimization import apply_video_optimization

from conftest import skip_no_ffmpeg


@skip_no_ffmpeg
class TestApplyVideoOptimization:
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
