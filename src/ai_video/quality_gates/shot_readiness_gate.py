"""Compatibility imports for the shared generation preflight implementation."""

from ai_video.production.generation_preflight.readiness import (
    ShotReadinessGate,
    require_ready,
)
from ai_video.production.generation_preflight.readiness_models import (
    PlanEligibilityOutcome,
    PlanEligibilityPayload,
    ReadinessCheckStatus,
    ReadinessReason,
    ReadinessStatus,
    RequestPlanBindingOutcome,
    RequestPlanBindingPayload,
    RequiredAssetReadinessOutcome,
    RequiredAssetReadinessPayload,
    ShotReadinessRequest,
    ShotReadinessResult,
)

__all__ = [
    "PlanEligibilityOutcome",
    "PlanEligibilityPayload",
    "ReadinessCheckStatus",
    "ReadinessReason",
    "ReadinessStatus",
    "RequestPlanBindingOutcome",
    "RequestPlanBindingPayload",
    "RequiredAssetReadinessOutcome",
    "RequiredAssetReadinessPayload",
    "ShotReadinessGate",
    "ShotReadinessRequest",
    "ShotReadinessResult",
    "require_ready",
]
