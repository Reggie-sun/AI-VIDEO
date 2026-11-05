import test from 'node:test';
import assert from 'node:assert/strict';
import { flapDone, flapText } from '../src/flap.js';
import { meterLevels, tickerOffset, timecode } from '../src/hud.js';
import { kineticState, stripRects } from '../src/kinetic.js';
import { kneeSeries } from '../src/osd-charts.js';
import { accentIndex, lyricState } from '../src/lyrics.js';
import { Clock, syntheticGrid } from '../src/clock.js';

const FPS = 30;

test('a flap resolves to its target, deterministically, and never early', () => {
  const t0 = 0.5, done = flapDone('03:47', t0);
  assert.equal(flapText('03:47', t0 - 1e-3, t0), null);
  assert.equal(flapText('03:47', done, t0), '03:47');
  for (let f = 15; f < done * FPS; f++) {
    const t = f / FPS, a = flapText('03:47', t, t0);
    assert.equal(a, flapText('03:47', t, t0), 'same t, same string');
    assert.equal(a.length, 5); assert.equal(a[2], ':', 'separators hold');
  }
  // a character that still flaps never shows its answer
  const mid = flapText('03:47', t0 + 1 / FPS, t0);
  for (let i of [0, 1, 3, 4]) assert.notEqual(mid[i], '03:47'[i]);
});

test('a flap changes only on ticks: never on two frames in a row (qa.py strobe scan)', () => {
  const t0 = 0.5;
  let prev = null, changedLast = false;
  for (let f = 15; f < 60; f++) {
    const s = flapText('03:47', f / FPS, t0);
    const changed = prev !== null && s !== prev;
    assert.ok(!(changed && changedLast), `frames ${f - 1} and ${f} both change`);
    changedLast = changed; prev = s;
  }
});

test('from: characters already shown hold while the others flap', () => {
  const s = flapText('11', 0.01, 0, { settle: 1, stagger: 0, from: '10' });
  assert.equal(s[0], '1');
  assert.notEqual(s[1], '1');
  assert.equal(flapDone('11', 0, { settle: 1, stagger: 0, from: '10' }), 1 / 15);
});

test('timecode counts frames from a start time of day', () => {
  const start = 3 * 3600 + 47 * 60 + 30;
  assert.equal(timecode(0, start, FPS), '03:47:30:00');
  assert.equal(timecode(1 / FPS, start, FPS), '03:47:30:01');
  assert.equal(timecode(30, start, FPS), '03:48:00:00');
});

test('the ticker offset wraps inside one period and is continuous', () => {
  for (const t of [0, 1.3, 7.7, 29.9]) {
    const o = tickerOffset(t, 42, 900);
    assert.ok(o >= 0 && o < 900);
  }
  assert.ok(Math.abs(tickerOffset(1 + 1 / FPS, 42, 1e6) - tickerOffset(1, 42, 1e6) - 42 / FPS) < 1e-9);
});

test('meter levels are a pure function of t, in 0..1', () => {
  const g = syntheticGrid();
  const clock = new Clock(g.beats, { ...g.hits, env24: { low: [0, 1, 0.5, 0.2], mid: [0.2, 0.4, 0.6, 0.8], high: [1, 0, 1, 0] } }, { fps: FPS });
  const a = meterLevels(clock, 0.07, 14), b = meterLevels(clock, 0.07, 14);
  assert.deepEqual(a, b);
  assert.equal(a.length, 14);
  for (const v of a) assert.ok(v >= 0 && v <= 1);
});

test('kinetic words are off before t0 and after the exit, landed while held', () => {
  const o = { t0: 1, t1: 2 };
  assert.equal(kineticState(0.99, o), null);
  assert.equal(kineticState(1.5, o).scale, 1);
  assert.equal(kineticState(1.5, o).cut, 0);
  assert.ok(kineticState(2 + 1 / FPS, o).cut > 0);
  assert.equal(kineticState(2 + 3 / FPS + 1e-6, o), null);
});

test('strip masks run only around the boundary; no bars after the cut when post = 0', () => {
  assert.equal(stripRects(10 - 0.3, 10).length, 0);
  assert.ok(stripRects(10 - 2 / FPS, 10).length > 0);
  assert.ok(stripRects(10, 10).length > 0);
  assert.equal(stripRects(10, 10, { post: 0 }).length, 0);
  assert.equal(stripRects(10 + 4 / FPS, 10).length, 0);
  const pre = stripRects(10 - 2 / FPS, 10);
  const area = pre.reduce((a, r) => a + Math.max(0, r.w) * r.h, 0);
  assert.ok(area < 0.05 * 1920 * 1080, 'thin strips keep the cut the largest change');
});

test('a knee series is flat before the knee and climbs after it', () => {
  const s = kneeSeries(48, { knee: 0.5, jitter: 0 });
  assert.equal(s[0], s[20]);
  assert.ok(s[47] > s[30] && s[30] > s[24]);
});

test('lyric accent marks one key word per line; no accent option leaves every word plain', () => {
  const lines = [{ en: 'a copy of your internet, cached.', zh: '', mode: 'spoken', start: 0, end: 2,
    words: ['a', 'copy', 'of', 'your', 'internet,', 'cached.'].map((text, i) => ({ text, start: i * 0.3, end: i * 0.3 + 0.25 })) }];
  assert.equal(accentIndex(lines[0], 'cached'), 5);
  assert.equal(accentIndex(lines[0], 'Internet'), 4);
  assert.equal(accentIndex(lines[0], 'missing'), -1);
  const st = lyricState(1, lines, s => s, { color: '#E3342F', keys: { 0: 'cached' } });
  assert.deepEqual(st.words.map(w => w.accent), [false, false, false, false, false, true]);
  assert.ok(lyricState(1, lines).words.every(w => !w.accent));
});
