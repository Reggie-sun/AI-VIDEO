import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, symlink, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { createRunsApiHandler, RunsApiError } from "../scripts/runs-api.mjs";

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sealedReviewRequest(artifactSha256) {
  const semantic = {
    attempt_id: "attempt-1",
    source_shot_id: "shot-source",
    target_shot_id: "shot-target",
    target_shot_content_hash: "4".repeat(64),
    resolved_generation_hash: "5".repeat(64),
    artifact_sha256: artifactSha256,
    continuity_constraints_hash: "6".repeat(64),
    qa_policy_content_hash: "7".repeat(64),
    automatic_evaluator: { name: "continuity-cuda", version: "1" },
    required_reviewer: { name: "continuity-human", version: "1" },
    media_identity: `sha256:${artifactSha256}`,
  };
  return {
    ...semantic,
    content_hash: createHash("sha256").update(canonicalJson({ schema: "human-continuity-review-request/1", ...semantic })).digest("hex"),
  };
}

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

test("continuity review is GET-only, no-store, exact-bound, and rejects tampered projections", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-api-"));
  const media = path.join(root, "runs", "demo", "candidate.mp4");
  const bytes = Buffer.from("exact-continuity-video");
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  await mkdir(path.dirname(media), { recursive: true });
  await writeFile(media, bytes);
  const calls = [];
  const projection = {
    workspace: "demo/project.yaml",
    attempt_id: "attempt-1",
    review_request: sealedReviewRequest(sha256),
    media: { token: "continuity-token", mime_type: "video/mp4", bytes: bytes.length, sha256 },
    _media: { "continuity-token": { source_path: media, mime_type: "video/mp4", bytes: bytes.length, sha256 } },
  };
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async (...args) => { calls.push(args); return projection; },
  });

  const review = await invoke(handler, request("GET", "/api/runs/continuity-review?workspace=demo%2Fproject.yaml&attempt=attempt-1"));
  assert.equal(review.res.statusCode, 200);
  assert.equal(review.res.headers.get("cache-control"), "no-store");
  assert.deepEqual(calls, [["continuity-review", "demo/project.yaml", "attempt-1"]]);
  assert.equal(review.res.body.toString().includes("source_path"), false);
  assert.equal(review.res.body.toString().includes(media), false);
  const served = await invoke(handler, request("GET", "/api/runs/media/continuity-token"));
  assert.equal(served.res.statusCode, 200);
  assert.deepEqual(served.res.body, bytes);

  const method = await invoke(handler, request("POST", "/api/runs/continuity-review?workspace=demo%2Fproject.yaml&attempt=attempt-1"));
  assert.equal(method.res.statusCode, 405);
  assert.equal(method.res.headers.get("allow"), "GET");

  const tamperedHandler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      ...projection,
      review_request: { ...projection.review_request, target_shot_id: "shot-other" },
    }),
  });
  const tampered = await invoke(tamperedHandler, request("GET", "/api/runs/continuity-review?workspace=demo%2Fproject.yaml&attempt=attempt-1"));
  assert.equal(tampered.res.statusCode, 503);
  assert.equal(tampered.res.body.toString().includes("shot-other"), false);

  const wrongBytesHandler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      ...projection,
      _media: {
        "continuity-token": {
          ...projection._media["continuity-token"],
          sha256: createHash("sha256").update(Buffer.alloc(bytes.length, "x")).digest("hex"),
        },
      },
    }),
  });
  const wrongBytes = await invoke(wrongBytesHandler, request("GET", "/api/runs/continuity-review?workspace=demo%2Fproject.yaml&attempt=attempt-1"));
  assert.equal(wrongBytes.res.statusCode, 503);
  const unavailableMedia = await invoke(wrongBytesHandler, request("GET", "/api/runs/media/continuity-token"));
  assert.equal(unavailableMedia.res.statusCode, 404);

  const missingShaHandler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => {
      const { sha256: _omitted, ...entry } = projection._media["continuity-token"];
      return { ...projection, _media: { "continuity-token": entry } };
    },
  });
  const missingSha = await invoke(missingShaHandler, request("GET", "/api/runs/continuity-review?workspace=demo%2Fproject.yaml&attempt=attempt-1"));
  assert.equal(missingSha.res.statusCode, 503);

  const staleTargetHandler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ ...projection, attempt_id: "attempt-other" }),
  });
  const staleTarget = await invoke(staleTargetHandler, request("GET", "/api/runs/continuity-review?workspace=demo%2Fproject.yaml&attempt=attempt-1"));
  assert.equal(staleTarget.res.statusCode, 503);
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
