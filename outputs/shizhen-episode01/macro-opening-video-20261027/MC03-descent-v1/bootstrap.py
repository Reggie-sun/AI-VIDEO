"""Task data through existing Production bootstrap owners; no submission."""
from pathlib import Path
import json,hashlib
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.models import *
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,_canonical_yaml_bytes
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-descent-v1';label='MC03-DESCENT'
assert not (ROOT/'project.yaml').exists()
data=json.loads((V/'data.json').read_text());row=json.loads((V/'row.json').read_text());bound=json.loads((V/'operator-bound.json').read_text());audit=json.loads((V.parent/'historical-generation-audit.json').read_text())
envelope={'kind':'shizhen-macro-authoring/1','row':row,'data':data,'bound':bound,'history_audit_sha256':hashlib.sha256((V.parent/'historical-generation-audit.json').read_bytes()).hexdigest(),'authority':'user requested generation; bounded qualification preview only, no production activation'};ref=authoring_input_reference(envelope)
packet={'source_snapshot_sha256':canonical_sha256(envelope),'assets':[{'id':a['node_id'],'type':'image','data':{'resourceId':a['resource_id']}} for a in data['images']]}
registry,images=prepare_canvas_png_assets(packet=packet,selections=data['images'],allowed_asset_root=Path.cwd());source=(ref,*(authoring_input_reference(json.loads(a.payload)) for a in images if str(a.relative_path).startswith('evidence/authoring-input/')))
def seal(cls,key,**kw):return seal_artifact(cls(artifact_id='shizhen-macro-'+label+'-'+key,revision=1,content_hash='0'*64,creation_receipt_id='shizhen-macro-'+label+'-'+key+'-authored',source_provenance=source,**kw))
brief=seal(ProductionBrief,'brief',title='失帧 独立冷开场 楼梯异常',objective=data['objective'],audience='都市灵异悬疑剧观众',format='可信真人摄影',language='zh',constraints=tuple(row['shot']['continuity_constraints']))
story=seal(Story,'story',language='zh',logline='下楼之后，熟悉凹痕旁的管道消失',synopsis=data['objective'],beats=(StoryBeat(beat_id=row['shot']['storyboard_beat_id'],summary=data['objective']),))
chars=[seal(Character,'character-'+x['character_id'],**x) for x in data['characters']]
scene=seal(Scene,'scene',scene_id='residential-switchback',location='雨夜老住宅折返楼梯与防火门',time='雨夜',mood='普通下行路径出现熟悉细节的缺失',visual_reference_asset_ids=tuple(data['scene_images']))
shot=seal(Shot,'shot',**row['shot']);board=seal(Storyboard,'board',beats=(StoryboardBeat(beat_id=row['shot']['storyboard_beat_id'],scene_id='residential-switchback',shot_ids=(label,),narrative_intent=data['objective']),))
models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),(scene,'creative/scenes/residential-switchback.yaml'),(shot,'creative/shots/'+label+'.yaml'),*((x,'creative/characters/'+x.character_id+'.yaml') for x in chars)]
def ar(m):return ArtifactReference(artifact_id=m.artifact_id,revision=m.revision,content_hash=m.content_hash,path=Path(next(p for x,p in models if x==m)))
p=seal_artifact(ProductionProject(artifact_id='shizhen-macro-project-'+label,revision=1,content_hash='0'*64,creation_receipt_id='shizhen-macro-'+label+'-bootstrap',source_provenance=source,project_id='shizhen-macro-'+label+'-descent-v1-20261027',title='失帧 独立冷开场 楼梯异常',default_language='zh',delivery_profile=DeliveryProfile(width=1920,height=1080,fps=24),renderer_policy=RendererPolicy(),artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),characters=tuple(ar(x) for x in chars),scenes=(ar(scene),),storyboard=ar(board),shots=(ar(shot),))))
old=load_production_project('runs/shizhen-episode01-jimeng25-20261025-001/trial-S02-v1/project.yaml');payload={k:v for k,v in old.qa_policy.generation_acceptance.profile_payload.items() if k not in {'content_hash','generation_requirements'}};obs=data['observations']
payload.update(profile_id='shizhen-macro-'+label+'-raw',profile_version='1',required_requirement_ids=list(obs),generation_requirements=[{'requirement_id':k,'level':'acceptance','stage':'raw_generation','dimension':k,'observable':v,'tolerance':'逐项满足原分镜与完整动作；不凭静态图片或工具成功推断视频通过','measurement':'Exact project-local video-analysis plus frame sequences and qualified audio observations','proof':'analyzer','intent_paths':data['paths'][k],'native_text':data['fragments'][k],'native_text_mapping':{'intent_sha256':data['intent_sha256'],'bindings':[{'intent_path':path,'fragment_indices':list(range(len(data['fragments'][k])))} for path in data['paths'][k]]},'production_owner':'shot_authoring'} for k,v in obs.items()]);h=canonical_sha256(payload)
final=FinalOutputContract(goal_id='shizhen-independent-macro-opening',goal_version='20261027-second-event',user_goal=data['objective'],requirements=tuple({'requirement_id':k,'observable':v,'proof':'human'} for k,v in obs.items()))
qa=seal_artifact(old.qa_policy.model_copy(update={'artifact_id':'shizhen-macro-'+label+'-qa','revision':1,'source_provenance':source,'policy_id':'shizhen-macro-'+label+'-raw','policy_version':'1','final_output':final,'generation_acceptance':DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='1',measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(obs),profile_content_hash=h,profile_payload={**payload,'content_hash':h})}))
def art(path,b):return PreparedArtifact(Path(path),b,hashlib.sha256(b).hexdigest())
ROOT.mkdir(parents=True,exist_ok=True,mode=0o700);c=ProductionStateCommitter(ROOT);m=c.bootstrap_initial_state(attempt_id='shizhen-macro-'+label+'-bootstrap',project=p,registry=registry,artifacts=tuple([*images,art(ref.reference,authoring_input_payload(envelope)),*(art(path,_canonical_yaml_bytes(x)) for x,path in models)]));m=initialize_canvas_graph(c,'shizhen-macro-'+label+'-graph');m=c.upgrade_manifest_schema('2.14',expected_manifest_revision=m.manifest_revision);m=c.activate_qa_policy(qa,attempt_id='shizhen-macro-'+label+'-qa',expected_manifest_revision=m.manifest_revision)
print(json.dumps({'root':str(ROOT),'manifest_revision':m.manifest_revision,'new_video_calls':0}))
