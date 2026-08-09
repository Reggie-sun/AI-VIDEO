from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai_video.config import load_yaml
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    ArtifactReference,
    Character,
    LoadedProductionProject,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    Scene,
    Shot,
    Story,
    Storyboard,
    VersionedArtifact,
)
from ai_video.production.paths import resolve_contained_path
from ai_video.production.registry import load_asset_registry
from ai_video.production.validation import validate_project_references

ModelT = TypeVar("ModelT", bound=BaseModel)
ArtifactT = TypeVar("ArtifactT", bound=VersionedArtifact)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _resolve_input(
    root: Path,
    stored: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    try:
        return resolve_contained_path(root, stored, allowed_root=allowed_root)
    except ValueError as exc:
        raise _invalid(
            f"Production artifact path must be clean and contained: {stored}",
            str(exc),
        ) from exc


def _load_yaml_artifact(path: Path, model_type: type[ArtifactT]) -> ArtifactT:
    try:
        model = model_type.model_validate(load_yaml(path))
    except (ValidationError, AiVideoError) as exc:
        raise _invalid(f"Could not load production artifact: {path}", str(exc)) from exc
    if not verify_artifact_hash(model):
        raise _invalid(f"Production artifact content hash mismatch: {path}")
    return model


def _load_json_model(path: Path, model_type: type[ModelT]) -> ModelT:
    try:
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(f"Could not load production state: {path}", str(exc)) from exc


def _load_referenced_artifact(
    root: Path,
    reference: ArtifactReference,
    model_type: type[ArtifactT],
) -> ArtifactT:
    model = _load_yaml_artifact(
        _resolve_input(root, reference.path, allowed_root=root / "creative"),
        model_type,
    )
    actual = (model.artifact_id, model.revision, model.content_hash)
    expected = (reference.artifact_id, reference.revision, reference.content_hash)
    if actual != expected:
        raise _invalid(
            f"Production artifact does not match its project reference: {reference.path}"
        )
    return model


def load_production_project(path: str | Path) -> LoadedProductionProject:
    supplied_path = Path(path)
    if supplied_path.name != "project.yaml":
        raise _invalid("Production project entry point must be named project.yaml.")
    try:
        root = supplied_path.parent.resolve()
    except (OSError, RuntimeError) as exc:
        raise _invalid("Production project root could not be resolved safely.", str(exc)) from exc
    project_path = _resolve_input(root, Path("project.yaml"))
    manifest = _load_json_model(
        _resolve_input(
            root,
            Path("state/manifest.json"),
            allowed_root=root / "state",
        ),
        ProductionManifest,
    )
    project = _load_yaml_artifact(project_path, ProductionProject)
    if manifest.project_id != project.project_id:
        raise _invalid("Production manifest project_id does not match project.")
    if manifest.active_project_revision != project.revision:
        raise _invalid("Production manifest active project revision does not match project.")
    if manifest.active_project_content_hash != project.content_hash:
        raise _invalid("Production manifest active project content hash does not match project.")

    registry_path = Path(f"assets/registry.{manifest.active_registry_revision}.json")
    asset_root = _resolve_input(root, project.asset_root, allowed_root=root / "assets")
    registry, asset_paths = load_asset_registry(registry_path, root, asset_root)
    refs = project.artifacts
    bundle = LoadedProductionProject(
        root=root,
        project=project,
        manifest=manifest,
        brief=_load_referenced_artifact(root, refs.brief, ProductionBrief),
        story=_load_referenced_artifact(root, refs.story, Story),
        characters=tuple(
            _load_referenced_artifact(root, item, Character) for item in refs.characters
        ),
        scenes=tuple(_load_referenced_artifact(root, item, Scene) for item in refs.scenes),
        storyboard=_load_referenced_artifact(root, refs.storyboard, Storyboard),
        shots=tuple(_load_referenced_artifact(root, item, Shot) for item in refs.shots),
        registry=registry,
        asset_paths=asset_paths,
    )
    validate_project_references(bundle)
    return bundle
