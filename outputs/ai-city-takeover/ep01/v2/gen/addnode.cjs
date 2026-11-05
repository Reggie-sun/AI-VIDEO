// Add ONE empty video node to the IRIS canvas through its own toolbar button, then report the new node.
// No generation request is made. Writes intent before and observation after into the unit folder.
const fs = require('fs');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const PROJECT = '829df260-5a63-4f0d-8265-8353dc693b3b';
const unitDir = process.argv[2];
function locate(projectId) {
  const visited = new Set(); let canvas;
  for (const element of document.querySelectorAll('*')) {
    let fiber = element[Object.keys(element).find(k => k.startsWith('__reactFiber$'))];
    for (let i = 0; fiber && i < 240 && !visited.has(fiber); i++, fiber = fiber.return) {
      visited.add(fiber);
      const value = fiber.memoizedProps?.value;
      if (value?.generationRuntime && value?.controller && value.actions?.projectId === projectId) canvas = value;
    }
  }
  const api = canvas.mutableFeaturesApi.canvas;
  return api.getNodeIds().map(id => { const n = api.getObjectSnapshot(id); const d = n?.data?.generationDraft;
    return { id, type: n?.type, resourceId: n?.data?.resourceId || null,
             emptyDraft: !d || ((d.parts || []).length === 0 && (d.references || []).length === 0) }; });
}
(async () => {
  if (fs.existsSync(unitDir + '/node-created.json')) throw Error('node already created for this unit');
  const port = fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort', 'utf8').split('\n')[0];
  const browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url() === 'https://jimeng.jianying.com/ai-tool/ai-canvas/' + PROJECT);
  if (pages.length !== 1) throw Error('expected exactly one IRIS canvas page');
  const page = pages[0];
  const before = await page.evaluate(locate, PROJECT);
  fs.writeFileSync(unitDir + '/node-create-intent.json', JSON.stringify({ operation: 'add_one_empty_video_node',
    via: 'canvas left toolbar 视频 button', prior_node_ids: before.map(n => n.id), created_at: new Date().toISOString(),
    generation_POSTs: 0 }, null, 2) + '\n', { flag: 'wx' });
  const button = page.locator('button[data-toolbar-item="video"]');
  const box = await button.boundingBox();
  if (!box || box.x > 80) throw Error('left toolbar 视频 button not found');
  await button.click();
  await page.waitForTimeout(1500);
  const after = await page.evaluate(locate, PROJECT);
  const added = after.filter(n => !before.some(b => b.id === n.id));
  const balance = await page.evaluate(() => (document.body.innerText.match(/\d{4,6}\s*\n?\s*超级会员/) || [''])[0].replace(/\s+/g, ' '));
  console.log(JSON.stringify({ added, total_after: after.length, balance }));
  if (added.length === 1 && added[0].type === 'video' && !added[0].resourceId && added[0].emptyDraft) {
    fs.writeFileSync(unitDir + '/node-created.json', JSON.stringify({ node_id: added[0].id, empty: true, project_id: PROJECT,
      observed_balance: balance, created_at: new Date().toISOString(), generation_POSTs: 0 }, null, 2) + '\n', { flag: 'wx' });
  } else {
    await page.screenshot({ path: unitDir + '/node-create-unexpected.png' });
  }
  await browser.close().catch(() => {});
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
