from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from urllib.parse import urlparse

import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode, config_error
from ai_video.models import ProjectConfig, ShotList, ShotSpec


def load_yaml(path: str | Path) -> dict:
    yaml_path = Path(path)
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise config_error(
            ErrorCode.CONFIG_INVALID,
            f"Could not read config file: {yaml_path}",
            str(exc),
        ) from exc
    if not isinstance(data, dict):
        raise config_error(ErrorCode.CONFIG_INVALID, f"YAML file must contain a mapping: {yaml_path}")
    return data


def is_local_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    return host in {"localhost", "127.0.0.1", "::1"}


def _resolve_path(base_dir: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


def resolve_project_paths(project: ProjectConfig, base_dir: Path) -> ProjectConfig:
    data = project.model_dump()
    data["workflow"]["template"] = _resolve_path(base_dir, project.workflow.template)
    data["workflow"]["binding"] = _resolve_path(base_dir, project.workflow.binding)
    data["output"]["root"] = _resolve_path(base_dir, project.output.root)
    characters = []
    for character in project.characters:
        character_data = character.model_dump()
        character_data["reference_images"] = [
            _resolve_path(base_dir, image) for image in character.reference_images
        ]
        if character.future_lora.path is not None:
            character_data["future_lora"]["path"] = _resolve_path(base_dir, character.future_lora.path)
        characters.append(character_data)
    data["characters"] = characters
    return ProjectConfig.model_validate(data)


def _validation_error(message: str, exc: ValidationError) -> AiVideoError:
    return config_error(ErrorCode.CONFIG_INVALID, message, str(exc))


def load_project(path: str | Path) -> ProjectConfig:
    project_path = Path(path)
    data = load_yaml(project_path)
    try:
        project = ProjectConfig.model_validate(data)
    except ValidationError as exc:
        raise _validation_error("Project config validation failed", exc) from exc

    if not is_local_url(project.comfy.base_url) and not project.comfy.allow_non_local:
        raise config_error(
            ErrorCode.CONFIG_INVALID,
            "ComfyUI base_url is non-local; set comfy.allow_non_local: true to allow this.",
            project.comfy.base_url,
        )
    return resolve_project_paths(project, project_path.parent)


def _resolve_shot_paths(shots: list[ShotSpec], base_dir: Path) -> list[ShotSpec]:
    resolved = []
    for shot in shots:
        data = shot.model_dump()
        if shot.init_image is not None:
            data["init_image"] = _resolve_path(base_dir, shot.init_image)
        resolved.append(ShotSpec.model_validate(data))
    return resolved


def load_shots(path: str | Path, project: ProjectConfig) -> list[ShotSpec]:
    shots_path = Path(path)
    data = load_yaml(shots_path)
    try:
        shot_list = ShotList.model_validate(data)
    except ValidationError as exc:
        raise _validation_error("Shot list validation failed", exc) from exc

    known_characters = {character.id for character in project.characters}
    for shot in shot_list.shots:
        unknown = sorted(set(shot.characters) - known_characters)
        if unknown:
            raise config_error(
                ErrorCode.CONFIG_INVALID,
                f"Shot {shot.id} references unknown character(s): {', '.join(unknown)}",
            )
    return _resolve_shot_paths(shot_list.shots, shots_path.parent)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_min_free_space(path: str | Path, min_free_gb: float) -> None:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(target).free
    required = min_free_gb * 1024**3
    if free_bytes < required:
        raise AiVideoError(
            code=ErrorCode.DISK_SPACE_LOW,
            user_message=f"Output root has less than {min_free_gb:g} GB free.",
            technical_detail=str(target),
            retryable=False,
        )
