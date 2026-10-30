// Frame runtime for HyperFrames. One render per `hf-seek`: every frame is a pure function of
// comp time t. Scenes return GL parameters and draw into four software 2D canvases:
//   overlay (crisp readable type), feed (in-image signal: OSD/detectors), emit (light), ui (screen).
import { Clock } from './clock.js';
import { createGL, draw, program, target, texture, updateTexture, use } from './gl.js';
import { BRIGHT, DOWN, FINAL, SCENE, UP } from './shaders.js';
import { canvas2d, loadFonts, reset } from './draw2d.js';

async function loadImage(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`load ${url}: ${res.status}`);
  return createImageBitmap(await res.blob(), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}
async function loadJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`load ${url}: ${res.status}`);
  return res.json();
}

const DEFAULT_GRADE = {
  uExposure: 1.0, uBloomGain: 0.55, uHalation: 0.35, uLift: [0.043, 0.059, 0.078], uLiftAmt: 0.06,
  uHalftone: 0.10, uCell: 4.0, uGrain: 0.035, uGrainOverlay: 0.45, uVignette: 0.32, uCA: 0.25,
  uMisreg: 0, uFlash: 0, uFade: 0, uSat: 0.86, uRedKeep: 1.12, uWeave: [0, 0], uFeedGain: 0.92,
};

export async function boot(cfg) {
  const W = cfg.width, H = cfg.height;
  const canvas = document.getElementById(cfg.canvasId || 'stage');
  const { gl, info } = createGL(canvas);
  await loadFonts(cfg.fontsUrl);
  const [beats, hits] = await Promise.all([loadJSON(cfg.beatsUrl), loadJSON(cfg.hitsUrl)]);
  const music = cfg.musicUrl ? await loadJSON(cfg.musicUrl) : {};
  const data = {};
  for (const [k, url] of Object.entries(cfg.data || {})) data[k] = await loadJSON(url);
  const tex = {}, size = {};
  for (const [k, spec] of Object.entries(cfg.images)) {
    const img = await loadImage(spec.url);
    tex[k] = texture(gl, img, { mipmap: spec.mipmap !== false });
    size[k] = [img.width, img.height];
  }
  const layers = {
    overlay: canvas2d(W, H), feed: canvas2d(W, H), emit: canvas2d(W, H),
    ui: canvas2d(cfg.uiSize?.[0] || 1268, cfg.uiSize?.[1] || 400),
  };
  const ltex = {};
  for (const [k, l] of Object.entries(layers)) ltex[k] = texture(gl, l.c, { mipmap: false });
  const prog = {
    scene: program(gl, SCENE, 'scene'), bright: program(gl, BRIGHT, 'bright'),
    down: program(gl, DOWN, 'down'), up: program(gl, UP, 'up'), final: program(gl, FINAL, 'final'),
  };
  const rt = { scene: target(gl, W, H, { float: info.floatRT }) };
  const chain = [];
  let w = W >> 1, h = H >> 1;
  for (let i = 0; i < 5; i++) { chain.push(target(gl, Math.max(w, 8), Math.max(h, 8), { float: info.floatRT })); w >>= 1; h >>= 1; }
  const ups = chain.map(c => target(gl, c.w, c.h, { float: info.floatRT }));
  const clock = new Clock(beats, hits, { offset: music.song_offset ?? 0, windowBar0: music.window_bar0 ?? 0, fps: cfg.fps });
  const ctx = { W, H, fps: cfg.fps, clock, data, size, layers, info };
  window.__mk = { info, scenes: Object.keys(cfg.scenes), music, ready: true };

  function renderFrame(t) {
    const frame = Math.round(t * cfg.fps);
    for (const l of Object.values(layers)) reset(l.ctx);
    const shot = cfg.pickShot(t, clock, data);
    const scene = cfg.scenes[shot.id];
    const p = scene(t, { ...ctx, frame, shot, t0: shot.t0, t1: shot.t1 });
    for (const [k, l] of Object.entries(layers)) updateTexture(gl, ltex[k], l.c);

    // scene pass
    const plate = p.plate;
    use(gl, prog.scene, {
      uRes: [W, H], uTime: t, uFrame: frame, uPlateSize: size[plate], uView: p.view, uFit: p.fit,
      uShake: p.shake || [0, 0], uPlateGain: p.plateGain ?? 1, uPlateTint: p.plateTint || [1, 1, 1],
      uFogA: p.fogA || [0, 1, 0, 0], uFogB: p.fogB || [0, 1, 0, 0], uFogTint: p.fogTint || [0.05, 0.07, 0.09], uFogLift: p.fogLift ?? 0.2,
      uLN: p.lights?.n || 0, uLP: p.lights?.p || new Float32Array(96), uLC: p.lights?.c || new Float32Array(96),
      uSN: p.segs?.n || 0, uSA: p.segs?.a || new Float32Array(256), uSW: p.segs?.w || new Float32Array(128), uSColor: p.segs?.color || [1, 0.1, 0.05],
      uBN: p.bodies?.n || 0, uBP: p.bodies?.p || new Float32Array(48), uBA: p.bodies?.a || new Float32Array(12),
      uEmitGain: p.emitGain ?? 0,
      uScreenOn: p.screen ? 1 : 0, uScreenH: p.screen?.H || [1, 0, 0, 0, 1, 0, 0, 0, 1], uScreenGain: p.screen?.gain ?? 1,
      uSpillColor: p.screen?.spillColor || [0.6, 0.75, 0.95], uSpill: p.screen?.spill ?? 0,
      uScreenCenter: p.screen?.center || [0, 0], uScreenRadius: p.screen?.radius || 1,
      uMaskOn: p.mask ? 1 : 0, uSweep: p.sweep || [1, 0, -9999, 1], uSweepGain: p.sweepGain || 0, uFlowVP: p.flowVP || [0, 0, 1],
      uTrailOn: 0, uBeatPos: 0, uLambda: 1, uPulseGain: 0, uFlashGain: 0, uTrailColor: [1, 0.1, 0.05],
    }, { uPlate: tex[plate], uUI: ltex.ui, uMask: p.mask ? tex[p.mask] : tex[plate], uEmit: ltex.emit, uFlow: tex[plate] });
    draw(gl, rt.scene);

    // bloom chain
    use(gl, prog.bright, { uRes: [chain[0].w, chain[0].h], uThreshold: p.bloomThreshold ?? 0.9, uKnee: 0.5,
      uOverlayGlow: p.overlayGlow ?? 0.12, uFeedGlow: p.feedGlow ?? 0.25 },
    { uScene: rt.scene.tex, uOverlay: ltex.overlay, uFeed: ltex.feed });
    draw(gl, chain[0]);
    for (let i = 1; i < chain.length; i++) {
      use(gl, prog.down, { uRes: [chain[i].w, chain[i].h], uSrcTexel: [1 / chain[i - 1].w, 1 / chain[i - 1].h] }, { uSrc: chain[i - 1].tex });
      draw(gl, chain[i]);
    }
    let src = chain[chain.length - 1];
    for (let i = chain.length - 2; i >= 0; i--) {
      use(gl, prog.up, { uRes: [ups[i].w, ups[i].h], uSrcTexel: [1 / src.w, 1 / src.h], uRadius: 1.0 }, { uSrc: src.tex, uBase: chain[i].tex });
      draw(gl, ups[i]);
      src = ups[i];
    }

    // final
    const grade = { ...DEFAULT_GRADE, ...(p.grade || {}) };
    use(gl, prog.final, { uRes: [W, H], uTime: t, uFrame: frame, ...grade },
      { uScene: rt.scene.tex, uBloom: ups[0].tex, uOverlay: ltex.overlay, uFeed: ltex.feed });
    draw(gl, null);
    gl.finish();
  }
  return { renderFrame, info, clock };
}

export function install(cfg) {
  const ready = boot(cfg).catch(err => {
    window.__mkError = String(err && err.stack || err);
    document.title = 'MK-ERROR';
    throw err;
  });
  window.addEventListener('hf-seek', e => {
    const t = e.detail.time;
    e.detail.waitUntil(ready.then(r => r.renderFrame(t)));
  });
  window.__mkRender = t => ready.then(r => r.renderFrame(t));
  return ready;
}
