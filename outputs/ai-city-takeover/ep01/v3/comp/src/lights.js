// Light family and in-picture effects on the stills: her red light flickering on, breathing, flickering alone in the
// dark; red light spreading over the floor; the door gap dimming and closing to a line; the spotlight snapping on;
// every red pressed to grey; the picture covered to black; the city breathing on the kick; the racks re-lighting; the
// EVAL screens going dark; the grey photo; the glass reflection; breath fog; the fingertip trace; the impact pulse.
// Signal red is the only warm light (scene grade uRedKeep presses the plate's own red to grey). Pure functions of t.
import { glowPath } from '../../../../../../motion-kit/src/draw2d.js';
import { clamp, easeInOutCubic, easeOutCubic, hash2, lerp } from '../../../../../../motion-kit/src/math.js';
import { ANCHORS } from './anchors.js';
import { DIM, H, INK, RED_RGB, W, along, beatLen, glow, grow, point, shade, text, tokAt } from './util.js';

const A = key => ANCHORS[key] || {};
const outPath = (cm, pts) => pts.map(p => cm.out(p));
const RED_KEEP = 1.12;                                                   // motion-kit's default red keep (lit)
const BLOOM = 0.55, HALATION = 0.35;                                     // motion-kit's default bloom and halation
// her red light as emitted light, scaled with the camera: the collar line (both ways, so it is even) and the ear LED
function herRed(k, cm, key, alpha, { core = 3, halo = 18, led = 22, plate = null } = {}) {
  if (alpha <= 0) return;
  const a = A(key), s = cm.s / 1.15, e = k.layers.emit.ctx;
  if (a.collar) {
    glowPath(e, outPath(cm, a.collar), { color: RED_RGB, core: core * s, halo: halo * s, alpha, head: 1 });
    glowPath(e, outPath(cm, [...a.collar].reverse()), { color: RED_RGB, core: core * s, halo: halo * s, alpha, head: 1 });
  }
  const p = plate || a.led;
  if (p) glow(e, cm.out(p), led * s, { alpha: 0.9 * alpha });
}
let SCRATCH = null;                                                    // reused scratch canvas, cleared on every use
function scratch() {
  if (!SCRATCH) { SCRATCH = document.createElement('canvas'); SCRATCH.width = W; SCRATCH.height = H; }
  const c = SCRATCH.getContext('2d', { willReadFrequently: true });
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.filter = 'none'; c.clearRect(0, 0, W, H);
  return c;
}
// the door gap of a still as a screen rect [x, y, w, h] (slit anchor; a target moves its x)
function gapRect(k, u, cm, half = 26) {
  const a = A(cm.key);
  if (!a.slit && !u.target) return null;
  const [[x0, y0], [, y1]] = a.slit || [[0, 0], [0, k.size[cm.key][1]]];
  const x = u.target ? u.target[0] * k.size[cm.key][0] : x0;
  const p = cm.out([x - half, y0]), q = cm.out([x + half, y1]);
  return [p[0], p[1], q[0] - p[0], q[1] - p[1]];
}

// light_flicker_on's state at t: off before the cue; on the cue it flickers twice (2 frames on, 3 off, 2 on, 2 off),
// then holds. main.js shows the unit's lights-off still (build.py lights_off) whenever it is off.
export function lightOn(u, t) {
  const n = Math.round((t - u.cue) * 30);
  return t >= u.cue - 1e-6 && (n <= 1 || (n >= 5 && n <= 6) || n >= 9);
}

export const LIGHTS = {
  // her lights come on at the cue: before it the still is the lights-off one (main.js) and every other red of the
  // picture is pressed to grey too (a2 修正 U002: fully neutral grey, no dim orange line); then the flicker, then red
  light_flicker_on(k, t, u, cm) {
    const on = lightOn(u, t);
    herRed(k, cm, cm.key, on ? 1 : 0, { halo: 22 });
    return { emitGain: on ? 2.2 : 0, grade: { uRedKeep: on ? RED_KEEP : 0 } };
  },
  // the searchlight falters once on the cue: two frames almost dark, then it snaps back a little over-bright and
  // settles (one dip, not a strobe)
  spotlight_flicker(k, t, u) {
    const n = Math.round((t - u.cue) * 30);
    if (t < u.cue - 1e-6) return {};
    if (n <= 1) return { plateGain: 0.16, emitGain: 0 };
    const dt = t - u.cue - 2 / 30;
    return { plateGain: 1 + 0.35 * Math.exp(-dt / 0.12), grade: { uExposure: 1 + 0.18 * Math.exp(-dt / 0.16) } };
  },
  // the film's end: the last 0.8 s of the unit fade to black, picture, type and chrome together (black on the last frame)
  fade_out_end(k, t) {
    const d = clamp((t - (k.t1 - 0.8)) / (0.8 - 1 / 30));
    return d > 0 ? { grade: { uFade: easeInOutCubic(d) } } : {};
  },
  // her red light breathes (about one breath per two beats)
  led_breathe(k, t, u, cm) {
    const bl = beatLen(k, t), a = 0.15 + 0.75 * Math.sin(Math.PI * (t - k.t0) / (2 * bl)) ** 2;
    herRed(k, cm, cm.key, a, { core: 2.5, halo: 16, led: 18 });
    return { emitGain: 2.0 };
  },
  // dark; only her red light left
  darken_all_but_red(k, t, u, cm) {
    herRed(k, cm, cm.key, grow(t, k.t0, 0.3), { led: 14 });
    return { plateGain: lerp(0.35, 0.03, easeOutCubic(clamp((t - k.t0) / 0.35))), emitGain: 2.4 };
  },
  // the thin line of red from the door gap leaks onto the wet floor: a narrow, soft reflection that grows from the cue
  // (limited access is a line, not a flood: the streak stays a few door-gap widths wide)
  light_spread_floor(k, t, u, cm) {
    const a = A(cm.key), e = k.layers.emit.ctx, sz = k.size[cm.key];
    const gx = u.target ? u.target[0] * sz[0] : a.floor?.[0];
    if (gx === undefined) return {};
    const fy = a.floor?.[1] ?? (u.target ? u.target[1] * sz[1] + 0.15 * sz[1] : sz[1] * 0.6);
    const p = easeOutCubic(clamp((t - u.cue) / 1.2)), apex = cm.out([gx, fy]), bot = cm.out([gx, sz[1]]);
    const half = lerp(6, 120, p) * cm.s;
    e.save(); e.globalCompositeOperation = 'lighter'; e.filter = `blur(${Math.round(6 * cm.s)}px)`;
    const g = e.createLinearGradient(0, apex[1], 0, bot[1]);
    g.addColorStop(0, `rgba(${RED_RGB},${0.42 * (0.4 + 0.6 * p)})`); g.addColorStop(1, `rgba(${RED_RGB},${0.03 + 0.09 * p})`);
    e.fillStyle = g; e.beginPath(); e.moveTo(apex[0] - 4, apex[1]); e.lineTo(apex[0] + 4, apex[1]);
    e.lineTo(bot[0] + half, bot[1]); e.lineTo(bot[0] - half * 0.85, bot[1]); e.closePath(); e.fill();
    e.restore();
    glowPath(e, [apex, [lerp(apex[0], bot[0], p), lerp(apex[1], bot[1], p)]], { color: RED_RGB, core: 2, halo: 12, alpha: 0.5 * p });
    if (a.slit) glowPath(e, outPath(cm, [[gx, a.slit[0][1]], [gx, a.slit[1][1]]]), { color: RED_RGB, core: 2.5 + 1.5 * p, halo: 16 + 14 * p, alpha: 0.55 + 0.35 * p });
    return { emitGain: 1.4 };
  },
  // the door gap's red light dims (over 1.2 s around the cue, or after it when the cue is the unit's start)
  gap_dim(k, t, u, cm) {
    const r = gapRect(k, u, cm);
    const start = Math.max(k.t0, u.cue - 0.6), d = easeInOutCubic(clamp((t - start) / 1.2));
    if (r) {
      shade(k.layers.feed.ctx, r[0] - 12, r[1], r[2] + 24, r[3], 0.82 * d, 10);
      const a = A(cm.key);
      if (a.floor) {                                                     // its reflection on the floor dims with it
        const f0 = cm.out([a.floor[0] - 40, a.floor[1]]), f1 = cm.out([a.floor[0] + 40, k.size[cm.key][1]]);
        shade(k.layers.feed.ctx, f0[0], f0[1], f1[0] - f0[0], f1[1] - f0[1], 0.75 * d, 16);
      }
    }
    // the gap's glow dims with it: the bloom is taken from the plate before the feed's shading, so it is turned down too
    return { grade: { uRedKeep: lerp(RED_KEEP, 0.55, d), uBloomGain: lerp(BLOOM, 0.3, d), uHalation: lerp(HALATION, 0.18, d) } };
  },
  // the door closes by itself: the gap's red shrinks to a line at the target x, the line goes out, the pool fades
  gap_close_mask(k, t, u, cm) {
    const a = A(cm.key), sz = k.size[cm.key], f = k.layers.feed.ctx;
    const x = u.target ? u.target[0] * sz[0] : a.slit?.[0][0];
    if (x === undefined) return {};
    const span = k.t1 - u.cue, close = easeInOutCubic(clamp((t - u.cue) / (0.6 * span)));
    const out = clamp((t - u.cue - 0.68 * span) / (0.17 * span));
    const top = a.slit ? a.slit[0][1] : 0, bot = a.slit ? a.slit[1][1] : sz[1];
    const halfW = 90 * (1 - close) + 2;                                  // plate px of red left open around x
    const l0 = cm.out([x - 260, top]), l1 = cm.out([x - halfW, bot + 6]), r0 = cm.out([x + halfW, top]), r1 = cm.out([x + 260, bot + 6]);
    shade(f, l0[0], l0[1] - 4, l1[0] - l0[0], l1[1] - l0[1] + 8, 0.92 * close, 4);
    shade(f, r0[0], r0[1] - 4, r1[0] - r0[0], r1[1] - r0[1] + 8, 0.92 * close, 4);
    if (out > 0) {                                                       // the last line goes out, and its spill with it
      const m0 = cm.out([x - halfW - 6, top]), m1 = cm.out([x + halfW + 6, bot + 6]);
      shade(f, m0[0], m0[1] - 4, m1[0] - m0[0], m1[1] - m0[1] + 8, out, 3);
      const s0 = cm.out([x - 140, top]), s1 = cm.out([x + 140, bot + 6]);
      shade(f, s0[0], s0[1] - 4, s1[0] - s0[0], s1[1] - s0[1] + 8, 0.7 * out, 40);
    }
    if (a.pool) {                                                        // the red pool on the floor fades with the gap
      const p0 = cm.out(a.pool[0]), p1 = cm.out(a.pool[1]);
      shade(f, p0[0] - 40, p0[1], p1[0] - p0[0] + 80, p1[1] - p0[1] + 40, Math.max(0.8 * close, 0.95 * out), 30);
    }
    // the gap's red fades with it and is gone (pressed to grey) once the line is out
    return { grade: { uRedKeep: lerp(RED_KEEP, 0.25, close) * (1 - out), uSat: lerp(0.86, 0.55, out),
      uBloomGain: lerp(BLOOM, 0.2, close) * (1 - 0.75 * out), uHalation: lerp(HALATION, 0.1, close) * (1 - out) } };
  },
  // the overhead light hard-cuts on at the cue: exposure jumps, then settles
  spotlight_snap_on(k, t, u) {
    if (t < u.cue) return { plateGain: 0.05 };
    const dt = t - u.cue;
    return { plateGain: 1 + 0.9 * Math.exp(-dt / 0.12), grade: { uExposure: 1 + 0.35 * Math.exp(-dt / 0.18) } };
  },
  // every red of the unit pressed to grey (the door is shut, every light is off)
  red_off() {
    return { grade: { uRedKeep: 0 } };
  },
  // the picture is covered to black around the cue (a hand over the lens); the OSD goes with it
  fade_to_black(k, t, u) {
    const d = easeInOutCubic(clamp((t - (u.cue - 0.35)) / 0.45));
    return { plateGain: 1 - d, emitGain: 2.0, osdAlpha: 1 - d };
  },
  // in the dark one red point flickers on (after the picture has gone black) and stays
  red_dot_flicker(k, t, u, cm) {
    const p = point(k, u, cm.key, 'dot') || point(k, u, cm.key, 'led');
    const t0 = u.cue + 0.25, n = Math.floor((t - t0) * 30);
    if (!p || t < t0) return {};
    const on = n <= 2 || (n >= 6 && n <= 7) || n >= 13;
    if (on) { glow(k.layers.emit.ctx, cm.out(p), 26 * cm.s, { alpha: 0.95 }); glow(k.layers.feed.ctx, cm.out(p), 9 * cm.s, { alpha: 0.95 }); }
    return { emitGain: 2.4 };
  },
  // the city's lights breathe on the kick (no hard flash)
  city_flicker_on_beat(k, t) {
    const kick = k.clock.pulse('kick', t + 1 / 30, 0.16);
    return { plateGain: 0.62 + 0.5 * kick };
  },
  // an impact on the cue (the camera's punch is in camera.js) with a short exposure lift
  pulse_on_beat(k, t, u) {
    if (t < u.cue) return {};
    return { grade: { uExposure: 1 + 0.22 * Math.exp(-(t - u.cue) / 0.14) } };
  },
  // the racks behind her come back on, a strip per beat from the cue (outside her body)
  lights_back_on(k, t, u, cm) {
    const f = k.layers.feed.ctx, tL = u.cue, bl = beatLen(k, tL), [pw] = k.size[cm.key];
    const body = A(cm.key).body || A(cm.key).face || [pw / 2 - 160, 0, 320, 0], left = body[0], right = body[0] + body[2], n = 5;
    for (let i = 0; i < n; i++) {
      const a = 0.9 * (1 - grow(t, tL + i * bl, 0.25));
      if (a <= 0) continue;
      const lx0 = cm.out([left * (1 - (i + 1) / n), 0])[0], lx1 = cm.out([left * (1 - i / n), 0])[0];
      const rx0 = cm.out([right + (pw - right) * i / n, 0])[0], rx1 = cm.out([right + (pw - right) * (i + 1) / n, 0])[0];
      shade(f, lx0 - 1, 0, lx1 - lx0 + 2, H, a); shade(f, rx0 - 1, 0, rx1 - rx0 + 2, H, a);
    }
    return {};
  },
  // EVAL tags go grey and the screens dark, one per half beat from the EVAL token
  eval_labels_dim(k, t, u, cm) {
    const f = k.layers.feed.ctx, tD = tokAt(u, 0), bl = beatLen(k, tD), word = u.toks[0]?.text || '';
    (A(cm.key).screens || []).forEach((s, i) => {
      const b = cm.box(s), d = grow(t, tD + i * bl * 0.5, 0.2);
      shade(f, b[0], b[1], b[2], b[3], 0.86 * d);
      const x = b[0] + 8, y = b[1] + b[3] + 30;
      f.save(); f.globalAlpha = 1 - 0.55 * d; f.fillStyle = d > 0.5 ? DIM : INK; f.fillRect(b[0], b[1] + b[3] + 8, 4, 28); f.restore();
      text(f, word, x + 4, y, { size: 18, tracking: 3, color: d > 0.5 ? 'rgba(236,241,244,0.4)' : INK });
    });
    return { emitGain: 0 };
  },
  // the photo is grey, frozen like an old print
  desaturate() {                                                        // grey from the cut (no colour frame first)
    return { grade: { uSat: 0, uRedKeep: 0, uLiftAmt: 0.12 } };
  },
  // her reflection in the glass, mirrored, faint and offset, facing her
  reflection_layer(k, t, u, cm) {
    const img = k.bitmaps[cm.key];
    if (!img) return {};
    const c = scratch(), a = 0.4 * easeOutCubic(clamp((t - k.t0 - 0.2) / (0.6 * (k.t1 - k.t0))));
    const s = cm.s * 0.86, sw = img.width * s, sh = img.height * s;
    const face = A(cm.key).face, fx = face ? face[0] + face[2] / 2 : img.width / 2;
    const mx = cm.out([fx, 0])[0] + 470;                                 // the mirrored face sits beside hers
    c.save(); c.translate(mx + fx * s, (H - sh) / 2 + 10); c.scale(-1, 1); c.drawImage(img, 0, 0, sw, sh); c.restore();
    c.globalCompositeOperation = 'destination-in';
    const g = c.createLinearGradient(W * 0.5, 0, W, 0);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.3, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0.8)');
    c.fillStyle = g; c.fillRect(0, 0, W, H);
    const f = k.layers.feed.ctx;
    f.save(); f.globalAlpha = a; f.globalCompositeOperation = 'lighter'; f.drawImage(c.canvas, 0, 0); f.restore();
    return {};
  },
  // a small patch of fog on the glass by her mouth, rising from the cue to the end of the unit: a frosted haze that
  // veils what is behind the glass (laid over the feed, never added as light, so it does not glow)
  breath_fog(k, t, u, cm) {
    const p = point(k, u, cm.key, 'fog');
    if (!p) return {};
    const g = easeOutCubic(clamp((t - u.cue) / Math.max(0.5, k.t1 - u.cue - 0.2))), q = cm.out(p), f = k.layers.feed.ctx;
    const r = 150 * cm.s * (0.4 + 0.6 * g);
    if (g <= 0) return {};
    f.save(); f.filter = `blur(${Math.round(8 * cm.s)}px)`;
    for (let i = 0; i < 14; i++) {                                      // a blotchy patch, not a disc
      const ang = hash2(i, 71) * Math.PI * 2, d = hash2(i, 72) * r * 0.55;
      const c = [q[0] + Math.cos(ang) * d, q[1] + Math.sin(ang) * d * 1.3], rr = r * (0.35 + 0.3 * hash2(i, 73));
      const gr = f.createRadialGradient(c[0], c[1], 0, c[0], c[1], rr);
      gr.addColorStop(0, `rgba(200,212,224,${0.1 * g})`); gr.addColorStop(1, 'rgba(200,212,224,0)');
      f.fillStyle = gr; f.beginPath(); f.arc(c[0], c[1], rr, 0, Math.PI * 2); f.fill();
    }
    f.restore();
    return {};
  },
  // a fine red trace along the skyline from her fingertip
  fingertip_light_trail(k, t, u, cm) {
    const a = A(cm.key);
    if (!a.skyline) return {};
    const p = clamp((t - k.t0 - 0.25) / (k.t1 - k.t0 - 0.6)), pts = outPath(cm, along(a.skyline, p));
    if (pts.length > 1) {
      glowPath(k.layers.emit.ctx, pts, { color: RED_RGB, core: 2.2, halo: 10, alpha: 0.9 });
      glow(k.layers.emit.ctx, pts[pts.length - 1], 16, { alpha: 0.9 });
    }
    return { emitGain: 2.0 };
  },
  // (monitor_frame) only her red light breathes
  breathe_red(k, t, u, cm) {
    herRed(k, cm, cm.key, 0.3 + 0.35 * Math.sin((t - k.t0) * 1.7) ** 2, { core: 2, halo: 12, led: 12 });
    return { emitGain: 2.0 };
  },
};
