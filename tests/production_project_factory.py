from __future__ import annotations

import json
from pathlib import Path

import yaml

from ai_video.config import sha256_file
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ArtifactReference,
    AssetRecord,
    AssetRegistrySnapshot,
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    Character,
    CompositionLayerSpec,
    CompositionSpec,
    DeliveryProfile,
    DurationPolicy,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    ProjectSnapshotPointer,
    ProjectArtifactRefs,
    RendererKind,
    RendererPolicy,
    RegistrySnapshotPointer,
    Scene,
    Shot,
    SourceReference,
    Story,
    StoryBeat,
    Storyboard,
    StoryboardBeat,
    ToolIdentity,
    TransitionKind,
    TransitionSpec,
    VisualStrategy,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256

ZERO_HASH = "0" * 64


def _write_yaml(path: Path, model: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _ref(model: object, path: str) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=model.artifact_id,
        revision=model.revision,
        content_hash=model.content_hash,
        path=path,
    )


def write_production_project(root: Path) -> Path:
    provenance = (SourceReference(kind="user_input", reference="brief-input-1"),)
    brief = seal_artifact(
        ProductionBrief(
            artifact_id="brief-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-brief-1",
            source_provenance=provenance,
            title="Comic Demo",
            objective="Introduce the hero",
            audience="General",
            format="short comic video",
            language="en",
        )
    )
    story = seal_artifact(
        Story(
            artifact_id="story-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-story-1",
            source_provenance=provenance,
            language="en",
            logline="A hero enters a mysterious room.",
            synopsis="The hero enters and discovers a clue.",
            beats=(StoryBeat(beat_id="story-beat-1", summary="The hero enters"),),
        )
    )
    character = seal_artifact(
        Character(
            artifact_id="character-hero",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-character-1",
            source_provenance=provenance,
            character_id="hero",
            name="Hero",
            identity="Lead detective",
            appearance_bible="Blue jacket and silver badge",
            reference_asset_ids=("image-hero-1",),
        )
    )
    scene = seal_artifact(
        Scene(
            artifact_id="scene-room",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-scene-1",
            source_provenance=provenance,
            scene_id="room",
            location="Investigation room",
            time="Night",
            mood="Mysterious",
            participant_ids=("hero",),
            visual_reference_asset_ids=("image-hero-1",),
        )
    )
    shot = seal_artifact(
        Shot(
            artifact_id="shot-artifact-1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-shot-1",
            source_provenance=provenance,
            shot_id="shot-1",
            scene_id="room",
            storyboard_beat_id="beat-1",
            intent="Introduce the hero in the room",
            duration_policy=DurationPolicy(mode="fixed", seconds=3),
            character_ids=("hero",),
            visual_strategy=VisualStrategy.STATIC_IMAGE,
            required_asset_roles=(
                AssetRoleRequirement(
                    role="hero_still",
                    asset_ids=("image-hero-1",),
                    allowed_asset_types=(AssetType.IMAGE,),
                ),
            ),
        )
    )
    storyboard = seal_artifact(
        Storyboard(
            artifact_id="storyboard-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-storyboard-1",
            source_provenance=provenance,
            beats=(
                StoryboardBeat(
                    beat_id="beat-1",
                    scene_id="room",
                    shot_ids=("shot-1",),
                    narrative_intent="Reveal the hero",
                ),
            ),
        )
    )

    asset_path = root / "assets/files/hero.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"fixture-hero-image")
    asset = AssetRecord(
        asset_id="image-hero-1",
        asset_type=AssetType.IMAGE,
        artifact_path="assets/files/hero.png",
        sha256=sha256_file(asset_path),
        size_bytes=asset_path.stat().st_size,
        mime_type="image/png",
        width=1,
        height=1,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=(character.artifact_id,),
        input_fingerprint=character.content_hash,
        creation_receipt_id="receipt-image-hero-1",
        usage_license="test-only",
    )
    registry = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(asset,),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )

    refs = ProjectArtifactRefs(
        brief=_ref(brief, "creative/brief.yaml"),
        story=_ref(story, "creative/story.yaml"),
        characters=(_ref(character, "creative/characters/hero.yaml"),),
        scenes=(_ref(scene, "creative/scenes/room.yaml"),),
        storyboard=_ref(storyboard, "creative/storyboard.yaml"),
        shots=(_ref(shot, "creative/shots/shot-1.yaml"),),
    )
    project = seal_artifact(
        ProductionProject(
            artifact_id="project-comic-demo",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-project-1",
            source_provenance=provenance,
            project_id="comic-demo",
            title="Comic Demo",
            default_language="en",
            delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
            renderer_policy=RendererPolicy(),
            artifacts=refs,
        )
    )
    _write_yaml(root / "creative/brief.yaml", brief)
    _write_yaml(root / "creative/story.yaml", story)
    _write_yaml(root / "creative/characters/hero.yaml", character)
    _write_yaml(root / "creative/scenes/room.yaml", scene)
    _write_yaml(root / "creative/storyboard.yaml", storyboard)
    _write_yaml(root / "creative/shots/shot-1.yaml", shot)
    project_path = root / "project.yaml"
    _write_yaml(project_path, project)
    registry_path = root / f"assets/registry.{registry.revision_id}.json"
    registry_payload = (
        json.dumps(
            registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    manifest = ProductionManifest(
        project_id=project.project_id,
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=sha256_file(project_path),
        ),
        active_registry=RegistrySnapshotPointer(
            path=registry_path.relative_to(root),
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=sha256_file(registry_path),
        ),
    )
    manifest_path = root / "state/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return project_path


def write_and_load_two_shot_project(
    root: Path,
    *,
    filenames: tuple[str, str] = ("shot-1.png", "shot-2.png"),
    seconds: tuple[float, float] = (2.0, 2.0),
    fps: int = 24,
):
    """Build a valid two-Shot raster project through the public P2 loader."""
    write_production_project(root)
    project, registry = load_initial_models(root)

    character = Character.model_validate(
        yaml.safe_load((root / "creative/characters/hero.yaml").read_text(encoding="utf-8"))
    )
    character = seal_artifact(
        character.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "reference_asset_ids": ("image-shot-1",),
            }
        )
    )
    scene = Scene.model_validate(
        yaml.safe_load((root / "creative/scenes/room.yaml").read_text(encoding="utf-8"))
    )
    scene = seal_artifact(
        scene.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "visual_reference_asset_ids": ("image-shot-1",),
            }
        )
    )
    base_shot = Shot.model_validate(
        yaml.safe_load((root / "creative/shots/shot-1.yaml").read_text(encoding="utf-8"))
    )
    shots = tuple(
        seal_artifact(
            base_shot.model_copy(
                update={
                    "artifact_id": f"shot-artifact-{index}",
                    "content_hash": ZERO_HASH,
                    "creation_receipt_id": f"receipt-shot-{index}",
                    "shot_id": f"shot-{index}",
                    "duration_policy": DurationPolicy(
                        mode="fixed", seconds=seconds[index - 1]
                    ),
                    "required_asset_roles": (
                        AssetRoleRequirement(
                            role="still",
                            asset_ids=(f"image-shot-{index}",),
                            allowed_asset_types=(AssetType.IMAGE,),
                        ),
                    ),
                }
            )
        )
        for index in (1, 2)
    )
    storyboard = Storyboard.model_validate(
        yaml.safe_load((root / "creative/storyboard.yaml").read_text(encoding="utf-8"))
    )
    storyboard = seal_artifact(
        storyboard.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "beats": (
                    storyboard.beats[0].model_copy(
                        update={"shot_ids": ("shot-1", "shot-2")}
                    ),
                ),
            }
        )
    )

    assets: list[AssetRecord] = []
    for index, filename in enumerate(filenames, start=1):
        if Path(filename).name != filename:
            raise ValueError("composition fixture filenames must be basenames")
        asset_path = root / "assets/files" / filename
        payload = b"\x89PNG\r\n\x1a\n" + f"fixture-raster-{index}".encode()
        asset_path.write_bytes(payload)
        assets.append(
            registry.assets[0].model_copy(
                update={
                    "asset_id": f"image-shot-{index}",
                    "artifact_path": asset_path.relative_to(root),
                    "sha256": sha256_file(asset_path),
                    "size_bytes": len(payload),
                    "mime_type": "image/png",
                    "input_artifact_ids": (character.artifact_id,),
                    "input_fingerprint": character.content_hash,
                    "creation_receipt_id": f"receipt-image-shot-{index}",
                }
            )
        )
    registry = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=tuple(assets),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )

    refs = project.artifacts.model_copy(
        update={
            "characters": (_ref(character, "creative/characters/hero.yaml"),),
            "scenes": (_ref(scene, "creative/scenes/room.yaml"),),
            "storyboard": _ref(storyboard, "creative/storyboard.yaml"),
            "shots": tuple(
                _ref(shot, f"creative/shots/shot-{index}.yaml")
                for index, shot in enumerate(shots, start=1)
            ),
        }
    )
    project = seal_artifact(
        project.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "delivery_profile": project.delivery_profile.model_copy(
                    update={"fps": fps}
                ),
                "artifacts": refs,
            }
        )
    )

    _write_yaml(root / "creative/characters/hero.yaml", character)
    _write_yaml(root / "creative/scenes/room.yaml", scene)
    _write_yaml(root / "creative/storyboard.yaml", storyboard)
    for index, shot in enumerate(shots, start=1):
        _write_yaml(root / f"creative/shots/shot-{index}.yaml", shot)
    project_path = root / "project.yaml"
    _write_yaml(project_path, project)
    registry_path = root / f"assets/registry.{registry.revision_id}.json"
    registry_path.write_text(
        json.dumps(
            registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = ProductionManifest(
        project_id=project.project_id,
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=sha256_file(project_path),
        ),
        active_registry=RegistrySnapshotPointer(
            path=registry_path.relative_to(root),
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=sha256_file(registry_path),
        ),
    )
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    return load_production_project(project_path)


def make_composition_spec(
    *,
    shot_ids: tuple[str, ...] = ("shot-1", "shot-2"),
    sample_rate: int = 48_000,
) -> CompositionSpec:
    transitions = tuple(
        TransitionSpec(
            from_shot_id=source,
            to_shot_id=target,
            kind=TransitionKind.CUT,
            duration_frames=0,
        )
        for source, target in zip(shot_ids, shot_ids[1:])
    )
    return seal_artifact(
        CompositionSpec(
            artifact_id="composition-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-composition-1",
            source_provenance=(
                SourceReference(kind="user_input", reference="composition-input-1"),
            ),
            composition_id="main",
            shot_ids=shot_ids,
            layers=tuple(
                CompositionLayerSpec(
                    layer_id=f"layer-{shot_id}",
                    shot_id=shot_id,
                    asset_role="still",
                    asset_id=f"image-{shot_id}",
                )
                for shot_id in shot_ids
            ),
            transitions=transitions,
            delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
            sample_rate=sample_rate,
            requested_renderer=RendererKind.HYPERFRAMES,
        )
    )


def make_loaded_project_and_spec(root: Path):
    loaded = write_and_load_two_shot_project(root)
    return loaded, make_composition_spec()


def load_initial_models(root: Path) -> tuple[ProductionProject, AssetRegistrySnapshot]:
    project = ProductionProject.model_validate(
        yaml.safe_load((root / "project.yaml").read_text(encoding="utf-8"))
    )
    manifest = ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )
    registry = AssetRegistrySnapshot.model_validate_json(
        (root / manifest.active_registry.path).read_text(encoding="utf-8")
    )
    return project, registry


def load_revision_two_models(root: Path) -> tuple[ProductionProject, AssetRegistrySnapshot]:
    project, registry = load_initial_models(root)
    revision_two = seal_artifact(
        project.model_copy(
            update={
                "revision": 2,
                "content_hash": ZERO_HASH,
                "title": "Comic Demo Revision 2",
            }
        )
    )
    return revision_two, registry


def make_revision_two_request(root: Path, *, attempt_id: str = "attempt-revision-2") -> object:
    from ai_video.production.state_commit import prepare_project_registry_commit

    manifest = ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )
    project, registry = load_revision_two_models(root)
    return prepare_project_registry_commit(
        manifest=manifest,
        project=project,
        registry=registry,
        attempt_id=attempt_id,
    )
