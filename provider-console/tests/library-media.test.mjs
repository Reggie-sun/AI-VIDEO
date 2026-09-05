import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
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
