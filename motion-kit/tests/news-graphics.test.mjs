import test from 'node:test';
import assert from 'node:assert/strict';
import { CACHE_MECHANISMS, dateIntervals, drawDnsRoute, drawResearchPause, drawCacheDistinction, drawWebCache, drawCpuCache } from '../src/news-graphics.js';

function recorder() {
  const ops = [], target = {};
  for (const method of ['save', 'restore', 'scale', 'fillRect', 'strokeRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fillText']) {
    target[method] = (...args) => ops.push([method, ...args]);
  }
  return { ops, ctx: new Proxy(target, { set(o, k, v) { ops.push(['set', k, v]); o[k] = v; return true; } }) };
}
const texts = ops => ops.filter(x => x[0] === 'fillText').map(x => x[1]);

test('pause represents 11 elapsed intervals across month boundary, not 12 inclusive dates', () => {
  const days = dateIntervals();
  assert.equal(days.length, 11);
  assert.deepEqual(days[0], { from: '2026-09-20', to: '2026-09-21' });
  assert.deepEqual(days.at(-1), { from: '2026-09-30', to: '2026-10-01' });
  for (let i = 1; i < days.length; i++) assert.equal(days[i - 1].to, days[i].from);
  assert.equal(dateIntervals('2024-02-28', '2024-03-01').length, 2);
  for (const end of ['2026-02-30', '2026-09-20', '2026-01-01']) assert.throws(() => dateIntervals('2026-09-20', end), RangeError);
});

test('cache facts describe separate storage and experiment mechanisms', () => {
  assert.match(CACHE_MECHANISMS.web.kind, /WEB/);
  assert.match(CACHE_MECHANISMS.cpu.kind, /CPU/);
  const r = recorder(); drawCacheDistinction(r.ctx, { progress: 1 });
  const output = texts(r.ops).join('|');
  for (const label of ['离线网页缓存', '处理器缓存侧信道', '另一项受控红队测试', '事件发生前已存在']) assert.ok(output.includes(label));
});

test('DNS and pause scope qualifications remain on screen at every animation progress', () => {
  for (const progress of [0, .25, .75, 1]) {
    let r = recorder(); drawDnsRoute(r.ctx, { progress });
    assert.ok(texts(r.ops).includes('有限联网'));
    assert.ok(texts(r.ops).some(t => t.includes('不代表获得不受限')));
    r = recorder(); drawResearchPause(r.ctx, { progress });
    assert.ok(texts(r.ops).includes('并非所有 AI 或 ChatGPT 服务停运'));
  }
});

test('draws are independent of evaluation order and preserve caller context', () => {
  for (const draw of [drawDnsRoute, drawResearchPause, drawCacheDistinction, drawWebCache, drawCpuCache]) {
    const a = recorder(); draw(a.ctx, { width: 1280, height: 720, progress: .6 });
    const other = recorder(); draw(other.ctx, { progress: .9 }); draw(other.ctx, { progress: 0 });
    const b = recorder(); draw(b.ctx, { width: 1280, height: 720, progress: .6 });
    assert.deepEqual(b.ops, a.ops);
    assert.deepEqual(a.ops[0], ['save']); assert.deepEqual(a.ops.at(-1), ['restore']);
    assert.deepEqual(a.ops[1], ['scale', 1280 / 1920, 720 / 1080]);
    assert.throws(() => draw(a.ctx, { progress: NaN }), RangeError);
  }
});


test('individual cache cards retain their separate scope', () => {
  let r = recorder(); drawWebCache(r.ctx);
  assert.ok(texts(r.ops).includes('网页缓存方案在该事件前已存在'));
  assert.ok(!texts(r.ops).some(t => t.includes('红队')));
  r = recorder(); drawCpuCache(r.ctx);
  assert.ok(texts(r.ops).includes('另一项受控红队测试'));
  assert.ok(texts(r.ops).includes('非网页缓存；相关漏洞已修补'));
});
