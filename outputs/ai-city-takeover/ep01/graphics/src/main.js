import { loadFonts } from '../../../../../motion-kit/src/draw2d.js';
import { drawDnsRoute, drawResearchPause, drawWebCache, drawCpuCache } from '../../../../../motion-kit/src/news-graphics.js';
const draws = { dns: drawDnsRoute, pause: drawResearchPause, 'web-cache': drawWebCache, 'cpu-cache': drawCpuCache };
const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
const ready = Promise.all([loadFonts('fonts'), fetch('config.json').then(r => { if (!r.ok) throw new Error('Missing local graphic config'); return r.json(); })]);
function render(t) {
  return ready.then(([, config]) => {
    const draw = draws[config.kind];
    if (!draw) throw new Error('Unknown source graphic');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, 1920, 1080);
    // Local source animation only: advance over 3s, then hold the complete explanation.
    const progress = Math.max(0, Math.min(1, t / 3));
    draw(ctx, { width: 1920, height: 1080, progress });
  });
}
window.addEventListener('hf-seek', e => e.detail.waitUntil(render(e.detail.time)));
window.__graphicRender = render;
render(0);
