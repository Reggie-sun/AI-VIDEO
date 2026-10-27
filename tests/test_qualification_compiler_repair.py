"""Pure model fixtures; actual mixed-history admission is also replayed through the committer."""
from types import SimpleNamespace
import hashlib
import pytest
from ai_video.production.generation_decision import GenerationCandidate, DecisionPolicy, ExecutionLimits
from ai_video.production.generation_diagnosis import AttemptEvidence
from ai_video.production.generation_runtime_repair import RuntimeRepairAuthorization,RuntimeRepairGrant,PaidNoEffectRetarget
from ai_video.production.models import ActorIdentity
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.video import VideoGenerationRequest
from test_jimeng_authored_prompt import _fixture, TEXT


def fixture(monkeypatch, media_count=5):
    provider,bound,requirement=_fixture(monkeypatch,text=TEXT+'\n',fragment=TEXT)
    baseline=provider.compile_request(bound,requirement).request
    source=GenerationCandidate(candidate_id='jimeng/'+bound.capability_id,provider_profile=bound.provider_profile,
        capabilities=provider.capabilities(),capability_id=bound.capability_id,compiler_contract=bound.compiler_contract,
        output_requirement=bound.output_requirement,recipe=bound.generation_recipe)
    compiler=AdapterCompilerContract.create(compiler_id=bound.compiler_contract.compiler_id,compiler_version='2')
    recipe=bound.generation_recipe.model_copy(update={'compiler_hash':compiler.compiler_hash})
    target=source.model_copy(update={'compiler_contract':compiler,'recipe':recipe})
    updated=type(bound).create(**{k:getattr(bound,k) for k in type(bound).model_fields
        if k not in {'provider_bound_request_hash','compiler_contract','generation_recipe'}},
        compiler_contract=compiler,generation_recipe=recipe)
    compiled=provider.compile_request(updated,requirement)
    assert compiled.outcome=='compiled'
    request=compiled.request
    shot=requirement.target_shot.shot_id;task='compiler-repair-task'
    def sha(text):return hashlib.sha256(text.encode()).hexdigest()
    media=tuple(AttemptEvidence(task_id=task,shot_id=shot,attempt_id=f'media-{i}',recipe_scope_hash=source.scope_hash,
        facts_hash='a'*64,rubric_hash=recipe.rubric_hash,request_hash=sha(f'request-{i}'),
        artifact_sha256=sha(f'media-{i}'),outcome='media') for i in range(media_count))
    latest=AttemptEvidence(task_id=task,shot_id=shot,attempt_id='failed-before-dispatch',recipe_scope_hash=source.scope_hash,
        facts_hash='a'*64,rubric_hash=recipe.rubric_hash,request_hash=baseline.request_input_hash,outcome='not_submitted')
    repair=RuntimeRepairAuthorization.create(schema_version='runtime-repair/3',attempt_id=latest.attempt_id,
        evidence_hash=latest.evidence_hash,repair_basis='Verified no effect, exact compiler whitespace adaptation.',
        actor=ActorIdentity(actor_id='operator',actor_kind='codex'),expected_manifest_revision=12,
        paid_no_effect_retarget=PaidNoEffectRetarget(submit_receipt_fingerprint='f'*64,target_scope_hash=target.scope_hash))
    limits=ExecutionLimits(task_id=task,generation_forbidden=False,allowed_remote_candidates=(target.candidate_id,),
        paid_submit_ceiling=media_count+2,paid_submits_used=media_count+1,local_batch_limit=1,
        local_batch_used=0,local_total_used=0,local_resource_available=False)
    inputs=SimpleNamespace(limits=limits,policy=DecisionPolicy(max_resamples=0),candidates=(target,),
        evidence=(*media,latest),latest_attempt_hash=latest.evidence_hash,baseline_request=baseline,
        experiences=(SimpleNamespace(candidate=source,evidence=(latest,)),),
        runtime_repairs=(RuntimeRepairGrant(authorization=repair,consumed=False),))
    b=SimpleNamespace(policy=SimpleNamespace(execution_purpose='qualification'),inputs=inputs,
        context=SimpleNamespace(target_shot_id=shot),decision=SimpleNamespace(runtime_repair=repair,intervention=None),
        compiled_request=SimpleNamespace(activation_scope=SimpleNamespace(request=request)))
    return b,target


@pytest.mark.parametrize('media_count',[1,2,5,9])
def test_first_exact_compiler_repair_keeps_all_media_and_no_effect_consumption(monkeypatch,media_count):
    from ai_video.production._qualification_compiler_repair import allows_first_no_effect_compiler_repair
    b,target=fixture(monkeypatch,media_count)
    assert allows_first_no_effect_compiler_repair(b,target)


@pytest.mark.parametrize('change',['count','ceiling','missing_history','extra_history','unknown','unpaid_prefix',
    'consumed','missing_grant','second_grant','wrong_source','wrong_target','intervention','resample',
    'wrong_task','wrong_shot','duplicate_attempt','prompt_content','output','image','compiler_id'])
def test_mixed_history_recovery_does_not_relax_any_protected_boundary(monkeypatch,change):
    from ai_video.production._qualification_compiler_repair import allows_first_no_effect_compiler_repair
    b,target=fixture(monkeypatch);i=b.inputs;e=i.evidence[-1]
    if change=='count':i.limits=i.limits.model_copy(update={'paid_submits_used':5})
    elif change=='ceiling':i.limits=i.limits.model_copy(update={'paid_submit_ceiling':8})
    elif change=='missing_history':i.evidence=i.evidence[1:]
    elif change=='extra_history':i.evidence=(i.evidence[0].model_copy(update={'attempt_id':'hidden'}),*i.evidence)
    elif change=='unknown':i.evidence=(i.evidence[0].model_copy(update={'outcome':'unknown_outcome','artifact_sha256':None}),*i.evidence[1:])
    elif change=='unpaid_prefix':i.evidence=(i.evidence[0].model_copy(update={'outcome':'not_submitted','artifact_sha256':None}),*i.evidence[1:])
    elif change=='consumed':i.runtime_repairs=(RuntimeRepairGrant(authorization=b.decision.runtime_repair,consumed=True),)
    elif change=='missing_grant':i.runtime_repairs=()
    elif change=='second_grant':i.runtime_repairs=(*i.runtime_repairs,*i.runtime_repairs)
    elif change=='wrong_source':i.latest_attempt_hash='b'*64
    elif change=='wrong_target':target=target.model_copy(update={'recipe':target.recipe.model_copy(update={'rubric_hash':'b'*64})})
    elif change=='intervention':b.decision.intervention=object()
    elif change=='resample':i.policy=i.policy.model_copy(update={'max_resamples':1})
    elif change in {'wrong_task','wrong_shot','duplicate_attempt'}:
        changes={'wrong_task':{'task_id':'other'},'wrong_shot':{'shot_id':'other'},'duplicate_attempt':{'attempt_id':i.evidence[1].attempt_id}}
        i.evidence=(i.evidence[0].model_copy(update=changes[change]),*i.evidence[1:])
    else:
        request=b.compiled_request.activation_scope.request
        changes={'prompt_content':{'prompt_text':request.prompt_text+' 未批准动作'},
            'output':{'output_requirement':request.output_requirement.model_copy(update={'duration_seconds':7})},
            'image':{'image_bindings':(request.image_bindings[0].model_copy(update={'asset_sha256':'b'*64}),)},
            'compiler_id':{'adapter_compiler_id':'other-compiler'}}
        raw=request.model_dump(mode='python',exclude={'request_input_hash'});raw.update(changes[change])
        b.compiled_request.activation_scope.request=VideoGenerationRequest.create(**raw)
    assert not allows_first_no_effect_compiler_repair(b,target)


def test_reevaluating_same_paid_media_does_not_count_a_second_submit(monkeypatch):
    from ai_video.production._qualification_compiler_repair import allows_first_no_effect_compiler_repair
    b,target=fixture(monkeypatch)
    b.inputs.evidence=(b.inputs.evidence[0],*b.inputs.evidence)
    assert allows_first_no_effect_compiler_repair(b,target)


def test_conflicting_artifact_for_same_attempt_is_rejected(monkeypatch):
    from ai_video.production._qualification_compiler_repair import allows_first_no_effect_compiler_repair
    b,target=fixture(monkeypatch)
    b.inputs.evidence=(b.inputs.evidence[0].model_copy(update={'artifact_sha256':'f'*64}),*b.inputs.evidence)
    assert not allows_first_no_effect_compiler_repair(b,target)
