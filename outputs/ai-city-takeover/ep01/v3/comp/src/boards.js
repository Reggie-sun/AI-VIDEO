// Split-flap family (motion-kit flap.js): the flip clocks, the date, the day calendar, the OUTSIDE wall, and the cached
// photos flipping like flap tiles. Words and numbers come from graphic_text (03:46 → 03:47 · IRIS CLOCK, SEP 20,
// DAY 01 → DAY 11, OUTSIDE, CACHED), falling back to the component name's argument; flips land on the unit cue or the
// token's CTC onset. A board's change starts on its cue frame (qa.py measures the change's onset there).
import { F, font } from '../../../../../../motion-kit/src/draw2d.js';
import { drawFlap, flapText } from '../../../../../../motion-kit/src/flap.js';
import { clamp, easeOutCubic } from '../../../../../../motion-kit/src/math.js';
import { timelineBar } from '../../../../../../motion-kit/src/osd-charts.js';
import { stamp } from './labels.js';
import { DIM, H, W, accent, arrowParts, beatLen, boardCaption, boardText, text, tokAt } from './util.js';

const flaps = ch => /[0-9A-Za-z]/.test(ch);
// width of a drawFlap row (same arithmetic as flap.js) so a board can be centred
function flapWidth(ctx, s, { size, gap = null, padX = null, sepW = 0.7 }) {
  ctx.save(); font(ctx, F.monoB, size, 0);
  const cw = ctx.measureText('0').width; ctx.restore();
  const px = padX ?? size * 0.08, g = gap ?? size * 0.06, tw = cw + 2 * px;
  return [...s].reduce((a, c) => a + (!flaps(c) && c !== ' ' ? cw * sepW : tw) + g, 0) - g;
}
function centred(ctx, s, y, opts) {
  drawFlap(ctx, s, (W - flapWidth(ctx, s, opts)) / 2, y, opts);
}
const hhmm = s => `${s.slice(0, 2)}:${s.slice(2)}`;
// a string that keeps flapping until its own settle time (the board 'turning' before it lands)
const rolling = (s, t, t0, seed) => flapText(s, t, t0, { settle: 1e6, seed });
// a board turning in from the cut onto `s`: every flapping character settles together after at most two ticks, at
// least 0.2 s before `land` (the cue), so nothing on the board moves in the frames before the cue; with no room it
// simply shows `s` from the cut (a2 修正: a1's staggered roll-in settled 3 frames before U004's cue)
function intro(s, t, t0, land, seed) {
  const settle = Math.min(2, Math.floor((land - 0.2 - t0) * 15 + 1e-6));
  return settle > 0 ? flapText(s, t, t0, { settle, stagger: 0, seed }) ?? s : s;
}
// the before / after pair of a board: graphic_text's two sides of the arrow, else the name's argument
function pair(u, arg, fmt = x => x) {
  const p = arrowParts(boardText(u.text));
  return p.length === 2 ? p : arg.split('_').map(fmt);
}

const CLOCK = { size: 250, gap: 14, padX: 14, sepW: 0.55, tile: 'rgba(16,22,30,0.92)', rise: 0.82, drop: 0.12 };

export const BOARDS = {
  // flipclock_0346_0347: the changed digit turns to the spoken time on the cue frame itself (no flap tick between: a
  // random digit there read as a made-up time, 03:48 at U004's cue); the caption after ' · ' (IRIS CLOCK: the series'
  // own clock, not event time) sits small under the board from the cut
  flipclock(k, t, u, arg) {
    const [a, b] = pair(u, arg, hhmm), o = k.layers.overlay.ctx, tF = u.cue;
    const shown = t < tF ? intro(a, t, k.t0, tF, 346) : b;
    centred(o, shown, 640, CLOCK);
    const cap = boardCaption(u.text);
    if (cap) text(o, cap, W / 2, 760, { size: 28, align: 'center', tracking: 9, color: DIM, shadow: null });
    return {};
  },
  flipdate(k, t, u, arg) {                                          // flipdate_SEP_20: each part settles on its word
    const parts = u.toks.length ? u.toks.map(x => x.text) : arg.split('_'), o = k.layers.overlay.ctx;
    const shown = parts.map((s, i) => {
      const at = tokAt(u, i);
      return t < at ? rolling(s, t, k.t0, 9 + i) : flapText(s, t, at, { settle: 2, stagger: 1, seed: 920 + i });
    });
    centred(o, shown.join(' '), 640, CLOCK);
    return {};
  },
  // calendar_day01_day11: one day per sixteenth from the word, counting straight up (no random digits between days)
  calendar(k, t, u, arg) {
    const [fromS, toS] = pair(u, arg, s => s.toUpperCase().replace(/(\D+)(\d+)/, '$1 $2'));
    const from = Number(fromS.replace(/\D/g, '')), to = Number(toS.replace(/\D/g, '')), prefix = toS.replace(/\s*\d+\s*$/, '');
    const voiced = u.toks.filter(x => x.voiced).map(x => x.at), tC = voiced.length ? Math.min(...voiced) : u.cue, o = k.layers.overlay.ctx;
    const step = beatLen(k, tC) / 4, j = t < tC ? -1 : Math.floor((t - tC) / step);
    const n = Math.min(to, from + Math.max(0, j + 1));
    const pad = v => String(v).padStart(2, '0'), lab = v => `${prefix} ${pad(v)}`;
    const shown = t < tC ? intro(lab(from), t, k.t0, tC, 32) : lab(n);
    centred(o, shown, 600, { ...CLOCK, size: 210 });
    timelineBar(o, to, [560, 690, 800, 16], { filled: t < tC ? from : clamp(n, from, to), from: fromS, to: toS, size: 18 });
    return {};
  },
  flipwall(k, t, u, arg) {                                          // flipwall_OUTSIDE: the whole wall turns to the word
    // six rows in the upper two thirds, clear of a lyric_chant word on the same unit (its caps start at y 740)
    const o = k.layers.overlay.ctx, word = (u.text || arg).toUpperCase(), row = `${word} ${word} ${word}`, size = 78, rows = 6, lead = 1.24;
    const y0 = 390 - (rows - 1) * size * lead / 2 + size * 0.36;
    const opts = { size, gap: 5, padX: 6, tile: 'rgba(16,22,30,0.92)', rise: 0.8, drop: 0.14 };
    for (let r = 0; r < rows; r++) {
      // rows start one after another (a frame apart) and every row has settled well inside the unit
      const t0 = k.t0 + r * (1 / 30) + (r % 2) * 0.02, shown = flapText(row, t, t0, { settle: 2, stagger: 0.25, seed: 54 + r });
      centred(o, shown ?? row, y0 + r * size * lead, shown ? opts : { ...opts, color: 'rgba(0,0,0,0)' });   // blank tiles first
    }
    return {};
  },
  // photo_flip_cached: the unit's stills as grey, frozen photos; each switch flips like a split-flap tile: on the switch
  // frame the old top half has fallen (the new top shows) and the new bottom half swings down over the old one in the
  // next frames, so the picture changes most on the switch frame itself (a2 修正: a1's fold peaked 2 frames late);
  // CACHED stamped on the cue
  photo_flip_cached(k, t, u) {
    const f = k.layers.feed.ctx, cw = 1120, ch = 630, x = 1000 - cw / 2, y = 470 - ch / 2, dur = 4 / 30;
    const img = key => k.bitmaps[key];
    const cur = u.plates.filter(p => k.frame >= p.f).pop() || u.plates[0];
    const i = u.plates.indexOf(cur), prevKey = i > 0 ? u.plates[i - 1].key : null, ft = (k.frame - cur.f) / 30;
    const card = (key, part = 'all', sy = 1) => {                       // part: top / bottom half, folded by sy (0..1)
      const im = img(key);
      if (!im || sy <= 0) return;
      const sw = im.width, sh = im.height, half = part === 'bottom' ? 1 : 0;
      f.save();
      f.filter = 'grayscale(1)';                                        // grey from the first frame (spec: 去饱和)
      if (part === 'all') f.drawImage(im, 0, 0, sw, sh, x, y, cw, ch);
      else {
        const hy = y + ch / 2;
        f.translate(0, hy); f.scale(1, sy); f.translate(0, -hy);
        f.drawImage(im, 0, half * sh / 2, sw, sh / 2, x, y + half * ch / 2, cw, ch / 2);
      }
      f.restore();
    };
    f.save(); f.fillStyle = 'rgba(0,0,0,0.5)'; f.filter = 'blur(18px)'; f.fillRect(x + 16, y + 24, cw, ch); f.restore();
    if (prevKey && ft < dur - 1e-6) {                                   // the new bottom half swinging down
      card(cur.key, 'top'); card(prevKey, 'bottom'); card(cur.key, 'bottom', easeOutCubic((ft + 1 / 30) / dur));
      f.save(); f.globalAlpha = 0.7; f.fillStyle = '#05070a'; f.fillRect(x, y + ch / 2 - 2, cw, 4); f.restore();
    } else card(cur.key);
    f.save(); f.strokeStyle = 'rgba(236,241,244,0.75)'; f.lineWidth = 3; f.strokeRect(x - 1.5, y - 1.5, cw + 3, ch + 3); f.restore();
    if (u.text) stamp(k.layers.overlay.ctx, u.text, x + cw - 230, y + ch - 110, t, tokAt(u, 0), { size: 70, color: accent(u) });
    return { grade: { uGrain: 0.05 } };
  },
};
