"""Read-only validation of the frozen, actually materialized C source request."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from ai_video.production.project import load_production_project
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from scripts.jimeng_feedback_driver import registered_reference_resolver
from assert_resolved_bindings import validate as validate_bindings
P=Path(__file__).resolve().parent
project=load_production_project(P/'project/project.yaml')
parent=load_production_project(P.parent/'a01-first-frame-repair/project/project.yaml')
saved=json.loads((P/'prepare-result.json').read_text())
request=saved['resolved_request'];binding=GenerationDecisionExecutionBinding.model_validate(saved['execution_binding'])
assert saved['decision']['disposition']=='GENERATE_ONCE' and saved['compilation']['outcome']=='compiled'
validate_bindings(saved)
assert project.characters==parent.characters
assert len(request['image_bindings'])==2 and all(a['asset_id']!='iris-cf-face' for a in request['image_bindings'])
resolver=registered_reference_resolver(project.root)
from ai_video.production.video import ResolvedVideoGenerationRequest
resolved=ResolvedVideoGenerationRequest.model_validate(request)
for item in resolved.image_bindings:resolver(item)
try:resolver(resolved.image_bindings[0].model_copy(update={'asset_sha256':'0'*64}))
except ValueError:tamper=True
else:raise AssertionError('wrong reference bytes accepted')
text=request['prompt_text']
assert '观察者看到的始终是显示器背面' in text and '不向背面贴图' in text
assert '嘴唇自然静置' in text and '不出现说话或演唱的连续口型' in text
assert '保留平台正常人工智能生成标识，不删除、不遮挡它' in text
assert '不敲键盘' in text and '不操作设备' in text
assert '阳台' not in text
qa=project.qa_policy.generation_acceptance
observer=next(r for r in qa.profile_payload['generation_requirements'] if r['requirement_id']=='observer')
assert '不要求必须观察到某次事件' in observer['observable']
gate=json.loads((P.parent/'qa/A01-v2/post-media-gate.json').read_text())
assert gate['attempt_id']=='iris-ep01-a01-two-reference-repair-002' and gate['verdict']=='PASS' and gate['all_required_observed_pass']
assert all(item['verdict']=='PASS' for item in gate['required_findings'])
oldgate=json.loads((P.parent/'qa/A01/post-media-gate.json').read_text());assert oldgate['verdict']=='FAIL'
assert not any(a.video_generation_state for a in project.manifest.attempts)
lineage=[]
for ref in project.project.source_provenance:
 if ref.reference.startswith('evidence/authoring-input/'):
  value=json.loads((project.root/ref.reference).read_text())
  if value.get('kind')=='iris-c-cumulative-source-budget/1':lineage.append(value)
assert len(lineage)==1
budget=lineage[0]
assert budget['prior_video_submits']==2 and budget['prior_observed_total_credits']==396
assert budget['cumulative_video_submit_ceiling']==3 and budget['cumulative_operator_credit_ceiling']==750
assert budget['new_c_unit_max_submits']==1 and budget['new_c_operator_credit_ceiling']==250
out={'project_root':str(project.root),'authoring_project_revision':project.project.revision,'validation_manifest_revision':project.manifest.manifest_revision,'selected_strategy':'multimodal A03 scene + ID7b full identity','prepare_disposition':saved['decision']['disposition'],'compiled':True,'actual_reference_order':[a['asset_id'] for a in request['image_bindings']],'actual_reference_sha256':[a['asset_sha256'] for a in request['image_bindings']],'cf_a_in_payload':False,'canonical_iris_character_exactly_preserved':True,'all_payload_bytes_verified':True,'stale_binding_rejected':tamper,'a2_parent_gate_exact_all_pass':True,'a1_fail_retained':True,'ai_label_allowed':True,'natural_static_lips_no_continuous_articulation':True,'no_added_pixel_or_required_breathing_event_measurement':True,'monitor_back_and_no_operation':True,'prior_video_submits':2,'prior_observed_credits':396,'cumulative_video_submit_ceiling':3,'cumulative_operator_credit_ceiling':750,'new_c_unit_submit_ceiling':1,'new_c_operator_credit_ceiling':250,'request_sha256':resolved.resolved_generation_hash,'binding_sha256':binding.binding_hash,'prompt_sha256':hashlib.sha256(text.encode()).hexdigest(),'c_video_attempts_started':0,'new_provider_calls':0,'c_media_quality':'NOT_EVALUATED','production_activation':False}
(P/'final-preparation-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))
