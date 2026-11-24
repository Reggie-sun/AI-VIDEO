// Read the Jimeng balance shown on the IRIS canvas page; read-only (no click, no request), then disconnect.
// v4 copy: differs from v3 only in the header-number fallback below (Jimeng UI change, 2026-11-17).
const fs = require('fs');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const PROJECT = '829df260-5a63-4f0d-8265-8353dc693b3b';
(async () => {
  const port = fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort', 'utf8').split('\n')[0];
  const browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url() === 'https://jimeng.jianying.com/ai-tool/ai-canvas/' + PROJECT);
  if (pages.length !== 1) throw Error('expected exactly one IRIS canvas page');
  // 2026-11-17: the canvas header no longer prints "超级会员" after the credits; it shows one number in a
  // font-dreamina-number span at the top of the page. Accept the old form, else exactly one such header number.
  const balance = await pages[0].evaluate(() => {
    const old = (document.body.innerText.match(/\d{4,6}\s*\n?\s*超级会员/) || [''])[0].replace(/\s+/g, ' ');
    if (old) return old;
    const hits = [...document.querySelectorAll('span.font-dreamina-number')]
      .filter(el => el.children.length === 0 && /^\s*\d{4,7}\s*$/.test(el.textContent) && el.getBoundingClientRect().top < 80);
    return hits.length === 1 ? hits[0].textContent.trim() : '';
  });
  console.log(JSON.stringify({ observed_balance: balance, read_at: new Date().toISOString() }));
  await browser.close().catch(() => {});
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
