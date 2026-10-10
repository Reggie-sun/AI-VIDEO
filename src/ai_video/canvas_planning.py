"""Derive current Planner/Router inputs from director data and canonical bytes."""
from pydantic import TypeAdapter
from ai_video.planning import (
    AssetRole, AvailableAsset, ProductionPolicyInput, ShotIntentEvidence,
    VideoPlanner, VideoPlanningRequest, require_current_video_plan,
)
from ai_video.planning.generation_feedback_context import require_feedback_context
from ai_video.planning.sequence_continuity import build_sequence_video_planning_request
from ai_video.production._sequence_source import accepted_sequence_source
from ai_video.production._sequence_source import causal_state_column_hash
from ai_video.production._shot_router_contracts import (
    RouterAssetIdentity, ShotRoutingContext, VideoGenerationLifecycleEnvelope,
)
from ai_video.production.video import VideoGenerationMode
from ai_video.production.video_requirement import (
    ProviderNeutralGenerationIntentProjection, SemanticReferenceRole,
)
from ai_video.production.video_transition import (
    BoundaryKind, CausalEdgeSemantics, CausalStateChange, ContinuityObligation,
    CreativeArtifactIdentity,
)


_ROLES = {
    AssetRole.APPROVED_KEYFRAME: SemanticReferenceRole.FIRST_FRAME,
    AssetRole.LAST_FRAME: SemanticReferenceRole.LAST_FRAME,
    AssetRole.PREVIOUS_SHOT_TERMINAL: SemanticReferenceRole.FIRST_FRAME,
    AssetRole.CHARACTER_REFERENCE: SemanticReferenceRole.IDENTITY,
    AssetRole.SCENE_REFERENCE: SemanticReferenceRole.SCENE,
    AssetRole.EXISTING_VIDEO: SemanticReferenceRole.VIDEO_REFERENCE,
    AssetRole.REFERENCE_AUDIO: SemanticReferenceRole.AUDIO_REFERENCE,
}
_ROUTER_ROLES = {
    AssetRole.APPROVED_KEYFRAME: "first_frame", AssetRole.LAST_FRAME: "last_frame",
    AssetRole.PREVIOUS_SHOT_TERMINAL: "continuity_terminal",
    AssetRole.CHARACTER_REFERENCE: "character_reference", AssetRole.SCENE_REFERENCE: "scene_reference",
    AssetRole.EXISTING_VIDEO: "reference_video", AssetRole.REFERENCE_AUDIO: "reference_audio",
}


def canvas_feedback_context(*, loaded, row, policy, execution_stack=None, handoff_preparer=None):
    """No identity/hash/receipt fields belong in per-story director input.

    A configured canonical handoff preparer may supply already materialized C2/C4
    conditioning. Its evidence is checked by the existing sequence owner, never
    inferred from an original prompt or generated here as a PASS receipt.
    """
    shot = next(s for s in loaded.shots if s.shot_id == row["shot"]["shot_id"])
    scene = next(s for s in loaded.scenes if s.scene_id == shot.scene_id)
    characters = tuple(sorted((c for c in loaded.characters if c.character_id in shot.character_ids),
                              key=lambda c: c.character_id))
    generation = dict(row["generation"])
    references = generation.pop("references", ())
    evidence = generation.pop("intent_evidence", {})
    # These hashes seal explicit director columns. They do not assert that a
    # generated frame contains those states; accepted-source evidence owns that.
    from copy import deepcopy
    from ai_video.production.hashing import canonical_sha256
    authored = deepcopy(generation.get("generation_intent", {}))
    if authored.get("close_causal_facts") is not None:
        authored.setdefault("close_state", {"kind": "typed_hash",
            "state_hash": canonical_sha256(authored["close_causal_facts"])})
    edge = row.get("boundary")
    if edge is not None and edge.get("independent") is not True:
        changes = tuple(CausalStateChange.model_validate(c) for c in edge["causal_state_changes"])
        authored.setdefault("open_state", {"kind": "typed_hash",
            "state_hash": causal_state_column_hash(changes, endpoint="target_open")})
    generation["generation_intent"] = authored
    if set(evidence) & {"target_shot_id", "target_shot_content_hash"}:
        raise ValueError("intent evidence identities are computed from the selected Shot")
    assets = {a.asset_id: a for a in loaded.registry.assets}
    selected, routed = [], {}
    for ref in references:
        if set(ref) - {"role", "asset_id", "owner_id"}:
            raise ValueError("references accept roles and selections, not internal bindings")
        role = AssetRole(ref["role"])
        if role not in _ROLES:
            raise ValueError("unsupported canvas planning reference role")
        a = assets[ref["asset_id"]]
        owner = None
        selected_owner_id, selected_owner_hash = shot.shot_id, shot.content_hash
        if role is AssetRole.CHARACTER_REFERENCE:
            candidates = [c for c in characters if a.asset_id in c.reference_asset_ids
                          and (ref.get("owner_id") is None or c.character_id == ref["owner_id"])]
            if len(candidates) != 1:
                raise ValueError("character reference needs one exact selected owner")
            owner, owner_kind, owner_id = candidates[0], "character", candidates[0].character_id
        elif role is AssetRole.SCENE_REFERENCE:
            if a.asset_id not in scene.visual_reference_asset_ids:
                raise ValueError("scene reference is not owned by the selected Scene")
            owner, owner_kind, owner_id = scene, "scene", scene.scene_id
        elif role is AssetRole.PREVIOUS_SHOT_TERMINAL:
            order = [s for beat in loaded.storyboard.beats for s in beat.shot_ids]
            index = order.index(shot.shot_id)
            if index == 0:
                raise ValueError("first Shot has no accepted predecessor terminal")
            previous = next(s for s in loaded.shots if s.shot_id == order[index - 1])
            _, _, terminal, _, _ = accepted_sequence_source(loaded, previous)
            if terminal is None or terminal.extracted_asset_id != a.asset_id:
                raise ValueError("terminal selection is not the exact accepted predecessor")
            selected_owner_id = terminal.source_shot_id
            selected_owner_hash = terminal.source_shot_content_hash
        selected.append(AvailableAsset(role=role, asset_id=a.asset_id, asset_sha256=a.sha256,
            mime_type=a.mime_type, width=a.width, height=a.height, size_bytes=a.size_bytes,
            duration_millis=round(a.duration_seconds * 1000) if a.duration_seconds else None,
            fps=a.video_metadata.fps_numerator if a.video_metadata and a.video_metadata.fps_denominator == 1 else None,
            canonical_owner_id=owner_id if owner else selected_owner_id,
            canonical_owner_content_hash=owner.content_hash if owner else selected_owner_hash))
        routed.setdefault(role, []).append(RouterAssetIdentity(role=_ROUTER_ROLES[role],
            asset_id=a.asset_id, asset_sha256=a.sha256, source_registry_revision_id=loaded.registry.revision_id,
            mime_type=a.mime_type, width=a.width, height=a.height, size_bytes=a.size_bytes,
            duration_millis=round(a.duration_seconds * 1000) if a.duration_seconds else None,
            fps=a.video_metadata.fps_numerator // a.video_metadata.fps_denominator
                if a.video_metadata and a.video_metadata.fps_denominator == 1 else None,
            canonical_owner_kind=owner_kind if owner else None,
            canonical_owner_id=owner_id if owner else None,
            canonical_owner_content_hash=owner.content_hash if owner else None))
    generation.setdefault("output_need", {"duration_seconds": shot.duration_policy.seconds,
        "width": loaded.project.delivery_profile.width, "height": loaded.project.delivery_profile.height,
        "fps": loaded.project.delivery_profile.fps, "container_mime": "video/mp4"})
    generation.setdefault("semantic_reference_roles", tuple(sorted({_ROLES[a.role] for a in selected},
                                                                   key=lambda r: r.value)))
    fields = ProviderNeutralGenerationIntentProjection.model_fields
    if set(generation) - (set(fields) - {"projection_hash", "schema_version"}):
        raise ValueError("generation data contains unknown or internally computed fields")
    intent = ProviderNeutralGenerationIntentProjection.create(**{
        key: TypeAdapter(fields[key].annotation).validate_python(value)
        for key, value in generation.items()})
    neutral = VideoPlanningRequest.create(request_id=f"canvas-{shot.shot_id}", target_shot=shot,
        scene_context=scene, character_context=characters, available_assets=tuple(selected),
        previous_shot_state=None, review_decision=None,
        shot_intent_evidence=ShotIntentEvidence(target_shot_id=shot.shot_id,
            target_shot_content_hash=shot.content_hash, **evidence),
        production_policy=ProductionPolicyInput(local_resources_available=policy.local_resources_available,
            remote_authorized=policy.remote_authorized, budget_authorized=policy.budget_authorized),
        generation_intent=intent, planning_contract_version="video-planner/3")
    from ai_video.production.hashing import canonical_sha256
    identity = canonical_sha256({"shot": shot.content_hash, "input": neutral.request_content_hash})[:32]
    lifecycle = VideoGenerationLifecycleEnvelope(generation_id=f"canvas-generation-{identity}",
        target_asset_role="primary_visual", output_asset_id=f"canvas-video-{identity}",
        base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id, scene.artifact_id, *(c.artifact_id for c in characters),
                            *(a.asset_id for a in selected)),
        seal_terminal_frame=execution_stack is not None,
        execution_stack_hash=execution_stack.execution_stack_hash if execution_stack else None)
    routing = None
    if edge is not None and edge.get("independent") is not True:
        if execution_stack is None:
            raise ValueError("a declared boundary requires the configured materialized execution stack")
        order = [s for beat in loaded.storyboard.beats for s in beat.shot_ids]
        index = order.index(shot.shot_id)
        if index == 0:
            raise ValueError("first Shot cannot declare a predecessor boundary")
        previous = next(s for s in loaded.shots if s.shot_id == order[index - 1])
        obligation = ContinuityObligation(edge["continuity_obligation"])
        source, _, _, _, _ = accepted_sequence_source(loaded, previous,
            require_causal_close=obligation is ContinuityObligation.FULL_CONTINUITY)
        supplemental = handoff_preparer(loaded, row, source, lifecycle) if handoff_preparer else {}
        if set(supplemental) - {"lifecycle", "anchors", "current_request"}:
            raise ValueError("handoff preparer cannot override sequence identities or semantics")
        lifecycle = supplemental.get("lifecycle", lifecycle)
        neutral = supplemental.get("current_request", neutral)
        authored_source = source.projection.requirement.target_shot
        neutral, routing = build_sequence_video_planning_request(project_root=loaded.root,
            current_request=neutral, continuity_obligation=obligation,
            boundary_kind=BoundaryKind(edge["boundary_kind"]),
            causal_edge_semantics=CausalEdgeSemantics(edge["causal_edge_semantics"]),
            source_shot=CreativeArtifactIdentity(artifact_id=authored_source.artifact_id,
                revision=authored_source.revision, content_hash=authored_source.content_hash),
            source_generation_intent_hash=source.projection.requirement.generation_intent_hash,
            causal_state_changes=tuple(CausalStateChange.model_validate(c) for c in edge["causal_state_changes"]),
            required_carryover_dimensions=tuple(edge["required_carryover_dimensions"]),
            anchors=tuple(supplemental.get("anchors", ())), source_execution_stack=execution_stack,
            lifecycle=lifecycle, take_id=edge.get("take_id"))
        # Materialized C2/C4 conditioning may change actual selected assets.
        # Rebuild the Router projection from that verified request, not stale
        # pre-handoff references supplied in the original director data.
        routed = {}
        for selected_asset in neutral.available_assets:
            a = assets[selected_asset.asset_id]
            if selected_asset.asset_sha256 != a.sha256:
                raise ValueError("handoff selected bytes do not match the current Registry")
            role = selected_asset.role
            owner = next((c for c in characters if c.character_id == selected_asset.canonical_owner_id), None)
            if role is AssetRole.SCENE_REFERENCE:
                owner = scene
            routed.setdefault(role, []).append(RouterAssetIdentity(role=_ROUTER_ROLES[role],
                asset_id=a.asset_id, asset_sha256=a.sha256, source_registry_revision_id=loaded.registry.revision_id,
                mime_type=a.mime_type, width=a.width, height=a.height, size_bytes=a.size_bytes,
                duration_millis=selected_asset.duration_millis, fps=selected_asset.fps,
                canonical_owner_kind="character" if owner in characters else "scene" if owner else None,
                canonical_owner_id=owner.character_id if owner in characters else scene.scene_id if owner else None,
                canonical_owner_content_hash=owner.content_hash if owner else None))
    plan = VideoPlanner().plan(neutral)
    projection = require_current_video_plan(current_request=neutral, plan=plan,
        continuity_transition_policy=routing.transition_policy if routing else None)

    def single(role):
        values = routed.get(role, ())
        if len(values) > 1:
            raise ValueError(f"{role.value} requires one selected asset")
        return values[0] if values else None

    context = ShotRoutingContext(activated_shot=shot, target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision, target_shot_content_hash=shot.content_hash,
        storyboard_revision=loaded.storyboard.revision, storyboard_content_hash=loaded.storyboard.content_hash,
        selected_registry_revision_id=loaded.registry.revision_id,
        character_bible_content_hashes=tuple(c.content_hash for c in characters),
        important_character_ids=tuple(c.character_id for c in characters), scene_content_hash=scene.content_hash,
        canonical_character_references=tuple(routed.get(AssetRole.CHARACTER_REFERENCE, ())),
        canonical_scene_reference=next(iter(routed.get(AssetRole.SCENE_REFERENCE, ())), None),
        additional_scene_references=tuple(routed.get(AssetRole.SCENE_REFERENCE, ()))[1:],
        approved_existing_video=None, shot_keyframe=single(AssetRole.APPROVED_KEYFRAME),
        upstream_terminal=single(AssetRole.PREVIOUS_SHOT_TERMINAL), last_frame=single(AssetRole.LAST_FRAME),
        reference_videos=tuple(routed.get(AssetRole.EXISTING_VIDEO, ())),
        reference_audios=tuple(routed.get(AssetRole.REFERENCE_AUDIO, ())),
        motion_requirement=projection.requirement.motion_requirement.value,
        continuity_mode=projection.requirement.continuity_mode.value, semantic_continuity_state=None,
        allowed_visual_strategies=(shot.visual_strategy,), allowed_generation_modes=tuple(VideoGenerationMode))
    return require_feedback_context(loaded=loaded, planning_request=neutral, video_plan=plan,
        context=context, routing_policy=policy, lifecycle=lifecycle, continuity_routing=routing)
