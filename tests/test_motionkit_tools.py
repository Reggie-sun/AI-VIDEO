"""Offline regressions for motion-kit tool failure and input identity boundaries."""
import importlib.util
import json
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image

TOOLS = Path(__file__).resolve().parents[1] / 'motion-kit' / 'tools'


def module(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize('length', [0, 1, 2047])
def test_short_audio_rejected(length):
    with pytest.raises(ValueError, match='at least 2048'):
        module('beatmap').stft_mag(np.zeros(length, np.float32))


@pytest.mark.parametrize('length', [2048, 8192])
def test_valid_stft_matches_explicit_bounded_windows(length):
    m = module('beatmap')
    x = np.random.default_rng(2).normal(size=length).astype(np.float32)
    expected = np.array([np.abs(np.fft.rfft(x[i:i+2048] * np.hanning(2048).astype(np.float32)))
                         for i in range(0, length-2048+1, 256)], dtype=np.float32)
    np.testing.assert_array_equal(m.stft_mag(x), expected)


@pytest.mark.parametrize('duration,exit_code', [(10, 0), (11, 2)])
def test_qa_exit_status_tracks_required_spec_and_keeps_report(tmp_path, monkeypatch, duration, exit_code):
    m = module('qa')
    comp = tmp_path / 'comp'; data = comp / 'data'; data.mkdir(parents=True)
    (data/'beats.json').write_text(json.dumps({'beats': list(np.arange(0, 20, .5)), 'downbeats': list(range(0,20,2))}))
    (data/'music.json').write_text('{}'); (data/'events.json').write_text('{"events": {}}')
    meta = {'streams': [{'codec_type':'video','width':1920,'height':1080,'r_frame_rate':'30/1','nb_frames':'300'}],
            'format':{'duration':'10'}}
    monkeypatch.setattr(m, 'probe', lambda _:meta)
    monkeypatch.setattr(m, 'read_small', lambda *args:np.zeros((300,108,192,3),np.uint8))
    monkeypatch.setattr(m, 'tile', lambda *args:None)
    monkeypatch.setattr(m, 'safe_overlay', lambda *args:None)
    def grab(video, frames, out, prefix):
        out.mkdir(parents=True, exist_ok=True)
        result = {}
        for f in set(frames):
            p=out/f'{f}.png'; Image.new('RGB',(1,1)).save(p); result[f]=p
        return result
    monkeypatch.setattr(m, 'grab', grab)
    out = tmp_path/'qa'
    monkeypatch.setattr('sys.argv', ['qa','--video','unused.mp4','--comp',str(comp),'--out',str(out),'--dur',str(duration)])
    assert m.main() == exit_code
    assert json.loads((out/'report.json').read_text())['verdicts']['spec'] == (duration == 10)
    assert (out/'report.md').is_file()


def plate_args(tmp_path, monkeypatch, ref):
    book=tmp_path/'prompts.md'; book.write_text('## P1\n```prompt\n中文画面\n```\n')
    dest=tmp_path/'result.png'; runs=tmp_path/'runs.md'
    monkeypatch.setattr('sys.argv',['plate','--book',str(book),'--plate','P1','--dest',str(dest),'--runs',str(runs),'--ref',str(ref)])
    return dest, runs


def test_reference_snapshot_survives_original_mutation(tmp_path, monkeypatch):
    m=module('codex_plate'); ref=tmp_path/'ref.png'; original=b'original-reference'; ref.write_bytes(original)
    dest,runs=plate_args(tmp_path,monkeypatch,ref)
    scratch=tmp_path/'scratch'; scratch.mkdir()
    # Redirect only the scratch parent; all execution is mocked.
    real_path=m.Path
    monkeypatch.setattr(m,'Path',lambda p: scratch if str(p)=='/tmp/ev-codex' else real_path(p))
    def execute(argv, **kwargs):
        root=Path(argv[argv.index('-C')+1]); intent=json.loads((root/'intent.json').read_text())
        frozen=Path(next(a.split('=',1)[1] for a in argv if a.startswith('--image=')))
        assert frozen != ref and frozen.read_bytes() == original
        assert intent['refs'][0]['sha256'] == hashlib.sha256(original).hexdigest()
        assert str(frozen) in kwargs['input']
        ref.unlink()
        Image.new('RGB',(2,2)).save(root/'P1.png')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(m.subprocess,'run',execute)
    assert m.main() == 0
    record=json.loads(runs.read_text().strip()[3:-1])
    assert record['refs'][0]['sha256'] == hashlib.sha256(original).hexdigest()
    assert Path(record['refs'][0]['frozen_path']).read_bytes() == original
    assert dest.is_file()


def test_existing_destination_rejected_before_generation(tmp_path,monkeypatch):
    m=module('codex_plate'); ref=tmp_path/'ref.png'; ref.write_bytes(b'ref')
    dest,_=plate_args(tmp_path,monkeypatch,ref); dest.write_bytes(b'keep')
    execute=Mock(); monkeypatch.setattr(m.subprocess,'run',execute)
    with pytest.raises(SystemExit): m.main()
    execute.assert_not_called()
    assert dest.read_bytes() == b'keep'
