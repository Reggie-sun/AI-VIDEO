// Shared constants and helpers for the v3 animatic. Every helper is a pure function of its arguments (time passed in).
import { F, font } from '../../../../../../motion-kit/src/draw2d.js';
import { clamp, easeOutCubic } from '../../../../../../motion-kit/src/math.js';
import { ANCHORS } from './anchors.js';

export const W = 1920, H = 1080, FPS = 30;
// palette: signal red is the only warm colour; everything else white, silver, steel blue, blue-black
export const RED = '#E3342F', RED_RGB = [227, 52, 47];
export const INK = 'rgba(236,241,244,0.92)', DIM = 'rgba(236,241,244,0.55)', FAINT = 'rgba(236,241,244,0.3)';
export const STEEL = 'rgba(150,178,204,0.95)', STEEL_RGB = [150, 178, 204], BLACK = '#0B0F14';
export const DARK_INK = 'rgba(11,15,20,0.9)', DARK_DIM = 'rgba(11,15,20,0.55)';
export const GROTESK = 'MK Grotesk Bold';
// the tall narrow bold of the chant and the long-note key words (build.py narrow_face: Nimbus Sans Narrow Bold)
export const NARROW = 'MK Narrow Bold';
// the surveillance OSD frame sits this far inside the picture: the outer band belongs to the editorial chrome
// (chrome.js: corner crosses, top rows at y 61, the ticker at y 1034-1067)
export const OSD_IN = 72;
export { F };

// ---- unit data ----
// the accent of a unit: signal red, except in the red-team room (spec: U036-U040 use no red) where it is steel blue
export const accent = u => (u.nored ? STEEL : RED);
export const accentRGB = u => (u.nored ? STEEL_RGB : RED_RGB);
// time token i of the unit's graphic_text appears (its CTC onset, else with the token before it, else the unit cue)
export const tokAt = (u, i) => (u.toks[i] ? u.toks[i].at : u.cue);
// first token whose text matches (case-insensitive) or null
export const tok = (u, text) => u.toks.find(x => x.text.toUpperCase() === text.toUpperCase()) || null;
// the graphic_text split on an arrow (node graph, before/after pairs), trimmed
export const arrowParts = s => String(s).split('→').map(x => x.trim()).filter(Boolean);
// a board's graphic_text is its board text, then ' · ' and a small caption (a2: 03:46 → 03:47 · IRIS CLOCK)
export const boardText = s => String(s || '').split(' · ')[0];
export const boardCaption = s => String(s || '').split(' · ').slice(1).join(' · ');
export const lines = k => k.data.words.lines;
export const beatLen = (k, t) => k.clock.beat(t).len;
// the n-th beat at or after time a (song time = comp time here: offset 0)
export function beatAfter(k, a, n = 0) {
  const b = k.clock.beats;
  let i = b.findIndex(x => x >= a - 1 / FPS);
  if (i < 0) i = b.length - 1;
  return b[Math.min(b.length - 1, i + n)];
}
export function downbeatAfter(k, a) {
  const d = k.clock.downbeats;
  const x = d.find(v => v >= a - 1 / FPS);
  return x === undefined ? a : x;
}
// a plate point: the unit's target (normalized still coordinates) when it has one, else the plate anchor `name`
export function point(k, u, key, name, i = null) {
  const sz = k.size[key];
  if (i !== null && u.targets?.[i]) return [u.targets[i][0] * sz[0], u.targets[i][1] * sz[1]];
  if (i === null && u.target) return [u.target[0] * sz[0], u.target[1] * sz[1]];
  const a = ANCHORS[key]?.[name];
  return a ? [...a] : null;
}
export const anchor = (key, name) => ANCHORS[key]?.[name] ?? null;

// ---- easing helpers ----
export const grow = (t, t0, dur = 0.12) => easeOutCubic(clamp((t - t0) / dur));
// slam() scales about (ax, ay) but draws in absolute coordinates, so a drawing made at the origin is moved there
export const placed = (x, y, draw) => c => { c.translate(x, y); draw(c); };
// a soft bump 0 -> 1 -> 0 over [a, b]
export const bump = (t, a, b) => (t <= a || t >= b ? 0 : Math.sin(Math.PI * (t - a) / (b - a)));

// ---- drawing helpers ----
export function text(ctx, s, x, y, { size = 22, family = F.mono, color = INK, align = 'left', tracking = 1.5, alpha = 1,
  shadow = 'rgba(0,0,0,0.6)', blur = 4 } = {}) {
  if (alpha <= 0 || !s) return 0;
  ctx.save();
  ctx.globalAlpha *= alpha; ctx.textAlign = align;
  if (shadow) { ctx.shadowColor = shadow; ctx.shadowBlur = blur; }
  font(ctx, family, size, tracking); ctx.fillStyle = color; ctx.fillText(s, x, y);
  const w = ctx.measureText(s).width;
  ctx.restore();
  return w;
}
export function measure(ctx, s, size, family = F.mono, tracking = 1.5) {
  ctx.save(); font(ctx, family, size, tracking); const w = ctx.measureText(s).width; ctx.restore(); return w;
}
export function line(ctx, a, b, { color = INK, width = 1.5, dash = null, alpha = 1 } = {}) {
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
  if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke();
  ctx.restore();
}
export function poly(ctx, pts, { color = INK, width = 1.5, dash = null, alpha = 1, close = false } = {}) {
  if (alpha <= 0 || pts.length < 2) return;
  ctx.save();
  ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.moveTo(...pts[0]);
  for (const p of pts.slice(1)) ctx.lineTo(...p);
  if (close) ctx.closePath();
  ctx.stroke();
  ctx.restore();
}
// a blurred dark patch on the feed behind type that sits on a bright plate
export function scrim(ctx, x, y, w, h, alpha = 0.5, color = '#05070a') {
  if (alpha <= 0) return;
  ctx.save();
  ctx.filter = 'blur(26px)'; ctx.globalAlpha = clamp(alpha); ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
  ctx.restore();
}
// darken a screen rect on the feed (black over the scene = exact darkening, before the grade); soft: blurred edges
export function shade(ctx, x, y, w, h, alpha, soft = 0) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = clamp(alpha); ctx.fillStyle = '#000';
  if (soft) ctx.filter = `blur(${soft}px)`;
  ctx.fillRect(x, y, w, h); ctx.restore();
}
// a dark veil in the scene pass (before bloom, so a light under it stops glowing): a screen rect [x, y, w, h] and its
// opacity, as one of the scene shader's soft dark bodies (main.js packs at most 12; edge softness 0.35 x half height)
export const veil = ([x, y, w, h], a) => [x + w / 2, y + h / 2, Math.abs(w) / 2, Math.abs(h) / 2, clamp(a)];
// a soft round light on a 2D layer (emit: HDR light; feed: a glow that survives darkening)
export function glow(ctx, [x, y], r, { color = RED_RGB, alpha = 1 } = {}) {
  if (alpha <= 0 || r <= 0) return;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, `rgba(${color[0]},${color[1]},${color[2]},${clamp(alpha)})`);
  g.addColorStop(0.25, `rgba(${color[0]},${color[1]},${color[2]},${clamp(alpha) * 0.55})`);
  g.addColorStop(1, `rgba(${color[0]},${color[1]},${color[2]},0)`);
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
// points along a polyline up to fraction u of its length
export function along(path, u) {
  const L = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
  const total = L.reduce((a, b) => a + b, 0);
  const seg = [path[0]];
  let s = clamp(u) * total;
  for (let i = 0; i < L.length; i++) {
    if (s <= L[i]) { const q = L[i] ? s / L[i] : 0; seg.push([path[i][0] + (path[i + 1][0] - path[i][0]) * q, path[i][1] + (path[i + 1][1] - path[i][1]) * q]); return seg; }
    s -= L[i]; seg.push(path[i + 1]);
  }
  return seg;
}

// A line of graphic_text drawn word by word: piece i (token i with the separators before it) appears at its token's
// time (u.toks: the CTC onset, else with the token before it). The layout is the whole line's, so nothing reflows.
// s: the line (a graphic_text line); toks: the unit's tokens from index `from` on. Returns the line width.
export function tokenLine(ctx, s, toks, from, t, x, y, { size = 22, family = F.mono, color = INK, align = 'left',
  tracking = 1.5, alpha = 1, shadow = 'rgba(0,0,0,0.6)', fade = 0.08, colorOf = null } = {}) {
  const total = measure(ctx, s, size, family, tracking);
  const x0 = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  let pos = 0, j = from;
  while (pos < s.length) {
    const tk = toks[j];
    let end = s.length;
    if (tk) {
      const at = s.indexOf(tk.text, pos);
      if (at >= 0) end = at + tk.text.length;
    }
    const piece = s.slice(pos, end), when = tk ? tk.at : (toks[j - 1]?.at ?? 0);
    const a = alpha * clamp((t - when) / fade);
    if (a > 0) text(ctx, piece, x0 + measure(ctx, s.slice(0, pos), size, family, tracking), y,
      { size, family, color: colorOf ? colorOf(tk) : color, tracking, alpha: a, shadow });
    pos = end; j += 1;
  }
  return total;
}

// ---- the story clock (seconds of the day). The flip boards set it: the first flipclock unit lands on its second time
// (03:47) at its cue, the second (03:48) at its cue; before the first the clock runs up from two seconds earlier, after
// the last it runs in real time. The film is IRIS's minute, so the OSD clock never disagrees with the flap boards. ----
const hhmm = s => { const m = /(\d\d):?(\d\d)\s*$/.exec(s); return m ? (+m[1]) * 3600 + (+m[2]) * 60 : null; };
let FLIPS = null;
function flips(k) {
  if (FLIPS) return FLIPS;
  FLIPS = k.data.units.units.filter(u => u.graphics.some(g => g.startsWith('flipclock_')))
    .map(u => ({ t: u.cue, s: hhmm(arrowParts(boardText(u.text)).pop() || '') ?? hhmm(u.graphics.find(g => g.startsWith('flipclock_')).split('_').pop()) }))
    .filter(x => x.s !== null);
  return FLIPS;
}
export function storyClock(k, t) {
  const fl = flips(k);
  if (!fl.length) return 3 * 3600 + 47 * 60 + t;
  if (t < fl[0].t) return fl[0].s - 2 + 2 * Math.max(0, t) / fl[0].t;
  for (let i = 0; i + 1 < fl.length; i++) {
    if (t < fl[i + 1].t) return fl[i].s + (fl[i + 1].s - fl[i].s) * (t - fl[i].t) / (fl[i + 1].t - fl[i].t);
  }
  const last = fl[fl.length - 1];
  return last.s + (t - last.t);
}
export function hms(s) {
  const p = n => String(Math.floor(n)).padStart(2, '0');
  return `${p(s / 3600 % 24)}:${p(s / 60 % 60)}:${p(s % 60)}`;
}
