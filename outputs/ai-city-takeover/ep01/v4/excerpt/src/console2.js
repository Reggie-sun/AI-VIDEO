// The on-call console in the EV interface language (design frames v2, 2026-11-19). The user rejected v1's interface as
// web UI chips (it looked cheap and out of the film's colour style). EV's grammar (design/ev-ui crops; visual_system.json): no filled
// boxes, small near-white monospace caps with wide tracking, hairline rules and thin underlines, tiny crosshair corner
// ticks, a tiny waveform under the title, one device built from small dark half-transparent tiles with its value in
// the accent, micro-type sub-lines under a hairline; the accent on a few characters only. Everything here is drawn on
// the layer that goes under the grade, halftone and grain (main.js underPrint), so it belongs to the picture.
import { clamp } from '../../../../../../motion-kit/src/math.js';
import { FONT, setFont } from './type.js';

const W = 1920, H = 1080;
export const AMBER = '#F2B134';
const INKW = 'rgba(240,236,228,0.92)';
const INKD = 'rgba(240,236,228,0.58)';
const RULE = 'rgba(240,236,228,0.42)';
const INKD5 = 'rgba(240,236,228,0.84)';     // v4r5: EV's small type is near-white, not grey

export function mono(ctx, text, x, y, { size = 13, track = 2.6, color = INKW, align = 'left', fam = FONT.mono } = {}) {
  ctx.save();
  setFont(ctx, fam, size, track);
  ctx.textAlign = align; ctx.fillStyle = color;
  ctx.fillText(text, x, y);
  const w = ctx.measureText(text).width;
  ctx.restore();
  return w;
}
export function rule(ctx, x0, y, x1, color = RULE) {
  ctx.save(); ctx.fillStyle = color; ctx.fillRect(Math.min(x0, x1), Math.round(y), Math.abs(x1 - x0), 1); ctx.restore();
}

// the ticket state through the excerpt (board chrome; SHOW SCALE tops out at HIGH here, no P0)
function ticketAt(s) {
  if (s < 32.934) return { id: 'INC-0804', title: 'BILLBOARD BEHIND A TREE', sev: 'MED' };
  if (s < 36.1999) return { id: 'INC-0902', title: 'BUS STOP', sev: 'MED' };
  if (s < 40.7859) return { id: 'INC-0902', title: 'FREEWAY', sev: 'MED' };
  return { id: 'ALL HANDS', title: 'RUNWAY ONE', sev: s < 42.769 ? 'MED' : 'HIGH' };
}

// small dark half-transparent tiles, one character each (EV's flap device); `accent` characters in amber
function tiles(ctx, text, x, y, { accentFrom = 99, tw = 17, th = 23, gap = 2 } = {}) {
  ctx.save();
  setFont(ctx, FONT.monoS, 14, 0);
  ctx.textAlign = 'center';
  let cx = x;
  [...text].forEach((ch, i) => {
    if (ch === ' ') { cx += tw * 0.6; return; }
    ctx.fillStyle = 'rgba(34,36,40,0.62)'; ctx.fillRect(cx, y, tw, th);
    ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(cx, y + th / 2, tw, 1);
    ctx.fillStyle = i >= accentFrom ? AMBER : INKW;
    ctx.fillText(ch, cx + tw / 2, y + th - 6);
    cx += tw + gap;
  });
  ctx.restore();
  return cx - x;
}

// the pager as a hairline glyph: body outline, its little screen (filled in the accent when lit), the button
export function pagerGlyph(ctx, x, y, s, { lit = 0, bright = false } = {}) {
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s);
  ctx.lineWidth = 1 / s;
  ctx.strokeStyle = lit > 0 ? 'rgba(240,236,228,0.9)' : 'rgba(240,236,228,0.42)';
  ctx.strokeRect(0.5, 0.5, 20, 13);
  if (lit > 0) {
    ctx.fillStyle = bright ? '#FFD27A' : AMBER;
    ctx.globalAlpha = 0.35 + 0.65 * lit;
    ctx.fillRect(3, 3, 11, 5);
  } else {
    ctx.strokeRect(3.5, 3.5, 10, 4);
  }
  ctx.globalAlpha = 1;
  ctx.fillStyle = ctx.strokeStyle; ctx.fillRect(16, 4, 1.5, 5);
  ctx.restore();
}
function bracket(ctx, x0, y0, x1, y1, arm = 5) {
  ctx.save(); ctx.strokeStyle = INKW; ctx.lineWidth = 1;
  for (const [x, y, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x1, y1, -1, -1], [x0, y1, 1, -1]]) {
    ctx.beginPath(); ctx.moveTo(x + 0.5, y + sy * arm); ctx.lineTo(x + 0.5, y + 0.5); ctx.lineTo(x + sx * arm, y + 0.5); ctx.stroke();
  }
  ctx.restore();
}

// the seat roster. 'thin': two rows of eight hairline pagers under the ticket; 'expanded': the two front rows in the
// runway's perspective on a faint panel with a hairline top, groups lit far -> near
function roster(ctx, { mode, lit, selected = [0, 1], sel = true, x = 72, y, v5 = false }) {
  const MS = v5 ? 11 : 9, MC = v5 ? INKD5 : INKD;
  const per = 8;
  if (mode === 'thin') {
    mono(ctx, 'FRONT ROW · ON CALL', x, y + 8, { size: MS, track: 2, color: MC });
    for (let r = 0; r < 2; r++) for (let i = 0; i < per; i++) {
      const sx = x + i * 22, sy = y + 18 + r * 16;
      pagerGlyph(ctx, sx, sy, 0.78, { lit: i / per < lit / 4 ? 1 : 0 });
      if (sel && r === selected[0] && i === selected[1]) bracket(ctx, sx - 4, sy - 4, sx + 20, sy + 14, 4);
    }
    return;
  }
  const pw = 340, ph = 214, vx = x + pw / 2, vy = y + 34;
  ctx.save();
  ctx.fillStyle = 'rgba(10,11,13,0.30)'; ctx.fillRect(x, y, pw, ph);
  rule(ctx, x, y, x + pw, 'rgba(240,236,228,0.55)');
  mono(ctx, 'FIG. 01 · FRONT ROW · ON CALL', x + 10, y + 18, { size: 10, track: 2 });
  mono(ctx, 'ALL HANDS', x + pw - 10, y + 18, { size: 10, track: 2, color: AMBER, align: 'right' });
  for (const sgn of [-1, 1]) {
    ctx.strokeStyle = 'rgba(240,236,228,0.28)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(vx, vy); ctx.lineTo(vx + sgn * 36, y + ph - 4); ctx.stroke();
  }
  for (let r = 0; r < 2; r++) {
    const sgn = r === 0 ? -1 : 1;
    for (let i = 0; i < per; i++) {
      const d = Math.pow(i / (per - 1), 1.35);
      const sx = vx + sgn * (40 + 96 * d), sy = vy + 12 + (ph - 56) * d;
      const sc = 0.42 + 0.7 * d;
      const order = Math.floor(i / 2);               // far group (i 0-1) lights first
      const f = clamp(lit - order);
      pagerGlyph(ctx, sx - 10.5 * sc, sy - 7 * sc, sc, { lit: f, bright: f > 0 && f < 1 });
      if (sel && r === selected[0] && i === per - 1 - selected[1]) bracket(ctx, sx - 15 * sc, sy - 11 * sc, sx + 15 * sc, sy + 11 * sc, 4);
    }
  }
  ctx.restore();
}

// the console: ticket top left, title + waveform + chapter top right, corner ticks, SONG / BAR bottom right
export function console2(k, ctx, { narrow = false, mode = 'thin', lit = 0, burn = [], sel = true, v5 = false } = {}) {
  const MS = v5 ? 11 : 8.5, MC = v5 ? INKD5 : INKD;
  const s = k.s, t = ticketAt(s);
  // on a pale ground (the light box) the type sits in a soft photographic burn, never in a box
  for (const [bx, by, br, ba] of burn) {
    const g = ctx.createRadialGradient(bx, by, 0, bx, by, br);
    g.addColorStop(0, `rgba(8,9,11,${ba})`); g.addColorStop(0.55, `rgba(8,9,11,${ba * 0.6})`); g.addColorStop(1, 'rgba(8,9,11,0)');
    ctx.fillStyle = g; ctx.fillRect(bx - br, by - br, 2 * br, 2 * br);
  }
  // corner crosshair ticks
  ctx.save(); ctx.fillStyle = 'rgba(240,236,228,0.62)';
  for (const [x, y] of [[24, 24], [W - 24, 24], [24, H - 24], [W - 24, H - 24]]) { ctx.fillRect(x - 11, y, 23, 1); ctx.fillRect(x, y - 11, 1, 23); }
  ctx.restore();
  // ticket: the id and title as one mono line, the severity as tiles, a hairline, micro sub-lines
  const x = 72;
  const head = narrow ? `${t.id} · ${t.title}` : `${t.id} · ${t.title}`;
  const hw = mono(ctx, head, x, 61, { size: 13, track: 2.6 });
  const tw = tiles(ctx, `SEV ${t.sev}`, x, 74, { accentFrom: 4 });
  const ruleW = narrow ? Math.max(hw, tw) : Math.max(300, hw, tw);
  rule(ctx, x, 106, x + ruleW);
  if (!narrow) mono(ctx, 'SHOW SCALE · LOW / MED / HIGH / CRIT', x, v5 ? 124 : 120, { size: MS, track: 1.8, color: MC });
  mono(ctx, 'STATUS · PAGED', x, narrow ? 120 : v5 ? 141 : 133, { size: MS, track: 1.8, color: MC });
  roster(ctx, { mode, lit, sel, v5, y: narrow ? 138 : v5 ? 162 : 152 });
  // title, waveform, chapter
  mono(ctx, 'IRIS · ALL HANDS · EP01', W - 72, 61, { size: 13, track: 2.6, align: 'right' });
  // the master's level, 56 bars of 45 ms ending now: per design frame (wave) or sliced from the window's steps (wave_db)
  let wave = [];
  if (k.data.wave_db) {
    const i = Math.floor((s - k.data.wave_t0) / k.data.wave_step);
    wave = k.data.wave_db.slice(Math.max(0, i - 55), i + 1);
  } else if (k.data.frame_song) wave = k.data.wave[k.data.frame_song.indexOf(s)] || [];
  const n = wave.length, bw = 2, bg = 1.4;
  const lo = Math.min(...wave), hi = Math.max(...wave);
  ctx.save();
  wave.forEach((db, i) => {
    const h = 2 + 16 * Math.pow(clamp((db - lo) / Math.max(hi - lo, 1e-3)), 1.6);
    ctx.fillStyle = i === n - 1 ? AMBER : 'rgba(240,236,228,0.72)';
    ctx.fillRect(W - 72 - (n - i) * (bw + bg), 108 - h, bw, h);
  });
  ctx.restore();
  const ch = s < 40.7859 ? 'CH 02 · STREET LOOKS' : 'CH 03 · RUNWAY ONE';
  mono(ctx, ch, W - 72, v5 ? 128 : 126, { size: v5 ? 11 : 9, track: 2, color: MC, align: 'right' });
  // song clock and bar
  const mm = String(Math.floor(s / 60)).padStart(2, '0'), ss = (s % 60).toFixed(2).padStart(5, '0');
  mono(ctx, `SONG ${mm}:${ss} · BAR ${k.barNo()}`, W - 72, H - 76, { size: 13, track: 2.6, align: 'right' });
  if (v5) { ticker(k, ctx); ruler(k, ctx); }
}

// v4r5: the bottom on-call event stream between two hairlines (EV's ticker grammar). Its items are the board's own
// text (build.py ticker_items: each read from its field in board/shots.json); it runs left at 80 px/s of song time.
function ticker(k, ctx) {
  const items = (k.data.ticker || []).map(i => i.text);
  if (!items.length) return;
  const y0 = H - 48, y1 = H - 14;
  ctx.fillStyle = 'rgba(8,9,11,0.38)'; ctx.fillRect(0, y0, W, y1 - y0);      // EV's band is a shade darker than the picture
  rule(ctx, 0, y0, W, 'rgba(240,236,228,0.5)'); rule(ctx, 0, y1, W, 'rgba(240,236,228,0.5)');
  ctx.save();
  // monospaced: one fixed advance a character (measured without tracking), so the loop's period is exact
  setFont(ctx, FONT.mono, 13, 0);
  const adv = ctx.measureText('M').width + 2.4;
  const sep = '   *   ';
  const line = items.join(sep) + sep;
  const lw = line.length * adv;
  const x0 = -((k.s * 80) % lw);
  ctx.fillStyle = 'rgba(240,236,228,0.9)';
  for (let rep = 0; x0 + rep * lw < W; rep++) {
    for (let i = 0; i < line.length; i++) {
      const x = x0 + rep * lw + i * adv;
      if (x < -adv || x > W || line[i] === ' ') continue;
      ctx.fillText(line[i], x, H - 25);
    }
  }
  ctx.restore();
}

// v4r5: a fine scale up the left edge (EV's): a tick a beat, a label a bar (the bar number), the current position held
// at the frame's middle and marked by one short accent tick
function ruler(k, ctx) {
  const db = k.data.downbeats || [];
  let i = 0;
  while (i + 1 < db.length && db[i + 1] <= k.s) i++;
  const frac = db[i + 1] ? (k.s - db[i]) / (db[i + 1] - db[i]) : 0;
  const pos = i + frac;                       // bars from the song's first downbeat
  const PX = 88, cy = H / 2, x = 34;
  ctx.save();
  for (let b = Math.floor(pos) - 6; b <= Math.floor(pos) + 7; b++) {
    for (let q = 0; q < 4; q++) {
      const yy = cy + (b + q / 4 - pos) * PX;
      if (yy < 220 || yy > H - 80) continue;
      ctx.fillStyle = 'rgba(240,236,228,0.4)';
      ctx.fillRect(x, Math.round(yy), q === 0 ? 9 : 5, 1);
      if (q === 0 && b >= 0) mono(ctx, String(b + 1).padStart(3, '0'), x + 14, yy + 3, { size: 9, track: 1.2, color: 'rgba(240,236,228,0.5)' });
    }
  }
  ctx.fillStyle = AMBER; ctx.fillRect(x - 6, cy, 14, 1.5);
  ctx.restore();
}

// v4r5: the lyric as EV's small mono annotation: an index line, then the line itself in tracked mono caps, each word on
// its onset; the big DINish words are drawn separately, only on the board's masthead words
export function lyricMono(k, ctx, words, drawWords, { index, x = 72, y = H - 82 } = {}) {
  mono(ctx, index, x, y - 30, { size: 11, track: 2, color: INKD5 });
  drawWords(k, ctx, words, x, y, FONT.mono, 20, { track: 4.5, space: 18, upper: true, pop: false, color: 'rgba(242,238,230,0.94)',
    shadow: { color: 'rgba(0,0,0,0.55)', blur: 10 } });
}

// the lyric low-left in the author's subtitle manner, a micro index line above it
export function lyricLow(k, ctx, words, drawWords, { index, x = 72, y = H - 92 } = {}) {
  mono(ctx, index, x, y - 50, { size: 9, track: 2, color: INKD });
  drawWords(k, ctx, words, x, y, FONT.nim, 42, { color: 'rgba(240,234,224,0.95)', shadow: { color: 'rgba(0,0,0,0.45)', blur: 16, dy: 2 },
    space: 12, pop: false });
}
