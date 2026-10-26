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
    const { MediaFolderButton } = await server.ssrLoadModule("/src/media-folder.jsx");
    const { GenerationActivity, generationActivity, PreparationActivityDetail } = await server.ssrLoadModule("/src/generation-activity.jsx");
    const details = [{ status: "valid", workspace: "current/project.yaml", project: { title: "当前作品" }, attempts: [
      { attempt_id: "live", target_shot_id: "S02", started_at: "2026-10-27T10:00:00Z", status: "running", phase: "polling" },
      { attempt_id: "review", target_shot_id: "S01", started_at: "2026-10-27T09:00:00Z", status: "running", phase: "validate" },
    ] }];
    const activity = renderToStaticMarkup(React.createElement(GenerationActivity, { details }));
    assert.match(activity, /S02 · 当前作品/);
    assert.match(activity, /1 个 Shot 执行中/);
    assert.match(activity, /正在生成/);
    assert.doesNotMatch(activity, /S01|<video/);
    const waiting = renderToStaticMarkup(React.createElement(GenerationActivity, { details: [{ ...details[0], attempts: [details[0].attempts[1]] }] }));
    assert.match(waiting, /没有生成中的 Shot/);
    assert.match(waiting, /等待验证/);
    assert.match(renderToStaticMarkup(React.createElement(GenerationActivity, { details, stale: true })), /状态可能已过期/);
    assert.deepEqual(generationActivity([{ ...details[0], status: "recovered_video_evidence" }]), []);
    const preparation = { id: "demo/S05", kind: "local_preparation", directory_name: "S05", run_id: "demo", source_directory: "demo/S05", updated_at: "2026-10-27T11:00:00Z", binding_status: "unbound_local_files", references: [{ file_name: "terminal.png", relative_path: "demo/S05/references/terminal.png", media: { token: "prepared-image", mime_type: "image/png" } }] };
    const preparing = renderToStaticMarkup(React.createElement(GenerationActivity, { details: [], preparations: [preparation] }));
    assert.match(preparing, /S05 · demo/);
    assert.match(preparing, /本地参考准备 · 未关联生成请求/);
    assert.doesNotMatch(preparing, /正在生成|Shot 执行中/);
    const both = renderToStaticMarkup(React.createElement(GenerationActivity, { details, preparations: [preparation] }));
    assert.match(both, /S02 · 当前作品/);
    assert.match(both, /S05 · demo/);
    const preparingDetail = renderToStaticMarkup(React.createElement(PreparationActivityDetail, { preparation }));
    assert.match(preparingDetail, /src="\/api\/runs\/media\/prepared-image"/);
    assert.match(preparingDetail, /不代表已登记的 Shot/);
    assert.match(renderToStaticMarkup(React.createElement(PreparationActivityDetail)), /已不在当前扫描范围/);
    const folder = renderToStaticMarkup(React.createElement(MediaFolderButton, { entry: { available: true, url: "/api/runs/media/exacttoken" } }));
    assert.match(folder, /打开所在文件夹/);
    assert.doesNotMatch(folder, /disabled/);
    for (const entry of [{ available: false }, { available: true, url: "https://example.com/video.mp4" }]) {
      assert.match(renderToStaticMarkup(React.createElement(MediaFolderButton, { entry })), /disabled/);
    }
    const markup = renderToStaticMarkup(React.createElement(LibraryBrowser, { renderContext() {}, renderRecord() {} }));
    assert.match(markup, /视频库/);
    assert.match(markup, /生成记录/);
    assert.equal((markup.match(/id="video-source-select"/g) || []).length, 1);
    assert.match(markup, /搜索已加载视频/);
    assert.match(markup, /全部证据状态/);
    assert.match(markup, /跟随最新/);
    assert.match(markup, /关联全部 Runs 证据/);
    assert.match(markup, /尚未执行全量关联/);
    assert.match(markup, /<details class="library-coverage"><summary>/);
    assert.match(markup, /扫描详情与加载选项/);
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
