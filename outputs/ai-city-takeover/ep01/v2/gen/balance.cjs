// Read the Jimeng balance shown on the IRIS canvas page; read-only (no click, no request), then disconnect.
const fs = require('fs');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const PROJECT = '829df260-5a63-4f0d-8265-8353dc693b3b';
(async () => {
  const port = fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort', 'utf8').split('\n')[0];
  const browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url() === 'https://jimeng.jianying.com/ai-tool/ai-canvas/' + PROJECT);
  if (pages.length !== 1) throw Error('expected exactly one IRIS canvas page');
  const balance = await pages[0].evaluate(() => (document.body.innerText.match(/\d{4,6}\s*\n?\s*超级会员/) || [''])[0].replace(/\s+/g, ' '));
  console.log(JSON.stringify({ observed_balance: balance, read_at: new Date().toISOString() }));
  await browser.close().catch(() => {});
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
