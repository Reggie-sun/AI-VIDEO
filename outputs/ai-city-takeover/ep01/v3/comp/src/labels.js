// Labels, tags, stamps, titles and the fact card. Text only from graphic_text (INTERNAL RESEARCH MODEL, OCT 01,
// OFFLINE, INDEXED · CACHED, SEPARATE · CONTROLLED RED-TEAM TEST, PATCHED, OUTSIDE, the U084 card lines) or the
// component name's argument when graphic_text is empty; each word appears on its token's time (u.toks: the CTC onset,
// else with the word before it, else the unit cue). The red-team room's labels use no red (accent()).
import { font, slam } from '../../../../../../motion-kit/src/draw2d.js';
import { clamp, easeOutCubic } from '../../../../../../motion-kit/src/math.js';
import { ANCHORS } from './anchors.js';
import { DARK_INK, F, GROTESK, H, OSD_IN, RED, W, accent, beatAfter, grow, line, measure, placed, point, text, tokAt,
  tokenLine } from './util.js';

const STAMP_DARK = '#2B4257';                                            // a stamp on the white room: dark steel, not red
// a small tag: dark translucent card, an accent tick on the left, mono caps; (x, y) is the card's top-left
export function tag(ctx, s, x, y, { size = 22, alpha = 1, tick = RED } = {}) {
  if (alpha <= 0) return;
  const pad = Math.round(size * 0.6), w = measure(ctx, s, size, F.mono, 3) + 2 * pad + 6, h = Math.round(size * 1.9);
  ctx.save(); ctx.globalAlpha *= alpha;
  ctx.fillStyle = 'rgba(7,10,14,0.72)'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = tick; ctx.fillRect(x, y, 4, h);
  ctx.restore();
  text(ctx, s, x + 6 + pad, y + h * 0.68, { size, tracking: 3, alpha, shadow: null });
}
// a rubber stamp, slammed in at t0
export function stamp(ctx, s, x, y, t, t0, { size = 92, rot = -0.12, color = RED } = {}) {
  if (t < t0) return;
  slam(ctx, placed(x, y, c => {
    c.rotate(rot);
    font(c, F.monoB, size, size * 0.12);
    const w = c.measureText(s).width + size * 0.7, h = size * 1.35;
    c.strokeStyle = color; c.lineWidth = Math.max(4, size * 0.07); c.strokeRect(-w / 2, -h / 2, w, h);
    c.lineWidth = 2; c.strokeRect(-w / 2 + 10, -h / 2 + 10, w - 20, h - 20);
    c.fillStyle = color; c.textAlign = 'center'; c.fillText(s, 0, size * 0.36);
  }), { t, t0, ax: x, ay: y, s0: 1.4, dur: 2 / 30, ghosts: 2 });
}
// a screen point for a label: the plate anchor `name` (or the unit's target) through the camera, else a fallback
const at = (k, u, cm, name, fb) => { const p = point(k, u, cm.key, name); return p ? cm.out(p) : fb; };
// greedy word wrap into rows of at most n characters, split at spaces (a longer word stands alone)
function wrapWords(s, n) {
  const rows = [];
  for (const w of String(s).split(' ')) {
    if (rows.length && rows[rows.length - 1].length + 1 + w.length <= n) rows[rows.length - 1] += ` ${w}`;
    else rows.push(w);
  }
  return rows;
}

export const LABELS = {
  // the author's look label (a narrative overlay, not OSD): a red tick and the words, beside her, word by word
  look_label(k, t, u, arg, cm) {
    const o = k.layers.overlay.ctx, s = u.text || arg.replace(/_/g, ' ').toUpperCase(), t0 = tokAt(u, 0);
    if (t < t0) return {};
    const [x, y] = at(k, u, cm, 'side', [W * 0.62, H * 0.42]), a = grow(t, t0, 0.14), dx = 24 * (1 - easeOutCubic(clamp((t - t0) / 0.2)));
    line(o, [x - 18 + dx, y - 34], [x - 18 + dx, y + 12], { color: accent(u), width: 4, alpha: a });
    tokenLine(o, s, u.toks, 0, t, x + dx, y, { size: 34, tracking: 4, shadow: 'rgba(0,0,0,0.65)' });
    return {};
  },
  // tag_offline and the like: the word on its token, near the subject (the plate's tag anchor, else beside the target)
  tag(k, t, u, arg, cm) {
    const s = u.text || arg.toUpperCase(), t0 = tokAt(u, u.toks.findIndex(x => x.text.toUpperCase() === s.toUpperCase()));
    let p = ANCHORS[cm.key]?.tag ? cm.out(ANCHORS[cm.key].tag) : null;
    if (!p) { const q = point(k, u, cm.key, 'her'); p = q ? [cm.out(q)[0] + 60, cm.out(q)[1] - 120] : [W * 0.62, H * 0.3]; }
    tag(k.layers.overlay.ctx, s, Math.min(p[0], W - 330), Math.max(120, p[1]), { size: 26, alpha: grow(t, t0, 0.1), tick: accent(u) });
    return {};
  },
  date_tag(k, t, u, arg, cm) {                                     // date_tag_OCT_01: on the month's word
    const s = u.text || arg.replace(/_/g, ' '), [x, y] = at(k, u, cm, 'tag', [1180, 300]);
    tag(k.layers.overlay.ctx, s, x, y, { size: 26, alpha: grow(t, tokAt(u, 0), 0.1), tick: accent(u) });
    return {};
  },
  // small tags on the floating sheets: the words of graphic_text in turn, each sheet's tag on its word
  tag_cached_timestamps(k, t, u, cm) {
    const sheets = ANCHORS[cm.key]?.sheets || [[W * 0.3, H * 0.25], [W * 0.62, H * 0.2]].map(p => p);
    const words = u.toks.length ? u.toks : [{ text: 'CACHED', at: u.cue }];
    sheets.forEach((p, i) => {
      const w = words[i % words.length], q = ANCHORS[cm.key]?.sheets ? cm.out(p) : p;
      // kept clear of the chrome's top row and the frame edges
      const x = clamp(q[0], 84, W - 240), y = clamp(q[1], 96, H - 140);
      tag(k.layers.overlay.ctx, w.text, x, y, { size: 17, alpha: grow(t, w.at + Math.floor(i / words.length) * 2 / 30, 0.1), tick: accent(u) });
    });
    return {};
  },
  stamp(k, t, u, arg, cm) {                                        // stamp_patched: slams on its word, mid-frame
    const s = u.text || arg.toUpperCase(), t0 = tokAt(u, 0);
    stamp(k.layers.overlay.ctx, s, W / 2, 300, t, t0, { size: 84, color: u.nored ? STAMP_DARK : accent(u) });
    return {};
  },
  // the red-team test's label on the white room (in the feed, like the OSD): word by word on the voiced words, dark ink,
  // mono bold 52 px (caps 38 px: a2 asks >= 28 px so it reads at a glance as a separate controlled test), never red
  label_redteam(k, t, u) {
    const f = k.layers.feed.ctx, t0 = tokAt(u, 0), size = 52, y = 300;
    if (t < t0) return {};
    const a = grow(t, t0, 0.1);
    f.save(); f.globalAlpha = a; f.fillStyle = u.nored ? STAMP_DARK : RED; f.fillRect(OSD_IN + 30, y - size * 0.86, 7, size * 1.02); f.restore();
    tokenLine(f, u.text, u.toks, 0, t, OSD_IN + 56, y, { size, family: F.monoB, color: DARK_INK, tracking: 2, shadow: null });
    return {};
  },
  // invert_flash_OUTSIDE: black, the word white; on the cue two frames inverted (white ground, black word)
  invert_flash(k, t, u, arg) {
    const o = k.layers.overlay.ctx, word = u.text || arg;
    if (t < u.cue) return { plateGain: 0 };
    font(o, GROTESK, 260, 6); o.textAlign = 'center'; o.fillStyle = '#f2f4f7'; o.fillText(word, W / 2, 630);
    return t < u.cue + 2 / 30 ? { plateGain: 0, grade: { uInvert: 1 } } : { plateGain: 0 };   // two frames: no single-frame pop
  },
  // invert_white_panel_words: the whole picture turns white, the words black (graphic_text), slammed on the cue
  white_panel(k, t, u) {
    const o = k.layers.overlay.ctx, words = (u.text || '').split(/\s+/).filter(Boolean), size = 230;
    o.save(); o.fillStyle = '#eef0f2'; o.fillRect(0, 0, W, H); o.restore();
    words.forEach((w, i) => {
      const t0 = tokAt(u, i), y = 600 + (i - (words.length - 1) / 2) * size * 0.95;
      if (t < t0) return;
      slam(o, placed(W / 2, y, c => {
        font(c, GROTESK, size, -4); c.textAlign = 'center'; c.fillStyle = '#0b0f14'; c.fillText(w, 0, 0);
      }), { t, t0, ax: W / 2, ay: y - size * 0.35, s0: 1.1, dur: 2 / 30, ghosts: 0 });
    });
    return {};
  },
  // label_card (U083): the fact card. graphic_text's lines in order, one per beat from just after the cut (not the unit
  // cue: U083's first hit is 3.8 s in); a fact line wraps at word gaps into rows of at most 62 characters (mono 30 px,
  // caps 22 px), the SOURCES line smaller and dim. All four are up about 1.6 s after the cut and the card holds them to
  // the end of the unit (a2 修正: four lines, then held, at least 2 s all readable). Exactly the card's words.
  label_card(k, t, u) {
    const o = k.layers.overlay.ctx, pad = 84, lead = 44, gap = 28;
    const blocks = u.lines.map(s => {
      const src = /^SOURCES\b/.test(s), size = src ? 22 : 30;
      return { src, size, rows: wrapWords(s, 62), w: 0 };
    });
    for (const b of blocks) b.w = Math.max(...b.rows.map(r => measure(o, r, b.size, F.mono, 1)));
    const w = Math.max(...blocks.map(b => b.w)) + 2 * pad;
    const h = 64 + blocks.reduce((s, b) => s + b.rows.length * (b.src ? lead * 0.8 : lead), 0) + gap * (blocks.length - 1) + 40;
    const x = Math.round((W - w) / 2), y = Math.round((H - h) / 2) - 10, a = grow(t, k.t0, 0.25);
    o.save(); o.globalAlpha = a;
    o.fillStyle = '#eceef0'; o.fillRect(x, y, w, h);
    o.strokeStyle = 'rgba(11,15,20,0.45)'; o.lineWidth = 1.5; o.setLineDash([7, 6]); o.strokeRect(x + 16, y + 16, w - 32, h - 32);
    o.setLineDash([]); o.fillStyle = accent(u); o.fillRect(x + 60, y, 120, 6);
    o.restore();
    let yy = y + 64 + 22;
    blocks.forEach((b, i) => {
      const ti = beatAfter(k, k.t0 + 0.2, i), al = grow(t, ti, 0.12) * a, step = b.src ? lead * 0.8 : lead;
      b.rows.forEach((r, j) => {
        if (t >= ti) text(o, r, x + pad, yy + j * step, { size: b.size, family: F.mono, color: b.src ? 'rgba(11,15,20,0.62)' : '#0b0f14',
          tracking: 1, alpha: al, shadow: null });
      });
      yy += b.rows.length * step + gap;
    });
    return {};
  },
};
