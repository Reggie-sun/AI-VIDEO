import test from 'node:test';
import assert from 'node:assert/strict';
import { Clock } from '../src/clock.js';
import { IMPACT, PUNCH, protectCentre, trackZoom } from '../src/beatcam.js';

const FPS = 30;
const near = (actual, expected, epsilon = 1e-9) => {
  assert.ok(Math.abs(actual - expected) <= epsilon, `${actual} != ${expected}`);
};
const beats = { beats: [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5], downbeats: [0, 2, 4] };
const flat = v => Array.from({ length: 24 * 6 }, () => v);
const clock = ({ kick = [2.0, 3.01], low = flat(1) } = {}) => new Clock(beats, { kick, env24: { low } }, { fps: FPS });
const z = (c, f, spec) => trackZoom(f / FPS, c, spec);

test('the camera holds outside its sections, even on a kick or a hit', () => {
  const c = clock();
  const spec = { sections: [[2.5, 4]], impacts: [2.0] };
  for (const f of [0, 59, 60, 61, 70, 74]) assert.equal(z(c, f, spec), 1);
  assert.equal(z(c, 120, spec), 1);                          // the section ends at 4 s
});

test('a punch shows at most one frame before its kick and never after it', () => {
  const c = clock();
  const spec = { sections: [[1.5, 4]] };
  for (const kick of [2.0, 3.01]) {
    let jump = null;
    for (let f = Math.round((kick - 0.4) * FPS); f <= Math.round((kick + 0.2) * FPS); f++) {
      if (z(c, f, spec) > z(c, f - 1, spec) + 1e-6) { jump = f; break; }
    }
    assert.ok(jump !== null, `no punch near ${kick}`);
    assert.ok(jump / FPS <= kick + 1e-9, `punch at ${jump / FPS} trails the kick ${kick}`);
    assert.ok(jump / FPS > kick - 1 / FPS - 1e-9, `punch at ${jump / FPS} leads the kick ${kick} by more than a frame`);
  }
  near(trackZoom(2.0 - 1 / FPS, c, spec), 1 + PUNCH.amp);    // full amplitude on the leading frame
  near(trackZoom(2.0 - 1 / FPS + PUNCH.decay, c, spec), 1 + PUNCH.amp * Math.exp(-1));
});

test('a kick before the section never carries into it', () => {
  const c = clock({ kick: [1.49, 3.01] });
  const spec = { sections: [[1.5, 4]] };
  assert.equal(trackZoom(1.5, c, spec), 1);
  assert.equal(trackZoom(1.6, c, spec), 1);
});

test('the drum envelope gates the punch', () => {
  const quiet = clock({ low: flat(PUNCH.gateLo - 0.05) });
  const loud = clock({ low: flat(PUNCH.gateHi) });
  const spec = { sections: [[1.5, 4]] };
  assert.equal(trackZoom(2.0, quiet, spec), 1);
  near(trackZoom(2.0 - 1 / FPS, loud, spec), 1 + PUNCH.amp);
});

test('an impact on a kick is one impact: the larger move wins, the two never add up', () => {
  const c = clock();
  const spec = { sections: [[1.5, 4]], impacts: [2.0] };
  near(trackZoom(2.0 - 1 / FPS, c, spec), 1 + IMPACT.amp);
  near(trackZoom(2.0 - 1 / FPS + IMPACT.decay, c, spec), 1 + IMPACT.amp * Math.exp(-1));
  near(trackZoom(2.0 - 1 / FPS, c, { ...spec, impact: null }), 1 + PUNCH.amp);
  near(trackZoom(2.0 - 1 / FPS, c, { ...spec, punch: null, impacts: [] }), 1);
});

test('the same time gives the same frame', () => {
  const c = clock();
  const spec = { sections: [[1.5, 4]], impacts: [3.01] };
  for (const t of [1.5, 2.0, 2.37, 3.0, 3.5]) assert.equal(trackZoom(t, c, spec), trackZoom(t, clock(), spec));
});

test('a protected rect stays inside the frame at any zoom the device makes', () => {
  const W = 1920, H = 1080, mark = [25, 26, 152, 70];
  for (const zoom of [1, 1.02, 1.06, 1.08, 1.1]) {
    const [cx, cy] = protectCentre(W / 2, H / 2, zoom, [mark], W, H);
    const x0 = (mark[0] - cx) * zoom + W / 2, y0 = (mark[1] - cy) * zoom + H / 2;
    const x1 = (mark[0] + mark[2] - cx) * zoom + W / 2, y1 = (mark[1] + mark[3] - cy) * zoom + H / 2;
    assert.ok(x0 >= -1e-9 && y0 >= -1e-9 && x1 <= W + 1e-9 && y1 <= H + 1e-9, `mark leaves the frame at ${zoom}`);
  }
  assert.deepEqual(protectCentre(W / 2, H / 2, 1.02, [mark], W, H), [W / 2, H / 2]);   // already fits: unchanged
  const face = [1500, 600, 300, 400];                                                    // two rects: both kept
  const [cx, cy] = protectCentre(W / 2, H / 2, 1.08, [mark, face], W, H);
  for (const [x, y, w, h] of [mark, face]) {
    assert.ok((x - cx) * 1.08 + W / 2 >= -1e-9 && (x + w - cx) * 1.08 + W / 2 <= W + 1e-9);
    assert.ok((y - cy) * 1.08 + H / 2 >= -1e-9 && (y + h - cy) * 1.08 + H / 2 <= H + 1e-9);
  }
});
