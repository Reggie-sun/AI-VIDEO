"""Import a locally composited shot for an isolated review, without activation."""
from pathlib import Path
import hashlib, json
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact, canonical_sha256
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.project import load_production_project
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, _canonical_yaml_bytes
R=Path.cwd(); H=Path(__file__).resolve().parent
T=R/'runs/shizhen-fusion-title-trial-20261026/project-r5'
old=load_production_project(R/'runs/shizhen-opening-A-revision-20261026/project-r3/project.yaml')
sha=lambda b:hashlib.sha256(b).hexdigest()
origin={'kind':'local-shot-composite-review/1','request':'那你先尝试做下；继续',
 'brief':(H/'design.md').read_text(),'source_mp4_sha256':'750326c44ba58ecd0093c52ff8c7337cb8942f4e3efd9bd61634d3cfe3b119cf',
 'source_frames':[288,359],'fusion_comp_sha256':sha((H/'title-trial.comp').read_bytes()),
 'fusion_version':'21.1.1.10','full_goal_status':'Macro footage and live-action consistency remain unfulfilled',
 'authority':'Shot-compositing review only. No qualification, activation, publication or final acceptance.'}
ref=authoring_input_reference(origin); prov=(ref,)
def seal(x,**kw):
 return seal_artifact(x.model_copy(update={**kw,'source_provenance':prov,'revision':1,'content_hash':'0'*64,'creation_receipt_id':'fusion-local-review'}))
shot=seal(next(s for s in old.shots if s.shot_id=='CO-TAIL'),artifact_id='fusion-title-shot',
 visual_strategy=VisualStrategy.EXISTING_VIDEO,dialogue='',narration='',voice_routing=None,
 generated_video_rationale=None,required_asset_roles=(AssetRoleRequirement(role='primary_visual',asset_ids=('fusion-title-composite',),allowed_asset_types=(AssetType.VIDEO,)),))
brief=seal(old.brief,artifact_id='fusion-title-brief',objective='独立开场尾段 Fusion 局部合成试片；原雨声和音乐窗口不变，完整开场目标仍未通过。')
story=seal(old.story,artifact_id='fusion-title-story',beats=(StoryBeat(beat_id='CO-TAIL',summary=shot.intent),))
board=seal(old.storyboard,artifact_id='fusion-title-board',beats=(StoryboardBeat(beat_id='CO-TAIL',scene_id=shot.scene_id,shot_ids=('CO-TAIL',),narrative_intent=shot.intent),))
chars=[seal(x) for x in old.characters]; scenes=[seal(x) for x in old.scenes]
models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),(shot,'creative/shots/CO-TAIL.yaml'),*((x,'creative/characters/'+x.character_id+'.yaml') for x in chars),*((x,'creative/scenes/'+x.scene_id+'.yaml') for x in scenes)]
def ar(x):return ArtifactReference(artifact_id=x.artifact_id,revision=x.revision,content_hash=x.content_hash,path=Path(next(p for o,p in models if o==x)))
project=seal(old.project,artifact_id='fusion-title-project',project_id='shizhen-fusion-title-trial-20261026',title='失帧 Fusion 单镜合成试片',artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),storyboard=ar(board),characters=tuple(ar(x) for x in chars),scenes=tuple(ar(x) for x in scenes),shots=(ar(shot),)))
artifacts={}
def add(p,b):
 p=Path(p);artifacts[p]=PreparedArtifact(p,b,sha(b))
records=[]
for a in old.registry.assets:
 if a.asset_type in {AssetType.IMAGE,AssetType.MUSIC} or a.asset_id=='CO-TAIL-original-mix':
  records.append(a);add(a.artifact_path,old.asset_paths[a.asset_id].read_bytes())
video=H/'fusion-plate.mp4';raw=video.read_bytes();digest=sha(raw);fp=canonical_sha256(origin)
from ai_video.production.hyperframes import probe_clip_fd_with_executable
with video.open('rb') as f:probe=probe_clip_fd_with_executable(f.fileno(),Path('/home/reggie/.config/jianji/tools/ffmpeg/bin/ffprobe'))
v=next(x for x in probe['streams'] if x['codec_type']=='video')
assert int(v['nb_frames'])==72 and v['width']==1920 and v['height']==1080
a=AssetRecord(asset_id='fusion-title-composite',asset_type=AssetType.VIDEO,artifact_path=Path('assets/files/'+digest+'.mp4'),sha256=digest,size_bytes=len(raw),mime_type='video/mp4',duration_seconds=3,width=1920,height=1080,source_kind=AssetSourceKind.IMPORTED,input_artifact_ids=('CO-TAIL-review-video',),tool=ToolIdentity(name='DaVinci-Resolve-Fusion',version='21.1.1.10'),input_fingerprint=fp,creation_receipt_id=fp,usage_license='Task-owned generated source composited locally; AI badge preserved; review only, original rights and quality limits retained.',video_metadata=VideoAssetMetadata(container_name='mp4',codec_name='h264',width=1920,height=1080,fps_numerator=24,fps_denominator=1,duration_milliseconds=3000,frame_count=72,probe_receipt_id='fusion-probe-'+fp,request_receipt_fingerprint=fp,resolved_generation_hash=fp,provenance_receipt_id=fp))
records.append(a);add(a.artifact_path,raw)
registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records))
h=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':h,'content_hash':h})
for obj,path in models:add(path,_canonical_yaml_bytes(obj))
add(ref.reference,authoring_input_payload(origin))
T.mkdir(parents=True,exist_ok=False)
from ai_video.production.repair_input_admission import verify_repair_input
from ai_video.production.qualification_preview_input import prepare_qualification_preview_input
source=next(a for a in old.registry.assets if a.asset_id=='CO-TAIL-review-video')
admission=verify_repair_input(source,old.root)
registry,source_artifacts=prepare_qualification_preview_input(target_root=T,project=project,registry=registry,source_root=R/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A3',source_attempt_id='shizhen-CO-A3-qualification-001',source_sha256=source.sha256,asset_id=source.asset_id,usage_license='Unchanged generated source retained as explicit provenance and original audio dependency, not active visual',preview_use=dict(shot_id='CO-TAIL',asset_role='primary_visual',trim_start_frame=288,trim_duration_frames=72,source_time_map=dict(contract_version='video-time-map/1',audio_policy='mute',points=[dict(source_frame=0,output_frame=0),dict(source_frame=72,output_frame=72)]),transform={},scope='replacement_audio_preview'),preview_probe=admission.preview_probe)
for artifact in source_artifacts:add(artifact.relative_path,artifact.payload)
ProductionStateCommitter(T).bootstrap_initial_state(attempt_id='fusion-local-bootstrap',project=project,registry=registry,artifacts=tuple(artifacts.values()))
loaded=load_production_project(T/'project.yaml');assert loaded.project==project
(H/'input-receipt.json').write_text(json.dumps({'project':str(T),'sources':[{'shot_id':'CO-TAIL','asset_id':a.asset_id,'start':0,'frames':72,'audio_id':'CO-TAIL-original-mix','audio_start':288,'transform':{}}],'music_asset_id':'two-passengers-missing-response-B','scope':'local compositing review only','origin':origin},ensure_ascii=False,indent=2))
print('Isolated shot review project prepared')
