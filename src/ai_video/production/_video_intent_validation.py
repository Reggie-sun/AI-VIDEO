from __future__ import annotations

import re
from typing import Protocol

from pydantic import ValidationError

from ai_video.production.video_transition import (
    CausalDimension,
    CausalEdgeSemantics,
    CausalTransitionMode,
    ContinuityTransitionPolicy,
)
from ai_video.production.video_requirement import (
    AudioNeed,
    ConditioningCompatibilityEvidence,
    ConditioningLane,
    CameraSubjectRelation,
    ContinuityMode,
    ContinuityStateKind,
    GenerationIntent,
    GenerationMode,
    ProviderNeutralVideoRequirement,
    SemanticReferenceRole,
)


_SECONDARY_CAMERA_MOTION = re.compile(
    r"\b(?:orbit|pan|tilt|dolly|truck|pedestal|crane|zoom)\b|"
    r"\b(?:push|pull)(?:es)?\s+(?:in|out)\b",
    flags=re.IGNORECASE,
)


class PreviousShotStateLike(Protocol):
    previous_shot_id: str | None
    previous_shot_content_hash: str | None
    previous_shot_artifact_id: str | None
    previous_shot_revision: int | None
    previous_generation_intent_hash: str | None


def validate_generation_intent_for_continuity(
    intent: GenerationIntent,
    *,
    audio_need: AudioNeed = AudioNeed.OPTIONAL,
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    if intent.open_state.kind is ContinuityStateKind.UNSPECIFIED:
        diagnostics.append("generation_intent.open_state")
    if intent.close_state.kind is ContinuityStateKind.UNSPECIFIED:
        diagnostics.append("generation_intent.close_state")
    if intent.subject_action.start_state == "unspecified":
        diagnostics.append("generation_intent.subject_action.start_state")
    if intent.subject_action.progression == "unspecified":
        diagnostics.append("generation_intent.subject_action.progression")
    endpoint = intent.subject_action.endpoint
    if not any((endpoint.state_ref, endpoint.state_text, endpoint.state_hash)):
        diagnostics.append("generation_intent.subject_action.endpoint")
    if intent.space_continuity.screen_direction == "unspecified":
        diagnostics.append("generation_intent.space_continuity.screen_direction")
    if intent.axis_continuity.camera_axis == "unspecified":
        diagnostics.append("generation_intent.axis_continuity.camera_axis")
    if intent.axis_continuity.framing_continuity == "unspecified":
        diagnostics.append("generation_intent.axis_continuity.framing_continuity")
    for field in (
        "performance_intent",
        "visual_treatment",
        "lighting_intent",
        "ambience_intent",
        "dialogue_intent",
        "music_intent",
        "primary_camera_motion",
        "camera_subject_relation",
    ):
        if getattr(intent, field) is None:
            diagnostics.append(f"generation_intent.{field}")
    if intent.camera_endpoint.start_framing == "unspecified":
        diagnostics.append("generation_intent.camera_endpoint.start_framing")
    if intent.camera_endpoint.end_framing == "unspecified":
        diagnostics.append("generation_intent.camera_endpoint.end_framing")
    if intent.pacing.shot_duration_seconds is None:
        diagnostics.append("generation_intent.pacing.shot_duration_seconds")
    if audio_need is AudioNeed.FORBIDDEN:
        ambience = intent.ambience_intent
        dialogue = intent.dialogue_intent
        music = intent.music_intent
        if ambience is not None and not ambience.explicitly_silent:
            diagnostics.append("generation_intent.ambience_intent.explicitly_silent")
        if dialogue is not None and dialogue.mode != "none":
            diagnostics.append("generation_intent.dialogue_intent.mode")
        if music is not None and music.mode != "none":
            diagnostics.append("generation_intent.music_intent.mode")
    return tuple(diagnostics)


def validate_camera_subject_relation(
    relation: CameraSubjectRelation,
) -> tuple[str, ...]:
    return tuple(
        f"generation_intent.camera_subject_relation.{field}"
        for field in ("start_relation", "end_relation")
        if _SECONDARY_CAMERA_MOTION.search(getattr(relation, field))
    )


def validate_conditioning_compatibility(
    evidence: ConditioningCompatibilityEvidence | None,
) -> tuple[str, ...]:
    if evidence is None:
        return ("conditioning_compatibility",)
    if evidence.lane is ConditioningLane.I2VA:
        return ()
    diagnostics = [
        f"conditioning_compatibility.{field}"
        for field in (
            "same_subject_scale",
            "composition_compatible",
            "screen_order_compatible",
            "axis_compatible",
            "camera_path_reachable",
            "character_prop_state_reachable",
            "action_endpoint_reachable",
        )
        if getattr(evidence, field) is not True
    ]
    return tuple(diagnostics)


def validate_requirement_conditioning_compatibility(
    requirement: ProviderNeutralVideoRequirement,
) -> tuple[str, ...]:
    evidence = requirement.conditioning_compatibility
    if requirement.generation_mode is GenerationMode.TEXT_TO_VIDEO:
        diagnostics: list[str] = []
        if evidence is not None:
            diagnostics.append("conditioning_compatibility")
        if requirement.asset_evidence:
            diagnostics.append("asset_evidence")
        if requirement.semantic_reference_roles:
            diagnostics.append("semantic_reference_roles")
        if requirement.continuity_mode not in {
            ContinuityMode.NONE,
            ContinuityMode.SEMANTIC,
        }:
            diagnostics.append("continuity_mode")
        capability = requirement.capability_need
        for field in (
            "needs_identity_reference",
            "needs_scene_reference",
            "needs_first_frame",
            "needs_last_frame",
            "needs_terminal_reference",
        ):
            if getattr(capability, field):
                diagnostics.append(f"capability_need.{field}")
        if capability.max_reference_count not in {None, 0}:
            diagnostics.append("capability_need.max_reference_count")
        return tuple(diagnostics)
    diagnostics = list(validate_conditioning_compatibility(evidence))
    if evidence is None:
        return tuple(diagnostics)
    if requirement.generation_mode is not GenerationMode.IMAGE_TO_VIDEO:
        diagnostics.append("generation_mode")

    first_roles = {
        SemanticReferenceRole.FIRST_FRAME,
        SemanticReferenceRole.CONTINUITY_TERMINAL,
    }
    last_roles = {
        SemanticReferenceRole.LAST_FRAME,
        SemanticReferenceRole.APPROVED_ENDPOINT,
    }
    first_assets = tuple(
        item for item in requirement.asset_evidence if item.role in first_roles
    )
    last_assets = tuple(
        item for item in requirement.asset_evidence if item.role in last_roles
    )
    if len(first_assets) != 1:
        diagnostics.append("asset_evidence.first_anchor")
    elif first_assets[0].asset_id != evidence.first_anchor_id:
        diagnostics.append("conditioning_compatibility.first_anchor_id")
    if not requirement.capability_need.needs_first_frame:
        diagnostics.append("capability_need.needs_first_frame")

    if evidence.lane is ConditioningLane.I2VA:
        if last_assets:
            diagnostics.append("asset_evidence.last_anchor")
        if requirement.capability_need.needs_last_frame:
            diagnostics.append("capability_need.needs_last_frame")
    else:
        if len(last_assets) != 1:
            diagnostics.append("asset_evidence.last_anchor")
        elif last_assets[0].asset_id != evidence.last_anchor_id:
            diagnostics.append("conditioning_compatibility.last_anchor_id")
        if not requirement.capability_need.needs_last_frame:
            diagnostics.append("capability_need.needs_last_frame")
        if len(first_assets) == 1 and len(last_assets) == 1:
            first, last = first_assets[0], last_assets[0]
            if (
                first.width is None
                or first.height is None
                or last.width is None
                or last.height is None
                or (first.width, first.height) != (last.width, last.height)
            ):
                diagnostics.append("asset_evidence.anchor_geometry")

    output = requirement.output_need
    output_duration = (
        output.frame_count / output.fps
        if output.frame_count is not None and output.fps is not None
        else output.duration_seconds
    )
    intent_duration = requirement.generation_intent.pacing.shot_duration_seconds
    for path, duration in (
        ("output_need.duration", output_duration),
        ("generation_intent.pacing.shot_duration_seconds", intent_duration),
    ):
        if duration is None or abs(duration - evidence.available_duration_seconds) > 1e-6:
            diagnostics.append(path)
    return tuple(dict.fromkeys(diagnostics))


def validate_causal_transition_readiness(
    policy: ContinuityTransitionPolicy | None,
    *,
    previous_shot_state: PreviousShotStateLike | None,
    requirement: ProviderNeutralVideoRequirement,
) -> tuple[str, ...]:
    if policy is None:
        return ("continuity_transition_policy",)
    try:
        policy = ContinuityTransitionPolicy.model_validate(
            policy.model_dump(mode="python")
        )
    except ValidationError:
        return ("continuity_transition_policy.policy_hash",)
    diagnostics: list[str] = []
    if policy.schema_version != "2":
        diagnostics.append("continuity_transition_policy.schema_version")
    if previous_shot_state is None:
        diagnostics.append("current_request.previous_shot_state")
    else:
        if (
            policy.source_shot.artifact_id
            != previous_shot_state.previous_shot_artifact_id
            or policy.source_shot.revision
            != previous_shot_state.previous_shot_revision
            or policy.source_shot.content_hash
            != previous_shot_state.previous_shot_content_hash
        ):
            diagnostics.append("continuity_transition_policy.source_shot")
        if (
            policy.source_generation_intent_hash
            != previous_shot_state.previous_generation_intent_hash
        ):
            diagnostics.append(
                "continuity_transition_policy.source_generation_intent_hash"
            )
    if (
        policy.target_shot.artifact_id != requirement.target_shot.artifact_id
        or policy.target_shot.revision != requirement.target_shot.revision
        or policy.target_shot.content_hash != requirement.target_shot.content_hash
    ):
        diagnostics.append("continuity_transition_policy.target_shot")
    if policy.target_generation_intent_hash != requirement.generation_intent_hash:
        diagnostics.append(
            "continuity_transition_policy.target_generation_intent_hash"
        )

    changes = {item.dimension: item for item in policy.causal_state_changes}
    for dimension in CausalDimension:
        if dimension not in changes:
            diagnostics.append(
                f"continuity_transition_policy.causal_state_changes.{dimension.value}"
            )
    for dimension, change in changes.items():
        if (
            change.transition_mode is CausalTransitionMode.CARRY
            and change.source_close != change.target_open
        ):
            diagnostics.append(
                f"continuity_transition_policy.causal_state_changes.{dimension.value}"
            )
        if (
            policy.causal_edge_semantics is CausalEdgeSemantics.COMMERCIAL_CUT
            and dimension
            in {CausalDimension.PROP_IDENTITY, CausalDimension.PROP_FUNCTIONAL_STATE}
            and change.transition_mode is CausalTransitionMode.AUTHORIZED_RELEASE
        ):
            diagnostics.append(
                f"continuity_transition_policy.causal_state_changes.{dimension.value}"
            )
    return tuple(dict.fromkeys(diagnostics))


__all__ = [
    "ConditioningCompatibilityEvidence",
    "ConditioningLane",
    "validate_conditioning_compatibility",
    "validate_camera_subject_relation",
    "validate_causal_transition_readiness",
    "validate_requirement_conditioning_compatibility",
    "validate_generation_intent_for_continuity",
]
