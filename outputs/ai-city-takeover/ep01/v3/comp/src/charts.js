// Explanatory diagrams in the OSD language (hairlines, mono caps, one accent): the node graph, its control gap and its
// single external endpoint, the red overlay, the cache-timing chart and its flatline, the red line from the door to the
// city and its retraction, the cut channel. Shapes only, no invented numbers; every word is graphic_text's (MODEL → DNS
// RESOLVER → EXTERNAL; CONTROL · DNS RESOLVER · MISCONFIGURED; DNS → EXTERNAL CHATBOT · LIMITED; PROCESSOR CACHE
// TIMING). In the red-team room (U036-U040) the accent is steel, never red.
import { glowPath, roundRect } from '../../../../../../motion-kit/src/draw2d.js';
import { clamp, easeInCubic, easeInOutCubic, easeOutCubic, hash2, lerp } from '../../../../../../motion-kit/src/math.js';
import { ANCHORS } from './anchors.js';
import { tag } from './labels.js';
import { DARK_INK, DIM, F, FAINT, INK, RED, RED_RGB, W, accent, along, arrowParts, beatLen, glow, grow, line, measure, poly,
  scrim, text, tokAt, tokenLine } from './util.js';

// ---- node graph: the parts of graphic_text joined by arrows; part i appears on its first token ----
function partTimes(u) {
  let j = 0;
  return arrowParts(u.text).map(p => {
    const n = p.split(/[\s·]+/).filter(Boolean).length, at = tokAt(u, j);
    j += n;
    return at;
  });
}
// the node boxes [x, y, w, h] of a row of parts centred on the frame at height y (shared, so a later diagram can stand
// on an earlier one's nodes)
function nodeBoxes(ctx, parts, { y = 520, size = 30 } = {}) {
  const n = parts.length, widths = parts.map(s => measure(ctx, s, size, undefined, 3) + 70);
  const gap = Math.max(90, (1640 - widths.reduce((a, b) => a + b, 0)) / Math.max(1, n - 1));
  let x = (W - (widths.reduce((a, b) => a + b, 0) + gap * (n - 1))) / 2;
  return parts.map((s, i) => { const b = [x, y - 46, widths[i], 92]; x += widths[i] + gap; return b; });
}
function nodes(ctx, t, parts, times, { y = 520, red = Infinity, redLink = 1, alpha = 1, frame = 0, accentColor = RED, size = 30 }) {
  const boxes = nodeBoxes(ctx, parts, { y, size });
  ctx.save(); ctx.globalAlpha *= alpha;
  boxes.forEach((b, i) => {
    const a = grow(t, times[i], 0.15), isRed = t >= red && (i === redLink || i === redLink + 1);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = isRed && i === redLink ? accentColor : INK; ctx.lineWidth = 2;
    roundRect(ctx, b[0], b[1], b[2], b[3], 10); ctx.stroke(); ctx.restore();
    text(ctx, parts[i], b[0] + b[2] / 2, y + 10, { size, align: 'center', tracking: 3, alpha: a, color: isRed && i === redLink ? accentColor : INK });
    if (i === 0) return;
    const p = boxes[i - 1], l = easeOutCubic(clamp((t - times[i] + 0.05) / 0.35));
    const x0 = p[0] + p[2] + 8, x1 = lerp(x0, b[0] - 16, l), hot = t >= red && i === redLink + 1;
    const j = hot ? (hash2(frame, 9) - 0.5) * 5 : 0;
    line(ctx, [x0, y + j], [x1, y - j], { color: hot ? accentColor : INK, width: hot ? 4 : 2, alpha: Math.max(a, 0.6) });
    if (l >= 1) poly(ctx, [[b[0] - 30, y - 12], [b[0] - 14, y], [b[0] - 30, y + 12]], { color: hot ? accentColor : INK, width: hot ? 4 : 2 });
  });
  ctx.restore();
}
// the words of the nearest earlier node graph (a diagram that stands on it: the overlay, the control gap)
const earlierGraph = (k, u) => [...k.data.units.units].slice(0, u.i).reverse().find(x => x.graphics.includes('nodegraph_resolver'))?.text || '';
// the node graph's words for a unit that overlays it with no words of its own
const graphText = (k, u) => u.text || earlierGraph(k, u);
// a node box: outline and its words (or none), stroke colour and alpha
function nodeBox(ctx, b, s, { color = INK, alpha = 1, size = 30, width = 2 } = {}) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
  roundRect(ctx, b[0], b[1], b[2], b[3], 10); ctx.stroke(); ctx.restore();
  if (s) text(ctx, s, b[0] + b[2] / 2, b[1] + b[3] / 2 + size * 0.36, { size, align: 'center', tracking: 3, alpha, color });
}
// an arrow head pointing right at (x, y)
const head = (ctx, x, y, color, width) => poly(ctx, [[x - 16, y - 12], [x, y], [x - 16, y + 12]], { color, width });
// the broken ends of a boundary line at a gap: two short jagged strokes
function crack(ctx, x, y, dir, alpha, color) {
  poly(ctx, [[x - 9, y], [x + 5, y + dir * 7], [x - 3, y + dir * 13]], { color, width: 2, alpha });
}

// ---- cache timing: two lanes of pulses on the beats; lane B lags, then comes into step ----
function lanes(k, ctx, t, u, { t0, t1, flat = Infinity, title = null }) {
  const x0 = 260, x1 = 1660, ys = [430, 650], amp = 64, bl = beatLen(k, t), speed = 520, acc = accent(u);
  // the title in mono bold 44 px (caps 32 px: a2 asks >= 28 px for PROCESSOR CACHE in the red-team test)
  if (title) tokenLine(ctx, title, u.toks, 0, t, x0, 286, { size: 44, family: F.monoB, tracking: 4 });
  const lag = lerp(0.42, 0, easeInOutCubic(clamp((t - t0) / (t1 - t0)))) * bl;
  ys.forEach((y, li) => {
    line(ctx, [x0, y], [x1, y], { color: FAINT, width: 1 });
    const pts = [[x0, y]];
    for (const b of k.clock.beats.filter(x => x >= t0 - 4 && x <= Math.min(t, flat))) {
      const tb = b + (li ? lag : 0), x = x1 - (t - tb) * speed, w = bl * 0.28 * speed;
      if (x + w < x0 || x > x1) continue;
      pts.push([Math.max(x0, x), y], [Math.max(x0, x), y - amp], [Math.min(x1, x + w), y - amp], [Math.min(x1, x + w), y]);
    }
    pts.push([x1, y]);
    pts.sort((a, b) => a[0] - b[0]);
    poly(ctx, pts, { color: li ? acc : INK, width: 2.5 });
  });
  for (const b of k.clock.beats.filter(x => x >= t0 - 4 && x <= Math.min(t, flat))) {   // the crossing through the cache
    const x = x1 - (t - b) * speed;
    if (x < x0 || x > x1) continue;
    line(ctx, [x, ys[0]], [x + lag * speed, ys[1] - amp], { color: acc, width: 1.5, dash: [4, 5], alpha: 0.75 });
  }
}

export const CHARTS = {
  nodegraph_resolver(k, t, u) {
    const parts = arrowParts(u.text);
    nodes(k.layers.overlay.ctx, t, parts, partTimes(u), { frame: k.frame, accentColor: accent(u) });
    return {};
  },
  // U013 (a2): the graph of the unit before stays where it was; a CONTROL boundary draws itself round MODEL and the
  // resolver, cutting the way out (the link to EXTERNAL stops at it, dashed). On the cue (the word misconfigured) the
  // resolver turns red with MISCONFIGURED under it, the boundary cracks open where the link meets it, and the link runs
  // red through the gap to EXTERNAL. A configuration gap, not a cable: no hardware drawn.
  nodegraph_control_gap(k, t, u) {
    const o = k.layers.overlay.ctx, e = k.layers.emit.ctx, parts = arrowParts(earlierGraph(k, u)), words = u.text.split(' · ');
    const [label, resolver, flag] = [words[0] || '', words[1] || parts[1] || '', words[2] || ''];
    const boxes = nodeBoxes(o, parts), y = 520, acc = accent(u), tC = u.cue;
    if (boxes.length < 3) return {};
    const [m, r, x] = boxes, xb = r[0] + r[2] + 0.45 * (x[0] - r[0] - r[2]), left = m[0] - 50, top = y - 160, bot = y + 160;
    const on = t >= tC, g = on ? 46 * easeOutCubic(clamp((t - tC) / 0.18)) : 0;
    // the boundary, drawn on from the crossing point round to it again
    const path = [[xb, y - g], [xb, top], [left, top], [left, bot], [xb, bot], [xb, y + g]];
    poly(o, along(path, easeInOutCubic(clamp((t - k.t0) / 0.35))), { color: INK, width: 2 });
    if (g > 0) { crack(o, xb, y - g, -1, 1, acc); crack(o, xb, y + g, 1, 1, acc); }
    text(o, label, left + 22, top - 18, { size: 24, tracking: 6, color: INK, alpha: grow(t, k.t0 + 0.1, 0.2) });
    // the nodes: MODEL and its link inside, the resolver (red from the cue), EXTERNAL dim until the line reaches it
    nodeBox(o, m, parts[0]);
    line(o, [m[0] + m[2] + 8, y], [r[0] - 16, y], { color: INK, width: 2 }); head(o, r[0] - 14, y, INK, 2);
    nodeBox(o, r, resolver, { color: on ? acc : INK });
    const reach = easeInOutCubic(clamp((t - tC - 0.08) / 0.3)), x0 = r[0] + r[2] + 8, x1 = x[0] - 16;
    nodeBox(o, x, parts[2], { color: reach >= 1 ? INK : FAINT });
    if (!on || reach <= 0) line(o, [x0, y], [xb - 10, y], { color: DIM, width: 2, dash: [8, 7] });
    if (on && reach > 0) {
      const xe = lerp(x0, x1, reach);
      glowPath(e, [[x0, y], [xe, y]], { color: RED_RGB, core: 2, halo: 10, alpha: 0.8 });
      line(o, [x0, y], [xe, y], { color: acc, width: 4 });
      if (reach >= 1) head(o, x1 + 2, y, acc, 4);
    }
    if (on) text(o, flag, r[0] + r[2] / 2, r[1] + r[3] + 50, { size: 26, align: 'center', tracking: 5, color: acc,
      alpha: grow(t, tC, 0.1) });
    return { emitGain: 2.0 };
  },
  // U017 (a2): past the gap the line reaches one node only. The cracked boundary edge with DNS inside on the left; on
  // the right a field of grey, unnamed nodes; the red line runs from DNS through the gap to the one node that lights,
  // EXTERNAL CHATBOT, and LIMITED stands small over the line. No city, no other path.
  nodegraph_single_endpoint(k, t, u) {
    const o = k.layers.overlay.ctx, e = k.layers.emit.ctx, acc = accent(u), y = 520;
    const [from = '', rest = ''] = arrowParts(u.text), [target = '', note = ''] = rest.split(' · ');
    const xb = 400, size = 30;
    // the boundary's broken edge (from U013), DNS inside it
    line(o, [xb, 300], [xb, y - 46], { color: INK, width: 2 }); line(o, [xb, y + 46], [xb, 740], { color: INK, width: 2 });
    crack(o, xb, y - 46, -1, 1, acc); crack(o, xb, y + 46, 1, 1, acc);
    const dw = measure(o, from, size, undefined, 3) + 70, dns = [xb - 90 - dw, y - 46, dw, 92];
    nodeBox(o, dns, from, { color: acc });
    // the grey field: a jittered grid, the line's corridor and the target's place left open
    const tw = measure(o, target, size, undefined, 3) + 70, tb = [1230, y - 46, tw, 92];
    const a = grow(t, k.t0, 0.25);
    [[700, 300], [1010, 300], [1320, 300], [1640, 300], [1700, 520], [700, 740], [1010, 740], [1320, 740], [1640, 740]].forEach(([cx, cy], i) => {
      const bx = cx + (hash2(i, 171) - 0.5) * 60, by = cy + (hash2(i, 172) - 0.5) * 50, b = [bx - 85, by - 30, 170, 60];
      nodeBox(o, b, '', { color: FAINT, alpha: a * grow(t, k.t0 + 0.03 * i, 0.15) });
      line(o, [b[0] + 22, by - 6], [b[0] + 22 + 70 + 40 * hash2(i, 173), by - 6], { color: FAINT, width: 4, alpha: a * 0.6 });
      line(o, [b[0] + 22, by + 10], [b[0] + 22 + 50 + 30 * hash2(i, 174), by + 10], { color: FAINT, width: 4, alpha: a * 0.4 });
    });
    // the line: from DNS through the gap to the target, arriving on the word internet's end
    const tA = k.t0 + 0.8, p = easeInOutCubic(clamp((t - k.t0 - 0.1) / (tA - k.t0 - 0.1))), x0 = dns[0] + dns[2] + 8, x1 = tb[0] - 16;
    if (p > 0) {
      const xe = lerp(x0, x1, p);
      glowPath(e, [[x0, y], [xe, y]], { color: RED_RGB, core: 2, halo: 10, alpha: 0.8 });
      line(o, [x0, y], [xe, y], { color: acc, width: 3 });
      if (p >= 1) head(o, x1 + 2, y, acc, 3);
    }
    const lit = t >= tA;
    nodeBox(o, tb, target, { color: lit ? INK : FAINT, width: lit ? 2.5 : 2 });
    if (lit) {
      const ring = clamp((t - tA) / 0.5);
      o.save(); o.globalAlpha = 0.6 * (1 - ring); o.strokeStyle = INK; o.lineWidth = 1.5;
      roundRect(o, tb[0] - 14 * ring, tb[1] - 14 * ring, tb[2] + 28 * ring, tb[3] + 28 * ring, 12); o.stroke(); o.restore();
    }
    text(o, note, (xb + x1) / 2, y - 26, { size: 22, align: 'center', tracking: 8, color: INK, alpha: grow(t, tA + 0.3, 0.15) });
    return { emitGain: 2.0 };
  },
  // the graph over the patch panel, half transparent; on the cue the resolver and its outgoing link turn red, and the
  // miswired port's light jumps from blue to red
  nodegraph_red_overlay(k, t, u, cm) {
    const f = k.layers.feed.ctx, parts = arrowParts(graphText(k, u)), tR = u.cue;
    scrim(f, 120, 160, 1680, 300, 0.5);
    f.save(); f.translate(W / 2, 300); f.scale(0.8, 0.8); f.translate(-W / 2, -300);
    nodes(f, t, parts, parts.map(() => -1), { y: 300, red: tR, redLink: Math.min(1, parts.length - 1), alpha: 0.85, frame: k.frame, accentColor: accent(u) });
    f.restore();
    const led = ANCHORS[cm.key]?.led;
    if (led) {
      const p = cm.out(led);
      if (t < tR) { glow(f, p, 30, { color: [70, 150, 255], alpha: 1 }); glow(f, p, 10, { color: [200, 230, 255], alpha: 1 }); }
      else glow(k.layers.emit.ctx, p, 40, { alpha: 0.9 * grow(t, tR, 0.05) });
    }
    return { emitGain: 2.0, grade: t < tR ? { uRedKeep: 0 } : {} };
  },
  timing_chart(k, t, u) {
    lanes(k, k.layers.overlay.ctx, t, u, { t0: u.cue, t1: k.t1 - 0.4, title: u.text || null });
    return {};
  },
  // the two waveforms keep pulsing in step, then both drop to a flat line on the cue
  timing_chart_flatline(k, t, u) {
    lanes(k, k.layers.overlay.ctx, t, u, { t0: k.t0 - 4, t1: k.t0 - 3, flat: u.cue });
    return {};
  },
  // a thin red line from the door (left edge) along one road to one point in the city; DNS at the start, the other
  // words of graphic_text at the end once the line arrives
  redline_door_to_city(k, t, u, cm) {
    const a = ANCHORS[cm.key] || {}, tR = u.cue, tN = u.cue + 0.55 * (k.t1 - u.cue), f = k.layers.feed.ctx, e = k.layers.emit.ctx;
    const road = a.highway;
    if (!road || t < tR) return {};
    const [first, ...rest] = arrowParts(u.text);
    const p = easeInOutCubic(clamp((t - tR) / (tN - tR))), pts = along(road, p).map(q => cm.out(q));
    glowPath(e, pts, { color: RED_RGB, core: 2.5, halo: 12, alpha: 1 });
    poly(f, pts, { color: RED, width: 2 });
    const o = k.layers.overlay.ctx, s0 = cm.out(road[0]);
    if (first) tag(o, first, Math.max(80, s0[0] + 60), s0[1] - 130, { size: 22, alpha: grow(t, tR, 0.12) });
    if (t >= tN) {
      const q = pts[pts.length - 1], m = grow(t, tN, 0.3);
      f.save(); f.globalAlpha = m; f.strokeStyle = RED; f.lineWidth = 1.5;
      f.beginPath(); f.arc(q[0], q[1], 14 + 8 * Math.sin((t - tN) * 9) ** 2, 0, Math.PI * 2); f.stroke(); f.restore();
      glow(e, q, 30, { alpha: m });
      if (rest.length) tag(o, rest.join(' '), Math.min(q[0] + 40, W - 420), q[1] - 110, { size: 22, alpha: m });
    }
    return { emitGain: 2.2 };
  },
  // that red line, from the door gap down the corridor floor out of frame: on the cue it snaps and both halves retract
  redline_retract(k, t, u, cm) {
    const a = ANCHORS[cm.key] || {}, sz = k.size[cm.key], e = k.layers.emit.ctx, f = k.layers.feed.ctx;
    const gx = u.target ? u.target[0] * sz[0] : (a.floor?.[0] ?? sz[0] / 2), gy = a.floor?.[1] ?? (u.target ? u.target[1] * sz[1] + 120 : sz[1] * 0.6);
    const A = cm.out([gx, gy]), B = cm.out([gx, sz[1] + 30]), brk = 0.55;
    const r = easeInCubic(clamp((t - u.cue) / 0.5));
    const segs = t < u.cue ? [[0, 1]] : [[0, brk * (1 - r)], [brk + (1 - brk) * r, 1]];
    for (const [s0, s1] of segs) {
      if (s1 - s0 < 0.003) continue;
      const P = [lerp(A[0], B[0], s0), lerp(A[1], B[1], s0)], Q = [lerp(A[0], B[0], s1), lerp(A[1], B[1], s1)];
      glowPath(e, [P, Q], { color: RED_RGB, core: 2.5, halo: 12, alpha: 1 }); glowPath(e, [Q, P], { color: RED_RGB, core: 2.5, halo: 12, alpha: 1 });
      line(f, P, Q, { color: RED, width: 2 });
    }
    if (t >= u.cue && t < u.cue + 0.12) glow(e, [lerp(A[0], B[0], brk), lerp(A[1], B[1], brk)], 40, { alpha: 1 - (t - u.cue) / 0.12 });
    return { emitGain: 2.2 };
  },
  // the channel between the two terminals: a pulse crosses it on the eighths; on the cue it is cut at the shared wall
  line_cut(k, t, u, cm) {
    const a = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, tP = u.cue;
    const sc = a.screens || a.terminals;
    if (!sc) return {};
    const [l, r] = sc.slice(0, 2).map(b => cm.out([b[0] + b[2] / 2, b[1] + b[3] / 2]));
    const ink = u.nored ? '#2B4257' : RED;
    const fade = 1 - easeOutCubic(clamp((t - tP - 0.05) / 0.4)), gap = t < tP ? 0 : easeOutCubic(clamp((t - tP) / 0.12)) * 60;
    const mid = [a.wall ? cm.out([a.wall, 0])[0] : (l[0] + r[0]) / 2, (l[1] + r[1]) / 2];
    if (fade > 0) {
      line(f, l, [mid[0] - gap, mid[1]], { color: ink, width: 3, alpha: fade }); line(f, [mid[0] + gap, mid[1]], r, { color: ink, width: 3, alpha: fade });
      const ph = ((t - k.t0) / (beatLen(k, t) / 2)) % 1, dot = [lerp(l[0], r[0], ph), lerp(l[1], r[1], ph)];
      if (t < tP) { f.save(); f.fillStyle = ink; f.beginPath(); f.arc(dot[0], dot[1], 7, 0, Math.PI * 2); f.fill(); f.restore(); }
    }
    if (t >= tP) {                                                     // the cut ends, two short ticks at the wall
      const al = 1 - clamp((t - tP - 0.6) / 0.6);
      line(f, [mid[0] - gap, mid[1] - 18], [mid[0] - gap, mid[1] + 18], { color: DARK_INK, width: 3, alpha: al });
      line(f, [mid[0] + gap, mid[1] - 18], [mid[0] + gap, mid[1] + 18], { color: DARK_INK, width: 3, alpha: al });
    }
    return {};
  },
};
