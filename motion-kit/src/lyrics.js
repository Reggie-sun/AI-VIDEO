// Lyric layer: the English line with word-by-word lighting and its Simplified Chinese translation
// underneath. Lines come from a timed word list (song seconds) such as ep01/v2/timing/words.json;
// `toComp` maps song time to comp time (the Clock's song offset). Pure function of comp time t.
import { clamp, easeOutCubic } from './math.js';
import { font, F } from './draw2d.js';

export const LYRIC_FAMILIES = Object.freeze({
  spoken: 'MK Display', whisper: 'MK Display Italic', sung: 'MK Serif Display Italic',
});

const STYLE = {
  spoken: { family: LYRIC_FAMILIES.spoken, size: 60, tracking: 0.5, zh: 44, base: 0.30, lit: 1.0, after: 0.9 },
  whisper: { family: LYRIC_FAMILIES.whisper, size: 54, tracking: 1.0, zh: 42, base: 0.22, lit: 0.82, after: 0.7 },
  sung: { family: LYRIC_FAMILIES.sung, size: 88, tracking: 0, zh: 46, base: 0.28, lit: 1.0, after: 0.92 },
};
const LEAD = 0.06;     // a line appears this long before its first word
const HOLD = 0.45;     // and stays this long after its last word unless the next line arrives
const FADE_IN = 0.10, FADE_OUT = 0.14, RISE = 8;
const LIGHT = 1 / 30;  // a word lights within one frame of its onset

// Subtitle rule: no punctuation at the end of a displayed line.
export const stripTrailing = s => s.replace(/[\s.,;:!?…—–-]+$/u, '');

// Accent: one key word per line in the accent colour (the EV toolkit's single accent). keys maps a line index to its
// key word, matched without case and trailing punctuation: { color: '#E3342F', keys: { 1: 'woke', 15: 'closed' } }.
const norm = s => stripTrailing(String(s)).replace(/^[\s"'“‘(]+/u, '').toLowerCase();
export function accentIndex(line, key) {
  if (key === undefined || key === null) return -1;
  return line.words.findIndex(w => norm(w.text) === norm(key));
}

// Which line is on screen at t, how visible it is, and how lit each word is. No drawing.
export function lyricState(t, lines, toComp = s => s, accent = null) {
  for (let i = 0; i < lines.length; i++) {
    const L = lines[i];
    const t0 = toComp(L.start) - LEAD;
    const next = i + 1 < lines.length ? toComp(lines[i + 1].start) - LEAD : Infinity;
    const t1 = Math.min(next, toComp(L.end) + HOLD);
    if (t < t0 || t >= t1) continue;
    const style = STYLE[L.mode] || STYLE.spoken;
    const alpha = clamp((t - t0) / FADE_IN, 0, 1) * clamp((t1 - t) / FADE_OUT, 0, 1);
    const last = L.words.length - 1;
    const key = accent ? accentIndex(L, accent.keys?.[i]) : -1;
    const words = L.words.map((w, k) => {
      const ws = toComp(w.start), we = toComp(w.end);
      const on = clamp((t - ws) / LIGHT + 1e-9, 0, 1);
      const level = t < we ? style.base + (style.lit - style.base) * on : style.after;
      return { text: k === last ? stripTrailing(w.text) : w.text, level, on, singing: t >= ws && t < we, accent: k === key };
    });
    return { index: i, mode: L.mode in STYLE ? L.mode : 'spoken', alpha, rise: (1 - easeOutCubic(clamp((t - t0) / FADE_IN, 0, 1))) * RISE,
             words, zh: stripTrailing(L.zh) };
  }
  return null;
}

// Draw the visible line into a 2D context. Spoken and whispered lines sit left in the lower title-safe
// area; sung lines are centred and larger. Returns the state for QA.
// accent: see lyricState; null (default) draws every word in the lyric ink as before.
// headline: opt-in coverline style (see drawHeadline); null (default) keeps the layout above for every film.
export function drawLyrics(ctx, t, lines, { toComp = s => s, W = 1920, x = 120, baseline = 952, sungBaseline = 918, stack = null, accent = null,
  headline = null } = {}) {
  const st = lyricState(t, lines, toComp, accent);
  if (!st || st.alpha <= 0) return st;
  const s = STYLE[st.mode];
  const sung = st.mode === 'sung';
  const ink = w => (w.accent ? accent.color : '#eef1f6');
  if (headline) return drawHeadline(ctx, st, headline, ink);
  if (sung && stack) return drawStack(ctx, st, s, stack, ink);
  const y = (sung ? sungBaseline : baseline) + st.rise;
  font(ctx, s.family, s.size, s.tracking);
  const space = ctx.measureText(' ').width;
  const widths = st.words.map(w => ctx.measureText(w.text).width);
  const total = widths.reduce((a, b) => a + b, 0) + space * (widths.length - 1);
  let cx = sung ? (W - total) / 2 : x;
  ctx.save();
  ctx.textAlign = 'left';
  st.words.forEach((w, k) => {
    ctx.globalAlpha = st.alpha * w.level;
    ctx.shadowColor = 'rgba(0,0,0,0.55)';
    ctx.shadowBlur = 10;
    ctx.fillStyle = ink(w);
    ctx.fillText(w.text, cx, y);
    if (sung && w.singing) {                       // a soft halo only on the word being sung
      ctx.globalAlpha = st.alpha * 0.35;
      ctx.shadowColor = 'rgba(238,241,246,0.9)';
      ctx.shadowBlur = 18;
      ctx.fillText(w.text, cx, y);
    }
    cx += widths[k] + space;
  });
  font(ctx, F.sansR, s.zh, 1);
  ctx.globalAlpha = st.alpha * 0.82;
  ctx.shadowColor = 'rgba(0,0,0,0.6)';
  ctx.shadowBlur = 8;
  ctx.fillStyle = '#d5dae3';
  const zw = ctx.measureText(st.zh).width;
  ctx.fillText(st.zh, sung ? (W - zw) / 2 : x, y + s.zh + 24);
  ctx.restore();
  return st;
}

// The EV toolkit's "stack" lyric mode for a sung line: one word per line, large, left-aligned at (x, top) clear of the
// face, the word being sung lit and haloed, the translation under the stack. Pass drawLyrics(..., { stack: { x, top } }).
export function stackLayout(st, { x, top, size = 132, lead = 0.92, zh = 46 }) {
  const rows = st.words.map((w, k) => ({ text: w.text, x, y: top + st.rise + (k + 1) * size * lead }));
  return { rows, size, zh: { text: st.zh, x: x + 4, y: top + st.rise + st.words.length * size * lead + zh + 30, size: zh } };
}
function drawStack(ctx, st, s, opts, ink = () => '#eef1f6') {
  const lay = stackLayout(st, opts);
  ctx.save();
  ctx.textAlign = 'left';
  font(ctx, s.family, lay.size, 0);
  st.words.forEach((w, k) => {
    const { x, y } = lay.rows[k];
    ctx.globalAlpha = st.alpha * w.level;
    ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 14; ctx.fillStyle = ink(w);
    ctx.fillText(w.text, x, y);
    if (w.singing) {
      ctx.globalAlpha = st.alpha * 0.35; ctx.shadowColor = 'rgba(238,241,246,0.9)'; ctx.shadowBlur = 22;
      ctx.fillText(w.text, x, y);
    }
  });
  font(ctx, F.sansR, lay.zh.size, 1);
  ctx.globalAlpha = st.alpha * 0.82; ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 8; ctx.fillStyle = '#d5dae3';
  ctx.fillText(lay.zh.text, lay.zh.x, lay.zh.y);
  ctx.restore();
  return st;
}

// Opt-in "headline" lyric style (the EV author's lyric coverlines, escape_velocity_analysis/visual_system.json
// typography_summary.lyric_headline): a Helvetica-like bold grotesque in sentence case, left aligned, tight leading,
// large, the accent word in the accent colour, no translation line. Spoken, whispered and sung lines share it. Words
// build up as they are voiced (the author's word-by-word coverline); the layout is fixed from the whole line, so
// nothing reflows. Rows wrap at maxWidth and the block is bottom-anchored: the last row's baseline sits at `bottom`.
// Pass drawLyrics(..., { headline: { x, bottom, size, lead, maxWidth } }); measure(text) -> px width at `size`.
export const HEADLINE_FAMILY = 'MK Grotesk Bold';
export const HEADLINE = Object.freeze({ x: 76, bottom: 968, size: 96, lead: 1.05, maxWidth: 1040, tracking: -1 });
export function headlineLayout(st, measure, opts = {}) {
  const o = { ...HEADLINE, ...opts }, space = measure(' ');
  const rows = [[]];
  let end = 0;                                                     // px from x to the end of the current row
  st.words.forEach((w, k) => {
    const wd = measure(w.text);
    let r = rows[rows.length - 1];
    if (r.length && end + space + wd > o.maxWidth) { r = []; rows.push(r); end = 0; }
    const x0 = r.length ? end + space : 0;
    r.push({ k, text: w.text, x: o.x + x0, w: wd });
    end = x0 + wd;
  });
  const step = o.size * o.lead, y0 = o.bottom + st.rise - (rows.length - 1) * step;
  const words = rows.flatMap((r, i) => r.map(w => ({ ...w, row: i, y: y0 + i * step })));
  const width = Math.max(...rows.map(r => r.length ? r[r.length - 1].x + r[r.length - 1].w - o.x : 0));
  return { words, rows: rows.length, size: o.size, box: [o.x, y0 - o.size * 0.75, width, (rows.length - 1) * step + o.size * 0.95] };
}
function drawHeadline(ctx, st, opts, ink) {
  const o = { ...HEADLINE, ...opts };
  ctx.save();
  ctx.textAlign = 'left';
  font(ctx, o.family || HEADLINE_FAMILY, o.size, o.tracking);
  const lay = headlineLayout(st, s => ctx.measureText(s).width, o);
  const dim = st.mode === 'whisper' ? 0.86 : 1;
  ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 14;
  for (const w of lay.words) {
    const a = st.alpha * st.words[w.k].on * dim;
    if (a <= 0) continue;
    ctx.globalAlpha = a; ctx.fillStyle = ink(st.words[w.k]);
    ctx.fillText(w.text, w.x, w.y);
  }
  ctx.restore();
  return { ...st, layout: lay };
}
