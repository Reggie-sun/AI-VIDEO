"""Qualification trials remain separate from failures and Production source use."""
import pytest
from ai_video.errors import AiVideoError

from ai_video.production.hashing import seal_artifact
from ai_video.production.qualification_preview_input import prepare_qualification_preview_input
from ai_video.production.state_commit import ProductionStateCommitter
from test_production_bootstrap import _bootstrap_inputs
from test_repair_input_admission import _preview_arguments
from test_generation_quality_rejection import _fetched_experience
from test_production_generated_video_e2e import ATTEMPT_ID


def _qualification_bundle(tmp_path):
    from test_jimeng_qualification_trial import make_fetched_qualification_trial
    from ai_video.production.project import load_production_project
    from ai_video.production.video import ResolvedVideoGenerationRequest, VideoFetchReceipt
    from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt
    source=tmp_path/'source';source.mkdir()
    _,_,committer,attempt_id=make_fetched_qualification_trial(source)
    manifest=committer._read_manifest()
    state=committer._video_attempt(manifest,attempt_id).video_generation_state
    request=ResolvedVideoGenerationRequest.model_validate_json((source/state.request.path).read_bytes())
    fetch=VideoFetchReceipt.model_validate_json((source/state.fetch_receipt.path).read_bytes())
    measured=MeasuredVideoMetadata(container_name='mp4',codec_name='h264',width=640,height=360,
        fps_numerator=24,fps_denominator=1,duration_milliseconds=2000,frame_count=48,
        audio_stream_count=1,size_bytes=fetch.size_bytes,artifact_sha256=fetch.artifact_sha256)
    probe=VideoProbeReceipt.create(request=request,fetch_receipt=fetch,measured=measured)
    target=tmp_path/'target';target.mkdir()
    template=tmp_path/'template';template.mkdir()
    writer=ProductionStateCommitter(target)
    project,registry,artifacts=_bootstrap_inputs(template,writer)
    project=seal_artifact(project.model_copy(update={'project_id':'qualification-review'}))
    original=load_production_project(template/'project.yaml')
    use=dict(shot_id=original.shots[0].shot_id,asset_role='final_visual',trim_start_frame=0,
        trim_duration_frames=48,source_time_map={'contract_version':'video-time-map/1',
            'audio_policy':'mute','points':[{'source_frame':0,'output_frame':0},
                {'source_frame':48,'output_frame':48}]},transform={},scope='replacement_audio_preview')
    arguments=dict(target_root=target,project=project,registry=registry,source_root=source,
        source_attempt_id=attempt_id,source_sha256=fetch.artifact_sha256,asset_id='trial-preview',
        usage_license='fixture only',preview_use=use,preview_probe=probe)
    return writer,arguments,artifacts


def test_exact_paid_trial_capture_strict_reopens_and_cannot_promote(tmp_path):
    from types import SimpleNamespace
    from ai_video.production.project import load_production_project
    from ai_video.production.repair_input_admission import verify_repair_input, require_production_render_sources
    writer,arguments,artifacts=_qualification_bundle(tmp_path)
    source=arguments['source_root'];target=arguments['target_root']
    before={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    registry,captured=prepare_qualification_preview_input(**arguments)
    writer.bootstrap_initial_state(attempt_id='qualification-preview-bootstrap',
        project=arguments['project'],registry=registry,artifacts=(*artifacts,*captured))
    loaded=load_production_project(target/'project.yaml')
    asset=next(a for a in loaded.registry.assets if a.asset_id=='trial-preview')
    receipt=verify_repair_input(asset,target)
    assert receipt.contract_version=='development-qualification-preview/1'
    assert receipt.qualification=='NOT_EVALUATED'
    assert loaded.manifest.attempts==()
    assert loaded.manifest.active_paid_provider_budget is None
    assert not any(asset.asset_id in r.asset_ids for s in loaded.shots for r in s.required_asset_roles)
    assert {p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}==before
    with pytest.raises(ValueError,match='cannot be activated'):
        require_production_render_sources(target,loaded.manifest.active_registry,
            SimpleNamespace(visual_spans=(SimpleNamespace(asset_sha256=asset.sha256),)))


def test_qualification_capture_rejects_changed_exact_bytes(tmp_path):
    writer,arguments,_=_qualification_bundle(tmp_path)
    source=arguments['source_root']
    state=next(a.video_generation_state for a in writer.__class__(source)._read_manifest().attempts
        if a.attempt_id==arguments['source_attempt_id'])
    media=source/state.fetch_receipt.artifact_path
    media.write_bytes(media.read_bytes()+b'changed')
    with pytest.raises(AiVideoError) as error:
        prepare_qualification_preview_input(**arguments)
    assert error.value.retryable is False
    assert not (arguments['target_root']/'state/manifest.json').exists()


def test_production_fetch_cannot_be_relabelled_as_qualification_preview(tmp_path):
    source=tmp_path/'source';source.mkdir()
    _, experience, _, _=_fetched_experience(source, verdict='PASS')
    template=tmp_path/'template';template.mkdir()
    target=tmp_path/'target';target.mkdir()
    writer=ProductionStateCommitter(target)
    project,registry,artifacts=_bootstrap_inputs(template,writer)
    project=seal_artifact(project.model_copy(update={'project_id':'qualification-review'}))
    arguments=dict(source_sha256=experience.evidence[0].artifact_sha256,project=project)
    # The helper measures fixture bytes and supplies an exact bounded preview use.
    use,probe,_=_preview_arguments(source,{**arguments,'artifacts':artifacts})
    use.update(scope='replacement_audio_preview',source_time_map={
        'contract_version':'video-time-map/1','audio_policy':'mute',
        'points':[{'source_frame':0,'output_frame':0},{'source_frame':48,'output_frame':48}]})
    before={p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()}
    with pytest.raises(AiVideoError) as error:
        prepare_qualification_preview_input(target_root=target,project=project,registry=registry,
            source_root=source,source_attempt_id=ATTEMPT_ID,
            source_sha256=arguments['source_sha256'],asset_id='trial-preview',
            usage_license='fixture only',preview_use=use,preview_probe=probe)
    assert 'exact paid source chain' in error.value.technical_detail
    assert {p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()}==before
