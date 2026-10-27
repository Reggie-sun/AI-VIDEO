"""Complete missing typed acting and raw acceptance before first submission."""
from pathlib import Path
import json
from ai_video.production.video_requirement import GenerationIntent
from ai_video.production.project import load_production_project
from ai_video.production.hashing import canonical_sha256,seal_artifact
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.state_commit import ProductionStateCommitter
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC01-02'
r=json.loads((V/'row.json').read_text());d=json.loads((V/'data.json').read_text())
r['generation']['generation_intent']['performance_intent']['character_directions']=[{'character_id':'municipal-worker','screen_identity':'控制箱旁工人','role':'principal','visibility':'visible','beats':[{'phase':'throughout','trigger':'右手按下停止控制，工作灯熄灭、马达声停止','emotion':'从普通作业转为确认停机后仍受力的疑惑','intensity':'subtle','facial_expression':'先确认控制箱，再看向仍受力的牵引点','gaze_target':'控制箱后牵引点','breathing':'动作与反应完整、节奏自然','body_behavior':'不靠近钢索，右手按停止，先确认控制箱再看牵引点'}]}]
i=GenerationIntent.model_validate(r['generation']['generation_intent']);r['generation']['generation_intent']=i.model_dump(mode='json');ih=canonical_sha256(i.model_dump(mode='json'))
def leaves(x,path):
 if isinstance(x,dict):
  for k,v in x.items():yield from leaves(v,path+'.'+k)
 elif isinstance(x,list):
  for k,v in enumerate(x):yield from leaves(v,path+'.'+str(k))
 elif x is not None:yield path
new=list(leaves(i.model_dump(mode='json')['performance_intent']['character_directions'],'generation_intent.performance_intent.character_directions'))
d['paths']['performance']+=new;d['fragments']['performance']+=['工人见门接近限位，右手按下停止控制，工作灯熄灭、马达声停止','动作与反应完整、节奏自然'];d['intent_sha256']=ih
for name,obj in [('row.json',r),('data.json',d)]: (V/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
p=load_production_project(ROOT/'project.yaml');assert not [a for a in p.manifest.attempts if a.operation=='video_generation'];old=p.qa_policy;payload=dict(old.generation_acceptance.profile_payload);payload.pop('content_hash');payload['profile_version']='2';rules=[]
for rule in payload['generation_requirements']:
 rule=dict(rule);k=rule['requirement_id'];rule.update(intent_paths=d['paths'][k],native_text=d['fragments'][k],native_text_mapping={'intent_sha256':ih,'bindings':[{'intent_path':path,'fragment_indices':list(range(len(d['fragments'][k])))} for path in d['paths'][k]]});rules.append(rule)
payload['generation_requirements']=rules;h=canonical_sha256(payload)
qa=seal_artifact(old.model_copy(update={'revision':old.revision+1,'policy_version':'2','generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='2',measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(d['observations']),profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
m=ProductionStateCommitter(ROOT).activate_qa_policy(qa,attempt_id='shizhen-macro-acting-input-completion',expected_manifest_revision=p.manifest.manifest_revision)
print(json.dumps({'qa_revision':qa.revision,'manifest_revision':m.manifest_revision,'new_submissions':0}))
