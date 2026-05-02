from __future__ import annotations

from pathlib import Path

import yaml

from ai_video.config import load_project, load_shots, load_yaml
from ai_video.manifest import load_manifest
from ai_video.models import WorkflowBinding
from ai_video.workflow_loader import load_workflow_template
from ai_video.workflow_renderer import validate_api_workflow
from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.tools.optimize_plan import video_optimize_plan


def _resolve_paths(
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
    return (
        Path(project_path).resolve() if project_path else None,
        Path(shots_path).resolve() if shots_path else None,
    )


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _ensure_prompt_motion(prompt: str) -> str:
    updated = prompt.replace("static camera", "slow cinematic camera drift")
    lower = updated.lower()
    if "camera" not in lower:
        updated = f"{updated}, slow cinematic camera drift"
    if "motion" not in lower and "move" not in lower:
        updated = f"{updated}, natural body motion"
    return updated


def _apply_project_defaults(project_path: Path) -> list[str]:
    data = load_yaml(project_path)
    defaults = data.setdefault("defaults", {})
    changes: list[str] = []

    width = int(defaults.get("width", 0) or 0)
    height = int(defaults.get("height", 0) or 0)
    fps = int(defaults.get("fps", 0) or 0)

    if width < 1024:
        defaults["width"] = 1024
        changes.append("Raised defaults.width to 1024.")
    if height < 576:
        defaults["height"] = 576
        changes.append("Raised defaults.height to 576.")
    if fps < 24:
        defaults["fps"] = 24
        changes.append("Raised defaults.fps to 24.")

    if changes:
        _write_yaml(project_path, data)
    return changes


def _apply_shot_prompts(shots_path: Path) -> list[str]:
    data = load_yaml(shots_path)
    shots = data.get("shots", [])
    changes: list[str] = []
    for shot in shots:
        prompt = shot.get("prompt")
        if not isinstance(prompt, str):
            continue
        new_prompt = _ensure_prompt_motion(prompt)
        if new_prompt != prompt:
            shot["prompt"] = new_prompt
            changes.append(f"Updated prompt motion cues for shot {shot.get('id', '<unknown>')}.")
    if changes:
        _write_yaml(shots_path, data)
    return changes


def _validate_project_inputs(project_path: Path, shots_path: Path) -> dict:
    project = load_project(project_path)
    shots = load_shots(shots_path, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)
    validate_api_workflow(template)
    return {
        "ok": True,
        "project_name": project.project_name,
        "shot_count": len(shots),
        "binding_path": str(project.workflow.binding),
        "template_path": str(project.workflow.template),
    }


def apply_video_optimization(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    project_path: str | None = None,
    shots_path: str | None = None,
    manifest_path: str | None = None,
) -> dict:
    plan = video_optimize_plan(
        video_path,
        config,
        cache,
        project_path=project_path,
        shots_path=shots_path,
        manifest_path=manifest_path,
    )
    resolved_project, resolved_shots = _resolve_paths(
        project_path=project_path,
        shots_path=shots_path,
        manifest_path=manifest_path,
    )

    updated_files: list[str] = []
    applied_changes: list[dict] = []

    if resolved_project:
        project_changes = _apply_project_defaults(resolved_project)
        if project_changes:
            updated_files.append(str(resolved_project))
            applied_changes.append({"file_path": str(resolved_project), "changes": project_changes})

    if resolved_shots and "static_visuals" in plan["issue_ids"]:
        shot_changes = _apply_shot_prompts(resolved_shots)
        if shot_changes:
            updated_files.append(str(resolved_shots))
            applied_changes.append({"file_path": str(resolved_shots), "changes": shot_changes})

    pending_followups = [
        target for target in plan["targets"] if target["file_path"] not in set(updated_files)
    ]

    validation = {"ok": False}
    if resolved_project and resolved_shots:
        validation = _validate_project_inputs(resolved_project, resolved_shots)

    return {
        "video_path": plan["video_path"],
        "issue_ids": plan["issue_ids"],
        "updated_files": updated_files,
        "applied_changes": applied_changes,
        "pending_followups": pending_followups,
        "validation": validation,
    }
