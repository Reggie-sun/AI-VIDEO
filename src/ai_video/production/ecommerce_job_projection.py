"""Pure Ecommerce Job next-action and blocker projections."""

from ai_video.errors import ErrorCode
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobBlocker,
    EcommerceJobNextAction,
    EcommerceProductionJobProjection,
    EcommerceProductionJobRequest,
)
from ai_video.production.ecommerce_job_review import EcommerceFinalReviewFrontier


def project_ecommerce_job(
    request: EcommerceProductionJobRequest,
    *,
    next_action: EcommerceJobNextAction,
    manifest_revision: int | None = None,
    next_shot_id: str | None = None,
    blocker: EcommerceJobBlocker | None = None,
) -> EcommerceProductionJobProjection:
    return EcommerceProductionJobProjection(
        schema_version="ecommerce-production-job-projection/1",
        job_id=request.job_id,
        handoff_id=request.handoff_id,
        expected_project_id=request.expected_project_id,
        next_action=next_action,
        manifest_revision=manifest_revision,
        next_shot_id=next_shot_id,
        blocker=blocker,
    )


def block_ecommerce_job(
    request: EcommerceProductionJobRequest,
    *,
    blocker_code: str,
    stage: str,
    subject_id: str,
    failure_classification: str,
    required_action: str,
    error_code: ErrorCode = ErrorCode.PRODUCTION_STATE_INVALID,
    manifest_revision: int | None = None,
    evidence_pointers: tuple[str, ...] = (),
    outcome_known: bool = True,
) -> EcommerceProductionJobProjection:
    return project_ecommerce_job(
        request,
        next_action=EcommerceJobNextAction.BLOCKED,
        manifest_revision=manifest_revision,
        blocker=EcommerceJobBlocker(
            blocker_code=blocker_code,
            error_code=error_code,
            stage=stage,
            subject_id=subject_id,
            failure_classification=failure_classification,
            diagnosis_id=None,
            evidence_pointers=evidence_pointers,
            retryable=False,
            required_owner="EcommerceProductionJobService",
            required_action=required_action,
            outcome_known=outcome_known,
        ),
    )


def project_ecommerce_review_frontier(
    request: EcommerceProductionJobRequest,
    *,
    frontier: EcommerceFinalReviewFrontier,
    manifest_revision: int,
) -> EcommerceProductionJobProjection:
    actions = {
        EcommerceFinalReviewFrontier.PACKAGE_DELIVERY: (
            EcommerceJobNextAction.PACKAGE_DELIVERY
        ),
        EcommerceFinalReviewFrontier.PREPARE_COMPOSITION: (
            EcommerceJobNextAction.PREPARE_COMPOSITION
        ),
        EcommerceFinalReviewFrontier.REVIEW_FINAL: EcommerceJobNextAction.REVIEW_FINAL,
    }
    action = actions.get(frontier)
    if action is not None:
        return project_ecommerce_job(
            request,
            next_action=action,
            manifest_revision=manifest_revision,
        )
    return block_ecommerce_job(
        request,
        blocker_code="ECOMMERCE_FINAL_REPAIR_DIAGNOSIS_REQUIRED",
        stage="final_review",
        subject_id=request.job_id,
        failure_classification="WHOLE_VIDEO_FAILURE",
        required_action=(
            "Diagnose the exact failed final requirement and select its smallest "
            "canonical repair frontier."
        ),
        manifest_revision=manifest_revision,
    )


__all__ = [
    "block_ecommerce_job",
    "project_ecommerce_job",
    "project_ecommerce_review_frontier",
]
