// Design frames (2026-11-19; reviews/2026-11-19-codex-excerpt-gaps-r3.md sections 1-3): three full composites shown to
// the user before any re-edit. The on-call console is the persistent interface: the P0 ticket card (SHOW SCALE, this
// section tops out at HIGH; no P0), the chapter flap, corner marks, SONG / BAR with a small master-level meter, and the
// seat roster: pager icons laid out like the two front rows, a thin strip in the verses, expanded in perspective in the
// chorus (lighting group by group), shrunk back while a singing face is on screen; one seat stays selected (the
// engineer). One readable result per line; big type sparingly; amber only where a source gives it.
import { clamp } from '../../../../../../motion-kit/src/math.js';
import { frameChrome, hairline, pagerIcon, ticketCard } from './devices.js';
import { W_, clampView, fwd, monoLine } from './shots.js';
import { FONT, INK, drawWords, micro, setFont } from './type.js';
import { console2, lyricLow, mono } from './console2.js';

const W = 1920, H = 1080;
const AMBER = '#F2B134';
const COLD = 'rgba(232,240,250,0.95)';
const SHADOW = { color: 'rgba(0,0,0,0.6)', blur: 20, dy: 2 };

// ---------------------------------------------------------------- the console
function meter(k, o) {
  const lv = (k.data.meter || [])[k.data.frame_song.indexOf(k.s)] || [-60, -60];
  const x0 = W - 470, y0 = H - 72;
  micro(o, 'MASTER', x0, y0 + 9, { size: 9, track: 2, color: 'rgba(236,232,222,0.6)' });
  lv.forEach((db, row) => {
    const n = Math.round(clamp((db + 48) / 48) * 24);
    for (let i = 0; i < 24; i++) {
      o.fillStyle = i < n ? (i >= 20 ? AMBER : 'rgba(236,232,222,0.85)') : 'rgba(236,232,222,0.16)';
      o.fillRect(x0 + 52 + i * 6, y0 + row * 6, 4, 4);
    }
  });
}

// the seat roster. mode 'thin': two columns of small seats under the card; 'expanded': the two front rows in
// perspective, far to near, lit by groups. lit: groups lit (0-4, far first; a fraction = the group lighting now)
function roster(o, { mode, lit = 0, selected = [0, 1], x = 60, y = 176 }) {
  const rows = 2, per = 8;
  if (mode === 'thin') {
    micro(o, 'FRONT ROW · ON CALL', x, y + 8, { size: 9, track: 2, color: 'rgba(236,232,222,0.6)' });
    for (let r = 0; r < rows; r++) for (let i = 0; i < per; i++) {
      const sx = x + i * 21, sy = y + 18 + r * 15;
      const on = i / per < lit / 4;
      const sel = r === selected[0] && i === selected[1];
      pagerIcon(o, sx, sy, 0.72, { body: on ? AMBER : 'rgba(236,232,222,0.28)', lcd: 'rgba(14,15,17,0.9)' });
      if (sel) { o.strokeStyle = AMBER; o.lineWidth = 1.5; o.strokeRect(sx - 3.5, sy - 3.5, 22, 17); }
    }
    return;
  }
  // expanded: a little floor plan seen from the end of the runway; vanishing point above the panel's centre
  const pw = 340, ph = 220, vx = x + pw / 2, vy = y + 24;
  o.save();
  o.fillStyle = 'rgba(10,11,13,0.55)'; o.fillRect(x, y, pw, ph);
  o.strokeStyle = 'rgba(236,232,222,0.25)'; o.lineWidth = 1; o.strokeRect(x + 0.5, y + 0.5, pw - 1, ph - 1);
  micro(o, 'FRONT ROW · ON CALL', x + 12, y + 18, { size: 10, track: 2.2, color: 'rgba(236,232,222,0.75)' });
  micro(o, 'ALL HANDS', x + pw - 12, y + 18, { size: 10, track: 2.2, color: AMBER, align: 'right', fam: FONT.monoS });
  // the runway between the rows
  for (const sgn of [-1, 1]) hairline(o, vx, vy + 6, vx + sgn * 40, y + ph - 6, 'rgba(236,232,222,0.35)');
  for (let r = 0; r < rows; r++) {
    const sgn = r === 0 ? -1 : 1;
    for (let i = 0; i < per; i++) {
      const u = i / (per - 1);                      // 0 far .. 1 near
      const d = Math.pow(u, 1.35);
      const sx = vx + sgn * (44 + 100 * d), sy = vy + 18 + (ph - 60) * d;
      const sc = 0.42 + 0.72 * d;
      const group = 3 - Math.floor(i / 2);          // far group 3 lights first ... near group 0 last
      const order = 3 - group;                      // 0 far .. 3 near
      const f = clamp(lit - order);                 // 0 off .. 1 lit
      const lighting = f > 0 && f < 1;
      o.save();
      if (f > 0) { o.shadowColor = `rgba(242,177,52,${lighting ? 0.95 : 0.6})`; o.shadowBlur = lighting ? 18 : 8; }
      pagerIcon(o, sx - 11 * sc, sy - 7 * sc, sc, { body: f > 0 ? (lighting ? '#FFD27A' : AMBER) : 'rgba(236,232,222,0.22)', lcd: 'rgba(14,15,17,0.9)' });
      o.restore();
      if (r === selected[0] && i === per - 1 - selected[1]) {
        o.strokeStyle = AMBER; o.lineWidth = 1.5; o.strokeRect(sx - 15 * sc, sy - 11 * sc, 30 * sc, 22 * sc);
      }
    }
  }
  o.restore();
}

// v2 (style 2): the EV interface language, drawn under the print layer; a stronger halftone screen like EV's
const V2 = k => k.data.style === 2;
const PRINT = { uHalftone: 0.085, uCell: 3.0, uGrain: 0.034 };
function fin(k, ret) { return V2(k) ? { ...ret, underPrint: true, grade: { ...(ret.grade || {}), ...PRINT } } : ret; }

function chrome(k, o, { narrow = false, mode = 'thin', lit = 0, burn = [] } = {}) {
  if (V2(k)) { console2(k, o, { narrow, mode, lit, burn }); return; }
  ticketCard(k, o, { accent: k.s >= 40.7859 ? '#E8E4DA' : AMBER, narrow, icons: false });
  frameChrome(k, o);
  meter(k, o);
  roster(o, { mode, lit, y: narrow ? 154 : 176 });
}

const stillView = (size, c) => clampView(size, c);

// ---------------------------------------------------------------- frame 1 · 49.89 "awake"
// First read: her closed-eye singing face. Second: the engineer (his shoulder, his laptop corner). Third: his sleep
// line leaping from the laptop's edge to AWAKE. The roster shrunk, his seat still selected; one lyric line.
function d1(k) {
  const size = [1672, 941];
  const v = stillView(size, [836, 470, 1.0, 0]);
  const L = k.layers, o = L.overlay.ctx, e = L.emit.ctx;
  chrome(k, o, { mode: 'thin', lit: 4 });
  // the line of his night: from the top edge of his screen, along the dark floor, then the leap
  const [lx, ly] = fwd(size, v, 492, 806);
  const steps = [[lx, ly], [lx + 60, ly], [lx + 60, ly + 26], [lx + 230, ly + 26], [lx + 230, ly + 8], [lx + 420, ly + 8],
    [lx + 420, ly + 30], [lx + 640, ly + 30], [lx + 640, ly + 4], [lx + 780, ly + 4]];
  const leapX = lx + 780, top = ly - 330;
  if (V2(k)) {
    // a hairline from the top edge of his screen, the leap a single step; the result in the accent
    o.save(); o.strokeStyle = 'rgba(236,242,250,0.9)'; o.lineWidth = 1.25; o.lineJoin = 'miter';
    o.beginPath(); o.moveTo(...steps[0]); for (const p of steps.slice(1)) o.lineTo(...p);
    o.lineTo(leapX, top); o.lineTo(leapX + 260, top); o.stroke();
    o.setLineDash([2, 4]); o.strokeStyle = 'rgba(236,242,250,0.4)'; o.beginPath(); o.moveTo(lx, top); o.lineTo(leapX, top); o.stroke();
    o.restore();
    o.fillStyle = 'rgba(236,242,250,0.9)'; o.fillRect(leapX - 2, top - 2, 5, 5);
    mono(o, 'SLEEP · LAST NIGHT', lx + 8, ly + 40, { size: 10, track: 2 });
    mono(o, 'HIS LAPTOP · ILLUSTRATIVE CURVE', lx + 8, ly + 55, { size: 8, track: 1.6, color: 'rgba(240,236,228,0.55)' });
    mono(o, 'AWAKE', leapX + 14, top - 12, { size: 16, track: 4, color: '#F2B134', fam: FONT.monoS });
    mono(o, 'DEEP → AWAKE · 49.31', leapX + 14, top + 22, { size: 8, track: 1.6, color: 'rgba(240,236,228,0.55)' });
    lyricLow(k, o, W_(k, 8), drawWords, { index: 'L08 · CHORUS', x: 1150, y: 330 });
    return fin(k, { A: { tex: 'D1-b', view: v, lod: 0 }, chrome: false, emitGain: 1.4 });
  }
  e.save();
  e.lineJoin = 'round';
  for (const [wd, col] of [[10, 'rgba(200,225,255,0.18)'], [3.2, 'rgba(225,238,255,0.85)'], [1.3, 'rgba(255,255,255,1)']]) {
    e.strokeStyle = col; e.lineWidth = wd; e.beginPath(); e.moveTo(...steps[0]);
    for (const p of steps.slice(1)) e.lineTo(...p);
    e.lineTo(leapX, top); e.lineTo(leapX + 300, top);
    e.stroke();
  }
  const g = e.createRadialGradient(leapX, top, 0, leapX, top, 70);
  g.addColorStop(0, 'rgba(235,245,255,0.7)'); g.addColorStop(1, 'rgba(235,245,255,0)');
  e.fillStyle = g; e.beginPath(); e.arc(leapX, top, 70, 0, Math.PI * 2); e.fill();
  e.restore();
  micro(o, 'SLEEP · LAST NIGHT', lx + 8, ly + 58, { size: 11, track: 2.2, color: 'rgba(225,235,248,0.8)' });
  micro(o, 'ILLUSTRATIVE CURVE', lx + 8, ly + 74, { size: 9, track: 1.6, color: 'rgba(225,235,248,0.5)' });
  setFont(o, FONT.monoS, 24, 3); o.fillStyle = COLD; o.fillText('AWAKE', leapX + 18, top - 14);
  // one lyric line, in the dark beside her
  drawWords(k, o, W_(k, 8), 1150, 300, FONT.nim, 46, { color: INK.warm, shadow: SHADOW, space: 13, pop: false });
  return { A: { tex: 'D1-b', view: v, lod: 0 }, chrome: false, emitGain: 1.4 };
}

// ---------------------------------------------------------------- frame 2 · 42.77 "NIGHT"
// The walk take as placed in v4r1, the picture where her whole body and the long sleeve read; the roster expanded in
// the perspective of the two rows behind her, far groups lit, the nearest group lighting now; amber in the floor.
function d2(k) {
  const size = [2304, 1296];
  const v = stillView(size, [1152, 648, 1.0, 0]);
  const L = k.layers, o = L.overlay.ctx, e = L.emit.ctx, f = L.feed.ctx;
  chrome(k, o, { mode: 'expanded', lit: 3.45 });
  // the lit seats' light in the wet floor: soft amber streaks under the two rows
  e.save(); e.filter = 'blur(14px)';
  for (const [x, y0, len, a] of [[250, 840, 200, 0.26], [470, 790, 140, 0.2], [640, 760, 90, 0.16], [1290, 760, 90, 0.16],
    [1450, 790, 140, 0.2], [1660, 840, 200, 0.26]]) {
    const g = e.createLinearGradient(x, y0, x, y0 + len);
    g.addColorStop(0, `rgba(242,177,52,${a})`); g.addColorStop(1, 'rgba(242,177,52,0)');
    e.fillStyle = g; e.beginPath(); e.ellipse(x, y0 + len / 2, 46, len / 2, 0, 0, Math.PI * 2); e.fill();
  }
  e.restore();
  // the big word, small and out of the way; the line below it
  if (V2(k)) {
    mono(o, 'LOOK W1 · ON-CALL HOODIE COUTURE', 74, 846, { size: 10, track: 2.2, color: 'rgba(240,236,228,0.6)' });
    o.save(); setFont(o, FONT.din, 112, 1); o.shadowColor = 'rgba(0,0,0,0.38)'; o.shadowBlur = 22; o.shadowOffsetY = 3;
    o.fillStyle = 'rgba(236,230,220,0.86)'; o.fillText('NIGHT!', 70, 950); o.restore();
    k.mark(6, 3);
    mono(o, 'L06 · ALL HANDS! ALL NIGHT!', 74, 990, { size: 11, track: 3.2, color: 'rgba(240,236,228,0.78)' });
    return fin(k, { A: { tex: 'walk', view: v, lod: 0 }, chrome: false, emitGain: 1.3 });
  }
  micro(f, 'RUNWAY ONE · LOOK W1 · ON-CALL HOODIE COUTURE', 74, 862, { size: 12, track: 3, color: 'rgba(242,238,230,0.8)' });
  setFont(f, FONT.din, 120, 0); f.save(); f.shadowColor = 'rgba(0,0,0,0.5)'; f.shadowBlur = 14; f.shadowOffsetY = 4;
  f.fillStyle = INK.warm; f.fillText('NIGHT!', 70, 970); f.restore();
  monoLine(k, o, 6);
  return { A: { tex: 'walk', view: v, lod: 0 }, chrome: false, emitGain: 1.3 };
}

// ---------------------------------------------------------------- frame 3 · 35.78 the struck NOT
// The macro on the light box: cold white glass, the old scratch, her fingertip, one warm reflection running along the
// scratch so it shows; NOT printed on the glass and struck by the real scratch; the ticket narrowed, the roster quiet.
const SCRATCH = [[20, 460], [115, 498], [210, 536], [305, 574], [395, 610]];
function d3(k) {
  const size = [1672, 941];
  const v = stillView(size, [836, 470, 1.0, 0.01]);
  const L = k.layers, o = L.overlay.ctx, e = L.emit.ctx, f = L.feed.ctx;
  chrome(k, o, { narrow: true, mode: 'thin', lit: 0, burn: [[170, 120, 390, 0.86], [330, 1015, 540, 0.82]] });
  const P = (x, y) => fwd(size, v, x, y);
  f.save();
  const [nx, ny] = P(56, 560);
  const sc = 1.148 * v[2];
  f.translate(nx, ny); f.rotate(v[3]); f.scale(sc, sc);
  setFont(f, FONT.din, 150, 2); f.fillStyle = 'rgba(20,22,25,0.86)'; f.fillText('NOT', 0, 0);
  f.restore();
  // the warm reflection along the scratch (a glint near its middle, fading both ways)
  e.save(); e.lineCap = 'round';
  const pts = SCRATCH.map(([x, y]) => P(x, y));
  const g = e.createLinearGradient(...pts[0], ...pts[pts.length - 1]);
  g.addColorStop(0, 'rgba(242,177,52,0.0)'); g.addColorStop(0.45, 'rgba(255,196,96,0.95)'); g.addColorStop(0.7, 'rgba(242,177,52,0.5)'); g.addColorStop(1, 'rgba(242,177,52,0.15)');
  for (const [wd, a] of [[12, 0.25], [4, 0.8], [1.6, 1]]) {
    e.globalAlpha = a; e.strokeStyle = g; e.lineWidth = wd; e.beginPath(); e.moveTo(...pts[0]);
    for (const p of pts.slice(1)) e.lineTo(...p);
    e.stroke();
  }
  const [gx, gy] = P(170, 518);
  const rg = e.createRadialGradient(gx, gy, 0, gx, gy, 90);
  rg.addColorStop(0, 'rgba(255,190,90,0.55)'); rg.addColorStop(1, 'rgba(255,190,90,0)');
  e.globalAlpha = 1; e.fillStyle = rg; e.beginPath(); e.arc(gx, gy, 90, 0, Math.PI * 2); e.fill();
  e.restore();
  if (V2(k)) {
    lyricLow(k, o, W_(k, 4, [7, 8, 9, 10]), drawWords, { index: 'L04 · VERSE 1', y: H - 96 });
    mono(o, 'SOURCE · BUS-SHELTER AD · SF STANDARD · SEP 2 2026', 74, H - 60, { size: 9, track: 1.8, color: 'rgba(240,236,228,0.6)' });
    return fin(k, { A: { tex: 'X09b', view: v, lod: 0 }, chrome: false, emitGain: 1.3, tint: [0.97, 1.0, 1.035] });
  }
  drawWords(k, o, W_(k, 4, [7, 8, 9, 10]), 72, H - 92, FONT.nim, 44, { color: INK.warm, shadow: SHADOW, space: 12, pop: false });
  micro(o, 'SOURCE · BUS-SHELTER AD · SF STANDARD · SEP 2 2026', 74, H - 56, { size: 11, track: 1.6 });
  return { A: { tex: 'X09b', view: v, lod: 0 }, chrome: false, emitGain: 1.3, tint: [0.97, 1.0, 1.035] };
}

export const SHOT_FN_DESIGN = { d1, d2, d3 };
