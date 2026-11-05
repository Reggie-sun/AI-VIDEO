// Explanatory charts in the in-image OSD language (mono labels, hairlines, one red accent): a line chart, a level gauge
// and a day timeline bar. They show shape, not invented numbers: no axis values unless the caller passes them.
// Pure Canvas2D draws; the caller owns time (progress / level / filled) and the layer.
import { F, font } from './draw2d.js';
import { clamp, hash2, lerp } from './math.js';

const INK = 'rgba(236,241,244,0.88)', DIM = 'rgba(236,241,244,0.45)', RULE = 'rgba(236,241,244,0.28)', RED = '#E3342F';

// Schematic series: n points, a low flat level with a little deterministic texture until `knee` (0..1), then a climb
// to `peak`. Values 0..1.
export function kneeSeries(n = 48, { knee = 0.62, base = 0.12, jitter = 0.05, peak = 0.9, seed = 5 } = {}) {
  return Array.from({ length: n }, (_, i) => {
    const u = i / (n - 1), j = (hash2(i, seed) - 0.5) * 2 * jitter;
    if (u < knee) return clamp(base + j);
    const r = (u - knee) / (1 - knee);
    return clamp(base + (peak - base) * Math.sqrt(r) + j * 0.5);
  });
}

// Line chart in box [x, y, w, h]: the series drawn up to `progress` (0..1), grey before index `accentFrom`, red after.
export function lineChart(ctx, series, [x, y, w, h], { progress = 1, accentFrom = Infinity, label = null, note = null,
  size = 14, alpha = 1 } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.fillStyle = RULE;
  ctx.fillRect(Math.round(x), Math.round(y + h) + 0.5, Math.round(w), 1);              // baseline
  ctx.fillRect(Math.round(x), Math.round(y), 1, Math.round(h));                         // axis
  for (let k = 1; k < 4; k++) ctx.fillRect(Math.round(x + (w * k) / 4), Math.round(y + h) - 4, 1, 4);
  if (label) { font(ctx, F.mono, size, 2); ctx.fillStyle = DIM; ctx.fillText(label, x + 8, y + size); }
  if (note) { font(ctx, F.mono, size - 2, 1.5); ctx.fillStyle = DIM; ctx.textAlign = 'right'; ctx.fillText(note, x + w, y + h + size + 8); ctx.textAlign = 'left'; }
  const n = series.length, last = clamp(progress) * (n - 1);
  const pt = i => [x + (w * i) / (n - 1), y + h - h * series[i]];
  const seg = (a, b, color, lw) => {
    if (b <= a) return;
    ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.beginPath();
    ctx.moveTo(...pt(a));
    for (let i = a + 1; i <= Math.floor(b); i++) ctx.lineTo(...pt(i));
    const f = b - Math.floor(b);
    if (f > 0 && Math.floor(b) + 1 < n) {
      const [ax, ay] = pt(Math.floor(b)), [bx, by] = pt(Math.floor(b) + 1);
      ctx.lineTo(lerp(ax, bx, f), lerp(ay, by, f));
    }
    ctx.stroke();
  };
  const k = Math.min(accentFrom, n - 1);
  seg(0, Math.min(last, k), INK, 1.5);
  if (last > k) seg(k, last, RED, 2.5);
  if (last > 0) {                                                                    // the head
    const i = Math.floor(last), f = last - i, [ax, ay] = pt(i), [bx, by] = i + 1 < n ? pt(i + 1) : pt(i);
    ctx.fillStyle = last > k ? RED : INK;
    ctx.fillRect(Math.round(lerp(ax, bx, f)) - 2, Math.round(lerp(ay, by, f)) - 2, 5, 5);
  }
  ctx.restore();
}

// Segmented level gauge in box [x, y, w, h]: `n` cells, `level` (0..1) of them lit red, a label left and a state right.
export function levelGauge(ctx, [x, y, w, h], { n = 10, level = 0, label = '', state = '', size = 14, alpha = 1 } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  font(ctx, F.mono, size, 2);
  ctx.fillStyle = DIM; ctx.fillText(label, x, y - 8);
  ctx.textAlign = 'right'; ctx.fillStyle = level > 0 ? RED : INK; ctx.fillText(state, x + w, y - 8); ctx.textAlign = 'left';
  const gap = 4, cw = (w - gap * (n - 1)) / n, lit = level * n;
  for (let i = 0; i < n; i++) {
    const cx = Math.round(x + i * (cw + gap)), fill = clamp(lit - i);
    ctx.strokeStyle = RULE; ctx.lineWidth = 1; ctx.strokeRect(cx + 0.5, Math.round(y) + 0.5, Math.round(cw) - 1, Math.round(h) - 1);
    if (fill > 0) { ctx.fillStyle = RED; ctx.fillRect(cx + 2, Math.round(y) + 2, Math.round((cw - 4) * fill), Math.round(h) - 4); }
  }
  ctx.restore();
}

// Day timeline bar in box [x, y, w, h]: one cell per day, `filled` days lit (fractional fills the next cell), tick
// labels under the first and last edge (e.g. '09/20', '10/01') and an optional title above.
export function timelineBar(ctx, days, [x, y, w, h], { filled = 0, from = '', to = '', title = null, size = 14, alpha = 1 } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  const gap = 3, cw = (w - gap * (days - 1)) / days;
  for (let i = 0; i < days; i++) {
    const cx = Math.round(x + i * (cw + gap)), f = clamp(filled - i);
    ctx.fillStyle = 'rgba(236,241,244,0.12)'; ctx.fillRect(cx, Math.round(y), Math.round(cw), Math.round(h));
    if (f > 0) { ctx.fillStyle = RED; ctx.fillRect(cx, Math.round(y), Math.round(cw * f), Math.round(h)); }
  }
  ctx.fillStyle = RULE;
  ctx.fillRect(Math.round(x), Math.round(y + h + 5), 1, 6); ctx.fillRect(Math.round(x + w) - 1, Math.round(y + h + 5), 1, 6);
  font(ctx, F.mono, size, 1.5);
  ctx.fillStyle = DIM;
  if (from) ctx.fillText(from, x, y + h + 12 + size);
  if (to) { ctx.textAlign = 'right'; ctx.fillText(to, x + w, y + h + 12 + size); ctx.textAlign = 'left'; }
  if (title) { ctx.fillStyle = INK; ctx.fillText(title, x, y - 10); }
  ctx.restore();
}
