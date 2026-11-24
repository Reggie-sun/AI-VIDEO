// The board's explaining graphics and the through-line chrome, as generic drawing functions (each a pure function of
// the frame). Positions are output pixels; the shot code places them on the thing in frame.
import { clamp, easeOutCubic, hash2 } from '../../../../../../motion-kit/src/math.js';
import { FONT, INK, micro, setFont, since, shown, typed } from './type.js';

const W = 1920, H = 1080;
const FLAP = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-';

// a field that flaps from its previous text to its new one on ticks (12 a second), never two changes in a row of frames
export function flap(prev, next, a, f) {
  if (a < 0) return prev;
  const ticks = Math.floor(a / 2);
  const n = Math.max(prev.length, next.length);
  let out = '';
  for (let i = 0; i < n; i++) {
    const ch = next[i] || ' ';
    const settle = 1 + (i % 4);
    if (ticks >= settle || ch === ' ' || ch === (prev[i] || ' ')) out += ch;
    else out += FLAP[Math.floor(hash2(i * 31 + ticks, f >> 1) * FLAP.length)];
  }
  return out.replace(/\s+$/, '');
}

export function hairline(ctx, x0, y0, x1, y1, color = 'rgba(236,232,222,0.8)', w = 1) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); ctx.restore();
}

// leader line drawn from a to b over `dur` frames after it starts
export function leader(ctx, a, b, age, { dur = 4, color = 'rgba(236,232,222,0.85)', dot = true } = {}) {
  if (age < 0) return;
  const e = easeOutCubic(clamp((age + 1) / dur));
  ctx.save();
  ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e); ctx.stroke();
  if (dot) { ctx.beginPath(); ctx.arc(a[0], a[1], 3, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}

// detector corner brackets round a box
export function brackets(ctx, x0, y0, x1, y1, age, { color = 'rgba(236,232,222,0.9)', arm = 14, w = 1.5 } = {}) {
  if (age < 0) return;
  const g = age < 2 ? 1.06 - 0.03 * age : 1;
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  const hx = (x1 - x0) / 2 * g, hy = (y1 - y0) / 2 * g;
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w;
  for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
    const x = cx + sx * hx, y = cy + sy * hy;
    ctx.beginPath(); ctx.moveTo(x - sx * arm, y); ctx.lineTo(x, y); ctx.lineTo(x, y - sy * arm); ctx.stroke();
  }
  ctx.restore();
}

// small pager glyph (body, LCD window, button), no digits
export function pagerIcon(ctx, x, y, s = 1, { body = 'rgba(236,232,222,0.92)', lcd = 'rgba(20,22,24,0.9)' } = {}) {
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = body; ctx.beginPath(); ctx.roundRect(0, 0, 22, 14, 2.5); ctx.fill();
  ctx.fillStyle = lcd; ctx.fillRect(3, 3, 12, 6);
  ctx.fillRect(17, 4, 2.5, 6);
  ctx.restore();
}

// ---------------------------------------------------------------- chrome: the P0 ticket card (top left)
// state from the song time; board chrome: INC-0804 BILLBOARD BEHIND A TREE -> INC-0902 BUS STOP -> FREEWAY -> card
// turns white at 39.897 -> ALL HANDS, SEV-MED -> SEV-HIGH -> stamped ALL HANDS 53.767; pager icons under it (two from
// s006, one more on every snare of s012, no digits)
const TICKET = [
  { at: 0, id: 'INC-0804', sev: 'SEV-MED', title: 'BILLBOARD BEHIND A TREE', status: 'PAGED' },
  { at: 32.934, id: 'INC-0902', sev: 'SEV-MED', title: 'BUS STOP', status: 'PAGED' },
  { at: 36.1999, id: 'INC-0902', sev: 'SEV-MED', title: 'FREEWAY', status: 'PAGED' },
  { at: 40.7859, id: 'ALL HANDS', sev: 'SEV-MED', title: 'RUNWAY ONE', status: 'PAGED' },
  { at: 42.769, id: 'ALL HANDS', sev: 'SEV-HIGH', title: 'RUNWAY ONE', status: 'PAGED' },
];
export function ticketCard(k, ctx, { accent = INK.amber, alpha = 1, narrow = false, icons = true } = {}) {
  const s = k.s;
  let i = 0;
  for (let j = 0; j < TICKET.length; j++) if (shown(k, TICKET[j].at) || TICKET[j].at === 0) i = j;
  const cur = TICKET[i], prev = TICKET[Math.max(0, i - 1)];
  const a = i === 0 ? 99 : since(k, cur.at);
  const white = shown(k, 39.897);
  const wa = since(k, 39.897);
  const x = 60, y = 56, w = narrow ? 268 : 382, h = narrow ? 82 : 104;
  ctx.save();
  ctx.globalAlpha = alpha;
  const paper = white ? INK.paper : 'rgba(12,14,16,0.74)';
  const ink = white ? INK.dark : 'rgba(240,236,228,0.95)';
  const sub = white ? 'rgba(23,25,28,0.62)' : 'rgba(240,236,228,0.6)';
  // the white turn wipes down the card over 3 frames
  ctx.fillStyle = 'rgba(12,14,16,0.74)';
  ctx.fillRect(x, y, w, h);
  if (white) { ctx.fillStyle = paper; ctx.fillRect(x, y, w, h * clamp((wa + 1) / 3)); }
  ctx.strokeStyle = white ? 'rgba(23,25,28,0.5)' : accent; ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  ctx.fillStyle = white ? INK.dark : accent; ctx.fillRect(x, y, 5, h);
  const id = flap(prev.id, cur.id, a, k.f), sev = flap(prev.sev, cur.sev, a, k.f), title = flap(prev.title, cur.title, a, k.f);
  setFont(ctx, FONT.monoS, 19, 1.5); ctx.fillStyle = ink; ctx.fillText(id, x + 20, y + 30);
  // severity pill, SHOW SCALE micro under it
  setFont(ctx, FONT.monoS, 13, 1.6);
  const sw = ctx.measureText(sev).width + 18;
  ctx.strokeStyle = ink; ctx.strokeRect(x + w - 16 - sw + 0.5, y + 13.5, sw, 22);
  ctx.fillText(sev, x + w - 16 - sw + 9, y + 29);
  micro(ctx, 'SHOW SCALE', x + w - 16, y + 50, { size: 9, track: 1.8, color: sub, align: 'right' });
  setFont(ctx, FONT.mono, narrow ? 12 : 15, 1.2); ctx.fillStyle = ink; ctx.fillText(title, x + 20, y + (narrow ? 54 : 60));
  micro(ctx, `STATUS · ${cur.status}`, x + 20, y + (narrow ? 72 : 88), { size: narrow ? 10 : 12, track: 2, color: sub });
  ctx.restore();
  // pager icons under the card
  const n = !icons ? 0 : 2 + k.snaresBetween(44.9422, Math.min(s, 50.933));
  for (let j = 0; j < n; j++) {
    const born = j < 2 ? -99 : k.snareTimes(44.9422, 50.933)[j - 2];
    const ag = born < 0 ? 99 : since(k, born);
    const sc = ag < 2 ? 1.25 - 0.12 * ag : 1;
    pagerIcon(ctx, x + (j % 14) * 27, y + h + 12 + Math.floor(j / 14) * 20, sc * 0.9);
  }
  // the ALL HANDS stamp (s013 board chrome: the card stamped ALL HANDS) at 53.767
  const st = since(k, 53.767);
  if (st >= 0) {
    const sc = st >= 3 ? 1 : [1.45, 1.12, 1.03][st];
    ctx.save();
    ctx.translate(x + w * 0.62, y + h * 0.58); ctx.rotate(-0.13); ctx.scale(sc, sc);
    ctx.globalAlpha = st < 1 ? 0.7 : 0.92;
    ctx.strokeStyle = INK.dark; ctx.lineWidth = 3;
    ctx.strokeRect(-104, -26, 208, 52); ctx.lineWidth = 1; ctx.strokeRect(-98, -20, 196, 40);
    setFont(ctx, FONT.din, 40, 1); ctx.fillStyle = INK.dark; ctx.textAlign = 'center'; ctx.fillText('ALL HANDS', 0, 14);
    // ink wear (fixed, from hash)
    ctx.globalCompositeOperation = 'destination-out';
    for (let q = 0; q < 70; q++) {
      ctx.globalAlpha = 0.5 * hash2(q, 7);
      ctx.fillRect(-104 + hash2(q, 3) * 208, -26 + hash2(q, 5) * 52, 1 + hash2(q, 9) * 4, 1 + hash2(q, 11) * 2);
    }
    ctx.restore();
  }
}

// ---------------------------------------------------------------- chrome: corners, chapter flap, bottom micro row
const CHAPTERS = [{ at: 0, text: '02 STREET LOOKS' }, { at: 40.7859, text: '03 RUNWAY ONE · ALL HANDS' }];
export function frameChrome(k, ctx) {
  ctx.save();
  ctx.fillStyle = 'rgba(236,232,222,0.7)';
  for (const [x, y] of [[28, 28], [W - 28, 28], [28, H - 28], [W - 28, H - 28]]) {
    ctx.fillRect(x - 7, y, 15, 1); ctx.fillRect(x, y - 7, 1, 15);
  }
  // chapter flap, top right: one dark tile per character
  let i = 0;
  for (let j = 0; j < CHAPTERS.length; j++) if (shown(k, CHAPTERS[j].at) || j === 0) i = j;
  const a = i === 0 ? 99 : since(k, CHAPTERS[i].at);
  const txt = flap(CHAPTERS[Math.max(0, i - 1)].text, CHAPTERS[i].text, a, k.f);
  setFont(ctx, FONT.monoS, 15, 0);
  const cw = 15, gap = 2, x1 = W - 60, y = 54;
  const n = txt.length;
  for (let c = 0; c < n; c++) {
    const xx = x1 - (n - c) * (cw + gap);
    const ch = txt[c];
    if (ch === ' ') continue;
    ctx.fillStyle = 'rgba(14,16,18,0.78)'; ctx.fillRect(xx, y, cw, 23);
    ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(xx, y + 11, cw, 1);
    ctx.fillStyle = 'rgba(240,236,228,0.95)'; ctx.textAlign = 'center'; ctx.fillText(ch, xx + cw / 2, y + 17);
  }
  ctx.textAlign = 'left';
  micro(ctx, 'IRIS · EP01 · ALL HANDS', x1, y - 10, { size: 10, track: 2.4, align: 'right', color: 'rgba(236,232,222,0.62)' });
  // bottom: song clock and the show, right; a hairline
  const sec = k.s;
  const mm = String(Math.floor(sec / 60)).padStart(2, '0'), ss = (sec % 60).toFixed(2).padStart(5, '0');
  hairline(ctx, W - 470, H - 50.5, W - 60, H - 50.5, 'rgba(236,232,222,0.35)');
  micro(ctx, `INCIDENT WEEK · SONG ${mm}:${ss} · BAR ${k.barNo()}`, W - 60, H - 34, { size: 11, track: 2.2, align: 'right',
    color: 'rgba(236,232,222,0.7)' });
  ctx.restore();
}

// ---------------------------------------------------------------- a garment-tag label (s007)
export function tagLabel(ctx, x, y, age, { tag, sub, source, rot = -0.06 }) {
  if (age < 0) return;
  const e = easeOutCubic(clamp((age + 1) / 4));
  ctx.save();
  ctx.translate(x, y); ctx.rotate(rot * e); ctx.translate(0, (1 - e) * -14);
  ctx.globalAlpha = clamp(0.3 + e);
  ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 6;
  ctx.fillStyle = INK.paper; ctx.beginPath(); ctx.roundRect(0, 0, 300, 150, 3); ctx.fill();
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = 'rgba(23,25,28,0.85)'; ctx.beginPath(); ctx.arc(150, 13, 4.5, 0, Math.PI * 2); ctx.fill();
  setFont(ctx, FONT.monoS, 29, 0); ctx.fillStyle = INK.dark; ctx.fillText(typed(tag, age, 3), 18, 62);
  micro(ctx, typed(sub, age - 4, 4), 18, 90, { size: 12, track: 1.6, color: INK.dark });
  // barcode strip (fixed, from hash) and the source
  ctx.fillStyle = INK.dark;
  let bx = 18;
  for (let q = 0; q < 46 && bx < 200; q++) { const bw = 1 + Math.floor(hash2(q, 41) * 3); if (hash2(q, 43) > 0.38) ctx.fillRect(bx, 104, bw, 22); bx += bw + 1; }
  micro(ctx, source, 18, 141, { size: 9, track: 1.2, color: 'rgba(23,25,28,0.75)' });
  ctx.fillStyle = INK.amber; ctx.fillRect(282, 104, 6, 22);
  ctx.restore();
}

// ---------------------------------------------------------------- a classifier panel: rows type one per tick
export function classifier(k, ctx, x, y, rows, { title, source, width = 420, accent = INK.amber, dark = true } = {}) {
  const shownRows = rows.filter(r => shown(k, r.at));
  if (!shownRows.length) return;
  const a0 = since(k, rows[0].at);
  const e = easeOutCubic(clamp((a0 + 1) / 3));
  const rh = 30, h = 46 + rows.length * rh + (source ? 22 : 0);
  ctx.save();
  ctx.globalAlpha = e;
  ctx.fillStyle = dark ? 'rgba(10,12,14,0.62)' : 'rgba(236,232,222,0.88)';
  ctx.fillRect(x, y, width, h * e);
  ctx.strokeStyle = 'rgba(236,232,222,0.55)'; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, y + 0.5, width - 1, h * e - 1);
  micro(ctx, title, x + 14, y + 22, { size: 11, track: 2.4, color: 'rgba(236,232,222,0.7)' });
  hairline(ctx, x + 14, y + 32.5, x + width - 14, y + 32.5, 'rgba(236,232,222,0.3)');
  rows.forEach((r, i) => {
    const a = since(k, r.at);
    if (a < 0) return;
    const yy = y + 58 + i * rh;
    setFont(ctx, FONT.mono, 16, 1.2);
    ctx.fillStyle = 'rgba(240,236,228,0.95)';
    ctx.fillText(typed(r.k, a, 4), x + 14, yy);
    const v = a >= 2 ? r.v : '';
    setFont(ctx, FONT.monoS, 16, 1.4);
    ctx.fillStyle = r.hot ? accent : 'rgba(240,236,228,0.95)';
    ctx.textAlign = 'right'; ctx.fillText(v, x + width - 14, yy); ctx.textAlign = 'left';
    if (r.lyric) for (const [li, wi] of r.lyric) k.mark(li, wi);
  });
  if (source) micro(ctx, source, x + 14, y + h - 10, { size: 9, track: 1.2, color: 'rgba(236,232,222,0.6)' });
  ctx.restore();
}

// ---------------------------------------------------------------- hypnogram (s012): SLEEP · LAST NIGHT
export function hypnogram(k, ctx, x, y, { t0, drop, w = 360, h = 150 }) {
  const a0 = since(k, t0);
  if (a0 < 0) return;
  const e = easeOutCubic(clamp((a0 + 1) / 3));
  ctx.save();
  ctx.globalAlpha = e;
  ctx.fillStyle = 'rgba(10,12,14,0.62)'; ctx.fillRect(x, y, w, h + 50);
  ctx.strokeStyle = 'rgba(236,232,222,0.5)'; ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h + 49);
  micro(ctx, 'SLEEP · LAST NIGHT', x + 14, y + 22, { size: 12, track: 2.4, color: 'rgba(240,236,228,0.92)' });
  micro(ctx, 'ILLUSTRATIVE CURVE', x + w - 14, y + 22, { size: 9, track: 1.6, align: 'right', color: 'rgba(236,232,222,0.55)' });
  const stages = ['AWAKE', 'REM', 'LIGHT', 'DEEP'];
  const gx = x + 74, gw = w - 92, gy = y + 44, gh = h - 20;
  stages.forEach((s, i) => {
    const yy = gy + i * gh / 3;
    micro(ctx, s, x + 14, yy + 4, { size: 9, track: 1.2, color: s === 'AWAKE' ? INK.bone : 'rgba(236,232,222,0.55)' });
    hairline(ctx, gx, yy + 0.5, gx + gw, yy + 0.5, 'rgba(236,232,222,0.14)');
  });
  // a night of stages (fixed), drawn left to right one step per sixteenth; on `drop` it climbs to AWAKE and stays
  const seq = [2, 3, 3, 2, 1, 2, 3, 3, 2, 2, 1, 2, 3, 2, 1, 1, 2];
  const n = Math.min(seq.length, Math.floor(a0 / 3) + 1);
  const dropped = shown(k, drop);
  ctx.strokeStyle = 'rgba(240,236,228,0.95)'; ctx.lineWidth = 2;
  ctx.beginPath();
  const step = gw / (seq.length + 2);
  for (let i = 0; i < n; i++) {
    const xx = gx + i * step, yy = gy + seq[i] * gh / 3;
    if (i === 0) ctx.moveTo(xx, yy); else ctx.lineTo(xx, yy);
    ctx.lineTo(xx + step, yy);
  }
  ctx.stroke();
  if (dropped) {
    const da = since(k, drop);
    const lastX = gx + n * step, lastY = gy + seq[n - 1] * gh / 3;
    const ey = lastY + (gy - lastY) * easeOutCubic(clamp((da + 1) / 2));
    ctx.strokeStyle = INK.bone; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(lastX, ey); ctx.lineTo(gx + gw, ey); ctx.stroke();
    if (da >= 1) {
      setFont(ctx, FONT.din, 44, 0.5); ctx.fillStyle = INK.warm; ctx.textAlign = 'right';
      ctx.fillText('AWAKE', x + w - 14, y + h + 38);
      ctx.textAlign = 'left';
    }
  }
  ctx.restore();
}

// ---------------------------------------------------------------- a semicircle gauge painted on the pillar (s011)
export function gauge(k, ctx, cx, cy, r, { at, full, label, from, to, fill }) {
  const a = since(k, at);
  if (a < 0) return;
  const e = easeOutCubic(clamp((a + 1) / 3));
  // fill steps on sixteenths from `at` to `full`
  const p = clamp(k.sixteenthsBetween(at, Math.min(k.s, full)) / Math.max(1, k.sixteenthsBetween(at, full)));
  ctx.save();
  ctx.globalAlpha = e;
  ctx.lineCap = 'butt';
  ctx.strokeStyle = 'rgba(236,232,222,0.35)'; ctx.lineWidth = r * 0.16;
  ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, 2 * Math.PI); ctx.stroke();
  ctx.strokeStyle = INK.warm;
  ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, Math.PI + Math.PI * p); ctx.stroke();
  for (let i = 0; i <= 8; i++) {
    const t = Math.PI + Math.PI * i / 8;
    hairline(ctx, cx + Math.cos(t) * r * 1.12, cy + Math.sin(t) * r * 1.12, cx + Math.cos(t) * r * 1.22, cy + Math.sin(t) * r * 1.22,
      'rgba(236,232,222,0.7)', 1.2);
  }
  const nt = Math.PI + Math.PI * p;
  ctx.strokeStyle = INK.warm; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(nt) * r * 0.86, cy + Math.sin(nt) * r * 0.86); ctx.stroke();
  micro(ctx, from, cx - r * 1.2, cy + 22, { size: 12, track: 2, color: 'rgba(240,236,228,0.85)', align: 'center' });
  micro(ctx, to, cx + r * 1.2, cy + 22, { size: 12, track: 2, color: 'rgba(240,236,228,0.85)', align: 'center' });
  micro(ctx, label, cx, cy - r * 0.42, { size: 13, track: 2.6, color: 'rgba(240,236,228,0.95)', align: 'center', fam: FONT.monoS });
  if (p >= 1) {
    setFont(ctx, FONT.din, r * 0.42, 0.5); ctx.fillStyle = INK.warm; ctx.textAlign = 'center';
    ctx.fillText(fill, cx, cy + r * 0.62);
  }
  ctx.restore();
}

// ---------------------------------------------------------------- an incoming call (s013)
export function callScreen(k, ctx, x, y, { at, takeAt, flashAt, caller, label, decline }) {
  const a = since(k, at);
  if (a < 0) return;
  const e = easeOutCubic(clamp((a + 1) / 4));
  const w = 300, h = 520;
  ctx.save();
  ctx.translate(x, y + (1 - e) * 24); ctx.rotate(-0.05);
  ctx.globalAlpha = e;
  ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 30; ctx.shadowOffsetY = 10;
  ctx.fillStyle = 'rgba(16,18,21,0.9)'; ctx.beginPath(); ctx.roundRect(0, 0, w, h, 34); ctx.fill();
  ctx.shadowColor = 'transparent';
  ctx.strokeStyle = 'rgba(236,232,222,0.35)'; ctx.lineWidth = 1.5; ctx.stroke();
  const taken = shown(k, takeAt);
  micro(ctx, taken ? 'ON CALL · 00:00' : label, w / 2, 92, { size: 13, track: 2.2, align: 'center', fam: FONT.monoS,
    color: taken ? INK.bone : 'rgba(240,236,228,0.8)' });
  setFont(ctx, FONT.nim, 40, 0); ctx.fillStyle = INK.warm; ctx.textAlign = 'center';
  ctx.fillText('Incident', w / 2, 150); ctx.fillText('Week', w / 2, 196);
  micro(ctx, caller, w / 2, 228, { size: 11, track: 2.4, align: 'center', color: 'rgba(236,232,222,0.55)' });
  // buttons: decline greyed and struck (disabled), accept pressed on "take"
  const by = h - 110;
  ctx.fillStyle = 'rgba(120,122,126,0.35)'; ctx.beginPath(); ctx.arc(78, by, 36, 0, Math.PI * 2); ctx.fill();
  hairline(ctx, 54, by + 24, 102, by - 24, 'rgba(236,232,222,0.7)', 2);
  micro(ctx, decline, 78, by + 62, { size: 10, track: 1.8, align: 'center', color: 'rgba(236,232,222,0.7)' });
  const ta = since(k, takeAt);
  const press = ta >= 0 ? (ta < 3 ? 0.9 + 0.033 * ta : 1) : 1;
  ctx.fillStyle = taken ? INK.warm : 'rgba(236,232,222,0.85)';
  ctx.beginPath(); ctx.arc(w - 78, by, 36 * press, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = INK.dark; ctx.font = `600 13px "${FONT.monoS}"`; ctx.letterSpacing = '1.5px';
  ctx.fillText(taken ? 'TAKEN' : 'ACCEPT', w - 78, by + 5);
  micro(ctx, 'ANSWER', w - 78, by + 62, { size: 10, track: 1.8, align: 'center', color: 'rgba(236,232,222,0.7)' });
  // the screen light on the bar line: one soft pulse
  const fa = since(k, flashAt);
  if (fa >= 0 && fa < 8) {
    ctx.globalAlpha = e * 0.5 * Math.exp(-fa / 2.2);
    ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.roundRect(0, 0, w, h, 34); ctx.fill();
  }
  ctx.restore();
}

// ---------------------------------------------------------------- a stack of pager icons piling up (s014, top right)
export function pagerStack(k, ctx, x1, yBase, { from, to, label }) {
  const n = Math.min(40, k.sixteenthsBetween(from, Math.min(k.s, to)) + 1);
  if (!shown(k, from)) return;
  for (let j = 0; j < n; j++) {
    const col = j % 5, row = Math.floor(j / 5);
    const born = k.sixteenthAt(from, j);
    const ag = since(k, born);
    const sc = ag < 2 ? 1.3 - 0.15 * ag : 1;
    pagerIcon(ctx, x1 - (5 - col) * 28, yBase - row * 19, sc);
  }
  micro(ctx, label, x1, yBase + 34, { size: 12, track: 2.6, align: 'right', fam: FONT.monoS, color: 'rgba(240,236,228,0.9)' });
}

// ---------------------------------------------------------------- the pager LCD readout card (s014 -> c4)
export function lcdCard(k, ctx, x, y, { at, text, label, source }) {
  const a = since(k, at);
  if (a < 0) return;
  const e = easeOutCubic(clamp((a + 1) / 3));
  ctx.save();
  ctx.globalAlpha = e;
  ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 20; ctx.shadowOffsetY = 6;
  ctx.fillStyle = '#20231F'; ctx.beginPath(); ctx.roundRect(x, y, 420, 150, 14); ctx.fill();
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = '#A3AE93'; ctx.fillRect(x + 18, y + 18, 384, 84);
  setFont(ctx, FONT.monoS, 62, 2); ctx.fillStyle = '#1C2219'; ctx.fillText(typed(text, a, 3), x + 34, y + 82);
  setFont(ctx, FONT.monoS, 16, 2.4); ctx.fillStyle = INK.signal; ctx.fillText(label, x + 20, y + 130);
  ctx.restore();
  // the source in one or two lines, split at a separator so it stays inside the frame
  const parts = source.split(' · ');
  let l1 = source, l2 = '';
  if (source.length > 52) { const h = Math.ceil(parts.length / 2); l1 = parts.slice(0, h).join(' · '); l2 = parts.slice(h).join(' · '); }
  micro(ctx, l1, x, y + 176, { size: 10, track: 1.3, color: 'rgba(236,232,222,0.75)' });
  if (l2) micro(ctx, l2, x, y + 192, { size: 10, track: 1.3, color: 'rgba(236,232,222,0.75)' });
}
