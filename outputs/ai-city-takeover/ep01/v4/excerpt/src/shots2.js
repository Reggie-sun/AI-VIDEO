// v2/v3 (2026-11-18): the excerpt cut from the flash-snapshot stills only, the author's `still` tier (wiki_storyboard
// "What moves, and what it costs": a plate moved in code - crops landing on beats, stills swapped on the beat). Each
// shot is one still, or two swapped on a beat/bar line (k.shot.stills); its camera is a list of hard crops, each taking
// effect on its own beat (no easing, no slow zoom), plus a slight handheld drift (deterministic noise, about 2 px).
// The type and the explaining graphics sit in the photograph's planned empty third; the photograph stays dominant.
// v3 keeps v2's edit (cuts, swaps, crop beats, timing, type, chrome, grade) on the stills remade in wardrobe W1; only
// the geometry differs: GEO[2] / GEO[3] hold every place read off each still (plate px) and every screen place that
// depends on the composition.
import { clamp, easeOutCubic, lerp, noise1 } from '../../../../../../motion-kit/src/math.js';
import { brackets, callScreen, classifier, gauge, hairline, hypnogram, lcdCard, leader, pagerStack, tagLabel } from './devices.js';
import { W_, clampView, fwd, monoLine, srcTransform, subtitle } from './shots.js';
import { FONT, INK, drawWords, micro, setFont, shown, since, slamWord } from './type.js';

const W = 1920, H = 1080;
const SZ = [1672, 941];
const SHADOW = { color: 'rgba(0,0,0,0.55)', blur: 18, dy: 2 };
const BIG_SH = { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 };

const GEO = {
  2: {
    look: 'RUNWAY ONE · LOOK 01 · SCULPTURAL WHITE',
    s007: { crops: [[26.0528, 836, 470, 1.0, 0], [27.8872, 720, 360, 1.15, -0.008]], text: [120, 290, -0.2, 34, 46], branch: [1300, 140], key: [0.72, 0.86] },
    s008: { crops: [[29.7448, 836, 470, 1.0, 0], [30.662, 1000, 560, 1.22, 0.012]], tag: [1137, 756, 1388, 874], ai: [1262, 828, 46], panel: [1480, 400], lead: [1500, 560] },
    s009: {
      crops: [[31.1263, 836, 470, 1.0, 0], [33.4367, 1029, 380, 1.3, -0.01], [35.2827, 836, 470, 1.0, 0.01], [35.7355, 700, 400, 1.18, -0.006]],
      busStop: [1456, 120, 28], X0: 1452, rows: [210, 320, 420, 520, 620], size: 84, tail: [690, 722, 25], source: [880, 896],
      scratchA: [[1572, 234], [1530, 270], [1490, 303], [1452, 334], [1421, 360]],
      scratchB: [[67, 151], [140, 237], [215, 325], [290, 413], [360, 496]], not: [96, 380, 150], face: [690, 90, 960, 430], key: [0.6, 0.78],
    },
    s010: {
      crops: [[36.1999, 836, 470, 1.0, 0], [37.0939, 643, 400, 1.3, 0.012], [38.9399, 760, 420, 1.12, -0.01], [39.8454, 836, 470, 1.0, 0]],
      bill: [209, 286, 502, 487], freeway: [80, 220], field: [80, 240], popup: [696, 240], forgot: [680, 424], micro: [80, 348],
    },
    s011: { crops: [[40.7859, 836, 470, 1.0, 0], [42.6318, 836, 430, 1.12, -0.008], [44.0134, 635, 294, 1.5, 0.01]], gauge: [1330, 210], size: 250, rows: 'X11a-rows' },
    s012: {
      crops: [[44.9422, 836, 470, 1.0, 0], [46.3238, 836, 430, 1.1, -0.01], [48.1698, 900, 470, 1.0, 0.0], [50.0158, 900, 380, 1.14, 0.01]],
      massX: 1414, lap: [560, 540], b: [68, 262, 392, 514],
    },
    s013: {
      crops: [[50.933, 836, 470, 1.0, 0], [51.8502, 850, 400, 1.3, 0.01], [53.7078, 836, 470, 1.06, -0.005]],
      mass: [1244, 140, 330, 440], phone: [860, 525], card: [1500, 540],
    },
    s014: { crops: [[55.0777, 836, 470, 1.0, 0], [55.5421, 836, 440, 1.1, 0.01], [57.3765, 880, 380, 1.28, -0.01], [58.7697, 886, 380, 2.1, -0.02]],
      lcd: [886, 336, 0.1], night: [106, 236, 450, 230], ten: 360 },
  },
  3: {
    look: 'RUNWAY ONE · LOOK W1 · ON-CALL HOODIE COUTURE',
    // X07a: the billboard is smaller (x 0-550, its lower edge rising 12 deg to the right); the branch at (1270, 150)
    s007: { crops: [[26.0528, 836, 470, 1.0, 0], [27.8872, 700, 360, 1.15, -0.008]], text: [60, 230, -0.21, 30, 40], branch: [1300, 170], key: [0.72, 0.86] },
    // X08a: the blank name badge on her chest (1102-1210, 572-636), under her thumb; the dark city top right
    s008: { crops: [[29.7448, 836, 470, 1.0, 0], [30.662, 1150, 500, 1.22, 0.012]], tag: [1102, 572, 1210, 636], ai: [1170, 618, 32], panel: [1480, 120], lead: [1520, 250] },
    // X09a: the scratch from (1590, 150) to her nail at (1386, 289); glass from x 1300; X09b: scratch (20, 460) -> nail (395, 610)
    s009: {
      crops: [[31.1263, 836, 470, 1.0, 0], [33.4367, 1029, 362, 1.3, -0.01], [35.2827, 836, 470, 1.0, 0.01], [35.7355, 708, 470, 1.18, -0.006]],
      busStop: [1346, 140, 21], X0: 1440, rows: [140, 235, 335, 430, 525], size: 84, tail: [600, 632, 25], source: [880, 896],
      scratchA: [[1590, 150], [1543, 156], [1507, 179], [1450, 214], [1386, 289]],
      scratchB: [[20, 460], [115, 498], [210, 536], [305, 574], [395, 610]], not: [56, 560, 150], face: [640, 20, 940, 300], key: [0.6, 0.78],
    },
    // X10a: the graffiti billboard at (50-326, 318-485), her head at (736-1037, 100-335)
    s010: {
      crops: [[36.1999, 836, 470, 1.0, 0], [37.0939, 643, 400, 1.3, 0.012], [38.9399, 760, 420, 1.12, -0.01], [39.8454, 836, 470, 1.0, 0]],
      bill: [50, 318, 326, 485], freeway: [80, 232], field: [80, 246], popup: [500, 342], forgot: [500, 520], micro: [80, 352],
    },
    s011: { crops: [[40.7859, 836, 470, 1.0, 0], [42.6318, 836, 430, 1.12, -0.008], [44.0134, 635, 294, 1.5, 0.01]], gauge: [1330, 230], size: 230, rows: 'X11a-w1-rows' },
    s012: {
      crops: [[44.9422, 836, 470, 1.0, 0], [46.3238, 836, 430, 1.1, -0.01], [48.1698, 900, 470, 1.0, 0.0], [50.0158, 900, 380, 1.14, 0.01]],
      massX: 1520, lap: [450, 540], b: [68, 262, 392, 514],
    },
    s013: {
      crops: [[50.933, 836, 470, 1.0, 0], [51.8502, 800, 400, 1.3, 0.01], [53.7078, 836, 470, 1.06, -0.005]],
      mass: [1244, 120, 300, 400], phone: [720, 500], card: [1500, 540],
    },
    s014: { crops: [[55.0777, 836, 470, 1.0, 0], [55.5421, 836, 440, 1.1, 0.01], [57.3765, 880, 380, 1.28, -0.01], [58.7697, 902, 470, 2.1, -0.02]],
      lcd: [902, 498, -0.08], night: [470, 196, 380, 230], ten: 360 },
  },
};
const G = k => GEO[k.version >= 3 ? 3 : k.version] || GEO[2];       // v4 rounds reuse v3's W1 geometry

// the still on screen and its crop: plan = [[t, cx, cy, zoom, rot], ...] (plate px), each a hard cut on its time
function frameOf(k, plan, seed) {
  let still = k.shot.stills[0][0];
  for (const [key, at] of k.shot.stills) if (shown(k, at)) still = key;
  let c = plan[0];
  for (const p of plan) if (shown(k, p[0])) c = p;
  const v = clampView(SZ, [c[1], c[2], c[3], c[4]]);
  const t = k.s;
  const shake = [noise1(t * 0.9, seed) * 2.2, noise1(t * 0.8, seed + 7) * 1.6];
  v[3] += noise1(t * 0.6, seed + 13) * 0.0012;
  return { still, v, shake };
}
const P = (fr, x, y) => fwd(SZ, fr.v, x, y, fr.shake);
const plateCtx = (ctx, fr) => srcTransform(ctx, SZ, fr.v, fr.shake);
const out = (fr, extra = {}) => ({ A: { tex: fr.still, view: fr.v, lod: 0 }, shake: fr.shake, ...extra });

// ---------------------------------------------------------------- s007: the billboard behind the tree
function s007(k) {
  const g = G(k).s007;
  const fr = frameOf(k, g.crops, 1);
  const L = k.layers;
  // coverline printed on the billboard's lit face, along its perspective; keyed to the lit face, so the leaves cover it
  const sf = L.surf.ctx;
  const [tx0, ty0, rot, fs, lh] = g.text;
  sf.save();
  plateCtx(sf, fr);
  sf.translate(tx0, ty0); sf.rotate(rot);
  const l2 = W_(k, 2), l3 = W_(k, 3);
  drawWords(k, sf, l2.slice(0, 4), 0, 0, FONT.nim, fs, { color: INK.dark, space: fs * 0.3 });
  drawWords(k, sf, l2.slice(4), 0, lh, FONT.nim, fs, { color: INK.dark, space: fs * 0.3 });
  drawWords(k, sf, l3.slice(0, 4), 0, 2 * lh, FONT.nim, fs, { color: INK.dark, space: fs * 0.3 });
  sf.restore();
  // the label hung from the branch she pulls down: $6,000 / MONTH on "grand"
  const o = L.overlay.ctx;
  const a = since(k, 26.293);
  if (a >= 0) {
    const [bx, by] = P(fr, g.branch[0], g.branch[1]);
    const tx = Math.min(W - 340, bx + 50), ty = by + 110;
    o.save(); o.strokeStyle = 'rgba(236,232,222,0.8)'; o.lineWidth = 1;
    o.beginPath(); o.moveTo(bx, by); o.lineTo(tx + 150, ty + 12); o.stroke(); o.restore();
    tagLabel(o, tx, ty, a, { tag: '$6,000 / MONTH', sub: 'PARTIALLY OBSCURED BY A TREE', source: 'SOURCE · SF STANDARD · AUG 4 2026', rot: 0.04 });
  }
  return out(fr, { key: g.key });
}

// ---------------------------------------------------------------- s008: the name sticker
function s008(k) {
  const g = G(k).s008;
  const fr = frameOf(k, g.crops, 2);
  const L = k.layers;
  // the classifier drawn from the blank sticker: A.I. printed on it, rows on the beat in the dark street top right
  const f = L.feed.ctx;
  f.save(); plateCtx(f, fr);
  f.translate(g.ai[0], g.ai[1]); f.rotate(-0.03);
  setFont(f, FONT.nim, g.ai[2], 0); f.fillStyle = 'rgba(23,25,28,0.9)'; f.textAlign = 'center'; f.fillText('A.I.', 0, 0);
  setFont(f, FONT.mono, g.ai[2] * 0.24, 1.4); f.fillText('AVERAGE INDIVIDUAL', 0, g.ai[2] * 0.48);
  f.restore();
  const o = L.overlay.ctx;
  const [x0, y0] = P(fr, g.tag[0], g.tag[1]), [x1, y1] = P(fr, g.tag[2], g.tag[3]);
  brackets(o, x0 - 6, y0 - 6, x1 + 6, y1 + 6, since(k, 29.7448), { color: INK.amber });
  leader(o, [x1 + 6, y0 - 6], g.lead, since(k, 29.7448), { dot: false, color: 'rgba(242,177,52,0.85)' });
  classifier(k, o, g.panel[0], g.panel[1], [
    { k: 'AI', v: 'DETECTED', at: 29.7448 },
    { k: 'AI = AVERAGE INDIVIDUAL', v: 'MATCH', at: 30.238, hot: true },
  ], { title: 'CLASSIFIER · NAME TAG', width: 400, source: 'CHATTJB BILLBOARD · 6TH & FOLSOM · SF STANDARD · AUG 4 2026' });
  subtitle(k, o, 3, 99);
  return out(fr);
}

// ---------------------------------------------------------------- s009: the bus shelter, the scratch
function strokePath(e, pts, upto, widths) {
  const n = pts.length - 1, u = upto * n;
  for (const [wd, col] of widths) {
    e.strokeStyle = col; e.lineWidth = wd; e.lineCap = 'round'; e.beginPath(); e.moveTo(...pts[0]);
    for (let i = 1; i <= Math.ceil(u); i++) {
      const q = Math.min(1, u - (i - 1));
      e.lineTo(lerp(pts[i - 1][0], pts[i][0], q), lerp(pts[i - 1][1], pts[i][1], q));
    }
    e.stroke();
  }
}
function s009(k) {
  const g = G(k).s009;
  const fr = frameOf(k, g.crops, 3);
  const L = k.layers, o = L.overlay.ctx;
  if (fr.still === 'X09a') {
    // the ad as printed on the lightbox glass (right third), keyed to the lit glass so her hand covers it;
    // NOT sits on the real scratch
    const sf = L.surf.ctx;
    sf.save(); plateCtx(sf, fr);
    const [bsx, bsy, bss] = g.busStop, X0 = g.X0, R = g.rows, S = g.size;
    drawWords(k, sf, W_(k, 4, [0, 1]), bsx, bsy, FONT.nim, bss, { color: INK.dark, space: 8 });
    [2, 3, 4, 5, 6].forEach((wi, i) => drawWords(k, sf, W_(k, 4, [wi]), X0, R[i], FONT.din, S, { color: INK.dark, upper: true, track: 1 }));
    drawWords(k, sf, W_(k, 4, [7, 8]), X0 + 2, g.tail[0], FONT.nim, g.tail[2], { color: INK.dark, space: 7 });
    drawWords(k, sf, W_(k, 4, [9, 10]), X0 + 2, g.tail[1], FONT.nim, g.tail[2], { color: INK.dark, space: 7 });
    if (shown(k, 32.934)) {
      setFont(sf, FONT.mono, 10, 1.2); sf.fillStyle = 'rgba(23,25,28,0.8)';
      sf.fillText('SOURCE · BUS-SHELTER AD', X0 + 2, g.source[0]); sf.fillText('SF STANDARD · SEP 2 2026', X0 + 2, g.source[1]);
    }
    sf.restore();
    // "scratched": the light runs down the real scratch to her nail and lands on the 35.283 bar line
    if (shown(k, 35.158)) {
      const e = L.emit.ctx;
      e.save(); plateCtx(e, fr);
      strokePath(e, g.scratchA, clamp((k.s - 35.158) / (35.2827 - 35.158)),
        [[8, 'rgba(255,214,150,0.25)'], [3, 'rgba(255,236,200,0.85)'], [1.1, 'rgba(255,255,255,1)']]);
      e.restore();
    }
    // That's me: the classifier's third row, confirmed on her face
    const ca = since(k, 32.007);
    if (ca >= 0 && k.s < 33.4367) {
      const [bx0, by0] = P(fr, g.face[0], g.face[1]), [bx1, by1] = P(fr, g.face[2], g.face[3]);
      brackets(o, bx0, by0, bx1, by1, ca, { color: INK.amber, arm: 20 });
      const me = shown(k, 32.289);
      micro(o, 'AI = AVERAGE INDIVIDUAL', bx0 - 16, by0 + 40, { size: 12, track: 2, color: 'rgba(240,236,228,0.85)', align: 'right' });
      setFont(o, FONT.monoS, 18, 2); o.fillStyle = INK.amber; o.textAlign = 'right';
      o.fillText(me ? "THAT'S ME · CONFIRMED" : "THAT'S", bx0 - 16, by0 + 66); o.textAlign = 'left';
      k.mark(3, 4); if (me) k.mark(3, 5);
    }
    subtitle(k, o, 3, 32.369 + 0.4);
  } else {
    // the macro: NOT on the glass, struck through by the scratch the light just ran down; the line's last words
    const f = L.feed.ctx;
    f.save(); plateCtx(f, fr);
    setFont(f, FONT.din, g.not[2], 2); f.fillStyle = 'rgba(20,22,25,0.86)'; f.fillText('NOT', g.not[0], g.not[1]);
    f.restore();
    const e = L.emit.ctx;
    e.save(); plateCtx(e, fr);
    const fade = 0.45 + 0.55 * Math.exp(-Math.max(0, k.s - 35.2827) / 0.35);
    strokePath(e, g.scratchB, 1, [[10, `rgba(255,214,150,${0.25 * fade})`], [3.4, `rgba(255,236,200,${0.85 * fade})`], [1.2, `rgba(255,255,255,${fade})`]]);
    e.restore();
    drawWords(k, o, W_(k, 4, [7, 8, 9, 10]), 72, H - 92, FONT.nim, 44, { color: INK.warm, shadow: SHADOW, space: 12 });
    micro(o, 'SOURCE · BUS-SHELTER AD · SF STANDARD · SEP 2 2026', 74, H - 56, { size: 11, track: 1.6 });
  }
  return out(fr, { key: g.key });
}

// ---------------------------------------------------------------- s010: the freeway, the graffiti
function s010(k) {
  const g = G(k).s010;
  const fr = frameOf(k, g.crops, 4);
  const kickA = k.s - 38.9399;
  if (kickA >= 0 && kickA < 0.3) {
    fr.shake[0] += Math.sin(kickA * 90) * 6 * Math.exp(-kickA / 0.08);
    fr.shake[1] += Math.cos(kickA * 70) * 3.5 * Math.exp(-kickA / 0.08);
  }
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  const [fx, fy] = g.field, [px, py] = g.popup;
  if (fr.still === 'X10a') {
    drawWords(k, f, W_(k, 5, [0]), g.freeway[0], g.freeway[1], FONT.nim, 40, { color: INK.warm, shadow: SHADOW });
    const fa = since(k, 37.226);
    if (fa >= 0) {
      // the graffiti on the real billboard, typed into a spell-check field above it in the sky (board ui.spellcheck)
      const [b0x, b0y] = P(fr, g.bill[0], g.bill[1]), [b1x, b1y] = P(fr, g.bill[2], g.bill[3]);
      brackets(o, b0x, b0y, b1x, b1y, fa, { color: INK.amber, arm: 10 });
      leader(o, [(b0x + b1x) / 2, b0y], [fx + 220, fy + 86], fa, { color: 'rgba(242,177,52,0.85)' });
      const e = easeOutCubic(clamp((fa + 1) / 3));
      o.save(); o.globalAlpha = e; o.fillStyle = 'rgba(244,241,234,0.94)'; o.beginPath(); o.roundRect(fx, fy, 600, 86, 6); o.fill(); o.restore();
      const ws = W_(k, 5, [1, 2, 3, 4, 5, 6]);
      const toks = [{ w: [ws[0], ws[1]], t: 'SF' }, { w: [ws[2]], t: 'HATES' }, { w: [ws[3], ws[4]], t: 'AI' }, { w: [ws[5]], t: 'BILLBOARS!!!' }];
      setFont(o, FONT.nim, 40, 0.5);
      let x = fx + 18, sq = null;
      for (const tk of toks) {
        const vis = tk.w.filter(w => shown(k, w.start));
        if (vis.length) {
          const txt = tk.t === 'SF' && vis.length === 1 ? 'S' : tk.t === 'AI' && vis.length === 1 ? 'A' : tk.t;
          o.fillStyle = INK.dark; o.fillText(txt, x, fy + 59);
          vis.forEach(w => k.mark(w.li, w.wi));
        }
        if (tk.t.startsWith('BILL')) sq = [x, x + o.measureText('BILLBOARS').width];
        x += o.measureText(tk.t).width + 15;
      }
      if (sq && shown(k, 38.69)) {
        o.save(); o.strokeStyle = INK.amber; o.lineWidth = 2.5; o.beginPath();
        for (let xx = sq[0]; xx <= sq[1]; xx += 2) o.lineTo(xx, fy + 69 + Math.sin((xx - sq[0]) / 3.2) * 2.6);
        o.stroke(); o.restore();
      }
      const pa = since(k, 38.751), ig = since(k, 39.674);
      if (pa >= 0 && ig < 3) {
        const e2 = easeOutCubic(clamp((pa + 1) / 3));
        o.save(); o.globalAlpha = e2;
        o.shadowColor = 'rgba(0,0,0,0.4)'; o.shadowBlur = 18; o.shadowOffsetY = 6;
        o.fillStyle = 'rgba(250,248,243,0.97)'; o.beginPath(); o.roundRect(px, py, 270, 128, 6); o.fill();
        o.shadowColor = 'transparent';
        setFont(o, FONT.nim, 28, 0); o.fillStyle = INK.dark; o.fillText('billboards?', px + 16, py + 40);
        hairline(o, px + 10, py + 55.5, px + 260, py + 55.5, 'rgba(23,25,28,0.25)');
        if (ig >= 0) { o.fillStyle = 'rgba(242,177,52,0.9)'; o.fillRect(px + 6, py + 61, 258, 30); }
        setFont(o, FONT.monoS, 14, 2); o.fillStyle = INK.dark; o.fillText('IGNORE', px + 16, py + 82);
        setFont(o, FONT.mono, 12, 1.4); o.fillStyle = 'rgba(23,25,28,0.6)'; o.fillText('ADD TO DICTIONARY', px + 16, py + 112);
        o.restore();
      }
      micro(o, 'GRAFFITI ON AN AI-RECEPTIONIST BILLBOARD · US-101 NEAR POTRERO HILL · SF STANDARD · SEP 2 2026', g.micro[0], g.micro[1],
        { size: 9, track: 1.1, color: 'rgba(236,232,222,0.72)' });
    }
  } else {
    // masthead.in: ALL lands early on 39.897 and is held across the cut (board s010)
    micro(f, G(k).look, 106, 236, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
    slamWord(k, f, 'ALL', 39.897, 100, 470, G(k).s011.size, { marks: [[6, 0]] });
    monoLine(k, o, 6);
  }
  if (k.s < 40.055 + 0.4) drawWords(k, f, W_(k, 5, [7, 8, 9]), g.forgot[0], g.forgot[1], FONT.nim, 38, { color: INK.warm, shadow: SHADOW, space: 13 });
  return out(fr);
}

// ---------------------------------------------------------------- s011: runway one, the rows snap on
function s011(k) {
  const g = G(k).s011;
  const fr = frameOf(k, g.crops, 5);
  const six = k.sixteenthLen(40.7859);
  const gains = [0, 1, 2, 3].map(b => (shown(k, 40.7859 + b * six) ? 1 : 0));
  const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  micro(f, G(k).look, 106, 236, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
  const words = [['ALL', 39.897, [6, 0]], ['HANDS!', 40.861, [6, 1]], ['ALL', 42.247, [6, 2]], ['NIGHT!', 42.769, [6, 3]], ['EVERYBODY,', 44.077, [7, 0]]];
  let cur = null;
  for (const w of words) if (shown(k, w[1])) cur = w;
  if (cur) slamWord(k, f, cur[0], cur[1], 100, 470, cur[0] === 'EVERYBODY,' ? 200 : g.size, { marks: [cur[2]] });
  monoLine(k, o, 6, { until: 44.0 });
  if (shown(k, 44.077)) drawWords(k, o, W_(k, 7, [0]), 72, H - 46, FONT.mono, 21, { track: 7, upper: true, pop: false,
    color: 'rgba(242,238,230,0.9)', shadow: { color: 'rgba(0,0,0,0.6)', blur: 10 } });
  // the gauge painted on the ceiling slab right of her, like the garage's level stencils
  const ga = since(k, 42.247);
  if (ga >= 0 && k.s < 44.0134) {
    const [gx, gy] = P(fr, g.gauge[0], g.gauge[1]);
    gauge(k, f, gx, gy, 80, { at: 42.247, full: 43.854, label: 'B2 · ON CALL', from: 'DUSK', to: 'DAWN', fill: 'ALL NIGHT' });
  }
  return out(fr, { rows: { tex: g.rows, gain: gains, ambient: amb, dark: 0.12 } });
}

// ---------------------------------------------------------------- s012: the front row, she sings
function s012(k) {
  const g = G(k).s012;
  const fr = frameOf(k, g.crops, 6);
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  const MX = g.massX;
  if (fr.still === 'X12a') {
    // mass, upper right over the dark garage: lead-in row, then the big line
    if (k.s < 47.517 - 0.06) {
      drawWords(k, f, W_(k, 7, [0]), MX + 6, 128, FONT.nim, 38, { color: INK.warm, shadow: SHADOW, pop: false });
      drawWords(k, f, W_(k, 7, [1, 2]), MX, 252, FONT.din, 116, { upper: true, color: INK.warm, space: 26, shadow: BIG_SH });
      drawWords(k, f, W_(k, 7, [3]), MX, 366, FONT.din, 116, { upper: true, color: INK.warm, shadow: BIG_SH });
    } else {
      drawWords(k, f, W_(k, 8, [0, 1]), MX + 6, 128, FONT.nim, 38, { color: INK.warm, shadow: SHADOW, space: 11 });
    }
    const lap = P(fr, g.lap[0], g.lap[1]);
    if (k.s < 47.517) {
      const a = since(k, 45.625);
      leader(o, lap, [460, 790], a, { color: 'rgba(236,232,222,0.8)' });
      const six = k.sixteenthLen(45.625);
      classifier(k, o, 60, 770, [
        { k: 'HOLDING ON', v: 'YES', at: 45.625 },
        { k: 'HOLDING ON', v: 'YES', at: 45.625 + six },
        { k: 'HOLDING ON', v: 'WHITE-KNUCKLED', at: 45.625 + 2 * six, hot: true },
      ], { title: 'FRONT ROW · CLASSIFIER', width: 400, accent: INK.bone });
    } else {
      leader(o, lap, [420, 790], since(k, 47.517), { color: 'rgba(236,232,222,0.8)' });
      hypnogram(k, o, 60, 770, { t0: 47.517, drop: 49.307, w: 360, h: 120 });
    }
  } else {
    // the close-up: the line in the dark left third, the night's chart small under it
    const [bx, b1, b2, b3] = g.b;
    drawWords(k, f, W_(k, 8, [0, 1]), bx, b1, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, space: 12, pop: false });
    drawWords(k, f, W_(k, 8, [2]), bx - 6, b2, FONT.din, 124, { upper: true, color: INK.warm, shadow: BIG_SH });
    drawWords(k, f, W_(k, 8, [3, 4]), bx - 6, b3, FONT.din, 124, { upper: true, color: INK.warm, space: 26, shadow: BIG_SH });
    hypnogram(k, o, 60, 770, { t0: 47.517, drop: 49.307, w: 360, h: 120 });
  }
  return out(fr);
}

// ---------------------------------------------------------------- s013: the call she takes from him
function s013(k) {
  const g = G(k).s013;
  const fr = frameOf(k, g.crops, 7);
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  const [mx, m1, m2, m3] = g.mass;
  if (k.s < 54.187 + 0.35) {
    drawWords(k, f, W_(k, 9, [0, 1]), mx, m1, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, space: 12 });
    drawWords(k, f, W_(k, 9, [2]), mx - 6, m2, FONT.din, 190, { upper: true, color: INK.warm, shadow: BIG_SH });
    drawWords(k, f, W_(k, 9, [3, 4, 5, 6]), mx - 2, m3, FONT.din, 92, { upper: true, color: INK.warm, space: 22, shadow: BIG_SH });
  }
  const mw = [['ALL', 53.767, [10, 0]], ['HANDS!', 54.59, [10, 1]]];
  let cur = null;
  for (const w of mw) if (shown(k, w[1])) cur = w;
  monoLine(k, o, 10, { from: 53.767 - 0.03 });
  if (cur) {
    micro(f, G(k).look, 70, 790, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
    slamWord(k, f, cur[0], cur[1], 64, 1000, 240, { marks: [cur[2]] });
  }
  // the incoming call (board ui.call; the screen faces her, so its face is lifted out beside the phone)
  const ph = P(fr, g.phone[0], g.phone[1]);
  const ca = since(k, 51.76);
  leader(o, ph, [g.card[0], g.card[1] + 160], ca, { color: 'rgba(236,232,222,0.8)' });
  o.save(); o.translate(g.card[0], g.card[1]); o.scale(0.7, 0.7);
  callScreen(k, o, 0, 0, { at: 51.76, takeAt: 53.645, flashAt: 53.708, caller: 'INCOMING CALL', label: 'INCOMING · SEV-HIGH',
    decline: 'DECLINE · DISABLED' });
  o.restore();
  // the phone's light on the bar line (soft, local)
  const fl = since(k, 53.708);
  const e = L.emit.ctx;
  const glow = 0.25 + (fl >= 0 ? 1.3 * Math.exp(-fl / 3) : 0);
  const gr = e.createRadialGradient(ph[0], ph[1], 0, ph[0], ph[1], 240);
  gr.addColorStop(0, `rgba(200,220,255,${0.5 * glow})`); gr.addColorStop(0.35, `rgba(170,195,240,${0.16 * glow})`); gr.addColorStop(1, 'rgba(160,190,240,0)');
  e.fillStyle = gr; e.beginPath(); e.arc(ph[0], ph[1], 240, 0, Math.PI * 2); e.fill();
  return out(fr);
}

// ---------------------------------------------------------------- s014: the turn, the pager at her waist
function s014(k) {
  const g = G(k).s014;
  const fr = frameOf(k, g.crops, 8);
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  const mw = [['ALL', 55.152, [10, 2]], ['NIGHT!', 55.513, [10, 3]]];
  let cur = k.s < 55.152 ? ['HANDS!', 54.59, [10, 1]] : null;
  for (const w of mw) if (shown(k, w[1])) cur = w;
  const [nmx, nmy, nby, nsz] = g.night;
  if (cur && k.s < 58.6) {
    micro(f, G(k).look, nmx, nmy, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
    slamWord(k, f, cur[0], cur[1], 100, nby, nsz, { marks: [cur[2]] });
  }
  monoLine(k, o, 10, { until: 58.6 });
  pagerStack(k, o, W - 60, 300, { from: 55.0777, to: 58.726, label: 'PAGED' });
  if (shown(k, 58.726)) {
    drawWords(k, f, W_(k, 11), 80, g.ten, FONT.din, 170, { upper: true, color: INK.warm, space: 34, shadow: { color: 'rgba(0,0,0,0.55)', blur: 22, dy: 7 } });
    const [lx, ly] = P(fr, g.lcd[0], g.lcd[1]);
    const sc = 1.148 * fr.v[2];
    f.save(); f.translate(lx, ly); f.rotate(fr.v[3] + g.lcd[2]);
    setFont(f, FONT.monoS, 9 * sc, 0.3 * sc); f.fillStyle = 'rgba(28,34,25,0.92)'; f.textAlign = 'center'; f.fillText('10:02', 0, 3.2 * sc);
    f.restore();
    const e = L.emit.ctx;
    const gr = e.createRadialGradient(lx, ly, 0, lx, ly, 22 * sc);
    gr.addColorStop(0, 'rgba(170,190,150,0.35)'); gr.addColorStop(1, 'rgba(170,190,150,0)');
    e.fillStyle = gr; e.beginPath(); e.arc(lx, ly, 22 * sc, 0, Math.PI * 2); e.fill();
    leader(o, [lx + 20 * sc, ly], [1300, 680], since(k, 58.726));
    lcdCard(k, o, 1300, 600, { at: 58.726, text: '10:02:11', label: 'P0 ALERT RAISED',
      source: 'SOURCE · OPENAI ALIGNMENT REPORT · SEP 20 2026 (UPDATED SEP 25) · NO TIME ZONE GIVEN' });
  }
  return out(fr);
}

export const SHOT_FN_V2 = { s007, s008, s009, s010, s011, s012, s013, s014 };
