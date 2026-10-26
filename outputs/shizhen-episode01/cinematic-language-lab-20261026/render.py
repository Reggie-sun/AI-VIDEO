"""Render independent source-specific concept arms through the existing P4 owner."""
from pathlib import Path
import importlib.util
import hashlib
import json
import os
import shutil
import sys

from ai_video.production.models import (
    AudioTrackSpec, CompositionLayerSpec, CompositionSpec, RendererSelectionReceipt,
    FixedTransform, TransitionSpec,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.composition import resolve_composition
from ai_video.production.hyperframes import (
    HyperFramesAdapter, HyperFramesRenderAttempt, _NetworkIsolatedHyperFramesRunner,
    decoded_audio_sha256_fd_with_executable, probe_clip_fd_with_executable,
)
from designs import graphics

REPO=Path.cwd(); HERE=Path(__file__).resolve().parent
OLD=REPO/'outputs/shizhen-episode01/cold-open-execution-20261026/composition'
TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
BROWSER=Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')


def main():
    variant=sys.argv[1]
    if variant not in {'A','B','C'}:
        raise ValueError('Expected A, B or C')
    os.environ['PATH']=str(TOOLS)+os.pathsep+os.environ.get('PATH',os.defpath)
    receipt=json.loads((OLD/'input-receipt.json').read_text())
    p=load_production_project(Path(receipt['project'])/'project.yaml')
    before=(p.root/'state/manifest.json').read_bytes()
    mod_spec=importlib.util.spec_from_file_location('existing_font_tools',OLD/'render.py')
    font_tools=importlib.util.module_from_spec(mod_spec);mod_spec.loader.exec_module(font_tools)
    refined='--refined' in sys.argv
    font=font_tools.font('/usr/share/fonts/opentype/noto/'+('NotoSerifCJK-Bold.ttc' if refined else 'NotoSansCJK-Bold.ttc'),
                         '失帧翌夜',2,'Noto Serif CJK SC' if refined else 'Noto Sans CJK SC')
    draw=graphics
    if refined:
        from designs_refined import graphics as draw
    layers=[]
    for row in receipt['sources']:
        if row['shot_id'] not in {'CO-A2','CO-A3'}:
            continue
        layers.append(CompositionLayerSpec(layer_id='concept-source-'+row['shot_id'],
            shot_id=row['shot_id'],asset_role='primary_visual',asset_id=row['asset_id'],
            trim_start_frame=row['start'],trim_duration_frames=row['frames'],
            source_audio_policy='MUTE',
            source_audio_reason='MOTION_CONCEPT_ONLY: these abstract image/type arms are not a dialogue edit; protected original dialogue remains untouched',
            transform=FixedTransform.model_validate(row['transform'])))
    spec=seal_artifact(CompositionSpec(artifact_id='shizhen-language-arm-'+variant,
        schema_version='2.3',revision=1,content_hash='0'*64,
        creation_receipt_id='no-paid-motion-concept-'+variant,source_provenance=p.project.source_provenance,
        composition_id='shizhen-cinematic-language-'+variant,shot_ids=('CO-A2','CO-A3'),
        layers=tuple(layers),transitions=(TransitionSpec(from_shot_id='CO-A2',to_shot_id='CO-A3',kind='cut',duration_frames=0),),
        delivery_profile=p.project.delivery_profile,sample_rate=48000,requested_renderer='hyperframes',
        audio_tracks=(AudioTrackSpec(track_id='same-original-B-phrase',audio_kind='bgm',
            asset_id=receipt['music_asset_id'],start_sample=0,trim_duration_samples=432000,
            gain_millidb=-8500,fade_in_samples=8000,fade_out_samples=24000),),
        text_layers=draw(variant,font)))
    timeline=resolve_composition(p,spec,renderer_version='0.7.103')
    assert timeline.total_frames==216 and timeline.total_samples==432000
    assert timeline.usage_scope=='development_audio_preview'
    arm=HERE/(variant+'-refined' if refined else variant);arm.mkdir(exist_ok=True)
    (arm/'composition.json').write_text(spec.model_dump_json(indent=2))
    (arm/'resolved-timeline.json').write_text(timeline.model_dump_json(indent=2))
    if '--resolve-only' in sys.argv:
        print(json.dumps({'variant':variant,'resolved':True,'frames':216,'scope':timeline.usage_scope}),flush=True)
        return
    suffix=next((x.split('=',1)[1] for x in sys.argv if x.startswith('--local-attempt=')),'initial')
    stage=REPO/'runs/shizhen-episode01-jimeng25-20261025-001/cinematic-language-lab-20261026'/(variant+'-'+suffix)
    stage.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(stage,0o700)
    ip=Path('/usr/sbin/ip').resolve(strict=True)
    class Runner(_NetworkIsolatedHyperFramesRunner):
        def run(self,command,args,**kwargs):
            result=super().run(command,args,**kwargs)
            (stage/(command+'-local-diagnostic.json')).write_text(json.dumps({
                'command':command,'exit_code':result.returncode,'stdout':result.stdout,
                'stderr':result.stderr},ensure_ascii=False,indent=2))
            return result
    runner=Runner(project_root=REPO,binary=REPO/'node_modules/.bin/hyperframes',
        browser_path=BROWSER,ip_path=ip,unshare_path=Path('/usr/bin/unshare'),bash_path=Path('/usr/bin/bash'))
    adapter=HyperFramesAdapter(runner=runner,expected_version='0.7.103',browser_path=BROWSER,ip_path=ip,
        decoded_audio=lambda fd,rate,channels:decoded_audio_sha256_fd_with_executable(fd,rate,channels,TOOLS/'ffmpeg'),
        probe=lambda fd:probe_clip_fd_with_executable(fd,TOOLS/'ffprobe'))
    selection=RendererSelectionReceipt(receipt_id='language-'+variant,attempt_id='language-'+variant,
        requested_kind='hyperframes',selected_kinds=('hyperframes',),renderer_version='0.7.103',
        timeline_fingerprint=timeline.composition_fingerprint,current_project=p.manifest.active_project,
        current_registry=p.manifest.active_registry)
    assets={s.asset_id:p.asset_paths[s.asset_id] for s in (*timeline.visual_spans,*timeline.audio_spans)}
    output=stage/('output/失帧-视觉方向-'+variant+'-概念片.mp4')
    result=adapter.render(HyperFramesRenderAttempt(attempt_id=selection.attempt_id,selection=selection,
        timeline=timeline,asset_sources=assets,allowed_asset_root=p.root,staging_root=stage/'source',
        allowed_staging_parent=stage,output_path=output,verification_snapshot_path=stage/'verified.mp4'))
    assert before==(p.root/'state/manifest.json').read_bytes()
    assert all(c.exit_code==0 and c.error_count==0 for c in result.checks)
    dest=arm/output.name
    if dest.exists():
        raise FileExistsError(dest)
    shutil.copyfile(output,dest)
    report={'variant':variant,'output':str(dest.relative_to(REPO)),'sha256':result.output.output_sha256,
        'bytes':result.output.output_size_bytes,'measured':result.output.measured.model_dump(mode='json'),
        'checks':[c.model_dump(mode='json') for c in result.checks],
        'composition_fingerprint':timeline.composition_fingerprint,'usage_scope':timeline.usage_scope,
        'research_only':True,'live_action_acceptance':'NOT_EVALUATED','native_dialogue':'MUTED_IN_CONCEPT_ONLY',
        'source_manifest_unchanged':True,'paid_generation_calls':0,'publication':'NOT_PUBLISHED',
        'design_source_sha256':hashlib.sha256((HERE/('designs_refined.py' if refined else 'designs.py')).read_bytes()).hexdigest()}
    (arm/'render-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['variant','output','sha256','bytes']},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
