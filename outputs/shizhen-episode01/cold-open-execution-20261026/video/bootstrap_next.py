"""Small task caller: ordinary Director data into existing Production owners."""
from pathlib import Path
from datetime import datetime
import json,hashlib,sys
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.models import *
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,_canonical_yaml_bytes
V=Path(__file__).resolve().parent;DATA=V.parent;RUN=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001'
def main(label):
 assert label in {'CO-A2','CO-A3'};root=RUN/'cold-open-execution'/label;assert not (root/'project.yaml').exists()
 data=json.loads((V/(label+'-data.json')).read_text());row=json.loads((V/(label+'-row.json')).read_text());bound=json.loads((V/'operator-bound-cross-window.json').read_text());assert datetime.now().astimezone()<datetime.fromisoformat(bound['expires_at'])
 gate=json.loads((DATA/'qa'/data['predecessor_gate']).read_text());assert gate['verdict']=='PASS' and all(x['verdict']=='PASS' for x in gate['required_findings']);assert hashlib.sha256(Path(gate['artifact_path']).read_bytes()).hexdigest()==gate['artifact_sha256']
 old=load_production_project(RUN/'trial-S02-v1/project.yaml');hist=[load_production_project(RUN/p/'project.yaml') for p in ['trial-S01-v3','trial-S02-v1','cold-open-execution/CO-A1','trial-S03-v2']+(['cold-open-execution/CO-A2'] if label=='CO-A3' else [])]
 calls=[a for p in hist for a in p.manifest.attempts if a.operation=='video_generation'];assert len(calls)==data['historical_video_calls'] and len(calls)<bound['new_film_video_ceiling'];assert all(a.paid_provider_state and a.paid_provider_state.phase.value not in {'outcome_unknown','submit_intent'} for a in calls)
 envelope={'kind':'cold-open-successor-authoring/1','row':row,'data':data,'bound':bound,'predecessor_gate':gate,'ancestors':[{'root':str(p.root),'manifest_sha256':hashlib.sha256((p.root/'state/manifest.json').read_bytes()).hexdigest(),'calls':[a.attempt_id for a in p.manifest.attempts if a.operation=='video_generation']} for p in hist],'authority':'development qualification only; no Production activation or fake accepted-source lineage'};ref=authoring_input_reference(envelope)
 packet={'source_snapshot_sha256':canonical_sha256(envelope),'assets':[{'id':a['node_id'],'type':'image','data':{'resourceId':a['resource_id']}} for a in data['images']]}
 registry,images=prepare_canvas_png_assets(packet=packet,selections=data['images'],allowed_asset_root=DATA);source=(ref,*(authoring_input_reference(json.loads(a.payload)) for a in images if str(a.relative_path).startswith('evidence/authoring-input/')))
 def seal(cls,key,**kw):return seal_artifact(cls(artifact_id='shizhen-'+label+'-'+key,revision=1,content_hash='0'*64,creation_receipt_id='shizhen-'+label+'-'+key+'-authored',source_provenance=source,**kw))
 brief=seal(ProductionBrief,'brief',title='失帧 两位 '+label,objective=data['objective'],audience='都市灵异短剧观众',format='电影级原创3D国漫写实',language='zh',constraints=('保护原S01及结尾反转','不增加规则；不保留第二位记忆者','exact前序Gate通过才提交'))
 story=seal(Story,'story',language='zh',logline='两位普通同事被现实改写成一位',synopsis=data['objective'],beats=(StoryBeat(beat_id=row['shot']['storyboard_beat_id'],summary=data['objective']),))
 chars=[seal(Character,'character-'+x['character_id'],**x) for x in data['characters']]
 scene=seal(Scene,'scene',scene_id='rain-stop',location='临江玻璃接车站棚',time='前一夜2026-10-24雨夜',mood='雨夜普通候车，人物不预知异常',visual_reference_asset_ids=tuple(data.get('scene_images',[data['scene_image']])))
 shot=seal(Shot,'shot',**row['shot']);board=seal(Storyboard,'board',beats=(StoryboardBeat(beat_id=row['shot']['storyboard_beat_id'],scene_id='rain-stop',shot_ids=(label,),narrative_intent=data['objective']),))
 models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),(scene,'creative/scenes/rain-stop.yaml'),(shot,'creative/shots/'+label+'.yaml'),*((x,'creative/characters/'+x.character_id+'.yaml') for x in chars)]
 def ar(m):return ArtifactReference(artifact_id=m.artifact_id,revision=m.revision,content_hash=m.content_hash,path=Path(next(p for x,p in models if x==m)))
 p=seal_artifact(ProductionProject(artifact_id='shizhen-project-'+label,revision=1,content_hash='0'*64,creation_receipt_id='shizhen-'+label+'-bootstrap',source_provenance=source,project_id='shizhen-cold-open-'+label+'-20261026',title='失帧 两位 '+label,default_language='zh',delivery_profile=DeliveryProfile(width=1920,height=1080,fps=24),renderer_policy=RendererPolicy(),artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),characters=tuple(ar(x) for x in chars),scenes=(ar(scene),),storyboard=ar(board),shots=(ar(shot),))))
 payload={k:v for k,v in old.qa_policy.generation_acceptance.profile_payload.items() if k not in {'content_hash','generation_requirements'}};obs=data['observations'];payload.update(profile_id='shizhen-'+label+'-raw',profile_version='1',required_requirement_ids=list(obs),generation_requirements=[{'requirement_id':k,'level':'acceptance','stage':'raw_generation','dimension':k,'observable':v,'tolerance':'逐项满足；导演表演偏好不变成硬秒点','measurement':'Exact project-local video-analysis, qualified audio observations and frame sequence; no fabricated human review','proof':'analyzer','intent_paths':data['paths'][k],'production_owner':'shot_authoring'} for k,v in obs.items()]);h=canonical_sha256(payload)
 qa=seal_artifact(old.qa_policy.model_copy(update={'artifact_id':'shizhen-'+label+'-qa','revision':1,'policy_id':'shizhen-'+label+'-raw','policy_version':'1','generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='1',measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(obs),profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
 def art(path,b):return PreparedArtifact(Path(path),b,hashlib.sha256(b).hexdigest())
 root.mkdir(parents=True,exist_ok=True,mode=0o700);c=ProductionStateCommitter(root);m=c.bootstrap_initial_state(attempt_id='shizhen-'+label+'-bootstrap',project=p,registry=registry,artifacts=tuple([*images,art(ref.reference,authoring_input_payload(envelope)),*(art(path,_canonical_yaml_bytes(x)) for x,path in models)]));m=initialize_canvas_graph(c,'shizhen-'+label+'-graph');m=c.upgrade_manifest_schema('2.14',expected_manifest_revision=m.manifest_revision);m=c.activate_qa_policy(qa,attempt_id='shizhen-'+label+'-qa',expected_manifest_revision=m.manifest_revision)
 print(json.dumps({'root':str(root),'manifest_revision':m.manifest_revision,'historical_calls':len(calls),'new_calls':0}))
if __name__=='__main__':main(sys.argv[1])
