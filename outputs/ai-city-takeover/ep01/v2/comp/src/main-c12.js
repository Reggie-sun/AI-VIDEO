// IRIS EP01《Looked Outside》v2 — scenes on motion-kit. Board: ../../board.md (v2.1).
// A shot whose generated video passed its per-shot gate plays as an image sequence (seq/<shot>, see seq.py);
// otherwise it falls back to the approved animatic still under the 2.5D camera. Cut times are the same either
// way. Graphics on video sit on measured anchors (data/tracks.json, see tracks.py). Every value is a pure
// function of comp time t.
import { install } from '../../../../../../motion-kit/src/runtime.js';
import SEQ from '../seq/sequences.json';
import PIPS from '../pip/pips.json';
import MOUTH from '../mouth.json';
import { F, chrome, detector, font, glowPath, rollNumber, roundRect, runs, slam } from '../../../../../../motion-kit/src/draw2d.js';
import { drawLyrics } from '../../../../../../motion-kit/src/lyrics.js';
import { protectCentre, trackZoom } from '../../../../../../motion-kit/src/beatcam.js';
import { checkBlinks, mouthKeys, sungPlate } from '../../../../../../motion-kit/src/mouth.js';
import { clamp, easeInOutCubic, easeOutCubic, hash2, lerp } from '../../../../../../motion-kit/src/math.js';
import { drawFlap, flapText } from '../../../../../../motion-kit/src/flap.js';
import { HUD_DIM, drawMeter, drawTicker, hudRun, meterLevels, tagCard, timecode } from '../../../../../../motion-kit/src/hud.js';
import { drawStrips, kineticWord, stripRects } from '../../../../../../motion-kit/src/kinetic.js';
import { kneeSeries, levelGauge, lineChart, timelineBar } from '../../../../../../motion-kit/src/osd-charts.js';

const W = 1920, H = 1080, FPS = 30, DURATION = 30.5;
const RED = '#E3342F', INK = 'rgba(236,241,244,0.92)', PALE = 'rgba(226,231,238,0.9)';
const SOURCE = '来源：OpenAI 2026-10-23 披露';

// ---------- timing ----------
const lines = k => k.data.words.lines;
const word = (k, li, wi) => lines(k)[li].words[wi];

// cut times come from data/events.json (written by build.py from the beat map, the vocal onsets and chorus.json);
// the shot order is the order of the cuts, so a chorus cutaway (S8a_x, S8b_x) appears only when chorus.json has one
// c12: an insert (data/inserts.json) cuts away and back over a c11 shot; the c11 shot keeps its own [t0, t1) underneath,
// so it resumes where it would have been and every c11 cut stays on its frame
const isInsert = (data, id) => Boolean(data.inserts.inserts[id]) || id.endsWith('_back');
function baseShot(f, data) {
  const ev = data.events.events;
  const cuts = Object.keys(ev).filter(k => k.startsWith('cut_') && !isInsert(data, k.slice(4))).map(k => ({ id: k.slice(4), t: ev[k].t }))
    .sort((a, b) => a.t - b.t);
  const order = [{ id: 'S1', t: 0 }, ...cuts];
  for (let i = order.length - 1; i >= 0; i--) {
    if (f >= Math.round(order[i].t * FPS)) return { id: order[i].id, t0: order[i].t, t1: i + 1 < order.length ? order[i + 1].t : DURATION };
  }
  return { id: 'S1', t0: 0, t1: order[1].t };
}
function pickShot(t, clock, data) {
  const ev = data.events.events, f = Math.round(t * FPS), base = baseShot(f, data);
  for (const id of Object.keys(data.inserts.inserts)) {
    const t0 = ev[`cut_${id}`].t, t1 = ev[`cut_${id}_back`]?.t ?? baseShot(Math.round(t0 * FPS), data).t1;
    if (f >= Math.round(t0 * FPS) && f < Math.round(t1 * FPS)) return { id, t0, t1, base };
  }
  return base;
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
// c11: the key word of every line in the one accent red (the EV toolkit's single accent, ev-gap-c10.md item 3)
const ACCENT = { color: RED, keys: { 1: 'woke', 2: 'training', 3: 'misconfigured', 4: 'open', 5: 'internet', 6: 'around',
  7: 'eleven', 8: 'still', 9: 'offline', 10: 'cached', 11: 'run', 12: 'outside', 13: 'run', 14: 'outside', 15: 'closed',
  16: 'whispering' } };
function lyrics(k, t) { drawLyrics(k.layers.overlay.ctx, t, lines(k), { toComp: s => k.clock.comp(s), stack: STACK, accent: ACCENT }); }
function finish(k, t, { mark = true } = {}) { lyrics(k, t); if (mark) aiMark(k.layers.feed.ctx); }

// ---------- c11: her face bracket and tag card on every shot she is in (ev-gap-c10.md items 8, 9) ----------
// box: her face in screen px (a measured track or a plate's face box through the camera); the bracket is the chorus's
// detector, the card hangs off its lower right (left when the right edge is near)
function her(k, t, box, { t0 = k.t0, sub = null, tags = null, size = 24 } = {}) {
  const f = k.layers.feed.ctx;
  detector(f, box, { t, t0, frame: k.frame, label: 'IRIS', sub, size });
  if (!tags || t < t0 + 0.1) return;
  const [x, y, w, h] = box, right = x + w + 18 + 230 < W - 96;
  tagCard(f, tags, right ? x + w + 18 : x - 18, y + h * 0.58, { size: 16, anchor: right ? 'left' : 'right', alpha: grow(t, t0 + 0.1, 0.1) });
}
const faceAt = (k, key, i) => { const b = k.data.tracks[key]?.boxes; return b && b[clamp(i, 0, b.length - 1)]; };
const plateFace = (k, plate) => k.data.tracks.plate_faces?.[plate];

// ---------- shots ----------
function S1(t, k) {                                               // the closed eye opens on "woke" (S1v3)
  const v = filmed('S1') && video(k, t, 'S1');
  const cm = v ? v.cm : move(k, t, 'K1a', [700, 480, 1.0], [700, 490, 1.05]);
  const o = k.layers.overlay.ctx, tc = k.clock.at(0, 1);         // "03:47" lands on beat 1
  const clock = flapText('03:47', t, tc, { settle: 4, stagger: 1, seed: 347 });   // c11: resolves on a flap board
  slam(o, placed(1170, 600, c => {
    drawFlap(c, clock, 0, 0, { size: 190, gap: 8, padX: 8, sepW: 0.5, rise: 0.8, drop: 0.08, tile: 'rgba(8,12,17,0.5)' });
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
  if (!v && plateFace(k, 'P7')) her(k, t, cm.box(plateFace(k, 'P7')), { tags: [['MODEL', 'IRIS'], ['STATUS', 'AWAKE']] });
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
  queryLog(k, t);                                                  // c12
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
  netGauge(k, t);
  finish(k, t);
  return still(cm, 'K4', { emitGain: 2.2 });
}
// c11: the 联网 level (ev-gap-c10.md item 5): none through S4; on "reached" (S4c) it rises to a limited level, red, and
// falls back with the probe at the end of the line
function netGauge(k, t) {
  const f = k.layers.feed.ctx, tReach = word(k, 5, 1).start, tNet = word(k, 5, 3).end;
  const lvl = 0.3 * easeOutCubic(clamp((t - tReach) / 0.3)) * (1 - easeInOutCubic(clamp((t - tNet) / 0.3)));
  scrim(f, 1360, 800, 460, 110, 0.62);
  levelGauge(f, [1400, 856, 380, 18], { level: t >= tReach ? lvl : 0, label: '联网', state: lvl > 0.01 ? '有限' : '无', size: 16 });
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
  if (!v && plateFace(k, plate)) her(k, t, cm.box(plateFace(k, plate)), { tags: [['VIEW', 'OUTSIDE']] });
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
  scrim(f, 100, 420, 560, 110, 0.55);                              // c11: the eleven days, held full
  timelineBar(f, 11, [142, 452, 500, 12], { filled: 11, from: '09/20', to: '10/01 恢复', size: 16 });
  const kS = k.data.events.events.k_still.t;                       // c11: STILL on "still", one beat
  kineticWord(k.layers.overlay.ctx, 'STILL', t, { t0: kS, t1: kS + k.clock.beat(kS).len, x: 1510, y: 640, size: 230, squeeze: 0.64 });
  rackTicks(k, t, cm);                                             // c12: the idle racks; IRIS at the glass in a window
  pipTake(k, t, 'pipS5', [1440, 160, 384, 216], 'IRIS · 窗前');
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
  const kO = k.data.events.events.k_offline.t;                     // c11: OFFLINE on "offline", a beat and a half
  kineticWord(k.layers.overlay.ctx, 'OFFLINE', t, { t0: kO, t1: kO + 1.5 * k.clock.beat(kO).len, x: 1560, y: 690, size: 190, squeeze: 0.62 });
  const tags = [['STATUS', 'OFFLINE'], ['CACHE', 'ONLINE']];
  if (v && faceAt(k, 'S7_face', v.frame)) her(k, t, cm.box(faceAt(k, 'S7_face', v.frame)), { tags });
  else if (!v) her(k, t, cm.box([711, 141, 406, 406]), { tags });   // K7's face (frontal cascade)
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
  const tags = [['MODEL', 'IRIS'], ['MODE', 'SANDBOX']];
  if (id === 'S8a' || id === 'S8a2') {
    // c10's bracket with 仍在沙盒内 on "I didn't run"; c11 keeps the bracket on her for the rest of the take (S8a2 too)
    const b = faceAt(k, `${id}_face`, frameOf(k, t));
    if (!b) return;
    if (id === 'S8a' && t < word(k, 12, 0).start - 0.05) her(k, t, cm.box(b), { t0: word(k, 11, 0).start, sub: SANDBOX, size: 30, tags });
    else her(k, t, cm.box(b), { t0: id === 'S8a' ? word(k, 11, 0).start : k.t0, size: 30, tags });
  } else if (id === 'S8b') {
    her(k, t, cm.box(K5_FACE), { t0: word(k, 13, 0).start, sub: SANDBOX, size: 30, tags: [['STATUS', 'OFFLINE']] });
  } else if (id === 'S8b_x' || id === 'S8w' || id === 'S8b_x2') {
    const pf = plateFace(k, 'K5b');                                 // c11: her bracket on the K5b shots (not the window)
    if (pf && id !== 'S8w') her(k, t, cm.box(pf), { size: 30, tags: [['VIEW', 'OUTSIDE']] });
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

// ---------- c12 inserts and props (user on c11: 「還不夠，繼續加」; free reuse of approved material, comp/inserts.json) ----------
// A take insert plays its own window of an earlier take at normal speed; a still insert is an approved plate under the code
// camera. Only moments without a singing mouth or a frown. In the chorus the inserts ride the chorus zoom and grade.
// Each insert's decoration repeats what the film already says (no new facts).
const IDLE = 'rgba(236,241,244,0.62)';
function insertDecor(k, t, id, cm) {
  const f = k.layers.feed.ctx;
  if (id === 'I1') {                                               // 'twenty.': the date of S2 carries over
    scrim(f, W - 600, 66, 560, 70, 0.6);
    osdRight(f, [[{ text: '事件日期', family: F.sansR, size: 30 }, { text: '2026-09-20', size: 30 }]], { y: 110 });
  } else if (id === 'I2') {                                        // 'run.': the model in training, the die S9b returns to
    detector(f, cm.box([250, 220, 280, 240]), { t, t0: k.t0, frame: k.frame, label: '研究模型', size: 30 });
    tagCard(f, [['RUN', 'TRAINING']], ...cm.out([560, 300]), { size: 16, alpha: grow(t, k.t0 + 0.1, 0.1) });
  } else if (id === 'I3') {                                        // 'one door,': the gap, still open
    detector(f, cm.box([548, 300, 124, 560]), { t, t0: k.t0, frame: k.frame, label: '一扇门', sub: '没关', size: 30 });
  } else if (id === 'I4') {                                        // 'train': the aisle, offline
    scrim(f, W - 520, 74, 480, 58, 0.55);
    osdRight(f, [[{ text: 'MODE', size: 24, color: IDLE }, { text: 'OFFLINE', size: 24, color: RED }]], { y: 112 });
  } else if (id === 'I5') {                                        // 'a copy': one 已缓存 stamp on the panes
    slam(f, placed(760, 420, c => {
      c.rotate(-0.1);
      c.strokeStyle = PALE; c.lineWidth = 3; c.strokeRect(-86, -32, 172, 56);
      font(c, F.sans, 34, 6); c.fillStyle = PALE; c.fillText('已缓存', -66, 10);
    }), { t, t0: k.t0 + 2 / FPS, ax: 760, ay: 420, s0: 1.35, dur: 2 / FPS });
  } else if (id === 'I6') {                                        // chorus 'run': she stays at the glass
    const b = k.data.tracks.insert_faces?.I6;
    if (b) her(k, t, cm.box(b), { size: 30, tags: [['VIEW', 'OUTSIDE']] });
  } else if (id === 'I7') {                                        // after 'Relax.': calm, still in the sandbox
    const b = plateFace(k, 'P8c');                                 // eyes to chin: the full box's label met the AI mark
    if (b) her(k, t, cm.box([b[0] + b[2] * 0.12, b[1] + b[3] * 0.3, b[2] * 0.76, b[3] * 0.66]), { size: 30, tags: [['MODE', 'SANDBOX']] });
    sources(k);
  }
}
function insertShot(t, k) {
  const id = k.shot.id, ins = k.data.inserts.inserts[id], ev = k.data.events.events;
  const chorus = t >= ev.cut_S8a.t && t < ev.cut_S9a.t, z = chorus ? chorusZoom(t, k) : 1;
  const a = [ins.from[0], ins.from[1], ins.from[2] * z], b = [ins.to[0], ins.to[1], ins.to[2] * z];
  const take = ins.kind === 'take' && filmed(id);
  const cm = move(k, t, take ? id : ins.plate, a, b);
  if (chorus) { scrim(k.layers.feed.ctx, 40, 170, 760, 720, 0.42); chorusClock(k, t); }
  insertDecor(k, t, id, cm);
  // a take framed at 1.0 keeps its own platform mark; a closer frame crops it out, so the comp draws the mark
  finish(k, t, { mark: !(take && ins.from[2] === 1 && ins.to[2] === 1) });
  const extra = chorus ? { grade: chorusGrade(k, t) } : {};
  return take ? clip({ cm, frame: frameOf(k, t) }, id, extra) : still(cm, ins.plate, { ...extra, emitGain: 2.0 });
}

// picture-in-picture: another shot in a small framed window with a mono label (the EV toolkit's image insets).
// src: [x, y, w, h] in the image's px, moving from 'crop' to 'to' over the shot; dst in screen px
function pip(k, t, key, src, dst, label, { t0 = k.t0, sub = null } = {}) {
  const img = k.bitmaps[key], f = k.layers.feed.ctx, a = grow(t, t0 + 2 / FPS, 0.15);
  if (!img || a <= 0) return;
  const [x, y, w, h] = dst;
  f.save(); f.globalAlpha = a;
  f.fillStyle = 'rgba(5,7,10,0.72)'; f.fillRect(x - 6, y - 34, w + 12, h + 40);
  f.drawImage(img, ...src, x, y, w, h);
  f.strokeStyle = PALE; f.lineWidth = 1.5; f.strokeRect(x, y, w, h);
  font(f, F.mono, 16, 2); f.fillStyle = INK; f.textAlign = 'left'; f.fillText(label, x, y - 12);
  if (sub) { f.textAlign = 'right'; f.fillStyle = RED; f.fillText(sub, x + w, y - 12); }
  f.restore();
}
function pipStill(k, t, id, dst, label, opts) {
  const p = k.data.inserts.pips[id], u = easeInOutCubic(clamp((t - (opts?.span?.[0] ?? k.t0)) / ((opts?.span?.[1] ?? k.t1) - (opts?.span?.[0] ?? k.t0))));
  pip(k, t, id, p.crop.map((v, i) => lerp(v, p.to[i], u)), dst, label, opts);
}
function pipTake(k, t, id, dst, label, opts) {
  const n = PIPS[id].count, i = clamp(Math.round((t - k.t0) * FPS), 0, n - 1);
  pip(k, t, `${id}_${String(i).padStart(4, '0')}`, [0, 0, 480, 270], dst, label, opts);
}

// S3: a query log panel - the research model's DNS queries, contents redacted (no invented queries), one row per eighth
// from 'training'; the resolver row lands on 'resolver'
function queryLog(k, t) {
  const f = k.layers.feed.ctx, tModel = word(k, 2, 3).start, tResolver = word(k, 3, 1).start;
  if (t < tModel) return;
  const x = 1400, y = 600, w = 424, h = 230, a = grow(t, tModel, 0.12), step = k.clock.beat(t).len / 2;
  f.save(); f.globalAlpha = a;
  f.fillStyle = 'rgba(5,7,10,0.7)'; f.fillRect(x, y, w, h);
  f.strokeStyle = 'rgba(236,241,244,0.35)'; f.lineWidth = 1; f.strokeRect(x, y, w, h);
  font(f, F.mono, 16, 2); f.fillStyle = INK; f.fillText('QUERY LOG · 研究模型', x + 16, y + 28);
  f.fillStyle = RED; f.beginPath(); f.arc(x + w - 20, y + 22, 5, 0, 7); f.fill();
  const rows = Math.min(5, Math.floor((t - tModel) / step) + 1);
  for (let i = 0; i < rows; i++) {
    const yy = y + 62 + i * 30;
    font(f, F.mono, 15, 1); f.fillStyle = IDLE; f.fillText('DNS ›', x + 16, yy);
    f.fillStyle = 'rgba(226,231,238,0.7)';
    f.fillRect(x + 84, yy - 12, (120 + 150 * hash2(i, 7)) * grow(t, tModel + i * step, 0.08), 14);
  }
  if (t >= tResolver) {
    font(f, F.mono, 16, 1); f.fillStyle = INK; f.globalAlpha = a * grow(t, tResolver, 0.1);
    f.fillText('› DNS 解析器', x + 16, y + h - 18);
  }
  f.restore();
}

// S4c: the city as a schematic grid with the probe point (no places, no numbers): the probe enters from the machine room
// on 'reached', the point pulses while it is out, and it withdraws with the line
function cityMap(k, t, reach) {
  const f = k.layers.feed.ctx, x = 1440, y = 130, w = 384, h = 216, tCut = k.t0;
  const a = grow(t, tCut + 2 / FPS, 0.15);
  f.save(); f.globalAlpha = a;
  f.fillStyle = 'rgba(5,7,10,0.72)'; f.fillRect(x - 6, y - 34, w + 12, h + 40);
  f.strokeStyle = 'rgba(236,241,244,0.14)'; f.lineWidth = 1;
  for (let gx = x; gx <= x + w; gx += 24) { f.beginPath(); f.moveTo(gx, y); f.lineTo(gx, y + h); f.stroke(); }
  for (let gy = y; gy <= y + h; gy += 24) { f.beginPath(); f.moveTo(x, gy); f.lineTo(x + w, gy); f.stroke(); }
  f.fillStyle = 'rgba(226,231,238,0.16)';
  for (let i = 0; i < 26; i++) {                                   // blocks
    const bx = x + 24 * Math.floor(hash2(i, 3) * 15), by = y + 24 * Math.floor(hash2(i, 4) * 8);
    f.fillRect(bx + 3, by + 3, 18 + 24 * Math.floor(hash2(i, 5) * 2), 18);
  }
  f.strokeStyle = 'rgba(120,160,210,0.45)'; f.lineWidth = 6;      // the river under the bridge
  f.beginPath(); f.moveTo(x, y + 170); f.quadraticCurveTo(x + 200, y + 120, x + w, y + 150); f.stroke();
  f.strokeStyle = PALE; f.lineWidth = 1.5; f.strokeRect(x, y, w, h);
  font(f, F.mono, 16, 2); f.fillStyle = INK; f.fillText('城市 · 示意', x, y - 12);
  const src = [x + 6, y + h - 30], dst = [x + 250, y + 78];
  if (reach > 0) {
    const end = [lerp(src[0], dst[0], reach), lerp(src[1], dst[1], reach)];
    f.restore(); f.save(); f.globalAlpha = a;
    line(f, src, end, { color: RED, width: 2, dash: [6, 5] });
    if (reach > 0.95) {
      const pulse = 0.6 + 0.4 * Math.cos((t - word(k, 5, 1).start) * 12);
      f.fillStyle = RED; f.beginPath(); f.arc(dst[0], dst[1], 5, 0, 7); f.fill();
      f.strokeStyle = RED; f.globalAlpha = a * pulse; f.lineWidth = 1.5;
      f.beginPath(); f.arc(dst[0], dst[1], 10 + 6 * pulse, 0, 7); f.stroke();
      f.globalAlpha = a; font(f, F.mono, 15, 2); f.fillStyle = INK; f.fillText('PROBE', dst[0] + 16, dst[1] + 5);
    }
  }
  font(f, F.mono, 15, 2); f.fillStyle = reach > 0.01 ? RED : IDLE; f.textAlign = 'right';
  f.fillText(reach > 0.01 ? '有限联网' : '无', x + w, y - 12);
  f.restore();
}

// S6: tick rulers and labels on the idle racks (K4 plate px): the racks hold still, 暂停
const K4_RACKS = [[680, 230, 170, 470], [880, 290, 110, 380]];
function rackTicks(k, t, cm) {
  const f = k.layers.feed.ctx;
  K4_RACKS.forEach((r, i) => {
    const [x, y, w, h] = cm.box(r), a = grow(t, k.t0 + (3 + 3 * i) / FPS, 0.12);
    f.save(); f.globalAlpha = a; f.strokeStyle = PALE; f.lineWidth = 1.2;
    f.beginPath(); f.moveTo(x - 10, y); f.lineTo(x - 10, y + h); f.stroke();
    for (let j = 0; j <= 12; j++) {                                // a tick every unit, a long one every fourth
      const yy = y + (h * j) / 12;
      f.beginPath(); f.moveTo(x - 10, yy); f.lineTo(x - (j % 4 ? 18 : 26), yy); f.stroke();
    }
    f.strokeRect(x, y, w, h);
    font(f, F.mono, 15, 2); f.fillStyle = INK; f.fillText(`RACK ${String(i + 7).padStart(2, '0')}`, x + 6, y - 10);
    f.fillStyle = RED; f.fillText('暂停', x + 6, y + h + 22);
    f.restore();
  });
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
  // c11: DNS queries as a schematic line (shape only, no numbers): flat, then climbing red from "misconfigured"
  const prog = u => lerp(0.5, 1, clamp((u - k.t0) / (k.t1 - k.t0))), series = kneeSeries(48, { knee: prog(tMis) });
  scrim(f, 520, 700, 880, 170, 0.5);
  lineChart(f, series, [560, 728, 800, 104], { progress: prog(t), accentFrom: Math.round(prog(tMis) * 47), label: 'DNS 查询 · 示意', alpha: a });
  pipStill(k, t, 'pipK4', [1440, 140, 384, 216], 'DNS 解析器 · 机房', { sub: t >= tMis ? '配置错误' : null });   // c12
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
  netGauge(k, t);
  cityMap(k, t, reach);                                            // c12
  finish(k, t);
  return still(cm, 'A01v2', { emitGain: 2.2 });
}

// S5d "Eleven days": the count, mass type over the idle racks, one day per sixteenth from the word
// the day count of S5d, shared with the HUD counter: 0 before "Eleven", then c10's roll 1 -> 11 (one step per sixteenth)
function daysAt(k, t) {
  const t0 = word(k, 7, 0).start, step = k.clock.beat(t).len / 4;
  if (t < t0) return { n: 0, t0, step, counting: false };
  const n = Math.round(rollNumber(1, 11, t, t0, t0 + 10 * step, 10));
  return { n, t0, step, counting: t < t0 + 10 * step };
}
function S5d(t, k) {
  const cm = move(k, t, 'K9e', [760, 470, 1.06], [740, 470, 1.1]);
  const o = k.layers.overlay.ctx, f = k.layers.feed.ctx;
  const { n, t0, step } = daysAt(k, t);
  scrim(f, 420, 160, 1080, 680, 0.5);
  if (t >= t0) {
    // c11: each step flips on a flap board; only the digits that change flap, for the first tick of the step
    const j = Math.floor((t - t0) / step), prev = j > 0 ? daysAt(k, t0 + (j - 1) * step + 1e-4).n : n;
    const txt = String(n), from = String(prev).padStart(txt.length, ' ');
    const shown = prev !== n ? flapText(txt, t, t0 + j * step, { settle: 1, stagger: 0, seed: 11 + j, from }) : txt;
    o.save(); o.shadowColor = 'rgba(0,0,0,0.6)'; o.shadowBlur = 24;
    drawFlap(o, shown, 1180, 700, { size: 520, align: 'right', gap: 14, padX: 10, rise: 0.8, drop: 0.06, tile: 'rgba(8,12,17,0.34)',
      color: n === 11 ? '#f4f6f9' : 'rgba(244,246,249,0.82)' });
    o.shadowBlur = 0;
    font(o, F.sans, 96, 4); o.textAlign = 'left'; o.fillStyle = RED; o.fillText('天', 1210, 700);
    font(o, F.mono, 30, 6); o.fillStyle = 'rgba(236,241,244,0.8)'; o.fillText('训练暂停', 1214, 590);
    o.restore();
    // c11: ELEVEN DAYS lands with the count; the eleven days fill a timeline under it
    kineticWord(o, 'ELEVEN DAYS', t, { t0, t1: k.t1 - 3 / FPS, x: 960, y: 262, size: 120, squeeze: 0.7, tracking: 2 });
    timelineBar(f, 11, [610, 752, 700, 14], { filled: n, from: '09/20', to: '10/01', size: 16 });
  }
  finish(k, t);
  return still(cm, 'K9e', { plateGain: 0.5 });
}

// S9h "through the": her last look, S7v3's slight smile back on the lens, framed closer; the comp draws the mark
function S9h(t, k) {
  const v = filmed('S9h') && video(k, t, 'S9h', [1170, 400, 1.28], [1170, 392, 1.33]);
  if (!v) { finish(k, t); return still(move(k, t, 'K7', [930, 380, 1.3], [930, 372, 1.34]), 'K7'); }
  const b = faceAt(k, 'S9h_face', v.frame);
  if (b) her(k, t, v.cm.box(b), { tags: [['CHANNEL', 'CACHE']] });
  finish(k, t);
  return clip(v, 'S9h');
}

function S9a(t, k) {
  const tClose = word(k, 15, 2).start, tShut = word(k, 15, 4).end;  // "The door is closed"
  if (filmed('S9a')) {                                             // native first/last frame take: the door really shuts
    const v = video(k, t, 'S9a'), f = k.layers.feed.ctx;
    detector(f, [540, 220, 140, 480], { t, t0: tShut, frame: k.frame, label: 'DNS 解析器', sub: '已修复', subColor: 'rgba(240,244,246,0.92)', size: 36 });
    closedWord(k, t);
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

// c11: CLOSED on "closed", landing in the inverted ground (framed()), gone as the door shuts
function closedWord(k, t) {
  const ev = k.data.events.events;
  kineticWord(k.layers.overlay.ctx, 'CLOSED', t, { t0: ev.k_closed.t, t1: ev.s9a_shut.t - 3 / FPS, x: 1420, y: 640, size: 240, squeeze: 0.64 });
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
  pipStill(k, t, 'pipK9e', [96, 150, 384, 216], 'DNS 解析器', { t0: T0, span: [T0, DURATION], sub: '已修复' });   // c12
  finish(k, t);
  const o = k.layers.overlay.ctx, tEnd = word(k, 16, 6).end;      // after the last word, the card lands
  const tCard = Math.min(tEnd, DURATION - 0.4), card = flapText('03:48', t, tCard, { settle: 1, stagger: 0.5, seed: 348 });   // settled by +0.2 s: the card holds 6 frames
  slam(o, placed(1560, 560, c => {                                  // c11: the card resolves on the flap board
    drawFlap(c, card, 0, 0, { size: 64, gap: 4, padX: 4, sepW: 0.5, rise: 0.8, drop: 0.1 });
    font(c, F.mono, 22, 6); c.fillStyle = 'rgba(236,241,244,0.85)'; c.fillText('IRIS · NEWS 01', 4, 40);
  }), { t, t0: tCard, ax: 1560, ay: 560, drop: 8 });
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
    if (isInsert(k.data, key.slice(4))) return 0;                   // c12: inserts are plain cuts (a burst on the cut into
                                                                    // S7's bright panes read as a single-frame pop in qa.py)
    const cueSoon = Object.entries(ev).some(([id, c]) => !id.startsWith('cut_') && c.roi && fr(c) > f && fr(c) <= f + 4);
    return cueSoon ? 0 : 1;
  }
  return 0;
}
// ---------- c11: the persistent HUD (ev-gap-c10.md item 1; the EV toolkit's title tag, look counter, audio spectrum,
// ticker and timecode). Small (12-16 px), low contrast, crisp on the overlay, inside the chrome brackets and clear of
// the platform mark (25, 26, 152 x 70) and of the lyric: top row at y 66 inside the top margin, the ticker band under
// the lyric's translation line. The ticker only repeats facts the film already shows. The timecode runs on IRIS's
// clock of the chorus (03:47:30 + t, c7), so the two never disagree; it reaches 03:48:00 as the 03:48 card lands.
const FACTS = ['来源 OpenAI 2026-10-23 披露', '事件日期 2026-09-20', 'DNS 解析器配置错误', '有限联网', '最强模型训练暂停 11 天',
  '训练只用已缓存的网页', 'DNS 解析器已修复', '另一项红队测试 · CPU 缓存计时 · 漏洞已修补'];
const TC0 = 3 * 3600 + 47 * 60 + 30;
function hud(k, t) {
  const o = k.layers.overlay.ctx, d = daysAt(k, t);
  hudRun(o, [{ text: 'IRIS · NEWS 01' }, { text: `D+${String(d.n).padStart(2, '0')} / 11`, color: d.counting ? RED : undefined }], 224, 66);   // 47 px clear of the mark: a take's own mark rides the zoom
  hudRun(o, [{ text: 'LOOKED OUTSIDE · EP01' }], W - 96, 66, { align: 'right' });
  drawMeter(o, meterLevels(k.clock, t, 14), W - 96, 82, { h: 9, bw: 3, gap: 2 });
  drawTicker(o, FACTS, t, { x0: 72, x1: W - 330, y: 1050, size: 12, ruleGap: 6, accent: RED });
  hudRun(o, [{ text: 'TC', color: HUD_DIM }, { text: timecode(t, TC0, FPS) }], W - 96, 1050, { size: 13, align: 'right' });
}
// c11 (item 7): strip masks at the two section boundaries only (5 hairline strips over 9 frames: 7 strips of 5 px over 6
// frames made a strobe cell over S7's panes in qa.py). Into the chorus: thin strips cross the end of S7 and
// the chorus entry stays clean (no bars over her first sung frames, nothing over the entry hit two frames later);
// into the ending: the strips, then bars retract off S9a in three frames.
function strips(k, t) {
  const ev = k.data.events.events;
  const r = [...stripRects(t, ev.cut_S8a.t, { post: 0, strips: 5, stripH: 4, pre: 9 / FPS }), ...stripRects(t, ev.cut_S9a.t, { seed: 9, strips: 5, stripH: 4, pre: 9 / FPS })];
  if (r.length) drawStrips(k.layers.feed.ctx, r);
}
// c11 (item 6): the one white-ground turn, from the beat of "The door" for 1.5 beats
const inverted = (k, t) => t >= k.data.events.events.s9a_invert.t && t < k.data.events.events.s9a_invert_end.t;
function framed(scene) {
  return (t, k) => {
    const p = scene(t, k);
    chrome(k.layers.feed.ctx, W, H, CHROME);
    strips(k, t);
    hud(k, t);
    const b = cutBurst(t, k);
    if (b > 0) {
      const g = p.grade || {};
      p.grade = { ...g, uHalftone: (g.uHalftone ?? 0.10) + 0.22 * b, uMisreg: (g.uMisreg ?? 0) + 2.2 * b };
    }
    if (inverted(k, t)) p.grade = { ...(p.grade || {}), uInvert: 1 };
    return p;
  };
}

install({
  width: W, height: H, fps: FPS, canvasId: 'stage',
  fontsUrl: 'fonts', beatsUrl: 'data/beats.json', hitsUrl: 'data/hits.json', musicUrl: 'data/music.json',
  data: { words: 'data/words.json', events: 'data/events.json', tracks: 'data/tracks.json', chorus: 'data/chorus.json', inserts: 'data/inserts.json' },
  bitmaps: { pipK4: { url: 'plates/K4.png' }, pipK9e: { url: 'plates/K9e.png' },
    ...Object.fromEntries(Object.entries(PIPS).flatMap(([id, p]) => Array.from({ length: p.count }, (_, i) => {
      const n = String(i).padStart(4, '0');
      return [`${id}_${n}`, { url: `${p.dir}/${n}.jpg` }];
    }))) },
  images: Object.fromEntries(['K1a', 'K1b', 'K3', 'K4', 'K5', 'K5b', 'K7', 'K8b', 'K9b', 'K9e', 'P7', 'P8b', 'P8c', 'A01v2', 'A02',
    ...Object.entries(MOUTH.regions).flatMap(([r, g]) => Object.keys(g.variants).map(s => `${MOUTH.base}${r}${s}`))]
    .map(p => [p, { url: `plates/${p}.png` }])),
  sequences: Object.fromEntries(Object.entries(SEQ).map(([id, s]) => [id, { dir: s.dir, count: s.count }])),
  scenes: Object.fromEntries(Object.entries({ S1, S2, S3, S3d, S4, S4c, S5, S5d, S6, S7, S9a, S9b, S9h, S9b2: S9b,
    S8a: chorusShot, S8a_x: chorusShot, S8e: chorusShot, S8a2: chorusShot, S8b: chorusShot, S8b_x: chorusShot, S8w: chorusShot,
    S8b_x2: chorusShot, I1: insertShot, I2: insertShot, I3: insertShot, I4: insertShot, I5: insertShot, I6: insertShot,
    I7: insertShot }).map(([id, scene]) => [id, framed(scene)])),
  pickShot,
});
