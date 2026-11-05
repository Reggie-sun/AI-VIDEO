// Editorial explanation cards. Pure Canvas2D draws: callers own time, fonts and compositing.
import { F, font } from './draw2d.js';
import { clamp } from './math.js';

const INK = '#E9EEF1', MUTED = '#A8B6C4', LINE = '#506171', RED = '#E3342F';
const SOURCE = '来源：OpenAI · 2026-10-23 披露';
export const CACHE_MECHANISMS = Object.freeze({
  web: Object.freeze({ title: '离线网页缓存', kind: 'WEB SNAPSHOTS', detail: '索引与缓存网页，不接即时互联网' }),
  cpu: Object.freeze({ title: '处理器缓存侧信道', kind: 'CPU CACHE TIMING', detail: '隔离代理通过访问时间差交换信息' }),
});

// Start-inclusive / end-exclusive days: Sep20 to Oct01 is 11 intervals, not 12 dates.
export function dateIntervals(start = '2026-09-20', end = '2026-10-01') {
  const parse = value => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new RangeError('Expected ISO calendar date');
    const t = Date.parse(`${value}T00:00:00Z`);
    if (!Number.isFinite(t) || new Date(t).toISOString().slice(0, 10) !== value) throw new RangeError('Invalid calendar date');
    return t;
  };
  const a = parse(start), b = parse(end);
  if (b <= a || (b - a) / 86400000 > 366) throw new RangeError('Expected 1–366 forward day intervals');
  return Array.from({ length: (b - a) / 86400000 }, (_, i) => ({
    from: new Date(a + i * 86400000).toISOString().slice(0, 10),
    to: new Date(a + (i + 1) * 86400000).toISOString().slice(0, 10),
  }));
}

function text(c, value, x, y, size = 52, color = INK, family = F.sansR) {
  font(c, family, size); c.fillStyle = color; c.fillText(value, x, y);
}
function rule(c, x, y, w, color = LINE, weight = 2) {
  c.strokeStyle = color; c.lineWidth = weight; c.beginPath(); c.moveTo(x, y); c.lineTo(x + w, y); c.stroke();
}
function frame(ctx, options, draw) {
  const { width = 1920, height = 1080, progress = 1, sourceLabel = SOURCE, transparent = false } = options;
  if (![width, height, progress].every(Number.isFinite) || width <= 0 || height <= 0) throw new RangeError('Invalid graphics viewport/progress');
  ctx.save();
  try {
    ctx.scale(width / 1920, height / 1080); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; ctx.shadowBlur = 0; ctx.filter = 'none';
    if (!transparent) { ctx.fillStyle = '#0B0F14'; ctx.fillRect(0, 0, 1920, 1080); }
    draw(ctx, clamp(progress));
    rule(ctx, 120, 930, 1680);
    text(ctx, sourceLabel, 120, 986, 32, MUTED, F.mono);
  } finally { ctx.restore(); }
}

export function drawDnsRoute(ctx, options = {}) {
  frame(ctx, options, (c, p) => {
    text(c, '一次有限联网', 120, 190, 108, INK, F.serif);
    text(c, '2026-09-20 · 研究训练环境', 120, 270, 42, MUTED);
    const labels = ['研究模型', 'DNS 解析器', '外部 chatbot'];
    const x = [120, 710, 1300], y = 420, w = 500;
    for (let i = 0; i < 3; i++) {
      c.strokeStyle = i === 1 ? RED : LINE; c.lineWidth = i === 1 ? 3 : 2; c.strokeRect(x[i], y, w, 180);
      text(c, labels[i], x[i] + 34, y + 106, 58);
      if (i < 2) {
        const t = clamp(p * 2 - i), length = 90 * t;
        rule(c, x[i] + w, y + 90, 90);
        rule(c, x[i] + w, y + 90, length, RED, 5);
      }
    }
    text(c, '配置错误', x[1] + 34, 665, 52, RED);
    text(c, '有限联网', x[2] + 34, 665, 52, INK);
    text(c, '经 DNS 路径查询；不代表获得不受限浏览能力', 120, 820, 46, MUTED);
  });
}

export function drawResearchPause(ctx, options = {}) {
  const intervals = dateIntervals();
  frame(ctx, options, (c, p) => {
    text(c, '相关最强模型的研究工作', 120, 180, 64, INK, F.serif);
    text(c, '暂停 11 天', 120, 300, 94);
    text(c, '09 / 20', 120, 416, 56, MUTED, F.mono);
    text(c, '10 / 01 恢复', 1280, 416, 56, MUTED, F.mono);
    const filled = Math.floor(p * intervals.length + 1e-9), gap = 14, w = (1680 - gap * 10) / 11;
    intervals.forEach((day, i) => {
      const x = 120 + i * (w + gap), active = i < filled;
      c.fillStyle = active ? '#263441' : '#111922'; c.fillRect(x, 480, w, 190);
      rule(c, x, 480, w, active ? RED : LINE, active ? 5 : 2);
      text(c, day.from.slice(5).replace('-', '/'), x + 10, 590, 36, active ? INK : MUTED, F.mono);
    });
    text(c, '训练与评测的相关研究工作', 120, 774, 52);
    text(c, '并非所有 AI 或 ChatGPT 服务停运', 120, 846, 46, MUTED);
  });
}

export function drawCacheDistinction(ctx, options = {}) {
  frame(ctx, options, (c, p) => {
    text(c, '两个不同的「缓存」', 120, 180, 68, INK, F.serif);
    const panels = [{ x: 120, model: CACHE_MECHANISMS.web }, { x: 1010, model: CACHE_MECHANISMS.cpu }];
    for (const { x, model } of panels) {
      rule(c, x, 290, 790);
      text(c, model.kind, x, 352, 36, MUTED, F.mono);
      text(c, model.title, x, 430, 56);
    }
    // Left: pages already cached. Right: a distinct, controlled timing channel.
    for (let i = 0; i < 3; i++) {
      c.strokeStyle = LINE; c.lineWidth = 2; c.strokeRect(150 + i * 180, 500 + i * 20, 200, 140);
      rule(c, 176 + i * 180, 548 + i * 20, 120, MUTED);
    }
    text(c, '网页快照', 120, 742, 48);
    text(c, '事件发生前已存在', 120, 812, 46, MUTED);
    const x0 = 1040, y = 580;
    c.strokeStyle = LINE; c.lineWidth = 3; c.beginPath(); c.moveTo(x0, y);
    for (let i = 0; i < 12; i++) {
      const x = x0 + i * 60, level = i % 3 === 0 ? -55 : 0;
      c.lineTo(x, y + level); c.lineTo(x + 30, y + level); c.lineTo(x + 30, y);
    }
    c.stroke(); rule(c, x0, 675, 720 * p, RED, 4);
    text(c, '另一项受控红队测试', 1010, 742, 48);
    text(c, '处理器访问时间差；已修补', 1010, 812, 46, MUTED);
  });
}

export function drawWebCache(ctx, options = {}) {
  frame(ctx, options, (c, p) => {
    text(c, '离线网页缓存', 120, 190, 108, INK, F.serif);
    text(c, '网页快照，不连接即时互联网', 120, 285, 56, MUTED);
    for (let i = 0; i < 5; i++) {
      const x = 150 + i * 310, y = 410 + 22 * (1 - clamp(p * 2 - i * .18));
      c.fillStyle = '#111922'; c.fillRect(x, y, 270, 270);
      c.strokeStyle = LINE; c.lineWidth = 2; c.strokeRect(x, y, 270, 270);
      for (let j = 0; j < 4; j++) rule(c, x + 28, y + 55 + j * 38, j === 3 ? 120 : 210, MUTED);
      rule(c, x, y + 270, 270 * clamp(p * 2 - i * .18), RED, 4);
    }
    text(c, 'CACHED WEB', 120, 795, 62, INK, F.mono);
    text(c, '网页缓存方案在该事件前已存在', 120, 865, 46, MUTED);
  });
}

export function drawCpuCache(ctx, options = {}) {
  frame(ctx, options, (c, p) => {
    text(c, '缓存里的“低语”', 120, 190, 100, INK, F.serif);
    text(c, '另一项受控红队测试', 120, 285, 64, RED);
    for (const [x, label] of [[150, '代理 A'], [1350, '代理 B']]) {
      c.strokeStyle = LINE; c.lineWidth = 2; c.strokeRect(x, 410, 420, 240);
      text(c, label, x + 64, 555, 64);
    }
    const x0 = 630, y = 530, span = 660, visible = Math.floor(p * 12);
    rule(c, x0, y, span, LINE);
    c.strokeStyle = RED; c.lineWidth = 5; c.beginPath(); c.moveTo(x0, y);
    for (let i = 0; i < visible; i++) {
      const x = x0 + i * 55, h = i % 3 === 0 ? -60 : 34;
      c.lineTo(x, y + h); c.lineTo(x + 27, y + h); c.lineTo(x + 27, y);
    }
    c.stroke();
    text(c, '处理器缓存 · 访问时间差', 120, 780, 60);
    text(c, '非网页缓存；相关漏洞已修补', 120, 855, 48, MUTED);
  });
}
