import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, rename, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { createRunsApiHandler } from "../scripts/runs-api.mjs";

function request(method, url) {
  return { method, url, headers: {}, socket: { remoteAddress: "127.0.0.1" } };
}

function response() {
  const headers = new Map();
  const chunks = [];
  return {
    headers,
    statusCode: 200,
    setHeader(name, value) { headers.set(name.toLowerCase(), value); },
    end(chunk) { if (chunk) chunks.push(Buffer.from(chunk)); this.finished = true; },
    get body() { return Buffer.concat(chunks); },
  };
}

async function invoke(handler, req) {
  const res = response();
  await handler(req, res, () => {});
  return res;
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

test("opening a video folder uses registered tokens and rejects stale, missing, cross-site and arbitrary paths", async (t) => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-folder-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const mediaRoot = path.join(root, "runs", "demo");
  const externalRoot = path.join(root, "external");
  await Promise.all([mkdir(mediaRoot, { recursive: true }), mkdir(externalRoot)]);
  const bytes = Buffer.from("exact-video");
  const source = path.join(mediaRoot, "video.mp4");
  const external = path.join(externalRoot, "video.mp4");
  await Promise.all([writeFile(source, bytes), writeFile(external, bytes)]);
  const descriptor = (source_path) => ({ source_path, mime_type: "video/mp4", bytes: bytes.length, sha256: sha256(bytes) });
  const calls = [];
  let openerFails = false;
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ _media: { "video-token": descriptor(source) } }),
    externalSources: [{ id: "external", root: externalRoot }],
    externalCatalog: async () => ({ _media: { "external-token": { ...descriptor(external), source_id: "external" } } }),
    openFolder: async (directory) => { if (openerFails) throw new Error("private desktop diagnostic"); calls.push(directory); },
  });
  await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));
  await invoke(handler, request("GET", "/api/external-media"));
  const action = (url, overrides = {}) => ({ ...request("POST", url), headers: {
    host: "127.0.0.1:5174", origin: "http://127.0.0.1:5174", "x-ai-video-action": "open-media-folder", "sec-fetch-site": "same-origin",
  }, ...overrides });
  const url = "/api/runs/media/video-token/open-folder";
  const opened = await invoke(handler, action(url));
  assert.equal(opened.statusCode, 200);
  assert.deepEqual(JSON.parse(opened.body), { opened: true });
  assert.doesNotMatch(opened.body.toString(), /source_path|\/tmp\//);
  assert.equal((await invoke(handler, action("/api/external-media/media/external-token/open-folder"))).statusCode, 200);
  assert.deepEqual(calls, [mediaRoot, externalRoot]);
  for (const req of [
    action(url, { method: "GET" }), action(url, { headers: {} }),
    action(url, { headers: { host: "127.0.0.1:5174", origin: "https://evil.example", "x-ai-video-action": "open-media-folder" } }),
    action(url, { socket: { remoteAddress: "192.0.2.1" } }),
    action(`${url}?path=/tmp`), action("/api/runs/media/unknown-token/open-folder"),
  ]) assert.ok((await invoke(handler, req)).statusCode >= 400);
  assert.equal(calls.length, 2, "denied requests never invoke the desktop opener");
  openerFails = true;
  const failed = await invoke(handler, action(url));
  assert.equal(failed.statusCode, 503);
  assert.equal(JSON.parse(failed.body).error.code, "FOLDER_OPEN_FAILED");
  assert.doesNotMatch(failed.body.toString(), /private desktop diagnostic|\/tmp\//);
  openerFails = false;
  await writeFile(source, Buffer.from("other-video"));
  assert.equal((await invoke(handler, action(url))).statusCode, 409);
  await writeFile(external, "changed-external");
  assert.equal((await invoke(handler, action("/api/external-media/media/external-token/open-folder"))).statusCode, 404);
  await rename(source, `${source}.old`);
  await symlink(`${source}.old`, source);
  assert.equal((await invoke(handler, action(url))).statusCode, 409);
  await rm(source);
  assert.equal((await invoke(handler, action(url))).statusCode, 409);
  assert.equal(calls.length, 2);
});

test("detail keeps valid media while invalid descriptors become unavailable and evict cached tokens", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-library-media-"));
  const mediaRoot = path.join(root, "runs", "demo");
  const goodBytes = Buffer.from("good-video");
  const originalBytes = Buffer.from("original-video");
  const goodPath = path.join(mediaRoot, "good.mp4");
  const reusedPath = path.join(mediaRoot, "reused.mp4");
  const wrongPath = path.join(mediaRoot, "wrong.mp4");
  const missingPath = path.join(mediaRoot, "missing.mp4");
  await mkdir(mediaRoot, { recursive: true });
  await Promise.all([
    writeFile(goodPath, goodBytes),
    writeFile(reusedPath, originalBytes),
    writeFile(wrongPath, "wrong-video"),
  ]);
  const descriptor = (source_path, bytes, digest) => ({
    source_path, mime_type: "video/mp4", bytes, sha256: digest,
  });
  const projection = () => ({
    workspace: "demo/project.yaml",
    attempts: [{
      candidate_media: { token: "good-token", asset_id: "good", mime_type: "video/mp4" },
      fetched_media: { token: "reused-token", mime_type: "video/mp4" },
      candidate_media_items: [
        { role: "candidate", asset_id: "good", media: { token: "good-token", mime_type: "video/mp4" } },
        { role: "candidate", asset_id: "wrong", media: { token: "wrong-token", mime_type: "video/mp4" } },
        { role: "candidate", asset_id: "missing", media: { token: "missing-token", mime_type: "video/mp4" } },
      ],
    }],
    _media: {
      "good-token": descriptor(goodPath, goodBytes.length, sha256(goodBytes)),
      "reused-token": descriptor(reusedPath, originalBytes.length, sha256(originalBytes)),
      "wrong-token": descriptor(wrongPath, 11, sha256(Buffer.from("expected-video"))),
      "missing-token": descriptor(missingPath, 1, sha256(Buffer.from("x"))),
    },
  });
  const handler = createRunsApiHandler({ repoRoot: root, runProjector: async () => projection() });

  const first = await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));
  assert.equal(first.statusCode, 200);
  assert.equal((await invoke(handler, request("GET", "/api/runs/media/reused-token"))).statusCode, 200);

  await writeFile(reusedPath, "changed-video!");
  const second = await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));
  assert.equal(second.statusCode, 200);
  const detail = JSON.parse(second.body);
  assert.equal(detail.attempts[0].candidate_media.token, "good-token");
  assert.equal(detail.attempts[0].fetched_media.token, undefined);
  assert.equal(detail.attempts[0].fetched_media.availability, "unavailable");
  for (const item of detail.attempts[0].candidate_media_items.slice(1)) {
    assert.equal(item.media.token, undefined);
    assert.equal(item.media.availability, "unavailable");
  }
  assert.equal((await invoke(handler, request("GET", "/api/runs/media/good-token"))).statusCode, 200);
  for (const token of ["reused-token", "wrong-token", "missing-token"]) {
    assert.equal((await invoke(handler, request(`GET`, `/api/runs/media/${token}`))).statusCode, 404);
  }
});

test("valid cached media stays readable throughout a concurrent detail revalidation", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-library-refresh-"));
  const mediaRoot = path.join(root, "runs", "demo");
  await mkdir(mediaRoot, { recursive: true });
  const bytes = Buffer.alloc(8 * 1024 * 1024, 42);
  const source = path.join(mediaRoot, "video.mp4");
  await writeFile(source, bytes);
  const projection = { attempts: [{ fetched_media: { token: "stable-token" } }], _media: {
    "stable-token": { source_path: source, mime_type: "video/mp4", bytes: bytes.length, sha256: sha256(bytes) },
  } };
  const handler = createRunsApiHandler({ repoRoot: root, runProjector: async () => projection });
  const detailRequest = () => invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));
  await detailRequest();
  let finished = false;
  const refreshing = detailRequest().finally(() => { finished = true; });
  await new Promise((resolve) => setImmediate(resolve));
  let reads = 0;
  while (!finished) {
    const head = await invoke(handler, request("HEAD", "/api/runs/media/stable-token"));
    assert.equal(head.statusCode, 200, "refresh must never expose a missing-token window");
    reads += 1;
    await new Promise((resolve) => setImmediate(resolve));
  }
  await refreshing;
  assert.ok(reads > 0);
});
