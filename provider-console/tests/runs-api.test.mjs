import assert from "node:assert/strict";
import { mkdtemp, mkdir, symlink, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { createRunsApiHandler, RunsApiError } from "../scripts/runs-api.mjs";

function request(method, url, headers = {}) {
  return { method, url, headers, socket: { remoteAddress: "127.0.0.1" } };
}

function response() {
  const headers = new Map();
  const chunks = [];
  return {
    headers,
    chunks,
    statusCode: 200,
    setHeader(name, value) { headers.set(name.toLowerCase(), value); },
    end(chunk) { if (chunk) chunks.push(Buffer.from(chunk)); this.finished = true; },
    write(chunk) { chunks.push(Buffer.from(chunk)); },
    get body() { return Buffer.concat(chunks); },
  };
}

async function invoke(handler, req) {
  const res = response();
  let nextCalled = false;
  await handler(req, res, () => { nextCalled = true; });
  return { res, nextCalled };
}

test("catalog and detail are GET-only, no-store, and sanitize internal media paths", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-api-"));
  const media = path.join(root, "runs", "demo", "output.mp4");
  await mkdir(path.dirname(media), { recursive: true });
  await writeFile(media, "0123456789");
  const calls = [];
  const runProjector = async (command, workspace) => {
    calls.push([command, workspace]);
    if (command === "catalog") return { boundary: { read_only: true }, workspaces: [{ workspace: "demo/project.yaml" }] };
    return {
      workspace,
      attempts: [{ id: "attempt-1", media: { token: "opaque-token", mime_type: "video/mp4" } }],
      _media: { "opaque-token": { source_path: media, mime_type: "video/mp4", bytes: 10 } },
    };
  };
  const handler = createRunsApiHandler({ repoRoot: root, runProjector });

  const catalog = await invoke(handler, request("GET", "/api/runs"));
  assert.equal(catalog.res.statusCode, 200);
  assert.equal(catalog.res.headers.get("cache-control"), "no-store");
  assert.deepEqual(JSON.parse(catalog.res.body), { boundary: { read_only: true }, workspaces: [{ workspace: "demo/project.yaml" }] });

  const detail = await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));
  assert.equal(detail.res.statusCode, 200);
  assert.equal(detail.res.body.toString().includes("source_path"), false);
  assert.equal(detail.res.body.toString().includes(media), false);
  assert.deepEqual(calls.at(-1), ["detail", "demo/project.yaml"]);

  const method = await invoke(handler, request("POST", "/api/runs"));
  assert.equal(method.res.statusCode, 405);
  assert.equal(method.res.headers.get("allow"), "GET");
});

test("detail rejects missing or traversal workspace keys and projector failures are sanitized", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-api-"));
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => { throw new Error("secret=/private/token raw traceback"); },
  });

  const missing = await invoke(handler, request("GET", "/api/runs/detail"));
  assert.equal(missing.res.statusCode, 400);
  const traversal = await invoke(handler, request("GET", "/api/runs/detail?workspace=..%2Fsecret"));
  assert.equal(traversal.res.statusCode, 400);
  const failure = await invoke(handler, request("GET", "/api/runs"));
  assert.equal(failure.res.statusCode, 503);
  assert.deepEqual(JSON.parse(failure.res.body), {
    error: { code: "RUNS_SOURCE_UNAVAILABLE", message: "本地 runs 数据源不可用。" },
  });
  assert.equal(failure.res.body.toString().includes("secret"), false);

  const detailFailure = await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));
  assert.equal(detailFailure.res.statusCode, 503);
  assert.equal(detailFailure.res.body.toString().includes("secret"), false);

  const unknownHandler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => { throw new RunsApiError(404, "WORKSPACE_NOT_FOUND"); },
  });
  const unknown = await invoke(unknownHandler, request("GET", "/api/runs/detail?workspace=missing%2Fproject.yaml"));
  assert.equal(unknown.res.statusCode, 404);
  assert.deepEqual(JSON.parse(unknown.res.body), {
    error: { code: "WORKSPACE_NOT_FOUND", message: "workspace 不存在。" },
  });
});

test("media endpoint serves only cached registered tokens and supports HEAD and byte ranges", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-api-"));
  const media = path.join(root, "runs", "demo", "output.mp4");
  await mkdir(path.dirname(media), { recursive: true });
  await writeFile(media, "0123456789");
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      workspace: "demo/project.yaml",
      attempts: [],
      _media: { token123: { source_path: media, mime_type: "video/mp4", bytes: 10 } },
    }),
  });
  await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));

  const ranged = await invoke(handler, request("GET", "/api/runs/media/token123", { range: "bytes=2-5" }));
  assert.equal(ranged.res.statusCode, 206);
  assert.equal(ranged.res.body.toString(), "2345");
  assert.equal(ranged.res.headers.get("content-range"), "bytes 2-5/10");
  assert.equal(ranged.res.headers.get("content-type"), "video/mp4");

  const head = await invoke(handler, request("HEAD", "/api/runs/media/token123"));
  assert.equal(head.res.statusCode, 200);
  assert.equal(head.res.body.length, 0);
  assert.equal(head.res.headers.get("content-length"), 10);

  const unknown = await invoke(handler, request("GET", "/api/runs/media/unknown"));
  assert.equal(unknown.res.statusCode, 404);

  const outside = path.join(root, "outside.mp4");
  await writeFile(outside, "outside-bytes");
  await unlink(media);
  await symlink(outside, media);
  const swapped = await invoke(handler, request("GET", "/api/runs/media/token123"));
  assert.equal(swapped.res.statusCode, 503);
  assert.equal(swapped.res.body.toString().includes(outside), false);
  const swappedHead = await invoke(handler, request("HEAD", "/api/runs/media/token123"));
  assert.equal(swappedHead.res.statusCode, 503);

  await unlink(media);
  await writeFile(media, "abcdefghij");
  const sameSizeReplacement = await invoke(handler, request("GET", "/api/runs/media/token123"));
  assert.equal(sameSizeReplacement.res.statusCode, 503);
});

test("non-api requests pass through to Vite", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-api-"));
  const handler = createRunsApiHandler({ repoRoot: root, runProjector: async () => ({}) });
  const result = await invoke(handler, request("GET", "/src/main.jsx"));
  assert.equal(result.nextCalled, true);
  assert.equal(result.res.finished, undefined);
});

test("runs API rejects non-loopback clients before invoking the projector", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-api-"));
  let called = false;
  const handler = createRunsApiHandler({ repoRoot: root, runProjector: async () => { called = true; return {}; } });
  const req = { ...request("GET", "/api/runs"), socket: { remoteAddress: "192.168.1.50" } };
  const result = await invoke(handler, req);
  assert.equal(result.res.statusCode, 403);
  assert.equal(called, false);

  const missingAddress = await invoke(handler, { ...request("GET", "/api/runs"), socket: {} });
  assert.equal(missingAddress.res.statusCode, 403);
  assert.equal(called, false);
});
