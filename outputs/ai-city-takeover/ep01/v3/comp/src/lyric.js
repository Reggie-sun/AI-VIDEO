// English lyric layer for the animatic, styled per unit by its lyric_* graphic and the a2 type roles (spec a2 版式按角色
// 分工; escape_velocity_analysis/visual_system.json typography_summary): words and times only from the CTC timing, and
// only the unit's own words (spec: 单元内按 [t0, t1) 取): build.py puts them in units.json `lyr` (unit_lyric: the words
// sounding inside the unit, by midpoint or at least 0.1 s of the word), grouped per CTC line. motion-kit lyrics.js
// lyricState runs over those groups: a group shows from 0.06 s before its first word, each word lights within a frame of
// its onset; a spelled-out acronym (D N S) shows as one word (spelled()). A unit with no lyric_* graphic draws no lyric.
// No translation line is ever drawn (the groups carry an empty zh). Roles:
//   headline (lyric_word on a unit with a still: the voice-over over a picture): the author's sentence coverline, MK
//     Grotesk Bold (Nimbus Sans Bold) 88 px (caps 63 px), sentence case, left at x 76, the whole group on one row, its
//     words shown faint and lit on their onsets, the line's key word in signal red
//   word (lyric_word on a full-screen graphic: flap boards, node graphs, the timing chart): the small deadpan subtitle,
//     bottom left, so it does not repeat the graphic
//   stack (lyric_stack, the sung lines): v2 c15's coverline (Nimbus Sans Bold 72 px, x 76, bottom 968, lead 0.98, rows
//     wrap at 600 px, words build up as voiced, key word red); a key word sung as a long note (>= 0.8 s) leaves the
//     stack and stands on its own row in the tall narrow bold (MK Narrow Bold 190 px, caps), slammed on its onset and
//     widening while the note holds
//   chant (lyric_chant, the drop): the word being chanted in MK Narrow Bold caps, 260 px, slammed on its onset and
//     kicked on every beat
//   whisper / tiny (lyric_whisper, lyric_tiny: whisper, bridge): kept very small
//   flip (lyric_flip_words): flap tiles, one word per row
// On a system unit the block moves inside the OSD frame; on a light ground (the white lab) the ink is dark and no dark
// scrim is laid behind it; in the red-team room no word is red.
import { drawFlap, flapText } from '../../../../../../motion-kit/src/flap.js';
import { font, slam } from '../../../../../../motion-kit/src/draw2d.js';
import { clamp, easeOutCubic } from '../../../../../../motion-kit/src/math.js';
import { drawLyrics, headlineLayout, lyricState, stripTrailing } from '../../../../../../motion-kit/src/lyrics.js';
import { F, GROTESK, NARROW, OSD_IN, RED, placed, scrim } from './util.js';

// one key word per line in signal red (the single accent; v2 c11's rule); line indices are words.json's (a2's words.json
// re-timed lines 43/44 only, same 47 lines and texts)
const KEYS = { 1: 'woke', 4: 'misconfigured', 5: 'open', 6: 'internet', 7: 'limited', 9: 'inside', 12: 'outside', 14: 'outside',
  16: 'paused', 19: 'offline', 20: 'Cached', 24: 'whispering', 25: 'patched', 29: 'outside', 31: 'outside', 33: 'outside',
  35: 'outside', 37: 'outside', 41: 'outside', 43: 'outside', 44: 'back', 45: 'closed' };
const HEAD = { size: 72, lead: 0.98, maxWidth: 600 };                                   // v2 c15
const COVER = { size: 88, lead: 1.05, maxWidth: 1700, tracking: -1 };                    // the voice-over headline
const SMALL = { word: { size: 40, family: GROTESK, maxWidth: 1100, tracking: 0 },
  whisper: { size: 30, family: 'MK Display Italic', maxWidth: 900, tracking: 0.5 },
  tiny: { size: 26, family: 'MK Display', maxWidth: 820, tracking: 1 } };
const STYLE = { lyric_word: 'word', lyric_stack: 'stack', lyric_whisper: 'whisper', lyric_tiny: 'tiny', lyric_chant: 'chant',
  lyric_flip_words: 'flip' };
const LONG = 0.8;                                                                        // s: a long note
export const LYRIC_STYLES = Object.keys(STYLE);
// the block's left edge and bottom baseline: inside the OSD frame on a system unit, else the author's x 76
const origin = u => (u.view === 'system' ? { x: OSD_IN + 44, bottom: 948 } : { x: 76, bottom: 968 });
export const roleOf = u => {
  const s = STYLE[u.lyric];
  return s === 'word' && u.view !== 'graphic' && u.plates.length ? 'headline' : s;
};

// a spelled-out acronym shows as one word (a2.1: the CTC splits DNS into D / N / S, which read "One D N S resolver"): a
// run of two or more single capital-letter tokens becomes one word, lit from the first letter's start to the last
// letter's end, keeping the last letter's trailing punctuation. A lone letter (I, A) stays as it is.
const LETTER = /^[A-Z][^\w\s]*$/u;
function spelled(words) {
  const out = [];
  for (let i = 0; i < words.length;) {
    let j = i;
    while (j < words.length && LETTER.test(words[j].text)) j += 1;
    if (j - i >= 2) {
      const run = words.slice(i, j), tail = run[run.length - 1].text.slice(1);
      out.push({ ...run[0], text: run.map(w => w.text[0]).join('') + tail, end: run[run.length - 1].end });
      i = j;
    } else { out.push(words[i]); i += 1; }
  }
  return out;
}
// the unit's word groups as lyric lines (lyricState reads L.zh: give it an empty one), and its key words by group
const SEGS = {};
function segsOf(u) {
  if (!SEGS[u.id]) {
    const lines = (u.lyr || []).map(s => ({ ...s, words: spelled(s.words), zh: '' }));
    const keys = Object.fromEntries(lines.map((s, n) => [n, KEYS[s.line]]).filter(([, w]) => w));
    SEGS[u.id] = { lines, accent: u.nored ? null : { color: RED, keys } };     // the red-team room has no red
  }
  return SEGS[u.id];
}
const inkOf = light => w => (w.accent ? RED : light ? '#0b0f14' : '#eef1f6');

// fixed-layout text whose words light on their onsets: unlit words faint (lyricState's level), never reflowed
function lit(k, ctx, st, o, light) {
  ctx.save();
  font(ctx, o.family, o.size, o.tracking);
  const lay = headlineLayout(st, s => ctx.measureText(s).width, { x: o.x, bottom: o.bottom, size: o.size, lead: o.lead ?? 1.12, maxWidth: o.maxWidth });
  if (!light) { ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = o.size > 60 ? 14 : 8; }
  ctx.textAlign = 'left';
  const ink = inkOf(light);
  for (const w of lay.words) {
    const a = st.alpha * st.words[w.k].level;
    if (a <= 0) continue;
    ctx.globalAlpha = a; ctx.fillStyle = ink(st.words[w.k]);
    ctx.fillText(w.text, w.x, w.y);
  }
  ctx.restore();
  const [x, y, w, h] = lay.box;
  if (!light) scrim(k.layers.feed.ctx, x - 30, y - 20, w + 60, h + 36, (o.size > 60 ? 0.42 : 0.34) * st.alpha);
}

// the word being sung (or the last one sung) of the active group, with its onset
function current(L, st) {
  let j = -1;
  st.words.forEach((w, i) => { if (w.on > 0) j = i; });
  if (j < 0) return null;
  return { text: stripTrailing(L.words[j].text).replace(/^[\s"'“‘(]+/u, ''), t0: L.words[j].start, accent: st.words[j].accent };
}

function chant(k, ctx, L, st, t, u) {
  const c = current(L, st);
  if (!c) return;
  const size = 260, { x } = origin(u), y = origin(u).bottom - 30, word = c.text.toUpperCase();
  const kick = 1 + 0.035 * k.clock.pulse('kick', t + 1 / 30, 0.12);                   // the beat: a small kick in scale
  ctx.save();
  font(ctx, NARROW, size, 2);
  const w = ctx.measureText(word).width;
  ctx.restore();
  slam(ctx, placed(x, y, cx => {
    cx.translate(w / 2, -size * 0.36); cx.scale(kick, kick); cx.translate(-w / 2, size * 0.36);
    font(cx, NARROW, size, 2); cx.textAlign = 'left'; cx.globalAlpha *= st.alpha;
    cx.shadowColor = 'rgba(0,0,0,0.5)'; cx.shadowBlur = 18; cx.fillStyle = c.accent ? RED : '#f2f4f7';
    cx.fillText(word, 0, 0);
  }), { t, t0: c.t0, ax: x, ay: y - size * 0.36, s0: 1.12, dur: 2 / 30, ghosts: 0 });
  scrim(k.layers.feed.ctx, x - 30, y - size * 0.8, w + 60, size * 0.95, 0.3 * st.alpha);
}

function flip(k, ctx, L, st, t, u) {
  const n = st.words.length, size = 66, lead = 1.32, { x: X, bottom: BOTTOM } = origin(u);
  st.words.forEach((w, i) => {
    const word = w.text.toUpperCase().replace(/[^A-Z0-9' ]/g, '');
    const y = BOTTOM - (n - 1 - i) * size * lead, ws = L.words[i].start;
    if (t < ws) {                                                          // empty tiles wait for the word
      ctx.save(); ctx.globalAlpha = st.alpha * 0.5; ctx.fillStyle = 'rgba(8,12,17,0.72)';
      font(ctx, F.monoB, size, 0);
      const cw = ctx.measureText('0').width + 10;
      for (let c = 0; c < word.length; c++) ctx.fillRect(X + c * (cw + 5), y - size * 0.86, cw, size * 1.02);
      ctx.restore();
      return;
    }
    drawFlap(ctx, flapText(word, t, ws, { settle: 3, stagger: 1, seed: 63 + i }), X, y,
      { size, alpha: st.alpha, color: w.accent ? RED : '#f2f4f7', tile: 'rgba(8,12,17,0.72)', gap: 5, padX: 5 });
  });
}

// the c15 stack; a long-note key word at the end of the line stands on its own row in the narrow bold
function stack(k, ctx, lines, accent, t, u, light) {
  const { x, bottom } = origin(u), st = lyricState(t, lines, s => s, accent);
  if (!st || st.alpha <= 0) return;
  const L = lines[st.index], last = st.words.length - 1, kw = L.words[last];
  const long = last >= 1 && st.words[last].accent && kw.end - kw.start >= LONG;
  if (!long) {
    const res = drawLyrics(ctx, t, lines, { accent, headline: { ...HEAD, x, bottom } });
    if (res?.layout && !light) { const [bx, by, bw, bh] = res.layout.box; scrim(k.layers.feed.ctx, bx - 40, by - 30, bw + 80, bh + 50, 0.42 * res.alpha); }
    return;
  }
  const size = 190, gapY = 30, rowsBottom = bottom - size * 0.718 - gapY;
  // the other words: the c15 stack, bottom-anchored above the narrow row
  const head = { ...st, words: st.words.slice(0, last) };
  ctx.save();
  font(ctx, GROTESK, HEAD.size, -1);
  const lay = headlineLayout(head, s => ctx.measureText(s).width, { x, bottom: rowsBottom, size: HEAD.size, lead: HEAD.lead, maxWidth: HEAD.maxWidth });
  ctx.textAlign = 'left';
  if (!light) { ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 14; }
  const ink = inkOf(light);
  for (const w of lay.words) {
    const a = st.alpha * st.words[w.k].on;
    if (a <= 0) continue;
    ctx.globalAlpha = a; ctx.fillStyle = ink(st.words[w.k]); ctx.fillText(w.text, w.x, w.y);
  }
  ctx.restore();
  // the key word: slammed on its onset, widening a little while the note holds
  const word = stripTrailing(kw.text).toUpperCase(), grow = 1 + 0.06 * easeOutCubic(clamp((t - kw.start) / (kw.end - kw.start)));
  if (t >= kw.start) {
    slam(ctx, placed(x, bottom, cx => {
      font(cx, NARROW, size, 2); cx.textAlign = 'left'; cx.globalAlpha *= st.alpha;
      cx.scale(grow, 1);
      if (!light) { cx.shadowColor = 'rgba(0,0,0,0.5)'; cx.shadowBlur = 18; }
      cx.fillStyle = RED; cx.fillText(word, 0, 0);
    }), { t, t0: kw.start, ax: x, ay: bottom - size * 0.36, s0: 1.1, dur: 2 / 30, ghosts: 0 });
  }
  if (!light) {
    ctx.save(); font(ctx, NARROW, size, 2); const ww = ctx.measureText(word).width * grow; ctx.restore();
    const top = Math.min(lay.box[1], bottom - size * 0.8);
    scrim(k.layers.feed.ctx, x - 40, top - 30, Math.max(lay.box[2], ww) + 80, bottom - top + 60, 0.42 * st.alpha);
  }
}

// draw the lyric of time t for unit u (the unit containing t). light: the ground under the type is light. Returns the
// role used or null.
export function drawLyric(k, t, u, { light = false } = {}) {
  const role = roleOf(u);
  if (!role) return null;
  const o = k.layers.overlay.ctx, { lines, accent } = segsOf(u);
  if (!lines.length) return role;
  if (role === 'stack') { stack(k, o, lines, accent, t, u, light); return role; }
  const st = lyricState(t, lines, s => s, accent);
  if (!st || st.alpha <= 0) return role;
  if (role === 'chant') chant(k, o, lines[st.index], st, t, u);
  else if (role === 'flip') flip(k, o, lines[st.index], st, t, u);
  else if (role === 'headline') lit(k, o, st, { family: GROTESK, ...COVER, ...origin(u) }, light);
  else lit(k, o, st, { ...SMALL[role], ...origin(u) }, light);
  return role;
}
