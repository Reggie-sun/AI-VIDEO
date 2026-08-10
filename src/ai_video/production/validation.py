from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    AssetRecord,
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    Shot,
    VisualStrategy,
)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        retryable=False,
    )


def _role_bindings(shot: Shot) -> dict[str, AssetRoleRequirement]:
    roles = [item.role for item in shot.required_asset_roles]
    if len(roles) != len(set(roles)):
        raise _invalid(f"Shot {shot.shot_id} has duplicate required asset roles.")
    for item in shot.required_asset_roles:
        if len(item.asset_ids) != len(set(item.asset_ids)):
            raise _invalid(f"Shot {shot.shot_id} role {item.role} has duplicate asset IDs.")
    return {item.role: item for item in shot.required_asset_roles}


def _bound_assets(
    shot: Shot,
    assets_by_id: dict[str, AssetRecord],
) -> tuple[dict[str, AssetRoleRequirement], dict[str, AssetRecord]]:
    roles = _role_bindings(shot)
    bound: dict[str, AssetRecord] = {}
    for role in roles.values():
        for asset_id in role.asset_ids:
            asset = assets_by_id.get(asset_id)
            if asset is None:
                raise _invalid(
                    f"Shot {shot.shot_id} role {role.role} references unknown asset {asset_id}."
                )
            if asset.asset_type not in role.allowed_asset_types:
                raise _invalid(
                    f"Shot {shot.shot_id} role {role.role} rejects asset type "
                    f"{asset.asset_type.value}."
                )
            bound[asset_id] = asset
    return roles, bound


def _has_type(bound: dict[str, AssetRecord], asset_type: AssetType) -> bool:
    return any(asset.asset_type is asset_type for asset in bound.values())


_MOTION_NUMERIC_PARAMETERS = {
    "pan": ("x", "y"),
    "zoom": ("scale",),
    "parallax": ("depth", "offset"),
    "reveal": ("duration_seconds", "progress"),
    "layered": ("duration_seconds", "offset"),
    "animate": ("duration_seconds",),
    "particles": ("count",),
    "transition": ("duration_seconds",),
}


def _validate_deterministic_motion(shot: Shot) -> None:
    for directive in shot.motion_directives:
        parameter_names = _MOTION_NUMERIC_PARAMETERS[directive.kind]
        has_required_number = any(
            isinstance(directive.parameters.get(name), (int, float))
            and not isinstance(directive.parameters.get(name), bool)
            and math.isfinite(directive.parameters[name])
            for name in parameter_names
        )
        if not has_required_number:
            raise _invalid(
                f"Shot {shot.shot_id} {directive.kind} motion directive requires a "
                f"deterministic numeric parameter named {' or '.join(parameter_names)}."
            )


def validate_shot_strategy(
    shot: Shot,
    assets_by_id: dict[str, AssetRecord],
) -> None:
    roles, bound = _bound_assets(shot, assets_by_id)
    if shot.visual_strategy is VisualStrategy.STATIC_IMAGE:
        if not _has_type(bound, AssetType.IMAGE):
            raise _invalid(f"Shot {shot.shot_id} static_image requires an image role.")
        if shot.motion_directives:
            raise _invalid(
                f"Shot {shot.shot_id} static_image must not define motion_directives."
            )
    if shot.visual_strategy is VisualStrategy.IMAGE_MOTION:
        if not _has_type(bound, AssetType.IMAGE):
            raise _invalid(f"Shot {shot.shot_id} image_motion requires an image role.")
        if not shot.motion_directives:
            raise _invalid(f"Shot {shot.shot_id} image_motion requires motion_directives.")
        _validate_deterministic_motion(shot)
    if shot.visual_strategy is VisualStrategy.MOTION_GRAPHICS:
        if not any(
            _has_type(bound, asset_type)
            for asset_type in (AssetType.IMAGE, AssetType.COMPOSITION_SOURCE)
        ):
            raise _invalid(
                f"Shot {shot.shot_id} motion_graphics requires an image or "
                "composition_source role."
            )
        if not shot.motion_directives:
            raise _invalid(
                f"Shot {shot.shot_id} motion_graphics requires motion_directives."
            )
        _validate_deterministic_motion(shot)
    if shot.visual_strategy is VisualStrategy.GENERATED_VIDEO:
        generated_videos = [
            asset
            for asset in bound.values()
            if asset.asset_type is AssetType.VIDEO
            and asset.source_kind is AssetSourceKind.GENERATED
        ]
        if not generated_videos:
            raise _invalid(
                f"Shot {shot.shot_id} generated_video requires a generated video role."
            )
        if not shot.generated_video_rationale or not shot.generated_video_rationale.strip():
            raise _invalid(f"Shot {shot.shot_id} generated_video requires a rationale.")
    if shot.visual_strategy is VisualStrategy.EXISTING_VIDEO:
        imported_videos = [
            asset
            for asset in bound.values()
            if asset.asset_type is AssetType.VIDEO
            and asset.source_kind is AssetSourceKind.IMPORTED
        ]
        if not imported_videos:
            raise _invalid(
                f"Shot {shot.shot_id} existing_video requires an imported video role."
            )
    if shot.visual_strategy is VisualStrategy.HYBRID:
        if len(shot.hybrid_layers) < 2:
            raise _invalid(f"Shot {shot.shot_id} hybrid requires at least two layers.")
        layer_roles = [layer.role for layer in shot.hybrid_layers]
        if len(layer_roles) != len(set(layer_roles)):
            raise _invalid(f"Shot {shot.shot_id} hybrid layer roles must be unique.")
        if len({layer.asset_id for layer in shot.hybrid_layers}) < 2:
            raise _invalid(f"Shot {shot.shot_id} hybrid requires two source assets.")
        for layer in shot.hybrid_layers:
            role = roles.get(layer.asset_role)
            if role is None:
                raise _invalid(
                    f"Shot {shot.shot_id} hybrid references undeclared role {layer.asset_role}."
                )
            if layer.asset_id not in role.asset_ids:
                raise _invalid(
                    f"Shot {shot.shot_id} hybrid source {layer.asset_id} is not bound "
                    f"to role {layer.asset_role}."
                )
        required_layer_bindings = {
            (role.role, asset_id)
            for role in roles.values()
            for asset_id in role.asset_ids
        }
        actual_layer_bindings = {
            (layer.asset_role, layer.asset_id) for layer in shot.hybrid_layers
        }
        missing_layer_bindings = sorted(required_layer_bindings - actual_layer_bindings)
        if missing_layer_bindings:
            formatted = ", ".join(
                f"{role}={asset_id}" for role, asset_id in missing_layer_bindings
            )
            raise _invalid(
                f"Shot {shot.shot_id} hybrid is missing layers for bound sources: "
                f"{formatted}"
            )


def _unique(values: Iterable[str], label: str) -> set[str]:
    counts = Counter(values)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    if duplicates:
        raise _invalid(f"duplicate {label}: {', '.join(duplicates)}")
    return set(counts)


def validate_project_references(bundle: LoadedProductionProject) -> None:
    character_ids = _unique(
        [item.character_id for item in bundle.characters], "character_id"
    )
    scene_ids = _unique([item.scene_id for item in bundle.scenes], "scene_id")
    shot_ids = _unique([item.shot_id for item in bundle.shots], "shot_id")
    beat_ids = _unique([item.beat_id for item in bundle.storyboard.beats], "beat_id")
    asset_ids = _unique([item.asset_id for item in bundle.registry.assets], "asset_id")
    artifact_ids = _unique(
        [
            bundle.project.artifact_id,
            bundle.brief.artifact_id,
            bundle.story.artifact_id,
            bundle.storyboard.artifact_id,
            *(item.artifact_id for item in bundle.characters),
            *(item.artifact_id for item in bundle.scenes),
            *(item.artifact_id for item in bundle.shots),
        ],
        "artifact_id",
    )
    known_inputs = artifact_ids | asset_ids | character_ids | scene_ids | shot_ids | beat_ids
    assets_by_id = {item.asset_id: item for item in bundle.registry.assets}
    shots_by_id = {item.shot_id: item for item in bundle.shots}

    for asset in bundle.registry.assets:
        missing_inputs = sorted(set(asset.input_artifact_ids) - known_inputs)
        if missing_inputs:
            raise _invalid(
                f"Asset {asset.asset_id} references unknown input(s): "
                f"{', '.join(missing_inputs)}"
            )
        metadata = asset.caption_metadata
        if metadata is None:
            continue
        source = assets_by_id.get(metadata.source_audio_asset_id)
        if source is None:
            raise _invalid(
                f"Caption asset {asset.asset_id} references unknown source audio."
            )
        if source.asset_type not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}:
            raise _invalid(f"Caption asset {asset.asset_id} source audio type is invalid.")
        source_metadata = source.audio_metadata
        if source_metadata is None:
            raise _invalid(f"Caption asset {asset.asset_id} source audio metadata is missing.")
        if source.sha256 != metadata.source_audio_sha256:
            raise _invalid(f"Caption asset {asset.asset_id} source audio hash is invalid.")
        if source_metadata.script_hash != metadata.script_hash:
            raise _invalid(f"Caption asset {asset.asset_id} script hash is invalid.")
        if (
            asset.input_artifact_ids != (source.asset_id,)
            or asset.input_fingerprint != source.sha256
        ):
            raise _invalid(f"Caption asset {asset.asset_id} source linkage is invalid.")

    for scene in bundle.scenes:
        missing_characters = sorted(set(scene.participant_ids) - character_ids)
        missing_assets = sorted(set(scene.visual_reference_asset_ids) - asset_ids)
        if missing_characters or missing_assets:
            raise _invalid(
                f"Scene {scene.scene_id} has unknown references: "
                f"{', '.join(missing_characters + missing_assets)}"
            )
    for character in bundle.characters:
        missing_assets = sorted(set(character.reference_asset_ids) - asset_ids)
        if missing_assets:
            raise _invalid(
                f"Character {character.character_id} references unknown asset(s): "
                f"{', '.join(missing_assets)}"
            )

    for shot in bundle.shots:
        if shot.scene_id not in scene_ids:
            raise _invalid(f"Shot {shot.shot_id} references unknown scene {shot.scene_id}.")
        if shot.storyboard_beat_id not in beat_ids:
            raise _invalid(
                f"Shot {shot.shot_id} references unknown beat {shot.storyboard_beat_id}."
            )
        missing_characters = sorted(set(shot.character_ids) - character_ids)
        if missing_characters:
            raise _invalid(
                f"Shot {shot.shot_id} references unknown character(s): "
                f"{', '.join(missing_characters)}"
            )
        validate_shot_strategy(shot, assets_by_id)

    storyboard_membership: dict[str, str] = {}
    for beat in bundle.storyboard.beats:
        if beat.scene_id not in scene_ids:
            raise _invalid(f"Storyboard beat {beat.beat_id} references unknown scene.")
        for shot_id in beat.shot_ids:
            if shot_id not in shot_ids:
                raise _invalid(
                    f"Storyboard beat {beat.beat_id} references unknown shot {shot_id}."
                )
            if shot_id in storyboard_membership:
                raise _invalid(f"Shot {shot_id} appears in multiple storyboard beats.")
            storyboard_membership[shot_id] = beat.beat_id
            if shots_by_id[shot_id].scene_id != beat.scene_id:
                raise _invalid(
                    f"Storyboard beat {beat.beat_id} scene does not match Shot {shot_id}."
                )
    for shot in bundle.shots:
        if storyboard_membership.get(shot.shot_id) != shot.storyboard_beat_id:
            raise _invalid(f"Shot {shot.shot_id} storyboard membership does not match.")
