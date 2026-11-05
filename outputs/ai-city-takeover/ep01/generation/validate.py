"""Offline exact-source and prepared-request checks; no transport or state mutation."""
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
before=loaded.manifest.model_dump_json()
r=create_runtime(project_root=root,configuration=load_configuration(P/'driver-config.json'))
a=r.prepare();b=r.prepare()
assert a.resolved_request and a.execution_binding and a.compilation.outcome=='compiled'
assert a.resolved_request.resolved_generation_hash==b.resolved_request.resolved_generation_hash
assert a.execution_binding.binding_hash==b.execution_binding.binding_hash
assert load_production_project(root/'project.yaml').manifest.model_dump_json()==before
for binding in a.resolved_request.image_bindings:r.reference_resolver(binding)
binding=a.resolved_request.image_bindings[0]
wrong=binding.model_copy(update={'asset_sha256':'0'*64})
try:r.reference_resolver(wrong)
except ValueError:tamper=True
else:raise AssertionError('stale bytes binding accepted')
prompt=a.compilation.request.prompt_text
order=[x.asset_id for x in a.resolved_request.image_bindings]
assert order==['iris-a01-balcony','iris-cf-details','iris-cf-face']
assert '第一张已认可阳台图' in prompt and '第二张只锁定左耳' in prompt and '第三张只锁定同一女性的面貌' in prompt
out={'canonical_reload':True,'manifest_revision':loaded.manifest.manifest_revision,'project_revision':loaded.project.revision,'prepare_disposition':a.decision.disposition,'compiled':True,'exact_request_hash':a.resolved_request.resolved_generation_hash,'exact_binding_hash':a.execution_binding.binding_hash,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'deterministic_prepare':True,'prepare_no_state_writes':True,'all_reference_bytes_verified':True,'stale_binding_rejected':tamper,'actual_order':order,'reference_duty_order_matches_prompt':True,'actual_roles':[x.role for x in a.resolved_request.image_bindings],'timing_mode':a.compilation.request.output_requirement.timing_mode,'nominal_duration_seconds':a.compilation.request.output_requirement.duration_seconds,'preview_approval_in_provenance':True,'profile_supplied':True,'live_transport_supplied':False,'paid_submits':0,'actual_quality':'NOT_EVALUATED','human_acceptance':'NOT_EVALUATED'}
(P/'final-preparation-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))
