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
from designs_context_v2 import context_title

REPO=Path.cwd();HERE=Path(__file__).resolve().parent
OLD=REPO/'outputs/shizhen-episode01/cold-open-execution-20261026/composition'
TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
BROWSER=Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')


def main():
    os.environ['PATH']=str(TOOLS)+os.pathsep+os.environ.get('PATH',os.defpath)
    inp=json.loads((OLD/'input-receipt.json').read_text())
    p=load_production_project(Path(inp['project'])/'project.yaml')
    m=importlib.util.spec_from_file_location('old_context_tools',OLD/'render.py')
    old=importlib.util.module_from_spec(m);m.loader.exec_module(old)
    font=old.font('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc','失帧翌夜',2,'Noto Serif CJK SC')
    layers=[];audio=[]
    for row in inp['sources']:
        layers.append(CompositionLayerSpec(layer_id='original-visual-'+row['shot_id'],
            shot_id=row['shot_id'],asset_role='primary_visual',asset_id=row['asset_id'],
            trim_start_frame=row['start'],trim_duration_frames=row['frames'],source_audio_policy='KEEP',
            transform=FixedTransform.model_validate(row['transform'])))
        audio.append(AudioTrackSpec(track_id='original-mix-'+row['shot_id'],audio_kind='dialogue',
            asset_id=row['audio_id'],shot_id=row['shot_id'],trim_start_sample=row['start']*2000,
            trim_duration_samples=row['frames']*2000))
    # Use only the rightmost city texture from the existing still. The mask is
    # an expressly photographic title plate; neither worker returns on screen.
    layers.insert(3,CompositionLayerSpec(layer_id='title-base',shot_id='TITLE',
        asset_role='primary_visual',asset_id='co-before-image',
        transform=FixedTransform(scale_x_milli=4000,scale_y_milli=4000,
                                 translate_x_px=-5760,translate_y_px=-1480)))
    audio.append(AudioTrackSpec(track_id='missing-response-title',audio_kind='bgm',asset_id=inp['music_asset_id'],
        start_sample=800000,trim_duration_samples=168000,gain_millidb=-8500,
        fade_in_samples=8000,fade_out_samples=16000))
    style=CaptionStyleReference.model_validate(inp['style'])
    spec=seal_artifact(CompositionSpec(artifact_id='portrait-in-narrative-context',schema_version='2.3',
        revision=1,content_hash='0'*64,creation_receipt_id='no-paid-title-context',
        source_provenance=p.project.source_provenance,composition_id='portrait-plus-S01-context',
        shot_ids=tuple(inp['order']),layers=tuple(layers),transitions=tuple(
            TransitionSpec(from_shot_id=a,to_shot_id=b,kind='cut',duration_frames=0)
            for a,b in zip(inp['order'],inp['order'][1:])),delivery_profile=p.project.delivery_profile,
        sample_rate=48000,requested_renderer='hyperframes',audio_tracks=tuple(audio),
        caption_tracks=(CaptionTrackBinding(binding_id='protected-S01-bilingual',caption_asset_id=inp['caption_id'],
            source_audio_track_id='original-mix-S01',shot_id='S01',style_reference=style),),
        text_layers=(*old.clock_graphics(),context_title(font))))
    timeline=resolve_composition(p,spec,renderer_version='0.7.103')
    assert timeline.total_frames==868 and timeline.total_samples==1736000
    expected=json.loads((OLD/'resolved-timeline.json').read_text())
    assert [x.model_dump(mode='json') for x in timeline.audio_spans]==expected['audio_spans']
    folder=HERE/'context-r2';folder.mkdir(exist_ok=True)
    (folder/'composition.json').write_text(spec.model_dump_json(indent=2))
    (folder/'resolved-timeline.json').write_text(timeline.model_dump_json(indent=2))
    stage=REPO/'runs/shizhen-episode01-jimeng25-20261025-001/cinematic-language-context-r2-20261026'
    stage.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(stage,0o700)
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
    selection=RendererSelectionReceipt(receipt_id='portrait-context',attempt_id='portrait-context',
        requested_kind='hyperframes',selected_kinds=('hyperframes',),renderer_version='0.7.103',
        timeline_fingerprint=timeline.composition_fingerprint,current_project=p.manifest.active_project,
        current_registry=p.manifest.active_registry)
    assets={x.asset_id:p.asset_paths[x.asset_id] for x in (*timeline.visual_spans,*timeline.audio_spans)}
    assets.update({x.caption_asset_id:p.asset_paths[x.caption_asset_id] for x in timeline.caption_cues})
    assets[style.artifact_id]=p.root/style.path
    before=(p.root/'state/manifest.json').read_bytes()
    result=adapter.render(HyperFramesRenderAttempt(attempt_id=selection.attempt_id,selection=selection,
        timeline=timeline,asset_sources=assets,allowed_asset_root=p.root,staging_root=stage/'source',
        allowed_staging_parent=stage,output_path=stage/'output/失帧-肖像与城市-前后语境研究.mp4',
        verification_snapshot_path=stage/'verified.mp4'))
    assert before==(p.root/'state/manifest.json').read_bytes()
    assert all(c.exit_code==0 and c.error_count==0 for c in result.checks)
    output=folder/'失帧-肖像与城市-前后语境研究.mp4'
    if output.exists():raise FileExistsError(output)
    shutil.copyfile(result.output.untrusted_staged_path,output)
    report={'output':str(output.relative_to(REPO)),'sha256':result.output.output_sha256,
        'bytes':result.output.output_size_bytes,'measured':result.output.measured.model_dump(mode='json'),
        'checks':[c.model_dump(mode='json') for c in result.checks],
        'audio_spans_identical_to_old':True,'usage_scope':timeline.usage_scope,
        'native_dialogue':'KEEP: identical source intervals, no gain or fade changes',
        'title_plate':'existing city image deliberately frozen inside portrait; no generated new shot',
        's01':'same 384 frames, original mix and bilingual captions',
        'paid_generation_calls':0,'human_review':'PENDING','publication':'NOT_PUBLISHED'}
    (folder/'render-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['output','sha256','bytes']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
