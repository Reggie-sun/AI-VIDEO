from __future__ import annotations

from pathlib import Path

from ai_video.config import load_project
from ai_video.manifest import load_manifest
from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.tools.review import video_review


def _append_change(targets: list[dict], file_path: Path, issue_id: str, priority: int, reason: str, changes: list[str]) -> None:
    resolved_path = str(file_path.resolve())
    for target in targets:
        if target["file_path"] == resolved_path:
            target["issue_ids"].append(issue_id)
            target["priority"] = min(target["priority"], priority)
            target["reasons"].append(reason)
            target["proposed_changes"].extend(changes)
            return

    targets.append(
        {
            "file_path": resolved_path,
            "issue_ids": [issue_id],
            "priority": priority,
            "reasons": [reason],
            "proposed_changes": list(changes),
        }
    )


def _dedupe_targets(targets: list[dict]) -> list[dict]:
    for target in targets:
        target["issue_ids"] = sorted(set(target["issue_ids"]))
        target["reasons"] = list(dict.fromkeys(target["reasons"]))
        target["proposed_changes"] = list(dict.fromkeys(target["proposed_changes"]))
    return sorted(targets, key=lambda item: (item["priority"], item["file_path"]))


def _resolve_inputs(
    *,
    project_path: str | None,
    shots_path: str | None,
    manifest_path: str | None,
) -> tuple[Path | None, Path | None]:
    if manifest_path:
        manifest = load_manifest(manifest_path)
        resolved_project = Path(manifest.project_config_path).resolve() if manifest.project_config_path else None
        resolved_shots = Path(manifest.shot_list_path).resolve() if manifest.shot_list_path else None
        return resolved_project, resolved_shots

    resolved_project = Path(project_path).resolve() if project_path else None
    resolved_shots = Path(shots_path).resolve() if shots_path else None
    return resolved_project, resolved_shots


def video_optimize_plan(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    project_path: str | None = None,
    shots_path: str | None = None,
    manifest_path: str | None = None,
) -> dict:
    review = video_review(video_path, config, cache)
    resolved_project, resolved_shots = _resolve_inputs(
        project_path=project_path,
        shots_path=shots_path,
        manifest_path=manifest_path,
    )

    workflow_template_path: Path | None = None
    workflow_binding_path: Path | None = None
    if resolved_project:
        project = load_project(resolved_project)
        workflow_template_path = project.workflow.template
        workflow_binding_path = project.workflow.binding

    ffmpeg_tools_path = Path("src/ai_video/ffmpeg_tools.py").resolve()
    pipeline_path = Path("src/ai_video/pipeline.py").resolve()

    targets: list[dict] = []
    for issue in review["issues"]:
        issue_id = issue["id"]
        if issue_id == "low_resolution":
            if resolved_project:
                _append_change(
                    targets,
                    resolved_project,
                    issue_id,
                    1,
                    issue["summary"],
                    [
                        "Raise defaults.width to at least 1024.",
                        "Raise defaults.height to at least 576.",
                    ],
                )
            if workflow_template_path:
                _append_change(
                    targets,
                    workflow_template_path,
                    issue_id,
                    2,
                    issue["summary"],
                    [
                        "Inspect nodes that hard-code output width/height and align them with project defaults.",
                    ],
                )
            _append_change(
                targets,
                ffmpeg_tools_path,
                issue_id,
                3,
                issue["summary"],
                [
                    "Confirm normalize_clip does not downscale below the intended workflow output size.",
                ],
            )

        if issue_id == "low_fps":
            if resolved_project:
                _append_change(
                    targets,
                    resolved_project,
                    issue_id,
                    1,
                    issue["summary"],
                    [
                        "Raise defaults.fps to at least 20, preferably 24.",
                    ],
                )
            _append_change(
                targets,
                ffmpeg_tools_path,
                issue_id,
                2,
                issue["summary"],
                [
                    "Confirm normalize_clip preserves the requested fps during scaling.",
                ],
            )
            _append_change(
                targets,
                pipeline_path,
                issue_id,
                3,
                issue["summary"],
                [
                    "Verify per-shot fps flows through rendering and normalization without fallback to a lower value.",
                ],
            )

        if issue_id == "static_visuals":
            if resolved_shots:
                _append_change(
                    targets,
                    resolved_shots,
                    issue_id,
                    1,
                    issue["summary"],
                    [
                        "Strengthen each shot prompt with explicit motion verbs and camera movement cues.",
                        "Reduce repeated near-identical prompts across adjacent shots.",
                    ],
                )
            if workflow_binding_path:
                _append_change(
                    targets,
                    workflow_binding_path,
                    issue_id,
                    2,
                    issue["summary"],
                    [
                        "Confirm prompt and init-image bindings are not over-constraining motion between shots.",
                    ],
                )
            if workflow_template_path:
                _append_change(
                    targets,
                    workflow_template_path,
                    issue_id,
                    3,
                    issue["summary"],
                    [
                        "Inspect workflow nodes controlling motion strength, conditioning carry-over, or image-to-video guidance.",
                    ],
                )

    targets = _dedupe_targets(targets)
    next_actions = [
        "Apply the highest-priority target edits first.",
        "Run ai-video validate on the chosen project and shot files before rendering again.",
        "Render a short comparison run and review the new final.mp4 with video_review.",
    ]

    return {
        "video_path": review["video_path"],
        "issue_ids": [issue["id"] for issue in review["issues"]],
        "review_summary": review["analysis_summary"],
        "targets": targets,
        "next_actions": next_actions,
    }
