"""One canonical timeline and HyperFrames render; source-speed native A/V windows."""
from pathlib import Path
import json, os, shutil
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.composition import resolve_composition
from ai_video.production.hyperframes import HyperFramesAdapter, HyperFramesRenderAttempt, _NetworkIsolatedHyperFramesRunner, decoded_audio_sha256_fd_with_executable, probe_clip_fd_with_executable

R=Path.cwd();H=Path(__file__).resolve().parent
FF=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
BROWSER=Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')
os.environ['PATH']=str(FF)+os.pathsep+os.environ.get('PATH',os.defpath)
inp=json.loads((H/'input-receipt.json').read_text());p=load_production_project(Path(inp['project'])/'project.yaml')
layers=[];audio=[]
for row in inp['sources']:
 layers.append(CompositionLayerSpec(layer_id='retained-'+row['shot_id'],shot_id=row['shot_id'],asset_role='primary_visual',asset_id=row['asset_id'],trim_start_frame=row['start'],trim_duration_frames=row['frames'],source_audio_policy='KEEP',transform=FixedTransform()))
 audio.append(AudioTrackSpec(track_id='native-'+row['shot_id'],audio_kind='dialogue',asset_id=row['audio_id'],shot_id=row['shot_id'],trim_start_sample=row['start']*2000,trim_duration_samples=row['frames']*2000))
order=tuple(r['shot_id'] for r in inp['sources'])
spec=seal_artifact(CompositionSpec(artifact_id='macro-hd-cut-composition',schema_version='2.3',revision=1,content_hash='0'*64,creation_receipt_id='user-requested-dissolve-cut',source_provenance=p.project.source_provenance,composition_id='macro-hd-cut-v4',shot_ids=order,layers=tuple(layers),transitions=(TransitionSpec(from_shot_id=order[0],to_shot_id=order[1],kind='cut',duration_frames=0),),delivery_profile=p.project.delivery_profile,sample_rate=48000,requested_renderer='hyperframes',audio_tracks=tuple(audio),caption_tracks=(),text_layers=()))
timeline=resolve_composition(p,spec,renderer_version='0.7.103')
assert (timeline.total_frames,timeline.total_samples,timeline.usage_scope)==(164,328000,'development_audio_preview')
(H/'composition.json').write_text(spec.model_dump_json(indent=2));(H/'resolved-timeline.json').write_text(timeline.model_dump_json(indent=2))
stage=R/'runs/shizhen-macro-opening-20261027/MC01-02-edit-v4/render-002-software';stage.mkdir(parents=True,mode=0o700,exist_ok=False);os.chmod(stage,0o700)
ip=Path('/usr/sbin/ip').resolve(strict=True)
class Runner(_NetworkIsolatedHyperFramesRunner):
 def run(self,command,args,**kwargs):
  r=super().run(command,args,**kwargs)
  (stage/(command+'-diagnostic.json')).write_text(json.dumps({'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2))
  return r
runner=Runner(project_root=R,binary=R/'node_modules/.bin/hyperframes',browser_path=BROWSER,ip_path=ip,unshare_path=Path('/usr/bin/unshare'),bash_path=Path('/usr/bin/bash'),browser_gpu_mode='software')
adapter=HyperFramesAdapter(runner=runner,expected_version='0.7.103',browser_path=BROWSER,ip_path=ip,browser_gpu_mode='software',decoded_audio=lambda fd,rate,channels:decoded_audio_sha256_fd_with_executable(fd,rate,channels,FF/'ffmpeg'),probe=lambda fd:probe_clip_fd_with_executable(fd,FF/'ffprobe'))
selection=RendererSelectionReceipt(receipt_id='macro-hd-cut-v4',attempt_id='macro-hd-cut-v4',requested_kind='hyperframes',selected_kinds=('hyperframes',),renderer_version='0.7.103',timeline_fingerprint=timeline.composition_fingerprint,current_project=p.manifest.active_project,current_registry=p.manifest.active_registry)
assets={x.asset_id:p.asset_paths[x.asset_id] for x in (*timeline.visual_spans,*timeline.audio_spans)};before=(p.root/'state/manifest.json').read_bytes()
print(json.dumps({'resolved':True,'frames':timeline.total_frames,'seconds':timeline.total_frames/24,'usage_scope':timeline.usage_scope}),flush=True)
result=adapter.render(HyperFramesRenderAttempt(attempt_id=selection.attempt_id,selection=selection,timeline=timeline,asset_sources=assets,allowed_asset_root=p.root,staging_root=stage/'source',allowed_staging_parent=stage,output_path=stage/'output/macro-hd-cut-v4.mp4',verification_snapshot_path=stage/'verified.mp4'))
assert before==(p.root/'state/manifest.json').read_bytes()
assert all(c.exit_code==0 and c.error_count==0 for c in result.checks)
output=H/'失帧-市政异常-1080p-剪辑修订04.mp4';assert not output.exists();shutil.copyfile(result.output.untrusted_staged_path,output)
report={'output':str(output.relative_to(R)),'renderer_output':str(result.output.untrusted_staged_path),'sha256':result.output.output_sha256,'bytes':result.output.output_size_bytes,'size_bytes':result.output.output_size_bytes,'timeline_frames':164,'timeline_fingerprint':timeline.composition_fingerprint,'measured':result.output.measured.model_dump(mode='json'),'checks':[c.model_dump(mode='json') for c in result.checks],'source_sha256':inp['source_sha256'],'source_audio_matches_new_visual_windows':True,'source_windows':inp['sources'],'usage_scope':timeline.usage_scope,'production_activation':False,'publication':'NOT_PUBLISHED','human_review':'PENDING','paid_generation_calls':0}
(H/'render-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'output':str(output),'sha256':report['sha256'],'bytes':report['bytes']},ensure_ascii=False),flush=True)
