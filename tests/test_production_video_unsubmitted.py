"""Canonical zero-effect closure retains task history and an unused ceiling."""

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.generation_feedback import record_attempt_evaluation
from ai_video.production.models import ActorIdentity
from ai_video.production.project import load_production_project
from test_production_paid_budget_extension import _bytes
from test_production_paid_submit_quota import NEXT, _pending, _entry, _successor_guard_inputs


ACTOR = ActorIdentity(actor_id="parent", actor_kind="codex")


def _close(writer, **changes):
    values = dict(attempt_id=NEXT, actor=ACTOR, reason="expired_execution_window",
                  expected_manifest_revision=writer._read_manifest().manifest_revision)
    values.update(changes)
    return writer.close_unsubmitted_video_generation(**values)


def test_close_retains_exact_request_history_budget_and_replays_without_writes(tmp_path):
    writer, _, _, prior = _pending(tmp_path)
    writer.extend_paid_provider_submit_quota(_entry(writer, prior))
    experience = record_attempt_evaluation(committer=writer, attempt_id=NEXT)
    before = load_production_project(tmp_path / "project.yaml").manifest
    closed = _close(writer)
    attempt = next(a for a in closed.attempts if a.attempt_id == NEXT)
    original = next(a for a in before.attempts if a.attempt_id == NEXT)
    assert attempt.status.value == "failed"
    assert attempt.error_code == "video_generation_not_submitted"
    assert attempt.video_generation_state == original.video_generation_state
    assert attempt.paid_provider_state is None
    assert closed.active_paid_provider_budget == before.active_paid_provider_budget
    assert closed.active_project == before.active_project
    assert record_attempt_evaluation(committer=writer, attempt_id=NEXT) == experience
    frozen = _bytes(tmp_path)
    assert _close(writer, expected_manifest_revision=before.manifest_revision) == closed
    assert _bytes(tmp_path) == frozen
    with pytest.raises(AiVideoError):
        _close(writer, reason="superseded_before_submit")
    assert _bytes(tmp_path) == frozen
    manifest, state, binding = _successor_guard_inputs(writer, used=1)
    writer._require_persisted_generation_limits(manifest, state, binding)
    with pytest.raises(AiVideoError, match="ceilings cannot expand"):
        manifest, state, binding = _successor_guard_inputs(writer, used=1, ceiling=3)
        writer._require_persisted_generation_limits(manifest, state, binding)


def test_close_requires_current_revision_and_durable_not_submitted_evidence(tmp_path):
    writer, _, _, _ = _pending(tmp_path)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        _close(writer)
    assert _bytes(tmp_path) == before
    record_attempt_evaluation(committer=writer, attempt_id=NEXT)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        _close(writer, expected_manifest_revision=1)
    assert _bytes(tmp_path) == before


def test_submitted_or_unknown_attempt_cannot_be_relabelled_unsubmitted(tmp_path):
    writer, service, preview, prior = _pending(tmp_path)
    writer.extend_paid_provider_submit_quota(_entry(writer, prior))
    service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        _close(writer)
    assert _bytes(tmp_path) == before


def test_closed_request_can_start_fresh_successor_with_complete_history_and_same_cap(tmp_path):
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.shot_router import VideoGenerationResolver
    from ai_video.production.video import VideoGenerationRequest
    from ai_video.production.video_generation import VideoGenerationService
    import test_production_generated_video_e2e as e2e

    writer, service, _, prior = _pending(tmp_path)
    writer.extend_paid_provider_submit_quota(_entry(writer, prior))
    experience = record_attempt_evaluation(committer=writer, attempt_id=NEXT)
    _close(writer)
    loaded = load_production_project(tmp_path/'project.yaml')
    previous = next(a for a in loaded.manifest.attempts if a.attempt_id==NEXT)
    resolved = writer._reopen_video_request(previous.video_generation_state.request)
    provider = service._provider
    old_binding = writer._reopen_generation_execution_binding(previous.video_generation_state.execution_binding)
    values = resolved.activation_scope.request.model_dump(mode='python',exclude={'request_input_hash'})
    values.update(generation_id='fresh-successor',output_asset_id='fresh-successor-video')
    fresh = e2e.prepare_generation_execution(project=loaded,provider=provider,
        request=provider.resolve(VideoGenerationRequest.create(**values)),
        task_id=old_binding.inputs.limits.task_id,compiler_id='generated-video-e2e-fixture',compiler_version='1')
    binding = fresh.binding
    inputs=binding.inputs.model_copy(update={
        'limits':old_binding.inputs.limits,'evidence':experience.evidence,
        'experiences':(experience,), 'latest_attempt_hash':experience.evidence[-1].evidence_hash,
    })
    decision=VideoGenerationResolver().resolve_requirement(projection=binding.projection,
        context=binding.context,policy=binding.policy,lifecycle=binding.lifecycle,inputs=inputs)
    compiled=provider.compile_request(decision.routing.provider_bound_request,binding.projection.requirement)
    request=provider.resolve(compiled.request)
    successor=GenerationDecisionExecutionBinding.create(projection=binding.projection,context=binding.context,
        policy=binding.policy,lifecycle=binding.lifecycle,inputs=inputs,decision=decision,compiled_request=request)
    service.start(attempt_id='fresh-successor',request=request,execution_binding=successor)
    manifest=load_production_project(tmp_path/'project.yaml').manifest
    state=next(a for a in manifest.attempts if a.attempt_id=='fresh-successor').video_generation_state
    writer._require_submit_execution_binding(manifest,state,request)
    budget=writer._reopen_paid_budget(manifest.active_paid_provider_budget)
    assert len(budget.reservations)==1
    assert len(budget.submit_quota_extensions)==1


@pytest.mark.parametrize('code',[ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,ErrorCode.VIDEO_PROVIDER_FAILED])
def test_unknown_or_failed_request_is_not_a_zero_effect_close(tmp_path,code):
    writer, service, preview, prior = _pending(tmp_path)
    writer.extend_paid_provider_submit_quota(_entry(writer, prior))
    service.submit_once(attempt_id=NEXT,paid_preview=preview,reservation_id='quota-reservation')
    writer.record_video_provider_failure(attempt_id=NEXT,error_code=code,message='fixture outcome')
    before=_bytes(tmp_path)
    with pytest.raises(AiVideoError):_close(writer)
    assert _bytes(tmp_path)==before


def test_closed_request_rejects_changed_experience_and_corrupt_evidence(tmp_path):
    writer, _, _, _ = _pending(tmp_path)
    experience=record_attempt_evaluation(committer=writer,attempt_id=NEXT)
    _close(writer)
    changed=experience.model_copy(update={'evidence':(experience.evidence[0].model_copy(
        update={'outcome':'runtime_failure','runtime_reason':'spoofed failure'}),)})
    before=_bytes(tmp_path)
    with pytest.raises(AiVideoError):writer.record_generation_experience(attempt_id=NEXT,experience=changed)
    assert _bytes(tmp_path)==before
    attempt=next(a for a in writer._read_manifest().attempts if a.attempt_id==NEXT)
    path=tmp_path/attempt.video_generation_state.generation_experiences[0].path
    path.write_bytes(path.read_bytes()+b' ')
    before=_bytes(tmp_path)
    with pytest.raises(AiVideoError):_close(writer)
    assert _bytes(tmp_path)==before
