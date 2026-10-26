// Actual encoded output at 1x; verifies playback, not human audio acceptance.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('/home/reggie/.npm/_npx/e78b33305587cb7c/node_modules/playwright');
(async () => {
  const file = path.resolve(__dirname, '../focus-002/失帧-两位-关键事件重剪-002.mp4');
  const browser = await chromium.launch({
    executablePath: '/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome',
    headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required']
  });
  const page = await browser.newPage({viewport: {width: 1280, height: 800}});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(file).href);
  await page.waitForFunction(() => document.querySelector('video')?.readyState >= 2);
  const begin = Date.now();
  await page.evaluate(async () => {
    const v = document.querySelector('video');
    v.pause(); v.currentTime = 0; v.playbackRate = 1; v.muted = false; v.volume = 1;
    window.samples = [];
    const sample = (now, m) => {
      window.samples.push({mediaTime: m.mediaTime, presentedFrames: m.presentedFrames});
      if (!v.ended) v.requestVideoFrameCallback(sample);
    };
    v.requestVideoFrameCallback(sample);
    await v.play();
  });
  for (const t of [7.5, 7.8, 8.5, 10.4, 10.6, 11.1, 17]) {
    await page.waitForFunction(t => document.querySelector('video').currentTime >= t, t);
    await page.screenshot({path: path.join(__dirname, `playback-${t}.png`)});
  }
  await page.waitForFunction(() => document.querySelector('video').ended);
  const evidence = await page.evaluate(() => {
    const v = document.querySelector('video');
    return {ended: v.ended, duration: v.duration, currentTime: v.currentTime,
      playbackRate: v.playbackRate, muted: v.muted, volume: v.volume,
      width: v.videoWidth, height: v.videoHeight, error: v.error,
      quality: v.getVideoPlaybackQuality().toJSON?.() || {
        totalVideoFrames: v.getVideoPlaybackQuality().totalVideoFrames,
        droppedVideoFrames: v.getVideoPlaybackQuality().droppedVideoFrames},
      samples: window.samples};
  });
  const report = {source: file, elapsedWallMs: Date.now() - begin, errors,
    evidence, browser: await browser.version(),
    proof: 'Browser 1x playback only. Not human viewing/listening acceptance.'};
  fs.writeFileSync(path.join(__dirname, 'browser-playback-002.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({...report, evidence: {...evidence, samples: evidence.samples.length}}));
  await browser.close();
})().catch(e => {console.error(e.message);process.exitCode = 1;});
