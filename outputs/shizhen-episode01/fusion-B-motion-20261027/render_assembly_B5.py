"""Full narrative context; keep original timings, captured sound and captions."""
from pathlib import Path
import importlib.util
import json
import os
import shutil
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.composition import resolve_composition
from ai_video.production.hyperframes import (
    HyperFramesAdapter,HyperFramesRenderAttempt,_NetworkIsolatedHyperFramesRunner,
    decoded_audio_sha256_fd_with_executable,probe_clip_fd_with_executable,
)

import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'opening-A-revision-20261026'))
from title_design import FONT

REPO=Path.cwd();HERE=Path(__file__).resolve().parent
OLD=REPO/'outputs/shizhen-episode01/cold-open-execution-20261026/composition'
TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
BROWSER=Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')


def clocks(old):
    original=old.clock_graphics()
    before=[x for x in original if x.shot_id=='CO-A1']
    after=next(x for x in original if x.graphic_id=='clock-after')
    # Original A2 panel becomes visible at source frame 84; revised trim starts at 30.
    tail=after.model_copy(update={'start_frame_offset':54})
    return (*before,tail)

def tail_clocks(old):
    base=next(x for x in old.clock_graphics() if x.graphic_id=='clock-after')
    # 03:17:11 starts at output frame238; tail begins417 (7s+11frames later).
    out=[]
    for i,(offset,n,second) in enumerate([(0,26,18),(26,48,19),(74,48,20),(122,22,21)]):
        node=base.text_design.nodes[0]
        text=f'03:17:{second:02d}'
        node=node.model_copy(update={'node_id':'tail-time-'+str(i),'runs':(node.runs[0].model_copy(update={'text':text}),)})
        design=base.text_design.model_copy(update={'nodes':(node,)})
        out.append(base.model_copy(update={'graphic_id':'tail-time-'+str(i),'text':text,'shot_id':'CO-TAIL','start_frame_offset':offset,'duration_frames':n,'text_design':design}))
    return tuple(out)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['ASSEMBLY-B5'],default='ASSEMBLY-B5');args=parser.parse_args();variant=args.variant
    lead=0;total=561
    os.environ['PATH']=str(TOOLS)+os.pathsep+os.environ.get('PATH',os.defpath)
    inp=json.loads((HERE/'assembly-input-receipt.json').read_text())
    p=load_production_project(Path(inp['project'])/'project.yaml')
    m=importlib.util.spec_from_file_location('old_context_tools',OLD/'render.py')
    old=importlib.util.module_from_spec(m);m.loader.exec_module(old)
    font=old.font(FONT,'失帧',2,'Noto Serif CJK SC')
    layers=[];audio=[]
    for row in inp['sources']:
        layers.append(CompositionLayerSpec(layer_id='original-visual-'+row['shot_id'],
            shot_id=row['shot_id'],asset_role='primary_visual',asset_id=row['asset_id'],
            trim_start_frame=row['start'],trim_duration_frames=row['frames'],source_audio_policy='MUTE' if row['shot_id']=='CO-TAIL' else 'KEEP',
            source_audio_reason='Fusion title plate is silent; original rain explicitly retained' if row['shot_id']=='CO-TAIL' else None,
            transform=FixedTransform.model_validate(row['transform'])))
        if row['shot_id']!='CO-TAIL':
            audio.append(AudioTrackSpec(track_id='original-mix-'+row['shot_id'],audio_kind='dialogue',
                asset_id=row['audio_id'],shot_id=row['shot_id'],trim_start_sample=row['start']*2000,
                trim_duration_samples=row['frames']*2000))
        else:
            audio.append(AudioTrackSpec(track_id='rain-first',audio_kind='dialogue',asset_id=row['audio_id'],
                shot_id='CO-TAIL',trim_start_sample=576000,trim_duration_samples=144000,fade_out_samples=9600))
            audio.append(AudioTrackSpec(track_id='rain-continued',audio_kind='dialogue',asset_id=row['audio_id'],
                shot_id='CO-TAIL',start_sample=834000+134400,trim_start_sample=566400,
                trim_duration_samples=153600,fade_in_samples=9600))
    # Keep original B entrance relative to the event, extend its unlooped source into the city.
    music_start=706000
    audio.append(AudioTrackSpec(track_id='missing-response-after-reveal',audio_kind='bgm',asset_id=inp['music_asset_id'],start_sample=music_start,trim_duration_samples=total*2000-music_start,gain_millidb=-10000,fade_in_samples=24000,fade_out_samples=72000))
    order=['CO-A1','CO-A2','CO-A3','CO-TAIL']
    style=CaptionStyleReference.model_validate(inp['style'])
    spec=seal_artifact(CompositionSpec(artifact_id='event-led-narrative-integration',schema_version='2.3',
        revision=1,content_hash='0'*64,creation_receipt_id='no-paid-title-context',
        source_provenance=p.project.source_provenance,composition_id='two-passengers-standalone-002',
        shot_ids=tuple(order),layers=tuple(layers),transitions=tuple(
            TransitionSpec(from_shot_id=a,to_shot_id=b,kind='cut',duration_frames=0)
            for a,b in zip(order,order[1:])),delivery_profile=p.project.delivery_profile,
        sample_rate=48000,requested_renderer='hyperframes',audio_tracks=tuple(audio),
        caption_tracks=(CaptionTrackBinding(binding_id='A1-editorial-captions',caption_asset_id=inp['caption_id'],
            source_audio_track_id='original-mix-CO-A1',shot_id='CO-A1',style_reference=style),),
        text_layers=(*clocks(old),*tail_clocks(old))))
    timeline=resolve_composition(p,spec,renderer_version='0.7.103')
    assert timeline.total_frames==total and timeline.total_samples==total*2000
    folder=HERE/('variant-'+variant);folder.mkdir(exist_ok=False)
    (folder/'composition.json').write_text(spec.model_dump_json(indent=2))
    (folder/'resolved-timeline.json').write_text(timeline.model_dump_json(indent=2))
    stage=REPO/('runs/shizhen-fusion-B-motion-20261027/render-'+variant)
    stage.mkdir(parents=True,exist_ok=False,mode=0o700);os.chmod(stage,0o700)
    ip=Path('/usr/sbin/ip').resolve(strict=True)
    class Runner(_NetworkIsolatedHyperFramesRunner):
        def run(self,command,args,**kwargs):
            r=super().run(command,args,**kwargs)
            (stage/(command+'-diagnostic.json')).write_text(json.dumps({
                'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2))
            return r
    runner=Runner(project_root=REPO,binary=REPO/'node_modules/.bin/hyperframes',browser_path=BROWSER,
        ip_path=ip,unshare_path=Path('/usr/bin/unshare'),bash_path=Path('/usr/bin/bash'))
    adapter=HyperFramesAdapter(runner=runner,expected_version='0.7.103',browser_path=BROWSER,ip_path=ip,
        decoded_audio=lambda fd,rate,channels:decoded_audio_sha256_fd_with_executable(fd,rate,channels,TOOLS/'ffmpeg'),
        probe=lambda fd:probe_clip_fd_with_executable(fd,TOOLS/'ffprobe'))
    selection=RendererSelectionReceipt(receipt_id='event-led-integration',attempt_id='event-led-integration',
        requested_kind='hyperframes',selected_kinds=('hyperframes',),renderer_version='0.7.103',
        timeline_fingerprint=timeline.composition_fingerprint,current_project=p.manifest.active_project,
        current_registry=p.manifest.active_registry)
    assets={x.asset_id:p.asset_paths[x.asset_id] for x in (*timeline.visual_spans,*timeline.audio_spans)}
    assets.update({x.caption_asset_id:p.asset_paths[x.caption_asset_id] for x in timeline.caption_cues})
    assets[style.artifact_id]=p.root/style.path
    before=(p.root/'state/manifest.json').read_bytes()
    result=adapter.render(HyperFramesRenderAttempt(attempt_id=selection.attempt_id,selection=selection,
        timeline=timeline,asset_sources=assets,allowed_asset_root=p.root,staging_root=stage/'source',
        allowed_staging_parent=stage,output_path=stage/('output/失帧-独立开场-'+variant+'-结构预演.mp4'),
        verification_snapshot_path=stage/'verified.mp4'))
    assert before==(p.root/'state/manifest.json').read_bytes()
    assert all(c.exit_code==0 and c.error_count==0 for c in result.checks)
    output=folder/('失帧-独立开场-'+variant+'.mp4')
    if output.exists():raise FileExistsError(output)
    shutil.copyfile(result.output.untrusted_staged_path,output)
    report={'output':str(output.relative_to(REPO)),'sha256':result.output.output_sha256,
        'bytes':result.output.output_size_bytes,'size_bytes':result.output.output_size_bytes,'timeline_frames':total,'timeline_fingerprint':timeline.composition_fingerprint,'measured':result.output.measured.model_dump(mode='json'),
        'checks':[c.model_dump(mode='json') for c in result.checks],
        'source_audio_matches_new_visual_windows':False,'usage_scope':timeline.usage_scope,
        'native_dialogue':'KEEP exact native source sound; A3 starts at closeup frame361, trimming 25 pre-dialogue frames. No dialogue gain/fade changes',
        'title_plate':'User-approved B5 reused unchanged: six-second title-only optical-flow slowdown, original-speed rain/music. Same-station editorial return, no second disappearance. B5 first music sample 128000 continues preceding music without restart.',
        's01':'OUT_OF_SCOPE_NOT_INCLUDED',
        'paid_generation_calls':0,'human_review':'PENDING','publication':'NOT_PUBLISHED'}
    (folder/'render-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['output','sha256','bytes']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
