from __future__ import annotations

from typing import Any, Literal

from ai_video.production._video_capability_fingerprint import (
    c4_exact_cardinality_grammar_satisfies_variant,
    capability_variant_fingerprint,
)
from ai_video.production.video import VideoGenerationMode, VideoOutputRequirement
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import (
    AudioNeed,
    GenerationMode,
    OutputGeometryPolicy,
    ProviderNeutralVideoRequirement,
    SemanticReferenceRole,
)
from ai_video.production.video_transition import ContinuityObligation


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
        SemanticReferenceRole.APPROVED_ENDPOINT: "last_frame",
        SemanticReferenceRole.LAST_FRAME: "last_frame",
        SemanticReferenceRole.IDENTITY: "reference",
        SemanticReferenceRole.SCENE: "reference",
        SemanticReferenceRole.VIDEO_REFERENCE: "reference_video",
        SemanticReferenceRole.CONTINUITY_MOTION_TAIL: "reference_video",
        SemanticReferenceRole.AUDIO_REFERENCE: "reference_audio",
    }[role]


def context_asset_role(role: SemanticReferenceRole) -> str:
    return {
        SemanticReferenceRole.FIRST_FRAME: "first_frame",
        SemanticReferenceRole.CONTINUITY_TERMINAL: "continuity_terminal",
        SemanticReferenceRole.APPROVED_ENDPOINT: "last_frame",
        SemanticReferenceRole.LAST_FRAME: "last_frame",
        SemanticReferenceRole.IDENTITY: "character_reference",
        SemanticReferenceRole.SCENE: "scene_reference",
        SemanticReferenceRole.VIDEO_REFERENCE: "reference_video",
        SemanticReferenceRole.CONTINUITY_MOTION_TAIL: "reference_video",
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
    if requirement.c4_multi_anchor_binding is not None:
        native_order = {
            "first_frame": 0,
            "last_frame": 1,
            "reference": 2,
            "reference_video": 3,
            "reference_audio": 4,
        }
        ordered = sorted(
            zip(roles, assets, strict=True),
            key=lambda item: (native_order[item[0]], item[1].asset_id),
        )
        roles = [item[0] for item in ordered]
        assets = [item[1] for item in ordered]
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


def commercial_requirement_context_is_current(
    requirement: ProviderNeutralVideoRequirement,
    context: Any,
) -> bool:
    if requirement.contract_version != "provider-neutral-video-requirement/3":
        return not requirement.capability_need.needs_product_fidelity
    approval = requirement.approved_commercial_source
    keyframe = context.shot_keyframe
    return bool(
        approval is not None
        and requirement.capability_need.needs_product_fidelity
        and requirement.generation_mode is GenerationMode.IMAGE_TO_VIDEO
        and keyframe is not None
        and keyframe.role == "first_frame"
        and keyframe.asset_id == approval.keyframe_asset_id
        and keyframe.asset_sha256 == approval.keyframe_sha256
        and keyframe.source_registry_revision_id
        == context.selected_registry_revision_id
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


def validate_continuity_transition(
    *,
    projection: Any,
    context: Any,
    lifecycle: Any,
    continuity_routing: Any | None,
) -> Any | None:
    if continuity_routing is None:
        if context.continuity_mode.value != "none":
            raise ValueError(
                "continuity-bearing requirement requires exact sequence routing evidence"
            )
        return None
    continuity_routing = type(continuity_routing).model_validate(
        continuity_routing.model_dump(mode="python")
    )
    policy = continuity_routing.transition_policy
    target = policy.target_shot
    requirement = projection.requirement
    context_mode = context.continuity_mode.value
    requirement_mode_value = requirement.continuity_mode.value
    if context_mode != requirement_mode_value:
        raise ValueError(
            "continuity policy requires matching context and requirement modes"
        )
    _validate_obligation_mode(policy, requirement)
    if (target.artifact_id, target.revision, target.content_hash) != (
        context.activated_shot.artifact_id,
        context.target_shot_revision,
        context.target_shot_content_hash,
    ):
        raise ValueError("continuity policy must match the exact current routing target")
    if (
        policy.project != lifecycle.base_project
        or policy.registry != lifecycle.base_registry
    ):
        raise ValueError(
            "continuity routing inputs must share exact Project and Registry snapshots"
        )
    if (
        policy.continuity_obligation is ContinuityObligation.FULL_CONTINUITY
    ):
        _validate_full_continuity_terminal(
            projection,
            context,
            lifecycle,
            continuity_routing.previous_shot,
            continuity_routing.previous_provider_bound_request,
        )
        if (
            policy.source_execution_stack_hash
            != policy.destination_execution_stack_hash
        ):
            _validate_cross_stack_spatial_intent(projection.requirement, policy)
    return continuity_routing


def _validate_obligation_mode(policy: Any, requirement: Any) -> None:
    mode = requirement.continuity_mode.value
    obligation = policy.continuity_obligation
    if obligation is ContinuityObligation.FULL_CONTINUITY:
        if mode not in {"exact_terminal", "multi_anchor"}:
            raise ValueError(
                "full continuity requires terminal-bearing continuity mode"
            )
        return
    if obligation is ContinuityObligation.SUBSTANTIAL_RESET:
        if mode != "none":
            raise ValueError(
                "substantial reset requires continuity mode none"
            )
        return
    if mode == "reference":
        evidence_roles = {item.role for item in requirement.asset_evidence}
        required_roles = {
            SemanticReferenceRole.IDENTITY,
            SemanticReferenceRole.SCENE,
        }
        if not evidence_roles.intersection(required_roles):
            raise ValueError(
                "identity/style carryover requires identity or scene reference evidence"
            )
        if (
            "identity" in policy.required_carryover_dimensions
            and SemanticReferenceRole.IDENTITY not in evidence_roles
        ):
            raise ValueError(
                "identity carryover requires exact identity reference evidence"
            )
        return
    if mode == "semantic":
        identity = requirement.generation_intent.identity_continuity
        if (
            "identity" in policy.required_carryover_dimensions
            and (
                identity.preservation.value == "unspecified"
                or not identity.character_ids
            )
        ):
            raise ValueError(
                "semantic identity carryover requires typed identity continuity"
            )
        return
    raise ValueError(
        "identity/style carryover requires reference or semantic continuity mode"
    )


def _validate_full_continuity_terminal(
    projection: Any,
    context: Any,
    lifecycle: Any,
    previous_shot: Any,
    previous_provider_bound_request: Any,
) -> None:
    terminal = context.upstream_terminal
    c4_binding = projection.requirement.c4_multi_anchor_binding
    lifecycle_binding = lifecycle.continuity_binding
    if lifecycle_binding is not None and (
        lifecycle_binding.target_shot_id,
        lifecycle_binding.target_shot_revision,
        lifecycle_binding.target_shot_content_hash,
    ) != (
        context.target_shot_id,
        context.target_shot_revision,
        context.target_shot_content_hash,
    ):
        raise ValueError(
            "continuity lifecycle binding does not match the exact current target"
        )
    evidence = (
        lifecycle_binding.terminal_frame
        if lifecycle_binding is not None
        else c4_binding.terminal if c4_binding is not None else None
    )
    if terminal is None or evidence is None:
        raise ValueError("full continuity routing requires exact previous terminal evidence")
    if (
        (
            evidence.source_shot_id,
            evidence.source_shot_revision,
            evidence.source_shot_content_hash,
            evidence.source_video_asset_id,
            evidence.source_generation_id,
            evidence.source_registry,
        )
        != (
            previous_shot.shot_id,
            previous_shot.revision,
            previous_shot.content_hash,
            previous_provider_bound_request.lifecycle.output_asset_id,
            previous_provider_bound_request.lifecycle.generation_id,
            previous_provider_bound_request.lifecycle.base_registry,
        )
        or (
            evidence.extracted_asset_id,
            evidence.extracted_sha256,
            evidence.extracted_mime_type,
            evidence.extracted_size_bytes,
            evidence.extracted_width,
            evidence.extracted_height,
        )
        != (
            terminal.asset_id,
            terminal.asset_sha256,
            terminal.mime_type,
            terminal.size_bytes,
            terminal.width,
            terminal.height,
        )
    ):
        raise ValueError(
            "full continuity terminal does not match the exact previous request"
        )


def _validate_cross_stack_spatial_intent(requirement: Any, policy: Any) -> None:
    intent = requirement.generation_intent
    required_dimensions = {"camera_velocity", "screen_axis", "subject_position"}
    if (
        not required_dimensions.issubset(policy.required_carryover_dimensions)
        or intent.space_continuity.subject_position == "unspecified"
        or intent.space_continuity.screen_direction == "unspecified"
        or intent.axis_continuity.camera_axis == "unspecified"
        or intent.axis_continuity.framing_continuity == "unspecified"
    ):
        raise ValueError(
            "cross-stack full continuity requires explicit spatial and camera intent"
        )


def apply_continuity_transition(
    *,
    decision: Any,
    context: Any,
    provider_profile: Any,
    capabilities: Any,
    selected_capability_id: str,
    compiler_contract: Any,
    continuity_routing: Any | None,
) -> Any:
    if continuity_routing is None:
        return decision
    decision = _bind_continuity_lineage(
        decision,
        continuity_routing,
    )
    selected = next(
        (
            variant
            for variant in capabilities.variants
            if variant.capability_id == selected_capability_id
        ),
        None,
    )
    policy = continuity_routing.transition_policy
    if selected is not None:
        current_route = type(continuity_routing.destination_route).create(
            provider_name=capabilities.provider_name,
            provider_kind=selected.provider_kind,
            model_id=selected.model_id,
            provider_profile=provider_profile,
            capability_id=selected.capability_id,
            capability_fingerprint=capability_variant_fingerprint(selected),
            execution_kind=selected.execution_kind,
            billing_kind=selected.billing_kind,
            compiler_contract=compiler_contract,
        )
        if current_route != continuity_routing.destination_route:
            same_stack = (
                policy.source_execution_stack_hash
                == policy.destination_execution_stack_hash
            )
            reason_type = type(decision.reason_codes[0])
            outcome_type = type(decision.outcome)
            return as_capability_blocked(
                decision,
                reason_code=reason_type(
                    "CONTINUITY_PROVIDER_LOCKED"
                    if same_stack
                    else "CONTINUITY_DESTINATION_ROUTE_MISMATCH"
                ),
                outcome=outcome_type("blocked_policy"),
                rationale=(
                    "The continuity edge locks the previous Provider route."
                    if same_stack
                    else "The selected Provider route is not the destination sealed by the continuity edge."
                ),
            )
    if (
        policy.source_execution_stack_hash
        != policy.destination_execution_stack_hash
        and policy.continuity_obligation
        is ContinuityObligation.FULL_CONTINUITY
        and not _uses_exact_terminal_frame(decision, context, selected)
    ):
        reason_type = type(decision.reason_codes[0])
        outcome_type = type(decision.outcome)
        return as_capability_blocked(
            decision,
            reason_code=reason_type("CONTINUITY_FRAME_CONDITIONING_REQUIRED"),
            outcome=outcome_type("blocked_capability"),
            rationale=(
                "A cross-stack full-continuity route must condition the destination "
                "Provider on the exact previous terminal as its first frame."
            ),
        )
    return decision


def _bind_continuity_lineage(
    decision: Any,
    continuity_routing: Any,
) -> Any:
    values = {
        field_name: getattr(decision, field_name)
        for field_name in type(decision).model_fields
        if field_name not in {"semantic_routing_hash", "audit_decision_hash"}
    }
    values.update(
        continuity_transition_policy_hash=(
            continuity_routing.transition_policy.policy_hash
        ),
        previous_provider_bound_request_hash=(
            continuity_routing.previous_provider_bound_request.provider_bound_request_hash
        ),
        continuity_provider_route_binding_hash=continuity_routing.binding_hash,
    )
    return type(decision).create(**values)


def _uses_exact_terminal_frame(
    decision: Any,
    context: Any,
    selected: Any,
) -> bool:
    terminal = context.upstream_terminal
    return bool(
        selected is not None
        and selected.mode is VideoGenerationMode.IMAGE_TO_VIDEO
        and "first_frame" in selected.allowed_image_roles
        and decision.required_binding_roles
        and decision.required_binding_roles[0] == "first_frame"
        and decision.input_assets
        and terminal is not None
        and decision.input_assets[0] == terminal
    )


def enforce_c4_requirement_gate(
    requirement: ProviderNeutralVideoRequirement,
    context: Any,
    capabilities: Any,
    selected_capability_id: str,
    decision: Any,
) -> Any:
    """Apply exact C4 Registry and one-variant grammar checks before binding."""

    binding = requirement.c4_multi_anchor_binding
    if binding is None or decision.outcome.value != "selected":
        return decision
    reason_code_type = type(decision.reason_codes[0])
    outcome_type = type(decision.outcome)
    if binding.selected_registry_revision_id != context.selected_registry_revision_id:
        return as_capability_blocked(
            decision,
            reason_code=reason_code_type("C4_REGISTRY_REVISION_MISMATCH"),
            outcome=outcome_type("blocked_missing_input"),
            rationale=(
                "The sealed C4 requirement does not use the selected Registry revision."
            ),
        )
    selected = next(
        (
            variant
            for variant in capabilities.variants
            if variant.capability_id == selected_capability_id
        ),
        None,
    )
    if selected is None or not c4_exact_cardinality_grammar_satisfies_variant(
        selected,
        motion=binding.tier.value == "motion_boundary",
    ):
        return as_capability_blocked(
            decision,
            reason_code=reason_code_type("PROVIDER_CAPABILITY_DENIED"),
            outcome=outcome_type("blocked_capability"),
            rationale="The selected capability lacks the exact complete C4 grammar.",
        )
    return decision


def requirement_route_is_unsupported(
    requirement: ProviderNeutralVideoRequirement,
    context: Any,
    expected_mode: VideoGenerationMode,
    decision: Any,
    output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement,
) -> bool:
    """Return whether neutral intent cannot be represented by the routing result."""

    return (
        requirement.continuity_mode.value != context.continuity_mode.value
        or expected_mode is not decision.required_mode
        or not requirement_output_matches(requirement, output_requirement)
        or requirement.generation_intent.camera_intent.expression_strength.value
        == "native_control_required"
    )
