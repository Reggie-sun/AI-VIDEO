from __future__ import annotations

from typing import Any, Literal

from ai_video.production.video import VideoGenerationMode, VideoOutputRequirement
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import (
    AudioNeed,
    GenerationMode,
    OutputGeometryPolicy,
    ProviderNeutralVideoRequirement,
    SemanticReferenceRole,
)


def requirement_mode(mode: GenerationMode) -> VideoGenerationMode | None:
    return {
        GenerationMode.TEXT_TO_VIDEO: VideoGenerationMode.TEXT_TO_VIDEO,
        GenerationMode.IMAGE_TO_VIDEO: VideoGenerationMode.IMAGE_TO_VIDEO,
        GenerationMode.FIRST_LAST_FRAME_VIDEO: VideoGenerationMode.IMAGE_TO_VIDEO,
        GenerationMode.REFERENCE_TO_VIDEO: VideoGenerationMode.REFERENCE_TO_VIDEO,
        GenerationMode.VIDEO_EDIT: VideoGenerationMode.VIDEO_EDIT,
        GenerationMode.VIDEO_EXTEND: VideoGenerationMode.VIDEO_EXTEND,
    }.get(mode)


def effective_policy_for_requirement(
    requirement: ProviderNeutralVideoRequirement,
    policy: Any,
) -> Any:
    need = requirement.capability_need
    return policy.model_copy(
        update={
            "local_resources_available": bool(
                policy.local_resources_available and need.accepts_local_execution
            ),
            "remote_authorized": bool(
                policy.remote_authorized and need.accepts_remote_execution
            ),
            "budget_authorized": bool(
                policy.budget_authorized and need.accepts_remote_execution
            ),
        }
    )


def native_binding_role(
    role: SemanticReferenceRole,
) -> Literal[
    "first_frame",
    "last_frame",
    "reference",
    "reference_video",
    "reference_audio",
]:
    return {
        SemanticReferenceRole.FIRST_FRAME: "first_frame",
        SemanticReferenceRole.CONTINUITY_TERMINAL: "first_frame",
        SemanticReferenceRole.LAST_FRAME: "last_frame",
        SemanticReferenceRole.IDENTITY: "reference",
        SemanticReferenceRole.SCENE: "reference",
        SemanticReferenceRole.VIDEO_REFERENCE: "reference_video",
        SemanticReferenceRole.AUDIO_REFERENCE: "reference_audio",
    }[role]


def context_asset_role(role: SemanticReferenceRole) -> str:
    return {
        SemanticReferenceRole.FIRST_FRAME: "first_frame",
        SemanticReferenceRole.CONTINUITY_TERMINAL: "continuity_terminal",
        SemanticReferenceRole.LAST_FRAME: "last_frame",
        SemanticReferenceRole.IDENTITY: "character_reference",
        SemanticReferenceRole.SCENE: "scene_reference",
        SemanticReferenceRole.VIDEO_REFERENCE: "reference_video",
        SemanticReferenceRole.AUDIO_REFERENCE: "reference_audio",
    }[role]


def requirement_bindings(
    requirement: ProviderNeutralVideoRequirement,
    context: Any,
) -> tuple[tuple[str, ...], tuple[Any, ...]] | None:
    pool = (
        *context.canonical_character_references,
        *(
            (context.canonical_scene_reference,)
            if context.canonical_scene_reference
            else ()
        ),
        *((context.shot_keyframe,) if context.shot_keyframe else ()),
        *((context.upstream_terminal,) if context.upstream_terminal else ()),
        *((context.last_frame,) if context.last_frame else ()),
        *context.reference_videos,
        *context.reference_audios,
    )
    roles: list[str] = []
    assets: list[Any] = []
    for evidence in requirement.asset_evidence:
        matches = tuple(
            asset
            for asset in pool
            if asset.role == context_asset_role(evidence.role)
            and asset.asset_id == evidence.asset_id
            and asset.asset_sha256 == evidence.asset_sha256
        )
        if len(matches) != 1:
            return None
        roles.append(native_binding_role(evidence.role))
        assets.append(matches[0])
    return tuple(roles), tuple(assets)


def requirement_output_matches(
    requirement: ProviderNeutralVideoRequirement,
    output: VideoOutputRequirement | VideoFlexibleOutputRequirement,
) -> bool:
    need = requirement.output_need
    selected_timing_mode = getattr(output, "timing_mode", "exact_seconds")
    expected_timing_modes = {
        "fixed": {"exact_seconds"},
        "content_driven": {"exact_seconds", "provider_selected"},
        "voice_driven": {"exact_seconds", "provider_selected"},
        "provider_selected": {"provider_selected"},
        "frame_count": {"frame_count"},
    }[need.timing_mode]
    if selected_timing_mode not in expected_timing_modes:
        return False
    if need.container_mime is not None and need.container_mime != output.mime_type:
        return False
    if need.duration_seconds is not None:
        selected_duration = getattr(output, "duration_seconds", None)
        if selected_duration is None or selected_duration != need.duration_seconds:
            return False
    if need.frame_count is not None and (
        getattr(output, "frame_count", None) != need.frame_count
    ):
        return False
    if need.fps is not None and getattr(output, "fps", None) != need.fps:
        return False
    selected_geometry = getattr(output, "dimension_mode", "exact")
    if selected_geometry != need.geometry_policy.value:
        return False
    if need.geometry_policy is OutputGeometryPolicy.EXACT:
        if need.width is not None and getattr(output, "width", None) != need.width:
            return False
        if need.height is not None and getattr(output, "height", None) != need.height:
            return False
    if need.aspect_ratio is not None:
        selected_ratio = getattr(output, "ratio", None)
        if selected_ratio is not None:
            if selected_ratio != need.aspect_ratio:
                return False
        elif not _exact_dimensions_match_ratio(output, need.aspect_ratio):
            return False
    native_audio = getattr(output, "native_audio", None)
    if requirement.audio_need is AudioNeed.REQUIRED and native_audio is not True:
        return False
    if requirement.audio_need is AudioNeed.FORBIDDEN and native_audio is not False:
        return False
    return True


def _exact_dimensions_match_ratio(
    output: VideoOutputRequirement | VideoFlexibleOutputRequirement,
    ratio: str,
) -> bool:
    width = getattr(output, "width", None)
    height = getattr(output, "height", None)
    try:
        ratio_width_text, ratio_height_text = ratio.split(":", maxsplit=1)
        ratio_width = int(ratio_width_text)
        ratio_height = int(ratio_height_text)
    except (AttributeError, TypeError, ValueError):
        return False
    return bool(
        width is not None
        and height is not None
        and ratio_width > 0
        and ratio_height > 0
        and width * ratio_height == height * ratio_width
    )


def validate_requirement_asset_lineage(
    requirement: ProviderNeutralVideoRequirement,
    decision: Any,
) -> None:
    evidence = {
        (native_binding_role(item.role), item.asset_id, item.asset_sha256)
        for item in requirement.asset_evidence
    }
    selected = {
        (role, item.asset_id, item.asset_sha256)
        for role, item in zip(
            decision.required_binding_roles,
            decision.input_assets,
            strict=True,
        )
    }
    if selected != evidence:
        raise ValueError(
            "provider-bound assets do not match exact requirement evidence"
        )


def validate_provider_bound_projection(bound: Any) -> None:
    if len(bound.binding_roles) != len(bound.input_assets):
        raise ValueError("provider-bound roles and assets must have equal length")
    compatible_source_roles = {
        "first_frame": {"first_frame", "continuity_terminal"},
        "last_frame": {"last_frame"},
        "reference": {"character_reference", "scene_reference"},
        "reference_video": {"reference_video"},
        "reference_audio": {"reference_audio"},
    }
    for role, asset in zip(bound.binding_roles, bound.input_assets, strict=True):
        if asset.role not in compatible_source_roles[role]:
            raise ValueError("provider-bound role does not match source asset semantics")
        if role in {"first_frame", "last_frame", "reference"} and any(
            value is None for value in (asset.size_bytes, asset.width, asset.height)
        ):
            raise ValueError("provider-bound image asset lacks measured metadata")
    required_inputs = {asset.asset_id for asset in bound.input_assets}
    if not required_inputs.issubset(bound.lifecycle.input_artifact_ids):
        raise ValueError(
            "provider-bound lifecycle inputs must include every selected asset"
        )
    if bound.lifecycle.continuity_binding is not None:
        terminal_id = (
            bound.lifecycle.continuity_binding.terminal_frame.extracted_asset_id
        )
        if not bound.input_assets or bound.input_assets[0].asset_id != terminal_id:
            raise ValueError(
                "continuity lifecycle binding must match the selected first frame"
            )
    if bound.lifecycle.hard_cut_keyframe_binding is not None:
        keyframe_id = bound.lifecycle.hard_cut_keyframe_binding.keyframe_asset_id
        if not bound.input_assets or bound.input_assets[0].asset_id != keyframe_id:
            raise ValueError(
                "hard-cut lifecycle binding must match the selected first frame"
            )


def as_capability_blocked(
    decision: Any,
    *,
    reason_code: Any,
    outcome: Any,
    rationale: str,
) -> Any:
    values = {
        field_name: getattr(decision, field_name)
        for field_name in type(decision).model_fields
        if field_name not in {"semantic_routing_hash", "audit_decision_hash"}
    }
    values.update(
        selected_mode=None,
        reason_codes=(reason_code,),
        rationale=rationale,
        outcome=outcome,
    )
    return type(decision).create(**values)
