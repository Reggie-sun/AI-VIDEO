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
R=Path.cwd();H=Path(__file__).resolve().parent;T=R/'runs/shizhen-opening-A-revision-20261026/project-r3'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 resume=(T/'project.yaml').exists()
 src=json.loads((R/'outputs/shizhen-episode01/cold-open-execution-20261026/composition/input-receipt.json').read_text())
 old=load_production_project(Path(src['project'])/'project.yaml')
 pre=load_production_project(R/'runs/shizhen-opening-reconstruction-20261026/project-r2/project.yaml')
 windows={'CO-A1':(8,184),'CO-A2':(30,66),'CO-A3':(361,167)}
 rows=[{**x,'start':windows[x['shot_id']][0],'frames':windows[x['shot_id']][1]} for x in src['sources'] if x['shot_id']!='S01']
 rows.append({**next(x for x in rows if x['shot_id']=='CO-A3'),'shot_id':'CO-TAIL','source_asset_id':'CO-A3-review-video','asset_id':'CO-TAIL-review-video','audio_id':'CO-TAIL-original-mix','start':288,'frames':72})
 evidence={'kind':'narrative-integration-development/1','request':(H/'creative-input.txt').read_text(),
  'source_windows':rows,'scope':'Standalone event seam repair plus same-station title study. Latest user reassigned typography to this agent. Macro footage still missing.',
  'decisions':'Keep A1 and A2 exact windows; remove A3 redundant fullshot frames336..360, enter observed closeup361 before driver line. Four dialogue lines preserved. No new footage or title design.',
  'authority':'No paid generation, activation, final artistic acceptance or publication'}
 ref=authoring_input_reference(evidence);prov=(*old.project.source_provenance,ref)
 def seal(obj,**kw):return seal_artifact(obj.model_copy(update={**kw,'revision':1,'content_hash':'0'*64,'source_provenance':prov,'creation_receipt_id':'narrative-integration-local'}))
 shots=[]
 for s in old.shots:
  if s.shot_id in {'S01','TITLE'}:continue
  n=36 if s.shot_id=='TITLE' else windows[s.shot_id][1]
  shots.append(seal(s,artifact_id='integrated-shot-'+s.shot_id,storyboard_beat_id=s.shot_id,
   intent=('翌夜，独立时间转场，无新异常' if s.shot_id=='TITLE' else s.intent),duration_policy=DurationPolicy(mode='fixed',seconds=(n-.000001)/24)))
 shots.append(seal(next(s for s in old.shots if s.shot_id=='CO-A3'),artifact_id='tail-shot',shot_id='CO-TAIL',storyboard_beat_id='CO-TAIL',intent='回答后的同站台全景作为后期片名画面；空位保持，幸存者继续通话，无第二事件。',duration_policy=DurationPolicy(mode='fixed',seconds=(72-.000001)/24),required_asset_roles=(AssetRoleRequirement(role='primary_visual',asset_ids=(),allowed_asset_types=(AssetType.VIDEO,)),)))
 shots.sort(key=lambda x:['CO-A1','CO-A2','CO-A3','CO-TAIL'].index(x.shot_id))
 board=seal(old.storyboard,artifact_id='integration-board',beats=tuple(StoryboardBeat(beat_id=s.shot_id,scene_id=s.scene_id,shot_ids=(s.shot_id,),narrative_intent=s.intent) for s in shots))
 story=seal(old.story,artifact_id='integration-story',beats=tuple(StoryBeat(beat_id=s.shot_id,summary=s.intent) for s in shots))
 brief=seal(old.brief,artifact_id='integration-brief',objective='保护两位到一位与四句对白，修复接缝；宏观同地画面仍缺，字体已由用户转回本轮制作。本次是局部可观看版本，不是全目标最终片')
 models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),*((x,'creative/characters/'+x.character_id+'.yaml') for x in old.characters),*((x,'creative/scenes/'+x.scene_id+'.yaml') for x in old.scenes),*((x,'creative/shots/'+x.shot_id+'.yaml') for x in shots)]
 def ar(x):return ArtifactReference(artifact_id=x.artifact_id,revision=x.revision,content_hash=x.content_hash,path=Path(next(p for o,p in models if o==x)))
 project=seal(old.project,artifact_id='integration-project',project_id='shizhen-opening-A-revision-20261026',title='失帧 独立开场 接缝修订',artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),storyboard=ar(board),characters=tuple(ar(x) for x in old.characters),scenes=tuple(ar(x) for x in old.scenes),shots=tuple(ar(x) for x in shots)))
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
 from ai_video.production.audio import AudioImportRequest, AudioProbeToolchain
 from ai_video.production.hashing import canonical_sha256
 import subprocess
 tools=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
 version=subprocess.run([str(tools/'ffmpeg'),'-version'],capture_output=True,text=True,check=True).stdout.splitlines()[0].split()[2]
 tool=ToolIdentity(name='ffmpeg',version=version)
 chain=AudioProbeToolchain(ffmpeg_path=tools/'ffmpeg',ffprobe_path=tools/'ffprobe',ffmpeg=tool,ffprobe=ToolIdentity(name='ffprobe',version=version))
 row=next(x for x in rows if x['shot_id']=='CO-TAIL')
 wav=old.asset_paths['CO-A3-original-mix']
 request=AudioImportRequest(asset_id=row['audio_id'],audio_kind='dialogue',mime_type='audio/wav',source=AudioSource(kind='derived',provider_or_tool=tool,input_artifact_ids=(row['asset_id'],),input_fingerprint=row['sha256'],original_reference='exact-MP4:'+row['sha256']+':0:a:0'),language='zh',script_hash=sha(b'Original source mix; tail window has ambience only'),provenance_receipt_id=canonical_sha256({'source_mp4_sha256':row['sha256'],'source_wav_sha256':sha(wav.read_bytes()),'role':'same bytes registered for tail captured video'}),creation_receipt_id='tail-original-audio-registration',usage_license='Same original source mix, no generation or processing change')
 with wav.open('rb') as stream: imported=request.prepare(stream.fileno(),toolchain=chain)
 records[imported.asset_record.asset_id]=imported.asset_record
 add(imported.asset_record.artifact_path,imported.payload)
 registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records.values()))
 h=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':h,'content_hash':h})
 T.mkdir(parents=True,exist_ok=True,mode=0o700)
 for row in rows:
  captured=next(a for a in old.registry.assets if a.asset_id==row.get('source_asset_id',row['asset_id']))
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
 (H/'qa/full-protected-inputs.json').write_text(json.dumps(protected,indent=2))
 (H/'full-input-receipt.json').write_text(json.dumps({**src,'project':str(T),'sources':rows,'order':[s.shot_id for s in shots],'total_frames':489,'cold_open_frames':417,'title_frames':0,'caption_id':ca.asset_id},ensure_ascii=False,indent=2))
 print('Prepared isolated canonical project; no source mutation')
if __name__=='__main__':main()
