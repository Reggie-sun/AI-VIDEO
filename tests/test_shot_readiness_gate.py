from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning import (
    AssetRole,
    PlanOutcome,
    PlanWarning,
    VideoPlanner,
    VideoPlanningRequest,
    require_current_video_plan,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import AssetRoleRequirement, AssetType, Shot, VisualStrategy
from ai_video.production.video_requirement import (
    AudioNeed,
    ConditioningCompatibilityEvidence,
    ConditioningLane,
    GenerationIntent,
    MotionEnvelope,
    OutputGeometryPolicy,
    OutputNeed,
    ProviderNeutralGenerationIntentProjection,
    QualityNeed,
    SemanticReferenceRole,
    SubjectAction,
    VerifiedGenerationRequirementProjection,
)
from ai_video.production.video_transition import (
    BoundaryKind,
    CausalDimension,
    CausalEdgeSemantics,
    CausalStateChange,
    CausalTransitionMode,
    ContinuityObligation,
    ContinuityTransitionPolicy,
    CreativeArtifactIdentity,
)
from tests.test_production_video_intent_validation import _complete_intent
from tests.test_production_video_transition import _policy as _transition_policy
from tests.fixtures.planning_factory import (
    TWO_HASH,
    make_available_asset,
    make_character,
    make_intent_evidence,
    make_previous_state,
    make_request,
    make_review_decision,
    make_scene,
    make_shot,
)


def _gate_api() -> ModuleType:
    try:
        return importlib.import_module("ai_video.quality_gates")
    except ModuleNotFoundError:
        pytest.fail("ShotReadinessGate public API is not implemented")


def _generation_intent() -> ProviderNeutralGenerationIntentProjection:
    return ProviderNeutralGenerationIntentProjection.create(
        generation_intent=GenerationIntent(
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
    )


def _current_dynamic_request() -> VideoPlanningRequest:
    shot = make_shot(
        visual_strategy=VisualStrategy.GENERATED_VIDEO,
        character_ids=(),
    )
    return make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=_generation_intent(),
    )


def _current_static_request() -> VideoPlanningRequest:
    shot = make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE)
    return make_request(
        target_shot=shot,
        available_assets=(
            make_available_asset().model_copy(
                update={"canonical_owner_content_hash": shot.content_hash}
            ),
        ),
        shot_intent_evidence=make_intent_evidence(target_shot=shot),
        review_decision=make_review_decision(target_shot=shot),
        planning_contract_version="video-planner/3",
        generation_intent=_generation_intent(),
    )


def _current_v4_causal_request() -> VideoPlanningRequest:
    shot = make_shot(
        visual_strategy=VisualStrategy.GENERATED_VIDEO,
        character_ids=(),
    )
    previous = make_previous_state(
        previous_shot_id="shot-0",
        previous_shot_content_hash=TWO_HASH,
        previous_shot_artifact_id="shot-0-artifact",
        previous_shot_revision=1,
        previous_generation_intent_hash="3" * 64,
        is_same_action=True,
        has_terminal_frame_asset_id="anchor-first",
    )
    projection = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=_complete_intent(),
        conditioning_compatibility=ConditioningCompatibilityEvidence(
            lane=ConditioningLane.I2VA,
            first_anchor_id="anchor-first",
            available_duration_seconds=124 / 24,
        ),
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=1920,
            height=1080,
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.OPTIONAL,
        quality_need=QualityNeed(objective_tier="production"),
    )
    return make_request(
        target_shot=shot,
        character_context=(),
        available_assets=(
            make_available_asset(
                role=AssetRole.PREVIOUS_SHOT_TERMINAL,
                asset_id="anchor-first",
                canonical_owner_id="shot-0",
                canonical_owner_content_hash=TWO_HASH,
            ),
        ),
        previous_shot_state=previous,
        shot_intent_evidence=make_intent_evidence(
            target_shot=shot,
            character_action_required=True,
            continuous_action_required=True,
        ),
        review_decision=None,
        planning_contract_version="video-planner/3",
        generation_intent=projection,
    )


def _complete_causal_policy(
    requirement_hash: str,
    target_shot: Shot,
    *,
    omit_dimension: CausalDimension | None = None,
    schema_version: str = "2",
) -> ContinuityTransitionPolicy:
    original = _transition_policy(source=1, target=2, stack_hash="0" * 64)
    excluded = {
            "schema_version",
            "source_shot",
            "target_shot",
            "source_generation_intent_hash",
            "target_generation_intent_hash",
            "causal_edge_semantics",
            "causal_state_changes",
            "policy_hash",
    }
    base = {
        field: getattr(original, field)
        for field in type(original).model_fields
        if field not in excluded
    }
    changes = tuple(
        CausalStateChange(
            dimension=dimension,
            source_close=f"{dimension.value}-stable",
            target_open=f"{dimension.value}-stable",
            transition_mode=CausalTransitionMode.CARRY,
        )
        for dimension in sorted(CausalDimension, key=lambda item: item.value)
        if dimension is not omit_dimension
    )
    return ContinuityTransitionPolicy.create(
        **base,
        schema_version=schema_version,
        source_shot=CreativeArtifactIdentity(
            artifact_id="shot-0-artifact",
            revision=1,
            content_hash=TWO_HASH,
        ),
        target_shot=CreativeArtifactIdentity(
            artifact_id=target_shot.artifact_id,
            revision=target_shot.revision,
            content_hash=target_shot.content_hash,
        ),
        **({
            "source_generation_intent_hash": "3" * 64,
            "target_generation_intent_hash": requirement_hash,
            "causal_edge_semantics": CausalEdgeSemantics.DIRECT_CONTINUITY,
            "causal_state_changes": changes,
        } if schema_version == "2" else {}),
    )


def test_v4_continuity_blocks_without_pairwise_causal_policy() -> None:
    api = _gate_api()
    current_request = _current_v4_causal_request()
    plan = VideoPlanner().plan(current_request)
    assert plan.generation_requirement is not None
    assert plan.generation_requirement.contract_version.endswith("/4")

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id="readiness-v4-causal-missing",
            current_request=current_request,
            plan=plan,
        )
    )

    assert result.status.value == "blocked"
    binding = result.checks[0]
    assert "causal_transition_invalid" in {
        item.value for item in binding.reason_codes
    }
    assert binding.payload.failure_field_paths == (
        "continuity_transition_policy",
    )


def _hard_cut_first_frame_request(*, rich_intent: bool, defect: str | None = None):
    original = _current_v4_causal_request()
    shot = seal_artifact(original.target_shot.model_copy(update={
        "required_asset_roles": (
            AssetRoleRequirement(role="final_visual", asset_ids=(), allowed_asset_types=(AssetType.VIDEO,)),
            AssetRoleRequirement(
                role="first_frame", asset_ids=("other-frame" if defect == "unbound" else "derived-opening",),
                allowed_asset_types=(AssetType.IMAGE,),
            ),
        ),
    }))
    intent = original.generation_intent if rich_intent else _generation_intent()
    intent = ProviderNeutralGenerationIntentProjection.create(**{
        **{name: getattr(intent, name) for name in type(intent).model_fields if name != "projection_hash"},
        "semantic_reference_roles": (SemanticReferenceRole.FIRST_FRAME,),
        **({"conditioning_compatibility": intent.conditioning_compatibility.model_copy(update={
            "first_anchor_id": "derived-opening",
        })} if rich_intent else {}),
    })
    frame = make_available_asset(
        asset_id="derived-opening", role=AssetRole.APPROVED_KEYFRAME,
        canonical_owner_id="other-shot" if defect == "wrong_owner" else shot.shot_id,
        canonical_owner_content_hash=TWO_HASH if defect == "stale_owner" else shot.content_hash,
    )
    previous = original.previous_shot_state.model_copy(update={
        "is_same_action": defect == "continuous_take",
        "is_angle_change": defect != "continuous_take",
        "has_terminal_frame_asset_id": None if defect == "continuous_take" else "anchor-first",
    })
    return VideoPlanningRequest.create(**{
        **original.model_dump(mode="python", exclude={"request_content_hash"}),
        "target_shot": shot, "generation_intent": intent, "previous_shot_state": previous,
        "available_assets": () if defect == "missing" else (frame,),
        "shot_intent_evidence": make_intent_evidence(target_shot=shot, character_action_required=True),
    })


@pytest.mark.parametrize("rich_intent", [False, True])
def test_full_hard_cut_first_frame_reaches_standard_planner_and_readiness(rich_intent):
    request = _hard_cut_first_frame_request(rich_intent=rich_intent)
    plan = VideoPlanner().plan(request)
    assert plan.outcome is PlanOutcome.PROPOSED
    assert plan.generation_mode.value == "image_to_video"
    assert plan.continuity_mode.value == "reference"
    requirement = plan.generation_requirement
    assert requirement is not None
    policy = _complete_causal_policy(requirement.generation_intent_hash, request.target_shot)
    projection = require_current_video_plan(
        current_request=request, plan=plan, continuity_transition_policy=policy,
    )
    assert projection.requirement == requirement
    assert requirement.capability_need.needs_first_frame
    assert requirement.semantic_reference_roles == (SemanticReferenceRole.FIRST_FRAME,)
    assert requirement.asset_evidence[0].asset_id == "derived-opening"


@pytest.mark.parametrize("defect", ["wrong_owner", "stale_owner", "unbound", "missing", "continuous_take"])
def test_hard_cut_first_frame_keeps_exact_asset_and_terminal_guards(defect):
    request = _hard_cut_first_frame_request(rich_intent=False, defect=defect)
    plan = VideoPlanner().plan(request)
    assert plan.outcome is PlanOutcome.BLOCKED
    with pytest.raises(AiVideoError):
        require_current_video_plan(current_request=request, plan=plan)


@pytest.mark.parametrize("schema_version", ["1", "2"])
def test_readiness_explicit_full_policy_cannot_be_ignored_by_none_mode(schema_version) -> None:
    api = _gate_api()
    original = _current_dynamic_request()
    current_request = VideoPlanningRequest.create(**{
        **original.model_dump(mode="python", exclude={"request_content_hash"}),
        "previous_shot_state": None,
    })
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None
    assert requirement.continuity_mode.value == "none"
    policy = _complete_causal_policy(
        requirement.generation_intent_hash, requirement.target_shot, schema_version=schema_version,
    )
    result = api.ShotReadinessGate().evaluate(api.ShotReadinessRequest.create(
        request_id="explicit-full-none-downgrade", current_request=current_request,
        plan=plan, contract_version="shot-readiness-gate/2", continuity_transition_policy=policy,
    ))
    assert result.status.value == "blocked"
    assert "causal_transition_invalid" in {r.value for r in result.checks[0].reason_codes}


@pytest.mark.parametrize("schema_version", ["1", "2"])
def test_readiness_substantial_reset_remains_legal_without_previous_conditioning(schema_version) -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None
    assert requirement.continuity_mode.value == "none"
    original = _complete_causal_policy(
        requirement.generation_intent_hash, requirement.target_shot, schema_version=schema_version,
    )
    policy = ContinuityTransitionPolicy.create(**{
        **{name: getattr(original, name) for name in type(original).model_fields if name != "policy_hash"},
        "boundary_kind": BoundaryKind.SCENE_BOUNDARY,
        "continuity_obligation": ContinuityObligation.SUBSTANTIAL_RESET,
        **({"causal_edge_semantics": CausalEdgeSemantics.SCENE_RESET} if schema_version == "2" else {}),
        "required_carryover_dimensions": (),
        "anchors": (),
    })
    result = api.ShotReadinessGate().evaluate(api.ShotReadinessRequest.create(
        request_id="explicit-reset-without-conditioning", current_request=current_request,
        plan=plan, contract_version="shot-readiness-gate/2", continuity_transition_policy=policy,
    ))
    assert result.status.value == "ready", result.checks[0].payload.failure_field_paths


@pytest.mark.parametrize("obligation", [
    ContinuityObligation.FULL_CONTINUITY,
    ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
])
def test_readiness_legacy_v1_policy_preserves_valid_conditioning_paths(obligation) -> None:
    api = _gate_api()
    original = _current_v4_causal_request()
    previous = original.previous_shot_state.model_copy(update={
        "previous_shot_artifact_id": None, "previous_shot_revision": None,
        "previous_generation_intent_hash": None,
        "is_same_action": obligation is ContinuityObligation.FULL_CONTINUITY,
        "is_angle_change": obligation is ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
    })
    current_request = VideoPlanningRequest.create(**{
        **original.model_dump(mode="python", exclude={"request_content_hash"}),
        "generation_intent": _generation_intent(), "previous_shot_state": previous,
    })
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None and requirement.contract_version.endswith("/1")
    original = _complete_causal_policy(
        requirement.generation_intent_hash, requirement.target_shot, schema_version="1",
    )
    policy = ContinuityTransitionPolicy.create(**{
        **{name: getattr(original, name) for name in type(original).model_fields if name != "policy_hash"},
        "continuity_obligation": obligation,
    })
    result = api.ShotReadinessGate().evaluate(api.ShotReadinessRequest.create(
        request_id="legacy-v1-continuity", current_request=current_request,
        plan=plan, contract_version="shot-readiness-gate/2", continuity_transition_policy=policy,
    ))
    assert result.status.value == "ready", result.checks[0].payload.failure_field_paths


def test_readiness_v4_continuity_still_requires_v2_causality() -> None:
    api = _gate_api()
    current_request = _current_v4_causal_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    policy = _complete_causal_policy(
        requirement.generation_intent_hash, requirement.target_shot, schema_version="1",
    )
    result = api.ShotReadinessGate().evaluate(api.ShotReadinessRequest.create(
        request_id="v4-cannot-use-legacy-causality", current_request=current_request,
        plan=plan, contract_version="shot-readiness-gate/2", continuity_transition_policy=policy,
    ))
    assert result.status.value == "blocked"
    assert "continuity_transition_policy.schema_version" in result.checks[0].payload.failure_field_paths


def test_readiness_legacy_policy_still_binds_exact_target() -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    original = _complete_causal_policy(
        requirement.generation_intent_hash, requirement.target_shot, schema_version="1",
    )
    policy = ContinuityTransitionPolicy.create(**{
        **{name: getattr(original, name) for name in type(original).model_fields if name != "policy_hash"},
        "boundary_kind": BoundaryKind.SCENE_BOUNDARY,
        "continuity_obligation": ContinuityObligation.SUBSTANTIAL_RESET,
        "required_carryover_dimensions": (), "anchors": (),
        "target_shot": original.target_shot.model_copy(update={"content_hash": "5" * 64}),
    })
    result = api.ShotReadinessGate().evaluate(api.ShotReadinessRequest.create(
        request_id="legacy-v1-wrong-target", current_request=current_request,
        plan=plan, contract_version="shot-readiness-gate/2", continuity_transition_policy=policy,
    ))
    assert result.status.value == "blocked"
    assert "continuity_transition_policy.target_shot" in result.checks[0].payload.failure_field_paths


def test_v4_continuity_ready_only_with_exact_complete_pairwise_policy() -> None:
    api = _gate_api()
    current_request = _current_v4_causal_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None
    policy = _complete_causal_policy(
        requirement.generation_intent_hash,
        requirement.target_shot,
    )

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id="readiness-v4-causal-complete",
            current_request=current_request,
            plan=plan,
            contract_version="shot-readiness-gate/2",
            continuity_transition_policy=policy,
        )
    )

    assert result.status.value == "ready"
    assert result.verified_generation_requirement is not None


def test_v4_continuity_blocks_when_one_causal_dimension_is_missing() -> None:
    api = _gate_api()
    current_request = _current_v4_causal_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None
    policy = _complete_causal_policy(
        requirement.generation_intent_hash,
        requirement.target_shot,
        omit_dimension=CausalDimension.PROP_HOLDER,
    )

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id="readiness-v4-causal-holder-missing",
            current_request=current_request,
            plan=plan,
            contract_version="shot-readiness-gate/2",
            continuity_transition_policy=policy,
        )
    )

    assert result.status.value == "blocked"
    assert (
        "continuity_transition_policy.causal_state_changes.prop_holder"
        in result.checks[0].payload.failure_field_paths
    )


def test_v4_continuity_blocks_stale_transition_policy_seal() -> None:
    api = _gate_api()
    current_request = _current_v4_causal_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None
    policy = _complete_causal_policy(
        requirement.generation_intent_hash,
        requirement.target_shot,
    )
    sealed = api.ShotReadinessRequest.create(
        request_id="readiness-v4-causal-stale-policy",
        current_request=current_request,
        plan=plan,
        contract_version="shot-readiness-gate/2",
        continuity_transition_policy=policy,
    )
    changed = policy.causal_state_changes[0].model_copy(
        update={"source_close": "mutated after sealing"}
    )
    stale_policy = policy.model_copy(
        update={
            "causal_state_changes": (changed,) + policy.causal_state_changes[1:]
        }
    )
    stale_request = sealed.model_copy(
        update={"continuity_transition_policy": stale_policy}
    )

    result = api.ShotReadinessGate().evaluate(stale_request)

    assert result.status.value == "blocked"
    assert result.checks[0].payload.failure_field_paths == (
        "continuity_transition_policy.policy_hash",
    )


def test_ready_current_v3_plan_returns_exact_verified_projection() -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)

    readiness_request = api.ShotReadinessRequest.create(
        request_id="readiness-shot-1-attempt-1",
        current_request=current_request,
        plan=plan,
    )
    result = api.ShotReadinessGate().evaluate(readiness_request)
    projection = api.require_ready(result)

    assert result.status.value == "ready"
    assert tuple(check.check_id for check in result.checks) == (
        "request_plan_binding",
        "plan_eligibility",
        "required_asset_readiness",
    )
    assert all(check.status.value == "pass" for check in result.checks)
    assert isinstance(projection, VerifiedGenerationRequirementProjection)
    assert projection == result.verified_generation_requirement
    assert projection.requirement == plan.generation_requirement
    assert projection.plan_hash == plan.plan_hash


def test_readiness_request_hash_excludes_both_diagnostic_request_ids() -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)

    first = api.ShotReadinessRequest.create(
        request_id="readiness-diagnostic-1",
        current_request=current_request,
        plan=plan,
    )
    second = api.ShotReadinessRequest.create(
        request_id="readiness-diagnostic-2",
        current_request=current_request.model_copy(
            update={"request_id": "planner-diagnostic-2"}
        ),
        plan=plan,
    )

    assert first.request_content_hash == second.request_content_hash


def test_tampered_outer_request_seal_blocks_without_exposing_projection() -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    sealed = api.ShotReadinessRequest.create(
        request_id="readiness-shot-1-attempt-1",
        current_request=current_request,
        plan=plan,
    )

    result = api.ShotReadinessGate().evaluate(
        sealed.model_copy(update={"request_content_hash": TWO_HASH})
    )

    assert result.status.value == "blocked"
    assert result.verified_generation_requirement is None
    binding = result.checks[0]
    assert binding.status.value == "blocked"
    assert "readiness_request_seal_invalid" in {
        reason.value for reason in binding.reason_codes
    }
    with pytest.raises(AiVideoError) as exc:
        api.require_ready(result)
    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED
    assert exc.value.retryable is False


@pytest.mark.parametrize(
    ("mutation", "expected_field_path"),
    [
        ("request_seal", "current_request.request_content_hash"),
        ("plan_seal", "plan.plan_hash"),
        ("plan_id", "plan.plan_id"),
        ("source_request", "plan.source_request_content_hash"),
        ("target_shot", "plan.target_shot_id"),
        ("embedded_requirement", "plan.generation_requirement"),
    ],
)
def test_binding_mutation_matrix_emits_typed_complete_diagnostics(
    mutation: str,
    expected_field_path: str,
) -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    if mutation == "request_seal":
        current_request = current_request.model_copy(
            update={"request_content_hash": TWO_HASH}
        )
    elif mutation == "plan_seal":
        plan = plan.model_copy(update={"confidence": 0.1})
    elif mutation == "plan_id":
        plan = plan.model_copy(update={"plan_id": "plan-arbitrary"})
    elif mutation == "source_request":
        plan = plan.model_copy(update={"source_request_content_hash": TWO_HASH})
    elif mutation == "target_shot":
        plan = plan.model_copy(update={"target_shot_id": "shot-other"})
    else:
        requirement = plan.generation_requirement
        assert requirement is not None
        plan = plan.model_copy(
            update={
                "generation_requirement": requirement.model_copy(
                    update={"requirement_hash": TWO_HASH}
                )
            }
        )

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id=f"readiness-mutation-{mutation}",
            current_request=current_request,
            plan=plan,
        )
    )

    binding = result.checks[0]
    assert result.status.value == "blocked"
    assert binding.status.value == "blocked"
    assert "current_plan_projection_invalid" in {
        reason.value for reason in binding.reason_codes
    }
    assert expected_field_path in binding.payload.failure_field_paths
    assert binding.payload.verified_projection_valid is False


def test_historical_v2_plan_is_reopen_only_at_new_attempt_boundary() -> None:
    api = _gate_api()
    current_request = make_request()
    plan = VideoPlanner().plan(current_request)
    assert current_request.planning_contract_version == "video-planner/2"
    assert plan.planning_contract_version == "video-planner/2"

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id="readiness-v2-reopen-only",
            current_request=current_request,
            plan=plan,
        )
    )

    assert result.status.value == "blocked"
    assert result.verified_generation_requirement is None
    assert "legacy_planner_reopen_only" in {
        reason.value for reason in result.checks[0].reason_codes
    }
    binding = result.checks[0].payload
    assert binding.current_v3_contract is False
    assert binding.request_seal_valid is False
    assert binding.plan_seal_valid is False
    assert binding.unique_current_derivation_valid is False
    assert binding.plan_id_valid is False
    assert binding.source_request_valid is False
    assert binding.target_shot_valid is False
    assert binding.embedded_requirement_valid is False
    assert binding.verified_projection_valid is False


@pytest.mark.parametrize(
    ("plan_update", "expected_reason"),
    [
        ({"outcome": PlanOutcome.BLOCKED}, "plan_blocked"),
        (
            {"warnings": (PlanWarning.REQUIRES_HUMAN_REVIEW,)},
            "human_review_unresolved",
        ),
    ],
)
def test_plan_eligibility_is_owned_by_gate(
    plan_update: dict[str, object], expected_reason: str
) -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request).model_copy(update=plan_update)

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id=f"readiness-{expected_reason}",
            current_request=current_request,
            plan=plan,
        )
    )

    eligibility = result.checks[1]
    assert eligibility.status.value == "blocked"
    assert expected_reason in {reason.value for reason in eligibility.reason_codes}
    assert result.verified_generation_requirement is None


def test_required_asset_diagnostics_use_current_exact_binding() -> None:
    api = _gate_api()
    planned_request = _current_static_request()
    plan = VideoPlanner().plan(planned_request)
    current_request = VideoPlanningRequest.create(
        **{
            **planned_request.model_dump(
                mode="python",
                exclude={"request_content_hash"},
            ),
            "available_assets": (
                make_available_asset(canonical_owner_id="shot-unrelated"),
            ),
        }
    )

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id="readiness-wrong-asset-owner",
            current_request=current_request,
            plan=plan,
        )
    )

    assets = result.checks[2]
    assert assets.status.value == "blocked"
    assert assets.payload.required_roles == (AssetRole.APPROVED_KEYFRAME,)
    assert assets.payload.ready_roles == ()
    assert assets.payload.missing_roles == (AssetRole.APPROVED_KEYFRAME,)
    assert "required_asset_missing" in {
        reason.value for reason in assets.reason_codes
    }


@pytest.mark.parametrize(
    "binding_kind",
    ["character", "scene", "previous_terminal", "final_visual"],
)
def test_v3_required_assets_reject_stale_canonical_content_binding(
    binding_kind: str,
) -> None:
    api = _gate_api()
    character = make_character()
    scene = make_scene()
    shot = make_shot(
        visual_strategy=(
            VisualStrategy.STATIC_IMAGE
            if binding_kind == "final_visual"
            else VisualStrategy.GENERATED_VIDEO
        ),
        character_ids=(
            (character.character_id,)
            if binding_kind in {"character", "scene"}
            else ()
        ),
    )
    assets = {
        "character": make_available_asset(
            role=AssetRole.CHARACTER_REFERENCE,
            asset_id="reference-hero",
            canonical_owner_id=character.character_id,
        ).model_copy(
            update={"canonical_owner_content_hash": character.content_hash}
        ),
        "scene": make_available_asset(
            role=AssetRole.SCENE_REFERENCE,
            asset_id="reference-room",
            canonical_owner_id=scene.scene_id,
        ).model_copy(
            update={"canonical_owner_content_hash": scene.content_hash}
        ),
        "previous_terminal": make_available_asset(
            role=AssetRole.PREVIOUS_SHOT_TERMINAL,
            asset_id="terminal-shot-0",
            canonical_owner_id="shot-0",
        ).model_copy(update={"canonical_owner_content_hash": TWO_HASH}),
        "final_visual": make_available_asset().model_copy(
            update={"canonical_owner_content_hash": shot.content_hash}
        ),
    }
    if binding_kind in {"character", "scene"}:
        selected_assets = (assets["character"], assets["scene"])
    else:
        selected_assets = (assets[binding_kind],)
    stale_assets = tuple(
        asset.model_copy(update={"canonical_owner_content_hash": "9" * 64})
        if asset is assets[binding_kind]
        else asset
        for asset in selected_assets
    )
    request_values = {
        "target_shot": shot,
        "character_context": ((character,) if shot.character_ids else ()),
        "scene_context": scene,
        "previous_shot_state": (
            make_previous_state(
                is_same_action=True,
                has_terminal_frame_asset_id="terminal-shot-0",
            )
            if binding_kind == "previous_terminal"
            else None
        ),
        "shot_intent_evidence": make_intent_evidence(target_shot=shot),
        "review_decision": (
            make_review_decision(target_shot=shot)
            if binding_kind == "final_visual"
            else None
        ),
        "planning_contract_version": "video-planner/3",
        "generation_intent": _generation_intent(),
    }
    planned_request = make_request(
        **request_values,
        available_assets=selected_assets,
    )
    plan = VideoPlanner().plan(planned_request)
    current_request = make_request(
        **request_values,
        available_assets=stale_assets,
    )
    current_plan = VideoPlanner().plan(current_request)
    current_result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id=f"readiness-current-stale-{binding_kind}",
            current_request=current_request,
            plan=current_plan,
        )
    )
    assert current_result.status.value == "blocked"

    result = api.ShotReadinessGate().evaluate(
        api.ShotReadinessRequest.create(
            request_id=f"readiness-stale-{binding_kind}",
            current_request=current_request,
            plan=plan,
        )
    )

    assert result.status.value == "blocked"
    assert result.checks[2].status.value == "blocked"
    assert "required_asset_missing" in {
        reason.value for reason in result.checks[2].reason_codes
    }


@pytest.mark.parametrize("forged_field", ["current_request", "plan"])
def test_low_level_forged_nested_input_stops_with_typed_error(
    forged_field: str,
) -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    sealed = api.ShotReadinessRequest.create(
        request_id="readiness-forged-nested",
        current_request=current_request,
        plan=VideoPlanner().plan(current_request),
    )

    with pytest.raises(AiVideoError) as exc:
        api.ShotReadinessGate().evaluate(
            sealed.model_copy(update={forged_field: {}})
        )

    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED
    assert exc.value.retryable is False


def test_blocked_result_cannot_be_forged_into_ready_projection() -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    request = api.ShotReadinessRequest.create(
        request_id="readiness-forged-result",
        current_request=current_request,
        plan=plan,
    )
    valid = api.ShotReadinessGate().evaluate(request)
    blocked_check = valid.checks[0].model_copy(
        update={
            "status": api.ReadinessCheckStatus.BLOCKED,
            "reason_codes": (
                api.ReadinessReason.READINESS_REQUEST_SEAL_INVALID,
            ),
        }
    )

    with pytest.raises(ValidationError):
        api.ShotReadinessResult.create(
            status=api.ReadinessStatus.READY,
            checks=(blocked_check, *valid.checks[1:]),
            verified_generation_requirement=valid.verified_generation_requirement,
        )
    with pytest.raises(ValidationError):
        api.ShotReadinessResult.create(
            status=api.ReadinessStatus.READY,
            checks=tuple(reversed(valid.checks)),
            verified_generation_requirement=valid.verified_generation_requirement,
        )


def test_readiness_result_hash_is_deterministic_for_exact_semantics() -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    request = api.ShotReadinessRequest.create(
        request_id="readiness-deterministic-result",
        current_request=current_request,
        plan=plan,
    )

    first = api.ShotReadinessGate().evaluate(request)
    second = api.ShotReadinessGate().evaluate(request)

    assert first == second
    assert first.result_hash == second.result_hash


def test_result_hash_and_projection_seal_tampering_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _gate_api()
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    readiness_request = api.ShotReadinessRequest.create(
        request_id="readiness-tampered-projection",
        current_request=current_request,
        plan=plan,
    )
    valid = api.ShotReadinessGate().evaluate(readiness_request)
    with pytest.raises(AiVideoError) as result_exc:
        api.require_ready(valid.model_copy(update={"result_hash": TWO_HASH}))
    assert result_exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED

    projection = valid.verified_generation_requirement
    assert projection is not None
    gate_module = importlib.import_module(
        "ai_video.quality_gates.shot_readiness_gate"
    )
    monkeypatch.setattr(
        gate_module,
        "_verify_current_generation_requirement_projection",
        lambda **_: projection.model_copy(update={"projection_hash": TWO_HASH}),
    )
    result = api.ShotReadinessGate().evaluate(readiness_request)
    assert result.status.value == "blocked"
    assert "verified_projection_binding_invalid" in {
        reason.value for reason in result.checks[0].reason_codes
    }


def test_compatibility_handoff_receives_projection_without_plan_hint() -> None:
    current_request = _current_dynamic_request()
    plan = VideoPlanner().plan(current_request)
    handoff = Mock(return_value="eligible")

    from ai_video.planning import prepare_shot_for_existing_production

    result = prepare_shot_for_existing_production(
        current_request=current_request,
        plan=plan,
        production_handoff=handoff,
    )

    assert result == "eligible"
    assert handoff.call_count == 1
    assert set(handoff.call_args.kwargs) == {
        "current_shot",
        "generation_requirement",
    }
    assert isinstance(
        handoff.call_args.kwargs["generation_requirement"],
        VerifiedGenerationRequirementProjection,
    )


def test_continuity_handoff_preserves_exact_transition_policy() -> None:
    current_request = _current_v4_causal_request()
    plan = VideoPlanner().plan(current_request)
    requirement = plan.generation_requirement
    assert requirement is not None
    policy = _complete_causal_policy(
        requirement.generation_intent_hash,
        requirement.target_shot,
    )
    handoff = Mock(return_value="eligible")

    from ai_video.planning import prepare_shot_for_existing_production

    result = prepare_shot_for_existing_production(
        current_request=current_request,
        plan=plan,
        production_handoff=handoff,
        continuity_transition_policy=policy,
    )

    assert result == "eligible"
    assert handoff.call_count == 1
    assert handoff.call_args.kwargs["continuity_transition_policy"] == policy
    assert isinstance(
        handoff.call_args.kwargs["generation_requirement"],
        VerifiedGenerationRequirementProjection,
    )


def test_readiness_import_and_single_owner_boundaries() -> None:
    quality_root = Path("src/ai_video/quality_gates")
    forbidden_prefixes = (
        "ai_video.production.shot_router",
        "ai_video.production.video_generation",
        "ai_video.production.state_commit",
        "ai_video.production.registry",
        "ai_video.production.dependency",
        "ai_video.production.composition",
        "ai_video.production.hyperframes",
        "ai_video.production.review",
        "ai_video.production.video",
        "ai_video.cli",
        "ai_video.comfy_client",
        "ai_video.ffmpeg_tools",
        "os",
        "subprocess",
        "httpx",
        "requests",
        "keyring",
    )
    for path in quality_root.glob("*.py"):
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
                ), f"{path}:{node.lineno} forbidden readiness import {module}"

    production_sources = tuple(Path("src/ai_video/production").glob("*.py"))
    assert all(
        "ai_video.quality_gates" not in path.read_text(encoding="utf-8")
        for path in production_sources
    )
    planning_source = Path(
        "src/ai_video/planning/video_planner.py"
    ).read_text(encoding="utf-8")
    assert "plan_hint" not in planning_source
    assert planning_source.count(
        "def _verify_current_generation_requirement_projection("
    ) == 1
    integration_examples = tuple(Path("docs").rglob("*.md"))
    assert all(
        "plan_hint=" not in path.read_text(encoding="utf-8")
        for path in integration_examples
    )
