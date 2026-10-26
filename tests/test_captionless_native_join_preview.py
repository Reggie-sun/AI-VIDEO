"""Original dialogue review does not require creating subtitles before approval."""
from types import SimpleNamespace
import pytest
from ai_video.production._composition_visual import _validate_captured_dialogue_preview
from test_caption_development_preview import _resolved_preview_fixture


def test_captionless_preview_keeps_exact_source_and_audio_window_guards(monkeypatch):
    import ai_video.production.repair_input_admission as admission
    monkeypatch.setattr(admission, 'allows_repair_preview_layer', lambda *_:True)
    monkeypatch.setattr(admission, 'verify_repair_input', lambda *_:SimpleNamespace(
        preview_use=SimpleNamespace(scope='replacement_audio_preview')))
    for change, expected in [(None,None),('source','exact captured video bytes'),
                              ('trim','exact unmodified visual source interval')]:
        kwargs={'source_video_sha':'e'*64} if change=='source' else (
            {'audio_end':767999} if change=='trim' else {})
        project,spec,timeline,shots=_resolved_preview_fixture(**kwargs)
        spec.caption_tracks=()
        def check():
            _validate_captured_dialogue_preview(project,spec,timeline,shots,
                dialogue_tracks=spec.audio_tracks,invalid=lambda message,*_:ValueError(message))
        if expected:
            with pytest.raises(ValueError,match=expected):check()
        else:check()
