"""Standard creative artifact assembly, using the strict project reader primitives."""

from pathlib import Path
from ai_video.production.models import (
    ProductionManifest, ProductionProject, LoadedProductionProject,
    ProductionBrief, Story, Character, Scene, Storyboard, Shot,
)
from ai_video.production.registry import load_asset_registry
from ai_video.production.validation import validate_project_references


def _build_loaded_project(
    root: Path,
    manifest: ProductionManifest,
    project: ProductionProject,
    registry_path: Path,
) -> LoadedProductionProject:
    from ai_video.production.project import _resolve_input, _load_referenced_artifact
    from ai_video.production.production_strategy_reader import load_production_parents, load_production_allocation_policies

    asset_root = _resolve_input(root, project.asset_root, allowed_root=root / "assets")
    registry, asset_paths = load_asset_registry(registry_path, root, asset_root)
    refs = project.artifacts
    shots = tuple(_load_referenced_artifact(root, item, Shot) for item in refs.shots)
    bundle = LoadedProductionProject(
        root=root,
        project=project,
        manifest=manifest,
        brief=_load_referenced_artifact(root, refs.brief, ProductionBrief),
        story=_load_referenced_artifact(root, refs.story, Story),
        characters=tuple(
            _load_referenced_artifact(root, item, Character) for item in refs.characters
        ),
        scenes=tuple(
            _load_referenced_artifact(root, item, Scene) for item in refs.scenes
        ),
        storyboard=_load_referenced_artifact(root, refs.storyboard, Storyboard),
        shots=shots,
        production_allocation_policies=load_production_allocation_policies(root, shots),
        production_parents=load_production_parents(
            root=root,
            manifest=manifest,
            project=project,
            shots=shots,
        ),
        registry=registry,
        asset_paths=asset_paths,
    )
    validate_project_references(bundle)
    return bundle
