"""Data-only bootstrap caller over canonical Production owners, no generation I/O."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.models import *
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,_canonical_yaml_bytes
V=Path(__file__).resolve().parent; DATA=V.parent; REPO=Path.cwd();RUN=REPO/'runs/shizhen-episode01-jimeng25-20261025-001'
ROOT=RUN/'cold-open-execution/CO-A1'
def dump(name,x):
 p=V/name
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def art(path,raw):return PreparedArtifact(Path(path),raw,hashlib.sha256(raw).hexdigest())
def main():
 if (ROOT/'project.yaml').exists():raise RuntimeError('Already bootstrapped; strict reopen only')
 old=load_production_project(RUN/'trial-S02-v1/project.yaml');s01=load_production_project(RUN/'trial-S01-v3/project.yaml')
 histories=[a for p in (s01,old) for a in p.manifest.attempts if a.operation=='video_generation'];assert len(histories)==6
 assert all(a.paid_provider_state and a.paid_provider_state.phase.value not in {'outcome_unknown','submit_intent'} for a in histories)
 row=json.loads((V/'CO-A1-row.json').read_text());i=row['generation']['generation_intent'];now=datetime.now(timezone.utc)
 bound={'authority':'current-task-parent-bounded-operator','authorization_quote':'开始做吧','model_id':'seedance_2.5','provider':'jimeng','old_video_submit_count':6,'old_film_video_ceiling':6,'new_film_video_ceiling':9,'new_cold_open_submit_ceiling':3,'per_shot_initial_submit_ceiling':1,'automatic_retries':0,'initial_submit_ceiling':1,'per_call_credit_upper_bound':1500,'project_credit_upper_bound':4500,'historical_internal_bound_CRD':5000,'combined_internal_bound_CRD':9500,'currency':'CRD','credit_microunits':1000000,'issued_at':now.isoformat(),'expires_at':(now+timedelta(hours=3)).isoformat(),'settled_cost':'UNKNOWN','scope':'Three new logical cold-open components, one call each; all six ancestors retained and counted; no Production qualification claim'}
 bound=json.loads((V/'operator-bound.json').read_text()) if (V/'operator-bound.json').exists() else bound
 if not (V/'operator-bound.json').exists():dump('operator-bound.json',bound)
 envelope={'kind':'cold-open-authoring/1','authorization':'用户：开始做吧；已接受Rhythm02','row':row,'bound':bound,'ancestor_roots':[{'path':str(p.root),'manifest_sha256':hashlib.sha256((p.root/'state/manifest.json').read_bytes()).hexdigest(),'attempts':[a.model_dump(mode='json') for a in p.manifest.attempts if a.operation=='video_generation']} for p in (s01,old)],'source_origin':'new typed creative authoring, not a claim of previously generated platform resource','art':json.loads((V/'CO-A1-images.json').read_text())}
 ref=authoring_input_reference(envelope);source=(ref,)
 packet={'source_snapshot_sha256':canonical_sha256(envelope),'assets':[{'id':'co-before-image-node','type':'image','data':{'resourceId':'co-before-local-generated'}},{'id':'co-truck-image-node','type':'image','data':{'resourceId':'co-truck-local-generated'}}]}
 registry,images=prepare_canvas_png_assets(packet=packet,selections=envelope['art'],allowed_asset_root=DATA)
 source=(ref,*(authoring_input_reference(json.loads(a.payload)) for a in images if str(a.relative_path).startswith('evidence/authoring-input/')))
 def seal(cls,label,**kw):return seal_artifact(cls(artifact_id='shizhen-CO-A1-'+label,revision=1,content_hash='0'*64,creation_receipt_id='shizhen-CO-A1-'+label+'-authored',source_provenance=source,**kw))
 brief=seal(ProductionBrief,'brief',title='失帧 两位 CO-A1',objective='以两位普通人的短暂关心建立后续缺席的具体对象',audience='都市灵异短剧观众',format='电影级原创3D国漫写实',language='zh',constraints=('前一夜至翌夜，原世界观与结尾保留','本单元只到遮挡，不提前失踪','S01原片原音字幕不重生'))
 story=seal(Story,'story',language='zh',logline='普通同事雨夜等车，现实即将改写两人一起回家的关系',synopsis='第一动态组件：两位、关心路滑、货车遮满；后续才发生缺席并自然回答一位。',beats=(StoryBeat(beat_id='before',summary='普通同事两位，短暂关心，车厢遮挡'),))
 chars=[seal(Character,'character-'+c['character_id'],**c) for c in json.loads((V/'CO-A1-direction.json').read_text())['characters']]
 scene=seal(Scene,'scene',scene_id='rain-stop',location='临江玻璃接车站棚',time='前一夜2026-10-24雨夜',mood='普通候车、疲倦而清醒',visual_reference_asset_ids=('co-before-image',))
 shot=seal(Shot,'shot',**row['shot']);sb=seal(Storyboard,'storyboard',beats=(StoryboardBeat(beat_id='before',scene_id='rain-stop',shot_ids=('CO-A1',),narrative_intent='先给两人具体关系，保住后续缺席对照空间'),))
 models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),*((c,'creative/characters/'+c.character_id+'.yaml') for c in chars),(scene,'creative/scenes/rain-stop.yaml'),(shot,'creative/shots/CO-A1.yaml'),(sb,'creative/storyboard.yaml')]
 def aref(m):return ArtifactReference(artifact_id=m.artifact_id,revision=m.revision,content_hash=m.content_hash,path=Path(next(p for x,p in models if x==m)))
 project=seal_artifact(ProductionProject(artifact_id='shizhen-project-CO-A1',revision=1,content_hash='0'*64,creation_receipt_id='shizhen-CO-A1-bootstrap',source_provenance=source,project_id='shizhen-cold-open-CO-A1-20261026',title='失帧 两位 CO-A1 前态',default_language='zh',delivery_profile=DeliveryProfile(width=1920,height=1080,fps=24),renderer_policy=RendererPolicy(),artifacts=ProjectArtifactRefs(brief=aref(brief),story=aref(story),characters=tuple(aref(c) for c in chars),scenes=(aref(scene),),storyboard=aref(sb),shots=(aref(shot),))))
 observations={'relationship':'两位普通同事清楚在场，先通话后关心，普通候车目标成立，无额外人物。','action':i['subject_action']['progression'],'identity':'同实际首帧的高峥和罗敏成年CG脸、服装、眼镜和各自包保持，罗敏左手手机贴左耳。','camera':'固定同一机位，出口与地面在遮挡前可读，车厢左向右经过最终完全填满画面，不靠切镜或黑屏。','performance':'先听见再回应目光，自然站立与口型，不加速、不呆脸、不预知恐惧。','sound':'仅两句完整中文，罗敏先说师傅，我们在站里，两位。高峥后说让他别急，路滑。说话人与口型正确，无抢词、串声、额外对白、音乐或突然全局静音；雨和车流可辨。','story-scope':'此组件不实际消失，不走开、上车、烟化或变透明；无片名、字幕和精确时钟数字，准确时间由后期完成。','art':'两名人物与站棚、背景保持同一原创电影级3D国漫写实语言，成人比例、CG眼睑发丝与真实湿材质，不变成真人或蜡像。'}
 paths={'relationship':['generation_intent.subject_action.progression'],'action':['generation_intent.subject_action.progression'],'identity':['generation_intent.identity_continuity.preservation'],'camera':['generation_intent.camera_intent.framing_intent'],'performance':['generation_intent.performance_intent'],'sound':['generation_intent.dialogue_intent.turns','generation_intent.ambience_intent'],'story-scope':['generation_intent.scene_continuity.state_constraints'],'art':['generation_intent.visual_treatment']}
 payload={k:v for k,v in old.qa_policy.generation_acceptance.profile_payload.items() if k not in {'content_hash','generation_requirements'}}
 payload.update(profile_id='shizhen-CO-A1-raw',profile_version='1',required_requirement_ids=list(observations),generation_requirements=[{'requirement_id':k,'level':'acceptance','stage':'raw_generation','dimension':k,'observable':v,'tolerance':'逐项满足，不能以总分抵消缺陷；表演偏好不变硬deadline','measurement':'Exact MP4 project-local video-analysis plus normal-speed audio/visual observations; missing evidence stays NOT_EVALUATED','proof':'analyzer','intent_paths':paths[k],'production_owner':'shot_authoring'} for k,v in observations.items()])
 h=canonical_sha256(payload);acceptance=DomainAcceptancePolicy(domain_id=payload['domain_id'],profile_id=payload['profile_id'],profile_version='1',measurement_contract_version=payload['measurement_contract_version'],required_requirement_ids=tuple(observations),profile_content_hash=h,profile_payload={**payload,'content_hash':h})
 qa=seal_artifact(old.qa_policy.model_copy(update={'artifact_id':'shizhen-CO-A1-qa','revision':1,'policy_id':'shizhen-CO-A1-raw','policy_version':'1','generation_acceptance':acceptance}));
 if not (V/'CO-A1-qa-policy.json').exists():dump('CO-A1-qa-policy.json',qa.model_dump(mode='json'))
 ROOT.mkdir(parents=True,mode=0o700,exist_ok=True);c=ProductionStateCommitter(ROOT)
 m=c.bootstrap_initial_state(attempt_id='shizhen-CO-A1-bootstrap',project=project,registry=registry,artifacts=tuple([*images,art(ref.reference,authoring_input_payload(envelope)),*(art(p,_canonical_yaml_bytes(x)) for x,p in models)]))
 m=initialize_canvas_graph(c,'shizhen-CO-A1-graph');m=c.upgrade_manifest_schema('2.14',expected_manifest_revision=m.manifest_revision);m=c.activate_qa_policy(qa,attempt_id='shizhen-CO-A1-qa',expected_manifest_revision=m.manifest_revision)
 loaded=load_production_project(ROOT/'project.yaml');print(json.dumps({'canonical_root':str(ROOT),'registry_assets':len(loaded.registry.assets),'manifest_revision':m.manifest_revision,'old_paid_calls_counted':6,'new_paid_calls':0}))
if __name__=='__main__':main()
