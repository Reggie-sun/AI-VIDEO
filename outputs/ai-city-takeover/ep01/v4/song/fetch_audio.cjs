// Read-only: fetch each P Zero clip's MP3 from inside the user's logged-in Suno tab (private clips need its session).
//   node outputs/ai-city-takeover/ep01/v4/song/fetch_audio.cjs
const fs = require('fs'), path = require('path');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
(async () => {
  const D = __dirname, rows = JSON.parse(fs.readFileSync(path.join(D, 'ui/takes-list.json'), 'utf8'));
  const b = await chromium.connectOverCDP('http://127.0.0.1:19232', { timeout: 10000 });
  let p = null;
  for (const x of b.contexts().flatMap(c => c.pages()).filter(x => x.url().includes('suno.com/create')))
    if (await x.evaluate(() => window.name).catch(() => '') === 'iris-ep01-v4') { p = x; break; }
  for (const r of rows) {
    const res = await p.evaluate(async (id) => {
      for (const u of [`https://cdn1.suno.ai/${id}.mp3`, `https://cdn2.suno.ai/${id}.mp3`]) {
        try {
          const rr = await fetch(u, { credentials: 'include' });
          if (rr.ok) { const buf = new Uint8Array(await rr.arrayBuffer()); let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000)); return { u, b64: btoa(s) }; }
        } catch (e) {}
      }
      // the clip record through the page's own logged-in session: its audio_url is the signed, playable one
      try {
        const tok = window.Clerk && window.Clerk.session ? await window.Clerk.session.getToken() : null;
        const rr = await fetch(`https://studio-api.prod.suno.com/api/clip/${id}`, { headers: tok ? { Authorization: `Bearer ${tok}` } : {} });
        if (rr.ok) {
          const c = await rr.json();
          for (const u of [c.audio_url, c.audio_url_hq].filter(Boolean)) {
            const ar = await fetch(u);
            if (ar.ok) { const buf = new Uint8Array(await ar.arrayBuffer()); let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000)); return { u, b64: btoa(s) }; }
          }
          return { u: null, why: 'clip ok, audio fetch failed', keys: Object.keys(c).slice(0, 30) };
        }
        return { u: null, why: 'clip ' + rr.status + (tok ? '' : ' (no token)') };
      } catch (e) { return { u: null, why: String(e) }; }
    }, r.id);
    if (res.u) { fs.writeFileSync(path.join(D, 'takes', r.id + '.mp3'), Buffer.from(res.b64, 'base64')); console.log('ok', r.id, res.u); }
    else console.log('fail', r.id, JSON.stringify(res));
  }
  await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
