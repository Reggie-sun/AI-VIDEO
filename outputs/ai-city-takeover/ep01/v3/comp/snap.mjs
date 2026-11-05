// Still frames of the built composition at chosen times, without a full render (development check only; the
// deliverable is rendered by HyperFrames). Serves this folder on loopback, drives the engine's own render entry
// (window.__mkRender, the same renderFrame HyperFrames calls on hf-seek) in headless Chrome and saves PNGs.
//
//   node outputs/ai-city-takeover/ep01/v3/comp/snap.mjs --out <dir> [--units] [--t 1.5,10.2,...] [--gpu]
//     --units: first, middle and last frame of every unit (data/units.json)
import { createServer } from 'node:http';
import { mkdirSync, readFileSync, existsSync, statSync } from 'node:fs';
import { extname, join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';
import puppeteer from 'puppeteer-core';

const COMP = dirname(fileURLToPath(import.meta.url));
const arg = (name, dflt = null) => { const i = process.argv.indexOf(name); return i < 0 ? dflt : process.argv[i + 1]; };
const out = resolve(arg('--out', '/tmp/iris-v3-snaps'));
mkdirSync(out, { recursive: true });
const FPS = 30;
const units = JSON.parse(readFileSync(join(COMP, 'data/units.json'), 'utf8')).units;
let shots = [];
if (process.argv.includes('--units')) {
  for (const u of units) for (const [tag, f] of [['a', u.f0], ['m', Math.floor((u.f0 + u.f1) / 2)], ['z', u.f1 - 1]]) shots.push({ name: `${u.id}-${tag}`, f });
}
for (const t of (arg('--t', '') || '').split(',').filter(Boolean)) shots.push({ name: `t${Number(t).toFixed(3)}`, f: Math.round(Number(t) * FPS) });

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.otf': 'font/otf', '.wav': 'audio/wav' };
const server = createServer((req, res) => {
  const p = join(COMP, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(COMP) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[extname(p)] || 'application/octet-stream' });
  res.end(readFileSync(p));
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const port = server.address().port;

const chrome = join(homedir(), '.cache/puppeteer/chrome/linux-146.0.7680.153/chrome-linux64/chrome');
const gpu = process.argv.includes('--gpu');
const browser = await puppeteer.launch({ executablePath: chrome, headless: true,
  args: gpu ? ['--enable-gpu', '--ignore-gpu-blocklist', '--use-angle=vulkan'] : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  const logs = [];
  page.on('console', m => logs.push(`${m.type()}: ${m.text()}`));
  page.on('pageerror', e => logs.push(`pageerror: ${e.message}`));
  page.on('response', r => { if (r.status() >= 400) logs.push(`error: ${r.status()} ${r.url()}`); });
  await page.goto(`http://127.0.0.1:${port}/index.html`, { waitUntil: 'load' });
  await page.waitForFunction('window.__mk?.ready || window.__mkError', { timeout: 120000 });
  const err = await page.evaluate('window.__mkError || null');
  if (err) throw new Error(err);
  const canvas = await page.$('#stage');
  for (const s of shots) {
    const t0 = Date.now();
    await page.evaluate(t => window.__mkRender(t), s.f / FPS);
    await canvas.screenshot({ path: join(out, `${s.name}.png`) });
    process.stdout.write(`${s.name} f=${s.f} ${Date.now() - t0} ms\n`);
  }
  const bad = logs.filter(l => /error/i.test(l));
  if (bad.length) console.log(bad.slice(0, 20).join('\n'));
} finally {
  await browser.close();
  server.close();
}
