// v4 round 6 (2026-11-19): v4r5 (shots6.js) with the closed-eye close-up (SG03C-d1) cut into s012: SG03-w1 sings to the
// 49.087 beat, d1 sings "you're awake" to the 50.4686 beat, then v4r5's crop into the engineer carries the sleep line's
// leap to AWAKE (s012d: SG03-w1's picture at song 50.303 under the same crop) to the 50.933 cut. On the singing face
// only the mono lyric annotation and the console: no big type, nothing over her mouth.
import { console2, lyricMono } from './console2.js';
import { SHOT_FN_V6 } from './shots6.js';
import { W_, clampView } from './shots.js';
import { drawWords } from './type.js';

const SEQ = [2304, 1296];
const PRINT = { uHalftone: 0.085, uCell: 3.0, uGrain: 0.034 };

function s012c(k) {
  const o = k.layers.overlay.ctx;
  console2(k, o, { v5: true, mode: 'thin', lit: 4, sel: true });
  lyricMono(k, o, W_(k, 8), drawWords, { index: 'L08 · CHORUS' });
  return { A: { tex: 'seq', view: clampView(SEQ, [1152, 648, 1.0, 0]), lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT } };
}
// the crop into the engineer: shots6's s012b in its punched state (its shot carries punch = 50.4686)
const s012d = k => SHOT_FN_V6.s012b(k);

export const SHOT_FN_V7 = { ...SHOT_FN_V6, s012c, s012d };
