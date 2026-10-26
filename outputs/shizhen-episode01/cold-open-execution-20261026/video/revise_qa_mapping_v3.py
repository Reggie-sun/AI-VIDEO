from pathlib import Path
import json
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.state_commit import ProductionStateCommitter
v=Path(__file__).resolve().parent;r=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A1';l=load_production_project(r/'project.yaml')
assert not any(a.operation=='video_generation' for a in l.manifest.attempts)
i=json.loads((v/'CO-A1-row.json').read_text())['generation']['generation_intent']
p=json.loads(json.dumps(l.qa_policy.generation_acceptance.profile_payload));p.pop('content_hash');p['profile_version']='3'
for item in p['generation_requirements']:
 item.pop('native_text',None)
 if item['requirement_id']=='art':item['intent_paths']=['generation_intent.visual_treatment.'+k for k in i['visual_treatment']]
 if item['requirement_id']=='sound':item['intent_paths']=['generation_intent.dialogue_intent.turns','generation_intent.ambience_intent.environment_bed','generation_intent.ambience_intent.foley_cues']
h=canonical_sha256(p);a=DomainAcceptancePolicy(domain_id=p['domain_id'],profile_id=p['profile_id'],profile_version='3',measurement_contract_version=p['measurement_contract_version'],required_requirement_ids=tuple(p['required_requirement_ids']),profile_content_hash=h,profile_payload={**p,'content_hash':h})
q=seal_artifact(l.qa_policy.model_copy(update={'revision':l.qa_policy.revision+1,'policy_version':'3','generation_acceptance':a}));m=ProductionStateCommitter(r).activate_qa_policy(q,attempt_id='shizhen-CO-A1-qa-native-mapping-v3',expected_manifest_revision=l.manifest.manifest_revision)
(v/'CO-A1-qa-policy-v3.json').write_text(json.dumps(q.model_dump(mode='json'),ensure_ascii=False,indent=2)+'\n');print({'manifest_revision':m.manifest_revision,'observables_unchanged':True,'new_video_calls':0})
