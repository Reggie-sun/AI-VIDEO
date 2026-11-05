// 2.5D code camera for the stills, from the unit's camera_move (shots-map.json, parsed by build.py into units.json
// `move`: hold / push / pull / pan / truck / eye / up / rotate with their amounts). A view is [cx, cy, z, rot] in plate px
// around the plate's focus anchor (the centre when there is none); z multiplies the cover fit. Each move eases in and
// out inside its unit, so it is continuous with no jump; a unit whose first still is the previous unit's last still
// starts where that unit's camera stopped (the move continues across the cut). A second still inside a unit keeps the
// same normalized move. Pure functions of t.
import { clamp, easeInOutSine, hash2, lerp } from '../../../../../../motion-kit/src/math.js';
import { ANCHORS } from './anchors.js';
import { H, W } from './util.js';

const DEG = Math.PI / 180;
// start / end offsets: dx, dy in plate widths / heights, z as a zoom multiplier, r in radians. dir: the plate's `dir`
// anchor, else +1 / -1 per unit (hashed from its index) so neighbouring holds and pans do not all drift the same way.
function moveDef(u, key) {
  const m = u.move, d = ANCHORS[key]?.dir ?? (hash2(u.i, 7) < 0.5 ? -1 : 1);
  switch (m.kind) {
    case 'push': return { a: [-m.drift * d, 0, 1.0, 0], b: [m.drift * d, 0, 1 + m.z, 0] };
    case 'pull': return { a: [0, 0, 1 + m.z, 0], b: [0, 0, 1.0, 0] };
    case 'pan': case 'truck': case 'eye': {
      const z = 1 / (1 - m.dx) + 0.012;
      return { a: [-m.dx / 2 * d, 0, z, 0], b: [m.dx / 2 * d, 0, z, 0] };
    }
    case 'up': { const z = 1 / (1 - m.dy) + 0.012; return { a: [0, m.dy / 2, z, 0], b: [0, -m.dy / 2, z, 0] }; }
    case 'rotate': return { a: [0, 0, 1.1, 0], b: [0, 0, 1.14, m.r * d * DEG] };
    default: return { a: [0, 0, 1.0, 0], b: [0.005 * d, 0, 1 + (m.z ?? 0.015), 0] };
  }
}

const focusOf = (key, size) => ANCHORS[key]?.focus || [size[0] / 2, size[1] / 2];
// the move of a unit in absolute view terms [cx, cy, z, r], before the cover clamp
function rawMove(u, key, size) {
  const [fx, fy] = focusOf(key, size), m = moveDef(u, key);
  const v = o => [fx + o[0] * size[0], fy + o[1] * size[1], o[2], o[3]];
  return { a: v(m.a), b: v(m.b) };
}
// start/end views of every unit's first still, resolved once: a continuing unit (same still across the cut) adds its
// move's delta to the previous unit's end view
let RESOLVED = null;
function resolve(units, sizeOf) {
  const out = {};
  let prev = null;
  for (const u of units) {
    const key = u.plates.length ? u.plates[0].key : null;
    if (!key) { prev = null; continue; }
    const size = sizeOf(key), mv = rawMove(u, key, size);
    const lastKey = prev && prev.u.plates[prev.u.plates.length - 1].key;
    if (prev && lastKey === key && prev.u.plates.length === 1) {
      const a = prev.b, dl = mv.b.map((x, i) => (i === 2 ? x / mv.a[2] : x - mv.a[i]));
      out[u.id] = { a, b: [a[0] + dl[0], a[1] + dl[1], Math.max(1, a[2] * dl[2]), a[3] + dl[3]] };
    } else out[u.id] = mv;
    prev = { u, b: out[u.id].b };
  }
  return out;
}

// cover fit: the frame never leaves the plate. With a rotation the zoom must also cover the rotated frame's corners.
export function camAt(k, key, [cx, cy, z, r], shake = [0, 0]) {
  const [pw, ph] = k.size[key];
  const fit = Math.max(W / pw, H / ph);
  const c = Math.cos(r), sn = Math.sin(r), ac = Math.abs(c), as = Math.abs(sn);
  const cover = ac + (W / H) * as;
  z = Math.max(z, r ? cover * 1.002 : 1);
  const s = fit * z;
  // half extents of the (rotated) frame in plate px: the centre stays this far inside the plate edges
  const hx = ((W / 2) * ac + (H / 2) * as) / s, hy = ((W / 2) * as + (H / 2) * ac) / s;
  cx = clamp(cx + shake[0] / s, Math.min(hx, pw / 2), Math.max(pw - hx, pw / 2));
  cy = clamp(cy + shake[1] / s, Math.min(hy, ph / 2), Math.max(ph - hy, ph / 2));
  // plate px -> screen px (the scene shader's outToPlate inverted)
  const out = ([x, y]) => {
    const dx = (x - cx) * s, dy = (y - cy) * s;
    return [dx * c - dy * sn + W / 2, dx * sn + dy * c + H / 2];
  };
  const box = ([x, y, w, h]) => {
    const p = [out([x, y]), out([x + w, y]), out([x, y + h]), out([x + w, y + h])];
    const xs = p.map(q => q[0]), ys = p.map(q => q[1]);
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
  };
  return { key, view: [cx, cy, z, r], fit, s, out, box };
}

// the camera of unit u at time t (k.t0 / k.t1 are the unit's frame-quantised bounds) on plate `key`
//   freeze: hold the unit's first view (a frozen feed); punch: an impact at time `punch` (zoom kick + two frames of shake)
export function unitCam(k, u, t, key, { freeze = false, punch = null } = {}) {
  if (!RESOLVED) RESOLVED = resolve(k.data.units.units, kk => k.size[kk]);
  const first = u.plates[0]?.key;
  let mv = key === first && RESOLVED[u.id] ? RESOLVED[u.id] : rawMove(u, key, k.size[key]);
  if (key !== first && RESOLVED[u.id]) {                               // a second still: the same normalized move
    const s0 = k.size[first], s1 = k.size[key], f0 = focusOf(first, s0), f1 = focusOf(key, s1);
    const map = v => [f1[0] + (v[0] - f0[0]) * s1[0] / s0[0], f1[1] + (v[1] - f0[1]) * s1[1] / s0[1], v[2], v[3]];
    mv = { a: map(RESOLVED[u.id].a), b: map(RESOLVED[u.id].b) };
  }
  const e = freeze ? 0 : easeInOutSine(clamp((t - k.t0) / (k.t1 - k.t0)));
  const v = mv.a.map((x, i) => lerp(x, mv.b[i], e));
  if (u.move.kind === 'eye' && !freeze) v[1] += Math.sin((t - k.t0) * 1.3) * 0.002 * k.size[key][1];   // an eye's float
  let shake = [0, 0];
  if (punch !== null && t >= punch) {
    const dt = t - punch;
    v[2] *= 1 + 0.06 * Math.exp(-dt / 0.14);
    if (dt < 2 / 30) shake = [(hash2(k.frame, 31) - 0.5) * 14, (hash2(k.frame, 32) - 0.5) * 10];
  }
  return camAt(k, key, v, shake);
}
