"""Bounded routing for Ecommerce Shot evidence and media repair."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_video.errors import AiVideoError
from ai_video.production.ecommerce_job_contracts import EcommerceJobNextAction
from ai_video.production.generation_diagnosis import Diagnosis, Intervention
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetType,
    CommercialShotEvaluationPhase,
    QaVerdict,
    StateCommitStatus,
    VideoAttemptPhase,
    VisualStrategy,
)
from ai_video.production.project import load_production_project


@dataclass(frozen=True)
class EcommerceAttemptIdentity:
    attempt_id: str
    routing_binding_hash: str
    permit_id: str
    resolved_generation_hash: str


@dataclass(frozen=True)
class EcommerceShotRepairContext:
    shot_id: str
    verdict: QaVerdict | None
    outcome_known: bool
    diagnosis: Diagnosis
    intervention: Intervention | None
    prior_attempt: EcommerceAttemptIdentity
    proposed_attempt: EcommerceAttemptIdentity | None
    existing_job_attempts: int
    existing_shot_repairs: int
    request_delta_verified: bool = False


@dataclass(frozen=True)
class EcommerceShotRepairDecision:
    next_action: EcommerceJobNextAction
    media_submit_allowed: bool
    changed_variables: tuple[str, ...] = ()
    blocker_code: str | None = None


def plan_ecommerce_shot_repair(
    context: EcommerceShotRepairContext,
    *,
    max_new_generation_attempts: int,
    max_repairs_per_shot: int,
) -> EcommerceShotRepairDecision:
    if not context.outcome_known or "UNKNOWN_OUTCOME" in context.diagnosis.failure_classes:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME,
            media_submit_allowed=False,
        )

    if context.verdict is QaVerdict.NOT_EVALUATED:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
            media_submit_allowed=False,
        )

    if context.verdict is not QaVerdict.FAIL:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_OUTCOME_INVALID",
        )
    if (
        "QUALITY_FAILURE" not in context.diagnosis.failure_classes
        or context.intervention is None
        or context.proposed_attempt is None
    ):
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_DIAGNOSIS_INCOMPLETE",
        )
    if context.intervention.disposition in {"CAPABILITY_BOUNDARY", "SPLIT_SHOT"}:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_AUTHORING_REQUIRED",
        )
    if context.existing_shot_repairs >= max_repairs_per_shot:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_CEILING_EXHAUSTED",
        )
    if context.existing_job_attempts >= max_new_generation_attempts:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED",
        )

    intervention = context.intervention
    prior = context.prior_attempt
    proposed = context.proposed_attempt
    common_reused = (
        prior.attempt_id == proposed.attempt_id
        or prior.permit_id == proposed.permit_id
        or prior.resolved_generation_hash == proposed.resolved_generation_hash
    )
    provider_switch = intervention.disposition == "CHANGE_PROVIDER_MODEL"
    if provider_switch and (
        common_reused
        or prior.routing_binding_hash == proposed.routing_binding_hash
    ):
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_PROVIDER_SWITCH_IDENTITY_REUSED",
        )
    if not provider_switch and common_reused:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_IDENTITY_REUSED",
        )
    if not provider_switch and len(intervention.changed_variables) != 1:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_DELTA_INVALID",
        )
    if not context.request_delta_verified:
        return EcommerceShotRepairDecision(
            next_action=EcommerceJobNextAction.BLOCKED,
            media_submit_allowed=False,
            blocker_code="ECOMMERCE_SHOT_REPAIR_DELTA_INVALID",
        )

    return EcommerceShotRepairDecision(
        next_action=EcommerceJobNextAction.REPAIR_SHOT_MEDIA,
        media_submit_allowed=True,
        changed_variables=intervention.changed_variables,
    )


def attempt_requires_explicit_recovery(attempt: Any) -> bool:
    """Project durable uncertain boundaries without mutating canonical state."""

    state = getattr(attempt, "video_generation_state", None)
    return attempt.status is StateCommitStatus.OUTCOME_UNKNOWN or (
        attempt.status is StateCommitStatus.RUNNING
        and state is not None
        and getattr(state, "phase", None) is VideoAttemptPhase.SUBMIT_INTENT
    )


def bound_generation_attempt_ids(root: Path, execution: Any) -> tuple[str, ...]:
    from ai_video.production._video_project_reader import load_video_request_receipt

    expected = {
        (
            execution.handoff.plan_content_hash,
            item.projection_hash,
            item.target_shot_id,
        )
        for item in execution.handoff.commercial_execution_projections
        if item.invoke_video_provider
    }
    expected_shot_ids = {
        item.target_shot_id
        for item in execution.handoff.commercial_execution_projections
        if item.invoke_video_provider
    }
    loaded = load_production_project(root / "project.yaml")
    matched: list[str] = []
    for attempt in loaded.manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        resolved = load_video_request_receipt(root, state.request)
        binding = resolved.commercial_binding
        if binding is None or binding.target_shot_id not in expected_shot_ids:
            continue
        identity = (
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
        )
        if identity not in expected:
            raise ValueError(
                "Existing Ecommerce Shot attempt belongs to another selected plan"
            )
        matched.append(attempt.attempt_id)
    return tuple(matched)


def bound_generation_attempt_ids_for_shot(
    root: Path,
    execution: Any,
    *,
    shot_id: str | None,
) -> tuple[str, ...]:
    if shot_id is None:
        return ()
    from ai_video.production._video_project_reader import load_video_request_receipt

    projection = next(
        (
            item
            for item in execution.handoff.commercial_execution_projections
            if item.target_shot_id == shot_id and item.invoke_video_provider
        ),
        None,
    )
    if projection is None:
        return ()
    loaded = load_production_project(root / "project.yaml")
    matched: list[str] = []
    for attempt in loaded.manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        resolved = load_video_request_receipt(root, state.request)
        binding = resolved.commercial_binding
        if binding is not None and (
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
        ) == (
            execution.handoff.plan_content_hash,
            projection.projection_hash,
            shot_id,
        ):
            matched.append(attempt.attempt_id)
    return tuple(matched)


def ecommerce_manifest_revision(root: Path, fallback: int | None) -> int | None:
    try:
        return load_production_project(root / "project.yaml").manifest.manifest_revision
    except (AiVideoError, OSError, ValueError):
        return fallback


def ecommerce_attempt_status(
    root: Path,
    execution: Any,
    *,
    shot_id: str,
) -> StateCommitStatus | None:
    attempt_id = next(
        item.attempt_id for item in execution.shots if item.shot_id == shot_id
    )
    try:
        manifest = load_production_project(root / "project.yaml").manifest
    except (AiVideoError, OSError, ValueError):
        return None
    attempt = next(
        (item for item in manifest.attempts if item.attempt_id == attempt_id),
        None,
    )
    return None if attempt is None else attempt.status


def input_attempt_identity(item: Any) -> EcommerceAttemptIdentity:
    binding = item.request.commercial_binding
    routing_hash = getattr(item.execution_binding, "binding_hash", None)
    if routing_hash is None:
        routing_hash = getattr(item.execution_binding, "content_hash", None)
    if routing_hash is None:
        routing_hash = canonical_sha256(
            {
                "provider_kind": item.request.provider_kind,
                "model_id": item.request.model_id,
                "plan_hash": binding.ad_creative_plan_hash,
                "projection_hash": binding.commercial_execution_projection_hash,
                "shot_id": binding.target_shot_id,
            }
        )
    permit_id = (
        getattr(item.paid_preview, "preview_fingerprint", None)
        if item.lane == "paid"
        else None
    ) or f"local-attempt:{item.attempt_id}"
    return EcommerceAttemptIdentity(
        attempt_id=item.attempt_id,
        routing_binding_hash=routing_hash,
        permit_id=permit_id,
        resolved_generation_hash=item.request.resolved_generation_hash,
    )


def canonical_attempt_identity(
    root: Path,
    attempt_id: str,
) -> EcommerceAttemptIdentity:
    from ai_video.production._video_project_reader import load_video_request_receipt

    loaded = load_production_project(root / "project.yaml")
    attempt = next(
        item for item in loaded.manifest.attempts if item.attempt_id == attempt_id
    )
    state = attempt.video_generation_state
    if state is None:
        raise ValueError("Repair prior attempt is not video generation")
    resolved = load_video_request_receipt(root, state.request)
    binding = resolved.commercial_binding
    if binding is None:
        raise ValueError("Repair prior attempt has no commercial binding")
    routing_hash = (
        state.execution_binding.binding_hash
        if state.execution_binding is not None
        else canonical_sha256(
            {
                "provider_kind": resolved.provider_kind,
                "model_id": resolved.model_id,
                "plan_hash": binding.ad_creative_plan_hash,
                "projection_hash": binding.commercial_execution_projection_hash,
                "shot_id": binding.target_shot_id,
            }
        )
    )
    if state.local_submit_intent is not None:
        permit_id = state.local_submit_intent.intent_fingerprint
    elif attempt.paid_provider_state is not None:
        paid = attempt.paid_provider_state
        permit_id = canonical_sha256(
            {
                "gate": paid.gate_receipt.content_hash,
                "reservation_id": paid.reservation_id,
            }
        )
    else:
        permit_id = f"pre-submit:{attempt_id}"
    return EcommerceAttemptIdentity(
        attempt_id=attempt_id,
        routing_binding_hash=routing_hash,
        permit_id=permit_id,
        resolved_generation_hash=resolved.resolved_generation_hash,
    )


def repair_request_delta_is_verified(
    root: Path,
    *,
    prior_attempt_id: str,
    proposed_request: Any,
    intervention: Intervention,
) -> bool:
    from ai_video.production._video_project_reader import load_video_request_receipt
    from ai_video.production.generation_diagnosis import verify_intervention_comparison

    loaded = load_production_project(root / "project.yaml")
    prior_attempt = next(
        (
            item
            for item in loaded.manifest.attempts
            if item.attempt_id == prior_attempt_id
        ),
        None,
    )
    if prior_attempt is None:
        return False
    state = prior_attempt.video_generation_state
    if state is None:
        return False
    prior = load_video_request_receipt(root, state.request)
    before = None if prior.activation_scope is None else prior.activation_scope.request
    after = (
        None
        if getattr(proposed_request, "activation_scope", None) is None
        else proposed_request.activation_scope.request
    )
    if before is None or after is None:
        return False
    try:
        verify_intervention_comparison(intervention, before, after)
    except (TypeError, ValueError):
        return False
    return True


def canonical_attempt_verdict(root: Path, attempt: Any) -> QaVerdict | None:
    state = attempt.video_generation_state
    evaluation = None if state is None else state.commercial_evaluation
    if evaluation is None:
        return None
    if evaluation.evidence is None:
        return QaVerdict.NOT_EVALUATED
    from ai_video.production._video_project_reader import (
        load_generated_commercial_shot_evidence,
        load_video_request_receipt,
    )
    from ai_video.production.ecommerce_media_acceptance import (
        adjudicate_generated_commercial_shot_evidence,
    )

    resolved = load_video_request_receipt(root, state.request)
    binding = resolved.commercial_binding
    if binding is None:
        return QaVerdict.NOT_EVALUATED
    evidence = load_generated_commercial_shot_evidence(root, evaluation.evidence)
    return adjudicate_generated_commercial_shot_evidence(evidence, binding=binding)


def shot_gate_verdict(
    root: Path,
    execution: Any,
    facades: dict[str, Any],
    *,
    shot_id: str,
) -> QaVerdict | None:
    try:
        verdict = facades[shot_id].current_validation_verdict()
    except (AiVideoError, OSError, ValueError):
        verdict = None
    if verdict in {QaVerdict.FAIL, QaVerdict.NOT_EVALUATED}:
        return verdict
    attempt_id = next(
        item.attempt_id for item in execution.shots if item.shot_id == shot_id
    )
    try:
        loaded = load_production_project(root / "project.yaml")
        attempt = next(
            item for item in loaded.manifest.attempts
            if item.attempt_id == attempt_id
        )
        return canonical_attempt_verdict(root, attempt)
    except (AiVideoError, OSError, StopIteration, ValueError):
        return None


def canonical_repair_frontier(
    root: Path,
    execution: Any,
    manifest: Any,
) -> tuple[EcommerceJobNextAction, str] | None:
    from ai_video.production._video_project_reader import load_video_request_receipt

    expected = {
        item.target_shot_id: item.projection_hash
        for item in execution.handoff.commercial_execution_projections
        if item.invoke_video_provider
    }
    latest_by_shot: dict[str, Any] = {}
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        resolved = load_video_request_receipt(root, state.request)
        binding = resolved.commercial_binding
        if (
            binding is not None
            and binding.ad_creative_plan_hash == execution.handoff.plan_content_hash
            and expected.get(binding.target_shot_id)
            == binding.commercial_execution_projection_hash
        ):
            latest_by_shot[binding.target_shot_id] = attempt
    for proposal in execution.handoff.shot_proposals:
        attempt = latest_by_shot.get(proposal.shot_id)
        if attempt is None:
            continue
        if attempt_requires_explicit_recovery(attempt):
            return EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME, proposal.shot_id
        evaluation = attempt.video_generation_state.commercial_evaluation
        if (
            evaluation is not None
            and evaluation.phase is CommercialShotEvaluationPhase.INTENT
        ):
            return EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME, proposal.shot_id
        verdict = canonical_attempt_verdict(root, attempt)
        if verdict is QaVerdict.FAIL:
            return EcommerceJobNextAction.REPAIR_SHOT_MEDIA, proposal.shot_id
        if verdict is QaVerdict.NOT_EVALUATED:
            return EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE, proposal.shot_id
    return None


def shots_match_handoff(
    root: Path,
    *,
    expected_shots: tuple[Any, ...],
    active_shots: tuple[Any, ...],
    manifest: Any,
) -> bool:
    if len(expected_shots) != len(active_shots):
        return False
    from ai_video.production._video_project_reader import load_video_request_receipt

    activations: dict[str, list[tuple[Any, Any]]] = {}
    try:
        for attempt in manifest.attempts:
            state = attempt.video_generation_state
            if (
                attempt.status is not StateCommitStatus.SUCCEEDED
                or state is None
                or state.phase is not VideoAttemptPhase.ACTIVATE
            ):
                continue
            request = load_video_request_receipt(root, state.request)
            binding = request.commercial_binding
            if binding is None:
                continue
            activations.setdefault(binding.target_shot_id, []).append((request, state))
    except (AiVideoError, OSError, ValueError):
        return False
    for expected, active in zip(expected_shots, active_shots, strict=True):
        if (
            active.artifact_id,
            active.revision,
            active.content_hash,
        ) == (
            expected.artifact_id,
            expected.revision,
            expected.content_hash,
        ):
            continue
        if (
            active.artifact_id != expected.artifact_id
            or active.shot_id != expected.shot_id
            or active.revision <= expected.revision
        ):
            return False
        if not any(
            _is_canonical_activated_shot_descendant(
                expected,
                active,
                request=request,
                state=state,
            )
            for request, state in activations.get(active.shot_id, ())
        ):
            return False
    return True


def _is_canonical_activated_shot_descendant(
    expected: Any,
    active: Any,
    *,
    request: Any,
    state: Any,
) -> bool:
    scope = request.activation_scope
    if scope is None:
        return False
    original = scope.request
    if (
        original.target_shot_id != expected.shot_id
        or state.candidate_video_asset_ids != (request.output_asset_id,)
        or active.visual_strategy is not VisualStrategy.GENERATED_VIDEO
        or active.generated_video_rationale
        != f"Sealed generation {state.generation_id}."
    ):
        return False
    mutable_fields = {
        "revision",
        "content_hash",
        "creation_receipt_id",
        "visual_strategy",
        "generated_video_rationale",
        "required_asset_roles",
    }
    if expected.model_dump(exclude=mutable_fields) != active.model_dump(
        exclude=mutable_fields
    ):
        return False
    expected_roles = tuple(
        role.model_copy(
            update={
                "asset_ids": (request.output_asset_id,),
                "allowed_asset_types": (AssetType.VIDEO,),
            }
        )
        if role.role == original.target_asset_role
        else role
        for role in expected.required_asset_roles
    )
    return active.required_asset_roles == expected_roles


__all__ = [
    "EcommerceAttemptIdentity",
    "EcommerceShotRepairContext",
    "EcommerceShotRepairDecision",
    "bound_generation_attempt_ids",
    "bound_generation_attempt_ids_for_shot",
    "canonical_attempt_identity",
    "canonical_attempt_verdict",
    "canonical_repair_frontier",
    "ecommerce_attempt_status",
    "ecommerce_manifest_revision",
    "input_attempt_identity",
    "plan_ecommerce_shot_repair",
    "shot_gate_verdict",
    "shots_match_handoff",
]
