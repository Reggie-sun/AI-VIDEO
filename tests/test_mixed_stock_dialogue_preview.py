"""Authored silent stock must not make captured dialogue optional."""
from types import SimpleNamespace as NS
import pytest
from ai_video.production.models import AssetSourceKind, AssetType, VisualStrategy
from ai_video.production.composition_contracts import CompositionLayerSpec
from ai_video.production._composition_visual import _validate_captured_dialogue_preview
from test_caption_development_preview import _two_captured_dialogue_previews


@pytest.mark.parametrize('failure', [None, 'speech', 'narration', 'keep', 'unbound',
    'generated', 'capture', 'missing_original', 'changed_original', 'short_original'])
def test_silent_imported_stock_preserves_every_original_dialogue_guard(monkeypatch, failure):
    import ai_video.production.repair_input_admission as admission
    monkeypatch.setattr(admission, 'allows_repair_preview_layer', lambda *_: True)
    monkeypatch.setattr(admission, 'verify_repair_input', lambda *_: NS(
        preview_use=NS(scope='replacement_audio_preview')))
    monkeypatch.setattr(admission, 'is_repair_input_record', lambda asset, *_:
        asset.asset_id != 'stock' or failure == 'capture')
    p, spec, timeline, shots = _two_captured_dialogue_previews()
    stock = NS(asset_id='stock', asset_type=AssetType.VIDEO,
               source_kind=AssetSourceKind.IMPORTED)
    p.registry.assets += (stock,)
    shots['world'] = NS(shot_id='world', visual_strategy=VisualStrategy.EXISTING_VIDEO,
        dialogue='', narration='', required_asset_roles=(NS(role='primary_visual', asset_ids=('stock',)),))
    spec.shot_ids += ('world',)
    layer = CompositionLayerSpec(layer_id='world', shot_id='world', asset_role='primary_visual',
        asset_id='stock', trim_start_frame=0, trim_duration_frames=48,
        source_audio_policy='MUTE', source_audio_reason='Authored speech-free licensed city footage')
    spec.layers += (layer,)
    timeline.visual_spans += (NS(layer_id='world',start_sample=timeline.total_samples,
        duration_samples=96000),)
    timeline.total_samples += 96000
    if failure == 'speech': shots['world'].dialogue = 'not silent'
    elif failure == 'narration': shots['world'].narration = 'new voice'
    elif failure == 'keep': spec.layers = (*spec.layers[:-1], layer.model_copy(update={'source_audio_policy':'KEEP'}))
    elif failure == 'unbound': shots['world'].required_asset_roles = ()
    elif failure == 'generated': stock.source_kind = AssetSourceKind.GENERATED
    elif failure == 'missing_original': spec.audio_tracks = spec.audio_tracks[:1]
    elif failure == 'changed_original': p.registry.assets[3].audio_metadata.source.input_fingerprint='f'*64
    elif failure == 'short_original': timeline.audio_spans[1].duration_samples -= 1
    def check():
        _validate_captured_dialogue_preview(p,spec,timeline,shots,
            dialogue_tracks=spec.audio_tracks,invalid=lambda message,*_:ValueError(message))
    if failure is None: check()
    else:
        with pytest.raises(ValueError): check()
