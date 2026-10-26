"""Isolated source-preserving editorial project, using canonical committer."""
from pathlib import Path
import json, hashlib
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.project import load_production_project
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, _canonical_yaml_bytes
from ai_video.production.qualification_preview_input import prepare_qualification_preview_input
from ai_video.production.repair_input_admission import verify_repair_input
R=Path.cwd();H=Path(__file__).resolve().parent;T=R/'runs/shizhen-opening-world-title-20261026/project-r1'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 resume=(T/'project.yaml').exists()
 src=json.loads((R/'outputs/shizhen-episode01/cold-open-execution-20261026/composition/input-receipt.json').read_text())
 old=load_production_project(Path(src['project'])/'project.yaml')
 pre=load_production_project(R/'runs/shizhen-opening-reconstruction-20261026/project-r2/project.yaml')
 windows={'CO-A1':(8,184),'CO-A2':(30,66),'CO-A3':(336,192)}
 rows=[{**x,'start':windows[x['shot_id']][0],'frames':windows[x['shot_id']][1]} for x in src['sources'] if x['shot_id']!='S01']
 evidence={'kind':'narrative-integration-development/1','request':(H/'creative-input.txt').read_text(),
  'source_windows':rows,'scope':'Standalone world/event/title comparison; mixed stock and existing stylized event are development material only.',
  'decisions':'Preserve accepted focus002 exact windows and four lines. Social crowd before event, later same stock shot continues naturally after event. No repeated stock time. No claim of physical same street/weather. No new supernatural rule.',
  'authority':'No paid generation, activation, final artistic acceptance or publication'}
 ref=authoring_input_reference(evidence);prov=(*old.project.source_provenance,ref)
 def seal(obj,**kw):return seal_artifact(obj.model_copy(update={**kw,'revision':1,'content_hash':'0'*64,'source_provenance':prov,'creation_receipt_id':'narrative-integration-local'}))
 shots=[]
 for s in old.shots:
  if s.shot_id in {'S01','TITLE'}:continue
  n=36 if s.shot_id=='TITLE' else windows[s.shot_id][1]
  shots.append(seal(s,artifact_id='integrated-shot-'+s.shot_id,storyboard_beat_id=s.shot_id,
   intent=('翌夜，独立时间转场，无新异常' if s.shot_id=='TITLE' else s.intent),duration_policy=DurationPolicy(mode='fixed',seconds=(n-.000001)/24)))
 for sid,n in [('WORLD-IN',72),('WORLD-OUT',144)]:
  shots.append(seal(Shot(artifact_id='world-shot-'+sid,revision=1,content_hash='0'*64,creation_receipt_id='world-local',source_provenance=prov,shot_id=sid,scene_id=old.scenes[0].scene_id,storyboard_beat_id=sid,intent=('人群过街，各自继续日常；先建立社会关系的常态' if sid=='WORLD-IN' else '事件之后回到继续运行的城市；行人自然走出画面，出租车照常通过，无第二次消失。片名完成情绪收束'),duration_policy=DurationPolicy(mode='fixed',seconds=(n-.000001)/24),character_ids=(),visual_strategy='existing_video',required_asset_roles=(AssetRoleRequirement(role='primary_visual',asset_ids=('stock-social-street',),allowed_asset_types=(AssetType.VIDEO,)),))))
 shots.sort(key=lambda x:['WORLD-IN','CO-A1','CO-A2','CO-A3','WORLD-OUT'].index(x.shot_id))
 board=seal(old.storyboard,artifact_id='integration-board',beats=tuple(StoryboardBeat(beat_id=s.shot_id,scene_id=s.scene_id,shot_ids=(s.shot_id,),narrative_intent=s.intent) for s in shots))
 story=seal(old.story,artifact_id='integration-story',beats=tuple(StoryBeat(beat_id=s.shot_id,summary=s.intent) for s in shots))
 brief=seal(old.brief,artifact_id='integration-brief',objective='城市尺度收束至两位被改写为一位；完整保留普通人的关照与两位到一位的异常。现阶段只验剪辑，尚缺统一真人摄影')
 models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),*((x,'creative/characters/'+x.character_id+'.yaml') for x in old.characters),*((x,'creative/scenes/'+x.scene_id+'.yaml') for x in old.scenes),*((x,'creative/shots/'+x.shot_id+'.yaml') for x in shots)]
 def ar(x):return ArtifactReference(artifact_id=x.artifact_id,revision=x.revision,content_hash=x.content_hash,path=Path(next(p for o,p in models if o==x)))
 project=seal(old.project,artifact_id='integration-project',project_id='shizhen-opening-narrative-integration-20261026',title='失帧 两位 完整叙事预演',artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),storyboard=ar(board),characters=tuple(ar(x) for x in old.characters),scenes=tuple(ar(x) for x in old.scenes),shots=tuple(ar(x) for x in shots)))
 artifacts={};records={}
 def add(path,raw):
  path=Path(path)
  if path in artifacts:assert artifacts[path].payload==raw
  else:artifacts[path]=PreparedArtifact(path,raw,sha(raw))
 protected={str(old.root/'state/manifest.json'):sha((old.root/'state/manifest.json').read_bytes()),str(pre.root/'state/manifest.json'):sha((pre.root/'state/manifest.json').read_bytes())}
 for a in old.registry.assets:
  protected[str(old.asset_paths[a.asset_id])]=sha(old.asset_paths[a.asset_id].read_bytes())
  if a.asset_type in {AssetType.IMAGE,AssetType.MUSIC} or a.asset_id in {'CO-A1-original-mix','CO-A2-original-mix','CO-A3-original-mix'}:records[a.asset_id]=a;add(a.artifact_path,old.asset_paths[a.asset_id].read_bytes())
 for aid in ['rain-public-domain']:
  a=next(x for x in pre.registry.assets if x.asset_id==aid);records[aid]=a;add(a.artifact_path,pre.asset_paths[aid].read_bytes())
 for r in old.project.source_provenance:
  if r.reference.startswith('evidence/authoring-input/'):add(r.reference,(old.root/r.reference).read_bytes())
 style=src['style'];add(style['path'],(old.root/style['path']).read_bytes())
 # Local editorial captions from the existing exact A1 ASR timing, not invented speech.
 from ai_video.production.captions import CaptionImportRequest,caption_timing_fingerprint
 from ai_video.production.hashing import canonical_sha256
 src_caption=next(a for a in old.registry.assets if a.asset_id==src['caption_id'])
 template=CaptionTrack.model_validate_json(old.asset_paths[src_caption.asset_id].read_bytes())
 voice=next(a for a in old.registry.assets if a.asset_id=='CO-A1-original-mix')
 texts=['师傅，我们在站里，两位','让他别急，路滑']
 ct=template.model_copy(update=dict(artifact_id='A1-local-editorial-captions',caption_track_id='A1-local-editorial-captions',revision=1,language='zh',source_provenance=prov,creation_receipt_id='existing-A1-ASR-editorial-punctuation',
  source_audio_asset_id=voice.asset_id,source_audio_sha256=voice.sha256,script_hash=voice.audio_metadata.script_hash,transcript_hash=sha(''.join(texts).encode()),alignment_provider='existing-local-whisper-plus-editorial-word-correction',alignment_model='medium',alignment_receipt_id='CO-A1-transcription-preserved',
  segments=tuple(CaptionSegment(segment_id='a1-'+str(i),text=t,start_sample=int(a*48000),end_sample=int(b*48000)) for i,(t,a,b) in enumerate(zip(texts,[.64,3.22],[3.22,5.58])))))
 ct=seal_artifact(ct.model_copy(update={'timing_fingerprint':caption_timing_fingerprint(ct)}))
 ci=CaptionImportRequest.create(caption_track=ct,style_reference=CaptionStyleReference.model_validate(style),style_bytes=(old.root/style['path']).read_bytes())
 cm=src_caption.caption_metadata.model_copy(update=dict(caption_track_id=ct.caption_track_id,language='zh',source_audio_asset_id=voice.asset_id,source_audio_sha256=voice.sha256,script_hash=ct.script_hash,transcript_hash=ct.transcript_hash,segment_count=2,alignment_receipt_id=ct.alignment_receipt_id,timing_fingerprint=ct.timing_fingerprint))
 ca=src_caption.model_copy(update=dict(asset_id=ct.caption_track_id,artifact_path=Path('assets/captions/'+ci.track_sha256+'.json'),sha256=ci.track_sha256,size_bytes=len(ci.track_bytes),input_artifact_ids=(voice.asset_id,),input_fingerprint=voice.sha256,creation_receipt_id=ct.creation_receipt_id,caption_metadata=cm))
 records[ca.asset_id]=ca;add(ca.artifact_path,ci.track_bytes)
 from fractions import Fraction
 from ai_video.production.hyperframes import probe_clip_fd_with_executable
 from ai_video.production.hashing import canonical_sha256
 stock=H/'assets/street-24fps.mp4';raw=stock.read_bytes();digest=sha(raw)
 with stock.open('rb') as f:probe=probe_clip_fd_with_executable(f.fileno(),Path('/home/reggie/.config/jianji/tools/ffmpeg/bin/ffprobe'))
 v=next(x for x in probe['streams'] if x['codec_type']=='video');fps=Fraction(v['avg_frame_rate']);ms=round(float(v['duration'])*1000)
 origin=dict(kind='stock-video-import-development/1',page='https://www.pexels.com/video/nighttime-urban-life-in-china-36407445/',author='LayG Traveller',license='https://www.pexels.com/license/',original_sha256=sha((H/'assets/pexels-36407445-original.mp4').read_bytes()),derivative_sha256=digest,processing='1920x1080 normal-speed 24fps frame selection, no optical interpolation',usage='Structure previs only: different location, dry street and evening crowd; NOT same rainy 03:17 street',metadata_semantics='Legacy generation-named metadata fingerprints identify this import, not a generation')
 fp=canonical_sha256(origin)
 a=AssetRecord(asset_id='stock-social-street',asset_type=AssetType.VIDEO,artifact_path=Path('assets/files/'+digest+'.mp4'),sha256=digest,size_bytes=len(raw),mime_type='video/mp4',duration_seconds=ms/1000,width=v['width'],height=v['height'],source_kind=AssetSourceKind.IMPORTED,tool=ToolIdentity(name='ffmpeg',version='8.1.2'),input_fingerprint=fp,creation_receipt_id=fp,usage_license='Pexels License edited development previs; LayG Traveller; '+origin['page'],video_metadata=VideoAssetMetadata(container_name='mp4',codec_name=v['codec_name'],width=v['width'],height=v['height'],fps_numerator=fps.numerator,fps_denominator=fps.denominator,duration_milliseconds=ms,frame_count=int(v['nb_frames']),probe_receipt_id='stock-import-'+fp,request_receipt_fingerprint=fp,resolved_generation_hash=fp,provenance_receipt_id=fp))
 records[a.asset_id]=a;add(a.artifact_path,raw)
 (H/'assets/stock-provenance.json').write_text(json.dumps(origin,ensure_ascii=False,indent=2))
 registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records.values()))
 h=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':h,'content_hash':h})
 T.mkdir(parents=True,exist_ok=True,mode=0o700)
 for row in rows:
  captured=next(a for a in old.registry.assets if a.asset_id==row['asset_id'])
  admission=verify_repair_input(captured,old.root)
  n=row['frames'];use=dict(shot_id=row['shot_id'],asset_role='primary_visual',trim_start_frame=row['start'],trim_duration_frames=n,
    source_time_map=dict(contract_version='video-time-map/1',audio_policy='mute',points=[dict(source_frame=0,output_frame=0),dict(source_frame=n,output_frame=n)]),transform=row['transform'],scope='replacement_audio_preview')
  registry,new=prepare_qualification_preview_input(target_root=T,project=project,registry=registry,source_root=Path(row['raw_root']),source_attempt_id=row['attempt_id'],source_sha256=row['sha256'],asset_id=row['asset_id'],usage_license='Exact task-owned source; development cut. Old A3 raw FAIL unchanged.',preview_use=use,preview_probe=admission.preview_probe)
  for item in new:add(item.relative_path,item.payload)
 for obj,path in models:add(path,_canonical_yaml_bytes(obj))
 add(ref.reference,authoring_input_payload(evidence))
 from ai_video.production.state_commit import prepare_audio_registry_commit
 caps=[a for a in registry.assets if a.asset_type==AssetType.CAPTION]
 cap_paths={a.artifact_path for a in caps}|{Path(style['path'])}
 registry=registry.model_copy(update={'assets':tuple(a for a in registry.assets if a.asset_type!=AssetType.CAPTION)})
 rh=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':rh,'content_hash':rh})
 writer=ProductionStateCommitter(T)
 if resume:
  check=load_production_project(T/'project.yaml');assert check.project==project and check.registry==registry,'Only exact known bootstrap may resume'
 else:
  writer.bootstrap_initial_state(attempt_id='integration-bootstrap',project=project,registry=registry,artifacts=tuple(artifacts[p] for p in sorted(artifacts) if p not in cap_paths))
 final_registry=registry.model_copy(update={'assets':(*registry.assets,*sorted(caps,key=lambda a:a.asset_id))})
 rh=registry_semantic_sha256(final_registry);final_registry=final_registry.model_copy(update={'revision_id':rh,'content_hash':rh})
 current=load_production_project(T/'project.yaml');ptr=current.manifest.active_project
 writer.commit(prepare_audio_registry_commit(manifest=current.manifest,project=project,base_registry=registry,registry=final_registry,attempt_id='register-focus-captions',active_project_artifact=PreparedArtifact(ptr.path,(T/ptr.path).read_bytes(),sha((T/ptr.path).read_bytes())),artifacts=tuple(artifacts[p] for p in sorted(cap_paths))))
 loaded=load_production_project(T/'project.yaml');assert loaded.project==project
 assert all(sha(Path(p).read_bytes())==h for p,h in protected.items())
 (H/'qa/protected-inputs.json').write_text(json.dumps(protected,indent=2))
 (H/'input-receipt.json').write_text(json.dumps({**src,'project':str(T),'sources':rows,'order':[s.shot_id for s in shots],'total_frames':658,'cold_open_frames':442,'title_frames':0,'caption_id':ca.asset_id},ensure_ascii=False,indent=2))
 print('Prepared isolated canonical project; no source mutation')
if __name__=='__main__':main()
