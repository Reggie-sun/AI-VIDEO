#!/usr/bin/env python3
"""Prepare the user-approved rainy-station P0 qualification bundle.

This script performs no Provider call and makes no quality or P6 claim. It
imports exact GPT Image 2 MCP outputs, freezes model-facing tensor preparation,
and records only ``qualification_prepared`` through ProductionStateCommitter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.image_import import (
    AutomatedBrowserImageImportReceipt,
    automated_browser_image_import_asset,
)
from ai_video.production.models import (
    ActorIdentity,
    ArtifactReference,
    AssetRegistrySnapshot,
    AssetRoleRequirement,
    AssetType,
    Character,
    DeliveryProfile,
    DurationPolicy,
    ProductionBrief,
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
    VisualStrategy,
)
from ai_video.production.paths import (
    canonical_automated_browser_image_import_receipt_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
)
from ai_video.production.shot_continuity_source_stack import (
    load_shot_continuity_source_execution_sources,
)
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    RuntimeSeal,
    StackComponentIdentity,
)
from ai_video.production.video_transition import (
    BoundaryKind,
    CandidateStackBinding,
    ContinuityAnchorBinding,
    ContinuityAnchorRole,
    ContinuityObligation,
    ContinuityTransitionPolicy,
    CreativeArtifactIdentity,
    MotionCoverage,
    P0QualificationInput,
    P0QualificationPreparedReceipt,
    RealShotValidationSet,
    ValidationEdgeBinding,
)


ZERO_HASH = "0" * 64
SOURCE_WIDTH = 1659
SOURCE_HEIGHT = 948
TARGET_WIDTH = 1344
TARGET_HEIGHT = 768
FRAME_COUNT = 124
FPS = 24
STOCK_REF2VA_SHA256 = (
    "9eef934046a0671bc8a5daf87100705e1478419c574cfde70c50fbe6885f76a9"
)
PRUNED_FL2VA_SHA256 = (
    "e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a"
)
PRUNED_REF2VA_SHA256 = (
    "9255f52b6677845ad238f20dfaafa94727053694127ab7f255c048f0f9365779"
)
TEXT_ENCODER_SHA256 = (
    "35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6"
)
VIDEO_VAE_SHA256 = (
    "7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522"
)
AUDIO_VAE_SHA256 = (
    "8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48"
)


def _artifact(path: Path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def _reference(value, path: str) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=value.artifact_id,
        revision=value.revision,
        content_hash=value.content_hash,
        path=Path(path),
    )


def _metadata(path: Path) -> tuple[dict[str, object], bytes, int, int]:
    value = json.loads(path.with_name("metadata.json").read_text(encoding="utf-8"))
    if value.get("backend") != "chatgpt-web" or value.get("mode") != "direct-typescript-browser":
        raise ValueError(f"unexpected GPT Image 2 MCP metadata for {path.name}")
    prompt = value.get("prompt")
    created_at = value.get("created_at")
    if not isinstance(prompt, str) or not prompt or not isinstance(created_at, str):
        raise ValueError(f"incomplete GPT Image 2 MCP metadata for {path.name}")
    payload = path.read_bytes()
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        mode = image.mode
    if (width, height, mode) != (SOURCE_WIDTH, SOURCE_HEIGHT, "RGB"):
        raise ValueError(
            f"{path.name} must be RGB {SOURCE_WIDTH}x{SOURCE_HEIGHT}, got "
            f"{width}x{height} {mode}"
        )
    if width * TARGET_HEIGHT != height * TARGET_WIDTH:
        raise ValueError(f"{path.name} does not preserve the exact target aspect ratio")
    return value, payload, width, height


def validate_h3_prompt_contract(prompt: str) -> str:
    markers = (
        "integrated_multimodal_description:",
        "overall_soundscape:",
        "non_diegetic_music:",
    )
    if not prompt.startswith("For the target video,") or "\n\n" not in prompt:
        raise ValueError("H3 prompt requires an explicit conditioning instruction")
    conditioning = prompt.split("\n\n", 1)[0]
    if not all(
        token in conditioning
        for token in ("<Picture 1>", "<Picture 2>", "<Picture 3>", "<Video 1>")
    ):
        raise ValueError("H3 prompt requires canonical bracketed conditioning roles")
    if any(prompt.count(marker) != 1 for marker in markers):
        raise ValueError("H3 prompt requires exactly one canonical three-field set")
    positions = tuple(prompt.index(marker) for marker in markers)
    if positions != tuple(sorted(positions)):
        raise ValueError("H3 prompt fields are not canonically ordered")
    visible = prompt[positions[0] : positions[1]].lower()
    if not all(token in visible for token in ("live-action", "camera", "amplitude", "speed")):
        raise ValueError("H3 visual field requires style and concrete camera motion")
    return prompt


def _receipt(
    *,
    image_path: Path,
    target_kind: str,
    target_artifact_id: str,
    target_asset_role: str,
    approved_at: str,
    imported_at: str,
) -> tuple[AutomatedBrowserImageImportReceipt, bytes]:
    metadata, payload, width, height = _metadata(image_path)
    prompt = str(metadata["prompt"])
    return (
        AutomatedBrowserImageImportReceipt.create(
            declared_ui_product_label="GPT Image 2",
            original_filename=image_path.name,
            output_sha256=hashlib.sha256(payload).hexdigest(),
            output_size_bytes=len(payload),
            output_width=width,
            output_height=height,
            generated_at=str(metadata["created_at"]),
            approved_at=approved_at,
            imported_at=imported_at,
            prompt_fingerprint=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            references=(),
            target_kind=target_kind,
            target_artifact_id=target_artifact_id,
            target_asset_role=target_asset_role,
            automation_actor=ActorIdentity(
                actor_id="gpt-image-2-mcp-chatgpt-web",
                actor_kind="automation",
            ),
            human_approval_actor=ActorIdentity(
                actor_id="user-shot-continuity-owner",
                actor_kind="human",
            ),
            approved=True,
            license_source_note=(
                "User-approved GPT Image 2 generated reference; ownership and "
                "downstream usage rights are not inferred."
            ),
        ),
        payload,
    )


def _build_project(
    *,
    image_paths: tuple[Path, Path, Path, Path],
    approved_at: str,
    imported_at: str,
):
    provenance = (
        SourceReference(
            kind="user_input",
            reference="shot-continuity-rainy-station-approved-direction-2026-08-23",
        ),
    )
    brief = seal_artifact(
        ProductionBrief(
            artifact_id="brief-rainy-station-continuity",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="authoring-rainy-station-brief-v1",
            source_provenance=provenance,
            title="Rainy Station Continuity Pilot",
            objective="Validate exact four-anchor continuity across three adjacent hard cuts.",
            audience="Internal AI-VIDEO continuity qualification reviewers",
            format="Four-shot photorealistic cinematic sequence",
            language="en",
            constraints=(
                "Exactly one traveler",
                "Persistent mustard-yellow raincoat and red cross-body satchel",
                "Rightward screen axis and stable medium side-profile scale",
                "No retry, no fallback, no quality claim before P6/human review",
            ),
        )
    )
    story = seal_artifact(
        Story(
            artifact_id="story-rainy-station-continuity",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="authoring-rainy-station-story-v1",
            source_provenance=provenance,
            language="en",
            logline="A lone traveler crosses a rain-soaked platform and settles beneath the clock.",
            synopsis=(
                "The same traveler advances screen-right through three measured motion "
                "handoffs before coming to rest beneath the station clock."
            ),
            beats=(
                StoryBeat(beat_id="platform-walk", summary="Measured rightward walk and stop."),
            ),
        )
    )

    character_receipt, character_bytes = _receipt(
        image_path=image_paths[1],
        target_kind="character_master",
        target_artifact_id="character-rainy-station-traveler",
        target_asset_role="canonical_identity",
        approved_at=approved_at,
        imported_at=imported_at,
    )
    character_asset = automated_browser_image_import_asset(character_receipt)
    character = seal_artifact(
        Character(
            artifact_id="character-rainy-station-traveler",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=character_receipt.content_hash,
            source_provenance=provenance,
            character_id="traveler",
            name="The Traveler",
            identity="Fictional adult East Asian woman, strict right-facing side profile.",
            appearance_bible=(
                "Short blunt black bob, stable facial silhouette and body proportions; "
                "exactly one visible person."
            ),
            wardrobe=(
                "mustard-yellow hooded raincoat",
                "black trousers",
                "black boots",
                "red cross-body leather satchel on the same side",
            ),
            reference_asset_ids=(character_asset.asset_id,),
            allowed_variations=("natural stride phase", "small physical satchel swing"),
        )
    )

    scene_receipt, scene_bytes = _receipt(
        image_path=image_paths[3],
        target_kind="scene_reference",
        target_artifact_id="scene-rainy-station-platform",
        target_asset_role="canonical_scene",
        approved_at=approved_at,
        imported_at=imported_at,
    )
    scene_asset = automated_browser_image_import_asset(scene_receipt)
    scene = seal_artifact(
        Scene(
            artifact_id="scene-rainy-station-platform",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=scene_receipt.content_hash,
            source_provenance=provenance,
            scene_id="rainy-station-platform",
            location="Exterior railway platform with cream columns and dark blue bases",
            time="Blue hour at night",
            mood="Restrained cinematic rain, wet reflections, warm distant practicals",
            participant_ids=(character.character_id,),
            continuity_constraints=(
                "Clock remains ahead at upper right",
                "Level horizon and chest-height camera",
                "Fixed 50mm-equivalent field of view",
                "Stable rightward screen axis",
            ),
            visual_reference_asset_ids=(scene_asset.asset_id,),
        )
    )

    shot_receipts: list[AutomatedBrowserImageImportReceipt] = []
    shot_payloads: list[bytes] = []
    shot_assets = []
    shots = []
    intents = (
        "Enter from screen-left in a measured rightward stride.",
        "Continue rightward with clear subject-motion handoff and stable scale.",
        "Approach the clock while camera tracking remains smooth and level.",
        "Finish the walk and settle naturally beneath the clock.",
    )
    for ordinal, (image_path, intent) in enumerate(zip(image_paths, intents, strict=True), 1):
        artifact_id = f"shot-rainy-station-{ordinal}"
        receipt, payload = _receipt(
            image_path=image_path,
            target_kind="key_shot",
            target_artifact_id=artifact_id,
            target_asset_role="approved_endpoint",
            approved_at=approved_at,
            imported_at=imported_at,
        )
        asset = automated_browser_image_import_asset(receipt)
        shot = seal_artifact(
            Shot(
                artifact_id=artifact_id,
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id=receipt.content_hash,
                source_provenance=provenance,
                shot_id=f"rainy-station-{ordinal}",
                scene_id=scene.scene_id,
                storyboard_beat_id="platform-walk",
                intent=intent,
                duration_policy=DurationPolicy(mode="fixed", seconds=FRAME_COUNT / FPS),
                character_ids=(character.character_id,),
                continuity_constraints=(
                    "same exact traveler identity and wardrobe",
                    "rightward axis",
                    "stable 7:4 medium side-profile framing",
                    "continuous action phase and camera velocity",
                ),
                visual_strategy=VisualStrategy.STATIC_IMAGE,
                required_asset_roles=(
                    AssetRoleRequirement(
                        role="approved_endpoint",
                        asset_ids=(asset.asset_id,),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
                review_policy=shot_review_policy(),
            )
        )
        shot_receipts.append(receipt)
        shot_payloads.append(payload)
        shot_assets.append(asset)
        shots.append(shot)

    storyboard = seal_artifact(
        Storyboard(
            artifact_id="storyboard-rainy-station-continuity",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="authoring-rainy-station-storyboard-v1",
            source_provenance=provenance,
            beats=(
                StoryboardBeat(
                    beat_id="platform-walk",
                    scene_id=scene.scene_id,
                    shot_ids=tuple(item.shot_id for item in shots),
                    narrative_intent="Preserve one coherent rightward walk through a final stop.",
                ),
            ),
        )
    )
    refs = ProjectArtifactRefs(
        brief=_reference(brief, "creative/brief.yaml"),
        story=_reference(story, "creative/story.yaml"),
        characters=(_reference(character, "creative/characters/traveler.yaml"),),
        scenes=(_reference(scene, "creative/scenes/rainy-station.yaml"),),
        storyboard=_reference(storyboard, "creative/storyboard.yaml"),
        shots=tuple(
            _reference(item, f"creative/shots/rainy-station-{ordinal}.yaml")
            for ordinal, item in enumerate(shots, 1)
        ),
    )
    project = seal_artifact(
        ProductionProject(
            artifact_id="project-rainy-station-continuity",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="authoring-rainy-station-project-v1",
            source_provenance=provenance,
            project_id="rainy-station-continuity-p0",
            title="Rainy Station Continuity P0",
            default_language="en",
            delivery_profile=DeliveryProfile(
                width=TARGET_WIDTH,
                height=TARGET_HEIGHT,
                fps=FPS,
            ),
            renderer_policy=RendererPolicy(),
            artifacts=refs,
        )
    )
    registry = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(character_asset, scene_asset, *shot_assets),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )

    artifact_payloads = {
        Path("creative/brief.yaml"): _canonical_yaml_bytes(brief),
        Path("creative/story.yaml"): _canonical_yaml_bytes(story),
        Path("creative/characters/traveler.yaml"): _canonical_yaml_bytes(character),
        Path("creative/scenes/rainy-station.yaml"): _canonical_yaml_bytes(scene),
        Path("creative/storyboard.yaml"): _canonical_yaml_bytes(storyboard),
        **{
            Path(f"creative/shots/rainy-station-{ordinal}.yaml"): _canonical_yaml_bytes(shot)
            for ordinal, shot in enumerate(shots, 1)
        },
    }
    all_receipts = (character_receipt, scene_receipt, *shot_receipts)
    all_payloads = (character_bytes, scene_bytes, *shot_payloads)
    for receipt, payload in zip(all_receipts, all_payloads, strict=True):
        asset = automated_browser_image_import_asset(receipt)
        artifact_payloads.setdefault(asset.artifact_path, payload)
        artifact_payloads[
            canonical_automated_browser_image_import_receipt_path(receipt.content_hash)
        ] = _canonical_json_bytes(receipt)
    return (
        project,
        registry,
        tuple(
            _artifact(path, payload)
            for path, payload in sorted(
                artifact_payloads.items(), key=lambda item: item[0].as_posix()
            )
        ),
        tuple(shots),
        character,
        scene,
        tuple(shot_assets),
        character_asset,
        scene_asset,
        tuple(shot_receipts),
    )


def shot_review_policy():
    from ai_video.production.models import ReviewPolicy

    return ReviewPolicy(
        required_checks=(
            "technical",
            "boundary",
            "identity",
            "motion",
            "human_full_speed_sequence",
            "p6_final_acceptance",
        )
    )


def _runtime_seals() -> tuple[RuntimeSeal, ...]:
    return (
        RuntimeSeal(
            name="comfyui",
            version="0.33.2+7cee3ceb1a35",
            content_hash=canonical_sha256(
                {"commit": "7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa"}
            ),
        ),
        RuntimeSeal(
            name="minimax-h3-audio-t8",
            version="1.36.2+977df788fcf8",
            content_hash=canonical_sha256(
                {"commit": "977df788fcf8b971dc3d0fc7d6baa79a0edfaf40"}
            ),
        ),
        RuntimeSeal(
            name="videohelpersuite",
            version="4ee72c065db2",
            content_hash=canonical_sha256(
                {"commit": "4ee72c065db22c9d96c2427954dc69e7b908444b"}
            ),
        ),
    )


def _qualification_inputs(
    *,
    shot_assets,
    shot_receipts,
    approved_at: str,
) -> tuple[P0QualificationInput, ...]:
    source_images = [
        {
            "candidate": f"A{ordinal}",
            "sha256": asset.sha256,
            "width": asset.width,
            "height": asset.height,
            "mode": "RGB",
            "prompt_fingerprint": receipt.prompt_fingerprint,
        }
        for ordinal, (asset, receipt) in enumerate(
            zip(shot_assets, shot_receipts, strict=True), 1
        )
    ]
    inventory = P0QualificationInput.create(
        input_kind="inventory",
        input_id="local-t8-rainy-station-inventory-20260823-v1",
        payload={
            "observed_at": "2026-08-23",
            "comfyui": {
                "version": "0.33.2",
                "commit": "7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa",
            },
            "t8_plugin": {
                "version": "1.36.2",
                "commit": "977df788fcf8b971dc3d0fc7d6baa79a0edfaf40",
            },
            "videohelpersuite_commit": "4ee72c065db22c9d96c2427954dc69e7b908444b",
            "components": [
                {"id": "stock-ref2va", "presence": "present", "size": 34038894550, "sha256": STOCK_REF2VA_SHA256},
                {"id": "pruned-fl2va", "presence": "present", "size": 20970379616, "sha256": PRUNED_FL2VA_SHA256},
                {"id": "pruned-ref2va", "presence": "present", "size": 20970379616, "sha256": PRUNED_REF2VA_SHA256},
                {"id": "hybrid-artifact-candidate-v1", "presence": "absent", "sha256": "none"},
                {"id": "qwen-clip", "presence": "present", "size": 15687142551, "sha256": TEXT_ENCODER_SHA256},
                {"id": "video-vae", "presence": "present", "size": 5207808496, "sha256": VIDEO_VAE_SHA256},
                {"id": "audio-vae", "presence": "present", "size": 605254808, "sha256": AUDIO_VAE_SHA256},
            ],
            "hybrid_artifact_present": False,
            "loopback_endpoint": "http://127.0.0.1:8188",
            "remote_provider_enabled": False,
            "cloud_fallback_enabled": False,
        },
    )
    prompt = (
        "For the target video, at 0.00 seconds into the target video, <Picture 1> "
        "(from [Shot 1]) is fully referenced as the exact first frame; the ending "
        "frame aligns with <Picture 2>; <Picture 3> fully defines identity and "
        "wardrobe; <Video 1> supplies the opening gait phase and "
        "parallel camera velocity.\n\n"
        "integrated_multimodal_description: [Shot 1] Live-action, photorealistic "
        "cinematic medium right-facing side-profile shot on the same rain-soaked "
        "railway platform at blue hour. The exact same lone adult East Asian woman "
        "with a short blunt black bob, mustard-yellow hooded raincoat, black trousers, "
        "black boots and the same red cross-body leather satchel walks steadily "
        "screen-right toward the clock. A chest-height 50mm-equivalent camera tracks "
        "parallel with small amplitude at slow constant speed, keeping a level horizon "
        "and stable body scale. She preserves the supplied gait phase, decelerates "
        "naturally, and arrives at the exact approved last-frame pose. Exactly one "
        "person; no cut, zoom, axis reversal, teleport, text, logo, wardrobe change or "
        "unmotivated camera movement.\n"
        "overall_soundscape: Steady rain strikes the platform roof and wet concrete. "
        "Measured boot footsteps and a small physical leather-satchel movement remain "
        "synchronized with the walk; distant station ambience stays restrained.\n"
        "non_diegetic_music: No non-diegetic music."
    )
    prompt = validate_h3_prompt_contract(prompt)
    calibration = P0QualificationInput.create(
        input_kind="calibration_fixture",
        input_id="rainy-station-c4-stock20-v1",
        payload={
            "source_images": source_images,
            "source_format": "PNG RGB",
            "source_aspect_ratio": "7:4",
            "source_dimensions": [SOURCE_WIDTH, SOURCE_HEIGHT],
            "target_canvas": [TARGET_WIDTH, TARGET_HEIGHT],
            "target_tensor_layout": "BHWC",
            "target_tensor_shape": [1, TARGET_HEIGHT, TARGET_WIDTH, 3],
            "target_tensor_dtype": "float32_normalized_0_to_1",
            "dimension_multiple": 32,
            "exact_scale_ratio": "64/79",
            "preprocessing": {
                "first_frame": "lanczos_crop_disabled_isotropic",
                "last_frame": "lanczos_center_crop_no_crop_at_exact_7_to_4",
                "reference": "match_area_round32_resolves_1344x768",
            },
            "task_type": "Hybrid",
            "role_mapping": {
                "first_frame": "conditioning.first_frame",
                "last_frame": "conditioning.last_frame",
                "reference": "ref_images.ref_image_0",
                "reference_video": "ref_videos.ref_video_0",
            },
            "ref_video_audios": [],
            "ref_audios": [],
            "prompt": prompt,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "frame_count": FRAME_COUNT,
            "fps": FPS,
            "steps": 20,
            "sampler": "dual_clock_euler",
            "scheduler": "native_flow",
            "turbo_lora": False,
            "output_container": "mp4",
            "output_crf": 17,
            "native_audio": True,
        },
    )
    rubric = P0QualificationInput.create(
        input_kind="rubric",
        input_id="rainy-station-continuity-rubric-v1",
        payload={
            "boundary": {
                "decoded_first_and_last_required": True,
                "ssim_minimum": 0.90,
                "psnr_db_minimum": 30.0,
                "perceptual_backend_missing": "NOT_EVALUATED_requires_exact_human_review",
            },
            "identity": {
                "dimensions": ["face", "hair", "wardrobe", "satchel", "body_scale"],
                "automatic_missing": "NOT_EVALUATED_requires_exact_human_review",
            },
            "motion": {
                "dimensions": [
                    "subject_direction_velocity",
                    "camera_direction_velocity",
                    "action_phase",
                    "entrance_exit",
                    "unexpected_stop_or_reentry",
                ],
                "single_frame_metric_sufficient": False,
            },
            "sequence": {
                "raw_full_speed_review_required": True,
                "crossfade_optical_flow_interpolation_retime_forbidden": True,
            },
            "verdict_owner": "P6",
            "human_evidence_required": True,
        },
    )
    effect_budget = P0QualificationInput.create(
        input_kind="effect_budget",
        input_id="rainy-station-local-one-submit-v1",
        payload={
            "provider": "loopback_local_comfyui",
            "submits_per_generation": 1,
            "retry": False,
            "fallback": False,
            "remote": False,
            "paid": False,
            "automatic_activation": False,
            "unknown_outcome": "explicit_recovery_only",
        },
    )
    human_freeze = P0QualificationInput.create(
        input_kind="human_freeze",
        input_id="rainy-station-a1-a4-human-freeze-v2",
        payload={
            "recorded_at": approved_at,
            "actor": "user-shot-continuity-owner",
            "approved_candidate_order": ["A1", "A2", "A3", "A4"],
            "candidate_sha256": [item["sha256"] for item in source_images],
            "approval_scope": "freeze_source_candidates_for_P0_only",
            "not_claimed": ["creative_PASS", "P6_PASS", "Final_Acceptance"],
            "limitations": [
                "A2 source metadata prompt says dark raincoat although the frozen output visibly retains the canonical mustard-yellow raincoat.",
                "GPT Image 2 emitted 1659x948; exact 7:4 geometry permits isotropic 64/79 preparation to the sealed 1344x768 T8 tensor canvas.",
            ],
        },
    )
    return inventory, calibration, rubric, effect_budget, human_freeze


def _stack(
    *,
    candidate_id: str,
    components: tuple[tuple[str, str, str, str], ...],
) -> GenerationExecutionStackIdentity:
    return GenerationExecutionStackIdentity.create(
        materialization_status="unmaterialized",
        candidate_id=candidate_id,
        contract_version="1",
        provider_kind="comfy-local-h3-t8",
        deployment_identity="loopback-127.0.0.1-8188",
        model_id="minimax-h3-t8-hybrid-stock20",
        capability_id="c4-native-boundary-motion-qualification-candidate",
        profile_hash="none",
        compiler_hash="none",
        workflow_hash="none",
        components=tuple(
            StackComponentIdentity(
                ordinal=ordinal,
                kind=kind,
                component_id=component_id,
                presence=presence,
                content_hash=content_hash,
            )
            for ordinal, (kind, component_id, presence, content_hash) in enumerate(
                components
            )
        ),
        sampler_identity="dual_clock_euler",
        scheduler_identity="native_flow",
        runtime_seals=_runtime_seals(),
        output_contract_hash=canonical_sha256(
            {
                "width": TARGET_WIDTH,
                "height": TARGET_HEIGHT,
                "frames": FRAME_COUNT,
                "fps": FPS,
                "container": "mp4",
                "crf": 17,
                "native_audio": True,
            }
        ),
    )


def _record_p0(
    *,
    root: Path,
    shot_assets,
    shot_receipts,
    approved_at: str,
):
    writer = ProductionStateCommitter(root)
    loaded = load_production_project(root / "project.yaml")
    upgraded = writer.upgrade_manifest_schema(
        "2.11", expected_manifest_revision=loaded.manifest.manifest_revision
    )
    loaded = load_production_project(root / "project.yaml")
    if loaded.manifest != upgraded:
        raise ValueError("Manifest 2.11 upgrade did not reopen exactly")

    inputs = _qualification_inputs(
        shot_assets=shot_assets,
        shot_receipts=shot_receipts,
        approved_at=approved_at,
    )
    by_kind = {item.input_kind: item for item in inputs}
    m0 = _stack(
        candidate_id="minimax-h3-t8-c4-motion-ref2va-stock20-v1",
        components=(
            ("checkpoint", "stock-ref2va", "present", STOCK_REF2VA_SHA256),
            ("artifact", "qwen-clip", "present", TEXT_ENCODER_SHA256),
            ("artifact", "video-vae", "present", VIDEO_VAE_SHA256),
            ("artifact", "audio-vae", "present", AUDIO_VAE_SHA256),
        ),
    )
    m1 = _stack(
        candidate_id="minimax-h3-t8-c4-motion-hybrid-stock20-v1",
        components=(
            ("checkpoint", "pruned-fl2va", "present", PRUNED_FL2VA_SHA256),
            ("checkpoint", "pruned-ref2va", "present", PRUNED_REF2VA_SHA256),
            (
                "artifact",
                "hybrid-artifact-candidate-v1",
                "absent",
                "none",
            ),
            ("artifact", "qwen-clip", "present", TEXT_ENCODER_SHA256),
            ("artifact", "video-vae", "present", VIDEO_VAE_SHA256),
            ("artifact", "audio-vae", "present", AUDIO_VAE_SHA256),
        ),
    )
    source_stack = load_shot_continuity_source_execution_sources(
        artifact_root=REPO_ROOT,
    ).initial_stack
    shot_identities = tuple(
        CreativeArtifactIdentity(
            artifact_id=shot.artifact_id,
            revision=shot.revision,
            content_hash=shot.content_hash,
        )
        for shot in loaded.shots
    )
    character = loaded.characters[0]
    scene = loaded.scenes[0]
    policies = []
    for index, (source_shot, target) in enumerate(
        zip(shot_identities, shot_identities[1:])
    ):
        terminal_hash = canonical_sha256(
            {"derivation": "exact-terminal-frame/1", "source_shot": source_shot.model_dump(mode="json")}
        )
        motion_tail_hash = canonical_sha256(
            {"derivation": "exact-motion-tail/1", "source_shot": source_shot.model_dump(mode="json")}
        )
        endpoint_asset = shot_assets[index + 1]
        endpoint_receipt = shot_receipts[index + 1]
        anchors = (
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.FIRST_FRAME,
                source_kind="planned_derivation",
                source_identity=f"{source_shot.artifact_id}:terminal-frame",
                content_hash=terminal_hash,
                evidence_fingerprint=canonical_sha256(
                    {"kind": "terminal", "source": source_shot.content_hash}
                ),
            ),
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.LAST_FRAME,
                source_kind="registered_asset",
                source_identity=endpoint_asset.asset_id,
                content_hash=endpoint_asset.sha256,
                evidence_fingerprint=endpoint_receipt.content_hash,
                materialization_receipt_id=endpoint_receipt.content_hash,
            ),
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.REFERENCE,
                source_kind="registered_asset",
                source_identity=loaded.registry.assets[0].asset_id,
                content_hash=loaded.registry.assets[0].sha256,
                evidence_fingerprint=loaded.registry.assets[0].creation_receipt_id,
                materialization_receipt_id=loaded.registry.assets[0].creation_receipt_id,
            ),
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.REFERENCE_VIDEO,
                source_kind="planned_derivation",
                source_identity=f"{source_shot.artifact_id}:motion-tail",
                content_hash=motion_tail_hash,
                evidence_fingerprint=canonical_sha256(
                    {"kind": "motion-tail", "source": source_shot.content_hash}
                ),
            ),
        )
        policies.append(
            ContinuityTransitionPolicy.create(
                policy_id=f"rainy-station-edge-{index + 1}-{index + 2}",
                project=loaded.manifest.active_project,
                registry=loaded.manifest.active_registry,
                source_shot=source_shot,
                target_shot=target,
                boundary_kind=BoundaryKind.HARD_CUT,
                continuity_obligation=ContinuityObligation.FULL_CONTINUITY,
                take_id=None,
                source_execution_stack_hash=source_stack.execution_stack_hash,
                destination_execution_stack_hash=m0.execution_stack_hash,
                continuity_grade="c4_native_boundary_motion",
                required_carryover_dimensions=(
                    "action_phase",
                    "camera_velocity",
                    "identity",
                    "screen_axis",
                    "wardrobe",
                ),
                anchors=anchors,
                qa_policy_hash=by_kind["rubric"].content_hash,
                authoring_evidence_hash=by_kind["human_freeze"].content_hash,
            )
        )
    policies_tuple = tuple(policies)
    validation_set = RealShotValidationSet.create(
        validation_set_id="rainy-station-four-shot-v1",
        project=loaded.manifest.active_project,
        registry=loaded.manifest.active_registry,
        character=CreativeArtifactIdentity(
            artifact_id=character.artifact_id,
            revision=character.revision,
            content_hash=character.content_hash,
        ),
        scene=CreativeArtifactIdentity(
            artifact_id=scene.artifact_id,
            revision=scene.revision,
            content_hash=scene.content_hash,
        ),
        shots=shot_identities,
        edges=(
            ValidationEdgeBinding(
                source_shot_id=shot_identities[0].artifact_id,
                target_shot_id=shot_identities[1].artifact_id,
                policy_hash=policies_tuple[0].policy_hash,
                motion_coverage=(MotionCoverage.SUBJECT_MOTION,),
            ),
            ValidationEdgeBinding(
                source_shot_id=shot_identities[1].artifact_id,
                target_shot_id=shot_identities[2].artifact_id,
                policy_hash=policies_tuple[1].policy_hash,
                motion_coverage=(MotionCoverage.CAMERA_MOTION,),
            ),
            ValidationEdgeBinding(
                source_shot_id=shot_identities[2].artifact_id,
                target_shot_id=shot_identities[3].artifact_id,
                policy_hash=policies_tuple[2].policy_hash,
                motion_coverage=(MotionCoverage.CAMERA_MOTION, MotionCoverage.SUBJECT_MOTION),
            ),
        ),
        human_freeze_evidence_hash=by_kind["human_freeze"].content_hash,
        rubric_hash=by_kind["rubric"].content_hash,
    )
    receipt = P0QualificationPreparedReceipt.create(
        receipt_id="rainy-station-p0-qualification-prepared-v1",
        project=loaded.manifest.active_project,
        registry=loaded.manifest.active_registry,
        inventory_receipt_hash=by_kind["inventory"].content_hash,
        calibration_fixture_hash=by_kind["calibration_fixture"].content_hash,
        rubric_hash=by_kind["rubric"].content_hash,
        effect_budget_hash=by_kind["effect_budget"].content_hash,
        human_freeze_evidence_hash=by_kind["human_freeze"].content_hash,
        validation_set_hash=validation_set.content_hash,
        policy_hashes=tuple(sorted(item.policy_hash for item in policies_tuple)),
        candidate_stacks=(
            CandidateStackBinding(label="m0", execution_stack_hash=m0.execution_stack_hash),
            CandidateStackBinding(label="m1", execution_stack_hash=m1.execution_stack_hash),
        ),
        limitations=(
            "No video media has been generated.",
            "No candidate winner or active capability has been selected.",
            "M1 Hybrid artifact is absent and the M1 stack remains unmaterialized.",
            "Candidate profile, compiler, and workflow identities are canonical empty fields until a real qualification execution stack is materialized and resealed.",
            "No creative PASS, P6 verdict, Final Acceptance, push, or release is claimed.",
        ),
    )
    manifest = writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        source_stacks=(source_stack,),
        policies=policies_tuple,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="rainy-station-p0-qualification-prepared-v1",
    )
    reopened = writer.reopen_p0_qualification_prepared()
    if reopened != (receipt, (m0, m1), policies_tuple, validation_set, inputs):
        raise ValueError("P0 qualification bundle did not reopen exactly")
    if writer.reopen_p0_qualification_source_stacks() != (source_stack,):
        raise ValueError("P0 source execution stack did not reopen exactly")
    return manifest, receipt, validation_set, source_stack, m0, m1, inputs


def prepare(args: argparse.Namespace) -> dict[str, object]:
    root = args.root.resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"target root must be absent or empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    image_paths = tuple(path.resolve(strict=True) for path in (args.a1, args.a2, args.a3, args.a4))
    project, registry, artifacts, _, _, _, shot_assets, _, _, shot_receipts = _build_project(
        image_paths=image_paths,
        approved_at=args.approved_at,
        imported_at=args.imported_at,
    )
    writer = ProductionStateCommitter(root)
    writer.bootstrap_initial_state(
        attempt_id="rainy-station-bootstrap-v1",
        project=project,
        registry=registry,
        artifacts=artifacts,
    )
    manifest, receipt, validation_set, source, m0, m1, inputs = _record_p0(
        root=root,
        shot_assets=shot_assets,
        shot_receipts=shot_receipts,
        approved_at=args.approved_at,
    )
    return {
        "root": root.as_posix(),
        "manifest_schema_version": manifest.schema_version,
        "manifest_revision": manifest.manifest_revision,
        "p0_status": receipt.status,
        "p0_receipt_hash": receipt.content_hash,
        "validation_set_hash": validation_set.content_hash,
        "source_execution_stack_hash": source.execution_stack_hash,
        "m0_execution_stack_hash": m0.execution_stack_hash,
        "m1_execution_stack_hash": m1.execution_stack_hash,
        "qualification_input_hashes": {
            item.input_kind: item.content_hash for item in inputs
        },
        "claims": {
            "video_generated": False,
            "winner_selected": False,
            "p6_pass": False,
            "final_acceptance": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--a1", type=Path, required=True)
    parser.add_argument("--a2", type=Path, required=True)
    parser.add_argument("--a3", type=Path, required=True)
    parser.add_argument("--a4", type=Path, required=True)
    parser.add_argument("--approved-at", required=True)
    parser.add_argument("--imported-at", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    for value in (args.approved_at, args.imported_at):
        timestamp = datetime.fromisoformat(value)
        if timestamp.tzinfo is None:
            raise ValueError("timestamps require explicit offsets")
    print(json.dumps(prepare(args), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
