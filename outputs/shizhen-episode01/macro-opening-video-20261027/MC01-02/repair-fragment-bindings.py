"""Repair only exact fragment segmentation; retain authored request prose."""
from pathlib import Path
import json
from ai_video.production.project import load_production_project
from ai_video.production.hashing import canonical_sha256,seal_artifact
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.state_commit import ProductionStateCommitter
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC01-02';d=json.loads((V/'data.json').read_text());text=(V/'native-prompt.zh.txt').read_text().strip()
d['fragments']['identity']=[text[:text.index('雨夜市政')].strip(),'全程同一工人、设备、受力方向和雨夜']
d['fragments']['art']=[text[text.index('雨夜市政'):text.index('先用稳定')],text[text.index('动作与反应'):]]
assert all(f in text for fs in d['fragments'].values() for f in fs)
(V/'data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');p=load_production_project(ROOT/'project.yaml');assert not [a for a in p.manifest.attempts if a.operation=='video_generation'];old=p.qa_policy;payload=dict(old.generation_acceptance.profile_payload);payload.pop('content_hash');version=str(old.revision+1);payload['profile_version']=version;rules=[]
for rule in payload['generation_requirements']:
 rule=dict(rule);k=rule['requirement_id'];rule.update(native_text=d['fragments'][k],native_text_mapping={'intent_sha256':d['intent_sha256'],'bindings':[{'intent_path':path,'fragment_indices':list(range(len(d['fragments'][k])))} for path in d['paths'][k]]});rules.append(rule)
payload['generation_requirements']=rules;h=canonical_sha256(payload)
qa=seal_artifact(old.model_copy(update={'revision':old.revision+1,'policy_version':version,'generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version=version,measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(d['observations']),profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
ProductionStateCommitter(ROOT).activate_qa_policy(qa,attempt_id='shizhen-macro-native-fragment-segmentation',expected_manifest_revision=p.manifest.manifest_revision);print('exact fragment segmentation verified; zero submissions')
