"""Public planning entrypoints over the shared generation preflight."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_video.production.video_transition import ContinuityTransitionPolicy
from ai_video.production.generation_preflight.models import (
    AssetRole, CapabilityRequirements, ContinuityMode, CurrentPlanProjectionFailure,
    GenerationMode, MotionRequirement, PlanOutcome, PlanWarning, PreviousShotState,
    ReasonCode, RequiredAssetRole, VideoGenerationPlan, VideoPlanningRequest,
)
from ai_video.production.generation_preflight.planner import (
    VideoPlanner, _verify_current_generation_requirement_projection,
)
from ai_video.production.generation_preflight.projection import (
    verify_current_generation_requirement_projection,
)
from ai_video.production.generation_preflight.readiness import require_current_video_plan

__all__ = [
    "AssetRole", "CapabilityRequirements", "ContinuityMode", "CurrentPlanProjectionFailure",
    "GenerationMode", "MotionRequirement", "PlanOutcome", "PlanWarning", "PreviousShotState",
    "ReasonCode", "RequiredAssetRole", "VideoGenerationPlan", "VideoPlanner", "VideoPlanningRequest",
    "prepare_shot_for_existing_production", "require_current_video_plan",
    "verify_current_generation_requirement_projection",
]


def prepare_shot_for_existing_production(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
    production_handoff: Callable[..., Any],
    continuity_transition_policy: ContinuityTransitionPolicy | None = None,
) -> Any:
    projection = require_current_video_plan(
        current_request=current_request,
        plan=plan,
        continuity_transition_policy=continuity_transition_policy,
    )
    continuity_transition_policy = continuity_transition_policy or current_request.continuity_transition_policy
    handoff: dict[str, object] = {
        "current_shot": current_request.target_shot,
        "generation_requirement": projection,
    }
    if continuity_transition_policy is not None:
        handoff["continuity_transition_policy"] = (
            ContinuityTransitionPolicy.model_validate(
                continuity_transition_policy.model_dump(mode="python")
            )
        )
    return production_handoff(
        **handoff,
    )
