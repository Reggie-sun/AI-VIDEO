// Read-only: list the "P Zero" clips on the user's Suno create page (clip id, title, style text, duration) once they finish.
//   node outputs/ai-city-takeover/ep01/v4/song/list_takes.cjs [want=6] [maxSeconds=420]
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
(async () => {
  const want = +(process.argv[2] || 6), maxS = +(process.argv[3] || 420);
  const b = await chromium.connectOverCDP('http://127.0.0.1:19232', { timeout: 10000 });
  let p = null;
  for (const x of b.contexts().flatMap(c => c.pages()).filter(x => x.url().includes('suno.com/create')))
    if (await x.evaluate(() => window.name).catch(() => '') === 'iris-ep01-v4') { p = x; break; }
  if (!p) throw Error('no iris-ep01-v4 tab');
  let rows = [];
  for (let t = 0; t < maxS; t += 10) {
    rows = await p.evaluate(() => {
      const seen = new Map();
      for (const a of document.querySelectorAll('a[href*="/song/"]')) {
        const id = (a.getAttribute('href').match(/\/song\/([0-9a-f-]{36})/) || [])[1];
        if (!id || seen.has(id)) continue;
        let row = a; for (let i = 0; i < 8 && row && !/\d:\d\d/.test(row.innerText || ''); i++) row = row.parentElement;
        const txt = row ? row.innerText : '';
        seen.set(id, { id, title: (a.innerText || '').trim(), duration: (txt.match(/\b(\d+:\d\d)\b/) || [])[1] || null, text: txt.slice(0, 300) });
      }
      return [...seen.values()].filter(r => /All Hands r4/.test(r.title) || /All Hands r4/.test(r.text));
    });
    if (rows.filter(r => r.duration).length >= want) break;
    await p.waitForTimeout(10000);
  }
  console.log(JSON.stringify(rows, null, 1));
  await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
