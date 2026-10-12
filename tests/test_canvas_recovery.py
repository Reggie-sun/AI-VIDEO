"""Explicit repair through the shared facade, with canonical failure history."""
import asyncio
from dataclasses import replace
import subprocess

import pytest

from ai_video.canvas_production import CanvasProductionService
from ai_video.production.generation_diagnosis import Intervention
from ai_video.production.generation_evaluation import GenerationObservation
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity
from test_canvas_production import runtime, submit_and_fetch, pass_evaluation
from test_generation_feedback_review import Session


def closed_unsubmitted_canvas(tmp_path):
    from ai_video.production.generation_feedback import record_attempt_evaluation
    service, provider, limits, _ = runtime(tmp_path)
    service.decision_policy = service.decision_policy.model_copy(update={"max_resamples": 0})
    old = service.start(limits=limits)
    experience = record_attempt_evaluation(committer=service.committer, attempt_id=old.attempt_id)
    service.committer.close_unsubmitted_video_generation(attempt_id=old.attempt_id,
        expected_manifest_revision=service._load().manifest.manifest_revision,
        actor=ActorIdentity(actor_id="canvas-test", actor_kind="codex"),
        reason="superseded_before_submit")
    return service, provider, limits, old, experience


def test_closed_unsubmitted_preparation_preserves_history_and_zero_consumption(tmp_path):
    service, provider, limits, old, experience = closed_unsubmitted_canvas(tmp_path)
    history = service.committer.read_generation_experiences()
    prepared = service.prepare_repair(limits=limits)
    assert prepared.execution_binding is not None, prepared.decision
    assert prepared.inputs.limits.paid_submits_used == 0
    assert prepared.inputs.latest_attempt_hash == experience.evidence[-1].evidence_hash
    assert prepared.inputs.experiences == history
    current = service.start_repair(limits=limits)
    assert current.attempt_id != old.attempt_id
    assert current.next_action == "submit"
    assert service.position() == current
    assert service.start_repair(limits=limits) == current
    assert service.committer.read_generation_experiences() == history
    assert provider.call_counts.submit == 0
    reopened = CanvasProductionService(committer=service.committer, packet=service.packet,
        direction=service.direction, targets=service.targets,
        routing_policy=service.routing_policy, decision_policy=service.decision_policy)
    assert reopened.position() == current


def test_closed_unsubmitted_revision_cannot_rename_task(tmp_path):
    service, provider, limits, _, _ = closed_unsubmitted_canvas(tmp_path)
    before = service._load().manifest
    with pytest.raises(Exception, match="predecessor task identity"):
        service.start_repair(limits=limits.model_copy(update={"task_id": "renamed"}))
    assert service._load().manifest == before
    assert provider.call_counts.submit == 0


@pytest.mark.parametrize("damage", ["fork", "closure_metadata"])
def test_unsubmitted_successor_refuses_fork_or_false_closure(tmp_path, damage):
    from ai_video.canvas_recovery import current_canvas_attempt
    service, provider, limits, _, _ = closed_unsubmitted_canvas(tmp_path)
    service.start_repair(limits=limits)
    attempts = service._attempts(service._load(), "one")
    if damage == "fork":
        attempts.append(attempts[-1].model_copy(update={"attempt_id": "forked-unsubmitted"}))
    else:
        attempts[0] = attempts[0].model_copy(update={"error_message": "unverified assertion"})
    with pytest.raises(Exception):
        current_canvas_attempt(service.committer, attempts)
    assert provider.call_counts.submit == 0


def test_registry_only_revision_preserves_creative_input_and_closed_history(tmp_path):
    from ai_video.production.registry import registry_semantic_sha256
    service, provider, limits, old, _ = closed_unsubmitted_canvas(tmp_path)
    previous = service._load()
    record = previous.registry.assets[0].model_copy(update={"usage_license": "updated-explicit-license"})
    registry = previous.registry.model_copy(update={"assets": (record,)})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    service.revise_authoring(attempt_id="registry-only-provenance", registry=registry)
    loaded = service._load()
    assert loaded.registry == registry
    assert loaded.shots == previous.shots
    assert loaded.project.revision == previous.project.revision + 1
    assert next(a for a in loaded.manifest.attempts if a.attempt_id == old.attempt_id) == next(
        a for a in previous.manifest.attempts if a.attempt_id == old.attempt_id)
    assert service.start_repair(limits=limits).next_action == "submit"
    assert provider.call_counts.submit == 0


def failed_canvas(tmp_path, *, mixed=False):
    service, provider, limits, auth = runtime(tmp_path)
    service.decision_policy = service.decision_policy.model_copy(update={"max_resamples": 0})
    if mixed:
        from ai_video.production.hashing import seal_artifact
        from ai_video.production.models import GenerationEvaluationAuthority
        loaded = service._load()
        policy = seal_artifact(loaded.qa_policy.model_copy(update={
            "revision": loaded.qa_policy.revision + 1, "content_hash": "0" * 64,
            "generation_evaluation_authorities": (*loaded.qa_policy.generation_evaluation_authorities,
                GenerationEvaluationAuthority(proof="human", evaluator=loaded.qa_policy.semantic_authorities[0]))}))
        service.committer.activate_qa_policy(policy, attempt_id="scripted-mixed-proof-policy",
            expected_manifest_revision=loaded.manifest.manifest_revision)
    position = submit_and_fetch(service, provider, limits, auth)

    def fail(review):
        source = pass_evaluation(review)[0]
        failed = source.model_copy(update={"observations": (
            GenerationObservation(requirement_id="duration", verdict="FAIL",
                observation="Scripted evaluator rejects this exact raw duration."),)})
        if not mixed:
            return (failed,)
        gap = source.model_copy(update={"observations": (
            GenerationObservation(requirement_id="duration", verdict="NOT_EVALUATED",
                observation="Scripted technical observation is irrecoverable."),)})
        return (gap, failed.model_copy(update={"proof": "human"}))

    asyncio.run(service.evaluate(session=Session(), adjudicate=fail))
    experience = service.committer.read_generation_experiences()[-1]
    provider.prompt_text = "Walk into the road with continuous motion through the endpoint."
    intervention = Intervention(intervention_id="canvas-prompt-repair",
        candidate_id=experience.candidate.candidate_id, purpose="production_repair",
        disposition="GENERATE_ONCE", closes=("duration",),
        support=(experience.evidence[-1].evidence_hash,), changed_variables=("prompt_text", "seed"),
        held_constants=(), uncontrolled_variables=(), regression_risks=("Recheck all new media.",),
        hypothesis="Test one explicit native expression change against the duration failure.",
        confidence_basis="Exact retained failure; this scripted test proves control flow only.",
        improvement_prediction="New duration observation passes.",
        falsification_prediction="New duration observation fails.",
        insufficient_evidence_condition="New media lacks exact evaluation.",
        semantic_variable_hashes=(("prompt_text", canonical_sha256({"value": provider.prompt_text})),))
    return service, provider, limits, position, experience, intervention


def close_failure(service, position, *, mixed=False):
    loaded = service._load()
    attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == position.attempt_id)
    close = service.committer.abandon_video_generation if mixed else service.committer.reject_video_generation
    extra = {"reason": "Scripted known failure retains an irrecoverable technical proof gap."} if mixed else {}
    return close(attempt_id=position.attempt_id,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
        actor=ActorIdentity(actor_id="canvas-test", actor_kind="codex"), **extra)


def test_explicit_repair_preserves_history_and_reopens_unique_successor(tmp_path):
    service, provider, limits, old, experience, intervention = failed_canvas(tmp_path)
    close_failure(service, old)
    history = service.committer.read_generation_experiences()
    prepared = service.prepare_repair(limits=limits, interventions=(intervention,))
    assert prepared.execution_binding is not None, (prepared.decision, prepared.compilation)
    assert prepared.inputs.limits.paid_submits_used == 1
    assert prepared.inputs.experiences == history
    assert prepared.inputs.latest_attempt_hash == experience.evidence[-1].evidence_hash
    current = service.start_repair(limits=limits, interventions=(intervention,))
    assert current.attempt_id != old.attempt_id
    assert current.next_action == "submit"
    assert service.committer.read_generation_experiences() == history
    reopened = CanvasProductionService(committer=service.committer, packet=service.packet,
        direction=service.direction, targets=service.targets,
        routing_policy=service.routing_policy, decision_policy=service.decision_policy)
    assert reopened.position() == current
    assert reopened.start_repair(limits=limits, interventions=(intervention,)) == current
    assert provider.call_counts.submit == 1
    attempts = reopened._attempts(reopened._load(), "one")
    assert len(attempts) == 2
    assert attempts[0].video_generation_state.quality_rejection is not None
    assert attempts[1].video_generation_state.execution_binding is not None
    with pytest.raises(Exception, match="durable next action"):
        reopened.execute(action="validate")

    from production_e2e_support import require_audio_toolchain
    from test_production_video import _paid_preview, _paid_authorization
    tools = require_audio_toolchain()
    media = tmp_path / "repaired-scripted.mp4"
    subprocess.run([str(tools.ffmpeg_path), "-nostdin", "-v", "error", "-y", "-f", "lavfi",
        "-i", "color=c=green:s=64x64:r=24:d=1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-threads", "1", str(media)], capture_output=True, check=True)
    provider._artifact_bytes = media.read_bytes()
    provider._scenario = replace(provider._scenario, external_effect_id="canvas-repaired-effect")
    request = service.committer._reopen_video_request(attempts[1].video_generation_state.request)
    preview = _paid_preview(request, attempt_id=current.attempt_id, video_preview=provider.preview(request))
    service.committer._paid_provider_authorizer = lambda value: _paid_authorization(value)
    reopened.execute(action="submit", paid_preview=preview, reservation_id="canvas-repaired-reservation")
    reopened.execute(action="poll")
    service.committer.settle_paid_provider_reservation(attempt_id=current.attempt_id,
        actual_cost_microunits=1_000_000)
    reopened.execute(action="fetch")
    assert reopened.position().attempt_id == current.attempt_id
    result = asyncio.run(reopened.evaluate(session=Session(), adjudicate=pass_evaluation))
    assert result.all_required_observed_pass
    reopened.execute(action="validate")
    reopened.execute(action="activate")
    assert reopened.position().shot_id == "two"
    assert reopened.position().next_action == "prepare"
    assert provider.call_counts.submit == 2
    assert service.committer.read_generation_experiences()[0] == history[0]


def test_repair_refuses_unclosed_failure_without_new_attempt(tmp_path):
    service, provider, limits, old, _, intervention = failed_canvas(tmp_path)
    before = service._load().manifest
    with pytest.raises(Exception, match="closed quality"):
        service.start_repair(limits=limits, interventions=(intervention,))
    assert service._load().manifest == before
    assert provider.call_counts.submit == 1


def test_repair_budget_exhaustion_retains_closed_result(tmp_path):
    service, provider, limits, old, _, intervention = failed_canvas(tmp_path)
    close_failure(service, old)
    before = service._load().manifest
    limited = limits.model_copy(update={"paid_submit_ceiling": 1})
    result = service.start_repair(limits=limited, interventions=(intervention,))
    assert result.execution_binding is None
    assert result.decision.disposition == "BLOCKED_EXECUTION"
    assert service._load().manifest == before
    assert service.position().next_action == "stop"
    assert provider.call_counts.submit == 1


def test_repair_cannot_rename_task_to_reset_consumption(tmp_path):
    service, provider, limits, old, _, intervention = failed_canvas(tmp_path)
    close_failure(service, old)
    before = service._load().manifest
    with pytest.raises(Exception, match="predecessor task identity"):
        service.start_repair(limits=limits.model_copy(update={"task_id": "renamed-task"}),
            interventions=(intervention,))
    assert service._load().manifest == before
    assert provider.call_counts.submit == 1


def test_abandoned_mixed_result_remains_in_repair_binding(tmp_path):
    service, provider, limits, old, experience, intervention = failed_canvas(tmp_path, mixed=True)
    close_failure(service, old, mixed=True)
    history = service.committer.read_generation_experiences()
    prepared = service.prepare_repair(limits=limits, interventions=(intervention,))
    assert prepared.execution_binding is not None, (prepared.decision, prepared.compilation)
    assert prepared.inputs.abandoned_result.attempt_id == old.attempt_id
    assert prepared.inputs.abandoned_result.diagnosis.failure_classes == ("EVIDENCE_GAP", "QUALITY_FAILURE")
    assert prepared.inputs.experiences == history
    assert prepared.inputs.latest_attempt_hash == experience.evidence[-1].evidence_hash
    assert prepared.inputs.limits.paid_submits_used == 1
    current = service.start_repair(limits=limits, interventions=(intervention,))
    assert current.next_action == "submit"
    assert service.position() == current
    assert service.committer.read_generation_experiences() == history
    assert provider.call_counts.submit == 1


def test_unknown_cannot_enter_repair_path(tmp_path):
    from ai_video.errors import AiVideoError
    from test_production_video import _paid_preview, _paid_authorization
    service, provider, limits, auth = runtime(tmp_path)
    provider._scenario = replace(provider._scenario, submit_outcome="outcome_unknown")
    current = service.start(limits=limits)
    _, state = service._service(current.attempt_id)._state(current.attempt_id)
    request = service.committer._reopen_video_request(state.request)
    preview = _paid_preview(request, attempt_id=current.attempt_id, video_preview=provider.preview(request))
    auth[preview.preview_fingerprint] = _paid_authorization(preview)
    with pytest.raises(AiVideoError):
        service.execute(action="submit", paid_preview=preview, reservation_id="unknown-repair-source")
    before = service._load().manifest
    with pytest.raises(AiVideoError, match="closed quality"):
        service.start_repair(limits=limits, interventions=(object(),))
    assert service._load().manifest == before
    assert provider.call_counts.submit == 1


def test_forked_successors_remain_ambiguous(tmp_path):
    from ai_video.canvas_recovery import current_canvas_attempt
    service, _, limits, old, _, intervention = failed_canvas(tmp_path)
    close_failure(service, old)
    service.start_repair(limits=limits, interventions=(intervention,))
    attempts = service._attempts(service._load(), "one")
    # Exercise the read-only selector on a fork view; do not persist invented state.
    sibling = attempts[1].model_copy(update={"attempt_id": "other-successor"})
    with pytest.raises(ValueError, match="Multiple attempts"):
        current_canvas_attempt(service.committer, (*attempts, sibling))


def rejected_canvas(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_feedback import record_attempt_evaluation
    from test_production_video import _paid_preview, _paid_authorization
    service, provider, limits, auth = runtime(tmp_path)
    provider._scenario = replace(provider._scenario, submit_outcome="rejected")
    old = service.start(limits=limits)
    state = service._service(old.attempt_id)._state(old.attempt_id)[1]
    request = service.committer._reopen_video_request(state.request)
    preview = _paid_preview(request, attempt_id=old.attempt_id, video_preview=provider.preview(request))
    auth[preview.preview_fingerprint] = _paid_authorization(preview)
    with pytest.raises(AiVideoError):
        service.execute(action="submit", paid_preview=preview, reservation_id="rejected-source")
    experience = record_attempt_evaluation(committer=service.committer, attempt_id=old.attempt_id)
    assert experience.evidence[-1].outcome == "runtime_failure"
    assert service.position().next_action == "stop"
    return service, provider, limits, auth, old, experience


def test_paid_no_effect_stays_blocked_without_explicit_runtime_grant(tmp_path):
    service, provider, limits, _, old, experience = rejected_canvas(tmp_path)
    before = service._load().manifest
    blocked = service.prepare_repair(limits=limits)
    assert blocked.decision.disposition == "RUNTIME_FAILURE"
    assert blocked.inputs.latest_attempt_hash == experience.evidence[-1].evidence_hash
    assert blocked.inputs.limits.paid_submits_used == 1
    assert service.start_repair(limits=limits).execution_binding is None
    assert service._load().manifest == before
    assert service.position().attempt_id == old.attempt_id
    assert provider.call_counts.submit == 1


def test_explicit_paid_retarget_preserves_history_and_consumes_grant_atomically(tmp_path):
    import hashlib
    from pathlib import Path
    from ai_video.production.generation_runtime_repair import PaidNoEffectRetarget
    from ai_video.production.generation_feedback import RegisteredGenerationTarget
    from ai_video.production.state_commit import PreparedArtifact
    from test_production_video import _paid_preview, _paid_authorization
    service, provider, limits, auth, old, experience = rejected_canvas(tmp_path)
    target = service.targets[0]
    payload = b'{"scripted-profile":"replacement"}'
    sha = hashlib.sha256(payload).hexdigest()
    profile = target.profile.model_copy(update={"profile_sha256": sha,
        "profile_path": Path(f"provider-profiles/{sha}.json")})
    service.committer._write_immutable_artifact(PreparedArtifact(profile.profile_path, payload, sha),
        attempt_id="scripted-replacement-profile")
    service.targets = (RegisteredGenerationTarget(provider, profile, target.compiler_contract,
        target.output_requirement),)
    blocked = service.prepare_repair(limits=limits)
    replacement = blocked.inputs.candidates[0]
    assert replacement.scope_hash != experience.candidate.scope_hash
    assert replacement.recipe.seed == experience.candidate.recipe.seed
    failed = next(a for a in service._load().manifest.attempts if a.attempt_id == old.attempt_id)
    receipt = service.committer._reopen_paid_submit(failed.paid_provider_state.submit_receipt)
    scope = PaidNoEffectRetarget(submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
        target_scope_hash=replacement.scope_hash)
    args = dict(attempt_id=old.attempt_id, repair_basis="scripted same-provider model/profile recovery",
        actor=ActorIdentity(actor_id="canvas-test", actor_kind="codex"), paid_no_effect_retarget=scope)
    pointer = service.committer.record_runtime_repair_authorization(**args)
    assert service.committer.record_runtime_repair_authorization(**args) == pointer
    history = service.committer.read_generation_experiences()
    current = service.start_repair(limits=limits)
    assert hasattr(current, "next_action"), current.decision.rationale
    assert current.next_action == "submit" and current.attempt_id != old.attempt_id
    assert service.position() == current
    assert service.start_repair(limits=limits) == current
    assert provider.call_counts.submit == 1
    assert service.committer.read_generation_experiences() == history
    assert service._load().manifest.attempts[-1].video_generation_state.execution_binding is not None
    provider._scenario = replace(provider._scenario, submit_outcome="accepted",
        external_effect_id="paid-replacement-effect")
    state = service._service(current.attempt_id)._state(current.attempt_id)[1]
    request = service.committer._reopen_video_request(state.request)
    preview = _paid_preview(request, attempt_id=current.attempt_id, video_preview=provider.preview(request))
    auth[preview.preview_fingerprint] = _paid_authorization(preview)
    service.execute(action="submit", paid_preview=preview, reservation_id="replacement-reservation")
    failed = next(a for a in service._load().manifest.attempts if a.attempt_id == old.attempt_id)
    assert failed.video_generation_state.runtime_repairs[0].consumed
    assert provider.call_counts.submit == 2
    assert service.position().next_action == "poll"
    assert service.committer.read_generation_experiences() == history


def test_paid_retarget_rejects_wrong_receipt_without_mutation(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_runtime_repair import PaidNoEffectRetarget
    service, provider, _, _, old, experience = rejected_canvas(tmp_path)
    before = service._load().manifest
    with pytest.raises(AiVideoError, match="exact failed receipt"):
        service.committer.record_runtime_repair_authorization(attempt_id=old.attempt_id,
            repair_basis="scripted mismatch", actor=ActorIdentity(actor_id="canvas-test", actor_kind="codex"),
            paid_no_effect_retarget=PaidNoEffectRetarget(submit_receipt_fingerprint="d" * 64,
                target_scope_hash=experience.candidate.scope_hash))
    assert service._load().manifest == before
    assert provider.call_counts.submit == 1
