"""Provider-neutral sequence orchestration regressions; no live effects."""

import pytest

from ai_video.planning.sequence_continuity import (
    build_sequence_video_planning_request,
    causal_state_column_hash,
    prepare_sequence_shot_for_existing_production,
)
from ai_video.production.video_transition import (
    BoundaryKind, CausalDimension, CausalEdgeSemantics, CausalStateChange, CausalTransitionMode,
    ContinuityAnchorBinding, ContinuityAnchorRole, ContinuityObligation, CreativeArtifactIdentity,
)
from ai_video.errors import AiVideoError
from ai_video.planning import (
    AssetRole, AvailableAsset, ProductionPolicyInput, ShotIntentEvidence, VideoPlanner,
    VideoPlanningRequest, require_current_video_plan,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.video_requirement import (
    ActionEndpoint, GenerationIntent, ProviderNeutralGenerationIntentProjection,
    OutputNeed, AudioNeed, QualityNeed, SemanticReferenceRole, SubjectAction, TypedStateReference,
)


def _intent(changes):
    return GenerationIntent(
        open_state=TypedStateReference(kind="typed_hash", state_hash=causal_state_column_hash(
            changes, endpoint="target_open")),
        close_state=TypedStateReference(kind="typed_hash", state_hash=causal_state_column_hash(
            changes, endpoint="source_close")),
        subject_action=SubjectAction(start_state="release completed", progression="continue walking right",
                                    endpoint=ActionEndpoint(state_text="continue right")),
    )


def _planning(loaded, shot, changes, *, roles=(SemanticReferenceRole.FIRST_FRAME,), terminal=None):
    assets = {a.asset_id: a for a in loaded.registry.assets}
    first_ids = tuple(i for r in shot.required_asset_roles if r.role == "first_frame" for i in r.asset_ids)
    selected = []
    if SemanticReferenceRole.FIRST_FRAME in roles and first_ids:
        a = assets[first_ids[0]]
        selected.append(AvailableAsset(role=AssetRole.APPROVED_KEYFRAME,
            asset_id=a.asset_id, asset_sha256=a.sha256, mime_type=a.mime_type, width=a.width,
            height=a.height, size_bytes=a.size_bytes, canonical_owner_id=shot.shot_id,
            canonical_owner_content_hash=shot.content_hash))
    if terminal is not None:
        a = assets[terminal.extracted_asset_id]
        selected.append(AvailableAsset(role=AssetRole.PREVIOUS_SHOT_TERMINAL,
            asset_id=a.asset_id, asset_sha256=a.sha256, mime_type=a.mime_type, width=a.width,
            height=a.height, size_bytes=a.size_bytes, canonical_owner_id=terminal.source_shot_id,
            canonical_owner_content_hash=terminal.source_shot_content_hash))
    if SemanticReferenceRole.IDENTITY in roles:
        c = loaded.characters[0]
        a = assets[c.reference_asset_ids[0]]
        selected.append(AvailableAsset(role=AssetRole.CHARACTER_REFERENCE,
            asset_id=a.asset_id, asset_sha256=a.sha256, mime_type=a.mime_type, width=a.width,
            height=a.height, size_bytes=a.size_bytes, canonical_owner_id=c.character_id,
            canonical_owner_content_hash=c.content_hash))
    if SemanticReferenceRole.SCENE in roles:
        scene = loaded.scenes[0]
        a = assets[scene.visual_reference_asset_ids[0]]
        selected.append(AvailableAsset(role=AssetRole.SCENE_REFERENCE,
            asset_id=a.asset_id, asset_sha256=a.sha256, mime_type=a.mime_type, width=a.width,
            height=a.height, size_bytes=a.size_bytes, canonical_owner_id=scene.scene_id,
            canonical_owner_content_hash=scene.content_hash))
    return VideoPlanningRequest.create(request_id=f"sequence-input-{shot.shot_id}",
        target_shot=shot, character_context=tuple(c for c in loaded.characters if c.character_id in shot.character_ids),
        scene_context=next(s for s in loaded.scenes if s.scene_id == shot.scene_id),
        available_assets=tuple(selected), previous_shot_state=None,
        shot_intent_evidence=ShotIntentEvidence(target_shot_id=shot.shot_id,
            target_shot_content_hash=shot.content_hash, character_action_required=True),
        review_decision=None, production_policy=ProductionPolicyInput(remote_authorized=True, budget_authorized=True),
        generation_intent=ProviderNeutralGenerationIntentProjection.create(generation_intent=_intent(changes),
            output_need=OutputNeed(duration_seconds=1, width=64, height=64, fps=24, container_mime="video/mp4"),
            audio_need=AudioNeed.FORBIDDEN, quality_need=QualityNeed(), semantic_reference_roles=roles),
        planning_contract_version="video-planner/3")


@pytest.fixture
def activated_source(tmp_path):
    return _activated_source(tmp_path)


def _activated_source(tmp_path, *, seal_terminal=True, close_evaluation=True, close_verdict="PASS"):
    """Actual committer/reader lifecycle with existing scripted fixture bytes."""
    from test_production_generated_video_e2e import _runtime, ATTEMPT_ID, FIXTURE
    from test_production_video import _paid_preview, _paid_authorization
    from production_generation_execution_factory import prepare_generation_execution
    from production_project_factory import make_p8_video_candidate_preparer
    from test_production_shot_router import _bound_route_identity, _execution_stack_identity
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video import VideoTaskState
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
    from ai_video.production.generation_feedback import record_attempt_evaluation
    import hashlib

    inputs, provider, template, original, _, _ = _runtime(tmp_path, seal_terminal_frame=seal_terminal,
        activate_second_shot=True, status_events=(VideoTaskState.SUCCEEDED,))
    if close_evaluation:
        from dataclasses import replace
        from test_production_generation_decision import acceptance_policy
        from ai_video.production.generation_recipe import RequirementExpression
        from ai_video.production.hashing import seal_artifact
        from ai_video.production.models import GenerationEvaluationAuthority
        current = inputs.project.qa_policy
        duration = original.inputs.candidates[0].recipe.expressions[0]
        close_hash = causal_state_column_hash(causal_changes(), endpoint="source_close")
        acceptance = acceptance_policy((RequirementExpression(requirement_id="causal-close",
            level="acceptance", stage="raw_generation", dimension="causal_state",
            observable=close_hash, tolerance="exact", measurement="exact close-state evaluation",
            proof="human", intent_paths=("generation_intent.close_state.state_hash",),
            native_text=(close_hash,), production_owner="test_fixture"), duration))
        updated = seal_artifact(current.model_copy(update={"revision": current.revision + 1,
            "content_hash": "0" * 64, "generation_acceptance": acceptance,
            "generation_evaluation_authorities": (*current.generation_evaluation_authorities,
                GenerationEvaluationAuthority(evaluator=current.semantic_authorities[0], proof="human"))}))
        ProductionStateCommitter(tmp_path).activate_qa_policy(updated,
            expected_manifest_revision=inputs.project.manifest.manifest_revision,
            attempt_id="sequence-causal-qa")
        inputs = replace(inputs, project=load_production_project(tmp_path / "project.yaml"))
    from ai_video.production.video import VideoProviderCapabilities
    from ai_video.production._video_capability_fingerprint import capability_variant_fingerprint
    from ai_video.production.shot_router import ProviderRouteIdentity
    variant = provider.capabilities().variants[0].model_copy(update={"max_image_bytes": 4096})
    provider._capabilities = VideoProviderCapabilities.create(provider_name="fake-video", variants=(variant,))
    route = _bound_route_identity(original.decision.routing.provider_bound_request)
    source_route = ProviderRouteIdentity.create(**{**route.model_dump(mode="python", exclude={"route_identity_hash"}),
        "capability_fingerprint": capability_variant_fingerprint(variant)})
    stack = _execution_stack_identity(source_route)
    authored = _planning(inputs.project, inputs.project.shots[0], causal_changes())
    provider._native_prompt_text = "release completed; continue walking right; continue right; " + (
        authored.generation_intent.generation_intent.open_state.state_hash)
    prepared = prepare_generation_execution(project=inputs.project, provider=provider, request=template,
        task_id="sequence-source", compiler_id="generated-video-e2e-fixture", compiler_version="1",
        planning_request=authored, execution_stack_hash=stack.execution_stack_hash,
        use_current_generation_acceptance=close_evaluation)
    preview = _paid_preview(prepared.resolved, attempt_id=ATTEMPT_ID, video_preview=provider.preview(prepared.resolved))
    authorization = _paid_authorization(preview)
    committer = ProductionStateCommitter(tmp_path, video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: authorization.issued_at)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=ATTEMPT_ID, request=prepared.resolved, execution_binding=prepared.binding)
    service.submit_once(attempt_id=ATTEMPT_ID, paid_preview=preview, reservation_id="sequence-source-reservation")
    service.refresh_once(attempt_id=ATTEMPT_ID)
    committer.settle_paid_provider_reservation(attempt_id=ATTEMPT_ID, actual_cost_microunits=1_000_000)
    service.fetch_and_activate(attempt_id=ATTEMPT_ID)
    loaded = load_production_project(tmp_path / "project.yaml")
    candidate = prepared.binding.inputs.candidates[0]
    evaluations = [
        GenerationEvaluationSource(request_hash=prepared.resolved.request_input_hash,
            artifact_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            rubric_hash=candidate.recipe.rubric_hash, qa_policy_content_hash=loaded.qa_policy.content_hash,
            evaluator=loaded.qa_policy.semantic_authorities[0], proof="technical",
            observations=(GenerationObservation(requirement_id="duration", verdict="PASS",
                observation="offline fixture duration PASS; no live semantic qualification"),))]
    if close_evaluation and close_verdict is not None:
        evaluations.append(GenerationEvaluationSource(request_hash=prepared.resolved.request_input_hash,
            artifact_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            rubric_hash=candidate.recipe.rubric_hash, qa_policy_content_hash=loaded.qa_policy.content_hash,
            evaluator=loaded.qa_policy.semantic_authorities[0], proof="human",
            observations=(GenerationObservation(requirement_id="causal-close", verdict=close_verdict,
                observation="scripted close-column verdict; no real human or media qualification"),)))
    record_attempt_evaluation(committer=committer, attempt_id=ATTEMPT_ID, evaluation_sources=tuple(evaluations))
    loaded = load_production_project(tmp_path / "project.yaml")
    from ai_video.production._video_project_reader import load_terminal_frame_evidence
    state = next(a.video_generation_state for a in loaded.manifest.attempts if a.attempt_id == ATTEMPT_ID)
    terminal = (load_terminal_frame_evidence(tmp_path, state.terminal_frame_evidence)
                if state.terminal_frame_evidence is not None else None)
    return dict(root=tmp_path, loaded=loaded, inputs=inputs, provider=provider,
                source_request=authored, binding=prepared.binding, stack=stack, route=source_route,
                terminal=terminal)


def _constraints(loaded):
    from ai_video.production.video import ContinuityConstraintSet
    return ContinuityConstraintSet.create(
        scene_identity=_identity(loaded.scenes[0]).model_dump(mode="python"),
        character_identities=tuple(_identity(c).model_dump(mode="python") for c in loaded.characters),
        camera_axis="camera remains on authored axis", framing="new medium camera angle",
        lighting="unchanged", color="unchanged", motion_direction="right",
        exit_state="prop P detached on ground; release_completed; characters moving right",
        entrance_state="prop P stays detached on ground; no repeated release; moving right")


def _identity(artifact):
    return CreativeArtifactIdentity(artifact_id=artifact.artifact_id,
        revision=artifact.revision, content_hash=artifact.content_hash)


def _prepare_keyframe(source):
    import test_production_generated_video_e2e as e
    loaded = load_production_project(source["root"] / "project.yaml")
    target, terminal = loaded.shots[1], source["terminal"]
    assets = {a.asset_id: a for a in loaded.registry.assets}
    character = loaded.characters[0]
    reference = assets[character.reference_asset_ids[0]]
    constraints = _constraints(loaded)
    request = e.ImageGenerationRequest.create(attempt_id="sequence-c2-keyframe",
        provider_kind="fake-local", model_id="fixture-image-model-1", target_shot_id=target.shot_id,
        target_asset_role="first_frame", prompt_text="explicit typed rightward continuation with new camera angle",
        negative_prompt_text="", parameters=e.ImageProviderParameters(seed=23, width=2, height=1,
            output_format="png", generation_revision=1), references=(
            e.ImageReferenceBinding(role="character", creative_artifact_id=character.artifact_id,
                creative_revision=character.revision, creative_content_hash=character.content_hash,
                asset_id=reference.asset_id, asset_sha256=reference.sha256),
            e.ContinuityTerminalImageReferenceBinding.create(role="continuity_terminal", terminal_frame=terminal,
                asset_id=terminal.extracted_asset_id, asset_sha256=terminal.extracted_sha256,
                target_shot_id=target.shot_id, target_shot_revision=target.revision,
                target_shot_content_hash=target.content_hash, constraints=constraints)),
        base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph)
    preview = e.ImageGenerationPreview.create(request=request,
        reference_total_bytes=reference.size_bytes + terminal.extracted_size_bytes)
    authorization = e.ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="fixture-only", policy_receipt_id="sequence-c2-local-fixture")

    class FixtureProvider:
        def generate(self, candidate, auth, permit):
            assert permit._consume_image_generation_permit(request_fingerprint=candidate.request_fingerprint)
            return e.make_image_provider_result(candidate, auth, e._p7_png())

    e.ProductionStateCommitter(source["root"], image_candidate_preparer=e.make_p7_image_candidate_preparer(
        source["inputs"])).generate_image_asset(request, preview, authorization, FixtureProvider())
    loaded = load_production_project(source["root"] / "project.yaml")
    target = loaded.shots[1]
    keyframe = next(a for a in loaded.registry.assets if a.asset_id == request.output_asset_id)
    return e.HardCutKeyframeBinding.create(role="hard_cut_keyframe", terminal_frame=terminal,
        keyframe_asset_id=keyframe.asset_id, keyframe_asset_sha256=keyframe.sha256,
        keyframe_mime_type=keyframe.mime_type, keyframe_width=keyframe.width, keyframe_height=keyframe.height,
        keyframe_size_bytes=keyframe.size_bytes, keyframe_request_fingerprint=keyframe.input_fingerprint,
        keyframe_provenance_receipt_id=keyframe.creation_receipt_id, target_shot_id=target.shot_id,
        target_shot_revision=target.revision, target_shot_content_hash=target.content_hash, constraints=constraints)


def _edge_inputs(source, *, obligation=ContinuityObligation.FULL_CONTINUITY,
                 boundary=BoundaryKind.HARD_CUT, semantics=CausalEdgeSemantics.DIRECT_CONTINUITY,
                 roles=(SemanticReferenceRole.FIRST_FRAME,), prepare_keyframe=True):
    from ai_video.production.shot_router import VideoGenerationLifecycleEnvelope
    from ai_video.production.video import ContinuityReferenceBinding
    keyframe = (_prepare_keyframe(source) if prepare_keyframe and boundary is BoundaryKind.HARD_CUT
                and obligation is ContinuityObligation.FULL_CONTINUITY else None)
    loaded = load_production_project(source["root"] / "project.yaml")
    previous = source["source_request"].target_shot
    changes = causal_changes()
    anchors = tuple(ContinuityAnchorBinding(role=role, source_kind="planned_derivation",
        source_identity=f"explicit-{role.value}-preparation", content_hash=canonical_sha256({"anchor": role.value}),
        evidence_fingerprint=canonical_sha256({"preparation": role.value}))
        for role in sorted(ContinuityAnchorRole, key=lambda r: r.value))
    if obligation is ContinuityObligation.SUBSTANTIAL_RESET:
        anchors = ()
    if obligation is ContinuityObligation.IDENTITY_STYLE_CARRYOVER:
        anchors = tuple(a for a in anchors if a.role is ContinuityAnchorRole.REFERENCE)
    if obligation is ContinuityObligation.FULL_CONTINUITY:
        frame_id = (keyframe.keyframe_asset_id if keyframe else
                    source["terminal"].extracted_asset_id if source["terminal"] else None)
        if frame_id is not None:
            frame = next(a for a in loaded.registry.assets if a.asset_id == frame_id)
            anchors = tuple(ContinuityAnchorBinding(role=a.role, source_kind="registered_asset",
                source_identity=frame.asset_id, content_hash=frame.sha256,
                evidence_fingerprint=frame.input_fingerprint, materialization_receipt_id=frame.creation_receipt_id)
                if a.role is ContinuityAnchorRole.FIRST_FRAME else a for a in anchors)
    lifecycle = VideoGenerationLifecycleEnvelope(generation_id="sequence-target-generation",
        target_asset_role=loaded.shots[1].required_asset_roles[0].role, base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry, base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(loaded.shots[1].artifact_id, *((source["terminal"].extracted_asset_id,) if source["terminal"] else ()),
            *((source["terminal"].source_shot_id, source["terminal"].source_video_asset_id)
              if source["terminal"] and boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE else ()),
            keyframe.keyframe_asset_id if keyframe else next(i for r in loaded.shots[1].required_asset_roles
                                                          if r.role == "first_frame" for i in r.asset_ids)),
        output_asset_id="sequence-target-video",
        execution_stack_hash=source["stack"].execution_stack_hash, hard_cut_keyframe_binding=keyframe,
        continuity_binding=ContinuityReferenceBinding.create(role="first_frame",
            terminal_frame=source["terminal"], target_shot_id=loaded.shots[1].shot_id,
            target_shot_revision=loaded.shots[1].revision, target_shot_content_hash=loaded.shots[1].content_hash,
            constraints=_constraints(loaded)) if boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE else None)
    return dict(project_root=source["root"], current_request=_planning(loaded, loaded.shots[1], changes,
        roles=roles, terminal=source["terminal"] if boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE else None),
        continuity_obligation=obligation, boundary_kind=boundary, causal_edge_semantics=semantics,
        source_shot=CreativeArtifactIdentity(artifact_id=previous.artifact_id, revision=previous.revision,
                                           content_hash=previous.content_hash),
        source_generation_intent_hash=source["source_request"].generation_intent.projection_hash,
        causal_state_changes=changes,
        required_carryover_dimensions=(() if obligation is ContinuityObligation.SUBSTANTIAL_RESET else
            tuple(sorted(d.value for d in CausalDimension)) if obligation is ContinuityObligation.FULL_CONTINUITY else ("identity",)),
        anchors=anchors, source_execution_stack=source["stack"], destination_execution_stack=source["stack"],
        destination_route=source["route"], lifecycle=lifecycle,
        take_id="continuous-take-1" if boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE else None)


def test_hard_cut_full_materializes_existing_state_and_policy(activated_source):
    inputs = _edge_inputs(activated_source)
    request, routing = build_sequence_video_planning_request(**inputs)
    assert request.previous_shot_state.is_angle_change
    assert not request.previous_shot_state.semantic_jump
    policy = request.continuity_transition_policy
    assert policy == routing.transition_policy
    assert policy.boundary_kind is BoundaryKind.HARD_CUT
    assert policy.continuity_obligation is ContinuityObligation.FULL_CONTINUITY
    assert policy.causal_edge_semantics is CausalEdgeSemantics.DIRECT_CONTINUITY
    assert policy.causal_state_changes == causal_changes()
    plan = VideoPlanner().plan(request)
    assert plan.continuity_mode.value == "reference"
    assert plan.generation_mode.value == "image_to_video"
    assert require_current_video_plan(current_request=request, plan=plan).requirement == plan.generation_requirement


def test_continuous_action_uses_original_terminal(activated_source):
    request, routing = build_sequence_video_planning_request(**_edge_inputs(activated_source,
        boundary=BoundaryKind.WITHIN_CONTINUOUS_TAKE, roles=()))
    assert request.previous_shot_state.is_same_action
    assert not request.previous_shot_state.is_angle_change
    assert request.previous_shot_state.has_terminal_frame_asset_id == activated_source["terminal"].extracted_asset_id
    assert VideoPlanner().plan(request).continuity_mode.value == "exact_terminal"
    assert require_current_video_plan(current_request=request, plan=VideoPlanner().plan(request))


@pytest.mark.parametrize("defect", ["missing_causal", "missing_intent", "stale_intent", "artifact", "revision", "hash", "target_intent"])
def test_incomplete_or_stale_edge_never_becomes_none(activated_source, defect):
    inputs = _edge_inputs(activated_source)
    if defect == "missing_causal":
        inputs["causal_state_changes"] = causal_changes()[:-1]
    elif defect in {"missing_intent", "stale_intent"}:
        inputs["source_generation_intent_hash"] = None if defect == "missing_intent" else "f" * 64
    elif defect in {"artifact", "revision", "hash"}:
        field = {"artifact": "artifact_id", "revision": "revision", "hash": "content_hash"}[defect]
        inputs["source_shot"] = inputs["source_shot"].model_copy(update={field:
            99 if defect == "revision" else "other-source" if defect == "artifact" else "f" * 64})
    else:
        inputs["current_request"] = inputs["current_request"].model_copy(update={
            "generation_intent": inputs["current_request"].generation_intent.model_copy(update={"projection_hash": "f" * 64})})
    with pytest.raises(AiVideoError) as blocked:
        build_sequence_video_planning_request(**inputs)
    assert blocked.value.code.value == "planning_preflight_blocked"


def test_previous_exists_but_explicit_independent_is_legal(activated_source):
    current = _edge_inputs(activated_source)["current_request"]
    request, routing = build_sequence_video_planning_request(project_root=activated_source["root"],
        current_request=current, continuity_obligation=None)
    assert routing is None and request.previous_shot_state is None
    assert VideoPlanner().plan(request).continuity_mode.value == "none"


def test_scene_reset_allows_none(activated_source):
    request, routing = build_sequence_video_planning_request(**_edge_inputs(activated_source,
        obligation=ContinuityObligation.SUBSTANTIAL_RESET, boundary=BoundaryKind.SCENE_BOUNDARY,
        semantics=CausalEdgeSemantics.SCENE_RESET))
    plan = VideoPlanner().plan(request)
    assert request.previous_shot_state is None
    assert plan.continuity_mode.value == "none"
    assert require_current_video_plan(current_request=request, plan=plan)


def test_identity_only_retains_reference_route(activated_source):
    request, routing = build_sequence_video_planning_request(**_edge_inputs(activated_source,
        obligation=ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
        roles=(SemanticReferenceRole.IDENTITY, SemanticReferenceRole.SCENE)))
    plan = VideoPlanner().plan(request)
    assert plan.continuity_mode.value == "reference"
    assert plan.generation_mode.value == "reference_to_video"
    assert require_current_video_plan(current_request=request, plan=plan)


def _context(loaded, request, plan, terminal):
    from ai_video.production.shot_router import ShotRoutingContext, RouterAssetIdentity, ContinuityMode, MotionRequirement
    from ai_video.production.models import VisualStrategy
    from ai_video.production.video import VideoGenerationMode

    def asset(identity, role, owner=None):
        return RouterAssetIdentity(role=role, asset_id=identity.asset_id, asset_sha256=identity.sha256,
            mime_type=identity.mime_type, size_bytes=identity.size_bytes, width=identity.width,
            height=identity.height, source_registry_revision_id=loaded.registry.revision_id,
            canonical_owner_kind="character" if role == "character_reference" else "scene" if owner else None,
            canonical_owner_id=owner.character_id if role == "character_reference" else owner.scene_id if owner else None,
            canonical_owner_content_hash=owner.content_hash if owner else None)

    assets = {a.asset_id: a for a in loaded.registry.assets}
    keyframe = next((a for a in request.available_assets if a.role is AssetRole.APPROVED_KEYFRAME), None)
    return ShotRoutingContext(activated_shot=request.target_shot, target_shot_id=request.target_shot.shot_id,
        target_shot_revision=request.target_shot.revision, target_shot_content_hash=request.target_shot.content_hash,
        storyboard_revision=loaded.storyboard.revision, storyboard_content_hash=loaded.storyboard.content_hash,
        selected_registry_revision_id=loaded.registry.revision_id,
        character_bible_content_hashes=tuple(c.content_hash for c in request.character_context),
        scene_content_hash=request.scene_context.content_hash,
        important_character_ids=tuple(c.character_id for c in request.character_context),
        canonical_character_references=tuple(asset(assets[c.reference_asset_ids[0]], "character_reference", c)
            for c in request.character_context),
        canonical_scene_reference=None,
        approved_existing_video=None, shot_keyframe=asset(assets[keyframe.asset_id], "first_frame") if keyframe else None,
        upstream_terminal=asset(assets[terminal.extracted_asset_id], "continuity_terminal") if terminal else None,
        motion_requirement=MotionRequirement.CHARACTER_ACTION, continuity_mode=ContinuityMode(plan.continuity_mode.value),
        semantic_continuity_state=None, allowed_visual_strategies=tuple(VisualStrategy),
        allowed_generation_modes=tuple(VideoGenerationMode))


def test_canonical_handoff_consumes_policy_and_routes_valid_c2(activated_source, monkeypatch):
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from ai_video.production.shot_router import VideoGenerationResolver
    from test_production_shot_router import _policy
    inputs = _edge_inputs(activated_source)
    from ai_video.quality_gates import ShotReadinessGate
    evaluated = []
    original_evaluate = ShotReadinessGate.evaluate

    def observe_gate(self, request):
        evaluated.append(request)
        return original_evaluate(self, request)

    monkeypatch.setattr(ShotReadinessGate, "evaluate", observe_gate)

    def production_handoff(**handoff):
        request, plan = handoff["current_request"], handoff["plan"]
        routing = handoff["continuity_routing"]
        loaded = load_production_project(activated_source["root"] / "project.yaml")
        context = _context(loaded, request, plan, activated_source["terminal"])
        current = require_feedback_context(loaded=loaded, planning_request=request, video_plan=plan,
            context=context, routing_policy=_policy(remote_authorized=True, budget_authorized=True),
            lifecycle=handoff["lifecycle"], continuity_routing=handoff["continuity_routing"])
        assert current["projection"] == handoff["generation_requirement"]
        assert handoff["continuity_transition_policy"] == request.continuity_transition_policy
        assert current["projection"].verified_source_request_content_hash == request.request_content_hash
        provider = activated_source["provider"]
        route = activated_source["route"]
        result = VideoGenerationResolver()._bind_requirement(**current,
            provider_profile=route.provider_profile, capabilities=provider.capabilities(),
            selected_capability_id=route.capability_id, output_requirement=activated_source["binding"].compiled_request.effective_output,
            compiler_contract=route.compiler_contract)
        assert result.provider_bound_request is not None, (result.decision.reason_codes, result.decision.rationale)
        assert result.provider_bound_request.mode.value == "image_to_video"
        from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
        from ai_video.production.state_commit import ProductionStateCommitter
        prepared = GenerationFeedbackOrchestrator.for_project(
            committer=ProductionStateCommitter(activated_source["root"]),
            targets=(RegisteredGenerationTarget(provider=provider, profile=route.provider_profile,
                compiler_contract=route.compiler_contract, output_requirement=activated_source["binding"].compiled_request.effective_output),),
            context_loader=lambda loaded: current, policy=activated_source["binding"].inputs.policy,
        ).prepare(limits=activated_source["binding"].inputs.limits.model_copy(update={
            "task_id": "sequence-target",
            "allowed_remote_candidates": (f"{route.provider_name}/{route.capability_id}",)}))
        assert prepared.resolved_request is not None, (prepared.decision.disposition, prepared.decision.rationale)
        assert prepared.execution_binding.continuity_routing == handoff["continuity_routing"]
        prepared.execution_binding.validate_current_project(loaded)
        from ai_video.production.shot_router import ContinuityProviderRouteBinding
        for change in ("activation", "source_intent", "target_intent"):
            values = {name: getattr(routing, name) for name in type(routing).model_fields if name != "binding_hash"}
            if change == "activation":
                values["source_activation_registry"] = routing.previous_provider_bound_request.lifecycle.base_registry
            else:
                policy_values = {name: getattr(routing.transition_policy, name)
                    for name in type(routing.transition_policy).model_fields if name != "policy_hash"}
                policy_values[f"{change.split('_')[0]}_generation_intent_hash"] = "f" * 64
                from ai_video.production.video_transition import ContinuityTransitionPolicy
                values["transition_policy"] = ContinuityTransitionPolicy.create(**policy_values)
            stale = ContinuityProviderRouteBinding.create(**values)
            with pytest.raises(ValueError, match="activation or intent"):
                VideoGenerationResolver().resolve_requirement(**{**current, "continuity_routing": stale},
                    inputs=prepared.inputs, source_project=loaded)
            with pytest.raises(ValueError, match="activation or intent"):
                prepared.execution_binding.model_copy(update={"continuity_routing": stale}).validate_current_project(loaded)
        return request, current

    request, current = prepare_sequence_shot_for_existing_production(production_handoff=production_handoff, **inputs)
    assert evaluated[0].contract_version == "shot-readiness-gate/2"
    assert evaluated[0].continuity_transition_policy == request.continuity_transition_policy
    with pytest.raises(ValueError, match="exact continuity routing"):
        require_feedback_context(loaded=load_production_project(activated_source["root"] / "project.yaml"),
            planning_request=request, video_plan=VideoPlanner().plan(request), context=current["context"],
            routing_policy=current["policy"], lifecycle=current["lifecycle"])


def test_incomplete_edge_calls_no_production_handoff(activated_source):
    inputs = _edge_inputs(activated_source, prepare_keyframe=False)
    inputs["causal_state_changes"] = causal_changes()[:-1]
    with pytest.raises(AiVideoError):
        prepare_sequence_shot_for_existing_production(**inputs,
            production_handoff=lambda **kw: pytest.fail("incomplete edge reached Production"))


def test_legacy_request_omits_absent_policy_in_nested_serialization(activated_source):
    from ai_video.quality_gates import ShotReadinessRequest
    request = _edge_inputs(activated_source, prepare_keyframe=False)["current_request"]
    readiness = ShotReadinessRequest.create(request_id="legacy-omission", current_request=request,
                                           plan=VideoPlanner().plan(request))
    assert "continuity_transition_policy" not in readiness.model_dump(mode="json")["current_request"]
    assert VideoPlanningRequest.model_validate(request.model_dump(mode="json")).request_content_hash == request.request_content_hash


def test_hard_cut_full_missing_c2_blocks_before_planner(activated_source):
    with pytest.raises(AiVideoError) as blocked:
        build_sequence_video_planning_request(**_edge_inputs(activated_source, prepare_keyframe=False))
    assert "existing C2 keyframe preparation" in blocked.value.technical_detail


def test_soft_only_metaso_full_is_still_blocked():
    from test_production_shot_router import _metaso_continuity_fixture
    from ai_video.production.shot_router import VideoGenerationResolver, RouterReasonCode
    fixture = _metaso_continuity_fixture()
    result = VideoGenerationResolver()._bind_requirement(**fixture)
    assert RouterReasonCode.CONTINUITY_FRAME_CONDITIONING_REQUIRED in result.decision.reason_codes


def causal_changes():
    values = {
        CausalDimension.CHARACTER_PRESENCE: "actor-a and actor-b present",
        CausalDimension.PROP_IDENTITY: "prop-P detached",
        CausalDimension.PROP_HOLDER: "ground; no holder",
        CausalDimension.HAND_CONTACT: "no hand contact with P",
        CausalDimension.PROP_FUNCTIONAL_STATE: "released",
        CausalDimension.ACTION_PHASE: "release_completed; do not repeat release",
        CausalDimension.GAZE_TARGET: "toward path on right",
        CausalDimension.DIALOGUE_TURN: "explicitly no dialogue",
        CausalDimension.SCREEN_MOTION_AXIS: "right",
        CausalDimension.AUDIO_BRIDGE: "continuous footsteps",
    }
    return tuple(CausalStateChange(
        dimension=dimension, source_close=values[dimension], target_open=values[dimension],
        transition_mode=CausalTransitionMode.CARRY,
    ) for dimension in sorted(CausalDimension, key=lambda d: d.value))


def test_complete_causal_columns_are_deterministic_and_equal():
    changes = causal_changes()
    assert causal_state_column_hash(changes, endpoint="source_close") == causal_state_column_hash(
        changes, endpoint="target_open")
    assert len(causal_state_column_hash(changes, endpoint="target_open")) == 64


def test_missing_causal_dimension_cannot_be_hashed_as_complete_truth():
    with pytest.raises(ValueError, match="complete causal"):
        causal_state_column_hash(causal_changes()[:-1], endpoint="source_close")


def test_full_edge_cannot_accept_technical_only_source(tmp_path):
    source = _activated_source(tmp_path, close_evaluation=False)
    with pytest.raises(AiVideoError, match="authoring evidence"):
        build_sequence_video_planning_request(**_edge_inputs(source))


@pytest.mark.parametrize("verdict", [None, "FAIL", "NOT_EVALUATED"])
def test_full_edge_requires_observed_causal_close_pass(tmp_path, verdict):
    source = _activated_source(tmp_path, close_verdict=verdict)
    with pytest.raises(AiVideoError, match="authoring evidence"):
        build_sequence_video_planning_request(**_edge_inputs(source))


def test_feedback_rejects_changed_destination_stack(activated_source):
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from test_production_shot_router import _policy
    inputs = _edge_inputs(activated_source)
    request, routing = build_sequence_video_planning_request(**inputs)
    plan = VideoPlanner().plan(request)
    loaded = load_production_project(activated_source["root"] / "project.yaml")
    with pytest.raises(ValueError, match="stack"):
        require_feedback_context(loaded=loaded, planning_request=request, video_plan=plan,
            context=_context(loaded, request, plan, activated_source["terminal"]),
            routing_policy=_policy(), continuity_routing=routing,
            lifecycle=inputs["lifecycle"].model_copy(update={"execution_stack_hash": "f" * 64}))


def test_public_resolver_requires_activation_proof_for_new_snapshot_pointer():
    from test_production_shot_router import _metaso_continuity_fixture
    from ai_video.production.shot_router import VideoGenerationResolver, ContinuityProviderRouteBinding
    fixture = _metaso_continuity_fixture(ContinuityObligation.IDENTITY_STYLE_CARRYOVER)
    routing = fixture["continuity_routing"]
    routing = ContinuityProviderRouteBinding.create(**{
        **{name: getattr(routing, name) for name in type(routing).model_fields if name != "binding_hash"},
        "source_activation_registry": routing.previous_provider_bound_request.lifecycle.base_registry})
    with pytest.raises(ValueError, match="activation"):
        VideoGenerationResolver().resolve_requirement(
            **{k: fixture[k] for k in ("projection", "context", "policy", "lifecycle")},
            continuity_routing=routing, inputs=None)


def test_typed_identity_carryover_needs_no_terminal():
    from test_production_shot_router import _metaso_continuity_fixture
    from ai_video.production.shot_router import VideoGenerationResolver
    fixture = _metaso_continuity_fixture(ContinuityObligation.IDENTITY_STYLE_CARRYOVER)
    fixture["context"] = fixture["context"].model_copy(update={
        "upstream_terminal": None, "semantic_continuity_state": None})
    result = VideoGenerationResolver()._bind_requirement(**fixture)
    assert result.provider_bound_request is not None, result.decision.reason_codes


def test_sequence_identity_carryover_without_terminal_passes_readiness(tmp_path):
    source = _activated_source(tmp_path, seal_terminal=False)
    inputs = _edge_inputs(source, obligation=ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
        roles=(SemanticReferenceRole.IDENTITY, SemanticReferenceRole.SCENE))
    request, routing = prepare_sequence_shot_for_existing_production(**inputs,
        production_handoff=lambda **handoff: (handoff["current_request"], handoff["continuity_routing"]))
    assert request.previous_shot_state.has_terminal_frame_asset_id is None
    assert routing.transition_policy.continuity_obligation is ContinuityObligation.IDENTITY_STYLE_CARRYOVER
    assert VideoPlanner().plan(request).generation_mode.value == "reference_to_video"


def test_full_without_terminal_stops_before_handoff(tmp_path):
    source = _activated_source(tmp_path, seal_terminal=False)
    with pytest.raises(AiVideoError, match="authoring evidence"):
        prepare_sequence_shot_for_existing_production(**_edge_inputs(source, prepare_keyframe=False),
            production_handoff=lambda **kw: pytest.fail("FULL without terminal reached Production"))


def test_legacy_pointer_omission_cannot_authorize_new_production(tmp_path, monkeypatch):
    from ai_video.production.video_transition import ContinuityTransitionPolicy
    from ai_video.production.shot_router import ContinuityProviderRouteBinding
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
    from ai_video.production.state_commit import ProductionStateCommitter
    from test_production_shot_router import _policy
    source = _activated_source(tmp_path, close_evaluation=False)
    inputs = _edge_inputs(source, boundary=BoundaryKind.WITHIN_CONTINUOUS_TAKE, roles=())
    seed, lifecycle, loaded = inputs["current_request"], inputs["lifecycle"], source["loaded"]
    policy = ContinuityTransitionPolicy.create(schema_version="2", policy_id="legacy-omission",
        project=loaded.manifest.active_project, registry=loaded.manifest.active_registry,
        source_shot=inputs["source_shot"], target_shot=_identity(seed.target_shot),
        boundary_kind=inputs["boundary_kind"], continuity_obligation=inputs["continuity_obligation"],
        take_id=inputs["take_id"], source_execution_stack_hash=source["stack"].execution_stack_hash,
        destination_execution_stack_hash=source["stack"].execution_stack_hash,
        continuity_grade="c4_native_boundary_motion", required_carryover_dimensions=inputs["required_carryover_dimensions"],
        anchors=inputs["anchors"], qa_policy_hash=loaded.qa_policy.content_hash,
        authoring_evidence_hash=canonical_sha256({"untrusted": "legacy re-sealed proposal"}),
        source_generation_intent_hash=inputs["source_generation_intent_hash"],
        target_generation_intent_hash=seed.generation_intent.projection_hash,
        causal_edge_semantics=inputs["causal_edge_semantics"], causal_state_changes=inputs["causal_state_changes"])
    current_previous = source["binding"].decision.routing.provider_bound_request
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    current_previous = ProviderBoundVideoRequest.create(**{
        **{name: getattr(current_previous, name) for name in type(current_previous).model_fields
           if name != "provider_bound_request_hash"},
        "lifecycle": current_previous.lifecycle.model_copy(update={"base_project": lifecycle.base_project,
            "base_registry": lifecycle.base_registry, "base_dependency_graph": lifecycle.base_dependency_graph})})
    routing = ContinuityProviderRouteBinding.create(transition_policy=policy,
        previous_shot=source["source_request"].target_shot, previous_provider_bound_request=current_previous,
        source_route=source["route"], destination_route=source["route"],
        source_execution_stack=source["stack"], destination_execution_stack=source["stack"])
    state = VideoPlanner.derive_previous_shot_state(previous_shot=source["source_request"].target_shot,
        target_shot=seed.target_shot, previous_generation_intent_hash=inputs["source_generation_intent_hash"],
        is_same_action=True, is_angle_change=False, semantic_jump=False,
        has_terminal_frame_asset_id=source["terminal"].extracted_asset_id)
    request = VideoPlanningRequest.create(**{**{n: getattr(seed, n) for n in type(seed).model_fields
        if n != "request_content_hash"}, "previous_shot_state": state, "continuity_transition_policy": policy})
    plan = VideoPlanner().plan(request)
    current = dict(projection=require_current_video_plan(current_request=request, plan=plan),
        context=_context(loaded, request, plan, source["terminal"]),
        policy=_policy(remote_authorized=True, budget_authorized=True), lifecycle=lifecycle, continuity_routing=routing)
    from ai_video.production.shot_router import VideoGenerationResolver
    captured = {}
    resolve = VideoGenerationResolver.resolve_requirement

    def capture(self, **kwargs):
        captured.update(kwargs)
        return resolve(self, **kwargs)

    monkeypatch.setattr(VideoGenerationResolver, "resolve_requirement", capture)
    compile_fixture = source["provider"].compile_request
    monkeypatch.setattr(source["provider"], "compile_request", lambda *_a: pytest.fail("legacy route reached compiler"))
    route = source["route"]
    with pytest.raises(ValueError, match="activation pointer"):
        GenerationFeedbackOrchestrator.for_project(committer=ProductionStateCommitter(source["root"]),
            targets=(RegisteredGenerationTarget(provider=source["provider"], profile=route.provider_profile,
                compiler_contract=route.compiler_contract, output_requirement=source["binding"].compiled_request.effective_output),),
            context_loader=lambda loaded: current, policy=source["binding"].inputs.policy,
        ).prepare(limits=source["binding"].inputs.limits.model_copy(update={"task_id": "legacy-omission",
            "allowed_remote_candidates": (f"{route.provider_name}/{route.capability_id}",)}))
    from ai_video.production.generation_decision import resolve_generation_decision
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    pure = resolve_generation_decision(VideoGenerationResolver(), **current, inputs=captured["inputs"])
    compiled = compile_fixture(pure.routing.provider_bound_request, current["projection"].requirement)
    legacy_binding = GenerationDecisionExecutionBinding.create(**current, inputs=captured["inputs"],
        decision=pure, compiled_request=source["provider"].resolve(compiled.request))
    with pytest.raises(ValueError, match="activation pointer"):
        legacy_binding.validate_current_project(loaded)


def _cross_stack_inputs(source):
    from ai_video.production.shot_router import ProviderRouteIdentity
    from ai_video.production.video import VideoProviderCapabilities
    from ai_video.production._video_capability_fingerprint import capability_variant_fingerprint
    from test_production_shot_router import _execution_stack_identity
    inputs = _edge_inputs(source)
    variant = source["provider"].capabilities().variants[0].model_copy(update={
        "model_id": "sequence-destination-model", "capability_id": "sequence-destination-i2v"})
    source["provider"]._capabilities = VideoProviderCapabilities.create(
        provider_name=source["route"].provider_name, variants=(variant,))
    route = ProviderRouteIdentity.create(**{
        **{n: getattr(source["route"], n) for n in type(source["route"]).model_fields
           if n != "route_identity_hash"},
        "model_id": variant.model_id, "capability_id": variant.capability_id,
        "capability_fingerprint": capability_variant_fingerprint(variant)})
    stack = _execution_stack_identity(route)
    inputs.update(destination_route=route, destination_execution_stack=stack,
        lifecycle=inputs["lifecycle"].model_copy(update={"execution_stack_hash": stack.execution_stack_hash}),
        required_carryover_dimensions=tuple(sorted(set(inputs["required_carryover_dimensions"])
            | {"camera_velocity", "screen_axis", "subject_position"})))
    request = inputs["current_request"]
    intent = request.generation_intent
    authored = intent.generation_intent.model_copy(update={
        "space_continuity": intent.generation_intent.space_continuity.model_copy(update={
            "subject_position": "right", "screen_direction": "right"}),
        "axis_continuity": intent.generation_intent.axis_continuity.model_copy(update={
            "camera_axis": "fixed axis", "framing_continuity": "same subject"})})
    intent = ProviderNeutralGenerationIntentProjection.create(**{
        **{n: getattr(intent, n) for n in type(intent).model_fields if n != "projection_hash"},
        "generation_intent": authored})
    inputs["current_request"] = VideoPlanningRequest.create(**{
        **{n: getattr(request, n) for n in type(request).model_fields if n != "request_content_hash"},
        "generation_intent": intent})
    source["provider"]._native_prompt_text += " right fixed axis same subject"
    return inputs


@pytest.mark.parametrize("boundary", [BoundaryKind.WITHIN_CONTINUOUS_TAKE, BoundaryKind.HARD_CUT])
def test_same_stack_full_inherits_destination_without_caller_selection(activated_source, boundary):
    inputs = _edge_inputs(activated_source, boundary=boundary,
        roles=(SemanticReferenceRole.CONTINUITY_TERMINAL,) if boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE
              else (SemanticReferenceRole.FIRST_FRAME,))
    inputs.pop("destination_route")
    inputs.pop("destination_execution_stack")
    request, routing = build_sequence_video_planning_request(**inputs)
    assert routing.destination_route == routing.source_route == activated_source["route"]
    assert routing.destination_execution_stack == routing.source_execution_stack
    plan = VideoPlanner().plan(request)
    assert plan.continuity_mode.value == (
        "exact_terminal" if boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE else "reference")
    assert not {"provider_name", "model_id", "provider_profile", "capability_id"}.intersection(
        type(plan.generation_requirement).model_fields)


def test_cross_stack_bare_route_stops_before_planner_or_handoff(activated_source, monkeypatch):
    inputs = _cross_stack_inputs(activated_source)
    monkeypatch.setattr(VideoPlanner, "plan", lambda *_: pytest.fail("bare route reached Planner"))
    with pytest.raises(AiVideoError, match="authoring evidence"):
        prepare_sequence_shot_for_existing_production(**inputs,
            production_handoff=lambda **kw: pytest.fail("bare route reached handoff"))


def _prepare_sequence_generation(source, inputs, request, routing=None):
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
    from ai_video.production.state_commit import ProductionStateCommitter
    from test_production_shot_router import _policy
    plan = VideoPlanner().plan(request)
    route = inputs["destination_route"]

    def current(loaded):
        return require_feedback_context(loaded=loaded, planning_request=request, video_plan=plan,
            context=_context(loaded, request, plan, source["terminal"]),
            routing_policy=_policy(remote_authorized=True, budget_authorized=True),
            lifecycle=inputs["lifecycle"], continuity_routing=routing)

    return GenerationFeedbackOrchestrator.for_project(committer=ProductionStateCommitter(source["root"]),
        targets=(RegisteredGenerationTarget(provider=source["provider"], profile=route.provider_profile,
            compiler_contract=route.compiler_contract, output_requirement=source["binding"].compiled_request.effective_output),),
        context_loader=current, policy=source["binding"].inputs.policy).prepare(
            limits=source["binding"].inputs.limits.model_copy(update={"task_id": "sequence-destination",
                "allowed_remote_candidates": tuple(f"{route.provider_name}/{v.capability_id}"
                    for v in source["provider"].capabilities().variants)}))


def test_cross_stack_consumes_prior_canonical_selection_and_reselects_final_requirement(activated_source):
    inputs = _cross_stack_inputs(activated_source)
    selected = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    assert selected.execution_binding is not None, (selected.decision.disposition, selected.compilation)
    assert selected.execution_binding.continuity_routing is None
    assert selected.execution_binding.selected_provider_route == inputs["destination_route"]
    inputs["destination_selection_binding"] = selected.execution_binding
    asserted_route = inputs.pop("destination_route")
    request, routing = build_sequence_video_planning_request(**inputs)
    assert routing.destination_route == asserted_route
    assert routing.destination_selection_binding == selected.execution_binding.model_dump(mode="json")
    inputs["destination_route"] = asserted_route
    prepared = _prepare_sequence_generation(activated_source, inputs, request, routing)
    assert prepared.execution_binding is not None, (prepared.decision.disposition, prepared.compilation)
    assert prepared.execution_binding.projection != selected.execution_binding.projection
    assert prepared.execution_binding.selected_provider_route == asserted_route
    assert prepared.execution_binding.lifecycle.execution_stack_hash == routing.transition_policy.destination_execution_stack_hash
    prepared.execution_binding.validate_current_project(load_production_project(activated_source["root"] / "project.yaml"))


def test_same_stack_caller_cannot_forge_destination_route(activated_source):
    from ai_video.production.shot_router import ProviderRouteIdentity
    inputs = _edge_inputs(activated_source)
    route = inputs["destination_route"]
    inputs["destination_route"] = ProviderRouteIdentity.create(**{
        **{n: getattr(route, n) for n in type(route).model_fields if n != "route_identity_hash"},
        "model_id": "caller-selected-model"})
    with pytest.raises(AiVideoError) as stopped:
        build_sequence_video_planning_request(**inputs)
    assert "inherit" in stopped.value.technical_detail


@pytest.mark.parametrize("change", ["route", "stack", "lifecycle", "seed", "decision", "target"])
def test_cross_stack_rejects_stale_or_tampered_selection(activated_source, change):
    inputs = _cross_stack_inputs(activated_source)
    selected = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    assert selected.execution_binding is not None, (selected.decision.disposition, selected.compilation)
    proof = selected.execution_binding
    if change == "route":
        inputs["destination_route"] = activated_source["route"]
    elif change == "stack":
        from ai_video.production.video_execution_stack import GenerationExecutionStackIdentity
        stack = inputs["destination_execution_stack"]
        inputs["destination_execution_stack"] = GenerationExecutionStackIdentity.create(**{
            **{n: getattr(stack, n) for n in type(stack).model_fields if n != "execution_stack_hash"},
            "deployment_identity": "different-deployment"})
    elif change == "lifecycle":
        inputs["lifecycle"] = inputs["lifecycle"].model_copy(update={"output_asset_id": "different-output"})
    elif change == "seed":
        request = inputs["current_request"]
        inputs["current_request"] = VideoPlanningRequest.create(**{
            **{n: getattr(request, n) for n in type(request).model_fields if n != "request_content_hash"},
            "production_policy": request.production_policy.model_copy(update={
                "accept_static_image_fallback": not request.production_policy.accept_static_image_fallback})})
    elif change == "target":
        proof = activated_source["binding"]
    else:
        proof = proof.model_copy(update={"decision": proof.decision.model_copy(update={"selected_candidate_id": "forged"})})
    inputs["destination_selection_binding"] = proof
    with pytest.raises(AiVideoError, match="authoring evidence"):
        build_sequence_video_planning_request(**inputs)


def test_cross_stack_legacy_binding_cannot_bypass_production_reopen(activated_source):
    from ai_video.production.shot_router import ContinuityProviderRouteBinding, VideoGenerationResolver
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from test_production_shot_router import _policy
    inputs = _cross_stack_inputs(activated_source)
    initial = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    inputs["destination_selection_binding"] = initial.execution_binding
    request, routing = build_sequence_video_planning_request(**inputs)
    prepared = _prepare_sequence_generation(activated_source, inputs, request, routing)
    legacy = ContinuityProviderRouteBinding.create(**{
        **{n: getattr(routing, n) for n in type(routing).model_fields
           if n not in {"binding_hash", "destination_selection_binding"}}})
    assert "destination_selection_binding" not in legacy.model_dump(mode="json")
    loaded = load_production_project(activated_source["root"] / "project.yaml")
    binding = prepared.execution_binding
    with pytest.raises(ValueError, match="prior Router execution binding"):
        require_feedback_context(loaded=loaded, planning_request=request, video_plan=VideoPlanner().plan(request),
            context=binding.context, routing_policy=_policy(), lifecycle=inputs["lifecycle"], continuity_routing=legacy)
    with pytest.raises(ValueError, match="prior Router execution binding"):
        VideoGenerationResolver().resolve_requirement(projection=binding.projection, context=binding.context,
            policy=binding.policy, lifecycle=binding.lifecycle, inputs=binding.inputs,
            continuity_routing=legacy, source_project=loaded)
    with pytest.raises(ValueError, match="prior Router execution binding"):
        binding.model_copy(update={"continuity_routing": legacy}).validate_current_project(loaded)


@pytest.mark.parametrize("entrypoint", ["feedback", "resolver", "execution"])
def test_cross_stack_other_seed_selection_cannot_bypass_production_reopen(activated_source, entrypoint):
    from ai_video.production.generation_decision import resolve_generation_decision
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.shot_router import ContinuityProviderRouteBinding, VideoGenerationResolver
    inputs = _cross_stack_inputs(activated_source)
    seed = inputs["current_request"]
    initial = _prepare_sequence_generation(activated_source, inputs, seed)
    inputs["destination_selection_binding"] = initial.execution_binding
    request, routing = build_sequence_video_planning_request(**inputs)
    prepared = _prepare_sequence_generation(activated_source, inputs, request, routing)
    binding = prepared.execution_binding
    other_seed = VideoPlanningRequest.create(**{
        **{n: getattr(seed, n) for n in type(seed).model_fields if n != "request_content_hash"},
        "production_policy": seed.production_policy.model_copy(update={
            "accept_static_image_fallback": not seed.production_policy.accept_static_image_fallback})})
    other = _prepare_sequence_generation(activated_source, inputs, other_seed).execution_binding
    assert other is not None
    assert other.selected_provider_route == initial.execution_binding.selected_provider_route
    assert other.projection.requirement.generation_intent_hash == seed.generation_intent.projection_hash
    assert other.projection.requirement.source_request_content_hash != seed.request_content_hash
    substituted = ContinuityProviderRouteBinding.create(**{
        **{n: getattr(routing, n) for n in type(routing).model_fields if n != "binding_hash"},
        "destination_selection_binding": other.model_dump(mode="json")})
    loaded = load_production_project(activated_source["root"] / "project.yaml")
    arguments = dict(projection=binding.projection, context=binding.context, policy=binding.policy,
        lifecycle=binding.lifecycle, inputs=binding.inputs, continuity_routing=substituted)
    if entrypoint == "feedback":
        with pytest.raises(ValueError, match="seed|authoring evidence"):
            _prepare_sequence_generation(activated_source, inputs, request, substituted)
    elif entrypoint == "resolver":
        with pytest.raises(ValueError, match="seed|authoring evidence"):
            VideoGenerationResolver().resolve_requirement(**arguments, source_project=loaded)
    else:
        decision = resolve_generation_decision(VideoGenerationResolver(), **arguments)
        assert decision.disposition == "GENERATE_ONCE"
        compiled = activated_source["provider"].compile_request(
            decision.routing.provider_bound_request, binding.projection.requirement)
        resealed = GenerationDecisionExecutionBinding.create(**arguments, decision=decision,
            compiled_request=activated_source["provider"].resolve(compiled.request))
        with pytest.raises(ValueError, match="seed|authoring evidence"):
            resealed.validate_current_project(loaded)


def test_final_router_rejects_candidate_destination_route_mismatch(activated_source):
    from ai_video.production.shot_router import VideoGenerationResolver
    inputs = _cross_stack_inputs(activated_source)
    initial = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    inputs["destination_selection_binding"] = initial.execution_binding
    request, routing = build_sequence_video_planning_request(**inputs)
    prepared = _prepare_sequence_generation(activated_source, inputs, request, routing)
    binding = prepared.execution_binding
    other = activated_source["binding"].inputs.candidates[0]
    other = other.model_copy(update={"recipe": other.recipe.model_copy(update={
        "requirement_hash": binding.projection.requirement.requirement_hash})})
    inputs = binding.inputs.model_copy(update={"candidates": (other,), "limits": binding.inputs.limits.model_copy(
        update={"allowed_remote_candidates": (other.candidate_id,)})})
    decision = VideoGenerationResolver().resolve_requirement(projection=binding.projection,
        context=binding.context, policy=binding.policy, lifecycle=binding.lifecycle, inputs=inputs,
        continuity_routing=routing, source_project=load_production_project(activated_source["root"] / "project.yaml"))
    assert decision.selected_candidate_id is None
    assert "CONTINUITY_DESTINATION_ROUTE_MISMATCH" in decision.assessments[0].reasons


def test_route_candidate_is_not_selection_and_forced_decision_cannot_be_resealed(activated_source):
    from ai_video.production.video import VideoProviderCapabilities
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    inputs = _cross_stack_inputs(activated_source)
    initial = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    provider = activated_source["provider"]
    other = provider.capabilities().variants[0].model_copy(update={
        "model_id": "another-destination-model", "capability_id": "another-destination-i2v"})
    provider._capabilities = VideoProviderCapabilities.create(provider_name=inputs["destination_route"].provider_name,
        variants=(provider.capabilities().variants[0], other))
    ambiguous = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    assert ambiguous.execution_binding is None
    assert ambiguous.decision.disposition == "UNRESOLVED_TIE"
    proof = initial.execution_binding
    with pytest.raises(ValueError, match="stale or altered"):
        GenerationDecisionExecutionBinding.create(projection=proof.projection, context=proof.context,
            policy=proof.policy, lifecycle=proof.lifecycle, inputs=ambiguous.inputs,
            decision=proof.decision, compiled_request=proof.compiled_request)


def test_cross_stack_cannot_reuse_sequence_decision_as_its_own_initial_selection(activated_source):
    inputs = _cross_stack_inputs(activated_source)
    initial = _prepare_sequence_generation(activated_source, inputs, inputs["current_request"])
    inputs["destination_selection_binding"] = initial.execution_binding
    request, routing = build_sequence_video_planning_request(**inputs)
    final = _prepare_sequence_generation(activated_source, inputs, request, routing)
    inputs["destination_selection_binding"] = final.execution_binding
    with pytest.raises(AiVideoError) as stopped:
        build_sequence_video_planning_request(**inputs)
    assert "preselected continuity route" in stopped.value.technical_detail
