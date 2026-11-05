// The camera plays the track (method from the ESCAPE VELOCITY toolkit, tool 18; code original to this project):
// a punch on kicks gated by the drum envelope, an impact on a declared hit, and stillness everywhere else
// ("Hold still where the song breathes"). Pure functions of comp time t.
//
// - Only inside the declared sections. A kick or hit before a section's start never carries into it, so the
//   camera holds through verses and starts moving on the first event of the section.
// - The picture may lead the sound by one frame, never trail it: events are read at t + lead.
// - Punch and impact do not add up: the larger one wins, so a hit on a kick is one impact.
// - A zoomed view keeps protected plate rects (a burned-in platform mark, a face) inside the frame:
//   protectCentre() moves the zoom centre, it never shrinks the zoom.
import { clamp, smoothstep } from './math.js';

export const PUNCH = Object.freeze({ kind: 'kick', amp: 0.02, decay: 0.09, gate: 'low', gateLo: 0.2, gateHi: 0.6 });
export const IMPACT = Object.freeze({ amp: 0.06, decay: 0.10 });

// zoom multiplier (>= 1) at comp time t
//   sections: [[t0, t1], ...] comp seconds where the camera moves
//   impacts: comp times of declared hits
//   punch / impact: shapes (null turns one off); amp is the zoom at the event, decay the 1/e time in seconds
export function trackZoom(t, clock, { sections = [], impacts = [], punch = PUNCH, impact = IMPACT, lead } = {}) {
  const tl = t + (lead ?? 1 / clock.fps);
  const section = sections.find(([a, b]) => t >= a && t < b);
  if (!section) return 1;
  const t0 = section[0];
  let p = 0;
  if (punch) {
    const e = clock.last(clock.hits[punch.kind], tl);
    if (e !== null && e >= t0) {
      const gate = smoothstep(punch.gateLo, punch.gateHi, clock.env(punch.gate, e));
      p = punch.amp * gate * Math.exp(-(tl - e) / punch.decay);
    }
  }
  let q = 0;
  if (impact) {
    for (const h of impacts) {
      if (h >= t0 && h <= tl) q = Math.max(q, impact.amp * Math.exp(-(tl - h) / impact.decay));
    }
  }
  return 1 + Math.max(p, q);
}

// centre [cx, cy] (plate px) of a view at s output px per plate px, moved so every protected plate rect
// [x, y, w, h] stays inside the W x H frame; unchanged when they already fit. Rects that cannot all fit at this
// zoom keep the upper bound (best effort): callers keep the zoom small enough for their rects.
export function protectCentre(cx, cy, s, rects, W, H) {
  const hx = W / 2 / s, hy = H / 2 / s;
  let lox = -Infinity, hix = Infinity, loy = -Infinity, hiy = Infinity;
  for (const [x, y, w, h] of rects) {
    lox = Math.max(lox, x + w - hx); hix = Math.min(hix, x + hx);
    loy = Math.max(loy, y + h - hy); hiy = Math.min(hiy, y + hy);
  }
  return [clamp(cx, lox, hix), clamp(cy, loy, hiy)];
}
