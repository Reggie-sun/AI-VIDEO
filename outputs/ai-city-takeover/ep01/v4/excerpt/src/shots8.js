// v4 round 7 (2026-11-19): v4r6 (shots7.js) to the end of the chorus. s011 keeps v4r6's code on its new take
// (MO06-s-1); s012 is v4r6's; new here:
//   s013a 50.933-52.3146  the INS13-a still: the phone held out to the lens, her mouth cropped out, a slow push; on
//                         'call' (51.76) the screen lights with the board's ui.call (s013 devices: INCOMING · SEV-HIGH,
//                         caller INCIDENT WEEK, decline DISABLED)
//   s013b 52.3146-55.0777 SG04-r2-1 sings "had to take / All hands!" (held at clip 4.958 from 54.95, main.js freeze)
//   s014a/b               MO07-s-2: the turn and the sleeve out, a jump on the 57.3765 beat, the sleeve down, she walks off
//   s014c 58.7697-59.2341 the INS14-b still: her hand on the pager; its LCD backlight on, reading 10:02 (Ten oh two)
// Type (board s013/s014 type): DINish only on ALL / HANDS! / ALL / NIGHT!; every other line a mono annotation, low left,
// never on her mouth. Amber only on the lit LCD (a light source) and the console's few characters.
import { clamp, noise1 } from '../../../../../../motion-kit/src/math.js';
import { AMBER, console2, lyricMono } from './console2.js';
import { SHOT_FN_V7 } from './shots7.js';
import { W_, clampView, fwd, srcTransform } from './shots.js';
import { FONT, drawWords, setFont, shown, since } from './type.js';

const W = 1920, H = 1080;
const PLATE = [1672, 941], SEQ = [2304, 1296];
const PRINT = { uHalftone: 0.085, uCell: 3.0, uGrain: 0.034 };
const fin = ret => ({ ...ret, chrome: false, underPrint: true, grade: { ...PRINT, ...(ret.grade || {}) } });

// the chorus's big word (as shots6.js): the author's condensed type toned into the picture, landing in 3 frames
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
// the masthead words of line 10 ("All hands! All night!"), the last one shown until `until`
function masthead(k, o, pos, until = 58.6) {
  const words = [['ALL', 53.767, [10, 0]], ['HANDS!', 54.59, [10, 1]], ['ALL', 55.152, [10, 2]], ['NIGHT!', 55.513, [10, 3]]];
  let cur = null;
  for (const w of words) if (shown(k, w[1])) cur = w;
  if (cur && k.s < until) bigWord(k, o, cur[0], cur[1], cur[2], pos);
}
// the sung lines as mono annotations, low left: every line that is sounding (from just before its first word to 0.4 s
// after its last), the newest at the bottom, the one before it above
const IDX = { 8: 'L08 · CHORUS', 9: 'L09 · CHORUS', 10: 'L10 · CHORUS · ALL HANDS', 11: 'L11 · POST-CHORUS' };
function lyrics(k, o) {
  const act = [];
  for (const li of [8, 9, 10, 11]) {
    const ws = W_(k, li);
    if (!ws.length) continue;
    if (k.s >= ws[0].start - 0.05 && k.s <= ws[ws.length - 1].end + 0.4) act.push(li);
  }
  act.slice(-2).reverse().forEach((li, i) => lyricMono(k, o, W_(k, li), drawWords, { index: IDX[li], y: H - 82 - i * 64 }));
}

// ---------------------------------------------------------------- s013a the phone (INS13-a)
// the screen's corners in the plate: top-left, top-right, bottom-left (its long side runs down-left)
const SCR = { tl: [905, 358], tr: [1090, 394], bl: [753, 631], w: 188, h: 312 };
function s013a(k) {
  const u = clamp((k.s - 50.933) / (52.3146 - 50.933));
  // her mouth (plate y ~165, chin ~220) stays above the frame's top edge: top = cy - 540 / (1.148 z) >= 256
  const v = clampView(PLATE, [900 + 20 * u, 560 - 20 * u, 1.55 + 0.35 * u, 0]);
  const shake = [noise1(k.s * 0.9, 61) * 1.6, noise1(k.s * 0.8, 67) * 1.2];
  const o = k.layers.overlay.ctx, f = k.layers.feed.ctx, e = k.layers.emit.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  const P = (x, y) => fwd(PLATE, v, x, y, shake);
  const [tlx, tly] = P(...SCR.tl), [trx, try_] = P(...SCR.tr), [blx, bly] = P(...SCR.bl);
  f.save();
  f.setTransform((trx - tlx) / SCR.w, (try_ - tly) / SCR.w, (blx - tlx) / SCR.h, (bly - tly) / SCR.h, tlx, tly);
  const a = since(k, 51.76);
  const lit = a < 0 ? 0 : a === 0 ? 0.55 : 1;
  // the screen: dark glass until the call, then lit cold white with the call on it
  f.beginPath(); f.roundRect(4, 4, SCR.w - 8, SCR.h - 8, 18);
  f.fillStyle = `rgba(${Math.round(14 + 214 * lit)},${Math.round(16 + 220 * lit)},${Math.round(20 + 226 * lit)},0.97)`; f.fill();
  if (lit > 0) {
    f.globalAlpha = lit;
    setFont(f, FONT.monoS, 10, 1.6); f.fillStyle = 'rgba(20,22,26,0.75)'; f.textAlign = 'center';
    f.fillText('INCOMING · SEV-HIGH', SCR.w / 2, 46);
    f.fillStyle = 'rgba(20,22,26,0.3)'; f.fillRect(24, 58, SCR.w - 48, 1);
    setFont(f, FONT.din, 40, 0.5); f.fillStyle = 'rgba(16,18,22,0.92)';
    f.fillText('INCIDENT', SCR.w / 2, 112); f.fillText('WEEK', SCR.w / 2, 152);
    // decline (disabled, struck) and the other button, hairline rings; every word is the board's (s013 ui.call)
    f.lineWidth = 1.2;
    f.strokeStyle = 'rgba(20,22,26,0.35)'; f.beginPath(); f.arc(52, 248, 20, 0, Math.PI * 2); f.stroke();
    f.beginPath(); f.moveTo(38, 262); f.lineTo(66, 234); f.stroke();
    f.strokeStyle = 'rgba(20,22,26,0.85)'; f.beginPath(); f.arc(SCR.w - 52, 248, 20, 0, Math.PI * 2); f.stroke();
    setFont(f, FONT.mono, 8, 1.2); f.fillStyle = 'rgba(20,22,26,0.6)';
    f.fillText('DECLINE · DISABLED', 52, 286);
    f.globalAlpha = 1;
  }
  f.restore();
  // the screen's light on her hand and sleeve once it is on (soft, local)
  if (lit > 0) {
    const cx = (tlx + trx + blx + (trx + blx - tlx)) / 4, cy = (tly + try_ + bly + (try_ + bly - tly)) / 4;
    const g = e.createRadialGradient(cx, cy, 0, cx, cy, 520);
    g.addColorStop(0, `rgba(200,220,250,${0.22 * lit})`); g.addColorStop(1, 'rgba(200,220,250,0)');
    e.fillStyle = g; e.beginPath(); e.arc(cx, cy, 520, 0, Math.PI * 2); e.fill();
  }
  lyrics(k, o);
  return fin({ A: { tex: 'INS13-a', view: v, lod: 0 }, shake });
}

// ---------------------------------------------------------------- s013b SG04-r2-1: she sings it to him
function s013b(k) {
  const o = k.layers.overlay.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  // her face is top centre; the chorus words sit right, over the garage's dark lights, clear of her mouth
  masthead(k, o, { x: 1300, y: 640 });
  lyrics(k, o);
  return fin({ A: { tex: 'seq', view: clampView(SEQ, [1152, 648, 1.0, 0]), lod: 0 } });
}

// ---------------------------------------------------------------- s014a/b MO07-s-2: the turn, then she walks off
function s014(k) {
  const o = k.layers.overlay.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  masthead(k, o, { x: 70, y: 860 });
  lyrics(k, o);
  return fin({ A: { tex: 'seq', view: clampView(SEQ, [1152, 648, 1.0, 0]), lod: 0 } });
}

// ---------------------------------------------------------------- s014p (v3, 2026-11-21) the punch-in on the pager press
// r6-2 pictures 0-43 from the take's own 3840x2160 (media/hr3/seq/s014p); the view from the EDL, shot.punch.keys
// [{f, cx, cy, z}] in the 2304 picture's px, linear between keys (a slow drift following her); main.js scales the view by
// the picture's own width, so z 2 shows the 4K picture 1:1
function s014p(k) {
  const o = k.layers.overlay.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  masthead(k, o, { x: 70, y: 860 });
  lyrics(k, o);
  const K = k.shot.punch.keys;
  let j = 0;
  while (j < K.length - 2 && k.f >= K[j + 1].f) j++;
  const a = K[j], b = K[Math.min(j + 1, K.length - 1)];
  const u = b.f > a.f ? clamp((k.f - a.f) / (b.f - a.f)) : 0;
  const L = (p, q) => p + (q - p) * u;
  return fin({ A: { tex: 'seq', view: clampView(SEQ, [L(a.cx, b.cx), L(a.cy, b.cy), L(a.z, b.z), 0]), lod: 0 } });
}

// ---------------------------------------------------------------- s014c the pager (INS14-b)
const LCD = { x0: 756, y0: 453, x1: 894, y1: 509 };
function s014c(k) {
  const u = clamp((k.s - 58.7697) / (59.2341 - 58.7697));
  const v = clampView(PLATE, [835, 480, 1.25 + 0.1 * u, 0]);
  const shake = [noise1(k.s * 0.9, 71) * 1.4, noise1(k.s * 0.8, 73) * 1.0];
  const o = k.layers.overlay.ctx, f = k.layers.feed.ctx, e = k.layers.emit.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  // the LCD's backlight (amber: the one light source the accent is for) and its reading
  f.save(); srcTransform(f, PLATE, v, shake);
  const w = LCD.x1 - LCD.x0, h = LCD.y1 - LCD.y0;
  const g = f.createLinearGradient(LCD.x0, LCD.y0, LCD.x0, LCD.y1);
  g.addColorStop(0, '#E9A62C'); g.addColorStop(0.5, AMBER); g.addColorStop(1, '#D9971F');
  f.fillStyle = g; f.beginPath(); f.roundRect(LCD.x0 + 3, LCD.y0 + 3, w - 6, h - 6, 4); f.fill();
  setFont(f, FONT.monoS, 34, 3); f.fillStyle = 'rgba(46,30,6,0.9)'; f.textAlign = 'center';
  f.fillText('10:02', (LCD.x0 + LCD.x1) / 2, LCD.y1 - 14);
  f.restore();
  const [cx, cy] = fwd(PLATE, v, (LCD.x0 + LCD.x1) / 2, (LCD.y0 + LCD.y1) / 2, shake);
  const gl = e.createRadialGradient(cx, cy, 0, cx, cy, 240);
  gl.addColorStop(0, 'rgba(242,177,52,0.28)'); gl.addColorStop(1, 'rgba(242,177,52,0)');
  e.fillStyle = gl; e.beginPath(); e.arc(cx, cy, 240, 0, Math.PI * 2); e.fill();
  lyrics(k, o);
  return fin({ A: { tex: 'INS14-b', view: v, lod: 0 }, shake });
}

export const SHOT_FN_V8 = { ...SHOT_FN_V7, s013a, s013b, s014a: s014, s014b: s014, s014p, s014c };
