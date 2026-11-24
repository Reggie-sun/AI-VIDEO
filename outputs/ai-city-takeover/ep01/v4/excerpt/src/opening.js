// IRIS EP01 opening (2026-11-21, opening.py): song 0-40.7859 s, s001-s010 as Seedance takes (pilot/opening), each
// picture shown whole (2304x1296 prepared, 1.2x the output), no overlay, no depth of field, no push: the print of
// shots8.js (PRINT) under main.js's v4r11 grade, as the v4r11 picture of song 40.79-59.23 that follows it.
import { clampView } from './shots.js';

const SEQ = [2304, 1296];
const PRINT = { uHalftone: 0.085, uCell: 3.0, uGrain: 0.034 };

export function openingShot() {
  return { A: { tex: 'seq', view: clampView(SEQ, [1152, 648, 1.0, 0]), lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT } };
}

// IRIS EP01 opening v2 (2026-11-21, opening_v2.py, plan/v2.html): the same print, and per shot from the EDL a still's
// slow push (shot.still: one prepared picture, zoom z0 -> z1 over the shot round its centre cx, cy in picture px) and
// per-frame events (shot.fx: digital push steps, zoom multiplied); the screens and one-off treatments are grade fields
// the engine merges last (main.js: shot.screen, shot.fx[].grade).
export function openingShotV2(k) {
  const sh = k.shot, st = sh.still;
  let z = 1.0, cx = 1152, cy = 648;
  if (st) {
    const u = (k.f - sh.f0) / Math.max(1, sh.f1 - 1 - sh.f0);
    z = st.zoom[0] + (st.zoom[1] - st.zoom[0]) * u;
    [cx, cy] = st.center;
  }
  for (const e of sh.fx || []) if (k.f >= e.f0 && k.f < e.f1 && e.zoom) z *= e.zoom;
  return { A: { tex: 'seq', view: clampView(SEQ, [cx, cy, z, 0]), lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT } };
}
