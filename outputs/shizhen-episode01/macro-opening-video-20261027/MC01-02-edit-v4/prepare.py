"""Capture exact qualification footage for a bounded editorial preview, never promotion."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import hashlib, json, subprocess
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact, canonical_sha256
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.project import load_production_project
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, _canonical_yaml_bytes
from ai_video.production.qualification_preview_input import prepare_qualification_preview_input
from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt
from ai_video.production.video import ResolvedVideoGenerationRequest, VideoFetchReceipt
from ai_video.production.hyperframes import probe_clip_fd_with_executable
from ai_video.production.audio import AudioImportRequest, AudioProbeToolchain

R=Path.cwd(); H=Path(__file__).resolve().parent
T=R/'runs/shizhen-macro-opening-20261027/MC01-02-edit-v4/project'
OLD=R/'runs/shizhen-macro-opening-20261027/MC01-02-1080p-v3'
FF=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert not (T/'project.yaml').exists() and not list(T.rglob('*')), 'Only an empty known pre-bootstrap directory may be reused'
p=load_production_project(OLD/'project.yaml')
a=next(a for a in p.manifest.attempts if a.attempt_id=='shizhen-macro-MC01-02-1080p-approved-003')
state=a.video_generation_state; media=p.root/state.fetch_receipt.artifact_path
raw=media.read_bytes(); digest=sha(raw)
assert digest=='88564a7f7399edc432dbe25778c762f48f65217524ddad67c913331628eb0e52'
windows=[dict(shot_id='MC01-W',asset_id='hd-wide-capture',start=0,frames=104),dict(shot_id='MC02-C',asset_id='hd-close-capture',start=132,frames=60)]
origin={'kind':'bounded-editorial-repair/1','user_request':'这个不能剪辑吗','failed_source_sha256':digest,'original_gate':'MC01-02-1080p-v3/qa/post-media-gate.json','edit':'Remove source [104,132) on the 24fps delivery grid, preserving original-speed [0,104) and [132,192). Direct cut, no dissolve, retiming, repeated frames, new footage or music. Keep same-window native sound at unity gain.','windows':windows,'scope':'development_audio_preview, inherited raw FAIL and NOT_EVALUATED retained; not Production acceptance','new_video_submissions':0,'review_extension':{'previous_rounds':3,'maximum_total_rounds':4,'reason':'New explicit user feedback identifies HD dissolve; one local deterministic cut candidate with exact new media, no generation loop'}}
origin=json.loads(json.dumps(origin)); ref=authoring_input_reference(origin); prov=(ref,)
def seal(x,**changes):
 return seal_artifact(x.model_copy(update={**changes,'revision':1,'content_hash':'0'*64,'source_provenance':prov,'creation_receipt_id':'macro-hd-editorial-cut'}))
shots=[]
for i,w in enumerate(windows):
 shots.append(seal(p.shots[0],artifact_id='macro-cut-'+w['shot_id'],shot_id=w['shot_id'],storyboard_beat_id='macro-cut-'+str(i),intent=('保留原片停机、门继续右移和工人确认观察的完整动作' if i==0 else '直接切入原片干净连接近景，保留随后受力变化'),duration_policy=DurationPolicy(mode='fixed',seconds=(w['frames']-.000001)/24)))
chars=[seal(x) for x in p.characters]; scenes=[seal(x) for x in p.scenes]
brief=seal(p.brief,objective='修剪原1080p片的叠化重影，直接接入干净近景，保留其余原速声画，不追加生成')
story=seal(p.story,beats=tuple(StoryBeat(beat_id=s.storyboard_beat_id,summary=s.intent) for s in shots))
board=seal(p.storyboard,beats=tuple(StoryboardBeat(beat_id=s.storyboard_beat_id,scene_id=s.scene_id,shot_ids=(s.shot_id,),narrative_intent=s.intent) for s in shots))
models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),*((x,'creative/shots/'+x.shot_id+'.yaml') for x in shots),*((x,'creative/characters/'+x.character_id+'.yaml') for x in chars),*((x,'creative/scenes/'+x.scene_id+'.yaml') for x in scenes)]
def ar(x):return ArtifactReference(artifact_id=x.artifact_id,revision=x.revision,content_hash=x.content_hash,path=Path(next(path for obj,path in models if obj==x)))
project=seal(p.project,project_id='shizhen-macro-hd-editorial-v4',title='失帧 市政异常 1080p 剪辑修订04',artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),storyboard=ar(board),characters=tuple(ar(x) for x in chars),scenes=tuple(ar(x) for x in scenes),shots=tuple(ar(x) for x in shots)))
artifacts={}
def add(path,data):
 path=Path(path)
 if path in artifacts:assert artifacts[path].payload==data
 else:artifacts[path]=PreparedArtifact(path,data,sha(data))
records=[x for x in p.registry.assets if x.asset_type is AssetType.IMAGE]
for x in records:add(x.artifact_path,p.asset_paths[x.asset_id].read_bytes())
registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records))
rh=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':rh,'content_hash':rh})
request=ResolvedVideoGenerationRequest.model_validate_json((p.root/state.request.path).read_bytes())
fetch=VideoFetchReceipt.model_validate_json((p.root/state.fetch_receipt.path).read_bytes())
with media.open('rb') as f:probe=probe_clip_fd_with_executable(f.fileno(),FF/'ffprobe')
v=next(x for x in probe['streams'] if x['codec_type']=='video');fps=Fraction(v['avg_frame_rate'])
measured=MeasuredVideoMetadata(container_name='mp4',codec_name=v['codec_name'],width=v['width'],height=v['height'],fps_numerator=fps.numerator,fps_denominator=fps.denominator,frame_count=int(v['nb_frames']),duration_milliseconds=int((Decimal(v['duration'])*1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP)),audio_stream_count=sum(x['codec_type']=='audio' for x in probe['streams']),size_bytes=len(raw),artifact_sha256=digest)
vp=VideoProbeReceipt.create(request=request,fetch_receipt=fetch,measured=measured)
version=subprocess.check_output([str(FF/'ffmpeg'),'-version'],text=True).splitlines()[0].split()[2]
tool=ToolIdentity(name='ffmpeg',version=version)
chain=AudioProbeToolchain(ffmpeg_path=FF/'ffmpeg',ffprobe_path=FF/'ffprobe',ffmpeg=tool,ffprobe=ToolIdentity(name='ffprobe',version=version))
wav=H/'source-native-48k.wav'
if wav.exists():
 import wave
 with wave.open(str(wav)) as f:existing=f.readframes(f.getnframes());assert (f.getframerate(),f.getnchannels(),f.getsampwidth())==(48000,2,2)
 current=subprocess.check_output([str(FF/'ffmpeg'),'-v','error','-i',str(media),'-map','0:a:0','-vn','-ar','48000','-ac','2','-f','s16le','pipe:1']);assert existing==current
else:subprocess.run([str(FF/'ffmpeg'),'-n','-v','error','-i',str(media),'-map','0:a:0','-vn','-ar','48000','-ac','2','-c:a','pcm_s16le',str(wav)],check=True)
T.mkdir(parents=True,mode=0o700,exist_ok=True)
for w in windows:
 n=w['frames']; use=dict(shot_id=w['shot_id'],asset_role='primary_visual',trim_start_frame=w['start'],trim_duration_frames=n,source_time_map={'contract_version':'video-time-map/1','audio_policy':'mute','points':[{'source_frame':0,'output_frame':0},{'source_frame':n,'output_frame':n}]},transform={},scope='replacement_audio_preview')
 registry,captured=prepare_qualification_preview_input(target_root=T,project=project,registry=registry,source_root=p.root,source_attempt_id=a.attempt_id,source_sha256=digest,asset_id=w['asset_id'],usage_license='Exact task-owned fetched qualification trial, development editorial preview only; raw FAIL/unknown audio acceptance retained',preview_use=use,preview_probe=vp)
 for x in captured:add(x.relative_path,x.payload)
 w['audio_id']=w['shot_id']+'-original-mix'
 fp=canonical_sha256({'source_mp4_sha256':digest,'audio_sha256':sha(wav.read_bytes()),'shot_id':w['shot_id'],'processing':'Full native stereo decode/resample48k, no gain/fade/retime'})
 req=AudioImportRequest(asset_id=w['audio_id'],audio_kind='dialogue',mime_type='audio/wav',source=AudioSource(kind='derived',provider_or_tool=tool,input_artifact_ids=(w['asset_id'],),input_fingerprint=digest,original_reference='exact-MP4:'+digest+':0:a:0'),language='zh',script_hash=sha(b''),provenance_receipt_id=fp,creation_receipt_id=w['audio_id'],usage_license='Same source environmental mix; dialogue is the existing captured native-mix transport role, no speech added')
 with wav.open('rb') as f:imp=req.prepare(f.fileno(),toolchain=chain)
 assets=(*registry.assets,imp.asset_record);registry=registry.model_copy(update={'assets':assets});rh=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':rh,'content_hash':rh});add(imp.asset_record.artifact_path,imp.payload)
for obj,path in models:add(path,_canonical_yaml_bytes(obj))
add(ref.reference,authoring_input_payload(origin))
ProductionStateCommitter(T).bootstrap_initial_state(attempt_id='macro-hd-cut-bootstrap',project=project,registry=registry,artifacts=tuple(artifacts.values()))
assert load_production_project(T/'project.yaml').project==project
(H/'input-receipt.json').write_text(json.dumps({'project':str(T),'sources':windows,'total_frames':164,'source_sha256':digest,'origin':origin},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prepared':True,'frames':164,'seconds':164/24,'new_paid_video_calls':0}))
