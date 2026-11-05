"""Offline checks for motion-kit/tools/sync_check.py on synthetic sung signals (no media, no ffmpeg)."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

TOOLS = Path(__file__).resolve().parents[1] / "motion-kit" / "tools"
SR = 16000


def module():
    spec = importlib.util.spec_from_file_location("sync_check", TOOLS / "sync_check.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def syllables(seed: int, dur: float = 5.0, start: float = 0.3) -> list[tuple[float, float, float]]:
    """(onset, length, pitch) of sung syllables separated by short gaps."""
    rng = np.random.default_rng(seed)
    out, t = [], start
    while t < dur - 0.6:
        n = float(rng.uniform(0.18, 0.45))
        out.append((t, n, float(rng.uniform(170, 330))))
        t += n + float(rng.uniform(0.06, 0.30))
    return out


def voice(syl, dur: float = 5.0, seed: int = 0, shift: float = 0.0, detune: float = 0.0) -> np.ndarray:
    """Harmonic tones with soft edges. A re-sung take keeps the rhythm but not the waveform: another seed
    (phases, breath noise), a per-syllable pitch offset up to `detune` and a light vibrato."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros_like(t)
    for on, n, f0 in syl:
        on += shift
        env = np.clip(np.minimum((t - on) / 0.02, (on + n - t) / 0.03), 0, 1)
        f = f0 * (1 + rng.uniform(-detune, detune))
        vib = (detune > 0) * 0.01 * np.sin(2 * np.pi * 5.5 * t)
        for h in range(1, 6):
            x += env * np.sin(2 * np.pi * f * h * t * (1 + vib) + rng.uniform(0, 2 * np.pi)) / h
    return (x + 0.01 * rng.normal(size=len(t))).astype(np.float32)


def shifted(x: np.ndarray, lag_s: float) -> np.ndarray:
    k = int(round(lag_s * SR))
    out = np.zeros_like(x)
    if k >= 0:
        out[k:] = x[:len(x) - k]
    else:
        out[:k] = x[-k:]
    return out


def run_check(m, monkeypatch, tmp_path, take: np.ndarray, ref: np.ndarray, song_t0: float = 18.4):
    paths = {tmp_path / "take.wav": take, tmp_path / "window.wav": ref}
    for p in paths:
        p.write_bytes(p.name.encode())
    monkeypatch.setattr(m, "decode", lambda p, sr=SR: paths[Path(p)])
    return m.check(tmp_path / "take.wav", tmp_path / "window.wav", song_t0)


@pytest.mark.parametrize("lag", [-0.4, -0.107, 0.0, 0.23, 0.83])
def test_a_copied_take_is_placed_at_its_own_lag(monkeypatch, tmp_path, lag):
    m = module()
    ref = voice(syllables(1))
    res = run_check(m, monkeypatch, tmp_path, shifted(ref, lag), ref)
    assert res["copy"] and res["ncc"] > 0.2
    assert abs(res["lag_s"] - lag) < 1e-3
    assert res["placement"]["method"].startswith("tool 15")
    assert res["divergence"]["rule"] == "none"
    # song time = song_t0 + clip time - lag: the take's clip 0 plays song_t0 - lag
    assert abs(res["placement"]["song_t_of_clip0"] - (18.4 - res["lag_s"])) < 1e-6
    covered = sum(b - a for a, b in (s["clip_s"] for s in res["spans"]))
    assert covered > 3.0


def test_a_take_that_stops_copying_diverges_there(monkeypatch, tmp_path):
    m = module()
    syl = syllables(2)
    ref = voice(syl)
    other = voice(syllables(9), seed=5)                       # a different line, sung over the second half
    split = int(2.6 * SR)
    take = np.concatenate([ref[:split], other[split:]])
    res = run_check(m, monkeypatch, tmp_path, take, ref)
    div = res["divergence"]["clip_s"]
    assert div is not None and 2.3 <= div <= 3.0, res["divergence"]
    assert res["synced_until"]["clip_s"] < div
    assert all(s["clip_s"][0] < div for s in res["spans"])


def test_a_re_sung_take_is_placed_by_its_envelope_lag(monkeypatch, tmp_path):
    m = module()
    syl = syllables(3)
    ref = voice(syl, seed=1)
    take = voice(syl, seed=2, shift=0.31, detune=0.04)          # same rhythm, new waveform, 0.31 s late
    res = run_check(m, monkeypatch, tmp_path, take, ref)
    assert not res["copy"]
    env = res["envelope"]
    assert abs(env["lag_s"] - 0.31) <= 0.02, env
    assert env["steady"] and len(env["segments"]) == 1
    assert res["placement"]["lag_s"] == env["lag_s"]
    assert "steady" in res["placement"]["method"]


def test_phrases_at_different_lags_become_segments():
    m = module()
    rows = [{"clip_t0": 0.25 * i, "clip_t1": 0.25 * i + 1.5, "lag_s": -0.39 if i < 5 else -0.08, "ncc": 0.8}
            for i in range(12)]
    segs = m.lag_segments(rows)
    assert [s["lag_s"] for s in segs] == [-0.39, -0.08]
    assert segs[0]["clip_s"][1] <= segs[1]["clip_s"][0]


def test_spans_bridge_silence_and_short_misses_but_drop_short_spans():
    m = module()
    n = 400
    active = np.zeros(n, bool)
    matched = np.zeros(n, bool)
    active[10:190] = True
    matched[10:60] = True                                      # 0.2 s of unmatched voice next: bridged
    matched[80:150] = True                                     # then 0.4 s of unmatched voice: the span ends
    active[200:260] = True
    matched[200:230] = True                                    # 0.3 s, then unmatched voice: too short, dropped
    active[300:330] = True
    matched[300:330] = True
    active[360:390] = True
    matched[360:390] = True                                    # a silence between two matches is bridged
    assert m.sync_spans(active, matched) == [(10, 149), (300, 389)]


def test_a_window_placed_on_the_take_timeline():
    m = module()
    ref = np.arange(10, dtype=np.float64) + 1
    assert list(m.place(ref, 3, 8)) == [0, 0, 0, 1, 2, 3, 4, 5]
    assert list(m.place(ref, -3, 5)) == [4, 5, 6, 7, 8]


def test_a_silent_or_missing_soundtrack_is_refused(monkeypatch):
    m = module()
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": b""})())
    with pytest.raises(ValueError, match="no audio"):
        m.decode(Path("nothing.mp4"))
