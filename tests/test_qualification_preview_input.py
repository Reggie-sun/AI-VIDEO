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
    assert 'captioned_music' not in receipt.model_dump()
    assert asset.tool.version == '7'
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


def _captioned_music_preview(tmp_path, *, opt_in=True, duration_samples=96_000,
        generated=False, bilingual=False, pending=False, conflict=False, ordinary_target=False):
    """Use real fixture WAV/canonical captions through public bootstrap and reopen."""
    import hashlib
    import yaml
    from ai_video.production.captions import CaptionImportRequest, caption_timing_fingerprint
    from ai_video.production.composition_contracts import AudioTrackSpec, CaptionTrackBinding, CompositionLayerSpec, CompositionSpec
    from ai_video.production.models import AssetRoleRequirement, AssetSourceKind, AssetType, CaptionTrack, DurationPolicy, Shot, VisualStrategy
    from ai_video.production.project import load_production_project
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production.state_commit import PreparedArtifact, prepare_audio_registry_commit
    from production_project_factory import make_p4_composition_fixture

    writer, arguments, artifacts = _qualification_bundle(tmp_path)
    root = arguments['target_root']
    reference = arguments['project'].artifacts.shots[0]
    shot_payload = next(a.payload for a in artifacts if a.relative_path == reference.path)
    changes = {'duration_policy': DurationPolicy(mode='fixed', seconds=2)}
    if not ordinary_target:
        changes.update({
        'visual_strategy': VisualStrategy.GENERATED_VIDEO,
        'generated_video_rationale': 'Offline qualification preview fixture',
        'required_asset_roles': (AssetRoleRequirement(role='final_visual', asset_ids=(),
            allowed_asset_types=(AssetType.VIDEO,)),)})
    shot = seal_artifact(Shot.model_validate(yaml.safe_load(shot_payload)).model_copy(update=changes))
    payload = yaml.safe_dump(shot.model_dump(mode='json'), sort_keys=False).encode()
    def artifact(path, data):
        return PreparedArtifact(path, data, hashlib.sha256(data).hexdigest())
    artifacts = tuple(artifact(reference.path, payload) if a.relative_path == reference.path else a
                      for a in artifacts)
    arguments['project'] = seal_artifact(arguments['project'].model_copy(update={
        'artifacts': arguments['project'].artifacts.model_copy(update={'shots': tuple(
            r.model_copy(update={'content_hash': shot.content_hash}) if r == reference else r
            for r in arguments['project'].artifacts.shots)})}))
    arguments['preview_use'].update(transform={'video_fit': 'cover'})
    sound_root = tmp_path / 'sound'
    sound_root.mkdir()
    sound, sound_spec = make_p4_composition_fixture(sound_root)
    music = next(a for a in sound.registry.assets if a.asset_id == 'bgm-theme')
    if generated:
        music = music.model_copy(update={'source_kind': AssetSourceKind.GENERATED,
            'audio_metadata': music.audio_metadata.model_copy(update={
                'source': music.audio_metadata.source.model_copy(update={'kind': AssetSourceKind.GENERATED})})})
    caption = next(a for a in sound.registry.assets if a.asset_type is AssetType.CAPTION)
    track = CaptionTrack.model_validate_json((sound_root / caption.artifact_path).read_bytes())
    track = track.model_copy(update={'source_audio_asset_id': music.asset_id,
                                    'source_audio_sha256': music.sha256})
    track = seal_artifact(track.model_copy(update={'timing_fingerprint': caption_timing_fingerprint(track)}))
    style = sound_spec.caption_tracks[0].style_reference
    style_bytes = (sound_root / style.path).read_bytes()
    imported = CaptionImportRequest.create(caption_track=track, style_reference=style, style_bytes=style_bytes)
    metadata = caption.caption_metadata.model_copy(update={
        'source_audio_asset_id': music.asset_id, 'source_audio_sha256': music.sha256,
        'timing_fingerprint': track.timing_fingerprint})
    caption = caption.model_copy(update={'sha256': hashlib.sha256(imported.track_bytes).hexdigest(),
        'size_bytes': len(imported.track_bytes), 'input_artifact_ids': (music.asset_id,),
        'input_fingerprint': music.sha256, 'caption_metadata': metadata})
    caption_inputs = [(caption, imported.track_bytes)]
    if bilingual:
        translated = track.model_copy(update={'artifact_id': 'caption-artifact-zh',
            'caption_track_id': 'caption-track-zh', 'language': 'zh-CN',
            'script_hash': hashlib.sha256('中文译句脚本'.encode()).hexdigest(),
            'transcript_hash': hashlib.sha256('你好世界'.encode()).hexdigest(),
            'segments': tuple(segment.model_copy(update={'text': text})
                for segment, text in zip(track.segments, ('你好', '世界')))})
        translated = seal_artifact(translated.model_copy(update={
            'timing_fingerprint': caption_timing_fingerprint(translated)}))
        imported_zh = CaptionImportRequest.create(caption_track=translated,
            style_reference=style, style_bytes=style_bytes)
        translated_asset = caption.model_copy(update={'asset_id': 'caption-asset-zh',
            'artifact_path': caption.artifact_path.with_name('caption-track-zh.json'),
            'sha256': hashlib.sha256(imported_zh.track_bytes).hexdigest(),
            'size_bytes': len(imported_zh.track_bytes),
            'caption_metadata': metadata.model_copy(update={
                'caption_track_id': translated.caption_track_id, 'language': translated.language,
                'script_hash': translated.script_hash, 'transcript_hash': translated.transcript_hash,
                'timing_fingerprint': translated.timing_fingerprint})})
        caption_inputs.append((translated_asset, imported_zh.track_bytes))
    caption_assets = tuple(asset for asset, _ in caption_inputs)
    base_registry = arguments['registry']
    registry = base_registry.model_copy(update={
        'schema_version': '2.1', 'assets': (*base_registry.assets, music, *caption_assets)})
    digest = registry_semantic_sha256(registry)
    arguments['registry'] = registry.model_copy(update={'revision_id': digest, 'content_hash': digest})
    music_track = AudioTrackSpec(track_id='song', asset_id=music.asset_id, audio_kind='bgm',
        start_sample=0, trim_start_sample=0, trim_duration_samples=duration_samples)
    if opt_in:
        arguments['captioned_music'] = {'track': music_track, 'audio_asset_sha256': music.sha256,
            'captions': tuple({'caption_asset_id': asset.asset_id, 'caption_asset_sha256': asset.sha256,
                'script_hash': asset.caption_metadata.script_hash,
                'transcript_hash': asset.caption_metadata.transcript_hash} for asset in caption_assets)}
    spec = seal_artifact(CompositionSpec(artifact_id='song-preview', revision=1, content_hash='0'*64,
        creation_receipt_id='song-preview', source_provenance=arguments['project'].source_provenance,
        schema_version='2.3', composition_id='song-preview', shot_ids=(shot.shot_id,),
        delivery_profile=arguments['project'].delivery_profile,
        layers=(CompositionLayerSpec(layer_id='visual', shot_id=shot.shot_id,
            asset_role='final_visual', asset_id=arguments['asset_id'], trim_start_frame=0,
            trim_duration_frames=48, transform={'video_fit': 'cover'}, source_audio_policy='REPLACE',
            source_audio_reason='Use only the explicitly bound external fixture song.'),),
        audio_tracks=(music_track,), caption_tracks=tuple(CaptionTrackBinding(
            binding_id=asset.asset_id, caption_asset_id=asset.asset_id,
            source_audio_track_id=music_track.track_id, style_reference=style)
            for asset in caption_assets)))
    before = {p.relative_to(arguments['source_root']): p.read_bytes()
              for p in arguments['source_root'].rglob('*') if p.is_file()}
    registry, captured = prepare_qualification_preview_input(**arguments)
    captured_record = next(a for a in registry.assets if a.asset_id == arguments['asset_id'])
    capture_records = [captured_record]
    if conflict:
        other = {**arguments, 'asset_id': 'other-preview', 'captioned_music': {
            **arguments['captioned_music'], 'track': music_track.model_copy(update={'track_id': 'other-song'})}}
        other_registry, other_artifacts = prepare_qualification_preview_input(**other)
        capture_records.append(next(a for a in other_registry.assets if a.asset_id == other['asset_id']))
        captured += tuple(a for a in other_artifacts
                          if a.relative_path not in {old.relative_path for old in captured})
    registry = base_registry.model_copy(update={
        'schema_version': '2.2', 'assets': (*base_registry.assets, *capture_records)})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={'revision_id': digest, 'content_hash': digest})
    writer.bootstrap_initial_state(attempt_id='song-preview-bootstrap', project=arguments['project'],
        registry=registry, artifacts=(*artifacts, *captured))
    loaded = load_production_project(root / 'project.yaml')
    assert music.asset_id not in loaded.asset_paths
    assert caption.asset_id not in loaded.asset_paths
    assert loaded.manifest.attempts == ()
    from ai_video.production.composition import resolve_composition
    with pytest.raises(AiVideoError):
        resolve_composition(loaded, spec, '0.7.103')
    if pending:
        return loaded, spec, arguments, before
    registry = loaded.registry.model_copy(update={'assets': (*loaded.registry.assets, music, *caption_assets)})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={'revision_id': digest, 'content_hash': digest})
    pointer = loaded.manifest.active_project
    writer.commit(prepare_audio_registry_commit(manifest=loaded.manifest, project=loaded.project,
        base_registry=loaded.registry, registry=registry, attempt_id='song-caption-import',
        artifacts=(artifact(music.artifact_path, (sound_root / music.artifact_path).read_bytes()),
            *(artifact(asset.artifact_path, data) for asset, data in caption_inputs), artifact(style.path, style_bytes)),
        active_project_artifact=artifact(pointer.path, (root / pointer.path).read_bytes())))
    loaded = load_production_project(root / 'project.yaml')
    return loaded, spec, arguments, before


@pytest.mark.parametrize('generated', [False, True])
def test_captioned_music_qualification_preview_public_resolution_stays_unaccepted(tmp_path, generated):
    from ai_video.production.composition import resolve_composition
    from ai_video.production.repair_input_admission import require_production_render_sources, verify_repair_input
    loaded, spec, arguments, before = _captioned_music_preview(tmp_path,
        generated=generated, bilingual=generated)
    timeline = resolve_composition(loaded, spec, '0.7.103')
    asset = next(a for a in loaded.registry.assets if a.asset_id == arguments['asset_id'])
    receipt = verify_repair_input(asset, loaded.root)
    assert receipt.contract_version == 'development-qualification-preview/2'
    assert receipt.qualification == 'NOT_EVALUATED'
    assert timeline.usage_scope == 'development_audio_preview'
    assert timeline.total_samples == 96_000
    assert timeline.audio_spans[0].track_id == 'song'
    assert {cue.text for cue in timeline.caption_cues} == (
        {'Hello', 'world', '你好', '世界'} if generated else {'Hello', 'world'})
    assert {attempt.operation for attempt in loaded.manifest.attempts} == {'audio_import'}
    assert {p.relative_to(arguments['source_root']): p.read_bytes()
            for p in arguments['source_root'].rglob('*') if p.is_file()} == before
    with pytest.raises(ValueError, match='cannot be activated'):
        require_production_render_sources(loaded.root, loaded.manifest.active_registry, timeline)


def test_song_captions_without_explicit_qualification_binding_are_rejected(tmp_path):
    with pytest.raises(AiVideoError, match='script hash is invalid'):
        _captioned_music_preview(tmp_path, opt_in=False)


def test_conflicting_captioned_music_captures_do_not_authorize_reader(tmp_path):
    with pytest.raises(AiVideoError, match='script hash is invalid'):
        _captioned_music_preview(tmp_path, conflict=True)


def test_unconsumed_captioned_music_capture_is_reopenable_but_not_resolvable(tmp_path):
    from ai_video.production.composition import resolve_composition
    loaded, spec, _, _ = _captioned_music_preview(tmp_path, pending=True)
    with pytest.raises(AiVideoError):
        resolve_composition(loaded, spec, '0.7.103')


def test_unused_capture_cannot_launder_song_captions_into_production(tmp_path):
    from ai_video.production.composition import resolve_composition
    from ai_video.production.composition_contracts import CompositionLayerSpec
    loaded, spec, _, _ = _captioned_music_preview(tmp_path, ordinary_target=True)
    role = loaded.shots[0].required_asset_roles[0]
    assert role.asset_ids
    ordinary = CompositionLayerSpec(layer_id='ordinary-visual', shot_id=loaded.shots[0].shot_id,
        asset_role=role.role, asset_id=role.asset_ids[0])
    spec = seal_artifact(spec.model_copy(update={'layers': (ordinary,)}))
    with pytest.raises(AiVideoError, match='actual qualification preview visuals'):
        resolve_composition(loaded, spec, '0.7.103')


@pytest.mark.parametrize('failure', ['changed_song_sha', 'extra_track', 'wrong_caption_track',
    'shot_caption', 'keep_native_audio', 'retimed_visual', 'short_song'])
def test_captioned_music_public_resolution_rejects_unsealed_changes(tmp_path, failure):
    from ai_video.production.composition import resolve_composition
    loaded, spec, _, _ = _captioned_music_preview(tmp_path,
        duration_samples=95_999 if failure == 'short_song' else 96_000)
    if failure == 'changed_song_sha':
        source = next(a for a in loaded.registry.assets if a.asset_id == spec.audio_tracks[0].asset_id)
        registry = loaded.registry.model_copy(update={'assets': tuple(
            a.model_copy(update={'sha256': 'b'*64}) if a == source else a
            for a in loaded.registry.assets)})
        loaded = loaded.model_copy(update={'registry': registry})
    elif failure == 'extra_track':
        spec = seal_artifact(spec.model_copy(update={'audio_tracks': (
            *spec.audio_tracks, spec.audio_tracks[0].model_copy(update={'track_id': 'extra-song'}))}))
    elif failure in {'wrong_caption_track', 'shot_caption'}:
        update = {'source_audio_track_id': 'other-song'} if failure == 'wrong_caption_track' else {
            'shot_id': spec.shot_ids[0]}
        spec = seal_artifact(spec.model_copy(update={'caption_tracks': (
            spec.caption_tracks[0].model_copy(update=update),)}))
    elif failure == 'keep_native_audio':
        spec = seal_artifact(spec.model_copy(update={'layers': (
            spec.layers[0].model_copy(update={'source_audio_policy': 'KEEP'}),)}))
    elif failure == 'retimed_visual':
        from ai_video.production.video_retime import VideoTimeMap
        time_map = VideoTimeMap.model_validate({'audio_policy': 'mute', 'points': [
            {'source_frame': 0, 'output_frame': 0}, {'source_frame': 48, 'output_frame': 40}]})
        spec = seal_artifact(spec.model_copy(update={'layers': (
            spec.layers[0].model_copy(update={'source_time_map': time_map}),)}))
    with pytest.raises(AiVideoError):
        resolve_composition(loaded, spec, '0.7.103')
