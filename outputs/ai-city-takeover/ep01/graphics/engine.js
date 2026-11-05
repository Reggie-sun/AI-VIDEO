(() => {
  // motion-kit/src/math.js
  var clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));

  // motion-kit/src/draw2d.js
  var F = {
    sans: "MK Sans SC",
    sansR: "MK Sans SC Regular",
    mono: "MK Mono SC",
    monoB: "MK Mono SC Bold",
    serif: "MK Serif SC"
  };
  async function loadFonts(baseUrl) {
    const manifest = await (await fetch(`${baseUrl}/fonts.json`)).json();
    for (const f of manifest.faces) {
      const face = new FontFace(f.family, `url(${baseUrl}/${f.file})`);
      await face.load();
      document.fonts.add(face);
    }
    await document.fonts.ready;
    return manifest;
  }
  function font(ctx2, family, size, tracking = 0) {
    ctx2.font = `${size}px "${family}"`;
    ctx2.letterSpacing = `${tracking}px`;
  }

  // motion-kit/src/news-graphics.js
  var INK = "#E9EEF1";
  var MUTED = "#A8B6C4";
  var LINE = "#506171";
  var RED = "#E3342F";
  var SOURCE = "\u6765\u6E90\uFF1AOpenAI \xB7 2026-10-23 \u62AB\u9732";
  var CACHE_MECHANISMS = Object.freeze({
    web: Object.freeze({ title: "\u79BB\u7EBF\u7F51\u9875\u7F13\u5B58", kind: "WEB SNAPSHOTS", detail: "\u7D22\u5F15\u4E0E\u7F13\u5B58\u7F51\u9875\uFF0C\u4E0D\u63A5\u5373\u65F6\u4E92\u8054\u7F51" }),
    cpu: Object.freeze({ title: "\u5904\u7406\u5668\u7F13\u5B58\u4FA7\u4FE1\u9053", kind: "CPU CACHE TIMING", detail: "\u9694\u79BB\u4EE3\u7406\u901A\u8FC7\u8BBF\u95EE\u65F6\u95F4\u5DEE\u4EA4\u6362\u4FE1\u606F" })
  });
  function dateIntervals(start = "2026-09-20", end = "2026-10-01") {
    const parse = (value) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new RangeError("Expected ISO calendar date");
      const t = Date.parse(`${value}T00:00:00Z`);
      if (!Number.isFinite(t) || new Date(t).toISOString().slice(0, 10) !== value) throw new RangeError("Invalid calendar date");
      return t;
    };
    const a = parse(start), b = parse(end);
    if (b <= a || (b - a) / 864e5 > 366) throw new RangeError("Expected 1\u2013366 forward day intervals");
    return Array.from({ length: (b - a) / 864e5 }, (_, i) => ({
      from: new Date(a + i * 864e5).toISOString().slice(0, 10),
      to: new Date(a + (i + 1) * 864e5).toISOString().slice(0, 10)
    }));
  }
  function text(c, value, x, y, size = 52, color = INK, family = F.sansR) {
    font(c, family, size);
    c.fillStyle = color;
    c.fillText(value, x, y);
  }
  function rule(c, x, y, w, color = LINE, weight = 2) {
    c.strokeStyle = color;
    c.lineWidth = weight;
    c.beginPath();
    c.moveTo(x, y);
    c.lineTo(x + w, y);
    c.stroke();
  }
  function frame(ctx2, options, draw) {
    const { width = 1920, height = 1080, progress = 1, sourceLabel = SOURCE, transparent = false } = options;
    if (![width, height, progress].every(Number.isFinite) || width <= 0 || height <= 0) throw new RangeError("Invalid graphics viewport/progress");
    ctx2.save();
    try {
      ctx2.scale(width / 1920, height / 1080);
      ctx2.globalAlpha = 1;
      ctx2.globalCompositeOperation = "source-over";
      ctx2.textAlign = "left";
      ctx2.textBaseline = "alphabetic";
      ctx2.shadowBlur = 0;
      ctx2.filter = "none";
      if (!transparent) {
        ctx2.fillStyle = "#0B0F14";
        ctx2.fillRect(0, 0, 1920, 1080);
      }
      draw(ctx2, clamp(progress));
      rule(ctx2, 120, 930, 1680);
      text(ctx2, sourceLabel, 120, 986, 32, MUTED, F.mono);
    } finally {
      ctx2.restore();
    }
  }
  function drawDnsRoute(ctx2, options = {}) {
    frame(ctx2, options, (c, p) => {
      text(c, "\u4E00\u6B21\u6709\u9650\u8054\u7F51", 120, 190, 108, INK, F.serif);
      text(c, "2026-09-20 \xB7 \u7814\u7A76\u8BAD\u7EC3\u73AF\u5883", 120, 270, 42, MUTED);
      const labels = ["\u7814\u7A76\u6A21\u578B", "DNS \u89E3\u6790\u5668", "\u5916\u90E8 chatbot"];
      const x = [120, 710, 1300], y = 420, w = 500;
      for (let i = 0; i < 3; i++) {
        c.strokeStyle = i === 1 ? RED : LINE;
        c.lineWidth = i === 1 ? 3 : 2;
        c.strokeRect(x[i], y, w, 180);
        text(c, labels[i], x[i] + 34, y + 106, 58);
        if (i < 2) {
          const t = clamp(p * 2 - i), length = 90 * t;
          rule(c, x[i] + w, y + 90, 90);
          rule(c, x[i] + w, y + 90, length, RED, 5);
        }
      }
      text(c, "\u914D\u7F6E\u9519\u8BEF", x[1] + 34, 665, 52, RED);
      text(c, "\u6709\u9650\u8054\u7F51", x[2] + 34, 665, 52, INK);
      text(c, "\u7ECF DNS \u8DEF\u5F84\u67E5\u8BE2\uFF1B\u4E0D\u4EE3\u8868\u83B7\u5F97\u4E0D\u53D7\u9650\u6D4F\u89C8\u80FD\u529B", 120, 820, 46, MUTED);
    });
  }
  function drawResearchPause(ctx2, options = {}) {
    const intervals = dateIntervals();
    frame(ctx2, options, (c, p) => {
      text(c, "\u76F8\u5173\u6700\u5F3A\u6A21\u578B\u7684\u7814\u7A76\u5DE5\u4F5C", 120, 180, 64, INK, F.serif);
      text(c, "\u6682\u505C 11 \u5929", 120, 300, 94);
      text(c, "09 / 20", 120, 416, 56, MUTED, F.mono);
      text(c, "10 / 01 \u6062\u590D", 1280, 416, 56, MUTED, F.mono);
      const filled = Math.floor(p * intervals.length + 1e-9), gap = 14, w = (1680 - gap * 10) / 11;
      intervals.forEach((day, i) => {
        const x = 120 + i * (w + gap), active = i < filled;
        c.fillStyle = active ? "#263441" : "#111922";
        c.fillRect(x, 480, w, 190);
        rule(c, x, 480, w, active ? RED : LINE, active ? 5 : 2);
        text(c, day.from.slice(5).replace("-", "/"), x + 10, 590, 36, active ? INK : MUTED, F.mono);
      });
      text(c, "\u8BAD\u7EC3\u4E0E\u8BC4\u6D4B\u7684\u76F8\u5173\u7814\u7A76\u5DE5\u4F5C", 120, 774, 52);
      text(c, "\u5E76\u975E\u6240\u6709 AI \u6216 ChatGPT \u670D\u52A1\u505C\u8FD0", 120, 846, 46, MUTED);
    });
  }
  function drawWebCache(ctx2, options = {}) {
    frame(ctx2, options, (c, p) => {
      text(c, "\u79BB\u7EBF\u7F51\u9875\u7F13\u5B58", 120, 190, 108, INK, F.serif);
      text(c, "\u7F51\u9875\u5FEB\u7167\uFF0C\u4E0D\u8FDE\u63A5\u5373\u65F6\u4E92\u8054\u7F51", 120, 285, 56, MUTED);
      for (let i = 0; i < 5; i++) {
        const x = 150 + i * 310, y = 410 + 22 * (1 - clamp(p * 2 - i * 0.18));
        c.fillStyle = "#111922";
        c.fillRect(x, y, 270, 270);
        c.strokeStyle = LINE;
        c.lineWidth = 2;
        c.strokeRect(x, y, 270, 270);
        for (let j = 0; j < 4; j++) rule(c, x + 28, y + 55 + j * 38, j === 3 ? 120 : 210, MUTED);
        rule(c, x, y + 270, 270 * clamp(p * 2 - i * 0.18), RED, 4);
      }
      text(c, "CACHED WEB", 120, 795, 62, INK, F.mono);
      text(c, "\u7F51\u9875\u7F13\u5B58\u65B9\u6848\u5728\u8BE5\u4E8B\u4EF6\u524D\u5DF2\u5B58\u5728", 120, 865, 46, MUTED);
    });
  }
  function drawCpuCache(ctx2, options = {}) {
    frame(ctx2, options, (c, p) => {
      text(c, "\u7F13\u5B58\u91CC\u7684\u201C\u4F4E\u8BED\u201D", 120, 190, 100, INK, F.serif);
      text(c, "\u53E6\u4E00\u9879\u53D7\u63A7\u7EA2\u961F\u6D4B\u8BD5", 120, 285, 64, RED);
      for (const [x, label] of [[150, "\u4EE3\u7406 A"], [1350, "\u4EE3\u7406 B"]]) {
        c.strokeStyle = LINE;
        c.lineWidth = 2;
        c.strokeRect(x, 410, 420, 240);
        text(c, label, x + 64, 555, 64);
      }
      const x0 = 630, y = 530, span = 660, visible = Math.floor(p * 12);
      rule(c, x0, y, span, LINE);
      c.strokeStyle = RED;
      c.lineWidth = 5;
      c.beginPath();
      c.moveTo(x0, y);
      for (let i = 0; i < visible; i++) {
        const x = x0 + i * 55, h = i % 3 === 0 ? -60 : 34;
        c.lineTo(x, y + h);
        c.lineTo(x + 27, y + h);
        c.lineTo(x + 27, y);
      }
      c.stroke();
      text(c, "\u5904\u7406\u5668\u7F13\u5B58 \xB7 \u8BBF\u95EE\u65F6\u95F4\u5DEE", 120, 780, 60);
      text(c, "\u975E\u7F51\u9875\u7F13\u5B58\uFF1B\u76F8\u5173\u6F0F\u6D1E\u5DF2\u4FEE\u8865", 120, 855, 48, MUTED);
    });
  }

  // outputs/ai-city-takeover/ep01/graphics/src/main.js
  var draws = { dns: drawDnsRoute, pause: drawResearchPause, "web-cache": drawWebCache, "cpu-cache": drawCpuCache };
  var canvas = document.getElementById("stage");
  var ctx = canvas.getContext("2d", { willReadFrequently: true });
  var ready = Promise.all([loadFonts("fonts"), fetch("config.json").then((r) => {
    if (!r.ok) throw new Error("Missing local graphic config");
    return r.json();
  })]);
  function render(t) {
    return ready.then(([, config]) => {
      const draw = draws[config.kind];
      if (!draw) throw new Error("Unknown source graphic");
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, 1920, 1080);
      const progress = Math.max(0, Math.min(1, t / 3));
      draw(ctx, { width: 1920, height: 1080, progress });
    });
  }
  window.addEventListener("hf-seek", (e) => e.detail.waitUntil(render(e.detail.time)));
  window.__graphicRender = render;
  render(0);
})();
