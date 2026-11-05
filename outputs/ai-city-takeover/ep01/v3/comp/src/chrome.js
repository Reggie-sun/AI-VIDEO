// The editorial chrome (spec a2 剪辑界面层; shots-map `chrome`, resolved to frames in units.json): the author's continuous
// interface over the whole film. It belongs to the edit, not to the story: the surveillance OSD stays in the system units
// (osd.js, inside its OSD_IN frame); this frames every unit. Four thin registration crosses at the corners; top left the
// film tag and the day counter, top right the title with the IRIS clock (each switches on its frame, a plain cut: a flap
// would show made-up digits for a few frames); at the bottom the five fact lines scrolling left between two hairlines
// (motion-kit hud.js drawTicker), 90 px/s (3 px a frame, about ten characters a second). Mono caps in MK Mono SC (Noto Sans
// Mono CJK SC, the bundled mono: the author's IBM Plex Mono 500 is not installed here), 15 px (caps 11 px, the author's
// 11-12 px class), tracked out. Light ink on a dark ground; on a light one (the white lab, the white panel) dark ink with
// a pale pill behind the top rows, the author's light-look treatment (the inverted frames of U053 turn it dark by
// themselves); 40% inside the dim units; no ticker in the no-ticker units. Words only from the map's chrome. Pure
// function of t.
import { font } from '../../../../../../motion-kit/src/draw2d.js';
import { drawTicker, hudRun } from '../../../../../../motion-kit/src/hud.js';
import { F, H, W } from './util.js';

const SIZE = 15, TRACK = 3, GAP = 34, X0 = 72, X1 = W - 72, TOP = 61, TICK_Y = 1058, SPEED = 90, ARM = 7;
const CORNERS = [[24, 24], [W - 24, 24], [24, H - 24], [W - 24, H - 24]];
const INK = { false: ['rgba(236,241,244,0.88)', 'rgba(236,241,244,0.36)'], true: ['rgba(11,15,20,0.86)', 'rgba(11,15,20,0.34)'] };

// a switch list's text at frame f: the last switch at or before it
function switched(list, f) {
  let s = null;
  for (const x of list) if (x.f <= f) s = x;
  return s ? s.text : '';
}
// a pale pill behind a run of top-row text from x0 to x1 (light grounds only)
function pill(o, x0, x1) {
  o.save(); o.fillStyle = 'rgba(240,243,246,0.62)'; o.beginPath();
  o.roundRect(x0 - 10, TOP - 16, x1 - x0 + 20, 22, 11); o.fill(); o.restore();
}
const width = (o, parts) => {
  o.save(); font(o, F.mono, SIZE, TRACK);
  const w = parts.reduce((a, p) => a + o.measureText(p.text).width, 0) + GAP * (parts.length - 1);
  o.restore();
  return w;
};

export function drawChrome(k, t, u, { light = false } = {}) {
  const c = k.data.units.chrome;
  if (!c) return;
  const o = k.layers.overlay.ctx, [ink, rule] = INK[light], f = k.frame;
  o.save();
  o.globalAlpha = u.chromeDim ? 0.4 : 1;
  if (!light) { o.shadowColor = 'rgba(0,0,0,0.55)'; o.shadowBlur = 3; }
  if (c.corners) {
    o.fillStyle = ink;
    for (const [x, y] of CORNERS) { o.fillRect(x - ARM, y, 2 * ARM + 1, 1); o.fillRect(x, y - ARM, 1, 2 * ARM + 1); }
  }
  const left = [c.topLeft, switched(c.counter, f)].filter(Boolean).map(text => ({ text, color: ink }));
  if (left.length) {
    if (light) pill(o, X0, X0 + width(o, left));
    hudRun(o, left, X0, TOP, { size: SIZE, tracking: TRACK, gap: GAP, family: F.mono });
  }
  const right = switched(c.topRight, f);
  if (right) {
    if (light) pill(o, X1 - width(o, [{ text: right }]), X1);
    hudRun(o, [{ text: right, color: ink }], X1, TOP, { size: SIZE, tracking: TRACK, align: 'right', family: F.mono });
  }
  if (u.ticker && c.ticker?.length) {
    drawTicker(o, c.ticker, t, { x0: 0, x1: W, y: TICK_Y, size: SIZE, speed: SPEED, color: ink, rule, ruleGap: 9,
      tracking: TRACK - 1, family: F.mono });
  }
  o.restore();
}
