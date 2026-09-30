"""Explicit additional submit authorization on the original durable task."""
from datetime import timedelta
from dataclasses import replace
from datetime import timedelta

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity
from ai_video.production.project import load_production_project
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import VideoGenerationRequest
from ai_video.production.video_generation import VideoGenerationService
from test_production_paid_budget_extension import _bytes, _entry as _money_entry
import test_production_generated_video_e2e as e2e


NEXT = "quota-next"


def _goal(version):
    from ai_video.production.final_output_contracts import (
        FinalOutputContract,
        FinalOutputRequirement,
    )

    return FinalOutputContract(
        goal_id="fixture-same-shot-goal",
        goal_version=version,
        user_goal="The fetched shot remains a usable exact candidate.",
        requirements=(
            FinalOutputRequirement(
                requirement_id="whole-shot",
                observable="The whole shot remains usable.",
                proof="evaluator",
            ),
        ),
    )


def _activate_goal(writer, *, goal, acceptance=None, attempt_id):
    from ai_video.production.hashing import canonical_sha256, seal_artifact
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy

    loaded = load_production_project(writer.project_root / "project.yaml")
    policy = loaded.qa_policy
    assert policy is not None
    if acceptance is not None:
        payload = dict(acceptance.profile_payload)
        payload.pop("content_hash")
        payload["profile_version"] = acceptance.profile_version
        digest = canonical_sha256(payload)
        acceptance = DomainAcceptancePolicy.model_validate({
            **acceptance.model_dump(mode="python"),
            "profile_content_hash": digest,
            "profile_payload": {**payload, "content_hash": digest},
        })
    from ai_video.production.models import GenerationEvaluationAuthority

    updated = policy.model_copy(update={
        "revision": policy.revision + 1,
        "content_hash": "0" * 64,
        "policy_version": f"goal-{goal.goal_version}",
        "final_output": goal,
        **({"generation_acceptance": acceptance} if acceptance is not None else {}),
        **({"generation_evaluation_authorities": (
            GenerationEvaluationAuthority(
                evaluator=policy.semantic_authorities[0], proof="technical"
            ),
        )} if acceptance is not None else {}),
    })
    writer.activate_qa_policy(
        seal_artifact(updated),
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id=attempt_id,
    )
    return load_production_project(writer.project_root / "project.yaml")


def _new_goal_pending(
    tmp_path, *, before_target=None, evaluation_verdict="NOT_EVALUATED",
    stop_after_goal=False,
):
    """One real paid fetch/NE history followed by a same-shot goal revision."""
    from ai_video.production.generation_evaluation import (
        GenerationEvaluationSource,
        GenerationObservation,
        _seal_presentation_recording,
    )
    from ai_video.production.generation_evaluation_criteria import (
        PresentationEvidence,
        evaluation_items,
    )
    from ai_video.production.generation_feedback import record_attempt_evaluation
    from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.paid_provider import PaidProviderAuthorizationDecision

    from test_requirement_semantics import marked_policy, semantic_rule

    _, provider, resolved, _, _, bootstrap = e2e._runtime(tmp_path)
    rule = semantic_rule("duration")
    rule.update(
        proof="technical",
        observable="1 seconds",
        tolerance="exact",
        measurement="technical probe",
        intent_paths=["output_need.duration_seconds"],
        native_text=[],
    )
    old_acceptance = marked_policy([rule])
    selected = _activate_goal(
        bootstrap,
        goal=_goal("1"),
        acceptance=old_acceptance,
        attempt_id="goal-v1",
    )
    values = resolved.activation_scope.request.model_dump(
        mode="python", exclude={"request_input_hash"}
    )
    values.update(
        generation_id="quota-goal-prior",
        output_asset_id="quota-goal-prior-video",
        base_project=selected.manifest.active_project,
        base_registry=selected.manifest.active_registry,
        base_dependency_graph=selected.manifest.active_dependency_graph,
    )
    prior_prepared = e2e.prepare_generation_execution(
        project=selected,
        provider=provider,
        request=provider.resolve(VideoGenerationRequest.create(**values)),
        task_id="quota-new-goal-fixture",
        compiler_id="generated-video-e2e-fixture",
        compiler_version="1",
    )
    prior_recipe = GenerationRecipe.model_validate({
        **prior_prepared.binding.inputs.candidates[0].recipe.model_dump(mode="python"),
        "rubric_hash": old_acceptance.profile_content_hash,
        "acceptance_policy": old_acceptance,
        "expressions": tuple(
            RequirementExpression.model_validate(rule)
            for rule in old_acceptance.profile_payload["generation_requirements"]
        ),
    })
    prior_candidate = prior_prepared.binding.inputs.candidates[0].model_copy(update={
        "recipe": prior_recipe,
        "final_output_goal": _goal("1"),
    })
    prior_inputs = prior_prepared.binding.inputs.model_copy(
        update={
            "candidates": (prior_candidate,),
            "rubric_hash": old_acceptance.profile_content_hash,
        }
    )
    prior_decision = VideoGenerationResolver().resolve_requirement(
        projection=prior_prepared.binding.projection,
        context=prior_prepared.binding.context,
        policy=prior_prepared.binding.policy,
        lifecycle=prior_prepared.binding.lifecycle,
        inputs=prior_inputs,
    )
    prior_compiled = provider.compile_request(
        prior_decision.routing.provider_bound_request,
        prior_prepared.binding.projection.requirement,
    )
    prior_request = provider.resolve(prior_compiled.request)
    prior_binding = GenerationDecisionExecutionBinding.create(
        projection=prior_prepared.binding.projection,
        context=prior_prepared.binding.context,
        policy=prior_prepared.binding.policy,
        lifecycle=prior_prepared.binding.lifecycle,
        inputs=prior_inputs,
        decision=prior_decision,
        compiled_request=prior_request,
    )
    prior_preview = e2e._paid_preview(
        prior_request,
        attempt_id="quota-goal-prior",
        video_preview=provider.preview(prior_request),
    )
    prior_authorization = e2e._paid_authorization(prior_preview)
    prior_authorization_values = prior_authorization.model_dump(
        mode="python", exclude={"authorization_fingerprint"}
    )
    prior_authorization_values["project_budget_ceiling_microunits"] = 2_000_000
    prior_authorization = PaidProviderAuthorizationDecision.create(
        **prior_authorization_values
    )
    writer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda exact: (
            prior_authorization if exact == prior_preview else None
        ),
        paid_provider_clock=lambda: prior_authorization.issued_at,
    )
    service = VideoGenerationService(committer=writer, provider=provider)
    service.start(
        attempt_id="quota-goal-prior",
        request=prior_request,
        execution_binding=prior_binding,
    )
    provider._scenario = replace(
        provider._scenario, status_events=(e2e.VideoTaskState.SUCCEEDED,)
    )
    service.submit_once(
        attempt_id="quota-goal-prior",
        paid_preview=prior_preview,
        reservation_id="quota-goal-prior-reservation",
    )
    service.refresh_once(attempt_id="quota-goal-prior")
    service.fetch_once(attempt_id="quota-goal-prior")
    selected = load_production_project(tmp_path / "project.yaml")
    prior = next(item for item in selected.manifest.attempts if item.attempt_id == "quota-goal-prior")
    state = prior.video_generation_state
    assert state is not None and state.fetch_receipt is not None
    fetched = writer._reopen_video_fetch(state.fetch_receipt)
    candidate = prior_binding.inputs.candidates[0]
    items = evaluation_items(
        acceptance=old_acceptance,
        qa_policy_content_hash=selected.qa_policy.content_hash,
        request_hash=prior_request.request_input_hash,
        artifact_sha256=fetched.artifact_sha256,
        size_bytes=fetched.size_bytes,
    )
    assert len(items) == 1
    item = items[0]
    observation = GenerationObservation(
        requirement_id=item.requirement_id,
        verdict=evaluation_verdict,
        observation="Exact fixture evaluator has no conclusive quality verdict.",
        evaluation_item_hash=item.evaluation_item_hash,
        question_text=item.question_text,
        presentation_ref="fixture/goal-v1/presentation",
        answer_ref="fixture/goal-v1/answer",
    )
    import json
    source = GenerationEvaluationSource(
        schema_version="generation-evaluation/2",
        request_hash=prior_request.request_input_hash,
        artifact_sha256=fetched.artifact_sha256,
        size_bytes=fetched.size_bytes,
        rubric_hash=candidate.recipe.rubric_hash,
        qa_policy_content_hash=selected.qa_policy.content_hash,
        qa_policy_snapshot=selected.qa_policy,
        evaluator=selected.qa_policy.semantic_authorities[0],
        proof="technical",
        observations=(observation,),
        presentation_evidence=PresentationEvidence(
            namespace="controlled-evaluator/1",
            interaction_ref="fixture/goal-v1",
            presentation_ref=observation.presentation_ref,
            answer_ref=observation.answer_ref,
            event_order=("presentation", "answer"),
            actor_name=selected.qa_policy.semantic_authorities[0].name,
            actor_version=selected.qa_policy.semantic_authorities[0].version,
            items=items,
            answers_json=json.dumps({
                "observations": [observation.model_dump(mode="json")],
                "advisory_observations": [],
                "unresolved_quality_observations": [],
            }),
        ),
    )
    experience = record_attempt_evaluation(
        committer=writer,
        attempt_id="quota-goal-prior",
        evaluation_sources=(source,),
        presentation_proof=_seal_presentation_recording(
            attempt_id="quota-goal-prior", sources=(source,)
        ),
    )
    selected = load_production_project(tmp_path / "project.yaml")
    prior = next(
        item for item in selected.manifest.attempts
        if item.attempt_id == "quota-goal-prior"
    )
    old_acceptance = selected.qa_policy.selected_generation_acceptance()
    assert old_acceptance is not None
    payload = dict(old_acceptance.profile_payload)
    payload.pop("content_hash")
    payload["profile_version"] = "3"
    next_acceptance = DomainAcceptancePolicy.model_validate({
        **old_acceptance.model_dump(mode="python"),
        "profile_version": "3",
        "profile_content_hash": canonical_sha256(payload),
        "profile_payload": {**payload, "content_hash": canonical_sha256(payload)},
    })
    selected = _activate_goal(
        writer,
        goal=_goal("2"),
        acceptance=next_acceptance,
        attempt_id="goal-v2",
    )
    if stop_after_goal:
        return writer, selected, prior, experience, source
    if before_target is not None:
        before_target(writer, selected, prior)
        selected = load_production_project(tmp_path / "project.yaml")
    target_values = prior_request.activation_scope.request.model_dump(
        mode="python", exclude={"request_input_hash"}
    )
    target_values.update(
        generation_id=NEXT,
        output_asset_id="quota-next-goal-video",
        base_project=selected.manifest.active_project,
        base_registry=selected.manifest.active_registry,
        base_dependency_graph=selected.manifest.active_dependency_graph,
    )
    fresh = e2e.prepare_generation_execution(
        project=selected,
        provider=provider,
        request=provider.resolve(VideoGenerationRequest.create(**target_values)),
        task_id="quota-new-goal-fixture",
        compiler_id="generated-video-e2e-fixture",
        compiler_version="1",
    )
    fresh_candidate = fresh.binding.inputs.candidates[0]
    recipe = GenerationRecipe.model_validate({
        **fresh_candidate.recipe.model_dump(mode="python"),
        "rubric_hash": next_acceptance.profile_content_hash,
        "acceptance_policy": next_acceptance,
        "expressions": tuple(
            RequirementExpression.model_validate(rule)
            for rule in next_acceptance.profile_payload["generation_requirements"]
        ),
    })
    candidate = fresh_candidate.model_copy(update={
        "recipe": recipe,
        "final_output_goal": _goal("2"),
    })
    limits = fresh.binding.inputs.limits.model_copy(update={
        "paid_submit_ceiling": 2,
        "paid_submits_used": 1,
    })
    inputs = fresh.binding.inputs.model_copy(update={
        "candidates": (candidate,),
        "rubric_hash": recipe.rubric_hash,
        "limits": limits,
        "evidence": experience.evidence,
        "experiences": (experience,),
        "historical_recipes": (candidate.model_copy(update={
            "recipe": prior_binding.inputs.candidates[0].recipe,
            "final_output_goal": _goal("1"),
        }),),
        "latest_attempt_hash": experience.evidence[0].evidence_hash,
        "baseline_request": prior_request.activation_scope.request,
    })
    assert inputs.policy.version == "3"
    assert experience.evidence[0].rubric_hash != inputs.rubric_hash
    assert inputs.historical_recipes[0].scope_hash == experience.evidence[0].recipe_scope_hash
    assert inputs.historical_recipes[0].final_output_goal != candidate.final_output_goal
    decision = VideoGenerationResolver().resolve_requirement(
        projection=fresh.binding.projection,
        context=fresh.binding.context,
        policy=fresh.binding.policy,
        lifecycle=fresh.binding.lifecycle,
        inputs=inputs,
    )
    assert decision.disposition == "GENERATE_ONCE" and decision.intervention is None, (
        decision.rationale,
        decision.diagnosis,
    )
    compiled = provider.compile_request(
        decision.routing.provider_bound_request, fresh.binding.projection.requirement
    )
    target_request = provider.resolve(compiled.request)
    target_binding = GenerationDecisionExecutionBinding.create(
        projection=fresh.binding.projection,
        context=fresh.binding.context,
        policy=fresh.binding.policy,
        lifecycle=fresh.binding.lifecycle,
        inputs=inputs,
        decision=decision,
        compiled_request=target_request,
    )
    target_preview = e2e._paid_preview(
        target_request,
        attempt_id=NEXT,
        video_preview=provider.preview(target_request),
    )
    target_authorization = e2e._paid_authorization(target_preview)
    authorization_values = target_authorization.model_dump(
        mode="python", exclude={"authorization_fingerprint"}
    )
    authorization_values["project_budget_ceiling_microunits"] = 2_000_000
    target_authorization = PaidProviderAuthorizationDecision.create(**authorization_values)
    writer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda exact: (
            target_authorization if exact == target_preview else None
        ),
        paid_provider_clock=lambda: target_authorization.issued_at,
    )
    service = VideoGenerationService(committer=writer, provider=provider)
    service.start(attempt_id=NEXT, request=target_request, execution_binding=target_binding)
    provider._scenario = replace(provider._scenario, external_effect_id="quota-goal-next-effect")
    return writer, service, provider, target_preview, prior, experience


def _pending(tmp_path, *, used=1, local_batch_limit=1):
    _, provider, resolved, committer = e2e._reach_fetch(tmp_path, activate_second_shot=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_and_activate(attempt_id=e2e.ATTEMPT_ID)
    selected = load_production_project(tmp_path / "project.yaml")
    base = committer._reopen_paid_budget(selected.manifest.active_paid_provider_budget)
    money = _money_entry(selected.manifest, selected.manifest.active_paid_provider_budget, base,
                         now=committer._paid_provider_clock())
    committer.extend_paid_provider_budget(money)
    selected = load_production_project(tmp_path / "project.yaml")
    prior = next(a for a in selected.manifest.attempts if a.attempt_id == e2e.ATTEMPT_ID)
    prior_binding = committer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    values = resolved.activation_scope.request.model_dump(mode="python", exclude={"request_input_hash"})
    shot = selected.shots[1]
    values.update(generation_id=NEXT, output_asset_id="quota-next-video",
                  target_shot_id=shot.shot_id, target_shot_revision=shot.revision,
                  target_shot_content_hash=shot.content_hash, target_asset_role=shot.required_asset_roles[0].role,
                  base_project=selected.manifest.active_project, base_registry=selected.manifest.active_registry,
                  base_dependency_graph=selected.manifest.active_dependency_graph,
                  input_artifact_ids=(shot.artifact_id, selected.registry.assets[0].asset_id))
    prepared = e2e.prepare_generation_execution(project=selected, provider=provider,
        request=provider.resolve(VideoGenerationRequest.create(**values)), task_id=prior_binding.inputs.limits.task_id,
        compiler_id="generated-video-e2e-fixture", compiler_version="1")
    old = prepared.binding
    limits = old.inputs.limits.model_copy(update={"paid_submit_ceiling": 2, "paid_submits_used": used,
                                                "local_batch_limit": local_batch_limit})
    inputs = old.inputs.model_copy(update={"limits": limits})
    decision = VideoGenerationResolver().resolve_requirement(projection=old.projection, context=old.context,
        policy=old.policy, lifecycle=old.lifecycle, inputs=inputs)
    compiled = provider.compile_request(decision.routing.provider_bound_request, old.projection.requirement)
    request = provider.resolve(compiled.request)
    binding = GenerationDecisionExecutionBinding.create(projection=old.projection, context=old.context,
        policy=old.policy, lifecycle=old.lifecycle, inputs=inputs, decision=decision, compiled_request=request)
    preview = e2e._paid_preview(request, attempt_id=NEXT, video_preview=provider.preview(request))
    authorization = e2e._paid_authorization(preview)
    from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
    auth_values = authorization.model_dump(mode="python", exclude={"authorization_fingerprint"})
    auth_values["project_budget_ceiling_microunits"] = money.new_ceiling_microunits
    authorization = PaidProviderAuthorizationDecision.create(**auth_values)
    writer = ProductionStateCommitter(tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: authorization.issued_at,
        video_candidate_preparer=committer._video_candidate_preparer)
    service = VideoGenerationService(committer=writer, provider=provider)
    service.start(attempt_id=NEXT, request=request, execution_binding=binding)
    provider._scenario = replace(provider._scenario, external_effect_id="quota-next-effect")
    return writer, service, preview, prior


def _entry(writer, prior):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    manifest = writer._read_manifest()
    target = next(a for a in manifest.attempts if a.attempt_id == NEXT)
    binding = writer._reopen_generation_execution_binding(target.video_generation_state.execution_binding)
    now = writer._paid_provider_clock()
    return PaidProviderSubmitQuotaExtension.create(
        extension_id="quota-one-more", project_id=manifest.project_id,
        actor=ActorIdentity(actor_id="human-owner", actor_kind="human"), explicit_opt_in=True,
        authorization_receipt_id="user-one-additional-submit", expected_manifest_revision=manifest.manifest_revision,
        base_budget=manifest.active_paid_provider_budget, target_attempt_id=NEXT,
        target_binding=target.video_generation_state.execution_binding, prior_attempt_id=prior.attempt_id,
        prior_binding=prior.video_generation_state.execution_binding, task_id=binding.inputs.limits.task_id,
        old_paid_submit_ceiling=1, new_paid_submit_ceiling=2, issued_at=now, expires_at=now + timedelta(minutes=5))


def test_same_task_extension_resumes_pending_request_and_preserves_durable_used_count(tmp_path):
    writer, service, preview, prior = _pending(tmp_path)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError, match="ceilings cannot expand"):
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    assert _bytes(tmp_path) == before

    entry = _entry(writer, prior)
    old_manifest = writer._read_manifest()
    old_budget = writer._reopen_paid_budget(old_manifest.active_paid_provider_budget)
    amended = writer.extend_paid_provider_submit_quota(entry)
    assert amended.attempts == old_manifest.attempts
    budget = writer._reopen_paid_budget(amended.active_paid_provider_budget)
    assert budget.project_ceiling_microunits == old_budget.project_ceiling_microunits
    assert budget.reservations == old_budget.reservations
    assert budget.ceiling_extensions == old_budget.ceiling_extensions
    assert budget.submit_quota_extensions == (entry,)
    service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    selected = load_production_project(tmp_path / "project.yaml")
    current = writer._reopen_paid_budget(selected.manifest.active_paid_provider_budget)
    assert len(current.reservations) == len(old_budget.reservations) + 1
    assert current.reservations[:-1] == old_budget.reservations
    assert current.submit_quota_extensions == (entry,)
    replay = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: entry.expires_at + timedelta(days=1))
    before = _bytes(tmp_path)
    assert replay.extend_paid_provider_submit_quota(entry) == selected.manifest
    assert _bytes(tmp_path) == before
    with pytest.raises(AiVideoError):
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation-other")
    assert _bytes(tmp_path) == before


def _successor_guard_inputs(writer, *, used=2, ceiling=2, task_id=None):
    manifest = load_production_project(writer.project_root / "project.yaml").manifest
    ancestor = next(item for item in manifest.attempts if item.attempt_id == NEXT)
    state = ancestor.video_generation_state.model_copy(update={"generation_id": "quota-successor"})
    successor = ancestor.model_copy(update={"attempt_id": "quota-successor", "video_generation_state": state})
    binding = writer._reopen_generation_execution_binding(state.execution_binding)
    limits = binding.inputs.limits.model_copy(update={
        "paid_submit_ceiling": ceiling, "paid_submits_used": used,
        **({"task_id": task_id} if task_id is not None else {}),
    })
    binding = binding.model_copy(update={"inputs": binding.inputs.model_copy(update={"limits": limits})})
    return manifest.model_copy(update={"attempts": (*manifest.attempts, successor)}), state, binding


def test_applied_quota_is_inherited_and_original_durable_ceiling_still_stops_successor(tmp_path):
    writer, service, preview, prior = _pending(tmp_path)
    writer.extend_paid_provider_submit_quota(_entry(writer, prior))
    service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    service.refresh_once(attempt_id=NEXT)
    writer.settle_paid_provider_reservation(attempt_id=NEXT, actual_cost_microunits=1_000_000)
    service.fetch_and_activate(attempt_id=NEXT)
    before = _bytes(tmp_path)
    manifest, state, binding = _successor_guard_inputs(writer)
    with pytest.raises(AiVideoError, match="Durable paid submit ceiling is exhausted"):
        writer._require_persisted_generation_limits(manifest, state, binding)
    assert _bytes(tmp_path) == before
    manifest, state, binding = _successor_guard_inputs(writer, used=1)
    with pytest.raises(AiVideoError, match="counters are below durable"):
        writer._require_persisted_generation_limits(manifest, state, binding)
    manifest, state, binding = _successor_guard_inputs(writer, ceiling=3)
    with pytest.raises(AiVideoError, match="ceilings cannot expand"):
        writer._require_persisted_generation_limits(manifest, state, binding)
    from ai_video.production.paid_provider_submit_quota import retained_submit_quota_allows
    ancestor = next(item for item in manifest.attempts if item.attempt_id == NEXT)
    for invalid in (
        ancestor.model_copy(update={"status": type(ancestor.status).OUTCOME_UNKNOWN}),
        ancestor.model_copy(update={"status": type(ancestor.status).RUNNING}),
        ancestor.model_copy(update={"video_generation_state": ancestor.video_generation_state.model_copy(
            update={"fetch_receipt": None})}),
        ancestor.model_copy(update={"paid_provider_state": None}),
    ):
        amended = manifest.model_copy(update={"attempts": tuple(
            invalid if item.attempt_id == NEXT else item for item in manifest.attempts)})
        assert not retained_submit_quota_allows(
            committer=writer, manifest=amended, state=state,
            current_limits=binding.inputs.limits.model_copy(update={"paid_submit_ceiling": 2}),
            prior_limits=binding.inputs.limits.model_copy(update={"paid_submit_ceiling": 1}),
        )
    assert not retained_submit_quota_allows(
        committer=writer, manifest=manifest, state=state,
        current_limits=binding.inputs.limits.model_copy(update={"task_id": "other-task", "paid_submit_ceiling": 2}),
        prior_limits=binding.inputs.limits.model_copy(update={"paid_submit_ceiling": 1}),
    )


def test_unsubmitted_quota_target_does_not_establish_inherited_cap(tmp_path):
    writer, _, _, prior = _pending(tmp_path)
    writer.extend_paid_provider_submit_quota(_entry(writer, prior))
    before = _bytes(tmp_path)
    manifest, state, binding = _successor_guard_inputs(writer, used=1)
    with pytest.raises(AiVideoError, match="ceilings cannot expand"):
        writer._require_persisted_generation_limits(manifest, state, binding)
    assert _bytes(tmp_path) == before


def test_new_goal_allows_only_fetched_not_evaluated_prior_to_remain_validating(tmp_path):
    writer, service, provider, preview, prior, experience = _new_goal_pending(tmp_path)
    before = writer._read_manifest()
    prior_before = next(item for item in before.attempts if item.attempt_id == prior.attempt_id)
    budget_before = writer._reopen_paid_budget(before.active_paid_provider_budget)
    assert prior_before.paid_provider_state.phase.value == "accepted"
    assert [(reservation.status.value, reservation.actual_cost_microunits)
            for reservation in budget_before.reservations] == [("reserved", None)]
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension

    entry_values = _entry(writer, prior).model_dump(mode="python", exclude={"content_hash"})
    entry_values.update({
        "extension_id": "quota-new-goal-one-more",
        "task_id": "quota-new-goal-fixture",
        "old_paid_submit_ceiling": 1,
        "new_paid_submit_ceiling": 2,
    })
    entry = PaidProviderSubmitQuotaExtension.create(**entry_values)

    with pytest.raises(AiVideoError, match="ceilings cannot expand"):
        service.submit_once(
            attempt_id=NEXT,
            paid_preview=preview,
            reservation_id="quota-goal-next-reservation",
        )
    amended = writer.extend_paid_provider_submit_quota(entry)
    current_prior = next(item for item in amended.attempts if item.attempt_id == prior.attempt_id)
    assert current_prior == prior_before
    assert current_prior.video_generation_state.generation_experiences[-1].content_hash == canonical_sha256(
        experience.model_dump(mode="json")
    )
    assert writer._reopen_paid_budget(amended.active_paid_provider_budget).reservations == budget_before.reservations

    service.submit_once(
        attempt_id=NEXT,
        paid_preview=preview,
        reservation_id="quota-goal-next-reservation",
    )
    assert provider.call_counts.submit == 2
    reopened = load_production_project(tmp_path / "project.yaml")
    assert next(item for item in reopened.manifest.attempts if item.attempt_id == prior.attempt_id) == prior_before


def test_new_goal_extension_rejects_mismatched_target_binding_without_writes(tmp_path):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension

    writer, _, _, _, prior, _ = _new_goal_pending(tmp_path)
    original = _entry(writer, prior)
    values = original.model_dump(mode="python", exclude={"content_hash"})
    values.update({
        "extension_id": "quota-new-goal-mismatched-target",
        "target_binding": original.target_binding.model_copy(
            update={"file_sha256": "0" * 64}
        ),
    })
    entry = PaidProviderSubmitQuotaExtension.create(**values)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
    assert _bytes(tmp_path) == before


def test_new_goal_prior_requires_snapshot_canonical_criterion_and_complete_ne(tmp_path):
    from ai_video.production.generation_evaluation import validate_generation_evaluation_sources
    from ai_video.production.video_pre_generation import (
        verified_fetched_prior_for_new_goal,
    )

    writer, _, prior, experience, source = _new_goal_pending(
        tmp_path, stop_after_goal=True
    )
    snapshot = source.qa_policy_snapshot
    assert snapshot is not None
    missing_snapshot = source.model_copy(update={"qa_policy_snapshot": None})
    wrong_criterion = source.model_copy(update={
        "observations": (
            source.observations[0].model_copy(
                update={"question_text": "[other] wrong canonical criterion"}
            ),
        ),
    })
    before = _bytes(tmp_path)
    for invalid in (missing_snapshot, wrong_criterion):
        with pytest.raises(ValueError):
            validate_generation_evaluation_sources(
                sources=(invalid,),
                evidence=experience.evidence[0],
                qa_policy=snapshot,
                size_bytes=source.size_bytes,
            )
    assert _bytes(tmp_path) == before

    failed_writer, failed_loaded, failed_prior, _, _ = _new_goal_pending(
        tmp_path / "non-ne", evaluation_verdict="FAIL", stop_after_goal=True
    )
    before = _bytes(tmp_path / "non-ne")
    assert verified_fetched_prior_for_new_goal(
        failed_writer, failed_loaded, failed_prior
    ) is None
    assert _bytes(tmp_path / "non-ne") == before


@pytest.mark.parametrize("field,value", [
    ("project_id", "foreign"), ("task_id", "foreign"),
    ("target_attempt_id", "foreign"), ("prior_attempt_id", "foreign"),
    ("expected_manifest_revision", 999),
])
def test_resealed_wrong_authorization_refuses_without_writes(tmp_path, field, value):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    writer, _, _, prior = _pending(tmp_path)
    values = _entry(writer, prior).model_dump(mode="python", exclude={"content_hash"})
    values[field] = value
    entry = PaidProviderSubmitQuotaExtension.create(**values)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
    assert _bytes(tmp_path) == before


def test_expired_and_missing_opt_in_are_not_authorization(tmp_path):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    writer, _, _, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    expired = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: entry.expires_at)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        expired.extend_paid_provider_submit_quota(entry)
    values = entry.model_dump(mode="python", exclude={"content_hash"})
    values["explicit_opt_in"] = False
    with pytest.raises(ValueError):
        PaidProviderSubmitQuotaExtension.create(**values)
    assert _bytes(tmp_path) == before


@pytest.mark.parametrize("used,local_batch_limit", [(0, 1), (1, 2)])
def test_quota_cannot_reset_counters_or_raise_local_limits(tmp_path, used, local_batch_limit):
    writer, service, preview, prior = _pending(tmp_path, used=used, local_batch_limit=local_batch_limit)
    entry = _entry(writer, prior)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    if used == 0:
        assert _bytes(tmp_path) == before
    else:
        target = next(a for a in writer._read_manifest().attempts if a.attempt_id == NEXT)
        assert target.paid_provider_state is None


def test_quota_base_raw_tamper_blocks_standard_reader_and_replay(tmp_path):
    writer, _, _, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    writer.extend_paid_provider_submit_quota(entry)
    base = tmp_path / entry.base_budget.path
    base.write_bytes(base.read_bytes() + b" ")
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
    assert _bytes(tmp_path) == before


def test_current_reservation_cannot_discard_quota_lineage(tmp_path):
    import hashlib
    from ai_video.production._state_commit_common import _canonical_json_bytes
    from ai_video.production.models import PaidProviderBudgetSnapshotPointer
    from ai_video.production.paid_provider import PaidProviderBudgetSnapshot
    from ai_video.production.paths import canonical_paid_provider_budget_path
    writer, service, preview, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    writer.extend_paid_provider_submit_quota(entry)
    service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    manifest = writer._read_manifest()
    current = writer._reopen_paid_budget(manifest.active_paid_provider_budget)
    values = current.model_dump(mode="python", exclude={"content_hash"})
    values["submit_quota_extensions"] = ()
    forged = PaidProviderBudgetSnapshot.create(**values)
    raw = _canonical_json_bytes(forged)
    pointer = PaidProviderBudgetSnapshotPointer(path=canonical_paid_provider_budget_path(forged.content_hash),
        revision=forged.revision, content_hash=forged.content_hash, file_sha256=hashlib.sha256(raw).hexdigest())
    (tmp_path / pointer.path).write_bytes(raw)
    writer._write_manifest_atomic(manifest.model_copy(update={"active_paid_provider_budget": pointer}))
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("published", [False, True])
def test_quota_publication_fault_replays_exactly_once(tmp_path, monkeypatch, published):
    writer, _, _, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    original_manifest = writer._read_manifest()
    publish = writer._write_manifest_atomic
    def fault(manifest):
        if published:
            publish(manifest)
        raise OSError("quota publication fault")
    monkeypatch.setattr(writer, "_write_manifest_atomic", fault)
    with pytest.raises(OSError, match="quota publication fault"):
        writer.extend_paid_provider_submit_quota(entry)
    monkeypatch.setattr(writer, "_write_manifest_atomic", publish)
    completed = writer.extend_paid_provider_submit_quota(entry)
    assert completed.manifest_revision == original_manifest.manifest_revision + 1
    assert load_production_project(tmp_path / "project.yaml").manifest == completed
    before = _bytes(tmp_path)
    assert writer.extend_paid_provider_submit_quota(entry) == completed
    assert _bytes(tmp_path) == before


def test_new_quota_after_submit_intent_is_rejected(tmp_path):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    writer, _, preview, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    writer.extend_paid_provider_submit_quota(entry)
    writer.record_paid_provider_submit_intent(preview, reservation_id="quota-reservation")
    values = entry.model_dump(mode="python", exclude={"content_hash"})
    manifest = writer._read_manifest()
    values.update(extension_id="another-extension", expected_manifest_revision=manifest.manifest_revision,
                  base_budget=manifest.active_paid_provider_budget)
    new = PaidProviderSubmitQuotaExtension.create(**values)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(new)
    assert _bytes(tmp_path) == before
