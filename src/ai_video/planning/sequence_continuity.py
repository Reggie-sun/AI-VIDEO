"""Storyboard adjacency to the existing typed continuity and Planning owners.

No prose inference, state store, route selection, or media effects live here.
"""

from collections.abc import Callable
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning._planner_models import VideoPlanningRequest, _canonical_hash_without
from ai_video.planning.video_planner import (
    VideoPlanner, prepare_shot_for_existing_production, require_current_video_plan,
)
from ai_video.production.generation_execution import (
    GenerationDecisionExecutionBinding, require_sequence_destination_selection,
)
from ai_video.production._sequence_source import (
    accepted_sequence_source, causal_state_column_hash, require_causal_columns, require_sequence_source,
)
from ai_video.production._shot_router_contracts import (
    ContinuityProviderRouteBinding, ProviderRouteIdentity, VideoGenerationLifecycleEnvelope,
)
from ai_video.production._video_continuity import validate_hard_cut_keyframe_binding_against_project
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.video_execution_stack import GenerationExecutionStackIdentity
from ai_video.production.video_transition import (
    BoundaryKind, CausalEdgeSemantics, CausalStateChange, CausalTransitionMode,
    ContinuityAnchorBinding, ContinuityAnchorRole, ContinuityObligation,
    ContinuityTransitionPolicy, CreativeArtifactIdentity,
)


def _identity(shot):
    return CreativeArtifactIdentity(
        artifact_id=shot.artifact_id, revision=shot.revision, content_hash=shot.content_hash)


def require_current_sequence_route(*, loaded, routing: ContinuityProviderRouteBinding,
                                   planning_request, projection, lifecycle) -> None:
    """Reopen the activation proof when a sealed sequence reaches Production."""
    routing = ContinuityProviderRouteBinding.model_validate(routing.model_dump(mode="python"))
    policy = routing.transition_policy
    binding, _, _, accepted, _ = require_sequence_source(loaded=loaded, routing=routing,
        requirement=projection.requirement, lifecycle=lifecycle)
    seed = VideoPlanningRequest.create(**{**planning_request.model_dump(mode="python",
        exclude={"request_content_hash", "previous_shot_state", "continuity_transition_policy"}),
        "previous_shot_state": None})
    if routing.destination_selection_binding is not None:
        selection = require_sequence_destination_selection(
            selection=routing.destination_selection_binding, target_shot=seed.target_shot,
            target_generation_intent_hash=seed.generation_intent.projection_hash,
            destination_execution_stack=routing.destination_execution_stack, lifecycle=lifecycle,
            destination_route=routing.destination_route, source_request_content_hash=seed.request_content_hash)
        if selection.projection != require_current_video_plan(current_request=seed, plan=VideoPlanner().plan(seed)):
            raise ValueError("destination selection lacks the exact Planner-derived seed projection")
    expected = canonical_sha256({"storyboard": loaded.storyboard.content_hash,
        "source_execution_binding": binding.binding_hash, "accepted_media": accepted,
        "target_request": seed.request_content_hash,
        "causal_state_changes": [c.model_dump(mode="json") for c in policy.causal_state_changes]})
    if policy.authoring_evidence_hash != expected:
        raise ValueError("sequence authoring evidence seal is stale")


def build_sequence_video_planning_request(
    *, project_root: str | Path, current_request: VideoPlanningRequest,
    continuity_obligation: ContinuityObligation | None,
    boundary_kind: BoundaryKind | None = None,
    causal_edge_semantics: CausalEdgeSemantics | None = None,
    source_shot: CreativeArtifactIdentity | None = None,
    source_generation_intent_hash: str | None = None,
    causal_state_changes: tuple[CausalStateChange, ...] = (),
    required_carryover_dimensions: tuple[str, ...] = (),
    anchors: tuple[ContinuityAnchorBinding, ...] = (),
    source_execution_stack: GenerationExecutionStackIdentity | None = None,
    destination_execution_stack: GenerationExecutionStackIdentity | None = None,
    destination_route: ProviderRouteIdentity | None = None,
    destination_selection_binding: GenerationDecisionExecutionBinding | None = None,
    lifecycle: VideoGenerationLifecycleEnvelope | None = None,
    take_id: str | None = None,
) -> tuple[VideoPlanningRequest, ContinuityProviderRouteBinding | None]:
    """Explicit None means independent; incomplete declared edges always STOP.

    Same-stack destination inherits accepted source authority. A new stack needs
    prior canonical Router selection for the exact neutral seed, then this edge
    reaches sequence-aware Planner/Router afresh; the prior binding cannot execute it.
    """
    try:
        loaded = load_production_project(Path(project_root) / "project.yaml")
        current_request = VideoPlanningRequest.model_validate(current_request.model_dump(mode="python"))
        if (current_request.planning_contract_version != "video-planner/3"
                or current_request.request_content_hash != _canonical_hash_without(
                    current_request, "request_id", "request_content_hash")):
            raise ValueError("target planning request seal is stale")
        target = next(s for s in loaded.shots if s.shot_id == current_request.target_shot.shot_id)
        scene = next(s for s in loaded.scenes if s.scene_id == target.scene_id)
        characters = tuple(sorted((c for c in loaded.characters if c.character_id in target.character_ids),
                                  key=lambda c: c.character_id))
        if (target != current_request.target_shot or scene != current_request.scene_context
                or characters != tuple(sorted(current_request.character_context, key=lambda c: c.character_id))):
            raise ValueError("target authoring context is stale")
        if current_request.previous_shot_state is not None or current_request.continuity_transition_policy is not None:
            raise ValueError("sequence adapter requires unmaterialized target input")
        order = tuple(shot_id for beat in loaded.storyboard.beats for shot_id in beat.shot_ids)
        index = order.index(target.shot_id)
        if continuity_obligation is None:
            if any((boundary_kind, causal_edge_semantics, source_shot, source_generation_intent_hash,
                    causal_state_changes, required_carryover_dimensions, anchors,
                    source_execution_stack, destination_execution_stack, destination_route,
                    destination_selection_binding, lifecycle, take_id)):
                raise ValueError("independent Shot cannot discard an authored edge")
            return current_request, None
        if (not isinstance(continuity_obligation, ContinuityObligation)
                or not isinstance(boundary_kind, BoundaryKind)
                or not isinstance(causal_edge_semantics, CausalEdgeSemantics)):
            raise ValueError("sequence classification requires typed authoring enums")
        if (index == 0 or boundary_kind is None or causal_edge_semantics is None
                or source_shot is None or source_generation_intent_hash is None
                or source_execution_stack is None or lifecycle is None or loaded.qa_policy is None):
            raise ValueError("declared edge requires exact source, semantics, stacks, route and QA")
        previous = next(s for s in loaded.shots if s.shot_id == order[index - 1])
        binding, source_request, terminal, accepted_hashes, source_registry = accepted_sequence_source(loaded, previous, require_causal_close=continuity_obligation is ContinuityObligation.FULL_CONTINUITY)
        source_requirement = binding.projection.requirement
        bound = binding.decision.routing.provider_bound_request
        source_route = binding.selected_provider_route
        destination_execution_stack = destination_execution_stack or source_execution_stack
        if destination_execution_stack.execution_stack_hash == source_execution_stack.execution_stack_hash:
            if destination_route is not None and destination_route != source_route:
                raise ValueError("same-stack destination must inherit the accepted source Provider route")
            if destination_selection_binding is not None:
                raise ValueError("same-stack destination inherits source authority without a new selection")
            destination_route = source_route
        else:
            destination_selection_binding = require_sequence_destination_selection(
                selection=destination_selection_binding, target_shot=target,
                target_generation_intent_hash=current_request.generation_intent.projection_hash,
                destination_execution_stack=destination_execution_stack, lifecycle=lifecycle,
                destination_route=destination_route, project=loaded,
                source_request_content_hash=current_request.request_content_hash)
            if destination_selection_binding.projection != require_current_video_plan(
                    current_request=current_request, plan=VideoPlanner().plan(current_request)):
                raise ValueError("destination selection lacks the exact Planner-derived seed projection")
            destination_route = destination_selection_binding.selected_provider_route
        if (_identity(source_requirement.target_shot) != source_shot
                or source_requirement.generation_intent_hash != source_generation_intent_hash):
            raise ValueError("source Shot identity or generation intent hash is stale")
        changes = tuple(sorted((CausalStateChange.model_validate(c.model_dump(mode="python"))
                                for c in causal_state_changes), key=lambda c: c.dimension.value))
        intent = current_request.generation_intent
        require_causal_columns(changes, source_requirement.generation_intent, intent.generation_intent)
        if continuity_obligation is ContinuityObligation.FULL_CONTINUITY:
            carries = {c.dimension.value for c in changes if c.transition_mode is CausalTransitionMode.CARRY}
            if not carries <= set(required_carryover_dimensions) or terminal is None:
                raise ValueError("FULL requires all authored carries and an exact terminal")
        for stack in (source_execution_stack, destination_execution_stack):
            GenerationExecutionStackIdentity.model_validate(stack.model_dump(mode="python"))
            if stack.materialization_status != "materialized":
                raise ValueError("edge execution stack is not materialized")
        if source_request.execution_stack_hash != source_execution_stack.execution_stack_hash:
            raise ValueError("accepted source execution stack is missing or stale")
        lifecycle = VideoGenerationLifecycleEnvelope.model_validate(lifecycle.model_dump(mode="python"))
        if (lifecycle.base_project != loaded.manifest.active_project
                or lifecycle.base_registry != loaded.manifest.active_registry
                or lifecycle.base_dependency_graph != loaded.manifest.active_dependency_graph
                or lifecycle.execution_stack_hash != destination_execution_stack.execution_stack_hash):
            raise ValueError("destination lifecycle snapshot or stack is stale")
        if continuity_obligation is ContinuityObligation.FULL_CONTINUITY:
            if boundary_kind is BoundaryKind.HARD_CUT:
                if lifecycle.hard_cut_keyframe_binding is None:
                    raise ValueError("hard-cut FULL requires existing C2 keyframe preparation")
                validate_hard_cut_keyframe_binding_against_project(lifecycle, loaded)
                frame = lifecycle.hard_cut_keyframe_binding
                first_assets = tuple(a.asset_id for a in current_request.available_assets
                                     if a.role.value == "approved_keyframe")
                if frame.terminal_frame != terminal or first_assets != (frame.keyframe_asset_id,):
                    raise ValueError("hard-cut FIRST_FRAME or source terminal is stale")
            elif boundary_kind is BoundaryKind.WITHIN_CONTINUOUS_TAKE:
                if lifecycle.continuity_binding is None or lifecycle.continuity_binding.terminal_frame != terminal:
                    raise ValueError("continuous FULL requires exact terminal lifecycle binding")
        for anchor in anchors:
            if anchor.source_kind == "registered_asset":
                asset = next(a for a in loaded.registry.assets if a.asset_id == anchor.source_identity)
                if (asset.sha256 != anchor.content_hash
                        or asset.input_fingerprint != anchor.evidence_fingerprint
                        or asset.creation_receipt_id != anchor.materialization_receipt_id):
                    raise ValueError("registered continuity anchor is stale")
        if continuity_obligation is ContinuityObligation.FULL_CONTINUITY:
            first = next(a for a in anchors if a.role is ContinuityAnchorRole.FIRST_FRAME)
            expected_first = (lifecycle.hard_cut_keyframe_binding.keyframe_asset_id
                if boundary_kind is BoundaryKind.HARD_CUT else terminal.extracted_asset_id)
            if first.source_kind != "registered_asset" or first.source_identity != expected_first:
                raise ValueError("FULL first-frame anchor requires exact materialized conditioning")
        policy = ContinuityTransitionPolicy.create(
            schema_version="2", policy_id=f"sequence-{previous.shot_id}-{target.shot_id}",
            project=loaded.manifest.active_project, registry=loaded.manifest.active_registry,
            source_shot=source_shot, target_shot=_identity(target), boundary_kind=boundary_kind,
            continuity_obligation=continuity_obligation, take_id=take_id,
            source_execution_stack_hash=source_execution_stack.execution_stack_hash,
            destination_execution_stack_hash=destination_execution_stack.execution_stack_hash,
            continuity_grade="c4_native_boundary_motion",
            required_carryover_dimensions=tuple(sorted(set(required_carryover_dimensions))),
            anchors=tuple(sorted(anchors, key=lambda a: a.role.value)), qa_policy_hash=loaded.qa_policy.content_hash,
            authoring_evidence_hash=canonical_sha256({
                "storyboard": loaded.storyboard.content_hash,
                "source_execution_binding": binding.binding_hash, "accepted_media": accepted_hashes,
                "target_request": current_request.request_content_hash,
                "causal_state_changes": [c.model_dump(mode="json") for c in changes],
            }), source_generation_intent_hash=source_generation_intent_hash,
            target_generation_intent_hash=intent.projection_hash,
            causal_edge_semantics=causal_edge_semantics, causal_state_changes=changes,
        )
        routing = ContinuityProviderRouteBinding.create(
            transition_policy=policy, previous_shot=source_requirement.target_shot,
            previous_provider_bound_request=bound, source_route=source_route,
            destination_route=destination_route, source_execution_stack=source_execution_stack,
            destination_execution_stack=destination_execution_stack,
            source_activation_registry=source_registry,
            destination_selection_binding=(destination_selection_binding.model_dump(mode="json")
                if destination_selection_binding is not None else None),
        )
        state = (None if continuity_obligation is ContinuityObligation.SUBSTANTIAL_RESET else
            VideoPlanner.derive_previous_shot_state(
                previous_shot=source_requirement.target_shot, target_shot=target,
                previous_generation_intent_hash=source_generation_intent_hash,
                is_same_action=boundary_kind is BoundaryKind.WITHIN_CONTINUOUS_TAKE,
                is_angle_change=boundary_kind is BoundaryKind.HARD_CUT,
                semantic_jump=boundary_kind is BoundaryKind.SCENE_BOUNDARY,
                has_terminal_frame_asset_id=terminal.extracted_asset_id if terminal is not None else None))
        payload = {name: getattr(current_request, name) for name in type(current_request).model_fields
                   if name != "request_content_hash"}
        return VideoPlanningRequest.create(**{**payload, "previous_shot_state": state,
            "continuity_transition_policy": policy}), routing
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
        raise AiVideoError(code=ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
            user_message="Sequence continuity needs exact authoring evidence before planning.",
            technical_detail=f"NEEDS_AUTHORING_EVIDENCE: {exc}", retryable=False) from None


def prepare_sequence_shot_for_existing_production(
    *, production_handoff: Callable, **sequence_inputs,
):
    """Canonical Sequence -> Planner -> Readiness -> existing production handoff."""
    request, routing = build_sequence_video_planning_request(**sequence_inputs)
    plan = VideoPlanner().plan(request)

    def handoff(**values):
        return production_handoff(current_request=request, plan=plan,
            continuity_routing=routing, lifecycle=sequence_inputs.get("lifecycle"), **values)

    return prepare_shot_for_existing_production(
        current_request=request, plan=plan, production_handoff=handoff)
