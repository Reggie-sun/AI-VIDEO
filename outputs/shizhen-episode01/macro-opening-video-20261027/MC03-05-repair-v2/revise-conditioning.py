"""Register a compatible existing descent anchor and seal its frame-lane assessment."""
from pathlib import Path
from dataclasses import replace
import json,hashlib
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.production.project import load_production_project
from ai_video.production.hashing import canonical_sha256,seal_artifact
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.models import AssetRegistrySnapshot
from ai_video.production.video_requirement import GenerationIntent,ConditioningCompatibilityEvidence
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,prepare_project_registry_commit
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition

R=Path.cwd();V=Path(__file__).resolve().parent;ROOT=R/'runs/shizhen-macro-opening-20261027/MC03-05-repair-v2'
p=load_production_project(ROOT/'project.yaml');assert not [a for a in p.manifest.attempts if a.operation=='video_generation']
row=json.loads((V/'row.json').read_text());data=json.loads((V/'data.json').read_text());initial=(V/'row-initial-preflight.json');assert not initial.exists();initial.write_bytes((V/'row.json').read_bytes())
path=R/'referces/shizhen/macro-opening-20261027/L01-X.png';aid='MC03-05-repair-v2-first-frame-down'
record=dict(schema_version='agent-generated-image-observation/1',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size_bytes=path.stat().st_size,width=1672,height=941,generator='builtin image_gen.imagegen',tool_identity_claim='builtin only; exact internal model not exposed',fictional_characters=True,platform_admission='NOT_EVALUATED',semantic_review='Parent viewed complete extinguisher and pipe on upper landing, woman back-facing true descent toward visible lower closed door; full-body scale comparable to endpoint',source_path=str(path.relative_to(R)),reference_role='first_frame')
(V/'reference-first-descent-source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
selection=dict(asset_id=aid,node_id=aid+'-node',resource_id=aid+'-local-generated',path=str(path),usage_license='Task-owned existing same-identity descent reference for authorized bounded repair',generated_source=dict(record_path=str((V/'reference-first-descent-source.json').relative_to(R)),record_sha256=hashlib.sha256((V/'reference-first-descent-source.json').read_bytes()).hexdigest(),tool=dict(name='builtin-imagegen',version='tool-interface')))
e=ConditioningCompatibilityEvidence(lane='fl2va',first_anchor_id=aid,last_anchor_id=data['images'][1]['asset_id'],same_subject_scale=True,composition_compatible=True,screen_order_compatible=True,axis_compatible=True,camera_path_reachable=True,character_prop_state_reachable=True,action_endpoint_reachable=True,available_duration_seconds=12)
g=row['generation']['generation_intent'];op='董文慧已在上平台连通的下行梯段上，背对摄影机向较低平台走；上平台带凹痕的灭火器与外露管道同框，下方关闭的门可定位'
g['open_state']['state_text']=op;g['subject_action']['start_state']=op;g=GenerationIntent.model_validate(g).model_dump(mode='json');row['generation']['generation_intent']=g
row['generation']['conditioning_compatibility']=e.model_dump(mode='json');row['generation']['references'][0]=dict(role='approved_keyframe',asset_id=aid)
data['images'][0]=selection;data['scene_images']=[x['asset_id'] for x in data['images']];data['intent_sha256']=canonical_sha256(g)
assessment=dict(kind='explicit-frame-conditioning-assessment/1',row=row,source_identity_sha256='53075b370bc0dd00285d4384e74cd521d8672243a417801f177f807776e69458',compatibility=e.model_dump(mode='json'),rationale={'same_subject_scale':'Both actual references show one full-body figure occupying roughly60 percent of image height; earlier front-facing93-percent-height frame was not selected','composition_compatible':'Normal landing clue is visible left of descending subject, lower closed door locatable; endpoint is the corresponding lower doorway, intentional scene progression','screen_order_compatible':'Single woman, pipe/extinguisher normal-state left and lower doorway after descent; no unexplained subject exchange','axis_compatible':'Back-facing down-flight and camera behind-left at doorway, no reverse upward movement required','camera_path_reachable':'Follow a short flight down, then an explicitly motivated direct cut at completed arrival, within12s','character_prop_state_reachable':'Same woman/outfit, free right hand reaches handle and pushes inward while feet stay outside','action_endpoint_reachable':'Ordinary descent, one door push and restrained pause are the same approved event; endpoint geometry recedes behind threshold'},boundary='Author assessment of compatible endpoint route, not proof that model obeys the intermediate action')
ref=authoring_input_reference(assessment);packet=dict(source_snapshot_sha256=canonical_sha256(assessment),assets=[dict(id=selection['node_id'],type='image',data=dict(resourceId=selection['resource_id']))])
extra,artifacts=prepare_canvas_png_assets(packet=packet,selections=[selection],allowed_asset_root=R)
registry=p.registry.model_copy(update={'assets':(*p.registry.assets,*extra.assets)});rh=registry_semantic_sha256(registry);registry=AssetRegistrySnapshot.model_validate({**registry.model_dump(mode='python'),'revision_id':rh,'content_hash':rh})
project=seal_artifact(p.project.model_copy(update={'revision':p.project.revision+1,'content_hash':'0'*64,'source_provenance':(*p.project.source_provenance,ref)}))
request=prepare_project_registry_commit(manifest=p.manifest,project=project,registry=registry,attempt_id='stair-firstlast-compatible-descent-authoring')
payload=authoring_input_payload(assessment);auth=PreparedArtifact(Path(ref.reference),payload,hashlib.sha256(payload).hexdigest())
request=replace(request,artifacts=tuple(sorted((*request.artifacts,*artifacts,auth),key=lambda a:a.relative_path.as_posix())))
request=prepare_strategy_dependency_transition(base_loaded=p,candidate_loaded=p.model_copy(update={'project':project,'registry':registry}),request=request)
c=ProductionStateCommitter(ROOT);c.commit(request)
cur=load_production_project(ROOT/'project.yaml');old=cur.qa_policy;payload=json.loads(json.dumps(old.generation_acceptance.profile_payload));payload.pop('content_hash');payload['profile_version']='2'
for rule in payload['generation_requirements']:
 k=rule['requirement_id'];rule['native_text_mapping']={'intent_sha256':data['intent_sha256'],'bindings':[dict(intent_path=path,fragment_indices=list(range(len(data['fragments'][k])))) for path in data['paths'][k]]}
h=canonical_sha256(payload);qa=seal_artifact(old.model_copy(update={'revision':old.revision+1,'content_hash':'0'*64,'policy_version':'2','source_provenance':(*old.source_provenance,ref),'generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='2',measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(data['observations']),profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
c.activate_qa_policy(qa,attempt_id='stair-firstlast-compatible-descent-QA',expected_manifest_revision=cur.manifest.manifest_revision)
for name,obj in [('row.json',row),('data.json',data),('conditioning-assessment.json',assessment)]: (V/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'canonical_revision':project.revision,'registry_added_reference':aid,'lane':e.lane.value,'paid_video_calls':0}))
