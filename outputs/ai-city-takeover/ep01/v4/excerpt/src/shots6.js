// v4 round 5 (2026-11-19), derived from shots5.js (round 2): the console in its v5 form (EV-size small type, the bottom
// event stream, the left scale), the lyric as a mono annotation with DINish only on the board's masthead words, and s012
// as the SG03-w1 take for the whole line, its picture held from 50.32 and a hard crop into the engineer on the 50.4686
// beat carrying the sleep line's leap to AWAKE. Earlier notes (round 2): the round-1 review cut (song 36.1999-50.933) rebuilt in the approved design-v2 language
// (console2.js: EV interface grammar under the print layer) and the per-shot plan of
// reviews/2026-11-19-codex-excerpt-gaps-r3.md section 2 (s010-s012). One readable result per line; one lyric line low
// left (the author's subtitle manner, a micro index above it); big chorus words small and toned; amber only where a
// source gives it; red only her ear lamp. s012 now: two inserts (44.942), the SG03-w1 take for the relationship
// (46.788), and on the 48.170 bar line the closed-eye close-up (PLACEHOLDER: the still D1-b, light change only, until
// its clip is made).
import { clamp, easeOutCubic, noise1 } from '../../../../../../motion-kit/src/math.js';
import { AMBER, console2, lyricMono, mono } from './console2.js';
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
const lyric = (k, o, li, idx, opts = {}) => lyricMono(k, o, W_(k, li), drawWords, { index: idx, ...opts });

// ---------------------------------------------------------------- s010 X10a -> X10b: the freeway
const BILL = [50, 318, 326, 485];
function s010(k) {
  const key = still(k);
  const { v, shake } = crop(k, [[36.1999, 836, 470, 1.0, 0], [37.0939, 643, 400, 1.3, 0.012], [38.9399, 760, 420, 1.12, -0.01],
    [39.8454, 836, 470, 1.0, 0]], 4);
  const kickA = k.s - 38.9399;
  if (kickA >= 0 && kickA < 0.3) { shake[0] += Math.sin(kickA * 90) * 6 * Math.exp(-kickA / 0.08); shake[1] += Math.cos(kickA * 70) * 3.5 * Math.exp(-kickA / 0.08); }
  const o = k.layers.overlay.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 0, sel: false });
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
      const lx = Math.max(x0, 84), ly = y0 - 64;           // clear of the left scale
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
  console2(k, o, { v5: true, mode: 'expanded', lit, sel: shown(k, 44.077) });
  mono(o, 'LOOK W1 · ON-CALL HOODIE COUTURE', 74, 790, { size: 10, track: 2.2, color: INKD });
  const words = [['ALL', 39.897, [6, 0]], ['HANDS!', 40.861, [6, 1]], ['ALL', 42.247, [6, 2]], ['NIGHT!', 42.769, [6, 3]]];
  let cur = null;
  for (const w of words) if (shown(k, w[1])) cur = w;
  if (cur && !shown(k, 44.077)) bigWord(k, o, cur[0], cur[1], cur[2]);   // 'Everybody' is a line, not a masthead word: NIGHT! clears
  if (k.s < 44.077 - 0.04) lyric(k, o, 6, 'L06 · CHORUS · ALL HANDS');
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
  console2(k, o, { v5: true, mode: 'expanded', lit: 4, sel: true });
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

// ---------------------------------------------------------------- s012b SG03-w1: the whole line, then the hold
// to 50.32 the take (she leans in, he looks up; his sleep line grows along his laptop's top edge from 47.517); from 50.32
// its picture holds; on the 50.4686 beat a hard crop into him and the laptop: the line leaps from the screen's edge and
// AWAKE lands (the board's word), held through the 50.933 cut
function s012b(k) {
  const punched = shown(k, k.shot.punch);
  const v = clampView(SEQ, punched ? [790, 905, 1.8, 0] : [1152, 648, 1.0, 0]);
  const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  // his laptop's top edge in the take (1920 px): from (520, 868) to the lid's corner (828, 782)
  const S = 1.2;
  const [ax, ay] = fwd(SEQ, v, 520 * S, 868 * S), [bx, by] = fwd(SEQ, v, 828 * S, 782 * S);
  const grow = clamp((k.s - 47.517) / (50.32 - 47.517));
  if (shown(k, 47.517)) {
    o.save(); o.strokeStyle = 'rgba(236,242,250,0.9)'; o.lineWidth = punched ? 1.6 : 1.2;
    // the night as small steps along the edge (deep / light / REM), drawn left to right
    const n = 9, pts = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n, dy = [0, 10, 10, 4, 4, 12, 12, 2, 2, 0][i] * (punched ? 1.8 : 1);
      pts.push([ax + (bx - ax) * u, ay + (by - ay) * u - 14 * (punched ? 1.8 : 1) - dy]);
    }
    const upto = punched ? n : Math.max(1, Math.round(grow * n));
    o.beginPath(); o.moveTo(...pts[0]); for (let i = 1; i <= upto; i++) o.lineTo(...pts[i]); o.stroke();
    const la = since(k, k.shot.punch);
    if (la >= 0) {
      const eu = easeOutCubic(clamp((la + 1) / 3));
      const top = 300;
      const [px_, py_] = pts[n];
      o.beginPath(); o.moveTo(px_, py_); o.lineTo(px_, py_ + (top - py_) * eu); if (eu >= 1) o.lineTo(px_ + 60, top); o.stroke();
      o.setLineDash([2, 4]); o.strokeStyle = 'rgba(236,242,250,0.4)'; o.beginPath(); o.moveTo(pts[0][0], top); o.lineTo(px_, top); o.stroke();
      o.restore();
      mono(o, 'SLEEP · LAST NIGHT', pts[0][0], py_ + 70, { size: 11, track: 2 });
      mono(o, 'HIS LAPTOP · ILLUSTRATIVE CURVE', pts[0][0], py_ + 88, { size: 10, track: 1.6, color: 'rgba(240,236,228,0.8)' });
      if (eu >= 1) {
        o.fillStyle = AMBER; o.fillRect(px_ - 3, top - 3, 7, 7);
        bigWord(k, o, 'AWAKE', k.shot.punch + 2 / 24, [8, 4], { x: px_ + 76, y: top + 40, size: 120 });
      }
    } else o.restore();
  }
  lyric(k, o, 8, 'L08 · CHORUS');
  return fin({ A: { tex: 'seq', view: v, lod: 0 } });
}

export const SHOT_FN_V6 = { s010, s011, s012a, s012b };
