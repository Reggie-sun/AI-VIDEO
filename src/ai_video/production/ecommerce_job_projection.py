"""Read-only Ecommerce Job next-action and blocker projections."""

from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ecommerce_job_assembly import (
    EcommerceCompositionExecutionPlan,
    inspect_ecommerce_job_assembly,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobBlocker,
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
    EcommerceProductionJobProjection,
    EcommerceProductionJobRequest,
)
from ai_video.production.ecommerce_job_execution import EcommerceShotExecutionPlan
from ai_video.production.ecommerce_job_repair import (
    bound_generation_attempt_ids,
    bound_generation_attempt_ids_for_shot,
    canonical_repair_frontier,
)
from ai_video.production.ecommerce_job_review import (
    EcommerceDeliveryExecutionPlan,
    EcommerceFinalReviewFrontier,
    EcommercePostMediaExecutionPlan,
    inspect_ecommerce_review_frontier,
)
from ai_video.production.models import LoadedProductionProject, ReviewLifecycle


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
            "Diagnose the exact failed final requirement. Plan-bound CTA or other "
            "commercial graphic changes require a new authoring handoff and immutable "
            "Project revision before re-rendering."
        ),
        manifest_revision=manifest_revision,
    )


def project_ecommerce_job_progress(
    request: EcommerceProductionJobRequest,
    handoff: EcommerceProductionHandoff,
    *,
    loaded: LoadedProductionProject,
    shot_execution: EcommerceShotExecutionPlan | None = None,
    composition_execution: EcommerceCompositionExecutionPlan | None = None,
    review_execution: EcommercePostMediaExecutionPlan | None = None,
    delivery_execution: EcommerceDeliveryExecutionPlan | None = None,
) -> EcommerceProductionJobProjection:
    """Project read-only Shot, composition, review, and delivery frontiers."""

    revision = loaded.manifest.manifest_revision
    if shot_execution is not None:
        try:
            shot_execution.validate(
                handoff,
                project_root=request.project_root,
            )
            repair = canonical_repair_frontier(
                request.project_root,
                shot_execution,
                loaded.manifest,
            )
        except (AiVideoError, OSError, TypeError, ValueError):
            return block_ecommerce_job(
                request,
                blocker_code="ECOMMERCE_SHOT_EXECUTION_INVALID",
                stage="shot_execution",
                subject_id=request.job_id,
                failure_classification="EXECUTION_INPUT_INVALID",
                required_action="Repair the exact Shot execution inputs through their owner.",
                manifest_revision=revision,
            )
        if repair is not None:
            action, shot_id = repair
            if action is EcommerceJobNextAction.REPAIR_SHOT_MEDIA:
                try:
                    shot_attempts = bound_generation_attempt_ids_for_shot(
                        request.project_root, shot_execution, shot_id=shot_id
                    )
                    job_attempts = bound_generation_attempt_ids(
                        request.project_root, shot_execution
                    )
                    if not shot_attempts:
                        raise ValueError("Failed Shot has no bound generation attempt")
                except (AiVideoError, OSError, TypeError, ValueError):
                    return block_ecommerce_job(
                        request,
                        blocker_code="ECOMMERCE_SHOT_EXECUTION_INVALID",
                        stage="shot_repair",
                        subject_id=shot_id,
                        failure_classification="EXECUTION_INPUT_INVALID",
                        required_action="Reopen the exact failed Shot attempt.",
                        manifest_revision=revision,
                    )
                if len(job_attempts) >= request.max_new_generation_attempts:
                    return block_ecommerce_job(
                        request,
                        blocker_code="ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED",
                        stage="shot_repair",
                        subject_id=shot_id,
                        failure_classification="ATTEMPT_CEILING",
                        required_action="Stop or authorize a new finite Job request.",
                        manifest_revision=revision,
                    )
                if len(shot_attempts) - 1 >= request.max_repairs_per_shot:
                    return block_ecommerce_job(
                        request,
                        blocker_code="ECOMMERCE_SHOT_REPAIR_CEILING_EXHAUSTED",
                        stage="shot_repair",
                        subject_id=shot_id,
                        failure_classification="ATTEMPT_CEILING",
                        required_action="Stop or authorize a new finite Shot repair request.",
                        manifest_revision=revision,
                    )
            return project_ecommerce_job(
                request,
                next_action=action,
                manifest_revision=revision,
                next_shot_id=shot_id,
            )

    for shot in loaded.shots:
        if any(not role.asset_ids for role in shot.required_asset_roles):
            if shot_execution is not None:
                try:
                    bound_attempts = bound_generation_attempt_ids(
                        request.project_root, shot_execution
                    )
                except (AiVideoError, OSError, TypeError, ValueError):
                    return block_ecommerce_job(
                        request,
                        blocker_code="ECOMMERCE_SHOT_EXECUTION_INVALID",
                        stage="shot_execution",
                        subject_id=shot.shot_id,
                        failure_classification="EXECUTION_INPUT_INVALID",
                        required_action="Reopen the exact Shot execution inputs.",
                        manifest_revision=revision,
                    )
            else:
                bound_attempts = ()
            if len(bound_attempts) >= request.max_new_generation_attempts:
                return block_ecommerce_job(
                    request,
                    blocker_code="ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED",
                    stage="shot_execution",
                    subject_id=shot.shot_id,
                    failure_classification="ATTEMPT_CEILING",
                    required_action="Stop or authorize a new finite Job request.",
                    manifest_revision=revision,
                )
            return project_ecommerce_job(
                request,
                next_action=EcommerceJobNextAction.GENERATE_SHOT,
                manifest_revision=revision,
                next_shot_id=shot.shot_id,
            )

    assembly = inspect_ecommerce_job_assembly(
        composition_execution,
        handoff,
        project_root=request.project_root,
    )
    if assembly.error is not None:
        return block_ecommerce_job(
            request,
            blocker_code="ECOMMERCE_COMPOSITION_EXECUTION_INVALID",
            stage="composition",
            subject_id=request.job_id,
            failure_classification="EXECUTION_INPUT_INVALID",
            required_action="Repair the exact composition inputs through their owner.",
            error_code=(
                assembly.error.code
                if isinstance(assembly.error, AiVideoError)
                else ErrorCode.PRODUCTION_STATE_INVALID
            ),
            manifest_revision=revision,
        )
    if assembly.next_action is not EcommerceJobNextAction.REVIEW_FINAL:
        return project_ecommerce_job(
            request,
            next_action=assembly.next_action,
            manifest_revision=revision,
        )
    acceptance = loaded.manifest.final_acceptance_state
    if (
        acceptance is None
        or acceptance.lifecycle is not ReviewLifecycle.FRESH
        or acceptance.active_receipt is None
    ):
        if review_execution is not None:
            try:
                frontier = review_execution.inspect_frontier(
                    handoff,
                    project_root=request.project_root,
                )
            except (AiVideoError, OSError, TypeError, ValueError) as exc:
                return block_ecommerce_job(
                    request,
                    blocker_code="ECOMMERCE_FINAL_REVIEW_BINDING_INVALID",
                    stage="final_review",
                    subject_id=request.job_id,
                    failure_classification="EXECUTION_INPUT_INVALID",
                    required_action=(
                        "Repair the exact review policy, evidence, or handoff binding."
                    ),
                    error_code=(
                        exc.code
                        if isinstance(exc, AiVideoError)
                        else ErrorCode.REVIEW_EVIDENCE_INVALID
                    ),
                    manifest_revision=revision,
                )
            return project_ecommerce_review_frontier(
                request,
                frontier=frontier,
                manifest_revision=revision,
            )
        return project_ecommerce_review_frontier(
            request,
            frontier=inspect_ecommerce_review_frontier(request.project_root),
            manifest_revision=revision,
        )
    if delivery_execution is not None:
        try:
            packaged = delivery_execution.inspect(
                handoff,
                project_root=request.project_root,
                job_id=request.job_id,
            )
        except (AiVideoError, OSError, TypeError, ValueError) as exc:
            return block_ecommerce_job(
                request,
                blocker_code="ECOMMERCE_DELIVERY_BUNDLE_INVALID",
                stage="delivery",
                subject_id=request.job_id,
                failure_classification="DELIVERY_INTEGRITY",
                required_action="Repair or remove the invalid delivery bundle.",
                error_code=(
                    exc.code
                    if isinstance(exc, AiVideoError)
                    else ErrorCode.PRODUCTION_STATE_INVALID
                ),
                manifest_revision=revision,
            )
        if packaged is not None:
            return project_ecommerce_job(
                request,
                next_action=EcommerceJobNextAction.COMPLETE,
                manifest_revision=revision,
            )
    return project_ecommerce_job(
        request,
        next_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        manifest_revision=revision,
    )


__all__ = [
    "block_ecommerce_job",
    "project_ecommerce_job",
    "project_ecommerce_job_progress",
    "project_ecommerce_review_frontier",
]
