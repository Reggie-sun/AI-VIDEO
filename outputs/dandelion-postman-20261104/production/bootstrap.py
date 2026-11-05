"""Offline canonical bootstrap for this new Postman root, never submit."""
from pathlib import Path
import hashlib,json
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.models import *
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,_canonical_yaml_bytes
from ai_video.production.jimeng_contracts import JimengProfile
HERE=Path(__file__).resolve().parent; BASE=HERE.parent; ROOT=Path.cwd()/'runs/dandelion-postman-20261104'
assert not (ROOT/'project.yaml').exists(), 'Refuse rebootstrap'
read=lambda n:json.loads((HERE/n).read_text())
data=read('data.json');row=read('row.json');operator=read('operator-bound.json')
coverage=json.loads((HERE/'director-coverage.v4.json').read_text());approval=read('preview-approval.json')
assert canonical_sha256(coverage)==data['coverage']['coverage_hash']
envelope={'kind':'dandelion-postman-authoring/1','row':row,'data':data,'bound':operator}
inputs=[envelope,coverage,approval]; refs=[authoring_input_reference(x) for x in inputs]
packet={'source_snapshot_sha256':canonical_sha256(envelope),'assets':[{'id':a['node_id'],'type':'image','data':{'resourceId':a['resource_id']}} for a in data['images']]}
registry,images=prepare_canvas_png_assets(packet=packet,selections=data['images'],allowed_asset_root=Path.cwd())
source=tuple(refs)+tuple(authoring_input_reference(json.loads(a.payload)) for a in images if str(a.relative_path).startswith('evidence/authoring-input/'))
def seal(cls,key,**kw): return seal_artifact(cls(artifact_id='dandelion-postman-'+key,revision=1,content_hash='0'*64,creation_receipt_id='dandelion-postman-'+key+'-authored',source_provenance=source,**kw))
brief=seal(ProductionBrief,'brief',title='蒲公英邮差',objective=data['objective'],audience='微缩动画观众',format='微缩定格动画',language='zh',constraints=tuple(row['shot']['continuity_constraints']))
story=seal(Story,'story',language='zh',logline='小邮差遇见一粒蒲公英种子',synopsis=data['objective'],beats=(StoryBeat(beat_id='postman',summary=data['objective']),))
chars=[seal(Character,'robot',**x) for x in data['characters']]
sc=data['scene'];scene=seal(Scene,'scene',scene_id=sc['scene_id'],location=sc['location'],time='午后',mood=sc['mood'],visual_reference_asset_ids=())
shot=seal(Shot,'shot',**row['shot']);board=seal(Storyboard,'board',beats=(StoryboardBeat(beat_id='postman',scene_id=sc['scene_id'],shot_ids=('postman',),narrative_intent=data['objective']),))
models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),(scene,'creative/scenes/meadow.yaml'),(shot,'creative/shots/postman.yaml'),(chars[0],'creative/characters/postman-robot.yaml')]
def ar(x): return ArtifactReference(artifact_id=x.artifact_id,revision=x.revision,content_hash=x.content_hash,path=Path(next(p for m,p in models if m==x)))
project=seal(ProductionProject,'project',project_id='dandelion-postman-20261104',title='蒲公英邮差',default_language='zh',delivery_profile=DeliveryProfile(width=1920,height=1080,fps=24),renderer_policy=RendererPolicy(),artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),characters=tuple(ar(x) for x in chars),scenes=(ar(scene),),storyboard=ar(board),shots=(ar(shot),)))
obs=data['observations'];payload={'domain_id':'original-drama','measurement_contract_version':'1','profile_id':'dandelion-postman-raw','profile_version':'1','required_requirement_ids':list(obs),'generation_requirements':[{'requirement_id':k,'level':'acceptance','stage':'raw_generation','dimension':k,'observable':v,'tolerance':'逐项满足；未知不算通过','measurement':'Exact project-local video-analysis and frame/audio evidence','proof':'analyzer','intent_paths':data['paths'][k],'native_text':data['fragments'][k],'native_text_mapping':{'intent_sha256':data['intent_sha256'],'bindings':[{'intent_path':p,'fragment_indices':[0]} for p in data['paths'][k]]},'production_owner':'shot_authoring'} for k,v in obs.items()]}
h=canonical_sha256(payload)
qa=seal(QaPolicy,'qa',policy_id='dandelion-postman-raw',policy_version='1',required_layers=('technical','layout','strategy','semantic'),technical_thresholds={'black_luma_max_milli':50,'silence_peak_max_millidb':-60000,'clipping_peak_min_millidb':-100},layout_rules={'safe_area_inset_milli':80,'caption_overflow_tolerance_milli':0},strategy_rules_version='1',semantic_requirement='required',semantic_authorities=({'name':'video-analysis','version':'project-local-current-session'},),generation_evaluation_authorities=({'evaluator':{'name':'video-analysis','version':'project-local-current-session'},'proof':'analyzer'},),generation_acceptance=DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='1',measurement_contract_version='1',required_requirement_ids=tuple(obs),profile_content_hash=h,profile_payload={**payload,'content_hash':h}),final_output=FinalOutputContract(goal_id='dandelion-postman',goal_version='1',user_goal=data['objective'],requirements=tuple({'requirement_id':k,'observable':v,'proof':'human'} for k,v in obs.items())))
def art(p,b):return PreparedArtifact(Path(p),b,hashlib.sha256(b).hexdigest())
ROOT.mkdir(parents=True,exist_ok=True,mode=0o700);c=ProductionStateCommitter(ROOT)
m=c.bootstrap_initial_state(attempt_id='dandelion-postman-bootstrap',project=project,registry=registry,artifacts=tuple([*images,*[art(r.reference,authoring_input_payload(i)) for r,i in zip(refs,inputs)],*[art(p,_canonical_yaml_bytes(x)) for x,p in models]]))
m=initialize_canvas_graph(c,'dandelion-postman-graph');m=c.upgrade_manifest_schema('2.14',expected_manifest_revision=m.manifest_revision);m=c.activate_qa_policy(qa,attempt_id='dandelion-postman-qa',expected_manifest_revision=m.manifest_revision)
loaded=load_production_project(ROOT/'project.yaml')
profile=JimengProfile.model_validate_json((BASE/'native/profile.json').read_bytes())
configuration={'schema_version':'jimeng-feedback-driver/1','row':row,'routing_policy':{'identity':{'policy_id':'dandelion-postman-qualification','policy_version':'1','policy_sha256':canonical_sha256(operator)},'local_resources_available':False,'remote_authorized':True,'budget_authorized':True,'execution_purpose':'qualification'},'decision_policy':{'max_resamples':0,'allow_bounded_exploration':True},'execution_limits':{'task_id':'dandelion-postman-preview','generation_forbidden':False,'allowed_remote_candidates':['jimeng/'+profile.capability_id],'paid_submit_ceiling':1,'paid_submits_used':0,'local_batch_limit':1,'local_batch_used':0,'local_total_used':0,'local_resource_available':False},'jimeng_profile':profile.model_dump(mode='json')}
(HERE/'driver-configuration.json').write_text(json.dumps(configuration,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'root':str(ROOT),'manifest_revision':loaded.manifest.manifest_revision,'video_calls':0}))
