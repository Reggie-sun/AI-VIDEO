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
R=Path.cwd();H=Path(__file__).resolve().parent;T=R/'runs/shizhen-opening-narrative-integration-20261026/project'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 if (T/'project.yaml').exists():raise FileExistsError(T)
 src=json.loads((R/'outputs/shizhen-episode01/cold-open-execution-20261026/composition/input-receipt.json').read_text())
 old=load_production_project(Path(src['project'])/'project.yaml')
 pre=load_production_project(R/'runs/shizhen-opening-reconstruction-20261026/project-r2/project.yaml')
 windows={'CO-A1':(8,184),'CO-A2':(48,48),'CO-A3':(336,192),'S01':(0,384)}
 rows=[{**x,'start':windows[x['shot_id']][0],'frames':windows[x['shot_id']][1]} for x in src['sources']]
 evidence={'kind':'narrative-integration-development/1','request':(H/'creative-input.txt').read_text(),
  'source_windows':rows,'scope':'Full spoken event + original B + next night + protected HD005. Stock/CG previs only.',
  'decisions':'Four-second macro placeholder; remove two fully occluded seconds without voice; extend actual one-person wide and post-answer motion; no silhouette. No new supernatural rule.',
  'authority':'No paid generation, activation, final artistic acceptance or publication'}
 ref=authoring_input_reference(evidence);prov=(*old.project.source_provenance,ref)
 def seal(obj,**kw):return seal_artifact(obj.model_copy(update={**kw,'revision':1,'content_hash':'0'*64,'source_provenance':prov,'creation_receipt_id':'narrative-integration-local'}))
 shots=[]
 for sid,n in [('CITY',60),('ROAD',36)]:
  s=next(x for x in pre.shots if x.shot_id==sid)
  shots.append(seal(s,artifact_id='integrated-shot-'+sid,duration_policy=DurationPolicy(mode='fixed',seconds=(n-.000001)/24)))
 for s in old.shots:
  n=36 if s.shot_id=='TITLE' else windows[s.shot_id][1]
  shots.append(seal(s,artifact_id='integrated-shot-'+s.shot_id,storyboard_beat_id=s.shot_id,
   intent=('翌夜，独立时间转场，无新异常' if s.shot_id=='TITLE' else s.intent),duration_policy=DurationPolicy(mode='fixed',seconds=(n-.000001)/24)))
 board=seal(old.storyboard,artifact_id='integration-board',beats=tuple(StoryboardBeat(beat_id=s.shot_id,scene_id=s.scene_id,shot_ids=(s.shot_id,),narrative_intent=s.intent) for s in shots))
 story=seal(old.story,artifact_id='integration-story',beats=tuple(StoryBeat(beat_id=s.shot_id,summary=s.intent) for s in shots))
 brief=seal(old.brief,artifact_id='integration-brief',objective='城市尺度收束至两位被改写为一位；恢复完整对白并进入翌夜原S01。现阶段只验剪辑，尚缺统一真人摄影')
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
  if a.asset_type!=AssetType.VIDEO:records[a.asset_id]=a;add(a.artifact_path,old.asset_paths[a.asset_id].read_bytes())
 for aid in ['stock-city','stock-road','rain-public-domain']:
  a=next(x for x in pre.registry.assets if x.asset_id==aid);records[aid]=a;add(a.artifact_path,pre.asset_paths[aid].read_bytes())
 for r in old.project.source_provenance:
  if r.reference.startswith('evidence/authoring-input/'):add(r.reference,(old.root/r.reference).read_bytes())
 style=src['style'];add(style['path'],(old.root/style['path']).read_bytes())
 registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records.values()))
 h=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':h,'content_hash':h})
 T.mkdir(parents=True,mode=0o700)
 for row in rows:
  captured=next(a for a in old.registry.assets if a.asset_id==row['asset_id'])
  admission=verify_repair_input(captured,old.root)
  n=row['frames'];use=dict(shot_id=row['shot_id'],asset_role='primary_visual',trim_start_frame=row['start'],trim_duration_frames=n,
    source_time_map=dict(contract_version='video-time-map/1',audio_policy='mute',points=[dict(source_frame=0,output_frame=0),dict(source_frame=n,output_frame=n)]),transform=row['transform'],scope='replacement_audio_preview')
  registry,new=prepare_qualification_preview_input(target_root=T,project=project,registry=registry,source_root=Path(row['raw_root']),source_attempt_id=row['attempt_id'],source_sha256=row['sha256'],asset_id=row['asset_id'],usage_license='Exact task-owned source; development cut. Old A3 raw FAIL unchanged.',preview_use=use,preview_probe=admission.preview_probe)
  for item in new:add(item.relative_path,item.payload)
 for obj,path in models:add(path,_canonical_yaml_bytes(obj))
 add(ref.reference,authoring_input_payload(evidence))
 ProductionStateCommitter(T).bootstrap_initial_state(attempt_id='integration-bootstrap',project=project,registry=registry,artifacts=tuple(artifacts[p] for p in sorted(artifacts)))
 loaded=load_production_project(T/'project.yaml');assert loaded.project==project
 assert all(sha(Path(p).read_bytes())==h for p,h in protected.items())
 (H/'qa/protected-inputs.json').write_text(json.dumps(protected,indent=2))
 (H/'input-receipt.json').write_text(json.dumps({**src,'project':str(T),'sources':rows,'order':[s.shot_id for s in shots],'total_frames':940,'cold_open_frames':556,'title_frames':36},ensure_ascii=False,indent=2))
 print('Prepared isolated canonical project; no source mutation')
if __name__=='__main__':main()
