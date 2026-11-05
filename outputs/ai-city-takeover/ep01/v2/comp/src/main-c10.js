// IRIS EP01《Looked Outside》v2 — scenes on motion-kit. Board: ../../board.md (v2.1).
// A shot whose generated video passed its per-shot gate plays as an image sequence (seq/<shot>, see seq.py);
// otherwise it falls back to the approved animatic still under the 2.5D camera. Cut times are the same either
// way. Graphics on video sit on measured anchors (data/tracks.json, see tracks.py). Every value is a pure
// function of comp time t.
import { install } from '../../../../../../motion-kit/src/runtime.js';
import SEQ from '../seq/sequences.json';
import MOUTH from '../mouth.json';
import { F, chrome, detector, font, glowPath, rollNumber, roundRect, runs, slam } from '../../../../../../motion-kit/src/draw2d.js';
import { drawLyrics } from '../../../../../../motion-kit/src/lyrics.js';
import { protectCentre, trackZoom } from '../../../../../../motion-kit/src/beatcam.js';
import { checkBlinks, mouthKeys, sungPlate } from '../../../../../../motion-kit/src/mouth.js';
import { clamp, easeInOutCubic, easeOutCubic, hash2, lerp } from '../../../../../../motion-kit/src/math.js';

const W = 1920, H = 1080, FPS = 30, DURATION = 30.5;
const RED = '#E3342F', INK = 'rgba(236,241,244,0.92)', PALE = 'rgba(226,231,238,0.9)';
const SOURCE = '来源：OpenAI 2026-10-23 披露';

// ---------- timing ----------
const lines = k => k.data.words.lines;
const word = (k, li, wi) => lines(k)[li].words[wi];

// cut times come from data/events.json (written by build.py from the beat map, the vocal onsets and chorus.json);
// the shot order is the order of the cuts, so a chorus cutaway (S8a_x, S8b_x) appears only when chorus.json has one
function pickShot(t, clock, data) {
  const ev = data.events.events, f = Math.round(t * FPS);
  const cuts = Object.keys(ev).filter(k => k.startsWith('cut_')).map(k => ({ id: k.slice(4), t: ev[k].t }))
    .sort((a, b) => a.t - b.t);
  const order = [{ id: 'S1', t: 0 }, ...cuts];
  for (let i = order.length - 1; i >= 0; i--) {
    if (f >= Math.round(order[i].t * FPS)) return { id: order[i].id, t0: order[i].t, t1: i + 1 < order.length ? order[i + 1].t : DURATION };
  }
  return { id: 'S1', t0: 0, t1: order[1].t };
}

// ---------- camera: plate px -> screen px, cover-fit, centre clamped inside the plate ----------
// protect: plate rects that must stay in frame (the platform mark burned into generated video)
function cam(k, plate, cx, cy, z, protect = []) {
  const [pw, ph] = k.size[plate];
  const fit = Math.max(W / pw, H / ph), s = fit * z;
  const hx = W / 2 / s, hy = H / 2 / s;
  [cx, cy] = protectCentre(cx, cy, s, protect, W, H);
  cx = clamp(cx, hx, pw - hx); cy = clamp(cy, hy, ph - hy);
  return { view: [cx, cy, z, 0], fit, s, out: ([x, y]) => [(x - cx) * s + W / 2, (y - cy) * s + H / 2],
           box: ([x, y, w, h]) => [(x - cx) * s + W / 2, (y - cy) * s + H / 2, w * s, h * s] };
}
function move(k, t, plate, a, b, ease = easeInOutCubic) {
  const u = ease(clamp((t - k.t0) / (k.t1 - k.t0)));
  return cam(k, plate, lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u));
}
// the same move over an absolute stretch [t0, t1): a cutaway inside it does not restart the move
function moveSpan(k, t, plate, a, b, t0, t1, ease = easeInOutCubic) {
  const u = ease(clamp((t - t0) / (t1 - t0)));
  return cam(k, plate, lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u));
}
const cutAt = (k, id) => k.data.events.events[`cut_${id}`].t;
const still = (cm, plate, extra = {}) => ({ plate, view: cm.view, fit: cm.fit, fogA: [0, 1, 0, 0], fogB: [0, 1, 0, 0], ...extra });
// generated video plate: screen px = video px (1920x1080), the clip's own camera does the moving
const filmed = id => Boolean(SEQ[id]);
const frameOf = (k, t) => Math.round((t - k.t0) * FPS);
const video = (k, t, id, a = [W / 2, H / 2, 1.0], b = a) => ({ cm: move(k, t, id, a, b), frame: frameOf(k, t) });
const clip = (v, id, extra = {}) => ({ ...still(v.cm, id, extra), plateFrame: v.frame });
// the chorus plays the track (motion-kit/src/beatcam.js): a punch on every kick from the S8a cut to the S9a cut and
// one impact on the chorus entry hit; verses and the opening hold still. The zoom keeps the platform mark in frame.
const MARK = [19, 20, 164, 82];                                   // the platform's AI mark (25, 26, 152 x 70) + 6 px, video px
function chorusZoom(t, k) {
  const ev = k.data.events.events;
  return trackZoom(t, k.clock, { sections: [[ev.cut_S8a.t, ev.cut_S9a.t]], impacts: [ev.chorus_impact.t] });
}
function chorusVideo(k, t, id) {
  return { cm: cam(k, id, W / 2, H / 2, chorusZoom(t, k), [MARK]), frame: frameOf(k, t) };
}

// ---------- in-image signal helpers (feed layer) ----------
const grow = (t, t0, dur = 0.12) => easeOutCubic(clamp((t - t0) / dur));
// slam() scales about (ax, ay) but draws in absolute coordinates, so a drawing made at the origin is moved there
const placed = (x, y, draw) => c => { c.translate(x, y); draw(c); };

function osdRight(ctx, rows, { right = W - 96, y = 96, size = 22 } = {}) {
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,0.65)'; ctx.shadowOffsetX = 1; ctx.shadowOffsetY = 1;
  let yy = y;
  rows.forEach(row => {
    const parts = row.map(p => ({ family: F.mono, size, tracking: 1.5, color: INK, ...p }));
    const sz = Math.max(...parts.map(p => p.size));
    let wsum = 0;
    for (const p of parts) { font(ctx, p.family, p.size, p.tracking); wsum += ctx.measureText(p.text).width + sz * 0.6; }
    runs(ctx, parts, right - wsum + sz * 0.6, yy, { gap: sz * 0.6 });
    yy += sz * 1.45;
  });
  ctx.restore();
}
function line(ctx, a, b, { color = INK, width = 1.5, dash = null, alpha = 1 } = {}) {
  ctx.save();
  ctx.globalAlpha = alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
  if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke();
  ctx.restore();
}
function label(ctx, text, x, y, { size = 48, color = INK, family = F.sans, alpha = 1, align = 'left' } = {}) {
  ctx.save();
  ctx.globalAlpha = alpha; ctx.textAlign = align;
  ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 12;
  font(ctx, family, size, 2); ctx.fillStyle = color; ctx.fillText(text, x, y);
  ctx.restore();
}
function scrim(ctx, x, y, w, h, alpha = 0.55) {
  ctx.save();
  ctx.filter = 'blur(28px)'; ctx.globalAlpha = alpha; ctx.fillStyle = '#05070a';
  ctx.fillRect(x, y, w, h);
  ctx.restore();
}
// the platform's AI-generated mark, drawn where generated shots carry it so the mark never blinks
function aiMark(ctx) {
  ctx.save();
  ctx.strokeStyle = 'rgba(255,255,255,0.42)'; ctx.lineWidth = 3;
  roundRect(ctx, 25, 26, 152, 70, 16); ctx.stroke();
  font(ctx, F.sansR, 42, 0); ctx.fillStyle = 'rgba(255,255,255,0.42)'; ctx.textAlign = 'center';
  ctx.fillText('AI生成', 101, 76);
  ctx.restore();
}
function sources(k) { osdRight(k.layers.feed.ctx, [[{ text: SOURCE, family: F.sansR, size: 24 }]], { y: H - 70 }); }
// sung (chorus) lines in the EV toolkit's "stack" lyric mode: one word per row, large, left of her face (c10)
const STACK = { x: 120, top: 200, size: 128, lead: 0.9 };
function lyrics(k, t) { drawLyrics(k.layers.overlay.ctx, t, lines(k), { toComp: s => k.clock.comp(s), stack: STACK }); }
function finish(k, t, { mark = true } = {}) { lyrics(k, t); if (mark) aiMark(k.layers.feed.ctx); }

// ---------- shots ----------
function S1(t, k) {                                               // the closed eye opens on "woke" (S1v3)
  const v = filmed('S1') && video(k, t, 'S1');
  const cm = v ? v.cm : move(k, t, 'K1a', [700, 480, 1.0], [700, 490, 1.05]);
  const o = k.layers.overlay.ctx, tc = k.clock.at(0, 1);         // "03:47" lands on beat 1
  slam(o, placed(1170, 600, c => {
    font(c, F.monoB, 190, 4); c.fillStyle = '#f2f4f7';
    c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = 18; c.fillText('03:47', 0, 0);
    font(c, F.mono, 26, 6); c.fillStyle = 'rgba(236,241,244,0.85)'; c.fillText('IRIS · NEWS 01', 8, 52);
  }), { t, t0: tc, ax: 1170, ay: 600, drop: 18 });
  finish(k, t, { mark: !v });                                      // generated video carries the platform mark
  return v ? clip(v, 'S1') : still(cm, 'K1a');
}

// c5: the eye of S1 belongs to this face, lit by the same panes (P7, awake, her eyes on the pages); c4's A01-v2 on the
// balcony looked down with another face right after the eye opened (user: "睁眼之后突然转到这个人也非常奇怪")
function S2(t, k) {                                               // cut on "woke": IRIS awake in her pane space
  const v = filmed('S2') && video(k, t, 'S2', [1300, 400, 1.0], [1350, 370, 1.05]);   // coverage: digital push 1.00->1.05
  const cm = v ? v.cm : move(k, t, 'P7', [836, 470, 1.0], [870, 450, 1.05]);
  const o = k.layers.overlay.ctx;
  scrim(k.layers.feed.ctx, 80, 370, 700, 150, v ? 0.5 : 0.62);    // a bright pane sits behind the title in P7
  slam(o, placed(120, 480, c => {
    font(c, F.mono, 24, 6); c.fillStyle = 'rgba(236,241,244,0.8)'; c.fillText('IRIS · NEWS 01', 0, -78);
    font(c, 'MK Serif Display Italic', 76, 0); c.fillStyle = '#f2f4f7'; c.fillText('Looked Outside', 0, 0);
  }), { t, t0: k.t0, ax: 120, ay: 480, drop: 10, s0: 1.04 });
  const tDate = word(k, 2, 0).start;                              // "September twenty": the incident date, not IRIS's 03:47
  if (t >= tDate) {                                               // the window frame behind it is bright: keep a scrim
    scrim(k.layers.feed.ctx, W - 600, 66, 560, 70, 0.6);
    osdRight(k.layers.feed.ctx, [[{ text: '事件日期', family: F.sansR, size: 30 }, { text: '2026-09-20', size: 30 }]], { y: 110 });
  }
  finish(k, t, { mark: !v });                                     // A01-v2 already carries the platform mark
  return v ? clip(v, 'S2') : still(cm, 'P7');
}

function S3(t, k) {
  const v = filmed('S3') && video(k, t, 'S3');
  const cm = v ? v.cm : move(k, t, 'K3', [836, 470, 1.0], [740, 450, 1.12]);
  const f = k.layers.feed.ctx;
  osdRight(f, [[{ text: 'OpenAI · 内部研究模型训练', family: F.sansR, size: 30 }], [{ text: '2026-09-20', size: 26 }]], { y: 110 });
  // the route faces the camera at the end of the aisle; the red gap is the misconfigured resolver
  const gap = v && k.data.tracks.S3_gap[clamp(v.frame, 0, k.data.tracks.S3_gap.length - 1)];
  const [dx, dy] = gap ? [gap[0] + gap[2] / 2, gap[1] + gap[3] / 2] : cm.out([720, 440]);
  const tModel = word(k, 2, 3).start, tResolver = word(k, 3, 1).start, tMis = word(k, 3, 2).start;
  if (t >= tModel) {
    const a = grow(t, tModel, 0.15);
    label(f, '研究模型', dx - 470, dy - 200, { size: 48, alpha: a, align: 'center' });
    line(f, [dx - 470, dy - 180], [dx - 470, dy - 150], { alpha: a, width: 2 });
  }
  if (t >= tResolver) {
    const p = grow(t, tResolver, 0.22);
    line(f, [dx - 470, dy - 150], [lerp(dx - 470, dx - 60, p), dy - 150], { width: 2.5, alpha: 0.9 });
    const box = gap ? [gap[0] - 26, gap[1] - 16, gap[2] + 52, gap[3] + 32] : cm.box([684, 316, 72, 252]);
    detector(f, box, { t, t0: tResolver, frame: k.frame, label: 'DNS 解析器', sub: t >= tMis ? '配置错误' : null, size: 36 });
  }
  finish(k, t, { mark: !v });
  return v ? clip(v, 'S3') : still(cm, 'K3');
}

// cable path in K4 plate px: out of the red gap, along the floor bundle, to the foot of the window glass
const K4_PATH = [[528, 380], [536, 560], [548, 700], [640, 728], [780, 712], [930, 668], [1080, 626], [1220, 590], [1340, 562], [1440, 540]];
function along(path, u) {
  const L = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
  const total = L.reduce((a, b) => a + b, 0);
  const seg = [path[0]];
  let s = u * total;
  for (let i = 0; i < L.length; i++) {
    if (s <= L[i]) { const q = s / L[i]; seg.push([lerp(path[i][0], path[i + 1][0], q), lerp(path[i][1], path[i + 1][1], q)]); return seg; }
    s -= L[i]; seg.push(path[i + 1]);
  }
  return seg;
}
function S4(t, k) {
  const cm = move(k, t, 'K4', [836, 470, 1.0], [960, 450, 1.06]);
  const e = k.layers.emit.ctx, tLeft = word(k, 4, 2).start;          // "left open"
  if (t >= tLeft) {                                                // the gap glows; the pulse runs to the glass by the cut
    glowPath(e, [cm.out([528, 60]), cm.out([532, 700])], { core: 3, halo: 16, alpha: 0.5 * grow(t, tLeft, 0.25) });
    const pts = along(K4_PATH, easeInOutCubic(clamp((t - tLeft) / (k.t1 - tLeft)))).map(p => cm.out(p));
    glowPath(e, pts.slice(-6), { core: 3.2, halo: 14, alpha: 1 });   // c10: S4c takes it through the glass into the city
    glowPath(e, pts, { core: 1.2, halo: 5, alpha: 0.35 });
  }
  finish(k, t);
  return still(cm, 'K4', { emitGain: 2.2 });
}

// K5b: one far window lights up red while IRIS watches; a redacted query log ghosts on the glass
const K5_WINDOW = [330, 300], S5_WINDOW = [450, 380];             // animatic plate px / video px
function S5(t, k) {
  const v = filmed('S5') && video(k, t, 'S5');
  const plate = k.size.K5b ? 'K5b' : 'K5';
  const cm = v ? v.cm : move(k, t, plate, [836, 470, 1.0], [800, 470, 1.03]);
  const e = k.layers.emit.ctx, f = k.layers.feed.ctx;
  const tAround = Math.max(word(k, 6, 2).start, k.t0 + 2 / FPS), tLog = tAround + 0.25;
  if (t >= tAround) {                                              // the far window that "looked" lights up
    const p = cm.out(v ? S5_WINDOW : K5_WINDOW), a = grow(t, tAround, 0.1) * (0.8 + 0.2 * Math.cos((t - tAround) * 9));
    glowPath(e, [p, [p[0] + 1, p[1]]], { core: 10, halo: 42, alpha: a });
  }
  if (t >= tLog) {                                                 // contents redacted: no invented queries
    const a = 0.55 * grow(t, tLog, 0.12);
    f.save(); f.globalAlpha = a; f.fillStyle = 'rgba(226,231,238,0.85)';
    font(f, F.mono, 22, 1); f.fillText('DNS QUERY', 150, 470);
    [[150, 500, 260], [150, 532, 180], [150, 564, 300], [150, 596, 220]].forEach(([x, y, w], i) => {
      f.fillRect(x, y, w * grow(t, tLog + i * 0.05, 0.08), 18);
    });
    f.restore();
  }
  finish(k, t, { mark: !v });
  return v ? clip(v, 'S5', { emitGain: 2.2 }) : still(cm, plate, { emitGain: 2.2 });
}

// racks hold still for eleven days while the city traffic outside keeps moving
const K4_ROAD = [[1112, 412], [1200, 436], [1300, 455], [1420, 470], [1540, 482], [1660, 492]];
function S6(t, k) {
  const cm = move(k, t, 'K4', [1000, 420, 1.12], [1010, 420, 1.14]);
  const e = k.layers.emit.ctx, f = k.layers.feed.ctx;
  for (let j = 0; j < 7; j++) {                                    // traffic: dashes flowing along the highway
    const u = ((t * 0.22 + j / 7) % 1);
    const pts = along(K4_ROAD, u).slice(-3).map(p => cm.out(p));
    glowPath(e, pts, { color: j % 2 ? [255, 236, 214] : [255, 40, 22], core: 1.6, halo: 5, alpha: 0.7 });
  }
  const days = 11;                                                 // c10: S5d counts the eleven days; S6 holds the last
  osdRight(f, [[{ text: `2026-${days < 11 ? '09' : '10'}-${String(days < 11 ? 19 + days : 1).padStart(2, '0')}`, size: 30 }, { text: `D+${days}`, size: 30, color: RED }]], { y: 110 });
  scrim(f, 100, 220, 560, 200, 0.6);
  slam(f, placed(140, 300, c => {
    label(c, '最强模型训练', 0, 0, { size: 56 });
    label(c, '暂停 11 天', 0, 76, { size: 72, color: '#f4f6f9' });
  }), { t, t0: k.t0 + 1 / FPS, ax: 140, ay: 300, drop: 10, ghosts: 0 });
  finish(k, t);
  return still(cm, 'K4', { emitGain: 2.0 });
}

const K7_PANES = [[500, 330], [130, 190], [1520, 440], [400, 760], [560, 250], [1480, 330], [260, 820], [180, 120]];
function S7(t, k) {
  const v = filmed('S7') && video(k, t, 'S7');
  const cm = v ? v.cm : move(k, t, 'K7', [900, 400, 1.0], [930, 380, 1.04]);
  const f = k.layers.feed.ctx;
  const brk = clamp((t - k.t0) / 0.3);                             // the connection snaps at the cut: offline
  if (brk < 1) {
    const gap = 60 * easeOutCubic(brk), y = 820, a = 1 - brk;    // below her face, above the lyric scrim
    line(f, [120, y], [W / 2 - gap, y], { color: RED, width: 2.5, dash: [10, 8], alpha: a });
    line(f, [W / 2 + gap, y], [W - 120, y], { color: RED, width: 2.5, dash: [10, 8], alpha: a });
  }
  scrim(f, 100, 160, 560, 160, 0.55);
  label(f, '离线', 140, 230, { size: 64, alpha: grow(t, k.t0, 0.15) });
  label(f, '训练只用已缓存的网页', 142, 282, { size: 30, family: F.sansR, alpha: grow(t, k.t0 + 0.2, 0.15) });
  scrim(f, 60, 870, 1180, 190, 0.6);                                // the bright pane sits behind the lyric
  if (v) {                                                        // panes slide fast: each stamp flashes on a pane
    k.data.tracks.S7_stamps.forEach(({ t: ts, at: [sx, sy] }) => {
      if (t < ts || t >= ts + 0.4) return;
      const a = 1 - easeInOutCubic(clamp((t - ts - 0.22) / 0.18));
      slam(f, placed(sx, sy, c => {
        c.globalAlpha = a; c.rotate(-0.1);
        c.strokeStyle = PALE; c.lineWidth = 3; c.strokeRect(-86, -32, 172, 56);
        font(c, F.sans, 34, 6); c.fillStyle = PALE; c.fillText('已缓存', -66, 10);
      }), { t, t0: ts, ax: sx, ay: sy, s0: 1.35, dur: 2 / FPS });
    });
    finish(k, t, { mark: false });
    return clip(v, 'S7');
  }
  const b0 = k.clock.beat(k.t0).idx;
  K7_PANES.forEach(([x, y], i) => {
    const ts = k.clock.comp(k.clock.beats[b0 + 1 + i]);            // one grey-white stamp per beat
    if (t < ts || ts >= k.t1) return;
    const [sx, sy] = cm.out([x, y]);
    slam(f, placed(sx, sy, c => {
      c.rotate(-0.1);
      c.strokeStyle = PALE; c.lineWidth = 3; c.strokeRect(-86, -32, 172, 56);
      font(c, F.sans, 34, 6); c.fillStyle = PALE; c.fillText('已缓存', -66, 10);
    }), { t, t0: ts, ax: sx, ay: sy, s0: 1.35, dur: 2 / FPS });
  });
  finish(k, t);
  return still(cm, 'K7');
}

// the chorus segments come from comp/chorus.json (via data/chorus.json): a take plays its image sequence at its measured
// lag (seq.py) and keeps its own platform mark; a still is an approved plate moved from 'from' to 'to' by the code
// camera, with the drawn mark. Both ride the chorus zoom; the lyric stays on screen.
// a 'sung' still steps through its mouth and blink plates on the measured sung words (comp/mouth.json,
// motion-kit/src/mouth.js); the keys depend only on the words, so they are built once
let SUNG = null;
function sungAt(t, k) {
  if (!SUNG) {
    SUNG = mouthKeys(lines(k).filter(l => l.mode === 'sung'), MOUTH, FPS);
    checkBlinks(SUNG, MOUTH.blinks, FPS);
  }
  return sungPlate(t, MOUTH.base, SUNG, MOUTH.blinks, FPS);
}
// ---------- chorus decoration: the footage plays plain, the graphics carry it (the author's way; user on the 数字人
// takes: 「后面的程序装饰还差点,作者不是就是简单放个视频」). Each "I didn't run" locks a detector on her (IRIS · 仍在沙盒内);
// on the second "I just looked outside" S5's far window lights again as she looks at it, without words (c7's red probe
// with 只看了一眼 was dropped, user: 「这个字体,我是真的看不懂」). Every kick hits the print (T01's slam recipe: halftone,
// misregistration, a weave jitter; a 3-frame flash on the entry hit). IRIS's clock ticks top right: the film's 30 s are her
// 03:47:30-03:48:00, between S1's 03:47 and S9b's 03:48.
const SANDBOX = '仍在沙盒内';
const K5_FACE = [950, 150, 320, 330];                               // plate px (K5)
function chorusGrade(k, t) {
  const ev = k.data.events.events, kick = k.clock.pulse('kick', t + 1 / FPS, 0.09);
  const entry = Math.ceil((ev.chorus_impact.t - 1 / FPS) * FPS - 1e-6);
  const flash = [0.06, 0.035, 0.015][k.frame - entry] ?? 0;         // decays over 3 frames: qa.py flags a 1-frame pop
  return { uHalftone: 0.10 + 0.14 * kick, uMisreg: 1.4 * kick, uCA: 0.9 + 1.0 * kick, uFlash: flash,
           uWeave: [(hash2(k.frame, 13) - 0.5) * 0.5, (hash2(k.frame, 14) - 0.5) * 0.5] };
}
function chorusClock(k, t) {
  const s = 30 + Math.floor(t), f = k.layers.feed.ctx;
  scrim(f, W - 430, 74, 390, 58, 0.55);
  osdRight(f, [[{ text: 'IRIS', size: 26, color: RED }, { text: `03:4${s >= 60 ? 8 : 7}:${String(s % 60).padStart(2, '0')}`, size: 26 }]], { y: 112 });
}
function chorusDecor(k, t, id, cm) {
  const f = k.layers.feed.ctx, e = k.layers.emit.ctx;
  chorusClock(k, t);
  if (id === 'S8a') {
    const boxes = k.data.tracks.S8a_face?.boxes;
    const b = boxes && boxes[clamp(frameOf(k, t), 0, boxes.length - 1)];
    if (!b) return;
    if (t < word(k, 12, 0).start - 0.05) detector(f, cm.box(b), { t, t0: word(k, 11, 0).start, frame: k.frame, label: 'IRIS', sub: SANDBOX, size: 30 });
  } else if (id === 'S8b') {
    detector(f, cm.box(K5_FACE), { t, t0: word(k, 13, 0).start, frame: k.frame, label: 'IRIS', sub: SANDBOX, size: 30 });
  } else if (id === 'S8b_x' || id === 'S8w' || id === 'S8b_x2') {
    const tLook = word(k, 14, 2).start, win = cm.out(K5_WINDOW);   // "looked": the window she looked at in S5 lights again
    const sc = cm.s / 1.42;                                         // the glow grows with the zoom (S8w is ~1.7x closer)
    if (t >= tLook) glowPath(e, [win, [win[0] + 1, win[1]]], { core: 10 * sc, halo: 42 * sc, alpha: grow(t, tLook, 0.1) * (0.8 + 0.2 * Math.cos((t - tLook) * 9)) });
  }
}
function segMove(k, t, plate, seg, z) {
  const a = [seg.from[0], seg.from[1], seg.from[2] * z], b = [seg.to[0], seg.to[1], seg.to[2] * z];
  return seg.span ? moveSpan(k, t, plate, a, b, cutAt(k, seg.span[0]), cutAt(k, seg.span[1])) : move(k, t, plate, a, b);
}
function chorusShot(t, k) {
  const id = k.shot.id, seg = k.data.chorus.shots[id];
  const grade = chorusGrade(k, t);
  scrim(k.layers.feed.ctx, 40, 170, 760, 720, 0.42);              // under the stacked sung line
  if (seg.kind === 'take' && filmed(id) && seg.from) {             // a take framed by the code camera (cut in like a still);
    const z = chorusZoom(t, k);                                     // its source carries no burned-in label, so the comp draws one
    const cm = segMove(k, t, id, seg, z);
    if (seg.scrim) scrim(k.layers.feed.ctx, ...seg.scrim);
    chorusDecor(k, t, id, cm);
    finish(k, t);
    return clip({ cm, frame: frameOf(k, t) }, id, { grade });
  }
  if (seg.kind === 'take' && filmed(id)) { finish(k, t, { mark: false }); return clip(chorusVideo(k, t, id), id, { grade }); }
  const z = chorusZoom(t, k);
  const cm = segMove(k, t, seg.plate, seg, z);
  if (seg.scrim) scrim(k.layers.feed.ctx, ...seg.scrim);          // a bright plate behind the sung line
  chorusDecor(k, t, id, cm);
  finish(k, t);
  return still(cm, seg.sung ? sungAt(t, k) : seg.plate, { grade, emitGain: 2.2 });   // the variants share the base plate's size
}

// ---------- c10 inserts (user on c9: 「对比原作者还是太单调,元素太少,片段太少,内容太少,也不够高级」): each one explains the
// word it lands on, with no new claims beyond the source ----------

// S3d "misconfigured": the route as a diagram over the dimmed aisle. Research model -> DNS resolver -> internet; on the
// word the resolver turns red (配置错误) and the closed link to the internet opens as a red line.
function node(f, x, y, w, text, { color = INK, alpha = 1, sub = null } = {}) {
  f.save(); f.globalAlpha = alpha; f.strokeStyle = color; f.lineWidth = 2;
  roundRect(f, x - w / 2, y - 44, w, 88, 10); f.stroke(); f.restore();
  label(f, text, x, y + 14, { size: 40, color, alpha, align: 'center' });
  if (sub) label(f, sub, x, y + 84, { size: 30, color: RED, family: F.sansR, alpha, align: 'center' });
}
function S3d(t, k) {
  const cm = move(k, t, 'K3', [836, 470, 1.12], [820, 460, 1.16]);
  const f = k.layers.feed.ctx;
  const tMis = word(k, 3, 2).start, a = grow(t, k.t0, 0.1), red = t >= tMis;
  const M = [400, 520], R = [960, 520], N = [1520, 520];
  scrim(f, 160, 380, 1600, 300, 0.55);
  line(f, [M[0] + 150, M[1]], [R[0] - 170, R[1]], { width: 2, alpha: a });
  if (!red) line(f, [R[0] + 170, R[1]], [N[0] - 130, N[1]], { width: 2, dash: [6, 10], alpha: 0.5 * a });
  else {                                                           // the link that should stay closed opens
    const u = easeOutCubic(clamp((t - tMis) / 0.35));
    line(f, [R[0] + 170, R[1]], [lerp(R[0] + 170, N[0] - 130, u), R[1]], { color: RED, width: 3 });
  }
  node(f, M[0], M[1], 300, '研究模型', { alpha: a });
  node(f, R[0], R[1], 340, 'DNS 解析器', { color: red ? RED : INK, alpha: a, sub: red ? '配置错误' : null });
  node(f, N[0], N[1], 260, '互联网', { alpha: a * (red ? 1 : 0.55) });
  finish(k, t);
  return still(cm, 'K3', { plateGain: 0.45 });
}

// S4c "It reached the internet": through the glass to the city. The thin dashed probe crosses in from the window edge
// on "reached", a few connection arcs touch lit buildings (有限联网), and all of it withdraws by the end of the line.
const CITY_NODES = [[620, 330], [760, 260], [880, 380], [480, 300], [980, 300], [700, 470], [380, 420]];   // A01v2 px
function S4c(t, k) {
  const cm = move(k, t, 'A01v2', [560, 380, 1.8], [590, 370, 1.86]);
  const f = k.layers.feed.ctx, e = k.layers.emit.ctx;
  const tReach = word(k, 5, 1).start, tNet = word(k, 5, 3).end;
  const reach = easeOutCubic(clamp((t - tReach) / 0.3)) * (1 - easeInOutCubic(clamp((t - tNet) / 0.3)));
  if (t >= tReach) {                                               // the breach: a hot point where it crosses the glass
    const b = grow(t, tReach, 0.05) * (1 - clamp((t - tReach - 0.35) / 0.3));
    if (b > 0) glowPath(e, [[110, 560], [111, 560]], { core: 12, halo: 54, alpha: b });
  }
  if (reach > 0) {
    const a = [110, 560], tip = cm.out([520, 520]);
    const end = [lerp(a[0], tip[0], reach), lerp(a[1], tip[1], reach)];
    line(f, a, end, { color: RED, width: 2.5, dash: [10, 8] });
    if (reach > 0.95) {
      const step = k.clock.beat(t).len / 4;
      CITY_NODES.forEach((n, i) => {                               // one arc per sixteenth, then they pulse
        const ti = tReach + 0.3 + i * step * 0.5;
        if (t < ti) return;
        const p = cm.out(n), g = grow(t, ti, 0.12) * reach;
        const mid = [(tip[0] + p[0]) / 2, Math.min(tip[1], p[1]) - 60];
        f.save(); f.globalAlpha = 0.85 * g; f.strokeStyle = i % 2 ? PALE : RED; f.lineWidth = 1.5;
        f.beginPath(); f.moveTo(...tip); f.quadraticCurveTo(...mid, ...p); f.stroke(); f.restore();
        glowPath(e, [p, [p[0] + 1, p[1]]], { core: 5, halo: 18, alpha: g * (0.7 + 0.3 * Math.cos((t - ti) * 12)) });
      });
      label(f, '有限联网', tip[0], tip[1] - 34, { size: 44, alpha: reach, align: 'center' });
    }
  }
  finish(k, t);
  return still(cm, 'A01v2', { emitGain: 2.2 });
}

// S5d "Eleven days": the count, mass type over the idle racks, one day per sixteenth from the word
function S5d(t, k) {
  const cm = move(k, t, 'K9e', [760, 470, 1.06], [740, 470, 1.1]);
  const o = k.layers.overlay.ctx, f = k.layers.feed.ctx;
  const t0 = word(k, 7, 0).start, step = k.clock.beat(t).len / 4;
  scrim(f, 420, 160, 1080, 680, 0.5);
  if (t >= t0) {
    const n = Math.round(rollNumber(1, 11, t, t0, t0 + 10 * step, 10));
    o.save(); o.textAlign = 'right'; o.shadowColor = 'rgba(0,0,0,0.6)'; o.shadowBlur = 24;
    font(o, F.monoB, 520, 0); o.fillStyle = n === 11 ? '#f4f6f9' : 'rgba(244,246,249,0.82)'; o.fillText(String(n), 1180, 700);
    font(o, F.sans, 96, 4); o.textAlign = 'left'; o.fillStyle = RED; o.fillText('天', 1210, 700);
    font(o, F.mono, 30, 6); o.fillStyle = 'rgba(236,241,244,0.8)'; o.fillText('训练暂停', 1214, 590);
    o.restore();
  }
  finish(k, t);
  return still(cm, 'K9e', { plateGain: 0.5 });
}

// S9h "through the": her last look, S7v3's slight smile back on the lens, framed closer; the comp draws the mark
function S9h(t, k) {
  const v = filmed('S9h') && video(k, t, 'S9h', [1170, 400, 1.28], [1170, 392, 1.33]);
  if (!v) { finish(k, t); return still(move(k, t, 'K7', [930, 380, 1.3], [930, 372, 1.34]), 'K7'); }
  finish(k, t);
  return clip(v, 'S9h');
}

function S9a(t, k) {
  const tClose = word(k, 15, 2).start, tShut = word(k, 15, 4).end;  // "The door is closed"
  if (filmed('S9a')) {                                             // native first/last frame take: the door really shuts
    const v = video(k, t, 'S9a'), f = k.layers.feed.ctx;
    detector(f, [540, 220, 140, 480], { t, t0: tShut, frame: k.frame, label: 'DNS 解析器', sub: '已修复', subColor: 'rgba(240,244,246,0.92)', size: 36 });
    sources(k);
    finish(k, t, { mark: false });
    return clip(v, 'S9a');
  }
  const shut = t >= tShut - 0.2 && k.size.K9e;
  const plate = shut ? 'K9e' : 'K4';
  const cm = move(k, t, plate, [700, 470, 1.04], [660, 470, 1.08]);
  const f = k.layers.feed.ctx, e = k.layers.emit.ctx;
  const p = easeInOutCubic(clamp((t - tClose) / (tShut - 0.2 - tClose)));
  if (!shut) {
    glowPath(e, [cm.out([528, 60]), cm.out([532, 700])], { core: 3, halo: 16, alpha: 0.5 * (1 - p) });
    if (t >= tClose) {                                             // animatic stand-in for the door leaf
      const [x0, y0] = cm.out([480, 0]), [x1, y1] = cm.out([480 + 100 * p, 760]);
      f.save(); f.fillStyle = 'rgba(6,8,11,0.96)'; f.fillRect(x0, y0, x1 - x0, y1 - y0); f.restore();
    }
  }
  detector(f, cm.box([480, 200, 100, 400]), { t, t0: tShut, frame: k.frame, label: 'DNS 解析器', sub: '已修复', subColor: 'rgba(240,244,246,0.92)', size: 36 });
  sources(k);
  finish(k, t);
  return still(cm, plate, { emitGain: 2.0 });
}

function S9b(t, k) {                                              // also S9b2: one stretch from cut_S9b to the end
  const T0 = cutAt(k, 'S9b');
  const cm = moveSpan(k, t, 'K9b', [836, 470, 1.0], [880, 480, 1.05], T0, DURATION);
  const e = k.layers.emit.ctx, f = k.layers.feed.ctx;
  const A = [390, 343], B = [1395, 533];
  const step = k.clock.beat(t).len / 4;
  const n = Math.floor((t - T0) / step);
  const long = i => hash2(i, 41) > 0.45;                           // a bit is a long or short hold
  const dt = (t - T0) - n * step, lvl = Math.exp(-dt / (step * (long(n) ? 0.9 : 0.35)));
  const src = n % 2 === 0 ? A : B, dst = n % 2 === 0 ? B : A;
  glowPath(e, [cm.out(A), cm.out([A[0] + 1, A[1]])], { core: 6, halo: 26, alpha: n % 2 === 0 ? lvl : 0.15 });
  glowPath(e, [cm.out(B), cm.out([B[0] + 1, B[1]])], { core: 6, halo: 26, alpha: n % 2 === 0 ? 0.15 : lvl });
  // the timing signal crosses the die surface itself, not a diagram on top of it
  const u = clamp(dt / step);
  const head = [lerp(src[0], dst[0], u), lerp(src[1], dst[1], u)];
  const tail = [lerp(src[0], dst[0], Math.max(0, u - 0.25)), lerp(src[1], dst[1], Math.max(0, u - 0.25))];
  glowPath(e, [cm.out(tail), cm.out(head)], { core: 2, halo: 9, alpha: 0.8 * lvl });
  scrim(f, W - 760, 170, 680, 180, 0.5);                           // the die's dark corner keeps the type clean
  slam(f, placed(W - 110, 250, c => {
    label(c, '另一项红队测试', 0, 0, { size: 48, align: 'right' });
    label(c, 'CPU 缓存计时 · 漏洞已修补', 0, 62, { size: 32, family: F.sansR, align: 'right' });
  }), { t, t0: T0 + 1 / FPS, ax: W - 110, ay: 250, drop: 8, ghosts: 0 });
  sources(k);
  finish(k, t);
  const o = k.layers.overlay.ctx, tEnd = word(k, 16, 6).end;      // after the last word, the card lands
  slam(o, placed(1560, 560, c => {
    font(c, F.monoB, 64, 6); c.fillStyle = '#f2f4f7'; c.fillText('03:48', 0, 0);
    font(c, F.mono, 22, 6); c.fillStyle = 'rgba(236,241,244,0.85)'; c.fillText('IRIS · NEWS 01', 4, 40);
  }), { t, t0: Math.min(tEnd, DURATION - 0.4), ax: 1560, ay: 560, drop: 8 });
  return still(cm, 'K9b', { emitGain: 2.4 });
}

// ---------- the series frame (user on c8: 「整体差不多了,还少点东西感觉」) ----------
// Every shot sits inside the series' HUD chrome (T01's corner brackets and centre ticks at 0.32; the EV toolkit's budgeted
// density has chrome in every shot), pulled in to 18 px so the top-left bracket clears the platform's AI mark
// (25, 26, 152 x 70). Every verse cut lands with a one-frame print burst (halftone and misregistration, no flash): the
// spec's dither transition. Neither adds words.
const CHROME = { inset: 18, alpha: 0.42, mark: 30, lw: 1.5 };     // T01's 1 px at 0.32 vanishes in IRIS's grain
// c10: on the cut frame only (a decay over the next frames read as a cue onset in qa.py) and not in the chorus, whose
// kicks already hit the print (cut bursts on top alternated with the kick hits: a strobe cell in qa.py)
// A burst never lands on a graphic's entrance: a cut with a timed graphic cue within 4 frames after it gets none (S4c's
// probe arrives 3 frames after its cut).
function cutBurst(t, k) {
  const ev = k.data.events.events, f = Math.round(t * FPS), fr = e => Math.ceil(e.t * FPS - 1e-6);
  if (t >= ev.cut_S8a.t && t < ev.cut_S9a.t) return 0;
  for (const [key, e] of Object.entries(ev)) {
    if (!key.startsWith('cut_') || f !== fr(e)) continue;
    const cueSoon = Object.entries(ev).some(([id, c]) => !id.startsWith('cut_') && c.roi && fr(c) > f && fr(c) <= f + 4);
    return cueSoon ? 0 : 1;
  }
  return 0;
}
function framed(scene) {
  return (t, k) => {
    const p = scene(t, k);
    chrome(k.layers.feed.ctx, W, H, CHROME);
    const b = cutBurst(t, k);
    if (b > 0) {
      const g = p.grade || {};
      p.grade = { ...g, uHalftone: (g.uHalftone ?? 0.10) + 0.22 * b, uMisreg: (g.uMisreg ?? 0) + 2.2 * b };
    }
    return p;
  };
}

install({
  width: W, height: H, fps: FPS, canvasId: 'stage',
  fontsUrl: 'fonts', beatsUrl: 'data/beats.json', hitsUrl: 'data/hits.json', musicUrl: 'data/music.json',
  data: { words: 'data/words.json', events: 'data/events.json', tracks: 'data/tracks.json', chorus: 'data/chorus.json' },
  images: Object.fromEntries(['K1a', 'K1b', 'K3', 'K4', 'K5', 'K5b', 'K7', 'K8b', 'K9b', 'K9e', 'P7', 'P8b', 'P8c', 'A01v2', 'A02',
    ...Object.entries(MOUTH.regions).flatMap(([r, g]) => Object.keys(g.variants).map(s => `${MOUTH.base}${r}${s}`))]
    .map(p => [p, { url: `plates/${p}.png` }])),
  sequences: Object.fromEntries(Object.entries(SEQ).map(([id, s]) => [id, { dir: s.dir, count: s.count }])),
  scenes: Object.fromEntries(Object.entries({ S1, S2, S3, S3d, S4, S4c, S5, S5d, S6, S7, S9a, S9b, S9h, S9b2: S9b,
    S8a: chorusShot, S8a_x: chorusShot, S8e: chorusShot, S8a2: chorusShot, S8b: chorusShot, S8b_x: chorusShot, S8w: chorusShot,
    S8b_x2: chorusShot }).map(([id, scene]) => [id, framed(scene)])),
  pickShot,
});
