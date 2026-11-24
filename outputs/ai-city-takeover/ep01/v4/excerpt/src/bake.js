// Agentcut bake (2026-11-20): the stills of the Agentcut replica's song 0-36.2 s (escape-velocity-replica, pic-motion)
// through this engine's v4r10c print, so the print and the grain sit in frame pixels and move per frame as in v4r10c.
// Each shot (data/edl-bake-*.json, bake_agentcut.py) carries its StillMove props; the camera here is StillMove's CSS
// (cover fit, a push about (ox, oy), a crop about its own origin from cut.at, the mosaic picture on a pixel cut's frame)
// as a view. No overlay, no shake; the grade is main.js's v4r10c grade with the shots' print trim (shots8.js PRINT).
import { fitOf } from './shots.js';

const W = 1920, H = 1080;
const PRINT = { uHalftone: 0.085, uCell: 3.0, uGrain: 0.034 };

export function bakeShot(k) {
  const m = k.shot.move, lf = k.f - k.shot.f0;
  const t = Math.min(1, Math.max(0, (lf - m.push.from) / Math.max(1, m.push.to - m.push.from)));
  const push = 1 + (m.push.scale - 1) * t;
  let cut = null;
  for (const c of m.cuts) if (c.at <= lf) cut = c;
  const tex = cut && cut.kind === 'pixel' && lf === cut.at && m.mosaic ? m.mosaic : m.src;
  const cs = cut ? cut.scale : 1, co = cut ? [cut.ox, cut.oy] : [0, 0];
  // screen P = z Q + b for a point Q of the cover layout (CSS: T(o) S(push) T(-o) T(co) S(cs) T(-co))
  const z = push * cs;
  const b = [push * (co[0] - cs * co[0] - m.push.ox) + m.push.ox, push * (co[1] - cs * co[1] - m.push.oy) + m.push.oy];
  const size = m.size, fit = fitOf(size);
  const off = [(W - size[0] * fit) / 2, (H - size[1] * fit) / 2];
  const view = [((W / 2 - b[0]) / z - off[0]) / fit, ((H / 2 - b[1]) / z - off[1]) / fit, z, 0];
  return { A: { tex, view, lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT } };
}
