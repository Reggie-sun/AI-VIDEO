import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const packageRoot = resolve(process.argv[2]);
const reportPath = resolve(process.argv[3]);
const expectedLimit = 32 * 1024 * 1024;
const cwd = mkdtempSync(join(tmpdir(), 'omx-media-stdin-'));
const env = { ...process.env, CODEX_HOME: join(cwd, 'codex-home') };
for (const key of Object.keys(env)) {
  if (key.startsWith('OMX_') || key.startsWith('CODEX_SESSION') || key === 'CODEX_THREAD_ID' || key === 'TMUX' || key === 'TMUX_PANE') delete env[key];
}
mkdirSync(env.CODEX_HOME);
const checks = [];
function run(input) {
  const result = spawnSync(process.execPath, [join(packageRoot, 'dist/scripts/codex-native-hook.js')], {
    input, cwd, env, encoding: 'utf8', timeout: 30_000, maxBuffer: 2 * 1024 * 1024,
  });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stderr, '');
  const lines = result.stdout.trim().split('\n');
  assert.equal(lines.length, 1);
  return JSON.parse(lines[0]);
}
function check(name, fn) {
  try { fn(); checks.push({ name, verdict: 'PASS' }); }
  catch (error) { checks.push({ name, verdict: 'FAIL', reason: error.message.slice(0, 400) }); }
}
function payloadAt(eventName, bytes) {
  const base = JSON.stringify({ hook_event_name: eventName, cwd, tool_name: 'view_image', unicode: '雨😀', padding: '' });
  const input = base.replace('"padding":""', `"padding":"${'x'.repeat(bytes - Buffer.byteLength(base))}"`);
  assert.equal(Buffer.byteLength(input), bytes);
  return input;
}
const images = [
  'referces/shizhen/macro-opening-20261027/full-opening-references-20261027/MC01-normal.png',
  'referces/shizhen/macro-opening-20261027/MC00-photoreal-20261027/01-city-reveal-v1.png',
  'referces/shizhen/macro-opening-20261027/MC00-photoreal-20261027/03-descent-v2.png',
  'referces/shizhen/macro-opening-20261027/MC00-photoreal-20261027/02-eave-start-v1.png',
].map(path => ({ path, bytes: readFileSync(path) }));
const mediaInput = JSON.stringify({ hook_event_name: 'PostToolUse', cwd, tool_name: 'view_image', tool_input: {},
  tool_response: { content: images.map(item => ({ type: 'image', mimeType: 'image/png', data: item.bytes.toString('base64') })) },
});
try {
  check('four actual PNG responses reach normal PostToolUse dispatch', () => {
    const output = run(mediaInput);
    assert.notEqual(output.continue, false);
    assert.equal(output.stopReason, undefined);
  });
  for (const eventName of ['PreToolUse', 'PostToolUse']) {
    for (const size of [expectedLimit - 1, expectedLimit]) {
      check(`${eventName} accepts ${size} UTF-8 bytes`, () => {
        const output = run(payloadAt(eventName, size));
        assert.doesNotMatch(JSON.stringify(output), /oversized/);
      });
    }
    check(`${eventName} rejects ${expectedLimit + 1} UTF-8 bytes`, () => {
      const output = run(payloadAt(eventName, expectedLimit + 1));
      if (eventName === 'PreToolUse') assert.equal(output.hookSpecificOutput?.permissionDecision, 'deny');
      else { assert.equal(output.continue, false); assert.equal(output.stopReason, 'native_hook_stdin_oversized'); }
      assert.match(output.systemMessage, /maxBytes=33554432/);
    });
  }
  check('malformed input above old 1 MiB limit still fails JSON parsing', () => {
    const output = run('{"hook_event_name":"PreToolUse","padding":"' + 'x'.repeat(2 * 1024 * 1024));
    assert.equal(output.hookSpecificOutput?.permissionDecision, 'deny');
    assert.match(output.systemMessage, /malformed JSON/);
    assert.doesNotMatch(output.systemMessage, /oversized/);
  });
  check('small PostToolUse still dispatches', () => {
    const output = run(JSON.stringify({ hook_event_name: 'PostToolUse', cwd, tool_name: 'view_image' }));
    assert.notEqual(output.continue, false);
  });
} finally {
  const report = { schema: 'omx-native-hook-stdin-reproduction/1', package_root: packageRoot,
    expected_limit_bytes: expectedLimit, media_payload_bytes: Buffer.byteLength(mediaInput),
    image_inputs: images.map(({ path, bytes }) => ({ path, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') })),
    checks, passed: checks.every(item => item.verdict === 'PASS'),
    boundary: 'Isolated CLI subprocess tests; no actual host callback or media acceptance claim',
  };
  writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
  rmSync(cwd, { recursive: true, force: true });
  console.log(JSON.stringify({ report: reportPath, passed: report.passed, media_payload_bytes: report.media_payload_bytes, checks }));
  process.exitCode = report.passed ? 0 : 1;
}
