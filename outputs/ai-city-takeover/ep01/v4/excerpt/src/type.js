// Type for the excerpt: the author's pairing (board type system): DINish Condensed Black for the mass words and mastheads,
// Nimbus Sans Bold for her lines, IBM Plex Mono for readouts, sources and micro-type. Every word a lyric shows is
// registered with k.mark(line, word) when it is drawn, so qa.py can count words on screen frame by frame.
import { clamp, easeOutCubic } from '../../../../../../motion-kit/src/math.js';

export const FONT = { din: 'XDIN', dinB: 'XDINB', nim: 'XNIM', nimR: 'XNIMR', mono: 'XMONO', monoR: 'XMONOR', monoS: 'XMONOS' };
export const INK = { warm: '#F3EEE4', paper: '#ECE8DE', dark: '#17191C', amber: '#F2B134', bone: '#E8E4DA', signal: '#D7263D' };

export function setFont(ctx, fam, size, track = 0) {
  ctx.font = `${size}px "${fam}"`;
  ctx.letterSpacing = `${track}px`;
}
export function textW(ctx, fam, size, track, text) {
  setFont(ctx, fam, size, track);
  return ctx.measureText(text).width;
}

// frames since a song time showed (-1 before it); a time shows on its nearest frame
export const since = (k, ts) => k.f - k.fo(ts);
export const shown = (k, ts) => k.f >= k.fo(ts);

// Lay out a run of words (each {text, start, li, wi}) on one baseline; returns their x positions and the total width.
export function layoutWords(ctx, words, fam, size, track, space) {
  setFont(ctx, fam, size, track);
  const xs = [];
  let x = 0;
  for (const w of words) {
    xs.push(x);
    x += ctx.measureText(w.text).width + space;
  }
  return { xs, w: x - space };
}

// Draw the words of a run that have been sung (on their onset frame), each registered. opts.pop: a 2-frame lift-in.
export function drawWords(k, ctx, words, x, y, fam, size, { track = 0, space = size * 0.28, color = INK.warm,
  shadow = null, align = 'left', pop = true, upper = false, dim = null } = {}) {
  const ws = upper ? words.map(w => ({ ...w, text: w.text.toUpperCase() })) : words;
  const L = layoutWords(ctx, ws, fam, size, track, space);
  const x0 = align === 'center' ? x - L.w / 2 : align === 'right' ? x - L.w : x;
  ctx.save();
  setFont(ctx, fam, size, track);
  if (shadow) { ctx.shadowColor = shadow.color; ctx.shadowBlur = shadow.blur; ctx.shadowOffsetY = shadow.dy || 0; }
  ws.forEach((w, i) => {
    const a = since(k, w.start);
    if (a < 0) {
      if (dim) { ctx.globalAlpha = dim; ctx.fillStyle = color; ctx.fillText(w.text, x0 + L.xs[i], y); }
      return;
    }
    const e = pop ? easeOutCubic(clamp((a + 1) / 3)) : 1;
    ctx.globalAlpha = pop ? clamp(0.55 + 0.45 * e) : 1;
    ctx.fillStyle = color;
    ctx.fillText(w.text, x0 + L.xs[i], y + (1 - e) * size * 0.08);
    k.mark(w.li, w.wi);
  });
  ctx.restore();
  return { x0, w: L.w, xs: L.xs.map(v => v + x0) };
}

// One giant word slammed on its accent: from 1.16x to 1x in 3 frames, one faint ghost on the first two frames, a soft
// drop shadow that presses it into the picture. (x, y) = left baseline unless align says otherwise.
export function slamWord(k, ctx, text, ts, x, y, size, { color = INK.warm, align = 'left', track = -1, shadowA = 0.5,
  fam = FONT.din, marks = [] } = {}) {
  const a = since(k, ts);
  if (a < 0) return null;
  setFont(ctx, fam, size, track);
  const w = ctx.measureText(text).width;
  const x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  const s = a >= 3 ? 1 : [1.16, 1.06, 1.015][a];
  const cx = x0 + w / 2, cy = y - size * 0.35;
  ctx.save();
  if (a < 2) {
    ctx.save();
    ctx.globalAlpha = 0.18;
    ctx.translate(cx, cy); ctx.scale(s * 1.07, s * 1.07); ctx.translate(-cx, -cy);
    ctx.fillStyle = color; ctx.fillText(text, x0, y);
    ctx.restore();
  }
  ctx.translate(cx, cy); ctx.scale(s, s); ctx.translate(-cx, -cy);
  ctx.shadowColor = `rgba(0,0,0,${shadowA})`; ctx.shadowBlur = size * 0.11; ctx.shadowOffsetY = size * 0.035;
  ctx.fillStyle = color;
  ctx.fillText(text, x0, y);
  ctx.restore();
  for (const [li, wi] of marks) k.mark(li, wi);
  return { x0, w };
}

// a one-line micro readout (IBM Plex Mono caps, tracked)
export function micro(ctx, text, x, y, { size = 12, track = 2.2, color = 'rgba(236,232,222,0.78)', align = 'left',
  fam = FONT.mono } = {}) {
  ctx.save();
  setFont(ctx, fam, size, track);
  ctx.textAlign = align;
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
  ctx.restore();
}

// type a string out on ticks (12 per second): n characters visible after `a` frames
export function typed(text, a, perTick = 2) {
  if (a < 0) return '';
  return text.slice(0, Math.min(text.length, (Math.floor(a / 2) + 1) * perTick));
}
