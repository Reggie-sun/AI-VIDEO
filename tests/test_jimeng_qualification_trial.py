from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._shot_router_contracts import (
    RouterPolicyIdentity,
    VideoRoutingPolicy,
)
from ai_video.production.generation_decision import (
    DecisionPolicy,
    resolve_generation_decision,
)
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from ai_video.production.generation_feedback import record_attempt_evaluation
from ai_video.production.generation_runtime_repair import (
    MAX_RUNTIME_REPAIRS_PER_SHOT,
    PaidNoEffectRetarget,
    PaidNoEffectRepairExtension,
    RuntimeRepairAuthorization,
    RuntimeRepairGrant,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, StateCommitStatus
from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import VideoProviderCapabilities, VideoTaskState
from ai_video.production.video_compiler import CompiledProviderVideoRequest
from ai_video.production.video_generation import VideoGenerationService
from production_project_factory import make_p8_video_candidate_preparer
from test_production_generated_video_e2e import _runtime
from test_production_video import _paid_authorization, _paid_preview


def _reconcile_qualification_no_effect(committer, attempt_id: str):
    from ai_video.production._state_commit_contracts import PreparedArtifact
    from ai_video.production.paid_provider_no_effect_reconciliation import (
        PaidProviderNoEffectEvidencePointer,
        PaidProviderNoEffectReconciliation,
        canonical_paid_provider_no_effect_evidence_path,
    )

    manifest = committer._read_manifest()
    attempt = committer._video_attempt(manifest, attempt_id)
    assert attempt.paid_provider_state is not None
    assert attempt.paid_provider_state.submit_receipt is not None
    assert manifest.active_paid_provider_budget is not None
    payload = b'{"proof":"canonical test transport failed before dispatch"}\n'
    digest = hashlib.sha256(payload).hexdigest()
    evidence = PreparedArtifact(
        relative_path=canonical_paid_provider_no_effect_evidence_path(digest),
        payload=payload,
        file_sha256=digest,
    )
    now = committer._paid_provider_clock()
    actor = ActorIdentity(actor_id="qualification-test-human", actor_kind="human")
    reconciliation = PaidProviderNoEffectReconciliation.create(
        project_id=manifest.project_id,
        attempt_id=attempt_id,
        actor=actor,
        explicit_user_authorization_receipt_id="qualification-test-reconciled-no-effect",
        prior_submit_receipt=attempt.paid_provider_state.submit_receipt,
        base_budget=manifest.active_paid_provider_budget,
        expected_manifest_revision=manifest.manifest_revision,
        evidence=(
            PaidProviderNoEffectEvidencePointer(
                path=evidence.relative_path,
                file_sha256=digest,
                size_bytes=len(payload),
            ),
        ),
        reason="verified_pre_transport_failure",
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    committer.reconcile_paid_provider_no_effect(
        reconciliation,
        evidence_artifacts=(evidence,),
        authorizer=lambda exact, artifacts: (
            actor if exact == reconciliation and artifacts == (evidence,) else None
        ),
    )


QUALIFICATION_ATTEMPT_ID = "jimeng-qualification-trial-fixture"


def _qualification_execution(
    root: Path,
    *,
    paid_submit_ceiling: int = 1,
    paid_submits_used: int = 0,
    max_resamples: int = 0,
    remote_authorized: bool = True,
    budget_authorized: bool = True,
):
    inputs, provider, _, production_binding, _, _ = _runtime(
        root,
        status_events=(VideoTaskState.SUCCEEDED,),
    )
    assert production_binding is not None
    return _qualification_binding(
        inputs,
        provider,
        production_binding,
        paid_submit_ceiling=paid_submit_ceiling,
        paid_submits_used=paid_submits_used,
        max_resamples=max_resamples,
        remote_authorized=remote_authorized,
        budget_authorized=budget_authorized,
    )


def _qualification_binding(
    inputs,
    provider,
    production_binding,
    *,
    paid_submit_ceiling: int = 1,
    paid_submits_used: int = 0,
    max_resamples: int = 0,
    remote_authorized: bool = True,
    budget_authorized: bool = True,
    evidence=(),
    latest_attempt_hash=None,
    experiences=(),
    runtime_repairs=(),
    lifecycle_updates=None,
):
    base = production_binding
    capability = base.inputs.candidates[0].capabilities
    variant = capability.variants[0].model_copy(
        update={"production_qualification": "UNQUALIFIED"}
    )
    trial_capability = VideoProviderCapabilities.create(
        provider_name=capability.provider_name,
        variants=(variant,),
    )
    provider._capabilities = trial_capability

    candidate = base.inputs.candidates[0].model_copy(
        update={"capabilities": trial_capability}
    )
    limits = base.inputs.limits.model_copy(
        update={
            "generation_forbidden": False,
            "allowed_remote_candidates": (candidate.candidate_id,),
            "paid_submit_ceiling": paid_submit_ceiling,
            "paid_submits_used": paid_submits_used,
            "local_batch_used": 0,
            "local_total_used": 0,
            "local_resource_available": False,
        }
    )
    decision_policy = base.inputs.policy.model_copy(
        update={"max_resamples": max_resamples, "allow_bounded_exploration": True}
    )
    decision_inputs = base.inputs.model_copy(
        update={
            "policy": decision_policy,
            "limits": limits,
            "candidates": (candidate,),
            "evidence": evidence,
            "latest_attempt_hash": latest_attempt_hash,
            "experiences": experiences,
            "runtime_repairs": runtime_repairs,
        }
    )
    identity = base.policy.identity.model_copy(
        update={
            "policy_id": "jimeng-qualification-trial",
            "policy_sha256": canonical_sha256(
                {
                    "purpose": "qualification",
                    "candidate_id": candidate.candidate_id,
                    "paid_submit_ceiling": paid_submit_ceiling,
                    "paid_submits_used": paid_submits_used,
                    "max_resamples": max_resamples,
                }
            ),
        }
    )
    policy = base.policy.model_copy(
        update={
            "identity": identity,
            "execution_purpose": "qualification",
            "remote_authorized": remote_authorized,
            "budget_authorized": budget_authorized,
            "local_resources_available": False,
        }
    )
    lifecycle = base.lifecycle.model_copy(update=lifecycle_updates or {})
    decision = resolve_generation_decision(
        VideoGenerationResolver(),
        projection=base.projection,
        context=base.context,
        policy=policy,
        lifecycle=lifecycle,
        inputs=decision_inputs,
        continuity_routing=base.continuity_routing,
    )
    if decision.routing is None:
        return inputs, provider, decision, None, None
    assert decision.routing.provider_bound_request is not None
    compiled = provider.compile_request(
        decision.routing.provider_bound_request,
        base.projection.requirement,
    )
    assert isinstance(compiled, CompiledProviderVideoRequest)
    request = provider.resolve(compiled.request)
    binding = GenerationDecisionExecutionBinding.create(
        projection=base.projection,
        context=base.context,
        policy=policy,
        lifecycle=lifecycle,
        inputs=decision_inputs,
        decision=decision,
        compiled_request=request,
        continuity_routing=base.continuity_routing,
    )
    return inputs, provider, decision, binding, request


def _failed_paid_qualification(root: Path):
    inputs, provider, _, base, _, _ = _runtime(
        root,
        status_events=(VideoTaskState.SUCCEEDED,),
    )
    assert base is not None
    _, _, _, binding, request = _qualification_binding(inputs, provider, base)
    assert binding is not None and request is not None

    first_attempt_id = "jimeng-qualification-known-no-effect"
    provider._scenario = replace(provider._scenario, submit_outcome="rejected")
    first_preview = _paid_preview(
        request,
        attempt_id=first_attempt_id,
        video_preview=provider.preview(request),
    )
    first_authorization = _paid_authorization(first_preview)
    authorizations = {first_preview.preview_fingerprint: first_authorization}

    def authorize(exact):
        authorization = authorizations.get(exact.preview_fingerprint)
        if authorization is None:
            authorization = _paid_authorization(exact)
            authorizations[exact.preview_fingerprint] = authorization
        return authorization

    committer = ProductionStateCommitter(
        root,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=authorize,
        paid_provider_clock=lambda: first_authorization.issued_at,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=first_attempt_id,
        request=request,
        execution_binding=binding,
    )
    with pytest.raises(AiVideoError) as error:
        service.submit_once(
            attempt_id=first_attempt_id,
            paid_preview=first_preview,
            reservation_id="jimeng-qualification-no-effect-reservation",
        )
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    first_attempt = committer._video_attempt(
        committer._read_manifest(), first_attempt_id
    )
    assert first_attempt.status is StateCommitStatus.FAILED
    assert first_attempt.paid_provider_state is not None
    receipt = committer._reopen_paid_submit(
        first_attempt.paid_provider_state.submit_receipt
    )
    assert receipt.outcome.value == "known_no_effect"

    experience = record_attempt_evaluation(
        committer=committer,
        attempt_id=first_attempt_id,
    )
    evidence = experience.evidence[-1]
    assert evidence.outcome == "runtime_failure"
    target = next(
        item for item in binding.inputs.candidates
        if item.candidate_id == binding.decision.selected_candidate_id
    )
    pointer = committer.record_runtime_repair_authorization(
        attempt_id=first_attempt_id,
        evidence_hash=evidence.evidence_hash,
        repair_basis="The transport dependency was repaired before provider dispatch.",
        actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
            target_scope_hash=target.scope_hash,
        ),
    )
    repair = committer._reopen_runtime_repair_authorization(pointer)
    grant = RuntimeRepairGrant(authorization=repair, consumed=False)
    return inputs, provider, base, committer, service, first_attempt_id, experience, grant


def _extend_paid_submit_quota(
    committer: ProductionStateCommitter,
    *,
    prior_attempt_id: str,
    target_attempt_id: str,
    new_ceiling: int,
):
    manifest = committer._read_manifest()
    target = committer._video_attempt(manifest, target_attempt_id)
    prior = committer._video_attempt(manifest, prior_attempt_id)
    assert target.video_generation_state is not None
    assert prior.video_generation_state is not None
    assert manifest.active_paid_provider_budget is not None
    binding = committer._reopen_generation_execution_binding(
        target.video_generation_state.execution_binding
    )
    now = committer._paid_provider_clock()
    extension = PaidProviderSubmitQuotaExtension.create(
        extension_id=f"jimeng-qualification-submit-quota-{new_ceiling}",
        project_id=manifest.project_id,
        actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
        explicit_opt_in=True,
        authorization_receipt_id=f"authorized-qualification-submit-quota-{new_ceiling}",
        expected_manifest_revision=manifest.manifest_revision,
        base_budget=manifest.active_paid_provider_budget,
        target_attempt_id=target_attempt_id,
        target_binding=target.video_generation_state.execution_binding,
        prior_attempt_id=prior_attempt_id,
        prior_binding=prior.video_generation_state.execution_binding,
        task_id=binding.inputs.limits.task_id,
        old_paid_submit_ceiling=new_ceiling - 1,
        new_paid_submit_ceiling=new_ceiling,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    return committer.extend_paid_provider_submit_quota(extension)


def _two_failed_paid_qualification(root: Path):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        first_experience,
        first_grant,
    ) = _failed_paid_qualification(root)
    second_attempt_id = "jimeng-qualification-second-reconciled-no-effect"
    first_failure = first_experience.evidence[-1]
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=2,
        paid_submits_used=1,
        evidence=first_experience.evidence,
        latest_attempt_hash=first_failure.evidence_hash,
        experiences=(first_experience,),
        runtime_repairs=(first_grant,),
        lifecycle_updates={
            "generation_id": "jimeng-qualification-second-generation",
            "output_asset_id": "jimeng-qualification-second-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert binding is not None and request is not None
    service.start(
        attempt_id=second_attempt_id,
        request=request,
        execution_binding=binding,
    )
    preview = _paid_preview(
        request,
        attempt_id=second_attempt_id,
        video_preview=provider.preview(request),
    )
    with pytest.raises(AiVideoError, match="submit ceilings cannot expand"):
        service.submit_once(
            attempt_id=second_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-second-reservation",
        )
    _extend_paid_submit_quota(
        committer,
        prior_attempt_id=first_attempt_id,
        target_attempt_id=second_attempt_id,
        new_ceiling=2,
    )
    provider._scenario = replace(provider._scenario, submit_outcome="outcome_unknown")
    with pytest.raises(AiVideoError) as error:
        service.submit_once(
            attempt_id=second_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-second-reservation",
        )
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    second_attempt = committer._video_attempt(
        committer._read_manifest(), second_attempt_id
    )
    assert second_attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert second_attempt.paid_provider_state is not None
    unknown_receipt = committer._reopen_paid_submit(
        second_attempt.paid_provider_state.submit_receipt
    )
    assert unknown_receipt.outcome.value == "outcome_unknown"
    _reconcile_qualification_no_effect(committer, second_attempt_id)
    second_experience = record_attempt_evaluation(
        committer=committer,
        attempt_id=second_attempt_id,
    )
    second_failure = second_experience.evidence[-1]
    assert second_failure.outcome == "not_submitted"
    second_attempt = committer._video_attempt(
        committer._read_manifest(), second_attempt_id
    )
    assert second_attempt.status is StateCommitStatus.FAILED
    assert second_attempt.paid_provider_state is not None
    second_receipt = committer._reopen_paid_submit(
        second_attempt.paid_provider_state.submit_receipt
    )
    assert second_receipt.outcome.value == "known_no_effect"
    assert second_receipt.no_effect_reconciliation is not None
    target = next(
        item for item in binding.inputs.candidates
        if item.candidate_id == binding.decision.selected_candidate_id
    )
    pointer = committer.record_runtime_repair_authorization(
        attempt_id=second_attempt_id,
        evidence_hash=second_failure.evidence_hash,
        repair_basis="Canonical evidence verified a pre-transport failure and retained the original UNKNOWN receipt.",
        actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint=second_receipt.submit_receipt_fingerprint,
            target_scope_hash=target.scope_hash,
        ),
    )

    grants = []
    for attempt_id in (first_attempt_id, second_attempt_id):
        attempt = committer._video_attempt(committer._read_manifest(), attempt_id)
        assert attempt.video_generation_state is not None
        for registered in attempt.video_generation_state.runtime_repairs:
            grants.append(
                RuntimeRepairGrant(
                    authorization=committer._reopen_runtime_repair_authorization(registered),
                    consumed=registered.consumed,
                )
            )
    assert len(grants) == 2
    assert grants[0].consumed is True
    assert grants[1].consumed is False
    return (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        second_attempt_id,
        first_experience,
        second_experience,
        tuple(grants),
    )


def _three_failed_paid_qualification(root: Path):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        second_attempt_id,
        first_experience,
        second_experience,
        grants,
    ) = _two_failed_paid_qualification(root)
    history = (*first_experience.evidence, *second_experience.evidence)
    latest = second_experience.evidence[-1]
    third_attempt_id = "jimeng-qualification-third-reconciled-no-effect"
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=3,
        paid_submits_used=2,
        evidence=history,
        latest_attempt_hash=latest.evidence_hash,
        experiences=(first_experience, second_experience),
        runtime_repairs=grants,
        lifecycle_updates={
            "generation_id": "jimeng-qualification-third-failed-generation",
            "output_asset_id": "jimeng-qualification-third-failed-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert binding is not None and request is not None
    service.start(attempt_id=third_attempt_id, request=request, execution_binding=binding)
    preview = _paid_preview(
        request,
        attempt_id=third_attempt_id,
        video_preview=provider.preview(request),
    )
    _extend_paid_submit_quota(
        committer,
        prior_attempt_id=second_attempt_id,
        target_attempt_id=third_attempt_id,
        new_ceiling=3,
    )
    provider._scenario = replace(provider._scenario, submit_outcome="outcome_unknown")
    with pytest.raises(AiVideoError) as error:
        service.submit_once(
            attempt_id=third_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-third-reservation",
        )
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    attempt = committer._video_attempt(committer._read_manifest(), third_attempt_id)
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.paid_provider_state is not None
    unknown_receipt = committer._reopen_paid_submit(
        attempt.paid_provider_state.submit_receipt
    )
    assert unknown_receipt.outcome.value == "outcome_unknown"
    unknown_experience = record_attempt_evaluation(
        committer=committer,
        attempt_id=third_attempt_id,
    )
    assert unknown_experience.evidence[-1].outcome == "unknown_outcome"

    manifest = committer._read_manifest()
    target = next(
        item for item in binding.inputs.candidates
        if item.candidate_id == binding.decision.selected_candidate_id
    )
    unknown_extension = PaidNoEffectRepairExtension(
        task_id=binding.inputs.limits.task_id,
        shot_id=binding.context.target_shot_id,
        failed_binding_hash=binding.binding_hash,
        expected_manifest_revision=manifest.manifest_revision,
        authorization_receipt_id="unknown-attempt-is-not-an-authorization",
    )
    for ceiling in (3, 4):
        with pytest.raises(AiVideoError, match="failed video attempt"):
            committer.record_runtime_repair_authorization(
                attempt_id=third_attempt_id,
                evidence_hash=unknown_experience.evidence[-1].evidence_hash,
                repair_basis="An UNKNOWN submit cannot be retried.",
                actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
                paid_no_effect_retarget=PaidNoEffectRetarget(
                    submit_receipt_fingerprint=unknown_receipt.submit_receipt_fingerprint,
                    target_scope_hash=target.scope_hash,
                ),
                paid_no_effect_extension=unknown_extension.model_copy(
                    update={"ceiling": ceiling}
                ),
        )

    _reconcile_qualification_no_effect(committer, third_attempt_id)
    third_experience = record_attempt_evaluation(
        committer=committer,
        attempt_id=third_attempt_id,
    )
    assert third_experience.evidence[-1].outcome == "not_submitted"
    attempt = committer._video_attempt(committer._read_manifest(), third_attempt_id)
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.paid_provider_state is not None
    receipt = committer._reopen_paid_submit(attempt.paid_provider_state.submit_receipt)
    assert receipt.outcome.value == "known_no_effect"
    assert receipt.no_effect_reconciliation is not None
    return (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        second_attempt_id,
        third_attempt_id,
        first_experience,
        second_experience,
        third_experience,
        binding,
        receipt,
    )


def _fourth_failed_paid_qualification(root: Path):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        second_attempt_id,
        third_attempt_id,
        first_experience,
        second_experience,
        third_experience,
        third_binding,
        third_receipt,
    ) = _three_failed_paid_qualification(root)
    third_evidence = third_experience.evidence[-1]
    actor = ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex")
    target = next(
        item for item in third_binding.inputs.candidates
        if item.candidate_id == third_binding.decision.selected_candidate_id
    )
    manifest = committer._read_manifest()
    third_extension = PaidNoEffectRepairExtension(
        task_id=third_binding.inputs.limits.task_id,
        shot_id=third_binding.context.target_shot_id,
        failed_binding_hash=third_binding.binding_hash,
        expected_manifest_revision=manifest.manifest_revision,
        authorization_receipt_id="qualification-test-third-recovery",
    )
    committer.record_runtime_repair_authorization(
        attempt_id=third_attempt_id,
        evidence_hash=third_evidence.evidence_hash,
        repair_basis="The reconciled no-effect outcome authorizes one exact bounded replacement.",
        actor=actor,
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint=third_receipt.submit_receipt_fingerprint,
            target_scope_hash=target.scope_hash,
        ),
        paid_no_effect_extension=third_extension,
    )

    experiences = committer.read_generation_experiences()
    experiences = tuple(
        experience for experience in experiences
        if any(item.shot_id == third_evidence.shot_id for item in experience.evidence)
    )
    evidence = tuple(
        item for experience in experiences for item in experience.evidence
        if item.shot_id == third_evidence.shot_id
    )
    grants = []
    for prior_id in (first_attempt_id, second_attempt_id, third_attempt_id):
        prior = committer._video_attempt(committer._read_manifest(), prior_id)
        assert prior.video_generation_state is not None
        grants.extend(
            RuntimeRepairGrant(
                authorization=committer._reopen_runtime_repair_authorization(pointer),
                consumed=pointer.consumed,
            )
            for pointer in prior.video_generation_state.runtime_repairs
        )
    assert [grant.consumed for grant in grants] == [True, True, False]

    fourth_attempt_id = "jimeng-qualification-fourth-known-no-effect"
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=4,
        paid_submits_used=3,
        evidence=evidence,
        latest_attempt_hash=third_evidence.evidence_hash,
        experiences=experiences,
        runtime_repairs=tuple(grants),
        lifecycle_updates={
            "generation_id": "jimeng-qualification-fourth-failed-generation",
            "output_asset_id": "jimeng-qualification-fourth-failed-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert binding is not None and request is not None
    service.start(attempt_id=fourth_attempt_id, request=request, execution_binding=binding)
    preview = _paid_preview(
        request,
        attempt_id=fourth_attempt_id,
        video_preview=provider.preview(request),
    )
    _extend_paid_submit_quota(
        committer,
        prior_attempt_id=third_attempt_id,
        target_attempt_id=fourth_attempt_id,
        new_ceiling=4,
    )
    provider._scenario = replace(provider._scenario, submit_outcome="rejected")
    with pytest.raises(AiVideoError) as error:
        service.submit_once(
            attempt_id=fourth_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-fourth-no-effect-reservation",
        )
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    attempt = committer._video_attempt(committer._read_manifest(), fourth_attempt_id)
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.paid_provider_state is not None
    receipt = committer._reopen_paid_submit(attempt.paid_provider_state.submit_receipt)
    assert receipt.outcome.value == "known_no_effect"
    assert receipt.no_effect_reconciliation is None
    experience = record_attempt_evaluation(
        committer=committer,
        attempt_id=fourth_attempt_id,
    )
    assert experience.evidence[-1].outcome == "runtime_failure"
    experiences = committer.read_generation_experiences()
    experiences = tuple(
        item for item in experiences
        if any(e.shot_id == experience.evidence[-1].shot_id for e in item.evidence)
    )
    evidence = tuple(
        entry for stored in experiences for entry in stored.evidence
        if entry.shot_id == experience.evidence[-1].shot_id
    )
    prior = committer._video_attempt(committer._read_manifest(), third_attempt_id)
    assert prior.video_generation_state is not None
    assert prior.video_generation_state.runtime_repairs[-1].consumed is True
    return (
        inputs,
        provider,
        base,
        committer,
        service,
        (first_attempt_id, second_attempt_id, third_attempt_id, fourth_attempt_id),
        experiences,
        evidence,
        binding,
        receipt,
        actor,
        grants,
    )


def make_fetched_qualification_trial(root: Path):
    """Build a canonical fake paid trial stopped at VALIDATE for capture tests."""

    inputs, provider, _, binding, request = _qualification_execution(root)
    assert binding is not None
    assert request is not None
    attempt_id = QUALIFICATION_ATTEMPT_ID
    video_preview = provider.preview(request)
    paid_preview = _paid_preview(
        request,
        attempt_id=attempt_id,
        video_preview=video_preview,
    )
    authorization = _paid_authorization(paid_preview)
    committer = ProductionStateCommitter(
        root,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=(
            lambda exact: authorization if exact == paid_preview else None
        ),
        paid_provider_clock=lambda: authorization.issued_at,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=attempt_id,
        request=request,
        execution_binding=binding,
    )
    service.submit_once(
        attempt_id=attempt_id,
        paid_preview=paid_preview,
        reservation_id="jimeng-qualification-trial-reservation",
    )
    service.refresh_once(attempt_id=attempt_id)
    committer.settle_paid_provider_reservation(
        attempt_id=attempt_id,
        actual_cost_microunits=paid_preview.estimated_cost_upper_bound_microunits,
    )
    service.fetch_once(attempt_id=attempt_id)
    state = committer._video_attempt(
        committer._read_manifest(), attempt_id
    ).video_generation_state
    assert state is not None
    assert state.phase.value == "validate"
    assert state.execution_binding is not None
    assert state.candidate_video_asset_ids == ()
    assert state.quality_rejection is None
    return inputs, provider, committer, attempt_id


def test_qualification_trial_fetches_without_candidate_or_activation(tmp_path: Path):
    _, provider, committer, attempt_id = make_fetched_qualification_trial(tmp_path)
    service = VideoGenerationService(committer=committer, provider=provider)

    with pytest.raises(
        AiVideoError,
        match="Qualification execution cannot prepare a production candidate",
    ):
        service.validate_once(attempt_id=attempt_id)
    with pytest.raises(
        AiVideoError,
        match="Qualification execution cannot prepare a production candidate",
    ):
        service.fetch_and_activate(attempt_id=attempt_id)
    with pytest.raises(
        AiVideoError,
        match="Qualification execution cannot be activated as production",
    ):
        committer.activate_video_candidate(attempt_id=attempt_id)
    with pytest.raises(
        AiVideoError,
        match="Qualification execution cannot be activated as production",
    ):
        committer.replay_active_video_generation(attempt_id=attempt_id)
    state = committer._video_attempt(
        committer._read_manifest(), attempt_id
    ).video_generation_state
    assert state is not None
    assert state.candidate_video_asset_ids == ()


@pytest.mark.parametrize(
    "limits",
    ({"paid_submit_ceiling": 2}, {"max_resamples": 1}),
)
def test_qualification_execution_binding_rejects_expanded_trial_limits(
    tmp_path: Path,
    limits: dict[str, int],
):
    with pytest.raises(
        ValidationError,
        match="qualification execution binding exceeds its bounded remote trial scope",
    ):
        _qualification_execution(tmp_path, **limits)


def test_qualification_known_no_effect_recovery_uses_one_committer_quota_extension(
    tmp_path: Path,
):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        experience,
        grant,
    ) = _failed_paid_qualification(tmp_path)
    failure = experience.evidence[-1]
    recovery_attempt_id = "jimeng-qualification-recovery"
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=2,
        paid_submits_used=1,
        evidence=experience.evidence,
        latest_attempt_hash=failure.evidence_hash,
        experiences=(experience,),
        runtime_repairs=(grant,),
        lifecycle_updates={
            "generation_id": "jimeng-qualification-recovery-generation",
            "output_asset_id": "jimeng-qualification-recovery-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert decision.runtime_repair == grant.authorization
    assert binding is not None and request is not None
    service.start(
        attempt_id=recovery_attempt_id,
        request=request,
        execution_binding=binding,
    )

    preview = _paid_preview(
        request,
        attempt_id=recovery_attempt_id,
        video_preview=provider.preview(request),
    )
    submits_before_block = provider.call_counts.submit
    with pytest.raises(AiVideoError, match="submit ceilings cannot expand"):
        service.submit_once(
            attempt_id=recovery_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-recovery-reservation",
        )
    assert provider.call_counts.submit == submits_before_block

    manifest = committer._read_manifest()
    target = committer._video_attempt(manifest, recovery_attempt_id)
    prior = committer._video_attempt(manifest, first_attempt_id)
    assert target.video_generation_state is not None
    assert prior.video_generation_state is not None
    now = committer._paid_provider_clock()
    extension = PaidProviderSubmitQuotaExtension.create(
        extension_id="jimeng-qualification-one-known-no-effect-recovery",
        project_id=manifest.project_id,
        actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
        explicit_opt_in=True,
        authorization_receipt_id="authorized-one-qualification-recovery-submit",
        expected_manifest_revision=manifest.manifest_revision,
        base_budget=manifest.active_paid_provider_budget,
        target_attempt_id=recovery_attempt_id,
        target_binding=target.video_generation_state.execution_binding,
        prior_attempt_id=first_attempt_id,
        prior_binding=prior.video_generation_state.execution_binding,
        task_id=binding.inputs.limits.task_id,
        old_paid_submit_ceiling=1,
        new_paid_submit_ceiling=2,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    committer.extend_paid_provider_submit_quota(extension)

    provider._scenario = replace(
        provider._scenario,
        submit_outcome="accepted",
        external_effect_id="jimeng-qualification-recovery-effect",
    )
    service.submit_once(
        attempt_id=recovery_attempt_id,
        paid_preview=preview,
        reservation_id="jimeng-qualification-recovery-reservation",
    )
    assert provider.call_counts.submit == submits_before_block + 1
    recovered_manifest = committer._read_manifest()
    recovered = committer._video_attempt(recovered_manifest, recovery_attempt_id)
    prior = committer._video_attempt(recovered_manifest, first_attempt_id)
    assert recovered.paid_provider_state is not None
    assert recovered.paid_provider_state.submit_receipt is not None
    assert (
        committer._reopen_paid_submit(recovered.paid_provider_state.submit_receipt)
        .outcome.value
        == "accepted"
    )
    assert prior.video_generation_state is not None
    assert prior.video_generation_state.runtime_repairs[0].consumed is True


@pytest.mark.parametrize("bad_grant", ("missing", "wrong_scope", "unknown_outcome"))
def test_qualification_recovery_blocks_without_exact_known_no_effect_grant(
    tmp_path: Path,
    bad_grant: str,
):
    inputs, provider, base, committer, _, first_attempt_id, experience, grant = (
        _failed_paid_qualification(tmp_path)
    )
    failure = experience.evidence[-1]
    evidence = experience.evidence
    latest_hash = failure.evidence_hash
    experiences = (experience,)
    grants = (grant,)
    if bad_grant == "missing":
        grants = ()
        expected = "RUNTIME_FAILURE"
    elif bad_grant == "wrong_scope":
        wrong_authorization = RuntimeRepairAuthorization.create(
            schema_version="runtime-repair/3",
            attempt_id=first_attempt_id,
            evidence_hash=failure.evidence_hash,
            repair_basis="A mismatched target must remain blocked.",
            actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
            expected_manifest_revision=committer._read_manifest().manifest_revision,
            paid_no_effect_retarget=PaidNoEffectRetarget(
                submit_receipt_fingerprint=(
                    grant.authorization.paid_no_effect_retarget.submit_receipt_fingerprint
                ),
                target_scope_hash="f" * 64,
            ),
        )
        grants = (RuntimeRepairGrant(authorization=wrong_authorization, consumed=False),)
        expected = "EVIDENCE_GAP"
    else:
        unknown = failure.model_copy(
            update={"outcome": "unknown_outcome", "runtime_reason": None}
        )
        unknown_experience = experience.model_copy(update={"evidence": (unknown,)})
        evidence = (unknown,)
        latest_hash = unknown.evidence_hash
        experiences = (unknown_experience,)
        expected = "UNKNOWN_OUTCOME"

    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=2,
        paid_submits_used=1,
        evidence=evidence,
        latest_attempt_hash=latest_hash,
        experiences=experiences,
        runtime_repairs=grants,
        lifecycle_updates={
            "generation_id": f"jimeng-qualification-blocked-{bad_grant}",
            "output_asset_id": f"jimeng-qualification-blocked-video-{bad_grant}",
        },
    )
    assert decision.disposition == expected
    assert decision.routing is None
    assert binding is None
    assert request is None


def test_qualification_second_recovery_requires_two_predecessor_failures(tmp_path: Path):
    inputs, provider, base, _, _, _, experience, grant = _failed_paid_qualification(tmp_path)
    failure = experience.evidence[-1]
    with pytest.raises(
        ValidationError,
        match="qualification execution binding exceeds its bounded remote trial scope",
    ):
        _qualification_binding(
            inputs,
            provider,
            base,
            paid_submit_ceiling=3,
            paid_submits_used=2,
            evidence=experience.evidence,
            latest_attempt_hash=failure.evidence_hash,
            experiences=(experience,),
            runtime_repairs=(grant,),
            lifecycle_updates={
                "generation_id": "jimeng-qualification-third-submit-denied",
                "output_asset_id": "jimeng-qualification-third-submit-denied-video",
            },
        )


def test_qualification_second_recovery_uses_two_quota_extensions_and_stops_at_three(
    tmp_path: Path,
):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        second_attempt_id,
        first_experience,
        second_experience,
        grants,
    ) = _two_failed_paid_qualification(tmp_path)
    evidence = (*first_experience.evidence, *second_experience.evidence)
    assert len({item.attempt_id for item in evidence}) == 2
    assert first_experience.evidence[-1].outcome == "runtime_failure"
    assert second_experience.evidence[-1].outcome == "not_submitted"
    latest = second_experience.evidence[-1]
    third_attempt_id = "jimeng-qualification-third-submit"
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=3,
        paid_submits_used=2,
        evidence=evidence,
        latest_attempt_hash=latest.evidence_hash,
        experiences=(first_experience, second_experience),
        runtime_repairs=grants,
        lifecycle_updates={
            "generation_id": "jimeng-qualification-third-generation",
            "output_asset_id": "jimeng-qualification-third-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert decision.runtime_repair == grants[1].authorization
    assert binding is not None and request is not None
    service.start(
        attempt_id=third_attempt_id,
        request=request,
        execution_binding=binding,
    )
    preview = _paid_preview(
        request,
        attempt_id=third_attempt_id,
        video_preview=provider.preview(request),
    )
    submits_before_block = provider.call_counts.submit
    with pytest.raises(AiVideoError, match="submit ceilings cannot expand"):
        service.submit_once(
            attempt_id=third_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-third-reservation",
        )
    assert provider.call_counts.submit == submits_before_block == 2

    _extend_paid_submit_quota(
        committer,
        prior_attempt_id=second_attempt_id,
        target_attempt_id=third_attempt_id,
        new_ceiling=3,
    )
    provider._scenario = replace(
        provider._scenario,
        submit_outcome="accepted",
        external_effect_id="jimeng-qualification-third-effect",
    )
    service.submit_once(
        attempt_id=third_attempt_id,
        paid_preview=preview,
        reservation_id="jimeng-qualification-third-reservation",
    )
    assert provider.call_counts.submit == 3
    manifest = committer._read_manifest()
    third = committer._video_attempt(manifest, third_attempt_id)
    second = committer._video_attempt(manifest, second_attempt_id)
    assert third.paid_provider_state is not None
    assert third.paid_provider_state.submit_receipt is not None
    assert (
        committer._reopen_paid_submit(third.paid_provider_state.submit_receipt)
        .outcome.value
        == "accepted"
    )
    assert second.video_generation_state is not None
    assert second.video_generation_state.runtime_repairs[0].consumed is True
    assert second.paid_provider_state is not None
    second_receipt = committer._reopen_paid_submit(second.paid_provider_state.submit_receipt)
    assert second_receipt.no_effect_reconciliation is not None
    budget = committer._reopen_paid_budget(manifest.active_paid_provider_budget)
    assert tuple(
        (item.old_paid_submit_ceiling, item.new_paid_submit_ceiling)
        for item in budget.submit_quota_extensions
    ) == ((1, 2), (2, 3))


def test_qualification_second_recovery_requires_latest_unconsumed_exact_grant(
    tmp_path: Path,
):
    (
        inputs,
        provider,
        base,
        _committer,
        _service,
        _first_attempt_id,
        _second_attempt_id,
        first_experience,
        second_experience,
        grants,
    ) = _two_failed_paid_qualification(tmp_path)
    evidence = (*first_experience.evidence, *second_experience.evidence)
    latest = second_experience.evidence[-1]
    current_grant = grants[1]
    wrong_scope = RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/3",
        attempt_id=latest.attempt_id,
        evidence_hash=latest.evidence_hash,
        repair_basis="A mismatched target scope must remain blocked.",
        actor=current_grant.authorization.actor,
        expected_manifest_revision=current_grant.authorization.expected_manifest_revision,
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint=(
                current_grant.authorization.paid_no_effect_retarget.submit_receipt_fingerprint
            ),
            target_scope_hash="f" * 64,
        ),
    )
    cases = (
        ("missing", (grants[0],)),
        ("wrong_scope", (grants[0], RuntimeRepairGrant(authorization=wrong_scope, consumed=False))),
        ("consumed", (grants[0], RuntimeRepairGrant(
            authorization=current_grant.authorization, consumed=True))),
    )
    for case, supplied_grants in cases:
        _, _, decision, binding, request = _qualification_binding(
            inputs,
            provider,
            base,
            paid_submit_ceiling=3,
            paid_submits_used=2,
            evidence=evidence,
            latest_attempt_hash=latest.evidence_hash,
            experiences=(first_experience, second_experience),
            runtime_repairs=supplied_grants,
            lifecycle_updates={
                "generation_id": f"jimeng-qualification-invalid-grant-{case}",
                "output_asset_id": f"jimeng-qualification-invalid-grant-video-{case}",
            },
        )
        assert decision.disposition == "EVIDENCE_GAP", case
        assert decision.routing is None, case
        assert binding is None and request is None, case


def test_qualification_rejects_unsubmitted_evidence_without_paid_reconciliation(
    tmp_path: Path,
):
    inputs, provider, _, binding, request = _qualification_execution(tmp_path)
    assert binding is not None and request is not None
    committer = ProductionStateCommitter(
        tmp_path,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    attempt_id = "jimeng-qualification-unverified-not-submitted"
    service.start(attempt_id=attempt_id, request=request, execution_binding=binding)
    experience = record_attempt_evaluation(committer=committer, attempt_id=attempt_id)
    evidence = experience.evidence[-1]
    assert evidence.outcome == "not_submitted"
    committer.close_unsubmitted_video_generation(
        attempt_id=attempt_id,
        expected_manifest_revision=committer._read_manifest().manifest_revision,
        actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
        reason="expired_execution_window",
    )
    target = next(
        item for item in binding.inputs.candidates
        if item.candidate_id == binding.decision.selected_candidate_id
    )
    with pytest.raises(AiVideoError, match="exact closed known-no-effect attempt"):
        committer.record_runtime_repair_authorization(
            attempt_id=attempt_id,
            evidence_hash=evidence.evidence_hash,
            repair_basis="Unsubmitted preparation without paid reconciliation is not a paid retarget.",
            actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
            paid_no_effect_retarget=PaidNoEffectRetarget(
                submit_receipt_fingerprint="0" * 64,
                target_scope_hash=target.scope_hash,
            ),
        )
    attempt = committer._video_attempt(committer._read_manifest(), attempt_id)
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.runtime_repairs == ()


@pytest.mark.parametrize(("ceiling", "used"), ((4, 3), (3, 1)))
def test_qualification_second_recovery_rejects_ceiling_above_three_or_reset_count(
    tmp_path: Path,
    ceiling: int,
    used: int,
):
    (
        inputs,
        provider,
        base,
        _,
        _,
        _,
        _,
        first_experience,
        second_experience,
        grants,
    ) = _two_failed_paid_qualification(tmp_path)
    evidence = (*first_experience.evidence, *second_experience.evidence)
    latest = second_experience.evidence[-1]
    with pytest.raises(
        ValidationError,
        match="qualification execution binding exceeds its bounded remote trial scope",
    ):
        _qualification_binding(
            inputs,
            provider,
            base,
            paid_submit_ceiling=ceiling,
            paid_submits_used=used,
            evidence=evidence,
            latest_attempt_hash=latest.evidence_hash,
            experiences=(first_experience, second_experience),
            runtime_repairs=grants,
            lifecycle_updates={
                "generation_id": f"jimeng-qualification-invalid-{ceiling}-{used}",
                "output_asset_id": f"jimeng-qualification-invalid-video-{ceiling}-{used}",
            },
        )


def test_qualification_paid_no_effect_extension_authorizes_only_fourth_submit(
    tmp_path: Path,
):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        first_attempt_id,
        second_attempt_id,
        third_attempt_id,
        first_experience,
        second_experience,
        third_experience,
        third_binding,
        third_receipt,
    ) = _three_failed_paid_qualification(tmp_path)
    latest = third_experience.evidence[-1]
    experiences = committer.read_generation_experiences()
    experiences = tuple(
        experience
        for experience in experiences
        if any(item.shot_id == latest.shot_id for item in experience.evidence)
    )
    evidence = tuple(
        item
        for experience in experiences
        for item in experience.evidence
        if item.shot_id == latest.shot_id
    )
    assert [item.outcome for item in evidence] == [
        "runtime_failure", "not_submitted", "unknown_outcome",
        "not_submitted",
    ]
    manifest = committer._read_manifest()
    target = next(
        item for item in third_binding.inputs.candidates
        if item.candidate_id == third_binding.decision.selected_candidate_id
    )
    actor = ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex")
    retarget = PaidNoEffectRetarget(
        submit_receipt_fingerprint=third_receipt.submit_receipt_fingerprint,
        target_scope_hash=target.scope_hash,
    )

    with pytest.raises(AiVideoError, match="budget is exhausted"):
        committer.record_runtime_repair_authorization(
            attempt_id=third_attempt_id,
            evidence_hash=latest.evidence_hash,
            repair_basis="No fourth attempt without the explicit third-recovery extension.",
            actor=actor,
            paid_no_effect_retarget=retarget,
        )

    def extension(**updates):
        values = {
            "task_id": third_binding.inputs.limits.task_id,
            "shot_id": third_binding.context.target_shot_id,
            "failed_binding_hash": third_binding.binding_hash,
            "expected_manifest_revision": manifest.manifest_revision,
            "authorization_receipt_id": "authorized-jimeng-third-no-effect-recovery",
        }
        values.update(updates)
        return PaidNoEffectRepairExtension(**values)

    invalid_extensions = (
        extension(failed_binding_hash="0" * 64),
        extension(task_id="another-task"),
        extension(expected_manifest_revision=manifest.manifest_revision + 1),
    )
    for invalid in invalid_extensions:
        with pytest.raises(AiVideoError):
            committer.record_runtime_repair_authorization(
                attempt_id=third_attempt_id,
                evidence_hash=latest.evidence_hash,
                repair_basis="Incorrect extension identity must remain blocked.",
                actor=actor,
                paid_no_effect_retarget=retarget,
                paid_no_effect_extension=invalid,
            )

    authorized = extension()
    pointer = committer.record_runtime_repair_authorization(
        attempt_id=third_attempt_id,
        evidence_hash=latest.evidence_hash,
        repair_basis="The exact native benefit selection is fixed before one final bounded submit.",
        actor=actor,
        paid_no_effect_retarget=retarget,
        paid_no_effect_extension=authorized,
    )
    authorization = committer._reopen_runtime_repair_authorization(pointer)
    assert authorization.schema_version == "runtime-repair/6"
    assert authorization.paid_no_effect_extension == authorized
    assert MAX_RUNTIME_REPAIRS_PER_SHOT == 2

    grants = []
    for attempt_id in (first_attempt_id, second_attempt_id, third_attempt_id):
        attempt = committer._video_attempt(committer._read_manifest(), attempt_id)
        assert attempt.video_generation_state is not None
        grants.extend(
            RuntimeRepairGrant(
                authorization=committer._reopen_runtime_repair_authorization(item),
                consumed=item.consumed,
            )
            for item in attempt.video_generation_state.runtime_repairs
        )
    assert [grant.consumed for grant in grants] == [True, True, False]

    with pytest.raises(
        ValidationError,
        match="qualification execution binding exceeds its bounded remote trial scope",
    ):
        _qualification_binding(
            inputs,
            provider,
            base,
            paid_submit_ceiling=5,
            paid_submits_used=4,
            evidence=evidence,
            latest_attempt_hash=latest.evidence_hash,
            experiences=experiences,
            runtime_repairs=tuple(grants),
            lifecycle_updates={
                "generation_id": "jimeng-qualification-fifth-submit-denied",
                "output_asset_id": "jimeng-qualification-fifth-video-denied",
            },
        )

    fourth_attempt_id = "jimeng-qualification-fourth-submit"
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=4,
        paid_submits_used=3,
        evidence=evidence,
        latest_attempt_hash=latest.evidence_hash,
        experiences=experiences,
        runtime_repairs=tuple(grants),
        lifecycle_updates={
            "generation_id": "jimeng-qualification-fourth-generation",
            "output_asset_id": "jimeng-qualification-fourth-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert decision.runtime_repair == authorization
    assert binding is not None and request is not None
    service.start(attempt_id=fourth_attempt_id, request=request, execution_binding=binding)
    preview = _paid_preview(
        request,
        attempt_id=fourth_attempt_id,
        video_preview=provider.preview(request),
    )
    before_submit = provider.call_counts.submit
    with pytest.raises(AiVideoError, match="submit ceilings cannot expand"):
        service.submit_once(
            attempt_id=fourth_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-fourth-reservation",
        )
    assert provider.call_counts.submit == before_submit == 3
    _extend_paid_submit_quota(
        committer,
        prior_attempt_id=third_attempt_id,
        target_attempt_id=fourth_attempt_id,
        new_ceiling=4,
    )
    provider._scenario = replace(
        provider._scenario,
        submit_outcome="accepted",
        external_effect_id="jimeng-qualification-fourth-effect",
    )
    service.submit_once(
        attempt_id=fourth_attempt_id,
        paid_preview=preview,
        reservation_id="jimeng-qualification-fourth-reservation",
    )
    assert provider.call_counts.submit == 4
    service.refresh_once(attempt_id=fourth_attempt_id)
    committer.settle_paid_provider_reservation(
        attempt_id=fourth_attempt_id,
        actual_cost_microunits=preview.estimated_cost_upper_bound_microunits,
    )
    service.fetch_once(attempt_id=fourth_attempt_id)
    committer._load_production_project(committer.project_root / "project.yaml")
    manifest = committer._read_manifest()
    fourth = committer._video_attempt(manifest, fourth_attempt_id)
    third = committer._video_attempt(manifest, third_attempt_id)
    assert fourth.paid_provider_state is not None
    assert fourth.paid_provider_state.submit_receipt is not None
    assert (
        committer._reopen_paid_submit(fourth.paid_provider_state.submit_receipt)
        .outcome.value == "accepted"
    )
    assert fourth.video_generation_state is not None
    assert fourth.video_generation_state.phase.value == "validate"
    assert fourth.video_generation_state.candidate_video_asset_ids == ()
    assert third.video_generation_state is not None
    assert third.video_generation_state.runtime_repairs[-1].consumed is True
    assert third_receipt.no_effect_reconciliation is not None


def test_paid_no_effect_extension_rejects_unconsumed_prior_grant(tmp_path: Path):
    (
        _inputs,
        _provider,
        _base,
        committer,
        _service,
        _first_attempt_id,
        second_attempt_id,
        _first_experience,
        second_experience,
        _grants,
    ) = _two_failed_paid_qualification(tmp_path)
    manifest = committer._read_manifest()
    attempt = committer._video_attempt(manifest, second_attempt_id)
    assert attempt.video_generation_state is not None
    binding = committer._reopen_generation_execution_binding(
        attempt.video_generation_state.execution_binding
    )
    from ai_video.production._state_commit_video_runtime_repair import (
        _require_paid_no_effect_repair_extension,
    )

    extension = PaidNoEffectRepairExtension(
        task_id=binding.inputs.limits.task_id,
        shot_id=binding.context.target_shot_id,
        failed_binding_hash=binding.binding_hash,
        expected_manifest_revision=manifest.manifest_revision,
        authorization_receipt_id="must-not-extend-with-unconsumed-predecessor",
    )
    with pytest.raises(AiVideoError, match="both prior grants consumed"):
        _require_paid_no_effect_repair_extension(
            committer,
            manifest,
            attempt,
            second_experience.evidence[-1],
            extension,
            expected_current_revision=True,
            actor=ActorIdentity(actor_id="qualification-test-owner", actor_kind="codex"),
        )


def test_qualification_paid_no_effect_extension_authorizes_only_fifth_submit(
    tmp_path: Path,
):
    (
        inputs,
        provider,
        base,
        committer,
        service,
        prior_attempt_ids,
        experiences,
        evidence,
        failed_binding,
        receipt,
        actor,
        _prior_grants,
    ) = _fourth_failed_paid_qualification(tmp_path)
    attempt_id = prior_attempt_ids[-1]
    failure = evidence[-1]
    assert failure.outcome == "runtime_failure"
    assert [item.outcome for item in evidence] == [
        "runtime_failure", "not_submitted", "unknown_outcome",
        "not_submitted", "runtime_failure",
    ]
    manifest = committer._read_manifest()
    target = next(
        item for item in failed_binding.inputs.candidates
        if item.candidate_id == failed_binding.decision.selected_candidate_id
    )
    extension = PaidNoEffectRepairExtension(
        task_id=failed_binding.inputs.limits.task_id,
        shot_id=failed_binding.context.target_shot_id,
        failed_binding_hash=failed_binding.binding_hash,
        expected_manifest_revision=manifest.manifest_revision,
        ceiling=4,
        authorization_receipt_id="qualification-test-fourth-no-effect-recovery",
    )
    with pytest.raises(AiVideoError):
        committer.record_runtime_repair_authorization(
            attempt_id=attempt_id,
            evidence_hash=failure.evidence_hash,
            repair_basis="A new actor cannot inherit the prior repair chain.",
            actor=ActorIdentity(actor_id="different-qualification-owner", actor_kind="codex"),
            paid_no_effect_retarget=PaidNoEffectRetarget(
                submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
                target_scope_hash=target.scope_hash,
            ),
            paid_no_effect_extension=extension,
        )
    pointer = committer.record_runtime_repair_authorization(
        attempt_id=attempt_id,
        evidence_hash=failure.evidence_hash,
        repair_basis="The exact fourth paid call is proven no-effect before dispatch.",
        actor=actor,
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
            target_scope_hash=target.scope_hash,
        ),
        paid_no_effect_extension=extension,
    )
    authorization = committer._reopen_runtime_repair_authorization(pointer)
    assert authorization.schema_version == "runtime-repair/6"
    assert authorization.paid_no_effect_extension == extension
    assert MAX_RUNTIME_REPAIRS_PER_SHOT == 2

    def registered_grants():
        result = []
        for prior_id in prior_attempt_ids:
            prior = committer._video_attempt(committer._read_manifest(), prior_id)
            assert prior.video_generation_state is not None
            result.extend(
                RuntimeRepairGrant(
                    authorization=committer._reopen_runtime_repair_authorization(item),
                    consumed=item.consumed,
                )
                for item in prior.video_generation_state.runtime_repairs
            )
        return tuple(result)

    grants = registered_grants()
    assert [grant.consumed for grant in grants] == [True, True, True, False]
    assert [grant.authorization.schema_version for grant in grants] == [
        "runtime-repair/3", "runtime-repair/3",
        "runtime-repair/6", "runtime-repair/6",
    ]

    with pytest.raises(ValidationError):
        _qualification_binding(
            inputs,
            provider,
            base,
            paid_submit_ceiling=6,
            paid_submits_used=5,
            evidence=evidence,
            latest_attempt_hash=failure.evidence_hash,
            experiences=experiences,
            runtime_repairs=grants,
            lifecycle_updates={
                "generation_id": "jimeng-qualification-sixth-submit-denied",
                "output_asset_id": "jimeng-qualification-sixth-video-denied",
            },
        )

    missing_prior = (*grants[:2], grants[3])
    _, _, missing_decision, missing_binding, missing_request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=5,
        paid_submits_used=4,
        evidence=evidence,
        latest_attempt_hash=failure.evidence_hash,
        experiences=experiences,
        runtime_repairs=missing_prior,
        lifecycle_updates={
            "generation_id": "jimeng-qualification-fifth-missing-prior-denied",
            "output_asset_id": "jimeng-qualification-fifth-missing-prior-video",
        },
    )
    assert missing_decision.disposition != "GENERATE_ONCE"
    assert missing_binding is None and missing_request is None

    fifth_attempt_id = "jimeng-qualification-fifth-submit"
    _, _, decision, binding, request = _qualification_binding(
        inputs,
        provider,
        base,
        paid_submit_ceiling=5,
        paid_submits_used=4,
        evidence=evidence,
        latest_attempt_hash=failure.evidence_hash,
        experiences=experiences,
        runtime_repairs=grants,
        lifecycle_updates={
            "generation_id": "jimeng-qualification-fifth-generation",
            "output_asset_id": "jimeng-qualification-fifth-video",
        },
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert decision.runtime_repair == authorization
    assert binding is not None and request is not None
    service.start(attempt_id=fifth_attempt_id, request=request, execution_binding=binding)
    preview = _paid_preview(
        request,
        attempt_id=fifth_attempt_id,
        video_preview=provider.preview(request),
    )
    with pytest.raises(AiVideoError, match="submit ceilings cannot expand"):
        service.submit_once(
            attempt_id=fifth_attempt_id,
            paid_preview=preview,
            reservation_id="jimeng-qualification-fifth-reservation",
        )
    assert provider.call_counts.submit == 4
    _extend_paid_submit_quota(
        committer,
        prior_attempt_id=attempt_id,
        target_attempt_id=fifth_attempt_id,
        new_ceiling=5,
    )
    provider._scenario = replace(
        provider._scenario,
        submit_outcome="accepted",
        external_effect_id="jimeng-qualification-fifth-effect",
    )
    service.submit_once(
        attempt_id=fifth_attempt_id,
        paid_preview=preview,
        reservation_id="jimeng-qualification-fifth-reservation",
    )
    assert provider.call_counts.submit == 5
    service.refresh_once(attempt_id=fifth_attempt_id)
    committer.settle_paid_provider_reservation(
        attempt_id=fifth_attempt_id,
        actual_cost_microunits=preview.estimated_cost_upper_bound_microunits,
    )
    service.fetch_once(attempt_id=fifth_attempt_id)
    committer._load_production_project(committer.project_root / "project.yaml")

    manifest = committer._read_manifest()
    fifth = committer._video_attempt(manifest, fifth_attempt_id)
    fourth = committer._video_attempt(manifest, attempt_id)
    assert fifth.paid_provider_state is not None
    assert fifth.paid_provider_state.submit_receipt is not None
    assert (
        committer._reopen_paid_submit(fifth.paid_provider_state.submit_receipt)
        .outcome.value == "accepted"
    )
    assert fifth.video_generation_state is not None
    assert fifth.video_generation_state.phase.value == "validate"
    assert fifth.video_generation_state.candidate_video_asset_ids == ()
    assert fourth.video_generation_state is not None
    assert fourth.video_generation_state.runtime_repairs[-1].consumed is True


def test_consumed_no_effect_grant_closes_old_unknown_without_becoming_reusable():
    from test_production_generation_decision import evidence, setup_decision

    setup = setup_decision()
    unknown = evidence(
        setup,
        outcome="unknown_outcome",
        attempt="reconciled-no-effect-attempt",
        task_id="historical-task",
    )
    closed = evidence(
        setup,
        outcome="not_submitted",
        attempt="reconciled-no-effect-attempt",
        task_id="historical-task",
    )
    media = evidence(setup, attempt="later-media-pass", task_id="historical-task")
    extension = PaidNoEffectRepairExtension(
        task_id=closed.task_id,
        shot_id=closed.shot_id,
        failed_binding_hash="a" * 64,
        expected_manifest_revision=0,
        authorization_receipt_id="reconciled-no-effect-recovery",
        ceiling=3,
    )
    authorization = RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/6",
        attempt_id=closed.attempt_id,
        evidence_hash=closed.evidence_hash,
        repair_basis="The historical UNKNOWN was closed by exact no-effect reconciliation.",
        actor=ActorIdentity(actor_id="historical-qualification-owner", actor_kind="codex"),
        expected_manifest_revision=1,
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint="b" * 64,
            target_scope_hash=setup["inputs"].candidates[0].scope_hash,
        ),
        paid_no_effect_extension=extension,
    )
    inputs = setup["inputs"].model_copy(update={
        "evidence": (unknown, closed, media),
        "latest_attempt_hash": media.evidence_hash,
        "runtime_repairs": (RuntimeRepairGrant(authorization=authorization, consumed=True),),
    })
    from ai_video.production.generation_runtime_repair import (
        effective_latest_generation_evidence,
        is_paid_no_effect_repair_grant_for_evidence,
    )

    consumed_grant = inputs.runtime_repairs[0]
    assert not is_paid_no_effect_repair_grant_for_evidence(consumed_grant, closed)
    assert effective_latest_generation_evidence((unknown, closed), (consumed_grant,)) == unknown

    decision = resolve_generation_decision(
        VideoGenerationResolver(),
        projection=setup["projection"],
        context=setup["context"],
        policy=setup["policy"],
        lifecycle=setup["lifecycle"],
        inputs=inputs,
    )

    assert decision.disposition == "REVIEW_CURRENT_RESULT"
    assert decision.runtime_repair is None
    assert decision.routing is None


@pytest.mark.parametrize(
    ("authorization", "detail"),
    (
        ({"remote_authorized": False}, "lacks task-scoped authorization"),
        ({"budget_authorized": False}, "lacks an accepted budget decision"),
    ),
)
def test_qualification_trial_requires_remote_and_budget_authorization(
    tmp_path: Path,
    authorization: dict[str, bool],
    detail: str,
):
    _, _, decision, binding, request = _qualification_execution(
        tmp_path, **authorization
    )

    assert decision.routing is None
    assert binding is None
    assert request is None
    assert detail in str(decision.rationale)


def test_production_routing_policy_keeps_legacy_serialization():
    identity = RouterPolicyIdentity(
        policy_id="router-policy",
        policy_version="1",
        policy_sha256="a" * 64,
    )
    default_policy = VideoRoutingPolicy(
        identity=identity,
        local_resources_available=False,
        remote_authorized=True,
        budget_authorized=True,
    )
    trial_policy = default_policy.model_copy(
        update={"execution_purpose": "qualification"}
    )

    assert default_policy.execution_purpose == "production"
    assert "execution_purpose" not in default_policy.model_dump(mode="json")
    assert trial_policy.model_dump(mode="json")["execution_purpose"] == "qualification"

