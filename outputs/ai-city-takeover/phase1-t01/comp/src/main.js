// T01《最后一位人类司机》— scenes on motion-kit. Design: ../../design.md (rev 2).
// Every value below is a pure function of comp time t and the beat clock.
import { install } from '../../../../../motion-kit/src/runtime.js';
import { F, carDialog, chrome, detector, font, glowPath, osd, rollNumber, runs, slam, thousands, wipeOut } from '../../../../../motion-kit/src/draw2d.js';
import { applyH, clamp, easeInOutCubic, easeOutCubic, fbm1, hash2, invert3, lerp, noise1, remap, squareToQuad } from '../../../../../motion-kit/src/math.js';

const W = 1920, H = 1080, FPS = 30, DURATION = 10.0;
const PW = 1672, PH = 941, FIT = W / PW;
const RED = '#E3342F';

// ---------- camera ----------
function clampView(cx, cy, z) {
  const hx = (W / 2) / (FIT * z), hy = (H / 2) / (FIT * z);
  return [clamp(cx, hx, PW - hx), clamp(cy, hy, PH - hy), z, 0];
}
function cam(view, shake = [0, 0]) {
  const [cx, cy, z] = view, s = FIT * z;
  return { view, shake, s, out: ([x, y]) => [(x - cx) * s + W / 2 + shake[0], (y - cy) * s + H / 2 + shake[1]] };
}
const snap2 = (t, ts) => easeOutCubic(clamp((t - ts) / (2 / FPS)));          // lands in 2 frames
const impactKick = dt => (dt < 0 ? 0 : dt < 0.04 ? dt / 0.04 : Math.exp(-(dt - 0.04) / 0.03));

// ---------- packing ----------
function packLights(list) {
  const p = new Float32Array(32 * 4), c = new Float32Array(32 * 4);
  list.slice(0, 32).forEach((l, i) => { p.set([l.x, l.y, l.r, l.I], i * 4); c.set([...l.c, l.refl || 0], i * 4); });
  return { n: Math.min(32, list.length), p, c };
}
function packSegs(list, color) {
  const a = new Float32Array(64 * 4), w = new Float32Array(64 * 2);
  list.slice(0, 64).forEach((s, i) => { a.set([s.a[0], s.a[1], s.b[0], s.b[1]], i * 4); w.set([s.r, s.I], i * 2); });
  return { n: Math.min(64, list.length), a, w, color };
}
function packBodies(list) {
  const p = new Float32Array(12 * 4), a = new Float32Array(12);
  list.slice(0, 12).forEach((b, i) => { p.set([b.x, b.y, b.hw, b.hh], i * 4); a[i] = b.o; });
  return { n: Math.min(12, list.length), p, a };
}

// ---------- S1 road model (P1L plate px, measured: plates/measure/P1L-grid.png) ----------
const YH = 179, KZ = 461;
const xDivL = () => 1106;
const xDivR = y => 1290 + 0.483 * (y - 560);
const xEdgeL = y => 760 + 0.4167 * (900 - y);
const xEdgeR = y => 1270 + 0.638 * (y - 230);
const laneC = (lane, y) => (lane === 0 ? (xEdgeL(y) + xDivL(y)) / 2 : lane === 1 ? (xDivL(y) + xDivR(y)) / 2 : (xDivR(y) + xEdgeR(y)) / 2);
const depthW = y => 0.483 * (y - YH);                                            // lane width at depth (scale)

function car(lane, z, lat = 0) {
  const y = YH + KZ / z, w = depthW(y);
  return { x: laneC(lane, y) + lat * w, y, sep: 0.42 * w, z };
}
const humanZ = t => 1.55 + 0.50 * t + 0.05 * fbm1(t * 0.8, 5);
const humanLat = t => 0.07 * fbm1(t * 0.6, 9);
const aiCars = t => [
  ...[0, 1, 2, 3, 4].map(i => ({ lane: 0, z: 2.50 + 0.95 * i + 0.47 * t })),
  ...[0, 1, 2, 3].map(j => ({ lane: 2, z: 2.90 + 0.95 * j + 0.47 * t })),
];

function carLights(c, cm, { brake = 1, glow = true, ai = false }) {
  const att = Math.exp(-0.38 * (c.z - 1));
  if (att < 0.03) return { lights: [], body: null, att };
  const I = (ai ? 2.4 : 3.2) * att * brake;
  const col = brake > 1.05 ? [1.0, 0.075, 0.03] : [1.0, 0.045, 0.02];
  const yl = c.y - 0.40 * c.sep;
  const lights = [];
  for (const dx of [-0.5, 0.5]) {
    const [x, y] = cm.out([c.x + dx * c.sep, yl]);
    lights.push({ x, y, r: Math.max(0.9, 0.05 * c.sep * cm.s), I, c: col, refl: 0.75 * c.sep * cm.s });
  }
  if (glow) {
    const [gx, gy] = cm.out([c.x, yl - 1.9 * c.sep]);
    lights.push({ x: gx, y: gy, r: -(0.95 * c.sep * cm.s), I: (ai ? 0.035 : 0.05) * att, c: [0.55, 0.66, 0.82] });
  }
  const [bx, by] = cm.out([c.x, c.y - 0.18 * c.sep]);
  const body = { x: bx, y: by, hw: 0.62 * c.sep * cm.s, hh: 0.30 * c.sep * cm.s, o: 0.45 * Math.sqrt(att) };
  return { lights, body, att };
}

const ev = (k, id) => k.clock.at(...k.data.events.events[id].at);

function S1(t, k) {
  const { clock, frame, layers } = k;
  const at = (b, be = 0, s = 0) => clock.at(b, be, s);
  // PTZ digital zoom: two steps that land in 2 frames each, then a slow push
  const s1 = ev(k, 's1_ptz1'), s2 = ev(k, 's1_ptz2'), pushT0 = s2 + 2 / FPS, pushT1 = ev(k, 'cut_s2');
  let z = 1 + 0.06 * snap2(t, s1) + 0.06 * snap2(t, s2);
  z *= 1 + 0.045 * easeInOutCubic(clamp((t - pushT0) / (pushT1 - pushT0)));
  if (t >= ev(k, 's1_census')) z *= 1 + 0.010 * clock.pulse('kick', t, 0.12);
  const cz = clamp((z - 1) / 0.17);
  const view = clampView(lerp(836, 1080, cz), lerp(470, 470, cz), z);
  const cm = cam(view);

  // cars: the AI convoy is perfectly even; the human car is irregular and taps the brake
  const lights = [], segs = [], bodies = [];
  const brakeAt = [1.55, 3.05];
  const brake = tt => 1 + 0.85 * brakeAt.reduce((m, b) => Math.max(m, tt >= b && tt < b + 0.22 ? 1 - (tt - b) / 0.22 * 0.3 : 0), 0);
  const human = tt => car(1, humanZ(tt), humanLat(tt));
  const add = (c, opts, trailFn) => {
    const r = carLights(c, cm, opts);
    lights.push(...r.lights);
    if (r.body) bodies.push(r.body);
    if (trailFn && r.att > 0.08) {
      for (const dx of [-0.5, 0.5]) {
        let prev = null;
        for (let j = 0; j <= 3; j++) {
          const cc = trailFn(t - j * 0.06);
          const p = cm.out([cc.x + dx * cc.sep, cc.y - 0.40 * cc.sep]);
          if (prev) segs.push({ a: prev, b: p, r: Math.max(0.7, 0.035 * cc.sep * cm.s), I: 0.45 * r.att * (1 - j / 4) });
          prev = p;
        }
      }
    }
  };
  for (const a of aiCars(t)) add(car(a.lane, a.z), { ai: true }, tt => car(a.lane, a.z - 0.47 * (t - tt)));
  const hc = human(t);
  add(hc, { brake: brake(t) }, human);

  // in-image signal: CCTV OSD + detector box (lags 1.5 frames, confidence jitters)
  const f = layers.feed.ctx;
  chrome(f, W, H, { inset: 36, alpha: 0.32 });
  const secs = 12 + Math.floor(t);
  const blink = clock.beat(t).frac < 0.5;
  osd(f, 72, 96, [
    [{ text: 'CAM 07' }, { text: '环城高架 · 北向', family: F.sansR, size: 22 }],
    [{ text: `03:47:${String(secs).padStart(2, '0')}` }, { text: blink ? '● REC' : '  REC', color: blink ? 'rgba(227,52,47,0.95)' : 'rgba(236,241,244,0.86)' }],
  ]);
  const lag = human(t - 1.5 / FPS);
  const [bx, by] = cm.out([lag.x, lag.y - 0.2 * lag.sep]);
  const bw = Math.max(70, 1.55 * lag.sep * cm.s), bh = Math.max(46, 1.0 * lag.sep * cm.s);
  const conf = (0.95 + 0.04 * hash2(frame, 7)).toFixed(2);
  detector(f, [bx - bw / 2, by - bh / 2, bw, bh], {
    t, t0: 0, frame, label: `car ${conf}`, sub: t >= ev(k, 's1_census') ? 'HUMAN' : null,
  });

  // crisp story type: bar 1 title (beat 2), bar 2 census card (downbeat)
  const o = layers.overlay.ctx;
  const titleOn = ev(k, 's1_title'), titleOff = ev(k, 's1_census');
  const title = c => {
    c.fillStyle = '#F1F4F6';
    runs(c, [
      { text: '如果', family: F.serif, size: 104, tracking: 6 },
      { text: 'AI', family: F.serif, size: 96, tracking: 4, gap: 26 },
      { text: '在凌晨', family: F.serif, size: 104, tracking: 6 },
    ], 120, 452, { gap: 22 });
    runs(c, [{ text: '接管一座城市', family: F.serif, size: 104, tracking: 6 }], 120, 588);
  };
  if (t < titleOff) slam(o, title, { t, t0: titleOn, dur: 0.06, s0: 1.08, ax: 120, ay: 520 });
  else wipeOut(o, title, { t, t0: titleOff, dur: 0.10, x0: 100, y0: 330, w: 760, h: 300 });

  const cardOn = ev(k, 's1_census');
  if (t >= cardOn) {
    const ai = rollNumber(1284180, 1284329, t, cardOn, at(1, 1), 8);
    slam(o, c => {
      font(c, F.mono, 18, 3); c.fillStyle = 'rgba(236,241,244,0.55)';
      c.fillText('VEHICLE CENSUS · 03:47', 120, 724);
      c.fillStyle = 'rgba(236,241,244,0.35)'; c.fillRect(120, 740, 640, 1);
      font(c, F.sansR, 46, 4); c.fillStyle = '#E9EEF1'; c.fillText('自动驾驶', 120, 806);
      font(c, F.mono, 54, 0); c.textAlign = 'right'; c.fillText(thousands(ai), 760, 806); c.textAlign = 'left';
    }, { t, t0: cardOn, dur: 0.06, s0: 1.05, ax: 120, ay: 780 });
    slam(o, c => {
      font(c, F.sansR, 46, 4); c.fillStyle = '#E9EEF1'; c.fillText('人类驾驶', 120, 884);
      font(c, F.mono, 54, 0); c.fillStyle = RED; c.textAlign = 'right'; c.fillText('1', 760, 884); c.textAlign = 'left';
      c.fillStyle = RED; c.fillRect(120, 902, 18, 4);
    }, { t, t0: ev(k, 's1_census2'), dur: 0.06, s0: 1.05, ax: 120, ay: 860 });
  }

  return {
    plate: 'P1L', view, fit: FIT,
    fogA: [0.30, 0.0045, 9, -2.5], fogB: [0.22, 0.011, -14, 1.5], fogTint: [0.050, 0.068, 0.090], fogLift: 0.15,
    lights: packLights(lights), segs: packSegs(segs, [1.0, 0.05, 0.02]), bodies: packBodies(bodies),
    emitGain: 0, bloomThreshold: 1.1, feedGlow: 0.10, overlayGlow: 0.05,
    grade: { uHalation: 0.22, uWeave: [(hash2(frame, 11) - 0.5) * 0.5, (hash2(frame, 12) - 0.5) * 0.5] },
  };
}

// ---------- S2: inside the car (human view, no HUD) ----------
const SCREEN = [[1028, 490], [1631, 519], [1626, 710], [1009, 667]];   // inner glass, plate px (measured)
const VP2 = [1010, 330];

function S2(t, k) {
  const { clock, layers, t0, t1 } = k;
  const at = (b, be = 0, s = 0) => clock.at(b, be, s);
  const u = clamp((t - t0) / (t1 - t0));
  const rz = clock.riser(t);
  let z = 1.06 * (1 + 0.03 * easeInOutCubic(u));
  const amp = 3.5 * rz * rz;
  const shake = [2.4 * noise1(t * 0.7, 21) + amp * noise1(t * 9.0, 22), 1.8 * noise1(t * 0.6, 23) + amp * noise1(t * 8.0, 24)];
  const view = clampView(960, 470, z);
  const cm = cam(view, shake);

  // street lamps sweep over the dash and shoulders on beats 1 and 3
  const b = clock.beat(t);
  const beatInBar = Math.min(3, Math.floor(clock.bar(t).frac * 4 + 1e-6));
  const sweepAge = (beatInBar % 2) * b.len + b.frac * b.len;               // seconds since beat 1 or 3
  const sweepPos = lerp(-300, 1500, clamp(sweepAge / 0.42));
  const sweepGain = 0.85 * Math.exp(-sweepAge / 0.5);

  // the system dialog on the car's own screen
  const ui = layers.ui;
  carDialog(ui.ctx, ui.c.width, ui.c.height, {
    t, on: t0, title: '系统将接管驾驶', button: '保持手动', disabledAt: ev(k, 's2_disable'),
    progress: remap(t, t0 + 0.2, at(3, 0) - 0.05), frame: k.frame,
  });
  const quad = SCREEN.map(cm.out);
  const Hm = invert3(squareToQuad(quad));                                   // output px -> screen uv
  const Hcol = [Hm[0], Hm[3], Hm[6], Hm[1], Hm[4], Hm[7], Hm[2], Hm[5], Hm[8]];
  const cx = quad.reduce((s, p) => s + p[0], 0) / 4, cy = quad.reduce((s, p) => s + p[1], 0) / 4;
  const pulse = 1 + 0.05 * clock.pulse('kick', t, 0.15);

  return {
    plate: 'P2L', view, fit: FIT, shake, mask: 'P2Lmask', flowVP: [VP2[0], VP2[1], 1 + 0.10 * u],
    sweep: [0.35, 0.94, sweepPos, 150], sweepGain,
    fogA: [0.10, 0.006, 6, 0], fogB: [0.06, 0.013, -8, 1], fogTint: [0.05, 0.065, 0.085], fogLift: 0.1,
    screen: { H: Hcol, gain: 1.15 * pulse, spill: 0.55 * pulse, spillColor: [0.55, 0.70, 0.95], center: [cx, cy], radius: 520 },
    bloomThreshold: 0.8, feedGlow: 0,
    grade: { uExposure: 1.05, uHalation: 0.3, uVignette: 0.38 },
  };
}

// ---------- S3: aerial, the drop (system view) ----------
function S3(t, k) {
  const { clock, frame, layers, data, t0 } = k;
  const at = (b, be = 0, s = 0) => clock.at(b, be, s);
  const dt = t - t0;
  let z = lerp(1.10, 1.03, easeInOutCubic(clamp(dt / (DURATION - t0))));
  z *= 1 + 0.06 * impactKick(dt);
  const view = clampView(836, 520, z);
  const cm = cam(view);

  // pulses: chaotic for 5 frames, then snap to equal spacing and phase within a beat;
  // the hero path (the last human car) is the last to fall in.
  const b = clock.beat(t);
  const beatPos = b.idx + easeOutCubic(clamp(b.frac / 0.35));
  const settleStart = t0 + 5 / FPS;
  const e = layers.emit.ctx;
  const LAMBDA = 110, DASH = 58;
  let hero = null;
  const bpRef = clock.beat(t0 + b.len).pos;                                // hero pulse sits ~120 px into its path one beat after the drop
  data.paths.paths.forEach((path, i) => {
    const isHero = path.id === 'f';
    const settle = (isHero ? 1.0 : 0.5) * b.len;
    const chaos = 1 - easeInOutCubic(clamp((t - settleStart) / settle));
    const pts = path.points, arc = path.arc, len = arc[arc.length - 1];
    const at_s = s => {
      let j = 1; while (j < arc.length - 1 && arc[j] < s) j++;
      const f = clamp((s - arc[j - 1]) / Math.max(1e-6, arc[j] - arc[j - 1]));
      return [lerp(pts[j - 1][0], pts[j][0], f), lerp(pts[j - 1][1], pts[j][1], f)];
    };
    const N = Math.ceil(len / LAMBDA) + 2;
    const kHero = ((Math.round((120 + LAMBDA) / LAMBDA - bpRef) % N) + N) % N;
    for (let kk = 0; kk < N; kk++) {
      const off = (hash2(i * 31 + 7, kk + 100) - 0.5) * 0.95 * chaos;
      const s = ((((kk + beatPos + off) % N) + N) % N) * LAMBDA - LAMBDA;
      if (s < 0 || s > len) continue;
      const seg = [];
      for (let q = 0; q <= 6; q++) seg.push(cm.out(at_s(clamp(s - DASH + (q / 6) * DASH, 0, len))));
      const bright = lerp(0.35 + 0.65 * hash2(i, kk + 7), 1, 1 - chaos);
      const heroPulse = isHero && kk === kHero;
      glowPath(e, seg, { core: heroPulse ? 3.0 : 2.0, halo: heroPulse ? 11 : 7, alpha: (heroPulse ? 1 : 0.8) * bright });
      if (heroPulse) hero = seg[seg.length - 1];
    }
  });

  // in-image signal
  const f = layers.feed.ctx;
  chrome(f, W, H, { inset: 36, alpha: 0.32 });
  osd(f, 72, 96, [
    [{ text: 'AERIAL · CAM 01' }, { text: '环城立交', family: F.sansR, size: 22 }],
    [{ text: `03:48:${String(Math.max(0, Math.floor(dt))).padStart(2, '0')}` }],
  ]);
  if (hero && t >= t0 + b.len * 1.0) {
    const conf = (0.96 + 0.03 * hash2(frame, 9)).toFixed(2);
    detector(f, [hero[0] - 44, hero[1] - 30, 88, 60], { t, t0: t0 + b.len * 1.0, frame, label: `car ${conf}`, sub: 'AI', subColor: 'rgba(240,244,246,0.92)' });
  }

  // the payoff: one event on the impact frame
  const o = layers.overlay.ctx;
  slam(o, c => {
    font(c, F.sansR, 48, 6); c.fillStyle = '#E9EEF1'; c.fillText('人类驾驶', 124, 300);
    font(c, F.sans, 300, 0); c.fillStyle = '#F4F6F8'; c.fillText('0', 108, 590);
  }, { t, t0, dur: 0.05, s0: 1.16, ax: 120, ay: 440, ghosts: 2 });
  const tc = clamp((t - ev(k, 's3_time')) / 0.25);
  if (tc > 0) {
    o.save(); o.globalAlpha = tc; font(o, F.mono, 34, 4); o.fillStyle = 'rgba(236,241,244,0.82)';
    o.fillText('03:48', 128, 652); o.restore();
  }

  const mis = 4 * Math.max(0, 1 - dt / (3 / FPS));
  return {
    plate: 'P3L', view, fit: FIT,
    fogA: [0.16, 0.003, 7, -1], fogB: [0.10, 0.008, -10, 1], fogTint: [0.055, 0.07, 0.092], fogLift: 0.12,
    emitGain: 2.0 + 0.4 * clock.pulse('kick', t, 0.12),
    bloomThreshold: 1.0, feedGlow: 0.10, overlayGlow: 0.05,
    grade: { uMisreg: mis, uHalftone: 0.10 + 0.25 * Math.max(0, 1 - dt / (4 / FPS)), uFlash: frame === Math.ceil(t0 * FPS - 1e-6) ? 0.06 : 0,
      uWeave: [(hash2(frame, 13) - 0.5) * 0.5, (hash2(frame, 14) - 0.5) * 0.5] },
  };
}

// ---------- shots ----------
let _events = null;
const EVENTS = () => _events;
function pickShot(t, clock, data) {
  _events = data.events.events;
  const f = Math.round(t * FPS);
  const cut = x => Math.ceil(x * FPS - 1e-6);
  const c1 = cut(clock.at(...EVENTS().cut_s2.at)), c2 = cut(clock.at(...EVENTS().cut_s3_drop.at));
  if (f < c1) return { id: 'S1', t0: 0, t1: c1 / FPS };
  if (f < c2) return { id: 'S2', t0: c1 / FPS, t1: c2 / FPS };
  return { id: 'S3', t0: c2 / FPS, t1: DURATION };
}

install({
  width: W, height: H, fps: FPS, canvasId: 'stage',
  fontsUrl: 'fonts', beatsUrl: 'data/beats.json', hitsUrl: 'data/hits.json',
  musicUrl: 'data/music.json',
  data: { paths: 'data/P3L-paths.json', events: 'data/events.json' },
  images: {
    P1L: { url: 'plates/P1L.png' }, P2L: { url: 'plates/P2L.png' }, P3L: { url: 'plates/P3L.png' },
    P2Lmask: { url: 'plates/P2L-interior.png', mipmap: false },
  },
  uiSize: [1268, 400],
  scenes: { S1, S2, S3 },
  pickShot,
});
