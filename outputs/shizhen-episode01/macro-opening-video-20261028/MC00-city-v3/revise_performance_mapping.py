"""Complete authored worker coverage through existing Project/QA commit owners."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.models import ArtifactReference
from ai_video.production.project import load_production_project
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,prepare_project_registry_commit,_canonical_yaml_bytes

D=Path(__file__).resolve().parent
ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261028/MC00-city-v3'
old=load_production_project(ROOT/'project.yaml')
assert not [a for a in old.manifest.attempts if a.operation=='video_generation']
prompt=(D/'native-prompt.zh.txt').read_text().strip()
prompt=prompt.replace('工人只正常作业，不提前按停、收手或惊恐',
    '工人可见后始终平常专注看着设备、呼吸平稳，留在原位自然作业，不提前按停、收手或惊恐')
assert len(prompt)<=500 and not any(c.isascii() and c.isalpha() for c in prompt)
row=json.loads((D/'row.json').read_text());data=json.loads((D/'data.json').read_text());parts=prompt.splitlines()
row['shot']['intent']=prompt
row['generation']['generation_intent']['subject_action']['progression']='\n'.join(parts[:3])
base='generation_intent.performance_intent.character_directions.0.beats.0.'
paths=data['paths']['performance']
paths.extend(base+k for k in ['phase','trigger','emotion','intensity','facial_expression','gaze_target','breathing','body_behavior'] if base+k not in paths)
data['fragments']['performance']=[parts[2],parts[3]]
for key,indices in {'identity':[2,3],'action':[0,1,2],'camera':[0,1,3],'space':[0,1,2,3],'art':[0,1],'sound':[3]}.items():
    data['fragments'][key]=[parts[i] for i in indices]
data['intent_sha256']=canonical_sha256(row['generation']['generation_intent'])
data['observations']['performance']='工人可见后平常专注看向设备、自然呼吸并保持原位作业，不提前按停或收手；门正常缓慢右移，工作灯始终亮，尾态按源第0帧'
envelope={'kind':'MC00-explicit-worker-performance-mapping/1','row':row,'data':data,
    'reason':'Keep all acting fields and raw required rules explicit before one trial; no prior video submit'}
source=authoring_input_reference(envelope)
shot0=next(s for s in old.shots if s.shot_id=='MC00-CITY')
shot=seal_artifact(shot0.model_copy(update={'revision':shot0.revision+1,'content_hash':'0'*64,
    'creation_receipt_id':'MC00-worker-performance-v2','intent':prompt,
    'source_provenance':(*shot0.source_provenance,source)}))
shot_path=Path('creative/shots/MC00-CITY-performance-v2.yaml')
reference=ArtifactReference(artifact_id=shot.artifact_id,revision=shot.revision,content_hash=shot.content_hash,path=shot_path)
refs=old.project.artifacts.model_copy(update={'shots':tuple(reference if r.artifact_id==shot.artifact_id else r for r in old.project.artifacts.shots)})
project=seal_artifact(old.project.model_copy(update={'revision':old.project.revision+1,'content_hash':'0'*64,
    'creation_receipt_id':'MC00-worker-performance-project-v2','artifacts':refs,
    'source_provenance':(*old.project.source_provenance,source)}))
request=prepare_project_registry_commit(manifest=old.manifest,project=project,registry=old.registry,attempt_id='MC00-worker-performance-v2')
def artifact(path,payload):return PreparedArtifact(Path(path),payload,hashlib.sha256(payload).hexdigest())
request=replace(request,artifacts=tuple(sorted((*request.artifacts,
    artifact(shot_path,_canonical_yaml_bytes(shot)),artifact(source.reference,authoring_input_payload(envelope))),key=lambda a:a.relative_path.as_posix())))
candidate=old.model_copy(update={'project':project,'shots':tuple(shot if s.shot_id==shot.shot_id else s for s in old.shots)})
request=prepare_strategy_dependency_transition(base_loaded=old,candidate_loaded=candidate,request=request)
committer=ProductionStateCommitter(ROOT);manifest=committer.commit(request)
payload={k:v for k,v in old.qa_policy.generation_acceptance.profile_payload.items() if k not in {'content_hash','generation_requirements'}}
payload['profile_version']='2'
payload['generation_requirements']=[{'requirement_id':key,'level':'acceptance','stage':'raw_generation','dimension':key,
    'observable':value,'tolerance':'完整要求保持；前期检查不代视频通过','measurement':'Exact MP4 video-analysis and reliable audio observations','proof':'analyzer',
    'intent_paths':data['paths'][key],'native_text':data['fragments'][key],
    'native_text_mapping':{'intent_sha256':data['intent_sha256'],'bindings':[{'intent_path':path,'fragment_indices':list(range(len(data['fragments'][key])))} for path in data['paths'][key]]},
    'production_owner':'shot_authoring'} for key,value in data['observations'].items()]
h=canonical_sha256(payload)
qa=seal_artifact(old.qa_policy.model_copy(update={'revision':old.qa_policy.revision+1,'content_hash':'0'*64,
    'creation_receipt_id':'MC00-worker-performance-qa-v2','policy_version':'2',
    'source_provenance':(*old.qa_policy.source_provenance,source),
    'generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='2',
        measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(data['observations']),
        profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
manifest=committer.activate_qa_policy(qa,expected_manifest_revision=manifest.manifest_revision,attempt_id='MC00-worker-performance-qa-v2')
(D/'native-prompt.zh.txt').write_text(prompt+'\n')
(D/'row.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
(D/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(D/'performance-authoring-revision.json').write_text(json.dumps({'project_revision':project.revision,
    'shot_revision':shot.revision,'qa_version':'2','prompt_chars':len(prompt),'manifest_revision':manifest.manifest_revision,
    'video_attempts_started':0,'paid_submits':0},indent=2)+'\n')
print(json.dumps({'revised':True,'prompt_chars':len(prompt),'video_calls':0,'manifest_revision':manifest.manifest_revision}))
