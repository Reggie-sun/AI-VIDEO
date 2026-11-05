// System viewpoint: the surveillance OSD drawn into the feed (it takes the grain, bloom and misregistration like a real
// camera signal): corner brackets, camera label, story-clock timecode, a recording dot, a status row, detection boxes.
// The OSD frame sits OSD_IN (72 px) inside the picture: the outer band is the editorial chrome's (chrome.js), which
// frames every unit; the OSD stays in the system units.
// Words only from graphic_text (ANOMALY 1 / 4096, ACTIVE 1, TRAINING RUN, TRACK LOST, TRAINING PAUSED, the paused
// bar, DETECTED, CITY CAM, STATUS: ...) and the camera labels the data names (U001's HALL 07 · CAM 03, corner_LAB02).
// Numbers only from there and from the story clock. The iris viewpoint never calls anything here.
import { chrome } from '../../../../../../motion-kit/src/draw2d.js';
import { clamp, easeInOutCubic, easeOutCubic, hash2, hash3, lerp } from '../../../../../../motion-kit/src/math.js';
import { ANCHORS } from './anchors.js';
import { BLACK, DARK_INK, F, FAINT, H, INK, OSD_IN, RED, STEEL, W, accent, along, beatLen, downbeatAfter, glow, grow, hms,
  line, measure, point, shade, storyClock, text, tokenLine } from './util.js';

// ---- camera labels: the opening's (osd_power_on unit's graphic_text), a corner_* component's, the city monitor's ----
let LABELS = null;
function labels(k) {
  if (LABELS) return LABELS;
  const us = k.data.units.units;
  const hall = us.find(u => u.graphics.includes('osd_power_on'))?.text || 'HALL 07 · CAM 03';
  const byPlate = {};
  for (const u of us) {
    const c = u.graphics.find(g => g.startsWith('corner_'));
    if (c && u.plates[0]) byPlate[u.plates[0].key] = c.slice(7).replace(/([A-Z]+)(\d+)/, '$1 $2');
  }
  LABELS = { hall, byPlate };
  return LABELS;
}
export function camLabel(k, u, key) {
  const L = labels(k), c = u.graphics.find(g => g.startsWith('corner_'));
  if (c) return c.slice(7).replace(/([A-Z]+)(\d+)/, '$1 $2');
  if (/^(HALL|CAM|LAB)\b/.test(u.text)) return u.text;               // graphic_text names the camera (a2 U069: CAM 07)
  return L.byPlate[key] || L.hall;
}
const bright = key => /lab/.test(key || '');
// the recording dot: signal red; steel in the red-team room; grey when the unit has every red off, and for the whole of
// a unit whose beat is her light coming on (light_flicker_on: a2.1 U084, the closing image's only red is her light)
const recColor = u => (u.nored ? STEEL
  : u.graphics.includes('red_off') || u.graphics.includes('light_flicker_on') ? 'rgba(150,156,162,0.9)' : RED);

// ---- detection box: corners snap in from 1.6x over two frames, 1 px jitter per frame, a label tag above-left ----
export function detect(ctx, box, { t, t0, frame, label = null, sub = null, ink = 'rgba(240,244,246,0.95)', paper = 'rgba(8,10,12,0.95)',
  accentColor = RED, lw = 2, size = 18, alpha = 1, seed = 0, s0 = 1.6 }) {
  if (t < t0 || alpha <= 0 || !box) return;
  const e = easeOutCubic(clamp((t - t0) / 0.066)), sc = s0 + (1 - s0) * e;
  let [x, y, w, h] = box;
  const cx = x + w / 2, cy = y + h / 2;
  w *= sc; h *= sc; x = cx - w / 2; y = cy - h / 2;
  const j = n => (hash2(frame + seed * 131, n) - 0.5) * 2;
  x += j(1); y += j(2);
  const L = Math.max(7, Math.min(w, h) * 0.24);
  ctx.save();
  ctx.globalAlpha = alpha * Math.min(1, 0.3 + e);
  ctx.strokeStyle = ink; ctx.lineWidth = lw; ctx.lineCap = 'square';
  ctx.beginPath();
  for (const [px, py, dx, dy] of [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]]) {
    ctx.moveTo(px + dx * L, py); ctx.lineTo(px, py); ctx.lineTo(px, py + dy * L);
  }
  ctx.stroke();
  const th = Math.round(size * 1.35), pad = Math.round(size * 0.32);
  // the tag sits above-left of the box; a box reaching the top of the frame carries it inside its top edge instead
  const ty = y - th - 4 < OSD_IN + 8 ? Math.round(y + 6) : Math.round(y - th - 4);
  let lx = Math.round(Math.max(OSD_IN + 8, x));
  if (label) {
    const tw = measure(ctx, label, size, F.mono, 1) + 2 * pad;
    ctx.fillStyle = ink; ctx.fillRect(lx, ty, Math.round(tw), th);
    text(ctx, label, lx + pad, Math.round(ty + th * 0.72), { size, color: paper, tracking: 1, shadow: null });
    lx += Math.round(tw) + 4;
  }
  if (sub) {
    const sw = measure(ctx, sub, size, F.monoB, 1) + 2 * pad;
    ctx.fillStyle = accentColor; ctx.fillRect(lx, ty, Math.round(sw), th);
    text(ctx, sub, lx + pad, Math.round(ty + th * 0.72), { size, family: F.monoB, color: 'rgba(250,250,250,0.98)', tracking: 1, shadow: null });
  }
  ctx.restore();
}
// graphic_text "LABEL rest" -> a box label and its accent tag (ANOMALY 1 / 4096 -> ANOMALY, 1 / 4096)
export const boxText = s => { const m = /^(\S+)\s+(.+)$/.exec(String(s || '').trim()); return m ? [m[1], m[2]] : [s || null, null]; };

// ---- the OSD frame of a system unit ----
// opts: label (camera label or null), status (status-row text or null), statusRed, frozen (timecode held at the unit
// start), alpha (whole OSD), dark (dark ink for a bright plate), dot (recording dot), tc (timecode), glitch (0..1)
export function osd(k, t, { label = undefined, status = null, statusRed = false, frozen = false, alpha = 1, dark = undefined,
  dot = true, tc = true, glitch = undefined, statusAlpha = 1 } = {}) {
  k.osd = true;
  if (alpha <= 0) return;
  const u = k.shot.u, key = k.plateKey, f = k.layers.feed.ctx;
  if (glitch === undefined) glitch = glitchAmt(k, u, t);
  if (label === undefined) label = camLabel(k, u, key);
  if (dark === undefined) dark = bright(key);
  const ink = dark ? DARK_INK : INK, shadow = dark ? null : 'rgba(0,0,0,0.6)';
  const g = glitch > 0 ? Math.floor(t * 15) : -1;                       // glitch state changes on 15 Hz ticks only
  const garble = (s, seed) => (glitch > 0 ? [...s].map((ch, i) => (ch !== ' ' && hash3(i, g, seed) < glitch * 0.55
    ? '#%&*/\\<>=+0123456789ABCDEFGHJKMNPQRSTUVWXYZ'[Math.floor(hash3(i, g, seed + 1) * 43)] : ch)).join('') : s);
  f.save(); f.globalAlpha = alpha;
  if (dark) {                                                          // chrome() only draws light ink: dark brackets by hand
    f.strokeStyle = DARK_INK; f.lineWidth = 1.5; f.beginPath();
    const a = OSD_IN + 0.5;
    for (const [x, y, dx, dy] of [[a, a, 1, 1], [W - a, a, -1, 1], [a, H - a, 1, -1], [W - a, H - a, -1, -1]]) {
      f.moveTo(x + dx * 34, y); f.lineTo(x, y); f.lineTo(x, y + dy * 34);
    }
    f.stroke();
  } else chrome(f, W, H, { inset: OSD_IN, alpha: 0.55, mark: 34, lw: 1.5 });
  const tt = frozen ? k.t0 : t;
  if (dot) {                                                           // recording dot: a slow breath, never a flash
    const a = frozen ? 0.5 : 0.55 + 0.45 * Math.cos((t % 1.6) / 1.6 * Math.PI * 2);
    f.globalAlpha = alpha * a; f.fillStyle = recColor(u); f.beginPath(); f.arc(OSD_IN + 56, OSD_IN + 40, 7, 0, Math.PI * 2); f.fill(); f.globalAlpha = alpha;
  }
  if (label) text(f, garble(label, 3), OSD_IN + 74, OSD_IN + 48, { size: 22, color: ink, shadow });
  if (tc) text(f, garble(hms(storyClock(k, tt)), 5), W - OSD_IN - 56, OSD_IN + 48, { size: 24, color: ink, align: 'right', shadow });
  const cross = dark ? DARK_INK : FAINT;                               // centre crosshair
  line(f, [W / 2 - 16, H / 2], [W / 2 - 6, H / 2], { color: cross, width: 1.5 });
  line(f, [W / 2 + 6, H / 2], [W / 2 + 16, H / 2], { color: cross, width: 1.5 });
  line(f, [W / 2, H / 2 - 16], [W / 2, H / 2 - 6], { color: cross, width: 1.5 });
  line(f, [W / 2, H / 2 + 6], [W / 2, H / 2 + 16], { color: cross, width: 1.5 });
  if (status) { f.globalAlpha = alpha * statusAlpha; statusRow(f, garble(status, 7), { color: statusRed ? accent(u) : ink }); }
  if (glitch > 0) glitchBlocks(f, u, g, glitch);
  f.restore();
}
function statusRow(f, s, { color = INK, cells = 10, lit = 10 } = {}) {
  const x1 = W - OSD_IN - 56, y = H - OSD_IN - 32, w = measure(f, s, 18, F.mono, 2);
  text(f, s, x1, y, { size: 18, color, align: 'right', tracking: 2 });
  for (let i = 0; i < cells; i++) {
    f.save(); f.globalAlpha *= i < lit ? 0.85 : 0.3; f.fillStyle = color;
    f.fillRect(x1 - w - 24 - (cells - i) * 9, y - 14, 6, 14); f.restore();
  }
}
// signal break-up: displaced bars of the feed's own colours (white, steel, black, one in signal red), held two frames
function glitchBlocks(f, u, g, amt) {
  const n = Math.round(3 + 9 * amt);
  for (let i = 0; i < n; i++) {
    if (hash3(i, g, 11) > 0.35 + 0.5 * amt) continue;
    const y = Math.floor(hash3(i, g, 12) * H), h = 3 + Math.floor(hash3(i, g, 13) * 26), x = Math.floor(hash3(i, g, 14) * W * 0.8);
    const w = 60 + Math.floor(hash3(i, g, 15) * 520), c = hash3(i, g, 16);
    f.save(); f.globalAlpha = 0.35 + 0.4 * hash3(i, g, 17);
    f.fillStyle = c < 0.1 && !u.nored ? RED : c < 0.45 ? 'rgba(220,230,240,0.9)' : c < 0.75 ? 'rgba(120,150,180,0.9)' : BLACK;
    f.fillRect(x, y, w, h); f.restore();
  }
}

// how broken the OSD signal is at t (0 = clean): units with osd_glitch break up hardest on each beat, held on 15 Hz ticks
export function glitchAmt(k, u, t) {
  if (!u.graphics.includes('osd_glitch')) return 0;
  const bl = beatLen(k, t), ph = (((t - k.t0) % bl) + bl) % bl / bl;
  return clamp(0.25 + 0.75 * (ph < 0.3 ? 1 - ph / 0.3 : 0.15) * (0.6 + 0.4 * hash2(Math.floor(t * 15), 41)));
}

// ---- the hall lattice: a copy's head at a plate point, its box and its collar point (plate px) ----
export function latticeAt(A, [x, y]) {
  const L = A.lattice;
  return { x, y, s: (y - L.vy) / (L.y0 - L.vy) };
}
export const hallBox = ({ x, y, s }) => [x - 24 * s, y - 28 * s, 48 * s, 78 * s];
export const hallDot = ({ x, y, s }) => [x + 5 * s, y + 25 * s];
const inside = ([x, y], [bx, by, bw, bh]) => x >= bx && x <= bx + bw && y >= by && y <= by + bh;
const SCALE_W = { extreme_wide: 0.05, wide: 0.1, full: 0.16, medium: 0.28, close_up: 0.42 };
// the plate box of the unit's subject: around its target (or the plate's `her` anchor). On the hall lattice: the copy at
// that point; on a still with a figure / terminal anchor that contains the point: that box; else a figure-shaped box
// sized by the unit's scale. i: index into `targets` (several subjects).
export function subjectBox(k, u, key, i = null) {
  const A = ANCHORS[key] || {}, p = point(k, u, key, 'her', i);
  if (A.lattice && p) return hallBox(latticeAt(A, p));
  const boxes = [A.figure, ...(A.terminals || [])].filter(Boolean);
  if (p) {
    const hit = boxes.find(b => inside(p, b));
    if (hit) return hit;
    const w = k.size[key][0] * (SCALE_W[u.scale] ?? 0.12), h = w * 1.7;
    return [p[0] - w / 2, p[1] - h / 2, w, h];
  }
  return i !== null && A.terminals?.[i] ? A.terminals[i] : A.figure || null;
}
// her red point in a wide (emit, so it blooms; and a feed glow that survives darkening)
export function herLight(k, cm, p, { alpha = 1, feed = false, color } = {}) {
  if (!p) return;
  const q = cm.out(p);
  glow(k.layers.emit.ctx, q, 9 * cm.s, { alpha: 0.9 * alpha, color });
  if (feed) glow(k.layers.feed.ctx, q, 7 * cm.s, { alpha: 0.85 * alpha, color });
}
function herDot(k, u, key) {
  const A = ANCHORS[key] || {}, p = point(k, u, key, 'her');
  if (A.lattice && p) return hallDot(latticeAt(A, p));
  return A.led || p;
}

// ---- per-graphic OSD behaviours (system units). Each returns scene overrides (plate gain, grade) or nothing. ----
export const OSD = {
  osd_power_on(k, t, u) {                                             // black until the cue (first hit), then the feed opens
    const tOn = u.cue, f = k.layers.feed.ctx;
    if (t < tOn) { k.osd = true; return { plateGain: 0, emitGain: 0 }; }
    const open = easeOutCubic(clamp((t - tOn) / 0.22)), h = lerp(6, H, open);
    shade(f, 0, 0, W, (H - h) / 2, 1); shade(f, 0, (H + h) / 2, W, (H - h) / 2 + 1, 1);
    if (open < 1) line(f, [0, H / 2], [W, H / 2], { color: 'rgba(220,232,244,0.8)', width: 2, alpha: 1 - open });
    osd(k, t, { alpha: grow(t, tOn + 0.12, 0.2) });
    return {};
  },
  // the electronic zoom box: a 16:9 region around her row (her anchor, or the unit's target) that the feed is pushing
  // toward; dashed and faint from just after the cue, it locks (solid corners) on the next downbeat but one beat on
  osd_zoombox(k, t, u, cm) {
    const f = k.layers.feed.ctx, p = point(k, u, cm.key, 'her');
    if (!p || t < u.cue + 0.3) return {};
    const w = k.size[cm.key][0] * 0.3, h = w * 9 / 16, r = cm.box([p[0] - w / 2, p[1] - h / 2, w, h]);
    const lock = t >= downbeatAfter(k, u.cue + beatLen(k, u.cue)), a = grow(t, u.cue + 0.3, 0.2);
    f.save(); f.globalAlpha = a * (lock ? 0.9 : 0.6); f.strokeStyle = 'rgba(240,244,246,0.95)'; f.lineWidth = 1.5;
    f.setLineDash([10, 8]); f.strokeRect(Math.round(r[0]) + 0.5, Math.round(r[1]) + 0.5, Math.round(r[2]), Math.round(r[3])); f.restore();
    if (lock) detect(f, r, { t, t0: downbeatAfter(k, u.cue + beatLen(k, u.cue)), frame: k.frame, s0: 1.08, lw: 2 });
    return {};
  },
  osd_detect_one(k, t, u, cm) {                                       // one red point, then the box snaps onto it
    const [label, sub] = boxText(u.text);
    const A = ANCHORS[cm.key] || {};
    if (A.lattice) herLight(k, cm, herDot(k, u, cm.key));
    const b = subjectBox(k, u, cm.key);
    detect(k.layers.feed.ctx, b && cm.box(b), { t, t0: u.cue, frame: k.frame, label, sub, accentColor: accent(u) });
    return { emitGain: 2.4 };
  },
  osd_detect_lost(k, t, u, cm) {                                      // the box flashes on the target, then loses it
    const f = k.layers.feed.ctx, b = subjectBox(k, u, cm.key), t0 = u.cue, bl = beatLen(k, t0);
    const tLost = t0 + 1.5 * bl;
    if (b && t >= t0) {
      const on = t < tLost && ((t - t0) % (bl / 2)) < bl / 3;          // two short blinks, slower than 3 a second
      if (on) detect(f, cm.box(b), { t, t0, frame: k.frame, s0: 1.3 });
      if (t >= tLost) {                                                // lost: the corners drift apart and fade
        const e = clamp((t - tLost) / 0.5), r = cm.box(b), g = 1 + 0.35 * easeOutCubic(e);
        const c = [r[0] + r[2] / 2, r[1] + r[3] / 2];
        detect(f, [c[0] - r[2] * g / 2, c[1] - r[3] * g / 2, r[2] * g, r[3] * g], { t, t0: tLost - 1, frame: k.frame, alpha: (1 - e) * 0.6, lw: 1.5 });
      }
    }
    osd(k, t, { status: t >= tLost ? u.text : null, statusRed: true });
    return {};
  },
  osd_track_one(k, t, u, cm) {                                        // the box follows her out of the grid, a trail behind
    const A = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx;
    osd(k, t);
    const p0 = point(k, u, cm.key, 'her');
    if (!A.lattice || !p0) return {};
    const L = A.lattice, s0 = latticeAt(A, p0).s;
    const col = Math.round((p0[0] - L.vx) / (L.spacing * s0)), aisle = L.vx + col * L.spacing * s0;
    const far = [L.vx + (aisle - L.vx) * 0.22, L.vy + (p0[1] - L.vy) * 0.22];
    const path = [p0, [aisle, p0[1]], far];
    const tS = u.cue, p = easeInOutCubic(clamp((t - tS) / (k.t1 - 0.25 - tS)));
    const pts = along(path, p), head = pts[pts.length - 1], h = latticeAt(A, head);
    herLight(k, cm, hallDot(h));
    if (pts.length > 1) {
      const sp = pts.map(q => cm.out(q));
      f.save(); f.setLineDash([6, 6]); f.strokeStyle = RED; f.lineWidth = 2; f.globalAlpha = 0.85;
      f.beginPath(); f.moveTo(...sp[0]); for (const q of sp.slice(1)) f.lineTo(...q); f.stroke(); f.restore();
    }
    detect(f, cm.box(hallBox(h)), { t, t0: k.t0 + 2 / 30, frame: k.frame, label: u.text || null });
    return { emitGain: 2.4 };
  },
  osd_progress_training(k, t, u) {                                    // the run's label and a bar that keeps moving
    osd(k, t);
    const f = k.layers.feed.ctx, tR = u.toks[0]?.at ?? u.cue, x = 560, y = 176, w = 800, n = 40;
    const a = grow(t, tR, 0.15);
    if (a <= 0) return {};
    tokenLine(f, u.text, u.toks, 0, t, x, y - 14, { size: 20 });
    const lit = Math.floor(n * lerp(0.2, 0.62, clamp((t - tR) / (k.t1 - tR))));
    for (let i = 0; i < n; i++) {
      f.save(); f.globalAlpha = a * (i < lit ? 0.9 : 0.22); f.fillStyle = i < lit ? INK : FAINT;
      f.fillRect(x + i * (w / n), y, w / n - 4, 12); f.restore();
    }
    return {};
  },
  osd_paused_blackout(k, t, u, cm) {                                  // rows go dark one per beat; only her red point stays
    const A = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, tP = u.cue;
    const blink = t >= tP && Math.floor((t - tP) / 0.4) % 2 === 0;      // 1.25 Hz, small type: not a flash
    const bl = beatLen(k, tP), bands = 8;
    for (let i = 0; i < bands; i++) {                                 // far rows first
      const a = 0.9 * grow(t, tP + i * bl, 0.18);
      const y0 = cm.out([0, (i / bands) * k.size[cm.key][1]])[1], y1 = cm.out([0, ((i + 1) / bands) * k.size[cm.key][1]])[1];
      shade(f, 0, y0, W, y1 - y0 + 1, a);
    }
    herLight(k, cm, herDot(k, u, cm.key), { feed: true });
    if (!A.lattice) herLight(k, cm, point(k, u, cm.key, 'her'), { feed: true });
    osd(k, t, { status: blink ? u.text : null, statusRed: true });
    return { emitGain: 2.4 };
  },
  osd_paused_freeze(k, t, u) {                                        // frozen picture and clock, then the paused bar
    const f = k.layers.feed.ctx, tP = u.toks[0]?.at ?? u.cue;
    osd(k, t, { frozen: true });
    if (t >= tP) {
      const a = grow(t, tP, 0.08);
      f.save(); f.globalAlpha = 0.72 * a; f.fillStyle = BLACK; f.fillRect(0, 470, W, 140); f.restore();
      line(f, [0, 470], [W, 470], { color: FAINT, width: 1, alpha: a }); line(f, [0, 610], [W, 610], { color: FAINT, width: 1, alpha: a });
      f.save(); f.globalAlpha = a; f.fillStyle = INK; f.fillRect(150, 508, 14, 64); f.fillRect(176, 508, 14, 64); f.restore();
      const size = Math.min(54, 1450 / Math.max(1, u.text.length) / 0.62);
      tokenLine(f, u.text, u.toks, 0, t, 230, 540 + size * 0.36, { size, family: F.monoB, tracking: 4 });
    }
    return { grade: { uSat: 0.55 } };
  },
  osd_detected_two(k, t, u, cm) {                                     // both subjects at once, dark ink on a bright still
    const f = k.layers.feed.ctx, tF = u.toks[0]?.at ?? u.cue, dark = bright(cm.key);
    osd(k, t, { status: t >= tF ? u.text : null, statusRed: true });
    for (let i = 0; i < Math.max(2, u.targets?.length || 0); i++) {
      const b = subjectBox(k, u, cm.key, i);
      detect(f, b && cm.box(b), { t, t0: tF, frame: k.frame, label: u.text || null, seed: i + 1, accentColor: accent(u),
        ink: dark ? DARK_INK : 'rgba(240,244,246,0.95)', paper: dark ? 'rgba(240,244,246,0.98)' : 'rgba(8,10,12,0.95)' });
    }
    return {};
  },
  osd_boxes_multiply(k, t, u, cm) {                                   // boxes double on every sixteenth, layered on her
    const A = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, p = point(k, u, cm.key, 'her');
    osd(k, t);
    if (!p) return {};
    const b = cm.box(A.lattice ? hallBox(latticeAt(A, p)) : subjectBox(k, u, cm.key));
    if (A.lattice) herLight(k, cm, hallDot(latticeAt(A, p)));
    const q16 = beatLen(k, k.t0) / 4, step = Math.floor((t - k.t0) / q16), n = Math.min(32, 2 ** Math.max(0, step));
    for (let i = 0; i < n; i++) {
      // each copy a little off-centre and off-shape, so the layers pile up around her instead of lining their corners up
      // on the diagonals (which read as an X)
      const g = 1 + 0.16 * i + 0.05 * hash2(i, 3), dx = (hash2(i, 5) - 0.5) * 26 * i ** 0.5, dy = (hash2(i, 6) - 0.5) * 18 * i ** 0.5;
      const w = b[2] * g * (0.8 + 0.4 * hash2(i, 7)), hh = b[3] * g * (0.8 + 0.4 * hash2(i, 8));
      const x = b[0] + b[2] / 2 - w / 2 + dx, y = b[1] + b[3] / 2 - hh / 2 + dy;
      const t0 = k.t0 + Math.floor(Math.log2(i + 1)) * q16;
      detect(f, [x, y, w, hh], { t, t0, frame: k.frame, seed: i, ink: i % 3 === 2 ? RED : 'rgba(240,244,246,0.9)',
        lw: i ? 1.5 : 2, alpha: i ? 0.8 : 1 });
    }
    return { emitGain: 2.4 };
  },
  osd_boxes_chase(k, t, u, cm) {                                      // boxes from all over the grid converge on one point
    const A = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, p = point(k, u, cm.key, 'her');
    osd(k, t);
    if (!A.lattice || !p) return {};
    const h = latticeAt(A, p), target = cm.box(hallBox(h));
    herLight(k, cm, hallDot(h));
    const n = 18, bl = beatLen(k, k.t0);
    for (let i = 0; i < n; i++) {
      const row = Math.floor(hash2(i, 21) * 9), c = Math.floor(hash2(i, 22) * 16) - 8, L = A.lattice;
      const s = (L.rows[row] - L.vy) / (L.y0 - L.vy);
      const src = cm.box(hallBox({ x: L.vx + (c + 0.5) * L.spacing * s, y: L.rows[row], s }));
      const t0 = k.t0 + (i % 6) * bl / 4, e = easeInOutCubic(clamp((t - t0) / (bl * 2.2)));
      const bx = src.map((v, j) => lerp(v, target[j] * (j > 1 ? 1 + 0.12 * (i % 4) : 1) - (j < 2 ? target[j + 2] * 0.06 * (i % 4) : 0), e));
      detect(f, bx, { t, t0, frame: k.frame, seed: i + 7, ink: i % 4 === 0 ? RED : 'rgba(240,244,246,0.9)', lw: 1.5, alpha: 0.85 });
    }
    return { emitGain: 2.4 };
  },
  osd_status_normal(k, t, u) {                                        // the hall as it was: nothing flagged
    osd(k, t, { status: t >= u.cue ? u.text : null });
    return {};
  },
  osd_status_resetting(k, t, u) {                                     // the status row resets, its cells running
    osd(k, t, { status: t >= u.cue ? u.text : null, statusAlpha: 0.7 + 0.3 * Math.cos((t - u.cue) * 2.6) });
    return {};
  },
  osd_glitch(k, t, u) {                                               // OSD words and colour bars break up (osd() draws them)
    const mis = Math.floor(t * 15) % 3 === 0 ? 4 * glitchAmt(k, u, t) : 0;
    return { grade: { uMisreg: mis } };
  },
  corner_LAB02() { return {}; },                                     // the camera label (camLabel reads the name)
};

// ---- monitor graphics ----
// the wall (a2 U073, the unsung stare after the final chorus): nine windows, each a still of her not singing, looking
// into the lens (build.py WALL), framed on her face, with a recording dot and the story clock, inside the OSD frame. A
// detection box locks onto one face after another, one per half beat from just after the cut, in a fixed scattered
// order, and stays locked.
const LOCK_ORDER = [4, 0, 8, 2, 6, 1, 7, 3, 5];
export function monitorWall(k, t, u) {
  // three rows of 16:9 windows between the OSD's top row (label and clock at y OSD_IN + 48) and its bottom bracket
  const f = k.layers.feed.ctx, wall = k.data.units.wall || [], cols = 3, gw = 480, gh = 270, gap = 22;
  const gx = (W - cols * gw - (cols - 1) * gap) / 2, gy = OSD_IN + 66, half = beatLen(k, k.t0) / 2;
  wall.forEach((key, i) => {
    const img = k.bitmaps[key], A = ANCHORS[key] || {};
    const x = gx + (i % cols) * (gw + gap), y = gy + Math.floor(i / cols) * (gh + gap);
    const a = grow(t, k.t0 + (i % 5) * 0.035, 0.12);
    f.save(); f.globalAlpha = a; f.fillStyle = '#05070a'; f.fillRect(x, y, gw, gh);
    if (img) {
      const fc = A.face ? [A.face[0] + A.face[2] / 2, A.face[1] + A.face[3] * 0.45] : A.focus || [img.width / 2, img.height * 0.4];
      const z = 1.25 * (1 + 0.04 * clamp((t - k.t0) / (k.t1 - k.t0)) * (1 + (i % 3) * 0.5)), cw = img.width / z, ch = cw * gh / gw;
      const sx = clamp(fc[0] - cw / 2, 0, img.width - cw), sy = clamp(fc[1] - ch / 2, 0, img.height - ch);
      f.drawImage(img, sx, sy, cw, ch, x, y, gw, gh);
      if (A.face) {
        const bx = x + (A.face[0] - sx) / cw * gw, by = y + (A.face[1] - sy) / ch * gh;
        const lock = k.t0 + 0.3 + LOCK_ORDER.indexOf(i) * half;
        detect(f, [bx, by, A.face[2] / cw * gw, A.face[3] / ch * gh * 0.8], { t, t0: lock, frame: k.frame, seed: i, lw: 1.5, size: 12 });
      }
    }
    f.strokeStyle = 'rgba(236,241,244,0.35)'; f.lineWidth = 1; f.strokeRect(x + 0.5, y + 0.5, gw - 1, gh - 1);
    f.restore();
    text(f, hms(storyClock(k, t)), x + gw - 12, y + gh - 12, { size: 13, align: 'right', alpha: a });
    f.save(); f.globalAlpha = a * (0.55 + 0.45 * Math.cos((t + i * 0.2) * 3.9)); f.fillStyle = RED;
    f.beginPath(); f.arc(x + 18, y + 18, 4, 0, Math.PI * 2); f.fill(); f.restore();
  });
  osd(k, t, { label: null, dot: false });
  return { plateGain: 1 };
}
// the monitor frame: a bezel, the recording dot and the clock at the edges of her close-up (alpha 0..1); label: the
// camera label (CITY CAM from monitor_frame_city's graphic_text), else the hall's
export function monitorFrame(k, t, alpha, label = undefined) {
  k.osd = true;                                                        // this unit's OSD, even while it is still invisible
  if (alpha <= 0) return;
  const f = k.layers.feed.ctx, b = 34;
  f.save(); f.globalAlpha = alpha;
  f.fillStyle = '#030406';
  f.fillRect(0, 0, W, b); f.fillRect(0, H - b, W, b); f.fillRect(0, 0, b, H); f.fillRect(W - b, 0, b, H);
  f.strokeStyle = 'rgba(236,241,244,0.28)'; f.lineWidth = 1.5; f.strokeRect(b + 0.5, b + 0.5, W - 2 * b - 1, H - 2 * b - 1);
  f.restore();
  osd(k, t, { label, alpha, dot: true });
}
