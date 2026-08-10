from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
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
    HybridLayer,
    LoadedProductionProject,
    MotionDirective,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    ProjectArtifactRefs,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
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
from ai_video.production.validation import validate_project_references, validate_shot_strategy
from production_project_factory import make_p4_composition_fixture

HASH = "0" * 64
PROVENANCE = (SourceReference(kind="user_input", reference="brief-1"),)


def make_asset(
    asset_id: str,
    asset_type: AssetType,
    source_kind: AssetSourceKind = AssetSourceKind.IMPORTED,
    *,
    input_artifact_ids: tuple[str, ...] = (),
) -> AssetRecord:
    return AssetRecord(
        asset_id=asset_id,
        asset_type=asset_type,
        artifact_path=f"assets/files/{asset_id}.bin",
        sha256=HASH,
        size_bytes=1,
        mime_type="application/octet-stream",
        source_kind=source_kind,
        tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=input_artifact_ids,
        input_fingerprint=HASH,
        creation_receipt_id=f"receipt-{asset_id}",
        usage_license="test-only",
    )


def make_role(role: str, asset_id: str, asset_type: AssetType) -> AssetRoleRequirement:
    return AssetRoleRequirement(
        role=role,
        asset_ids=(asset_id,),
        allowed_asset_types=(asset_type,),
    )


def make_shot(strategy: VisualStrategy, **updates: object) -> Shot:
    data: dict[str, object] = {
        "artifact_id": "shot-artifact-1",
        "revision": 1,
        "content_hash": HASH,
        "creation_receipt_id": "receipt-shot-1",
        "source_provenance": PROVENANCE,
        "shot_id": "shot-1",
        "scene_id": "scene-1",
        "storyboard_beat_id": "beat-1",
        "intent": "Introduce the hero",
        "duration_policy": DurationPolicy(mode="fixed", seconds=3),
        "character_ids": ("hero",),
        "visual_strategy": strategy,
    }
    data.update(updates)
    return Shot(**data)


@pytest.mark.parametrize(
    ("shot", "assets"),
    [
        (
            make_shot(
                VisualStrategy.STATIC_IMAGE,
                required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
            ),
            {"hero.png": make_asset("hero.png", AssetType.IMAGE)},
        ),
        (
            make_shot(
                VisualStrategy.IMAGE_MOTION,
                required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
                motion_directives=(MotionDirective(kind="pan", parameters={"x": 12}),),
            ),
            {"hero.png": make_asset("hero.png", AssetType.IMAGE)},
        ),
        (
            make_shot(
                VisualStrategy.MOTION_GRAPHICS,
                required_asset_roles=(
                    make_role("card", "card.json", AssetType.COMPOSITION_SOURCE),
                ),
                motion_directives=(
                    MotionDirective(
                        kind="animate",
                        parameters={"property": "opacity", "duration_seconds": 1},
                    ),
                ),
            ),
            {"card.json": make_asset("card.json", AssetType.COMPOSITION_SOURCE)},
        ),
        (
            make_shot(
                VisualStrategy.GENERATED_VIDEO,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
                generated_video_rationale="The action cannot be expressed by image motion.",
            ),
            {
                "clip.mp4": make_asset(
                    "clip.mp4", AssetType.VIDEO, AssetSourceKind.GENERATED
                )
            },
        ),
        (
            make_shot(
                VisualStrategy.EXISTING_VIDEO,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
            ),
            {"clip.mp4": make_asset("clip.mp4", AssetType.VIDEO)},
        ),
        (
            make_shot(
                VisualStrategy.HYBRID,
                required_asset_roles=(
                    make_role("hero", "hero.png", AssetType.IMAGE),
                    make_role("clip", "clip.mp4", AssetType.VIDEO),
                ),
                hybrid_layers=(
                    HybridLayer(
                        role="background",
                        asset_role="clip",
                        asset_id="clip.mp4",
                        z_index=0,
                    ),
                    HybridLayer(
                        role="hero",
                        asset_role="hero",
                        asset_id="hero.png",
                        z_index=1,
                    ),
                ),
            ),
            {
                "hero.png": make_asset("hero.png", AssetType.IMAGE),
                "clip.mp4": make_asset("clip.mp4", AssetType.VIDEO),
            },
        ),
    ],
)
def test_all_visual_strategies_accept_concrete_assets(
    shot: Shot, assets: dict[str, AssetRecord]
):
    validate_shot_strategy(shot, assets)


@pytest.mark.parametrize(
    ("shot", "assets", "message"),
    [
        (
            make_shot(
                VisualStrategy.IMAGE_MOTION,
                required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
            ),
            {"hero.png": make_asset("hero.png", AssetType.IMAGE)},
            "motion_directives",
        ),
        (
            make_shot(
                VisualStrategy.MOTION_GRAPHICS,
                required_asset_roles=(
                    make_role("card", "card.json", AssetType.COMPOSITION_SOURCE),
                ),
            ),
            {"card.json": make_asset("card.json", AssetType.COMPOSITION_SOURCE)},
            "motion_directives",
        ),
        (
            make_shot(
                VisualStrategy.GENERATED_VIDEO,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
                generated_video_rationale="needed",
            ),
            {"clip.mp4": make_asset("clip.mp4", AssetType.VIDEO)},
            "generated_video",
        ),
        (
            make_shot(
                VisualStrategy.EXISTING_VIDEO,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
            ),
            {
                "clip.mp4": make_asset(
                    "clip.mp4", AssetType.VIDEO, AssetSourceKind.GENERATED
                )
            },
            "imported video",
        ),
        (
            make_shot(
                VisualStrategy.STATIC_IMAGE,
                required_asset_roles=(make_role("hero", "missing.png", AssetType.IMAGE),),
            ),
            {},
            "unknown asset",
        ),
        (
            make_shot(
                VisualStrategy.STATIC_IMAGE,
                required_asset_roles=(make_role("hero", "hero.mp4", AssetType.IMAGE),),
            ),
            {"hero.mp4": make_asset("hero.mp4", AssetType.VIDEO)},
            "rejects asset type",
        ),
    ],
)
def test_strategy_rejects_invalid_bound_inputs(
    shot: Shot, assets: dict[str, AssetRecord], message: str
):
    with pytest.raises(AiVideoError) as exc:
        validate_shot_strategy(shot, assets)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert message in exc.value.user_message


def test_static_image_rejects_continuous_motion_directives():
    shot = make_shot(
        VisualStrategy.STATIC_IMAGE,
        required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
        motion_directives=(MotionDirective(kind="pan", parameters={"x": 12}),),
    )
    with pytest.raises(AiVideoError, match="must not define motion_directives"):
        validate_shot_strategy(shot, {"hero.png": make_asset("hero.png", AssetType.IMAGE)})


def test_motion_strategy_rejects_directive_without_numeric_parameters():
    shot = make_shot(
        VisualStrategy.IMAGE_MOTION,
        required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
        motion_directives=(
            MotionDirective(kind="pan", parameters={"instruction": "more dynamic"}),
        ),
    )
    with pytest.raises(AiVideoError, match="deterministic numeric parameter"):
        validate_shot_strategy(shot, {"hero.png": make_asset("hero.png", AssetType.IMAGE)})


def test_motion_strategy_rejects_unrelated_numeric_parameter():
    shot = make_shot(
        VisualStrategy.IMAGE_MOTION,
        required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
        motion_directives=(
            MotionDirective(
                kind="pan",
                parameters={"instruction": "more dynamic", "duration_seconds": 1},
            ),
        ),
    )
    with pytest.raises(AiVideoError, match="pan.*x or y"):
        validate_shot_strategy(shot, {"hero.png": make_asset("hero.png", AssetType.IMAGE)})


def test_hybrid_requires_every_layer_source_to_be_bound():
    shot = make_shot(
        VisualStrategy.HYBRID,
        required_asset_roles=(
            make_role("hero", "hero.png", AssetType.IMAGE),
            make_role("background", "background.png", AssetType.IMAGE),
        ),
        hybrid_layers=(
            HybridLayer(
                role="background",
                asset_role="background",
                asset_id="background.png",
                z_index=0,
            ),
            HybridLayer(
                role="hero",
                asset_role="hero",
                asset_id="other.png",
                z_index=1,
            ),
        ),
    )
    assets = {
        "hero.png": make_asset("hero.png", AssetType.IMAGE),
        "background.png": make_asset("background.png", AssetType.IMAGE),
    }
    with pytest.raises(AiVideoError, match="other.png"):
        validate_shot_strategy(shot, assets)


def test_hybrid_requires_every_bound_source_to_have_a_layer():
    shot = make_shot(
        VisualStrategy.HYBRID,
        required_asset_roles=(
            make_role("hero", "hero.png", AssetType.IMAGE),
            make_role("background", "background.png", AssetType.IMAGE),
            make_role("overlay", "overlay.png", AssetType.IMAGE),
        ),
        hybrid_layers=(
            HybridLayer(
                role="background",
                asset_role="background",
                asset_id="background.png",
                z_index=0,
            ),
            HybridLayer(
                role="hero",
                asset_role="hero",
                asset_id="hero.png",
                z_index=1,
            ),
        ),
    )
    assets = {
        "hero.png": make_asset("hero.png", AssetType.IMAGE),
        "background.png": make_asset("background.png", AssetType.IMAGE),
        "overlay.png": make_asset("overlay.png", AssetType.IMAGE),
    }
    with pytest.raises(AiVideoError, match="missing layers.*overlay.png"):
        validate_shot_strategy(shot, assets)


def test_hybrid_requires_each_role_when_roles_share_an_asset():
    shot = make_shot(
        VisualStrategy.HYBRID,
        required_asset_roles=(
            make_role("hero", "hero.png", AssetType.IMAGE),
            make_role("overlay", "hero.png", AssetType.IMAGE),
            make_role("background", "background.png", AssetType.IMAGE),
        ),
        hybrid_layers=(
            HybridLayer(
                role="background",
                asset_role="background",
                asset_id="background.png",
                z_index=0,
            ),
            HybridLayer(
                role="hero",
                asset_role="hero",
                asset_id="hero.png",
                z_index=1,
            ),
        ),
    )
    with pytest.raises(AiVideoError, match="overlay.*hero.png"):
        validate_shot_strategy(
            shot,
            {
                "hero.png": make_asset("hero.png", AssetType.IMAGE),
                "background.png": make_asset("background.png", AssetType.IMAGE),
            },
        )


@pytest.mark.parametrize(
    ("shot", "assets", "message"),
    [
        (make_shot(VisualStrategy.STATIC_IMAGE), {}, "image role"),
        (
            make_shot(
                VisualStrategy.IMAGE_MOTION,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
                motion_directives=(MotionDirective(kind="pan", parameters={"x": 1}),),
            ),
            {"clip.mp4": make_asset("clip.mp4", AssetType.VIDEO)},
            "image role",
        ),
        (
            make_shot(
                VisualStrategy.MOTION_GRAPHICS,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
                motion_directives=(
                    MotionDirective(kind="animate", parameters={"property": "opacity"}),
                ),
            ),
            {"clip.mp4": make_asset("clip.mp4", AssetType.VIDEO)},
            "composition_source",
        ),
        (
            make_shot(
                VisualStrategy.GENERATED_VIDEO,
                required_asset_roles=(make_role("clip", "clip.mp4", AssetType.VIDEO),),
            ),
            {
                "clip.mp4": make_asset(
                    "clip.mp4", AssetType.VIDEO, AssetSourceKind.GENERATED
                )
            },
            "rationale",
        ),
        (
            make_shot(
                VisualStrategy.HYBRID,
                required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
                hybrid_layers=(
                    HybridLayer(
                        role="hero",
                        asset_role="hero",
                        asset_id="hero.png",
                        z_index=0,
                    ),
                ),
            ),
            {"hero.png": make_asset("hero.png", AssetType.IMAGE)},
            "at least two layers",
        ),
        (
            make_shot(
                VisualStrategy.HYBRID,
                required_asset_roles=(
                    make_role("hero", "hero.png", AssetType.IMAGE),
                    make_role("background", "background.png", AssetType.IMAGE),
                ),
                hybrid_layers=(
                    HybridLayer(
                        role="layer",
                        asset_role="hero",
                        asset_id="hero.png",
                        z_index=0,
                    ),
                    HybridLayer(
                        role="layer",
                        asset_role="background",
                        asset_id="background.png",
                        z_index=1,
                    ),
                ),
            ),
            {
                "hero.png": make_asset("hero.png", AssetType.IMAGE),
                "background.png": make_asset("background.png", AssetType.IMAGE),
            },
            "layer roles must be unique",
        ),
        (
            make_shot(
                VisualStrategy.HYBRID,
                required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
                hybrid_layers=(
                    HybridLayer(
                        role="background",
                        asset_role="hero",
                        asset_id="hero.png",
                        z_index=0,
                    ),
                    HybridLayer(
                        role="hero",
                        asset_role="hero",
                        asset_id="hero.png",
                        z_index=1,
                    ),
                ),
            ),
            {"hero.png": make_asset("hero.png", AssetType.IMAGE)},
            "two source assets",
        ),
        (
            make_shot(
                VisualStrategy.STATIC_IMAGE,
                required_asset_roles=(
                    make_role("hero", "hero.png", AssetType.IMAGE),
                    make_role("hero", "background.png", AssetType.IMAGE),
                ),
            ),
            {
                "hero.png": make_asset("hero.png", AssetType.IMAGE),
                "background.png": make_asset("background.png", AssetType.IMAGE),
            },
            "duplicate required asset roles",
        ),
        (
            make_shot(
                VisualStrategy.STATIC_IMAGE,
                required_asset_roles=(
                    AssetRoleRequirement(
                        role="hero",
                        asset_ids=("hero.png", "hero.png"),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
            ),
            {"hero.png": make_asset("hero.png", AssetType.IMAGE)},
            "duplicate asset IDs",
        ),
    ],
)
def test_strategy_rejects_invalid_shape(
    shot: Shot, assets: dict[str, AssetRecord], message: str
):
    with pytest.raises(AiVideoError) as exc:
        validate_shot_strategy(shot, assets)
    assert message in exc.value.user_message


def artifact_ref(artifact: object, path: str) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=getattr(artifact, "artifact_id"),
        revision=getattr(artifact, "revision"),
        content_hash=getattr(artifact, "content_hash"),
        path=path,
    )


def make_bundle() -> LoadedProductionProject:
    asset = make_asset("hero.png", AssetType.IMAGE)
    brief = ProductionBrief(
        artifact_id="brief-1",
        revision=1,
        content_hash=HASH,
        creation_receipt_id="receipt-brief-1",
        source_provenance=PROVENANCE,
        title="Demo",
        objective="Tell a story",
        audience="General",
        format="short",
        language="en",
    )
    story = Story(
        artifact_id="story-1",
        revision=1,
        content_hash=HASH,
        creation_receipt_id="receipt-story-1",
        source_provenance=PROVENANCE,
        language="en",
        logline="Hero enters.",
        synopsis="A hero enters a room.",
        beats=(StoryBeat(beat_id="story-beat-1", summary="Entry"),),
    )
    character = Character(
        artifact_id="character-artifact-1",
        revision=1,
        content_hash=HASH,
        creation_receipt_id="receipt-character-1",
        source_provenance=PROVENANCE,
        character_id="hero",
        name="Hero",
        identity="Lead",
        appearance_bible="Blue jacket",
        reference_asset_ids=("hero.png",),
    )
    scene = Scene(
        artifact_id="scene-artifact-1",
        revision=1,
        content_hash=HASH,
        creation_receipt_id="receipt-scene-1",
        source_provenance=PROVENANCE,
        scene_id="scene-1",
        location="Room",
        time="Day",
        mood="Calm",
        participant_ids=("hero",),
        visual_reference_asset_ids=("hero.png",),
    )
    shot = make_shot(
        VisualStrategy.STATIC_IMAGE,
        required_asset_roles=(make_role("hero", "hero.png", AssetType.IMAGE),),
    )
    storyboard = Storyboard(
        artifact_id="storyboard-1",
        revision=1,
        content_hash=HASH,
        creation_receipt_id="receipt-storyboard-1",
        source_provenance=PROVENANCE,
        beats=(
            StoryboardBeat(
                beat_id="beat-1",
                scene_id="scene-1",
                shot_ids=("shot-1",),
                narrative_intent="Entry",
            ),
        ),
    )
    refs = ProjectArtifactRefs(
        brief=artifact_ref(brief, "creative/brief.yaml"),
        story=artifact_ref(story, "creative/story.yaml"),
        characters=(artifact_ref(character, "creative/characters/hero.yaml"),),
        scenes=(artifact_ref(scene, "creative/scenes/room.yaml"),),
        storyboard=artifact_ref(storyboard, "creative/storyboard.yaml"),
        shots=(artifact_ref(shot, "creative/shots/shot-1.yaml"),),
    )
    project = ProductionProject(
        artifact_id="project-artifact-1",
        revision=1,
        content_hash=HASH,
        creation_receipt_id="receipt-project-1",
        source_provenance=PROVENANCE,
        project_id="project-1",
        title="Demo",
        default_language="en",
        delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
        renderer_policy=RendererPolicy(),
        artifacts=refs,
    )
    manifest = ProductionManifest(
        project_id="project-1",
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=1,
            content_hash=HASH,
            file_sha256=HASH,
        ),
        active_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{HASH}.json"),
            revision_id=HASH,
            content_hash=HASH,
            file_sha256=HASH,
        ),
    )
    return LoadedProductionProject(
        root="/tmp/project",
        project=project,
        manifest=manifest,
        brief=brief,
        story=story,
        characters=(character,),
        scenes=(scene,),
        storyboard=storyboard,
        shots=(shot,),
        registry=AssetRegistrySnapshot(revision_id=HASH, content_hash=HASH, assets=(asset,)),
        asset_paths={"hero.png": "/tmp/project/assets/files/hero.png"},
    )


def test_project_references_accept_complete_graph():
    validate_project_references(make_bundle())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unknown", "unknown source audio"),
        ("wrong_type", "source audio type"),
        ("hash", "source audio hash"),
        ("script", "script hash"),
    ],
)
def test_project_references_reject_caption_source_identity_drift(
    tmp_path, mutation, message
):
    bundle, _ = make_p4_composition_fixture(tmp_path)
    caption = next(item for item in bundle.registry.assets if item.caption_metadata is not None)
    metadata = caption.caption_metadata
    assert metadata is not None
    assets = list(bundle.registry.assets)
    if mutation == "unknown":
        metadata = metadata.model_copy(update={"source_audio_asset_id": "missing-audio"})
    elif mutation == "wrong_type":
        source_index = next(
            index
            for index, item in enumerate(assets)
            if item.asset_id == metadata.source_audio_asset_id
        )
        assets[source_index] = assets[source_index].model_copy(
            update={"asset_type": AssetType.IMAGE, "audio_metadata": None}
        )
    elif mutation == "hash":
        metadata = metadata.model_copy(update={"source_audio_sha256": "f" * 64})
    elif mutation == "script":
        metadata = metadata.model_copy(update={"script_hash": "f" * 64})
    assets = [
        item.model_copy(update={"caption_metadata": metadata})
        if item.asset_id == caption.asset_id
        else item
        for item in assets
    ]
    changed = bundle.model_copy(
        update={
            "registry": bundle.registry.model_copy(update={"assets": tuple(assets)})
        }
    )

    with pytest.raises(AiVideoError, match=message):
        validate_project_references(changed)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda bundle: bundle.model_copy(
                update={"characters": bundle.characters + (bundle.characters[0],)}
            ),
            "duplicate character_id",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "scenes": (
                        bundle.scenes[0].model_copy(update={"participant_ids": ("missing",)}),
                    )
                }
            ),
            "unknown references",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "shots": (
                        bundle.shots[0].model_copy(update={"character_ids": ("missing",)}),
                    )
                }
            ),
            "unknown character",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "shots": (
                        bundle.shots[0].model_copy(update={"scene_id": "missing"}),
                    )
                }
            ),
            "unknown scene",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "storyboard": bundle.storyboard.model_copy(
                        update={
                            "beats": (
                                bundle.storyboard.beats[0].model_copy(
                                    update={"scene_id": "missing"}
                                ),
                            )
                        }
                    )
                }
            ),
            "unknown scene",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "storyboard": bundle.storyboard.model_copy(
                        update={
                            "beats": (
                                bundle.storyboard.beats[0].model_copy(
                                    update={"shot_ids": ("missing",)}
                                ),
                            )
                        }
                    )
                }
            ),
            "unknown shot",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "story": bundle.story.model_copy(
                        update={"artifact_id": bundle.brief.artifact_id}
                    )
                }
            ),
            "duplicate artifact_id",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "registry": bundle.registry.model_copy(
                        update={
                            "assets": (
                                bundle.registry.assets[0].model_copy(
                                    update={"input_artifact_ids": ("missing",)}
                                ),
                            )
                        }
                    )
                }
            ),
            "unknown input",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={"scenes": bundle.scenes + (bundle.scenes[0],)}
            ),
            "duplicate scene_id",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={"shots": bundle.shots + (bundle.shots[0],)}
            ),
            "duplicate shot_id",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "storyboard": bundle.storyboard.model_copy(
                        update={"beats": bundle.storyboard.beats + (bundle.storyboard.beats[0],)}
                    )
                }
            ),
            "duplicate beat_id",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "characters": (
                        bundle.characters[0].model_copy(
                            update={"reference_asset_ids": ("missing.png",)}
                        ),
                    )
                }
            ),
            "unknown asset",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "scenes": (
                        bundle.scenes[0].model_copy(
                            update={"visual_reference_asset_ids": ("missing.png",)}
                        ),
                    )
                }
            ),
            "unknown references",
        ),
        (
            lambda bundle: bundle.model_copy(
                update={
                    "project": bundle.project.model_copy(
                        update={"artifact_id": bundle.brief.artifact_id}
                    )
                }
            ),
            "duplicate artifact_id",
        ),
    ],
)
def test_project_references_reject_invalid_graph(
    mutate: Callable[[LoadedProductionProject], LoadedProductionProject], message: str
):
    with pytest.raises(AiVideoError) as exc:
        validate_project_references(mutate(make_bundle()))
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert message in exc.value.user_message


def test_storyboard_beat_scene_must_match_shot_scene():
    bundle = make_bundle()
    other_scene = bundle.scenes[0].model_copy(
        update={"artifact_id": "scene-artifact-2", "scene_id": "scene-2"}
    )
    changed = bundle.model_copy(update={"scenes": bundle.scenes + (other_scene,)})
    beat = changed.storyboard.beats[0].model_copy(update={"scene_id": "scene-2"})
    changed = changed.model_copy(
        update={"storyboard": changed.storyboard.model_copy(update={"beats": (beat,)})}
    )
    with pytest.raises(AiVideoError, match="scene does not match"):
        validate_project_references(changed)


def test_loaded_bundle_asset_paths_are_immutable():
    bundle = make_bundle()
    with pytest.raises(TypeError, match="immutable"):
        bundle.asset_paths["hero.png"] = bundle.root / "other.png"
