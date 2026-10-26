"""Exact development cut via canonical CompositionSpec/ResolvedTimeline/HyperFrames."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.composition import resolve_composition
from ai_video.production.hyperframes import (
    HyperFramesAdapter,HyperFramesRenderAttempt,_NetworkIsolatedHyperFramesRunner,
    decoded_audio_sha256_fd_with_executable,probe_clip_fd_with_executable,
)
from authoring import write
from graphics import graphics

REPO=Path.cwd();HERE=Path(__file__).resolve().parent
TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
BROWSER=Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')


def main():
    os.environ['PATH']=str(TOOLS)+os.pathsep+os.environ.get('PATH',os.defpath)
    inp=json.loads((HERE/'input-receipt.json').read_text());p=load_production_project(Path(inp['project'])/'project.yaml')
    layers=[]
    for sid,asset,start,n in [('CITY','stock-city',24,126),('ROAD','stock-road',144,66)]:
        layers.append(CompositionLayerSpec(layer_id='visual-'+sid,shot_id=sid,asset_role='primary_visual',asset_id=asset,
            trim_start_frame=start,trim_duration_frames=n,source_audio_policy='MUTE',
            source_audio_reason='Temporary stock macro previs only, explicitly remove its unrelated sound'))
    for row in inp['rows']:
        layers.append(CompositionLayerSpec(layer_id='visual-'+row['shot_id'],shot_id=row['shot_id'],
            asset_role='primary_visual',asset_id=row['asset_id'],trim_start_frame=row['start'],
            trim_duration_frames=row['frames'],transform=FixedTransform.model_validate(row['transform']),
            source_audio_policy='MUTE',source_audio_reason='Visual opening re-edit, not dialogue scene; original sources and speech protected; replace with original B score and separately bound ambience/effects'))
    # One selected recording, no stretch or new generated music. The score
    # briefly recedes under full occlusion; rain and truck remain ordinary.
    # Durations are authored inputs; all final timing is resolved below.
    audio=[AudioTrackSpec(track_id='B-world',audio_kind='bgm',asset_id=inp['music_asset_id'],start_sample=0,
        trim_start_sample=0,trim_duration_samples=696000,gain_millidb=-6500,fade_in_samples=48000,fade_out_samples=16000),
        AudioTrackSpec(track_id='B-occluded',audio_kind='bgm',asset_id=inp['music_asset_id'],start_sample=696000,
            trim_start_sample=696000,trim_duration_samples=144000,gain_millidb=-18000,fade_in_samples=1000,fade_out_samples=1000),
        AudioTrackSpec(track_id='B-absence',audio_kind='bgm',asset_id=inp['music_asset_id'],start_sample=840000,
            trim_start_sample=840000,trim_duration_samples=536000,gain_millidb=-6500,fade_in_samples=24000,fade_out_samples=48000),
        AudioTrackSpec(track_id='real-rain-bed',audio_kind='ambience',asset_id='rain-public-domain',start_sample=0,
            trim_start_sample=96000,trim_duration_samples=1376000,gain_millidb=-24000,fade_in_samples=96000,fade_out_samples=24000),
        AudioTrackSpec(track_id='original-truck-reveal',audio_kind='sfx',asset_id='original-truck-pass',shot_id='CO-A2',
            trim_start_sample=0,trim_duration_samples=192000,gain_millidb=-10500,fade_in_samples=2400,fade_out_samples=14400)]
    spec=seal_artifact(CompositionSpec(artifact_id='opening-reconstruction-composition',schema_version='2.3',revision=1,
        content_hash='0'*64,creation_receipt_id='opening-reconstruction-local',source_provenance=p.project.source_provenance,
        composition_id='shizhen-opening-reconstruction',shot_ids=tuple(inp['order']),layers=tuple(layers),
        transitions=tuple(TransitionSpec(from_shot_id=a,to_shot_id=b,kind='cut',duration_frames=0)
                          for a,b in zip(inp['order'],inp['order'][1:])),delivery_profile=p.project.delivery_profile,
        sample_rate=48000,requested_renderer='hyperframes',audio_tracks=tuple(audio),text_layers=graphics()))
    timeline=resolve_composition(p,spec,renderer_version='0.7.103')
    assert timeline.total_frames==688 and timeline.total_samples==1376000
    assert timeline.usage_scope=='development_audio_preview'
    write('composition.json',spec.model_dump(mode='json'));write('resolved-timeline.json',timeline.model_dump(mode='json'))
    print(json.dumps(dict(resolved=True,frames=timeline.total_frames,scope=timeline.usage_scope)),flush=True)
    if '--resolve-only' in sys.argv:return
    attempt=next((s.split('=',1)[1] for s in sys.argv if s.startswith('--attempt=')),'001')
    stage=REPO/'runs/shizhen-opening-reconstruction-20261026'/('render-'+attempt)
    if stage.exists():raise FileExistsError('Use a new local render attempt, never overwrite prior result')
    stage.mkdir(parents=True,mode=0o700);ip=Path('/usr/sbin/ip').resolve(strict=True)
    class Runner(_NetworkIsolatedHyperFramesRunner):
        def run(self,command,args,**kw):
            r=super().run(command,args,**kw)
            (stage/(command+'-diagnostic.json')).write_text(json.dumps(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),ensure_ascii=False,indent=2))
            return r
    runner=Runner(project_root=REPO,binary=REPO/'node_modules/.bin/hyperframes',browser_path=BROWSER,
        ip_path=ip,unshare_path=Path('/usr/bin/unshare'),bash_path=Path('/usr/bin/bash'))
    adapter=HyperFramesAdapter(runner=runner,expected_version='0.7.103',browser_path=BROWSER,ip_path=ip,
        decoded_audio=lambda fd,rate,channels:decoded_audio_sha256_fd_with_executable(fd,rate,channels,TOOLS/'ffmpeg'),
        probe=lambda fd:probe_clip_fd_with_executable(fd,TOOLS/'ffprobe'))
    selection=RendererSelectionReceipt(receipt_id='opening-render-'+attempt,attempt_id='opening-render-'+attempt,
        requested_kind='hyperframes',selected_kinds=('hyperframes',),renderer_version='0.7.103',
        timeline_fingerprint=timeline.composition_fingerprint,current_project=p.manifest.active_project,current_registry=p.manifest.active_registry)
    assets={s.asset_id:p.asset_paths[s.asset_id] for s in (*timeline.visual_spans,*timeline.audio_spans)}
    before=(p.root/'state/manifest.json').read_bytes()
    result=adapter.render(HyperFramesRenderAttempt(attempt_id=selection.attempt_id,selection=selection,timeline=timeline,
        asset_sources=assets,allowed_asset_root=p.root,staging_root=stage/'source',allowed_staging_parent=stage,
        output_path=stage/'output/失帧-开场重构-动态预演.mp4',verification_snapshot_path=stage/'verified.mp4'))
    assert before==(p.root/'state/manifest.json').read_bytes()
    assert all(c.exit_code==0 and c.error_count==0 for c in result.checks)
    dest=HERE/('失帧-开场重构-动态预演-'+attempt+'.mp4')
    if dest.exists():raise FileExistsError(dest)
    shutil.copyfile(result.output.untrusted_staged_path,dest)
    report=dict(output=str(dest.relative_to(REPO)),sha256=result.output.output_sha256,bytes=result.output.output_size_bytes,
        measured=result.output.measured.model_dump(mode='json'),checks=[c.model_dump(mode='json') for c in result.checks],
        composition_fingerprint=timeline.composition_fingerprint,usage_scope=timeline.usage_scope,
        source_manifest_unchanged=True,new_video_generation_calls=0,new_image_generation_calls=0,new_music_generation_calls=0,
        native_dialogue='Explicit MUTE in visual opening only; original source files retained',
        audio_semantics='NOT_EVALUATED until actual exact mix observation',artistic_acceptance='PENDING',
        production_activation=False,publication_state='NOT_PUBLISHED',render_attempt=attempt)
    write('render-receipt-'+attempt+'.json',report)
    print(json.dumps(dict(output=report['output'],sha256=report['sha256'],bytes=report['bytes']),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
