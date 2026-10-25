"""Known-quality qualification admission; public fixtures retain paid/media history."""
from copy import copy
from types import SimpleNamespace

import pytest

from ai_video.production._qualification_quality_repair import allows_one_known_quality_repair
from ai_video.production.generation_diagnosis import (
    Intervention, diagnose_exact_result, seal_intervention_comparison,
)
from ai_video.production.video import VideoGenerationRequest
from test_generation_quality_rejection import _fetched_experience


def _make_evaluated_trial(root):
    committer, experience, _, _ = _fetched_experience(root)
    state=committer._read_manifest().attempts[-1].video_generation_state
    old=committer._reopen_generation_execution_binding(state.execution_binding)
    evidence=experience.evidence[-1]
    baseline=committer._reopen_video_request(state.request).activation_scope.request
    raw=baseline.model_dump(mode='python',exclude={'request_input_hash'})
    raw['prompt_text']+=' Clear screen-identity speaker binding.'
    request=VideoGenerationRequest.create(**raw)
    diagnosis=diagnose_exact_result(evidence,(evidence,),experience.candidate.recipe,
        evaluation_sources=experience.evaluation_sources,requirement=experience.projection.requirement)
    intervention=Intervention(intervention_id='test-speaker-binding',candidate_id=experience.candidate.candidate_id,
        purpose='production_repair',disposition='GENERATE_ONCE',closes=diagnosis.failed_requirements,
        protected_requirements=diagnosis.preserved_requirements,support=(evidence.evidence_hash,),
        changed_variables=('prompt_text',),held_constants=(),uncontrolled_variables=('seed',),
        regression_risks=diagnosis.preserved_requirements,hypothesis='Explicit speaker binding repairs known mismatch.',
        confidence_basis='Exact evaluated failure.',improvement_prediction='Failed findings pass without regression.',
        falsification_prediction='Any remaining failure refutes the repair.',
        insufficient_evidence_condition='Incomplete observations remain undetermined.')
    recipe=experience.candidate.recipe.model_copy(update={'comparison':seal_intervention_comparison(intervention,baseline)})
    inputs=old.inputs.model_copy(update={'evidence':(evidence,),'experiences':(experience,),
        'latest_attempt_hash':evidence.evidence_hash,'runtime_repairs':(),
        'baseline_request':baseline,'policy':old.inputs.policy.model_copy(update={'max_resamples':0}),
        'limits':old.inputs.limits.model_copy(update={'paid_submit_ceiling':2,'paid_submits_used':1})})
    return SimpleNamespace(_committer=committer,policy=SimpleNamespace(execution_purpose='qualification'),inputs=inputs,context=old.context,
        compiled_request=SimpleNamespace(activation_scope=SimpleNamespace(request=request)),
        decision=SimpleNamespace(selected_candidate_id=experience.candidate.candidate_id,runtime_repair=None,intervention=intervention,
            routing=SimpleNamespace(provider_bound_request=SimpleNamespace(generation_recipe=recipe)))),experience.candidate


@pytest.fixture(scope='module')
def evaluated_trial(tmp_path_factory):
    return _make_evaluated_trial(tmp_path_factory.mktemp('qualification-quality'))


def test_one_prompt_repair_with_complete_known_failure_is_admissible(evaluated_trial):
    binding,selected=evaluated_trial
    assert allows_one_known_quality_repair(binding,selected)


@pytest.mark.parametrize('field,value',[
    ('paid_submit_ceiling',1),('paid_submit_ceiling',3),
    ('paid_submits_used',0),('paid_submits_used',2),
])
def test_cannot_reset_or_expand_the_single_successor_quota(evaluated_trial,field,value):
    old,selected=evaluated_trial;b=copy(old)
    b.inputs=old.inputs.model_copy(update={'limits':old.inputs.limits.model_copy(update={field:value})})
    assert not allows_one_known_quality_repair(b,selected)


@pytest.mark.parametrize('change',[
    'unknown','not_submitted','missing_media','different_task','different_shot','extra_submit',
    'missing_intervention','resample','runtime_grant','expanded_resample','no_failure',
    'missing_protection','wrong_delta','no_comparison','changed_output','missing_candidate',
])
def test_missing_mixed_unknown_or_changed_scope_cannot_admit(evaluated_trial,change):
    old,selected=evaluated_trial;b=copy(old);i=old.inputs;e=i.evidence[-1]
    d=copy(old.decision);b.decision=d
    if change=='unknown':
        u=e.model_copy(update={'outcome':'unknown_outcome'})
        b.inputs=i.model_copy(update={'evidence':(u,), 'latest_attempt_hash':u.evidence_hash})
    elif change=='not_submitted':
        n=e.model_copy(update={'outcome':'not_submitted'})
        b.inputs=i.model_copy(update={'evidence':(n,), 'latest_attempt_hash':n.evidence_hash})
    elif change in {'missing_media','different_task','different_shot'}:
        key,value={'missing_media':('artifact_sha256',None),'different_task':('task_id','other'),
            'different_shot':('shot_id','other')}[change]
        n=e.model_copy(update={key:value});b.inputs=i.model_copy(update={'evidence':(n,),'latest_attempt_hash':n.evidence_hash})
    elif change=='extra_submit':
        n=e.model_copy(update={'attempt_id':'hidden-second-submit'});b.inputs=i.model_copy(update={'evidence':(n,e)})
    elif change=='missing_intervention':d.intervention=None
    elif change=='resample':d.intervention=d.intervention.model_copy(update={'purpose':'resample','resample_limit':1})
    elif change=='runtime_grant':d.runtime_repair=object()
    elif change=='expanded_resample':b.inputs=i.model_copy(update={'policy':i.policy.model_copy(update={'max_resamples':1})})
    elif change=='no_failure':d.intervention=d.intervention.model_copy(update={'closes':('unobserved',)})
    elif change=='missing_protection':d.intervention=d.intervention.model_copy(update={'protected_requirements':()})
    elif change=='wrong_delta':d.intervention=d.intervention.model_copy(update={'changed_variables':('seed',)})
    elif change=='no_comparison':
        recipe=d.routing.provider_bound_request.generation_recipe.model_copy(update={'comparison':None})
        d.routing=SimpleNamespace(provider_bound_request=SimpleNamespace(generation_recipe=recipe))
    elif change=='changed_output':
        r=old.compiled_request.activation_scope.request
        raw=r.model_dump(mode='python',exclude={'request_input_hash'})
        raw['output_requirement']=r.output_requirement.model_copy(update={'duration_seconds':r.output_requirement.duration_seconds+1})
        b.compiled_request=SimpleNamespace(activation_scope=SimpleNamespace(request=VideoGenerationRequest.create(**raw)))
    elif change=='missing_candidate':selected=None
    assert not allows_one_known_quality_repair(b,selected)


@pytest.mark.parametrize('terminal',['quality_rejection','provider_failure','unknown','still_running'])
def test_locked_committer_requires_canonical_quality_closure_before_any_paid_effect(tmp_path,terminal):
    from ai_video.errors import AiVideoError,ErrorCode
    from ai_video.production.models import ActorIdentity
    from ai_video.production._qualification_quality_repair import require_quality_repair_predecessor
    binding,selected=_make_evaluated_trial(tmp_path)
    committer=binding._committer
    manifest=committer._read_manifest()
    attempt=next(a for a in manifest.attempts if a.attempt_id==binding.inputs.evidence[-1].attempt_id)
    if terminal=='quality_rejection':
        committer.reject_video_generation(attempt_id=attempt.attempt_id,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
            actor=ActorIdentity(actor_id='test-quality-close',actor_kind='codex'))
    elif terminal in {'provider_failure','unknown'}:
        committer.record_video_provider_failure(attempt_id=attempt.attempt_id,
            error_code=ErrorCode.VIDEO_PROVIDER_FAILED if terminal=='provider_failure' else ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            message='Public canonical terminal transition without a quality rejection.')
    before=committer._read_manifest()
    state_bytes=(tmp_path/'state/manifest.json').read_bytes()
    with committer._exclusive_lock():
        if terminal=='quality_rejection':
            require_quality_repair_predecessor(committer,before,binding)
        else:
            with pytest.raises(AiVideoError,match='exact terminal quality rejection'):
                require_quality_repair_predecessor(committer,before,binding)
    assert (tmp_path/'state/manifest.json').read_bytes()==state_bytes
    assert committer._read_manifest().active_paid_provider_budget==before.active_paid_provider_budget
    assert tuple(a.paid_provider_state for a in committer._read_manifest().attempts)==tuple(a.paid_provider_state for a in before.attempts)
