// Jimeng 数字人 (OmniHuman 1.5, 大师模式) browser side for the IRIS EP01 v2 trial units (trial/omnihuman/<unit>/).
//   node outputs/ai-city-takeover/ep01/v2/gen/omnihuman.cjs fill <unit>
// fill: only when gen/omnihuman.py lint passed. Opens its own tab (home#omnihuman-<unit>), picks 创作类型 数字人 and
// 大师模式, uploads the approved image to 角色 and the approved audio through 上传音频, types the approved action text,
// then reads what the page shows (mode, uploads, action text, price, balance) into <unit>/fill-observed.json together
// with the panel's buttons, and leaves the tab open. It never clicks the generate button.
// observe: re-read that open tab (no click) while no permit binds the observation.
// submit: the one click, under the permit gen/omnihuman.py wrote (see submit() below).
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');

const V2 = path.resolve(__dirname, '..');
const TRIAL = path.join(V2, process.env.OMNI_TRIAL || 'trial/omnihuman');   // a later trial names its own folder
const HOME = 'https://jimeng.jianying.com/ai-tool/home';
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const read = f => JSON.parse(fs.readFileSync(f, 'utf8'));

async function connect() {
  const port = fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort', 'utf8').split('\n')[0];
  return chromium.connectOverCDP('http://127.0.0.1:' + port);
}

// what the 数字人 panel shows now (the smallest block holding both 动作描述 and 上传音频)
function panelState() {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const panel = [...document.querySelectorAll('div')].filter(d => vis(d) && /动作描述/.test(d.innerText || '') && /上传音频/.test(d.innerText || '')
    && /大师模式|快速模式|基础模式/.test(d.innerText || ''))
    .sort((a, b) => (a.innerText || '').length - (b.innerText || '').length)[0];
  if (!panel) return { found: false };
  const box = panel.getBoundingClientRect();
  const text = panel.innerText;
  const mode = (text.match(/大师模式|快速模式|基础模式/) || [null])[0];
  const imgs = [...panel.querySelectorAll('img')].filter(vis).map(i => ({ src: (i.currentSrc || i.src || '').slice(0, 80), w: i.width, h: i.height }));
  const editors = [...panel.querySelectorAll('textarea,input[type=text],[contenteditable=true]')].map(el => ({
    tag: el.tagName, value: (el.value ?? el.innerText ?? '').trim(), placeholder: el.placeholder || el.getAttribute('data-placeholder') || null }));
  const buttons = [...panel.querySelectorAll('button,[role=button]')].filter(vis).map(b => {
    const r = b.getBoundingClientRect();
    return { text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30), x: Math.round(r.x - box.x), y: Math.round(r.y - box.y),
             w: Math.round(r.width), h: Math.round(r.height), disabled: b.disabled || /disabled/.test(b.className || ''), cls: String(b.className || '').slice(0, 120) };
  });
  const numbers = [...panel.querySelectorAll('span,div')].filter(el => vis(el) && el.children.length === 0 && /^\d+$/.test((el.innerText || '').trim()))
    .map(el => { const r = el.getBoundingClientRect(); return { n: Number(el.innerText.trim()), x: Math.round(r.x - box.x), y: Math.round(r.y - box.y) }; });
  const price = numbers.filter(n => n.x > box.width - 260).sort((a, b) => b.x - a.x)[0];
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const TOOLBAR = ['数字人', '大师模式', '快速模式', '基础模式', '上传音频'];  // an empty field's next line is the toolbar
  const row = label => {                                          // the text may follow the tag on its own line or the same line
    const i = lines.findIndex(l => l.startsWith(label));
    if (i < 0) return null;
    return lines[i].length > label.length ? lines[i].slice(label.length).trim() : (lines[i + 1] ?? '');
  };
  const said = row('角色说');                                       // with uploaded audio the speech row is a player
  const player = said !== null ? (text.match(/(\d\d:\d\d)\s*\/\s*(\d\d:\d\d)/) || [null, null, null]) : [null, null, null];
  const resolution = (text.match(/\b(1080P|720P|480P|2K|4K)\b/i) || [null])[0];
  return { found: true, text, mode, imgs, editors, buttons, numbers, price: price ? price.n : null, size: [Math.round(box.width), Math.round(box.height)],
           rows: { speech_text: row('说话内容'), speech_audio: player[2], action: TOOLBAR.includes(row('动作描述')) ? '' : row('动作描述') },
           resolution, vivid: /生动/.test(text) };
}

// the 4-6 digit balance shown on the IRIS canvas tab (the home page rounds it to 万)
const IRIS_CANVAS = 'https://jimeng.jianying.com/ai-tool/ai-canvas/829df260-5a63-4f0d-8265-8353dc693b3b';
async function preciseBalance(browser) {                       // its own tab: the user's canvas tab is not touched
  const page = await browser.contexts()[0].newPage();
  try {
    await page.goto(IRIS_CANVAS + '#balance', { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 20; i++) {                                // the canvas shell loads the balance late
      await page.waitForTimeout(1000);
      const m = await page.evaluate(() => (document.body.innerText.match(/(\d{4,6})\s*\n?\s*超级会员/) || [])[1] || null);
      if (m) return Number(m);
    }
    return null;
  } finally {
    await page.close().catch(() => {});
  }
}

// The 角色 card and 上传音频 open the File System Access picker (window.showOpenFilePicker), which Playwright's file
// chooser cannot answer. Answer it with the approved file: the page gets the exact bytes (checked by SHA-256 inside the
// page) through its own upload path, as if the user had picked that file; nothing else is changed.
async function upload(page, trigger, file, type, label) {
  const b64 = fs.readFileSync(file).toString('base64');
  const digest = await page.evaluate(async ({ b64, name, type }) => {
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const hex = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(b => b.toString(16).padStart(2, '0')).join('');
    window.__mkFile = new File([bytes], name, { type, lastModified: Date.now() });
    window.__mkPicked = 0;
    window.showOpenFilePicker = async () => {
      const f = window.__mkFile; window.__mkFile = null;
      if (!f) throw new DOMException('no approved file', 'AbortError');
      window.__mkPicked += 1;
      return [{ kind: 'file', name: f.name, getFile: async () => f }];
    };
    return hex;
  }, { b64, name: path.basename(file), type });
  if (digest !== sha(file)) throw Error(`${label}: the bytes in the page differ from the approved file`);
  await trigger.click();
  await page.waitForTimeout(2000);
  if (await page.evaluate(() => window.__mkPicked) !== 1) throw Error(`${label}: the page did not take the file`);
}

async function fill(unit) {
  const dir = path.join(TRIAL, unit);
  const lint = read(path.join(dir, 'lint.json'));
  if (!lint.pass) throw Error('lint has not passed');
  if (fs.existsSync(path.join(dir, 'permit.json'))) throw Error('a permit exists for this fill; a new fill needs a new unit');
  const approval = read(path.join(TRIAL, 'preview-approval.json'));
  const [shared, audio] = ['singer image', 'uploaded vocal'].map(role => approval.preview_artifacts.find(a => a.role === role));
  const image = approval.takes[unit].image || shared;              // a unit may carry its own approved image
  const files = [image, audio].map(a => path.join(V2, a.path));
  files.forEach((f, i) => { if (sha(f) !== [image, audio][i].sha256) throw Error(`${f} changed since the approval`); });
  const action = approval.takes[unit].action_prompt || '';
  const browser = await connect();
  const page = await browser.contexts()[0].newPage();
  try {
    await page.goto(`${HOME}#omnihuman-${unit}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(6000);
    await page.getByText('Agent 模式', { exact: false }).first().click();
    await page.waitForTimeout(800);
    await page.getByText('数字人', { exact: true }).last().click();
    await page.waitForTimeout(1500);
    // the visible toolbar mode select only (a combobox): a finished job card elsewhere on the page also reads 大师模式
    const modeButton = page.locator('[role=combobox]:visible').filter({ hasText: /快速模式|基础模式|大师模式/ }).first();
    await modeButton.click();
    await page.waitForTimeout(800);
    await page.locator('[class*="lv-select-option"]:visible').filter({ hasText: '大师模式' }).first().click();
    await page.waitForTimeout(1200);
    await modeButton.click();                                     // reopen only to read the menu title
    await page.waitForTimeout(800);
    const modelTitle = await page.evaluate(() => (document.body.innerText.match(/选择模型：[^\n]+/) || [null])[0]);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    if (action) {                                                 // typed before the uploads: typing after them dropped the audio
      const tag = page.locator('span.node-paragraph-tag:visible', { hasText: '动作描述' }).first();
      const b = await tag.boundingBox();
      if (!b) throw Error('no 动作描述 row');
      await page.mouse.click(b.x + b.width + 40, b.y + b.height / 2);
      await page.keyboard.press('End');
      await page.keyboard.insertText(action);
      await page.waitForTimeout(1500);
    }
    await upload(page, page.locator('div[class*="reference-upload"]').first(), files[0], 'image/png', 'image');
    await page.waitForTimeout(4000);
    await page.mouse.move(10, 900);                               // let the 角色 tooltip close
    await upload(page, page.getByText('上传音频', { exact: true }).first(), files[1], 'audio/wav', 'audio');
    await page.waitForTimeout(6000);
    // seen on OH-B: the audio chip showed but 生成 stayed disabled ("请添加说话内容或上传音频"); removing the chip and
    // giving the same bytes once more fixed it. Done at most once; the observation records the result either way.
    const enabled = () => page.evaluate(() => [...document.querySelectorAll('button[aria-label="生成"]')]
      .filter(b => b.getBoundingClientRect().width > 0).some(b => !b.disabled));
    if (!(await enabled())) {
      await page.locator('.ProseMirror:visible .node-audio-player button').nth(1).click();
      await page.waitForTimeout(1500);
      await upload(page, page.getByText('上传音频', { exact: true }).first(), files[1], 'audio/wav', 'audio (again)');
    }
    await page.waitForTimeout(6000);
    await page.waitForTimeout(3000);
    await writeObservation(page, dir, unit, image, audio, action, { model_title: modelTitle, browser });
  } catch (e) {
    await page.screenshot({ path: path.join(dir, 'fill-error.png') }).catch(() => {});
    await page.close().catch(() => {});
    throw e;
  }
  await browser.close().catch(() => {});                          // disconnect only: the filled tab stays open
}

// re-read the open tab of a unit (no click) while no permit binds its observation
async function observe(unit) {
  const dir = path.join(TRIAL, unit);
  if (fs.existsSync(path.join(dir, 'permit.json'))) throw Error('a permit already binds the observation');
  const approval = read(path.join(TRIAL, 'preview-approval.json'));
  const [shared, audio] = ['singer image', 'uploaded vocal'].map(role => approval.preview_artifacts.find(a => a.role === role));
  const image = approval.takes[unit].image || shared;              // a unit may carry its own approved image
  const browser = await connect();
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url().endsWith(`#omnihuman-${unit}`));
  if (pages.length !== 1) throw Error(`expected one tab for ${unit}, found ${pages.length}`);
  const prior = fs.existsSync(path.join(dir, 'fill-observed.json')) ? read(path.join(dir, 'fill-observed.json')) : {};
  await writeObservation(pages[0], dir, unit, image, audio, approval.takes[unit].action_prompt || '', { model_title: prior.model_title ?? null, browser });
  await browser.close().catch(() => {});
}

async function writeObservation(page, dir, unit, image, audio, action, { model_title, browser }) {
  const state = await page.evaluate(panelState);
  const balance_precise = await preciseBalance(browser);
  const balance = await page.evaluate(() => (document.body.innerText.match(/[\d.]+万?\s*\n?\s*超级会员/) || [''])[0].replace(/\s+/g, ' '));
  const generate_enabled = await page.evaluate(() => [...document.querySelectorAll('button[aria-label="生成"]')]
    .filter(b => b.getBoundingClientRect().width > 0).some(b => !b.disabled));
  await page.screenshot({ path: path.join(dir, 'fill.png') });
  const observed = {
    unit, observed_at: new Date().toISOString(), tab: `${HOME}#omnihuman-${unit}`, generation_POSTs: 0,
    inputs: [image, audio].map(a => ({ path: a.path, sha256: a.sha256 })),
    mode_label: state.mode, model_title, price: state.price, balance_text: balance, balance_precise, generate_enabled,
    rows: state.rows, resolution: state.resolution, vivid: state.vivid,
    image_uploaded: (state.imgs || []).some(i => i.w >= 40 && i.h >= 40), audio_uploaded: /\.wav|00:0\d|\d+(\.\d+)?\s*s|秒/.test(state.text || ''),
    action_text: state.rows && state.rows.action === action ? action : (state.rows ? state.rows.action : null),
    panel: state,
  };
  fs.writeFileSync(path.join(dir, 'fill-observed.json'), JSON.stringify(observed, null, 1) + '\n');
  console.log(JSON.stringify({ unit, mode: observed.mode_label, model_title, price: observed.price, image: observed.image_uploaded,
                               audio: observed.audio_uploaded, rows: state.rows, generate_enabled, resolution: state.resolution, vivid: state.vivid,
                               balance_precise }));
}

// submit: one click on the panel's 生成 button of the unit's open tab, only under an unexpired permit that binds the
// exact observation, after the page is re-read and still shows it. The intent is written (once) before the click; the
// outcome is "submitted" only when the precise balance fell or the page shows the job, otherwise "unknown" (stop).
async function submit(unit) {
  const dir = path.join(TRIAL, unit);
  const permitPath = path.join(dir, 'permit.json'), observedPath = path.join(dir, 'fill-observed.json');
  if (!fs.existsSync(permitPath)) throw Error('no permit');
  if (fs.existsSync(path.join(dir, 'submit-intent.json'))) throw Error('already submitted: a permit is used once');
  const permit = read(permitPath);
  if (new Date(permit.expires_at) < new Date()) throw Error('permit expired');
  if (permit.fill_observed_sha256 !== sha(observedPath)) throw Error('the observation changed after the permit');
  const observed = read(observedPath);
  const browser = await connect();
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url().endsWith(`#omnihuman-${unit}`));
  if (pages.length !== 1) throw Error(`expected one tab for ${unit}, found ${pages.length}`);
  const page = pages[0];
  const now = await page.evaluate(panelState);
  const same = now.mode === observed.mode_label && now.price === observed.price && now.price === permit.price
    && JSON.stringify(now.rows) === JSON.stringify(observed.rows) && now.vivid === observed.vivid;
  if (!same) throw Error('the page no longer shows what was permitted');
  // the panel renders its 生成 button twice at one place (hashed class names): click that place once, after checking
  // that the topmost element there is an enabled 生成 button
  const target = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('button[aria-label="生成"]')].filter(b => b.getBoundingClientRect().width > 0);
    if (!bs.length) return { error: 'no 生成 button' };
    const boxes = new Set(bs.map(b => { const r = b.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round).join(','); }));
    if (boxes.size !== 1) return { error: `生成 buttons at ${boxes.size} places` };
    const r = bs[0].getBoundingClientRect(), cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const hit = document.elementFromPoint(cx, cy)?.closest('button[aria-label="生成"]');
    return hit ? { cx, cy, disabled: hit.disabled, count: bs.length } : { error: 'the 生成 button is covered' };
  });
  if (target.error) throw Error(target.error);
  if (target.disabled) throw Error('the 生成 button is disabled');
  const before = await preciseBalance(browser);
  if (before === null) throw Error('cannot read the balance before');
  fs.writeFileSync(path.join(dir, 'submit-intent.json'), JSON.stringify({ unit, price: permit.price, balance_before: before,
    permit_sha256: sha(permitPath), observed_sha256: sha(observedPath), clicked_at: new Date().toISOString() }, null, 1) + '\n', { flag: 'wx' });
  await page.mouse.click(target.cx, target.cy);
  await page.waitForTimeout(10000);
  const after = await preciseBalance(browser);
  const job = await page.evaluate(() => /生成中|排队|预计|正在生成|造梦中/.test(document.body.innerText));
  await page.screenshot({ path: path.join(dir, 'submitted.png') });
  const outcome = (before !== null && after !== null && after < before) || job ? 'submitted' : 'unknown';
  fs.writeFileSync(path.join(dir, 'submitted.json'), JSON.stringify({ unit, outcome, balance_before: before, balance_after: after,
    charged: after !== null ? before - after : null, job_text_seen: job, observed_at: new Date().toISOString() }, null, 1) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ unit, outcome, balance_before: before, balance_after: after, job_text_seen: job }));
  await browser.close().catch(() => {});
}

// fetch: on the unit's generate workspace (<unit>/job.json), the one finished result video; its card's 下载 button saves
// the file through the browser's download, stored as <unit>/fetch/<sha256>.mp4. No other click.
async function fetchTake(unit) {
  const dir = path.join(TRIAL, unit);
  const job = read(path.join(dir, 'job.json'));
  if (!fs.existsSync(path.join(dir, 'submitted.json')) || read(path.join(dir, 'submitted.json')).outcome !== 'submitted') throw Error('not a submitted unit');
  const browser = await connect();
  const page = browser.contexts().flatMap(c => c.pages()).find(p => p.url().startsWith(job.workspace_url));
  if (!page) throw Error('the workspace tab is not open');
  const vids = await page.evaluate(() => [...document.querySelectorAll('video')].map(v => { const r = v.getBoundingClientRect();
    return { w: v.videoWidth, h: v.videoHeight, dur: v.duration, box: [r.x, r.y, r.width, r.height] }; }).filter(v => v.box[2] > 300 && v.w > 0));
  if (vids.length !== 1) throw Error(`expected one finished result video, found ${vids.length}`);
  const [x, y, w, h] = vids[0].box;
  await page.mouse.move(x + w / 2, y + h / 2);
  await page.waitForTimeout(1000);
  const btn = await page.evaluate(([x, y, w, h]) => {
    const b = [...document.querySelectorAll('[aria-label="下载"]')].map(e => e.getBoundingClientRect())
      .find(r => r.width > 0 && r.x >= x && r.x <= x + w && r.y >= y && r.y <= y + h);
    return b ? { cx: b.x + b.width / 2, cy: b.y + b.height / 2 } : null;
  }, [x, y, w, h]);
  if (!btn) throw Error('no 下载 button on the result card');
  const dl = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);
  await page.mouse.click(btn.cx, btn.cy);
  const d = await dl;
  if (!d) { await page.screenshot({ path: path.join(dir, 'fetch-no-download.png') }); throw Error('no download started (a menu?)'); }
  fs.mkdirSync(path.join(dir, 'fetch'), { recursive: true });
  const tmp = path.join(dir, 'fetch', 'incoming.mp4');
  await d.saveAs(tmp);
  const digest = sha(tmp);
  const dest = path.join(dir, 'fetch', `${digest}.mp4`);
  fs.renameSync(tmp, dest);
  fs.writeFileSync(path.join(dir, 'fetched.json'), JSON.stringify({ unit, file: path.relative(V2, dest), sha256: digest,
    bytes: fs.statSync(dest).size, suggested_name: d.suggestedFilename(), page_video: vids[0], fetched_at: new Date().toISOString() }, null, 1) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ unit, file: path.relative(V2, dest), sha256: digest, suggested: d.suggestedFilename() }));
  await browser.close().catch(() => {});
}

const [action, unit] = process.argv.slice(2);
({ fill, observe, submit, fetch: fetchTake })[action](unit).catch(e => { console.error('ERR', e.message); process.exit(1); });
