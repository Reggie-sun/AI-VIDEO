from __future__ import annotations

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
    DeliveryProfile,
    DurationPolicy,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    ProjectArtifactRefs,
    RendererPolicy,
    Scene,
    Shot,
    SourceReference,
    Story,
    StoryBeat,
    Storyboard,
    StoryboardBeat,
    ToolIdentity,
    VisualStrategy,
)
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
    manifest = ProductionManifest(
        project_id=project.project_id,
        active_project_revision=project.revision,
        active_project_content_hash=project.content_hash,
        active_registry_revision=registry.revision_id,
    )

    _write_yaml(root / "creative/brief.yaml", brief)
    _write_yaml(root / "creative/story.yaml", story)
    _write_yaml(root / "creative/characters/hero.yaml", character)
    _write_yaml(root / "creative/scenes/room.yaml", scene)
    _write_yaml(root / "creative/storyboard.yaml", storyboard)
    _write_yaml(root / "creative/shots/shot-1.yaml", shot)
    _write_yaml(root / "project.yaml", project)
    registry_path = root / f"assets/registry.{registry.revision_id}.json"
    registry_path.write_text(registry.model_dump_json(indent=2), encoding="utf-8")
    manifest_path = root / "state/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return root / "project.yaml"
