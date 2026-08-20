from __future__ import annotations

import ast
from enum import Enum
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

import ai_video.planning as planning
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning import (
    AssetRole,
    AvailableAsset,
    ContinuityMode,
    GenerationMode,
    MotionRequirement,
    PlanOutcome,
    PlanWarning,
    ProductionPolicyInput,
    ReasonCode,
    ReviewDecisionProjection,
    ShotIntentEvidence,
    VideoPlanner,
    VideoGenerationPlan,
    VideoPlanningRequest,
    prepare_shot_for_existing_production,
    require_current_video_plan,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetType,
    Character,
    Scene,
    Shot,
    VisualStrategy,
)
from ai_video.production.video_requirement import (
    AudioNeed,
    GenerationIntent as NeutralGenerationIntent,
    GenerationOperation,
    OutputGeometryPolicy,
    OutputNeed,
    ProviderNeutralGenerationIntentProjection,
    ProviderNeutralVideoRequirement,
    QualityNeed,
    SemanticReferenceRole,
    SubjectAction,
    MotionEnvelope,
    VerifiedGenerationRequirementProjection,
)
from tests.fixtures.planning_factory import (
    ONE_HASH,
    TWO_HASH,
    make_available_asset,
    make_character,
    make_intent_evidence,
    make_motion_directive,
    make_plan,
    make_policy,
    make_previous_state,
    make_request,
    make_review_decision,
    make_scene,
    make_shot,
)


def _semantic_hash(model: object, *excluded_fields: str) -> str:
    data = model.model_dump(mode="json")
    for field in excluded_fields:
        data.pop(field)
    return canonical_sha256(data)


def _neutral_generation_intent(
    *,
    generation_operation: GenerationOperation = GenerationOperation.AUTO,
    semantic_reference_roles: tuple[SemanticReferenceRole, ...] = (),
    media_reference_asset_ids: tuple[str, ...] = (),
) -> ProviderNeutralGenerationIntentProjection:
    return ProviderNeutralGenerationIntentProjection.create(
        generation_intent=NeutralGenerationIntent(
            subject_action=SubjectAction(
                start_state="standing",
                progression="walks across the room",
            ),
            motion_envelope=MotionEnvelope(
                onset="gentle",
                peak="steady",
                settle="complete",
            ),
        ),
        output_need=OutputNeed(
            timing_mode="fixed",
            duration_seconds=3,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.OPTIONAL,
        quality_need=QualityNeed(objective_tier="production"),
        generation_operation=generation_operation,
        semantic_reference_roles=semantic_reference_roles,
        media_reference_asset_ids=media_reference_asset_ids,
    )


def test_v3_dynamic_plan_blocks_prose_only_unspecified_generation_semantics():
    shot = _generated_shot(character_ids=())
    projection = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=NeutralGenerationIntent(),
        output_need=OutputNeed(
            duration_seconds=3,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.OPTIONAL,
        quality_need=QualityNeed(objective_tier="production"),
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=projection,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.ACTION_INTENT_REQUIRED in plan.reason_codes
    with pytest.raises(AiVideoError) as exc:
        require_current_video_plan(current_request=request, plan=plan)
    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED


def test_v3_plan_embeds_one_requirement_and_returns_verified_router_projection():
    request = make_request(
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(),
    )

    plan = VideoPlanner().plan(request)
    serialized = plan.model_dump(mode="json")
    projection = require_current_video_plan(current_request=request, plan=plan)

    assert plan.planning_contract_version == "video-planner/3"
    assert plan.generation_requirement.source_request_content_hash == (
        request.request_content_hash
    )
    assert "generation_requirement" in serialized
    for duplicate in (
        "generation_mode",
        "continuity_mode",
        "motion_requirement",
        "required_asset_roles",
        "capability_requirements",
    ):
        assert duplicate not in serialized
        assert duplicate not in type(plan).model_fields
    assert isinstance(projection, VerifiedGenerationRequirementProjection)
    assert projection.requirement == plan.generation_requirement
    assert projection.plan_hash == plan.plan_hash

    duplicate_payload = plan.model_dump(
        mode="python",
        exclude={"plan_id", "plan_hash"},
    )
    duplicate_payload["generation_mode"] = plan.generation_mode
    with pytest.raises(ValidationError, match="duplicate generation truth"):
        VideoGenerationPlan.create(**duplicate_payload)


def test_v3_typed_media_references_are_hash_bound_into_the_one_requirement():
    shot = _generated_shot(character_ids=())
    video = AvailableAsset(
        role=AssetRole.EXISTING_VIDEO,
        asset_id="reference-video-1",
        asset_sha256="3" * 64,
        canonical_owner_id="shot-reference",
        canonical_owner_content_hash="4" * 64,
        mime_type="video/mp4",
        width=1920,
        height=1080,
        size_bytes=4096,
        duration_millis=3200,
        fps=24,
    )
    audio = AvailableAsset(
        role=AssetRole.REFERENCE_AUDIO,
        asset_id="reference-audio-1",
        asset_sha256="5" * 64,
        canonical_owner_id="audio-reference",
        canonical_owner_content_hash="6" * 64,
        mime_type="audio/wav",
        size_bytes=2048,
        duration_millis=3200,
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(video, audio),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            semantic_reference_roles=(
                SemanticReferenceRole.VIDEO_REFERENCE,
                SemanticReferenceRole.AUDIO_REFERENCE,
            )
        ),
    )

    plan = VideoPlanner().plan(request)
    projection = require_current_video_plan(current_request=request, plan=plan)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is GenerationMode.REFERENCE_TO_VIDEO
    assert projection.requirement.semantic_reference_roles == (
        SemanticReferenceRole.AUDIO_REFERENCE,
        SemanticReferenceRole.VIDEO_REFERENCE,
    )
    evidence = {item.role: item for item in projection.requirement.asset_evidence}
    assert evidence[SemanticReferenceRole.VIDEO_REFERENCE].duration_millis == 3200
    assert evidence[SemanticReferenceRole.VIDEO_REFERENCE].fps == 24
    assert evidence[SemanticReferenceRole.VIDEO_REFERENCE].canonical_owner_content_hash == (
        "4" * 64
    )


def test_v3_missing_declared_media_reference_blocks_before_routing():
    shot = _generated_shot(character_ids=())
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            semantic_reference_roles=(SemanticReferenceRole.VIDEO_REFERENCE,)
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.MISSING_REFERENCES in plan.reason_codes
    with pytest.raises(AiVideoError) as exc:
        require_current_video_plan(current_request=request, plan=plan)
    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED


def test_v3_exact_terminal_is_preserved_with_declared_video_reference():
    shot = _generated_shot(character_ids=())
    terminal = _terminal_reference()
    video = AvailableAsset(
        role=AssetRole.EXISTING_VIDEO,
        asset_id="reference-video-1",
        asset_sha256="3" * 64,
        canonical_owner_id="reference-shot",
        canonical_owner_content_hash="4" * 64,
        mime_type="video/mp4",
        width=1920,
        height=1080,
        size_bytes=4096,
        duration_millis=5000,
        fps=24,
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(terminal, video),
        previous_shot_state=make_previous_state(
            is_same_action=True,
            has_terminal_frame_asset_id=terminal.asset_id,
        ),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            semantic_reference_roles=(SemanticReferenceRole.VIDEO_REFERENCE,)
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is GenerationMode.REFERENCE_TO_VIDEO
    assert plan.generation_requirement is not None
    assert set(plan.generation_requirement.semantic_reference_roles) == {
        SemanticReferenceRole.CONTINUITY_TERMINAL,
        SemanticReferenceRole.VIDEO_REFERENCE,
    }
    assert {item.asset_id for item in plan.generation_requirement.asset_evidence} == {
        terminal.asset_id,
        video.asset_id,
    }


@pytest.mark.parametrize(
    ("operation", "expected_mode"),
    [
        (GenerationOperation.VIDEO_EDIT, GenerationMode.VIDEO_EDIT),
        (GenerationOperation.VIDEO_EXTEND, GenerationMode.VIDEO_EXTEND),
    ],
)
def test_v3_video_edit_and_extend_are_reachable_neutral_modes(
    operation: GenerationOperation,
    expected_mode: GenerationMode,
):
    shot = _generated_shot(character_ids=())
    video = AvailableAsset(
        role=AssetRole.EXISTING_VIDEO,
        asset_id="reference-video-1",
        asset_sha256="3" * 64,
        canonical_owner_id="reference-shot",
        canonical_owner_content_hash="4" * 64,
        mime_type="video/mp4",
        width=1280,
        height=720,
        size_bytes=4096,
        duration_millis=5000,
        fps=24,
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(video,),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            generation_operation=operation,
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is expected_mode
    assert plan.generation_requirement is not None
    assert plan.generation_requirement.semantic_reference_roles == (
        SemanticReferenceRole.VIDEO_REFERENCE,
    )


def test_v3_requirement_excludes_unrelated_same_role_asset():
    shot = _generated_shot()
    unrelated = make_available_asset(
        role=AssetRole.CHARACTER_REFERENCE,
        asset_id="reference-villain",
        canonical_owner_id="villain",
    )
    request = make_request(
        target_shot=shot,
        available_assets=(_character_reference(), unrelated, _scene_reference()),
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_requirement is not None
    assert "reference-villain" not in {
        item.asset_id for item in plan.generation_requirement.asset_evidence
    }


def test_v3_requirement_blocks_ambiguous_generic_video_references():
    shot = _generated_shot(character_ids=())
    videos = tuple(
        AvailableAsset(
            role=AssetRole.EXISTING_VIDEO,
            asset_id=f"reference-video-{index}",
            asset_sha256=str(index + 7) * 64,
            canonical_owner_id=f"source-{index}",
            canonical_owner_content_hash=str(index + 4) * 64,
            mime_type="video/mp4",
            width=1280,
            height=720,
            size_bytes=1_024,
            duration_millis=5_000,
            fps=24,
        )
        for index in range(2)
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=videos,
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            generation_operation=GenerationOperation.VIDEO_EDIT,
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.MISSING_REFERENCES in plan.reason_codes
    assert plan.generation_requirement is not None
    assert plan.generation_requirement.asset_evidence == ()


@pytest.mark.parametrize("reference_count", (2, 3))
def test_v3_requirement_derives_exact_multi_video_selection(
    reference_count: int,
):
    shot = _generated_shot(character_ids=())
    videos = tuple(
        AvailableAsset(
            role=AssetRole.EXISTING_VIDEO,
            asset_id=f"selected-video-{index}",
            asset_sha256=str(index + 7) * 64,
            canonical_owner_id=f"source-{index}",
            canonical_owner_content_hash=str(index + 4) * 64,
            mime_type="video/mp4",
            width=1280,
            height=720,
            size_bytes=1_024,
            duration_millis=5_000,
            fps=24,
        )
        for index in range(reference_count)
    )
    unselected = AvailableAsset(
        role=AssetRole.EXISTING_VIDEO,
        asset_id="unselected-video",
        asset_sha256="a" * 64,
        canonical_owner_id="unselected-source",
        canonical_owner_content_hash="b" * 64,
        mime_type="video/mp4",
        width=1280,
        height=720,
        size_bytes=1_024,
        duration_millis=5_000,
        fps=24,
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(*videos, unselected),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            generation_operation=GenerationOperation.VIDEO_EDIT,
            media_reference_asset_ids=tuple(item.asset_id for item in videos),
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_requirement is not None
    assert tuple(
        item.asset_id for item in plan.generation_requirement.asset_evidence
    ) == tuple(item.asset_id for item in videos)


def test_v3_requirement_blocks_missing_exact_media_selection():
    shot = _generated_shot(character_ids=())
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(
            generation_operation=GenerationOperation.VIDEO_EXTEND,
            media_reference_asset_ids=("missing-video",),
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.MISSING_REFERENCES in plan.reason_codes


@pytest.mark.parametrize(
    "factory, mutation",
    [
        (make_intent_evidence, ("character_action_required", True)),
        (make_review_decision, ("rationale", "changed")),
        (make_available_asset, ("asset_id", "changed")),
        (make_policy, ("accept_static_image_fallback", True)),
        (make_request, ("request_id", "changed")),
        (make_plan, ("rationale", "changed")),
    ],
)
def test_t1_projection_models_are_frozen(factory, mutation):
    model = factory()

    with pytest.raises(ValidationError, match="frozen"):
        setattr(model, mutation[0], mutation[1])


@pytest.mark.parametrize(
    "factory",
    [
        make_intent_evidence,
        make_review_decision,
        make_available_asset,
        make_policy,
        make_request,
        make_plan,
    ],
)
def test_t1_projection_models_forbid_extra_fields(factory):
    model = factory()
    payload = model.model_dump(mode="python")
    payload["unexpected_truth"] = True

    with pytest.raises(ValidationError, match="extra"):
        type(model).model_validate(payload)


def test_t1_intent_projection_keeps_open_close_and_motion_evidence_typed():
    state_refs_only = make_intent_evidence(
        open_state_ref="hero-inside-room",
        close_state_ref="hero-outside-room",
    )
    subject_change = make_intent_evidence(
        open_state_ref="hero-inside-room",
        close_state_ref="hero-outside-room",
        state_change_required=True,
    )
    subject_directive = make_intent_evidence(
        subject_motion_directive_present=True
    )

    assert state_refs_only.requires_subject_motion is False
    assert subject_change.requires_subject_motion is True
    assert subject_directive.requires_subject_motion is True


def test_t1_intent_and_review_projection_reject_invalid_identity_hash_shape():
    with pytest.raises(ValidationError, match="target_shot_content_hash"):
        ShotIntentEvidence(
            target_shot_id="shot-1",
            target_shot_content_hash="not-a-sha256",
        )

    with pytest.raises(ValidationError, match="target_shot_content_hash"):
        ReviewDecisionProjection(
            evidence_ref="review-1",
            target_shot_id="shot-1",
            target_shot_content_hash="not-a-sha256",
            rationale="Current director decision.",
        )


def test_t1_available_asset_includes_approved_reusable_plate_role():
    reusable = make_available_asset(
        role=AssetRole.APPROVED_REUSABLE_PLATE,
        asset_id="plate-1",
    )

    assert reusable.role is AssetRole.APPROVED_REUSABLE_PLATE
    assert reusable.asset_sha256 == ONE_HASH

    with pytest.raises(ValidationError, match="asset_sha256"):
        AvailableAsset(
            role=AssetRole.APPROVED_KEYFRAME,
            asset_id="keyframe-1",
            asset_sha256="invalid",
            canonical_owner_id="shot-1",
            mime_type="image/png",
        )


def test_t1_static_fallback_policy_is_a_sealed_semantic_input():
    denied = make_request(
        production_policy=make_policy(accept_static_image_fallback=False)
    )
    accepted = make_request(
        production_policy=make_policy(accept_static_image_fallback=True)
    )

    assert denied.production_policy.accept_static_image_fallback is False
    assert accepted.production_policy.accept_static_image_fallback is True
    assert denied.request_content_hash != accepted.request_content_hash


def test_t1_request_create_seals_all_semantic_projections():
    request = make_request()

    assert request.request_content_hash == _semantic_hash(
        request,
        "request_id",
        "request_content_hash",
    )
    assert isinstance(request.target_shot, Shot)
    assert all(isinstance(item, Character) for item in request.character_context)
    assert isinstance(request.scene_context, Scene)
    assert (
        request.shot_intent_evidence.target_shot_content_hash
        == request.target_shot.content_hash
    )

    round_trip = VideoPlanningRequest.model_validate(
        request.model_dump(mode="python")
    )
    assert round_trip == request


def test_t1_diagnostic_request_id_is_excluded_from_semantic_hash():
    first = make_request(request_id="diagnostic-attempt-1")
    second = make_request(request_id="diagnostic-attempt-2")

    assert first.request_id != second.request_id
    assert first.request_content_hash == second.request_content_hash
    assert first.model_dump(exclude={"request_id"}) == second.model_dump(
        exclude={"request_id"}
    )


def test_t1_plan_create_binds_request_and_seals_deterministic_identity():
    request = make_request()
    first = make_plan(request=request)
    second = make_plan(request=request)

    assert first.source_request_content_hash == request.request_content_hash
    assert first.plan_id == f"plan-{request.request_content_hash[:24]}"
    assert first.plan_hash == _semantic_hash(first, "plan_hash")
    assert first == second
    assert VideoGenerationPlan.model_validate(
        first.model_dump(mode="python")
    ) == first


def test_t1_plan_outcome_has_only_proposed_and_blocked():
    assert {member.value for member in PlanOutcome} == {"proposed", "blocked"}
    assert all(isinstance(member, Enum) for member in PlanOutcome)


def test_t1_planning_public_surface_does_not_create_production_truth_owners():
    forbidden_exports = {
        "ProductionShot",
        "ProductionAsset",
        "ProductionManifest",
        "AssetRegistry",
        "Registry",
    }

    assert forbidden_exports.isdisjoint(planning.__all__)
    assert VideoPlanningRequest.model_fields["target_shot"].annotation is Shot
    assert ProductionPolicyInput.model_fields[
        "accept_static_image_fallback"
    ].default is False


def _character_reference():
    return make_available_asset(
        role=AssetRole.CHARACTER_REFERENCE,
        asset_id="reference-hero",
        canonical_owner_id="hero",
    )


def _scene_reference():
    return make_available_asset(
        role=AssetRole.SCENE_REFERENCE,
        asset_id="reference-room",
        canonical_owner_id="room",
    )


def _terminal_reference():
    return make_available_asset(
        role=AssetRole.PREVIOUS_SHOT_TERMINAL,
        asset_id="terminal-shot-0",
        canonical_owner_id="shot-0",
    )


def _generated_shot(**overrides):
    return make_shot(
        visual_strategy=VisualStrategy.GENERATED_VIDEO,
        **overrides,
    )


@pytest.mark.parametrize(
    ("previous_state", "expected"),
    [
        (None, ContinuityMode.NONE),
        (make_previous_state(semantic_jump=True), ContinuityMode.SEMANTIC),
        (
            make_previous_state(is_same_action=True, is_angle_change=False),
            ContinuityMode.EXACT_TERMINAL,
        ),
        (
            make_previous_state(is_same_action=True, is_angle_change=True),
            ContinuityMode.REFERENCE,
        ),
        (make_previous_state(), ContinuityMode.REFERENCE),
    ],
)
def test_t3_continuity_matrix(previous_state, expected):
    shot = _generated_shot(character_ids=())
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        previous_shot_state=previous_state,
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.continuity_mode is expected
    assert plan.capability_requirements.needs_terminal_reference is (
        expected is ContinuityMode.EXACT_TERMINAL
    )


def test_ac1_important_character_with_references_uses_reference_video():
    shot = _generated_shot()
    request = make_request(
        target_shot=shot,
        available_assets=(_character_reference(), _scene_reference()),
        previous_shot_state=make_previous_state(is_angle_change=True),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is GenerationMode.REFERENCE_TO_VIDEO
    assert plan.continuity_mode is ContinuityMode.REFERENCE
    assert plan.capability_requirements.needs_character_reference is True
    assert ReasonCode.IMPORTANT_CHARACTER in plan.reason_codes
    assert ReasonCode.REFERENCE_AVAILABLE in plan.reason_codes


def test_ac2_exact_continuation_uses_terminal_as_first_frame():
    shot = _generated_shot()
    request = make_request(
        target_shot=shot,
        available_assets=(_terminal_reference(),),
        previous_shot_state=make_previous_state(
            is_same_action=True,
            has_terminal_frame_asset_id="terminal-shot-0",
        ),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            continuous_action_required=True,
        ),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode in {
        GenerationMode.IMAGE_TO_VIDEO,
        GenerationMode.FIRST_LAST_FRAME_VIDEO,
    }
    assert plan.continuity_mode is ContinuityMode.EXACT_TERMINAL
    assert plan.capability_requirements.needs_terminal_reference is True
    assert ReasonCode.TERMINAL_AVAILABLE in plan.reason_codes


def test_ac2_terminal_must_be_owned_by_the_previous_shot():
    shot = _generated_shot()
    request = make_request(
        target_shot=shot,
        available_assets=(
            make_available_asset(
                role=AssetRole.PREVIOUS_SHOT_TERMINAL,
                asset_id="terminal-shot-0",
                canonical_owner_id="shot-unrelated",
            ),
        ),
        previous_shot_state=make_previous_state(
            is_same_action=True,
            has_terminal_frame_asset_id="terminal-shot-0",
        ),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            continuous_action_required=True,
        ),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.MISSING_TERMINAL in plan.reason_codes


def test_ac3_independent_environment_shot_uses_text_to_video():
    shot = _generated_shot(character_ids=())
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is GenerationMode.TEXT_TO_VIDEO
    assert plan.continuity_mode is ContinuityMode.NONE
    assert plan.capability_requirements.needs_character_reference is False


def test_ac4_important_character_without_anchor_is_blocked():
    shot = _generated_shot()
    request = make_request(
        target_shot=shot,
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert plan.generation_mode is not GenerationMode.TEXT_TO_VIDEO
    assert ReasonCode.NO_VISUAL_ANCHOR in plan.reason_codes


@pytest.mark.parametrize("wrong_context", ["character", "scene"])
def test_ac4_reference_context_must_match_the_target_shot(wrong_context):
    shot = _generated_shot(character_ids=("villain",), scene_id="vault")
    character_context = (
        make_character(character_id="hero")
        if wrong_context == "character"
        else make_character(character_id="villain"),
    )
    scene_context = (
        make_scene(scene_id="room")
        if wrong_context == "scene"
        else make_scene(scene_id="vault")
    )
    request = make_request(
        target_shot=shot,
        character_context=character_context,
        scene_context=scene_context,
        available_assets=(
            make_available_asset(
                role=AssetRole.CHARACTER_REFERENCE,
                asset_id=(
                    "reference-hero"
                    if wrong_context == "character"
                    else "reference-villain"
                ),
                canonical_owner_id=(
                    "hero" if wrong_context == "character" else "villain"
                ),
            ),
            make_available_asset(
                role=AssetRole.SCENE_REFERENCE,
                asset_id=(
                    "reference-room"
                    if wrong_context == "scene"
                    else "reference-vault"
                ),
                canonical_owner_id=(
                    "room" if wrong_context == "scene" else "vault"
                ),
            ),
        ),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.NO_VISUAL_ANCHOR in plan.reason_codes


def test_ac5_angle_change_does_not_promote_terminal_to_exact_continuity():
    shot = _generated_shot()
    request = make_request(
        target_shot=shot,
        available_assets=(
            _character_reference(),
            _scene_reference(),
            _terminal_reference(),
        ),
        previous_shot_state=make_previous_state(
            is_same_action=True,
            is_angle_change=True,
            has_terminal_frame_asset_id="terminal-shot-0",
        ),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.continuity_mode is ContinuityMode.REFERENCE
    assert plan.generation_mode is GenerationMode.REFERENCE_TO_VIDEO
    assert plan.capability_requirements.needs_terminal_reference is False


def test_ac11_action_shot_bootstrapped_static_is_blocked_not_certified():
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    request = make_request(
        target_shot=shot,
        available_assets=(_character_reference(), _scene_reference()),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            open_state_ref="hero-inside-room",
            close_state_ref="hero-outside-room",
            character_action_required=True,
            state_change_required=True,
        ),
        review_decision=None,
        production_policy=make_policy(accept_static_image_fallback=False),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert plan.motion_requirement is MotionRequirement.CHARACTER_ACTION
    assert ReasonCode.STRATEGY_MOTION_MISMATCH in plan.reason_codes
    assert PlanWarning.REQUIRES_HUMAN_REVIEW in plan.warnings
    assert not (
        plan.generation_mode is GenerationMode.STATIC_IMAGE
        and plan.confidence == 1.0
    )


@pytest.mark.parametrize("kind", ["pan", "zoom", "parallax"])
def test_ac12_camera_transform_is_not_subject_motion(kind):
    shot = make_shot(
        visual_strategy=VisualStrategy.IMAGE_MOTION,
        motion_directives=(
            make_motion_directive(
                kind,
                preset="zoompan" if kind == "zoom" else "camera-only",
            ),
        ),
    )
    request = make_request(
        target_shot=shot,
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=None,
        production_policy=make_policy(accept_static_image_fallback=False),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert plan.motion_requirement is MotionRequirement.CHARACTER_ACTION
    assert ReasonCode.CAMERA_MOTION_ONLY in plan.reason_codes
    assert ReasonCode.STRATEGY_MOTION_MISMATCH in plan.reason_codes
    assert PlanWarning.CAMERA_MOTION_NOT_SUBJECT_MOTION in plan.warnings


@pytest.mark.parametrize(
    "strategy", [VisualStrategy.STATIC_IMAGE, VisualStrategy.IMAGE_MOTION]
)
def test_ac13_fallback_false_blocks_even_with_keyframe(strategy):
    shot = make_shot(visual_strategy=strategy)
    request = make_request(
        target_shot=shot,
        available_assets=(make_available_asset(),),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=make_review_decision(
            target_shot=shot,
            allows_static_fallback=True,
        ),
        production_policy=make_policy(accept_static_image_fallback=False),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.STATIC_FALLBACK_ACCEPTED not in plan.reason_codes


def test_ac14_references_do_not_satisfy_final_shot_visual():
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    request = make_request(
        target_shot=shot,
        available_assets=(_character_reference(), _scene_reference()),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=make_review_decision(target_shot=shot),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert PlanWarning.FINAL_SHOT_VISUAL_MISSING in plan.warnings
    assert any(
        item.role
        in {AssetRole.APPROVED_KEYFRAME, AssetRole.APPROVED_REUSABLE_PLATE}
        for item in plan.required_asset_roles
    )


@pytest.mark.parametrize(
    "defect",
    ["wrong_owner", "wrong_role", "missing_binding", "reuse_no_review"],
)
def test_ac14_invalid_final_visual_projection_remains_blocked(defect):
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    asset = make_available_asset()
    review = make_review_decision(target_shot=shot)
    if defect == "wrong_owner":
        asset = make_available_asset(canonical_owner_id="shot-other")
    elif defect == "wrong_role":
        shot = make_shot(
            visual_strategy=VisualStrategy.STATIC_IMAGE,
            final_visual_role="character_reference",
        )
        review = make_review_decision(target_shot=shot)
    elif defect == "missing_binding":
        shot = make_shot(
            visual_strategy=VisualStrategy.STATIC_IMAGE,
            final_visual_asset_id="different-keyframe",
        )
        review = make_review_decision(target_shot=shot)
    else:
        asset = make_available_asset(
            role=AssetRole.APPROVED_REUSABLE_PLATE,
            asset_id="keyframe-shot-1",
        )

    request = make_request(
        target_shot=shot,
        available_assets=(asset,),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=review,
    )

    assert VideoPlanner().plan(request).outcome is PlanOutcome.BLOCKED


def test_ac15_intentional_static_with_shot_keyframe_is_proposed():
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    request = make_request(
        target_shot=shot,
        available_assets=(make_available_asset(),),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=make_review_decision(target_shot=shot),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is GenerationMode.STATIC_IMAGE
    assert ReasonCode.INTENTIONAL_STATIC in plan.reason_codes
    assert ReasonCode.FINAL_SHOT_VISUAL_AVAILABLE in plan.reason_codes
    assert PlanWarning.FINAL_SHOT_VISUAL_MISSING not in plan.warnings
    assert plan.confidence < 1.0


def test_ac15_reusable_plate_requires_current_reuse_approval():
    shot = make_shot(
        visual_strategy=VisualStrategy.STATIC_IMAGE,
        final_visual_asset_id="plate-1",
    )
    request = make_request(
        target_shot=shot,
        available_assets=(
            make_available_asset(
                role=AssetRole.APPROVED_REUSABLE_PLATE,
                asset_id="plate-1",
            ),
        ),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=make_review_decision(
            target_shot=shot,
            allows_reusable_plate=True,
        ),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert ReasonCode.REUSABLE_PLATE_APPROVED in plan.reason_codes


def test_ac16_fallback_true_without_current_review_remains_blocked():
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    request = make_request(
        target_shot=shot,
        available_assets=(make_available_asset(),),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=None,
        production_policy=make_policy(accept_static_image_fallback=True),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert PlanWarning.REQUIRES_HUMAN_REVIEW in plan.warnings


def test_ac16_fallback_true_with_all_evidence_is_auditable_proposal():
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    request = make_request(
        target_shot=shot,
        available_assets=(make_available_asset(),),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=make_review_decision(
            target_shot=shot,
            rationale="Director accepts a static fallback for this exact Shot.",
            allows_intentional_static=False,
            allows_static_fallback=True,
        ),
        production_policy=make_policy(accept_static_image_fallback=True),
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert ReasonCode.STATIC_FALLBACK_ACCEPTED in plan.reason_codes
    assert PlanWarning.STATIC_FALLBACK_REQUIRES_REVIEW in plan.warnings
    assert PlanWarning.REQUIRES_HUMAN_REVIEW not in plan.warnings
    assert plan.confidence < 1.0


def test_unresolved_prose_intent_requires_review_without_keyword_routing():
    shot = _generated_shot(intent="Hero runs through the door")
    request = make_request(
        target_shot=shot,
        available_assets=(_character_reference(), _scene_reference()),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            evidence_unresolved=True,
        ),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert PlanWarning.REQUIRES_HUMAN_REVIEW in plan.warnings
    assert plan.motion_requirement is MotionRequirement.HERO_OR_REPAIR


def test_t4_non_camera_directive_and_camera_only_directive_stay_distinct():
    animated = _generated_shot(
        character_ids=(),
        motion_directives=(make_motion_directive("animate"),),
    )
    transformed = _generated_shot(
        character_ids=(),
        motion_directives=(make_motion_directive("zoom", preset="zoompan"),),
    )

    animated_plan = VideoPlanner().plan(
        make_request(
            target_shot=animated,
            character_context=(),
            available_assets=(),
            shot_intent_evidence=make_intent_evidence(target_shot=animated),
            review_decision=None,
        )
    )
    transformed_plan = VideoPlanner().plan(
        make_request(
            target_shot=transformed,
            character_context=(),
            available_assets=(),
            shot_intent_evidence=make_intent_evidence(target_shot=transformed),
            review_decision=None,
        )
    )

    assert animated_plan.motion_requirement is MotionRequirement.CHARACTER_ACTION
    assert transformed_plan.motion_requirement is MotionRequirement.LIGHT_TRANSFORM
    assert ReasonCode.CAMERA_MOTION_ONLY in transformed_plan.reason_codes


def test_motion_graphics_is_a_provider_neutral_hybrid_proposal():
    shot = make_shot(
        visual_strategy=VisualStrategy.MOTION_GRAPHICS,
        character_ids=(),
    )
    plan = VideoPlanner().plan(
        make_request(
            target_shot=shot,
            character_context=(),
            available_assets=(),
            shot_intent_evidence=make_intent_evidence(target_shot=shot),
            review_decision=None,
        )
    )

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode is GenerationMode.HYBRID


@pytest.mark.parametrize("kind", ["reveal", "layered", "particles", "transition"])
def test_motion_graphics_directives_do_not_claim_character_action(kind):
    shot = make_shot(
        visual_strategy=VisualStrategy.MOTION_GRAPHICS,
        character_ids=(),
        motion_directives=(make_motion_directive(kind),),
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.motion_requirement is MotionRequirement.GRAPHIC
    assert plan.generation_mode is GenerationMode.HYBRID
    assert plan.motion_requirement is MotionRequirement.GRAPHIC


def test_existing_video_outside_the_accepted_path_is_blocked():
    shot = make_shot(
        visual_strategy=VisualStrategy.EXISTING_VIDEO,
        character_ids=(),
    )
    plan = VideoPlanner().plan(
        make_request(
            target_shot=shot,
            character_context=(),
            available_assets=(),
            shot_intent_evidence=make_intent_evidence(target_shot=shot),
            review_decision=None,
        )
    )

    assert plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.EXISTING_VIDEO_UNSUPPORTED in plan.reason_codes


def test_stale_intent_and_review_projections_fail_closed():
    shot = _generated_shot(character_ids=())
    stale_intent = make_intent_evidence(target_shot=shot).model_copy(
        update={"target_shot_content_hash": TWO_HASH}
    )
    stale_review = make_review_decision(target_shot=shot).model_copy(
        update={"target_shot_content_hash": TWO_HASH}
    )
    request = make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=stale_intent,
        review_decision=stale_review,
    )

    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert plan.motion_requirement is MotionRequirement.HERO_OR_REPAIR
    assert ReasonCode.INTENT_EVIDENCE_NOT_CURRENT in plan.reason_codes
    assert ReasonCode.REVIEW_EVIDENCE_NOT_CURRENT in plan.reason_codes


def test_request_seal_and_remote_eligibility_are_explicit():
    request = _current_dynamic_request()
    forged_request = request.model_copy(update={"request_content_hash": TWO_HASH})
    forged_plan = VideoPlanner().plan(forged_request)
    remote_request = _rebuild_request(
        request,
        production_policy=ProductionPolicyInput(
            local_resources_available=False,
            remote_authorized=True,
            budget_authorized=True,
        ),
    )
    remote_plan = VideoPlanner().plan(remote_request)

    assert forged_plan.outcome is PlanOutcome.BLOCKED
    assert ReasonCode.REQUEST_NOT_CURRENT in forged_plan.reason_codes
    assert remote_plan.capability_requirements.accepts_local_execution is False
    assert remote_plan.capability_requirements.accepts_remote_execution is True


@pytest.mark.parametrize(
    "field",
    [
        "provider_name",
        "provider_profile",
        "selected_capability_id",
        "manifest_revision",
        "timeline_position",
        "asset_path",
        "output_asset_id",
        "generated",
        "reviewed",
        "selected",
        "locked",
        "activated",
        "creative_pass",
        "final_acceptance",
    ],
)
def test_t8_plan_forbids_provider_lifecycle_and_acceptance_fields(field):
    payload = make_plan().model_dump(mode="python")
    payload[field] = True

    with pytest.raises(ValidationError, match=field):
        VideoGenerationPlan.model_validate(payload)


def test_t9_planner_is_deterministic_and_bound_to_current_request():
    request = make_request(
        target_shot=_generated_shot(character_ids=()),
        character_context=(),
        available_assets=(),
        review_decision=None,
    )

    plans = tuple(VideoPlanner().plan(request) for _ in range(3))

    assert plans[0] == plans[1] == plans[2]
    assert len({plan.plan_hash for plan in plans}) == 1
    assert plans[0].source_request_content_hash == request.request_content_hash


def test_t9_review_policy_and_asset_binding_each_change_request_identity():
    base = make_request()
    changed_review = make_request(
        review_decision=make_review_decision(
            rationale="A replacement current review decision."
        )
    )
    changed_policy = make_request(
        production_policy=make_policy(accept_static_image_fallback=True)
    )
    changed_asset = make_request(
        available_assets=(make_available_asset(asset_id="different-keyframe"),)
    )

    assert len(
        {
            base.request_content_hash,
            changed_review.request_content_hash,
            changed_policy.request_content_hash,
            changed_asset.request_content_hash,
        }
    ) == 4


def test_t10_planning_import_boundary_and_no_runtime_skill_calls():
    planning_root = Path("src/ai_video/planning")
    forbidden_prefixes = (
        "ai_video.production.state_commit",
        "ai_video.production.registry",
        "ai_video.production.dependency",
        "ai_video.production.composition",
        "ai_video.production.hyperframes",
        "ai_video.production.video",
        "ai_video.production.shot_router",
        "ai_video.cli",
        "ai_video.comfy_client",
        "ai_video.ffmpeg_tools",
        "os",
        "subprocess",
        "httpx",
        "requests",
        "keyring",
    )
    skill_tokens = {"higgsfield", "hell_grind", "video_shotcraft", "skills"}

    for path in planning_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                modules = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = (node.module,)
            for module in modules:
                assert not any(
                    module == prefix or module.startswith(f"{prefix}.")
                    for prefix in forbidden_prefixes
                ), (
                    f"{path}:{node.lineno} forbidden planning import {module}"
                )
                assert module not in skill_tokens


def test_t10_production_does_not_reverse_import_planning():
    for path in Path("src/ai_video/production").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = (node.module,)
            else:
                continue
            assert all(
                not module.startswith("ai_video.planning") for module in modules
            ), f"{path}:{node.lineno} Production reverse-imports planning"


def test_t11_previous_state_helper_uses_explicit_continuity_evidence():
    previous = _generated_shot(shot_id="shot-0")
    target = _generated_shot(shot_id="shot-1")

    assert (
        VideoPlanner.derive_previous_shot_state(
            previous_shot=None,
            target_shot=target,
        )
        is None
    )

    default = VideoPlanner.derive_previous_shot_state(
        previous_shot=previous,
        target_shot=target,
    )
    explicit = VideoPlanner.derive_previous_shot_state(
        previous_shot=previous,
        target_shot=target,
        is_same_action=True,
        is_angle_change=True,
        has_terminal_frame_asset_id="terminal-shot-0",
    )

    assert default is not None
    assert default.is_same_action is False
    assert explicit is not None
    assert explicit.is_same_action is True
    assert explicit.is_angle_change is True
    assert explicit.has_terminal_frame_asset_id == "terminal-shot-0"


def _current_dynamic_request():
    shot = _generated_shot(character_ids=())
    return make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(),
    )


def _rebuild_request(
    request: VideoPlanningRequest, **updates: object
) -> VideoPlanningRequest:
    payload = request.model_dump(
        mode="python",
        exclude={"request_content_hash"},
    )
    payload.update(updates)
    return VideoPlanningRequest.create(**payload)


def _rebuild_plan(
    plan: VideoGenerationPlan, **updates: object
) -> VideoGenerationPlan:
    payload = {
        field: getattr(plan, field)
        for field in type(plan).model_fields
        if field not in {"plan_id", "plan_hash"}
    }
    payload.update(updates)
    return VideoGenerationPlan.create(**payload)


@pytest.mark.parametrize(
    "stop_reason",
    [
        "blocked_outcome",
        "stale_source_request_hash",
        "stale_shot_id",
        "stale_shot_revision",
        "stale_shot_hash",
        "changed_review_same_shot_hash",
        "changed_policy_same_shot_hash",
        "changed_asset_binding_same_shot_hash",
        "missing_required_asset",
        "wrong_asset_owner_or_binding",
        "wrong_final_visual_role_binding",
        "wrong_terminal_owner",
        "unresolved_human_review",
    ],
)
def test_ac17_main_agent_preflight_stops_before_execution(stop_reason):
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    if stop_reason == "blocked_outcome":
        blocked_shot = _generated_shot()
        current_request = make_request(
            target_shot=blocked_shot,
            available_assets=(),
            shot_intent_evidence=make_intent_evidence(
                target_shot=blocked_shot,
                character_action_required=True,
            ),
            review_decision=None,
        )
        plan = VideoPlanner().plan(current_request)
    elif stop_reason == "stale_source_request_hash":
        plan = plan.model_copy(update={"source_request_content_hash": TWO_HASH})
    elif stop_reason == "stale_shot_id":
        plan = plan.model_copy(update={"target_shot_id": "shot-other"})
    elif stop_reason == "stale_shot_revision":
        plan = plan.model_copy(update={"target_shot_revision": 99})
    elif stop_reason == "stale_shot_hash":
        plan = plan.model_copy(update={"target_shot_content_hash": TWO_HASH})
    elif stop_reason == "changed_review_same_shot_hash":
        current_request = _rebuild_request(
            current_request,
            review_decision=make_review_decision(
                target_shot=current_request.target_shot,
                rationale="A current replacement decision.",
            ),
        )
    elif stop_reason == "changed_policy_same_shot_hash":
        current_request = _rebuild_request(
            current_request,
            production_policy=make_policy(accept_static_image_fallback=True),
        )
    elif stop_reason == "changed_asset_binding_same_shot_hash":
        current_request = _rebuild_request(
            current_request,
            available_assets=(_scene_reference(),),
        )
    elif stop_reason in {
        "missing_required_asset",
        "wrong_asset_owner_or_binding",
        "wrong_final_visual_role_binding",
    }:
        static_shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
        valid_request = make_request(
            target_shot=static_shot,
            available_assets=(make_available_asset(),),
            shot_intent_evidence=make_intent_evidence(target_shot=static_shot),
            review_decision=make_review_decision(target_shot=static_shot),
        )
        plan = VideoPlanner().plan(valid_request)
        current_shot = (
            make_shot(
                visual_strategy=VisualStrategy.STATIC_IMAGE,
                final_visual_role="character_reference",
            )
            if stop_reason == "wrong_final_visual_role_binding"
            else static_shot
        )
        current_request = make_request(
            target_shot=current_shot,
            available_assets=(
                ()
                if stop_reason == "missing_required_asset"
                else (make_available_asset(canonical_owner_id="shot-other"),)
                if stop_reason == "wrong_asset_owner_or_binding"
                else (make_available_asset(),)
            ),
            shot_intent_evidence=make_intent_evidence(target_shot=current_shot),
            review_decision=make_review_decision(target_shot=current_shot),
        )
        plan = _rebuild_plan(
            plan,
            source_request_content_hash=current_request.request_content_hash,
            target_shot_content_hash=current_shot.content_hash,
        )
    elif stop_reason == "wrong_terminal_owner":
        terminal_shot = _generated_shot()
        valid_request = make_request(
            target_shot=terminal_shot,
            available_assets=(_terminal_reference(),),
            previous_shot_state=make_previous_state(
                is_same_action=True,
                has_terminal_frame_asset_id="terminal-shot-0",
            ),
            shot_intent_evidence=make_intent_evidence(
                target_shot=terminal_shot,
                continuous_action_required=True,
            ),
            review_decision=None,
        )
        plan = VideoPlanner().plan(valid_request)
        current_request = _rebuild_request(
            valid_request,
            available_assets=(
                make_available_asset(
                    role=AssetRole.PREVIOUS_SHOT_TERMINAL,
                    asset_id="terminal-shot-0",
                    canonical_owner_id="shot-unrelated",
                ),
            ),
        )
        plan = _rebuild_plan(
            plan,
            source_request_content_hash=current_request.request_content_hash,
        )
    else:
        plan = _rebuild_plan(
            plan,
            warnings=(PlanWarning.REQUIRES_HUMAN_REVIEW,),
        )

    downstream = tuple(Mock(name=name) for name in (
        "router",
        "provider",
        "materializer",
        "composition",
        "render",
    ))
    handoff = Mock(side_effect=lambda **_: [call() for call in downstream])

    with pytest.raises(AiVideoError) as exc:
        prepare_shot_for_existing_production(
            current_request=current_request,
            plan=plan,
            production_handoff=handoff,
        )

    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED
    handoff.assert_not_called()
    for call in downstream:
        call.assert_not_called()


def test_ac18_proposed_plan_only_enters_existing_production_handoff():
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    handoff = Mock(return_value="eligible")

    result = prepare_shot_for_existing_production(
        current_request=current_request,
        plan=plan,
        production_handoff=handoff,
    )

    assert result == "eligible"
    handoff.assert_called_once()
    handoff_kwargs = handoff.call_args.kwargs
    assert handoff_kwargs["current_shot"] == current_request.target_shot
    assert isinstance(
        handoff_kwargs["generation_requirement"],
        VerifiedGenerationRequirementProjection,
    )
    assert "plan_hint" not in handoff_kwargs
    for forbidden in (
        "generated",
        "reviewed",
        "selected",
        "locked",
        "activated",
        "creative_pass",
        "final_acceptance",
    ):
        assert forbidden not in type(plan).model_fields


def test_consumer_accepts_current_plan_directly():
    request = _current_dynamic_request()
    plan = VideoPlanner().plan(request)

    projection = require_current_video_plan(
        current_request=request,
        plan=plan,
    )
    assert isinstance(projection, VerifiedGenerationRequirementProjection)
    assert projection.requirement == plan.generation_requirement


@pytest.mark.parametrize("forged", ["request", "plan", "plan_id"])
def test_consumer_rejects_invalid_request_or_plan_seal(forged):
    request = _current_dynamic_request()
    plan = VideoPlanner().plan(request)
    if forged == "request":
        request = request.model_copy(update={"request_content_hash": TWO_HASH})
    elif forged == "plan":
        plan = plan.model_copy(update={"confidence": 0.1})
    else:
        forged_plan = plan.model_copy(update={"plan_id": "plan-arbitrary"})
        plan = forged_plan.model_copy(
            update={"plan_hash": _semantic_hash(forged_plan, "plan_hash")}
        )

    with pytest.raises(AiVideoError) as exc:
        require_current_video_plan(current_request=request, plan=plan)

    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED


def test_consumer_rejects_resealed_requirement_not_uniquely_derived_by_planner():
    request = _current_dynamic_request()
    plan = VideoPlanner().plan(request)
    requirement = plan.generation_requirement
    assert requirement is not None
    forged_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            "output_need": requirement.output_need.model_copy(
                update={"fps": 30}
            ),
        }
    )
    forged_plan = VideoGenerationPlan.create(
        **{
            **plan.model_dump(
                mode="python",
                exclude={"plan_id", "plan_hash"},
            ),
            "generation_requirement": forged_requirement,
        }
    )

    with pytest.raises(AiVideoError) as exc:
        require_current_video_plan(current_request=request, plan=forged_plan)

    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED


def test_consumer_allows_auditable_static_fallback_warning_when_resolved():
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    request = make_request(
        target_shot=shot,
        available_assets=(make_available_asset(),),
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
        ),
        review_decision=make_review_decision(
            target_shot=shot,
            allows_intentional_static=False,
            allows_static_fallback=True,
        ),
        production_policy=make_policy(accept_static_image_fallback=True),
        planning_contract_version="video-planner/3",
        generation_intent=_neutral_generation_intent(),
    )
    plan = VideoPlanner().plan(request)

    assert PlanWarning.STATIC_FALLBACK_REQUIRES_REVIEW in plan.warnings
    assert PlanWarning.REQUIRES_HUMAN_REVIEW not in plan.warnings
    projection = require_current_video_plan(current_request=request, plan=plan)
    assert isinstance(projection, VerifiedGenerationRequirementProjection)
