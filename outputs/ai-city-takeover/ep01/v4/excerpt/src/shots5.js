// v4 round 2 (2026-11-19): the round-1 review cut (song 36.1999-50.933) rebuilt in the approved design-v2 language
// (console2.js: EV interface grammar under the print layer) and the per-shot plan of
// reviews/2026-11-19-codex-excerpt-gaps-r3.md section 2 (s010-s012). One readable result per line; one lyric line low
// left (the author's subtitle manner, a micro index above it); big chorus words small and toned; amber only where a
// source gives it; red only her ear lamp. s012 now: two inserts (44.942), the SG03-w1 take for the relationship
// (46.788), and on the 48.170 bar line the closed-eye close-up (PLACEHOLDER: the still D1-b, light change only, until
// its clip is made).
import { clamp, easeOutCubic, noise1 } from '../../../../../../motion-kit/src/math.js';
import { AMBER, console2, lyricLow, mono } from './console2.js';
import { W_, clampView, fwd } from './shots.js';
import { FONT, drawWords, setFont, shown, since } from './type.js';

const W = 1920, H = 1080;
const PLATE = [1672, 941], SEQ = [2304, 1296];
const INKD = 'rgba(240,236,228,0.58)';
const PRINT = { uHalftone: 0.085, uCell: 3.0, uGrain: 0.034 };
const fin = ret => ({ ...ret, chrome: false, underPrint: true, grade: { ...PRINT, ...(ret.grade || {}) } });

function still(k) {
  let key = k.shot.stills[0][0];
  for (const [kk, at] of k.shot.stills) if (shown(k, at)) key = kk;
  return key;
}
function crop(k, plan, seed, size = PLATE) {
  let c = plan[0];
  for (const p of plan) if (shown(k, p[0])) c = p;
  const v = clampView(size, [c[1], c[2], c[3], c[4]]);
  const shake = [noise1(k.s * 0.9, seed) * 2.0, noise1(k.s * 0.8, seed + 7) * 1.5];
  return { v, shake };
}
// the chorus's big word: the author's condensed type, toned into the picture (soft shadow, under the print layer)
function bigWord(k, ctx, text, ts, mark, { x = 70, y = 900, size = 112 } = {}) {
  const a = since(k, ts);
  if (a < 0) return;
  const sc = a >= 3 ? 1 : [1.12, 1.04, 1.01][a];
  ctx.save();
  setFont(ctx, FONT.din, size, 1);
  ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.shadowColor = 'rgba(0,0,0,0.38)'; ctx.shadowBlur = 22; ctx.shadowOffsetY = 3;
  ctx.fillStyle = 'rgba(236,230,220,0.86)'; ctx.fillText(text, 0, 0);
  ctx.restore();
  k.mark(...mark);
}
const lyric = (k, o, li, idx, opts = {}) => lyricLow(k, o, W_(k, li), drawWords, { index: idx, y: H - 96, ...opts });

// ---------------------------------------------------------------- s010 X10a -> X10b: the freeway
const BILL = [50, 318, 326, 485];
function s010(k) {
  const key = still(k);
  const { v, shake } = crop(k, [[36.1999, 836, 470, 1.0, 0], [37.0939, 643, 400, 1.3, 0.012], [38.9399, 760, 420, 1.12, -0.01],
    [39.8454, 836, 470, 1.0, 0]], 4);
  const kickA = k.s - 38.9399;
  if (kickA >= 0 && kickA < 0.3) { shake[0] += Math.sin(kickA * 90) * 6 * Math.exp(-kickA / 0.08); shake[1] += Math.cos(kickA * 70) * 3.5 * Math.exp(-kickA / 0.08); }
  const o = k.layers.overlay.ctx;
  console2(k, o, { mode: 'thin', lit: 0, sel: false });
  if (key === 'X10a') {
    // the graffiti read off the billboard once: a hairline bracket on the board, the words as sprayed, the misspelling
    // underlined; on "Forgot." the suggestion is ignored (the result of the line, in the accent)
    const a = since(k, 37.226);
    if (a >= 0) {
      const [x0, y0] = fwd(PLATE, v, BILL[0], BILL[1], shake), [x1, y1] = fwd(PLATE, v, BILL[2], BILL[3], shake);
      o.save(); o.strokeStyle = 'rgba(240,236,228,0.85)'; o.lineWidth = 1;
      for (const [x, y, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x1, y1, -1, -1], [x0, y1, 1, -1]]) {
        o.beginPath(); o.moveTo(x, y + sy * 10); o.lineTo(x, y); o.lineTo(x + sx * 10, y); o.stroke();
      }
      const lx = x0, ly = y0 - 64;
      o.fillStyle = 'rgba(240,236,228,0.5)'; o.fillRect(lx, ly + 12, Math.max(320, x1 - x0), 1);
      o.restore();
      mono(o, 'GRAFFITI · AI-RECEPTIONIST BILLBOARD · US-101', lx, ly - 4, { size: 9, track: 1.8, color: INKD });
      const txt = 'SF HATES AI BILLBOARS!!!';
      const n = clamp(Math.floor((k.s - 37.226) / (38.69 - 37.226) * txt.length) + 1, 1, txt.length);
      const w = mono(o, txt.slice(0, n), lx, ly + 34, { size: 17, track: 2.4 });
      if (shown(k, 38.69)) {
        o.save(); setFont(o, FONT.mono, 17, 2.4);
        const pre = o.measureText('SF HATES AI ').width, bw = o.measureText('BILLBOARS').width;
        o.strokeStyle = AMBER; o.lineWidth = 1.2; o.beginPath();
        for (let xx = 0; xx <= bw; xx += 2) o.lineTo(lx + pre + xx, ly + 42 + Math.sin(xx / 3) * 1.6);
        o.stroke(); o.restore();
      }
      if (shown(k, 38.751)) mono(o, 'SUGGEST · BILLBOARDS', lx, ly + 60, { size: 9, track: 1.8, color: INKD });
      if (shown(k, 39.674)) mono(o, 'IGNORED', lx + 190, ly + 60, { size: 9, track: 1.8, color: AMBER, fam: FONT.monoS });
      mono(o, 'SOURCE · SF STANDARD · SEP 2 2026', lx, ly + 76, { size: 8, track: 1.6, color: 'rgba(240,236,228,0.42)' });
      void w;
    }
  } else {
    // the chorus's first word lands early on the bridge and is carried across the cut (the one big-type exception)
    mono(o, 'LOOK W1 · ON-CALL HOODIE COUTURE', 74, 790, { size: 10, track: 2.2, color: INKD });
    bigWord(k, o, 'ALL', 39.897, [6, 0]);
  }
  if (k.s < 40.055 + 0.4) lyric(k, o, 5, 'L05 · VERSE 1');
  else lyric(k, o, 6, 'L06 · CHORUS');
  return fin({ A: { tex: key, view: v, lod: 0 }, shake });
}

// ---------------------------------------------------------------- s011 the walk (MO06-w1b)
function s011(k) {
  const six = k.sixteenthLen(40.7859);
  const gains = [0, 1, 2, 3].map(b => (shown(k, 40.7859 + b * six) ? 1 : 0));
  const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
  const o = k.layers.overlay.ctx;
  // the group page: the roster expands and its groups light far -> near, one per sixteenth from the 40.786 hit;
  // on "Everybody" the engineer's seat is picked out
  const lit = clamp((k.s - 40.7859) / six + 0.0, 0, 4);
  console2(k, o, { mode: 'expanded', lit, sel: shown(k, 44.077) });
  mono(o, 'LOOK W1 · ON-CALL HOODIE COUTURE', 74, 790, { size: 10, track: 2.2, color: INKD });
  const words = [['ALL', 39.897, [6, 0]], ['HANDS!', 40.861, [6, 1]], ['ALL', 42.247, [6, 2]], ['NIGHT!', 42.769, [6, 3]], ['EVERYBODY,', 44.077, [7, 0]]];
  let cur = null;
  for (const w of words) if (shown(k, w[1])) cur = w;
  if (cur) bigWord(k, o, cur[0], cur[1], cur[2]);
  if (k.s < 44.077 - 0.04) lyric(k, o, 6, 'L06 · CHORUS');
  else lyric(k, o, 7, 'L07 · CHORUS');
  return fin({ A: { tex: 'seq', view: [1152, 648, 1.0, 0], lod: 0 }, rows: { procedural: true, gain: gains, ambient: amb, dark: 0.08, ambDark: 0.55 } });
}

// ---------------------------------------------------------------- s012a the two inserts (p012-w1): hand, then him
function s012a(k) {
  const key = still(k);
  const hand = key === 'p012w1-hand';
  const v = clampView(PLATE, hand ? [775, 692, 3.2, 0] : [380, 420, 2.2, 0]);
  const shake = [noise1(k.s * 0.9, 41) * 1.6, noise1(k.s * 0.8, 47) * 1.2];
  const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
  console2(k, o, { mode: 'expanded', lit: 4, sel: true });
  // light change only: his laptop's screen glow breathing on the beats
  const bp = k.beatIndexFloat(k.s) % 1;
  const pulse = 0.55 + 0.45 * Math.exp(-bp * 3.2);
  const [gx, gy] = fwd(PLATE, v, hand ? 560 : 400, hand ? 690 : 600, shake);
  const gr = e.createRadialGradient(gx, gy, 0, gx, gy, hand ? 520 : 600);
  gr.addColorStop(0, `rgba(150,185,255,${0.22 * pulse})`); gr.addColorStop(1, 'rgba(150,185,255,0)');
  e.fillStyle = gr; e.beginPath(); e.arc(gx, gy, hand ? 520 : 600, 0, Math.PI * 2); e.fill();
  lyric(k, o, 7, 'L07 · CHORUS');
  return fin({ A: { tex: key, view: v, lod: 0 }, shake });
}

// the sleep line: a hairline of his night from the laptop's top edge; it leaps on "you're" (49.307) and AWAKE locks on
// "awake" (49.890)
function sleepLine(k, o, x0, y0, len, { leapX, top }) {
  const steps = [[0, 0], [60, 0], [60, 26], [230, 26], [230, 8], [420, 8], [420, 30], [640, 30], [640, 4], [len, 4]];
  const grow = clamp((k.s - 47.517) / (49.307 - 47.517));
  const reach = 0.12 + 0.88 * grow;
  o.save(); o.strokeStyle = 'rgba(236,242,250,0.9)'; o.lineWidth = 1.25; o.beginPath(); o.moveTo(x0, y0);
  for (const [dx, dy] of steps.slice(1)) { if (dx / len > reach) { o.lineTo(x0 + len * reach, y0 + dy); break; } o.lineTo(x0 + dx, y0 + dy); }
  const la = since(k, 49.307);
  if (la >= 0) {
    const e = easeOutCubic(clamp((la + 1) / 3));
    o.lineTo(leapX, y0 + 4 + (top - y0 - 4) * e);
    if (e >= 1) o.lineTo(leapX + 240, top);
  }
  o.stroke();
  if (la >= 0) { o.setLineDash([2, 4]); o.strokeStyle = 'rgba(236,242,250,0.4)'; o.beginPath(); o.moveTo(x0, top); o.lineTo(leapX, top); o.stroke(); }
  o.restore();
  mono(o, 'SLEEP · LAST NIGHT', x0 + 8, y0 + 40, { size: 10, track: 2 });
  mono(o, 'HIS LAPTOP · ILLUSTRATIVE CURVE', x0 + 8, y0 + 55, { size: 8, track: 1.6, color: INKD });
  if (shown(k, 49.890)) {
    mono(o, 'AWAKE', leapX + 14, top - 12, { size: 16, track: 4, color: AMBER, fam: FONT.monoS });
    mono(o, 'DEEP → AWAKE · 49.31', leapX + 14, top + 22, { size: 8, track: 1.6, color: INKD });
  }
}

// ---------------------------------------------------------------- s012b SG03-w1: she leans in, he looks up
function s012b(k) {
  const v = clampView(SEQ, [1152, 648, 1.0, 0]);
  const o = k.layers.overlay.ctx;
  console2(k, o, { mode: 'thin', lit: 4, sel: true });
  if (shown(k, 47.517)) {
    const [lx, ly] = fwd(SEQ, v, 0.2 * 2304, 0.75 * 1296);     // the top edge of his laptop
    sleepLine(k, o, lx, ly, 900, { leapX: lx + 900, top: ly - 300 });
  }
  lyric(k, o, 8, 'L08 · CHORUS');
  return fin({ A: { tex: 'seq', view: v, lod: 0 } });
}

// ---------------------------------------------------------------- s012c the closed-eye close-up (PLACEHOLDER still)
function s012c(k) {
  const v = clampView(PLATE, [836, 470, 1.0, 0]);
  const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
  console2(k, o, { mode: 'thin', lit: 4, sel: true });
  // light change only: the laptop's screen light on her, breathing on the beats
  const bp = k.beatIndexFloat(k.s) % 1;
  const pulse = 0.6 + 0.4 * Math.exp(-bp * 3.0);
  const [gx, gy] = fwd(PLATE, v, 420, 880);
  const gr = e.createRadialGradient(gx, gy, 0, gx, gy, 700);
  gr.addColorStop(0, `rgba(170,200,255,${0.2 * pulse})`); gr.addColorStop(1, 'rgba(170,200,255,0)');
  e.fillStyle = gr; e.beginPath(); e.arc(gx, gy, 700, 0, Math.PI * 2); e.fill();
  const [lx, ly] = fwd(PLATE, v, 492, 806);
  sleepLine(k, o, lx, ly, 780, { leapX: lx + 780, top: ly - 330 });
  lyric(k, o, 8, 'L08 · CHORUS', { x: 1150, y: 330 });
  mono(o, 'PLACEHOLDER STILL · CLOSE-UP CLIP TO COME', W - 72, H - 112, { size: 9, track: 2, color: 'rgba(240,236,228,0.5)', align: 'right' });
  return fin({ A: { tex: 'D1-b', view: v, lod: 0 } });
}

export const SHOT_FN_V5 = { s010, s011, s012a, s012b, s012c };
