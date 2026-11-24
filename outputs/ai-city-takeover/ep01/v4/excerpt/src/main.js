// IRIS EP01 v4 · finished excerpt (song 26.0528-59.2341 s, Verse 1 + Chorus 1) on HyperFrames. One frame per hf-seek,
// every frame a pure function of its time: the shot's picture (a clip picture conformed to 24 fps, or a 2.5D plate's
// two layers) through its camera and focus, the type and devices of the board drawn on five 2D layers, the gauze grade,
// the crisp overlay on top. Data: data/edl.json (build.py).
import { createGL, draw, program, target, texture, updateTexture, use } from '../../../../../../motion-kit/src/gl.js';
import { DOWN, UP } from '../../../../../../motion-kit/src/shaders.js';
import { canvas2d, reset } from '../../../../../../motion-kit/src/draw2d.js';
import { ticketCard, frameChrome } from './devices.js';
import { BRIGHT, FINAL, SCENE } from './shaders.js';
import { SHOT_FN, fitOf } from './shots.js';
import { SHOT_FN_V2 } from './shots2.js';
import { SHOT_FN_V4 } from './shots4.js';
import { SHOT_FN_DESIGN } from './design.js';
import { SHOT_FN_V5 } from './shots5.js';
import { SHOT_FN_V6 } from './shots6.js';
import { SHOT_FN_V7 } from './shots7.js';
import { SHOT_FN_V8 } from './shots8.js';
import { bakeShot } from './bake.js';
import { openingShot, openingShotV2 } from './opening.js';

const W = 1920, H = 1080;
const OFFSET_DATA = Number(document.getElementById('root')?.dataset?.exOffset || 0);   // sample pages start later
const EDL = document.getElementById('root')?.dataset?.exEdl || 'data/edl.json';         // v2: data/edl-v2.json

// the gauze: one look over clips and plates (per-shot trims in GRADE_TRIM)
const GRADE = {
  uExposure: 1.0, uMist: 0.16, uBloomGain: 0.34, uBloomKnee: 0.32, uHalation: 0.16, uBloomNorm: 0.1667,
  uLift: [0.105, 0.112, 0.118], uLiftAmt: 0.085, uSat: 0.86, uRedKeep: 1.15, uContrast: 0.96, uWarm: 0.35,
  uHalftone: 0.055, uCell: 3.2, uGrain: 0.036, uGrainOverlay: 0.5, uVignette: 0.26, uCA: 0.7, uOvAlpha: 1, uFade: 0, uCoolShadow: 0.5,
};
// v2: the stills already carry the flash look: less veil and lift so faces stay clean, the same bloom, grain, screen
const GRADE_V2 = { uMist: 0.09, uLiftAmt: 0.06, uBloomGain: 0.26, uBloomKnee: 0.4, uHalation: 0.1, uSat: 0.93, uContrast: 1.0,
  uWarm: 0.25, uHalftone: 0.045, uGrain: 0.032 };
const GRADE_TRIM_V2 = {};
// v4r3: the print measured against EV 70-95 s (qa/texture.py): soft base, EV's 4.0 px line screen at its angle,
// misregistration, warmer and more saturated
const GRADE_V4R3 = { uSoft: 1.5, uLine: 0.3, uLinePitch: 4.0, uLineAng: -0.3159, uMisregPx: 0.5, uHalftone: 0.0, uSat: 2.0,
  uWarmBal: 0.22, uGrain: 0.04, uRedKeep: 0.85, uPinkGuard: 1 };
// v4r4: the coordinator's read of crop-compare-v4r3 (too crisp, too cold and grey, screen weak in the lights): the base
// from the half / quarter copies (a low-res photo upscaled), the interface crisp under the print, peach/cream whites,
// warm brown lifted blacks, saturation toward EV's, an AM screen deepest in the mid tones; cold screens kept cold
const GRADE_V4R4 = { uSoft: 0, uSoftMix: 1.0, uSoftQ: 0.45, uOvInPrint: 1, uOvAlpha: 0, uLine: 0, uLineAM: 0.3, uLinePitch: 4.0,
  uLineAng: -0.3159, uMisregPx: 0.6, uHalftone: 0, uSat: 1.85, uWarmBal: 0.14, uWarm: 0.55, uCoolShadow: 0,
  uSoftE: 0, uShadowTint: [1.10, 0.98, 0.84], uLift: [0.16, 0.11, 0.075], uLiftAmt: 0.075, uColdGuard: 1, uRedCap: 0.62, uRedKeep: 1.5,
  uPinkGuard: 0, uGrain: 0.035, uGrainOverlay: 1 };
// v4r8: the viewing-scale softness (qa/grad.py; the pictures carry depth of field from prep_dof.py): highlights bloom out
// warm (a Pro-Mist-like halation), a veil that lowers local contrast, the structure softened a notch further
const GRADE_V4R8 = { uMist: 0.38, uMistLocal: 0.25, uBloomGain: 0.6, uBloomKnee: 0.22, uHalation: 0.34, uSoftQ: 0.85,
  uSat: 1.85, uWarmBal: 0.21 };
// v4r9: a third of v4r8's depth of field (prep_dof.py --v9), the rest of the softness uniform over the whole frame
const GRADE_V4R9 = { uSoftQ: 1.0, uMist: 0.62, uMistLocal: 0.1, uSoftE: 0, uVignette: 0.45 };
// v4r10: v4r9 with EV's tonal range (qa/grad.py quantiles p2/p10/p50/p90): deeper blacks, brighter lights; the veil kept
// to the mid tones and the lights (it no longer lifts the blacks)
const GRADE_V4R10 = { uToneOn: 1, uToneBP: 0.016, uToneWP: 0.69, uToneG: 1.3, uMistLocal: 0.6, uMist: 0.75,
  uWarmBal: 0.13, uWarm: 0.45, uSoftE: 0.25, uSat: 1.75 };
// v4r11 (2026-11-20, blur_study/REPORT.md): EV's softness is per shot, not one layer over every shot. The uniform
// softening goes (no quarter / eighth copies; the half-size copy only, a picture shown from half its resolution, not
// a Gaussian), the veil and the bloom only round the light sources; tone curve, warmth, red caps, AM screen,
// misregistration and grain as v4r10c. Per shot (GRADE_V4R11_SHOT): the chorus's closed-eye close-up (s012c) darker
// and flatter, as EV's S0054 / S0056 / S0063.
const GRADE_V4R11 = { uSoftMix: 1.0, uSoftQ: 0.4, uSoftE: 0, uMist: 0.07, uMistLocal: 1, uBloomGain: 0.3, uBloomKnee: 0.35,
  uHalation: 0.14 };
const GRADE_V4R11_SHOT = { s012c: { uToneBP: -0.012, uToneWP: 1.2 } };
// design frames (2026-11-19, Codex r3 section 3): less grey, deeper garage black, mist only round the light sources
const GRADE_DESIGN = { uMist: 0.07, uMistLocal: 1, uLiftAmt: 0.035, uLift: [0.06, 0.065, 0.075], uBloomGain: 0.3, uBloomKnee: 0.35,
  uHalation: 0.14, uSat: 1.04, uRedKeep: 1.1, uContrast: 1.05, uWarm: 0.3, uHalftone: 0.04, uGrain: 0.03 };
const GRADE_TRIM = {
  s007: { uExposure: 0.95 }, s008: { uExposure: 1.0 }, s009: { uExposure: 0.95 }, s010: { uExposure: 1.12 },
  s011: { uExposure: 1.05 }, s012: { uExposure: 1.06 }, s013: { uExposure: 1.0 }, s014: { uExposure: 1.02 },
};

async function loadImage(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`load ${url}: ${res.status}`);
  return createImageBitmap(await res.blob(), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}
async function loadFonts(manifestUrl) {
  const m = await (await fetch(manifestUrl)).json();
  for (const f of m.faces) {
    const face = new FontFace(f.family, `url(fonts/${f.file})`);
    await face.load();
    document.fonts.add(face);
  }
  await document.fonts.ready;
}
const search = (arr, s) => { let lo = 0, hi = arr.length - 1, ans = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (arr[m] <= s) { ans = m; lo = m + 1; } else hi = m - 1; } return ans; };

async function boot() {
  const canvas = document.getElementById('stage');
  const { gl, info } = createGL(canvas);
  const D = await (await fetch(EDL)).json();
  // D.bake: the Agentcut stills (bake.js), every shot through the one StillMove camera
  // D.opening: the opening's Seedance takes (opening.js), every shot shown whole through the v4r11 print
  // D.opening_v2: opening v2 (opening.js openingShotV2: stills, digital pushes)
  const FNS = D.opening_v2 ? Object.fromEntries(D.shots.map(x => [x.id, openingShotV2])) : D.opening ? Object.fromEntries(D.shots.map(x => [x.id, openingShot])) : D.bake ? Object.fromEntries(D.shots.map(x => [x.id, bakeShot])) : D.version === 'design' ? SHOT_FN_DESIGN : D.version >= 10 ? SHOT_FN_V8 : D.version >= 9 ? SHOT_FN_V7 : D.version >= 8 ? SHOT_FN_V6 : D.version >= 5 ? SHOT_FN_V5 : D.version >= 4 ? { ...SHOT_FN_V2, ...SHOT_FN_V4 } : D.version >= 2 ? SHOT_FN_V2 : SHOT_FN;
  await loadFonts('fonts/fonts.json');
  const FPS = D.fps, OFF = D.offset;
  const tex = {}, size = {};
  for (const [k, url] of Object.entries(D.images)) {
    const img = await loadImage(url);
    tex[k] = texture(gl, img, { mipmap: true });
    size[k] = [img.width, img.height];
    img.close();
  }
  // one texture for the clip pictures, refilled per frame
  const seqShot = D.shots.find(s => s.seq);
  if (seqShot) {
    const seq0 = await loadImage(`${seqShot.seq.dir}/0000.jpg`);
    tex.seq = texture(gl, seq0, { mipmap: true });
    size.seq = [seq0.width, seq0.height];
    seq0.close();
  }
  let shownSeq = null;
  let seqSize = size.seq;                 // v4r11: the shown picture's own size (s012d's picture is the 4K take's)
  async function showSeq(shot, i) {
    const key = `${shot.id}/${i}`;
    if (shownSeq === key) return;
    const img = await loadImage(`${shot.seq.dir}/${String(i).padStart(4, '0')}.jpg`);
    gl.bindTexture(gl.TEXTURE_2D, tex.seq);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    if (D.version >= 16) seqSize = [img.width, img.height];
    img.close();
    shownSeq = key;
  }
  const layers = { overlay: canvas2d(W, H), feed: canvas2d(W, H), feedBack: canvas2d(W, H), surf: canvas2d(W, H), emit: canvas2d(W, H) };
  const ltex = {};
  for (const [k, l] of Object.entries(layers)) ltex[k] = texture(gl, l.c, { mipmap: false });
  const prog = { scene: program(gl, SCENE, 'scene'), bright: program(gl, BRIGHT, 'bright'), down: program(gl, DOWN, 'down'),
    up: program(gl, UP, 'up'), final: program(gl, FINAL, 'final') };
  const rt = { scene: target(gl, W, H, { float: info.floatRT }) };
  const chain = [];
  let w = W >> 1, h = H >> 1;
  for (let i = 0; i < 6; i++) { chain.push(target(gl, Math.max(w, 8), Math.max(h, 8), { float: info.floatRT })); w >>= 1; h >>= 1; }
  const ups = chain.map(c => target(gl, c.w, c.h, { float: info.floatRT }));

  // lyric words by line; beat helpers
  const lines = {};
  for (const l of D.lines) lines[l.id] = l.words.map((w, i) => ({ ...w, li: l.id, wi: i }));
  const beats = D.beats, snares = D.snare, downbeats = D.downbeats;
  const fo = ts => Math.round((ts - OFF) * FPS);
  const beatIndexFloat = s => {
    const i = search(beats, s);
    if (i < 0) return (s - beats[0]) / (beats[1] - beats[0]);
    const nx = i + 1 < beats.length ? beats[i + 1] : beats[i] + (beats[i] - beats[i - 1]);
    return i + (s - beats[i]) / (nx - beats[i]);
  };
  const beatLen = s => { const i = Math.max(0, search(beats, s)); return beats[i + 1] - beats[i]; };
  let marks = [];

  async function renderFrame(t) {
    const fr = Math.round((t + OFFSET_DATA) * FPS);
    // design frames: render frame fr shows its own song time; the timeline state (ticket, flap, words) is read at the
    // excerpt frame of that time
    const s = D.frame_song ? D.frame_song[fr] : OFF + fr / FPS;
    const f = D.frame_song ? fo(s) : fr;
    for (const l of Object.values(layers)) reset(l.ctx);
    marks = [];
    const shot = D.shots.find(x => fr >= x.f0 && fr < x.f1) || D.shots[D.shots.length - 1];
    const sixteenthLen = ts => beatLen(ts) / 4;
    const k = {
      f, s, fo, layers, shot, version: D.version || 1, data: D,
      mark: (li, wi) => marks.push(`${li}:${wi}`),
      line: li => lines[li] || [],
      track: id => (D.tracks[id] ? D.tracks[id][Math.min(D.tracks[id].length - 1, f - shot.f0)] : null),
      beatIndexFloat,
      beatsBetween: (a, b) => Math.round(beatIndexFloat(b) - beatIndexFloat(a)),
      sixteenthLen,
      sixteenthsBetween: (a, b) => Math.max(0, Math.floor((beatIndexFloat(b) - beatIndexFloat(a)) * 4 + 1e-6)),
      sixteenthAt: (a, j) => { let ts = a; for (let q = 0; q < j; q++) ts += sixteenthLen(ts); return ts; },
      snareTimes: (a, b) => snares.filter(x => x >= a - 1e-6 && x < b),
      snaresBetween: (a, b) => snares.filter(x => x >= a - 1e-6 && x < b && fo(x) <= f).length,
      barNo: () => 1 + search(downbeats, s + 1e-6),
    };
    const p = FNS[shot.id](k);
    // chrome over every shot
    const o = layers.overlay.ctx;
    if (p.chrome !== false) {
      ticketCard(k, o, { accent: shot.chapter === 'c3' ? '#E8E4DA' : '#F2B134' });
      frameChrome(k, o);
    }
    if (D.picture_only) reset(o);          // v4r10c-picture / bake: the picture alone, the overlay layer left empty
    // v2: shot.hold = { f, idx }: from frame f the shot shows its prepared picture idx (s004's handset frame)
    const seqIdx = shot.hold && f >= shot.hold.f ? shot.hold.idx : shot.seq?.fixed ?? ((shot.freeze_f ? Math.min(f, shot.freeze_f) : f) - shot.f0);
    if (p.A.tex === 'seq') await showSeq(shot, seqIdx);
    if (p.underPrint && D.version < 7) {
      // the interface and the type go under the grade, the halftone and the grain with the picture (design v2)
      layers.feed.ctx.save(); layers.feed.ctx.setTransform(1, 0, 0, 1, 0, 0);
      layers.feed.ctx.drawImage(layers.overlay.c, 0, 0); layers.feed.ctx.restore();
      reset(layers.overlay.ctx);
    }
    for (const [kk, l] of Object.entries(layers)) updateTexture(gl, ltex[kk], l.c);

    const A = p.A, B = p.B;
    const rows = p.rows;
    // v4r11: a clip picture larger than the shot's view was set for: the same view, scaled to the picture's own pixels
    let aSize = size[A.tex], aView = A.view;
    if (D.version >= 16 && A.tex === 'seq' && seqSize[0] !== size.seq[0]) {
      const r = seqSize[0] / size.seq[0];
      aSize = seqSize; aView = [A.view[0] * r, A.view[1] * r, A.view[2], A.view[3]];
    }
    use(gl, prog.scene, {
      uRes: [W, H], uTime: t, uFrame: f,
      uASize: aSize, uViewA: aView, uFitA: fitOf(aSize), uLodA: A.lod || 0, uGainA: A.gain ?? 1,
      uBSize: B ? size[B.tex] : [1, 1], uViewB: B ? B.view : [0, 0, 1, 0], uFitB: B ? fitOf(size[B.tex]) : 1, uLodB: B?.lod || 0,
      uBOn: B ? 1 : 0, uGainB: B?.gain ?? 1,
      uShake: p.shake || [0, 0],
      uRowsOn: rows ? (rows.procedural ? 2 : 1) : 0, uRowGain: rows ? rows.gain : [1, 1, 1, 1], uAmbient: rows ? rows.ambient : 1, uDark: rows ? rows.dark : 1,
      uAmbDark: rows?.ambDark ?? (rows ? rows.dark : 1), uLevels: (D.levels || {})[A.tex === 'seq' ? shot.id : A.tex] || [0, 1, 0],
      uKey: p.key || [0.6, 0.8], uEmitGain: p.emitGain ?? 1.6, uTint: p.tint || [1, 1, 1],
    }, { uA: tex[A.tex], uB: B ? tex[B.tex] : tex[A.tex], uRows: (rows && tex[rows.tex || 'p011-rows']) || tex[A.tex], uFeedBack: ltex.feedBack,
      uFeed: ltex.feed, uSurf: ltex.surf, uEmit: ltex.emit });
    draw(gl, rt.scene);
    use(gl, prog.bright, { uRes: [chain[0].w, chain[0].h] }, { uScene: rt.scene.tex });
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
    const grade = D.version >= 7 ? { ...GRADE, ...GRADE_DESIGN, ...(p.grade || {}), ...GRADE_V4R4, ...(D.version >= 11 ? GRADE_V4R8 : {}), ...(D.version >= 12 ? GRADE_V4R9 : {}), ...(D.version >= 13 ? GRADE_V4R10 : {}), ...(D.version >= 14 ? { uRedCapPost: 0.42 } : {}), ...(D.version >= 15 && shot.id === 's013a' ? { uRedCapPost: 0.30 } : {}), ...(D.version >= 16 ? { ...GRADE_V4R11, ...(GRADE_V4R11_SHOT[shot.id] || {}) } : {}), ...(p.grade7 || {}) }   // v4r10c: 0.30 on the phone insert's skin
      : D.version >= 6 ? { ...GRADE, ...GRADE_DESIGN, ...(p.grade || {}), ...GRADE_V4R3, ...(p.grade6 || {}) }
      : D.version === 'design' || D.version >= 5 ? { ...GRADE, ...GRADE_DESIGN, ...(p.grade || {}) } : D.version >= 2 ? { ...GRADE, ...GRADE_V2, ...(GRADE_TRIM_V2[shot.id] || {}), ...(p.grade || {}) }
      : { ...GRADE, ...(GRADE_TRIM[shot.id] || {}), ...(p.grade || {}) };
    // v2 (2026-11-21): the shot's screen (shot.screen) and its one-frame events (shot.fx[].grade) merged last; absent
    // in every earlier EDL, so earlier versions render as before
    // v3 (2026-11-21): the shot's blur class (shot.blur from opening_v2.py --build-3; A: the uniform softening taken down,
    // D: soft, darker, flatter) merged before the screen; absent in every earlier EDL
    if (shot.blur?.grade) Object.assign(grade, shot.blur.grade);
    if (shot.screen) Object.assign(grade, shot.screen);
    for (const e of shot.fx || []) if (f >= e.f0 && f < e.f1 && e.grade) Object.assign(grade, e.grade);
    // v2 uniforms reset every frame (a uniform keeps its last value; 0 is their default, so earlier versions are unchanged)
    use(gl, prog.final, { uRes: [W, H], uTime: t, uFrame: f, uDotAM: 0, uMosaic: 0, uDither: 0, uBlack: 0, ...grade }, { uScene: rt.scene.tex, uBloom: ups[0].tex, uOverlay: ltex.overlay, uHalf: chain[0].tex, uQuarter: chain[1].tex, uEighth: chain[2].tex });
    draw(gl, null);
    gl.finish();
    window.__exMarks = { f, s, shot: shot.id, words: [...new Set(marks)], still: A.tex, view: aView, shake: p.shake || [0, 0],
      src: A.tex === 'seq' ? `${shot.seq.dir}/${String(seqIdx).padStart(4, '0')}.jpg` : D.images[A.tex], size: aSize };
  }
  window.__ex = { ready: true, info };
  return { renderFrame };
}

const ready = boot().catch(err => { window.__exError = String(err && err.stack || err); document.title = 'EX-ERROR'; throw err; });
let queue = ready;
const render = t => { const run = queue.then(r => r.renderFrame(t)); queue = run.then(() => ready, () => ready); return run; };
window.addEventListener('hf-seek', e => { e.detail.waitUntil(render(e.detail.time)); });
window.__exRender = render;
