"""Assemble existing rendered review films; preserve prior qualification failures and scopes."""
from pathlib import Path
import hashlib,json,subprocess
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.project import load_production_project
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,_canonical_yaml_bytes
from ai_video.production.audio import AudioImportRequest,AudioProbeToolchain
R=Path.cwd();H=Path(__file__).resolve().parent;T=R/'runs/shizhen-fusion-B-motion-20261027/project-assembly-rendered-B5-r3'
assert not T.exists()
ff=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
sha=lambda b:hashlib.sha256(b).hexdigest()
old=load_production_project(R/'runs/shizhen-opening-A-revision-20261026/project-r3/project.yaml')
inputs=[('event-render',R/'outputs/shizhen-episode01/opening-A-revision-20261026/variant-R3/失帧-独立开场-空位片名-R3.mp4',489,'587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc'),('title-render',H/'variant-B5/失帧-Fusion片名试片-B5.mp4',144,'f8b3b65e3554ba19a19ce0d5e818445acd21ef98cb29be06f39a7baaa1018067')]
origin={'request':'可以就先这样,拼接起来我看下','scope':'Existing rendered review films, no raw qualification or activation. R3 event prefix only; B5 unchanged. S01 excluded. No new music/video generation.','inputs':[dict(asset_id=i,path=str(p),frames=n,sha256=h) for i,p,n,h in inputs],'known_limits':'Original generated material, AI badge and prior raw QA history retained. Only B5 local appearance accepted by user. Assembly pending review.','source_windows':[[0,184],[184,66],[250,167],[0,144]],'audio':'Embedded final mix decoded without retiming; R3 prefix stops before its old title/fade. B5 music starts source sample128000, matching preceding R3 music offset.'}
ref=authoring_input_reference(origin);prov=(ref,)
def seal(x,**kw):return seal_artifact(x.model_copy(update={**kw,'revision':1,'content_hash':'0'*64,'source_provenance':prov,'creation_receipt_id':'rendered-review-assembly'}))
shots=[]
for s,n in zip(old.shots,[184,66,167,144]):
 aid='title-render' if s.shot_id=='CO-TAIL' else 'event-render'
 shots.append(seal(s,visual_strategy=VisualStrategy.EXISTING_VIDEO,duration_policy=DurationPolicy(mode='fixed',seconds=(n-.000001)/24),generated_video_rationale=None,voice_routing=None,required_asset_roles=(AssetRoleRequirement(role='primary_visual',asset_ids=(aid,),allowed_asset_types=(AssetType.VIDEO,)),)))
chars=[seal(x) for x in old.characters];scenes=[seal(x) for x in old.scenes]
brief=seal(old.brief,objective='将既有事件修订版和用户认可的B5片名合成独立审看片；不含S01、不新增生成、不宣称宏观和真人重制完成')
story=seal(old.story);board=seal(old.storyboard)
models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),*((x,'creative/shots/'+x.shot_id+'.yaml') for x in shots),*((x,'creative/characters/'+x.character_id+'.yaml') for x in chars),*((x,'creative/scenes/'+x.scene_id+'.yaml') for x in scenes)]
def ar(x):return ArtifactReference(artifact_id=x.artifact_id,revision=x.revision,content_hash=x.content_hash,path=Path(next(p for o,p in models if o==x)))
project=seal(old.project,project_id='shizhen-rendered-opening-B5-20261027',title='失帧 独立开场 B5 拼接审看',artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),storyboard=ar(board),characters=tuple(ar(x) for x in chars),scenes=tuple(ar(x) for x in scenes),shots=tuple(ar(x) for x in shots)))
artifacts={};records=[]
def add(p,b):
 p=Path(p)
 if p in artifacts:assert artifacts[p].payload==b
 else:artifacts[p]=PreparedArtifact(p,b,sha(b))
# Retain static character/scene reference dependencies without introducing qualification claims.
for a in old.registry.assets:
 if a.asset_type is AssetType.IMAGE:records.append(a);add(a.artifact_path,old.asset_paths[a.asset_id].read_bytes())
version=subprocess.check_output([str(ff/'ffmpeg'),'-version'],text=True).splitlines()[0].split()[2]
tool=ToolIdentity(name='ffmpeg',version=version)
chain=AudioProbeToolchain(ffmpeg_path=ff/'ffmpeg',ffprobe_path=ff/'ffprobe',ffmpeg=tool,ffprobe=ToolIdentity(name='ffprobe',version=version))
for aid,p,n,expected in inputs:
 raw=p.read_bytes();digest=sha(raw);assert digest==expected
 probe=json.loads(subprocess.check_output([str(ff/'ffprobe'),'-v','error','-show_streams','-of','json',str(p)]))
 v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==n and v['r_frame_rate']=='24/1'
 fp=canonical_sha256({'origin':origin,'asset_id':aid})
 a=AssetRecord(asset_id=aid,asset_type=AssetType.VIDEO,artifact_path=Path('assets/files/'+digest+'.mp4'),sha256=digest,size_bytes=len(raw),mime_type='video/mp4',duration_seconds=n/24,width=1920,height=1080,source_kind=AssetSourceKind.IMPORTED,input_artifact_ids=(project.artifact_id,),tool=ToolIdentity(name='HyperFrames',version='0.7.103'),input_fingerprint=fp,creation_receipt_id=fp,usage_license='Existing local review output only; inherited AI badge, source rights and QA limitations, not approved raw generation or publication.',video_metadata=VideoAssetMetadata(container_name='mp4',codec_name='h264',width=1920,height=1080,fps_numerator=24,fps_denominator=1,duration_milliseconds=round(n/24*1000),frame_count=n,probe_receipt_id='rendered-source-'+fp,request_receipt_fingerprint=fp,resolved_generation_hash=fp,provenance_receipt_id=fp))
 records.append(a);add(a.artifact_path,raw)
 wav=H/('assembly-'+aid+'.wav')
 if not wav.exists():subprocess.run([str(ff/'ffmpeg'),'-n','-v','error','-i',str(p),'-map','0:a:0','-ac','2','-ar','48000','-c:a','pcm_s16le',str(wav)],check=True)
 request=AudioImportRequest(asset_id=aid+'-mix',audio_kind='dialogue',mime_type='audio/wav',source=AudioSource(kind='derived',provider_or_tool=tool,input_artifact_ids=(aid,),input_fingerprint=digest,original_reference='exact-render-MP4:'+digest+':0:a:0'),language='zh',script_hash=sha(b'Existing final rendered review mix, no new speech'),provenance_receipt_id=fp,creation_receipt_id='assembly-source-audio',usage_license='Same review mix decoded to PCM, no gain/time changes; full inherited limitations')
 with wav.open('rb') as f:imp=request.prepare(f.fileno(),toolchain=chain)
 records.append(imp.asset_record);add(imp.asset_record.artifact_path,imp.payload)
registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records));rh=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':rh,'content_hash':rh})
for obj,p in models:add(p,_canonical_yaml_bytes(obj))
add(ref.reference,authoring_input_payload(origin))
T.mkdir(parents=True)
ProductionStateCommitter(T).bootstrap_initial_state(attempt_id='rendered-review-bootstrap',project=project,registry=registry,artifacts=tuple(artifacts.values()))
loaded=load_production_project(T/'project.yaml');assert loaded.project==project
rows=[dict(shot_id=s.shot_id,asset_id=('title-render' if i==3 else 'event-render'),audio_id=('title-render-mix' if i==3 else 'event-render-mix'),start=a,frames=n,transform={}) for i,(s,(a,n)) in enumerate(zip(shots,[(0,184),(184,66),(250,167),(0,144)]))]
(H/'assembly-rendered-input.json').write_text(json.dumps(dict(project=str(T),sources=rows,total_frames=561,origin=origin),ensure_ascii=False,indent=2))
print('Prepared existing-render assembly with immutable sources and retained review-only limits')
