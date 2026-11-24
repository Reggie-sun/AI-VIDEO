// Development stills and the lyric word log of the built composition, without a full render. Serves this folder on
// loopback, drives the engine's own render entry (window.__exRender, the function HyperFrames calls on hf-seek) in
// headless Chrome.
//
//   node outputs/ai-city-takeover/ep01/v4/excerpt/snap.mjs --out <dir> [--comp composition-v2.html] [--t 26.5,30.1,...] [--shots] [--marks <file>]
//     --t      song times (s) to save as PNG
//     --shots  first, middle and last frame of every shot
//     --marks  render every frame and write the words each frame drew (data for qa.py's lyric check)
import { createServer } from 'node:http';
import { mkdirSync, readFileSync, existsSync, statSync, writeFileSync } from 'node:fs';
import { extname, join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const DIR = dirname(fileURLToPath(import.meta.url));
const arg = (name, dflt = null) => { const i = process.argv.indexOf(name); return i < 0 ? dflt : process.argv[i + 1]; };
const out = resolve(arg('--out', '/tmp/iris-v4-excerpt-snaps'));
mkdirSync(out, { recursive: true });
const COMP = arg('--comp', 'composition.html');
const TAG = (COMP.match(/-v\d+(r\d+)?/) || [''])[0];
const D = JSON.parse(readFileSync(join(DIR, arg('--edl', `data/edl${TAG}.json`)), 'utf8'));
const FPS = D.fps, OFF = D.offset;
const shots = [];
if (process.argv.includes('--shots')) {
  for (const s of D.shots) for (const [tag, f] of [['a', s.f0], ['m', Math.floor((s.f0 + s.f1) / 2)], ['z', s.f1 - 1]]) shots.push({ name: `${s.id}-${tag}`, f: f - (D.window_f0 || 0) });
}
const F0 = D.window_f0 || 0;                                    // v4 rounds render a window of the excerpt
for (const t of (arg('--t', '') || '').split(',').filter(Boolean)) shots.push({ name: `t${Number(t).toFixed(3)}`, f: Math.round((Number(t) - OFF) * FPS) - F0 });
const marksFile = arg('--marks');

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.otf': 'font/otf', '.wav': 'audio/wav' };
const server = createServer((req, res) => {
  const p = join(DIR, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(DIR) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[extname(p)] || 'application/octet-stream' });
  res.end(readFileSync(p));
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const port = server.address().port;
const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: true,
  args: ['--enable-gpu', '--ignore-gpu-blocklist', '--use-angle=vulkan', '--enable-unsafe-webgpu', '--no-sandbox'] });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  const logs = [];
  page.on('console', m => logs.push(`${m.type()}: ${m.text()}`));
  page.on('pageerror', e => logs.push(`pageerror: ${e.message}`));
  page.on('response', r => { if (r.status() >= 400) logs.push(`error: ${r.status()} ${r.url()}`); });
  await page.goto(`http://127.0.0.1:${port}/${COMP}`, { waitUntil: 'load' });
  await page.waitForFunction('window.__ex?.ready || window.__exError', { timeout: 120000 });
  const err = await page.evaluate('window.__exError || null');
  if (err) throw new Error(err);
  console.log('renderer:', await page.evaluate('window.__ex.info.renderer'));
  const canvas = await page.$('#stage');
  for (const s of shots) {
    const t0 = Date.now();
    await page.evaluate(t => window.__exRender(t), s.f / FPS);
    await canvas.screenshot({ path: join(out, `${s.name}.png`) });
    process.stdout.write(`${s.name} f=${s.f} ${Date.now() - t0} ms\n`);
  }
  if (marksFile) {
    const rows = [];
    for (let f = 0; f < D.frames; f++) {
      await page.evaluate(t => window.__exRender(t), f / FPS);
      rows.push(await page.evaluate('window.__exMarks'));
    }
    writeFileSync(marksFile, JSON.stringify({ frames: rows }));
    console.log(`marks: ${rows.length} frames -> ${marksFile}`);
  }
  const bad = logs.filter(l => /error/i.test(l));
  if (bad.length) console.log(bad.slice(0, 20).join('\n'));
} finally {
  await browser.close();
  server.close();
}
