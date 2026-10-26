"""Exact-source editorial repair and title preparation via existing Production owners."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,ROUND_HALF_UP
import hashlib,json,subprocess
from ai_video.production.models import *
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact,canonical_sha256
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,_canonical_yaml_bytes,prepare_audio_registry_commit
from ai_video.production.qualification_preview_input import prepare_qualification_preview_input
from ai_video.production.video_artifact import MeasuredVideoMetadata,VideoProbeReceipt
from ai_video.production.video import ResolvedVideoGenerationRequest,VideoFetchReceipt
from ai_video.production.hyperframes import probe_clip_fd_with_executable
from ai_video.production.audio import AudioImportRequest,AudioProbeToolchain,probe_audio_candidate
from ai_video.production.suno_music import music_asset_record,direct_music,SceneMusicBrief,generation_identity
V=Path(__file__).resolve().parent;D=V.parent;RUN=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001';T=RUN/'cold-open-composition-v1/project';TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
def sha(b):return hashlib.sha256(b).hexdigest()
def art(p,b):return PreparedArtifact(Path(p),b,sha(b))
def main():
 resume=(T/'project.yaml').exists()
 loaded=[load_production_project(RUN/'cold-open-execution'/x/'project.yaml') for x in ['CO-A1','CO-A2','CO-A3']];s01=load_production_project(RUN/'caption-review-005/project/project.yaml');sources=[*loaded,s01];master=loaded[0]
 windows=[{'shot_id':'CO-A1','asset_id':'CO-A1-review-video','raw_root':str(loaded[0].root),'attempt_id':'shizhen-CO-A1-qualification-001','start':8,'frames':184}, {'shot_id':'CO-A2','asset_id':'CO-A2-review-video','raw_root':str(loaded[1].root),'attempt_id':'shizhen-CO-A2-qualification-001','start':0,'frames':96}, {'shot_id':'CO-A3','asset_id':'CO-A3-review-video','raw_root':str(loaded[2].root),'attempt_id':'shizhen-CO-A3-qualification-001','start':361,'frames':120}, {'shot_id':'S01','asset_id':'approved-HD005-review-source','raw_root':str(RUN/'trial-S01-v3'),'attempt_id':'shizhen-S01-qualification-attempt-005','start':0,'frames':384}]
 for label in ['CO-A1','CO-A2']:
  g=json.loads((D/'qa'/(label+'-post-media-gate.json')).read_text());assert g['verdict']=='PASS'
 assert json.loads((D/'qa/CO-A3-post-media-gate.json').read_text())['verdict']=='FAIL'
 old_report=json.loads((RUN/'caption-review-005/bilingual-v4/recovered-input-receipt.json').read_text());caption_id=old_report['caption_asset_id'];style=old_report['style']
 evidence={'kind':'cold-open-exact-source-editorial-repair/1','user_goal':'两位冷开场，先叙事异常，冷峻悬疑，原标题与完整认可S01','user_one_call_request':'可以直接用seedance 2.5一次完成.这个模型最多30s一次生成','one_call_result':'CO-A3 complete22s was actually generated; original preserved, raw identity FAIL (Gao bag absent); no raw PASS or activation','edit':'Use accepted A1 pair and full physical occlusion, accepted A2 one-person reveal, then A3 only actual closeup of phone question and calm answer. No Gao image from failed whole source enters film. No moved lines, voice replacement, time stretch or new paid generation. S01 nominal16s original interval and existing accepted bilingual captions preserved, same source decode; original MP4 bytes unchanged.','windows':json.loads(json.dumps(windows)),'title_frames':84,'cold_open_frames':484,'old_s01_source_sha256':'15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b','S01_tail_boundary':'Use approved nominal0..16s source/caption window as prior accepted review; source video16.017s/audio16.064s includes endpoint/AAC idle tail, last speech ends14.16s. Preserve original file; do not claim output byte-identical or all padding retained.','authority':'development editorial review only, no Production activation, Final Acceptance or publication'};ref=authoring_input_reference(evidence)
 provenance={x.reference:x for p in sources for x in p.project.source_provenance};provenance[ref.reference]=ref;source=tuple(provenance.values())
 def seal(cls,key,**kw):return seal_artifact(cls(artifact_id='two-passengers-edit-'+key,revision=1,content_hash='0'*64,creation_receipt_id='two-passengers-edit-authored',source_provenance=source,**kw))
 brief=seal(ProductionBrief,'brief',title='失帧 两位冷开场衔接S01',objective='迅速建立两位到一位的缺席和正常回答，保持S01好奇心，保护原片原声字幕',audience='原创都市灵异短剧观众',format='1920x1080 24fps 3D国漫写实',language='zh',constraints=('不泄露终场反转，不增加机制','冷开场配乐只在片名，S01前退出','不重生成S01，不替换或变速原声'))
 story=seal(Story,'story',language='zh',logline='普通候车被改写为独自等待，翌夜进入便利店',synopsis=evidence['edit'],beats=(StoryBeat(beat_id='two',summary='两位普通同事候车'),StoryBeat(beat_id='one',summary='遮挡后只剩一位，平常回答'),StoryBeat(beat_id='title',summary='失帧，翌夜'),*s01.story.beats))
 shots=[]
 for p,w in zip(sources,windows,strict=True):
  old=p.shots[0];n=w['frames'];seconds=(n-0.000001)/24
  changes={'artifact_id':'two-passengers-edit-shot-'+old.shot_id,'revision':1,'source_provenance':source,'duration_policy':DurationPolicy(mode='fixed',seconds=seconds)}
  if old.shot_id=='CO-A3':changes.update(character_ids=('luomin',),intent='取已生成整段版的实际胸上近景：电话核对一位，罗敏平常确认，继续听电话',dialogue='电话司机：就你一位？罗敏：嗯，就我一个。')
  shots.append(seal_artifact(old.model_copy(update=changes)))
 title=seal(Shot,'title',shot_id='TITLE',scene_id='rain-stop',storyboard_beat_id='title',intent='后期黑场电影片名失帧，随后翌夜，进入原S01',duration_policy=DurationPolicy(mode='fixed',seconds=3.5),character_ids=(),visual_strategy='static_image',required_asset_roles=(AssetRoleRequirement(role='primary_visual',asset_ids=('co-before-image',),allowed_asset_types=(AssetType.IMAGE,)),))
 shots.insert(3,title)
 chars=(*master.characters,*s01.characters);scenes=(*master.scenes,*s01.scenes)
 board=seal(Storyboard,'board',beats=tuple(StoryboardBeat(beat_id=s.storyboard_beat_id or s.shot_id,scene_id=s.scene_id,shot_ids=(s.shot_id,),narrative_intent=s.intent) for s in shots))
 # Storyboard beat IDs are unique in this selected order.
 models=[(brief,'creative/edit/brief.yaml'),(story,'creative/edit/story.yaml'),(board,'creative/edit/storyboard.yaml'),*((c,'creative/edit/characters/'+c.character_id+'.yaml') for c in chars),*((s,'creative/edit/scenes/'+s.scene_id+'.yaml') for s in scenes),*((s,'creative/edit/shots/'+s.shot_id+'.yaml') for s in shots)]
 def ar(m):return ArtifactReference(artifact_id=m.artifact_id,revision=m.revision,content_hash=m.content_hash,path=Path(next(p for x,p in models if x==m)))
 project=seal_artifact(ProductionProject(artifact_id='two-passengers-edit-project',revision=1,content_hash='0'*64,creation_receipt_id='two-passengers-editorial-repair',source_provenance=source,project_id='shizhen-cold-open-S01-review-v1',title='失帧 两位+S01 连续审看',default_language='zh',delivery_profile=DeliveryProfile(width=1920,height=1080,fps=24),renderer_policy=RendererPolicy(),artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),characters=tuple(ar(c) for c in chars),scenes=tuple(ar(s) for s in scenes),storyboard=ar(board),shots=tuple(ar(s) for s in shots))))
 records={};assets={};caption_records=[];caption_payloads={}
 def add(path,payload):
  path=Path(path)
  if path in assets:assert assets[path].payload==payload,'Conflicting canonical asset bytes'
  else:assets[path]=art(path,payload)
 for p in sources:
  for a in p.registry.assets:
   if a.asset_type is AssetType.VIDEO:continue
   if a.asset_type is AssetType.CAPTION:
    if a.asset_id==caption_id:caption_records.append(a);caption_payloads[a.artifact_path]=art(a.artifact_path,p.asset_paths[a.asset_id].read_bytes())
    continue
   if a.asset_id in records:assert records[a.asset_id]==a
   else:records[a.asset_id]=a
   add(a.artifact_path,p.asset_paths[a.asset_id].read_bytes())
  for r in source:
   if r.reference.startswith('evidence/authoring-input/') and (p.root/r.reference).exists():add(r.reference,(p.root/r.reference).read_bytes())
 registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(sorted(records.values(),key=lambda a:a.asset_id)));h=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':h,'content_hash':h});T.mkdir(mode=0o700,parents=True,exist_ok=True)
 version=subprocess.run([str(TOOLS/'ffmpeg'),'-version'],capture_output=True,text=True,check=True).stdout.splitlines()[0].split()[2];chain=AudioProbeToolchain(ffmpeg_path=TOOLS/'ffmpeg',ffprobe_path=TOOLS/'ffprobe',ffmpeg=ToolIdentity(name='ffmpeg',version=version),ffprobe=ToolIdentity(name='ffprobe',version=version))
 imported_audio=[];audio_payloads={}
 for w in windows:
  p=load_production_project(Path(w['raw_root'])/'project.yaml');state=next(a.video_generation_state for a in p.manifest.attempts if a.attempt_id==w['attempt_id']);media=p.root/state.fetch_receipt.artifact_path;raw=media.read_bytes();w['sha256']=sha(raw)
  request=ResolvedVideoGenerationRequest.model_validate_json((p.root/state.request.path).read_bytes());fetch=VideoFetchReceipt.model_validate_json((p.root/state.fetch_receipt.path).read_bytes())
  with media.open('rb') as f:probed=probe_clip_fd_with_executable(f.fileno(),TOOLS/'ffprobe')
  v=next(s for s in probed['streams'] if s['codec_type']=='video');fps=Fraction(v['avg_frame_rate']);measured=MeasuredVideoMetadata(container_name='mp4',codec_name=v['codec_name'],width=v['width'],height=v['height'],fps_numerator=fps.numerator,fps_denominator=fps.denominator,frame_count=int(v['nb_frames']),duration_milliseconds=int((Decimal(v['duration'])*1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP)),audio_stream_count=sum(s['codec_type']=='audio' for s in probed['streams']),size_bytes=len(raw),artifact_sha256=w['sha256']);probe=VideoProbeReceipt.create(request=request,fetch_receipt=fetch,measured=measured)
  w['transform']={'video_fit':'cover'} if v['width']!=1920 else {};n=w['frames'];use={'shot_id':w['shot_id'],'asset_role':'primary_visual','trim_start_frame':w['start'],'trim_duration_frames':n,'source_time_map':{'contract_version':'video-time-map/1','audio_policy':'mute','points':[{'source_frame':0,'output_frame':0},{'source_frame':n,'output_frame':n}]},'transform':w['transform'],'scope':'replacement_audio_preview'}
  registry,capture=prepare_qualification_preview_input(target_root=T,project=project,registry=registry,source_root=p.root,source_attempt_id=w['attempt_id'],source_sha256=w['sha256'],asset_id=w['asset_id'],usage_license='Exact task-owned original generated CG source, selected for authorized development editorial repair; no qualification/activation',preview_use=use,preview_probe=probe)
  for a in capture:add(a.relative_path,a.payload)
  if w['shot_id']=='S01':w['audio_id']='HD005-original-dialogue-mix';continue
  wav=V/(w['shot_id']+'-native-48k.wav')
  if wav.exists():
   import wave
   with wave.open(str(wav)) as f:
    assert (f.getframerate(),f.getnchannels(),f.getsampwidth())==(48000,2,2)
    previous_pcm=f.readframes(f.getnframes())
   current_pcm=subprocess.run([str(TOOLS/'ffmpeg'),'-v','error','-i',str(media),'-map','0:a:0','-vn','-ar','48000','-ac','2','-f','s16le','pipe:1'],capture_output=True,check=True).stdout
   assert previous_pcm==current_pcm,'Existing local audio snapshot changed'
  else:subprocess.run([str(TOOLS/'ffmpeg'),'-nostdin','-v','error','-i',str(media),'-map','0:a:0','-vn','-ar','48000','-ac','2','-c:a','pcm_s16le',str(wav)],check=True)
  deriv={'source_mp4_sha256':w['sha256'],'stream':'0:a:0','processing':'Full stereo PCM16 decode/resample to48k only; no voice/gain/stretch/denoise changes','source_audio_sha256':sha(wav.read_bytes())};finger=canonical_sha256(deriv);w['audio_id']=w['shot_id']+'-original-mix';req=AudioImportRequest(asset_id=w['audio_id'],audio_kind='dialogue',mime_type='audio/wav',source=AudioSource(kind='derived',provider_or_tool=chain.ffmpeg,input_artifact_ids=(w['asset_id'],),input_fingerprint=w['sha256'],original_reference='exact-MP4:'+w['sha256']+':0:a:0'),language='zh',script_hash=sha(next(s for s in shots if s.shot_id==w['shot_id']).dialogue.encode()),provenance_receipt_id=finger,creation_receipt_id=w['shot_id']+'-original-audio-decode',usage_license='Exact original source mix for requested editorial review')
  with wav.open('rb') as f:audio=req.prepare(f.fileno(),toolchain=chain)
  imported_audio.append(audio.asset_record);audio_payloads[audio.asset_record.artifact_path]=art(audio.asset_record.artifact_path,audio.payload)
 # Register the real Suno-generated original WAV using its existing music owner.
 mi=json.loads((D/'music/intent.json').read_text());briefs=json.loads(Path('docs/superpowers/artifacts/drama/shizhen-episode-01/cold-open-preparation/music/briefs.json').read_text());direction=direct_music(SceneMusicBrief.model_validate(next(b for b in briefs if b['cue_id']=='co-missing-response')));assert generation_identity(direction)==mi['generation_identity']
 mw=D/'music/audio/cold-open-title-suspense-atmosphere-fc0af846.wav'
 with mw.open('rb') as f:mp=probe_audio_candidate(f.fileno(),mime_type='audio/wav',toolchain=chain)
 ma=music_asset_record(asset_id='two-passengers-missing-response-B',probe=mp,direction=direction,usage_license='Task-authorized Suno v6 original instrumental; account terms/actual artistic acceptance remain independent');imported_audio.append(ma);audio_payloads[ma.artifact_path]=art(ma.artifact_path,mw.read_bytes())
 for m,path in models:add(path,_canonical_yaml_bytes(m))
 add(ref.reference,authoring_input_payload(evidence));writer=ProductionStateCommitter(T)
 if resume:
  current=load_production_project(T/'project.yaml');assert current.project==project and current.registry==registry,'Existing partial composition differs; no overwrite'
 else:writer.bootstrap_initial_state(attempt_id='two-passengers-edit-bootstrap',project=project,registry=registry,artifacts=tuple(assets[p] for p in sorted(assets)))
 current=load_production_project(T/'project.yaml');updated=registry.model_copy(update={'assets':(*registry.assets,*sorted((*imported_audio,*caption_records),key=lambda a:a.asset_id))});h=registry_semantic_sha256(updated);updated=updated.model_copy(update={'revision_id':h,'content_hash':h});ptr=current.manifest.active_project;stylepath=Path(style['path']);caption_payloads[stylepath]=art(stylepath,(s01.root/stylepath).read_bytes());writer.commit(prepare_audio_registry_commit(manifest=current.manifest,project=project,base_registry=registry,registry=updated,attempt_id='two-passengers-register-original-audio-music-captions',active_project_artifact=art(ptr.path,(T/ptr.path).read_bytes()),artifacts=tuple((*audio_payloads.values(),*caption_payloads.values()))))
 report={'project':str(T),'sources':windows,'order':['CO-A1','CO-A2','CO-A3','TITLE','S01'],'caption_id':caption_id,'style':style,'title_frames':84,'music_asset_id':ma.asset_id,'music_source_sha256':ma.sha256,'music_note':'B candidate used only on title, no score over the event or S01; motif/style human review pending','cold_open_frames':484,'total_frames':868,'scope':'development_audio_preview','production_activation':False,'publication_state':'NOT_PUBLISHED'};(V/'input-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'prepared':True,'cold_open_seconds':484/24,'total_seconds':868/24,'new_paid_generation':0}))
if __name__=='__main__':main()
