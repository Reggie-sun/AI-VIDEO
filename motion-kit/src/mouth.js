// Sung stills: the replacement-mouth method of 2D animation. A still that a vocal sings through steps, frame by frame,
// between plates that differ from it only at the mouth or the eyes (tools/region_plates.py), on the measured words.
// Every value is a pure function of t.
//
// cfg (the comp's mouth.json): words: { word: [[shape, fraction of the word], ...] } (lower case, letters and
// apostrophes); lead_frames: the mouth is formed this many frames before the sound (animation practice);
// min_hold_frames: a shorter shape gives way to the next one; rest_gap_s: a pause at least this long closes the mouth;
// blinks: [start s] (half-closed, closed, closed, half-closed), only where the mouth rests.

export const REST = 'X';
export const OPEN = 'O';
const OPEN_HALF = [['C', 0]];                                    // a word the table does not know

const key = text => text.toLowerCase().replace(/[^a-z']/g, '');

export function mouthKeys(lines, cfg, fps = 30) {
  const words = lines.flatMap(l => l.words);
  const raw = [];
  words.forEach((w, i) => {
    const shapes = cfg.words[key(w.text)] || OPEN_HALF;
    const dur = w.end - w.start;
    for (const [shape, f] of shapes) raw.push([w.start + f * dur, shape]);
    const next = words[i + 1];
    if (!next || next.start - w.end >= cfg.rest_gap_s) raw.push([w.end, REST]);
  });
  const lead = cfg.lead_frames / fps, hold = cfg.min_hold_frames / fps - 1e-9;
  const keys = [];
  for (const [t, shape] of raw.sort((a, b) => a[0] - b[0])) {
    const at = t - lead, last = keys[keys.length - 1];
    if (last && at - last[0] < hold) last[1] = shape;            // too short to read: the later shape takes its place
    else if (!last || last[1] !== shape) keys.push([at, shape]);
  }
  return keys;
}

export function shapeAt(keys, t) {
  let shape = REST;
  for (const [at, s] of keys) {
    if (at <= t + 1e-9) shape = s;
    else break;
  }
  return shape;
}

const BLINK = ['H', 'C', 'C', 'H'];
export function eyeAt(blinks, t, fps = 30) {
  for (const b of blinks) {
    const i = Math.floor((t - b) * fps + 1e-6);
    if (i >= 0 && i < BLINK.length) return BLINK[i];
  }
  return OPEN;
}

// a blink frame needs the resting mouth: there is no plate with both changed
export function checkBlinks(keys, blinks, fps = 30) {
  for (const b of blinks) {
    for (let i = 0; i < BLINK.length; i++) {
      const t = b + i / fps;
      if (shapeAt(keys, t) !== REST) throw new Error(`blink at ${b} s meets mouth ${shapeAt(keys, t)} at ${t.toFixed(3)} s`);
    }
  }
}

// plate names follow region_plates.py: <base>m<shape>, <base>e<eye>; the base itself rests
export function sungPlate(t, base, keys, blinks = [], fps = 30) {
  const eye = eyeAt(blinks, t, fps);
  if (eye !== OPEN) return `${base}e${eye}`;
  const shape = shapeAt(keys, t);
  return shape === REST ? base : `${base}m${shape}`;
}
