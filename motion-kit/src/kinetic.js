// Big condensed kinetic words and section-boundary strip masks (the EV toolkit's condensed display type and its
// strip/bar wipes). The fonts carry no condensed face, so a word is drawn horizontally squeezed. Pure functions of t.
import { F, font } from './draw2d.js';
import { clamp, easeInCubic, easeOutCubic, easeOutExpo, hash2 } from './math.js';

// Visibility of a kinetic word at t: lands at t0 (scale s0 -> 1 in `land` s), holds, then leaves by a slice wipe that
// starts at t1 and lasts `out` s. Returns null when not on screen, else { scale, cut } (cut = fraction wiped, 0..1).
export function kineticState(t, { t0, t1, land = 2 / 30, out = 3 / 30, s0 = 1.18 }) {
  if (t < t0 || t >= t1 + out) return null;
  const e = easeOutExpo(clamp((t - t0) / land));
  return { scale: s0 + (1 - s0) * e, cut: t < t1 ? 0 : easeInCubic(clamp((t - t1) / out)) };
}

// Draw a kinetic word. (x, y) is the baseline anchor; align 'left' | 'center' | 'right'. squeeze < 1 condenses it.
export function kineticWord(ctx, text, t, { t0, t1, x, y, size = 200, family = F.sans, color = '#f2f4f7', squeeze = 0.64,
  tracking = -2, align = 'center', land, out, s0, shadow = 'rgba(0,0,0,0.45)' }) {
  const st = kineticState(t, { t0, t1, land, out, s0 });
  if (!st) return null;
  ctx.save();
  font(ctx, family, size, tracking);
  const w = ctx.measureText(text).width * squeeze;
  const left = align === 'left' ? x : align === 'right' ? x - w : x - w / 2;
  const top = y - size * 0.86, h = size * 1.0;
  if (st.cut > 0) {                                   // leave as horizontal slices pulled out to the right
    ctx.beginPath();
    const n = 5;
    for (let i = 0; i < n; i++) {
      const d = clamp(st.cut * 1.6 - (i % 2) * 0.3 - i * 0.08);
      ctx.rect(left + w * d, top + (h * i) / n, w * (1 - d) + 2, h / n + 0.5);
    }
    ctx.clip();
  }
  ctx.translate(left + w / 2, y - size * 0.35);         // scale about the word's centre
  ctx.scale(st.scale * squeeze, st.scale);
  ctx.translate(0, size * 0.35);
  ctx.shadowColor = shadow; ctx.shadowBlur = 16;
  ctx.fillStyle = color; ctx.textAlign = 'center';
  ctx.fillText(text, 0, 0);
  ctx.restore();
  return { ...st, box: [left, top, w, h] };
}

// Strip mask for a section boundary at tCut (comp s). Before the cut, `pre` s of thin strips sweep across the outgoing
// picture (small area: the cut stays the frame's largest change); after it, `bars` horizontal bars cover the incoming
// picture and retract within `post` s, alternating directions. Returns the rects to fill: [{ x, y, w, h, red }].
export function stripRects(t, tCut, { W = 1920, H = 1080, strips = 7, stripH = 5, pre = 6 / 30, bars = 9, post = 3 / 30, seed = 3 } = {}) {
  const out = [];
  if (t >= tCut - pre && t < tCut) {
    const u = (t - (tCut - pre)) / pre;
    for (let i = 0; i < strips; i++) {
      const y = Math.round(H * (0.12 + 0.76 * hash2(i, seed)));
      const d = clamp(u * 1.4 - 0.4 * hash2(i, seed + 1));
      const len = W * 0.42 * (0.6 + 0.4 * hash2(i, seed + 2));
      const head = easeOutCubic(d) * (W + len);
      out.push({ x: head - len, y, w: len, h: stripH, red: i === 2 });
    }
  } else if (t >= tCut && t < tCut + post) {
    const u = (t - tCut) / post, bh = H / bars;
    for (let i = 0; i < bars; i++) {
      const k = clamp(u * 1.3 - (i % 3) * 0.12), w = W * (1 - easeOutCubic(k));
      if (w <= 0.5) continue;
      out.push({ x: i % 2 ? W - w : 0, y: Math.floor(i * bh), w, h: Math.ceil(bh) + 1, red: false });
    }
  }
  return out;
}
export function drawStrips(ctx, rects, { ink = 'rgba(10,16,23,0.96)', accent = '#E3342F', light = 'rgba(226,232,238,0.7)' } = {}) {
  ctx.save();
  for (const r of rects) {
    ctx.fillStyle = r.red ? accent : r.h <= 8 ? light : ink;
    ctx.fillRect(Math.round(r.x), Math.round(r.y), Math.round(r.w), Math.round(r.h));
  }
  ctx.restore();
}
