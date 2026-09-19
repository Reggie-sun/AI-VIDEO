from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai_video.production.ecommerce_job_contracts import EcommerceJobNextAction
from ai_video.production.ecommerce_job_repair import (
    EcommerceAttemptIdentity,
    EcommerceShotRepairContext,
    attempt_requires_explicit_recovery,
    plan_ecommerce_shot_repair,
    shot_gate_verdict,
)
from ai_video.production.generation_diagnosis import Diagnosis, Intervention
from ai_video.production.models import QaVerdict, StateCommitStatus, VideoAttemptPhase


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _diagnosis(*failure_classes: str) -> Diagnosis:
    return Diagnosis(
        failure_classes=tuple(failure_classes),
        failed_requirements=("product_identity",),
        preserved_requirements=("timing", "continuity"),
        evidence_hashes=(HASH_A,),
        next_owner=(
            "explicit_recovery"
            if "UNKNOWN_OUTCOME" in failure_classes
            else "evidence_owner"
            if "EVIDENCE_GAP" in failure_classes
            else "shot_router"
        ),
        all_required_observed_pass=False,
    )


def _intervention(
    *,
    disposition: str = "CHANGE_REFERENCE_STRATEGY",
    changed_variables: tuple[str, ...] = ("image_bindings",),
) -> Intervention:
    return Intervention(
        intervention_id="repair-product-identity",
        candidate_id="candidate-repair",
        purpose="production_repair",
        disposition=disposition,
        closes=("product_identity",),
        protected_requirements=("timing", "continuity"),
        support=(HASH_A,),
        changed_variables=changed_variables,
        held_constants=("prompt_text",),
        uncontrolled_variables=(),
        regression_risks=("product_identity",),
        hypothesis="The diagnosed reference binding caused the identity defect.",
        confidence_basis="Exact failed attempt evidence.",
        improvement_prediction="Product identity remains stable.",
        falsification_prediction="Identity drift remains visible.",
        insufficient_evidence_condition="The repaired exact bytes are unavailable.",
    )


def _identity(
    attempt_id: str,
    *,
    routing: str = HASH_A,
    permit: str = "permit-a",
    resolved: str = HASH_A,
) -> EcommerceAttemptIdentity:
    return EcommerceAttemptIdentity(
        attempt_id=attempt_id,
        routing_binding_hash=routing,
        permit_id=permit,
        resolved_generation_hash=resolved,
    )


def test_not_evaluated_routes_to_evidence_repair_without_media_submit() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.NOT_EVALUATED,
            outcome_known=True,
            diagnosis=_diagnosis("EVIDENCE_GAP"),
            intervention=None,
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=None,
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE
    assert decision.media_submit_allowed is False
    assert decision.blocker_code is None


def test_unknown_outcome_stops_for_explicit_recovery() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=None,
            outcome_known=False,
            diagnosis=_diagnosis("UNKNOWN_OUTCOME"),
            intervention=None,
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=None,
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
    assert decision.media_submit_allowed is False


def test_known_failure_allows_one_diagnosed_new_attempt() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.FAIL,
            outcome_known=True,
            diagnosis=_diagnosis("QUALITY_FAILURE"),
            intervention=_intervention(),
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=_identity(
                "attempt-2",
                routing=HASH_A,
                permit="permit-b",
                resolved=HASH_B,
            ),
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.REPAIR_SHOT_MEDIA
    assert decision.media_submit_allowed is True
    assert decision.changed_variables == ("image_bindings",)


def test_exhausted_shot_ceiling_returns_blocked() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.FAIL,
            outcome_known=True,
            diagnosis=_diagnosis("QUALITY_FAILURE"),
            intervention=_intervention(),
            prior_attempt=_identity("attempt-2"),
            proposed_attempt=_identity("attempt-3", permit="permit-c", resolved=HASH_C),
            existing_job_attempts=2,
            existing_shot_repairs=1,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=3,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.BLOCKED
    assert decision.blocker_code == "ECOMMERCE_SHOT_REPAIR_CEILING_EXHAUSTED"
    assert decision.media_submit_allowed is False


def test_provider_switch_requires_new_routing_permit_attempt_and_resolved_identity() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.FAIL,
            outcome_known=True,
            diagnosis=_diagnosis("QUALITY_FAILURE"),
            intervention=_intervention(
                disposition="CHANGE_PROVIDER_MODEL",
                changed_variables=("provider_name", "model_id"),
            ),
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=_identity("attempt-1"),
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.BLOCKED
    assert decision.blocker_code == "ECOMMERCE_PROVIDER_SWITCH_IDENTITY_REUSED"
    assert decision.media_submit_allowed is False


def test_provider_switch_accepts_fully_resealed_identity() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.FAIL,
            outcome_known=True,
            diagnosis=_diagnosis("QUALITY_FAILURE"),
            intervention=_intervention(
                disposition="CHANGE_PROVIDER_MODEL",
                changed_variables=("provider_name", "model_id"),
            ),
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=_identity(
                "attempt-2",
                routing=HASH_B,
                permit="permit-b",
                resolved=HASH_C,
            ),
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.REPAIR_SHOT_MEDIA
    assert decision.media_submit_allowed is True


@pytest.mark.parametrize("disposition", ("CAPABILITY_BOUNDARY", "SPLIT_SHOT"))
def test_authoring_disposition_never_authorizes_media_submit(disposition: str) -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.FAIL,
            outcome_known=True,
            diagnosis=_diagnosis("QUALITY_FAILURE"),
            intervention=_intervention(disposition=disposition),
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=_identity(
                "attempt-2", permit="permit-b", resolved=HASH_B
            ),
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=True,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.BLOCKED
    assert decision.blocker_code == "ECOMMERCE_SHOT_REPAIR_AUTHORING_REQUIRED"
    assert decision.media_submit_allowed is False


def test_declared_repair_without_verified_request_delta_is_blocked() -> None:
    decision = plan_ecommerce_shot_repair(
        EcommerceShotRepairContext(
            shot_id="shot-1",
            verdict=QaVerdict.FAIL,
            outcome_known=True,
            diagnosis=_diagnosis("QUALITY_FAILURE"),
            intervention=_intervention(),
            prior_attempt=_identity("attempt-1"),
            proposed_attempt=_identity(
                "attempt-2", permit="permit-b", resolved=HASH_B
            ),
            existing_job_attempts=1,
            existing_shot_repairs=0,
            request_delta_verified=False,
        ),
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )

    assert decision.next_action is EcommerceJobNextAction.BLOCKED
    assert decision.blocker_code == "ECOMMERCE_SHOT_REPAIR_DELTA_INVALID"
    assert decision.media_submit_allowed is False


@pytest.mark.parametrize("status", (StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN))
def test_submit_intent_requires_explicit_recovery(status: StateCommitStatus) -> None:
    attempt = SimpleNamespace(
        status=status,
        video_generation_state=SimpleNamespace(phase=VideoAttemptPhase.SUBMIT_INTENT),
    )

    assert attempt_requires_explicit_recovery(attempt) is True


def test_missing_deferred_facade_cannot_fabricate_a_gate_verdict(tmp_path) -> None:
    execution = SimpleNamespace(
        shots=(SimpleNamespace(shot_id="shot-1", attempt_id="attempt-1"),)
    )

    assert shot_gate_verdict(
        tmp_path,
        execution,
        {},
        shot_id="shot-1",
    ) is None
