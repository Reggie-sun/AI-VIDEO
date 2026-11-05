// IRIS EP01《Looked Outside》v3 — full-length animatic a2 on motion-kit (spec: ../../animatic-spec.md, a2 修订).
// Driven by data/units.json (build.py resolves ../../shots-map.json, board v2-a2): one generic scene draws every unit from
// its fields - the still(s) under the code camera (camera.js), the viewpoint's look (system: surveillance OSD; iris: no
// HUD or OSD at all, only the lyric and narrative labels; graphic: full-screen graphics on the blue-black ground), each
// named graphic through its family handler (osd / boards / labels / lights / charts), the lyric in its type role
// (lyric.js) and, over every unit, the editorial chrome (chrome.js: an edit layer, not the story's OSD). Every value is a
// pure function of comp time t.
// A sample composition (build.py --samples) sets data-mk-offset on the root: its time t shows the film at t + offset.
import { install } from '../../../../../../motion-kit/src/runtime.js';
import ASSETS from '../data/assets.json';
import PLATES from '../data/plates.json';
import { camAt, unitCam } from './camera.js';
import { drawChrome } from './chrome.js';
import { handlerOf } from './graphics.js';
import { lightOn } from './lights.js';
import { drawLyric } from './lyric.js';
import { osd } from './osd.js';
import { FPS, H, W, text } from './util.js';

const OFFSET = Number(document.getElementById('root')?.dataset?.mkOffset || 0);
// the viewpoint's base look: system = desaturated surveillance feed; iris keeps motion-kit's print grade; graphic too,
// but without its halation, whose orange-tinted glow would put a second warm colour round white type on black (spec:
// signal red is the only warm colour)
const LOOK = { system: { uSat: 0.6, uGrain: 0.045, uHalftone: 0.12, uVignette: 0.4 }, graphic: { uHalation: 0 } };

function merge(p, r) {
  if (!r) return;
  if (r.plateGain !== undefined) p.plateGain = Math.min(p.plateGain ?? Infinity, r.plateGain);
  if (r.emitGain !== undefined) p.emitGain = Math.max(p.emitGain ?? 0, r.emitGain);
  if (r.osdAlpha !== undefined) p.osdAlpha = Math.min(p.osdAlpha ?? 1, r.osdAlpha);
  if (r.grade) p.grade = { ...(p.grade || {}), ...r.grade };
}

function unitScene(t, k) {
  const u = k.shot.u;
  // a graphic unit is drawn on the flat ground (its stills, if any, are its graphics' material)
  const pl = u.view === 'graphic' ? null : u.plates.filter(p => k.frame >= p.f).pop() || u.plates[0];
  const key = pl ? pl.key : 'GROUND';
  // her lights switched off (light_flicker_on): the derived still with the red pressed to grey until the light is on;
  // the camera, anchors and OSD keep reading the still it was made from
  const tex = u.off && pl === u.plates[0] && !lightOn(u, t) ? u.off : key;
  k.plateKey = key;
  const opts = { freeze: u.graphics.includes('osd_paused_freeze'), punch: u.graphics.includes('pulse_on_beat') ? u.cue : null };
  const cm = pl ? unitCam(k, u, t, key, opts) : camAt(k, 'GROUND', [W / 2, H / 2, 1, 0]);
  const p = { plate: tex, view: cm.view, fit: cm.fit, fogA: [0, 1, 0, 0], fogB: [0, 1, 0, 0], emitGain: 2.0,
    grade: { ...(LOOK[u.view] || {}) } };
  for (const g of u.graphics) {
    const h = handlerOf(g);
    if (h) merge(p, h(k, t, u, cm));
  }
  // a system unit always carries the OSD (an osd_* or monitor graphic draws its own); iris and graphic never do
  if (u.view === 'system' && !k.osd) osd(k, t, { alpha: p.osdAlpha ?? 1 });
  // spec: the red-team room has no red: its own reds pressed to grey, no warm halation, and no chromatic aberration
  // (which fringes the dark OSD type and glass frames red on the white room)
  if (u.nored) Object.assign(p.grade, { uRedKeep: 0, uHalation: 0, uCA: 0 });
  if (p.plateGain === Infinity) delete p.plateGain;
  // the ground under the type is light on a light still (the white lab) and on the white panel: dark ink there
  const light = u.light || !!PLATES[key]?.light;
  drawLyric(k, t, u, { light });
  if (PLATES[key]?.status === 'placeholder') {
    text(k.layers.overlay.ctx, `PLACEHOLDER · ${u.id} · ${key}`, W / 2, 140, { size: 26, align: 'center', tracking: 4 });
  }
  drawChrome(k, t, u, { light });                                    // the edit layer, over everything
  return p;
}

function pickShot(t, clock, data) {
  const f = Math.round((t + OFFSET) * FPS), us = data.units.units;
  let lo = 0, hi = us.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (us[mid].f0 <= f) lo = mid; else hi = mid - 1; }
  const u = us[lo];
  return { id: 'unit', u, t0: u.f0 / FPS, t1: u.f1 / FPS };
}

install({
  width: W, height: H, fps: FPS, canvasId: 'stage',
  fontsUrl: 'fonts', beatsUrl: 'data/beats.json', hitsUrl: 'data/hits.json', musicUrl: 'data/music.json',
  data: { words: 'data/words.json', events: 'data/events.json', units: 'data/units.json' },
  images: Object.fromEntries(ASSETS.images.map(key => [key, { url: `plates/${key}.png` }])),
  bitmaps: Object.fromEntries(ASSETS.bitmaps.map(key => [key, { url: `plates/${key}.png` }])),
  scenes: { unit: (t, k) => { const T = t + OFFSET; k.frame = Math.round(T * FPS); return unitScene(T, k); } },
  pickShot,
});
