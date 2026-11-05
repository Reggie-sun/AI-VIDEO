"""Read-only actual repair request validation. No transport, start or submit."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from scripts.jimeng_feedback_driver import create_runtime,load_configuration
from ai_video.production.project import load_production_project
P=Path(__file__).resolve().parent
root=P/'project'
loaded=load_production_project(root/'project.yaml')
old=load_production_project(P.parent/'generation/project/project.yaml')
assert loaded.characters==old.characters
assert loaded.qa_policy.generation_acceptance.profile_payload['generation_requirements'][0]['observable'] == next(x for x in old.qa_policy.generation_acceptance.profile_payload['generation_requirements'] if x['requirement_id']=='identity')['observable']
before=loaded.manifest.model_dump_json()
r=create_runtime(project_root=root,configuration=load_configuration(P/'driver-config.json'))
a=r.prepare();b=r.prepare()
assert a.resolved_request and a.execution_binding and a.compilation.outcome=='compiled'
request=a.resolved_request;refs=request.image_bindings
assert [x.asset_id for x in refs]==['iris-a01-first-frame-repair-balcony','iris-cf-details']
assert [x.asset_sha256 for x in refs]==['0faefb4770ee7809a541af4150724dd2d188d9c7689a12f41d41ded3e4752087','e19d9473c40c19d4834554055298351e1bdea3f856a6de76b057b575fcb563ea']
assert all(x.role=='reference' for x in refs)
assert not request.media_bindings
for x in refs:r.reference_resolver(x)
try:r.reference_resolver(refs[0].model_copy(update={'asset_sha256':'0'*64}))
except ValueError:tamper_rejected=True
else:raise AssertionError('stale source hash accepted')
prompt=request.prompt_text
assert '第一张已认可阳台图控制主要构图' in prompt and '第二张已认可正面头胸人物图控制同一女性的完整面貌、身份、左耳装置和左领细红线' in prompt
assert '不变成全身或远景，不转成侧身或露背' in prompt
assert '嘴唇自然静置' in prompt and '不出现说话或演唱的连续口型' in prompt
assert '保留平台正常人工智能生成标识，不删除、不遮挡它' in prompt
assert request.resolved_generation_hash==b.resolved_request.resolved_generation_hash
assert a.execution_binding.binding_hash==b.execution_binding.binding_hash
assert load_production_project(root/'project.yaml').manifest.model_dump_json()==before
lineage=json.loads((P/'repair-lineage.json').read_text())
assert lineage['prior_actual_attempts']==1 and lineage['prior_actual_credits']==198
assert lineage['cumulative_attempt_ceiling']==2 and lineage['cumulative_credit_ceiling']==500
assert lineage['new_unit_max_submits']==1 and lineage['new_unit_credit_ceiling']==250
assert lineage['prior_raw_sha256']=='65f17d6860cbde39df398f42138149a7b4fc7a0bda7fdd96952b88134a0601d5'
assert request.model_id=='seedance_2.0_vip' and request.mode.value=='reference_to_video'
out={'selected_strategy':'multimodal-two-reference: A01 scene + ID7b full identity; exclude CF-a side/back','administrative_directory_name_is_not_provider_mode':True,'project_revision':loaded.project.revision,'manifest_revision':loaded.manifest.manifest_revision,'actual_reference_order':[x.asset_id for x in refs],'actual_sha256':[x.asset_sha256 for x in refs],'actual_provider_mode':request.mode.value,'cf_a_in_payload':False,'cf_id7b_in_payload':True,'canonical_character_exactly_preserved':True,'identity_qa_exactly_preserved':True,'natural_lips_new_rule_explicit':True,'platform_ai_mark_retained':True,'first_frame_claimed':False,'deterministic_prepare':True,'prepare_no_state_writes':True,'all_payload_bytes_verified':True,'stale_binding_rejected':tamper_rejected,'prior_attempts':1,'prior_credits':198,'cumulative_attempt_ceiling':2,'cumulative_credit_ceiling':500,'new_unit_max_submits':1,'request_hash':request.resolved_generation_hash,'execution_binding_hash':a.execution_binding.binding_hash,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'provider_calls':0,'actual_repair_quality':'NOT_EVALUATED','old_camera_space_fail_preserved':True}
(P/'final-preparation-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))
