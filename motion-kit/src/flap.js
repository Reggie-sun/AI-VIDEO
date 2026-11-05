// Split-flap board (the EV toolkit's G-FLAP-BOARD): a word resolves from random characters into its target, one
// character after another. Pure function of comp time t: the "random" characters are a hash of (position, tick, seed),
// never Math.random. Characters change only on ticks (default 15 per second = every second frame at 30 fps), so a
// flapping cell never changes on two frames in a row (qa.py's strobe scan looks for 4 alternating frame changes).
import { hash3 } from './math.js';
import { F, font } from './draw2d.js';

export const DIGITS = '0123456789';
export const ALNUM = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
const flaps = ch => /[0-9A-Za-z]/.test(ch);

// The string shown at t, or null before t0. Only letters and digits flap; separators (':', ' ', '/') hold.
//   settle: ticks the first flapping character keeps flapping; stagger: extra ticks per following flapping character
//   from: characters equal to `from` at the same position hold too (a counter flips only the digits that change)
export function flapText(target, t, t0, { rate = 15, settle = 4, stagger = 1, seed = 0, charset = null, from = null } = {}) {
  if (t < t0) return null;
  const tick = Math.floor((t - t0) * rate + 1e-6);
  let j = -1;
  return [...target].map((ch, i) => {
    if (!flaps(ch) || (from !== null && from[i] === ch)) return ch;
    j += 1;
    if (tick >= settle + j * stagger) return ch;
    const set = charset ?? (/[0-9]/.test(ch) ? DIGITS : ALNUM);
    let c = set[Math.floor(hash3(i, tick, seed) * set.length) % set.length];
    if (c === ch) c = set[(set.indexOf(c) + 1) % set.length];   // never shows the answer early
    return c;
  }).join('');
}

// Comp time at which flapText(target, ..., opts) has settled.
export function flapDone(target, t0, { rate = 15, settle = 4, stagger = 1, from = null } = {}) {
  const n = [...target].filter((ch, i) => flaps(ch) && !(from !== null && from[i] === ch)).length;
  return n === 0 ? t0 : t0 + (settle + (n - 1) * stagger) / rate;
}

// Draw a string as a row of flap tiles: one dark tile per character with the split hairline across its middle, the
// glyph centred in it. (x, y) is the baseline-left of the row. Returns [left, right] of the row.
// align 'right' ends the row at x. rise / drop: the tile's extent above and below the baseline, in units of size.
export function drawFlap(ctx, text, x, y, { size = 64, family = F.monoB, color = '#f2f4f7', tile = 'rgba(8,12,17,0.62)',
  split = 'rgba(0,0,0,0.55)', gap = null, padX = null, alpha = 1, align = 'left', rise = 0.86, drop = 0.16, sepW = 0.7 } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  font(ctx, family, size, 0);
  const cw = ctx.measureText('0').width, px = padX ?? size * 0.08, g = gap ?? size * 0.06;
  const tw = cw + 2 * px, top = y - size * rise, th = size * (rise + drop);
  const chars = [...text], width = c => (!flaps(c) && c !== ' ' ? cw * sepW : tw);
  const total = chars.reduce((a, c) => a + width(c) + g, 0) - g;
  let cx = align === 'right' ? x - total : x;
  const x0 = cx;
  for (const ch of chars) {
    const sep = !flaps(ch) && ch !== ' ';
    const w = width(ch);
    if (!sep && ch !== ' ') {
      ctx.fillStyle = tile; ctx.fillRect(cx, top, w, th);
    }
    ctx.fillStyle = color; ctx.textAlign = 'center';
    ctx.fillText(ch, cx + w / 2, y);
    if (!sep && ch !== ' ') {
      ctx.fillStyle = split; ctx.fillRect(cx, top + th / 2 - Math.max(1, size / 60), w, Math.max(2, size / 30));
    }
    cx += w + g;
  }
  ctx.restore();
  return [x0, x0 + total];
}
