"""Finish the known canonical project revision after immutable-map preparation rejection."""
from pathlib import Path
import json,hashlib
from ai_video.production.project import load_production_project
from ai_video.production.hashing import canonical_sha256,seal_artifact
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.state_commit import ProductionStateCommitter
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05-repair-v2';p=load_production_project(ROOT/'project.yaml');assert p.project.revision==2 and p.qa_policy.revision==1 and not [a for a in p.manifest.attempts if a.operation=='video_generation']
ref=p.project.source_provenance[-1];assessment=json.loads((ROOT/ref.reference).read_text());assert assessment['kind']=='explicit-frame-conditioning-assessment/1';row=assessment['row'];data=json.loads((V/'data.json').read_text());aid=assessment['compatibility']['first_anchor_id'];a=next(x for x in p.registry.assets if x.asset_id==aid);assert a.sha256==hashlib.sha256(Path('referces/shizhen/macro-opening-20261027/L01-X.png').read_bytes()).hexdigest()
selection=dict(asset_id=aid,node_id=aid+'-node',resource_id=aid+'-local-generated',path=str((Path.cwd()/'referces/shizhen/macro-opening-20261027/L01-X.png')),usage_license='Task-owned existing same-identity descent reference for authorized bounded repair',generated_source=dict(record_path=str((V/'reference-first-descent-source.json').relative_to(Path.cwd())),record_sha256=hashlib.sha256((V/'reference-first-descent-source.json').read_bytes()).hexdigest(),tool=dict(name='builtin-imagegen',version='tool-interface')))
data['images'][0]=selection;data['scene_images']=[x['asset_id'] for x in data['images']];data['intent_sha256']=canonical_sha256(row['generation']['generation_intent'])
old=p.qa_policy;payload=json.loads(json.dumps(old.generation_acceptance.profile_payload));payload.pop('content_hash');payload['profile_version']='2'
for rule in payload['generation_requirements']:
 k=rule['requirement_id'];rule['native_text_mapping']={'intent_sha256':data['intent_sha256'],'bindings':[dict(intent_path=path,fragment_indices=list(range(len(data['fragments'][k])))) for path in data['paths'][k]]}
h=canonical_sha256(payload);qa=seal_artifact(old.model_copy(update={'revision':2,'content_hash':'0'*64,'policy_version':'2','source_provenance':(*old.source_provenance,ref),'generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='2',measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(data['observations']),profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
ProductionStateCommitter(ROOT).activate_qa_policy(qa,attempt_id='stair-firstlast-compatible-descent-QA',expected_manifest_revision=p.manifest.manifest_revision)
for name,obj in [('row.json',row),('data.json',data),('conditioning-assessment.json',assessment)]: (V/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
plan=json.loads((V/'reference-input-plan.json').read_text());plan['images'][0]=dict(path=selection['path'],sha256=a.sha256,native_role='first_frame');plan['conditioning_assessment']='conditioning-assessment.json';(V/'reference-input-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'known_partial_revision_completed':True,'project_revision':2,'QA_revision':2,'first_anchor':aid,'new_paid_calls':0}))
