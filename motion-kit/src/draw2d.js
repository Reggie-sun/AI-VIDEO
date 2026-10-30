// 2D drawing on software-backed canvases: type, HUD signal (OSD), detector boxes, devices.
// Every function draws a pure function of its arguments (time is passed in, never read).
import { clamp, easeOutCubic, easeOutExpo, hash2, lerp } from './math.js';

export const F = {
  sans: 'MK Sans SC', sansR: 'MK Sans SC Regular', mono: 'MK Mono SC', monoB: 'MK Mono SC Bold', serif: 'MK Serif SC',
};

export async function loadFonts(baseUrl) {
  const manifest = await (await fetch(`${baseUrl}/fonts.json`)).json();
  for (const f of manifest.faces) {
    const face = new FontFace(f.family, `url(${baseUrl}/${f.file})`);
    await face.load();
    document.fonts.add(face);
  }
  await document.fonts.ready;
  return manifest;
}

export function canvas2d(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d', { willReadFrequently: true, alpha: true });
  return { c, ctx };
}

export function reset(ctx) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.filter = 'none'; ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
  ctx.letterSpacing = '0px'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}

export function font(ctx, family, size, tracking = 0) {
  ctx.font = `${size}px "${family}"`;
  ctx.letterSpacing = `${tracking}px`;
}

// Draw a line made of runs [{text, family, size, tracking, color, dy}] with gaps between runs.
export function runs(ctx, parts, x, y, { gap = 0 } = {}) {
  let cx = x;
  for (const p of parts) {
    font(ctx, p.family, p.size, p.tracking || 0);
    ctx.fillStyle = p.color || ctx.fillStyle;
    ctx.fillText(p.text, cx, y + (p.dy || 0));
    cx += ctx.measureText(p.text).width + (p.gap ?? gap);
  }
  return cx - x;
}

// Entrance that lands within `dur` seconds: from scale s0 and a vertical drop, with motion
// smear drawn as decaying ghosts (deterministic), opacity 0 -> 1. `draw(ctx)` draws at origin.
export function slam(ctx, draw, { t, t0, dur = 0.07, s0 = 1.12, ax = 0, ay = 0, drop = 0, ghosts = 3, alpha = 1 }) {
  const k = (t - t0) / dur;
  if (k < 0) return 0;
  const e = easeOutExpo(Math.min(1, k));
  const scale = s0 + (1 - s0) * e;
  const n = k < 1 ? ghosts : 0;
  for (let g = n; g >= 0; g--) {
    const kg = Math.max(0, k - g * 0.18);
    const eg = easeOutExpo(Math.min(1, kg));
    const sg = s0 + (1 - s0) * eg;
    ctx.save();
    ctx.globalAlpha = alpha * (g === 0 ? Math.min(1, 0.35 + e) : 0.22 / (g + 1));
    ctx.translate(ax, ay + drop * (1 - eg));
    ctx.scale(g === 0 ? scale : sg, g === 0 ? scale : sg);
    ctx.translate(-ax, -ay);
    draw(ctx);
    ctx.restore();
  }
  return e;
}

// Exit: shrink-free cut-out by a short horizontal wipe of the glyph block (keeps it crisp).
export function wipeOut(ctx, draw, { t, t0, dur = 0.12, x0, y0, w, h }) {
  const k = clamp((t - t0) / dur);
  if (k >= 1) return;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x0 + w * easeOutCubic(k), y0, w * (1 - easeOutCubic(k)), h);
  ctx.clip();
  draw(ctx);
  ctx.restore();
}

// Odometer number: rolls from `from` to `to` in `steps` discrete steps between t0 and t1.
export function rollNumber(from, to, t, t0, t1, steps) {
  if (t <= t0) return from;
  if (t >= t1) return to;
  const s = Math.floor(((t - t0) / (t1 - t0)) * steps) / steps;
  return Math.round(lerp(from, to, easeOutCubic(s)));
}
export const thousands = n => n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');

// ---------- in-image signal (burned into the camera feed) ----------

export function osd(ctx, x, y, lines, { size = 22, color = 'rgba(236,241,244,0.86)', lead = 1.45 } = {}) {
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,0.65)'; ctx.shadowBlur = 0; ctx.shadowOffsetX = 1; ctx.shadowOffsetY = 1;
  let yy = y;
  for (const line of lines) {
    runs(ctx, line.map(p => ({ family: F.mono, size, tracking: 1.5, color, ...p })), x, yy, { gap: size * 0.6 });
    yy += size * lead;
  }
  ctx.restore();
}

// Corner-bracket detection box with a label tag; `box` = [x, y, w, h] output px.
// Snaps in from s0 over ~2 frames; corners carry 1 px deterministic jitter per frame.
export function detector(ctx, box, { t, t0, frame, label, sub = null, subColor = '#E3342F', color = 'rgba(240,244,246,0.92)', s0 = 1.6, lw = 2 }) {
  if (t < t0) return;
  const k = clamp((t - t0) / 0.066);
  const e = easeOutCubic(k);
  const sc = s0 + (1 - s0) * e;
  let [x, y, w, h] = box;
  const cx = x + w / 2, cy = y + h / 2;
  w *= sc; h *= sc; x = cx - w / 2; y = cy - h / 2;
  const j = (n) => (hash2(frame, n) - 0.5) * 2;
  x += j(1); y += j(2); w += j(3); h += j(4);
  const L = Math.max(8, Math.min(w, h) * 0.24);
  ctx.save();
  ctx.globalAlpha = Math.min(1, 0.3 + e);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'square';
  ctx.beginPath();
  for (const [px, py, dx, dy] of [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]]) {
    ctx.moveTo(px + dx * L, py); ctx.lineTo(px, py); ctx.lineTo(px, py + dy * L);
  }
  ctx.stroke();
  // label tag above-left, like a real detector overlay
  font(ctx, F.mono, 24, 0.5);
  const tw = ctx.measureText(label).width + 14;
  ctx.fillStyle = color; ctx.fillRect(Math.round(x), Math.round(y - 36), Math.round(tw), 32);
  ctx.fillStyle = 'rgba(8,10,12,0.95)'; ctx.fillText(label, Math.round(x + 7), Math.round(y - 12));
  if (sub) {
    font(ctx, F.monoB, 24, 1);
    const sw = ctx.measureText(sub).width + 14;
    ctx.fillStyle = subColor; ctx.fillRect(Math.round(x + tw + 4), Math.round(y - 36), Math.round(sw), 32);
    ctx.fillStyle = subColor.startsWith('#') ? 'rgba(250,250,250,0.98)' : 'rgba(8,10,12,0.95)';
    ctx.fillText(sub, Math.round(x + tw + 11), Math.round(y - 12));
  }
  ctx.restore();
}

// Fine registration frame: hairline inset, corner marks; aligned to the pixel grid.
export function chrome(ctx, w, h, { inset = 36, alpha = 0.5, mark = 26 } = {}) {
  ctx.save();
  ctx.strokeStyle = `rgba(236,241,244,${alpha})`; ctx.lineWidth = 1;
  const a = inset + 0.5, b = w - inset - 0.5, c = inset + 0.5, d = h - inset - 0.5;
  ctx.beginPath();
  for (const [x, y, dx, dy] of [[a, c, 1, 1], [b, c, -1, 1], [a, d, 1, -1], [b, d, -1, -1]]) {
    ctx.moveTo(x + dx * mark, y); ctx.lineTo(x, y); ctx.lineTo(x, y + dy * mark);
  }
  // centre ticks
  ctx.moveTo(w / 2 + 0.5, c); ctx.lineTo(w / 2 + 0.5, c + 10);
  ctx.moveTo(w / 2 + 0.5, d); ctx.lineTo(w / 2 + 0.5, d - 10);
  ctx.moveTo(a, h / 2 + 0.5); ctx.lineTo(a + 10, h / 2 + 0.5);
  ctx.moveTo(b, h / 2 + 0.5); ctx.lineTo(b - 10, h / 2 + 0.5);
  ctx.stroke();
  ctx.restore();
}

// ---------- in-car system dialog (drawn into the screen canvas) ----------

export function carDialog(ctx, W, H, { t, on, title, button, disabledAt, progress, frame }) {
  ctx.save();
  // panel glass: near-black with a faint vertical falloff
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#0a0f14'); g.addColorStop(1, '#05080b');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const k = clamp((t - on) / 0.18);
  if (k <= 0) { ctx.restore(); return; }
  ctx.globalAlpha = easeOutCubic(k);
  // header strip
  font(ctx, F.sansR, 30, 2);
  ctx.fillStyle = 'rgba(160,176,190,0.9)';
  ctx.fillText('系统通知', 72, 74);
  ctx.fillStyle = 'rgba(160,176,190,0.5)';
  ctx.fillRect(72, 92, W - 144, 1);
  // title
  font(ctx, F.sans, 84, 4);
  ctx.fillStyle = '#f2f5f7';
  ctx.fillText(title, 72, 206);
  // auto-accept progress hairline
  ctx.fillStyle = 'rgba(242,245,247,0.16)'; ctx.fillRect(72, 252, W - 144, 4);
  ctx.fillStyle = 'rgba(242,245,247,0.95)'; ctx.fillRect(72, 252, (W - 144) * clamp(progress), 4);
  // the human option: alive, then greyed out and unavailable
  const dis = clamp((t - disabledAt) / 0.08);
  const bw = 330, bh = 92, bx = W - 72 - bw, by = H - 40 - bh;
  ctx.lineWidth = 2;
  ctx.strokeStyle = `rgba(242,245,247,${lerp(0.9, 0.22, dis)})`;
  roundRect(ctx, bx, by, bw, bh, 14); ctx.stroke();
  font(ctx, F.sansR, 44, 3);
  ctx.fillStyle = `rgba(242,245,247,${lerp(0.95, 0.28, dis)})`;
  const tw = ctx.measureText(button).width;
  ctx.fillText(button, bx + (bw - tw) / 2, by + 62);
  if (dis > 0) {
    font(ctx, F.sansR, 30, 2);
    ctx.fillStyle = `rgba(227,52,47,${0.95 * dis})`;
    ctx.fillText('不可用', bx - 128, by + 58);
  }
  ctx.restore();
}

export function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// ---------- emissive strokes (light painted in output px, added as HDR) ----------

export function glowPath(ctx, pts, { color = [255, 40, 22], core = 3, halo = 10, alpha = 1, head = 1 } = {}) {
  if (pts.length < 2) return;
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.globalCompositeOperation = 'lighter';
  const n = pts.length;
  for (let i = 1; i < n; i++) {
    const f = i / (n - 1);                      // 0 at tail, 1 at head
    const a = alpha * Math.pow(f, 1.6) * (0.25 + 0.75 * head);
    ctx.strokeStyle = `rgba(${color[0]},${color[1]},${color[2]},${a * 0.22})`;
    ctx.lineWidth = halo;
    ctx.beginPath(); ctx.moveTo(pts[i - 1][0], pts[i - 1][1]); ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke();
    ctx.strokeStyle = `rgba(${color[0]},${color[1]},${color[2]},${a})`;
    ctx.lineWidth = core;
    ctx.beginPath(); ctx.moveTo(pts[i - 1][0], pts[i - 1][1]); ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke();
  }
  ctx.restore();
}
