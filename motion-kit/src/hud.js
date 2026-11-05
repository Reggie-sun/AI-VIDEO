// Persistent HUD (the EV toolkit's G-TITLE-TAG, G-LOOK-COUNTER, G-AUDIO-SPECTRUM, G-TICKER, G-TIMECODE) and small tag
// cards (G-STICKER/tag). Small, mono, uppercase, low contrast: it frames the film and never competes with the lyric.
// Every function is a pure function of its arguments; time is passed in.
import { F, font } from './draw2d.js';
import { clamp, hash2 } from './math.js';

export const HUD_INK = 'rgba(226,232,238,0.62)';
export const HUD_DIM = 'rgba(226,232,238,0.34)';

// A run of small mono parts on one baseline: [{ text, color }]. align 'left' draws from x, 'right' ends at x.
// Returns [x0, x1] of the drawn run.
export function hudRun(ctx, parts, x, y, { size = 13, tracking = 2, align = 'left', gap = null, family = F.mono } = {}) {
  ctx.save();
  font(ctx, family, size, tracking);
  const g = gap ?? size * 1.1;
  const widths = parts.map(p => ctx.measureText(p.text).width);
  const total = widths.reduce((a, b) => a + b, 0) + g * (parts.length - 1);
  let cx = align === 'right' ? x - total : x;
  const x0 = cx;
  ctx.textAlign = 'left';
  parts.forEach((p, i) => {
    ctx.fillStyle = p.color || HUD_INK;
    ctx.fillText(p.text, cx, y);
    cx += widths[i] + g;
  });
  ctx.restore();
  return [x0, x0 + total];
}

// Bar levels (0..1) of a tiny audio meter at comp time t, from the clock's band envelopes (env24 low/mid/high) and the
// drum pulses. Bars run low -> high; each bar mixes the two nearest bands and gets a fixed per-bar tilt, so it moves with
// the song and nothing else.
export function meterLevels(clock, t, n = 14) {
  const bands = ['low', 'mid', 'high'].map(b => clock.env(b, t));
  const kick = clock.pulse('kick', t, 0.10), snare = clock.pulse('snare', t, 0.08), hat = clock.pulse('hat', t, 0.05);
  const out = [];
  for (let i = 0; i < n; i++) {
    const u = (i / Math.max(1, n - 1)) * 2, k = Math.min(1, Math.floor(u)), f = u - k;
    const band = bands[k] * (1 - f) + bands[k + 1] * f;
    const hit = i < n / 3 ? kick : i < (2 * n) / 3 ? snare : hat;
    const tilt = 0.75 + 0.5 * hash2(i, 97);
    out.push(clamp(band * tilt * 0.9 + 0.35 * hit * tilt));
  }
  return out;
}

// Draw the meter: n bars of width bw, right edge at x (align right) or left edge at x, bottom at y, max height h.
export function drawMeter(ctx, levels, x, y, { h = 10, bw = 3, gap = 2, align = 'right', color = HUD_INK, floor = 1 } = {}) {
  const w = levels.length * (bw + gap) - gap;
  const x0 = align === 'right' ? x - w : x;
  ctx.save();
  ctx.fillStyle = color;
  levels.forEach((v, i) => {
    const bh = Math.max(floor, Math.round(v * h));
    ctx.fillRect(Math.round(x0 + i * (bw + gap)), y - bh, bw, bh);
  });
  ctx.restore();
  return [x0, x0 + w];
}

// Film timecode HH:MM:SS:FF for comp time t, starting at `start` seconds of the day (e.g. 03:47:30 = 13650).
export function timecode(t, start = 0, fps = 30) {
  const total = Math.floor(start * fps + Math.max(0, t) * fps + 1e-6);
  const ff = total % fps, s = Math.floor(total / fps);
  const p = n => String(n).padStart(2, '0');
  return `${p(Math.floor(s / 3600) % 24)}:${p(Math.floor(s / 60) % 60)}:${p(s % 60)}:${p(ff)}`;
}

// Horizontal offset (px) of a ticker strip of width `period` at comp time t, scrolling left at `speed` px/s.
export const tickerOffset = (t, speed, period) => ((t * speed) % period + period) % period;

// A ticker: items scroll right -> left between two hairlines, clipped to [x0, x1]; y is the text baseline.
export function drawTicker(ctx, items, t, { x0, x1, y, size = 12, speed = 42, sep = '  ＊  ', color = HUD_INK,
  rule = HUD_DIM, ruleGap = 9, tracking = 1.5, family = F.mono, accent = null } = {}) {
  ctx.save();
  ctx.fillStyle = rule;
  ctx.fillRect(x0, Math.round(y - size - ruleGap) + 0.5, x1 - x0, 1);
  ctx.fillRect(x0, Math.round(y + ruleGap) - 0.5, x1 - x0, 1);
  ctx.beginPath(); ctx.rect(x0, y - size - ruleGap, x1 - x0, size + 2 * ruleGap); ctx.clip();
  font(ctx, family, size, tracking);
  const pieces = items.flatMap(s => [{ text: s, color }, { text: sep, color: accent || color }]);
  const widths = pieces.map(p => ctx.measureText(p.text).width);
  const period = widths.reduce((a, b) => a + b, 0);
  let cx = x0 - tickerOffset(t, speed, period);
  while (cx < x1) {
    pieces.forEach((p, i) => {
      if (cx + widths[i] > x0 && cx < x1) { ctx.fillStyle = p.color; ctx.fillText(p.text, cx, y); }
      cx += widths[i];
    });
  }
  ctx.restore();
  return period;
}

// A small tag card: rows of [key, value] in mono uppercase on a dark translucent card with a red tick on the left.
// (x, y) is the card's top-left; anchor 'right' puts its top-right there instead. Returns [x, y, w, h].
export function tagCard(ctx, rows, x, y, { size = 13, tracking = 1.5, alpha = 1, anchor = 'left', accent = '#E3342F',
  ink = 'rgba(236,241,244,0.9)', dim = 'rgba(236,241,244,0.55)', bg = 'rgba(7,10,14,0.66)' } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  font(ctx, F.mono, size, tracking);
  const kw = Math.max(...rows.map(r => ctx.measureText(r[0]).width));
  const vw = Math.max(...rows.map(r => ctx.measureText(r[1]).width));
  const pad = Math.round(size * 0.7), lead = Math.round(size * 1.6), dot = ctx.measureText(' · ').width;
  const w = Math.round(pad * 2 + 3 + kw + dot + vw), h = Math.round(pad * 1.2 + lead * rows.length);
  const x0 = Math.round(anchor === 'right' ? x - w : x), y0 = Math.round(y);
  ctx.fillStyle = bg; ctx.fillRect(x0, y0, w, h);
  ctx.fillStyle = accent; ctx.fillRect(x0, y0, 3, h);
  rows.forEach(([k, v], i) => {
    const by = y0 + pad * 0.6 + lead * (i + 1) - lead * 0.32;
    ctx.fillStyle = dim; ctx.fillText(k, x0 + 3 + pad, by);
    ctx.fillText(' · ', x0 + 3 + pad + kw, by);
    ctx.fillStyle = ink; ctx.fillText(v, x0 + 3 + pad + kw + dot, by);
  });
  ctx.restore();
  return [x0, y0, w, h];
}
