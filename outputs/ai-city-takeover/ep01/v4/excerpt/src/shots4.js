// v4 round 1 (2026-11-18, PLAN-v4.md): the still -> motion -> singing junction. s010 is v3's (shots2.js, W1 geometry);
// here s011 (the W1 walk clip), s012a (two still inserts cropped from p012-w1 on "hold on tight") and s012b (the W1 sung
// take). One readable result per line; the photograph or the footage stays dominant; the motion is the footage's own
// (no code camera moves on the clips beyond one hard 4% push on the 48.17 bar line).
import { clamp, noise1 } from '../../../../../../motion-kit/src/math.js';
import { brackets, hypnogram, leader } from './devices.js';
import { W_, clampView, fwd, monoLine } from './shots.js';
import { FONT, INK, drawWords, micro, setFont, shown, since, slamWord } from './type.js';

const W = 1920, H = 1080;
const SEQ = [2304, 1296];
const PLATE = [1672, 941];
const SHADOW = { color: 'rgba(0,0,0,0.55)', blur: 18, dy: 2 };
const BIG_SH = { color: 'rgba(0,0,0,0.5)', blur: 16, dy: 5 };
const LOOK = 'RUNWAY ONE · LOOK W1 · ON-CALL HOODIE COUTURE';

function pick(k, plan) {
  let c = plan[0];
  for (const p of plan) if (shown(k, p[0])) c = p;
  return c;
}

// ---------------------------------------------------------------- s011: the walk (MO06-w1b)
function s011(k) {
  const v = [1152, 648, 1.0, 0];
  const six = k.sixteenthLen(40.7859);
  const gains = [0, 1, 2, 3].map(b => (shown(k, 40.7859 + b * six) ? 1 : 0));
  const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  // the chorus words, one a picture on their accents, upper left over the dark ceiling (her face is top centre-right
  // for the first 0.8 s of the take, clear of them)
  micro(f, LOOK, 106, 236, { size: 13, track: 3, color: 'rgba(242,238,230,0.85)' });
  const words = [['ALL', 39.897, [6, 0]], ['HANDS!', 40.861, [6, 1]], ['ALL', 42.247, [6, 2]], ['NIGHT!', 42.769, [6, 3]], ['EVERYBODY,', 44.077, [7, 0]]];
  let cur = null;
  for (const w of words) if (shown(k, w[1])) cur = w;
  if (cur) slamWord(k, f, cur[0], cur[1], 100, 470, cur[0] === 'EVERYBODY,' ? 200 : 230, { marks: [cur[2]] });
  monoLine(k, o, 6, { until: 44.0 });
  if (shown(k, 44.077)) drawWords(k, o, W_(k, 7, [0]), 72, H - 46, FONT.mono, 21, { track: 7, upper: true, pop: false,
    color: 'rgba(242,238,230,0.9)', shadow: { color: 'rgba(0,0,0,0.6)', blur: 10 } });
  // the rows snap on far -> near from the 40.786 hit (procedural on the moving footage: the bright tubes in the upper
  // half, banded by height); the flash-lit figure and the room dim less than the tubes
  return { A: { tex: 'seq', view: v, lod: 0 }, rows: { procedural: true, gain: gains, ambient: amb, dark: 0.08, ambDark: 0.55 } };
}

// ---------------------------------------------------------------- s012a: two still inserts from p012-w1
// her hand on the chair back on "hold" (crop below her cuff: hand and chair, the laptop's lit edge at the left), then
// the engineer looking up on "on tight"; only the laptop's light changes
function s012a(k) {
  let still = k.shot.stills[0][0];
  for (const [key, at] of k.shot.stills) if (shown(k, at)) still = key;
  const hand = still === 'p012w1-hand';
  const c = hand ? [775, 692, 3.2, 0.0] : [380, 420, 2.2, 0.0];
  const v = clampView(PLATE, c);
  const t = k.s;
  const shake = [noise1(t * 0.9, 41) * 1.6, noise1(t * 0.8, 47) * 1.2];
  const P = (x, y) => fwd(PLATE, v, x, y, shake);
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx, e = L.emit.ctx;
  // the laptop's screen light breathing on the beats (soft, local)
  const bp = k.beatIndexFloat(k.s) % 1;
  const pulse = 0.55 + 0.45 * Math.exp(-bp * 3.2);
  const [gx, gy] = hand ? P(560, 690) : P(400, 600);
  const gr = e.createRadialGradient(gx, gy, 0, gx, gy, hand ? 520 : 600);
  gr.addColorStop(0, `rgba(150,185,255,${0.22 * pulse})`); gr.addColorStop(1, 'rgba(150,185,255,0)');
  e.fillStyle = gr; e.beginPath(); e.arc(gx, gy, hand ? 520 : 600, 0, Math.PI * 2); e.fill();
  if (hand) {
    // the result of the line: the grip, classified on the hand itself
    const ha = since(k, 45.625);
    const [x0, y0] = P(682, 604), [x1, y1] = P(826, 690);
    brackets(o, x0, Math.max(30, y0), x1, y1, ha, { color: INK.amber, arm: 22 });
    if (ha >= 0) {
      setFont(o, FONT.monoS, 20, 2.4); o.fillStyle = INK.amber; o.fillText('GRIP · WHITE-KNUCKLED', x0, y1 + 40);
      micro(o, 'FRONT ROW · CLASSIFIER', x0, y1 + 64, { size: 12, track: 2.4 });
    }
    drawWords(k, f, W_(k, 7, [1]), 1240, 900, FONT.din, 210, { upper: true, color: INK.warm, shadow: BIG_SH });
  } else {
    drawWords(k, f, W_(k, 7, [1, 2]), 1250, 430, FONT.din, 170, { upper: true, color: INK.warm, space: 36, shadow: BIG_SH, pop: false });
    drawWords(k, f, W_(k, 7, [3]), 1250, 620, FONT.din, 170, { upper: true, color: INK.warm, shadow: BIG_SH });
  }
  drawWords(k, o, W_(k, 7), 72, H - 46, FONT.mono, 21, { track: 7, upper: true, pop: false,
    color: 'rgba(242,238,230,0.9)', shadow: { color: 'rgba(0,0,0,0.6)', blur: 10 } });
  return { A: { tex: still, view: v, lod: 0 }, shake };
}

// ---------------------------------------------------------------- s012b: she sings it to him (SG03-w1)
function s012b(k) {
  const c = pick(k, [[46.7882, 1152, 648, 1.0, 0], [48.1698, 1290, 560, 1.04, 0]]);
  const v = clampView(SEQ, [c[1], c[2], c[3], c[4]]);
  const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
  // the line stays with her mouth; the words sit in the dark between the card and her hair
  drawWords(k, f, W_(k, 8, [0, 1]), 474, 116, FONT.nim, 36, { color: INK.warm, shadow: SHADOW, space: 11 });
  drawWords(k, f, W_(k, 8, [2]), 468, 222, FONT.din, 96, { upper: true, color: INK.warm, shadow: BIG_SH });
  drawWords(k, f, W_(k, 8, [3, 4]), 468, 318, FONT.din, 80, { upper: true, color: INK.warm, space: 20, shadow: BIG_SH });
  // the result of the line: his night, read off the laptop he clutches, climbing to AWAKE on "you're"
  const lap = fwd(SEQ, v, 0.3 * 2304, 0.86 * 1296);
  leader(o, lap, [400, 828], since(k, 47.517), { color: 'rgba(236,232,222,0.75)' });
  hypnogram(k, o, 60, 810, { t0: 47.517, drop: 49.307, w: 340, h: 100 });
  return { A: { tex: 'seq', view: v, lod: 0 } };
}

export const SHOT_FN_V4 = { s011, s012a, s012b };
