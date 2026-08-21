from __future__ import annotations

from ai_video.planning._planner_models import (
    AssetRole,
    AvailableAsset,
    RequiredAssetRole,
    ReviewDecisionProjection,
    VideoPlanningRequest,
)
from ai_video.production.models import AssetType


_FINAL_VISUAL_ROLE = "final_visual"


def _content_binding_matches(
    request: VideoPlanningRequest,
    asset: AvailableAsset,
    expected_content_hash: str | None,
) -> bool:
    if request.planning_contract_version == "video-planner/2":
        return True
    return (
        expected_content_hash is not None
        and asset.canonical_owner_content_hash == expected_content_hash
    )


def current_review(
    request: VideoPlanningRequest,
) -> ReviewDecisionProjection | None:
    review = request.review_decision
    if review is None:
        return None
    if (
        review.target_shot_id != request.target_shot.shot_id
        or review.target_shot_content_hash != request.target_shot.content_hash
    ):
        return None
    return review


def _has_exact_image_binding(
    request: VideoPlanningRequest,
    asset_id: str,
) -> bool:
    return any(
        requirement.role == _FINAL_VISUAL_ROLE
        and asset_id in requirement.asset_ids
        and AssetType.IMAGE in requirement.allowed_asset_types
        for requirement in request.target_shot.required_asset_roles
    )


def _is_shot_bound_final_visual(
    request: VideoPlanningRequest,
    asset: AvailableAsset,
    *,
    review: ReviewDecisionProjection | None,
) -> bool:
    if asset.canonical_owner_id != request.target_shot.shot_id:
        return False
    if not _content_binding_matches(
        request,
        asset,
        request.target_shot.content_hash,
    ):
        return False
    if not _has_exact_image_binding(request, asset.asset_id):
        return False
    if asset.role is AssetRole.APPROVED_KEYFRAME:
        return True
    return bool(
        asset.role is AssetRole.APPROVED_REUSABLE_PLATE
        and review is not None
        and review.allows_reusable_plate
        and review.rationale.strip()
    )


def asset_matches_role(
    request: VideoPlanningRequest,
    asset: AvailableAsset,
    role: AssetRole,
) -> bool:
    if asset.role is not role:
        return False
    if role is AssetRole.CHARACTER_REFERENCE:
        characters = {
            item.character_id: item
            for item in request.character_context
            if item.character_id in request.target_shot.character_ids
        }
        character = characters.get(asset.canonical_owner_id)
        return character is not None and _content_binding_matches(
            request,
            asset,
            character.content_hash,
        )
    if role is AssetRole.SCENE_REFERENCE:
        if request.scene_context.scene_id != request.target_shot.scene_id:
            return False
        return (
            asset.canonical_owner_id == request.target_shot.scene_id
            and _content_binding_matches(
                request,
                asset,
                request.scene_context.content_hash,
            )
        )
    if role is AssetRole.PREVIOUS_SHOT_TERMINAL:
        state = request.previous_shot_state
        terminal_id = state.has_terminal_frame_asset_id if state else None
        previous_shot_id = state.previous_shot_id if state else None
        return (
            terminal_id is not None
            and previous_shot_id is not None
            and asset.asset_id == terminal_id
            and asset.canonical_owner_id == previous_shot_id
            and _content_binding_matches(
                request,
                asset,
                state.previous_shot_content_hash if state else None,
            )
        )
    if role in {
        AssetRole.EXISTING_VIDEO,
        AssetRole.REFERENCE_AUDIO,
    }:
        selection = (
            request.generation_intent.media_reference_asset_ids
            if request.generation_intent is not None
            else ()
        )
        return not selection or asset.asset_id in selection
    if role is AssetRole.LAST_FRAME:
        return True
    return _is_shot_bound_final_visual(
        request,
        asset,
        review=current_review(request),
    )


def available_role(request: VideoPlanningRequest, role: AssetRole) -> bool:
    matches = tuple(
        asset
        for asset in request.available_assets
        if asset_matches_role(request, asset, role)
    )
    if role is AssetRole.CHARACTER_REFERENCE:
        target_characters = set(request.target_shot.character_ids)
        owners = tuple(asset.canonical_owner_id for asset in matches)
        return set(owners) == target_characters and len(owners) == len(
            target_characters
        )
    if role in {AssetRole.EXISTING_VIDEO, AssetRole.REFERENCE_AUDIO} and (
        request.generation_intent is not None
        and request.generation_intent.media_reference_asset_ids
    ):
        return bool(matches)
    return len(matches) == 1


def media_selection_is_complete(
    request: VideoPlanningRequest,
    required: tuple[RequiredAssetRole, ...],
) -> bool:
    projection = request.generation_intent
    selected_ids = (
        set(projection.media_reference_asset_ids) if projection is not None else set()
    )
    if not selected_ids:
        return True
    required_media_roles = {
        item.role
        for item in required
        if item.role in {AssetRole.EXISTING_VIDEO, AssetRole.REFERENCE_AUDIO}
    }
    selected_assets = tuple(
        asset for asset in request.available_assets if asset.asset_id in selected_ids
    )
    return bool(
        len(selected_assets) == len(selected_ids)
        and all(asset.role in required_media_roles for asset in selected_assets)
    )


def required_role_is_available(
    request: VideoPlanningRequest,
    requirement: RequiredAssetRole,
) -> bool:
    return available_role(request, requirement.role)


def required_role_readiness(
    request: VideoPlanningRequest,
    required: tuple[RequiredAssetRole, ...],
) -> tuple[tuple[AssetRole, ...], tuple[AssetRole, ...]]:
    incomplete_media = not media_selection_is_complete(request, required)
    ready: list[AssetRole] = []
    missing: list[AssetRole] = []
    for requirement in required:
        role = requirement.role
        role_ready = required_role_is_available(request, requirement)
        if incomplete_media and role in {
            AssetRole.EXISTING_VIDEO,
            AssetRole.REFERENCE_AUDIO,
        }:
            role_ready = False
        target = ready if role_ready else missing
        if role not in target:
            target.append(role)
    return tuple(ready), tuple(missing)
