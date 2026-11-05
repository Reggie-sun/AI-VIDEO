// Drive the user's logged-in Suno create page (Chrome profile cp-e7be810d639e, DevTools port 19232) for IRIS EP01.
//   node outputs/ai-city-takeover/ep01/v2/song-suno/suno_ui.cjs fill|observe|submit <n>
// fill:    Advanced mode, v6, lyrics/style/exclude/title from fields.json, Female vocal, Max Mode off, My Taste off. No submit.
// observe: read the form back and compare with fields.json exactly; writes ui/observe-<n>.json + screenshot.
// submit:  only after an observe that matches; writes ui/submit-<n>-intent.json first, clicks "Create song" once,
//          then reports captcha_pending (a human verification appeared: the user clicks it, nothing is retried),
//          submitted (new "Looked Outside" rows appeared) or unknown. A unit with an intent is never clicked again.
// Never solves a captcha, never deletes or edits library clips.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');

const HERE = __dirname;
const UI = path.join(HERE, 'ui');
const F = JSON.parse(fs.readFileSync(path.join(HERE, 'fields.json'), 'utf8'));
const norm = s => (s || '').replace(/\u00a0/g, ' ').replace(/[ \t]+\n/g, '\n').replace(/\n{2,}/g, '\n').trim();
const sha = s => crypto.createHash('sha256').update(s).digest('hex');

async function page() {
  const b = await chromium.connectOverCDP('http://127.0.0.1:19232', { timeout: 10000 });
  // our own tab (marked #iris-ep01), so another client's use of the user's Suno tab is never disturbed
  let p = b.contexts().flatMap(c => c.pages()).find(x => x.url().includes('#iris-ep01'));
  if (!p) {
    p = await b.contexts()[0].newPage();
    await p.goto('https://suno.com/create#iris-ep01', { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(6000);
  }
  return [b, p];
}

async function pickToggle(p, rowLabel, choice) {
  // a settings row: its label text, then Off/On (or Male/Female) buttons on the same line
  const ok = await p.evaluate(([rowLabel, choice]) => {
    const lab = [...document.querySelectorAll('div,span,label,p')].find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === rowLabel);
    if (!lab) return 'no row';
    const y = lab.getBoundingClientRect().y;
    const btn = [...document.querySelectorAll('button,[role="button"]')].find(e => e.innerText.trim() === choice && Math.abs(e.getBoundingClientRect().y - y) < 30);
    if (!btn) return 'no button';
    const sel = e => getComputedStyle(e).backgroundColor === 'rgba(255, 255, 255, 0.1)';   // the selected segment is lit
    if (!sel(btn)) btn.click();                                                             // idempotent: a second click would deselect
    return 'ok';
  }, [rowLabel, choice]);
  if (ok !== 'ok') throw Error(`${rowLabel}/${choice}: ${ok}`);
}

async function read(p) {
  return p.evaluate(() => {
    const vis = e => e && e.getBoundingClientRect().width > 0 && e.getBoundingClientRect().height > 0;
    const q = s => [...document.querySelectorAll(s)].find(vis) || null;
    const lyr = q('[aria-label="Lyrics editor"]');
    const style = q('textarea[aria-label="Styles"]');
    const ex = q('input[placeholder="Exclude styles"]');
    const title = q('input[placeholder="Song Title (Optional)"]');
    const rowState = label => {
      const lab = [...document.querySelectorAll('div,span,label,p')].find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === label);
      if (!lab) return null;
      const y = lab.getBoundingClientRect().y;
      return [...document.querySelectorAll('button,[role="button"]')].filter(e => Math.abs(e.getBoundingClientRect().y - y) < 30)
        .filter(e => ['Male', 'Female', 'Off', 'On'].includes(e.innerText.trim()))
        .map(e => ({ t: e.innerText.trim(), on: getComputedStyle(e).backgroundColor === 'rgba(255, 255, 255, 0.1)' }));
    };
    const model = [...document.querySelectorAll('button')].find(e => /^v\d/.test(e.innerText.trim()));
    const adv = [...document.querySelectorAll('button,[role="tab"]')].find(e => e.innerText.trim() === 'Advanced');
    return {
      lyrics: lyr ? lyr.innerText : null, style: style ? style.value : null, exclude: ex ? ex.value : null, title: title ? title.value : null,
      model: model ? model.innerText.trim() : null, advanced: adv ? (adv.getAttribute('aria-pressed') || adv.getAttribute('aria-selected')) : null,
      gender: rowState('Vocal Gender'), max_mode: rowState('Max Mode'), my_taste: rowState('My Taste'),
      create_enabled: (() => { const c = [...document.querySelectorAll('button')].find(e => (e.getAttribute('aria-label') || '') === 'Create song'); return c ? !c.disabled : null; })(),
      captcha: [...document.querySelectorAll('iframe')].some(f => /captcha|challenges\.cloudflare|turnstile/i.test(f.src || '')) || /verify you are human/i.test(document.body.innerText),
      looked_outside_rows: (document.body.innerText.match(/Looked Outside/g) || []).length,
    };
  });
}

async function fill(p) {
  const adv = p.getByRole('button', { name: 'Advanced', exact: true });
  if (await adv.count()) await adv.first().click();
  const lyr = p.locator('[aria-label="Lyrics editor"]:visible');
  await lyr.click();
  await p.keyboard.press('Control+A');
  await p.keyboard.press('Delete');
  const lines = F.lyrics.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i]) await p.keyboard.insertText(lines[i]);
    if (i < lines.length - 1) await p.keyboard.press('Enter');
  }
  await p.locator('textarea[aria-label="Styles"]:visible').fill(F.style);
  const ex = p.locator('input[placeholder="Exclude styles"]:visible');
  if (!(await ex.isVisible())) await p.getByText('More Options', { exact: true }).click();
  await ex.fill(F.exclude);
  await pickToggle(p, 'Vocal Gender', 'Female');
  await pickToggle(p, 'Max Mode', 'Off');
  await pickToggle(p, 'My Taste', 'Off');
  await p.locator('input[placeholder="Song Title (Optional)"]:visible').fill(F.title);
}

function compare(r) {
  return {
    lyrics: norm(r.lyrics) === norm(F.lyrics), style: r.style === F.style, exclude: r.exclude === F.exclude, title: r.title === F.title,
    model_v6: /^v6\b/.test(r.model || ''), create_enabled: r.create_enabled === true, no_captcha_on_page: !r.captcha,
    female: !!(r.gender || []).find(x => x.t === 'Female' && x.on), max_mode_off: !!(r.max_mode || []).find(x => x.t === 'Off' && x.on),
    my_taste_off: !!(r.my_taste || []).find(x => x.t === 'Off' && x.on),
  };
}

(async () => {
  const [mode, n] = process.argv.slice(2);
  fs.mkdirSync(UI, { recursive: true });
  const [b, p] = await page();
  try {
    if (mode === 'fill') {
      await fill(p);
      console.log(JSON.stringify({ filled: true }));
    } else if (mode === 'observe') {
      const r = await read(p);
      const checks = compare(r);
      const out = { n, at: new Date().toISOString(), fields_sha256: F.sha256, read: { ...r, lyrics: r.lyrics && r.lyrics.slice(0, 120) + '…', lyrics_sha256: r.lyrics && sha(norm(r.lyrics)) },
                    checks, pass: Object.values(checks).every(Boolean) };
      fs.writeFileSync(path.join(UI, `observe-${n}.json`), JSON.stringify(out, null, 1) + '\n');
      await p.screenshot({ path: path.join(UI, `observe-${n}.png`), timeout: 8000 }).catch(() => {});
      console.log(JSON.stringify({ n, pass: out.pass, checks, gender: r.gender, max_mode: r.max_mode, my_taste: r.my_taste, model: r.model }));
    } else if (mode === 'submit') {
      const intent = path.join(UI, `submit-${n}-intent.json`);
      if (fs.existsSync(intent)) throw Error(`unit ${n} already has an intent; never click twice`);
      const obs = JSON.parse(fs.readFileSync(path.join(UI, `observe-${n}.json`), 'utf8'));
      if (!obs.pass) throw Error('last observe did not pass');
      const before = await read(p);
      if (!compare(before).lyrics || before.captcha) throw Error('form changed since observe, or a captcha is showing');
      fs.writeFileSync(intent, JSON.stringify({ n, at: new Date().toISOString(), fields_sha256: F.sha256, rows_before: before.looked_outside_rows }, null, 1) + '\n');
      await p.locator('button[aria-label="Create song"]:visible').click();
      let outcome = 'unknown', after = null;
      for (let i = 0; i < 20; i++) {
        await p.waitForTimeout(1500);
        after = await read(p);
        if (after.captcha) { outcome = 'captcha_pending'; break; }
        if (after.looked_outside_rows > before.looked_outside_rows) { outcome = 'submitted'; break; }
      }
      await p.screenshot({ path: path.join(UI, `submit-${n}.png`), timeout: 8000 }).catch(() => {});
      const res = { n, outcome, at: new Date().toISOString(), rows_before: before.looked_outside_rows, rows_after: after && after.looked_outside_rows };
      fs.writeFileSync(path.join(UI, `submit-${n}-result.json`), JSON.stringify(res, null, 1) + '\n');
      console.log(JSON.stringify(res));
    } else if (mode === 'close') {
      if (p.url().includes('#iris-ep01')) await p.close();
      console.log(JSON.stringify({ closed: true }));
    } else throw Error('mode: fill|observe|submit|close <n>');
  } finally {
    await b.close().catch(() => {});
  }
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
