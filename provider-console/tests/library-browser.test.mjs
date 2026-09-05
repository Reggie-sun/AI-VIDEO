import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";
import { classifyPlaybackFailure, keepOneAudio } from "../src/library-preview.js";

test("playback failures distinguish missing bytes, decode support, network and abort", async () => {
  const signal = new AbortController().signal;
  const calls = [];
  const readable = async (...args) => { calls.push(args); return { ok: true, status: 200 }; };
  assert.equal(await classifyPlaybackFailure(4, "/api/runs/media/exact", signal, readable), "decode");
  assert.equal(await classifyPlaybackFailure(3, "/api/runs/media/exact", signal, readable), "decode");
  assert.equal(await classifyPlaybackFailure(2, "/api/runs/media/exact", signal, readable), "network");
  assert.equal(calls[0][1].method, "HEAD");
  assert.equal(await classifyPlaybackFailure(4, "/api/runs/media/exact", signal, async () => ({ status: 404 })), "unavailable");
  assert.equal(await classifyPlaybackFailure(4, "/api/runs/media/exact", signal, async () => ({ status: 503 })), "network");
  assert.equal(await classifyPlaybackFailure(4, "/api/runs/media/exact", signal, async () => { throw new Error("offline"); }), "network");
  const aborted = new AbortController(); aborted.abort();
  assert.equal(await classifyPlaybackFailure(4, "/api/runs/media/exact", aborted.signal, readable), null);
  assert.equal(await classifyPlaybackFailure(1, "/api/runs/media/exact", signal, readable), null);
  const switched = new AbortController();
  let resolveRequest;
  const pending = classifyPlaybackFailure(4, "/api/runs/media/exact", switched.signal, () => new Promise((resolve) => { resolveRequest = resolve; }));
  switched.abort();
  resolveRequest({ ok: true, status: 200 });
  assert.equal(await pending, null, "an old response cannot mark a switched player as failed");
});

test("default browser offers one cross-source search, records and explicit follow without decoder burst", async () => {
  const server = await createServer({ root: fileURLToPath(new URL("..", import.meta.url)), server: { middlewareMode: true }, appType: "custom", optimizeDeps: { noDiscovery: true } });
  try {
    const { LibraryBrowser, ExactPlayer, StatusSummary } = await server.ssrLoadModule("/src/library-browser.jsx");
    const { VideoLibraryRail } = await server.ssrLoadModule("/src/video-library-rail.jsx");
    const markup = renderToStaticMarkup(React.createElement(LibraryBrowser, { renderContext() {}, renderRecord() {} }));
    assert.match(markup, /视频库/);
    assert.match(markup, /生成记录/);
    assert.equal((markup.match(/id="video-source-select"/g) || []).length, 1);
    assert.match(markup, /搜索已加载视频/);
    assert.match(markup, /全部证据状态/);
    assert.match(markup, /跟随最新/);
    assert.doesNotMatch(markup, /<video/);
    const entries = Array.from({ length: 40 }, (_, index) => ({ id: String(index), title: `完整作品名 ${index}`, available: true }));
    const cards = renderToStaticMarkup(React.createElement(VideoLibraryRail, { entries }));
    assert.equal((cards.match(/class="library-card"/g) || []).length, 12);
    assert.doesNotMatch(cards, /<video/);
    assert.match(cards, /完整作品名 11/);
    assert.doesNotMatch(cards, /完整作品名 12/);
    assert.match(cards, /预览图暂不可用/);
    const player = renderToStaticMarkup(React.createElement(ExactPlayer, { entry: { id: "exact", title: "作品", available: true, url: "/api/runs/media/exacttoken" } }));
    assert.match(player, /muted=""/);
    assert.match(player, /controls=""/);
    assert.doesNotMatch(player, /autoPlay|loop=/);
    const incompatible = renderToStaticMarkup(React.createElement(ExactPlayer, { entry: { id: "exact", available: true, url: "/api/runs/media/exacttoken" }, measurement: { playbackError: "decode" } }));
    assert.match(incompatible, /浏览器无法解码/);
    assert.match(incompatible, /下载原文件/);
    assert.match(incompatible, /href="\/api\/runs\/media\/exacttoken"/);
    assert.doesNotMatch(incompatible, /文件不可用/);
    const status = renderToStaticMarkup(React.createElement(StatusSummary, { context: { attempt: { status: "running", phase: "validate" } }, available: true }));
    assert.match(status, /已获取 · 可预览/);
    assert.match(status, /等待验证（running \/ validate）/);
    assert.match(status, /未评估/);
  } finally { await server.close(); }
});

test("enabling one comparison audio mutes all other players without seeking or changing speed", () => {
  const left = { muted: false, volume: 1, currentTime: 3, playbackRate: 1 };
  const right = { muted: false, volume: 1, currentTime: 9, playbackRate: 1 };
  keepOneAudio(left, { querySelectorAll: () => [left, right] });
  assert.equal(right.muted, true);
  assert.equal(left.muted, false);
  assert.equal(right.currentTime, 9);
  assert.equal(right.playbackRate, 1);
});
