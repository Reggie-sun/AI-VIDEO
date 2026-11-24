// Read-only: the P Zero clips' records (audio_url, media_urls) through the user's logged-in Suno tab session.
//   node outputs/ai-city-takeover/ep01/v4/song/clip_urls.cjs > ui/clip-urls.json
const fs = require('fs'), path = require('path');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
(async () => {
  const rows = JSON.parse(fs.readFileSync(path.join(__dirname, 'ui/takes-list.json'), 'utf8'));
  const b = await chromium.connectOverCDP('http://127.0.0.1:19232', { timeout: 10000 });
  let p = null;
  for (const x of b.contexts().flatMap(c => c.pages()).filter(x => x.url().includes('suno.com/create')))
    if (await x.evaluate(() => window.name).catch(() => '') === 'iris-ep01-v4') { p = x; break; }
  const out = [];
  for (const r of rows) out.push(await p.evaluate(async (id) => {
    const c = await (await fetch(`https://studio-api.prod.suno.com/api/clip/${id}`, { credentials: 'include' })).json();
    return { id, title: c.title, status: c.status, model: c.model_name, audio_url: c.audio_url, media_urls: c.media_urls, duration: c.metadata && c.metadata.duration, tags: c.metadata && c.metadata.tags };
  }, r.id));
  console.log(JSON.stringify(out, null, 1));
  await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
