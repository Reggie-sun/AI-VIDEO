import test from 'node:test';
import assert from 'node:assert/strict';
import { OPEN, REST, checkBlinks, eyeAt, mouthKeys, shapeAt, sungPlate } from '../src/mouth.js';

const FPS = 30;
const cfg = {
  words: { run: [['F', 0], ['D', 0.1], ['B', 0.9]], "didn't": [['B', 0], ['C', 0.5]] },
  lead_frames: 2, min_hold_frames: 2, rest_gap_s: 0.12, blinks: [],
};
const lines = [{ words: [{ text: "Didn't", start: 1.0, end: 1.3 }, { text: 'run.', start: 1.32, end: 2.32 }] },
               { words: [{ text: 'outside', start: 3.0, end: 3.6 }] }];
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test('each shape is formed lead_frames before its sound', () => {
  const keys = mouthKeys(lines, cfg, FPS);
  near(keys[0][0], 1.0 - 2 / FPS);
  assert.equal(keys[0][1], 'B');
  assert.equal(shapeAt(keys, 1.0 - 3 / FPS), REST);                 // nothing before the first word
  assert.equal(shapeAt(keys, 1.15), 'C');                           // didn't: B then C halfway
});

test('a pause of rest_gap_s or more closes the mouth, a shorter one does not', () => {
  const keys = mouthKeys(lines, cfg, FPS);
  assert.notEqual(shapeAt(keys, 1.31 - 2 / FPS), REST);              // 0.02 s between didn't and run
  assert.equal(shapeAt(keys, 2.5), REST);                           // 0.68 s after run
  assert.equal(shapeAt(keys, 9), REST);                             // after the last word
});

test('a shape shorter than min_hold_frames gives way to the next one', () => {
  const keys = mouthKeys(lines, cfg, FPS);
  for (let i = 1; i < keys.length; i++) assert.ok(keys[i][0] - keys[i - 1][0] >= 2 / FPS - 1e-9, JSON.stringify(keys));
  // run.: F lasts 0.1 s, didn't's last shape C (from 1.15) runs into it; no key repeats its predecessor
  for (let i = 1; i < keys.length; i++) assert.notEqual(keys[i][1], keys[i - 1][1]);
});

test('a word the table does not know opens half-way; case and punctuation are ignored', () => {
  const keys = mouthKeys(lines, cfg, FPS);
  assert.equal(shapeAt(keys, 3.3), 'C');                            // outside is not in cfg.words
  assert.equal(shapeAt(keys, 1.5), 'D');                            // 'run.' matched 'run'
});

test('a blink is half, closed, closed, half for one frame each', () => {
  const b = [5.0];
  assert.deepEqual([-1, 0, 1, 2, 3, 4].map(i => eyeAt(b, 5.0 + i / FPS, FPS)), [OPEN, 'H', 'C', 'C', 'H', OPEN]);
});

test('a blink must fall where the mouth rests', () => {
  const keys = mouthKeys(lines, cfg, FPS);
  assert.doesNotThrow(() => checkBlinks(keys, [2.6], FPS));
  assert.throws(() => checkBlinks(keys, [1.5], FPS), /blink at 1.5/);
});

test('the plate is the base at rest, <base>m<shape> while singing, <base>e<eye> while blinking', () => {
  const keys = mouthKeys(lines, cfg, FPS);
  assert.equal(sungPlate(0.5, 'K7', keys, [2.6], FPS), 'K7');
  assert.equal(sungPlate(1.5, 'K7', keys, [2.6], FPS), 'K7mD');
  assert.equal(sungPlate(2.6 + 1 / FPS, 'K7', keys, [2.6], FPS), 'K7eC');
});
