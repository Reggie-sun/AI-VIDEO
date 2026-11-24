// The eight shots of the excerpt (board v4 s007-s014, edited by the user's edit decision list). Each returns the scene
// parameters (picture, camera, focus, layers) for the frame and draws its type and devices on the 2D layers. Song time
// k.s is the frame's own time; every value is a pure function of the frame.
import { clamp, easeInOutCubic, easeOutCubic, lerp } from '../../../../../../motion-kit/src/math.js';
import { brackets, callScreen, classifier, gauge, hairline, hypnogram, lcdCard, leader, pagerStack, tagLabel } from './devices.js';
import { FONT, INK, drawWords, micro, setFont, shown, since, slamWord, textW } from './type.js';

const W = 1920, H = 1080;
const SHADOW = { color: 'rgba(0,0,0,0.55)', blur: 18, dy: 2 };

// ---------------------------------------------------------------- cameras
// view = [cx, cy, zoom, rot] in source pixels; fit = output px per source px at zoom 1 (cover)
export function fitOf(size) { return Math.max(W / size[0], H / size[1]); }
export function clampView(size, v) {
  const fit = fitOf(size), hw = W / 2 / (fit * v[2]), hh = H / 2 / (fit * v[2]);
  return [clamp(v[0], hw, size[0] - hw), clamp(v[1], hh, size[1] - hh), v[2], v[3]];
}
// source px -> output px under a view (the shader's inverse)
export function fwd(size, v, x, y, shake = [0, 0]) {
  const k = fitOf(size) * v[2], c = Math.cos(v[3]), s = Math.sin(v[3]);
  const dx = (x - v[0]) * k, dy = (y - v[1]) * k;
  return [W / 2 + shake[0] + c * dx - s * dy, H / 2 + shake[1] + s * dx + c * dy];
}
// canvas transform that draws in source px under a view
export function srcTransform(ctx, size, v, shake = [0, 0]) {
  const k = fitOf(size) * v[2], c = Math.cos(v[3]), s = Math.sin(v[3]);
  const [ex, ey] = fwd(size, v, 0, 0, shake);
  ctx.setTransform(k * c, k * s, -k * s, k * c, ex, ey);
}
// a 2.5D pair: the background under v, her layer pushed off it by parallax `par` about her anchor, and scaled
// a little more on a push (`parZ`), so she separates from the room as the camera moves
function parallax(v, anchor, par, parZ = 0.6) {
  const z = Math.pow(v[2], 1 + parZ);
  return [anchor[0] + (v[0] - anchor[0]) * (1 + par), anchor[1] + (v[1] - anchor[1]) * (1 + par), z, v[3] * (1 + par * 0.5)];
}
// a move that steps on beats: progress p(0..1) across [a, b] advanced only on beats, eased over `ease` of a beat
function beatSteps(k, a, b, ease = 0.35) {
  const n = k.beatsBetween(a, b);
  if (n <= 0) return clamp((k.s - a) / (b - a));
  const bp = k.beatIndexFloat(k.s) - k.beatIndexFloat(a);
  const i = Math.floor(bp), f = bp - i;
  return clamp((Math.min(n, i) + (i < n ? easeOutCubic(f / ease) : 0)) / n);
}

// a lyric line's words, optionally only some of them (by index)
export const W_ = (k, li, idx = null) => {
  const ws = k.line(li);
  return idx ? idx.map(i => ws[i]) : ws;
};
const lastEnd = ws => Math.max(...ws.map(w => w.end));

// the lower-left lyric line in tracked mono caps (the author's lower-left lines; chorus only)
export function monoLine(k, ctx, li, { from = -1e9, until = 1e9 } = {}) {
  if (k.s < from || k.s > until) return;
  drawWords(k, ctx, W_(k, li), 72, H - 46, FONT.mono, 21, { track: 7, space: 22, upper: true, color: 'rgba(242,238,230,0.9)',
    shadow: { color: 'rgba(0,0,0,0.6)', blur: 10 }, pop: false });
}
// a subtitle line, low centre (board `subtitle`: Nimbus Sans Bold, warm white, soft shadow; in on its first word, out
// 0.4 s after its last; it never crosses a cut by accident)
export function subtitle(k, ctx, li, until) {
  if (k.s > until) return;
  drawWords(k, ctx, W_(k, li), W / 2, H - 92, FONT.nim, 44, { align: 'center', color: INK.warm, shadow: SHADOW, space: 12 });
}

// ---------------------------------------------------------------- s007 billboard behind a tree (MO04)
function s007(k) {
  const v = [1152, 648, 1.0 + 0.02 * clamp((k.s - 26.0528) / 3.7), 0];
  const L = k.layers;
  // board coverline: her lines printed on the billboard's lit face, along its perspective (the wall's top edge falls
  // 7 deg to the right); dark ink keyed to the lit face, so the leaves cover it
  const sf = L.surf.ctx;
  sf.save();
  sf.translate(96, 236); sf.rotate(0.118); sf.transform(1, 0, -0.06, 1, 0, 0);
  const l2 = W_(k, 2);
  drawWords(k, sf, l2.slice(0, 4), 0, 0, FONT.nim, 42, { color: INK.dark, space: 12 });
  drawWords(k, sf, l2.slice(4), 0, 54, FONT.nim, 42, { color: INK.dark, space: 12 });
  drawWords(k, sf, W_(k, 3), 0, 108, FONT.nim, 42, { color: INK.dark, space: 12 });
  sf.restore();
  // label on the branch she pulls: $6,000 / MONTH on "grand"
  const o = L.overlay.ctx;
  const a = since(k, 26.293);
  if (a >= 0) {
    o.save(); o.strokeStyle = 'rgba(236,232,222,0.8)'; o.lineWidth = 1;
    o.beginPath(); o.moveTo(1008, 196); o.lineTo(842, 332); o.stroke(); o.restore();
    tagLabel(o, 690, 326, a, { tag: '$6,000 / MONTH', sub: 'PARTIALLY OBSCURED BY A TREE', source: 'SOURCE · SF STANDARD · AUG 4 2026', rot: 0.05 });
  }
  return { A: { tex: 'seq', view: v, lod: 0.0 }, key: [0.55, 0.78] };
}

// ---------------------------------------------------------------- s008 name sticker (SG02, lip sync)
function s008(k) {
  const v = [1220, 640, 1.05, -0.012];
  const size = [2304, 1296];
  const tr = k.track('s008');
  const L = k.layers;
  if (tr) {
    const [x0, y0] = fwd(size, v, tr[0] * size[0], tr[1] * size[1]);
    const [x1, y1] = fwd(size, v, tr[2] * size[0], tr[3] * size[1]);
    // the classifier is drawn on the sticker: AI printed on it, the rows beside it (board: drawn_on the sticker)
    const f = L.feed.ctx;
    f.save();
    f.translate(x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.66); f.rotate(-0.02);
    setFont(f, FONT.nim, 38, 0); f.fillStyle = 'rgba(23,25,28,0.9)'; f.textAlign = 'center'; f.fillText('A.I.', 0, 0);
    setFont(f, FONT.mono, 10, 1.6); f.fillText('AVERAGE INDIVIDUAL', 0, 20);
    f.restore();
    const o = L.overlay.ctx;
    brackets(o, x0 - 8, y0 - 8, x1 + 8, y1 + 8, since(k, 29.7448), { color: INK.amber });
    leader(o, [x0 + 40, y0 - 8], [1560, 820], since(k, 29.7448), { dot: false, color: 'rgba(242,177,52,0.85)' });
    classifier(k, o, 1440, 672, [
      { k: 'AI', v: 'DETECTED', at: 29.7448, hot: false },
      { k: 'AI = AVERAGE INDIVIDUAL', v: 'MATCH', at: 30.238, hot: true },
    ], { title: 'CLASSIFIER · NAME TAG', width: 420,
      source: 'CHATTJB BILLBOARD · 6TH & FOLSOM · SF STANDARD · AUG 4 2026' });
  }
  subtitle(k, L.overlay.ctx, 3, 99);
  return { A: { tex: 'seq', view: v, lod: 0.0 } };
}

// ---------------------------------------------------------------- s009 bus stop (p009, 2.5D)
// Treatment (board: scratch-light travel): bar 1 she is the subject (the lightbox soft behind her) for "That's me.";
// on the 33.437 downbeat focus racks to the lightbox and the camera steps toward it on every beat, her layer sliding
// past faster (parallax); on "scratched" a thin light runs along the real scratch through NOT and finishes on the
// 35.283 bar line at her fingertip.
const SCRATCH = [[200, 300], [262, 318], [318, 333], [365, 345], [405, 358], [432, 370], [451, 382]];
function s009(k) {
  const size = [1672, 941];
  const anchor = [1000, 470];
  const rack = easeInOutCubic(clamp((k.s - 33.4367) / 0.35));
  const p = beatSteps(k, 33.4367, 36.1999);
  const z = lerp(1.14, 1.10, rack) + 0.05 * p;
  const v = clampView(size, [lerp(980, 700, rack) - 110 * p, lerp(430, 440, rack), z, lerp(0.012, -0.01, rack)]);
  const vb = parallax(v, anchor, 0.32, 0.5);
  const L = k.layers;
  // the lightbox: the ad as printed (keyed to the lit glass, so her finger covers it)
  const sf = L.surf.ctx;
  sf.save();
  srcTransform(sf, size, v);
  drawWords(k, sf, W_(k, 4, [0, 1]), 104, 214, FONT.nim, 34, { color: INK.dark, space: 10 });
  const big = W_(k, 4, [2, 3, 4, 5, 6]);
  const notA = since(k, 35.158);
  drawWords(k, sf, big.slice(0, 2), 104, 372, FONT.din, 104, { color: INK.dark, space: 22, upper: true, track: 1 });
  drawWords(k, sf, big.slice(2, 3), 104, 482, FONT.din, 104, { color: INK.dark, upper: true, track: 1 });
  drawWords(k, sf, big.slice(3), 104, 592, FONT.din, 104, { color: INK.dark, space: 22, upper: true, track: 1 });
  drawWords(k, sf, W_(k, 4, [7, 8]), 104, 668, FONT.nim, 32, { color: INK.dark, space: 9 });
  drawWords(k, sf, W_(k, 4, [9, 10]), 104, 708, FONT.nim, 32, { color: INK.dark, space: 9 });
  if (shown(k, 32.934)) {
    setFont(sf, FONT.mono, 12, 1.4); sf.fillStyle = 'rgba(23,25,28,0.8)';
    sf.fillText('SOURCE · BUS-SHELTER AD · SF STANDARD · SEP 2 2026', 104, 880);
  }
  sf.restore();
  // the scratch light: runs along the scratch from 35.158 and lands on the 35.283 bar line (emit, plate space), then
  // the struck NOT stays scored
  const e = L.emit.ctx;
  const run = clamp((k.s - 35.158) / (35.2827 - 35.158));
  if (notA >= 0) {
    e.save();
    srcTransform(e, size, v);
    const n = SCRATCH.length - 1, upto = run * n;
    e.lineCap = 'round';
    for (const [wd, col] of [[9, 'rgba(255,214,150,0.22)'], [3.2, 'rgba(255,236,200,0.85)'], [1.2, 'rgba(255,255,255,1)']]) {
      e.strokeStyle = col; e.lineWidth = wd; e.beginPath();
      e.moveTo(...SCRATCH[0]);
      for (let i = 1; i <= Math.ceil(upto); i++) {
        const f = Math.min(1, upto - (i - 1));
        e.lineTo(lerp(SCRATCH[i - 1][0], SCRATCH[i][0], f), lerp(SCRATCH[i - 1][1], SCRATCH[i][1], f));
      }
      e.stroke();
    }
    const fade = run >= 1 ? Math.exp(-Math.max(0, k.s - 35.2827) / 0.5) : 1;
    const i = Math.min(n - 1, Math.floor(upto)), f = upto - i;
    const hx = lerp(SCRATCH[i][0], SCRATCH[i + 1][0], Math.min(1, f)), hy = lerp(SCRATCH[i][1], SCRATCH[i + 1][1], Math.min(1, f));
    const g = e.createRadialGradient(hx, hy, 0, hx, hy, 34);
    g.addColorStop(0, `rgba(255,240,215,${0.9 * fade})`); g.addColorStop(1, 'rgba(255,240,215,0)');
    e.fillStyle = g; e.beginPath(); e.arc(hx, hy, 34, 0, Math.PI * 2); e.fill();
    e.restore();
  }
  // "That's me." confirmed on her: the classifier's third row, a detector box on her head and shoulders
  const o = L.overlay.ctx;
  const ca = since(k, 32.007);
  if (ca >= 0 && k.s < 33.4367) {
    const [x0, y0] = fwd(size, vb, 930, 70), [x1, y1] = fwd(size, vb, 1190, 390);
    brackets(o, x0, y0, x1, y1, ca, { color: INK.amber, arm: 22 });
    micro(o, 'AI = AVERAGE INDIVIDUAL', x0 - 16, y0 + 40, { size: 12, track: 2, color: 'rgba(240,236,228,0.85)', align: 'right' });
    const me = shown(k, 32.289);
    setFont(o, FONT.monoS, 18, 2); o.fillStyle = INK.amber; o.textAlign = 'right';
    o.fillText(me ? "THAT'S ME · CONFIRMED" : "THAT'S", x0 - 16, y0 + 66); o.textAlign = 'left';
    k.mark(3, 4); if (me) k.mark(3, 5);
  }
  subtitle(k, o, 3, 32.369 + 0.4);
  return {
    A: { tex: 'p009-bg', view: v, lod: lerp(1.5, 0.0, rack) },
    B: { tex: 'p009-fg', view: vb, lod: lerp(0.0, 0.9, rack) },
    key: [0.6, 0.8],
  };
}

// ---------------------------------------------------------------- s010 freeway (MO05)
function s010(k) {
  const kickA = k.s - 38.9399;
  const sh = kickA >= 0 && kickA < 0.3 ? [Math.sin(kickA * 90) * 7 * Math.exp(-kickA / 0.08), Math.cos(kickA * 70) * 4 * Math.exp(-kickA / 0.08)] : [0, 0];
  const v = [1152, 648, 1.0 + 0.025 * clamp((k.s - 36.1999) / 4.6), 0];
  const L = k.layers;
  const f = L.feed.ctx, o = L.overlay.ctx;
  const out = shown(k, 39.897);
  if (!out) {
    // coverline: "Freeway:" over the night sky above the billboard, the graffiti typed into a spell-check field
    // anchored on the billboard (board ui.spellcheck), "The D? Forgot." under it
    const [bx, by] = fwd([2304, 1296], v, 0.19 * 2304, 0.36 * 1296, sh);
    drawWords(k, f, W_(k, 5, [0]), 500, 176, FONT.nim, 40, { color: INK.warm, shadow: SHADOW });
    const fa = since(k, 37.226);
    if (fa >= 0) {
      leader(o, [bx, by], [500, 282], fa, { color: 'rgba(242,177,52,0.85)' });
      brackets(o, 0.105 * 1920 - 6, 0.355 * 1080, 0.195 * 1920 + 6, 0.445 * 1080, fa, { color: INK.amber, arm: 9 });
      const e = easeOutCubic(clamp((fa + 1) / 3));
      o.save(); o.globalAlpha = e;
      o.fillStyle = 'rgba(244,241,234,0.94)'; o.beginPath(); o.roundRect(500, 196, 620, 86, 6); o.fill();
      o.restore();
      // the field's words, caps as sprayed: SF HATES AI BILLBOARS!!!
      const ws = W_(k, 5, [1, 2, 3, 4, 5, 6]);
      const toks = [{ w: [ws[0], ws[1]], t: 'SF' }, { w: [ws[2]], t: 'HATES' }, { w: [ws[3], ws[4]], t: 'AI' }, { w: [ws[5]], t: 'BILLBOARS!!!' }];
      setFont(o, FONT.nim, 44, 0.5);
      let x = 524;
      let sq = null;
      for (const tk of toks) {
        const vis = tk.w.filter(w => shown(k, w.start));
        if (vis.length) {
          const txt = tk.t === 'SF' && vis.length === 1 ? 'S' : tk.t === 'AI' && vis.length === 1 ? 'A' : tk.t;
          o.fillStyle = INK.dark; o.fillText(txt, x, 256);
          vis.forEach(w => k.mark(w.li, w.wi));
        }
        const tw = o.measureText(tk.t).width;
        if (tk.t.startsWith('BILL')) sq = [x, x + o.measureText('BILLBOARS').width];
        x += tw + 16;
      }
      // the squiggle under BILLBOARS once the word is written; suggestion on "The", IGNORE taken on "Forgot."
      if (sq && shown(k, 38.69)) {
        o.save(); o.strokeStyle = INK.amber; o.lineWidth = 2.5; o.beginPath();
        for (let xx = sq[0]; xx <= sq[1]; xx += 2) o.lineTo(xx, 266 + Math.sin((xx - sq[0]) / 3.2) * 2.6);
        o.stroke(); o.restore();
      }
      const pa = since(k, 38.751), ig = since(k, 39.674);
      if (pa >= 0 && (ig < 3)) {
        const e2 = easeOutCubic(clamp((pa + 1) / 3));
        const px = sq ? sq[0] : 700;
        o.save(); o.globalAlpha = e2;
        o.shadowColor = 'rgba(0,0,0,0.4)'; o.shadowBlur = 18; o.shadowOffsetY = 6;
        o.fillStyle = 'rgba(250,248,243,0.97)'; o.beginPath(); o.roundRect(px, 290, 290, 132, 6); o.fill();
        o.shadowColor = 'transparent';
        setFont(o, FONT.nim, 30, 0); o.fillStyle = INK.dark; o.fillText('billboards?', px + 18, 332);
        hairline(o, px + 12, 348.5, px + 278, 348.5, 'rgba(23,25,28,0.25)');
        if (ig >= 0) { o.fillStyle = 'rgba(242,177,52,0.9)'; o.fillRect(px + 6, 354, 278, 32); }
        setFont(o, FONT.monoS, 15, 2); o.fillStyle = INK.dark; o.fillText('IGNORE', px + 18, 376);
        setFont(o, FONT.mono, 13, 1.4); o.fillStyle = 'rgba(23,25,28,0.6)'; o.fillText('ADD TO DICTIONARY', px + 18, 408);
        o.restore();
      }
      micro(o, 'GRAFFITI ON AN AI-RECEPTIONIST BILLBOARD · US-101 NEAR POTRERO HILL · SF STANDARD · SEP 2 2026', 500, 304,
        { size: 10, track: 1.3, color: 'rgba(236,232,222,0.72)' });
    }
  } else {
    // masthead.in: ALL lands early on 39.897 and is held across the cut (board s010)
    micro(f, 'RUNWAY ONE · LOOK 01 · SCULPTURAL WHITE', 116, 222, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
    slamWord(k, f, 'ALL', 39.897, 108, 480, 340, { marks: [[6, 0]] });
    monoLine(k, o, 6);
  }
  // "The D? Forgot." under the suggestion, held 0.4 s past its last word (over the ALL that lands at 39.897)
  if (k.s < 40.055 + 0.4) drawWords(k, f, W_(k, 5, [7, 8, 9]), 610, 470, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, space: 14 });
  return { A: { tex: 'seq', view: v, lod: 0.0 }, shake: sh };
}

// ---------------------------------------------------------------- s011 runway, lights row by row (p011, 2.5D)
function s011(k) {
  const size = [1672, 941];
  const anchor = [1060, 560];
  const p = beatSteps(k, 40.7859, 44.9422, 0.4);
  const v = clampView(size, [lerp(900, 990, p), lerp(470, 455, p), lerp(1.0, 1.08, p), 0]);
  const vb = parallax(v, anchor, 0.15, 1.1);
  // her walk: a small lift on every beat (the shoulders' bob)
  const bp = k.beatIndexFloat(k.s) % 1;
  vb[1] += Math.abs(Math.sin(bp * Math.PI)) * 2.2 - 1.1;
  // the rows snap on far -> near, one per sixteenth from the 40.786 hit
  const six = k.sixteenthLen(40.7859);
  const gains = [0, 1, 2, 3].map(b => (shown(k, 40.7859 + b * six) ? 1 : 0));
  const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
  const L = k.layers;
  const fb = L.feedBack.ctx, o = L.overlay.ctx;
  // masthead: one word a picture on its accent (ALL carried in from the cut, HANDS!, ALL, NIGHT!), then EVERYBODY,
  micro(fb, 'RUNWAY ONE · LOOK 01 · SCULPTURAL WHITE', 116, 222, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
  const words = [['ALL', 39.897, [6, 0]], ['HANDS!', 40.861, [6, 1]], ['ALL', 42.247, [6, 2]], ['NIGHT!', 42.769, [6, 3]],
    ['EVERYBODY,', 44.077, [7, 0]]];
  let cur = null;
  for (const w of words) if (shown(k, w[1])) cur = w;
  if (cur) {
    const size0 = cur[0] === 'EVERYBODY,' ? 236 : 340;
    slamWord(k, fb, cur[0], cur[1], 108, 480, size0, { marks: [cur[2]] });
  }
  monoLine(k, o, 6, { until: 44.0 });
  if (shown(k, 44.077)) drawWords(k, o, W_(k, 7, [0]), 72, H - 46, FONT.mono, 21, { track: 7, upper: true, pop: false,
    color: 'rgba(242,238,230,0.9)', shadow: { color: 'rgba(0,0,0,0.6)', blur: 10 } });
  // the gauge on the pillar's painted level sign: ON CALL, DUSK -> DAWN, full on "night!" (ALL NIGHT)
  const f = L.feed.ctx;
  const [px, py] = fwd(size, v, 1466, 372);
  const [gx, gy] = fwd(size, v, 1330, 262);
  const ga = since(k, 42.247);
  if (ga >= 0) {
    const sc = fitOf(size) * v[2];
    f.save(); f.globalAlpha = 0.85;
    setFont(f, FONT.din, 40 * sc, 0); f.fillStyle = 'rgba(232,228,218,0.8)'; f.textAlign = 'center'; f.fillText('B2', px, py);
    f.restore();
    leader(o, [px, py - 40 * sc], [gx + 40, gy + 46], ga, { color: 'rgba(236,232,222,0.7)' });
    f.save(); f.globalAlpha = easeOutCubic(clamp((ga + 1) / 3)) * 0.42; f.fillStyle = '#000';
    f.beginPath(); f.arc(gx, gy, 132, 0, Math.PI * 2); f.filter = 'blur(18px)'; f.fill(); f.restore();
  }
  gauge(k, f, gx, gy, 84, { at: 42.247, full: 43.854, label: 'ON CALL', from: 'DUSK', to: 'DAWN', fill: 'ALL NIGHT' });
  return {
    A: { tex: 'p011-bg', view: v, lod: 0.15 },
    B: { tex: 'p011-fg', view: vb, lod: 0.0 },
    rows: { gain: gains, ambient: amb, dark: 0.1 },
  };
}

// ---------------------------------------------------------------- s012 front row (SG03, lip sync)
function s012(k) {
  const push = easeInOutCubic(clamp((k.s - 48.1698) / 0.42));
  const v = [lerp(1152, 1300, push), lerp(648, 560, push), 1.0 + 0.04 * push, 0];
  const L = k.layers;
  const f = L.feed.ctx, o = L.overlay.ctx;
  // mass: small lead-in row above one big line, left third over the dark ceiling
  if (k.s < 47.517 - 0.06) {
    drawWords(k, f, W_(k, 7, [0]), 480, 112, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, pop: false });
    drawWords(k, f, W_(k, 7, [1, 2]), 474, 246, FONT.din, 124, { upper: true, color: INK.warm, space: 30,
      shadow: { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 } });
    drawWords(k, f, W_(k, 7, [3]), 474, 364, FONT.din, 124, { upper: true, color: INK.warm,
      shadow: { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 } });
  } else {
    drawWords(k, f, W_(k, 8, [0, 1]), 480, 112, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, space: 12 });
    drawWords(k, f, W_(k, 8, [2]), 474, 246, FONT.din, 112, { upper: true, color: INK.warm, shadow: { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 } });
    drawWords(k, f, W_(k, 8, [3, 4]), 474, 360, FONT.din, 112, { upper: true, color: INK.warm, space: 30,
      shadow: { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 } });
  }
  // the front row classifier (board, 45.625), then the engineer's night (hypnogram, drops to AWAKE on "you're")
  const lap = fwd([2304, 1296], v, 0.37 * 2304, 0.77 * 1296);
  if (k.s < 47.517) {
    const a = since(k, 45.625);
    brackets(o, ...fwd([2304, 1296], v, 0.02 * 2304, 0.5 * 1296), ...fwd([2304, 1296], v, 0.42 * 2304, 0.99 * 1296), a, { arm: 22 });
    leader(o, lap, [1170, 742], a, { color: 'rgba(236,232,222,0.8)' });
    const six = k.sixteenthLen(45.625);
    classifier(k, o, 1170, 712, [
      { k: 'HOLDING ON', v: 'YES', at: 45.625 },
      { k: 'HOLDING ON', v: 'YES', at: 45.625 + six },
      { k: 'HOLDING ON', v: 'WHITE-KNUCKLED', at: 45.625 + 2 * six, hot: true },
    ], { title: 'FRONT ROW · CLASSIFIER', width: 440, accent: INK.bone });
  } else {
    leader(o, lap, [1170, 742], since(k, 47.517), { color: 'rgba(236,232,222,0.8)' });
    hypnogram(k, o, 1170, 712, { t0: 47.517, drop: 49.307, w: 440, h: 150 });
  }
  return { A: { tex: 'seq', view: v, lod: 0.0 } };
}

// ---------------------------------------------------------------- s013 the call (p013, 2.5D cutaway)
// Cut away from her mouth (no take for the sung line): the frame holds her hands, the phone and the engineer's
// reaching hand below her chin; the camera drifts across on the beats, punches in on "call" and the phone's light
// pulses on the 53.708 bar line.
function s013(k) {
  const size = [1672, 941];
  const anchor = [900, 760];
  const p = beatSteps(k, 50.933, 55.0777, 0.4);
  const punch = easeOutCubic(clamp((k.s - 51.76) / 0.18));
  // her mouth is at plate (1210, 500): the window stays left of x 1180 (and her layer, pushed by parallax, further)
  const z = 2.0 + 0.08 * punch + 0.05 * p;
  const v = clampView(size, [lerp(690, 760, p), 700, z, lerp(-0.03, 0.015, p)]);
  const vb = parallax(v, anchor, 0.22, 0.4);
  const L = k.layers;
  const f = L.feed.ctx, o = L.overlay.ctx;
  // mass line 9 upper left; masthead line 10 lower left
  if (k.s < 54.187 + 0.35) {
    drawWords(k, f, W_(k, 9, [0, 1]), 80, 262, FONT.nim, 42, { color: INK.warm, shadow: SHADOW, space: 12 });
    drawWords(k, f, W_(k, 9, [2]), 74, 470, FONT.din, 210, { upper: true, color: INK.warm, shadow: { color: 'rgba(0,0,0,0.5)', blur: 22, dy: 7 } });
    drawWords(k, f, W_(k, 9, [3, 4, 5, 6]), 78, 600, FONT.din, 120, { upper: true, color: INK.warm, space: 28,
      shadow: { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 } });
  }
  const mw = [['ALL', 53.767, [10, 0]], ['HANDS!', 54.59, [10, 1]]];
  let cur = null;
  for (const w of mw) if (shown(k, w[1])) cur = w;
  monoLine(k, o, 10, { from: 53.767 - 0.03 });
  if (cur) {
    micro(f, 'RUNWAY ONE · LOOK 01 · SCULPTURAL WHITE', 84, 726, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
    slamWord(k, f, cur[0], cur[1], 74, 1000, 300, { marks: [cur[2]] });
  }
  // the incoming call (board ui.call on the phone screen; the screen faces her, so its face is lifted out beside it)
  const ph = fwd(size, vb, 1030, 845);
  const ca = since(k, 51.76);
  leader(o, ph, [1420, 600], ca, { color: 'rgba(236,232,222,0.8)' });
  callScreen(k, o, 1420, 250, { at: 51.76, takeAt: 53.645, flashAt: 53.708, caller: 'INCOMING CALL', label: 'INCOMING · SEV-HIGH',
    decline: 'DECLINE · DISABLED' });
  // the phone's light on the bar line (emit, soft and local)
  const fl = since(k, 53.708);
  const e = L.emit.ctx;
  const glow = 0.35 + (fl >= 0 ? 1.4 * Math.exp(-fl / 3) : 0);
  const g = e.createRadialGradient(ph[0], ph[1], 0, ph[0], ph[1], 260);
  g.addColorStop(0, `rgba(200,220,255,${0.55 * glow})`); g.addColorStop(0.35, `rgba(170,195,240,${0.18 * glow})`); g.addColorStop(1, 'rgba(160,190,240,0)');
  e.fillStyle = g; e.beginPath(); e.arc(ph[0], ph[1], 260, 0, Math.PI * 2); e.fill();
  return {
    A: { tex: 'p013-bg', view: v, lod: 0.9 },
    B: { tex: 'p013-fg', view: vb, lod: 0.1 },
  };
}

// ---------------------------------------------------------------- s014 the turn, the pager (p014, 2.5D)
// The camera arcs past her (the room slides one way, she the other) so the frontal still turns into an angle; a
// punch on the 55.542 bar line where she turns; on "Ten" (58.726) it pushes in on the pager at her belt and its LCD
// reads 10:02:11.
const PAGER = [997, 435];
function s014(k) {
  const size = [1672, 941];
  const anchor = [990, 470];
  const p = beatSteps(k, 55.0777, 58.726, 0.45);
  const tp = k.s - 55.542;
  const punch = tp >= 0 ? 0.05 * Math.exp(-tp / 0.12) * (tp < 0.05 ? tp / 0.05 : 1) : 0;
  const crash = easeInOutCubic(clamp((k.s - 58.726) / 0.21));
  let v = [lerp(1060, 880, p), lerp(470, 480, p), 1.06 + punch + 0.03 * p, lerp(0.02, -0.015, p)];
  v = [lerp(v[0], PAGER[0] + 60, crash), lerp(v[1], PAGER[1] - 20, crash), lerp(v[2], 1.85, crash), lerp(v[3], -0.03, crash)];
  v = clampView(size, v);
  const vb = parallax(v, anchor, -0.18, 0.25);
  const L = k.layers;
  const fb = L.feedBack.ctx, f = L.feed.ctx, o = L.overlay.ctx;
  const mw = [['ALL', 55.152, [10, 2]], ['NIGHT!', 55.513, [10, 3]]];
  let cur = null;
  for (const w of mw) if (shown(k, w[1])) cur = w;
  if (k.s < 55.152) cur = ['HANDS!', 54.59, [10, 1]];
  if (cur && k.s < 58.6) {
    micro(fb, 'RUNWAY ONE · LOOK 01 · SCULPTURAL WHITE', 116, 222, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
    slamWord(k, fb, cur[0], cur[1], 108, 480, 340, { marks: [cur[2]] });
  }
  monoLine(k, o, 10, { until: 58.6 });
  // the pager stack piles up on the sixteenths while the long "night!" holds (top right, no digits)
  pagerStack(k, o, W - 60, 300, { from: 55.0777, to: 58.726, label: 'PAGED' });
  // Ten oh two: the mass line, the pager's own LCD and its readout (board s015 device, at 58.726)
  if (shown(k, 58.726)) {
    drawWords(k, f, W_(k, 11), 80, 440, FONT.din, 200, { upper: true, color: INK.warm, space: 40,
      shadow: { color: 'rgba(0,0,0,0.55)', blur: 22, dy: 7 } });
    const [lx, ly] = fwd(size, vb, PAGER[0], PAGER[1]);
    const sc = fitOf(size) * vb[2];
    f.save();
    f.translate(lx, ly); f.rotate(vb[3] - 0.02);
    setFont(f, FONT.monoS, 8.5 * sc, 0.3 * sc); f.fillStyle = 'rgba(28,34,25,0.92)'; f.textAlign = 'center';
    f.fillText('10:02', 0, 3.2 * sc);
    f.restore();
    const e = L.emit.ctx;
    const g = e.createRadialGradient(lx, ly, 0, lx, ly, 22 * sc);
    g.addColorStop(0, 'rgba(170,190,150,0.35)'); g.addColorStop(1, 'rgba(170,190,150,0)');
    e.fillStyle = g; e.beginPath(); e.arc(lx, ly, 22 * sc, 0, Math.PI * 2); e.fill();
    leader(o, [lx + 22 * sc, ly], [1380, 640], since(k, 58.726));
    lcdCard(k, o, 1380, 560, { at: 58.726, text: '10:02:11', label: 'P0 ALERT RAISED',
      source: 'SOURCE · OPENAI ALIGNMENT REPORT · SEP 20 2026 (UPDATED SEP 25) · NO TIME ZONE GIVEN' });
  }
  return {
    A: { tex: 'p014-bg', view: v, lod: 0.35 },
    B: { tex: 'p014-fg', view: vb, lod: 0.0 },
  };
}

export const SHOT_FN = { s007, s008, s009, s010, s011, s012, s013, s014 };
