"""A local P4 type study, never a substitute for the missing live-action film."""
from pathlib import Path
import importlib.util
import json
import os

from ai_video.production.models import (
    AudioTrackSpec, CompositionLayerSpec, CompositionSpec, RendererSelectionReceipt,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.composition import resolve_composition
from ai_video.production.commercial_graphics import GraphicTreatment, GraphicRole
from ai_video.production.text_design import TextDesign, TextVisualNode, TextRun, MotionPose
from ai_video.production.hyperframes import (
    HyperFramesAdapter, HyperFramesRenderAttempt, _NetworkIsolatedHyperFramesRunner,
    decoded_audio_sha256_fd_with_executable, probe_clip_fd_with_executable,
)

REPO = Path.cwd()
HERE = Path(__file__).resolve().parent
OLD = REPO / 'outputs/shizhen-episode01/cold-open-execution-20261026/composition'
TOOLS = Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
BROWSER = Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')


def design(kind):
    module_spec = importlib.util.spec_from_file_location('existing_type_tools', OLD / 'render.py')
    old = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(old)
    title = kind == 'title'
    face = old.font('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', '失帧', 2,
                    'Noto Serif CJK SC') if title else old.font(
                        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                        '翌夜', 2, 'Noto Sans CJK SC')
    nodes = [TextVisualNode(node_id='opaque-field', purpose='Independent title field, no CG source visible',
                           x_px=0, y_px=0, width_px=1920, height_px=1080,
                           path='M0 0 L1920 0 L1920 1080 L0 1080 Z', fill='#10171B')]
    if title:
        # Individual boxes allow optical spacing without distorting either glyph.
        for i, (text, x) in enumerate((('失', 650), ('帧', 1010))):
            nodes.append(TextVisualNode(
                node_id='title-' + str(i), purpose='Intact, stable Chinese glyph; the interval carries absence',
                x_px=x, y_px=364, width_px=260, height_px=340,
                runs=(TextRun(text=text, font_family=face.family, font_size_px=244,
                              font_weight=700, color='#DCD5C7'),),
                motion=(MotionPose(frame=0, opacity_milli=0),
                        MotionPose(frame=14), MotionPose(frame=65),
                        MotionPose(frame=83, opacity_milli=0))))
    else:
        nodes.append(TextVisualNode(
            node_id='next-night', purpose='A separate temporal card, independent of main-title hierarchy',
            x_px=1530, y_px=802, width_px=220, height_px=80,
            runs=(TextRun(text='翌夜', font_family=face.family, font_size_px=44,
                          tracking_px=10, color='#BBC3C7'),),
            motion=(MotionPose(frame=0, opacity_milli=0), MotionPose(frame=10),
                    MotionPose(frame=65), MotionPose(frame=83, opacity_milli=0))))
    d = TextDesign(intent='Quiet independent cinematic typography study, not live-action story footage',
                   hierarchy='Main title has mass and an empty interval; the temporal card stays subordinate',
                   reference_width_px=1920, reference_height_px=1080,
                   fonts=(face,), nodes=tuple(nodes))
    return GraphicTreatment(graphic_id='live-action-' + kind + '-study', role=GraphicRole.HEADLINE,
                            text=d.text, shot_id='TITLE', start_frame_offset=0, duration_frames=84,
                            x_milli=0, y_milli=0, width_milli=1000,
                            font_size_px=244 if title else 44, font_weight=700 if title else 400,
                            text_color='#DCD5C7', z_index=100, text_design=d)


def main():
    os.environ['PATH'] = str(TOOLS) + os.pathsep + os.environ.get('PATH', os.defpath)
    inputs = json.loads((OLD / 'input-receipt.json').read_text())
    p = load_production_project(Path(inputs['project']) / 'project.yaml')
    before = (p.root / 'state/manifest.json').read_bytes()
    reports = []
    for kind in ('title', 'next-night'):
        graphic = design(kind)
        (HERE / (kind + '-design.json')).write_text(graphic.text_design.model_dump_json(indent=2))
        spec = seal_artifact(CompositionSpec(
            artifact_id='live-action-' + kind + '-type-study', schema_version='2.3', revision=1,
            content_hash='0' * 64, creation_receipt_id='local-type-study-only',
            source_provenance=p.project.source_provenance, composition_id='live-action-' + kind + '-study',
            shot_ids=('TITLE',), layers=(CompositionLayerSpec(
                layer_id='covered-base', shot_id='TITLE', asset_role='primary_visual', asset_id='co-before-image'),),
            delivery_profile=p.project.delivery_profile, sample_rate=48000, requested_renderer='hyperframes',
            audio_tracks=(AudioTrackSpec(track_id='existing-theme-study', audio_kind='bgm',
                asset_id=inputs['music_asset_id'], start_sample=0, trim_duration_samples=168000,
                gain_millidb=-8500, fade_in_samples=8000, fade_out_samples=16000),) if kind == 'title' else (),
            text_layers=(graphic,)))
        timeline = resolve_composition(p, spec, renderer_version='0.7.103')
        assert timeline.total_frames == 84
        (HERE / (kind + '-composition.json')).write_text(spec.model_dump_json(indent=2))
        (HERE / (kind + '-timeline.json')).write_text(timeline.model_dump_json(indent=2))
        stage = REPO / 'runs/shizhen-episode01-jimeng25-20261025-001/live-action-type-study-20261026' / kind
        stage.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(stage, 0o700)
        ip = Path('/usr/sbin/ip').resolve(strict=True)
        runner = _NetworkIsolatedHyperFramesRunner(
            project_root=REPO, binary=REPO / 'node_modules/.bin/hyperframes', browser_path=BROWSER,
            ip_path=ip, unshare_path=Path('/usr/bin/unshare'), bash_path=Path('/usr/bin/bash'))
        adapter = HyperFramesAdapter(runner=runner, expected_version='0.7.103', browser_path=BROWSER,
            ip_path=ip, decoded_audio=lambda fd, rate, channels:
                decoded_audio_sha256_fd_with_executable(fd, rate, channels, TOOLS / 'ffmpeg'),
            probe=lambda fd: probe_clip_fd_with_executable(fd, TOOLS / 'ffprobe'))
        selection = RendererSelectionReceipt(
            receipt_id='local-type-study-' + kind, attempt_id='local-type-study-' + kind,
            requested_kind='hyperframes', selected_kinds=('hyperframes',), renderer_version='0.7.103',
            timeline_fingerprint=timeline.composition_fingerprint,
            current_project=p.manifest.active_project, current_registry=p.manifest.active_registry)
        assets = {s.asset_id: p.asset_paths[s.asset_id] for s in (*timeline.visual_spans, *timeline.audio_spans)}
        output = stage / ('output/' + kind + '-typography-study.mp4')
        result = adapter.render(HyperFramesRenderAttempt(
            attempt_id=selection.attempt_id, selection=selection, timeline=timeline, asset_sources=assets,
            allowed_asset_root=p.root, staging_root=stage / 'source', allowed_staging_parent=stage,
            output_path=output, verification_snapshot_path=stage / 'verified.mp4'))
        assert before == (p.root / 'state/manifest.json').read_bytes()
        assert all(c.exit_code == 0 and c.error_count == 0 for c in result.checks)
        import shutil
        dest = HERE / output.name
        if dest.exists():
            raise FileExistsError(dest)
        shutil.copyfile(output, dest)
        reports.append({'kind':kind, 'path':str(dest.relative_to(REPO)),
                        'sha256':result.output.output_sha256, 'bytes':result.output.output_size_bytes,
                        'measured':result.output.measured.model_dump(mode='json'),
                        'checks':[c.model_dump(mode='json') for c in result.checks],
                        'scope':'TYPE_STUDY_ONLY', 'not_live_action_footage':True,
                        'new_paid_generation_calls':0, 'production_activation':False})
        print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    (HERE / 'render-receipt.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
