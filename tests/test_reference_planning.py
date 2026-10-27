"""Semantic decisions and their actual Planner/Router/compiler consequences."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from ai_video.planning import AssetRole, VideoPlanner, PlanOutcome, require_current_video_plan
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import VisualStrategy
from ai_video.production.reference_planning import plan_shot_references
from ai_video.production.reference_planning_contracts import ReferencePlanningIntent, ReferenceRole
from ai_video.production.reference_strategy import (
    select_reference_inputs, reference_execution_gaps, reference_prompt_issues,
    reference_revision_advice,
)
from ai_video.production.video_requirement import (
    GenerationIntent, SubjectAction, CameraEndpoint, Pacing, IdentityContinuity,
    ProviderNeutralGenerationIntentProjection, SemanticReferenceRole,
)
from tests.fixtures.planning_factory import make_request, make_shot, make_available_asset, make_scene, make_character
from tests.test_planning_video_planner import _neutral_generation_intent


def intent(**planning):
    return GenerationIntent(subject_action=SubjectAction(progression="按完整动作自然推进"),
                            reference_planning=ReferencePlanningIntent.model_validate(planning))


def event(identity, kind="state_change", **kw):
    return dict(event_id=identity, kind=kind, visual_state=f"视觉状态 {identity}",
                purpose=f"控制目的 {identity}", **kw)


def request_for(authored, *, assets=(), roles=(), shot=None):
    shot = shot or make_shot(visual_strategy=VisualStrategy.GENERATED_VIDEO, character_ids=())
    base = _neutral_generation_intent(semantic_reference_roles=roles)
    projection = ProviderNeutralGenerationIntentProjection.create(**{
        **{key: getattr(base, key) for key in type(base).model_fields if key != "projection_hash"}, "generation_intent": authored})
    return make_request(target_shot=shot, character_context=tuple(make_character(character_id=c) for c in shot.character_ids), available_assets=assets,
        generation_intent=projection, planning_contract_version="video-planner/3")


@pytest.mark.parametrize("duration", [1, 10, 120, 600])
@pytest.mark.parametrize("facets", [("stable",), ("dialogue",)])
def test_stable_empty_and_dialogue_shots_do_not_accumulate_temporal_images(duration, facets):
    directed = intent(facets=facets).model_copy(update={"pacing": Pacing(shot_duration_seconds=duration)})
    report = plan_shot_references(directed)
    assert report.keyframes == ()
    assert not report.image_reference_needed
    assert VideoPlanner().plan(request_for(directed)).generation_mode.value == "text_to_video"


def test_slow_camera_uses_framing_endpoints_without_inventing_times():
    directed = intent(facets=("slow_camera",)).model_copy(update={"camera_endpoint": CameraEndpoint(
        start_framing="广角全身与门框", end_framing="面部与背景窗")})
    plan = plan_shot_references(directed)
    assert [n.phase for n in plan.keyframes] == ["start", "end"]
    assert [n.mechanism for n in plan.keyframes] == ["first_frame", "last_frame"]
    assert all(n.at_seconds is None for n in plan.keyframes)


@pytest.mark.parametrize("facets,events,motion,frames", [
    (("emotional_change",), (event("hesitate", "performance"), event("resolve", "performance")), False, 2),
    (("multi_subject_blocking", "occlusion_change"), (event("cross", "blocking"), event("reveal", "occlusion")), False, 2),
    (("complex_camera",), (event("orbit", "composition"),), True, 1),
    (("high_speed", "continuous_physics"), (event("touch", "contact"), event("force", "force", after_event_ids=("touch",)), event("fall", "impact", after_event_ids=("force",))), True, 3),
    (("disappearance",), (event("present", phase="start"), event("gone", "disappearance", phase="end")), False, 2),
    (("visual_transformation",), (event("before", phase="start"), event("transition"), event("after", phase="end")), False, 3),
    (("environment_change",), (event("dry", phase="start"), event("wet", phase="end")), False, 2),
])
def test_composable_visual_events_have_purpose_and_motion_is_not_replaced_by_stills(facets, events, motion, frames):
    directed = intent(facets=facets, events=events)
    plan = plan_shot_references(directed)
    assert len(plan.keyframes) == frames
    assert all(n.purpose and n.at_seconds is None for n in plan.keyframes)
    assert any(n.role is ReferenceRole.MOTION for n in plan.needs) is motion
    assert any(n.role is ReferenceRole.BLOCKING for n in plan.needs) is (
        plan.motion_reference_level in {"previs_priority", "required"} or "multi_subject_blocking" in facets)
    assert plan == plan_shot_references(directed)


def test_long_take_follows_events_without_duration_slicing_or_hard_frame_cap():
    directed = intent(events=tuple(event(f"e{i}", "composition") for i in range(37)))
    plan = plan_shot_references(directed)
    assert len(plan.keyframes) == 37
    assert plan.structure == "continuous"
    assert all(n.at_seconds is None for n in plan.keyframes)
    req = request_for(directed)
    result = VideoPlanner().plan(req)
    assert result.outcome is PlanOutcome.PROPOSED
    assert not result.generation_requirement.asset_evidence  # all review-only states
    assert result.reference_plan["keyframe_count"] == 37
    assert result.reference_plan["execution_asset_count"] == 0


def test_redundant_adjacent_review_state_removed_but_causal_recurrence_preserved():
    first = event("one", "composition")
    duplicate = {**first, "event_id": "two"}
    causal = {**first, "event_id": "three", "after_event_ids": ("two",)}
    result = plan_shot_references(intent(events=(first, duplicate, causal)))
    assert [n.event_id for n in result.keyframes] == ["one", "two", "three"]
    assert result.keyframes[-1].after_event_ids == ("two",)


def test_persistent_roles_are_separate_from_temporal_frames_and_missing_product_blocks():
    directed = intent(facets=("product_accuracy", "product_rotation"), anchors=(
        dict(anchor_id="environment", role="scene_environment", purpose="保持厂房空间"),
        dict(anchor_id="look", role="style_lighting", purpose="保持柔光"),
    )).model_copy(update={"identity_continuity": IdentityContinuity(character_ids=("hero",))})
    plan = plan_shot_references(directed)
    assert not plan.keyframes
    assert {n.role for n in plan.needs} >= {ReferenceRole.IDENTITY, ReferenceRole.SCENE, ReferenceRole.STYLE, ReferenceRole.PRODUCT}
    result = VideoPlanner().plan(request_for(directed, shot=make_shot(visual_strategy=VisualStrategy.GENERATED_VIDEO)))
    assert result.outcome is PlanOutcome.BLOCKED
    assert "MISSING_REFERENCE:auto:product" in result.reference_plan["execution_gaps"]


@pytest.mark.parametrize("payload", [
    dict(events=(event("cut", "cut"),)),
    dict(structure="multi_shot"),
    dict(events=(event("one", after_event_ids=("later",)), event("later"))),
    dict(events=(event("one", at_seconds=3), event("two", at_seconds=2))),
    dict(events=(event("one", control="exact_time"),)),
    dict(events=(event("one", control="endpoint"),)),
    dict(events=(event("one", phase="end"), event("two", phase="start"))),
    dict(events=(event("one", at_seconds=float("nan")),)),
    dict(anchors=(dict(anchor_id="id", role="identity", purpose="same face"),)),
])
def test_invalid_boundaries_and_causal_time_claims_rejected(payload):
    with pytest.raises(ValidationError):
        intent(**payload)


def test_multishot_is_authored_not_guessed_from_duration_and_reports_control_gap():
    directed = intent(structure="multi_shot", segment_ids=("reverse", "reaction"), events=(
        event("a", "composition", segment_id="reverse", phase="start"),
        event("b", "cut", segment_id="reaction", phase="start", at_seconds=2),
    ))
    result = VideoPlanner().plan(request_for(directed))
    assert result.outcome is PlanOutcome.BLOCKED
    assert result.reference_plan["structure"] == "multi_shot"
    assert "MULTI_SHOT_NATIVE_CONTROL_UNDECLARED" in result.reference_plan["execution_gaps"]


@pytest.mark.parametrize("facet", ["exact_graphics", "visual_transformation", "multi_subject_blocking"])
def test_unfulfilled_control_requirements_block_actual_planner(facet):
    req = request_for(intent(facets=(facet,)))
    plan = VideoPlanner().plan(req)
    assert plan.outcome is PlanOutcome.BLOCKED
    with pytest.raises(Exception):
        require_current_video_plan(current_request=req, plan=plan)
    assert plan.reference_plan["execution_gaps"]


def test_motion_selection_requires_video_and_exact_duty_not_extra_stills():
    directed = intent(facets=("contact_timing",), selections=(dict(need_id="auto:motion", asset_id="motion"),))
    image = make_available_asset(role=AssetRole.SCENE_REFERENCE, asset_id="motion")
    assert select_reference_inputs(directed, (image,))[1] == ("MISSING_REFERENCE:auto:motion",)
    video = make_available_asset(role=AssetRole.EXISTING_VIDEO, asset_id="motion", mime_type="video/mp4")
    chosen, gaps, bindings = select_reference_inputs(directed, (video,))
    assert chosen == (video,) and gaps == () and bindings == (("auto:motion", "motion"),)
    unassigned = intent(facets=("contact_timing",))
    assert select_reference_inputs(unassigned, (video,)) == ((), (), ())  # availability is not responsibility
    result = VideoPlanner().plan(request_for(directed, assets=(video,)))
    assert result.outcome is PlanOutcome.PROPOSED
    assert result.generation_mode.value == "reference_to_video"
    assert result.generation_requirement.asset_evidence[0].role is SemanticReferenceRole.VIDEO_REFERENCE


@pytest.mark.parametrize("strategy", [VisualStrategy.GENERATED_VIDEO, VisualStrategy.HYBRID])
def test_explicit_duty_selects_one_image_without_filling_provider_capacity(strategy):
    scene = make_scene()
    assets = tuple(make_available_asset(role=AssetRole.SCENE_REFERENCE, asset_id=f"ref-{i}",
        canonical_owner_id=scene.scene_id, canonical_owner_content_hash=scene.content_hash)
        for i in range(5))
    directed = intent(anchors=(dict(anchor_id="look", role="style_lighting", purpose="蓝色侧光"),),
        selections=(dict(need_id="look", asset_id="ref-3"),))
    request = request_for(directed, assets=assets, shot=make_shot(visual_strategy=strategy, character_ids=()))
    plan = VideoPlanner().plan(request)
    assert plan.outcome is PlanOutcome.PROPOSED
    assert [a.asset_id for a in plan.generation_requirement.asset_evidence] == ["ref-3"]
    assert reference_prompt_issues(plan.generation_requirement, "generic scene")
    assert not reference_prompt_issues(plan.generation_requirement, "使用蓝色侧光")
    assert plan.plan_hash == VideoPlanner().plan(request).plan_hash
    assert request.available_assets == assets


@pytest.mark.parametrize("phase", ["start", "interior", "end"])
def test_partial_camera_events_only_replace_their_corresponding_endpoint(phase):
    directed = intent(facets=("slow_camera",), events=(event("authored", "composition", phase=phase),))
    directed = directed.model_copy(update={"camera_endpoint": CameraEndpoint(start_framing="全景", end_framing="近景")})
    result = VideoPlanner().plan(request_for(directed))
    needs = result.reference_plan["needs"]
    assert {n["phase"] for n in needs} >= {"start", "end"}
    assert {n["need_id"] for n in needs} == {"authored"} | {
        f"auto:camera:{p}" for p in ("start", "end") if p != phase}


@pytest.mark.parametrize("seconds,blocked", [(1, False), (2, False), (4, True)])
def test_frame_count_output_enforces_known_event_time_bound(seconds, blocked):
    from ai_video.production.video_requirement import OutputNeed
    from ai_video.planning import VideoPlanningRequest
    request = request_for(intent(events=(event("framing", "composition", at_seconds=seconds),)))
    base = request.generation_intent
    projection = ProviderNeutralGenerationIntentProjection.create(**{
        **{key: getattr(base, key) for key in type(base).model_fields if key != "projection_hash"},
        "output_need": OutputNeed(timing_mode="frame_count", frame_count=48, fps=24)})
    request = VideoPlanningRequest.create(**{
        **{key: getattr(request, key) for key in type(request).model_fields if key != "request_content_hash"},
        "generation_intent": projection})
    plan = VideoPlanner().plan(request)
    assert (plan.outcome is PlanOutcome.BLOCKED) is blocked
    assert ("EVENT_OUTSIDE_SHOT:framing" in plan.reference_plan["execution_gaps"]) is blocked
    if not blocked:
        assert require_current_video_plan(current_request=request, plan=plan)


def test_stale_owner_reference_cannot_satisfy_new_planning_duty():
    scene = make_scene()
    asset = make_available_asset(role=AssetRole.SCENE_REFERENCE, asset_id="ref",
        canonical_owner_id=scene.scene_id, canonical_owner_content_hash="0" * 64)
    directed = intent(anchors=(dict(anchor_id="layout", role="composition", purpose="保持布局"),),
        selections=(dict(need_id="layout", asset_id="ref"),))
    result = VideoPlanner().plan(request_for(directed, assets=(asset,)))
    assert result.outcome is PlanOutcome.BLOCKED
    assert not result.generation_requirement.asset_evidence


def test_reference_count_does_not_grant_strict_timing_or_out_of_shot_events():
    for ev, expected in ((event("beat", control="exact_time", at_seconds=2), "TIMED_KEYFRAME_CONTROL_UNSUPPORTED"),
                         (event("late", at_seconds=4), "EVENT_OUTSIDE_SHOT")):
        result = VideoPlanner().plan(request_for(intent(events=(ev,))))
        assert result.outcome is PlanOutcome.BLOCKED
        assert any(gap.startswith(expected) for gap in result.reference_plan["execution_gaps"])


def test_legacy_hash_shape_and_serialization_remain_unchanged():
    old = GenerationIntent(subject_action=SubjectAction(progression="walk"))
    payload = old.model_dump(mode="json")
    assert "reference_planning" not in payload
    assert GenerationIntent.model_validate(payload).model_dump(mode="json") == payload
    new = intent(events=(event("a"),))
    assert GenerationIntent.model_validate_json(new.model_dump_json()) == new
    before = request_for(new)
    after = request_for(intent(events=(event("b"),)))
    assert before.request_content_hash != after.request_content_hash


def test_qa_advice_uses_diagnosed_paths_preserves_pass_and_unknown_stops():
    from ai_video.production.generation_diagnosis import diagnose_attempt
    from tests.test_production_generation_decision import setup_decision, evidence, recipe_with_rules
    setup = setup_decision()
    recipe = setup["inputs"].candidates[0].recipe
    action = recipe.expressions[0].model_copy(update={"intent_paths": ("generation_intent.subject_action.progression",)})
    recipe = recipe_with_rules(recipe, (action,))
    candidate = setup["inputs"].candidates[0].model_copy(update={"recipe": recipe})
    observed = evidence(setup, candidate=candidate, verdict="FAIL")
    diagnosis = diagnose_attempt(observed, recipe)
    advice = reference_revision_advice(diagnosis, recipe.expressions, intent(facets=("continuous_physics",)))
    assert any("continuous motion" in a for a in advice)
    assert any("not automatic splitting" in a for a in advice)
    unknown = diagnose_attempt(evidence(setup, candidate=candidate, outcome="unknown_outcome"), recipe)
    assert reference_revision_advice(unknown, recipe.expressions, intent()) == (
        "Resolve unknown outcome through the canonical recovery owner; do not resubmit.",)


@pytest.mark.parametrize("strategy", [VisualStrategy.STATIC_IMAGE, VisualStrategy.IMAGE_MOTION])
def test_reference_declaration_preserves_existing_static_final_visual(strategy):
    shot = make_shot(visual_strategy=strategy)
    baseline = make_request(target_shot=shot)
    base = _neutral_generation_intent()
    projection = ProviderNeutralGenerationIntentProjection.create(generation_intent=intent(facets=("stable",)),
        output_need=base.output_need, audio_need=base.audio_need, quality_need=base.quality_need)
    request = make_request(target_shot=shot, generation_intent=projection, planning_contract_version="video-planner/3")
    plan = VideoPlanner().plan(request)
    assert plan.outcome is PlanOutcome.PROPOSED
    assert [a.asset_id for a in plan.generation_requirement.asset_evidence] == [baseline.available_assets[0].asset_id]
    assert plan.required_asset_roles[0].role is AssetRole.APPROVED_KEYFRAME
    assert require_current_video_plan(current_request=request, plan=plan).requirement.asset_evidence


@pytest.mark.parametrize("second", ["available", "missing", "ambiguous"])
def test_explicit_identity_for_one_character_never_skips_another_owner(second):
    shot = make_shot(visual_strategy=VisualStrategy.GENERATED_VIDEO, character_ids=("hero", "villain"))
    assets = []
    for i, name in enumerate(("hero", "villain")):
        if name == "villain" and second == "missing":
            continue
        character = make_character(character_id=name)
        assets.append(make_available_asset(role=AssetRole.CHARACTER_REFERENCE, asset_id=name + "-photo",
            canonical_owner_id=name, canonical_owner_content_hash=character.content_hash,
            asset_sha256=str(i + 1) * 64))
    if second == "ambiguous":
        assets.append(assets[-1].model_copy(update={"asset_id": "villain-alternate", "asset_sha256": "3" * 64}))
    directed = intent(anchors=(dict(anchor_id="hero-identity", role="identity", owner_id="hero", purpose="保留主角脸"),),
        selections=(dict(need_id="hero-identity", asset_id="hero-photo"),))
    request = request_for(directed, shot=shot, assets=tuple(assets), roles=(SemanticReferenceRole.IDENTITY,))
    plan = VideoPlanner().plan(request)
    if second == "available":
        assert plan.outcome is PlanOutcome.PROPOSED
        assert {a.canonical_owner_id for a in plan.generation_requirement.asset_evidence} == {"hero", "villain"}
        assert require_current_video_plan(current_request=request, plan=plan)
    else:
        assert plan.outcome is PlanOutcome.BLOCKED


def test_unrelated_performance_events_do_not_hide_spatial_or_camera_needs():
    directed = intent(facets=("multi_subject_blocking", "emotional_change", "slow_camera"),
        events=(event("emotion-a", "performance"), event("emotion-b", "performance")))
    directed = directed.model_copy(update={"camera_endpoint": CameraEndpoint(start_framing="全景", end_framing="近景")})
    plan = VideoPlanner().plan(request_for(directed))
    assert plan.outcome is PlanOutcome.BLOCKED
    assert "SPATIAL_EVENT_STATES_REQUIRED" in plan.reference_plan["execution_gaps"]
    assert {n["need_id"] for n in plan.reference_plan["needs"]} >= {"auto:camera:start", "auto:camera:end"}


def test_unrelated_composition_does_not_satisfy_emotional_change():
    plan = VideoPlanner().plan(request_for(intent(facets=("emotional_change",),
        events=(event("framing", "composition"),))))
    assert plan.outcome is PlanOutcome.BLOCKED
    assert "PERFORMANCE_BEATS_REQUIRED" in plan.reference_plan["execution_gaps"]


def test_composition_events_preserve_existing_typed_performance_beats():
    from tests.test_performance_direction import _beat, _direction, _complete_intent
    directed = intent(events=(event("frame", "composition"),)).model_copy(update={
        "performance_intent": _complete_intent().performance_intent.model_copy(update={"character_directions": (
            _direction(beats=(_beat("opening"), _beat("response"), _beat("settle"))),)})})
    plan = plan_shot_references(directed)
    assert [n.need_id for n in plan.keyframes] == ["frame", "auto:performance:hero:opening",
        "auto:performance:hero:response", "auto:performance:hero:settle"]
    assert "PERFORMANCE_BEATS_REQUIRED" not in plan.risks
    assert all(n.at_seconds is None for n in plan.keyframes)


@pytest.mark.parametrize("facets,events,level", [
    (("contact_timing",), (event("touch", "contact"),), "none"),
    (("high_speed",), (), "recommended"),
    (("complex_camera",), (), "recommended"),
    (("continuous_physics",), (), "recommended"),
    (("contact_timing", "continuous_physics"),
     (event("grip", "contact"), event("push", "force", after_event_ids=("grip",))), "recommended"),
    (("complex_camera", "multi_subject_blocking", "occlusion_change"),
     (event("cross", "blocking"), event("hide", "occlusion")), "previs_priority"),
    (("sustained_contact", "support_transfer"),
     (event("grip", "contact"), event("lift", "force", after_event_ids=("grip",))), "required"),
    (("continuous_physics", "multi_subject_blocking", "occlusion_change"),
     (event("touch", "contact"), event("force", "force", after_event_ids=("touch",)),
      event("cross", "blocking"), event("hide", "occlusion")), "required"),
])
def test_motion_risk_is_compositional_and_only_necessary_control_blocks(facets, events, level):
    directed = intent(facets=facets, events=events)
    plan = VideoPlanner().plan(request_for(directed))
    report = plan.reference_plan
    assert report["motion_reference_level"] == level
    assert bool(report["motion_reference_reasons"])
    assert (plan.outcome is PlanOutcome.BLOCKED) is (level == "required")
    motion = [n for n in report["needs"] if n["role"] == "motion_camera_video"]
    assert bool(motion) is (level != "none")
    assert all(n["priority"] == ("required" if level == "required" else "preferred") for n in motion)


def test_whitebox_has_specific_positive_and_negative_decisions_without_forcing_assets():
    simple = plan_shot_references(intent(facets=("dialogue",)))
    assert simple.whitebox_decision == "not_needed"
    assert simple.whitebox_reasons
    spatial = plan_shot_references(intent(facets=("spatial_precision",), events=(event("layout", "composition"),)))
    assert spatial.whitebox_decision == "optional_static"
    coupled = plan_shot_references(intent(facets=("complex_camera", "multi_subject_blocking", "occlusion_change"),
        events=(event("cross", "blocking"), event("hide", "occlusion"))))
    assert coupled.whitebox_decision == "reuse_motion_first"
    assert all(n.priority == "preferred" for n in coupled.needs if n.scope == "preparation")


def test_report_separates_review_states_missing_inputs_and_actual_selection():
    from ai_video.production.reference_strategy import reference_strategy_report
    directed = intent(events=(event("review", "composition"),
        event("first", "composition", phase="end", control="endpoint")))
    result = VideoPlanner().plan(request_for(directed))
    report = reference_strategy_report(result.generation_requirement)
    assert report["image_preparation"]["review_only_state_ids"] == ["review"]
    assert report["image_preparation"]["unbound_model_image_need_ids"] == ["first"]
    assert report["image_preparation"]["new_image_count_if_no_reuse"] == 1
    assert report["planned_model_inputs"] == []
    assert report["actual_model_inputs"] == "NOT_EVALUATED"
    assert report["whitebox_decision"] == "not_needed"
    assert report["minimum_viable_plan"] and report["higher_control_plan"]


def test_explicit_motion_control_is_sealed_but_auto_preserves_existing_intent_shape():
    auto = intent(facets=("contact_timing",))
    required = intent(facets=("contact_timing",), motion_reference_policy="required")
    assert "motion_reference_policy" not in auto.model_dump(mode="json")["reference_planning"]
    assert canonical_sha256(auto.model_dump(mode="json")) != canonical_sha256(required.model_dump(mode="json"))
    assert GenerationIntent.model_validate_json(required.model_dump_json()) == required
    plan = VideoPlanner().plan(request_for(required))
    assert plan.outcome is PlanOutcome.BLOCKED
    assert "MISSING_REFERENCE:auto:motion" in plan.reference_plan["execution_gaps"]


def test_review_board_cannot_be_selected_as_clean_endpoint_or_silently_uploaded():
    asset = make_available_asset(role=AssetRole.SCENE_REFERENCE, asset_id="board")
    review = intent(events=(event("board", "composition"),), selections=(dict(need_id="board", asset_id="board"),))
    assert select_reference_inputs(review, (asset,))[1] == ("NON_PROVIDER_REFERENCE_SELECTION:board",)
    endpoint = intent(events=(event("opening", "composition", phase="start", control="endpoint"),),
        selections=(dict(need_id="opening", asset_id="board"),))
    assert select_reference_inputs(endpoint, (asset,))[1] == ("MISSING_REFERENCE:opening",)


def test_independent_characters_cannot_share_identity_bytes_even_with_different_asset_ids():
    shot = make_shot(visual_strategy=VisualStrategy.GENERATED_VIDEO, character_ids=("hero", "villain"))
    assets = tuple(make_available_asset(role=AssetRole.CHARACTER_REFERENCE, asset_id=name + "-photo",
        canonical_owner_id=name, canonical_owner_content_hash=make_character(character_id=name).content_hash,
        asset_sha256="d" * 64) for name in shot.character_ids)
    directed = intent().model_copy(update={"identity_continuity": IdentityContinuity(character_ids=shot.character_ids)})
    result = VideoPlanner().plan(request_for(directed, shot=shot, assets=assets))
    assert result.outcome is PlanOutcome.BLOCKED
    assert "INDEPENDENT_IDENTITY_BYTES_CONFLICT" in result.reference_plan["execution_gaps"]


def test_sustained_contact_is_not_equated_with_support_transfer_without_coupling():
    for facet in ("sustained_contact", "support_transfer"):
        result = VideoPlanner().plan(request_for(intent(facets=(facet,))))
        assert result.outcome is PlanOutcome.PROPOSED
        assert result.reference_plan["motion_reference_level"] == "recommended"
