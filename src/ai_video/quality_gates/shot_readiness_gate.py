from __future__ import annotations

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning._asset_readiness import required_role_readiness
from ai_video.planning._planner_models import (
    CurrentPlanProjectionFailure,
    CurrentPlanProjectionFailureReason,
    PlanOutcome,
    PlanWarning,
    VideoGenerationPlan,
    VideoPlanningRequest,
)
from ai_video.planning.video_planner import (
    _verify_current_generation_requirement_projection,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import (
    VerifiedGenerationRequirementProjection,
)
from ai_video.quality_gates._readiness_models import (
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


class ShotReadinessGate:
    def evaluate(self, request: ShotReadinessRequest) -> ShotReadinessResult:
        try:
            if (
                not isinstance(request, ShotReadinessRequest)
                or not isinstance(request.current_request, VideoPlanningRequest)
                or not isinstance(request.plan, VideoGenerationPlan)
            ):
                raise TypeError("readiness request envelope is not typed")
            return self._evaluate_typed(request)
        except AiVideoError:
            raise
        except (
            AssertionError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise AiVideoError(
                code=ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
                user_message=(
                    "Video planning preflight blocked downstream execution."
                ),
                technical_detail="invalid shot readiness request envelope",
                retryable=False,
                cause=exc,
            ) from None

    def _evaluate_typed(
        self,
        request: ShotReadinessRequest,
    ) -> ShotReadinessResult:
        outer_request_seal_valid = (
            request.request_content_hash
            == canonical_sha256(request._hash_payload())
        )
        verification = _verify_current_generation_requirement_projection(
            current_request=request.current_request,
            plan=request.plan,
        )
        failure = (
            verification
            if isinstance(verification, CurrentPlanProjectionFailure)
            else None
        )
        projection = (
            verification
            if isinstance(
                verification,
                VerifiedGenerationRequirementProjection,
            )
            else None
        )
        failure_reasons = set(failure.reason_codes if failure else ())
        current_v3_contract = (
            CurrentPlanProjectionFailureReason.LEGACY_CONTRACT
            not in failure_reasons
        )
        requirement = request.plan.generation_requirement
        projection_seal_valid = False
        if projection is not None:
            try:
                VerifiedGenerationRequirementProjection.model_validate(
                    projection.model_dump(mode="python")
                )
            except ValidationError:
                pass
            else:
                projection_seal_valid = True
        projection_valid = bool(
            projection_seal_valid
            and projection is not None
            and requirement is not None
            and projection.plan_hash == request.plan.plan_hash
            and projection.requirement == requirement
            and projection.verified_source_request_content_hash
            == request.current_request.request_content_hash
            and projection.target_shot_id
            == request.current_request.target_shot.shot_id
            and projection.target_shot_revision
            == request.current_request.target_shot.revision
            and projection.target_shot_content_hash
            == request.current_request.target_shot.content_hash
        )

        binding_reasons: list[ReadinessReason] = []
        if not outer_request_seal_valid:
            binding_reasons.append(
                ReadinessReason.READINESS_REQUEST_SEAL_INVALID
            )
        if CurrentPlanProjectionFailureReason.LEGACY_CONTRACT in failure_reasons:
            binding_reasons.append(ReadinessReason.LEGACY_PLANNER_REOPEN_ONLY)
        elif failure is not None:
            binding_reasons.append(
                ReadinessReason.CURRENT_PLAN_PROJECTION_INVALID
            )
        if projection is not None and not projection_valid:
            binding_reasons.append(
                ReadinessReason.VERIFIED_PROJECTION_BINDING_INVALID
            )
        binding_status = (
            ReadinessCheckStatus.BLOCKED
            if binding_reasons
            else ReadinessCheckStatus.PASS
        )
        binding = RequestPlanBindingOutcome(
            status=binding_status,
            reason_codes=tuple(binding_reasons),
            payload=RequestPlanBindingPayload(
                outer_request_seal_valid=outer_request_seal_valid,
                current_v3_contract=current_v3_contract,
                request_seal_valid=(
                    current_v3_contract
                    and CurrentPlanProjectionFailureReason.REQUEST_SEAL_INVALID
                    not in failure_reasons
                ),
                plan_seal_valid=(
                    current_v3_contract
                    and CurrentPlanProjectionFailureReason.PLAN_SEAL_INVALID
                    not in failure_reasons
                ),
                unique_current_derivation_valid=(
                    current_v3_contract
                    and CurrentPlanProjectionFailureReason.PLAN_NOT_UNIQUE_CURRENT_DERIVATION
                    not in failure_reasons
                ),
                plan_id_valid=(
                    current_v3_contract
                    and CurrentPlanProjectionFailureReason.PLAN_ID_INVALID
                    not in failure_reasons
                ),
                source_request_valid=(
                    current_v3_contract
                    and CurrentPlanProjectionFailureReason.SOURCE_REQUEST_STALE
                    not in failure_reasons
                ),
                target_shot_valid=(
                    current_v3_contract
                    and CurrentPlanProjectionFailureReason.TARGET_SHOT_STALE
                    not in failure_reasons
                ),
                embedded_requirement_valid=(
                    current_v3_contract
                    and not bool(
                        {
                            CurrentPlanProjectionFailureReason.EMBEDDED_REQUIREMENT_MISSING,
                            CurrentPlanProjectionFailureReason.EMBEDDED_REQUIREMENT_STALE,
                        }
                        & failure_reasons
                    )
                ),
                verified_projection_valid=projection_valid,
                request_content_hash=request.current_request.request_content_hash,
                plan_hash=request.plan.plan_hash,
                requirement_hash=(
                    requirement.requirement_hash
                    if requirement is not None
                    else None
                ),
                projection_hash=(
                    projection.projection_hash
                    if projection_valid and projection is not None
                    else None
                ),
                failure_field_paths=(
                    failure.field_paths if failure is not None else ()
                ),
            ),
        )

        eligibility_reasons: list[ReadinessReason] = []
        if request.plan.outcome is PlanOutcome.BLOCKED:
            eligibility_reasons.append(ReadinessReason.PLAN_BLOCKED)
        unresolved_human_review = (
            PlanWarning.REQUIRES_HUMAN_REVIEW in request.plan.warnings
        )
        if unresolved_human_review:
            eligibility_reasons.append(
                ReadinessReason.HUMAN_REVIEW_UNRESOLVED
            )
        eligibility = PlanEligibilityOutcome(
            status=(
                ReadinessCheckStatus.BLOCKED
                if eligibility_reasons
                else ReadinessCheckStatus.PASS
            ),
            reason_codes=tuple(eligibility_reasons),
            payload=PlanEligibilityPayload(
                plan_outcome=request.plan.outcome,
                warnings=request.plan.warnings,
                unresolved_human_review=unresolved_human_review,
            ),
        )

        required_roles = request.plan.required_asset_roles
        ready_roles, missing_roles = required_role_readiness(
            request.current_request,
            required_roles,
        )
        asset_reasons = (
            (ReadinessReason.REQUIRED_ASSET_MISSING,)
            if missing_roles
            else ()
        )
        assets = RequiredAssetReadinessOutcome(
            status=(
                ReadinessCheckStatus.BLOCKED
                if missing_roles
                else ReadinessCheckStatus.PASS
            ),
            reason_codes=asset_reasons,
            payload=RequiredAssetReadinessPayload(
                required_roles=tuple(item.role for item in required_roles),
                ready_roles=ready_roles,
                missing_roles=missing_roles,
            ),
        )

        checks = (binding, eligibility, assets)
        ready = all(
            check.status is ReadinessCheckStatus.PASS for check in checks
        )
        return ShotReadinessResult.create(
            status=ReadinessStatus.READY if ready else ReadinessStatus.BLOCKED,
            checks=checks,
            verified_generation_requirement=(projection if ready else None),
        )


def require_ready(
    result: ShotReadinessResult,
) -> VerifiedGenerationRequirementProjection:
    try:
        validated = ShotReadinessResult.model_validate(
            result.model_dump(mode="python")
        )
    except ValidationError as exc:
        raise AiVideoError(
            code=ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
            user_message="Video planning preflight blocked downstream execution.",
            technical_detail="invalid shot readiness result",
            retryable=False,
            cause=exc,
        ) from None
    if (
        validated.status is not ReadinessStatus.READY
        or validated.verified_generation_requirement is None
    ):
        reasons = tuple(
            reason.value
            for check in validated.checks
            for reason in check.reason_codes
        )
        raise AiVideoError(
            code=ErrorCode.PLANNING_PREFLIGHT_BLOCKED,
            user_message="Video planning preflight blocked downstream execution.",
            technical_detail=", ".join(reasons),
            retryable=False,
        )
    return validated.verified_generation_requirement
