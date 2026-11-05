import test from 'node:test';
import assert from 'node:assert/strict';
import { Clock } from '../src/clock.js';
import { applyH, fbm1, hash1, hash2, hash3, invert3, noise1, squareToQuad } from '../src/math.js';

const near = (actual, expected, epsilon = 1e-9) => {
  assert.ok(Math.abs(actual - expected) <= epsilon, `${actual} != ${expected}`);
};
const beatMap = {
  beats: [0, 0.5, 1, 1.5, 2, 2.6, 3.2, 3.8, 4.4, 4.8, 5.2, 5.6, 6],
  downbeats: [0, 2, 4.4, 6],
};
const clock = () => new Clock(beatMap, {
  kick: [2.6, 3.8], hits: [{ t: 4.4 }],
}, { offset: 2, windowBar0: 1, fps: 30 });

test('window-relative bars and beat subdivisions follow changing tempo', () => {
  const c = clock();
  near(c.at(0), 0);
  near(c.at(0, 1), 0.6);
  near(c.at(0, 2, 0.5), 1.5);
  near(c.at(1), 2.4);
  near(c.at(1, 1, 0.5), 3);
  const beat = c.beat(1.5);
  assert.equal(beat.idx, 6);
  near(beat.frac, 0.5);
  near(beat.len, 0.6);
  const bar = c.bar(1.2);
  assert.equal(bar.idx, 0);
  near(bar.frac, 0.5);
  near(c.comp(c.song(1.75)), 1.75);
});

test('cuts land on the first frame at or after the requested time', () => {
  const c = clock();
  for (const frame of [0, 1, 38, 120, 180, 195, 299]) {
    const time = frame / 30;
    assert.ok(c.frameOf(time) === frame);
    near(c.quant(time), time);
    if (frame > 0) assert.equal(c.frameOf(time - 0.00001), frame);
    assert.equal(c.frameOf(time + 0.00001), frame + 1);
    assert.ok(c.quant(time + 0.00001) >= time + 0.00001);
  }
});

test('events remain silent before onset, peak exactly at onset, and decay', () => {
  const c = clock();
  assert.equal(c.last([], 10), null);
  assert.equal(c.last(undefined, 10), null);
  assert.equal(c.last([2.6, 3.8], 0.59), null);
  near(c.last([2.6, 3.8], 0.6), 0.6);
  assert.equal(c.pulse('kick', 0.59), 0);
  near(c.pulse('kick', c.at(0, 1)), 1);
  assert.ok(c.pulse('kick', 0.7) > c.pulse('kick', 0.8));
  assert.equal(c.pulse('missing', 1), 0);
  assert.equal(c.pulse('impact', 2.39), 0);
  near(c.pulse('impact', c.at(1)), 1);
});

test('a decimal event still peaks on its exact rendered frame with a song offset', () => {
  // 0.6s is frame 18 at 30fps; offset subtraction must not turn onset into silence.
  near(clock().pulse('kick', 18 / 30), 1);
});

test('hash and noise values do not depend on frame evaluation order', () => {
  const sample = frame => [hash1(frame), hash2(frame, 7), hash3(frame, 7, 11),
    noise1(frame / 30, 7), fbm1(frame / 30, 7)];
  const frames = [-30, -1, 0, 1, 38, 120, 180, 195, 299];
  const sequential = new Map(frames.map(f => [f, sample(f)]));
  for (const f of [195, 0, -30, 299, 1, 180, -1, 120, 38]) {
    const values = sample(f);
    assert.deepEqual(values, sequential.get(f));
    for (const x of values.slice(0, 3)) assert.ok(Number.isFinite(x) && x >= 0 && x < 1);
    for (const x of values.slice(3)) assert.ok(Number.isFinite(x) && x >= -1 && x <= 1);
  }
  assert.ok(new Set(frames.map(hash1)).size > 1);
  for (const x of [-2, -1, 0, 1, 2]) near(noise1(x - 1e-6, 7), noise1(x + 1e-6, 7), 1e-7);
});

test('perspective projection places corners and the diagonal intersection correctly', () => {
  const quad = [[0, 0], [4, 0], [3, 2], [1, 2]];
  const h = squareToQuad(quad);
  for (const [i, uv] of [[0, [0, 0]], [1, [1, 0]], [2, [1, 1]], [3, [0, 1]]]) {
    const point = applyH(h, ...uv);
    near(point[0], quad[i][0]); near(point[1], quad[i][1]);
  }
  const middle = applyH(h, 0.5, 0.5);
  near(middle[0], 2); near(middle[1], 4 / 3);
});

test('screen homography round trips interior points through a measured oblique screen', () => {
  const h = squareToQuad([[1028, 490], [1631, 519], [1626, 710], [1009, 667]]);
  const inverse = invert3(h);
  for (const uv of [[0, 0], [1, 1], [0.5, 0.5], [0.1, 0.9], [0.8, 0.2]]) {
    const actual = applyH(inverse, ...applyH(h, ...uv));
    near(actual[0], uv[0]); near(actual[1], uv[1]);
  }
});
