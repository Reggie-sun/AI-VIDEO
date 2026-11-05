import test from 'node:test';
import assert from 'node:assert/strict';
import { HEADLINE, drawLyrics, headlineLayout, lyricState, stackLayout, stripTrailing } from '../src/lyrics.js';

const FPS = 30;
const lines = [
  { en: 'One resolver, misconfigured —', zh: '一个解析器 配置错误', mode: 'spoken', start: 1.0, end: 2.4,
    words: [{ text: 'One', start: 1.0, end: 1.2 }, { text: 'resolver,', start: 1.25, end: 1.8 },
            { text: 'misconfigured', start: 1.9, end: 2.4 }] },
  { en: 'I just looked outside.', zh: '我只是看了看外面', mode: 'sung', start: 2.6, end: 4.0,
    words: [{ text: 'I', start: 2.6, end: 2.9 }, { text: 'just', start: 2.9, end: 3.2 },
            { text: 'looked', start: 3.2, end: 3.5 }, { text: 'outside.', start: 3.5, end: 4.0 }] },
];

test('a word is dim before its onset and fully lit one frame after it', () => {
  for (const L of lines) {
    for (const [k, w] of L.words.entries()) {
      const before = lyricState(w.start - 0.5 / FPS, lines);
      const after = lyricState(w.start + 1 / FPS, lines);
      if (before && before.index === lines.indexOf(L)) assert.ok(before.words[k].level < 0.5, `${w.text} dim before`);
      assert.equal(after.index, lines.indexOf(L));
      assert.ok(after.words[k].level >= 0.9, `${w.text} lit one frame after onset`);
    }
  }
});

test('at most one line is on screen and lines advance in order', () => {
  let last = -1;
  for (let f = 0; f < 5 * FPS; f++) {
    const st = lyricState(f / FPS, lines);
    if (!st) continue;
    assert.ok(st.index >= last, 'line order never goes back');
    last = st.index;
    assert.ok(st.alpha >= 0 && st.alpha <= 1);
  }
  assert.equal(last, 1);
});

test('the next line replaces the previous one before its first word', () => {
  const st = lyricState(2.6 - 0.01, lines);
  assert.equal(st.index, 1);
});

test('displayed lines carry no trailing punctuation; inner punctuation stays', () => {
  const st = lyricState(2.0, lines);
  assert.deepEqual(st.words.map(w => w.text), ['One', 'resolver,', 'misconfigured']);
  assert.equal(stripTrailing('outside.'), 'outside');
  assert.equal(stripTrailing('misconfigured —'), 'misconfigured');
  assert.equal(stripTrailing('一扇门 没关'), '一扇门 没关');
});

test('song offset maps word times into comp time', () => {
  const offset = 0.5;
  const st = lyricState(1.0 + offset + 1 / FPS, lines, s => s + offset);
  assert.ok(st.words[0].level >= 0.9);
  assert.equal(lyricState(1.0 + 1 / FPS - 0.3, lines, s => s + offset), null);
});

test('a stacked sung line puts one word per row, in order, with the translation under the last row', () => {
  const st = lyricState(3.3, lines);
  const lay = stackLayout(st, { x: 120, top: 250, size: 100, lead: 1 });
  assert.deepEqual(lay.rows.map(r => r.text), ['I', 'just', 'looked', 'outside']);
  for (let k = 1; k < lay.rows.length; k++) assert.ok(lay.rows[k].y > lay.rows[k - 1].y, 'rows go down');
  assert.ok(lay.rows.every(r => r.x === 120));
  assert.ok(lay.zh.y > lay.rows[lay.rows.length - 1].y);
  assert.equal(lay.zh.text, '我只是看了看外面');
});

// a fake 2D context: records fillText calls; every glyph is 0.5 em wide
function recorder() {
  const calls = [];
  let size = 10;
  const ctx = { calls, save() {}, restore() {}, set font(v) { size = Number(/(\d+(?:\.\d+)?)px/.exec(v)[1]); }, get font() { return `${size}px x`; },
    measureText: s => ({ width: s.length * size * 0.5 }), fillText(text, x, y) { calls.push({ text, x, y, alpha: this.globalAlpha, color: this.fillStyle }); } };
  return ctx;
}

test('headline: no translation, left aligned at x, rows bottom-anchored, words appear as they are voiced, accent in red', () => {
  const opts = { headline: { x: 76, bottom: 968, size: 96, maxWidth: 700 }, accent: { color: '#E3342F', keys: { 0: 'resolver' } } };
  const mid = recorder();
  drawLyrics(mid, 1.5, lines, opts);                               // 'One' and 'resolver,' voiced, 'misconfigured' not yet
  assert.deepEqual(mid.calls.map(c => c.text), ['One', 'resolver,']);
  assert.ok(!mid.calls.some(c => /[\u4e00-\u9fff]/u.test(c.text)), 'no Chinese translation line');
  assert.equal(mid.calls[0].x, 76);
  assert.equal(mid.calls[1].color, '#E3342F');
  const full = recorder();
  drawLyrics(full, 2.3, lines, opts);
  assert.deepEqual(full.calls.map(c => c.text), ['One', 'resolver,', 'misconfigured']);
  // 'misconfigured' (13 chars x 48 px) does not fit after 'One resolver,' in 700 px: it wraps to a second row at x
  const last = full.calls[2];
  assert.equal(last.x, 76);
  assert.ok(Math.abs(last.y - 968) < 1e-6, 'the last row sits on the bottom baseline');
  assert.ok(Math.abs(full.calls[0].y - (968 - 96 * HEADLINE.lead)) < 1e-6, 'one tight row step above');
});

test('headline layout covers sung lines too and keeps the layout fixed while words build up', () => {
  const measure = s => s.length * 30;
  const a = headlineLayout(lyricState(2.7, lines), measure, { maxWidth: 2000 });
  const b = headlineLayout(lyricState(3.9, lines), measure, { maxWidth: 2000 });
  assert.equal(lyricState(2.7, lines).mode, 'sung');
  assert.deepEqual(a.words.map(w => [w.text, w.x]), b.words.map(w => [w.text, w.x]));
  assert.equal(a.rows, 1);
  assert.ok(a.words.every(w => w.x >= HEADLINE.x));
});

test('the default style is unchanged: the translation line is still drawn', () => {
  const ctx = recorder();
  drawLyrics(ctx, 2.0, lines);
  assert.ok(ctx.calls.some(c => c.text === '一个解析器 配置错误'));
});
