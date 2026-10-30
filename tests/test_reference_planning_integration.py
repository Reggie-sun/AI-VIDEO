"""Reference decisions reach canonical loading, actual routing and compilation."""
import pytest

from ai_video.canvas_authoring import author_canvas_project
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.canvas_planning import canvas_feedback_context
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, GenerationHistory, RegisteredGenerationTarget
from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.video_reference_controls import prepared_generation_report
from ai_video.production.reference_planning_contracts import ReferencePlanningIntent
from ai_video.production.video_requirement import ProviderNeutralGenerationIntentProjection
from ai_video.planning import VideoPlanner, VideoPlanningRequest, require_current_video_plan
from tests.test_canvas_authoring import direction
from tests.test_canvas_sequence_packet import document
from scripts.canvas_sequence_packet import build_sequence_packet
from tests.test_generation_feedback import NativeFixtureProvider
from tests.test_production_generation_decision import setup_decision


def load_canvas(tmp_path, planning, *, seal_coverage=True, bind_coverage=True):
    from tests.reference_authoring_fixture import fixture_director_coverage, fixture_preview_approval, fixture_director_coverage_binding
    if isinstance(planning, dict) and bind_coverage:
        planning = {"director_coverage": fixture_director_coverage_binding(), **planning}
    raw = document()
    raw["edges"] = []
    for node in raw["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft is not None:
            draft["parts"] = [p for p in draft["parts"] if p["type"] == "text"]
            draft["references"] = []
    packet = build_sequence_packet(raw, {"node_ids": ["a", "b"]})
    data = direction()
    data["delivery_profile"] = {"width": 1024, "height": 576, "fps": 24}
    if seal_coverage:
        data["director_coverages"] = [fixture_director_coverage()]
    data["preview_approvals"] = [fixture_preview_approval()]
    row = data["shots"][0]
    row["shot"]["duration_policy"]["seconds"] = 4
    row["generation"] = {"generation_intent": {
        "subject_action": {"progression": "Generate 4 seconds."}, "reference_planning": planning},
        "audio_need": "forbidden", "quality_need": {}}
    bundle = author_canvas_project(packet=packet, direction=data)
    committer = ProductionStateCommitter(tmp_path)
    bundle.bootstrap(committer=committer, attempt_id="reference-plan")
    initialize_canvas_graph(committer, "reference-plan-graph")
    return load_production_project(tmp_path / "project.yaml"), row, bundle


def test_director_reference_events_survive_loader_planner_router_and_real_compiler(tmp_path):
    planning = {"facets": ["emotional_change"], "events": [
        {"event_id": "opening", "kind": "performance", "visual_state": "平静", "purpose": "建立情绪"},
        {"event_id": "response", "kind": "performance", "visual_state": "释然", "purpose": "情绪转折"},
    ]}
    loaded, row, bundle = load_canvas(tmp_path, planning)
    setup = setup_decision()
    current = canvas_feedback_context(loaded=loaded, row=row, policy=setup["policy"])
    candidate = setup["inputs"].candidates[0]
    current["acceptance"] = candidate.recipe.acceptance_policy
    provider = NativeFixtureProvider(capabilities=candidate.capabilities, artifact_bytes=b"never-submitted")
    provider.prompt_text = "Generate 4 seconds. 平静 建立情绪 释然 情绪转折"
    orchestrator = GenerationFeedbackOrchestrator(
        targets=(RegisteredGenerationTarget(provider, candidate.provider_profile,
            candidate.compiler_contract, candidate.output_requirement),),
        context_loader=lambda: current, history_loader=GenerationHistory,
        policy=DecisionPolicy(allow_bounded_exploration=True))
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert prepared.compilation.outcome == "compiled", prepared.compilation
    assert prepared.resolved_request is not None
    report = prepared_generation_report(prepared)["reference_control"]["reference_planning"]
    assert report["keyframe_count"] == 2
    assert report["execution_asset_count"] == 0
    assert report["capability_id"] == candidate.capability_id
    assert report["actual_quality"] == "NOT_EVALUATED"
    assert report["actual_model_inputs"] == []  # compiled text-only request, not an uncompiled estimate
    assert current["planning_request"].generation_intent.generation_intent.reference_planning.events[1].event_id == "response"


@pytest.mark.parametrize("facet", ["contact_timing", "high_speed", "complex_camera", "continuous_physics"])
def test_isolated_motion_labels_do_not_force_new_media_in_real_loading_seam(tmp_path, facet):
    loaded, row, _ = load_canvas(tmp_path, {"facets": [facet]})
    current = canvas_feedback_context(loaded=loaded, row=row, policy=setup_decision()["policy"])
    plan = VideoPlanner().plan(current["planning_request"])
    assert plan.outcome.value == "proposed"
    assert not plan.generation_requirement.asset_evidence
    assert plan.reference_plan["motion_reference_level"] in {"none", "recommended"}


@pytest.mark.parametrize("planning", [
    {"facets": ["sustained_contact", "support_transfer"]},
    {"facets": ["exact_graphics"]},
    {"events": [{"event_id": "timed", "kind": "composition", "visual_state": "定点",
                 "purpose": "定时", "control": "exact_time", "at_seconds": 2}]},
    {"structure": "multi_shot", "segment_ids": ["a", "b"]},
])
def test_director_control_gaps_stop_before_any_generation_preparation(tmp_path, planning):
    from ai_video.errors import AiVideoError
    loaded, row, _ = load_canvas(tmp_path, planning)
    with pytest.raises(AiVideoError):
        canvas_feedback_context(loaded=loaded, row=row, policy=setup_decision()["policy"])


def test_authored_planning_revision_invalidates_previous_plan_projection(tmp_path):
    loaded, row, _ = load_canvas(tmp_path, {"facets": ["stable"]})
    current = canvas_feedback_context(loaded=loaded, row=row, policy=setup_decision()["policy"])
    request = current["planning_request"]
    plan = VideoPlanner().plan(request)
    old = request.generation_intent
    revised = ProviderNeutralGenerationIntentProjection.create(**{
        **{key: getattr(old, key) for key in type(old).model_fields if key != "projection_hash"},
        "generation_intent": old.generation_intent.model_copy(update={
            "reference_planning": ReferencePlanningIntent(facets=("contact_timing",))})})
    request = VideoPlanningRequest.create(**{
        **{key: getattr(request, key) for key in type(request).model_fields if key != "request_content_hash"},
        "generation_intent": revised})
    from ai_video.errors import AiVideoError
    with pytest.raises(AiVideoError):
        require_current_video_plan(current_request=request, plan=plan)


def motion_preparer(*, supports_video=True, cardinality_conflict=False):
    from ai_video.planning import AvailableAsset, AssetRole
    from ai_video.production.video import VideoGenerationMode
    from ai_video.production.video_contracts import VideoMediaCapability, VideoBindingCardinalityConstraint
    from ai_video.production.shot_router import RouterAssetIdentity
    from tests.test_production_shot_router import _context, _lifecycle, _variant, _capabilities, _output
    from tests.fixtures.planning_factory import make_request, make_scene
    from tests.test_reference_planning import intent
    setup = setup_decision()
    asset = AvailableAsset(role=AssetRole.EXISTING_VIDEO, asset_id="motion", asset_sha256="e" * 64,
        mime_type="video/mp4", width=1024, height=576, size_bytes=100, duration_millis=1000, fps=24)
    routed_asset = RouterAssetIdentity(role="reference_video", asset_id=asset.asset_id, asset_sha256=asset.asset_sha256,
        source_registry_revision_id="f" * 64, mime_type=asset.mime_type, size_bytes=asset.size_bytes,
        width=asset.width, height=asset.height, duration_millis=asset.duration_millis, fps=asset.fps)
    context = _context(important=False, reference_videos=(routed_asset,))
    from tests.reference_authoring_fixture import fixture_director_coverage_binding
    authored = intent(facets=("contact_timing",), selections=({"need_id": "auto:motion", "asset_id": "motion"},),
                      director_coverage=fixture_director_coverage_binding())
    authored = authored.model_copy(update={"subject_action": authored.subject_action.model_copy(
        update={"progression": "Generate 4 seconds."})})
    original = setup["projection"].requirement
    projection = ProviderNeutralGenerationIntentProjection.create(generation_intent=authored,
        output_need=original.output_need, audio_need=original.audio_need, quality_need=original.quality_need)
    scene = make_scene(scene_id=context.activated_shot.scene_id)
    request = make_request(target_shot=context.activated_shot, scene_context=scene, character_context=(),
        available_assets=(asset,), generation_intent=projection, planning_contract_version="video-planner/3")
    plan = VideoPlanner().plan(request)
    verified = require_current_video_plan(current_request=request, plan=plan)
    context = type(context).model_validate({**context.model_dump(mode="python"),
        "motion_requirement": plan.motion_requirement.value,
        "continuity_mode": plan.continuity_mode.value, "scene_content_hash": scene.content_hash})
    lifecycle = _lifecycle(context)
    lifecycle = lifecycle.model_copy(update={"input_artifact_ids": (*lifecycle.input_artifact_ids, "motion")})
    base = setup["inputs"].candidates[0]
    variant = _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
    if supports_video:
        variant = variant.model_copy(update={"media_capabilities": (VideoMediaCapability(kind="video",
            roles=("reference_video",), min_count=0, max_count=1, allowed_mime_types=("video/mp4",),
            max_size_bytes=1000, min_duration_millis=1, max_duration_millis=2000),)})
    if cardinality_conflict:
        variant = variant.model_copy(update={"binding_cardinality_constraints": (
            VideoBindingCardinalityConstraint(roles=("reference_video",), min_count=0, max_count=0),)})
    provider = NativeFixtureProvider(capabilities=_capabilities(variant), artifact_bytes=b"never-used")
    current = dict(projection=verified, context=context, policy=setup["policy"], lifecycle=lifecycle,
        acceptance=base.recipe.acceptance_policy)
    orchestrator = GenerationFeedbackOrchestrator(targets=(RegisteredGenerationTarget(provider,
        base.provider_profile, base.compiler_contract, _output()),), context_loader=lambda: current,
        history_loader=GenerationHistory, policy=DecisionPolicy(allow_bounded_exploration=True))
    return orchestrator, setup["inputs"].limits, provider, current


@pytest.mark.parametrize("supported,conflict", [(True, False), (False, False), (True, True)])
def test_motion_reference_respects_real_provider_capability_and_cardinality(supported, conflict):
    orchestrator, limits, provider, _ = motion_preparer(supports_video=supported, cardinality_conflict=conflict)
    prepared = orchestrator.prepare(limits=limits)
    if supported and not conflict:
        assert prepared.decision.disposition == "GENERATE_ONCE"
        assert prepared.compilation.outcome == "compiled", prepared.compilation
        assert len(prepared.resolved_request.media_bindings) == 1
        assert not prepared.resolved_request.image_bindings
        report = prepared_generation_report(prepared)["reference_control"]["reference_planning"]
        assert report["actual_model_inputs"] == [prepared.resolved_request.media_bindings[0].model_dump(mode="json")]
        assert report["whitebox_decision"] == "not_needed"  # selected real footage doesn't require a new Blender build
        assert report["reuse_quality"] == "NOT_EVALUATED"
    else:
        assert prepared.decision.disposition != "GENERATE_ONCE"
        assert prepared.resolved_request is None
        assert prepared_generation_report(prepared)["reference_control"]["reference_planning"]["execution_asset_count"] == 1
    assert provider.call_counts.submit == provider.call_counts.fetch == 0


def test_failed_continuous_action_feedback_proposes_motion_review_not_automatic_cut():
    from ai_video.production.generation_feedback import project_attempt_evidence
    from ai_video.production.generation_experience import GenerationExperience
    from ai_video.production.generation_diagnosis import Finding
    from tests.test_production_generation_decision import acceptance_policy
    orchestrator, limits, _, current = motion_preparer()
    rule = current["acceptance"].profile_payload["generation_requirements"][0]
    from ai_video.production.generation_recipe import RequirementExpression
    rule = RequirementExpression.model_validate({**rule, "intent_paths": ("generation_intent.subject_action.progression",),
        "native_text": ("Generate 4 seconds.",)})
    current["acceptance"] = acceptance_policy((rule,))
    first = orchestrator.prepare(limits=limits)
    assert first.resolved_request is not None
    finding = Finding(requirement_id=rule.requirement_id, rubric_hash=first.inputs.rubric_hash,
        stage="raw_generation", proof="technical", verdict="FAIL", source_sha256="c" * 64,
        observation="Contact occurred after separation in fixture evidence.")
    failed = project_attempt_evidence(prepared=first, task_id="task", shot_id=current["context"].target_shot_id,
        attempt_id="failed", outcome="media", artifact_sha256="d" * 64, findings=(finding,))
    history = GenerationHistory((GenerationExperience(projection=current["projection"],
        candidate=first.inputs.candidates[0], evidence=(failed,)),), failed.evidence_hash, first.compilation.request)
    orchestrator.history_loader = lambda: history
    current["lifecycle"] = current["lifecycle"].model_copy(update={"generation_id": "repair"})
    repair = orchestrator.prepare(limits=limits)
    assert repair.inputs.interventions
    hypothesis = repair.inputs.interventions[0].hypothesis
    assert "continuous motion" in hypothesis and "not automatic splitting" in hypothesis
    assert repair.inputs.interventions[0].disposition != "SPLIT_SHOT"


@pytest.mark.parametrize("facet", ["product_accuracy", "product_rotation"])
def test_approved_commercial_first_frame_retains_product_duty_without_extra_images(tmp_path, facet):
    from tests.test_production_ecommerce_product_interaction_e2e import (
        _approved_commercial_project, _base_commercial_planning_request,
    )
    from ai_video.planning import build_commercial_video_planning_request
    loaded, execution, approved, _ = _approved_commercial_project(tmp_path, source_plan_shot_id="shot-03")
    base = _base_commercial_planning_request(loaded)
    original = base.generation_intent
    projection = ProviderNeutralGenerationIntentProjection.create(**{
        **{key: getattr(original, key) for key in type(original).model_fields if key != "projection_hash"},
        "generation_intent": original.generation_intent.model_copy(update={
            "reference_planning": ReferencePlanningIntent(facets=(facet,))})})
    base = VideoPlanningRequest.create(**{
        **{key: getattr(base, key) for key in type(base).model_fields if key != "request_content_hash"},
        "generation_intent": projection})
    request = build_commercial_video_planning_request(base_request=base, execution_projection=execution, loaded_project=loaded)
    plan = VideoPlanner().plan(request)
    verified = require_current_video_plan(current_request=request, plan=plan)
    assert [a.asset_id for a in verified.requirement.asset_evidence] == [approved.keyframe_asset_id]
    assert plan.reference_plan["selected_inputs"] == [{"need_id": "auto:product", "asset_id": approved.keyframe_asset_id}]
    assert plan.reference_plan["execution_gaps"] == []
    assert verified.requirement.capability_need.needs_product_fidelity


def _drama_prepare(tmp_path, planning, **load):
    loaded, row, _ = load_canvas(tmp_path, planning, **load)
    setup = setup_decision()
    current = canvas_feedback_context(loaded=loaded, row=row, policy=setup["policy"])
    candidate = setup["inputs"].candidates[0]
    current["acceptance"] = candidate.recipe.acceptance_policy
    current["source_project"] = loaded  # the canonical for_project loader supplies the current Project
    provider = NativeFixtureProvider(capabilities=candidate.capabilities, artifact_bytes=b"never-submitted")
    provider.prompt_text = "Generate 4 seconds."
    orchestrator = GenerationFeedbackOrchestrator(
        targets=(RegisteredGenerationTarget(provider, candidate.provider_profile,
            candidate.compiler_contract, candidate.output_requirement),),
        context_loader=lambda: current, history_loader=GenerationHistory,
        policy=DecisionPolicy(allow_bounded_exploration=True))
    return orchestrator.prepare(limits=setup["inputs"].limits), provider


def test_drama_director_coverage_sealed_through_canvas_authoring_reaches_execution_binding(tmp_path):
    prepared, provider = _drama_prepare(tmp_path, {"facets": ["stable"]})
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert prepared.execution_binding is not None and prepared.resolved_request is not None
    assert provider.call_counts.submit == provider.call_counts.fetch == 0


@pytest.mark.parametrize("load,message", [
    ({"seal_coverage": False}, "director_coverage.coverage_hash"),
    ({"bind_coverage": False}, "director_coverage"),
])
def test_unsealed_or_unbound_drama_coverage_blocks_before_any_effect(tmp_path, load, message):
    from ai_video.errors import AiVideoError
    with pytest.raises(AiVideoError, match=message):
        _drama_prepare(tmp_path, {"facets": ["stable"]}, **load)


def test_missing_reference_planning_blocks_fresh_canvas_generation(tmp_path):
    from ai_video.errors import AiVideoError
    with pytest.raises(AiVideoError, match="generation_intent.reference_planning"):
        _drama_prepare(tmp_path, None, seal_coverage=False)
